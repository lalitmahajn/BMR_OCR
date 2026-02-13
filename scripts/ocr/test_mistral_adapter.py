"""
Test Mistral OCR Adapter
Quick test to verify the adapter works correctly with PDF files
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parents[2]))

from app.engines.mistral_ocr import MistralOCRAdapter
from app.engines.ocr import OCRResult
from loguru import logger

# Configure logger
logger.add("test_mistral_adapter.log", rotation="10 MB")

if __name__ == "__main__":
    # Initialize adapter
    logger.info("Initializing Mistral OCR Adapter...")
    adapter = MistralOCRAdapter()

    # Test PDF
    test_pdf = "data/input/sample.pdf"

    if not Path(test_pdf).exists():
        logger.error(f"Test PDF not found: {test_pdf}")
        sys.exit(1)

    logger.info(f"Processing: {test_pdf}")

    # Extract text from first page only (to save credits)
    logger.info("Extracting first page only...")
    pages_markdown = adapter.extract_from_pdf(test_pdf)

    if not pages_markdown:
        logger.error("No pages extracted!")
        sys.exit(1)

    result_text = pages_markdown[0]

    # Display results
    print("=" * 80)
    print("MISTRAL OCR ADAPTER TEST - PDF")
    print("=" * 80)
    print(f"Total Pages Available: {len(pages_markdown)}")
    print(f"Page 1 Text length: {len(result_text)} characters")
    print("\\nExtracted Text (Page 1 - First 1500 chars):")
    print("-" * 80)
    print(result_text[:1500])
    if len(result_text) > 1500:
        print(f"\\n... ({len(result_text) - 1500} more characters)")
    print("=" * 80)

    # Parse QC report fields from first page
    if result_text:
        logger.info("Parsing QC report fields...")
        parsed_data = adapter.parse_qc_report_fields(result_text)

        print("\\nPARSED FIELDS (Page 1):")
        print("-" * 80)
        print("\\nProduct Info:")
        if parsed_data["product_info"]:
            for key, value in parsed_data["product_info"].items():
                print(f"  {key}: {value}")
        else:
            print("  (No product info found)")

        print(f"\\nTest Parameters ({len(parsed_data['test_parameters'])} found):")
        if parsed_data["test_parameters"]:
            for param in parsed_data["test_parameters"][:8]:  # Show first 8
                print(
                    f"  {param['sr_no']}. {param['test_parameter']}: {param['result']}"
                )

            if len(parsed_data["test_parameters"]) > 8:
                print(f"  ... and {len(parsed_data['test_parameters']) - 8} more")
        else:
            print("  (No test parameters found)")

        print("=" * 80)
        logger.info("✓ Test completed successfully!")
        print("\\n✓ Adapter works correctly!")
        print(f"✓ Extracted {len(pages_markdown)} pages")
        print(f"✓ Parsed {len(parsed_data['product_info'])} product fields")
        print(f"✓ Parsed {len(parsed_data['test_parameters'])} test parameters")
    else:
        logger.error("No text extracted!")
        sys.exit(1)
