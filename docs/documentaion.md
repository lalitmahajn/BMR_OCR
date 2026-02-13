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

--------------------------------------------------
2. CORE DESIGN PRINCIPLES (NON-NEGOTIABLE)
--------------------------------------------------
1. Never trust OCR directly
2. Never write to DB without human verification
3. Excel is the "Truth" during training; Human is the "Truth" during review.
4. Models are savable, replaceable, and rollback-safe.
5. CPU-only execution.

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

--------------------------------------------------
5. ENGINE MODULES (REVISED)
--------------------------------------------------

5.2 Training Engine (NEW)
- Processes 5-6 samples of PDF + Excel Ground Truth.
- Learns the exact location of fields by mapping Excel values to OCR results.
- Creates a savable `.model` file.

5.3 Savable Models (NEW)
- Each document type (BMR, SOP, QC) has its own model file.
- Contains Anchor points and field ROIs.
- Software can store and switch between infinite models.

5.4 Auto-Classifier
- Scans the page for headers or unique keywords to pick the correct model automatically.

--------------------------------------------------
6. LEARNING LAYER (REVISED)
--------------------------------------------------
6.1 Initial Training
- Use Excel Ground Truth to define "Correct Information" to prevent field confusion.
- System understands that "10/10/2025" is a Date and not a BMR Number.

--------------------------------------------------
9. PRE-DEVELOPMENT REQUIREMENTS (REVISED)
--------------------------------------------------
1. List of document types.
2. 5-6 sample scans for each document type.
3. 1 Excel sheet for each training sample with correct values.

--------------------------------------------------
10. FINAL ENGINEERING VERDICT
--------------------------------------------------
- Zero manual ROI coding.
- High accuracy through Excel-to-PDF truth-mapping.
- Fully scalable for hundreds of document types.
