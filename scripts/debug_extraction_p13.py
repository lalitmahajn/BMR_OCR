import sys
import cv2
from pathlib import Path
from loguru import logger
from sqlalchemy import text
from app.core.config import settings
from app.models.base import Base
from app.models.domain import Document, Page, Field
from app.engines.classification import PageType
from app.engines.storage import StorageEngine
from app.orchestrator import Orchestrator

# Setup logging to stdout
logger.remove()
logger.add(sys.stdout, level="INFO")


def run_debug():
    print("--- START DEBUG RUN ---")
    storage = StorageEngine()
    Base.metadata.create_all(storage.engine)
    session = storage.get_session()

    # 1. Document
    doc_name = "DEBUG_P13.pdf"
    doc = Document(filename=doc_name)
    session.add(doc)
    session.commit()
    print(f"Created Doc ID: {doc.id}")

    # 2. Page 13
    img_candidates = list((settings.DATA_DIR / "images").glob("p13_*.jpg"))
    if not img_candidates:
        print("Page 13 image not found!")
        return
    img_path = img_candidates[0]
    print(f"Using Image: {img_path.name}")

    orchestrator = Orchestrator()
    page_ocr = orchestrator.ocr_adapter.extract_text(str(img_path))
    class_res = orchestrator.classification.classify(page_ocr.text)

    db_page = Page(
        document_id=doc.id,
        page_number=13,
        image_path=str(img_path),
        page_type=class_res.page_type.name,
    )
    session.add(db_page)
    print("Added Page object to session.")

    # 3. Extraction
    template = orchestrator.template_engine.get_template(class_res.page_type.value)
    if template and template.extraction_template:
        res = orchestrator.extraction_engine.process_nested_template(
            page_ocr.text, template.extraction_template
        )
        print(f"Extracted {len(res['headers'])} headers and {len(res['rows'])} rows.")

        for k, v in res["headers"].items():
            f = Field(
                page=db_page, name=k, ocr_value=v["value"], roi_coordinates="0,0,0,0"
            )
            session.add(f)

        for row in res["rows"]:
            extracted = row["extracted"]
            config = row["config"]
            for col_name, col_val in extracted.items():
                if col_name == "_table_name":
                    continue
                param_name = config.parameter if hasattr(config, "parameter") else "ROW"
                f = Field(
                    page=db_page,
                    name=f"TABLE_{param_name}_{col_name}",
                    ocr_value=str(col_val),
                    roi_coordinates="0,0,0,0",
                )
                session.add(f)
    else:
        print("No template found.")

    print("Committing transaction...")
    session.commit()
    print("Commit complete.")

    # 4. Final Query
    p_count = session.query(Page).filter_by(document_id=doc.id).count()
    f_count = session.query(Field).join(Page).filter(Page.document_id == doc.id).count()
    print(f"Verification: Found {p_count} pages and {f_count} fields for this doc.")

    session.close()
    print("--- END DEBUG RUN ---")


if __name__ == "__main__":
    run_debug()
