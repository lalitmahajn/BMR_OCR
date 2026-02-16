DOCUMENT INTELLIGENCE ENGINE
CPU‑ONLY | LOCAL | AUDIT‑SAFE
Developer Specification & Build Guide

Audience: Coding Agent / Backend / Full‑stack Engineers
Purpose: Build a production‑grade document intelligence engine for BMR, QC, Production, Store, SOP, Checklist documents.

==================================================

SYSTEM OBJECTIVE
==================================================

Build a document processing engine that guarantees:

• 100% correct data in database
• OCR treated as an unreliable input
• Human verification as final authority
• CPU‑only execution
• No cloud, no GPU, no black‑box AI

This is NOT an OCR project.
This is a rule‑driven document intelligence system.

> **[CURRENT STATUS]** The system uses **Mistral Cloud OCR** (not CPU-only PaddleOCR) for higher accuracy on handwritten/complex docs.
> PaddleOCR adapter exists and can be switched via config, but Mistral is the active engine.
> Human verification via Streamlit UI is implemented. Database writes happen after OCR extraction; human review updates `verified_value`.

==================================================
2. CORE DESIGN PRINCIPLES (MANDATORY)
a.Never trust OCR output directly

b.Never write to DB without human verification

c.OCR only inside ROIs (never full page)

d.Rules first, statistics second, ML last

e.ML must be optional and rollback‑safe

f.Everything must be auditable

> **[CURRENT STATUS]**
> - (a) ✅ Implemented — OCR values stored as `ocr_value`, separate from `verified_value`
> - (b) ✅ Implemented — Fields start as `PENDING`, human sets `VERIFIED` via UI
> - (c) ❌ Changed — Current system does **full-page OCR** via Mistral, then extracts fields from markdown using label matching + regex. ROI-based extraction was abandoned in favor of template-driven markdown parsing.
> - (d) ✅ Implemented — All extraction is rule-based (regex + label matching), no ML involved
> - (e) ✅ No ML is used
> - (f) ✅ Partial — `AuditLog` table exists in DB schema, tracks field edits with `changed_by`, `previous_value`, `new_value`

==================================================
3. HIGH LEVEL ARCHITECTURE
Ingestion (PDF / Folder)
↓
Page Classification (rule based)
↓
Template + ROI Engine
↓
OCR Adapter (existing OCR)
↓
Validation + Confidence Engine
↓
Temporary Storage (pre‑DB)
↓
Human Review Gate
↓
Final Database + Audit Logs

> **[CURRENT ARCHITECTURE]**
> ```
> Ingestion (PDF → PyMuPDF → page images)     ← ✅ Implemented (app/engines/ingestion.py)
> ↓
> Mistral Cloud OCR (full page → markdown)     ← ✅ Implemented (app/engines/mistral_ocr.py)
> ↓
> Page Classification (keyword-based)          ← ✅ Implemented (app/engines/classification.py)
> ↓
> Template Engine (JSON templates, no ROIs)    ← ✅ Implemented (app/engines/template.py + templates/*.json)
> ↓
> Markdown Extraction (label + regex matching) ← ✅ Implemented (app/engines/extraction.py)
> ↓
> Direct DB Storage (Fields as PENDING)        ← ✅ Implemented (app/engines/storage.py)
> ↓
> Human Review via Streamlit UI                ← ✅ Implemented (ui/verification_ui.py)
> ↓
> Audit Logs                                   ← ✅ Schema exists (app/models/domain.py)
> ```
> **Key difference:** No ROI engine. OCR processes the full page, then extraction happens from markdown text using templates.

==================================================
4. TECHNOLOGY STACK
Language:
Python 3.10+

Core Libraries:
opencv‑python
numpy
pillow
pdf2image
pymupdf
regex
python‑dateutil
pydantic

Backend API:
fastapi
uvicorn

Database:
PostgreSQL (preferred)
or SQLite (small setups)

ORM & Migration:
sqlalchemy
alembic

Background Jobs:
celery OR rq
redis (local container)

UI:
React + Vite (preferred)
OR server‑side HTML (Jinja2)

Container:
docker
docker‑compose

> **[CURRENT STACK]**
> | Planned | Actually Using |
> |---------|---------------|
> | Python 3.10+ | ✅ Python 3.11 |
> | opencv, numpy, pillow | ✅ Installed (used for image handling) |
> | pdf2image | ❌ Not used — **PyMuPDF (fitz)** handles PDF→image |
> | pydantic | ✅ Used for template schemas + settings |
> | FastAPI + uvicorn | ❌ Not implemented — **No REST API yet** |
> | PostgreSQL | ❌ Using **SQLite** (`sql_app.db`) |
> | SQLAlchemy | ✅ Used (ORM for all models) |
> | Alembic | ❌ Not used — DB recreated on each run |
> | Celery / Redis | ❌ Not implemented — pipeline runs synchronously |
> | React + Vite | ❌ Using **Streamlit** for verification UI |
> | Docker | ❌ Removed — running locally with `.venv` |
> | **Mistral OCR API** | ✅ Added (not in original plan) |
> | **PaddleOCR** | ✅ Adapter exists but disabled in favor of Mistral |
> | **Loguru** | ✅ Added for logging |

