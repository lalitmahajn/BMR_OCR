import os
import json
import base64
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment
load_dotenv()
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

# Input PDF
PDF_PATH = r"data\input\sample.pdf"
OUTPUT_DIR = Path("output/sample_pdf_ocr")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("PROCESSING PDF WITH MISTRAL OCR")
print("=" * 80)
print(f"\nInput: {PDF_PATH}")
print(f"Output: {OUTPUT_DIR}/\n")

# Check if file exists
if not Path(PDF_PATH).exists():
    print(f"ERROR: File not found: {PDF_PATH}")
    exit(1)

# Read PDF and encode to base64
print("Reading PDF file...")
with open(PDF_PATH, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode("utf-8")

file_size_mb = len(pdf_data) * 0.75 / 1024 / 1024  # Approximate original size
print(f"✓ PDF loaded ({file_size_mb:.2f} MB)")

# Process with Mistral OCR
print("\nCalling Mistral OCR API...")
print("(This may take a moment for multi-page PDFs...)\n")

ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={
        "type": "document_url",
        "document_url": f"data:application/pdf;base64,{pdf_data}",
    },
    include_image_base64=False,
)

# Get results
num_pages = len(ocr_response.pages) if hasattr(ocr_response, "pages") else 0
print(f"✓ OCR completed!")
print(f"  Pages processed: {num_pages}")
print(f"  Document size: {ocr_response.usage_info.doc_size_bytes:,} bytes")

# Save each page as markdown
print(f"\nSaving results...")
all_pages_markdown = []

for idx, page in enumerate(ocr_response.pages):
    page_num = idx + 1

    # Save individual page
    page_file = OUTPUT_DIR / f"page_{page_num}.md"
    with open(page_file, "w", encoding="utf-8") as f:
        f.write(f"# Page {page_num}\n\n")
        f.write(page.markdown)

    all_pages_markdown.append(page.markdown)
    print(f"  ✓ Saved: page_{page_num}.md")

# Save combined document
combined_file = OUTPUT_DIR / "full_document.md"
with open(combined_file, "w", encoding="utf-8") as f:
    for idx, markdown in enumerate(all_pages_markdown):
        f.write(f"# Page {idx + 1}\n\n")
        f.write(markdown)
        f.write("\n\n---\n\n")

print(f"  ✓ Saved: full_document.md")

# Save metadata
metadata = {
    "pdf_file": PDF_PATH,
    "total_pages": num_pages,
    "model": ocr_response.model,
    "doc_size_bytes": ocr_response.usage_info.doc_size_bytes,
    "pages_processed": ocr_response.usage_info.pages_processed,
    "cost_estimate": f"${num_pages * 0.002:.4f}",
}

metadata_file = OUTPUT_DIR / "metadata.json"
with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(f"  ✓ Saved: metadata.json")

# Print summary
print("\n" + "=" * 80)
print("PROCESSING COMPLETE")
print("=" * 80)
print(f"\nTotal pages: {num_pages}")
print(f"Cost: ${num_pages * 0.002:.4f} (regular OCR)")
print(f"All files saved to: {OUTPUT_DIR}/")
print("\nNext steps:")
print("  1. Review extracted markdown files")
print("  2. Parse structured data from markdown")
print("  3. Validate against ground truth")
