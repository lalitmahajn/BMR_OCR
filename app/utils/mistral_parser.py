"""
Mistral OCR Markdown Parser
Utilities for parsing Mistral OCR markdown output into structured data
"""

import re
from typing import Dict, List, Optional, Any
from loguru import logger


def parse_product_info(markdown: str) -> Dict[str, str]:
    """
    Extract product information from markdown header section.

    Args:
        markdown: Raw markdown text from Mistral OCR

    Returns:
        Dictionary with extracted fields (product_name, batch_no, manufacturing_date, etc.)
    """
    result = {}

    # Pattern 1: "Product Name: RL-5065"
    product_match = re.search(
        r"Product\s+Name\s*:\s*([^\|\\n]+)", markdown, re.IGNORECASE
    )
    if product_match:
        result["product_name"] = product_match.group(1).strip()

    # Pattern 2: "Batch No: 10012601674" or "Batch No.: XXX/XXX/XXX"
    batch_match = re.search(r"Batch\s+No\.?\s*:\s*([^\|\\n]+)", markdown, re.IGNORECASE)
    if batch_match:
        result["batch_no"] = batch_match.group(1).strip()

    # Pattern 3: "Manufacturing Date: 03/01/26"
    mfg_date_match = re.search(
        r"Manufacturing\s+Date\s*:\s*([\\d/]+)", markdown, re.IGNORECASE
    )
    if mfg_date_match:
        result["manufacturing_date"] = mfg_date_match.group(1).strip()

    # Pattern 4: "Quantity: 5900 KGS"
    qty_match = re.search(r"Quantity\s*:\s*([^\|\\n]+)", markdown, re.IGNORECASE)
    if qty_match:
        result["quantity"] = qty_match.group(1).strip()

    # Pattern 5: "Exp. Date = 02/07/26"
    exp_date_match = re.search(
        r"Exp\.?\s*Date\s*[:=]\s*([\\d/]+)", markdown, re.IGNORECASE
    )
    if exp_date_match:
        result["exp_date"] = exp_date_match.group(1).strip()

    logger.debug(f"Extracted product info: {result}")
    return result


def parse_table(markdown: str) -> List[Dict[str, str]]:
    """
    Parse markdown table into list of dictionaries.

    Args:
        markdown: Markdown text containing table

    Returns:
        List of dictionaries, each representing a table row
    """
    rows = []

    # Split into lines
    lines = markdown.strip().split("\\n")

    # Find table header
    header_line = None
    header_cols = []

    for i, line in enumerate(lines):
        # Check for table separator (|---|---|)
        if re.match(r"^\\s*\\|[-\\s|]+\\|\\s*$", line):
            if i > 0:
                header_line = lines[i - 1]
                # Extract column names
                header_cols = [
                    col.strip() for col in header_line.split("|") if col.strip()
                ]

                # Process data rows
                for j in range(i + 1, len(lines)):
                    data_line = lines[j]
                    if "|" not in data_line:
                        break

                    # Extract cell values
                    cells = [
                        cell.strip() for cell in data_line.split("|") if cell.strip()
                    ]

                    if cells and len(cells) >= len(header_cols):
                        row_dict = {}
                        for k, col_name in enumerate(header_cols):
                            if k < len(cells):
                                row_dict[col_name] = cells[k]
                        rows.append(row_dict)

                break

    logger.debug(f"Parsed {len(rows)} table rows")
    return rows


def extract_test_parameters(markdown: str) -> List[Dict[str, str]]:
    """
    Extract test parameters from QC report markdown.
    Handles the specific format: "| Sr. No. | Test Parameters | Results |"

    Args:
        markdown: Markdown from Mistral OCR

    Returns:
        List of dicts with sr_no, test_parameter, result
    """
    # Parse the table first
    table_rows = parse_table(markdown)

    test_params = []
    for row in table_rows:
        # Normalize column names (case-insensitive matching)
        row_lower = {k.lower(): v for k, v in row.items()}

        # Extract fields
        param = {
            "sr_no": row_lower.get(
                "sr. no.", row_lower.get("sr no", row_lower.get("sn", ""))
            ),
            "test_parameter": row_lower.get(
                "test parameters", row_lower.get("parameter", row_lower.get("test", ""))
            ),
            "result": row_lower.get(
                "results", row_lower.get("result", row_lower.get("value", ""))
            ),
        }

        # Only add if we have at least a parameter name
        if param["test_parameter"]:
            test_params.append(param)

    logger.info(f"Extracted {len(test_params)} test parameters")
    return test_params


def extract_field(markdown: str, field_name: str, pattern: Optional[str] = None) -> str:
    """
    Generic field extraction using regex pattern.

    Args:
        markdown: Source markdown text
        field_name: Name of field to extract (used as default regex)
        pattern: Optional custom regex pattern

    Returns:
        Extracted value or empty string
    """
    if pattern is None:
        # Default pattern: "Field Name: <value>"
        pattern = rf"{field_name}\s*:\s*([^\|\\n]+)"

    match = re.search(pattern, markdown, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def clean_ocr_artifacts(text: str) -> str:
    """
    Clean common OCR artifacts from text.

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\\s+", " ", text)

    # Remove common OCR noise patterns
    text = re.sub(r"[_]{3,}", "", text)  # Remove underscores
    text = re.sub(r"\\.{3,}", "", text)  # Remove multiple dots

    # Strip
    text = text.strip()

    return text


def parse_qc_report(markdown: str) -> Dict[str, Any]:
    """
    Complete parser for QC Test Report.
    Combines product info and test parameters.

    Args:
        markdown: Full markdown from Mistral OCR

    Returns:
        Structured dictionary with all extracted data
    """
    result = {
        "product_info": parse_product_info(markdown),
        "test_parameters": extract_test_parameters(markdown),
        "raw_markdown": markdown,
    }

    logger.info(f"Parsed QC report: {len(result['test_parameters'])} parameters")
    return result
