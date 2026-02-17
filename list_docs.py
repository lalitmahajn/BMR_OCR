from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.models.domain import Document
import sys
import os

sys.path.append(os.getcwd())


def list_docs():
    engine = create_engine("sqlite:///./sql_app.db")
    with Session(engine) as session:
        docs = session.scalars(select(Document).order_by(Document.id)).all()
        print(f"{'ID':<5} {'Filename':<40} {'Ingested At'}")
        print("-" * 60)
        for d in docs:
            print(f"{d.id:<5} {d.filename:<40} {d.ingested_at}")


if __name__ == "__main__":
    list_docs()
