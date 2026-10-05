import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.entities import HealthWorker, Facility, Case
from backend.app.core.security import get_password_hash

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Seed a facility if not present
    if not db.query(Facility).filter(Facility.id == "TEST_FAC_01").first():
        db.add(Facility(
            id="TEST_FAC_01",
            name="Centre de Test",
            health_area="Aire Test",
            district="District Test",
            region="Region Test",
            latitude=5.0,
            longitude=-6.0
        ))
    # Seed test users
    if not db.query(HealthWorker).filter(HealthWorker.email == "test.admin@dermia.org").first():
        db.add(HealthWorker(
            id="TEST_ADMIN",
            email="test.admin@dermia.org",
            hashed_password=get_password_hash("password123"),
            full_name="Admin Test",
            role="admin",
            active=True
        ))
    db.commit()
    db.close()

def test_healthcheck():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_auth_login():
    res = client.post("/api/v1/auth/login", json={
        "email": "test.admin@dermia.org",
        "password": "password123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "admin"
    return data["access_token"]

def test_sync_cases_idempotent():
    # Login first
    login_res = client.post("/api/v1/auth/login", json={
        "email": "test.admin@dermia.org",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    case_uuid = str(uuid.uuid4())
    payload = {
        "cases": [
            {
                "uuid": case_uuid,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "age_group": "6-15",
                "sex": "M",
                "body_zone": "jambes",
                "model_version": "1.0.0",
                "model_prediction": [{"id": "buruli", "nom": "Ulcère de Buruli", "score": 8.0, "share": 0.85}],
                "confidence": 0.91,
                "indeterminate": False,
                "urgency": "prioritaire",
                "facility_id": "TEST_FAC_01"
            }
        ]
    }
    
    # First sync: should insert 1
    res1 = client.post("/api/v1/sync/cases", json=payload, headers=headers)
    assert res1.status_code == 200
    assert res1.json()["synced_count"] == 1
    assert res1.json()["duplicates_ignored"] == 0
    
    # Second sync of the exact same case: should ignore as duplicate (idempotent)
    res2 = client.post("/api/v1/sync/cases", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["synced_count"] == 0
    assert res2.json()["duplicates_ignored"] == 1

def test_list_and_filter_cases():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "test.admin@dermia.org",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/cases?urgency=prioritaire", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_surveillance_stats():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "test.admin@dermia.org",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/surveillance/stats", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_cases" in data
    assert "urgent_cases" in data

def test_dhis2_export():
    login_res = client.post("/api/v1/auth/login", json={
        "email": "test.admin@dermia.org",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/api/v1/export/dhis2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "dataSet" in data
    assert "dataValues" in data
    assert isinstance(data["dataValues"], list)
