import sys
import os
from pathlib import Path
from loguru import logger

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from app.engines.classification import PageClassificationEngine


def verify_page_4():
    engine = PageClassificationEngine()

    # We must run Page 3 first to set the context
    pages_to_run = ["3", "4", "5"]

    print("\nTargeted Verification for Page 4 (Interpolation Check):")
    print("-" * 60)

    for p_num in pages_to_run:
        file_path = Path(f"output/sample/page_{p_num}.md")
        with open(file_path, "r", encoding="utf-8") as f:
            markdown = f.read()

        # Suppress internal logs
        logger.remove()
        logger.add(sys.stdout, format="<green>{message}</green>", level="INFO")

        result = engine.classify(markdown, context=f"Page {p_num}")

        sub_info = (
            f" ({result.page_num}/{result.total_pages})"
            if result.page_num
            else " (MISSING INDEX)"
        )
        print(
            f"Page {p_num:<2} | Type: {result.page_type.name:<20} | Index: {sub_info}"
        )


if __name__ == "__main__":
    verify_page_4()
