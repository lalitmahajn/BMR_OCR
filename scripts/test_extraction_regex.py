import re

markdown = "|  Product Name: RL-5065 Manufacturing Date: 03/01/26 AR No. : R1261FG1 01674 Approval Date : 28/01/26 Batch No. : 10012601674 Packing Details : 5900 Kg x 01 Quantity : 5900 KGS Exp. Date = 02/07/26  |   |   |"


def test_extract(label, markdown):
    # Expanded pattern to handle tight spacing
    # 1. Match label + separator
    # 2. Match value until: next label (Word Word : or Word :), pipe |, or end

    # We use a combined lookahead for:
    # - " Date :" (Space + Word + Optional Space + Separator)
    # - " AR No. :" (Space + Word + Word + Optional Space + Separator)
    pattern = rf"{re.escape(label)}[.\s]*[:\-=]*\s*(.*?)(?=\s+[A-Z][a-z0-9.]+(?:\s+[A-Z][a-z0-9.]+)?\s*[:\-=]|\||$)"

    match = re.search(pattern, markdown, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "NOT FOUND"


labels_to_test = [
    "Product Name",
    "Manufacturing Date",
    "AR No",
    "Batch No",
    "Quantity",
    "Exp. Date",
]

print(f"Markdown: {markdown}\n")
for l in labels_to_test:
    val = test_extract(l, markdown)
    print(f"[{l}] -> '{val}'")
