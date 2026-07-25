"""Validation for uploaded mod files (roadmap C8.2).

`validate_mod` checks a parsed mod dict against the supported entity schemas, enforces
in-file id uniqueness, and verifies cross-entity references resolve (in the DB or the same
file). It returns a list of human-readable error strings — empty when the mod is valid —
so callers can reject the whole upload atomically.
"""

from typing import Any, Dict, List, Optional

from backend.database import Faction as DBFaction
from backend.database import ItemCategory
from backend.database import Location as DBLocation
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlmodel import select


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FactionMod(_StrictModel):
    id: str
    name: str
    description: str


class LocationMod(_StrictModel):
    id: str
    name: str
    description: str
    faction_id: Optional[str] = None


class NpcMod(_StrictModel):
    id: str
    name: str
    traits: Optional[List[str]] = None
    current_dialogue: Optional[str] = None
    disposition: Optional[float] = None
    memories: Optional[List[Dict[str, str]]] = None
    location_id: Optional[str] = None
    faction_id: Optional[str] = None
    custom_system_prompt: Optional[str] = None
    speed: Optional[int] = None
    hp: Optional[int] = None
    max_hp: Optional[int] = None
    armor: Optional[int] = None
    status_effects: Optional[List[str]] = None
    is_hostile: Optional[bool] = None


class ItemMod(_StrictModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    category: ItemCategory


# section name -> (schema model, key used for uniqueness)
_SECTIONS = {
    "factions": (FactionMod, "id"),
    "locations": (LocationMod, "id"),
    "npcs": (NpcMod, "id"),
    "items": (ItemMod, "name"),
}


def _label(section: str, index: int, entity: Dict[str, Any]) -> str:
    ident = entity.get("id") or entity.get("name") or "?"
    return f"{section}[{index}] ({ident})"


def _format_pydantic_errors(section: str, index: int, entity: Dict, exc: ValidationError) -> List[str]:
    out = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"]) or "(root)"
        out.append(f"{_label(section, index, entity)}: {field} — {err['msg']}")
    return out


def validate_mod(data: Any, session) -> List[str]:
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["Mod must be a JSON object."]

    # 1) Structure + schema validation.
    parsed: Dict[str, List[Dict]] = {}
    for section, (model, _key) in _SECTIONS.items():
        if section not in data:
            continue
        rows = data[section]
        if not isinstance(rows, list):
            errors.append(f"'{section}' must be a list.")
            continue
        parsed[section] = []
        for i, entity in enumerate(rows):
            if not isinstance(entity, dict):
                errors.append(f"{section}[{i}]: each entry must be an object.")
                continue
            try:
                model(**entity)
                parsed[section].append(entity)
            except ValidationError as exc:
                errors.extend(_format_pydantic_errors(section, i, entity, exc))

    # 2) In-file id/name uniqueness.
    for section, (_model, key) in _SECTIONS.items():
        seen = set()
        for i, entity in enumerate(parsed.get(section, [])):
            val = entity.get(key)
            if val is None:
                continue
            if val in seen:
                errors.append(f"{_label(section, i, entity)}: duplicate {key} '{val}' in file.")
            seen.add(val)

    # 3) Referential existence (DB rows + entities defined in this file).
    faction_ids = {f.id for f in session.exec(select(DBFaction)).all()}
    faction_ids |= {e.get("id") for e in parsed.get("factions", [])}
    location_ids = {loc.id for loc in session.exec(select(DBLocation)).all()}
    location_ids |= {e.get("id") for e in parsed.get("locations", [])}

    for i, loc in enumerate(parsed.get("locations", [])):
        fid = loc.get("faction_id")
        if fid and fid not in faction_ids:
            errors.append(f"{_label('locations', i, loc)}: faction_id '{fid}' does not exist.")

    for i, npc in enumerate(parsed.get("npcs", [])):
        lid = npc.get("location_id")
        if lid and lid not in location_ids:
            errors.append(f"{_label('npcs', i, npc)}: location_id '{lid}' does not exist.")
        fid = npc.get("faction_id")
        if fid and fid not in faction_ids:
            errors.append(f"{_label('npcs', i, npc)}: faction_id '{fid}' does not exist.")

    return errors
