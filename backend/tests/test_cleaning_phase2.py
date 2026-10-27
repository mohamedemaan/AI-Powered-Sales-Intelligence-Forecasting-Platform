import io
import os
import json
import uuid
import hashlib
import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantMember, TenantMemberRole
from app.models.dataset import DatasetVersion
from app.core import security

client = TestClient(app)
PRECOMPUTED_HASH = security.get_password_hash("SecretPass123!")


def create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, tier="PRO", prefix="cln"):
    uid = uuid.uuid4()
    email = f"{prefix}_{uid.hex[:6]}@salesmind.ai"
    user = User(
        id=uid,
        email=email,
        username=f"usr_{uid.hex[:6]}",
        full_name=f"User {prefix.capitalize()}",
        password_hash=PRECOMPUTED_HASH,
        role=UserRole.ANALYST,
        is_active=True,
    )
    db.add(user)
    db.flush()

    tenant = Tenant(
        name=f"Cleaning Test Workspace {prefix}",
        owner_id=user.id,
        subscription_tier=tier,
        subscription_status="ACTIVE",
        current_period_end=(datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    )
    db.add(tenant)
    db.flush()

    member = TenantMember(
        tenant_id=tenant.id,
        user_id=user.id,
        role=role
    )
    db.add(member)
    user.tenant_id = tenant.id
    db.commit()
    db.refresh(user)
    db.refresh(tenant)

    token = security.create_access_token(user.id)
    return user, tenant, token


def test_multi_format_upload_csv():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="csv")
        headers = {"Authorization": f"Bearer {token}"}

        csv_content = b"date,sku,units_sold,price\n2026-01-01,SKU-A,10,25.5\n2026-01-02,SKU-B,5,15.0\n"
        expected_sha = hashlib.sha256(csv_content).hexdigest()

        response = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            data={"dataset_name": "Retail Q1 Dataset"},
            files={"file": ("sales_data.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["status"] == "success"
        assert data["filename"] == "sales_data.csv"
        assert data["format_type"] == "csv"
        assert data["checksum_sha256"] == expected_sha
        assert data["row_count"] == 2
        assert data["col_count"] == 4
        assert data["organization_id"] == str(tenant.id)

        # Verify DB record
        ds = db.query(DatasetVersion).filter(DatasetVersion.id == uuid.UUID(data["dataset_id"])).first()
        assert ds is not None
        assert ds.name == "Retail Q1 Dataset"
        assert ds.file_size == len(csv_content)
        assert os.path.exists(ds.original_file_path)

        # Verify physical file matches exact bytes
        with open(ds.original_file_path, "rb") as f:
            assert f.read() == csv_content
    finally:
        db.close()


def test_multi_format_upload_tsv():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="tsv")
        headers = {"Authorization": f"Bearer {token}"}

        tsv_content = b"date\tsku\tunits_sold\n2026-02-01\tSKU-1\t40\n2026-02-02\tSKU-2\t80\n"
        response = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("inventory.tsv", io.BytesIO(tsv_content), "text/tab-separated-values")}
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["format_type"] == "tsv"
        assert data["row_count"] == 2
        assert data["col_count"] == 3
    finally:
        db.close()


def test_multi_format_upload_json():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="json")
        headers = {"Authorization": f"Bearer {token}"}

        json_data = [
            {"order_id": "ORD-1", "amount": 120.5, "status": "shipped"},
            {"order_id": "ORD-2", "amount": 85.0, "status": "delivered"}
        ]
        json_content = json.dumps(json_data).encode("utf-8")

        response = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("orders.json", io.BytesIO(json_content), "application/json")}
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["format_type"] == "json"
        assert data["row_count"] == 2
        assert data["col_count"] == 3
    finally:
        db.close()


def test_multi_format_upload_xlsx():
    import openpyxl
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="xlsx")
        headers = {"Authorization": f"Bearer {token}"}

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "SalesSheet"
        ws.append(["Region", "Sales", "Rep"])
        ws.append(["North", 4500, "Alice"])
        ws.append(["South", 3200, "Bob"])
        xlsx_buffer = io.BytesIO()
        wb.save(xlsx_buffer)
        xlsx_content = xlsx_buffer.getvalue()

        response = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("quarterly_report.xlsx", io.BytesIO(xlsx_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["format_type"] == "xlsx"
        assert data["row_count"] == 2
        assert data["col_count"] == 3
        assert "SalesSheet" in data["summary"].get("sheet_names", [])
    finally:
        db.close()


def test_multi_format_upload_text():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="txt")
        headers = {"Authorization": f"Bearer {token}"}

        text_content = b"Line 1: Log header\nLine 2: Customer feedback notes\nLine 3: Product review\n"
        response = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("notes.txt", io.BytesIO(text_content), "text/plain")}
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["format_type"] == "text"
        assert data["row_count"] == 3
        assert data["summary"]["line_count"] == 3
    finally:
        db.close()


