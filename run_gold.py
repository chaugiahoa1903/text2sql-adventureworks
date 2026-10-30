import json
import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()
conn_str = (
"DRIVER={ODBC Driver 18 for SQL Server};"
f"SERVER={os.getenv('DB_SERVER')};"
f"DATABASE={os.getenv('DB_NAME')};"
f"UID={os.getenv('DB_USER')};"
f"PWD={os.getenv('DB_PASSWORD')};"
"TrustServerCertificate=yes;"
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

with open("tests/test_set.json", encoding="utf-8") as f:
    tests = json.load(f)

for t in tests:
    print(t["id"], t["cau_hoi"])
    if not t["sql_chuan"]:
        print("   -> (không có SQL chuẩn, hành vi mong đợi:", t["hanh_vi_mong_doi"] + ")")
        continue
    cursor.execute(t["sql_chuan"])
    rows = cursor.fetchall()
    print("   ->", [tuple(r) for r in rows[:15]])
conn.close()