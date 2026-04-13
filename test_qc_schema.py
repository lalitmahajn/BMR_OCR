import json
from pathlib import Path
from dotenv import load_dotenv
from app.engines.mistral_ocr import MistralOCRAdapter
from app.schemas.qc_report import QCReportSchema

load_dotenv()

def test():
    adapter = MistralOCRAdapter()
    img = str(Path("data/images/p1_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.jpg"))
    
    # Delete cache to force fresh extraction
    cache_pattern = "p1_*_QCReportSchema.json"
    for f in Path("data/images").glob(cache_pattern):
        f.unlink()
        print(f"Deleted cache: {f.name}")
    
    result = adapter.extract_structured_data([img], QCReportSchema)
    if result:
        print("\n✅ SUCCESS — Extracted fields:\n")
        print(json.dumps(result, indent=2))
    else:
        print("\n❌ FAILED — No data returned")

if __name__ == "__main__":
    test()
