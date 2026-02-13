import sys
import json
from pathlib import Path
from app.engines.extraction import MarkdownExtractionEngine
from app.engines.template import TemplateEngine
from loguru import logger

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def test_bmr_extraction():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template
    template = template_engine.get_template("BMR")
    if not template:
        logger.error("BMR template not found!")
        return

    # 3. Test Pages
    images_dir = Path("data/images")
    test_pages = ["p19", "p20", "p21", "p22", "p23", "p24", "p25", "p26"]

    for p_name in test_pages:
        # Find md file
        md_files = list(images_dir.glob(f"{p_name}_*.md"))
        if not md_files:
            logger.warning(f"MD file for {p_name} not found.")
            continue

        md_path = md_files[0]
        logger.info(f"--- Testing {p_name} ({md_path.name}) ---")

        with open(md_path, "r", encoding="utf-8") as f:
            ocr_text = f.read()

        # 4. Extract
        res = extraction_engine.process_nested_template(
            ocr_text, template.extraction_template
        )

        # 5. Write Results to File
        output_file = Path("bmr_test_results.txt")
        mode = "a" if output_file.exists() else "w"

        with open(output_file, mode, encoding="utf-8") as out:
            out.write(f"\n{'=' * 40}\n")
            out.write(f"RESULTS FOR {p_name} ({md_path.name})\n")
            out.write(f"{'=' * 40}\n")

            out.write("\n[HEADERS]\n")
            for k in sorted(res["headers"].keys()):
                v = res["headers"][k]["value"]
                if v and len(v) > 50:
                    v = v[:47] + "..."
                out.write(f"  {k:<20}: {v}\n")

            out.write(f"\n[TABLES] - Found {len(res['rows'])} rows\n")

            tables = {}
            for row in res["rows"]:
                t_name = row["extracted"].get("_table_name", "Unknown Table")
                if t_name not in tables:
                    tables[t_name] = []
                tables[t_name].append(row["extracted"])

            for t_name, rows in tables.items():
                out.write(f"\n  Table: {t_name} ({len(rows)} rows)\n")
                if rows:
                    out.write(f"    Sample Row: {rows[0]}\n")

            out.write("\n")

    print(f"Results written to {output_file.resolve()}")


if __name__ == "__main__":
    test_bmr_extraction()
