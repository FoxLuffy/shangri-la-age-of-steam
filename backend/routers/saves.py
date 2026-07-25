from datetime import datetime
from typing import Optional

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


class SaveCreateRequest(BaseModel):
    character_id: int
    name: Optional[str] = None


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


@router.post("/saves")
async def create_save(req: SaveCreateRequest):
    with get_session() as session:
        character = session.get(Character, req.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        save = SaveState(
            character_id=character.id,
            name=req.name or f"{character.name} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.utcnow().isoformat() + "Z",
            snapshot=_build_snapshot(session, character),
        )
        session.add(save)
        session.commit()
        session.refresh(save)
        return {
            "id": save.id,
            "character_id": save.character_id,
            "name": save.name,
            "created_at": save.created_at,
        }


@router.get("/saves")
async def list_saves(character_id: int):
    with get_session() as session:
        saves = session.exec(
            select(SaveState)
            .where(SaveState.character_id == character_id)
            .order_by(SaveState.id.desc())
        ).all()
        return [
            {"id": s.id, "character_id": s.character_id, "name": s.name, "created_at": s.created_at}
            for s in saves
        ]


@router.get("/saves/{save_id}/load")
async def load_save(save_id: int):
    with get_session() as session:
        save = session.get(SaveState, save_id)
        if not save:
            raise HTTPException(status_code=404, detail="Save not found")

        snapshot = save.snapshot or {}
        character = session.get(Character, save.character_id)
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
            "save_id": save_id,
            "character_id": character.id,
            "name": save.name,
        }


@router.delete("/saves/{save_id}")
async def delete_save(save_id: int):
    with get_session() as session:
        save = session.get(SaveState, save_id)
        if not save:
            raise HTTPException(status_code=404, detail="Save not found")
        session.delete(save)
        session.commit()
        return {"status": "deleted", "save_id": save_id}
