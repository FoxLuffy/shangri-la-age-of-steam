from backend.models import WorldState, Location, NPC

# Example data
loc = Location(
    id="loc_001",
    name="Steam Factory",
    description="A bustling factory filled with the sound of hissing steam.",
    npcs=["npc_001", "npc_002"]
)

npc1 = NPC(
    id="npc_001",
    name="Arthur",
    traits=["Grumpy", "Experienced"],
    current_dialogue="Watch the pressure gauges!"
)

state = WorldState(
    current_location=loc,
    active_npcs=[npc1],
    global_event="The Great Steam Leak"
)

print(state.model_dump_json(indent=2))
