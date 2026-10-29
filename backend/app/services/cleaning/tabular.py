import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Union


def clean_column_name(col: str) -> str:
    """Standardizes column name to clean snake_case."""
    s = str(col).strip().lower()
    s = re.sub(r'[\s\-\.]+', '_', s)
    s = re.sub(r'[^\w_]', '', s)
    s = re.sub(r'_+', '_', s).strip('_')
    return s if s else "unnamed_column"


def profile_tabular_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Step 2 & 3: Deep statistical profiling of tabular dataframe.
    Calculates missing percentages, cardinality, numerical distributions,
    date ranges, and data type classifications.
    """
    total_rows = len(df)
    total_cols = len(df.columns)
    duplicate_rows = int(df.duplicated().sum())

    columns_profile = {}
    type_summary = {
        "numeric": 0,
        "categorical": 0,
        "datetime": 0,
        "boolean": 0,
        "text": 0
    }

    for col in df.columns:
        series = df[col]
        missing_count = int(series.isnull().sum())
        missing_pct = round((missing_count / total_rows * 100), 2) if total_rows > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))
        dtype_str = str(series.dtype)

        col_info: Dict[str, Any] = {
            "name": col,
            "raw_dtype": dtype_str,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "sample_values": [str(v) for v in series.dropna().iloc[:3].tolist()]
        }

        # Classify column semantics
        if pd.api.types.is_bool_dtype(series):
            col_info["type_class"] = "boolean"
            type_summary["boolean"] += 1
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_info["type_class"] = "datetime"
            type_summary["datetime"] += 1
            col_info["min_date"] = str(series.min()) if not series.empty else None
            col_info["max_date"] = str(series.max()) if not series.empty else None
        elif pd.api.types.is_numeric_dtype(series):
            col_info["type_class"] = "numeric"
            type_summary["numeric"] += 1
            valid_vals = series.dropna()
            if not valid_vals.empty:
                col_info["min"] = float(valid_vals.min())
                col_info["max"] = float(valid_vals.max())
                col_info["mean"] = round(float(valid_vals.mean()), 2)
                col_info["std"] = round(float(valid_vals.std()), 2) if len(valid_vals) > 1 else 0.0
                col_info["median"] = round(float(valid_vals.median()), 2)
                col_info["q25"] = round(float(valid_vals.quantile(0.25)), 2)
                col_info["q75"] = round(float(valid_vals.quantile(0.75)), 2)
        else:
            # Test if object series is convertible to date
            sample_non_null = series.dropna().head(20).astype(str)
            date_matches = 0
            for val in sample_non_null:
                if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', val) or re.match(r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', val):
                    date_matches += 1
            
            if len(sample_non_null) > 0 and (date_matches / len(sample_non_null)) >= 0.7:
                col_info["type_class"] = "datetime"
                type_summary["datetime"] += 1
            elif unique_count <= max(20, int(total_rows * 0.05)):
                col_info["type_class"] = "categorical"
                type_summary["categorical"] += 1
            else:
                col_info["type_class"] = "text"
                type_summary["text"] += 1

        columns_profile[col] = col_info

    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "duplicate_rows": duplicate_rows,
        "type_summary": type_summary,
        "columns": columns_profile
    }


def remove_irrelevant_data(
    df: pd.DataFrame,
    drop_all_null_cols: bool = True,
    drop_all_null_rows: bool = True,
    explicit_columns_to_drop: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 4: Prunes completely empty rows/columns and user-specified irrelevant attributes.
    """
    df_clean = df.copy()
    rows_before = len(df_clean)
    cols_before = len(df_clean.columns)
    dropped_cols = []

    if drop_all_null_cols:
        all_null_cols = [c for c in df_clean.columns if df_clean[c].isnull().all()]
        if all_null_cols:
            df_clean.drop(columns=all_null_cols, inplace=True)
            dropped_cols.extend(all_null_cols)

    if explicit_columns_to_drop:
        existing = [c for c in explicit_columns_to_drop if c in df_clean.columns]
        if existing:
            df_clean.drop(columns=existing, inplace=True)
            dropped_cols.extend(existing)

    if drop_all_null_rows:
        df_clean.dropna(how='all', inplace=True)

    rows_after = len(df_clean)
    cols_after = len(df_clean.columns)

    return df_clean, {
        "rows_removed": rows_before - rows_after,
        "cols_removed": cols_before - cols_after,
        "dropped_columns": dropped_cols
    }


