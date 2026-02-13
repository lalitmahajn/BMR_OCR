"""
Mistral OCR Adapter
Implements OCR interface using Mistral AI's cloud OCR API
"""

import os
import base64
import time
from pathlib import Path
from typing import Optional, List
from loguru import logger

from mistralai import Mistral
from dotenv import load_dotenv

from app.engines.ocr import OCRAdapter, OCRResult
from app.schemas.template import ROI
from app.utils.mistral_parser import parse_qc_report, clean_ocr_artifacts


# Load environment variables
load_dotenv()


class MistralOCRAdapter(OCRAdapter):
    """
    Mistral AI OCR Adapter
    Uses Mistral's cloud OCR API to extract text from images/PDFs
    Returns markdown-formatted structured content
    """

    def __init__(
        self, api_key: Optional[str] = None, model: str = "mistral-ocr-latest"
    ):
        """
        Initialize Mistral OCR adapter

        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model: OCR model to use (default: mistral-ocr-latest)
        """
        self.api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        self.model = model
        self.max_retries = int(os.environ.get("MISTRAL_MAX_RETRIES", "3"))
        self.timeout = int(os.environ.get("MISTRAL_TIMEOUT", "30"))

        if not self.api_key or self.api_key == "your_api_key_here":
            logger.error("Mistral API key not configured!")
            self.client = None
        else:
            self.client = Mistral(api_key=self.api_key)
            logger.info("Mistral OCR adapter initialized successfully")

    def extract_text(self, image_path: str, roi: Optional[ROI] = None) -> OCRResult:
        """
        Extract text from image using Mistral OCR with persistent caching.
        """
        if not self.client:
            logger.error("Mistral client not initialized - missing API key")
            return OCRResult("", 0.0)

        # 1. Check Cache
        img_path_obj = Path(image_path)
        # Assuming cache is in the same directory with .md extension
        cache_file = img_path_obj.with_suffix(".md")

        if cache_file.exists():
            try:
                logger.info(f"Loading cached Mistral OCR for {img_path_obj.name}")
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_text = f.read()
                return OCRResult(cached_text, 1.0)  # High confidence for cache
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")

        if roi:
            logger.warning(
                "ROI-based extraction not supported in Mistral OCR - extracting full page"
            )

        try:
            # Read and encode image
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Determine image type
            suffix = img_path_obj.suffix.lower()
            mime_type = "image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png"

            # Call Mistral OCR API with retry logic
            markdown_text = self._call_mistral_api_with_retry(image_data, mime_type)

            if not markdown_text:
                return OCRResult("", 0.0)

            # Clean OCR artifacts
            cleaned_text = clean_ocr_artifacts(markdown_text)

            # 2. Save to Cache
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                logger.info(f"Saved Mistral OCR result to cache: {cache_file.name}")
            except Exception as e:
                logger.error(f"Failed to save Mistral OCR result to cache: {e}")

            # Return with high confidence
            return OCRResult(cleaned_text, 0.95)

        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
            return OCRResult("", 0.0)
        except Exception as e:
            logger.error(f"Mistral OCR extraction failed: {e}")
            return OCRResult("", 0.0)

    def _call_mistral_api_with_retry(self, image_data: str, mime_type: str) -> str:
        """
        Call Mistral OCR API with exponential backoff retry logic

        Args:
            image_data: Base64-encoded image
            mime_type: MIME type of the image

        Returns:
            Markdown text from OCR
        """
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Calling Mistral OCR API (attempt {attempt + 1}/{self.max_retries})"
                )

                response = self.client.ocr.process(
                    model=self.model,
                    document={
                        "type": "image_url",
                        "image_url": f"data:{mime_type};base64,{image_data}",
                    },
                )

                # Extract markdown from response
                if hasattr(response, "pages") and len(response.pages) > 0:
                    markdown = response.pages[0].markdown
                    logger.info(f"Mistral OCR successful: {len(markdown)} characters")
                    return markdown
                else:
                    logger.warning("No pages in Mistral OCR response")
                    return ""

            except Exception as e:
                logger.warning(f"Mistral API call failed (attempt {attempt + 1}): {e}")

                if attempt < self.max_retries - 1:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All Mistral API retry attempts exhausted")
                    return ""

        return ""

    def extract_from_pdf(self, pdf_path: str) -> List[str]:
        """
        Extract text from multi-page PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of markdown strings, one per page
        """
        if not self.client:
            logger.error("Mistral client not initialized")
            return []

        try:
            # Read and encode PDF
            with open(pdf_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode("utf-8")

            logger.info(f"Processing PDF: {pdf_path}")

            response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{pdf_data}",
                },
            )

            # Extract markdown from all pages
            if hasattr(response, "pages") and response.pages:
                pages_markdown = [page.markdown for page in response.pages]
                logger.info(f"Extracted {len(pages_markdown)} pages from PDF")
                return pages_markdown
            else:
                logger.warning("No pages in PDF OCR response")
                return []

        except Exception as e:
            logger.error(f"PDF OCR extraction failed: {e}")
            return []

    def parse_qc_report_fields(self, markdown: str) -> dict:
        """
        Parse QC report fields from markdown

        Args:
            markdown: Markdown text from OCR

        Returns:
            Dictionary with extracted fields
        """
        return parse_qc_report(markdown)
