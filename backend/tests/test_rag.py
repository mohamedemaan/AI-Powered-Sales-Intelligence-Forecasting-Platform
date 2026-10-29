import io
import uuid
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant, TenantMember
from app.models.user import User
from app.models.rag import RagDocument, RagChunk
from app.models.data import RawSalesData
from app.core.security import create_access_token
from app.services.rag.document_parser import (
    parse_text_markdown_document,
    parse_csv_tsv_document,
    parse_json_document,
    extract_document_sections
)
from app.services.rag.chunking_service import (
    recursive_split_text,
    chunk_document_sections,
    estimate_token_count
)
from app.services.rag.embedding_service import (
    generate_deterministic_fallback_embedding,
    embed_texts,
    embed_single_query,
    EMBEDDING_DIM
)
from app.services.rag.hybrid_router import classify_user_intent
from app.services.rag.vector_store import (
    rebuild_tenant_faiss_index,
    search_tenant_vectors
)

client = TestClient(app)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_tenant_rag(db_session: Session):
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()

    tenant = Tenant(
        id=t_id,
        name="RAG Enterprise Workspace",
        slug=f"rag-{str(t_id)[:8]}",
        subscription_tier="PRO",
        subscription_status="ACTIVE",
        owner_id=u_id
    )
    user = User(
        id=u_id,
        email=f"rag_admin_{str(u_id)[:8]}@salesmind.ai",
        username=f"rag_admin_{str(u_id)[:8]}",
        password_hash="fakehashedpassword",
        is_active=True,
        tenant_id=t_id
    )
    membership = TenantMember(
        tenant_id=t_id,
        user_id=u_id,
        role="OWNER"
    )
    db_session.add(tenant)
    db_session.add(user)
    db_session.add(membership)
    db_session.commit()

    token = create_access_token(subject=str(u_id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(t_id)
    }

    return {"tenant": tenant, "user": user, "headers": headers, "token": token}


# ==========================================
# 1. UNIT TESTS: Document Parsers & Chunking
# ==========================================

def test_recursive_split_text():
    sample_text = (
        "# Sales Return Policy\n\n"
        "Customers may return unopened items within 30 days of purchase for a full refund.\n\n"
        "All returned merchandise must be accompanied by the original receipt or order confirmation email. "
        "Items returned after 30 days are subject to a 15% restocking fee.\n\n"
        "## Damaged Goods\n\n"
        "If goods arrive in damaged condition, notify support within 48 hours for immediate replacement."
    )
    chunks = recursive_split_text(sample_text, max_chunk_size=150, overlap=30)
    assert len(chunks) >= 2
    assert all(len(c) <= 150 for c in chunks)
    assert any("Sales Return Policy" in c for c in chunks)


def test_chunk_document_sections_preserves_metadata():
    from app.services.rag.document_parser import ParsedSection
    sections = [
        ParsedSection(
            text="Executive Policy Header. Section 1 outlines guidelines for discount approvals exceeding 20 percent.",
            page_number=1,
            section_title="Discount Approvals"
        ),
        ParsedSection(
            text="Section 2: Inventory reorder points must be audited weekly across fulfillment centers.",
            page_number=2,
            section_title="Inventory Controls"
        )
    ]
    chunks = chunk_document_sections(sections, chunk_size=300, chunk_overlap=50)
    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].section_title == "Discount Approvals"
    assert chunks[1].page_number == 2
    assert chunks[1].section_title == "Inventory Controls"
    assert chunks[0].token_count > 0


def test_csv_parser_structured_sections(tmp_path):
    csv_file = tmp_path / "test_policy.csv"
    csv_file.write_text("Policy ID,Category,Rule Description\nPOL-01,Returns,30-day window\nPOL-02,Shipping,Free over $50\n", encoding="utf-8")
    sections = extract_document_sections(str(csv_file), "csv")
    assert len(sections) >= 2
    assert "Columns: Policy ID, Category, Rule Description" in sections[0].text
    assert "POL-01" in sections[1].text


