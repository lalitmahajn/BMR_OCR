import json
from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path.cwd()))

from app.engines.extraction import MarkdownExtractionEngine
from app.engines.template import TemplateEngine
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def generate_full_report():
    template_dir = Path("templates")
    template_engine = TemplateEngine(template_dir=template_dir)
    extraction_engine = MarkdownExtractionEngine()

    sop_template = template_engine.get_template("SOP")

    pages = [13, 14, 15, 16, 17, 18]
    images_dir = Path("data/images")

    results = {}

    for p in pages:
        # Find file ending with _p{p}.md OR p{p}_*.md
        candidates = list(images_dir.glob(f"p{p}_*.md"))
        if not candidates:
            candidates = list(images_dir.glob(f"*_p{p}.md"))

        if not candidates:
            logger.warning(f"No markdown file found for Page {p}")
            continue

        md_path = candidates[0]

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        extraction_result = extraction_engine.process_nested_template(
            md_content, sop_template.extraction_template
        )

        # Clean up for display
        clean_headers = {
            k: v.get("value")
            for k, v in extraction_result.get("headers", {}).items()
            if v.get("value")
        }

        # Simplify rows for display (show first 3 rows + count)
        clean_rows = [r.get("extracted") for r in extraction_result.get("rows", [])]

        results[f"Page {p}"] = {
            "Headers": clean_headers,
            "Table Data": clean_rows,
            "Total Table Rows": len(clean_rows),
        }

    output_file = Path("output/sop_verification_report.json")
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Report saved to {output_file}")


if __name__ == "__main__":
    generate_full_report()
