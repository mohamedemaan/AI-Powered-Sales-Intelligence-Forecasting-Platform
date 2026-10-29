import os
import hashlib
import uuid
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.rag import RagDocument, RagChunk
from app.services.rag.document_service import get_rag_upload_dir, index_document_pipeline

logger = logging.getLogger(__name__)

DEFAULT_PLAYBOOK_CONTENT = """# SalesMind Enterprise Sales Playbook & Operational Policies

## Return, Refund, and Restocking Fee Policy
1. Return Window: All corporate and retail customers have a 30-calendar-day return window starting from the confirmed date of delivery.
2. Restocking Fee Schedule:
   - Unopened and factory-sealed products in original packaging are eligible for a 100% full refund with zero restocking fee.
   - Opened items in the Technology, Electronics, and Hardware categories are subject to a mandatory 15% restocking fee deducted from the refunded amount.
   - Office Supplies and Furniture returned in opened condition with non-defective status carry a 10% restocking fee.
3. Defective Goods & Carrier Damage Exemption:
   - Any product that arrives damaged, defective, or failing initial power-on diagnostics is 100% exempt from all restocking fees.
   - SalesMind covers prepaid return ground and air freight for all validated defective claims.
4. Final Sale Items:
   - Custom-engraved hardware, tailored ergonomic furniture, and clearance merchandise marked 'As-Is' are strictly non-refundable and final sale.

## Wholesale Bulk Discount Thresholds & Pricing Governance
To protect operating margins while incentivizing high-volume purchasing, the following volume pricing tiers apply:
- Tier 1 (10 to 49 units): Standard 5% discount across all catalog categories.
- Tier 2 (50 to 99 units): 12% discount on Technology and Office Supplies; 8% discount on Furniture.
- Tier 3 (100 to 499 units): 20% bulk wholesale discount. Strictly requires VP of Sales written authorization and must preserve minimum 15% net operating margin.
- Enterprise Tier (500+ units): Custom contracted rate requiring joint sign-off from VP of Sales and Chief Financial Officer (CFO).
- Deal Desk Guardrails: Sales representatives are strictly prohibited from offering discounts exceeding 20% without executive deal desk review.

## Hardware Warranty & Replacement Claims Guidelines
1. Standard Warranty Coverage:
   - All SalesMind hardware, phones, copiers, and office machines include a 1-year standard manufacturer limited warranty covering mechanical defects, component failure, and firmware anomalies.
2. Return Merchandise Authorization (RMA) Process:
   - Step 1: Customer contacts technical support or submits an online RMA ticket with serial number and invoice ID.
   - Step 2: Technical support validates telemetry and issues a formal RMA authorization code within 4 business hours.
   - Step 3: Advance Replacement dispatch is initiated; replacement units ship within 3 to 5 business days via expedited air.
3. Warranty Exclusions:
   - Physical trauma, unauthorized third-party repairs, water submersion, and electrical surge damage void all warranty coverage.

## Sales Commission & Margin Governance Policy
- Standard commission rate is 8% of gross revenue for deals achieving at least 18% operating profit margin.
- Discounted deals resulting in profit margins below 10% reduce rep commission to 2.5% and require branch manager sign-off.
- Zero or negative margin deals generate 0% commission and trigger an automatic finance audit.
"""

DEFAULT_CATALOG_CONTENT = """# SalesMind Product Catalog & Category Performance Standards

## Category Overview: Technology
- Phones & Smart Devices: High-velocity category generating substantial revenue with average margins of 13.5%. Leading SKUs include executive smartphones and dual-line conference phones.
- Accessories: High-margin category (25% - 40% margin) including wireless fast-chargers, heavy-duty surge protectors, and noise-canceling headsets.
- Machines & Copiers: Enterprise printing stations and multi-function laser copiers with recurring service contracts.

## Category Overview: Furniture
- Executive Task Chairs: Ergonomic mesh and high-back leather chairs engineered for lumbar support.
- Standing Desks & Conference Tables: Motorized adjustable height workstations.
- Bookcases & Storage: Modular steel shelving units and fireproof locking file cabinets.

## Category Overview: Office Supplies
- Binders & Fasteners: Heavy-duty vinyl ring binders and precision metal fasteners.
- Paper & Print Supplies: Premium multipurpose 20lb copier paper and archival cardstock.
- Storage & Organization: Heavy-duty corrugated document storage boxes and desktop organizers.
"""


def seed_sample_policies_for_tenant(db: Session, tenant_id: uuid.UUID, user_id: uuid.UUID = None) -> List[RagDocument]:
    """
    Seeds default corporate knowledge base documents into a tenant workspace.
    Idempotent: skips documents that have already been seeded.
    """
    docs_to_seed = [
        (
            "SalesMind Enterprise Sales Playbook & Return Policies",
            "sales_playbook_and_policies.md",
            DEFAULT_PLAYBOOK_CONTENT
        ),
        (
            "SalesMind Product Catalog & Specifications",
            "product_catalog_specifications.md",
            DEFAULT_CATALOG_CONTENT
        )
    ]

    upload_dir = get_rag_upload_dir(tenant_id)
    seeded_docs: List[RagDocument] = []

    for title, filename, content in docs_to_seed:
        file_bytes = content.encode("utf-8")
        checksum = hashlib.sha256(file_bytes).hexdigest()

        # Check existing
        existing = db.query(RagDocument).filter(
            RagDocument.tenant_id == tenant_id,
            RagDocument.checksum_sha256 == checksum
        ).first()

        if existing:
            seeded_docs.append(existing)
            continue

        doc_id = uuid.uuid4()
        disk_filename = f"{str(doc_id)[:8]}_{checksum[:8]}.md"
        phys_path = os.path.join(upload_dir, disk_filename)
        with open(phys_path, "wb") as f:
            f.write(file_bytes)

        doc = RagDocument(
            id=doc_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            original_filename=filename,
            file_path=phys_path,
            file_size=len(file_bytes),
            mime_type="text/markdown",
            file_type="md",
            checksum_sha256=checksum,
            status="UPLOADED"
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        index_document_pipeline(db=db, document=doc)
        seeded_docs.append(doc)
        logger.info(f"Seeded sample policy document '{title}' for tenant {tenant_id}")

    return seeded_docs

