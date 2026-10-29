import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.rag import RagChunk, RagDocument
from app.services.rag.embedding_service import EMBEDDING_DIM

logger = logging.getLogger(__name__)

# Check if faiss is available
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


def get_tenant_vector_dir(tenant_id: UUID) -> str:
    """
    Returns the persistent directory for a tenant's vector acceleration index.
    """
    base_dir = os.path.join("uploads", "tenants", str(tenant_id), "vector_index")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_tenant_faiss_paths(tenant_id: UUID) -> Tuple[str, str]:
    v_dir = get_tenant_vector_dir(tenant_id)
    index_path = os.path.join(v_dir, "index.faiss")
    mapping_path = os.path.join(v_dir, "chunk_ids.json")
    return index_path, mapping_path


def rebuild_tenant_faiss_index(db: Session, tenant_id: UUID) -> bool:
    """
    Synchronizes and rebuilds the on-disk FAISS index for a tenant from the persistent
    SQL database chunks (ACID single source of truth).
    """
    if not FAISS_AVAILABLE:
        return False

    index_path, mapping_path = get_tenant_faiss_paths(tenant_id)

    # 1. Fetch all active chunks for this tenant
    chunks = db.query(RagChunk).filter(
        RagChunk.tenant_id == tenant_id,
        RagChunk.embedding_json.isnot(None)
    ).order_by(RagChunk.created_at.asc()).all()

    if not chunks:
        # Clear index files if no chunks remain
        if os.path.exists(index_path):
            try:
                os.remove(index_path)
            except Exception:
                pass
        if os.path.exists(mapping_path):
            try:
                os.remove(mapping_path)
            except Exception:
                pass
        return True

    # 2. Assemble vector matrix
    vectors: List[List[float]] = []
    chunk_ids: List[str] = []

    for c in chunks:
        try:
            emb = json.loads(c.embedding_json)
            if isinstance(emb, list) and len(emb) == EMBEDDING_DIM:
                vectors.append(emb)
                chunk_ids.append(str(c.id))
        except Exception:
            continue

    if not vectors:
        return True

    try:
        arr = np.array(vectors, dtype=np.float32)
        # Normalize vectors for cosine similarity via Inner Product
        faiss.normalize_L2(arr)

        index = faiss.IndexFlatIP(EMBEDDING_DIM)
        index.add(arr)

        # Write index to disk
        faiss.write_index(index, index_path)
        with open(mapping_path, "w", encoding="utf-8") as f:
            json.dump(chunk_ids, f)

        logger.info(f"Rebuilt FAISS index for tenant {tenant_id} with {len(chunk_ids)} vectors.")
        return True
    except Exception as e:
        logger.error(f"Failed to build FAISS index for tenant {tenant_id}: {e}")
        return False


def search_tenant_vectors(
    db: Session,
    tenant_id: UUID,
    query_vector: List[float],
    top_k: int = 4,
    similarity_threshold: float = 0.60,
    document_id: Optional[UUID] = None
) -> List[Tuple[RagChunk, float]]:
    """
    Performs fast, multi-tenant vector similarity search:
    1. Attempts accelerated FAISS index lookup.
    2. Falls back to pure NumPy cosine similarity over SQL records if FAISS is unindexed or unavailable.
    Filters by similarity_threshold and document_id if supplied.
    """
    if not query_vector:
        return []

    q_arr = np.array([query_vector], dtype=np.float32)
    # L2 normalize query
    norm = np.linalg.norm(q_arr)
    if norm > 1e-9:
        q_arr = q_arr / norm

    index_path, mapping_path = get_tenant_faiss_paths(tenant_id)
    use_faiss = FAISS_AVAILABLE and os.path.exists(index_path) and os.path.exists(mapping_path)

    if use_faiss:
        try:
            index = faiss.read_index(index_path)
            with open(mapping_path, "r", encoding="utf-8") as f:
                chunk_ids: List[str] = json.load(f)

            if index.ntotal > 0 and len(chunk_ids) == index.ntotal:
                # Search FAISS (Inner Product on normalized vectors = Cosine Similarity)
                # Request extra k in case document_id filter is applied
                fetch_k = min(index.ntotal, top_k * 3)
                scores, indices = index.search(q_arr, fetch_k)

                matched_chunks: List[Tuple[RagChunk, float]] = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx < 0 or idx >= len(chunk_ids):
                        continue
                    sim_score = float(score)
                    if sim_score < similarity_threshold:
                        continue

                    c_id = chunk_ids[idx]
                    chunk = db.query(RagChunk).filter(RagChunk.id == UUID(c_id)).first()
                    if not chunk:
                        continue

                    # Filter by document_id if requested
                    if document_id and chunk.document_id != document_id:
                        continue

                    matched_chunks.append((chunk, round(sim_score, 4)))
                    if len(matched_chunks) >= top_k:
                        break

                return matched_chunks
        except Exception as e:
            logger.warning(f"FAISS search failed, falling back to NumPy: {e}")

    # Pure NumPy Exact Fallback
    query = db.query(RagChunk).filter(
        RagChunk.tenant_id == tenant_id,
        RagChunk.embedding_json.isnot(None)
    )
    if document_id:
        query = query.filter(RagChunk.document_id == document_id)

    db_chunks = query.all()
    if not db_chunks:
        return []

    vectors: List[List[float]] = []
    valid_chunks: List[RagChunk] = []

    for c in db_chunks:
        try:
            emb = json.loads(c.embedding_json)
            if isinstance(emb, list) and len(emb) == EMBEDDING_DIM:
                vectors.append(emb)
                valid_chunks.append(c)
        except Exception:
            continue

    if not vectors:
        return []

    mat = np.array(vectors, dtype=np.float32)
    # Normalize rows
    row_norms = np.linalg.norm(mat, axis=1, keepdims=True)
    row_norms[row_norms < 1e-9] = 1.0
    mat = mat / row_norms

    # Cosine similarities = dot product
    sims = np.dot(mat, q_arr.T).flatten()

    results: List[Tuple[RagChunk, float]] = []
    # Sort descending
    top_indices = np.argsort(-sims)
    for idx in top_indices:
        score = float(sims[idx])
        if score < similarity_threshold:
            break
        results.append((valid_chunks[idx], round(score, 4)))
        if len(results) >= top_k:
            break

    return results

