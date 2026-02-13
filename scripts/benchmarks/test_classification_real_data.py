import sys
import os
import json
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.engines.classification import PageClassificationEngine, PageType


def main():
    cache_dir = Path("output/sample")
    gt_path = Path("data/ground_truth_sample.json")

    if not cache_dir.exists():
        logger.error(f"Cache directory {cache_dir} not found!")
        return

    if not gt_path.exists():
        logger.error(f"Ground truth file {gt_path} not found!")
        return

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    engine = PageClassificationEngine()

    print("\n" + "=" * 95)
    print(f"{'PAGE':<10} | {'GROUND TRUTH':<35} | {'CLASSIFIED AS':<30} | {'STATUS'}")
    print("-" * 95)

    passed = 0
    total = 0

    # Sort files by page number strictly
    files = sorted(cache_dir.glob("*.md"), key=lambda x: int(x.stem.split("_")[1]))

    for file_path in files:
        page_num = file_path.stem.split("_")[1]
        with open(file_path, "r", encoding="utf-8") as f:
            markdown = f.read()

        result = engine.classify(markdown, context=f"Page {page_num}")
        expected = ground_truth.get(page_num, "UNKNOWN")

        status = "✅ PASS" if result.page_type.name == expected else "❌ FAIL"

        # Display sub-info if available
        sub_info = (
            f" ({result.page_num}/{result.total_pages})" if result.page_num else ""
        )
        display_name = f"{result.page_type.name}{sub_info}"

        print(f"Page {page_num:<5} | {expected:<35} | {display_name:<30} | {status}")

        if result.page_type.name == expected:
            passed += 1
        total += 1

    print("=" * 95)
    print(
        f"Summary: {passed}/{total} correctly classified ({(passed / total) * 100:.1f}%)"
    )
    print("=" * 95 + "\n")


if __name__ == "__main__":
    main()
