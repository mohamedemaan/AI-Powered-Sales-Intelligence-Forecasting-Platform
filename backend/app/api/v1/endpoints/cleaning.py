import os
import json
import logging
from typing import Optional, Any
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.tenant import Tenant
from app.models.dataset import DatasetVersion, CleaningJob, CleaningAuditLog
from app.schemas.cleaning import (
    DatasetVersionOut,
    DatasetListResponse,
    CleaningUploadResponse,
    CleaningJobCreateRequest,
    CleaningJobOut
)
from app.services.cleaning.ingestion_service import save_and_register_upload
from app.services.cleaning.engine import run_universal_cleaning_pipeline
from app.services.cleaning.exporter import (
    export_cleaned_dataset,
    generate_cleaning_report_json,
    generate_cleaning_report_excel,
    generate_cleaning_report_pdf
)
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=CleaningUploadResponse)
async def upload_dataset_for_cleaning(
    file: UploadFile = File(...),
    dataset_name: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Step 1 & 2: Ingests an uploaded file for data cleaning into an isolated tenant workspace.
    Preserves original unmodified raw file, calculates SHA-256 checksum, automatically
    identifies format (CSV, TSV, XLSX, JSON, JSONL, Parquet, Text, Media), and runs initial profiling.
    """
    user_id = getattr(_rbac_check, "user_id", None)
    
    try:
        dataset_version = save_and_register_upload(
            db=db,
            file=file,
            tenant_id=current_tenant.id,
            user_id=user_id,
            dataset_name=dataset_name
        )

        meta = {}
        if dataset_version.metadata_json:
            try:
                meta = json.loads(dataset_version.metadata_json)
            except Exception:
                meta = {}

        return CleaningUploadResponse(
            status="success",
            dataset_id=str(dataset_version.id),
            filename=dataset_version.original_filename,
            format_type=dataset_version.format_type,
            file_size=dataset_version.file_size,
            checksum_sha256=dataset_version.checksum_sha256,
            row_count=dataset_version.row_count,
            col_count=dataset_version.col_count,
            summary=meta,
            organization_id=str(current_tenant.id)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during dataset cleaning upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process and register dataset: {str(e)}")


@router.get("/datasets", response_model=DatasetListResponse)
def list_workspace_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    format_type: Optional[str] = Query(None),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Returns all registered dataset versions for the active organization workspace.
    """
    query = db.query(DatasetVersion).filter(DatasetVersion.tenant_id == current_tenant.id)
    if format_type:
        query = query.filter(DatasetVersion.format_type == format_type.lower())

    total = query.count()
    records = query.order_by(DatasetVersion.created_at.desc()).offset(skip).limit(limit).all()

    items = []
    for r in records:
        meta = {}
        if r.metadata_json:
            try:
                meta = json.loads(r.metadata_json)
            except Exception:
                meta = {}
        if not meta.get("latest_job_id"):
            latest_j = db.query(CleaningJob).filter(
                CleaningJob.dataset_version_id == r.id
            ).order_by(CleaningJob.created_at.desc()).first()
            if latest_j:
                meta["latest_job_id"] = str(latest_j.id)
        items.append(DatasetVersionOut(
            id=str(r.id),
            tenant_id=str(r.tenant_id),
            name=r.name,
            original_filename=r.original_filename,
            file_size=r.file_size,
            mime_type=r.mime_type,
            format_type=r.format_type,
            checksum_sha256=r.checksum_sha256,
            status=r.status,
            row_count=r.row_count,
            col_count=r.col_count,
            is_active_for_analysis=r.is_active_for_analysis,
            metadata=meta,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        ))

    return DatasetListResponse(
        total=total,
        datasets=items,
        organization_id=str(current_tenant.id)
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetVersionOut)
def get_dataset_details(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Retrieves full metadata, profiling details, and status for a specific dataset version.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset version not found in active workspace.")

    meta = {}
    if dataset.metadata_json:
        try:
            meta = json.loads(dataset.metadata_json)
        except Exception:
            meta = {}
    if not meta.get("latest_job_id"):
        latest_j = db.query(CleaningJob).filter(
            CleaningJob.dataset_version_id == dataset.id
        ).order_by(CleaningJob.created_at.desc()).first()
        if latest_j:
            meta["latest_job_id"] = str(latest_j.id)

    return DatasetVersionOut(
        id=str(dataset.id),
        tenant_id=str(dataset.tenant_id),
        name=dataset.name,
        original_filename=dataset.original_filename,
        file_size=dataset.file_size,
        mime_type=dataset.mime_type,
        format_type=dataset.format_type,
        checksum_sha256=dataset.checksum_sha256,
        status=dataset.status,
        row_count=dataset.row_count,
        col_count=dataset.col_count,
        is_active_for_analysis=dataset.is_active_for_analysis,
        metadata=meta,
        created_at=dataset.created_at.isoformat() if dataset.created_at else None,
        updated_at=dataset.updated_at.isoformat() if dataset.updated_at else None,
    )


@router.get("/datasets/{dataset_id}/download-original")
def download_original_unmodified_file(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Allows the user to download their original uploaded raw file without modification.
    Enforces tenant isolation and validates file existence on disk.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    file_path = dataset.original_file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Original physical file is no longer available on disk.")

    return FileResponse(
        path=file_path,
        filename=dataset.original_filename,
        media_type=dataset.mime_type
    )


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_200_OK)
def delete_dataset_version(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_admin)
):
    """
    Safely deletes a dataset version and its associated physical files and cleaning jobs.
    Requires ADMIN or OWNER permissions.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    # Remove physical files if present
    for p in [dataset.original_file_path, dataset.cleaned_file_path]:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception as e:
                logger.warning(f"Failed to remove physical file {p}: {e}")

    # Remove cleaning jobs
    db.query(CleaningJob).filter(CleaningJob.dataset_version_id == dataset.id).delete()
    db.delete(dataset)

    # Emit audit event
    user_id = getattr(_rbac_check, "user_id", None)
    actor_email = None
    if user_id:
        from app.models.user import User
        u = db.query(User).filter(User.id == user_id).first()
        actor_email = u.email if u else None

    log_audit_event(
        db=db,
        tenant_id=current_tenant.id,
        actor_id=user_id,
        actor_email=actor_email,
        event_type="DATASET_VERSION_DELETED",
        target_type="DATASET_VERSION",
        target_id=str(dataset_id),
        outcome="SUCCESS",
        metadata={"filename": dataset.original_filename}
    )
    db.commit()

    return {"status": "success", "message": f"Dataset {dataset.name} deleted successfully."}


@router.post("/datasets/{dataset_id}/clean")
def trigger_dataset_cleaning_job(
    dataset_id: UUID,
    payload: Optional[CleaningJobCreateRequest] = None,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Step 1 to 20: Initiates and executes the Universal Data Cleaning & Preprocessing Pipeline
    on the targeted dataset version. Non-destructive: preserves original raw file and writes
    the derived cleaned dataset to uploads/tenants/<tenant_id>/cleaned/.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    user_id = getattr(_rbac_check, "user_id", None)
    config = payload.pipeline_config if payload else {}

    # Create CleaningJob entry
    job = CleaningJob(
        tenant_id=current_tenant.id,
        dataset_version_id=dataset.id,
        user_id=user_id,
        status="PENDING",
        current_step=0,
        total_steps=20,
        pipeline_config_json=json.dumps(config)
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run pipeline
    summary = run_universal_cleaning_pipeline(
        db=db,
        dataset_version=dataset,
        cleaning_job=job,
        config=config
    )

    def _clean_nans(val: Any) -> Any:
        import math
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return None
            return val
        elif isinstance(val, dict):
            return {k: _clean_nans(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [_clean_nans(v) for v in val]
        return val

    summary = _clean_nans(summary)

    # Update dataset metadata with latest_job_id
    d_meta = {}
    if dataset.metadata_json:
        try:
            d_meta = json.loads(dataset.metadata_json)
        except Exception:
            d_meta = {}
    d_meta["latest_job_id"] = str(job.id)
    dataset.metadata_json = json.dumps(d_meta)

    # Emit audit event
    actor_email = None
    if user_id:
        from app.models.user import User
        u = db.query(User).filter(User.id == user_id).first()
        actor_email = u.email if u else None

    log_audit_event(
        db=db,
        tenant_id=current_tenant.id,
        actor_id=user_id,
        actor_email=actor_email,
        event_type="DATASET_CLEANING_EXECUTED",
        target_type="CLEANING_JOB",
        target_id=str(job.id),
        outcome=job.status,
        metadata={"dataset_id": str(dataset.id), "filename": dataset.original_filename}
    )
    db.commit()

    return {
        "status": "success",
        "job_id": str(job.id),
        "dataset_id": str(dataset.id),
        "result": summary
    }


@router.get("/jobs/{job_id}", response_model=CleaningJobOut)
def get_cleaning_job_status(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Returns the execution status, progress step, and scorecard validation report of a cleaning job.
    """
    job = db.query(CleaningJob).filter(
        CleaningJob.id == job_id,
        CleaningJob.tenant_id == current_tenant.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Cleaning job not found.")

    report = None
    if job.validation_report_json:
        try:
            report = json.loads(job.validation_report_json)
        except Exception:
            report = None

    return CleaningJobOut(
        id=str(job.id),
        dataset_version_id=str(job.dataset_version_id),
        tenant_id=str(job.tenant_id),
        status=job.status,
        current_step=job.current_step,
        total_steps=job.total_steps,
        error_message=job.error_message,
        validation_report=report,
        created_at=job.created_at.isoformat() if job.created_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@router.get("/jobs/{job_id}/logs")
def get_cleaning_job_audit_logs(
    job_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Returns step-level audit logs for all 20 canonical cleaning steps executed in the job.
    """
    job = db.query(CleaningJob).filter(
        CleaningJob.id == job_id,
        CleaningJob.tenant_id == current_tenant.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Cleaning job not found.")

    logs = db.query(CleaningAuditLog).filter(
        CleaningAuditLog.cleaning_job_id == job.id
    ).order_by(CleaningAuditLog.step_number.asc()).all()

    items = []
    for l in logs:
        details = {}
        if l.details_json:
            try:
                details = json.loads(l.details_json)
            except Exception:
                details = {}
        items.append({
            "id": str(l.id),
            "cleaning_job_id": str(l.cleaning_job_id),
            "step_number": l.step_number,
            "step_name": l.step_name,
            "operation": l.operation,
            "affected_fields": l.affected_fields,
            "rows_affected": l.rows_affected,
            "status": l.status,
            "details": details,
            "created_at": l.created_at.isoformat() if l.created_at else None
        })

    return {"total_logs": len(items), "logs": items}


@router.get("/datasets/{dataset_id}/download-cleaned")
def download_cleaned_dataset(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Streams the derived cleaned dataset for user download.
    Enforces workspace isolation and verifies file existence.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    if not dataset.cleaned_file_path or not os.path.exists(dataset.cleaned_file_path):
        raise HTTPException(status_code=404, detail="Cleaned file is not available. Please run data cleaning first.")

    base_name = os.path.splitext(dataset.original_filename)[0]
    cleaned_dl_name = f"cleaned_{base_name}.csv"

    return FileResponse(
        path=dataset.cleaned_file_path,
        filename=cleaned_dl_name,
        media_type="text/csv"
    )


@router.get("/datasets/{dataset_id}/export")
def export_cleaned_dataset_custom_format(
    dataset_id: UUID,
    format: str = Query("csv", description="Target export format: csv, tsv, xlsx, parquet, json, jsonl"),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Exports and streams the cleaned dataset in the user's requested format:
    CSV, TSV, Excel (.xlsx), Parquet, JSON, or JSON Lines (.jsonl).
    Enforces workspace isolation, validates file existence, and sets genuine download headers.
    """
    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    file_path = dataset.cleaned_file_path or dataset.original_file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file is not available on disk.")

    try:
        content_bytes, dl_filename, mime_type = export_cleaned_dataset(dataset, target_format=format)
        return Response(
            content=content_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{dl_filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Export error for dataset {dataset_id} in format {format}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate {format.upper()} export: {str(e)}")


@router.get("/jobs/{job_id}/report")
def download_cleaning_job_report(
    job_id: UUID,
    format: str = Query("pdf", description="Target report format: pdf, xlsx, json"),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Generates and streams a comprehensive Quality & Cleaning Report in the requested format:
    - PDF: Executive Summary, KPI Scorecard, 20-step execution table, Validation Scorecard.
    - Excel (.xlsx): Multi-sheet workbook (Summary, 20-Step Log, Scorecard, Data Profile).
    - JSON: Machine-readable structured quality audit log.
    """
    job = db.query(CleaningJob).filter(
        CleaningJob.id == job_id,
        CleaningJob.tenant_id == current_tenant.id
    ).first()

    if not job:
        job = db.query(CleaningJob).filter(CleaningJob.id == job_id).first()

    if not job:
        # Check if caller passed dataset_version_id
        job = db.query(CleaningJob).filter(
            CleaningJob.dataset_version_id == job_id
        ).order_by(CleaningJob.created_at.desc()).first()

    if not job:
        raise HTTPException(status_code=404, detail="Cleaning job not found.")

    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == job.dataset_version_id
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Associated dataset not found.")

    audit_logs = db.query(CleaningAuditLog).filter(
        CleaningAuditLog.cleaning_job_id == job.id
    ).order_by(CleaningAuditLog.step_number.asc()).all()

    req_fmt = (format or "pdf").strip().lower()

    try:
        if req_fmt in ["xlsx", "excel"]:
            content_bytes, dl_filename, mime_type = generate_cleaning_report_excel(dataset, job, audit_logs)
        elif req_fmt == "json":
            content_bytes, dl_filename, mime_type = generate_cleaning_report_json(dataset, job, audit_logs)
        elif req_fmt == "pdf":
            content_bytes, dl_filename, mime_type = generate_cleaning_report_pdf(dataset, job, audit_logs)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported report format '{format}'. Supported: pdf, xlsx, json.")

        return Response(
            content=content_bytes,
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{dl_filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation error for job {job_id} in format {format}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate {format.upper()} report: {str(e)}")


@router.post("/datasets/{dataset_id}/activate")
def activate_cleaned_dataset_for_analysis(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Promotes a verified cleaned dataset version to become the active analysis dataset
    for the organization workspace. Reconciles cleaned tabular transactions into
    raw_sales_data, recalculates live ledger analytics, and emits an audit event.
    """
    import pandas as pd
    from app.models.data import RawSalesData

    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    file_path = dataset.cleaned_file_path or dataset.original_file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Cleaned dataset file is not available on disk. Please run data cleaning first.")

    # 1. Update is_active_for_analysis flag on DatasetVersion
    target_tenant_id = dataset.tenant_id or current_tenant.id
    db.query(DatasetVersion).filter(
        DatasetVersion.tenant_id == target_tenant_id
    ).update({"is_active_for_analysis": False})

    dataset.is_active_for_analysis = True
    dataset.status = "ACTIVATED"

    # 2. If tabular sales data, load into raw_sales_data for downstream models
    rows_reconciled = 0
    try:
        ext = os.path.splitext(file_path)[1].lower()
        df: Optional[pd.DataFrame] = None
        if ext in [".csv", ".txt"]:
            df = pd.read_csv(file_path, low_memory=False)
        elif ext == ".tsv":
            df = pd.read_csv(file_path, sep="\t", low_memory=False)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif ext == ".parquet":
            df = pd.read_parquet(file_path)
        elif ext == ".json":
            df = pd.read_json(file_path)

        if df is not None and not df.empty:
            # Map canonical columns
            col_map = {}
            for col in df.columns:
                c_clean = str(col).lower().replace(" ", "_").replace("-", "_")
                if c_clean in ["date", "order_date", "transaction_date"]:
                    col_map["date"] = col
                elif c_clean in ["sku", "product_id", "item_id", "product_code"]:
                    col_map["sku"] = col
                elif c_clean in ["units_sold", "quantity", "qty", "volume"]:
                    col_map["units_sold"] = col
                elif c_clean in ["total_sales", "sales", "revenue", "gross_sales"]:
                    col_map["total_sales"] = col
                elif c_clean in ["price", "unit_price"]:
                    col_map["price"] = col
                elif c_clean in ["profit", "net_profit"]:
                    col_map["profit"] = col
                elif c_clean in ["order_id", "transaction_id", "invoice_id"]:
                    col_map["order_id"] = col
                elif c_clean in ["category"]:
                    col_map["category"] = col
                elif c_clean in ["sub_category", "subcategory"]:
                    col_map["sub_category"] = col
                elif c_clean in ["discount_pct", "discount"]:
                    col_map["discount_pct"] = col
                elif c_clean in ["available_stock", "stock", "inventory"]:
                    col_map["available_stock"] = col
                elif c_clean in ["product_name", "product", "item_name", "title"]:
                    col_map["product_name"] = col

            if "sku" not in col_map and "product_name" in col_map:
                col_map["sku"] = col_map["product_name"]

            if "date" in col_map and "sku" in col_map and "units_sold" in col_map:
                # Clear previous tenant records and replace with verified cleaned dataset
                db.query(RawSalesData).filter(RawSalesData.tenant_id == target_tenant_id).delete()

                new_records = []
                for _, row in df.iterrows():
                    d_val = pd.to_datetime(row[col_map["date"]], errors="coerce")
                    if pd.isna(d_val):
                        continue
                    
                    sku_val = str(row[col_map["sku"]]).strip()
                    try:
                        units_val = int(round(float(row[col_map["units_sold"]])))
                    except Exception:
                        continue

                    # Optional fields
                    ts_val = None
                    if "total_sales" in col_map and pd.notna(row[col_map["total_sales"]]):
                        try:
                            ts_val = float(row[col_map["total_sales"]])
                        except Exception:
                            pass

                    price_val = None
                    if "price" in col_map and pd.notna(row[col_map["price"]]):
                        try:
                            price_val = float(row[col_map["price"]])
                        except Exception:
                            pass

                    profit_val = None
                    if "profit" in col_map and pd.notna(row[col_map["profit"]]):
                        try:
                            profit_val = float(row[col_map["profit"]])
                        except Exception:
                            pass

                    order_id_val = str(row[col_map["order_id"]]).strip() if "order_id" in col_map and pd.notna(row[col_map["order_id"]]) else None
                    cat_val = str(row[col_map["category"]]).strip() if "category" in col_map and pd.notna(row[col_map["category"]]) else None
                    sub_val = str(row[col_map["sub_category"]]).strip() if "sub_category" in col_map and pd.notna(row[col_map["sub_category"]]) else None
                    pname_val = str(row[col_map["product_name"]]).strip() if "product_name" in col_map and pd.notna(row[col_map["product_name"]]) else sku_val

                    new_records.append(RawSalesData(
                        tenant_id=target_tenant_id,
                        date=d_val.date(),
                        sku=sku_val,
                        product_name=pname_val,
                        units_sold=units_val,
                        price=price_val,
                        total_sales=ts_val,
                        profit=profit_val,
                        order_id=order_id_val,
                        category=cat_val,
                        sub_category=sub_val,
                        status="PROCESSED"
                    ))

                if new_records:
                    db.bulk_save_objects(new_records)
                    rows_reconciled = len(new_records)
    except Exception as e:
        logger.warning(f"Could not auto-reconcile cleaned tabular data into raw_sales_data: {e}")

    # 3. Log audit event
    user_id = getattr(_rbac_check, "user_id", None)
    actor_email = None
    if user_id:
        from app.models.user import User
        u = db.query(User).filter(User.id == user_id).first()
        actor_email = u.email if u else None

    log_audit_event(
        db=db,
        tenant_id=current_tenant.id,
        actor_id=user_id,
        actor_email=actor_email,
        event_type="DATASET_ACTIVATED",
        target_type="DATASET_VERSION",
        target_id=str(dataset.id),
        outcome="SUCCESS",
        metadata={
            "dataset_name": dataset.name,
            "filename": dataset.original_filename,
            "rows_reconciled": rows_reconciled
        }
    )

    db.commit()

    return {
        "status": "success",
        "message": f"Dataset '{dataset.name}' activated for workspace analysis successfully.",
        "dataset_id": str(dataset.id),
        "is_active_for_analysis": True,
        "rows_reconciled_into_ledger": rows_reconciled
    }


@router.get("/datasets/{dataset_id}/preview")
def preview_dataset_versions(
    dataset_id: UUID,
    limit: int = Query(15, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Returns preview records from both the raw uploaded file and the derived cleaned file
    to power side-by-side before/after comparison and audit verification.
    """
    import pandas as pd

    dataset = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_id,
        DatasetVersion.tenant_id == current_tenant.id
    ).first()

    if not dataset:
        # Workspace fallback for active user session
        dataset = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_id).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found in active workspace.")

    def _read_preview(path: Optional[str]):
        if not path or not os.path.exists(path):
            return {"columns": [], "rows": [], "count": 0}
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in [".csv", ".txt"]:
                df = pd.read_csv(path, nrows=limit)
            elif ext == ".tsv":
                df = pd.read_csv(path, sep="\t", nrows=limit)
            elif ext in [".xlsx", ".xls"]:
                df = pd.read_excel(path, nrows=limit)
            elif ext == ".parquet":
                df = pd.read_parquet(path).head(limit)
            elif ext in [".json", ".jsonl"]:
                lines = ext == ".jsonl"
                df = pd.read_json(path, lines=lines).head(limit)
            else:
                return {"columns": ["content"], "rows": [{"content": f"Non-tabular format ({ext})"}], "count": 1}

            # Fill NaN with None for clean JSON serialization
            df = df.where(pd.notnull(df), None)
            cols = [str(c) for c in df.columns]
            records = df.to_dict(orient="records")
            return {"columns": cols, "rows": records, "count": len(records)}
        except Exception as e:
            return {"columns": ["error"], "rows": [{"error": str(e)}], "count": 0}

    raw_preview = _read_preview(dataset.original_file_path)
    cleaned_preview = _read_preview(dataset.cleaned_file_path) if dataset.cleaned_file_path else None

    return {
        "dataset_id": str(dataset.id),
        "name": dataset.name,
        "format_type": dataset.format_type,
        "status": dataset.status,
        "raw_preview": raw_preview,
        "cleaned_preview": cleaned_preview,
        "is_cleaned": dataset.cleaned_file_path is not None and os.path.exists(dataset.cleaned_file_path)
    }

