import argparse
import sys
import uvicorn
from pathlib import Path
from loguru import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.models.base import Base
from app.engines.storage import StorageEngine
from app.orchestrator import Orchestrator
from app.routers import verification

# --- FastAPI App Definition ---
app = FastAPI(title="BMR OCR Verification API")

# Configure CORS (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(verification.router)


@app.get("/")
def root():
    return {"message": "BMR OCR Engine API is running"}


# --- CLI Functions ---


def init_db():
    logger.info("Initializing Database...")
    storage = StorageEngine()
    # Create all tables
    Base.metadata.create_all(storage.engine)
    logger.info("Database initialized.")


def run_server(host: str = "0.0.0.0", port: int = 8000):
    logger.info(f"Starting API Server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


def main():
    parser = argparse.ArgumentParser(description="Document Intelligence Engine CLI")
    parser.add_argument(
        "--process", help="Path to document (PDF/Image) to process", type=str
    )
    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database tables"
    )
    parser.add_argument(
        "--server", action="store_true", help="Start the Verification API Server"
    )

    args = parser.parse_args()

    if args.init_db:
        init_db()
        return

    if args.server:
        run_server()
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
