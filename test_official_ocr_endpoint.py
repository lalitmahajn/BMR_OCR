import os
import sys
import base64
import json
import requests
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.schemas.qc_report import QCReportSchema

load_dotenv()
api_key = os.environ.get("MISTRAL_API_KEY")

if not api_key:
    print("WARNING: MISTRAL_API_KEY environment variable is not set!")
    sys.exit(1)

# Pick an image from the images directory
image_path = "data/images/p1_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.jpg"
if not os.path.exists(image_path):
    print(f"File not found: {image_path}")
    sys.exit(1)

with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# The schema definition we want Mistral to output
schema_rules = json.dumps(QCReportSchema.model_json_schema(), indent=2)

# Using exactly the official Mistral format for /v1/ocr
# https://docs.mistral.ai/api/endpoint/ocr#operation-ocr_v1_ocr_post
payload = {
    "model": "mistral-ocr-latest",
    "document": {
        "type": "document_url",
        "document_url": f"data:image/jpeg;base64,{image_data}"
    },
    # The OCR endpoint requires mapping instructions directly into this specific prompt parameter
    "document_annotation_prompt": f"Extract all the information from this QC test report into a structured JSON exactly matching this JSON schema:\n{schema_rules}",
    "document_annotation_format": {
        "type": "json_schema",
        "json_schema": {
            "name": "qc_report_structure",
            "schema": QCReportSchema.model_json_schema()
        }
    }
}

print(f"=== Testing Mistral official /v1/ocr endpoint ===")
print("Sending request... (This will take a few seconds)")

response = requests.post(
    "https://api.mistral.ai/v1/ocr",
    headers=headers,
    json=payload
)

print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    print("\nSUCCESS! Here is the response structure:")
    data = response.json()
    
    # Mistral nests the output inside pages -> document_annotation
    if "pages" in data and len(data["pages"]) > 0:
        page_0 = data["pages"][0]
        
        # Check standard markdown extraction
        if "markdown" in page_0:
            print(f" -> Got Markdown Text: {len(page_0['markdown'])} chars")
            
        # Check JSON extraction
        if "document_annotation" in page_0:
            print("\n=== EXTRACTED JSON STRUCTURE ===")
            print(page_0["document_annotation"])
            
            # Print parsed formatted version
            print("\n=== PARSED JSON ===")
            try:
                parsed = json.loads(page_0["document_annotation"])
                print(json.dumps(parsed, indent=2))
            except Exception as e:
                print(f"Failed to parse document_annotation as JSON: {e}")
        else:
            print(" -> Warning: No 'document_annotation' key found in the page object!")
            
else:
    print("\nFAILED: Received HTTP Error")
    print(json.dumps(response.json(), indent=2))
