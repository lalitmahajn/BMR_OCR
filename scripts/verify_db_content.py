import sys
from pathlib import Path
from loguru import logger
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.append(str(Path(__file__).parent.parent))

from app.engines.storage import StorageEngine
from app.models.domain import Page, Field

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_db():
    storage = StorageEngine()
    session = storage.get_session()

    try:
        # Check P27/P28 (Packing Details)
        logger.info("--- Checking Packing Details (P27/P28) ---")
        packing_pages = session.scalars(
            select(Page).where(Page.page_type == "PACKING_DETAILS")
        ).all()

        if not packing_pages:
            logger.error("❌ No PACKING_DETAILS pages found in DB!")
        else:
            for p in packing_pages:
                fields = {f.name: f.ocr_value for f in p.fields}
                logger.info(
                    f"Page {p.page_number} (ID: {p.id}): Found {len(fields)} fields"
                )
                required = ["PRODUCT_NAME", "BATCH_NO", "TOTAL_QTY"]
                missing = [k for k in required if k not in fields]
                if missing:
                    logger.error(f"  ❌ Missing headers: {missing}")
                else:
                    logger.info(
                        f"  ✅ Headers found: Product='{fields.get('PRODUCT_NAME')}', Batch='{fields.get('BATCH_NO')}'"
                    )

        # Check P29/P30 (Checklist)
        logger.info("\n--- Checking Checklist (P29/P30) ---")
        checklist_pages = session.scalars(
            select(Page).where(Page.page_type == "BMR_CHECKLIST")
        ).all()

        if not checklist_pages:
            logger.error("❌ No BMR_CHECKLIST pages found in DB!")
        else:
            for p in checklist_pages:
                fields = {f.name: f.ocr_value for f in p.fields}
                logger.info(
                    f"Page {p.page_number} (ID: {p.id}): Found {len(fields)} fields"
                )

                # Check for status
                status_fields = [f for f in fields.values() if f in ["Yes", "No", "NA"]]
                if len(status_fields) > 0:
                    logger.info(
                        f"  ✅ Found {len(status_fields)} status fields (Yes/No/NA)"
                    )
                else:
                    logger.warning("  ⚠️ No status fields found")

    finally:
        session.close()


if __name__ == "__main__":
    verify_db()
