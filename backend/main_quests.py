"""Main-quest presets and LLM generation (CR10)."""

import json
import random
import re
from typing import Any, Dict, List, Optional

# Curated, staged main-quest arcs.
PRESET_MAIN_QUESTS: List[Dict[str, Any]] = [
    {
        "id": "aether_heart",
        "title": "The Aether Heart",
        "description": "A dying inventor entrusts you with recovering the Aether Heart, a "
        "core that could power — or level — the whole city.",
        "stages": [
            "Track down the inventor's missing apprentice in the Undercity.",
            "Recover the stolen schematic from an Iron Syndicate vault.",
            "Assemble the Aether Heart at a hidden workshop.",
            "Decide the Heart's fate before the Syndicate seizes it.",
        ],
    },
    {
        "id": "syndicate_ledger",
        "title": "The Syndicate Ledger",
        "description": "A whistle-blower's ledger exposes the Iron Syndicate's crimes. Get it "
        "into the right hands before you're silenced.",
        "stages": [
            "Meet the whistle-blower at the Rusty Anchor after dark.",
            "Smuggle the ledger past a Syndicate checkpoint.",
            "Find a printer willing to publish the truth.",
            "Survive the Syndicate's reprisal.",
        ],
    },
    {
        "id": "clockwork_uprising",
        "title": "The Clockwork Uprising",
        "description": "Automata across the city are awakening. Guide the uprising — or "
        "quell it — and shape what freedom means for the machines.",
        "stages": [
            "Investigate the first self-aware automaton in the Foundry.",
            "Broker a meeting between the automata and the Alchemists Guild.",
            "Sabotage or protect the Syndicate's control tower.",
            "Lead the automata to their reckoning.",
        ],
    },
    {
        "id": "fog_beneath",
        "title": "The Fog Beneath",
        "description": "Something ancient stirs in the flooded tunnels below. Chart the depths "
        "and learn what the fog is hiding.",
        "stages": [
            "Buy a fog-lamp and a map of the lower tunnels.",
            "Descend past the old naval garrison.",
            "Confront the source of the fog.",
            "Escape with what you've learned.",
        ],
    },
]


def _stages_from_titles(titles: List[str]) -> List[Dict[str, str]]:
    stages = [{"description": t, "status": "pending"} for t in titles if t and str(t).strip()]
    if stages:
        stages[0]["status"] = "active"
    return stages


def preset_list() -> List[Dict[str, Any]]:
    return [
        {"id": p["id"], "title": p["title"], "description": p["description"], "stages": list(p["stages"])}
        for p in PRESET_MAIN_QUESTS
    ]


def random_preset() -> Dict[str, Any]:
    p = random.choice(PRESET_MAIN_QUESTS)
    return {"id": p["id"], "title": p["title"], "description": p["description"], "stages": list(p["stages"])}


def normalize_input(title: str, description: str, stages: List[Any]) -> Dict[str, Any]:
    """Shape an arbitrary main-quest choice into the stored form (stage 0 active)."""
    stage_titles = [s if isinstance(s, str) else s.get("description", "") for s in (stages or [])]
    return {
        "title": title or "Untitled Arc",
        "description": description or "",
        "stages": _stages_from_titles(stage_titles),
    }


def _parse_generated(text: str) -> Optional[Dict[str, Any]]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except (json.JSONDecodeError, ValueError):
        return None
    title = data.get("title")
    stages = data.get("stages")
    if not title or not isinstance(stages, list) or not stages:
        return None
    return {"title": title, "description": data.get("description", ""), "stages": stages}


def generate_main_quest(client, preset: str = "", origin: str = "", backstory: str = "") -> Dict[str, Any]:
    """Generate a staged main quest via the LLM; fall back to a random preset on failure."""
    prompt = (
        "Create a staged main quest for a steampunk RPG character. "
        f"Class/preset: {preset or 'unknown'}. Origin: {origin or 'unknown'}. "
        f"Backstory: {backstory or 'none'}.\n"
        "Return ONLY JSON: {\"title\": str, \"description\": str, "
        "\"stages\": [4 short objective strings]}."
    )
    try:
        resp = client.generate(prompt=prompt, max_tokens=400, temperature=0.8)
        text = ""
        if isinstance(resp, dict):
            if resp.get("choices"):
                choice = resp["choices"][0]
                text = choice.get("text", "") or choice.get("message", {}).get("content", "")
            else:
                text = resp.get("text", "")
        elif isinstance(resp, str):
            text = resp
        parsed = _parse_generated(text)
        if parsed:
            return parsed
    except Exception:
        pass
    return random_preset()
