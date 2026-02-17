from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.domain import Page, Field
import sys
import os
import json

sys.path.append(os.getcwd())


def dump_page(page_number):
    engine = create_engine("sqlite:///./sql_app.db")
    with Session(engine) as session:
        page = session.scalar(select(Page).where(Page.page_number == page_number))
        if not page:
            print(f"Page {page_number} not found")
            return

        fields = session.scalars(
            select(Field).where(Field.page_id == page.id).order_by(Field.id)
        ).all()

        data = {
            "page_type": page.page_type,
            "fields": [
                {"name": f.name, "value": f.ocr_value, "confidence": f.ocr_confidence}
                for f in fields
            ],
        }

        with open("page3_fields.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Done")


if __name__ == "__main__":
    dump_page(3)
