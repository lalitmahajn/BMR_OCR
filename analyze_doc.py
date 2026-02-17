from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from app.models.domain import Page, Field
import sys
import os

sys.path.append(os.getcwd())


def analyze_doc(doc_id):
    engine = create_engine("sqlite:///./sql_app.db")
    with Session(engine) as session:
        pages = session.scalars(
            select(Page).where(Page.document_id == doc_id).order_by(Page.page_number)
        ).all()

        print(f"Document {doc_id} Analysis:")
        print(f"{'Page':<5} {'Type':<30} {'Fields Found'}")
        print("-" * 50)

        for p in pages:
            field_count = session.scalar(
                select(func.count()).where(Field.page_id == p.id)
            )
            print(f"{p.page_number:<5} {str(p.page_type):<30} {field_count}")


if __name__ == "__main__":
    analyze_doc(1)
