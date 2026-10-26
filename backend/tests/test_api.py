import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_data_status():
    response = client.get("/api/v1/data/status")
    assert response.status_code == 200
    assert "total_raw_records" in response.json()

def test_analytics_overview():
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    data = response.json()
    assert "revenue" in data
    assert "active_predictions" in data

def test_analytics_forecast():
    response = client.get("/api/v1/analytics/forecast")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "forecast" in data[0]

def test_auth_registration_and_login():
    import uuid
    random_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "SuperSecurePassword123!"

    # 1. Register
    reg_response = client.post("/api/v1/auth/register", json={
        "email": random_email,
        "password": password,
        "role": "ANALYST",
        "is_active": True
    })
    assert reg_response.status_code in [200, 201]
    assert reg_response.json()["email"] == random_email

    # 2. Login
    login_response = client.post("/api/v1/auth/login", data={
        "username": random_email,
        "password": password
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

def test_analytics_anomalies():
    response = client.get("/api/v1/analytics/anomalies?sku=SKU-1001")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_copilot_query():
    response = client.post("/api/v1/analytics/copilot?query=Why+did+sales+drop?")
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "recommendation" in data

def test_csv_upload_endpoint():
    import io
    csv_content = b"date,sku,units_sold\n2026-03-01,SKU-9999,10\n2026-03-02,SKU-9999,15\n"
    response = client.post(
        "/api/v1/data/upload",
        files={"file": ("test_upload.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["records_processed"] == 2

def test_ml_train_endpoint():
    response = client.post("/api/v1/ml/train?sku=SKU-1001&forecast_days=7")
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert "best_model_selected" in data
        assert len(data["future_predictions"]) == 7
    else:
        assert response.status_code == 400
        assert "Insufficient data" in response.json()["detail"]



