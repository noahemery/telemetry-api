import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db

# Use an in-memory SQLite DB for tests
TEST_DATABASE_URL = "sqlite:///./test_telemetry.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
Base.metadata.create_all(bind=engine)
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# ── Session Tests ────────────────────────────────────────────────────────────

def test_create_session():
    res = client.post("/sessions/", json={
        "session_name": "run_01", "vehicle_id": "car_42",
        "driver": "Noah", "track": "Lexington Circuit"
    })
    assert res.status_code == 201
    assert res.json()["session_name"] == "run_01"


def test_duplicate_session_rejected():
    payload = {"session_name": "run_dup", "vehicle_id": "car_42", "driver": "Noah", "track": "Track A"}
    client.post("/sessions/", json=payload)
    res = client.post("/sessions/", json=payload)
    assert res.status_code == 409


def test_list_sessions():
    client.post("/sessions/", json={"session_name": "s1", "vehicle_id": "v1", "driver": "D", "track": "T"})
    res = client.get("/sessions/")
    assert res.status_code == 200
    assert len(res.json()) == 1


# ── Telemetry Tests ──────────────────────────────────────────────────────────

def _create_session(name="test_session"):
    res = client.post("/sessions/", json={
        "session_name": name, "vehicle_id": "car_01", "driver": "Noah", "track": "Track A"
    })
    return res.json()["id"]


VALID_RECORD = {
    "timestamp": 1.0, "speed_mph": 45.5, "engine_rpm": 6500.0,
    "throttle_pct": 80.0, "brake_pct": 0.0, "steering_angle": 5.0,
    "gear": 3, "coolant_temp_f": 195.0, "oil_pressure_psi": 55.0, "lap_number": 1
}


def test_ingest_telemetry_record():
    sid = _create_session()
    res = client.post(f"/sessions/{sid}/telemetry/", json=VALID_RECORD)
    assert res.status_code == 201
    assert res.json()["speed_mph"] == 45.5


def test_bulk_ingest():
    sid = _create_session()
    records = [{**VALID_RECORD, "timestamp": float(i)} for i in range(10)]
    res = client.post(f"/sessions/{sid}/telemetry/bulk", json=records)
    assert res.status_code == 201
    assert res.json()["inserted"] == 10


def test_invalid_throttle_brake():
    sid = _create_session()
    bad = {**VALID_RECORD, "throttle_pct": 50.0, "brake_pct": 50.0}
    res = client.post(f"/sessions/{sid}/telemetry/", json=bad)
    assert res.status_code == 422


def test_invalid_rpm():
    sid = _create_session()
    bad = {**VALID_RECORD, "engine_rpm": 99999.0}
    res = client.post(f"/sessions/{sid}/telemetry/", json=bad)
    assert res.status_code == 422


def test_session_metrics():
    sid = _create_session()
    records = [{**VALID_RECORD, "timestamp": float(i), "speed_mph": float(20 + i)} for i in range(5)]
    client.post(f"/sessions/{sid}/telemetry/bulk", json=records)
    res = client.get(f"/sessions/{sid}/telemetry/metrics")
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 5
    assert data["max_speed_mph"] == 24.0
