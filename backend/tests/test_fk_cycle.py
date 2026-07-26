import warnings

from backend.database import Character, Guild, SQLModel, engine
from sqlmodel import Session


def test_no_circular_fk_drop_warning():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        SQLModel.metadata.create_all(engine)
        SQLModel.metadata.drop_all(engine)

    messages = [str(w.message) for w in caught]
    offending = [m for m in messages if "unresolvable foreign key" in m]
    assert offending == [], f"circular-FK DROP warning still present: {offending}"


def test_guild_leader_relationship_still_works():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        leader = Character(name="Chief")
        session.add(leader)
        session.commit()
        session.refresh(leader)

        guild = Guild(name="The Cogturners", leader_id=leader.id)
        session.add(guild)
        session.commit()
        session.refresh(guild)

        leader.guild_id = guild.id
        session.add(leader)
        session.commit()

        assert guild.leader_id == leader.id
        assert session.get(Character, leader.id).guild_id == guild.id
