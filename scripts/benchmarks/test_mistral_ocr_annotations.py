import os
import json
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.environ.get("MISTRAL_API_KEY")
if not api_key or api_key == "your_api_key_here":
    print("ERROR: MISTRAL_API_KEY not configured in .env file")
    exit(1)

client = Mistral(api_key=api_key)

# Process BMR document
IMAGE_PATH = r"data\images\b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af_p1.jpg"
print(f"Processing: {IMAGE_PATH}\n")

# Convert to base64
import base64

with open(IMAGE_PATH, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Define document annotation schema for structured extraction
document_annotation_format = {
    "type": "object",
    "properties": {
        "product_info": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string"},
                "batch_no": {"type": "string"},
                "manufacturing_date": {"type": "string"},
                "approval_date": {"type": "string"},
                "expiry_date": {"type": "string"},
                "quantity": {"type": "string"},
                "ar_no": {"type": "string"},
            },
        },
        "test_parameters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sr_no": {"type": "integer"},
                    "parameter": {"type": "string"},
                    "result": {"type": "string"},
                },
            },
        },
    },
}

print("Calling Mistral OCR with annotations enabled...\n")

# Call Mistral OCR with annotations
ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
    include_image_base64=False,
    # Enable document annotation for structured extraction
    document_annotation={
        "format": document_annotation_format,
        "requirements": "Extract product information and all test parameters from the QC Test Report",
    },
)

# Extract results
print("=" * 80)
print("MISTRAL OCR RESULTS WITH ANNOTATIONS")
print("=" * 80 + "\n")

if hasattr(ocr_response, "pages") and len(ocr_response.pages) > 0:
    page = ocr_response.pages[0]

    # Save markdown
    if hasattr(page, "markdown"):
        with open("mistral_ocr_output.md", "w", encoding="utf-8") as f:
            f.write(page.markdown)
        print("✓ Markdown saved: mistral_ocr_output.md")

    # Check for document annotation
    if (
        hasattr(ocr_response, "document_annotation")
        and ocr_response.document_annotation
    ):
        print("✓ Document annotations found!")
        print("\n" + "-" * 80)
        print("STRUCTURED EXTRACTED DATA:")
        print("-" * 80)
        print(json.dumps(ocr_response.document_annotation, indent=2))

        # Save structured data
        with open("mistral_structured_data.json", "w", encoding="utf-8") as f:
            json.dump(ocr_response.document_annotation, f, indent=2, ensure_ascii=False)
        print("\n✓ Structured data saved: mistral_structured_data.json")

    # Check for bounding boxes
    if hasattr(page, "bboxes"):
        print(f"\n✓ Found {len(page.bboxes)} bounding boxes")
        bbox_data = []
        for idx, bbox in enumerate(page.bboxes):
            bbox_info = {
                "index": idx,
                "coordinates": bbox if isinstance(bbox, dict) else str(bbox),
            }
            bbox_data.append(bbox_info)

        with open("mistral_bboxes.json", "w", encoding="utf-8") as f:
            json.dump(bbox_data, f, indent=2)
        print("✓ Bounding boxes saved: mistral_bboxes.json")

    # Save complete response
    response_data = {
        "model": ocr_response.model,
        "usage_info": {
            "pages_processed": ocr_response.usage_info.pages_processed,
            "doc_size_bytes": ocr_response.usage_info.doc_size_bytes,
        },
        "markdown": page.markdown if hasattr(page, "markdown") else None,
        "document_annotation": ocr_response.document_annotation
        if hasattr(ocr_response, "document_annotation")
        else None,
        "has_bboxes": hasattr(page, "bboxes"),
    }

    with open("mistral_full_response.json", "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)
    print("✓ Full response saved: mistral_full_response.json")

print("\n" + "=" * 80)
print(f"Pages processed: {ocr_response.usage_info.pages_processed}")
print(f"Document size: {ocr_response.usage_info.doc_size_bytes:,} bytes")
print("=" * 80)
