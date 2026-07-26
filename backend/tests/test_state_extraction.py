"""Two-pass state extraction: a focused JSON-only call derives state changes when the
narration pass didn't emit any (CR11 in practice)."""

from backend.engine import NarrativeEngine
from backend.models import PlayerAction, WorldState


class _JsonClient:
    def __init__(self, payload):
        self._payload = payload

    def generate(self, **kwargs):
        return {"choices": [{"message": {"content": self._payload}}]}


class _BoomClient:
    def generate(self, **kwargs):
        raise RuntimeError("vllm down")


def _engine(client):
    return NarrativeEngine(vllm_client=client)


def test_extracts_inventory_and_coins_from_narration():
    eng = _engine(_JsonClient(
        '{"empire_updates":{"brass_coins_change":-30},'
        '"inventory_updates":[{"action":"add","item_name":"Crawlspace Key","quantity":1}]}'
    ))
    state = WorldState(brass_coins=100, inventory=[{"name": "Lockpick"}])
    action = PlayerAction(action_text="take the key", character_id=1)
    out = eng._extract_state(action, state, "You pocket the crawlspace key.")
    assert out["empire_updates"]["brass_coins_change"] == -30
    assert out["inventory_updates"][0]["item_name"] == "Crawlspace Key"


def test_extracts_main_quest_advance():
    eng = _engine(_JsonClient('{"main_quest_updates":{"advance_stage":true}}'))
    state = WorldState(main_quest={"current_objective": "Find the apprentice"})
    action = PlayerAction(action_text="find the apprentice", character_id=1)
    out = eng._extract_state(action, state, "You find the apprentice.")
    assert out["main_quest_updates"]["advance_stage"] is True


def test_returns_empty_on_client_failure():
    eng = _engine(_BoomClient())
    out = eng._extract_state(PlayerAction(action_text="look", character_id=1), WorldState(), "You look.")
    assert out == {}
