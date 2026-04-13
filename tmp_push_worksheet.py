import json
import sqlite3
import glob
import sys
from pathlib import Path

DB_PATH = "bmr_data.db"

def main():
    # Find the newly generated cache file
    cache_files = glob.glob("data/images/*PolymerWorksheetSchema*.json")
    if not cache_files:
        print("❌ No PolymerWorksheetSchema cache file found. Run extraction first!")
        sys.exit(1)
        
    cache_file = cache_files[0]
    print(f"Loading data from: {cache_file}")
    
    with open(cache_file, "r") as f:
        data = json.load(f)
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Locate ALL WORKSHEET_POLYMER pages in DB
    c.execute("SELECT id FROM pages WHERE page_type='WORKSHEET_POLYMER' ORDER BY id ASC")
    rows = c.fetchall()
    if len(rows) < 3:
        print("❌ Expected at least 3 WORKSHEET_POLYMER pages in the DB for distributing data.")
        sys.exit(1)
    
    page_1_id = rows[0][0] # DB Page 3
    page_2_id = rows[1][0] # DB Page 4
    page_3_id = rows[2][0] # DB Page 5
    print(f"Distributing over Base Pages: {page_1_id}, {page_2_id}, {page_3_id}")
    
    # 1. Clear old fields across ALL THREE pages
    c.execute("DELETE FROM fields WHERE page_id IN (?, ?, ?)", (page_1_id, page_2_id, page_3_id))
    print(f"Deleted {c.rowcount} stale fields across all 3 worksheet pages.")
    
    # Helper recursively flattens the dict just like the Orchestrator does!
    def flatten_to_fields(obj, prefix=""):
        flat_list = []
        for key, value in obj.items():
            if value is None:
                continue
                
            field_name = f"{prefix}_{key}".upper() if prefix else key.upper()
            
            if isinstance(value, dict):
                flat_list.extend(flatten_to_fields(value, prefix=field_name))
            else:
                # Build a polished UI label from the full hierarchy
                clean_name = field_name
                prefixes_to_strip = ["GENERIC_TESTS_", "PAGE_3_TESTS_", "PAGE_4_TESTS_", "PAGE_5_TESTS_"]
                for p in prefixes_to_strip:
                    if clean_name.startswith(p):
                        clean_name = clean_name.replace(p, "")
                if clean_name.endswith("_RESULTS"):
                    clean_name = clean_name.replace("_RESULTS", "")
                    
                label = clean_name.replace("_", " ").title().strip()
                
                # Exception: keep standard capitalization for pH optionally
                if label.startswith("Ph "):
                    label = "pH " + label[3:]
                elif label == "Ph":
                    label = "pH"
                
                field_type = "boolean" if isinstance(value, bool) else "string"
                if "date" in field_name.lower():
                    field_type = "date"
                    
                flat_list.append((field_name, label, str(value), field_type))
                
        return flat_list

    # Flatten the Mistral JSON output
    all_fields = flatten_to_fields(data)
    
    # Route logic natively tied to explicit schema blocks
    def get_target_page(name):
        if name.startswith("PAGE_4_TESTS"):
            return page_2_id  # DB Page 4
        elif name.startswith("PAGE_5_TESTS") or name in ("ANALYZED_BY", "CHECKED_BY", "APPROVED_BY", "COMPLIANCE_STATEMENT", "FINAL_REMARK"):
            return page_3_id  # DB Page 5
        return page_1_id      # DB Page 3 (default for PAGE_3_TESTS and Headers)

    # Insert everything natively into the fields table mapped to proper pages
    for name, label, val_str, ftype in all_fields:
        target_pid = get_target_page(name)
        c.execute("""
            INSERT INTO fields (page_id, name, label, field_type, roi_coordinates, ocr_value, ocr_confidence, status, confidence_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (target_pid, name, label, ftype, "0,0,0,0", val_str, 0.95, "PENDING", "GREEN"))
        
    conn.commit()
    conn.close()
    
    print(f"✅ Successfully inserted {len(all_fields)} totally flat fields. Refresh your UI!")

if __name__ == "__main__":
    main()
