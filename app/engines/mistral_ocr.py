"""
Mistral OCR Adapter
Implements OCR interface using Mistral AI's cloud OCR API
"""

import os
import base64
import time
import json
from pathlib import Path
from typing import Optional, List, Type, Union
from loguru import logger
from pydantic import BaseModel

from mistralai.client import Mistral
from mistralai.extra import response_format_from_pydantic_model
import fitz  # PyMuPDF
from dotenv import load_dotenv

from app.engines.ocr import OCRAdapter, OCRResult
from app.schemas.template import ROI


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

            # Clean OCR artifacts (inline)
            import re as _re

            # Preserve newlines while normalizing horizontal whitespace
            cleaned_text = _re.sub(
                r"[^\S\n]+", " ", markdown_text
            )  # Collapse spaces/tabs but keep \n
            cleaned_text = _re.sub(
                r"\n{3,}", "\n\n", cleaned_text
            )  # Collapse excess blank lines
            cleaned_text = _re.sub(r"[_]{3,}", "", cleaned_text)
            cleaned_text = _re.sub(r"\.{3,}", "", cleaned_text).strip()

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

    def extract_structured_data(
        self, image_paths: Union[str, List[str]], schema_class: Type[BaseModel]
    ) -> Optional[dict]:
        """
        Extract structured data using Mistral's native JSON Schema extraction (Pattern B).
        Bypasses Markdown parsing entirely.

        Args:
            image_path: Path to the image file
            schema_class: The Pydantic BaseModel class defining the expected JSON structure

        Returns:
            A python dictionary containing the structured data, or None if it fails.
        """
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        img_path_obj = Path(image_paths[0])
        
        # 1. Check Cache (Use first image's name as base, but add count to distinguish)
        cache_name = f"{img_path_obj.stem}_multi_{len(image_paths)}_{schema_class.__name__}.json"
        cache_file = img_path_obj.parent / cache_name

        if cache_file.exists():
            try:
                logger.info(
                    f"Loading cached Structured Mistral OCR for {len(image_paths)} pages starting with {img_path_obj.name}"
                )
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read cache file {cache_file}: {e}")

        try:
            temp_pdf_path = None
            if len(image_paths) == 1:
                # Single image or PDF
                image_path = image_paths[0]
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                
                suffix = Path(image_path).suffix.lower()
                mime_type = "application/pdf" if suffix == ".pdf" else ("image/jpeg" if suffix in [".jpg", ".jpeg"] else "image/png")
            else:
                # Multiple images - Merge into PDF
                logger.info(f"Merging {len(image_paths)} images into temporary PDF for extraction")
                doc = fitz.open()
                for img_p in image_paths:
                    imgdoc = fitz.open(img_p)
                    pdfbytes = imgdoc.convert_to_pdf()
                    imgpdf = fitz.open("pdf", pdfbytes)
                    doc.insert_pdf(imgpdf)
                
                temp_pdf_path = f"tmp_merge_{int(time.time())}.pdf"
                doc.save(temp_pdf_path)
                doc.close()

                with open(temp_pdf_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
                mime_type = "application/pdf"
                
                # Clean up temp PDF immediately after reading into memory
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

            # Execute Pattern B: Native OCR Structured Extraction
            logger.info(
                f"Calling Mistral OCR API with Pattern B (Structured) for {schema_class.__name__}"
            )

            for attempt in range(self.max_retries):
                try:
                    # Use the official helper to convert Pydantic to the correct format property
                    annotation_format = response_format_from_pydantic_model(schema_class)
                    
                    doc_payload = {
                        "type": "document_url" if mime_type == "application/pdf" else "image_url",
                    }
                    if mime_type == "application/pdf":
                        doc_payload["document_url"] = f"data:{mime_type};base64,{image_data}"
                    else:
                        doc_payload["image_url"] = f"data:{mime_type};base64,{image_data}"
                    
                    response = self.client.ocr.process(
                        model=self.model,
                        document=doc_payload,
                        document_annotation_format=annotation_format,
                        document_annotation_prompt=f"Extract all information from this document exactly into the following JSON schema: {schema_class.__name__}"
                    )

                    # Breakthrough: Structured JSON resides at Top-Level 'document_annotation' 
                    if hasattr(response, 'document_annotation') and response.document_annotation:
                        # Convert to dict and validate through schema class to trigger validators
                        if isinstance(response.document_annotation, str):
                            raw_dict = json.loads(response.document_annotation)
                        else:
                            raw_dict = response.document_annotation
                        
                        # Validate and dump to apply normalization (like CPS for Viscosity)
                        validated_data = schema_class.model_validate(raw_dict)
                        structured_json = validated_data.model_dump()
                        
                        # 2. Save to Cache
                        try:
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(structured_json, f, indent=4)
                            logger.info(
                                f"Saved Structured Result to cache: {cache_file.name}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Failed to save structured result to cache: {e}"
                            )

                        return structured_json
                    
                    logger.warning(f"No structured data returned for {schema_class.__name__}. Falling back to Markdown.")
                    break

                except Exception as e:
                    error_msg = str(e)
                    if len(error_msg) > 500:
                        error_msg = error_msg[:500] + "... [TRUNCATED DUE TO SIZE]"
                    
                    logger.warning(
                        f"Mistral Pattern B API call failed (attempt {attempt + 1}): {error_msg}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(2**attempt)
                    else:
                        logger.error(
                            "All Mistral API retry attempts exhausted for Pattern B"
                        )
                        return None

        except FileNotFoundError:
            logger.error(f"Image/Document file not found: {image_path}")
            return None
        except Exception as e:
            logger.error(f"Mistral Structured Data extraction failed: {e}")
            return None

        return None

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
