from unittest.mock import MagicMock

import pytest
from backend.database import Character, Quest, QuestState, QuestStateEnum
from backend.database import engine as db_engine
from backend.engine import NarrativeEngine
from backend.models import PlayerAction
from sqlmodel import Session, select


@pytest.fixture(autouse=True)
def setup_test_db():
    from backend.database import create_db_and_tables
    create_db_and_tables()
    with Session(db_engine) as session:
        # Create a test character if one doesn't exist
        char = session.get(Character, 1)
        if not char:
            char = Character(id=1, name="Test Player", user_id=1, location_id="1")
            session.add(char)
            session.commit()
    yield

def test_quest_generation():
    with Session(db_engine) as session:
        mock_vllm_client = MagicMock()
        mock_vllm_client.generate_stream.return_value = [
            {
                "text": "[Narration] The foreman gives you a task.\n[StateUpdates]\n```json\n{\n  \"quest_updates\": [\n    {\n      \"action\": \"add\",\n      \"quest_title\": \"Copper Shortage\",\n      \"description\": \"Bring 5 Copper Ore to the foreman.\"\n    }\n  ]\n}\n```"
            }
        ]

        # Use NarrativeEngine with the mock client and database session
        action = PlayerAction(action_text="I ask the foreman for work", current_location_id="1", character_id=1)
        engine = NarrativeEngine(vllm_client=mock_vllm_client)

        result_chunk = None
        for chunk in engine.process_action(action, session):
            if isinstance(chunk, dict) and "state_updates" in chunk:
                result_chunk = chunk

        assert result_chunk is not None
        assert "quest_updates" in result_chunk["state_updates"]

        # Verify the quest was created in the database
        quest = session.exec(select(Quest).where(Quest.title == "Copper Shortage")).first()
        assert quest is not None
        assert quest.description == "Bring 5 Copper Ore to the foreman."

        q_state = session.exec(select(QuestState).where(QuestState.character_id == 1, QuestState.quest_id == quest.id)).first()
        assert q_state is not None
        assert q_state.state == QuestStateEnum.active
