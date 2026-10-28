import os
import json
import logging
from typing import Optional, Any
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, status
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
        raise HTTPException(status_code=404, detail="Dataset version not found in active workspace.")

    meta = {}
    if dataset.metadata_json:
        try:
            meta = json.loads(dataset.metadata_json)
        except Exception:
            meta = {}

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
