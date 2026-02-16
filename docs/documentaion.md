DOCUMENT INTELLIGENCE ENGINE (CPU-ONLY)
Revised Technical Specification & Development Guide (Auto-Training Version)

--------------------------------------------------
1. SYSTEM OBJECTIVE (REVISED)
--------------------------------------------------
Build a Document Intelligence Engine with:
- 100% correct database output (guaranteed)
- **Auto-Training Engine**: Train new document types using Excel "Truth" sheets.
- **Multi-Model Support**: Save n-number of trained models for different layouts.
- **Auto-Identification**: Software automatically pehchanega ki kaun sa model kab chalana hai.
- CPU-only, Auditable, No manual ROI coding required.

> **[CURRENT STATUS]**
> - ✅ 100% correct DB output — OCR values stored separately from human-verified values
> - ❌ Auto-Training from Excel — **Not implemented**. Instead, templates are manually created as JSON files defining field labels, regex patterns, and table configs
> - ❌ Multi-Model / `.model` files — **Not implemented**. Using 13 JSON template files (one per document type), not ML models
> - ✅ Auto-Identification — Implemented as keyword-based page classifier (`app/engines/classification.py`) that auto-detects which template to apply
> - ❌ CPU-only — Using **Mistral Cloud OCR API** for higher accuracy on handwritten content
> - ✅ No manual ROI coding — Templates use text label matching, not pixel ROI coordinates

--------------------------------------------------
2. CORE DESIGN PRINCIPLES (NON-NEGOTIABLE)
--------------------------------------------------
1. Never trust OCR directly
2. Never write to DB without human verification
3. Excel is the "Truth" during training; Human is the "Truth" during review.
4. Models are savable, replaceable, and rollback-safe.
5. CPU-only execution.

> **[CURRENT STATUS]**
> 1. ✅ OCR output stored as `ocr_value`, human sets `verified_value` — never overwritten
> 2. ✅ Fields saved as `PENDING`, human reviewer marks as `VERIFIED` via Streamlit UI
> 3. ❌ No Excel training. Templates are **hand-crafted JSON** with field labels + regex
> 4. ⚠️ Templates are JSON files — easily swappable and version-controllable via git, but no formal model versioning
> 5. ❌ Cloud OCR (Mistral API) — PaddleOCR adapter exists for CPU fallback

--------------------------------------------------
3. HIGH-LEVEL ARCHITECTURE
--------------------------------------------------
Ingestion
  ↓
**Auto-Identification (Loaded Model)**
  ↓
**Trained ROI Engine**
  ↓
OCR Adapter
  ↓
Validation & Confidence Engine
  ↓
Human Review Gate
  ↓
Final Database

> **[CURRENT ARCHITECTURE]**
> ```
> Ingestion (PDF → PyMuPDF → p{N}_{hash}.jpg)
>   ↓
> Mistral Cloud OCR (full page → markdown, cached as .md)
>   ↓
> Keyword Classifier (auto-identifies page type from OCR text)
>   ↓
> Template Engine (loads matching JSON template)
>   ↓
> Markdown Extraction (label matching + regex from template)
>   ↓
> SQLite DB (fields as PENDING)
>   ↓
> Streamlit Review UI (human verifies → VERIFIED)
> ```
> No trained models or ROI engine — purely rule-based extraction from OCR markdown.

--------------------------------------------------
5. ENGINE MODULES (REVISED)
--------------------------------------------------

5.2 Training Engine (NEW)
- Processes 5-6 samples of PDF + Excel Ground Truth.
- Learns the exact location of fields by mapping Excel values to OCR results.
- Creates a savable `.model` file.

> **[CURRENT STATUS]** ❌ Not implemented
> Instead of training from Excel, the system uses:
> - **JSON templates** (`templates/*.json`) with manually defined field labels, regex patterns, and table column mappings
> - **Pydantic schema** (`app/schemas/template.py`) validates template structure
> - To add a new document type: create a JSON template + add keywords to classifier
> - A **gap analysis tool** (`scripts/template_gap_analysis.py`) helps identify missing fields

5.3 Savable Models (NEW)
- Each document type (BMR, SOP, QC) has its own model file.
- Contains Anchor points and field ROIs.
- Software can store and switch between infinite models.

> **[CURRENT STATUS]** ⚠️ Implemented differently
> - Each document type has a **JSON template** (not a `.model` file)
> - Contains: `header_fields`, `footer_fields`, `table_config`, `document_metadata`
> - 13 templates currently: `bmr.json`, `sop.json`, `qc_report.json`, `packing.json`, `checklist.json`, `production_report.json`, `worksheet_polymer.json`, `deviation_acceptance.json`, `product_spec.json`, `email.json`, `stores_requisition.json`, `rm_packing_issuance.json`, `issue_voucher.json`
> - No anchor points or field ROIs — uses text labels with regex

5.4 Auto-Classifier
- Scans the page for headers or unique keywords to pick the correct model automatically.

> **[CURRENT STATUS]** ✅ Implemented in `app/engines/classification.py`
> - Scans OCR markdown for keywords defined in `templates/pagetype_keywords.txt`
> - Returns `PageType` enum + sub-page number + total pages
> - Handles 13 document types
> - Correctly classifies all 30 pages in current BMR document

--------------------------------------------------
6. LEARNING LAYER (REVISED)
--------------------------------------------------
6.1 Initial Training
- Use Excel Ground Truth to define "Correct Information" to prevent field confusion.
- System understands that "10/10/2025" is a Date and not a BMR Number.

> **[CURRENT STATUS]** ❌ No Excel training
> - Field type differentiation is handled by **regex patterns** in templates
> - Example: `"regex": "\\d{2}/\\d{2}/\\d{4}"` for date fields, `"regex": "\\d{10,13}"` for batch numbers
> - 55 regex patterns currently defined across all templates

--------------------------------------------------
9. PRE-DEVELOPMENT REQUIREMENTS (REVISED)
--------------------------------------------------
1. List of document types.
2. 5-6 sample scans for each document type.
3. 1 Excel sheet for each training sample with correct values.

> **[CURRENT STATUS]**
> 1. ✅ 13 document types defined and classified
> 2. ✅ 30 pages from one BMR document processed (covers all 13 types)
> 3. ❌ No Excel sheets — templates built by analyzing OCR output directly
>
> **What's needed to add new document types:**
> - Sample PDF pages of the new type
> - Create a JSON template with field labels + regex
> - Add classification keywords to `pagetype_keywords.txt`

--------------------------------------------------
10. FINAL ENGINEERING VERDICT
--------------------------------------------------
- Zero manual ROI coding.
- High accuracy through Excel-to-PDF truth-mapping.
- Fully scalable for hundreds of document types.

> **[CURRENT VERDICT]**
> - ✅ Zero manual ROI coding — confirmed, uses label matching
> - ❌ Excel-to-PDF truth-mapping — replaced by template-driven regex extraction
> - ⚠️ Scalable — adding new types requires writing a JSON template (~100 lines), not training a model
> - The system processes 30 pages, extracts ~300+ fields, and provides a review UI
> - Main trade-offs vs original plan: cloud dependency (Mistral) for better OCR accuracy, manual template creation instead of auto-training
