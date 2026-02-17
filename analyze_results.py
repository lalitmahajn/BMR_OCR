import re


def analyze_results():
    with open("extraction_results.txt", "r", encoding="utf-8") as f:
        content = f.read()

    # Split by pages using the separator line
    page_blocks = re.split(r"={80,}", content)

    print(
        f"{'Page':<5} | {'Type':<25} | {'Missing':<10} | {'Total':<10} | {'Score':<10}"
    )
    print("-" * 70)

    for block in page_blocks:
        match_header = re.search(r"Page (\d+) \[(.*?)\]", block)
        if not match_header:
            continue

        page_num = match_header.group(1)
        page_type = match_header.group(2)

        # Find the table part
        lines = block.strip().split("\n")
        total = 0
        missing = 0

        for line in lines:
            # Look for lines like: FIELD_NAME | 0.85 | Value
            if "|" in line and "Field Name" not in line and "-----" not in line:
                # Use regex to split safely
                parts = [p.strip() for p in line.split("|", 2)]
                if len(parts) >= 3:
                    total += 1
                    try:
                        conf = float(parts[1])
                    except:
                        conf = 0.0
                    val = parts[2]

                    if conf == 0.0 or val == "" or val == "null" or val == "None":
                        missing += 1

        if total > 0:
            score = 100 * (1 - missing / total)
            print(
                f"{page_num:<5} | {page_type:<25} | {missing:<10} | {total:<10} | {score:.1f}%"
            )


if __name__ == "__main__":
    analyze_results()
