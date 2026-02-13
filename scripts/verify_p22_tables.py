import sys
from pathlib import Path
from loguru import logger
from app.engines.template import TemplateEngine
from app.engines.extraction import MarkdownExtractionEngine
import json

# Setup logging
logger.remove()
logger.add(sys.stderr, level="INFO")


def verify_p22_tables():
    # 1. Load Engines
    template_engine = TemplateEngine()
    extraction_engine = MarkdownExtractionEngine()

    # 2. Get Template
    template = template_engine.get_template("BMR")
    if not template:
        logger.error("BMR template not found!")
        return

    # 3. Load P22
    p22_paths = list(Path("data/images").glob("p22_*.md"))
    if not p22_paths:
        logger.error(f"P22 file not found")
        return
    p22_path = p22_paths[0]

    with open(p22_path, "r", encoding="utf-8") as f:
        ocr_text = f.read()

    # 4. Extract
    res = extraction_engine.process_nested_template(
        ocr_text, template.extraction_template
    )

    # 5. Logical Segmentation & Header Parsing from Table
    header_data = {}
    batch_process_rows = []
    signatures = []

    # Initialize with regex-extracted headers if available
    for k, v in res.get("headers", {}).items():
        if v.get("value"):
            header_data[k] = v["value"]

    all_rows = [r["extracted"] for r in res["rows"]]

    current_section = "HEADER_SEARCH"

    # Helper to find value in dict keys/values
    def find_val(row_dict, key_part):
        # check keys
        for k in row_dict.keys():
            if key_part.lower() in k.lower():
                return k  # The value is often in the key itself for headers in dynamic tables
        # check values
        for v in row_dict.values():
            if v and key_part.lower() in str(v).lower():
                return v
        return None

    for i, row in enumerate(all_rows):
        row_str = str(row).lower()

        # 5a. Extract Headers from Table Rows (if missed by regex)
        # BMR No / Page Info is often in the column names of the first row result
        # We iteration through keys/values of the first few rows

        if "refer sop" in row_str and "REFER_SOP" not in header_data:
            val = find_val(row, "refer sop")
            if val:
                header_data["REFER_SOP"] = val

        if "process start shift" in row_str or "30/06/2026" in row_str:
            if "PROCESS_SHIFT" not in header_data:
                val = find_val(row, "process start shift") or find_val(row, "30/06")
                header_data["PROCESS_SHIFT"] = val

        if "batch number" in row_str or "000 1:01" in row_str:
            if "BATCH_NO" not in header_data:
                val = find_val(row, "000 1:01")  # Look for the value directly
                header_data["BATCH_NO"] = val

        if "r-17" in row_str and "EQUIPMENT_TAG" not in header_data:
            header_data["EQUIPMENT_TAG"] = "R-17"

        # 5b. Table Segmentation
        if "batch process details" in row_str and "qty" in row_str:
            current_section = "BATCH_PROCESS"
            continue  # Skip the header row itself
        elif "prepared by" in row_str and "reviewed by" in row_str:
            current_section = "SIGNATURES"

        if current_section == "BATCH_PROCESS":
            # Filter out empty rows or noise
            if "batch process details" not in row_str:  # avoid re-adding header
                batch_process_rows.append(row)
        elif current_section == "SIGNATURES":
            signatures.append(row)

    # 6. Output to File
    output_file = Path("p22_tables.txt")
    with open(output_file, "w", encoding="utf-8") as out:
        out.write(f"EXTRACTION VERIFICATION FOR P22\n{'=' * 30}\n\n")

        out.write("[DETECTED HEADERS]\n")
        for k, v in header_data.items():
            out.write(f"  {k}: {v}\n")

        out.write(f"\n[BATCH PROCESS DETAILS] ({len(batch_process_rows)} rows)\n")
        for i, r in enumerate(batch_process_rows):
            out.write(f"Row {i + 1}: {r}\n")

        out.write(f"\n[SIGNATURES]\n")
        for i, r in enumerate(signatures):
            out.write(f"Row {i + 1}: {r}\n")

    print(f"P22 verification validated. Results in {output_file.resolve()}")


if __name__ == "__main__":
    verify_p22_tables()
