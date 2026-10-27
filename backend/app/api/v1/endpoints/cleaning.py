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
