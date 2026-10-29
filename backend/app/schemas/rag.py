from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RagDocumentOut(BaseModel):
    id: str
    tenant_id: str
    title: str
    original_filename: str
    file_size: int
    mime_type: str
    file_type: str
    status: str
    total_chunks: int
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class RagDocumentListResponse(BaseModel):
    total: int
    documents: List[RagDocumentOut]
    organization_id: str


class RagChunkOut(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    chunk_text: str
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None

    class Config:
        from_attributes = True


class RagDocumentDetailResponse(BaseModel):
    document: RagDocumentOut
    chunks: List[RagChunkOut]


class RagCitation(BaseModel):
    citation_id: str
    document_id: str
    document_title: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    snippet: str
    similarity_score: float


class RagChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = Field(default=4, ge=1, le=20)
    similarity_threshold: Optional[float] = Field(default=0.60, ge=0.0, le=1.0)
    document_id: Optional[str] = None
    sku: Optional[str] = None


class RagChatResponse(BaseModel):
    query: str
    answer: str
    intent: str  # KNOWLEDGE, LEDGER_ANALYTICS, HYBRID
    has_sufficient_context: bool
    citations: List[RagCitation] = Field(default_factory=list)
    model: str
    execution_time_ms: float
    grounded_evidence: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RagHealthResponse(BaseModel):
    status: str
    vector_store: str
    embedding_model: str
    total_documents: int
    total_chunks: int
    faiss_active: bool

