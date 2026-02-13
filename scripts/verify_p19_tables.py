import sys
from pathlib import Path
from loguru import logger
from app.engines.template import TemplateEngine
from app.engines.extraction import MarkdownExtractionEngine

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_p19_tables():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template
    template = template_engine.get_template("BMR")
    if not template:
        logger.error("BMR template not found!")
        return

    # 3. Load P19
    p19_path = Path(
        "data/images/p19_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af.md"
    )

    with open(p19_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 4. Extract
    res = extraction_engine.process_nested_template(
        ocr_text, template.extraction_template
    )

    # 5. Logical Segmentation
    batch_rec_rows = []
    packing_rows = []
    time_cycle_rows = []
    remarks_rows = []

    # Keywords to identify rows belonging to specific sections
    # Note: The engine might put headers in keys or values depending on structure

    all_rows = [r["extracted"] for r in res["rows"]]

    current_section = None

    for row in all_rows:
        # Convert row to string for keyword search
        row_str = str(row).lower()

        # Detect Section Start
        if "input caps" in row_str or "output caps" in row_str:
            current_section = "BATCH_REC"
        elif "packing material" in row_str or "packing details" in row_str:
            current_section = "PACKING"
        elif "time cycle" in row_str or "start time" in row_str:
            if current_section == "BATCH_REC":
                current_section = None
            current_section = "TIME_CYCLE"
        elif "remarks (if any)" in row_str:
            current_section = "REMARKS"

        # Assign to section
        if current_section == "BATCH_REC":
            batch_rec_rows.append(row)
            if (
                "total time" in row_str or "batch activity" in row_str
            ):  # End of Batch Rec
                # If this row is actually the start of Time Cycle, don't add it here?
                # Actually, let's rely on the explicit keyword check above for next iteration
                pass
        elif current_section == "PACKING":
            packing_rows.append(row)
        elif current_section == "TIME_CYCLE":
            time_cycle_rows.append(row)
        elif current_section == "REMARKS":
            remarks_rows.append(row)

    # 6. Output to File
    output_file = Path("p19_tables.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"TABLE EXTRACTION FOR P19\n{'=' * 30}\n\n")

        out.write(f"--- 1. BATCH RECONCILIATION ---\n")
        if batch_rec_rows:
            # Try to align keys if possible, or just dump
            headers = list(batch_rec_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(batch_rec_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Input Caps, Output Caps)\n")

        out.write(f"\n--- 2. TIME CYCLE ---\n")
        if time_cycle_rows:
            headers = list(time_cycle_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(time_cycle_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Time Cycle, Start Time)\n")

        out.write(f"\n--- 3. PACKING MATERIAL ---\n")
        if packing_rows:
            headers = list(packing_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(packing_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write(
                "No rows identified (Keywords: Packing Material, Packing Details)\n"
            )

        out.write(f"\n--- 4. REMARKS ---\n")
        if remarks_rows:
            headers = list(remarks_rows[0].keys())
            out.write(f"Columns found: {headers}\n")
            for i, r in enumerate(remarks_rows):
                out.write(f"Row {i + 1}: {r}\n")
        else:
            out.write("No rows identified (Keywords: Remarks)\n")

    print(f"Table verification validated. Results in {output_file.resolve()}")


if __name__ == "__main__":
    verify_p19_tables()
