# Confidence Scoring Strategy

Since Mistral OCR doesn't provide per-character confidence, we derive confidence from extraction logic.

---

## Approach 1: Extraction Method Score (Easiest)

| Method | Confidence | Why |
|--------|-----------|-----|
| Label match + regex validated | **0.95** | Both label found AND value matches expected pattern |
| Label match, no regex | **0.80** | Label found, but value format wasn't validated |
| Regex fallback (no label) | **0.70** | Label wasn't found, extracted purely by regex |
| Table cell (column matched) | **0.85** | Structured table data, column header matched |
| Table cell (unknown column) | **0.60** | Cell extracted but column couldn't be classified |
| No extraction | **0.00** | Field expected but nothing found |

---

## Approach 2: Value Format Validation

After extraction, validate the value against its `type`:

```python
def format_confidence(value, field_type):
    if field_type == "date":
        if re.match(r"\d{2}/\d{2}/\d{2,4}", value):
            return 1.0    # Perfect date format
        elif re.search(r"\d+", value):
            return 0.5    # Has numbers but wrong format
        return 0.2        # Doesn't look like a date at all

    if field_type == "string":
        if len(value) > 2 and not value.startswith("|"):
            return 0.9
        return 0.4        # Suspiciously short or contains table artifacts
```

---

## Approach 3: OCR Artifact Detection

Flag values containing common OCR noise:

```python
NOISE_PATTERNS = [
    r"[|]{2,}",            # Multiple pipes (table artifacts)
    r"!\[img",             # Image references leaked into value
    r"[^\x00-\x7F]{3,}",  # Clusters of non-ASCII chars
    r"^\s*[-=]{3,}",       # Table separator lines
]

def ocr_noise_penalty(value):
    for pattern in NOISE_PATTERNS:
        if re.search(pattern, value):
            return -0.3
    return 0.0
```

---

## Approach 4: Cross-Field Consistency

Compare related fields to catch errors:

```python
# Batch No appears in header and table — do they match?
if header_batch_no != table_batch_no:
    confidence -= 0.2

# Manufacturing Date > Expiry Date → something's wrong
if mfg_date > exp_date:
    confidence -= 0.3
```

---

## Recommended: Composite Score

Combine approaches 1 + 2 + 3:

```python
final_confidence = (
    extraction_method_score * 0.5
    + format_validation_score * 0.3
    + (1.0 + noise_penalty) * 0.2
)
```

## Where to Implement

- Modify `extract_field()` to return `(value, end_pos, confidence)` instead of `(value, end_pos)`
- Store in `Field.ocr_confidence` (already exists in DB model, currently unpopulated)
