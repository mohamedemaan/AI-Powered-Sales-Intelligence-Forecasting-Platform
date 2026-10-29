import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Uuid, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import BaseModel


class RagDocument(BaseModel):
    """
    Represents an ingested knowledge base document in an isolated tenant workspace.
    Tracks original file storage, metadata, processing status, and chunk associations.
    """
    __tablename__ = "rag_documents"

    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, txt, md, csv, json
    checksum_sha256 = Column(String(64), nullable=False, index=True)
    status = Column(String(50), default="UPLOADED", nullable=False)  # UPLOADED, PROCESSING, INDEXED, FAILED, DELETING
    error_message = Column(Text, nullable=True)
    total_chunks = Column(Integer, default=0, nullable=False)
    metadata_json = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chunks = relationship("RagChunk", back_populates="document", cascade="all, delete-orphan")


class RagChunk(BaseModel):
    """
    Represents a discrete semantic text chunk extracted from a RagDocument.
    Preserves exact provenance (page, section), token counts, and serialized vector embeddings.
    """
    __tablename__ = "rag_chunks"

    document_id = Column(Uuid(as_uuid=True), ForeignKey("rag_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    embedding_json = Column(Text, nullable=True)  # JSON-serialized float vector array
    page_number = Column(Integer, nullable=True)
    section_title = Column(String(255), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    indexing_version = Column(Integer, default=1, nullable=False)
    metadata_json = Column(Text, nullable=True)

    # Relationships
    document = relationship("RagDocument", back_populates="chunks")

