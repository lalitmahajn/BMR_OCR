import sys
import os

# Add the project root to sys.path to allow imports from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.engines.classification import PageClassificationEngine, PageType
from loguru import logger


def test_classification():
    engine = PageClassificationEngine()

    test_cases = [
        {
            "name": "Exact Markdown Match - QC",
            "text": "# Finished Good Q.C. Test Report for Speciality Chemicals\nBatch No: 123",
            "expected": PageType.QC_TEST_REPORT,
        },
        {
            "name": "Markdown Match - BMR Checklist",
            "text": "## BMR Review Checklist\nDate: 2023-01-01",
            "expected": PageType.BMR_CHECKLIST,
        },
        {
            "name": "Exact Match - Production Report",
            "text": "PRODUCTION REPORT\nShift: A",
            "expected": PageType.PRODUCTION_REPORT,
        },
        {
            "name": "Fuzzy Match - Minor OCR error",
            "text": "BATCH MANUFACTORING RECORD (BMR)\nProduct: RL-5065",
            "expected": PageType.BMR,
        },
        {
            "name": "Email Detection - Google Mail",
            "text": "Subject: Order Update\n...\nView in mail.google.com",
            "expected": PageType.EMAIL,
        },
        {
            "name": "Short Header Error - Stores Requisition",
            "text": "STORES REQ\nSLIP POLYMER",
            "expected": PageType.STORES_REQUISITION,
        },
        {
            "name": "Unknown Page Type",
            "text": "Random document text with no identifiable header",
            "expected": PageType.UNKNOWN,
        },
    ]

    print("\n" + "=" * 50)
    print("CLASSIFICATION ENGINE TEST RESULTS")
    print("=" * 50)

    passed = 0
    for case in test_cases:
        result = engine.classify(case["text"], context=case["name"])
        status = (
            "✅ PASS"
            if result == case["expected"]
            else f"❌ FAIL (Expected {case['expected'].name}, got {result.name})"
        )
        print(f"{case['name']:<30}: {status}")
        if result == case["expected"]:
            passed += 1

    print("=" * 50)
    print(f"Summary: {passed}/{len(test_cases)} cases passed")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    # Remove existing classification_report.txt if exists
    if os.path.exists("classification_report.txt"):
        os.remove("classification_report.txt")

    test_classification()
