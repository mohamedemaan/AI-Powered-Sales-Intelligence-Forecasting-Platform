from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Uuid, Text
from sqlalchemy.sql import func
from app.db.base import BaseModel


class DatasetVersion(BaseModel):
    """
    Represents an immutable dataset version in the multi-tenant cleaning workspace.
    Preserves exact original raw file paths and SHA-256 checksums alongside
    derived cleaned dataset assets.
    """
    __tablename__ = "dataset_versions"

    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    original_file_path = Column(String(500), nullable=False)
    cleaned_file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    format_type = Column(String(50), nullable=False)  # csv, tsv, xlsx, json, jsonl, parquet, text, image, audio, video
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PROFILING, CLEANED, FAILED, ACTIVATED
    row_count = Column(Integer, nullable=True)
    col_count = Column(Integer, nullable=True)
    is_active_for_analysis = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CleaningJob(BaseModel):
    """
    Tracks state, step execution, and validation telemetry of a 20-step data cleaning pipeline run.
    """
    __tablename__ = "cleaning_jobs"

    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Uuid(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=20, nullable=False)
    pipeline_config_json = Column(Text, nullable=True)
    validation_report_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class CleaningAuditLog(BaseModel):
    """
    Granular step-by-step audit record documenting every cleaning operation,
    affected fields, row deltas, and user-confirmed parameters.
    """
    __tablename__ = "cleaning_audit_logs"

    cleaning_job_id = Column(Uuid(as_uuid=True), ForeignKey("cleaning_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(Uuid(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=True, index=True)
    step_number = Column(Integer, nullable=False)
    step_name = Column(String(100), nullable=False)
    operation = Column(String(100), nullable=False)
    affected_fields = Column(String(255), nullable=True)
    rows_affected = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)  # APPLICABLE, SKIPPED, COMPLETED, WARNING, FAILED, NEEDS_REVIEW
    details_json = Column(Text, nullable=True)

