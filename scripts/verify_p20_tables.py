import sys
from pathlib import Path
from loguru import logger
from app.engines.template import TemplateEngine
from app.engines.extraction import MarkdownExtractionEngine

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_p20_tables():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template
    template = template_engine.get_template("BMR")
    if not template:
        logger.error("BMR template not found!")
        return

    # 3. Load P20
    p20_path = Path(
        "data/images/p20_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.md"
    )

    with open(p20_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 4. Extract
    res = extraction_engine.process_nested_template(
        ocr_text, template.extraction_template
    )

    # 5. Logical Segmentation
    material_rows = []
    test_rows = []
    packing_rows = []
    remarks_rows = []
    signature_rows = []

    all_rows = [r["extracted"] for r in res["rows"]]

    current_section = None

    for row in all_rows:
        row_str = str(row).lower()

        # Detect Section Start
        if "rm name" in row_str and "qty" in row_str:
            current_section = "MATERIAL"
        elif "inhouse test results" in row_str or "phy. app" in row_str:
            current_section = "TEST_RESULTS"
        elif "packing details" in row_str:
            current_section = "PACKING"
        elif "remarks" in row_str and "batch hold" in row_str:
            current_section = "REMARKS"
        elif "prepared by" in row_str and "reviewed by" in row_str:
            current_section = "SIGNATURES"

        # Assign to section
        if current_section == "MATERIAL":
            material_rows.append(row)
        elif current_section == "TEST_RESULTS":
            test_rows.append(row)
        elif current_section == "PACKING":
            packing_rows.append(row)
        elif current_section == "REMARKS":
            remarks_rows.append(row)
        elif current_section == "SIGNATURES":
            signature_rows.append(row)

    # 6. Output to File
    output_file = Path("p20_tables.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"TABLE EXTRACTION FOR P20\n{'=' * 30}\n\n")

        out.write(f"--- 1. MATERIAL ADDITION ---\n")
        if material_rows:
            headers = list(material_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(material_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: RM NAME, QTY)\n")

        out.write(f"\n--- 2. INHOUSE TEST RESULTS ---\n")
        if test_rows:
            headers = list(test_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(test_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Inhouse Test Results)\n")

        out.write(f"\n--- 3. PACKING DETAILS ---\n")
        if packing_rows:
            for i, r in enumerate(packing_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified\n")

        out.write(f"\n--- 4. REMARKS ---\n")
        if remarks_rows:
            for i, r in enumerate(remarks_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified\n")

        out.write(f"\n--- 5. SIGNATURES ---\n")
        if signature_rows:
            headers = list(signature_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(signature_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Prepared By)\n")

    print(f"Table verification validated. Results in {output_file.resolve()}")


if __name__ == "__main__":
    verify_p20_tables()
