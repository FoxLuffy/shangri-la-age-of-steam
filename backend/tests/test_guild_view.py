"""C3: a character can view their guild (with members + leader flag), so the panel can show
the guild immediately after creation instead of the same create form (report #9)."""

import asyncio

from backend.database import Character, SQLModel, engine
from backend.routers.gameplay import GuildCreateRequest, create_guild, get_my_guild
from sqlmodel import Session


def _fresh():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def test_unaffiliated_character_has_no_guild():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Loner", location_id="1")
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id

    data = asyncio.run(get_my_guild(cid))
    assert data["guild"] is None
    assert data["is_leader"] is False


def test_guild_visible_immediately_after_creation():
    _fresh()
    with Session(engine) as session:
        char = Character(name="Founder", location_id="1")
        session.add(char)
        session.commit()
        session.refresh(char)
        cid = char.id

    asyncio.run(create_guild(cid, GuildCreateRequest(name="Iron Circle", description="A steely brotherhood")))

    data = asyncio.run(get_my_guild(cid))
    assert data["guild"] and data["guild"]["name"] == "Iron Circle"
    assert data["is_leader"] is True
    assert [m["name"] for m in data["members"]] == ["Founder"]
    assert data["members"][0]["is_leader"] is True


def test_members_reflect_invited_characters():
    _fresh()
    with Session(engine) as session:
        leader = Character(name="Founder", location_id="1")
        recruit = Character(name="Recruit", location_id="1")
        session.add(leader)
        session.add(recruit)
        session.commit()
        session.refresh(leader)
        session.refresh(recruit)
        lid, rid = leader.id, recruit.id

    asyncio.run(create_guild(lid, GuildCreateRequest(name="Cogwrights", description="d")))
    with Session(engine) as session:
        gid = session.get(Character, lid).guild_id
        recruit = session.get(Character, rid)
        recruit.guild_id = gid  # simulate an accepted invite
        session.add(recruit)
        session.commit()

    data = asyncio.run(get_my_guild(rid))
    assert data["guild"]["name"] == "Cogwrights"
    assert data["is_leader"] is False  # recruit is not the leader
    assert {m["name"] for m in data["members"]} == {"Founder", "Recruit"}
