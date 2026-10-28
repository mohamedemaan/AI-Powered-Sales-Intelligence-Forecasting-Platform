from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DatasetVersionOut(BaseModel):
    id: str
    tenant_id: str
    name: str
    original_filename: str
    file_size: int
    mime_type: str
    format_type: str
    checksum_sha256: str
    status: str
    row_count: Optional[int] = None
    col_count: Optional[int] = None
    is_active_for_analysis: bool = False
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    total: int
    datasets: List[DatasetVersionOut]
    organization_id: str


class CleaningUploadResponse(BaseModel):
    status: str
    dataset_id: str
    filename: str
    format_type: str
    file_size: int
    checksum_sha256: str
    row_count: Optional[int] = None
    col_count: Optional[int] = None
    summary: Dict[str, Any] = Field(default_factory=dict)
    organization_id: str


class CleaningJobCreateRequest(BaseModel):
    pipeline_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CleaningJobOut(BaseModel):
    id: str
    dataset_version_id: str
    tenant_id: str
    status: str
    current_step: int
    total_steps: int
    error_message: Optional[str] = None
    validation_report: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CleaningAuditLogOut(BaseModel):
    id: str
    cleaning_job_id: str
    step_number: int
    step_name: str
    operation: str
    affected_fields: Optional[str] = None
    rows_affected: int = 0
    status: str
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

