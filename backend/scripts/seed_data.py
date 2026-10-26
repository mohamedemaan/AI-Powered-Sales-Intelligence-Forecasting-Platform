import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.pipelines.etl import process_upload
import app.models.user
import app.models.product
import app.models.order
import app.models.data
import app.models.tenant
import app.models.forecast

def seed():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    if str(engine.url).startswith("sqlite"):
        with engine.connect() as conn:
            try:
                cursor = conn.exec_driver_sql("PRAGMA table_info(users)")
                existing_cols = [row[1] for row in cursor.fetchall()]
                if "tenant_id" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE users ADD COLUMN tenant_id VARCHAR(36)")
                    conn.commit()
            except Exception:
                pass
    
    csv_path = backend_dir.parent / "data" / "sample_sales_data.csv"
    if not csv_path.exists():
        print(f"Sample data CSV not found at {csv_path}")
        return

    print(f"Reading sample data from {csv_path}...")
    db = SessionLocal()
    try:
        count = process_upload(db, str(csv_path))
        print(f" Successfully seeded {count} sales transaction records into database!")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

