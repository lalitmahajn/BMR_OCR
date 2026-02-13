# Template JSON Schema Definition

All templates must adhere to this structure.

## Root Object
| Key | Type | Description |
|---|---|---|
| `page_type` | String | Must match `PageType` enum (e.g. `QC_TEST_REPORT`) |
| `version` | String | Template version (e.g. "1.0") |
| `base_dimensions` | Object | `{ "width": int, "height": int }` - Reference resolution for ROIs |
| `fields` | List | Array of Field Objects |
| `tables` | List | Array of Table Objects |
| `signatures` | List | Array of Signature Objects |

## Field Object
Used for key-value extraction (Headers, Footers).
```json
{
  "name": "Batch No",
  "roi": [x, y, w, h],
  "type": "string | number | date | enum",
  "validation": {
    "regex": "^[A-Z0-9-]{5,10}$",
    "options": ["Pass", "Fail"], 
    "min": 0,
    "max": 100
  },
  "confidence_threshold": 0.85
}
```

## Table Object
Used for extracting tabular data.
```json
{
  "name": "Test Results",
  "roi_area": [x, y, w, h], // The bounding box of the entire table
  "columns": [
    {
      "name": "Parameter",
      "x_offset": 50, // Relative to table x
      "width": 200,
      "type": "string"
    },
    {
      "name": "Result",
      "x_offset": 250,
      "width": 100,
      "type": "number"
    }
  ],
  "row_strategy": "lines | fixed_height",
  "row_height_px": 40 // If fixed_height
}
```

## Signature Object
Used for signature verification (No OCR).
```json
{
  "role": "QA Manager",
  "roi": [x, y, w, h],
  "authorized_users": ["John Doe", "Jane Smith"]
}
```

## Example (QC Report)
```json
{
    "page_type": "QC_TEST_REPORT",
    "version": "1.0",
    "base_dimensions": { "width": 1700, "height": 2200 },
    "fields": [
        {
            "name": "Product Name",
            "roi": [100, 200, 500, 50],
            "type": "string"
        }
    ],
    "tables": [],
    "signatures": []
}
```
