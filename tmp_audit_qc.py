import sqlite3

conn = sqlite3.connect('bmr_data.db')
c = conn.cursor()

# Find QC Report pages
c.execute("SELECT id, page_number, page_type FROM pages WHERE page_type='QC_TEST_REPORT'")
pages = c.fetchall()
print("QC Report pages:", pages)

# Count existing fields
for p in pages:
    c.execute("SELECT COUNT(*) FROM fields WHERE page_id=?", (p[0],))
    print(f"  Page ID {p[0]} has {c.fetchone()[0]} fields")

conn.close()
