import logging
import random

from backend.models import WorldEvent, WorldState

logger = logging.getLogger(__name__)


class EventGenerator:
    """
    Generates procedural world events based on the current world state.
    """

    EVENT_TEMPLATES = {
        "steam_leak": {
            "descriptions": [
                "A high-pressure steam pipe has burst, creating a scalding mist in the corridor.",
                "Steam is whistling through a cracked valve, filling the room with heat.",
                "A massive steam release has obscured visibility and raised the ambient temperature.",
            ],
            "severity": 2,
            "impact_types": ["visibility", "temperature"],
        },
        "industrial_accident": {
            "descriptions": [
                "A heavy machinery component failed, causing a loud crash and localized debris.",
                "An industrial oversight has caused minor equipment damage and some minor repairs will be needed.",
                "A catastrophic equipment failure has left the area dangerous and smelling of scorched metal.",
            ],
            "severity": 4,
            "impact_types": ["hazard", "destruction"],
        },
        "factory_riot": {
            "descriptions": [
                "Workers have ceased production and are protesting the current working conditions.",
                "A heated argument between laborers has escalated into a organized protest outside the main hall.",
                "Tension in the factory has boiled over into a full-scale protest.",
            ],
            "severity": 3,
            "impact_types": ["labor_disruption", "social_unrest"],
        },
    }

    @staticmethod
    def generate_event(state: WorldState) -> WorldEvent:
        """
        Generates a procedural WorldEvent based on current state.
        """
        # In a full implementation, this would call an LLM or a complex heuristic.
        # For now, we use a weighted random selection.
        event_key = random.choice(list(EventGenerator.EVENT_TEMPLATES.keys()))
        template = EventGenerator.EVENT_TEMPLATES[event_key]

        description = random.choice(template["descriptions"])

        # Simulate faction impacts based on event type
        # (In a real system, these would be defined in a data file or derived from lore)
        faction_impacts = {}
        if event_key == "factory_riot":
            faction_impacts = {"Iron Syndicate": -0.3, "Alchemists Guild": 0.1}
        elif event_key == "industrial_accident":
            faction_impacts = {"Iron Syndicate": -0.2, "Alchemists Guild": -0.1}

        return WorldEvent(
            location_id=state.current_location_id or "1",
            event_type=event_key,
            event_text=description,
            severity=template["severity"],
            faction_impacts=faction_impacts,
            is_active=1,
        )
