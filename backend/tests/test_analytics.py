import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_overview_structure():
    response = client.get("/api/v1/analytics/overview?period=all")
    assert response.status_code == 200
    data = response.json()
    
    # 10 core business KPIs
    assert "revenue" in data
    assert "total_records" in data
    assert "total_orders" in data
    assert "total_quantity" in data
    assert "aov" in data
    assert "total_profit" in data
    assert "profit_margin_pct" in data
    assert "active_predictions" in data
    assert "anomalies_detected" in data
    assert "forecasted_revenue" in data
    assert "insights" in data
    assert isinstance(data["insights"], list)

def test_get_overview_period_filtering():
    for p in ["all", "today", "7d", "30d", "this_month", "last_month"]:
        res = client.get(f"/api/v1/analytics/overview?period={p}")
        assert res.status_code == 200
        data = res.json()
        assert data["period"] == p

def test_get_trends():
    for interval in ["daily", "weekly", "monthly"]:
        res = client.get(f"/api/v1/analytics/trends?interval={interval}&period=all")
        assert res.status_code == 200
        data = res.json()
        assert data["interval"] == interval
        assert "series" in data
        assert isinstance(data["series"], list)
        assert "peak_date" in data
        assert "lowest_date" in data

def test_get_categories_breakdown():
    res = client.get("/api/v1/analytics/categories?period=all")
    assert res.status_code == 200
    data = res.json()
    assert "total_store_revenue" in data
    assert "category_summary" in data
    assert "breakdown" in data
    assert isinstance(data["breakdown"], list)

def test_get_products_analytics():
    res = client.get("/api/v1/analytics/products?limit=10&period=all")
    assert res.status_code == 200
    data = res.json()
    assert "top_selling" in data
    assert "lowest_selling" in data
    assert "total_products" in data

def test_get_transactions_table():
    res = client.get("/api/v1/analytics/transactions?page=1&page_size=20&sort_by=date&sort_dir=desc")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total_count" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data

def test_get_data_preview():
    res = client.get("/api/v1/data/preview?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "has_data" in data
    assert "row_count" in data
    assert "column_count" in data
    assert "columns" in data
    assert "missing_values" in data
    assert "sample_rows" in data

def test_get_ml_prediction_history():
    res = client.get("/api/v1/ml/history?limit=20")
    assert res.status_code == 200
    data = res.json()
    assert "total_runs" in data
    assert "runs" in data
    assert isinstance(data["runs"], list)

