import io
import csv
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
import pandas as pd

from app.models.data import RawSalesData

logger = logging.getLogger(__name__)

def parse_date_safe(val: Any) -> Optional[date]:
    if not val:
        return None
    if isinstance(val, date) and not isinstance(val, datetime):
        return val
    if isinstance(val, datetime):
        return val.date()
    try:
        s = str(val).strip()[:10]
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        try:
            return pd.to_datetime(val).date()
        except Exception:
            return None

def format_date_safe(val: Any) -> Optional[str]:
    if not val:
        return None
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s

def build_detail_csv(category_breakdown: List[Dict[str, Any]], has_profit: bool = True) -> str:
    """
    Constructs an RFC 4180 compliant CSV string for the detailed category & sub-category report.
    Compatible with Excel, Tableau, and pandas.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Required column headers exactly following Professional_Sales_Summary_Report structure
    headers = [
        "Category",
        "Sub-Category",
        "Total_Orders",
        "Total_Quantity_Sold",
        "Total_Sales_USD",
        "Total_Profit_USD",
        "Profit_Margin_Percentage"
    ]
    writer.writerow(headers)
    
    for row in category_breakdown:
        profit_val = (
            f"{row['total_profit_usd']:.2f}"
            if (row.get('total_profit_usd') is not None)
            else "N/A"
        )
        margin_val = (
            f"{row['profit_margin_pct']:.2f}"
            if (row.get('profit_margin_pct') is not None)
            else "N/A"
        )
        
        writer.writerow([
            row.get("category", "Uncategorized"),
            row.get("sub_category", "General"),
            row.get("total_orders", 0),
            row.get("total_quantity_sold", 0),
            f"{row.get('total_sales_usd', 0.0):.2f}",
            profit_val,
            margin_val
        ])
        
    return output.getvalue()

def build_summary_csv(report_data: Dict[str, Any]) -> str:
    """
    Constructs a separate, clean Summary & Metadata CSV file.
    Does not contaminate the category detail rows.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    meta = report_data.get("report_metadata", {})
    summary = report_data.get("summary", {})
    
    writer.writerow(["Report_Metadata", "Value"])
    writer.writerow(["Report Title", meta.get("report_title", "Professional Sales Summary Report")])
    writer.writerow(["Report Generated At", meta.get("generated_at", "")])
    writer.writerow(["Analysis Mode", meta.get("analysis_mode", "")])
    writer.writerow(["Target Scope / Product", meta.get("target_product", "All Products")])
    writer.writerow(["Selected Date", meta.get("selected_date") or "N/A"])
    writer.writerow(["Date Range Start", meta.get("start_date") or "N/A"])
    writer.writerow(["Date Range End", meta.get("end_date") or "N/A"])
    writer.writerow(["Total Revenue (USD)", f"${summary.get('total_revenue', 0.0):,.2f}"])
    writer.writerow(["Total Distinct Orders", summary.get("total_distinct_orders", 0)])
    writer.writerow(["Total Quantity Sold", summary.get("total_quantity_sold", 0)])
    
    if summary.get("total_profit") is not None:
        writer.writerow(["Total Profit (USD)", f"${summary.get('total_profit', 0.0):,.2f}"])
    else:
        writer.writerow(["Total Profit (USD)", "N/A (Missing Profit data)"])
        
    if summary.get("overall_profit_margin_pct") is not None:
        writer.writerow(["Overall Profit Margin", f"{summary.get('overall_profit_margin_pct', 0.0):.2f}%"])
    else:
        writer.writerow(["Overall Profit Margin", "N/A"])
        
    writer.writerow(["Total Categories", summary.get("total_categories", 0)])
    writer.writerow(["Total Sub-Categories", summary.get("total_sub_categories", 0)])
    writer.writerow(["Total SKUs Analysed", summary.get("total_skus_analyzed", 0)])
    writer.writerow(["Total Transaction Records", summary.get("total_records_analyzed", 0)])
    
    cov = meta.get("data_coverage_period", {})
    writer.writerow(["Dataset Coverage Period", f"{cov.get('min_date', '')} to {cov.get('max_date', '')}"])
    writer.writerow(["Currency Unit", meta.get("currency", "USD")])
    writer.writerow(["Data Integrity Status", "Computed from Grounded Transaction Ledger"])
    
    return output.getvalue()

