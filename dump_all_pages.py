from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.domain import Page, Field
import sys
import os

sys.path.append(os.getcwd())


def dump_all_pages(doc_id):
    engine = create_engine("sqlite:///./sql_app.db")
    with Session(engine) as session:
        pages = session.scalars(
            select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
        ).all()

        with open("extraction_results.txt", "w", encoding="utf-8") as f:
            f.write(f"Extraction Results for Document ID: {doc_id}\n")
            f.write("=" * 80 + "\n\n")

            for p in pages:
                fields = session.scalars(
                    select(Field).where(Field.page_id == p.id).order_by(Field.id)
                ).all()
                f.write(f"Page {p.page_number} [{p.page_type}]\n")
                f.write("-" * 80 + "\n")
                if not fields:
                    f.write("(No fields extracted)\n")
                else:
                    f.write(f"{'Field Name':<50} | {'Confidence':<10} | {'Value'}\n")
                    f.write("-" * 80 + "\n")
                    for field in fields:
                        val = (field.ocr_value or "").replace("\n", " ")[
                            :100
                        ]  # Truncate for readability
                        conf = f"{field.ocr_confidence:.2f}"
                        f.write(f"{field.name:<50} | {conf:<10} | {val}\n")
                f.write("\n" + "=" * 80 + "\n\n")

    print(f"Results written to extraction_results.txt")


if __name__ == "__main__":
    dump_all_pages(1)