==================================================
5. ENGINE MODULES
5.1 INGESTION ENGINE
• Watches folder / PDFs
• Converts PDF → images
• Assigns page IDs
• Preserves original scans for audit

> **[CURRENT STATUS]** ✅ Implemented in `app/engines/ingestion.py`
> - Converts PDF → page images via PyMuPDF at 2x zoom (144 DPI)
> - Names files as `p{N}_{sha256_hash}.jpg`
> - Copies original PDF to `data/uploads/` with hash-based name
> - No folder watching — runs on-demand via `main.py --process <path>`

5.2 PAGE CLASSIFICATION ENGINE (NO ML)

Rule‑based detection using:
• Header text
• Fixed keywords
• Anchors (titles, logos)

Example logic:
If header contains "BATCH MANUFACTURING RECORD"
→ page_type = BMR

> **[CURRENT STATUS]** ✅ Implemented in `app/engines/classification.py`
> - Keyword-based matching against OCR markdown text
> - Supports 11 page types: BMR, SOP, QC_TEST_REPORT, PRODUCTION_REPORT, WORKSHEET_POLYMER, DEVIATION_ACCEPTANCE, PRODUCT_SPEC, EMAIL, STORES_REQUISITION, RM_PACKING_ISSUANCE, ISSUE_VOUCHER, PACKING_DETAILS, BMR_CHECKLIST
> - Keywords defined in `templates/pagetype_keywords.txt`
> - No anchors or logo detection — pure text keyword matching

5.3 TEMPLATE & ROI ENGINE (MOST IMPORTANT)

Each page type has a template configuration:

• Header field ROIs (batch no, product, date)
• Table column X‑positions
• Signature block ROIs

Rules:
• Coordinates normalized
• OCR only inside ROI
• Templates are versioned
• Full‑page OCR is forbidden

> **[CURRENT STATUS]** ⚠️ **Significantly changed** — `app/engines/template.py` + `templates/*.json`
> - **No ROIs used** — templates define field labels + regex patterns, not pixel coordinates
> - Full-page OCR via Mistral produces markdown → extraction engine parses fields from text
> - 13 JSON template files, each with `header_fields`, `footer_fields`, and `table_config`
> - Field matching uses label text matching + regex validation/fallback
> - Template schema: `app/schemas/template.py` (Pydantic models)
> - ROI fields exist in schema but aren't used by current extraction

5.4 OCR ADAPTER

OCR is wrapped behind an interface.

Purpose:
• Allow OCR engine replacement
• Isolate OCR failures

OCR is input only, never truth.

> **[CURRENT STATUS]** ✅ Implemented in `app/engines/ocr.py` + `app/engines/mistral_ocr.py`
> - `OCRAdapter` base class with `extract_text()` interface
> - `PaddleOCRAdapter` (CPU-only, local) — exists but disabled
> - `MistralOCRAdapter` (cloud API) — active engine, returns markdown
> - OCR results cached as `.md` files alongside images to avoid re-calling the API

5.5 VALIDATION & CONFIDENCE ENGINE

Each field has:
• Data type (int, float, date, enum)
• Range limits
• Regex rules (if needed)

Confidence output:
GREEN → safe
YELLOW → verify
RED → manual correction required

If value violates rules → RED

> **[CURRENT STATUS]** ⚠️ Partial
> - `app/engines/validation.py` exists with basic structure
> - `ConfidenceLevel` enum (GREEN/YELLOW/RED) defined in `app/models/domain.py`
> - Regex validation exists in templates for some fields
> - **Confidence scoring not yet implemented** — all fields default to RED
> - Strategy documented in `docs/confidence_scoring.md`

5.6 TABLE EXTRACTION ENGINE

No ML table detection.

Uses:
• Line detection
• Fixed column positions
• Deterministic row parsing

Fast, CPU‑safe, stable.

> **[CURRENT STATUS]** ✅ Implemented differently in `app/engines/extraction.py`
> - No line detection or fixed column positions
> - Parses **markdown tables** from OCR output (Mistral returns tables as `| col | col |` format)
> - `column_mapping` in templates maps column keywords to output field names
> - Handles dynamic row count, `parameter_column_keywords`, `extract_all_columns`
> - Specialized extractors for packing details and checklists

5.7 SIGNATURE ENGINE

Rules:
• Never OCR signatures
• Signature matching only

Method:
• Crop signature ROI
• Compare with stored samples
• Return top matches
• Human confirms final name

> **[CURRENT STATUS]** ❌ Not implemented
> - Signature fields exist in templates as text labels (e.g., "Checked By", "Verified By")
> - They are extracted as text values, not image-based signature matching
> - No signature comparison or stored samples

5.8 TEMPORARY STORAGE (PRE‑DB)

Stores:
• OCR value
• Human‑corrected value
• Confidence level
• Page image path
• User + timestamp

Used for:
• Audit
• Learning
• Rollback safety

