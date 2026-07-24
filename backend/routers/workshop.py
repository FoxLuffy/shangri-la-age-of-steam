import json
import os
import shutil

from backend.database import NPC, Faction, Item, Location, get_session
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import select

router = APIRouter()

@router.get("/export")
async def export_save():
    db_path = os.getenv("DATABASE_PATH", "saos.db")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database file not found.")
    return FileResponse(path=db_path, filename="saos_save.db", media_type="application/octet-stream")

@router.post("/import")
async def import_save(file: UploadFile = File(...)):
    db_path = os.getenv("DATABASE_PATH", "saos.db")
    try:
        with open(db_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Optionally, verify the database or trigger any post-import hooks here.
        # It's important the client calls /state immediately after to refresh data.
        return {"status": "success", "message": "Save state imported successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import save: {str(e)}")

@router.post("/modding/upload")
async def upload_mod(file: UploadFile = File(...)):
    """Upload a custom JSON file defining new Locations, NPCs, Items, and Factions."""
    try:
        content = await file.read()
        data = json.loads(content)

        with get_session() as session:
            if "factions" in data:
                for f_data in data["factions"]:
                    faction = session.exec(select(Faction).where(Faction.id == f_data["id"])).first()
                    if faction:
                        for k, v in f_data.items():
                            setattr(faction, k, v)
                    else:
                        faction = Faction(**f_data)
                        session.add(faction)

            if "locations" in data:
                for l_data in data["locations"]:
                    loc = session.exec(select(Location).where(Location.id == l_data["id"])).first()
                    if loc:
                        for k, v in l_data.items():
                            setattr(loc, k, v)
                    else:
                        loc = Location(**l_data)
                        session.add(loc)

            if "npcs" in data:
                for n_data in data["npcs"]:
                    npc = session.exec(select(NPC).where(NPC.id == n_data["id"])).first()
                    if npc:
                        for k, v in n_data.items():
                            setattr(npc, k, v)
                    else:
                        npc = NPC(**n_data)
                        session.add(npc)

            if "items" in data:
                for i_data in data["items"]:
                    item = session.exec(select(Item).where(Item.name == i_data["name"])).first()
                    if item:
                        for k, v in i_data.items():
                            setattr(item, k, v)
                    else:
                        item = Item(**i_data)
                        session.add(item)

            session.commit()

        return {"status": "success", "message": "Mod data uploaded and integrated successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process mod data: {str(e)}")

@router.get("/workshop/mods")
async def list_workshop_mods():
    """List available mods from the mock registry."""
    # Note: Using backend directory to find workshop_mods
    registry_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workshop_mods", "registry.json")
    if not os.path.exists(registry_path):
        return []
    with open(registry_path, "r") as f:
        return json.load(f)

@router.post("/workshop/mods/{mod_id}/install")
async def install_workshop_mod(mod_id: str):
    """Download and install a mod from the workshop."""
    mod_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workshop_mods", f"{mod_id}.json")
    if not os.path.exists(mod_path):
        raise HTTPException(status_code=404, detail="Mod not found")

    try:
        with open(mod_path, "r") as f:
            data = json.load(f)

        with get_session() as session:
            if "factions" in data:
                for f_data in data["factions"]:
                    faction = session.exec(select(Faction).where(Faction.id == f_data["id"])).first()
                    if faction:
                        for k, v in f_data.items():
                            setattr(faction, k, v)
                    else:
                        faction = Faction(**f_data)
                        session.add(faction)

            if "locations" in data:
                for l_data in data["locations"]:
                    loc = session.exec(select(Location).where(Location.id == l_data["id"])).first()
                    if loc:
                        for k, v in l_data.items():
                            setattr(loc, k, v)
                    else:
                        loc = Location(**l_data)
                        session.add(loc)

            if "npcs" in data:
                for n_data in data["npcs"]:
                    npc = session.exec(select(NPC).where(NPC.id == n_data["id"])).first()
                    if npc:
                        for k, v in n_data.items():
                            setattr(npc, k, v)
                    else:
                        npc = NPC(**n_data)
                        session.add(npc)

            if "items" in data:
                for i_data in data["items"]:
                    item = session.exec(select(Item).where(Item.name == i_data["name"])).first()
                    if item:
                        for k, v in i_data.items():
                            setattr(item, k, v)
                    else:
                        item = Item(**i_data)
                        session.add(item)

            session.commit()

        return {"status": "success", "message": f"Mod {mod_id} installed successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to install mod {mod_id}: {str(e)}")
