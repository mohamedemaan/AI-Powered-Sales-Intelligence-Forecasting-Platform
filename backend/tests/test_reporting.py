import pytest
import io
import pandas as pd
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.services.reporting_service import (
    build_detail_csv,
    build_summary_csv,
    generate_professional_sales_report,
    generate_professional_sales_report_excel,
    generate_professional_sales_report_pdf,
    generate_professional_sales_report_parquet,
    generate_professional_sales_report_tsv,
    generate_professional_sales_report_json
)

client = TestClient(app)

def test_build_detail_csv_structure():
    category_data = [
        {
            "category": "Technology",
            "sub_category": "Phones",
            "total_orders": 120,
            "total_quantity_sold": 350,
            "total_sales_usd": 45000.50,
            "total_profit_usd": 9000.10,
            "profit_margin_pct": 20.00
        },
        {
            "category": "Furniture",
            "sub_category": "Tables",
            "total_orders": 45,
            "total_quantity_sold": 80,
            "total_sales_usd": 15000.00,
            "total_profit_usd": -1200.00,
            "profit_margin_pct": -8.00
        }
    ]
    
    csv_str = build_detail_csv(category_data, has_profit=True)
    df = pd.read_csv(io.StringIO(csv_str))
    
    # Required columns
    expected_cols = [
        "Category",
        "Sub-Category",
        "Total_Orders",
        "Total_Quantity_Sold",
        "Total_Sales_USD",
        "Total_Profit_USD",
        "Profit_Margin_Percentage"
    ]
    assert list(df.columns) == expected_cols
    assert len(df) == 2
    assert df.iloc[0]["Category"] == "Technology"
    assert df.iloc[0]["Total_Sales_USD"] == 45000.50
    assert df.iloc[0]["Profit_Margin_Percentage"] == 20.00
    
    # Negative profit (commercial loss) verification
    assert df.iloc[1]["Total_Profit_USD"] == -1200.00
    assert df.iloc[1]["Profit_Margin_Percentage"] == -8.00

def test_build_detail_csv_missing_profit():
    category_data = [
        {
            "category": "Office Supplies",
            "sub_category": "Paper",
            "total_orders": 30,
            "total_quantity_sold": 100,
            "total_sales_usd": 1200.00,
            "total_profit_usd": None,
            "profit_margin_pct": None
        }
    ]
    csv_str = build_detail_csv(category_data, has_profit=False)
    df = pd.read_csv(io.StringIO(csv_str), dtype=str, keep_default_na=False)
    assert df.iloc[0]["Total_Profit_USD"] == "N/A"
    assert df.iloc[0]["Profit_Margin_Percentage"] == "N/A"

def test_build_summary_csv_metadata():
    report_data = {
        "report_metadata": {
            "report_title": "Professional Sales Summary Report",
            "generated_at": "2026-10-22T20:00:00Z",
            "analysis_mode": "Date Range: 2026-01-01 to 2026-03-31",
            "target_product": "All Products (Global Aggregate)",
            "selected_date": None,
            "start_date": "2026-01-01",
            "end_date": "2026-03-31"
        },
        "summary": {
            "total_revenue": 150000.00,
            "total_distinct_orders": 450,
            "total_quantity_sold": 1200,
            "total_profit": 25000.00,
            "overall_profit_margin_pct": 16.67
        }
    }
    csv_str = build_summary_csv(report_data)
    df = pd.read_csv(io.StringIO(csv_str))
    assert list(df.columns) == ["Report_Metadata", "Value"]
    assert len(df) >= 10

def test_report_endpoint_get():
    response = client.get("/api/v1/analytics/report?mode=range&start_date=2020-01-01&end_date=2030-12-31")
    assert response.status_code == 200
    data = response.json()
    assert "report_metadata" in data
    assert "summary" in data
    assert "category_breakdown" in data
    assert "detail_csv" in data
    assert "summary_csv" in data
    assert "filename" in data["report_metadata"]
    assert data["report_metadata"]["filename"].startswith("professional_sales_summary_")

def test_report_endpoint_post():
    response = client.post("/api/v1/analytics/report", json={
        "target_name": "ALL",
        "mode": "range",
        "start_date": "2020-01-01",
        "end_date": "2030-12-31"
    })
    assert response.status_code == 200
    data = response.json()
    assert "report_metadata" in data
    assert data["report_metadata"]["target_product"] == "All Products (Global Aggregate)"

def test_report_csv_download():
    response = client.get("/api/v1/analytics/report/csv?mode=range&start_date=2020-01-01&end_date=2030-12-31")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"professional_sales_summary_" in response.headers["content-disposition"]


def test_report_multi_format_exports():
    formats = [
        ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ("pdf", "application/pdf"),
        ("parquet", "application/vnd.apache.parquet"),
        ("tsv", "text/tab-separated-values"),
        ("json", "application/json"),
        ("summary_csv", "text/csv"),
    ]
    for fmt, mime in formats:
        response = client.get(f"/api/v1/analytics/report/export?format={fmt}&mode=range&start_date=2020-01-01&end_date=2030-12-31")
        assert response.status_code == 200, f"Format {fmt} failed with {response.status_code}"
        assert mime in response.headers["content-type"], f"Expected {mime} for {fmt}, got {response.headers['content-type']}"
        assert "Content-Disposition" in response.headers
        assert len(response.content) > 50