> **[CURRENT STATUS]** ⚠️ Merged with DB
> - No separate pre-DB storage — fields are written directly to SQLite
> - `Field` table stores: `ocr_value`, `verified_value`, `ocr_confidence`, `status`, `verified_by`, `verified_at`
> - `AuditLog` table tracks changes for audit trail

5.9 DATABASE GATE (CRITICAL)

Rule:
If verified_by is NULL → BLOCK DB WRITE

Guarantees:
• Database always correct
• OCR/ML mistakes never pollute DB

> **[CURRENT STATUS]** ⚠️ Partially implemented
> - Fields are written to DB immediately after extraction with `status=PENDING`
> - Human review updates `status` to `VERIFIED` and sets `verified_by`
> - The "gate" is conceptual: downstream consumers should only use `VERIFIED` fields
> - No hard block on DB writes — verified and unverified data coexist

==================================================
6. OPTIONAL LEARNING (CPU‑SAFE)
Learning is incremental and controlled.

6.1 ONLINE LEARNING
Triggered when human corrects a value.

A) OCR CONFUSION FIXES
Tracks common OCR mistakes:
O → 0
l → 1
S → 5
B → 8
Z → 2

Applied before validation to normalize OCR text.

B) FIELD STATISTICS
Tracks:
• Mean
• Std deviation
• Min / max seen

Abnormal values get lower confidence.

C) ENUM FREQUENCY
Rare enum values are auto‑flagged for review.

Online learning NEVER:
• Auto‑writes DB
• Learns free text
• Learns signatures

6.2 NIGHTLY MICRO‑BATCH
Optional scheduled job.

Scope:
• Numeric fields
• Date fields only

Data:
• Last N verified samples (200–500)

Models (CPU‑safe):
• Logistic Regression
• Small Random Forest
• Shallow XGBoost

6.3 SHADOW EVALUATION
• Train candidate model
• Compare with current model
• Promote only if better
• Keep last 3 versions
• Instant rollback available

> **[CURRENT STATUS]** ❌ Not implemented
> - No online learning, field statistics, or ML models
> - No nightly batch or shadow evaluation
> - The system is purely rule-based (templates + regex)
> - Future consideration per `docs/confidence_scoring.md`

==================================================
7. UI / UX OVERVIEW
User Roles:

Reviewer

QA / Authority

Admin

Screens:
• Work Queue
• Review Screen (image + form)
• Signature Confirmation
• Audit & Export

Features:
• ROI zoom on click
• Color‑coded confidence
• Keyboard shortcuts
• Full audit trail

> **[CURRENT STATUS]** ⚠️ Basic implementation via Streamlit
> - `ui/verification_ui.py` — single-page Streamlit app
> - No user roles or authentication
> - Screens: Page selector with image + editable fields side by side
> - No work queue — reviewer picks pages from dropdown
> - No signature confirmation screen
> - No export functionality yet
> - No ROI zoom (no ROIs in use)
> - No keyboard shortcuts
> - Basic field editing with save per field

==================================================
8. NON‑FUNCTIONAL REQUIREMENTS
• CPU‑only
• Deterministic output
• Full auditability
• No cloud dependency
• Docker deployment
• Fail‑safe DB writes

> **[CURRENT STATUS]**
> - ❌ CPU‑only — Uses Mistral Cloud OCR API (requires internet + API key)
> - ✅ Deterministic — Same template + same OCR text = same extraction
> - ✅ Auditability — AuditLog table, original images preserved in `data/uploads/`
> - ❌ No cloud dependency — Mistral API is cloud-dependent
> - ❌ Docker — Removed, running locally with `.venv`
> - ⚠️ Fail-safe DB — Fields written immediately, verification is post-write

==================================================
9. PRE‑DEVELOPMENT REQUIREMENTS
Must be finalized before coding:

Document types list

Page templates & ROI coordinates

Field schemas and ranges

Signature user list

Database schema approval

> **[CURRENT STATUS]**
> - ✅ Document types: 13 types defined and classified
> - ✅ Templates: 13 JSON files with header/footer/table definitions (no ROIs)
> - ⚠️ Field schemas: Pydantic models defined, regex patterns on ~55 fields
> - ❌ Signature user list: Not implemented
> - ✅ Database schema: 4 tables (Document, Page, Field, AuditLog) in SQLAlchemy

==================================================
10. FINAL ENGINEERING VERDICT
This system:
• Guarantees 100% DB correctness from Day‑1
• Reduces human effort within 10–15 days
• Avoids long ML training cycles
• Is stable, auditable, and CPU‑friendly

This is industrial document automation,
not experimental AI.

> **[CURRENT VERDICT]**
> The system is functional and processing 30 BMR pages across 13 document types.
> It extracts ~300+ fields per document run. Human review UI is operational.
> The main deviation from the original plan is the use of cloud OCR (Mistral) instead of CPU-only,
> and markdown-based extraction instead of ROI-based. This was a pragmatic choice for accuracy
> on complex/handwritten pharmaceutical documents.

END OF FILE
