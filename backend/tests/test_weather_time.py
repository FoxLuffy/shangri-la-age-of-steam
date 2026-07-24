import pytest
from backend.database import WorldState as DBWorldState
from backend.engine import simulate_weather_time
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_simulate_weather_time(session: Session):
    state = DBWorldState(current_location_id="1", world_time=7, time_period="Dawn", weather="Clear")
    session.add(state)
    session.commit()

    simulate_weather_time(session)

    session.refresh(state)
    assert state.world_time == 8
    assert state.time_period == "Day"
    assert state.weather in ["Clear", "Fog", "Rain", "Thunderstorm"]
