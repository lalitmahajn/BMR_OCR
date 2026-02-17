from app.engines.extraction import MarkdownExtractionEngine
from app.schemas.template import TableConfig
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)


def test_extraction():
    # Load real markdown
    with open("output/sample/page_3.md", "r", encoding="utf-8") as f:
        markdown = f.read()

    engine = MarkdownExtractionEngine()

    # Configure generic table extraction (matching worksheet_polymer.json)
    table_config = TableConfig(
        parameter_column_keywords=["parameter", "test"],
        result_column_keywords=["observation", "result", "finding"],
        column_mapping={
            "sr_no": ["Sr. No.", "Sr.No."],
            "test": ["Test"],
            "results": ["Results"],
        },
    )

    # Extract rows
    all_raw_rows = engine.extract_table_data(markdown, table_config)

    with open("debug_rows.json", "w", encoding="utf-8") as f:
        json.dump(all_raw_rows, f, indent=2)

    print(f"Dumped {len(all_raw_rows)} rows to debug_rows.json")


if __name__ == "__main__":
    test_extraction()
