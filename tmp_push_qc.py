"""
Re-push QC Report data to DB using the explicit flat fields schema.
Clears old fields and inserts fresh ones from the cached extraction.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = "bmr_data.db"
CACHE_FILE = Path("data/images/p1_b9dea736ca06ecf2d936d768df0063984457c1a177862059fd0381db1685b9af_multi_1_QCReportSchema.json")

# Unit and Label mapping from field_specs (constant metadata per test_parameter)
PARAM_METADATA = {
    "physical_appearance": {"label": "Physical Appearance", "unit": None, "sr_no": 1},
    "viscosity": {"label": "Viscosity", "unit": "CPS", "sr_no": 2},
    "ph": {"label": "pH", "unit": None, "sr_no": 3},
    "specific_gravity": {"label": "Specific Gravity @ 25°C", "unit": None, "sr_no": 4},
    "solid_content": {"label": "Solid Content / Active %", "unit": "%", "sr_no": 5},
    "ionicity": {"label": "Ionicity", "unit": None, "sr_no": 6},
    "charge": {"label": "Charge", "unit": "mg/lit", "sr_no": 7},
    "solubility": {"label": "Solubility", "unit": None, "sr_no": 8},
    "turbidity": {"label": "Turbidity", "unit": "NTU", "sr_no": 9},
    "color_gardner": {"label": "Color Gardner", "unit": None, "sr_no": 10},
    "presence_of_grains": {"label": "Presence of Grains / Gel", "unit": None, "sr_no": 11},
    "stability_test": {"label": "Stability Test / Boring Test", "unit": None, "sr_no": 12},
    "performance_test": {"label": "Performance Test / Cobb Value", "unit": None, "sr_no": 13},
    "tensile_strength": {"label": "Tensile Strength Test / Chloride Content", "unit": "N", "sr_no": 14},
}

def main():
    # 1. Load extracted data
    with open(CACHE_FILE, "r") as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 2. Find the QC Report page
    c.execute("SELECT id FROM pages WHERE page_type='QC_TEST_REPORT'")
    row = c.fetchone()
    if not row:
        print("No QC_TEST_REPORT page found in DB")
        return
    page_id = row[0]
    
    # 3. Clear old fields
    c.execute("DELETE FROM fields WHERE page_id=?", (page_id,))
    old_count = c.rowcount
    print(f"Deleted {old_count} old fields from page_id={page_id}")
    
    # 4. Insert header fields
    header_fields = [
        ("PRODUCT_NAME", "Product Name", data.get("product_name"), "string"),
        ("MFG_DATE", "Mfg Date", data.get("mfg_date"), "date"),
        ("AR_NO", "AR No.", data.get("ar_no"), "string"),
        ("APPROVAL_DATE", "Approval Date", data.get("approval_date"), "date"),
        ("BATCH_NO", "Batch No.", data.get("batch_no"), "string"),
        ("PACKING_DETAILS", "Packing Details", data.get("packing_details"), "string"),
        ("QUANTITY", "Quantity", data.get("quantity"), "string"),
        ("EXP_DATE", "Exp. Date", data.get("exp_date"), "date"),
    ]
    
    for name, label, value, ftype in header_fields:
        if value is not None:
            c.execute("""
                INSERT INTO fields (page_id, name, label, field_type, roi_coordinates, ocr_value, ocr_confidence, status, confidence_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (page_id, name, label, ftype, "0,0,0,0", str(value), 0.95, "PENDING", "GREEN"))
    
    print(f"Inserted {len(header_fields)} header fields")
    
    # 5. Insert explicit test results
    test_results = data.get("test_results", {})
    table_count = 0
    
    for param_key, result_val in test_results.items():
        if param_key not in PARAM_METADATA:
            continue
            
        meta = PARAM_METADATA[param_key]
        
        # Insert as top-level fields but prefixed with TEST_RESULTS_ for grouping
        c.execute("""
            INSERT INTO fields (page_id, name, label, field_type, roi_coordinates, ocr_value, ocr_confidence, unit, sr_no, status, confidence_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            page_id, 
            f"TEST_RESULTS_{param_key.upper()}", 
            meta["label"], 
            "string", 
            "0,0,0,0", 
            result_val, 
            0.95, 
            meta["unit"], 
            meta["sr_no"], 
            "PENDING", 
            "GREEN"
        ))
        
        table_count += 1
    
    print(f"Inserted {table_count} explicit test result fields")
    
    # 6. Insert footer fields
    footer_fields = [
        ("RESULT", "Result", data.get("result"), "string"),
        ("REMARKS", "Remarks", data.get("remarks"), "string"),
    ]
    
    for name, label, value, ftype in footer_fields:
        if value is not None:
            c.execute("""
                INSERT INTO fields (page_id, name, label, field_type, roi_coordinates, ocr_value, ocr_confidence, status, confidence_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (page_id, name, label, ftype, "0,0,0,0", str(value), 0.95, "PENDING", "GREEN"))
    
    print(f"Inserted {len(footer_fields)} footer fields")
    
    conn.commit()
    
    # 7. Verify
    c.execute("SELECT COUNT(*) FROM fields WHERE page_id=?", (page_id,))
    total = c.fetchone()[0]
    print(f"\nTotal fields now: {total}")
    
    conn.close()
    print("Done! Refresh the UI to see the data.")

if __name__ == "__main__":
    main()
