import asyncio
import json

from backend.database import (
    Augmentation,
    AutomataCompanion,
    Character,
    Inventory,
    Item,
    Location,
    Recipe,
    RecipeRequirement,
    ResourceMarket,
    WorldState,
    get_session,
)
from backend.schemas import MarketTradeRequest
from backend.websocket import manager
from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

router = APIRouter()

@router.get("/inventory")
async def get_inventory(character_id: int):
    """Retrieve the inventory for a given character."""
    with get_session() as session:
        inventory_items = session.exec(select(Inventory).where(Inventory.character_id == character_id)).all()
        return inventory_items

@router.post("/craft")
async def craft_item(character_id: int, recipe_id: int):
    """
    Crafts an item based on a recipe.
    Atomically deducts required materials from character's inventory and adds the new item.
    """
    with get_session() as session:
        recipe = session.exec(select(Recipe).where(Recipe.id == recipe_id)).first()
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

        # Faction check
        if recipe.required_faction_id:
            ws = session.exec(select(WorldState)).first()
            if ws:
                loc = session.exec(select(Location).where(Location.id == ws.current_location_id)).first()
                if not loc or loc.faction_id != recipe.required_faction_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"This recipe requires the '{recipe.required_faction_id}' faction facilities.",
                    )

        requirements = session.exec(select(RecipeRequirement).where(RecipeRequirement.recipe_id == recipe_id)).all()

        if not requirements:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recipe has no requirements")

        # Check if character has enough materials
        for req in requirements:
            inv_item = session.exec(
                select(Inventory).where(Inventory.character_id == character_id).where(Inventory.item_id == req.item_id)
            ).first()

            if not inv_item or inv_item.quantity < req.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough materials for item_id {req.item_id}. Needed: {req.quantity}, Have: {inv_item.quantity if inv_item else 0}",
                )

        try:
            # Deduct materials
            for req in requirements:
                inv_item = session.exec(
                    select(Inventory)
                    .where(Inventory.character_id == character_id)
                    .where(Inventory.item_id == req.item_id)
                ).first()
                inv_item.quantity -= req.quantity
                if inv_item.quantity == 0:
                    session.delete(inv_item)
                else:
                    session.add(inv_item)

            # Add resulting item to inventory
            result_inv_item = session.exec(
                select(Inventory)
                .where(Inventory.character_id == character_id)
                .where(Inventory.item_id == recipe.result_item_id)
            ).first()

            if result_inv_item:
                result_inv_item.quantity += recipe.result_quantity
                session.add(result_inv_item)
            else:
                new_inv_item = Inventory(
                    character_id=character_id, item_id=recipe.result_item_id, quantity=recipe.result_quantity
                )
                session.add(new_inv_item)

            session.commit()
        except Exception:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Crafting transaction failed")

        return {
            "message": "Crafting successful",
            "result_item_id": recipe.result_item_id,
            "quantity_added": recipe.result_quantity,
        }

@router.get("/market")
async def get_market():
    with get_session() as session:
        markets = session.exec(select(ResourceMarket)).all()
        return [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]

@router.post("/market/trade")
async def trade_market(character_id: int, req: MarketTradeRequest):
    with get_session() as session:
        char = session.exec(select(Character).where(Character.id == character_id)).first()
        market = session.exec(select(ResourceMarket).where(ResourceMarket.resource_name == req.resource_name)).first()
        if not char or not market:
            raise HTTPException(status_code=404, detail="Character or Market not found")

        item = session.exec(select(Item).where(Item.name == req.resource_name)).first()
        if not item:
            item = Item(name=req.resource_name, description=f"Raw {req.resource_name}", category="Crafting_Materials")
            session.add(item)
            session.commit()
            session.refresh(item)

        inv = session.exec(
            select(Inventory).where(Inventory.character_id == char.id, Inventory.item_id == item.id)
        ).first()

        total_price = int(market.current_price * req.quantity)

        if req.action == "buy":
            if char.brass_coins < total_price:
                raise HTTPException(status_code=400, detail="Not enough brass coins")
            char.brass_coins -= total_price
            if not inv:
                inv = Inventory(character_id=char.id, item_id=item.id, quantity=req.quantity)
                session.add(inv)
            else:
                inv.quantity += req.quantity
            market.current_price *= 1.0 + (0.01 * req.quantity)
        elif req.action == "sell":
            if not inv or inv.quantity < req.quantity:
                raise HTTPException(status_code=400, detail="Not enough resources")
            inv.quantity -= req.quantity
            char.brass_coins += total_price
            market.current_price *= 1.0 - (0.01 * req.quantity)
            market.current_price = max(1.0, market.current_price)

        session.add(char)
        session.add(market)
        session.commit()

        markets = session.exec(select(ResourceMarket)).all()
        markets_data = [{"name": m.resource_name, "price": round(m.current_price, 2)} for m in markets]

        asyncio.create_task(manager.broadcast(json.dumps({"type": "market_sync", "market": markets_data})))

        return {"status": "success", "brass_coins": char.brass_coins, "new_price": round(market.current_price, 2)}

@router.get("/automata")
async def get_automata():
    """Retrieve all automata companions."""
    with get_session() as session:
        automata = session.exec(select(AutomataCompanion)).all()
        return automata

@router.get("/augmentations")
async def get_augmentations(character_id: int = 1):
    """Retrieve augmentations installed on a character."""
    with get_session() as session:
        augs = session.exec(select(Augmentation).where(Augmentation.character_id == character_id)).all()
        return augs
