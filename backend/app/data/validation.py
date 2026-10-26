import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Intelligent column aliasing dictionary
COLUMN_ALIASES = {
    'date': [
        'date', 'order date', 'order_date', 'orderdate', 'transaction date',
        'transaction_date', 'trans_date', 'timestamp', 'invoice date',
        'invoicedate', 'day', 'time', 'date_id'
    ],
    'order_id': [
        'order id', 'order_id', 'orderid', 'order number', 'order_number',
        'transaction id', 'transaction_id', 'invoice', 'invoice no', 'invoice_no'
    ],
    'category': [
        'category', 'product category', 'product_category', 'department', 'class'
    ],
    'sub_category': [
        'sub-category', 'subcategory', 'sub category', 'sub_category',
        'product sub category', 'product subcategory'
    ],
    'sku': [
        'sku', 'product id', 'product_id', 'productid', 'item code',
        'item_code', 'item id', 'item_id', 'item'
    ],
    'product_name': [
        'product name', 'product_name', 'productname', 'item name', 'item_name',
        'title', 'product title', 'product_title', 'description'
    ],
    'units_sold': [
        'units_sold', 'units sold', 'units', 'quantity', 'qty',
        'quantity ordered', 'quantity_sold', 'units_ordered', 'volume',
        'sales_volume', 'count'
    ],
    'total_sales': [
        'sales', 'sales_amount', 'sales amount', 'total_sales', 'total sales',
        'revenue', 'total revenue', 'total_revenue', 'amount'
    ],
    'price': [
        'price', 'unit price', 'unit_price', 'unit_cost'
    ],
    'profit': [
        'profit', 'total profit', 'total_profit', 'net profit', 'net_profit',
        'margin', 'earnings'
    ],
    'discount_pct': [
        'discount_pct', 'discount', 'discount_rate', 'discount %',
        'promo_discount'
    ],
    'available_stock': [
        'available_stock', 'stock', 'inventory', 'stock_level',
        'quantity_on_hand', 'on_hand'
    ]
}

def normalize_column_name(col: str) -> str:
    """Strip punctuation, spaces, and lowercase for fuzzy column matching."""
    return str(col).strip().lower().replace("_", " ").replace("-", " ")

