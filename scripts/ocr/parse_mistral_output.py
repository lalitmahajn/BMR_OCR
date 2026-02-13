import json
import re

# Load the markdown output from Mistral
with open("mistral_ocr_output.md", "r", encoding="utf-8") as f:
    markdown = f.read()

print("=" * 80)
print("PARSING MISTRAL OCR OUTPUT")
print("=" * 80 + "\n")

# Extract product information using regex
product_line = [line for line in markdown.split("\n") if "Product Name:" in line][0]

# Simple regex extraction
product_name = re.search(r"Product Name:\s*([^\s]+)", product_line)
batch_no = re.search(r"Batch No\.\s*:\s*(\S+)", product_line)
mfg_date = re.search(r"Manufacturing Date:\s*(\S+)", product_line)
quantity = re.search(r"Quantity\s*:\s*([^|]+)", product_line)

print("PRODUCT INFORMATION:")
print("-" * 80)
if product_name:
    print(f"Product Name: {product_name.group(1)}")
if batch_no:
    print(f"Batch No: {batch_no.group(1)}")
if mfg_date:
    print(f"Manufacturing Date: {mfg_date.group(1)}")
if quantity:
    print(f"Quantity: {quantity.group(1).strip()}")

# Extract test parameters (simple table parsing)
print("\n\nTEST PARAMETERS:")
print("-" * 80)

lines = markdown.split("\n")
test_params = []

for line in lines:
    # Match table rows with format: | number | parameter | result |
    match = re.match(r"\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|", line)
    if match:
        sr_no, param, result = match.groups()
        test_params.append(
            {
                "sr_no": sr_no.strip(),
                "parameter": param.strip(),
                "result": result.strip(),
            }
        )
        print(f"{sr_no.strip():>3}. {param.strip():<35} = {result.strip()}")

# Save to JSON
output = {
    "product_info": {
        "product_name": product_name.group(1) if product_name else None,
        "batch_no": batch_no.group(1) if batch_no else None,
        "manufacturing_date": mfg_date.group(1) if mfg_date else None,
        "quantity": quantity.group(1).strip() if quantity else None,
    },
    "test_parameters": test_params,
}

with open("parsed_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n\n" + "=" * 80)
print("✓ Parsed data saved to: parsed_data.json")
print("=" * 80)
