import sqlite3

def audit_db():
    conn = sqlite3.connect('bmr_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, ocr_value, unit, sr_no FROM fields WHERE name LIKE "TABLE_TEST_PARAMS_%"')
    results = cursor.fetchall()
    
    print(f"{'Field Name':<40} | {'Value':<20} | {'Unit':<10} | {'Sr.No':<5}")
    print("-" * 85)
    for name, value, unit, sr_no in results:
        print(f"{name:<40} | {str(value):<20} | {str(unit):<10} | {str(sr_no):<5}")
    
    conn.close()

if __name__ == "__main__":
    audit_db()
