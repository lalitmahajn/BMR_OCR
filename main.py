import argparse
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings
from app.models.base import Base
from app.engines.storage import StorageEngine
from app.orchestrator import Orchestrator


def init_db():
    logger.info("Initializing Database...")
    storage = StorageEngine()
    # Create all tables
    Base.metadata.create_all(storage.engine)
    logger.info("Database initialized.")


def main():
    parser = argparse.ArgumentParser(description="Document Intelligence Engine CLI")
    parser.add_argument(
        "--process", help="Path to document (PDF/Image) to process", type=str
    )
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database tables"
    )

    args = parser.parse_args()

    if args.init_db:
        init_db()
        return

    if args.process:
        input_path = Path(args.process)
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)

        orchestrator = Orchestrator()
        orchestrator.process_document(str(input_path))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