def test_json_parser_structured_sections(tmp_path):
    json_file = tmp_path / "catalog.json"
    json_file.write_text(json.dumps([{"sku": "TEC-01", "name": "Phone", "warranty_months": 24}]), encoding="utf-8")
    sections = extract_document_sections(str(json_file), "json")
    assert len(sections) >= 2
    assert "warranty_months" in sections[1].text


# ==========================================
# 2. UNIT TESTS: Embeddings & Vector Search
# ==========================================

def test_deterministic_embedding_adapter():
    vec1 = generate_deterministic_fallback_embedding("Return policy within 30 days for electronics")
    vec2 = generate_deterministic_fallback_embedding("Return policy within 30 days for electronics")
    vec3 = generate_deterministic_fallback_embedding("Completely unrelated quantum astronomy mechanics")

    assert len(vec1) == EMBEDDING_DIM
    assert vec1 == vec2, "Deterministic embedding must be reproducible"
    
    # Check L2 unit norm
    import math
    norm1 = math.sqrt(sum(x * x for x in vec1))
    assert abs(norm1 - 1.0) < 1e-4

    # Dot product similarity (Cosine similarity of normalized vectors)
    sim_same = sum(a * b for a, b in zip(vec1, vec2))
    sim_diff = sum(a * b for a, b in zip(vec1, vec3))
    assert abs(sim_same - 1.0) < 1e-4
    assert sim_diff < sim_same


def test_hybrid_intent_classification():
    assert classify_user_intent("What is our sales return policy?") == "KNOWLEDGE"
    assert classify_user_intent("What is the total revenue and distinct orders?") == "LEDGER_ANALYTICS"
    assert classify_user_intent("Why did revenue decrease, and what does our sales policy say?") == "HYBRID"


# ==========================================
# 3. END-TO-END API TESTS
# ==========================================