def generate_professional_sales_report(
    db: Session,
    target_name: Optional[str] = "ALL",
    mode: Optional[str] = "range",
    selected_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tenant_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Core business intelligence engine for compiling the Professional Sales Summary Report.
    Works seamlessly with Option A (Selected Date) and Option B (Date Range).
    """
    now_utc = datetime.utcnow()
    report_gen_date = now_utc.strftime("%Y-%m-%d")
    gen_timestamp = now_utc.isoformat() + "Z"
    
    # 1. Dataset metadata & boundaries
    base_raw = db.query(RawSalesData)
    if tenant_id:
        base_raw = base_raw.filter(RawSalesData.tenant_id == tenant_id)
    total_db_records = base_raw.count()
    min_date_raw = base_raw.with_entities(func.min(RawSalesData.date)).scalar()
    max_date_raw = base_raw.with_entities(func.max(RawSalesData.date)).scalar()
    min_date_str = format_date_safe(min_date_raw)
    max_date_str = format_date_safe(max_date_raw)
    
    clean_target = (target_name or "ALL").strip()
    is_all_products = clean_target.upper() in ["ALL", "GLOBAL", "TOTAL", "", "ALL PRODUCTS", "ALL SKUS"]
    resolved_target_label = "All Products (Global Aggregate)" if is_all_products else clean_target
    
    clean_mode = (mode or "range").strip().lower()
    if clean_mode not in ["single", "range"]:
        clean_mode = "range"
        
    # 2. Build filtered SQL query
    query = db.query(RawSalesData).filter(RawSalesData.status == "PROCESSED")
    if tenant_id:
        query = query.filter(RawSalesData.tenant_id == tenant_id)
    
    # Filter by Product/SKU if specified
    if not is_all_products:
        query = query.filter(
            or_(
                RawSalesData.sku == clean_target,
                RawSalesData.product_name == clean_target,
                RawSalesData.sub_category == clean_target
            )
        )
        
    # Filter by Date
    parsed_selected = None
    parsed_start = None
    parsed_end = None
    mode_label = ""
    
    if clean_mode == "single":
        if not selected_date:
            parsed_selected = max_date_raw
        else:
            parsed_selected = parse_date_safe(selected_date)
            
        if parsed_selected:
            query = query.filter(RawSalesData.date == parsed_selected)
            mode_label = f"Selected Date: {format_date_safe(parsed_selected)}"
        else:
            mode_label = "Selected Date: (Unspecified)"
    else:
        # Date Range
        if start_date:
            parsed_start = parse_date_safe(start_date)
        if end_date:
            parsed_end = parse_date_safe(end_date)
            
        if parsed_start and parsed_end and parsed_start > parsed_end:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: Start Date ({parsed_start}) cannot be later than End Date ({parsed_end}). Please choose an ascending date range."
            )
            
        if parsed_start:
            query = query.filter(RawSalesData.date >= parsed_start)
        if parsed_end:
            query = query.filter(RawSalesData.date <= parsed_end)
            
        start_disp = format_date_safe(parsed_start) if parsed_start else (min_date_str or "Earliest")
        end_disp = format_date_safe(parsed_end) if parsed_end else (max_date_str or "Latest")
        mode_label = f"Date Range: {start_disp} to {end_disp}"

    # 3. Fetch matched records
    rows = query.all()
    
    # 4. Handle empty records state gracefully
    if not rows:
        reason = ""
        if total_db_records == 0:
            reason = "No sales records currently exist in the database. Please import a dataset in Data Ingestion."
        elif clean_mode == "single":
            reason = f"No sales transactions recorded for '{resolved_target_label}' on {format_date_safe(parsed_selected)}. Dataset coverage spans from {min_date_str} to {max_date_str}."
        else:
            reason = f"No sales transactions found for '{resolved_target_label}' between {format_date_safe(parsed_start) or 'Start'} and {format_date_safe(parsed_end) or 'End'}."
            
        return {
            "report_metadata": {
                "report_title": "Professional Sales Summary Report",
                "generated_at": gen_timestamp,
                "filename": f"professional_sales_summary_{report_gen_date}.csv",
                "summary_filename": f"professional_sales_summary_summary_{report_gen_date}.csv",
                "analysis_mode": mode_label,
                "mode_type": clean_mode,
                "selected_date": format_date_safe(parsed_selected),
                "start_date": format_date_safe(parsed_start),
                "end_date": format_date_safe(parsed_end),
                "target_product": resolved_target_label,
                "currency": "USD",
                "total_records_included": 0,
                "has_data": False,
                "empty_reason": reason,
                "data_coverage_period": {
                    "min_date": min_date_str,
                    "max_date": max_date_str,
                    "total_store_records": total_db_records
                },
                "features_available": {
                    "has_category": False,
                    "has_sub_category": False,
                    "has_order_id": False,
                    "has_profit": False,
                    "has_sales": False
                },
                "missing_data_notes": [reason]
            },
            "summary": {
                "total_revenue": 0.0,
                "total_distinct_orders": 0,
                "total_quantity_sold": 0,
                "total_profit": None,
                "overall_profit_margin_pct": None,
                "total_categories": 0,
                "total_sub_categories": 0,
                "total_skus_analyzed": 0,
                "total_records_analyzed": 0
            },
            "category_breakdown": [],
            "detail_csv": "Category,Sub-Category,Total_Orders,Total_Quantity_Sold,Total_Sales_USD,Total_Profit_USD,Profit_Margin_Percentage\n",
            "summary_csv": "Report_Metadata,Value\n"
        }

    # 5. Check column availability in the filtered records
    has_category = any(bool(r.category and str(r.category).strip()) for r in rows)
    has_sub_category = any(bool(r.sub_category and str(r.sub_category).strip()) for r in rows)
    has_order_id = any(bool(r.order_id and str(r.order_id).strip() and str(r.order_id).strip().lower() != 'nan') for r in rows)
    has_profit = any(r.profit is not None for r in rows)
    
    missing_notes = []
    if not has_category:
        missing_notes.append("Dataset does not include a 'Category' column. General Catalog used.")
    if not has_sub_category:
        missing_notes.append("Dataset does not include a 'Sub-Category' column. SKU labels used.")
    if not has_order_id:
        missing_notes.append("Dataset does not include an 'Order ID' column. Unique line items used as order proxy.")
    if not has_profit:
        missing_notes.append("Dataset does not include a 'Profit' column. Profit and Margin metrics marked as N/A.")

    # 6. Compute Global Metrics
    total_records = len(rows)
    
    # Calculate revenue: prefer total_sales column, fallback to units_sold * price
    def get_sale_amount(r: RawSalesData) -> float:
        if r.total_sales is not None:
            return float(r.total_sales)
        units = r.units_sold if r.units_sold is not None else 1
        price = float(r.price) if r.price is not None else 0.0
        return float(units * price)

    total_revenue = round(sum(get_sale_amount(r) for r in rows), 2)
    total_quantity = sum(int(r.units_sold or 0) for r in rows)
    
    # Calculate total unique distinct orders across entire scope
    if has_order_id:
        distinct_orders_set = set(str(r.order_id).strip() for r in rows if r.order_id and str(r.order_id).strip() and str(r.order_id).strip().lower() != 'nan')
        total_distinct_orders = len(distinct_orders_set)
    else:
        total_distinct_orders = total_records

    # Calculate total profit
    if has_profit:
        total_profit = round(sum(float(r.profit) for r in rows if r.profit is not None), 2)
        overall_margin = (
            round((total_profit / total_revenue) * 100.0, 2)
            if total_revenue > 0
            else 0.0
        )
    else:
        total_profit = None
        overall_margin = None

    categories_seen = set()
    sub_categories_seen = set()
    skus_seen = set()

    # 7. Group records by Category & Sub-Category
    grouped_data: Dict[tuple, Dict[str, Any]] = {}
    
    for r in rows:
        cat = str(r.category).strip() if (r.category and str(r.category).strip() and str(r.category).strip().lower() != 'nan') else ("General" if not has_category else "Uncategorized")
        sub_cat = str(r.sub_category).strip() if (r.sub_category and str(r.sub_category).strip() and str(r.sub_category).strip().lower() != 'nan') else (r.product_name or r.sku or "General")
        
        categories_seen.add(cat)
        sub_categories_seen.add(sub_cat)
        if r.sku:
            skus_seen.add(r.sku)
            
        key = (cat, sub_cat)
        if key not in grouped_data:
            grouped_data[key] = {
                "category": cat,
                "sub_category": sub_cat,
                "orders_set": set(),
                "transactions_count": 0,
                "quantity": 0,
                "sales": 0.0,
                "profit": 0.0,
                "has_profit_row": False
            }
            
        item = grouped_data[key]
        if r.order_id and str(r.order_id).strip() and str(r.order_id).strip().lower() != 'nan':
            item["orders_set"].add(str(r.order_id).strip())
        item["transactions_count"] += 1
        item["quantity"] += int(r.units_sold or 0)
        item["sales"] += get_sale_amount(r)
        if r.profit is not None:
            item["profit"] += float(r.profit)
            item["has_profit_row"] = True

    # 8. Transform into sorted breakdown list (Highest sales first)
    category_breakdown: List[Dict[str, Any]] = []
    
    for (cat, sub_cat), data in grouped_data.items():
        sales_usd = round(data["sales"], 2)
        profit_usd = round(data["profit"], 2) if has_profit else None
        
        if has_profit and sales_usd > 0:
            margin_pct = round((data["profit"] / sales_usd) * 100.0, 2)
        elif has_profit and sales_usd == 0:
            margin_pct = 0.0
        else:
            margin_pct = None
            
        total_orders_for_sub = len(data["orders_set"]) if has_order_id else data["transactions_count"]
        
        category_breakdown.append({
            "category": cat,
            "sub_category": sub_cat,
            "total_orders": total_orders_for_sub,
            "total_quantity_sold": data["quantity"],
            "total_sales_usd": sales_usd,
            "total_profit_usd": profit_usd,
            "profit_margin_pct": margin_pct
        })
        
    # Sort descending by sales amount
    category_breakdown.sort(key=lambda x: x["total_sales_usd"], reverse=True)

    # 9. Build final response structure
    report_manifest = {
        "report_title": "Professional Sales Summary Report",
        "generated_at": gen_timestamp,
        "filename": f"professional_sales_summary_{report_gen_date}.csv",
        "summary_filename": f"professional_sales_summary_summary_{report_gen_date}.csv",
        "analysis_mode": mode_label,
        "mode_type": clean_mode,
        "selected_date": format_date_safe(parsed_selected),
        "start_date": format_date_safe(parsed_start),
        "end_date": format_date_safe(parsed_end),
        "target_product": resolved_target_label,
        "currency": "USD",
        "total_records_included": total_records,
        "has_data": True,
        "data_coverage_period": {
            "min_date": min_date_str,
            "max_date": max_date_str,
            "total_store_records": total_db_records
        },
        "features_available": {
            "has_category": has_category,
            "has_sub_category": has_sub_category,
            "has_order_id": has_order_id,
            "has_profit": has_profit,
            "has_sales": True
        },
        "missing_data_notes": missing_notes
    }
    
    summary_metrics = {
        "total_revenue": total_revenue,
        "total_distinct_orders": total_distinct_orders,
        "total_quantity_sold": total_quantity,
        "total_profit": total_profit,
        "overall_profit_margin_pct": overall_margin,
        "total_categories": len(categories_seen),
        "total_sub_categories": len(sub_categories_seen),
        "total_skus_analyzed": len(skus_seen),
        "total_records_analyzed": total_records
    }
    
    # 10. Generate CSV payloads
    detail_csv = build_detail_csv(category_breakdown, has_profit=has_profit)
    full_report_obj = {
        "report_metadata": report_manifest,
        "summary": summary_metrics,
        "category_breakdown": category_breakdown
    }
    summary_csv = build_summary_csv(full_report_obj)
    
    return {
        "report_metadata": report_manifest,
        "summary": summary_metrics,
        "category_breakdown": category_breakdown,
        "detail_csv": detail_csv,
        "summary_csv": summary_csv
    }

