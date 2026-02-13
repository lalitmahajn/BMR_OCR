import sys
from pathlib import Path
from loguru import logger
from app.engines.classification import PageClassificationEngine
from app.engines.extraction import MarkdownExtractionEngine
from app.engines.template import TemplateEngine

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_p18():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template (SOP)
    # Based on previous runs, P18 is SOP
    template = template_engine.get_template("SOP")
    if not template:
        logger.error("SOP template not found!")
        return

    # 3. Load P18
    p18_path = Path(
        "data/images/p18_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.md"
    )
    if not p18_path.exists():
        logger.error(f"File not found: {p18_path}")
        return

    with open(p18_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    logger.info(f"Extracting content from: {p18_path.name}")

    # 4. Extract
    res = extraction_engine.process_nested_template(
        ocr_text, template.extraction_template
    )

    # 5. Write Comparison to File
    output_file = Path("p18_verification.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"\n{'=' * 40}\n")
        out.write(f"EXTRACTION RESULTS FOR PAGE 18\n")
        out.write(f"{'=' * 40}\n")

        out.write("\n[HEADERS]\n")
        for k in sorted(res["headers"].keys()):
            val = res["headers"][k]["value"]
            out.write(f"  {k:<20}: {val}\n")

        out.write(f"\n[TABLES] - Found {len(res['rows'])} rows\n")

        # Group by table/section
        tables = {}
        for row in res["rows"]:
            t_name = row["extracted"].get("_table_name", "Unknown Table")
            if t_name not in tables:
                tables[t_name] = []
            tables[t_name].append(row["extracted"])

        for t_name, rows in tables.items():
            out.write(f"\n  Table Section: {t_name} ({len(rows)} rows)\n")
            if rows:
                for idx, r in enumerate(rows):
                    out.write(f"    Row {idx + 1}: {r}\n")

    print(f"Verification results written to {output_file.resolve()}")


if __name__ == "__main__":
    verify_p18()
