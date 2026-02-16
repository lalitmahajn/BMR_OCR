# Template Coverage Gap Analysis

Analyzed 30 pages.


---

## Summary

| Metric | Count |
|--------|-------|
| Pages analyzed | 30 |
| Null extractions (template field → no value) | 180 |
| Potential missed fields (OCR label → no template) | 54 |
| Unmapped table columns | 1 |


---

## P1 — QC_TEST_REPORT

Template: 8 header + 5 footer fields | Extracted: 12/13


### ❌ Null Extraction (1 fields)

Fields defined in template but extracted nothing:

- `footer.REVIEWED_BY` (label: "Reviewed By / Date")

---

## P2 — PRODUCTION_REPORT

Template: 1 header + 2 footer fields | Extracted: 3/3


### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "mixing"
- "mixing Details
RT9063
10012601614"

---

## P3 — WORKSHEET_POLYMER

Template: 10 header + 5 footer fields | Extracted: 5/15


### ❌ Null Extraction (10 fields)

Fields defined in template but extracted nothing:

- `header.AR_NO` (label: "AR. No.")
- `header.BATCH_NO` (label: "Batch No.")
- `header.CONTAINERS_PACKS` (label: "No. of containers/packs")
- `header.BATCH_QUANTITY` (label: "Batch Quantity")
- `header.SAMPLING_DATE` (label: "Sampling date")
- `header.ANALYSIS_DATE` (label: "Date of Analysis")
- `header.ANALYZED_BY` (label: "Analyzed by")
- `header.RELEASED_DATE` (label: "Released Date")
- `footer.COMPLIANCE_STATEMENT` (label: "The product complies/under deviation/not complies to the specification")
- `footer.REMARK` (label: "Remark: Approved / Rejected")

### 🔍 Potential Missed Fields (4 labels)

Labels found in OCR text but NOT in template:

- "DATA SHEET"
- "Observation"
- "TITLE"
- "Turbidity"

---

## P4 — WORKSHEET_POLYMER

Template: 10 header + 5 footer fields | Extracted: 3/15


### ❌ Null Extraction (12 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_CODE` (label: "Product Code:")
- `header.AR_NO` (label: "AR. No.")
- `header.BATCH_NO` (label: "Batch No.")
- `header.CONTAINERS_PACKS` (label: "No. of containers/packs")
- `header.BATCH_QUANTITY` (label: "Batch Quantity")
- `header.SAMPLED_QUANTITY` (label: "Sampled quantity")
- `header.SAMPLING_DATE` (label: "Sampling date")
- `header.ANALYSIS_DATE` (label: "Date of Analysis")
- `header.ANALYZED_BY` (label: "Analyzed by")
- `header.RELEASED_DATE` (label: "Released Date")
- `footer.COMPLIANCE_STATEMENT` (label: "The product complies/under deviation/not complies to the specification")
- `footer.REMARK` (label: "Remark: Approved / Rejected")

### 🔍 Potential Missed Fields (5 labels)

Labels found in OCR text but NOT in template:

- "Avg."
- "BR X 0.001 X 1000"
- "Net weight of dried Sample (A-Y)"
- "TITLE"
- "Weight of sample (X-Y)"

---

## P5 — WORKSHEET_POLYMER

Template: 10 header + 5 footer fields | Extracted: 5/15


### ❌ Null Extraction (10 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_CODE` (label: "Product Code:")
- `header.AR_NO` (label: "AR. No.")
- `header.BATCH_NO` (label: "Batch No.")
- `header.CONTAINERS_PACKS` (label: "No. of containers/packs")
- `header.BATCH_QUANTITY` (label: "Batch Quantity")
- `header.SAMPLED_QUANTITY` (label: "Sampled quantity")
- `header.SAMPLING_DATE` (label: "Sampling date")
- `header.ANALYSIS_DATE` (label: "Date of Analysis")
- `header.ANALYZED_BY` (label: "Analyzed by")
- `header.RELEASED_DATE` (label: "Released Date")

### 🔍 Potential Missed Fields (3 labels)

Labels found in OCR text but NOT in template:

- "Grains/Gel"
- "TITLE"
- "Wet strength"

---

## P6 — DEVIATION_ACCEPTANCE

Template: 6 header + 6 footer fields | Extracted: 12/12


### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "ACCEPTANCE UNDER DEVIATION FOR RAW MATERIAL/ FINISHED PRODUCTS/PACKING MATERIAL"
- "RISHABH METALS &amp; CHEMICALS PVT.LTD"

---

## P7 — PRODUCT_SPEC

Template: 2 header + 1 footer fields | Extracted: 1/3


### ❌ Null Extraction (2 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_CODE` (label: "Product Specification")
- `footer.BATCH_NO` (label: "No:")

### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "Quality Control Module"
- "Special Instructions"

### 📊 Unmapped Table Columns (1)

Table columns in OCR not in `column_mapping`:

- "Main Page"

---

## P8 — EMAIL

Template: 4 header + 2 footer fields | Extracted: 4/6


### ❌ Null Extraction (2 fields)

Fields defined in template but extracted nothing:

- `footer.SIGNATURE` (label: "Thanks")
- `footer.DEPARTMENT` (label: "Dept")

### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "Sat, Jan 24, 2026 at 2"
- "https"

---

## P9 — STORES_REQUISITION

Template: 4 header + 4 footer fields | Extracted: 8/8


### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "RISHABH METALS &amp; CHEMICALS PVT. LTD."
- "STORES REQUISITION SLIP POLYMER PLANT"

---

## P10 — RM_PACKING_ISSUANCE

Template: 8 header + 6 footer fields | Extracted: 12/14


### ❌ Null Extraction (2 fields)

Fields defined in template but extracted nothing:

- `header.DOCUMENT_NO` (label: "DOCUMENT NO.")
- `header.REVISION_NO` (label: "REVISION NO.")

---

## P11 — ISSUE_VOUCHER

Template: 4 header + 3 footer fields | Extracted: 5/7


### ❌ Null Extraction (2 fields)

Fields defined in template but extracted nothing:

- `footer.CHECKED_BY` (label: "Checked by")
- `footer.VERIFIED_BY` (label: "Verified by")

### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "Maharashtra - 425001, India
CIN"
- "RISHABH METALS &amp; CHEMICALS PVT. LTD."

---

## P12 — UNKNOWN

> ⚠️ No template found — all text is unprocessed


---

## P13 — SOP

Template: 15 header + 4 footer fields | Extracted: 12/19


### ❌ Null Extraction (7 fields)

Fields defined in template but extracted nothing:

- `header.IMPORTANT_NOTES` (label: "IMPORTANT_NOTES")
- `header.PRE_CHECKS` (label: "PRE_CHECKS")
- `header.PRE_CHECKS_CONT` (label: "PRE_CHECKS_CONT")
- `header.PRE_OPERATING_STEPS` (label: "PRE_OPERATING_STEPS")
- `header.BATCH_OPERATING_PROCEDURE` (label: "BATCH_OPERATING_PROCEDURE")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")
- `header.PACKING_MATERIAL` (label: "PACKING_MATERIAL")

### 🔍 Potential Missed Fields (2 labels)

Labels found in OCR text but NOT in template:

- "1.1 STANDARD RECIPE"
- "1.2 BATCH RECIPE"

---

## P14 — SOP

Template: 15 header + 4 footer fields | Extracted: 5/19


### ❌ Null Extraction (14 fields)

Fields defined in template but extracted nothing:

- `header.DOC_TITLE` (label: "DOC_TITLE")
- `header.SOP_NO` (label: "SOP NO.")
- `header.REVISION` (label: "REVISION")
- `header.EFFECTIVE_DATE` (label: "EFFECTIVE DATE")
- `header.PRODUCT_NAME` (label: "NAME OF PRODUCT")
- `header.PAGE_INFO` (label: "Page")
- `header.SCOPE` (label: "SCOPE")
- `header.BATCH_SIZE_COPY` (label: "Batch Size Copy")
- `header.PRE_CHECKS_CONT` (label: "PRE_CHECKS_CONT")
- `header.PRE_OPERATING_STEPS` (label: "PRE_OPERATING_STEPS")
- `header.BATCH_OPERATING_PROCEDURE` (label: "BATCH_OPERATING_PROCEDURE")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")
- `header.PACKING_MATERIAL` (label: "PACKING_MATERIAL")
- `footer.ISSUED_BY_DATE` (label: "Issued By")

### 🔍 Potential Missed Fields (3 labels)

Labels found in OCR text but NOT in template:

- "2. PRE OPERATING PROCEDURE"
- "2.1 IMPORTANT NOTES"
- "2.2 PRE CHECKS"

