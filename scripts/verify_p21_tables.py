import sys
from pathlib import Path
from loguru import logger
from app.engines.template import TemplateEngine
from app.engines.extraction import MarkdownExtractionEngine

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_p21_tables():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template
    template = template_engine.get_template("BMR")
    if not template:
        logger.error("BMR template not found!")
        return

    # 3. Load P21
    p21_path = Path(
        "data/images/p21_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.md"
    )

    if not p21_path.exists():
        logger.error(f"File not found: {p21_path}")
        return

    with open(p21_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 4. Extract
    res = extraction_engine.process_nested_template(
        ocr_text, template.extraction_template
    )

    # 5. Logical Segmentation
    process_rows = []
    signature_rows = []

    all_rows = [r["extracted"] for r in res["rows"]]

    current_section = None

    for row in all_rows:
        row_str = str(row).lower()

        # Detect Section Start
        # "batch process" or "s.n." often signals the main table
        if "batch process" in row_str and "qty" in row_str:
            current_section = "PROCESS"
        elif "prepared by" in row_str and "reviewed by" in row_str:
            current_section = "SIGNATURES"

        # Assign to section
        if current_section == "PROCESS":
            process_rows.append(row)
        elif current_section == "SIGNATURES":
            signature_rows.append(row)

    # 6. Output to File
    output_file = Path("p21_tables.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"TABLE EXTRACTION FOR P21\n{'=' * 30}\n\n")

        out.write(f"--- 1. BATCH PROCESS DETAILS ---\n")
        if process_rows:
            headers = list(process_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(process_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Batch Process, Qty)\n")

        out.write(f"\n--- 2. SIGNATURES ---\n")
        if signature_rows:
            headers = list(signature_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(signature_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Prepared By)\n")

    print(f"Table verification validated. Results in {output_file.resolve()}")


if __name__ == "__main__":
    verify_p21_tables()
