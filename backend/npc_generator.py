import random
from sqlmodel import Session
from backend.database import NPC
import uuid

NAMES = {
    "industrial": ["Barnaby", "Silas", "Cora", "Thaddeus", "Bram", "Agnes"],
    "alchemical": ["Aurelia", "Lucius", "Septimus", "Valeria", "Ignatius", "Elara"],
    "high_society": ["Percival", "Victoria", "Archibald", "Beatrice", "Cornelius", "Eleanor"]
}

LAST_NAMES = ["Cogsworth", "Ironclad", "Brass", "Vapor", "Ash", "Tinker", "Pendulum", "Gear", "Copper", "Steel"]

ROLES = {
    "industrial": ["Steam-Pipe Worker", "Coal Shoveler", "Gear Machinist", "Foreman", "Pneumatic Engineer"],
    "alchemical": ["Aether Distiller", "Potion Brewer", "Transmutation Scholar", "Toxin Inspector", "Flask Blower"],
    "high_society": ["Airship Baron", "Clockwork Collector", "Syndicate Aristocrat", "Tea Importer", "Diplomat"]
}

APPEARANCES = {
    "industrial": ["covered in soot and grease", "wearing heavy leather overalls and welding goggles", "missing a finger, replaced with a brass digit", "smelling of sulfur and sweat"],
    "alchemical": ["wearing a stained apron smelling of ozone", "sporting thick magnifying spectacles", "with fingertips stained purple from reagents", "carrying a bandolier of glowing vials"],
    "high_society": ["wearing a pristine silk cravat", "holding a silver-tipped walking cane", "wearing an elaborate monocle with multiple lenses", "dressed in a velvet coat with brass buttons"]
}

def generate_procedural_npc(session: Session, location_flavor: str = "industrial") -> NPC:
    if location_flavor not in NAMES:
        location_flavor = "industrial"
        
    first_name = random.choice(NAMES[location_flavor])
    last_name = random.choice(LAST_NAMES)
    role = random.choice(ROLES[location_flavor])
    appearance = random.choice(APPEARANCES[location_flavor])
    
    full_name = f"{first_name} {last_name}"
    traits = [role, appearance, "Procedural"]
    
    npc_id = f"proc_{uuid.uuid4().hex[:8]}"
    
    npc = NPC(
        id=npc_id,
        name=full_name,
        traits=traits,
        disposition=0.0
    )
    
    session.add(npc)
    session.commit()
    session.refresh(npc)
    
    return npc
