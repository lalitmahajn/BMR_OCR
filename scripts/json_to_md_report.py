import json
from pathlib import Path


def json_to_md():
    json_path = Path("output/sop_verification_report.json")
    # Will be created in 'output' dir first
    out_path = Path("output/sop_full_extraction_results.md")

    if not json_path.exists():
        print(f"JSON report not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    markdown_lines = []
    markdown_lines.append("# SOP Full Extraction Results (Pages 13-18)")
    markdown_lines.append("> Generated for manual verification.")
    markdown_lines.append("")

    for page_name, content in data.items():
        markdown_lines.append(f"## {page_name}")

        # Headers
        headers = content.get("Headers", {})
        if headers:
            markdown_lines.append("### Headers")
            markdown_lines.append("| Field | Value |")
            markdown_lines.append("| :--- | :--- |")
            for k, v in headers.items():
                val = str(v).replace("\n", "<br>")
                markdown_lines.append(f"| {k} | {val} |")
            markdown_lines.append("")
        else:
            markdown_lines.append("_No Headers Extracted_")
            markdown_lines.append("")

        # Table Data
        rows = content.get("Table Data", [])

        if rows:
            # Group rows by _table_name
            grouped_tables = {}
            for r in rows:
                t_name = r.get("_table_name", "General / Unspecified")
                if t_name not in grouped_tables:
                    grouped_tables[t_name] = []
                grouped_tables[t_name].append(r)

            for t_name, t_rows in grouped_tables.items():
                markdown_lines.append(f"### Table: {t_name}")
                markdown_lines.append(f"_({len(t_rows)} Rows)_")

                # Identify columns for this specific table group
                all_cols = []
                for r in t_rows:
                    for k in r.keys():
                        if k not in all_cols and k != "_table_name":
                            all_cols.append(k)

                # Sort columns: try to keep order from first row
                if t_rows:
                    first_row_cols = [k for k in t_rows[0].keys() if k != "_table_name"]
                    for k in all_cols:
                        if k not in first_row_cols:
                            first_row_cols.append(k)
                    all_cols = first_row_cols

                if not all_cols:
                    markdown_lines.append("_No columns found in this table group_")
                    markdown_lines.append("")
                    continue

                # Markdown Table Construction
                markdown_lines.append("| " + " | ".join(all_cols) + " |")
                markdown_lines.append("| " + " | ".join(["---"] * len(all_cols)) + " |")

                for r in t_rows:
                    row_vals = []
                    for col in all_cols:
                        val = r.get(col, "")
                        val = str(val).replace("\n", "<br>")
                        row_vals.append(val)
                    markdown_lines.append("| " + " | ".join(row_vals) + " |")
                markdown_lines.append("")

        else:
            markdown_lines.append("### Table Data")
            markdown_lines.append("_No Table Data Extracted_")
            markdown_lines.append("")

        markdown_lines.append("---")
        markdown_lines.append("")

    # Write to file
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    print(f"Markdown report generated: {out_path}")


if __name__ == "__main__":
    json_to_md()
