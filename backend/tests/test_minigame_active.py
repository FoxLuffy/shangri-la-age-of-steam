"""CR3: "Start minigame" does nothing.

The Start Minigame button opens the panel only when /state reports `active_minigame`.
`get_latest_state` (and `trigger_minigame`'s dedup) filtered with `not Minigame.solved`
— a Python bool evaluated at query-build time (always False), so the WHERE became
`... AND False` and never matched. active_minigame was therefore always None and the panel
never opened.
"""

from backend.database import Character, Minigame, SQLModel, WorldState, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _seed_char():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        char = Character(name="Hacker", location_id="1")
        session.add(char)
        session.add(WorldState(current_location_id="1"))
        session.commit()
        session.refresh(char)
        return char.id


def test_unsolved_minigame_surfaces_as_active():
    cid = _seed_char()
    with Session(engine) as session:
        session.add(Minigame(character_id=cid, type="hack", state={"x": 1}, solved=False))
        session.commit()

    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    assert state.active_minigame is not None
    assert state.active_minigame["type"] == "hack"


def test_solved_minigame_is_not_active():
    cid = _seed_char()
    with Session(engine) as session:
        session.add(Minigame(character_id=cid, type="hack", state={}, solved=True))
        session.commit()

    with Session(engine) as session:
        state = StateRepository(session).get_latest_state(cid)
    assert state.active_minigame is None


def test_trigger_minigame_dedups_on_existing_unsolved():
    cid = _seed_char()
    with Session(engine) as session:
        repo = StateRepository(session)
        repo.trigger_minigame("hack", cid)
        repo.trigger_minigame("hack", cid)  # should no-op: one already unsolved
        count = len(session.exec(select(Minigame).where(Minigame.character_id == cid)).all())
    assert count == 1