---

## P15 — SOP

Template: 15 header + 4 footer fields | Extracted: 13/19


### ❌ Null Extraction (6 fields)

Fields defined in template but extracted nothing:

- `header.SCOPE` (label: "SCOPE")
- `header.BATCH_SIZE_COPY` (label: "Batch Size Copy")
- `header.IMPORTANT_NOTES` (label: "IMPORTANT_NOTES")
- `header.PRE_CHECKS` (label: "PRE_CHECKS")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")
- `header.PACKING_MATERIAL` (label: "PACKING_MATERIAL")

### 🔍 Potential Missed Fields (4 labels)

Labels found in OCR text but NOT in template:

- "2.3 PRE OPERATING STEPS"
- "3. STANDRAD OPERATING PROCEDURE"
- "3.1 BATCH OPERATING PROCEDURE"
- "STANDARD OPERATING PROCEDURE"

---

## P16 — SOP

Template: 15 header + 4 footer fields | Extracted: 10/19


### ❌ Null Extraction (9 fields)

Fields defined in template but extracted nothing:

- `header.SCOPE` (label: "SCOPE")
- `header.BATCH_SIZE_COPY` (label: "Batch Size Copy")
- `header.IMPORTANT_NOTES` (label: "IMPORTANT_NOTES")
- `header.PRE_CHECKS` (label: "PRE_CHECKS")
- `header.PRE_CHECKS_CONT` (label: "PRE_CHECKS_CONT")
- `header.PRE_OPERATING_STEPS` (label: "PRE_OPERATING_STEPS")
- `header.BATCH_OPERATING_PROCEDURE` (label: "BATCH_OPERATING_PROCEDURE")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")
- `header.PACKING_MATERIAL` (label: "PACKING_MATERIAL")

### 🔍 Potential Missed Fields (1 labels)

Labels found in OCR text but NOT in template:

- "STANDARD OPERATING PROCEDURE"

---

## P17 — SOP

Template: 15 header + 4 footer fields | Extracted: 10/19


### ❌ Null Extraction (9 fields)

Fields defined in template but extracted nothing:

- `header.SCOPE` (label: "SCOPE")
- `header.BATCH_SIZE_COPY` (label: "Batch Size Copy")
- `header.IMPORTANT_NOTES` (label: "IMPORTANT_NOTES")
- `header.PRE_CHECKS` (label: "PRE_CHECKS")
- `header.PRE_CHECKS_CONT` (label: "PRE_CHECKS_CONT")
- `header.PRE_OPERATING_STEPS` (label: "PRE_OPERATING_STEPS")
- `header.BATCH_OPERATING_PROCEDURE` (label: "BATCH_OPERATING_PROCEDURE")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")
- `header.PACKING_MATERIAL` (label: "PACKING_MATERIAL")

### 🔍 Potential Missed Fields (3 labels)

Labels found in OCR text but NOT in template:

- "NOTE 2)"
- "NOTE :"
- "STANDARD OPERATING PROCEDURE"

---

## P18 — SOP

Template: 15 header + 4 footer fields | Extracted: 11/19


### ❌ Null Extraction (8 fields)

Fields defined in template but extracted nothing:

- `header.SCOPE` (label: "SCOPE")
- `header.BATCH_SIZE_COPY` (label: "Batch Size Copy")
- `header.IMPORTANT_NOTES` (label: "IMPORTANT_NOTES")
- `header.PRE_CHECKS` (label: "PRE_CHECKS")
- `header.PRE_CHECKS_CONT` (label: "PRE_CHECKS_CONT")
- `header.PRE_OPERATING_STEPS` (label: "PRE_OPERATING_STEPS")
- `header.BATCH_OPERATING_PROCEDURE` (label: "BATCH_OPERATING_PROCEDURE")
- `header.BATCH_PROCEDURE_CONT` (label: "BATCH_PROCEDURE_CONT")

### 🔍 Potential Missed Fields (3 labels)

Labels found in OCR text but NOT in template:

- "3.2 AIM FOR 5065 PRODUCT SPECIFICATIONS AT 25°C"
- "4. PACKING OF MATERIAL"
- "5. RESPONSIBILITY"

---

## P19 — BMR

Template: 20 header + 3 footer fields | Extracted: 17/23


### ❌ Null Extraction (6 fields)

Fields defined in template but extracted nothing:

