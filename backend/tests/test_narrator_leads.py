"""CR8: the narrator prompt should instruct the model to lead, not just describe."""

import os

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "narrative_prompt.j2")


def test_prompt_instructs_the_narrator_to_lead():
    with open(TEMPLATE, encoding="utf-8") as f:
        text = f.read()
    assert "LEAD THE STORY" in text
    lowered = text.lower()
    assert "hook" in lowered
    assert "momentum" in lowered
    # Explicitly discourages passive, dead-end description.
    assert "don't just describe" in lowered