def auto_map_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Automatically detects and maps common column names to canonical schema.
    Returns the mapped dataframe and the mapping dict.
    """
    mapped_df = df.copy()
    col_mapping = {}
    normalized_cols = {normalize_column_name(col): col for col in df.columns}

    for canonical, aliases in COLUMN_ALIASES.items():
        matched_original = None
        for alias in aliases:
            norm_alias = normalize_column_name(alias)
            if norm_alias in normalized_cols:
                matched_original = normalized_cols[norm_alias]
                break
        
        if matched_original:
            col_mapping[matched_original] = canonical

    # Rename matched columns
    mapped_df.rename(columns=col_mapping, inplace=True)
    return mapped_df, col_mapping

def validate_sales_data(df: pd.DataFrame) -> tuple[bool, str, pd.DataFrame]:
    """
    Validates and normalizes sales data.
    Automatically recognizes Superstore, Kaggle, Shopify, and enterprise retail formats.
    Preserves order identifiers, categories, sub-categories, sales amounts, and profits.
    """
    if df.empty:
        return False, "CSV file is empty", df

    # Step 1: Auto-map columns
    df, mapping = auto_map_columns(df)

    # Step 2: Validate 'date' column
    if 'date' not in df.columns:
        avail = ", ".join(list(df.columns)[:8])
        return False, f"Missing required date column (e.g. 'Order Date', 'Transaction Date', or 'date'). Available columns: {avail}", df

    # Parse dates safely supporting mixed formats (e.g. 08/11/2017 or 2017-11-08)
    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    except Exception as e:
        return False, f"Failed to parse date column: {e}", df

    # Drop invalid/null dates
    invalid_dates_count = df['date'].isnull().sum()
    if invalid_dates_count == len(df):
        return False, "All dates in the 'date' column failed to parse.", df
    if invalid_dates_count > 0:
        logger.warning(f"Dropping {invalid_dates_count} rows with unparseable dates.")
        df = df.dropna(subset=['date'])

    # Step 3: Validate 'sku' and 'product_name'
    if 'product_name' in df.columns:
        df['product_name'] = df['product_name'].astype(str).str.strip()
    
    if 'sku' not in df.columns:
        if 'product_name' in df.columns and (df['product_name'] != '').any():
            df['sku'] = df['product_name']
            logger.info("Auto-assigned 'product_name' as SKU.")
        else:
            str_cols = [c for c in df.columns if df[c].dtype == 'object' and c != 'date']
            if str_cols:
                df['sku'] = df[str_cols[0]].astype(str)
                logger.info(f"Auto-assigned column '{str_cols[0]}' as SKU.")
            else:
                df['sku'] = "GLOBAL-CATALOG"
    else:
        df['sku'] = df['sku'].astype(str).str.strip()
        df = df[df['sku'] != '']

    if 'product_name' not in df.columns:
        df['product_name'] = df['sku']
    else:
        df['product_name'] = df['product_name'].replace('', np.nan).fillna(df['sku'])

    # Step 4: Validate 'units_sold' (Quantity)
    if 'units_sold' not in df.columns:
        return False, "Missing required column 'units_sold' (e.g. 'Quantity', 'Units Sold', 'Qty')", df

    numeric_units = pd.to_numeric(df['units_sold'], errors='coerce')
    if (numeric_units < 0).any():
        return False, "Validation failed: units_sold must be valid positive numbers.", df

    df['units_sold'] = numeric_units.fillna(1).round().astype(int)

    # Step 5: Validate 'total_sales' and 'price'
    if 'total_sales' in df.columns:
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce').fillna(0.0)
    
    if 'price' in df.columns:
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        if 'total_sales' not in df.columns:
            df['total_sales'] = (df['price'] * df['units_sold']).round(2)
    elif 'total_sales' in df.columns:
        # Calculate unit price from total_sales / units_sold
        df['price'] = (df['total_sales'] / df['units_sold'].replace(0, 1)).round(2)
    else:
        df['price'] = 25.0
        df['total_sales'] = (df['price'] * df['units_sold']).round(2)

    df['price'] = df['price'].fillna(0.0).clip(lower=0.0)

    # Step 6: Validate optional 'profit'
    if 'profit' in df.columns:
        df['profit'] = pd.to_numeric(df['profit'], errors='coerce')

    # Step 7: Validate optional 'order_id'
    if 'order_id' in df.columns:
        df['order_id'] = df['order_id'].astype(str).str.strip()
        df['order_id'] = df['order_id'].replace(['nan', 'None', '', 'NaN'], np.nan)

    # Step 8: Validate optional 'category' & 'sub_category'
    if 'category' in df.columns:
        df['category'] = df['category'].astype(str).str.strip()
        df['category'] = df['category'].replace(['nan', 'None', '', 'NaN'], np.nan)

    if 'sub_category' in df.columns:
        df['sub_category'] = df['sub_category'].astype(str).str.strip()
        df['sub_category'] = df['sub_category'].replace(['nan', 'None', '', 'NaN'], np.nan)

    # Step 9: Validate optional 'discount_pct'
    if 'discount_pct' in df.columns:
        df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce').fillna(0.0)
        # If discount is in decimal form (e.g. 0.2), convert to percentage (20.0)
        if (df['discount_pct'] <= 1.0).all() and (df['discount_pct'] > 0.0).any():
            df['discount_pct'] = df['discount_pct'] * 100.0
    else:
        df['discount_pct'] = 0.0

    # Step 10: Validate optional 'available_stock'
    if 'available_stock' in df.columns:
        df['available_stock'] = pd.to_numeric(df['available_stock'], errors='coerce')
    else:
        df['available_stock'] = None

    # Filter to only canonical database attributes while preserving full row-level granularity
    CANONICAL_COLUMNS = [
        'date', 'order_id', 'sku', 'product_name', 'category', 'sub_category',
        'units_sold', 'price', 'total_sales', 'profit', 'discount_pct',
        'available_stock', 'holiday_flag', 'festival_flag'
    ]
    cols_to_keep = [c for c in df.columns if c in CANONICAL_COLUMNS]
    df = df[cols_to_keep].reset_index(drop=True)

    return True, f"Successfully parsed and validated {len(df)} records across {df['sku'].nunique()} SKUs.", df
