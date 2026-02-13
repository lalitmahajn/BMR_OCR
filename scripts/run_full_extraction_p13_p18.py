import sys
import cv2
from pathlib import Path
from sqlalchemy import text
from app.core.config import settings
from app.models.base import Base
from app.models.domain import Document, Page, Field
from app.engines.classification import PageType
from app.engines.storage import StorageEngine
from app.orchestrator import Orchestrator


def run_extraction():
    print("--- START SYSTEM RUN ---")
    storage = StorageEngine()
    Base.metadata.create_all(storage.engine)
    session = storage.get_session()

    images_dir = settings.DATA_DIR / "images"
    target_pages = [13, 14, 15, 16, 17, 18]
    image_paths = []

    for p in target_pages:
        c = list(images_dir.glob(f"p{p}_*.jpg"))
        if c:
            image_paths.append(c[0])
            print(f"FOUND: {c[0].name}")

    print(f"TOTAL IMAGES TO PROCESS: {len(image_paths)}")
    if not image_paths:
        print("NO IMAGES FOUND. EXITING.")
        return

    doc = Document(filename="SOP_EXTRACT_RUN_FINAL.pdf")
    session.add(doc)
    session.commit()
    print(f"CREATED DOCUMENT ID: {doc.id}")

    orchestrator = Orchestrator()

    for img_path in image_paths:
        try:
            p_str = img_path.name.split("_")[0][1:]
            page_num = int(p_str)
            print(f"PROCESS: Page {page_num}...")

            ocr = orchestrator.ocr_adapter.extract_text(str(img_path))
            print(f"  OCR: {len(ocr.text)} chars")

            cl = orchestrator.classification.classify(ocr.text)
            print(f"  CLASS: {cl.page_type.name}")

            db_page = Page(
                document_id=doc.id,
                page_number=page_num,
                image_path=str(img_path),
                page_type=cl.page_type.name,
            )
            session.add(db_page)
            session.flush()
            print(f"  PAGE ID: {db_page.id}")

            if cl.page_type != PageType.UNKNOWN:
                tpl = orchestrator.template_engine.get_template(cl.page_type.value)
                if tpl and tpl.extraction_template:
                    res = orchestrator.extraction_engine.process_nested_template(
                        ocr.text, tpl.extraction_template
                    )
                    print(
                        f"  EXTRACT: {len(res['headers'])} headers, {len(res['rows'])} rows"
                    )

                    for k, v in res["headers"].items():
                        session.add(
                            Field(
                                page=db_page,
                                name=k,
                                ocr_value=v["value"],
                                roi_coordinates="0,0",
                            )
                        )
                    for row in res["rows"]:
                        ext = row["extracted"]
                        p_name = (
                            row["config"].parameter
                            if hasattr(row["config"], "parameter")
                            else "ROW"
                        )
                        for ck, cv in ext.items():
                            if ck == "_table_name":
                                continue
                            session.add(
                                Field(
                                    page=db_page,
                                    name=f"TABLE_{p_name}_{ck}",
                                    ocr_value=str(cv),
                                    roi_coordinates="0,0",
                                )
                            )

            session.commit()
            print(f"  PAGE {page_num} COMMITTED.")
        except Exception as e:
            print(f"  ERROR ON PAGE {img_path.name}: {e}")
            session.rollback()

    final_count = session.query(Page).filter_by(document_id=doc.id).count()
    print(f"--- FINISHED. PAGES IN DB: {final_count} ---")
    session.close()


if __name__ == "__main__":
    run_extraction()
