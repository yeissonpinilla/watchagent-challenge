import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Event, LiveReading
from app.main import app, get_db


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)

    db = testing_session()
    db.add(
        LiveReading(
            city="Ottawa",
            timestamp="2026-05-30T12:00",
            temperature_2m=18.0,
            apparent_temperature=17.0,
            precipitation=0.0,
            wind_speed_10m=10.0,
            weather_code=0,
        )
    )
    db.add(
        LiveReading(
            city="Toronto",
            timestamp="2026-05-30T11:00",
            temperature_2m=20.0,
            apparent_temperature=19.0,
            precipitation=0.5,
            wind_speed_10m=12.0,
            weather_code=61,
        )
    )
    db.add(
        Event(
            city="Ottawa",
            timestamp="2026-05-30T12:00",
            event_type="TEMP_ANOMALY",
            reason="outside 2 std dev of monthly baseline",
            value=18.0,
        )
    )
    db.commit()
    db.close()

    yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health_returns_counts(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "readings_stored": 2,
        "events_stored": 1,
    }


def test_readings_returns_all_fields_most_recent_first(client):
    response = client.get("/readings")

    assert response.status_code == 200
    body = response.json()
    assert "readings" in body
    assert len(body["readings"]) == 2
    assert body["readings"][0]["city"] == "Ottawa"
    assert body["readings"][0]["timestamp"] == "2026-05-30T12:00"
    assert set(body["readings"][0].keys()) == {
        "id",
        "city",
        "timestamp",
        "temperature_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
        "weather_code",
    }


def test_readings_filters_by_city(client):
    response = client.get("/readings", params={"city": "Toronto"})

    assert response.status_code == 200
    body = response.json()
    assert len(body["readings"]) == 1
    assert body["readings"][0]["city"] == "Toronto"


def test_readings_respects_limit(client):
    response = client.get("/readings", params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()["readings"]) == 1


def test_readings_rejects_invalid_limit(client):
    response = client.get("/readings", params={"limit": 0})

    assert response.status_code == 422


def test_events_returns_all_fields(client):
    response = client.get("/events")

    assert response.status_code == 200
    body = response.json()
    assert "events" in body
    assert len(body["events"]) == 1
    assert set(body["events"][0].keys()) == {
        "id",
        "city",
        "timestamp",
        "event_type",
        "reason",
        "value",
    }
    assert body["events"][0]["event_type"] == "TEMP_ANOMALY"


def test_events_filters_by_city(client):
    response = client.get("/events", params={"city": "Ottawa"})

    assert response.status_code == 200
    assert len(response.json()["events"]) == 1

    response = client.get("/events", params={"city": "Toronto"})
    assert response.status_code == 200
    assert response.json()["events"] == []
