"""World simulation is turn-gated (report #10): the world only ticks as a consequence of a
chat turn. See backend.engine.run_world_turn, invoked from the /chat handler. The former
background loops (world_simulation_loop, simulate_global_market, simulate_faction_wars) were
removed along with the NPC-to-NPC 'overheard' interactions that injected phantom NPCs from
other locations.
"""
