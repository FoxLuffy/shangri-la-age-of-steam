import random
from datetime import datetime
from typing import List, Optional

from backend.database import (
    Character,
    CraftingProficiency,
    KnownRecipe,
    Recipe,
    RecipeRequirement,
    get_session,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

router = APIRouter(prefix="/crafting")

# Probability that an experimentation attempt with the right materials yields a discovery.
DISCOVERY_CHANCE = 0.5

# Crafting specialization (C3.2).
BRANCHES = ["metallurgy", "alchemy", "clockwork"]
XP_PER_LEVEL = 3
MAX_LEVEL = 10
SUCCESS_BASE = 0.5
SUCCESS_PER_LEVEL = 0.1


def level_for_xp(xp: int) -> int:
    return min(MAX_LEVEL, xp // XP_PER_LEVEL)


def craft_success_chance(level: int, tier: int) -> float:
    chance = SUCCESS_BASE + SUCCESS_PER_LEVEL * (level - tier)
    return max(0.05, min(0.98, chance))


def roll_success(chance: float) -> bool:
    return random.random() < chance


def get_or_create_proficiency(session, character_id: int, branch: str) -> CraftingProficiency:
    prof = session.exec(
        select(CraftingProficiency).where(
            CraftingProficiency.character_id == character_id,
            CraftingProficiency.branch == branch,
        )
    ).first()
    if prof is None:
        prof = CraftingProficiency(character_id=character_id, branch=branch, xp=0)
        session.add(prof)
        session.commit()
        session.refresh(prof)
    return prof


def add_craft_xp(session, character_id: int, branch: str) -> None:
    prof = get_or_create_proficiency(session, character_id, branch)
    prof.xp += 1
    session.add(prof)


class DiscoverRequest(BaseModel):
    character_id: int
    recipe_id: int
    method: str = "discovery"


class ExperimentRequest(BaseModel):
    character_id: int
    item_ids: List[int] = []


def _grant(session, character_id: int, recipe_id: int, method: str) -> Optional[KnownRecipe]:
    """Create a KnownRecipe row if absent. Returns the new row, or None if already known."""
    existing = session.exec(
        select(KnownRecipe).where(
            KnownRecipe.character_id == character_id, KnownRecipe.recipe_id == recipe_id
        )
    ).first()
    if existing:
        return None
    known = KnownRecipe(
        character_id=character_id,
        recipe_id=recipe_id,
        method=method,
        discovered_at=datetime.utcnow().isoformat() + "Z",
    )
    session.add(known)
    return known


@router.get("/proficiency")
async def list_proficiency(character_id: int):
    with get_session() as session:
        result = []
        for branch in BRANCHES:
            prof = get_or_create_proficiency(session, character_id, branch)
            result.append({"branch": branch, "level": level_for_xp(prof.xp), "xp": prof.xp})
        return result


@router.get("/known")
async def list_known(character_id: int):
    with get_session() as session:
        rows = session.exec(
            select(KnownRecipe).where(KnownRecipe.character_id == character_id)
        ).all()
        result = []
        for row in rows:
            recipe = session.get(Recipe, row.recipe_id)
            result.append(
                {
                    "recipe_id": row.recipe_id,
                    "name": recipe.name if recipe else None,
                    "method": row.method,
                    "discovered_at": row.discovered_at,
                }
            )
        return result


@router.post("/discover")
async def discover(req: DiscoverRequest):
    with get_session() as session:
        if not session.get(Character, req.character_id):
            raise HTTPException(status_code=404, detail="Character not found")
        if not session.get(Recipe, req.recipe_id):
            raise HTTPException(status_code=404, detail="Recipe not found")

        granted = _grant(session, req.character_id, req.recipe_id, req.method)
        session.commit()
        if granted is None:
            return {"status": "already_known", "recipe_id": req.recipe_id}
        return {"status": "discovered", "recipe_id": req.recipe_id, "method": req.method}


@router.post("/experiment")
async def experiment(req: ExperimentRequest):
    with get_session() as session:
        if not session.get(Character, req.character_id):
            raise HTTPException(status_code=404, detail="Character not found")

        available = set(req.item_ids)
        known_ids = {
            k.recipe_id
            for k in session.exec(
                select(KnownRecipe).where(KnownRecipe.character_id == req.character_id)
            ).all()
        }

        # Candidate = an unknown recipe whose every requirement is covered by the materials.
        candidates = []
        for recipe in session.exec(select(Recipe)).all():
            if recipe.id in known_ids:
                continue
            reqs = session.exec(
                select(RecipeRequirement).where(RecipeRequirement.recipe_id == recipe.id)
            ).all()
            if reqs and all(r.item_id in available for r in reqs):
                candidates.append(recipe)

        if not candidates or random.random() >= DISCOVERY_CHANCE:
            return {"discovered": None}

        recipe = candidates[0]
        _grant(session, req.character_id, recipe.id, "experimentation")
        session.commit()
        return {"discovered": {"recipe_id": recipe.id, "name": recipe.name, "method": "experimentation"}}