- `header.REFER_SOP` (label: "Refer SOP")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

### 🔍 Potential Missed Fields (1 labels)

Labels found in OCR text but NOT in template:

- "Total Time Cycle (Hrs)"

---

## P20 — BMR

Template: 20 header + 3 footer fields | Extracted: 17/23


### ❌ Null Extraction (6 fields)

Fields defined in template but extracted nothing:

- `header.REFER_SOP` (label: "Refer SOP")
- `header.PROCESS_SHIFT` (label: "Process Start Shift")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")

### 🔍 Potential Missed Fields (3 labels)

Labels found in OCR text but NOT in template:

- "Final Results"
- "Packing Details"
- "Remarks"

---

## P21 — BMR

Template: 20 header + 3 footer fields | Extracted: 12/23


### ❌ Null Extraction (11 fields)

Fields defined in template but extracted nothing:

- `header.EQUIPMENT_TAG` (label: "EQUIPMENT_TAG_KEY")
- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P22 — BMR

Template: 20 header + 3 footer fields | Extracted: 12/23


### ❌ Null Extraction (11 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_NAME` (label: "Name of Product")
- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P23 — BMR

Template: 20 header + 3 footer fields | Extracted: 13/23


### ❌ Null Extraction (10 fields)

Fields defined in template but extracted nothing:

- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P24 — BMR

Template: 20 header + 3 footer fields | Extracted: 12/23


### ❌ Null Extraction (11 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_NAME` (label: "Name of Product")
- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P25 — BMR

Template: 20 header + 3 footer fields | Extracted: 12/23


### ❌ Null Extraction (11 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_NAME` (label: "Name of Product")
- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P26 — BMR

Template: 20 header + 3 footer fields | Extracted: 12/23


### ❌ Null Extraction (11 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_NAME` (label: "Name of Product")
- `header.REFER_SOP` (label: "Refer SOP")
- `header.TOTAL_TIME` (label: "TOTAL_TIME_KEY")
- `header.COMPLETION_DATE` (label: "COMPLETION_DATE_KEY")
- `header.ACTUAL_YIELD` (label: "ACTUAL_YIELD_KEY")
- `header.THEORETICAL_YIELD` (label: "THEORETICAL_YIELD_KEY")
- `header.PHYSICAL_APPEARANCE` (label: "Physical Appearance")
- `header.SP_GRAVITY` (label: "Sp. Gravity")
- `header.PH` (label: "pH")
- `header.VISCOSITY` (label: "Viscosity")
- `header.SOLID_CONTENT` (label: "Solid Content")

---

## P27 — PACKING_DETAILS

Template: 9 header + 0 footer fields | Extracted: 7/9


### ❌ Null Extraction (2 fields)

Fields defined in template but extracted nothing:

- `header.REF_BMR_NO` (label: "Ref. BMR No.")
- `header.PAGE_INFO` (label: "Page Info")

---

## P28 — PACKING_DETAILS

Template: 9 header + 0 footer fields | Extracted: 2/9


### ❌ Null Extraction (7 fields)

Fields defined in template but extracted nothing:

- `header.PRODUCT_NAME` (label: "Name of Product")
- `header.BATCH_NO` (label: "Batch No")
- `header.TOTAL_QTY` (label: "Total Qty")
- `header.TARE_WT` (label: "Tare Wet")
- `header.BALANCE_ID` (label: "Balance ID")
- `header.CALIBRATION_STATUS` (label: "Calibration Status")
- `header.RINSING_STATUS` (label: "Rinsing Status")

---

## P29 — BMR_CHECKLIST

Template: 5 header + 0 footer fields | Extracted: 5/5


### 🔍 Potential Missed Fields (4 labels)

Labels found in OCR text but NOT in template:

- "APPROVED BY
DESIGNATION"
- "PREPARED & ISSUED BY
DESIGNATION"
- "REVIEWED BY
DESIGNATION"
- "SECTION"

---

## P30 — BMR_CHECKLIST

Template: 5 header + 0 footer fields | Extracted: 5/5


### 🔍 Potential Missed Fields (6 labels)

Labels found in OCR text but NOT in template:

- "APPROVED BY
DESIGNATION"
- "Checked By"
- "PREPARED & ISSUED BY
DESIGNATION"
- "REVIEWED BY
DESIGNATION"
- "Reviewed By"
- "SECTION"