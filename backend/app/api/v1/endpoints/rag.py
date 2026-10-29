import os
import json
import logging
from typing import Optional, List, Any
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.tenant import Tenant
from app.models.rag import RagDocument, RagChunk
from app.schemas.rag import (
    RagDocumentOut,
    RagDocumentListResponse,
    RagChunkOut,
    RagDocumentDetailResponse,
    RagChatRequest,
    RagChatResponse,
    RagHealthResponse
)
from app.services.rag.document_service import (
    save_and_ingest_document,
    index_document_pipeline,
    delete_document
)
from app.services.rag.rag_service import execute_rag_chat
from app.services.rag.embedding_service import get_embedding_model_name
from app.services.rag.vector_store import FAISS_AVAILABLE, get_tenant_faiss_paths

from app.services.rag.sample_knowledge import seed_sample_policies_for_tenant

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/documents", response_model=RagDocumentOut, status_code=status.HTTP_201_CREATED)
def upload_rag_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Uploads and indexes an unstructured or semi-structured knowledge document
    (PDF, DOCX, TXT, MD, CSV, TSV, JSON) into the active tenant workspace.
    Enforces format validation, size quotas, duplicate hash detection,
    structure-aware chunking, vector embedding, and FAISS acceleration.
    """
    user_id = getattr(_rbac_check, "user_id", None)
    try:
        doc = save_and_ingest_document(
            db=db,
            file=file,
            tenant_id=current_tenant.id,
            user_id=user_id,
            custom_title=title
        )
        return RagDocumentOut(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id),
            title=doc.title,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            file_type=doc.file_type,
            status=doc.status,
            total_chunks=doc.total_chunks,
            error_message=doc.error_message,
            created_at=doc.created_at.isoformat() if doc.created_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error uploading RAG document: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ingest document: {str(e)}")


@router.get("/documents", response_model=RagDocumentListResponse)
def list_rag_documents(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Lists all indexed knowledge base documents authorized for the active organization workspace.
    """
    docs = db.query(RagDocument).filter(
        RagDocument.tenant_id == current_tenant.id
    ).order_by(RagDocument.created_at.desc()).all()

    items = [
        RagDocumentOut(
            id=str(d.id),
            tenant_id=str(d.tenant_id),
            title=d.title,
            original_filename=d.original_filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            file_type=d.file_type,
            status=d.status,
            total_chunks=d.total_chunks,
            error_message=d.error_message,
            created_at=d.created_at.isoformat() if d.created_at else None,
            updated_at=d.updated_at.isoformat() if d.updated_at else None
        )
        for d in docs
    ]

    return RagDocumentListResponse(
        total=len(items),
        documents=items,
        organization_id=str(current_tenant.id)
    )