def test_rag_document_upload_and_indexing(client, auth_tenant_rag, db_session):
    headers = auth_tenant_rag["headers"]

    doc_content = (
        "# Sales Operating Procedure 2026\n\n"
        "## Section 1: Pricing and Bulk Discounts\n"
        "Orders over 100 units qualify for an automatic 15 percent wholesale discount.\n"
        "Approval from the Sales Director is required for any commercial discount exceeding 25 percent.\n\n"
        "## Section 2: Returns and RMA Process\n"
        "All hardware returns must be submitted within 30 calendar days.\n"
        "Restocking fees of $25 apply to opened items missing original packaging."
    )

    files = {"file": ("sales_sop.md", io.BytesIO(doc_content.encode("utf-8")), "text/markdown")}
    res = client.post("/api/v1/rag/documents", files=files, data={"title": "Sales SOP 2026"}, headers=headers)
    assert res.status_code == 201, res.text
    doc_data = res.json()
    assert doc_data["status"] == "INDEXED"
    assert doc_data["total_chunks"] >= 2
    assert doc_data["file_type"] == "md"
    doc_id = doc_data["id"]

    # 2. List documents
    list_res = client.get("/api/v1/rag/documents", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # 3. Document Details
    detail_res = client.get(f"/api/v1/rag/documents/{doc_id}", headers=headers)
    assert detail_res.status_code == 200
    details = detail_res.json()
    assert len(details["chunks"]) >= 2
    assert any("wholesale discount" in c["chunk_text"] for c in details["chunks"])

    # 4. Ask RAG Knowledge Assistant (Grounded Query)
    chat_payload = {
        "query": "What is the policy for wholesale discounts on orders over 100 units?",
        "top_k": 3,
        "similarity_threshold": 0.30
    }
    chat_res = client.post("/api/v1/rag/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200, chat_res.text
    chat_data = chat_res.json()
    assert chat_data["has_sufficient_context"] is True
    assert len(chat_data["citations"]) > 0
    assert "wholesale discount" in chat_data["answer"].lower() or "15" in chat_data["answer"]
    assert chat_data["citations"][0]["document_title"] == "Sales SOP 2026"

    # 5. Reindex document
    reindex_res = client.post(f"/api/v1/rag/documents/{doc_id}/reindex", headers=headers)
    assert reindex_res.status_code == 200
    assert reindex_res.json()["status"] == "INDEXED"

    # 6. Delete document
    del_res = client.delete(f"/api/v1/rag/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify deleted
    get_res = client.get(f"/api/v1/rag/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404


def test_rag_abstention_on_unrelated_query(client, auth_tenant_rag):
    headers = auth_tenant_rag["headers"]

    # Ingest standard document
    doc_content = "This document only discusses industrial aluminum welding techniques and torch calibration."
    files = {"file": ("welding.txt", io.BytesIO(doc_content.encode("utf-8")), "text/plain")}
    client.post("/api/v1/rag/documents", files=files, headers=headers)

    # Query with strict similarity threshold for completely unrelated topic
    chat_payload = {
        "query": "What are the company health insurance dental benefits and copays?",
        "top_k": 3,
        "similarity_threshold": 0.85
    }
    chat_res = client.post("/api/v1/rag/chat", json=chat_payload, headers=headers)
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["has_sufficient_context"] is False
    assert "could not find sufficiently relevant information" in chat_data["answer"].lower()


def test_rag_multi_tenant_isolation(client, db_session):
    # Setup Tenant 1
    t1_id, u1_id = uuid.uuid4(), uuid.uuid4()
    t1 = Tenant(id=t1_id, name="Workspace Alpha", owner_id=u1_id)
    u1 = User(id=u1_id, email=f"u1_{str(u1_id)[:8]}@test.com", password_hash="hash", tenant_id=t1_id)
    m1 = TenantMember(tenant_id=t1_id, user_id=u1_id, role="OWNER")

    # Setup Tenant 2
    t2_id, u2_id = uuid.uuid4(), uuid.uuid4()
    t2 = Tenant(id=t2_id, name="Workspace Beta", owner_id=u2_id)
    u2 = User(id=u2_id, email=f"u2_{str(u2_id)[:8]}@test.com", password_hash="hash", tenant_id=t2_id)
    m2 = TenantMember(tenant_id=t2_id, user_id=u2_id, role="OWNER")

    db_session.add_all([t1, u1, m1, t2, u2, m2])
    db_session.commit()

    token1 = create_access_token(subject=str(u1_id))
    headers1 = {"Authorization": f"Bearer {token1}", "X-Organization-ID": str(t1_id)}

    token2 = create_access_token(subject=str(u2_id))
    headers2 = {"Authorization": f"Bearer {token2}", "X-Organization-ID": str(t2_id)}

    # Tenant 1 uploads confidential file
    confidential_text = "CONFIDENTIAL SECRET: Project Orion code phrase is BlueFalcon42."
    files = {"file": ("confidential.txt", io.BytesIO(confidential_text.encode("utf-8")), "text/plain")}
    upload_res = client.post("/api/v1/rag/documents", files=files, headers=headers1)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Tenant 2 attempts to query Tenant 1's secret -> must NOT retrieve it
    t2_chat = client.post("/api/v1/rag/chat", json={"query": "What is Project Orion code phrase?"}, headers=headers2)
    assert t2_chat.status_code == 200
    assert "BlueFalcon42" not in t2_chat.json()["answer"]
    assert len(t2_chat.json()["citations"]) == 0

    # Tenant 2 attempts to directly read or delete Tenant 1's document -> 404 Forbidden
    t2_read = client.get(f"/api/v1/rag/documents/{doc_id}", headers=headers2)
    assert t2_read.status_code == 404

    t2_del = client.delete(f"/api/v1/rag/documents/{doc_id}", headers=headers2)
    assert t2_del.status_code == 404


def test_rag_health_endpoint(client, auth_tenant_rag):
    headers = auth_tenant_rag["headers"]
    res = client.get("/api/v1/rag/health", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert "vector_store" in data
    assert "embedding_model" in data

