import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from backend.client import VLLMClient
from backend.models import Location, PlayerAction, WorldState
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def parse_vllm_response(raw_data: Any) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parses response from VLLM client into narration text, state_updates dict, and events list.
    """
    narration = ""
    state_updates: Dict[str, Any] = {}
    events: List[Dict[str, Any]] = []

    if isinstance(raw_data, dict):
        if "text" in raw_data and isinstance(raw_data["text"], str):
            narration = raw_data["text"]
        elif "choices" in raw_data and isinstance(raw_data["choices"], list) and len(raw_data["choices"]) > 0:
            choice = raw_data["choices"][0]
            if isinstance(choice, dict):
                narration = choice.get("text", "") or choice.get("message", {}).get("content", "")
        elif "narration" in raw_data:
            narration = str(raw_data["narration"])
    elif isinstance(raw_data, str):
        narration = raw_data

    # Parse [Narration] and [StateUpdates] section tags if embedded in narrative response
    if "[Narration]" in narration or "[StateUpdates]" in narration:
        parts = narration.split("[StateUpdates]")
        narration_clean = parts[0].replace("[Narration]", "").strip()

        if len(parts) > 1:
            updates_str = parts[1].strip()
            if "```" in updates_str:
                updates_str = updates_str.split("```")[1]
                if updates_str.startswith("json"):
                    updates_str = updates_str[4:]
                updates_str = updates_str.strip()
            if "[Events]" in updates_str:
                su_part, ev_part = updates_str.split("[Events]", 1)
                try:
                    state_updates = json.loads(su_part.strip())
                except Exception:
                    state_updates = {}
                try:
                    events = json.loads(ev_part.strip())
                except Exception:
                    events = []
            else:
                try:
                    state_updates = json.loads(updates_str)
                except Exception:
                    state_updates = {}
        narration = narration_clean
    else:
        # Strip out any JSON block at the end if present
        json_match = re.search(r"\{.*\}", narration, re.DOTALL)
        if json_match:
            try:
                state_updates = json.loads(json_match.group(0))
                narration = narration[: json_match.start()].strip()
            except Exception:
                pass

    # Override or supplement with direct dictionary keys if present (e.g. from mock return values)
    if isinstance(raw_data, dict):
        if raw_data.get("state_updates") is not None:
            state_updates = raw_data["state_updates"]
        if raw_data.get("events") is not None:
            events = raw_data["events"]

    return narration, state_updates, events


_NARR_TAG = "[Narration]"
_SU_TAG = "[StateUpdates]"


def _chunk_text(chunk) -> str:
    """Extract the text delta from a raw vLLM stream chunk (dict or str)."""
    if isinstance(chunk, dict):
        if chunk.get("choices"):
            choice = chunk["choices"][0]
            return (
                choice.get("text", "")
                or choice.get("delta", {}).get("content", "")
                or choice.get("message", {}).get("content", "")
            )
        return chunk.get("text", "") or ""
    if isinstance(chunk, str):
        return chunk
    return ""


def stream_narration(text_chunks):
    """Yield cleaned narration text from a stream of raw model text chunks.

    Strips the leading `[Narration]` header (even when split across chunks) and stops as
    soon as `[StateUpdates]` begins, holding back any trailing fragment that could be the
    start of either tag so a partial `[Narr…`/`[Stat…` never leaks to the client (CR12).
    """
    acc = ""
    emitted = 0
    for text in text_chunks:
        if not text:
            continue
        acc += text
        head = acc.split(_SU_TAG, 1)[0]
        cleaned = head.replace(_NARR_TAG, "")
        safe_len = len(cleaned)
        bracket = cleaned.rfind("[")
        if bracket != -1:
            frag = cleaned[bracket:]
            if any(t.startswith(frag) for t in (_NARR_TAG, _SU_TAG)):
                safe_len = bracket
        if safe_len > emitted:
            yield cleaned[emitted:safe_len]
            emitted = safe_len
        if _SU_TAG in acc:
            return


class NarrativeEngine:
    def __init__(self, state_or_client: Any = None, vllm_client: Optional[VLLMClient] = None):
        if isinstance(state_or_client, VLLMClient):
            self.vllm_client = state_or_client
            self.initial_state = None
        elif state_or_client is not None and not isinstance(state_or_client, VLLMClient):
            self.initial_state = state_or_client
            self.vllm_client = vllm_client if vllm_client is not None else VLLMClient()
        else:
            self.initial_state = None
            if vllm_client is None:
                raise ValueError("VLLMClient must be provided explicitly if no initial state is given.")
            self.vllm_client = vllm_client

    def _extract_state(self, action, state, narration: str) -> Dict[str, Any]:
        """Focused JSON-only second pass: derive concrete state changes from the action +
        narration. Returns {} on any failure so gameplay never breaks."""
        inv = ", ".join(i.get("name", "") for i in (getattr(state, "inventory", []) or [])) or "empty"
        coins = getattr(state, "brass_coins", 0)
        mq = getattr(state, "main_quest", None)
        mq_line = (
            f'Main quest current objective: "{mq.get("current_objective")}".'
            if isinstance(mq, dict) and mq.get("current_objective")
            else "No active main quest."
        )
        _npcs = getattr(state, "active_npcs", []) or []
        engaged_npcs = ", ".join(n.name for n in _npcs if getattr(n, "in_earshot", False)) or "none"
        nearby_npcs = ", ".join(n.name for n in _npcs if not getattr(n, "in_earshot", False)) or "none"
        prompt = (
            "You are the STATE ENGINE for a steampunk RPG. Given the player's action and the "
            "resulting narration, output ONLY a JSON object of the concrete mechanical changes. "
            "Output {} if nothing mechanical changed. No prose, no code fences.\n\n"
            f"Current wealth: {coins} brass coins. Inventory: {inv}. {mq_line} "
            f"Engaged NPCs (in earshot, actively interacting): {engaged_npcs}. "
            f"Other NPCs present nearby (not engaged): {nearby_npcs}. "
            f"Combat active: {getattr(state, 'is_combat_active', False)}.\n\n"
            f'Player action: "{action.action_text}"\n'
            f"Narration: {narration}\n\n"
            "Include ONLY keys that changed, from this schema:\n"
            '{ "empire_updates": {"brass_coins_change": <int delta>}, '
            '"inventory_updates": [{"action":"add|remove","item_name":<str>,"quantity":<int>,"description":<str>}], '
            '"quest_updates": [{"action":"add|update|complete|fail","quest_title":<str>,"description":<str>}], '
            '"combat_updates": {"is_combat_active":<bool>,"enemy":<str full name of who the player is fighting>,"player_updates":{"hp_change":<int>,"steam_change":<int>}}, '
            '"minigame_trigger": "hack|lockpick", '
            '"artifact_discovered": <full name of a legendary artifact the player just found, if any>, '
            '"main_quest_updates": {"advance_stage": true}, '
            '"active_npcs": [{"id":<str>,"name":<str>,"traits":[<str>],"location_id":<str id of where they physically are — omit for the current location>}] }\n'
            "Brass coins / currency changes go ONLY in empire_updates.brass_coins_change (a "
            "signed integer delta) — NEVER as an inventory_updates item. "
            "Only add to active_npcs a BRAND-NEW named character introduced this turn who is "
            "NOT already present (see the list above); never re-list an existing NPC, and "
            "always use their full name. "
            "COMBAT: if the player attacks, is attacked, or a fight breaks out, you MUST set "
            "combat_updates.is_combat_active=true, set combat_updates.enemy to the full name "
            "of the character or creature being fought (as named in the narration — normally "
            "the engaged/in-earshot NPC when the fight is with someone already present), and include "
            "player_updates hp_change/steam_change for any blows taken or abilities used. Set "
            "is_combat_active=false only once the fight is clearly over. "
            "Advance the main quest only if the narration clearly completes the current objective. "
            "Return ONLY the JSON object."
        )
        try:
            resp = self.vllm_client.generate(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            text = ""
            if isinstance(resp, dict):
                if resp.get("choices"):
                    choice = resp["choices"][0]
                    text = choice.get("message", {}).get("content", "") or choice.get("text", "")
                else:
                    text = resp.get("text", "")
            elif isinstance(resp, str):
                text = resp
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                if isinstance(data, dict):
                    return data
        except Exception as e:
            logger.warning(f"State extraction pass failed: {e}")
        return {}

    def process_action(self, action: PlayerAction, session: Optional[Session] = None):
        if session:
            from backend.database import Character
            from backend.database import WorldState as DBWorldState
            from sqlmodel import select

            if action.current_location_id:
                loc_changed = False
                if action.character_id:
                    char = session.get(Character, action.character_id)
                    if char and char.location_id != action.current_location_id:
                        char.location_id = action.current_location_id
                        session.add(char)
                        loc_changed = True

                db_state = session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()
                if db_state and db_state.current_location_id != action.current_location_id:
                    db_state.current_location_id = action.current_location_id
                    # Leaving a location leaves earshot of everyone there.
                    db_state.active_npcs_ids = []
                    session.add(db_state)
                    loc_changed = True

                if loc_changed:
                    session.commit()

            repository = StateRepository(session)
            state = repository.get_latest_state(action.character_id)
            # NPCs the player names this turn come within earshot / into active engagement.
            repository.engage_named_npcs(action.action_text, state)
            # Explorer's Journal: log the visited location + NPCs met (C2).
            repository.record_discoveries(
                action.character_id,
                getattr(state, "current_location_id", None),
                [n.id for n in (getattr(state, "active_npcs", []) or [])],
            )
        elif self.initial_state:
            repository = None
            state = self.initial_state
        else:
            repository = None
            state = WorldState(
                current_location_id="1",
                current_location=Location(id="1", name="Steamworks", description="A dark workshop.", npcs=[]),
                active_npcs=[],
            )

        ghost_echoes = []
        if session and state.is_combat_active and state.combat_state:
            cs = state.combat_state
            turn_order = cs.get("turn_order", [])
            idx = cs.get("current_turn_index", 0)
            if turn_order and idx < len(turn_order):
                current_turn = turn_order[idx]
                if current_turn["type"] == "player" and current_turn["id"] != f"player_{action.character_id}":
                    # NOT THIS PLAYER'S TURN
                    yield {
                        "narration": f"[System] It is not your turn! It is currently {current_turn['name']}'s turn.",
                        "state_updates": {},
                        "events": [],
                        "is_combat_active": True,
                    }
                    return

        if session:
            import random

            from backend.database import Character, LedgerEntry
            from sqlmodel import select

            # Get recent actions from other characters in the same location
            char_id = getattr(getattr(state, "player_stats", None), "id", None)
            loc_id = getattr(state, "current_location_id", "1")

            # Fetch up to 10 recent ledger entries in this location, not by this character
            echo_entries = session.exec(
                select(LedgerEntry)
                .where(LedgerEntry.location_id == str(loc_id), LedgerEntry.character_id != char_id)
                .order_by(LedgerEntry.timestamp.desc())
                .limit(10)
            ).all()

            if isinstance(echo_entries, list) and echo_entries:
                # Pick 1-2 random echoes to include as flavor
                chosen = random.sample(echo_entries, min(2, len(echo_entries)))
                for entry in chosen:
                    char = session.get(Character, entry.character_id)
                    char_name = char.name if char else "A stranger"
                    ghost_echoes.append(f"{char_name} recently did this here: {entry.action}")

        prompt_str = build_narrative_prompt(state, action, ghost_echoes=ghost_echoes)

        system_prompt = getattr(state, "global_system_prompt", None)

        full_raw_data = ""
        def _texts():
            nonlocal full_raw_data
            for chunk in self.vllm_client.generate_stream(
                prompt_str, system_prompt=system_prompt, max_tokens=1500
            ):
                t = _chunk_text(chunk)
                if t:
                    full_raw_data += t
                    yield t

        # Stream cleaned narration to the client (no [Narration]/[StateUpdates] tags leak).
        for piece in stream_narration(_texts()):
            if piece:
                yield piece

        narration, state_updates, events = parse_vllm_response(full_raw_data)

        # Second pass: many models won't reliably co-emit [StateUpdates] alongside rich prose.
        # If the first pass yielded no structured state, run a focused JSON-only extraction call
        # over the action + narration so the world actually reacts (CR11 in practice).
        if not state_updates:
            extracted = self._extract_state(action, state, narration)
            if extracted:
                state_updates = extracted
                full_raw_data += "\n[StateUpdates]\n" + json.dumps(extracted)

        if repository and state_updates:
            # Advance the staged main quest when the narrator completes the current objective (CR10).
            mqu = state_updates.get("main_quest_updates")
            if isinstance(mqu, dict) and mqu.get("advance_stage"):
                repository.advance_main_quest(action.character_id or 1)

            loc_id = state_updates.get("location_id") or getattr(state, "current_location_id", "1")
            if "location_name" in state_updates or "location_description" in state_updates:
                loc_data = {}
                if "location_name" in state_updates:
                    loc_data["name"] = state_updates["location_name"]
                if "location_description" in state_updates:
                    loc_data["description"] = state_updates["location_description"]
                repository.update_location(loc_id, loc_data)

            if "active_npcs" in state_updates and isinstance(state_updates["active_npcs"], list):
                for npc_info in state_updates["active_npcs"]:
                    if isinstance(npc_info, dict):
                        # Situate the NPC where the narration places them — honor an explicit
                        # location_id, else default to the player's current location (report #4).
                        npc_loc = npc_info.get("location_id") or loc_id
                        npc = repository.create_or_update_npc(npc_info, npc_loc)

                        is_dead = False
                        if npc.traits:
                            is_dead = any(t.lower() == "dead" for t in npc.traits)

                        # A dead NPC leaves the earshot scene set. New NPCs are NOT auto-added
                        # to it — earshot is reserved for NPCs the player actively engages
                        # (engage_named_npcs); a freshly-introduced NPC surfaces as "nearby".
                        if is_dead:
                            if isinstance(state.active_npcs_ids, list) and npc.id in state.active_npcs_ids:
                                state.active_npcs_ids.remove(npc.id)

                        try:
                            npc_dict = {
                                "id": npc.id,
                                "name": npc.name,
                                "traits": npc.traits or [],
                                "disposition": npc.disposition,
                                "hp": 0 if is_dead else 100,
                                "location_id": npc.location_id,
                            }
                            events.append({"type": "npc_state_change", "npc": npc_dict})
                        except Exception as e:
                            logger.error(f"Failed to append NPC state change event: {e}")

            if state_updates.get("artifact_discovered"):
                repository.discover_artifact_by_name(action.character_id, state_updates["artifact_discovered"])

            if "inventory_updates" in state_updates and isinstance(state_updates["inventory_updates"], list):
                for inv_update in state_updates["inventory_updates"]:
                    if isinstance(inv_update, dict):
                        repository.apply_inventory_update(inv_update, action.character_id or 1)

            if "tool_durability_updates" in state_updates and isinstance(
                state_updates["tool_durability_updates"], list
            ):
                for td_update in state_updates["tool_durability_updates"]:
                    if isinstance(td_update, dict):
                        repository.apply_tool_durability_update(td_update, action.character_id or 1)

            if "quest_updates" in state_updates and isinstance(state_updates["quest_updates"], list):
                for quest_update in state_updates["quest_updates"]:
                    if isinstance(quest_update, dict):
                        repository.apply_quest_update(quest_update, action.character_id or 1)

            if "faction_updates" in state_updates and isinstance(state_updates["faction_updates"], list):
                for faction_update in state_updates["faction_updates"]:
                    if isinstance(faction_update, dict):
                        repository.apply_faction_update(faction_update, action.character_id or 1)

            if "combat_updates" in state_updates:
                repository.apply_combat_update(state_updates["combat_updates"], action.character_id or 1)

            if "empire_updates" in state_updates:
                repository.apply_empire_update(state_updates["empire_updates"], action.character_id or 1)

            if "new_entities" in state_updates and isinstance(state_updates["new_entities"], list):
                repository.apply_new_entities(state_updates["new_entities"], loc_id)

            if "minigame_trigger" in state_updates:
                minigame_type = state_updates["minigame_trigger"]
                if minigame_type in ["hack", "lockpick"]:
                    repository.trigger_minigame(minigame_type, action.character_id or 1)

            if state_updates.get("location_id"):
                state.current_location_id = state_updates["location_id"]
                if action.character_id:
                    from backend.database import Character

                    char_to_update = session.get(Character, action.character_id)
                    if char_to_update:
                        char_to_update.location_id = state_updates["location_id"]
                        session.add(char_to_update)
                repository.save_state(state)

        if repository:
            repository.record_ledger_entry(
                action=action.action_text,
                narration=narration,
                state_updates=state_updates,
                events=events,
                location_id=getattr(state, "current_location_id", "1"),
                character_id=getattr(getattr(state, "player_stats", None), "id", None),
            )

        active_npcs = getattr(state, "active_npcs", []) or []
        npc_names = [getattr(npc, "name", str(npc)) for npc in active_npcs]

        if repository and getattr(state, "is_combat_active", False) and getattr(state, "combat_state", None):
            cs = state.combat_state
            turn_order = cs.get("turn_order", [])
            idx = cs.get("current_turn_index", 0)
            if turn_order:
                # Advance turn
                idx = (idx + 1) % len(turn_order)
                original_idx = idx
                while turn_order[idx].get("type") != "player":
                    idx = (idx + 1) % len(turn_order)
                    if idx == original_idx:
                        break

                from backend.database import CombatSession
                from sqlmodel import select

                loc_id = getattr(state, "current_location_id", "1")
                combat_session = session.exec(
                    select(CombatSession).where(CombatSession.location_id == loc_id, CombatSession.is_active)
                ).first()
                if combat_session:
                    combat_session.current_turn_index = idx
                    session.add(combat_session)
                    session.commit()

        yield {
            "narration": narration,
            "state_updates": state_updates,
            "npcs": npc_names,
            "events": events or [],
            "is_combat_active": getattr(state, "is_combat_active", False),
        }


import random

from backend.client import VLLMClient
from backend.database import ResourceMarket, WorldEvent
from sqlmodel import select


def simulate_economy_tick(session: Session):
    """
    Simulate the economy tick by fluctuating prices based on base price, volatility, and active world events.
    """
    import random

    # Get active events
    active_events = session.exec(select(WorldEvent).where(WorldEvent.is_active == 1)).all()

    # Aggregate modifiers from events
    modifiers = {}
    for event in active_events:
        for resource, impact in event.faction_impacts.items():
            if resource not in modifiers:
                modifiers[resource] = 1.0
            # Severity scales the impact
            modifiers[resource] += impact * event.severity

    markets = session.exec(select(ResourceMarket)).all()

    for market in markets:
        # Base random fluctuation based on volatility
        fluctuation = 1.0 + random.uniform(-market.volatility, market.volatility)

        # Apply event modifiers if any
        modifier = modifiers.get(market.resource_name, 1.0)

        # Calculate new price
        market.current_price = max(1.0, market.current_price * fluctuation * modifier)

        # Trend back towards base price slightly if no extreme events
        if modifier == 1.0:
            market.current_price += (market.base_price - market.current_price) * 0.05

        session.add(market)
    session.commit()


def simulate_weather_time(session: Session):
    import random

    from backend.database import WorldState as DBWorldState

    db_state = session.exec(select(DBWorldState).order_by(DBWorldState.id.desc())).first()
    if db_state:
        db_state.world_time = (db_state.world_time or 0) + 1
        hour = db_state.world_time % 24

        if 5 <= hour < 8:
            db_state.time_period = "Dawn"
        elif 8 <= hour < 18:
            db_state.time_period = "Day"
        elif 18 <= hour < 21:
            db_state.time_period = "Dusk"
        else:
            db_state.time_period = "Night"

        if random.random() < 0.02:
            db_state.weather = random.choice(["Clear", "Fog", "Rain", "Thunderstorm"])

        session.add(db_state)
        session.commit()

def _tick_property_income(session: Session):
    from backend.database import Character, Property

    chars = session.exec(select(Character)).all()
    for char in chars:
        properties = session.exec(select(Property).where(Property.owner_id == char.id)).all()
        total_income = sum(p.income_per_tick for p in properties)
        if total_income > 0:
            char.brass_coins += total_income
            session.add(char)
    session.commit()


def tick_market(session: Session):
    """One market-drift step (formerly the 10s background loop body). DB-only."""
    from backend.database import ResourceMarket as _RM

    markets = session.exec(select(_RM)).all()
    for m in markets:
        drift = random.uniform(-m.volatility, m.volatility)
        m.current_price = max(1.0, m.current_price * (1.0 + drift))
        if random.random() < 0.05:
            m.current_price = min(m.base_price * 5, m.current_price * 1.1)
        session.add(m)
    session.commit()


def tick_faction_wars(session: Session):
    """One faction-war step (formerly the 20s background loop body). DB-only; returns an
    optional global-event message when a faction annexes a location."""
    from backend.database import Faction, FactionStanding, Location
    from backend.database import WorldState as _WS
    from sqlalchemy import func

    event_msg = None
    results = session.exec(
        select(FactionStanding.faction_id, func.sum(FactionStanding.standing)).group_by(FactionStanding.faction_id)
    ).all()
    for faction_id, total_standing in results:
        if total_standing and total_standing > 10.0:
            target_locs = session.exec(select(Location).where(Location.faction_id != faction_id)).all()
            if not target_locs:
                continue
            target = random.choice(target_locs)
            target.faction_id = faction_id
            session.add(target)
            faction = session.exec(select(Faction).where(Faction.id == faction_id)).first()
            fact_name = faction.name if faction else faction_id
            event_msg = (
                f"GLOBAL WAR ALERT: Due to overwhelming player support, the {fact_name} "
                f"has permanently annexed {target.name}!"
            )
            for state in session.exec(select(_WS)).all():
                state.global_event = event_msg
                session.add(state)
            for s in session.exec(select(FactionStanding).where(FactionStanding.faction_id == faction_id)).all():
                if s.standing > 0:
                    s.standing = s.standing * 0.5
                    session.add(s)
            session.commit()
    return event_msg


def run_world_turn(session: Session):
    """One world tick, gated to a chat turn (no background timer — report #10). Advances
    time/weather, economy prices, property income, market drift, and faction wars. NPC-to-NPC
    'overheard' interactions were removed (they injected phantom NPCs from other locations).
    Returns an optional global-event message to surface."""
    simulate_weather_time(session)
    simulate_economy_tick(session)
    _tick_property_income(session)
    tick_market(session)
    return tick_faction_wars(session)
