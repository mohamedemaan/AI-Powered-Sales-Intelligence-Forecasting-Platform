from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, Any
from app.api import deps
from app.models.tenant import Tenant
from app.models.data import RawSalesData
import shutil
import os

router = APIRouter()

def format_date_safe(val: Optional[Any]) -> Optional[str]:
    if not val:
        return None
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    s = str(val).strip()
    return s[:10] if len(s) >= 10 else s

@router.post("/upload")
async def upload_data(
    file: UploadFile = File(...),
    replace: bool = Query(True, description="Whether to replace previous sales records or append"),
    db: Session = Depends(deps.get_db),
    current_tenant: Any = Depends(deps.get_current_tenant_or_default)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    # Extract tenant id before file and DB transactions to prevent session detach
    active_tenant_id = getattr(current_tenant, "id", None)
    if not active_tenant_id:
        active_tenant = deps.get_current_tenant_or_default(db=db)
        active_tenant_id = active_tenant.id

    # Sanitize filename to prevent path traversal
    import uuid
    safe_name = f"{uuid.uuid4().hex}_{os.path.basename(file.filename)}"
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{safe_name}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    from app.pipelines.etl import process_upload
    try:
        records = process_upload(db, file_path, replace=replace, tenant_id=active_tenant_id)
        return {"status": "success", "records_processed": records, "replaced": replace, "organization_id": str(active_tenant_id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/clean-duplicates")
def deduplicate_sales_data(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Scans raw_sales_data for the active organization workspace and removes duplicate rows.
    """
    total_before = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).count()
    if total_before == 0:
        return {"status": "success", "records_before": 0, "records_removed": 0, "total_records": 0}

    import pandas as pd
    rows = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).all()
    records = []
    for r in rows:
        records.append({
            'date': r.date,
            'order_id': r.order_id,
            'sku': r.sku,
            'product_name': r.product_name,
            'category': r.category,
            'sub_category': r.sub_category,
            'units_sold': r.units_sold,
            'price': float(r.price) if r.price is not None else None,
            'total_sales': float(r.total_sales) if r.total_sales is not None else None,
            'profit': float(r.profit) if r.profit is not None else None,
            'discount_pct': float(r.discount_pct) if r.discount_pct is not None else None,
            'available_stock': r.available_stock,
            'holiday_flag': r.holiday_flag,
            'festival_flag': r.festival_flag,
            'status': r.status
        })

    df = pd.DataFrame(records)
    subset_cols = ['date', 'sku', 'units_sold']
    if 'order_id' in df.columns and df['order_id'].notna().any():
        subset_cols.append('order_id')
    if 'product_name' in df.columns and df['product_name'].notna().any():
        subset_cols.append('product_name')
    if 'total_sales' in df.columns and df['total_sales'].notna().any():
        subset_cols.append('total_sales')
    df_unique = df.drop_duplicates(subset=subset_cols)
    
    records_removed = total_before - len(df_unique)
    if records_removed > 0:
        db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).delete()
        valid_cols = set(c.name for c in RawSalesData.__table__.columns)
        unique_records = df_unique.to_dict(orient='records')
        for ur in unique_records:
            clean_ur = {k: v for k, v in ur.items() if k in valid_cols and pd.notna(v) and k != 'id'}
            clean_ur['tenant_id'] = current_tenant.id
            db.add(RawSalesData(**clean_ur))
        db.commit()

    return {
        "status": "success",
        "records_before": total_before,
        "records_removed": records_removed,
        "total_records": len(df_unique),
        "organization_id": str(current_tenant.id)
    }

@router.post("/reset")
def reset_sales_data(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Clears raw sales data, forecasts, and model runs for the active organization workspace only.
    """
    from app.models.forecast import Forecast, ModelRun
    try:
        db.query(Forecast).filter(Forecast.tenant_id == current_tenant.id).delete()
        db.query(ModelRun).filter(ModelRun.tenant_id == current_tenant.id).delete()
        cleared = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).delete()
        db.commit()
        return {"status": "success", "records_cleared": cleared, "organization_id": str(current_tenant.id)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_status(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    count = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).count()
    min_date = db.query(func.min(RawSalesData.date)).filter(RawSalesData.tenant_id == current_tenant.id).scalar()
    max_date = db.query(func.max(RawSalesData.date)).filter(RawSalesData.tenant_id == current_tenant.id).scalar()
    return {
        "status": "ok",
        "total_raw_records": count,
        "min_date": format_date_safe(min_date),
        "max_date": format_date_safe(max_date),
        "organization_id": str(current_tenant.id),
        "organization_name": current_tenant.name
    }

@router.get("/preview")
def get_dataset_preview(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Returns comprehensive dataset inspection scoped to the active workspace.
    """
    base_query = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id)
    total_records = base_query.count()
    if total_records == 0:
        return {
            "has_data": False,
            "filename": f"No dataset loaded in {current_tenant.name}",
            "row_count": 0,
            "column_count": 0,
            "columns": [],
            "date_coverage": None,
            "product_count": 0,
            "category_count": 0,
            "missing_values": {},
            "sample_rows": [],
            "organization_id": str(current_tenant.id)
        }

    min_date = db.query(func.min(RawSalesData.date)).filter(RawSalesData.tenant_id == current_tenant.id).scalar()
    max_date = db.query(func.max(RawSalesData.date)).filter(RawSalesData.tenant_id == current_tenant.id).scalar()
    product_count = db.query(func.count(func.distinct(RawSalesData.sku))).filter(RawSalesData.tenant_id == current_tenant.id).scalar() or 0
    category_count = db.query(func.count(func.distinct(RawSalesData.category))).filter(RawSalesData.tenant_id == current_tenant.id).scalar() or 0

    span_days = None
    if min_date and max_date:
        d1 = min_date.date() if hasattr(min_date, 'date') else min_date
        d2 = max_date.date() if hasattr(max_date, 'date') else max_date
        try:
            span_days = (d2 - d1).days + 1
        except Exception:
            span_days = None

    null_order_id = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.order_id == None).count()
    null_product_name = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.product_name == None).count()
    null_category = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.category == None).count()
    null_sub_cat = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.sub_category == None).count()
    null_profit = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.profit == None).count()
    null_price = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.price == None).count()
    null_total_sales = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.total_sales == None).count()
    null_discount = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id, RawSalesData.discount_pct == None).count()

    columns = [
        {"name": "date", "type": "Date", "nullable": False, "description": "Transaction calendar date"},
        {"name": "order_id", "type": "String", "nullable": True, "description": "Unique order identifier"},
        {"name": "sku", "type": "String", "nullable": False, "description": "Product SKU code"},
        {"name": "product_name", "type": "String", "nullable": True, "description": "Item description or product name"},
        {"name": "category", "type": "String", "nullable": True, "description": "Primary product hierarchy / department"},
        {"name": "sub_category", "type": "String", "nullable": True, "description": "Secondary product group"},
        {"name": "units_sold", "type": "Integer", "nullable": False, "description": "Volume of units purchased"},
        {"name": "price", "type": "Numeric(10,2)", "nullable": True, "description": "Unit list price"},
        {"name": "total_sales", "type": "Numeric(12,2)", "nullable": True, "description": "Gross line-item sales amount"},
        {"name": "profit", "type": "Numeric(12,2)", "nullable": True, "description": "Net commercial gain or loss"},
        {"name": "discount_pct", "type": "Numeric(5,2)", "nullable": True, "description": "Promotional markdown rate"},
        {"name": "available_stock", "type": "Integer", "nullable": True, "description": "On-hand inventory level"}
    ]

    samples = db.query(RawSalesData).filter(RawSalesData.tenant_id == current_tenant.id).order_by(RawSalesData.id.asc()).limit(limit).all()
    sample_rows = []
    for r in samples:
        sample_rows.append({
            "id": r.id,
            "date": format_date_safe(r.date),
            "order_id": r.order_id or f"ORD-{r.id}",
            "sku": r.sku,
            "product_name": r.product_name or r.sku,
            "category": r.category or "N/A",
            "sub_category": r.sub_category or "N/A",
            "units_sold": r.units_sold,
            "price": float(r.price) if r.price is not None else None,
            "total_sales": float(r.total_sales) if r.total_sales is not None else (float(r.units_sold * (r.price or 0))),
            "profit": float(r.profit) if r.profit is not None else None,
            "discount_pct": float(r.discount_pct) if r.discount_pct is not None else None,
        })

    latest_filename = f"{current_tenant.name} Dataset"
    try:
        if os.path.exists("uploads"):
            files = [f for f in os.listdir("uploads") if f.endswith(".csv")]
            if files:
                files.sort(key=lambda x: os.path.getmtime(os.path.join("uploads", x)), reverse=True)
                raw_n = files[0]
                if "_" in raw_n and len(raw_n.split("_")[0]) == 32:
                    latest_filename = "_".join(raw_n.split("_")[1:])
                else:
                    latest_filename = raw_n
    except Exception:
        pass

    return {
        "has_data": True,
        "filename": latest_filename,
        "row_count": total_records,
        "column_count": len(columns),
        "columns": columns,
        "date_coverage": {
            "min_date": format_date_safe(min_date),
            "max_date": format_date_safe(max_date),
            "span_days": span_days
        },
        "product_count": product_count,
        "category_count": category_count,
        "missing_values": {
            "order_id": null_order_id,
            "product_name": null_product_name,
            "category": null_category,
            "sub_category": null_sub_cat,
            "profit": null_profit,
            "price": null_price,
            "total_sales": null_total_sales,
            "discount_pct": null_discount
        },
        "sample_rows": sample_rows,
        "organization_id": str(current_tenant.id),
        "organization_name": current_tenant.name
    }

@router.get("/products")
@router.get("/skus")
def get_available_products(
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default)
):
    """
    Returns unique products/SKUs present in the active organization workspace.
    """
    total_count = db.query(RawSalesData).filter(
        RawSalesData.status == "PROCESSED",
        RawSalesData.tenant_id == current_tenant.id
    ).count()
    dataset_min_date = db.query(func.min(RawSalesData.date)).filter(
        RawSalesData.status == "PROCESSED",
        RawSalesData.tenant_id == current_tenant.id
    ).scalar()
    dataset_max_date = db.query(func.max(RawSalesData.date)).filter(
        RawSalesData.status == "PROCESSED",
        RawSalesData.tenant_id == current_tenant.id
    ).scalar()
    
    query = db.query(
        func.coalesce(RawSalesData.product_name, RawSalesData.sku).label("p_name"),
        RawSalesData.sku,
        func.count(RawSalesData.id).label("count"),
        func.min(RawSalesData.date).label("p_min_date"),
        func.max(RawSalesData.date).label("p_max_date")
    ).filter(
        RawSalesData.status == "PROCESSED",
        RawSalesData.tenant_id == current_tenant.id
    )
    
    if search:
        s_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                RawSalesData.product_name.ilike(s_term),
                RawSalesData.sku.ilike(s_term)
            )
        )
        
    query = query.group_by(
        func.coalesce(RawSalesData.product_name, RawSalesData.sku),
        RawSalesData.sku
    ).order_by(func.count(RawSalesData.id).desc()).limit(limit)
    
    rows = query.all()
    
    name_occurrences = {}
    for r in rows:
        name_occurrences[r.p_name] = name_occurrences.get(r.p_name, 0) + 1
        
    result = []
    if not search and total_count > 0:
        result.append({
            "sku": "ALL",
            "product_name": "All Products (Global Aggregate)",
            "label": f"All Products (Global Aggregate) — {total_count} records",
            "count": total_count,
            "min_date": format_date_safe(dataset_min_date),
            "max_date": format_date_safe(dataset_max_date),
        })
        
    for r in rows:
        is_dup_name = name_occurrences.get(r.p_name, 0) > 1
        if is_dup_name and r.p_name != r.sku:
            label = f"{r.p_name} [SKU: {r.sku}] ({r.count} records)"
        elif r.p_name != r.sku:
            label = f"{r.p_name} ({r.count} records)"
        else:
            label = f"{r.sku} ({r.count} records)"
            
        result.append({
            "sku": r.sku,
            "product_name": r.p_name,
            "label": label,
            "count": r.count,
            "min_date": format_date_safe(r.p_min_date),
            "max_date": format_date_safe(r.p_max_date),
        })
        
    return result
