import io
import os
import uuid
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.tenant import Tenant, TenantMember
from app.models.user import User, UserRole
from app.models.dataset import DatasetVersion, CleaningJob, CleaningAuditLog
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def test_env(db_session: Session):
    # Setup test user and tenant
    user = db_session.query(User).filter(User.email == "cleaning_phase3_tester@example.com").first()
    if not user:
        user = User(
            email="cleaning_phase3_tester@example.com",
            password_hash="hashed_pw_test",
            full_name="Cleaning Tester",
            role=UserRole.ANALYST,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

    tenant = db_session.query(Tenant).filter(Tenant.name == "Cleaning Phase 3 Workspace").first()
    if not tenant:
        tenant = Tenant(
            name="Cleaning Phase 3 Workspace",
            owner_id=user.id,
            subscription_tier="PRO",
            subscription_status="ACTIVE"
        )
        db_session.add(tenant)
        db_session.commit()
        db_session.refresh(tenant)

    member = db_session.query(TenantMember).filter(
        TenantMember.tenant_id == tenant.id,
        TenantMember.user_id == user.id
    ).first()
    if not member:
        member = TenantMember(
            tenant_id=tenant.id,
            user_id=user.id,
            role="OWNER"
        )
        db_session.add(member)
        db_session.commit()

    token = create_access_token(user.id)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": str(tenant.id)
    }

    return {
        "user": user,
        "tenant": tenant,
        "headers": headers
    }


def test_tabular_cleaning_pipeline_execution(client: TestClient, test_env: dict, db_session: Session):
    """
    Tests the full 20-step Universal Data Cleaning Pipeline on a dirty CSV dataset:
    - Protects Order ID from imputation
    - Removes duplicate rows
    - Converts currency strings ($1,250.00 -> 1250.0)
    - Standardizes date formats (2026/10/24 -> 2026-10-24)
    - Validates cross-field consistency
    - Generates scorecard and 20-step audit logs
    - Never overwrites the raw file
    """
    headers = test_env["headers"]

    # Construct dirty CSV with duplicate, currency, missing quantity, and dirty text
    dirty_csv = (
        "Order ID,Product Name,Units Sold,Price,Total Sales,Order Date\n"
        "ORD-001,  <b>Wireless Mouse</b>  ,2,$25.00,$50.00,2026/10/24\n"
        "ORD-001,  <b>Wireless Mouse</b>  ,2,$25.00,$50.00,2026/10/24\n"  # Exact Duplicate
        "ORD-002,Mechanical Keyboard,,$100.00,$100.00,10-25-2026\n"       # Missing Units Sold
        ",USB-C Cable,1,$15.00,$15.00,2026-10-26\n"                       # Missing Order ID (Protected from imputation!)
        "ORD-004,Gaming Monitor,1,$300.00,$300.00,2026-10-27\n"
    )

    # 1. Upload dataset
    upload_res = client.post(
        "/api/v1/cleaning/upload",
        files={"file": ("dirty_sales.csv", io.BytesIO(dirty_csv.encode("utf-8")), "text/csv")},
        data={"dataset_name": "Test Dirty Sales"},
        headers=headers
    )
    assert upload_res.status_code == 200, upload_res.text
    dataset_id = upload_res.json()["dataset_id"]
    orig_checksum = upload_res.json()["checksum_sha256"]

    # 2. Trigger Cleaning Job
    clean_res = client.post(
        f"/api/v1/cleaning/datasets/{dataset_id}/clean",
        json={"pipeline_config": {
            "standardize_column_names": True,
            "duplicate_keep_strategy": "first",
            "default_numeric_strategy": "median",
            "strip_html": True,
            "strip_whitespace": True
        }},
        headers=headers
    )
    assert clean_res.status_code == 200, clean_res.text
    job_id = clean_res.json()["job_id"]
    result = clean_res.json()["result"]

    assert result["status"] == "COMPLETED"
    report = result["validation_report"]
    assert report["summary"]["duplicates_removed"] == 1
    assert report["quality_score"] > 0

    # 3. Check Job Status Endpoint
    status_res = client.get(f"/api/v1/cleaning/jobs/{job_id}", headers=headers)
    assert status_res.status_code == 200
    job_data = status_res.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["current_step"] == 20

    # 4. Check Step-by-Step Audit Logs
    logs_res = client.get(f"/api/v1/cleaning/jobs/{job_id}/logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()["logs"]
    assert len(logs) >= 10
    step_names = [l["step_name"] for l in logs]
    assert "Original Data Backup" in step_names
    assert "Duplicate Detection & Removal" in step_names
    assert "Missing Value Handling" in step_names

    # Verify ID column was protected from blind imputation
    missing_log = next(l for l in logs if l["step_name"] == "Missing Value Handling")
    assert "order_id" in missing_log["details"]
    assert missing_log["details"]["order_id"]["strategy"] == "preserved_unimputed"

    # 5. Verify Original Raw File was NOT modified or overwritten
    raw_ds = db_session.query(DatasetVersion).filter(DatasetVersion.id == uuid.UUID(dataset_id)).first()
    assert os.path.exists(raw_ds.original_file_path)
    with open(raw_ds.original_file_path, "rb") as f:
        current_checksum = hashlib.sha256(f.read()).hexdigest()
    assert current_checksum == orig_checksum, "Original file was modified during cleaning!"

    # 6. Verify Cleaned File is Available and Downloadable
    assert os.path.exists(raw_ds.cleaned_file_path)
    dl_res = client.get(f"/api/v1/cleaning/datasets/{dataset_id}/download-cleaned", headers=headers)
    assert dl_res.status_code == 200
    cleaned_content = dl_res.content.decode("utf-8")
    assert "order_id" in cleaned_content  # Standardized column name
    assert "<b>" not in cleaned_content    # HTML tags stripped
    assert "$25.00" not in cleaned_content # Currency punctuation cleansed
    assert "25.0" in cleaned_content       # Numeric value preserved


def test_text_document_cleaning(client: TestClient, test_env: dict):
    """
    Tests text document cleaning (Step 16) preserving original file and producing normalized text.
    """
    headers = test_env["headers"]
    dirty_text = "<h1>Contract</h1>\n\n\t   Payment terms:   Net 30.   "

    upload_res = client.post(
        "/api/v1/cleaning/upload",
        files={"file": ("contract.txt", io.BytesIO(dirty_text.encode("utf-8")), "text/plain")},
        data={"dataset_name": "Test Contract"},
        headers=headers
    )
    assert upload_res.status_code == 200
    dataset_id = upload_res.json()["dataset_id"]

    clean_res = client.post(
        f"/api/v1/cleaning/datasets/{dataset_id}/clean",
        json={"pipeline_config": {"strip_html": True, "strip_whitespace": True}},
        headers=headers
    )
    assert clean_res.status_code == 200
    res_data = clean_res.json()["result"]
    assert res_data["status"] == "COMPLETED"
    assert res_data["summary"]["cleaned_char_count"] < res_data["summary"]["original_char_count"]
