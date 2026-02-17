import re


def test_regex(name, regex, text):
    match = re.search(regex, text, re.MULTILINE | re.IGNORECASE)
    if match:
        print(f"[{name}] MATCH: '{match.group(1)}'")
    else:
        print(f"[{name}] NO MATCH")


# Page 27: Merged keys
page_27_text = """
|  Packing Details  |   |   |   |
|  Name of Product : Batch No.: 0000 10012601674  |   |   |   |
"""

print("--- Page 27 Final Tests ---")
# Fix: Tempered greedy token or explicit stop
test_regex(
    "PRODUCT_NAME_FIX",
    r"Name\s*of\s*Product\s*[:\-]?\s*\|?\s*((?:(?!Batch)[^\n|])*)",
    page_27_text,
)
test_regex("BATCH_NO_FIX", r"Batch\s*No\.?\s*[:\-]?\s*\|?\s*([^\n|]+)", page_27_text)


# Page 19: BMR Header
page_19_text = """
|  RISHABH RISHABH METALS AND CHEMICALS PVT. LTD. BATCH MANUFACTURING RECORD (BMR) NAME OF PRODUCT: 5065 REV: 01  |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- |
|  B.M.R. Form No.: RR-08-94, REV: 01 |   | B.M.R. Page No.: 01 of 08 |   | BMR Effective Date: 31/03/2023  |   |
"""

print("\n--- Page 19 Header Check ---")
test_regex(
    "PRODUCT_REV", r"NAME\s*OF\s*PRODUCT.*?REV\s*[:\-]?\s*\|?\s*(\d+)", page_19_text
)
test_regex(
    "EFFECTIVE_DATE",
    r"BMR\s*Effective\s*Date\s*[:\-]?\s*\|?\s*(\d{2}/\d{2}/\d{2,4})",
    page_19_text,
)
test_regex("PAGE_INFO", r"Page\s*No\.?\s*[:\-]?\s*\|?\s*(\d+\s*of\s*\d+)", page_19_text)

print("\n--- Page 3 Footer Check ---")
page_3_text = """
|  Analyzed By / Date: | Checked By / Date:  |
| --- | --- |
|  28/01/26 24/01/26 | 28/01/26  |
"""
# Fix: Look for Date pattern for Analyzed By
test_regex(
    "ANALYZED_BY_DATE",
    r"Analyzed\s*By\s*/\s*Date[\s\S]*?(\d{2}/\d{2}/\d{2,4}.*?)(?=\s*\|)",
    page_3_text,
)
