"""CR7: don't accumulate duplicate locations when the model invents a new id for a
place that already exists."""

from backend.database import Location, SQLModel, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _count():
    with Session(engine) as session:
        return len(session.exec(select(Location)).all())


def test_update_location_dedups_by_name():
    _fresh()
    with Session(engine) as session:
        session.add(Location(id="2", name="Clockwork Plaza", description="orig"))
        session.commit()
        repo = StateRepository(session)
        # Model invents a fresh id for the same-named place.
        repo.update_location("clockwork_plaza_01", {"name": "Clockwork Plaza", "description": "updated"})
    assert _count() == 1
    with Session(engine) as session:
        loc = session.get(Location, "2")
        assert loc.description == "updated"  # existing row updated, no duplicate


def test_apply_new_entities_skips_duplicate_location_name():
    _fresh()
    with Session(engine) as session:
        session.add(Location(id="2", name="Clockwork Plaza", description=""))
        session.commit()
        repo = StateRepository(session)
        repo.apply_new_entities(
            [{"type": "Location", "id": "cp_new", "name": "Clockwork Plaza", "description": "dupe"}], "2"
        )
    assert _count() == 1


def test_genuinely_new_location_is_created():
    _fresh()
    with Session(engine) as session:
        session.add(Location(id="2", name="Clockwork Plaza", description=""))
        session.commit()
        repo = StateRepository(session)
        repo.update_location("sewers_01", {"name": "The Sunken Sewers", "description": "new"})
    assert _count() == 2
