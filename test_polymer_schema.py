import sys
import json
import os
import glob
from loguru import logger
from app.engines.mistral_ocr import MistralOCRAdapter
from app.schemas.worksheet_polymer import PolymerWorksheetSchema

logger.remove()
logger.add(sys.stderr, level="INFO")

def get_image(basename):
    matches = glob.glob(f"data/images/{basename}.*")
    matches = [m for m in matches if not m.endswith('.md') and not m.endswith('.json')]
    return matches[0] if matches else None

def test_schema():
    print("Locating image files for extraction...")
    image_paths = [
        get_image("p3_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af"),
        get_image("p4_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af"),
        get_image("p5_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af")
    ]
    
    if not all(image_paths):
        print(f"Error: Could not find all images. Found: {image_paths}")
        return

    print(f"Using images: {image_paths}")
    adapter = MistralOCRAdapter()
    
    print("\nSending images to Mistral for structured extraction...")
    print("This might take a minute depending on the API speed.\n")
    
    try:
        result = adapter.extract_structured_data(image_paths, PolymerWorksheetSchema)
        if result:
            print("\n*** Extraction Successful! ***\nValidated Structure:")
            print(json.dumps(result, indent=2))
            
            # Save the result to a readable json file for inspection
            out_file = "test_polymer_result.json"
            with open(out_file, "w") as f:
                json.dump(result, f, indent=4)
            print(f"\nResult also saved to {out_file}")
            
        else:
            print("\nExtraction failed or returned None.")
            
    except Exception as e:
        print(f"\nAn error occurred during extraction: {e}")

if __name__ == "__main__":
    test_schema()
