from datetime import datetime
from typing import Tuple

def parse_date(value: str, format_str: str = "DD/MM/YYYY") -> Tuple[bool, str]:
    """Parse and validate date string, standardizing to DD/MM/YYYY."""
    if not value:
        return False, ""

    # Common OCR cleanup
    cleaned = value.strip().replace(".", "/").replace(",", "/").replace("-", "/")

    # Try to parse exact formats without slashes
    if len(cleaned) >= 8 and cleaned.isdigit():
        try:
            dt = datetime.strptime(cleaned[:8], "%d%m%Y")
            return True, dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            pass
    elif len(cleaned) == 6 and cleaned.isdigit():
        try:
            dt = datetime.strptime(cleaned, "%d%m%y")
            return True, dt.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            pass

    # Check if already in some format with slashes
    if "/" in cleaned:
        formats = ["%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%m/%d/%Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return True, dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                continue
                
    # If it contains alphabetical characters (e.g. 21-Jan-26)
    if any(c.isalpha() for c in cleaned):
        formats = ["%d/%b/%y", "%d/%b/%Y", "%b/%d/%Y", "%d %b %Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return True, dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                continue

    return False, cleaned

# Test cases
test_dates = [
    "28/10/26",
    "28/10/2026",
    "28.10.2026",
    "28-10-2026",
    "28 Jan 2026",
    "28-Jan-26",
    "2026/10/28",
    "28102026",
    "281026",
    "Oct 28 2026",
    "28/Oct/26"
]

print(f"{'Input':<20} | {'Status':<10} | {'Output':<15}")
print("-" * 50)
for d in test_dates:
    success, result = parse_date(d)
    print(f"{d:<20} | {str(success):<10} | {result:<15}")
