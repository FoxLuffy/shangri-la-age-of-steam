"""C1: one active bounty at a time (accepting a new one replaces the current), the active
bounty is returned by the bounties endpoint and surfaced into the narrative prompt as an
ACTIVE BOUNTY hint block."""

import asyncio

from backend.database import Bounty, Character, SQLModel, WorldState, engine
from backend.models import PlayerAction
from backend.prompt_utils import build_narrative_prompt
from backend.repository import StateRepository
from backend.routers.gameplay import BountyAcceptRequest, accept_bounty, get_bounties
from sqlmodel import Session


def _seed():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Hunter", location_id="1", brass_coins=0)
        session.add(char)
        session.add(WorldState(current_location_id="1"))
        b1 = Bounty(title="Bounty: Rogue Automata", description="d1", target_npc_type="Automata", reward_coins=100)
        b2 = Bounty(title="Bounty: Notorious Thug", description="d2", target_npc_type="Thug", reward_coins=80)
        session.add(b1)
        session.add(b2)
        session.commit()
        return char.id, b1.id, b2.id


def test_accepting_new_bounty_replaces_the_active_one():
    cid, b1, b2 = _seed()
    asyncio.run(accept_bounty(cid, BountyAcceptRequest(bounty_id=b1)))
    asyncio.run(accept_bounty(cid, BountyAcceptRequest(bounty_id=b2)))

    with Session(engine) as session:
        char = session.get(Character, cid)
        assert char.active_bounties == [b2]  # exactly one active, the newest
        assert session.get(Bounty, b1).status == "available"  # prior active returned to pool
        assert session.get(Bounty, b2).status == "active"


def test_get_bounties_returns_active_objects():
    cid, b1, _ = _seed()
    asyncio.run(accept_bounty(cid, BountyAcceptRequest(bounty_id=b1)))

    data = asyncio.run(get_bounties(cid))
    assert [b.id for b in data["active"]] == [b1]
    assert b1 not in [b.id for b in data["available"]]


def test_active_bounty_surfaces_in_state_and_prompt():
    cid, b1, _ = _seed()
    asyncio.run(accept_bounty(cid, BountyAcceptRequest(bounty_id=b1)))

    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
        assert state.active_bounty and state.active_bounty["title"] == "Bounty: Rogue Automata"
        prompt = build_narrative_prompt(state, PlayerAction(action_text="look around"))
        assert "ACTIVE BOUNTY" in prompt
        assert "Automata" in prompt


def test_no_active_bounty_no_prompt_block():
    cid, _, _ = _seed()
    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
        assert state.active_bounty is None
        prompt = build_narrative_prompt(state, PlayerAction(action_text="look around"))
        assert "ACTIVE BOUNTY" not in prompt
