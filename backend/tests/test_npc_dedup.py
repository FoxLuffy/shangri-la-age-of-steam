"""create_or_update_npc dedups by name so a model-invented id doesn't spawn a duplicate
NPC (reported: the same NPC appearing twice)."""

from backend.database import NPC as DBNPC
from backend.database import SQLModel, engine
from backend.repository import StateRepository
from sqlmodel import Session, select


def test_create_or_update_npc_dedups_by_name():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(DBNPC(id="silas", name="Silas the Smuggler", location_id="5"))
        session.commit()
        repo = StateRepository(session)
        # Model emits a fresh id but the same name.
        npc = repo.create_or_update_npc(
            {"id": "silas_smuggler", "name": "Silas the Smuggler", "traits": ["cynical"]}, "5"
        )
        assert npc.id == "silas"  # reused the existing row
        rows = session.exec(select(DBNPC).where(DBNPC.name == "Silas the Smuggler")).all()
        assert len(rows) == 1
