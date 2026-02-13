import os
import json
import base64
import time
from pathlib import Path
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment
load_dotenv()
api_key = os.environ.get("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

# Configuration
PDF_PATH = r"data\input\sample.pdf"
BATCH_INPUT_FILE = "batch_input.jsonl"
OUTPUT_DIR = Path("output/batch_ocr_results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("BATCH OCR PROCESSING")
print("=" * 80)
print(f"Input: {PDF_PATH}")
print(f"Output: {OUTPUT_DIR}/\n")

# ==================== STEP 1: CREATE BATCH INPUT ====================
print("Step 1: Creating batch input file...")

# Read and encode PDF
with open(PDF_PATH, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode("utf-8")

# Create JSONL with single PDF entry
batch_entry = {
    "custom_id": "sample_pdf",
    "body": {
        "document": {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{pdf_data}",
        },
        "include_image_base64": False,
    },
}

with open(BATCH_INPUT_FILE, "w", encoding="utf-8") as f:
    f.write(json.dumps(batch_entry) + "\n")

print(f"✓ Batch input created: {BATCH_INPUT_FILE}")

# ==================== STEP 2: UPLOAD FILE ====================
print("\nStep 2: Uploading batch file to Mistral...")

with open(BATCH_INPUT_FILE, "rb") as f:
    uploaded_file = client.files.upload(
        file={"file_name": BATCH_INPUT_FILE, "content": f}, purpose="batch"
    )

file_id = uploaded_file.id
print(f"✓ File uploaded: {file_id}")

# ==================== STEP 3: CREATE BATCH JOB ====================
print("\nStep 3: Creating batch OCR job...")

batch_job = client.batch.jobs.create(
    input_files=[file_id], model="mistral-ocr-latest", endpoint="/v1/ocr"
)

job_id = batch_job.id
print(f"✓ Batch job created: {job_id}")
print(f"  Status: {batch_job.status}")

# ==================== STEP 4: WAIT FOR COMPLETION ====================
print("\nStep 4: Waiting for batch job to complete...")
print("(This may take a few minutes for 30-page PDF...)\n")

check_count = 0
while True:
    job = client.batch.jobs.get(job_id=job_id)
    status = job.status

    check_count += 1
    print(f"[Check #{check_count}] Status: {status}", end="")

    # Show progress if available
    if hasattr(job, "metadata") and job.metadata:
        total = job.metadata.get("total_requests", 0)
        completed = job.metadata.get("completed_requests", 0)
        if total > 0:
            print(f" | Progress: {completed}/{total}", end="")
    print()

    if status == "SUCCESS":
        print("\n✓ Batch job completed successfully!")
        break
    elif status in ["FAILED", "CANCELLED", "EXPIRED"]:
        print(f"\n✗ Batch job {status.lower()}!")
        exit(1)

    # Wait 10 seconds before next check
    time.sleep(10)

# ==================== STEP 5: DOWNLOAD RESULTS ====================
print("\nStep 5: Downloading results...")

if not job.output_file:
    print("✗ No output file available")
    exit(1)

result_content = client.files.download(file_id=job.output_file)

results_file = "batch_output.jsonl"
with open(results_file, "wb") as f:
    f.write(result_content.content)

print(f"✓ Results downloaded: {results_file}")

# ==================== STEP 6: PARSE AND SAVE RESULTS ====================
print("\nStep 6: Parsing results...")

# Read JSONL results
with open(results_file, "r", encoding="utf-8") as f:
    result_line = f.readline()
    result_data = json.loads(result_line)

# Extract pages
response_body = result_data.get("response", {}).get("body", {})
pages = response_body.get("pages", [])
num_pages = len(pages)

print(f"✓ Extracted {num_pages} pages")

# Save each page
for idx, page in enumerate(pages):
    page_num = idx + 1
    markdown = page.get("markdown", "")

    # Save individual page
    page_file = OUTPUT_DIR / f"page_{page_num}.md"
    with open(page_file, "w", encoding="utf-8") as f:
        f.write(f"# Page {page_num}\n\n")
        f.write(markdown)

    print(f"  ✓ Saved: page_{page_num}.md")

# Save combined document
combined_file = OUTPUT_DIR / "full_document.md"
with open(combined_file, "w", encoding="utf-8") as f:
    for idx, page in enumerate(pages):
        f.write(f"# Page {idx + 1}\n\n")
        f.write(page.get("markdown", ""))
        f.write("\n\n---\n\n")

print(f"  ✓ Saved: full_document.md")

# Save metadata
usage_info = response_body.get("usage_info", {})
metadata = {
    "pdf_file": PDF_PATH,
    "total_pages": num_pages,
    "model": response_body.get("model", "mistral-ocr-latest"),
    "doc_size_bytes": usage_info.get("doc_size_bytes", 0),
    "pages_processed": usage_info.get("pages_processed", num_pages),
    "processing_method": "batch",
    "cost_estimate": f"${num_pages * 0.001:.4f}",
    "batch_job_id": job_id,
}

metadata_file = OUTPUT_DIR / "metadata.json"
with open(metadata_file, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)

print(f"  ✓ Saved: metadata.json")

# ==================== SUMMARY ====================
print("\n" + "=" * 80)
print("BATCH PROCESSING COMPLETE")
print("=" * 80)
print(f"\nTotal pages: {num_pages}")
print(f"\nCost Comparison:")
print(f"  Regular OCR: ${num_pages * 0.002:.4f}")
print(f"  Batch OCR:   ${num_pages * 0.001:.4f} ✅")
print(f"  Savings:     ${num_pages * 0.001:.4f} (50%)")
print(f"\nAll files saved to: {OUTPUT_DIR}/")
