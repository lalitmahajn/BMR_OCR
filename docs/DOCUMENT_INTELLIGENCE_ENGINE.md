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

==================================================
2. CORE DESIGN PRINCIPLES (MANDATORY)
a.Never trust OCR output directly

b.Never write to DB without human verification

c.OCR only inside ROIs (never full page)

d.Rules first, statistics second, ML last

e.ML must be optional and rollback‑safe

f.Everything must be auditable

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

==================================================
5. ENGINE MODULES
5.1 INGESTION ENGINE
• Watches folder / PDFs
• Converts PDF → images
• Assigns page IDs
• Preserves original scans for audit

5.2 PAGE CLASSIFICATION ENGINE (NO ML)

Rule‑based detection using:
• Header text
• Fixed keywords
• Anchors (titles, logos)

Example logic:
If header contains "BATCH MANUFACTURING RECORD"
→ page_type = BMR

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

5.4 OCR ADAPTER

OCR is wrapped behind an interface.

Purpose:
• Allow OCR engine replacement
• Isolate OCR failures

OCR is input only, never truth.

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

5.6 TABLE EXTRACTION ENGINE

No ML table detection.

Uses:
• Line detection
• Fixed column positions
• Deterministic row parsing

Fast, CPU‑safe, stable.

5.7 SIGNATURE ENGINE

Rules:
• Never OCR signatures
• Signature matching only

Method:
• Crop signature ROI
• Compare with stored samples
• Return top matches
• Human confirms final name

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

5.9 DATABASE GATE (CRITICAL)

Rule:
If verified_by is NULL → BLOCK DB WRITE

Guarantees:
• Database always correct
• OCR/ML mistakes never pollute DB

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

==================================================
8. NON‑FUNCTIONAL REQUIREMENTS
• CPU‑only
• Deterministic output
• Full auditability
• No cloud dependency
• Docker deployment
• Fail‑safe DB writes

==================================================
9. PRE‑DEVELOPMENT REQUIREMENTS
Must be finalized before coding:

Document types list

Page templates & ROI coordinates

Field schemas and ranges

Signature user list

Database schema approval

==================================================
10. FINAL ENGINEERING VERDICT
This system:
• Guarantees 100% DB correctness from Day‑1
• Reduces human effort within 10–15 days
• Avoids long ML training cycles
• Is stable, auditable, and CPU‑friendly

This is industrial document automation,
not experimental AI.

END OF FILE

