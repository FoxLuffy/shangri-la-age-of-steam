from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.database import (
    Character,
    Inventory,
    QuestState,
    QuestStateEnum,
    SaveState,
    WorldState,
    get_session,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

router = APIRouter()

# Character fields that are restored from a snapshot. Identity/ownership fields
# (id, user_id) are intentionally excluded so a load stays on the same slot.
_CHARACTER_RESTORE_EXCLUDE = {"id", "user_id"}
_WORLD_RESTORE_EXCLUDE = {"id"}

# Bump when the exported save JSON shape changes incompatibly.
CURRENT_SAVE_SCHEMA_VERSION = 1


class SaveCreateRequest(BaseModel):
    character_id: int
    name: Optional[str] = None


class InventoryEntry(BaseModel):
    item_id: int
    quantity: int
    durability: Optional[int] = None


class QuestEntry(BaseModel):
    quest_id: int
    state: str


class SaveSnapshot(BaseModel):
    character: Dict[str, Any]
    world: Optional[Dict[str, Any]] = None
    inventory: List[InventoryEntry] = []
    quests: List[QuestEntry] = []


class SaveExport(BaseModel):
    schema_version: int = CURRENT_SAVE_SCHEMA_VERSION
    name: str
    created_at: str
    snapshot: SaveSnapshot


def _build_snapshot(session, character: Character) -> dict:
    world = session.exec(select(WorldState)).first()
    inventory = session.exec(select(Inventory).where(Inventory.character_id == character.id)).all()
    quests = session.exec(select(QuestState).where(QuestState.character_id == character.id)).all()

    return {
        "character": character.model_dump(mode="json"),
        "world": world.model_dump(mode="json") if world else None,
        "inventory": [
            {"item_id": inv.item_id, "quantity": inv.quantity, "durability": inv.durability}
            for inv in inventory
        ],
        "quests": [{"quest_id": qs.quest_id, "state": qs.state.value} for qs in quests],
    }


def _save_payload(save: SaveState) -> dict:
    return {
        "id": save.id,
        "character_id": save.character_id,
        "name": save.name,
        "created_at": save.created_at,
    }


@router.post("/saves")
async def create_save(req: SaveCreateRequest):
    """Create or overwrite the single save slot for a character.

    Each character has at most one save state. Saving again (manually or via
    autosave) overwrites the existing slot rather than creating a new one.
    """
    with get_session() as session:
        character = session.get(Character, req.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        save = session.exec(
            select(SaveState).where(SaveState.character_id == character.id)
        ).first()
        is_new = save is None
        if is_new:
            save = SaveState(character_id=character.id)

        default_name = f"{character.name} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        if req.name:
            save.name = req.name
        elif is_new:
            save.name = default_name
        # Otherwise keep the existing slot name on overwrite/autosave.
        save.created_at = datetime.utcnow().isoformat() + "Z"
        save.snapshot = _build_snapshot(session, character)
        session.add(save)
        session.commit()
        session.refresh(save)
        return _save_payload(save)


@router.get("/saves/{character_id}")
async def get_save(character_id: int):
    with get_session() as session:
        save = session.exec(
            select(SaveState).where(SaveState.character_id == character_id)
        ).first()
        if not save:
            raise HTTPException(status_code=404, detail="No save for this character")
        return _save_payload(save)


@router.get("/saves/{character_id}/load")
async def load_save(character_id: int):
    with get_session() as session:
        save = session.exec(
            select(SaveState).where(SaveState.character_id == character_id)
        ).first()
        if not save:
            raise HTTPException(status_code=404, detail="No save for this character")

        snapshot = save.snapshot or {}
        character = session.get(Character, character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Restore character scalar fields.
        for key, value in (snapshot.get("character") or {}).items():
            if key in _CHARACTER_RESTORE_EXCLUDE:
                continue
            if hasattr(character, key):
                setattr(character, key, value)
        session.add(character)

        # Restore the global world state row.
        world_snapshot = snapshot.get("world")
        if world_snapshot:
            world = session.exec(select(WorldState)).first()
            if world is None:
                world = WorldState()
            for key, value in world_snapshot.items():
                if key in _WORLD_RESTORE_EXCLUDE:
                    continue
                if hasattr(world, key):
                    setattr(world, key, value)
            session.add(world)

        # Replace inventory rows for this character.
        for inv in session.exec(
            select(Inventory).where(Inventory.character_id == character.id)
        ).all():
            session.delete(inv)
        for row in snapshot.get("inventory", []):
            session.add(
                Inventory(
                    character_id=character.id,
                    item_id=row["item_id"],
                    quantity=row["quantity"],
                    durability=row.get("durability"),
                )
            )

        # Replace quest-state rows for this character.
        for qs in session.exec(
            select(QuestState).where(QuestState.character_id == character.id)
        ).all():
            session.delete(qs)
        for row in snapshot.get("quests", []):
            session.add(
                QuestState(
                    character_id=character.id,
                    quest_id=row["quest_id"],
                    state=QuestStateEnum(row["state"]),
                )
            )

        session.commit()
        return {
            "status": "loaded",
            "save_id": save.id,
            "character_id": character.id,
            "name": save.name,
        }


@router.delete("/saves/{character_id}")
async def delete_save(character_id: int):
    with get_session() as session:
        save = session.exec(
            select(SaveState).where(SaveState.character_id == character_id)
        ).first()
        if not save:
            raise HTTPException(status_code=404, detail="No save for this character")
        session.delete(save)
        session.commit()
        return {"status": "deleted", "character_id": character_id}


@router.get("/saves/{character_id}/export", response_model=SaveExport)
async def export_save(character_id: int):
    """Return the character's save slot as a versioned, downloadable JSON payload."""
    with get_session() as session:
        save = session.exec(
            select(SaveState).where(SaveState.character_id == character_id)
        ).first()
        if not save:
            raise HTTPException(status_code=404, detail="No save for this character")
        return SaveExport(
            schema_version=CURRENT_SAVE_SCHEMA_VERSION,
            name=save.name,
            created_at=save.created_at,
            snapshot=save.snapshot or {},
        )


@router.post("/saves/{character_id}/import")
async def import_save(character_id: int, payload: SaveExport):
    """Validate an uploaded save JSON and write it into the character's slot.

    The live game is left untouched; the player applies it later via load.
    """
    if payload.schema_version != CURRENT_SAVE_SCHEMA_VERSION:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported save schema_version {payload.schema_version}; "
            f"expected {CURRENT_SAVE_SCHEMA_VERSION}",
        )

    with get_session() as session:
        character = session.get(Character, character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        save = session.exec(
            select(SaveState).where(SaveState.character_id == character_id)
        ).first()
        if save is None:
            save = SaveState(character_id=character_id)

        save.name = payload.name or save.name or f"Imported — {character.name}"
        save.created_at = datetime.utcnow().isoformat() + "Z"
        save.snapshot = payload.snapshot.model_dump(mode="json")
        session.add(save)
        session.commit()
        session.refresh(save)
        return _save_payload(save)
