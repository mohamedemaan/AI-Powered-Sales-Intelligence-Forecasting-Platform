import pytest
from fastapi.testclient import TestClient
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd

from app.main import app
from app.services.simulation import simulate_scenario
from app.services.gemini_service import get_sales_business_context

client = TestClient(app)

def test_simulation_rejects_insufficient_data():
    """Verify simulation never synthesizes 120 units when data has < 5 observations."""
    empty_df = pd.DataFrame()
    res_empty = simulate_scenario(empty_df, price_change=0, discount=10, demand_multiplier=1.0)
    assert "error" in res_empty
    assert res_empty.get("has_data") is False
    assert "baseline_predictions" not in res_empty

    tiny_df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02"],
        "units_sold": [5, 10],
        "price": [20.0, 20.0]
    })
    res_tiny = simulate_scenario(tiny_df, price_change=0, discount=10, demand_multiplier=1.0)
    assert "error" in res_tiny
    assert res_tiny.get("has_data") is False

def test_reporting_date_range_validation_start_greater_than_end():
    """Verify reporting endpoint rejects invalid inverted date range with 400."""
    res = client.get("/api/v1/analytics/report?mode=range&start_date=2026-12-31&end_date=2026-01-01")
    assert res.status_code == 400
    assert "cannot be later than End Date" in res.json().get("detail", "")

def test_ml_analyze_date_range_validation_start_greater_than_end():
    """Verify forecast analyze endpoint rejects inverted date range with 400."""
    res = client.post("/api/v1/ml/analyze", json={
        "target_name": "ALL",
        "mode": "range",
        "start_date": "2026-12-31",
        "end_date": "2026-01-01"
    })
    assert res.status_code == 400

def test_model_health_uninitialized_null_checks():
    """Verify model health does not report hardcoded 0.042 or 5.8% when uninitialized."""
    res = client.get("/api/v1/analytics/model-health")
    assert res.status_code == 200
    data = res.json()
    if data.get("model_status") == "UNINITIALIZED":
        assert data.get("drift_score") is None
        assert data.get("avg_wape") is None
        assert data.get("avg_mae") is None
        assert data.get("drift_status") == "No Recorded Runs"

def test_inventory_intelligence_structure_and_non_fabrication():
    """Verify inventory endpoint returns has_inventory_tracking flag and respects null stock."""
    res = client.get("/api/v1/analytics/inventory")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for item in data:
        assert "has_inventory_tracking" in item
        assert "daily_velocity" in item
        assert "forecast_7d_demand" in item
        if not item["has_inventory_tracking"]:
            assert item["available_stock"] is None
            assert item["days_of_supply"] is None
            assert item["health_status"] == "DEMAND_ONLY"

def test_csv_upload_with_extra_columns_like_row_id():
    """Verify CSV upload succeeds when dataset contains extra retail columns like Row ID, Ship Mode."""
    import io
    csv_content = b"Row ID,Order ID,Order Date,Ship Mode,Customer ID,Product ID,Category,Quantity,Sales,Profit\n1,CA-2026-1,2026-05-01,Second Class,CG-12520,FUR-BO-10001798,Furniture,2,261.96,41.91\n"
    res = client.post(
        "/api/v1/data/upload?replace=true",
        files={"file": ("superstore_sample.csv", io.BytesIO(csv_content), "text/csv")}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["records_processed"] == 1


def test_model_health_persisted_from_forecast_and_root_endpoints():
    """Verify ModelRun log persistence when forecasting and root model-health endpoints."""
    # 1. Test root /api/model-health/latest
    res_root = client.get("/api/model-health/latest")
    assert res_root.status_code == 200
    assert "model_status" in res_root.json()

    # 2. Upload test data
    import io
    csv_rows = ["date,sku,units_sold,price"]
    for i in range(1, 16):
        csv_rows.append(f"2026-03-{i:02d},HEALTH-SKU-1,10,25.0")
    csv_bytes = "\n".join(csv_rows).encode("utf-8")
    client.post(
        "/api/v1/data/upload?replace=true",
        files={"file": ("test_health.csv", io.BytesIO(csv_bytes), "text/csv")}
    )

    # 3. Analyze in Forecast Lab
    res_fc = client.post("/api/v1/ml/analyze", json={
        "target_name": "HEALTH-SKU-1",
        "mode": "range",
        "start_date": "2026-03-01",
        "end_date": "2026-03-20"
    })
    assert res_fc.status_code == 200
    fc_data = res_fc.json()
    assert "model_run_id" in fc_data["summary"]

    # 4. Model Health should now be HEALTHY with logged metrics
    res_health = client.get("/api/v1/analytics/model-health")
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert health_data["model_status"] == "HEALTHY"
    assert health_data["active_model"] is not None
    assert health_data["avg_mae"] is not None
    assert health_data["avg_wape"] is not None
    assert len(health_data["last_trained_runs"]) >= 1

    # 5. Check root /api/model-health/latest returns matching metrics
    res_latest = client.get("/api/model-health/latest")
    assert res_latest.status_code == 200
    latest_data = res_latest.json()
    assert latest_data["model_status"] == "HEALTHY"
    assert latest_data["id"] == fc_data["summary"]["model_run_id"]
    assert latest_data["model_name"] is not None

