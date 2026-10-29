import io
import uuid
import json
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.api import deps
from app.db.session import SessionLocal
from app.models.tenant import Tenant, TenantMember
from app.models.user import User
from app.models.dataset import DatasetVersion, CleaningJob, CleaningAuditLog
from app.models.data import RawSalesData


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_tenant(db_session: Session):
    # Unique tenant for export testing
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    
    tenant = Tenant(
        id=t_id,
        name="Export Test Workspace",
        slug=f"export-{str(t_id)[:8]}",
        subscription_tier="PRO",
        subscription_status="ACTIVE",
        owner_id=u_id
    )
    user = User(
        id=u_id,
        email=f"tester_{str(u_id)[:8]}@salesmind.ai",
        username=f"tester_{str(u_id)[:8]}",
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
    db_session.refresh(tenant)
    db_session.refresh(user)

    yield {"tenant": tenant, "user": user}

    # Teardown
    db_session.query(CleaningAuditLog).filter(CleaningAuditLog.dataset_version_id.in_(
        db_session.query(DatasetVersion.id).filter(DatasetVersion.tenant_id == t_id)
    )).delete(synchronize_session=False)
    db_session.query(CleaningJob).filter(CleaningJob.tenant_id == t_id).delete()
    db_session.query(DatasetVersion).filter(DatasetVersion.tenant_id == t_id).delete()
    db_session.query(RawSalesData).filter(RawSalesData.tenant_id == t_id).delete()
    db_session.query(TenantMember).filter(TenantMember.tenant_id == t_id).delete()
    db_session.query(User).filter(User.id == u_id).delete()
    db_session.query(Tenant).filter(Tenant.id == t_id).delete()
    db_session.commit()


@pytest.fixture
def client(auth_tenant):
    def override_tenant():
        return auth_tenant["tenant"]

    def override_analyst():
        return auth_tenant["user"]

    def override_viewer():
        return auth_tenant["user"]

    app.dependency_overrides[deps.get_current_tenant_or_default] = override_tenant
    app.dependency_overrides[deps.require_analyst] = override_analyst
    app.dependency_overrides[deps.require_viewer] = override_viewer
    app.dependency_overrides[deps.require_owner] = override_analyst

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_multi_format_exports_and_reports(client, auth_tenant):
    # 1. Upload sample CSV with line items
    csv_data = (
        "Order ID,Date,Product Name,Category,Sub-Category,Units Sold,Price,Total Sales,Profit\n"
        "ORD-101,2026-06-01,Alpha Widget,Technology,Accessories,10,$25.00,$250.00,$50.00\n"
        "ORD-102,2026-06-02,Beta Gadget,Office Supplies,Binders,5,$12.50,$62.50,-$10.00\n"
        "ORD-103,2026-06-03,Gamma Tool,Furniture,Chairs,2,$100.00,$200.00,$35.00\n"
        "ORD-101,2026-06-01,Alpha Widget,Technology,Accessories,10,$25.00,$250.00,$50.00\n"  # Duplicate
    )
    files = {"file": ("test_sales.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    upload_res = client.post("/api/v1/cleaning/upload", files=files, data={"dataset_name": "Sales Q2 Test"})
    assert upload_res.status_code == 200, upload_res.text
    dataset_id = upload_res.json()["dataset_id"]

    # 2. Trigger Universal Data Cleaning Pipeline
    clean_res = client.post(f"/api/v1/cleaning/datasets/{dataset_id}/clean")
    assert clean_res.status_code == 200, clean_res.text
    job_id = clean_res.json()["job_id"]

    # 3. Test Tabular Multi-Format Exports
    formats = ["csv", "tsv", "xlsx", "parquet", "json", "jsonl"]
    for fmt in formats:
        export_res = client.get(f"/api/v1/cleaning/datasets/{dataset_id}/export?format={fmt}")
        assert export_res.status_code == 200, f"Export failed for format {fmt}: {export_res.text}"
        assert len(export_res.content) > 0
        content_disp = export_res.headers.get("content-disposition", "")
        assert f".{fmt}" in content_disp or (fmt == "jsonl" and ".jsonl" in content_disp)

        # Content validation
        if fmt == "csv":
            df_check = pd.read_csv(io.BytesIO(export_res.content))
            assert len(df_check) == 3  # Duplicate removed
        elif fmt == "tsv":
            df_check = pd.read_csv(io.BytesIO(export_res.content), sep="\t")
            assert len(df_check) == 3
        elif fmt == "parquet":
            df_check = pd.read_parquet(io.BytesIO(export_res.content))
            assert len(df_check) == 3
        elif fmt == "json":
            records = json.loads(export_res.content.decode("utf-8"))
            assert len(records) == 3

    # 4. Test Multi-Format Quality & Cleaning Reports
    # A. JSON Report
    rep_json = client.get(f"/api/v1/cleaning/jobs/{job_id}/report?format=json")
    assert rep_json.status_code == 200
    j_data = json.loads(rep_json.content.decode("utf-8"))
    assert j_data["cleaning_job"]["status"] == "COMPLETED"
    assert len(j_data["steps_executed"]) == 20
    assert "validation_scorecard" in j_data

    # B. Excel Multi-Sheet Report
    rep_xlsx = client.get(f"/api/v1/cleaning/jobs/{job_id}/report?format=xlsx")
    assert rep_xlsx.status_code == 200
    assert len(rep_xlsx.content) > 1000
    assert "spreadsheet" in rep_xlsx.headers.get("content-type", "")

    # C. Executive PDF Report
    rep_pdf = client.get(f"/api/v1/cleaning/jobs/{job_id}/report?format=pdf")
    assert rep_pdf.status_code == 200
    assert rep_pdf.content.startswith(b"%PDF-1.4")
    assert rep_pdf.headers.get("content-type") == "application/pdf"

    # 5. Test Dataset Preview (Before & After)
    prev_res = client.get(f"/api/v1/cleaning/datasets/{dataset_id}/preview")
    assert prev_res.status_code == 200, prev_res.text
    p_data = prev_res.json()
    assert p_data["raw_preview"]["count"] == 4
    assert p_data["cleaned_preview"]["count"] == 3
    assert p_data["is_cleaned"] is True

    # 6. Test Dataset Activation
    act_res = client.post(f"/api/v1/cleaning/datasets/{dataset_id}/activate")
    assert act_res.status_code == 200, act_res.text
    act_data = act_res.json()
    assert act_data["is_active_for_analysis"] is True
    assert act_data["rows_reconciled_into_ledger"] == 3
