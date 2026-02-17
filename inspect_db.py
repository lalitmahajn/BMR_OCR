from sqlalchemy import create_engine, inspect
import sys
import os

sys.path.append(os.getcwd())


def inspect_db():
    engine = create_engine("sqlite:///./sql_app.db")
    inspector = inspect(engine)
    columns = [c["name"] for c in inspector.get_columns("documents")]
    print(f"Columns in 'documents' table: {columns}")


if __name__ == "__main__":
    inspect_db()
