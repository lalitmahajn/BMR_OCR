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

# Call Mistral OCR
ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_data}"},
)

# Extract results
if hasattr(ocr_response, "pages") and len(ocr_response.pages) > 0:
    markdown_text = ocr_response.pages[0].markdown

    # Save markdown
    with open("mistral_ocr_output.md", "w", encoding="utf-8") as f:
        f.write(markdown_text)

    # Save JSON
    result_json = {
        "model": ocr_response.model,
        "pages_processed": ocr_response.usage_info.pages_processed,
        "doc_size_bytes": ocr_response.usage_info.doc_size_bytes,
        "markdown": markdown_text,
    }
    with open("mistral_ocr_output.json", "w", encoding="utf-8") as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)

    # Print results
    print("=" * 80)
    print("MISTRAL OCR RESULTS")
    print("=" * 80)
    print(markdown_text)
    print("=" * 80)
    print(f"\n✓ Saved: mistral_ocr_output.md")
    print(f"✓ Saved: mistral_ocr_output.json")
    print(f"✓ Pages processed: {ocr_response.usage_info.pages_processed}")
    print(f"✓ Document size: {ocr_response.usage_info.doc_size_bytes:,} bytes")
else:
    print("ERROR: No pages in OCR response")
    print(ocr_response)
