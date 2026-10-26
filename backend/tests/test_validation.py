import pandas as pd
import pytest
from app.data.validation import validate_sales_data

def test_validate_sales_data_valid():
    df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'sku': ['SKU-1001', 'SKU-1001', 'SKU-1001'],
        'units_sold': [10, 15, 20]
    })
    is_valid, msg, cleaned_df = validate_sales_data(df)
    assert is_valid is True
    assert "Successfully parsed and validated" in msg
    assert len(cleaned_df) == 3

def test_validate_sales_data_missing_column():
    df = pd.DataFrame({
        'date': ['2026-01-01'],
        'sku': ['SKU-1001']
        # missing units_sold
    })
    is_valid, msg, _ = validate_sales_data(df)
    assert is_valid is False
    assert "Missing required column" in msg

def test_validate_sales_data_negative_units():
    df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02'],
        'sku': ['SKU-1001', 'SKU-1001'],
        'units_sold': [10, -5]
    })
    is_valid, msg, _ = validate_sales_data(df)
    assert is_valid is False
    assert "units_sold must be valid positive numbers" in msg

def test_validate_sales_data_preserves_multiple_transactions():
    """Confirms row-level transactional granularity is preserved across orders on the same day."""
    df = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-01'],
        'sku': ['SKU-1001', 'SKU-1001'],
        'units_sold': [10, 25],
        'order_id': ['ORD-1', 'ORD-2'],
        'category': ['Furniture', 'Furniture'],
        'sub_category': ['Chairs', 'Chairs'],
        'sales': [100.0, 250.0],
        'profit': [20.0, 50.0]
    })
    is_valid, msg, cleaned_df = validate_sales_data(df)
    assert is_valid is True
    assert len(cleaned_df) == 2
    assert cleaned_df.iloc[0]['units_sold'] == 10
    assert cleaned_df.iloc[1]['units_sold'] == 25
    assert cleaned_df.iloc[0]['order_id'] == 'ORD-1'
    assert cleaned_df.iloc[1]['order_id'] == 'ORD-2'

