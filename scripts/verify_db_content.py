import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.domain import Document, Page, Field


def verify_db():
    print(f"Connecting to DB: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # DEBUG: List ALL pages
    all_pages = session.query(Page).all()
    print(f"Total Pages in DB: {len(all_pages)}")
    for p in all_pages:
        print(f" - Page ID={p.id}, DocID={p.document_id}, PageNum={p.page_number}")

    # Find all documents with this name
    doc_name = "SOP_EXTRACT_RUN_FINAL.pdf"
    docs = session.query(Document).filter_by(filename=doc_name).all()

    if not docs:
        print(f"Document {doc_name} NOT FOUND in DB.")
        return

    print(f"Found {len(docs)} Documents with name {doc_name}:")

    selected_doc = None
    for d in docs:
        page_count = session.query(Page).filter_by(document_id=d.id).count()
        print(f" - ID={d.id}, Created={d.ingested_at}, Pages={page_count}")
        if page_count > 0:
            selected_doc = d

    if not selected_doc:
        print("No document with pages found.")
        return

    doc = selected_doc
    print(f"\nVerifying details for Document ID={doc.id}...")

    # List Pages
    pages = (
        session.query(Page)
        .filter_by(document_id=doc.id)
        .order_by(Page.page_number)
        .all()
    )
    print(f"Found {len(pages)} Pages.")

    for p in pages:
        print(f"\n--- Page {p.page_number} ({p.page_type}) ---")
        fields = session.query(Field).filter_by(page_id=p.id).all()
        print(f"Extracted {len(fields)} Fields:")

        # Group by Table vs Header
        headers = []
        tables = []
        for f in fields:
            if f.name.startswith("TABLE_"):
                tables.append(f)
            else:
                headers.append(f)

        print(f"  Headers ({len(headers)}):")
        for h in headers:
            val_snippet = (
                (h.ocr_value[:50] + "...")
                if h.ocr_value and len(h.ocr_value) > 50
                else h.ocr_value
            )
            print(f"    - {h.name}: {val_snippet}")

        print(f"  Table Fields ({len(tables)}):")
        # Print first few table fields to verify structure
        for t in tables[:5]:
            val_snippet = (
                (t.ocr_value[:50] + "...")
                if t.ocr_value and len(t.ocr_value) > 50
                else t.ocr_value
            )
            print(f"    - {t.name}: {val_snippet}")
        if len(tables) > 5:
            print(f"    ... and {len(tables) - 5} more.")

    session.close()


if __name__ == "__main__":
    verify_db()
