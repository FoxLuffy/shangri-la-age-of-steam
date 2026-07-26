"""CR11: the narrative engine must reliably produce & apply [StateUpdates].

Two guards:
1. The prompt template no longer contradicts itself (the old "ONLY return the JSON" rule
   made weak models drop one of the two required sections), and now mandates a
   [StateUpdates] block every turn with a few-shot example.
2. parse_vllm_response correctly extracts state_updates from a well-formed two-section
   response, and returns empty updates (not a crash) when [StateUpdates] is absent.
"""

import os

from backend.engine import parse_vllm_response

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "narrative_prompt.j2")


def _template_text():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()


def test_prompt_drops_the_contradictory_json_only_rule():
    text = _template_text()
    assert "ONLY return the JSON. No other text." not in text


def test_prompt_mandates_stateupdates_every_turn_with_example():
    text = _template_text()
    # Mandate + empty-case guidance + a worked example.
    assert "MANDATORY" in text
    assert "{}" in text  # "use {} if nothing changed"
    assert "brass_coins_change" in text
    assert "[StateUpdates]" in text and "[Narration]" in text
    assert "EXAMPLE" in text.upper()


def test_parser_extracts_state_updates_from_two_section_response():
    raw = (
        "[Narration]\n"
        "You slide three coins across the counter and take the gears.\n\n"
        "[StateUpdates]\n"
        '{ "empire_updates": { "brass_coins_change": -30 },'
        '  "inventory_updates": [ { "action": "add", "item_name": "Calibration Gears", "quantity": 1 } ] }'
    )
    narration, state_updates, events = parse_vllm_response({"text": raw})
    assert "coins across the counter" in narration
    assert "[Narration]" not in narration  # header stripped
    assert state_updates["empire_updates"]["brass_coins_change"] == -30
    assert state_updates["inventory_updates"][0]["item_name"] == "Calibration Gears"


def test_parser_handles_narration_only_without_crashing():
    raw = "[Narration]\nYou look around the quiet tavern.\n"
    narration, state_updates, events = parse_vllm_response({"text": raw})
    assert "quiet tavern" in narration
    assert state_updates == {}
    assert events == []
