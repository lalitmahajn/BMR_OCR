import sqlite3
import pandas as pd

conn = sqlite3.connect("bmr_data.db")
query = """
SELECT p.id as page_id, d.filename, p.page_number, p.page_type, f.name, f.ocr_value 
FROM fields f 
JOIN pages p ON f.page_id = p.id 
JOIN documents d ON p.document_id = d.id 
WHERE p.page_type = 'QC_TEST_REPORT'
"""
df = pd.read_sql_query(query, conn)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
pd.set_option("display.max_rows", 100)
print(df)
