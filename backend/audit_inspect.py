import sqlite3
import pandas as pd
import numpy as np
import os
import glob

print("=== RAW CSV AUDIT ===")
upload_files = glob.glob("uploads/*samplesuperstore.csv")
if not upload_files:
    upload_files = glob.glob("backend/uploads/*samplesuperstore.csv")
print(f"Found upload files: {upload_files}")

csv_path = upload_files[0]
df_raw = pd.read_csv(csv_path, encoding_errors='replace')
print(f"CSV Columns: {list(df_raw.columns)}")
print(f"Raw Rows: {len(df_raw)}")

# Normalize column names for easy access
col_map = {c.strip().lower().replace(' ', '_').replace('-', '_'): c for c in df_raw.columns}
print(f"Normalized col keys: {list(col_map.keys())}")

order_col = col_map.get('order_id')
qty_col = col_map.get('quantity') or col_map.get('units_sold')
sales_col = col_map.get('sales') or col_map.get('total_sales')
profit_col = col_map.get('profit')
prod_col = col_map.get('product_id') or col_map.get('sku')
cat_col = col_map.get('category')
subcat_col = col_map.get('sub_category')
date_col = col_map.get('order_date') or col_map.get('date')

print("\n--- RAW CSV AGGREGATES ---")
print(f"Unique Orders: {df_raw[order_col].nunique() if order_col else 'N/A'}")
print(f"Quantity sum: {df_raw[qty_col].sum() if qty_col else 'N/A'}")
print(f"Sales sum: {df_raw[sales_col].sum():.4f}" if sales_col else 'N/A')
print(f"Profit sum: {df_raw[profit_col].sum():.4f}" if profit_col else 'N/A')
print(f"Unique Products: {df_raw[prod_col].nunique() if prod_col else 'N/A'}")
print(f"Unique Categories: {df_raw[cat_col].nunique() if cat_col else 'N/A'}")
print(f"Unique Subcategories: {df_raw[subcat_col].nunique() if subcat_col else 'N/A'}")
dates_parsed = pd.to_datetime(df_raw[date_col], errors='coerce')
print(f"Date range: {dates_parsed.min()} to {dates_parsed.max()}")
print(f"Null dates in raw: {dates_parsed.isna().sum()}")

print("\n=== SQLITE DB AUDIT ===")
db_path = "sql_app.db" if os.path.exists("sql_app.db") else "backend/sql_app.db"
conn = sqlite3.connect(db_path)
df_db = pd.read_sql_query("SELECT * FROM raw_sales_data", conn)
print(f"DB Rows: {len(df_db)}")
print(f"DB Columns: {list(df_db.columns)}")
print(f"DB Unique Orders: {df_db['order_id'].nunique()}")
print(f"DB Quantity sum: {df_db['units_sold'].sum()}")
print(f"DB Sales sum: {df_db['total_sales'].sum():.4f}")
print(f"DB Profit sum: {df_db['profit'].sum():.4f}")
print(f"DB Unique SKUs: {df_db['sku'].nunique()}")
print(f"DB Unique Categories: {df_db['category'].nunique()}")
print(f"DB Unique Subcategories: {df_db['sub_category'].nunique()}")
db_dates = pd.to_datetime(df_db['date'], errors='coerce')
print(f"DB Date range: {db_dates.min()} to {db_dates.max()}")

print("\n=== DISCREPANCY ANALYSIS ===")
row_diff = len(df_raw) - len(df_db)
qty_diff = df_raw[qty_col].sum() - df_db['units_sold'].sum()
sales_diff = df_raw[sales_col].sum() - df_db['total_sales'].sum()
profit_diff = df_raw[profit_col].sum() - df_db['profit'].sum()
print(f"Missing rows: {row_diff}")
print(f"Missing quantity: {qty_diff}")
print(f"Sales discrepancy: ${sales_diff:.4f}")
print(f"Profit discrepancy: ${profit_diff:.4f}")

# Check validation step on raw CSV to see where the 2 rows drop!
from app.data.validation import validate_sales_data, auto_map_columns
mapped_df, _ = auto_map_columns(df_raw)
print(f"\nAfter auto_map_columns: {len(mapped_df)} rows")
valid, msg, validated_df = validate_sales_data(df_raw)
print(f"After validate_sales_data: {len(validated_df)} rows. Msg: {msg}")

# Check if there are duplicate rows in raw CSV!
raw_dup = df_raw.duplicated()
print(f"Strict exact full-row duplicates in raw CSV: {raw_dup.sum()}")
if raw_dup.sum() > 0:
    print(df_raw[raw_dup][[date_col, order_col, prod_col, qty_col, sales_col, profit_col]])

# Check deduplicate_sales_data logic or drop_duplicates
subset_cols = ['date', 'sku', 'units_sold']
if 'order_id' in mapped_df.columns:
    subset_cols.append('order_id')
if 'product_name' in mapped_df.columns:
    subset_cols.append('product_name')
if 'total_sales' in mapped_df.columns:
    subset_cols.append('total_sales')

mapped_df['date'] = pd.to_datetime(mapped_df['date']).dt.date
mapped_df['units_sold'] = pd.to_numeric(mapped_df['units_sold'], errors='coerce').fillna(1).round().astype(int)
mapped_df['total_sales'] = pd.to_numeric(mapped_df['total_sales'], errors='coerce').fillna(0.0)

print(f"Duplicates in mapped_df by subset {subset_cols}: {mapped_df.duplicated(subset=subset_cols).sum()}")
dup_rows = mapped_df[mapped_df.duplicated(subset=subset_cols, keep=False)]
print("\nDuplicated candidates in mapped_df:")
print(dup_rows[['date', 'order_id', 'sku', 'units_sold', 'total_sales', 'profit']])
print("\nSums of duplicated rows:")
print(f"Quantity sum of second occurrence: {dup_rows.iloc[1::2]['units_sold'].sum()}")
print(f"Sales sum of second occurrence: {dup_rows.iloc[1::2]['total_sales'].sum()}")
print(f"Profit sum of second occurrence: {dup_rows.iloc[1::2]['profit'].sum()}")
