# Template System — How It Works

## Pipeline Flow

```
PDF → Mistral OCR → Markdown → Classification → Template Selection → Extraction → DB
```

---

## 1. Template Structure

Each template JSON (e.g., `bmr.json`) has **three extraction zones**:

```json
{
    "page_type": "BMR",
    "extraction_template": {
        "header_fields": { ... },   // Key-value pairs at top of page
        "table_config": { ... },    // Rules for parsing markdown tables
        "footer_fields": { ... }    // Key-value pairs at bottom
    }
}
```

---

## 2. Header & Footer Fields — Label + Regex Matching

Each field has two extraction strategies attempted in order:

```json
"BATCH_NO": {
    "label": "Batch No",
    "regex": "Batch\\s*No[:\\-]?\\s*(\\d+)",
    "type": "string"
}
```

### How `extract_field()` works:

1. **Label search first** — Finds the `label` text in the OCR markdown, then captures the value after it (up to the next label/pipe/newline)
2. **Boundary lookahead** — Uses other field labels as boundaries so values don't bleed into each other
3. **Regex validation** — If regex is present, checks if the captured value matches it. If not, skips that match
4. **Regex fallback** — If label search fails completely, tries the regex directly on the full text to extract via capture group `(...)`

```
OCR text: "Batch No.: 10012601674 | Packing Details..."
             ↑ label match          ↑ boundary (next label)
             Captures: "10012601674"
```

---

## 3. Table Config — Dynamic Table Parsing

This is where the bulk of data comes from (especially BMR pages with 100+ fields):

```json
"table_config": {
    "extract_all_columns": true,
    "dynamic_rows": true,
    "parameter_column_keywords": ["BATCH ACTIVITY", "RM NAME"],
    "result_column_keywords": ["QTY (KGS)", "REMARKS"],
    "index_column_keywords": ["S.N.", "SR.NO"],
    "header_identifier_keywords": ["BATCH ACTIVITY"]
}
```

### How `extract_table_data()` works:

1. **Finds markdown tables** — Parses `| col1 | col2 |` pipe-delimited rows
2. **Identifies headers** — Uses `header_identifier_keywords` to find the header row
3. **Classifies columns** — Tags each column as "parameter", "result", or "index" using the keyword lists
4. **Extracts rows** — Each cell becomes a field: `"Row_1_BATCH_ACTIVITY" = "Mixing"`, `"Row_1_QTY" = "500 kg"`
5. **When `extract_all_columns: true`** — Captures everything, not just recognized columns

---

## 4. Classification → Template Selection

The classifier (`app/engines/classification.py`) looks at the OCR text and matches it to a `page_type`:

```python
# Simplified logic:
if "BATCH MANUFACTURING RECORD" in text → PageType.BMR     → loads bmr.json
if "STANDARD OPERATING PROCEDURE"      → PageType.SOP     → loads sop.json
if "BMR CHECKLIST"                     → PageType.BMR_CHECKLIST → loads checklist.json
```

The template loader (`app/engines/template_loader.py`) then loads the matching JSON template.

---

## 5. Orchestrator — Ties It All Together

```python
# app/orchestrator.py (simplified)
def process_page(image_path):
    markdown = ocr_engine.extract(image_path)       # Step 1: OCR
    page_type = classifier.classify(markdown)         # Step 2: Classify
    template = loader.load(page_type)                 # Step 3: Load template
    fields = extractor.process_nested_template(       # Step 4: Extract
        markdown, template
    )
    storage.save(page, fields)                        # Step 5: Save to DB
```

---

## 6. Specialized Extractors

Some page types have custom logic beyond the generic template engine:

| Method | Used For | Why |
|--------|----------|-----|
| `extract_packing_details()` | P27-P28 | Headers embedded inside table rows |
| `extract_checklist()` | P29-P30 | Checkmarks (☑) need special parsing for Yes/No/NA status |

---

## Visual Summary

```
┌─────────────────────────────────────────────────┐
│  bmr.json Template                              │
├─────────────────────────────────────────────────┤
│  header_fields:                                 │
│    Label "Batch No" → regex → captured value    │
│    Label "Product"  → regex → captured value    │
├─────────────────────────────────────────────────┤
│  table_config:                                  │
│    | S.N. | BATCH ACTIVITY | QTY | REMARKS |    │
│    |  1   | Mixing         | 500 | OK      |    │
│    Each cell → separate DB field                │
├─────────────────────────────────────────────────┤
│  footer_fields:                                 │
│    Label "PREPARED BY" → regex → captured value │
└─────────────────────────────────────────────────┘
```
