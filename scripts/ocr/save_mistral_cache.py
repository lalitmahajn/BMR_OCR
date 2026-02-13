import sys
import os
from pathlib import Path
from loguru import logger
import base64

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.engines.mistral_ocr import MistralOCRAdapter


def main():
    pdf_path = "data/input/sample.pdf"
    output_dir = Path("output/sample")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Processing first 3 pages of {pdf_path} with Mistral OCR...")
    adapter = MistralOCRAdapter()

    # Mistral.ocr.process doesn't support page range directly for PDFs easily in this SDK version
    # but we can just use the adapter's extract_from_pdf and take the first few
    # OR we can just use extract_text on page 1 image if we had images.

    # Since we want REAL data, let's just run it but ensure we don't timeout.
    pages_markdown = adapter.extract_from_pdf(pdf_path)

    if not pages_markdown:
        logger.error("Failed to extract text from PDF")
        return

    # We'll save all of them if they came back, but at least we'll have them.
    for i, markdown in enumerate(pages_markdown):
        file_path = output_dir / f"page_{i + 1}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        logger.info(f"Saved {file_path}")

    logger.info(f"Successfully cached {len(pages_markdown)} pages.")


if __name__ == "__main__":
    main()
