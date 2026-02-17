import re


def test_regex_on_file():
    with open("output/sample/page_3.md", "r", encoding="utf-8") as f:
        markdown = f.read()

    regexes = {
        "PRODUCT_CODE": r"Product\s*Code\s*[:\-]?\s*\|?\s*([^\n|]+)",
        "AR_NO": r"AR\.?\s*No\.?\s*[:\-]?\s*\|?\s*([A-Z0-9\s]+?)(?=\s*(?:Batch|\||$))",
        "BATCH_NO": r"Batch\s*No\.?\s*[:\-]?\s*\|?\s*(\d[\d\s]*?)(?=\s*(?:No\.|containers|\||$))",
        "CONTAINERS_PACKS": r"No\.\s*of\s*containers?\s*/?\s*packs?\s*[:\-]?\s*\|?\s*([^\n|]+)",
        "BATCH_QUANTITY": r"Batch\s*Quantity\s*[:\-]?\s*\|?\s*([\d,]+\s*(?:Kg|KGS|kg)?)",
        "SAMPLED_QUANTITY": r"Sampled\s*quantity\s*[:\-]?\s*\|?\s*([^\n|]+)",
        "SAMPLING_DATE": r"Sampling\s*date\s*[:\-]?\s*\|?\s*(\d{2}/\d{2}/\d{2,4})",
        "ANALYSIS_DATE": r"Date\s*of\s*Analysis\s*[:\-]?\s*\|?\s*(\d{2}/\d{2}/\d{2,4})",
        "ANALYZED_BY": r"Analyzed\s*by\s*[:\-]?\s*\|?\s*([^\n|]+?)(?=\s*(?:Released|\||$))",
        "RELEASED_DATE": r"Released\s*Date\s*[:\-]?\s*\|?\s*(\d{2}/\d{2}/\d{2,4})",
    }

    print("Testing Regexes on Page 3 Markdown...")
    print("-" * 60)

    for field, pattern in regexes.items():
        match = re.search(pattern, markdown, re.IGNORECASE)
        if match:
            # Handle groups - usually group 1 is the value
            val = match.group(1).strip()
            print(f"{field:<20} | FOUND: '{val}'")
        else:
            print(f"{field:<20} | NOT FOUND")


if __name__ == "__main__":
    test_regex_on_file()
