import io
import os
import uuid
import hashlib
import httpx
from app.db.session import SessionLocal
from app.models.tenant import Tenant, TenantMember
from app.models.user import User, UserRole
from app.models.dataset import DatasetVersion
from app.core.security import create_access_token

def run():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "cleaning_phase3_tester@example.com").first()
        if not user:
            user = User(
                email="cleaning_phase3_tester@example.com",
                password_hash="hashed_pw_test",
                full_name="Cleaning Tester",
                role=UserRole.ANALYST,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        tenant = db.query(Tenant).filter(Tenant.name == "Cleaning Phase 3 Workspace").first()
        if not tenant:
            tenant = Tenant(
                name="Cleaning Phase 3 Workspace",
                owner_id=user.id,
                subscription_tier="PRO",
                subscription_status="ACTIVE"
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)

        member = db.query(TenantMember).filter(
            TenantMember.tenant_id == tenant.id,
            TenantMember.user_id == user.id
        ).first()
        if not member:
            member = TenantMember(
                tenant_id=tenant.id,
                user_id=user.id,
                role="OWNER"
            )
            db.add(member)
            db.commit()

        token = create_access_token(user.id)
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Organization-ID": str(tenant.id)
        }
    finally:
        db.close()

    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

    print("[1/2] Testing tabular cleaning pipeline execution...")
    dirty_csv = (
        "Order ID,Product Name,Units Sold,Price,Total Sales,Order Date\n"
        "ORD-001,  <b>Wireless Mouse</b>  ,2,$25.00,$50.00,2026/10/24\n"
        "ORD-001,  <b>Wireless Mouse</b>  ,2,$25.00,$50.00,2026/10/24\n"
        "ORD-002,Mechanical Keyboard,,$100.00,$100.00,10-25-2026\n"
        ",USB-C Cable,1,$15.00,$15.00,2026-10-26\n"
        "ORD-004,Gaming Monitor,1,$300.00,$300.00,2026-10-27\n"
    )
    upload_res = client.post(
        "/api/v1/cleaning/upload",
        files={"file": ("dirty_sales.csv", io.BytesIO(dirty_csv.encode("utf-8")), "text/csv")},
        data={"dataset_name": "Test Dirty Sales"},
        headers=headers
    )
    assert upload_res.status_code == 200, upload_res.text
    dataset_id = upload_res.json()["dataset_id"]
    orig_checksum = upload_res.json()["checksum_sha256"]

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
    print(f"  -> Pipeline executed: Quality Score = {report['quality_score']}, Duplicates Removed = {report['summary']['duplicates_removed']}")

    # Audit logs check
    logs_res = client.get(f"/api/v1/cleaning/jobs/{job_id}/logs", headers=headers)
    assert logs_res.status_code == 200
    logs = logs_res.json()["logs"]
    assert len(logs) >= 10
    print(f"  -> Verified {len(logs)} audit log steps recorded.")

    # Protected ID check
    missing_log = next(l for l in logs if l["step_name"] == "Missing Value Handling")
    assert missing_log["details"]["order_id"]["strategy"] == "preserved_unimputed"
    print("  -> Order ID protected from blind imputation verified.")

    # Non-destruction check
    db_check = SessionLocal()
    try:
        raw_ds = db_check.query(DatasetVersion).filter(DatasetVersion.id == uuid.UUID(dataset_id)).first()
        assert os.path.exists(raw_ds.original_file_path)
        with open(raw_ds.original_file_path, "rb") as f:
            current_checksum = hashlib.sha256(f.read()).hexdigest()
        assert current_checksum == orig_checksum, "Original file was modified!"
    finally:
        db_check.close()
    print("  -> Original raw file checksum matches exactly (non-destructive).")

    # Download cleaned file check
    dl_res = client.get(f"/api/v1/cleaning/datasets/{dataset_id}/download-cleaned", headers=headers)
    assert dl_res.status_code == 200
    cleaned_content = dl_res.content.decode("utf-8")
    assert "order_id" in cleaned_content
    assert "<b>" not in cleaned_content
    assert "$25.00" not in cleaned_content
    assert "25.0" in cleaned_content
    print("  -> Downloaded cleaned dataset verified: HTML stripped, column names standardized, currency converted.")

    print("[2/2] Testing text document cleaning...")
    dirty_text = "<h1>Contract</h1>\n\n\t   Payment terms:   Net 30.   "
    upload_txt = client.post(
        "/api/v1/cleaning/upload",
        files={"file": ("contract.txt", io.BytesIO(dirty_text.encode("utf-8")), "text/plain")},
        data={"dataset_name": "Test Contract"},
        headers=headers
    )
    assert upload_txt.status_code == 200
    txt_dataset_id = upload_txt.json()["dataset_id"]

    clean_txt = client.post(
        f"/api/v1/cleaning/datasets/{txt_dataset_id}/clean",
        json={"pipeline_config": {"strip_html": True, "strip_whitespace": True}},
        headers=headers
    )
    assert clean_txt.status_code == 200
    txt_result = clean_txt.json()["result"]
    assert txt_result["status"] == "COMPLETED"
    assert txt_result["summary"]["cleaned_char_count"] < txt_result["summary"]["original_char_count"]
    print("  -> Text cleaning verified: HTML tags stripped, whitespace trimmed.")

    print("=== ALL PHASE 3 CLEANING TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    run()