def handle_duplicates(
    df: pd.DataFrame,
    subset_columns: Optional[List[str]] = None,
    keep: str = "first"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 5: Detects and removes exact or key-based duplicate records.
    """
    df_clean = df.copy()
    rows_before = len(df_clean)

    valid_subset = [c for c in subset_columns if c in df_clean.columns] if subset_columns else None
    
    keep_val: Union[str, bool] = keep if keep in ["first", "last"] else False
    df_clean.drop_duplicates(subset=valid_subset, keep=keep_val, inplace=True)
    rows_after = len(df_clean)

    return df_clean, {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicates_removed": rows_before - rows_after,
        "subset_used": valid_subset or "all_columns",
        "keep_strategy": keep
    }


def handle_missing_values(
    df: pd.DataFrame,
    strategies: Optional[Dict[str, str]] = None,
    default_numeric_strategy: str = "median",
    default_categorical_strategy: str = "mode",
    threshold_row_drop_pct: Optional[float] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 6: Configurable missing value imputation.
    Guards: Never imputes identifier or primary key columns.
    """
    df_clean = df.copy()
    strategies = strategies or {}
    imputation_log = {}

    ID_COL_PATTERNS = ["id", "order_id", "transaction_id", "sku", "product_id", "uuid", "key"]

    # Optional: Drop rows where missing values exceed a given percentage
    if threshold_row_drop_pct is not None and 0.0 < threshold_row_drop_pct < 100.0:
        min_non_nulls = int(len(df_clean.columns) * (1.0 - threshold_row_drop_pct / 100.0))
        df_clean.dropna(thresh=min_non_nulls, inplace=True)

    for col in df_clean.columns:
        missing_count = int(df_clean[col].isnull().sum())
        if missing_count == 0:
            continue

        col_lower = col.lower().replace(" ", "_").replace("-", "_")
        is_id = any(pat == col_lower or col_lower.endswith(f"_{pat}") for pat in ID_COL_PATTERNS)

        # ID guard: do not impute IDs
        if is_id:
            imputation_info = {"strategy": "preserved_unimputed", "reason": "Identifier/Key field protected"}
            imputation_log[col] = imputation_info
            if col_lower != col:
                imputation_log[col_lower] = imputation_info
            continue

        strategy = strategies.get(col)
        if not strategy:
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                strategy = default_numeric_strategy
            else:
                strategy = default_categorical_strategy

        if strategy == "mean" and pd.api.types.is_numeric_dtype(df_clean[col]):
            fill_val = df_clean[col].mean()
            df_clean[col] = df_clean[col].fillna(fill_val)
            imputation_log[col] = {"strategy": "mean", "imputed_count": missing_count, "fill_value": round(float(fill_val), 2)}
        elif strategy == "median" and pd.api.types.is_numeric_dtype(df_clean[col]):
            fill_val = df_clean[col].median()
            df_clean[col] = df_clean[col].fillna(fill_val)
            imputation_log[col] = {"strategy": "median", "imputed_count": missing_count, "fill_value": round(float(fill_val), 2)}
        elif strategy == "mode":
            mode_vals = df_clean[col].mode(dropna=True)
            fill_val = mode_vals.iloc[0] if not mode_vals.empty else "N/A"
            df_clean[col] = df_clean[col].fillna(fill_val)
            imputation_log[col] = {"strategy": "mode", "imputed_count": missing_count, "fill_value": str(fill_val)}
        elif strategy == "ffill":
            df_clean[col] = df_clean[col].ffill()
            imputation_log[col] = {"strategy": "ffill", "imputed_count": missing_count}
        elif strategy == "bfill":
            df_clean[col] = df_clean[col].bfill()
            imputation_log[col] = {"strategy": "bfill", "imputed_count": missing_count}
        elif strategy == "drop":
            df_clean.dropna(subset=[col], inplace=True)
            imputation_log[col] = {"strategy": "drop_rows", "rows_dropped": missing_count}
        elif strategy == "constant":
            const_val = 0 if pd.api.types.is_numeric_dtype(df_clean[col]) else "Unknown"
            df_clean[col] = df_clean[col].fillna(const_val)
            imputation_log[col] = {"strategy": "constant", "imputed_count": missing_count, "fill_value": const_val}

    return df_clean, imputation_log


def correct_and_standardize_formats(
    df: pd.DataFrame,
    standardize_column_names: bool = True,
    parse_dates: bool = True,
    clean_numeric_strings: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Steps 7 & 8: Data type corrections and format standardizations.
    Coerces numeric strings, strips currency punctuation, parses ISO dates,
    normalizes snake_case columns.
    """
    df_clean = df.copy()
    conversions = {}

    # Standardize column headers to snake_case
    if standardize_column_names:
        rename_map = {col: clean_column_name(col) for col in df_clean.columns}
        df_clean.rename(columns=rename_map, inplace=True)
        conversions["renamed_columns"] = {orig: new for orig, new in rename_map.items() if orig != new}

    for col in df_clean.columns:
        series = df_clean[col]
        # Clean numeric strings ($1,234.50 -> 1234.50)
        if clean_numeric_strings and (series.dtype == 'object' or pd.api.types.is_string_dtype(series)):
            sample = series.dropna().astype(str).head(20)
            has_currency = sample.str.contains(r'[\$,€,£]').any()
            numeric_like = sample.str.replace(r'[\$,€,£\s]', '', regex=True).str.match(r'^-?\d+(\.\d+)?$').all()
            if has_currency and numeric_like:
                cleaned = series.astype(str).str.replace(r'[\$,€,£\s]', '', regex=True)
                df_clean[col] = pd.to_numeric(cleaned, errors='coerce')
                conversions[col] = "coerced_currency_to_numeric"
                continue

        # Date parsing
        if parse_dates and (series.dtype == 'object' or pd.api.types.is_string_dtype(series) or pd.api.types.is_datetime64_any_dtype(series)):
            sample = series.dropna().astype(str).head(15)
            date_like = sum(bool(re.match(r'^\d{2,4}[-/]\d{1,2}[-/]\d{1,4}', v)) for v in sample)
            if len(sample) > 0 and (date_like / len(sample)) >= 0.7:
                parsed = pd.to_datetime(series, errors='coerce')
                # If parsed successfully for non-null items
                if parsed.notna().sum() >= (series.notna().sum() * 0.8):
                    df_clean[col] = parsed.dt.strftime('%Y-%m-%d')
                    conversions[col] = "standardized_date_iso8601"

    return df_clean, conversions


def detect_and_handle_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    threshold: float = 1.5,
    action: str = "cap",
    target_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Steps 11 & 12: Evaluates and handles numerical outliers via IQR or Z-score.
    Actions: 'keep' (flags only), 'cap' (winsorize bounds), 'drop' (removes rows).
    """
    df_clean = df.copy()
    outlier_report = {}

    numeric_cols = [c for c in df_clean.columns if pd.api.types.is_numeric_dtype(df_clean[c])]
    if target_columns:
        numeric_cols = [c for c in numeric_cols if c in target_columns]

    rows_to_drop = set()

    for col in numeric_cols:
        series = df_clean[col].dropna()
        if len(series) < 5:
            continue

        if method == "iqr":
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            lower_bound = q25 - (threshold * iqr)
            upper_bound = q75 + (threshold * iqr)
        else:  # zscore
            mean = float(series.mean())
            std = float(series.std()) if len(series) > 1 else 1.0
            lower_bound = mean - (threshold * std)
            upper_bound = mean + (threshold * std)

        outlier_mask = (df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)
        outlier_count = int(outlier_mask.sum())

        outlier_report[col] = {
            "method": method,
            "threshold": threshold,
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "outliers_detected": outlier_count,
            "action_applied": action
        }

        if outlier_count > 0:
            if action == "cap":
                df_clean[col] = df_clean[col].clip(lower=lower_bound, upper=upper_bound)
            elif action == "drop":
                rows_to_drop.update(df_clean[outlier_mask].index.tolist())

    if rows_to_drop and action == "drop":
        df_clean.drop(index=list(rows_to_drop), inplace=True)
        outlier_report["total_rows_dropped"] = len(rows_to_drop)

    return df_clean, outlier_report


def validate_cross_field_rules(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Step 13: Evaluates business relationships across fields:
    - Quantity * Price vs Total Sales consistency
    - Units sold non-negative check
    """
    findings = []
    
    # Check 1: Units sold non-negative
    for qty_col in ["units_sold", "quantity", "units"]:
        if qty_col in df.columns and pd.api.types.is_numeric_dtype(df[qty_col]):
            neg_count = int((df[qty_col] < 0).sum())
            if neg_count > 0:
                findings.append({
                    "rule": f"{qty_col} must be non-negative",
                    "status": "VIOLATION",
                    "invalid_count": neg_count
                })

    # Check 2: total_sales vs units_sold * price
    sales_col = next((c for c in ["total_sales", "sales", "revenue"] if c in df.columns), None)
    qty_col = next((c for c in ["units_sold", "quantity"] if c in df.columns), None)
    price_col = next((c for c in ["price", "unit_price"] if c in df.columns), None)

    if sales_col and qty_col and price_col:
        def _to_num(series):
            if pd.api.types.is_numeric_dtype(series):
                return pd.to_numeric(series, errors='coerce')
            clean = series.astype(str).str.replace(r'[\$,]', '', regex=True)
            return pd.to_numeric(clean, errors='coerce')

        s_num = _to_num(df[sales_col])
        q_num = _to_num(df[qty_col])
        p_num = _to_num(df[price_col])

        mask = s_num.notna() & q_num.notna() & p_num.notna()
        if mask.any():
            expected = q_num[mask] * p_num[mask]
            diff = (s_num[mask] - expected).abs()
            mismatches = int((diff > 1.0).sum())  # Allow tolerance for promotional discounts
            if mismatches > 0:
                findings.append({
                    "rule": f"{sales_col} == {qty_col} * {price_col}",
                    "status": "FLAGGED",
                    "mismatches_detected": mismatches,
                    "note": "Line items variance likely represents discounts or promotions."
                })

    return df, {"cross_field_findings": findings}

