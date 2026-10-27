import os
import shutil
import hashlib
import uuid
import json
import logging
from typing import Dict, Any, Tuple, Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import pandas as pd

from app.models.dataset import DatasetVersion
from app.models.tenant import Tenant
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    # Tabular
    ".csv": ("csv", "text/csv"),
    ".tsv": ("tsv", "text/tab-separated-values"),
    ".xlsx": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".xls": ("xlsx", "application/vnd.ms-excel"),
    ".json": ("json", "application/json"),
    ".jsonl": ("jsonl", "application/x-ndjson"),
    ".parquet": ("parquet", "application/vnd.apache.parquet"),
    # Text / Document
    ".txt": ("text", "text/plain"),
    ".md": ("text", "text/markdown"),
    ".xml": ("xml", "application/xml"),
    # Media
    ".png": ("image", "image/png"),
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".webp": ("image", "image/webp"),
    ".wav": ("audio", "audio/wav"),
    ".mp3": ("audio", "audio/mpeg"),
    ".mp4": ("video", "video/mp4"),
}

MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image", "image/png"),
    (b"\xff\xd8\xff", "image", "image/jpeg"),
    (b"RIFF", "audio", "audio/wav"),  # Also checked for WAVE in header
    (b"PAR1", "parquet", "application/vnd.apache.parquet"),
    (b"PK\x03\x04", "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    (b"%PDF", "document", "application/pdf"),
]


def detect_file_format(filename: str, header_bytes: bytes) -> Tuple[str, str]:
    """
    Identifies the canonical format and MIME type using file extension and magic byte validation.
    """
    ext = os.path.splitext(filename.lower())[1]
    
    # 1. Match against known magic signatures where applicable
    if len(header_bytes) >= 4:
        if header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image", "image/png"
        if header_bytes.startswith(b"\xff\xd8\xff"):
            return "image", "image/jpeg"
        if header_bytes.startswith(b"PAR1"):
            return "parquet", "application/vnd.apache.parquet"
        if header_bytes.startswith(b"PK\x03\x04") and ext in [".xlsx", ".xls"]:
            return "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if len(header_bytes) >= 12 and header_bytes.startswith(b"RIFF") and b"WAVE" in header_bytes[:12]:
            return "audio", "audio/wav"

    # 2. Match against supported file extension mapping
    if ext in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[ext]

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file format '{ext}'. Supported formats include CSV, TSV, XLSX, JSON, JSONL, Parquet, TXT, XML, PNG, JPG, WEBP, WAV, MP3, MP4."
    )


def extract_initial_profile(file_path: str, format_type: str) -> Tuple[Optional[int], Optional[int], Dict[str, Any]]:
    """
    Performs safe preliminary profiling on the uploaded raw file based on its detected format.
    Never mutates or writes to the file.
    """
    row_count: Optional[int] = None
    col_count: Optional[int] = None
    metadata: Dict[str, Any] = {"format_type": format_type}

    try:
        if format_type in ["csv", "tsv"]:
            sep = "\t" if format_type == "tsv" else ","
            for enc in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    df_sample = pd.read_csv(file_path, sep=sep, encoding=enc, nrows=100)
                    metadata["encoding"] = enc
                    break
                except UnicodeDecodeError:
                    continue
            else:
                df_sample = pd.read_csv(file_path, sep=sep, encoding_errors='replace', nrows=100)
                metadata["encoding"] = "utf-8 (lossy)"

            # Full row count scan
            try:
                full_df = pd.read_csv(file_path, sep=sep, encoding=metadata.get("encoding", "utf-8"), low_memory=False)
                row_count = len(full_df)
                col_count = len(full_df.columns)
                metadata["columns"] = list(full_df.columns)
                metadata["sample_dtypes"] = {col: str(dtype) for col, dtype in full_df.dtypes.items()}
            except Exception:
                row_count = len(df_sample)
                col_count = len(df_sample.columns)
                metadata["columns"] = list(df_sample.columns)

        elif format_type == "xlsx":
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            metadata["sheet_names"] = sheet_names
            first_sheet = sheet_names[0] if sheet_names else None
            if first_sheet:
                df_excel = pd.read_excel(file_path, sheet_name=first_sheet)
                row_count = len(df_excel)
                col_count = len(df_excel.columns)
                metadata["active_sheet"] = first_sheet
                metadata["columns"] = list(df_excel.columns)
                metadata["sample_dtypes"] = {col: str(dtype) for col, dtype in df_excel.dtypes.items()}

        elif format_type == "parquet":
            df_parquet = pd.read_parquet(file_path)
            row_count = len(df_parquet)
            col_count = len(df_parquet.columns)
            metadata["columns"] = list(df_parquet.columns)
            metadata["sample_dtypes"] = {col: str(dtype) for col, dtype in df_parquet.dtypes.items()}

        elif format_type in ["json", "jsonl"]:
            lines = (format_type == "jsonl")
            try:
                df_json = pd.read_json(file_path, lines=lines)
                row_count = len(df_json)
                col_count = len(df_json.columns)
                metadata["columns"] = list(df_json.columns)
                metadata["sample_dtypes"] = {col: str(dtype) for col, dtype in df_json.dtypes.items()}
            except Exception:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(5000)
                    metadata["sample_text"] = content[:500]

        elif format_type == "text":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                row_count = len(lines)
                col_count = 1
                metadata["line_count"] = len(lines)
                metadata["char_count"] = sum(len(l) for l in lines)

        elif format_type in ["image", "audio", "video"]:
            metadata["unstructured_media"] = True
            metadata["media_category"] = format_type

    except Exception as e:
        logger.warning(f"Preliminary profiling exception for {file_path}: {e}")
        metadata["profiling_error"] = str(e)

    return row_count, col_count, metadata


