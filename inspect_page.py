from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.domain import Page, Field
import sys
import os

sys.path.append(os.getcwd())


def inspect_page(page_number):
    engine = create_engine("sqlite:///./sql_app.db")
    with Session(engine) as session:
        page = session.scalar(select(Page).where(Page.page_number == page_number))
        if not page:
            print(f"Page {page_number} not found")
            return

        fields = session.scalars(
            select(Field).where(Field.page_id == page.id).order_by(Field.id)
        ).all()

        print(f"Page {page_number} ({page.page_type}) Fields ({len(fields)} total):")
        print(f"{'Name':<40} | {'Value'}")
        print("-" * 80)

        for f in fields:
            val = f.ocr_value or ""
            # Sanitize value: replace newlines with space, truncate
            val_clean = val.replace("\n", " ").replace("\r", "")[:60]
            print(f"{f.name:<40} | {val_clean}")


if __name__ == "__main__":
    inspect_page(3)