@router.get("/documents/{document_id}", response_model=RagDocumentDetailResponse)
def get_rag_document_details(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Returns document metadata, indexing status, and sample semantic chunks.
    Enforces multi-tenant isolation.
    """
    doc = db.query(RagDocument).filter(
        RagDocument.id == document_id,
        RagDocument.tenant_id == current_tenant.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in active workspace.")

    chunks = db.query(RagChunk).filter(
        RagChunk.document_id == doc.id
    ).order_by(RagChunk.chunk_index.asc()).limit(50).all()

    chunk_outs = [
        RagChunkOut(
            id=str(c.id),
            document_id=str(c.document_id),
            chunk_index=c.chunk_index,
            chunk_text=c.chunk_text,
            token_count=c.token_count,
            page_number=c.page_number,
            section_title=c.section_title
        )
        for c in chunks
    ]

    doc_out = RagDocumentOut(
        id=str(doc.id),
        tenant_id=str(doc.tenant_id),
        title=doc.title,
        original_filename=doc.original_filename,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        file_type=doc.file_type,
        status=doc.status,
        total_chunks=doc.total_chunks,
        error_message=doc.error_message,
        created_at=doc.created_at.isoformat() if doc.created_at else None,
        updated_at=doc.updated_at.isoformat() if doc.updated_at else None
    )

    return RagDocumentDetailResponse(document=doc_out, chunks=chunk_outs)


@router.delete("/documents/{document_id}", status_code=status.HTTP_200_OK)
def delete_rag_document(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_admin)
):
    """
    Deletes a knowledge document, associated chunks, physical file, and syncs the vector index.
    Requires ADMIN or OWNER permissions.
    """
    success = delete_document(db=db, document_id=document_id, tenant_id=current_tenant.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in active workspace.")

    return {"status": "success", "message": "Document and associated vector chunks deleted successfully."}


@router.post("/documents/{document_id}/reindex", response_model=RagDocumentOut)
def reindex_rag_document(
    document_id: UUID,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Re-extracts, re-chunks, and re-embeds an existing document. Idempotent.
    """
    doc = db.query(RagDocument).filter(
        RagDocument.id == document_id,
        RagDocument.tenant_id == current_tenant.id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found in active workspace.")

    try:
        index_document_pipeline(db=db, document=doc)
        return RagDocumentOut(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id),
            title=doc.title,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            file_type=doc.file_type,
            status=doc.status,
            total_chunks=doc.total_chunks,
            error_message=doc.error_message,
            created_at=doc.created_at.isoformat() if doc.created_at else None,
            updated_at=doc.updated_at.isoformat() if doc.updated_at else None
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Reindexing failed: {str(e)}")


@router.post("/chat", response_model=RagChatResponse)
def ask_rag_knowledge_assistant(
    request: RagChatRequest,
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Submits an inquiry to the SalesMind AI Knowledge Assistant.
    Retrieves authorized evidence chunks, integrates verified SQL ledger analytics,
    invokes Gemini generation with citation grounding, and returns structured sources.
    """
    doc_uuid = None
    if request.document_id:
        try:
            doc_uuid = UUID(request.document_id.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid document_id UUID format.")

    try:
        response = execute_rag_chat(
            db=db,
            tenant_id=current_tenant.id,
            query=request.query,
            top_k=request.top_k or 4,
            similarity_threshold=request.similarity_threshold or 0.60,
            document_id=doc_uuid,
            sku=request.sku
        )
        return response
    except Exception as e:
        logger.error(f"Error in RAG chat: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"RAG query execution failed: {str(e)}")


@router.get("/health", response_model=RagHealthResponse)
def get_rag_health(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_viewer)
):
    """
    Public health check reporting RAG component status without exposing internal secrets or credentials.
    """
    total_docs = db.query(RagDocument).filter(RagDocument.tenant_id == current_tenant.id).count()
    total_chunks = db.query(RagChunk).filter(RagChunk.tenant_id == current_tenant.id).count()
    
    idx_path, _ = get_tenant_faiss_paths(current_tenant.id)
    faiss_active = FAISS_AVAILABLE and os.path.exists(idx_path)

    return RagHealthResponse(
        status="HEALTHY",
        vector_store="Dual-Layer FAISS + SQLite/PostgreSQL",
        embedding_model=get_embedding_model_name(),
        total_documents=total_docs,
        total_chunks=total_chunks,
        faiss_active=faiss_active
    )


@router.post("/seed-sample-knowledge", response_model=RagDocumentListResponse)
def seed_sample_knowledge(
    db: Session = Depends(deps.get_db),
    current_tenant: Tenant = Depends(deps.get_current_tenant_or_default),
    _rbac_check: Any = Depends(deps.require_analyst)
):
    """
    Seeds default corporate knowledge base documents (Sales Playbook, Return & Restocking Policies,
    Product Specifications) into the active tenant workspace.
    Idempotent: skips seeding if already present.
    """
    user_id = getattr(_rbac_check, "user_id", None)
    docs = seed_sample_policies_for_tenant(db=db, tenant_id=current_tenant.id, user_id=user_id)
    items = [
        RagDocumentOut(
            id=str(d.id),
            tenant_id=str(d.tenant_id),
            title=d.title,
            original_filename=d.original_filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            file_type=d.file_type,
            status=d.status,
            total_chunks=d.total_chunks,
            error_message=d.error_message,
            created_at=d.created_at.isoformat() if d.created_at else None,
            updated_at=d.updated_at.isoformat() if d.updated_at else None
        )
        for d in docs
    ]
    return RagDocumentListResponse(
        total=len(items),
        documents=items,
        organization_id=str(current_tenant.id)
    )

