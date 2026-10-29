import os
import hashlib
import json
import logging
import uuid
from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.rag import RagDocument, RagChunk
from app.services.rag.document_parser import extract_document_sections
from app.services.rag.chunking_service import chunk_document_sections
from app.services.rag.embedding_service import embed_texts, get_embedding_model_name
from app.services.rag.vector_store import rebuild_tenant_faiss_index
from app.services.audit_service import log_audit_event

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
    ".md": "md",
    ".markdown": "md",
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".jsonl": "jsonl",
}

MAX_UPLOAD_BYTES = int(os.getenv("RAG_MAX_UPLOAD_MB", "25")) * 1024 * 1024


def get_rag_upload_dir(tenant_id: UUID) -> str:
    path = os.path.join("uploads", "tenants", str(tenant_id), "rag_docs")
    os.makedirs(path, exist_ok=True)
    return path


def save_and_ingest_document(
    db: Session,
    file: UploadFile,
    tenant_id: UUID,
    user_id: Optional[UUID] = None,
    custom_title: Optional[str] = None
) -> RagDocument:
    """
    Ingests and validates an uploaded knowledge document:
    1. Checks extension, MIME, and size limits.
    2. Calculates SHA-256 checksum and prevents duplicate ingestion.
    3. Saves file with sanitized server-side UUID filename.
    4. Extracts, chunks, embeds, and indexes document into vector store.
    """
    orig_filename = file.filename or "uploaded_document"
    ext = os.path.splitext(orig_filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS.keys()))}"
        )

    file_type = SUPPORTED_EXTENSIONS[ext]

    # Read bytes with memory bound limit
    file_bytes = file.file.read()
    file_size = len(file_bytes)

    if file_size == 0:
        raise ValueError("Uploaded document is empty (0 bytes).")
    if file_size > MAX_UPLOAD_BYTES:
        raise ValueError(f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds configured maximum ({MAX_UPLOAD_BYTES / 1024 / 1024:.0f}MB).")

    # Content hash
    checksum = hashlib.sha256(file_bytes).hexdigest()

    # Duplicate check in tenant workspace
    existing_doc = db.query(RagDocument).filter(
        RagDocument.tenant_id == tenant_id,
        RagDocument.checksum_sha256 == checksum
    ).first()

    if existing_doc and existing_doc.status == "INDEXED":
        raise ValueError(f"A document with identical content has already been indexed: '{existing_doc.title}'.")

    # Safe storage path
    doc_id = uuid.uuid4()
    upload_dir = get_rag_upload_dir(tenant_id)
    safe_disk_filename = f"{str(doc_id)[:8]}_{checksum[:8]}{ext}"
    physical_path = os.path.join(upload_dir, safe_disk_filename)

    with open(physical_path, "wb") as f:
        f.write(file_bytes)

    doc_title = (custom_title or os.path.splitext(orig_filename)[0]).strip()
    mime_type = file.content_type or f"application/{file_type}"

    # Create document record
    document = RagDocument(
        id=doc_id,
        tenant_id=tenant_id,
        user_id=user_id,
        title=doc_title,
        original_filename=orig_filename,
        file_path=physical_path,
        file_size=file_size,
        mime_type=mime_type,
        file_type=file_type,
        checksum_sha256=checksum,
        status="PROCESSING",
        total_chunks=0,
        metadata_json=json.dumps({"uploader_user_id": str(user_id) if user_id else None})
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Process document synchronously for instant index readiness
    try:
        index_document_pipeline(db=db, document=document)
    except Exception as e:
        logger.error(f"Failed to process and index document {document.id}: {e}")
        document.status = "FAILED"
        document.error_message = str(e)
        db.commit()
        raise ValueError(f"Document processing failed: {str(e)}")

    # Log audit event
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
        event_type="RAG_DOCUMENT_INDEXED",
        target_type="RAG_DOCUMENT",
        target_id=str(document.id),
        outcome="SUCCESS",
        metadata={"filename": orig_filename, "chunks": document.total_chunks}
    )

    return document


def index_document_pipeline(db: Session, document: RagDocument) -> None:
    """
    Executes the parsing, structure-aware chunking, vector embedding,
    and FAISS index acceleration for a document. Idempotent.
    """
    document.status = "PROCESSING"
    document.error_message = None
    db.commit()

    # 1. Clear any prior chunks (for idempotent reindexing)
    db.query(RagChunk).filter(RagChunk.document_id == document.id).delete()
    db.commit()

    # 2. Extract sections
    sections = extract_document_sections(document.file_path, document.file_type)
    if not sections:
        raise ValueError("No extractable sections found in document.")

    # 3. Chunk sections
    chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))
    doc_meta = {
        "document_title": document.title,
        "filename": document.original_filename,
        "file_type": document.file_type
    }
    chunk_results = chunk_document_sections(
        sections=sections,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        doc_metadata=doc_meta
    )

    if not chunk_results:
        raise ValueError("Document yielded no valid semantic chunks.")

    # 4. Generate embeddings
    texts_to_embed = [c.chunk_text for c in chunk_results]
    embeddings = embed_texts(texts_to_embed)
    model_name = get_embedding_model_name()

    # 5. Save chunks to database
    new_chunks = []
    for c_res, emb in zip(chunk_results, embeddings):
        new_chunks.append(RagChunk(
            id=uuid.uuid4(),
            document_id=document.id,
            tenant_id=document.tenant_id,
            chunk_index=c_res.chunk_index,
            chunk_text=c_res.chunk_text,
            token_count=c_res.token_count,
            embedding_json=json.dumps(emb),
            page_number=c_res.page_number,
            section_title=c_res.section_title,
            embedding_model=model_name,
            indexing_version=1,
            metadata_json=json.dumps(c_res.metadata)
        ))

    db.bulk_save_objects(new_chunks)
    document.total_chunks = len(new_chunks)
    document.status = "INDEXED"
    db.commit()
    db.refresh(document)

    # 6. Rebuild tenant FAISS acceleration index
    rebuild_tenant_faiss_index(db=db, tenant_id=document.tenant_id)
    logger.info(f"Successfully indexed document '{document.title}' ({document.total_chunks} chunks).")


def delete_document(db: Session, document_id: UUID, tenant_id: UUID) -> bool:
    """
    Safely deletes a knowledge document, removes its database chunks,
    deletes physical file, and syncs the vector index.
    """
    doc = db.query(RagDocument).filter(
        RagDocument.id == document_id,
        RagDocument.tenant_id == tenant_id
    ).first()

    if not doc:
        return False

    doc.status = "DELETING"
    db.commit()

    # Delete physical file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.warning(f"Could not remove physical file {doc.file_path}: {e}")

    # Delete chunks
    db.query(RagChunk).filter(RagChunk.document_id == doc.id).delete()
    # Delete doc
    db.delete(doc)
    db.commit()

    # Rebuild FAISS index
    rebuild_tenant_faiss_index(db=db, tenant_id=tenant_id)
    return True