def save_and_register_upload(
    db: Session,
    file: UploadFile,
    tenant_id: Any,
    user_id: Optional[Any] = None,
    dataset_name: Optional[str] = None
) -> DatasetVersion:
    """
    Ingests an uploaded file with strict multi-tenant isolation, SHA-256 calculation,
    format detection, and immutable backup storage.
    """
    # 1. Sanitize original filename to prevent path traversal
    raw_filename = os.path.basename(file.filename or "uploaded_dataset")
    safe_token = uuid.uuid4().hex
    storage_filename = f"{safe_token}_{raw_filename}"

    # 2. Establish tenant-isolated directory structure
    tenant_dir = os.path.join("uploads", "tenants", str(tenant_id), "raw")
    os.makedirs(tenant_dir, exist_ok=True)
    destination_path = os.path.join(tenant_dir, storage_filename)

    # 3. Stream file to disk while calculating SHA-256 and capturing header bytes
    hasher = hashlib.sha256()
    file_size = 0
    header_bytes = b""

    with open(destination_path, "wb") as buffer:
        while True:
            chunk = file.file.read(64 * 1024)
            if not chunk:
                break
            if len(header_bytes) < 512:
                header_bytes += chunk[:512 - len(header_bytes)]
            hasher.update(chunk)
            file_size += len(chunk)
            buffer.write(chunk)

    if file_size == 0:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")

    checksum_sha256 = hasher.hexdigest()

    # 4. Detect format and MIME type
    format_type, mime_type = detect_file_format(raw_filename, header_bytes)

    # 5. Extract preliminary profile
    row_count, col_count, metadata = extract_initial_profile(destination_path, format_type)
    metadata["original_filename"] = raw_filename
    metadata["file_size_bytes"] = file_size
    metadata["checksum_sha256"] = checksum_sha256

    # 6. Create immutable DatasetVersion record
    effective_name = dataset_name.strip() if (dataset_name and dataset_name.strip()) else raw_filename
    dataset_version = DatasetVersion(
        tenant_id=tenant_id,
        user_id=user_id,
        name=effective_name,
        original_filename=raw_filename,
        original_file_path=destination_path,
        file_size=file_size,
        mime_type=mime_type,
        format_type=format_type,
        checksum_sha256=checksum_sha256,
        status="UPLOADED",
        row_count=row_count,
        col_count=col_count,
        is_active_for_analysis=False,
        metadata_json=json.dumps(metadata)
    )

    db.add(dataset_version)
    db.commit()
    db.refresh(dataset_version)

    # 7. Emit audit event
    try:
        actor_email = None
        if user_id:
            from app.models.user import User
            u = db.query(User).filter(User.id == user_id).first()
            actor_email = u.email if u else None

        log_audit_event(
            db=db,
            tenant_id=tenant_id,
            actor_id=user_id,
            actor_email=actor_email,
            event_type="DATASET_VERSION_UPLOADED",
            target_type="DATASET_VERSION",
            target_id=str(dataset_version.id),
            outcome="SUCCESS",
            metadata={
                "dataset_name": effective_name,
                "original_filename": raw_filename,
                "format_type": format_type,
                "file_size": file_size,
                "checksum_sha256": checksum_sha256,
                "row_count": row_count,
                "col_count": col_count
            }
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to emit audit event on upload: {e}")

    return dataset_version