def test_unsupported_format_and_empty_file():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="rej")
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Unsupported executable format
        resp1 = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/x-msdownload")}
        )
        assert resp1.status_code == 400
        assert "Unsupported file format" in resp1.json()["detail"]

        # 2. Empty 0-byte file
        resp2 = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
        )
        assert resp2.status_code == 400
        assert "empty (0 bytes)" in resp2.json()["detail"]
    finally:
        db.close()


def test_download_original_unmodified_file():
    db = SessionLocal()
    try:
        user, tenant, token = create_user_and_workspace(db, prefix="dl")
        headers = {"Authorization": f"Bearer {token}"}

        original_bytes = b"id,name,value\n1,alpha,100\n2,beta,200\n"
        upload_resp = client.post(
            "/api/v1/cleaning/upload",
            headers=headers,
            files={"file": ("original_dataset.csv", io.BytesIO(original_bytes), "text/csv")}
        )
        assert upload_resp.status_code == 200
        ds_id = upload_resp.json()["dataset_id"]

        # Download original unmodified file
        dl_resp = client.get(
            f"/api/v1/cleaning/datasets/{ds_id}/download-original",
            headers=headers
        )
        assert dl_resp.status_code == 200
        assert dl_resp.content == original_bytes
        assert "text/csv" in dl_resp.headers.get("content-type", "")
    finally:
        db.close()


def test_multi_tenant_isolation_on_datasets():
    db = SessionLocal()
    try:
        user_a, tenant_a, token_a = create_user_and_workspace(db, prefix="t_a")
        user_b, tenant_b, token_b = create_user_and_workspace(db, prefix="t_b")

        # Tenant A uploads
        upload_resp = client.post(
            "/api/v1/cleaning/upload",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"file": ("tenant_a_data.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
        )
        assert upload_resp.status_code == 200
        ds_a_id = upload_resp.json()["dataset_id"]

        # Tenant B lists datasets -> must NOT see Tenant A's dataset
        list_resp_b = client.get(
            "/api/v1/cleaning/datasets",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert list_resp_b.status_code == 200
        b_ids = [d["id"] for d in list_resp_b.json()["datasets"]]
        assert ds_a_id not in b_ids

        # Tenant B attempts to download Tenant A's original file -> 404 Not Found
        dl_resp_b = client.get(
            f"/api/v1/cleaning/datasets/{ds_a_id}/download-original",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert dl_resp_b.status_code == 404
    finally:
        db.close()


def test_delete_dataset_version_and_rbac():
    db = SessionLocal()
    try:
        # Owner / Admin user
        owner_user, tenant, owner_token = create_user_and_workspace(db, role=TenantMemberRole.OWNER.value, prefix="del_o")
        
        # Viewer user in same workspace
        viewer_uid = uuid.uuid4()
        viewer_user = User(
            id=viewer_uid,
            email=f"viewer_{viewer_uid.hex[:6]}@salesmind.ai",
            username=f"vwr_{viewer_uid.hex[:6]}",
            full_name="Viewer User",
            password_hash=PRECOMPUTED_HASH,
            role=UserRole.ANALYST,
            tenant_id=tenant.id,
            is_active=True
        )
        db.add(viewer_user)
        db.flush()
        db.add(TenantMember(tenant_id=tenant.id, user_id=viewer_user.id, role=TenantMemberRole.VIEWER.value))
        db.commit()
        viewer_token = security.create_access_token(viewer_user.id)

        # Upload dataset as owner
        up_resp = client.post(
            "/api/v1/cleaning/upload",
            headers={"Authorization": f"Bearer {owner_token}"},
            files={"file": ("to_delete.csv", io.BytesIO(b"x,y\n1,2\n"), "text/csv")}
        )
        assert up_resp.status_code == 200
        ds_id = up_resp.json()["dataset_id"]

        # Viewer tries to delete -> 403 Forbidden
        del_viewer_resp = client.delete(
            f"/api/v1/cleaning/datasets/{ds_id}",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert del_viewer_resp.status_code == 403

        # Owner deletes -> 200 OK
        del_owner_resp = client.delete(
            f"/api/v1/cleaning/datasets/{ds_id}",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert del_owner_resp.status_code == 200

        # Confirm deleted in DB
        assert db.query(DatasetVersion).filter(DatasetVersion.id == uuid.UUID(ds_id)).first() is None
    finally:
        db.close()
