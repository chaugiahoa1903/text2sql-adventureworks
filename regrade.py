import json
import os
import sys
from decimal import Decimal

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


def run(cursor, sql):
    cursor.execute(sql)
    return cursor.fetchmany(1000)


import re

def nums(row):
    out = []
    for v in row:
        if isinstance(v, bool):
            continue
        if isinstance(v, (Decimal, float, int)):
            out.append(round(float(v), 2))
        elif isinstance(v, str):
            m = re.fullmatch(r"Q([1-4])", v.strip(), re.IGNORECASE)
            if m:
                out.append(float(m.group(1)))
    return sorted(out)


def contains(model_row, gold_row):
    pool = nums(model_row)
    for g in nums(gold_row):
        if g in pool:
            pool.remove(g)
        else:
            return False
    return True


def loose_equal(got, gold):
    if len(got) != len(gold):
        return False
    remaining = list(got)
    for g in gold:
        hit = next((m for m in remaining if contains(m, g)), None)
        if hit is None:
            return False
        remaining.remove(hit)
    return True


def main(round_name):
    tests = {t["id"]: t for t in json.load(open("tests/test_set.json", encoding="utf-8"))}
    data = json.load(open(f"results/{round_name}.json", encoding="utf-8"))
    cursor = pyodbc.connect(conn_str).cursor()

    changed, total_ok = [], 0
    for r in data["results"]:
        t = tests[r["id"]]
        old = r["trang_thai"]
        new = old
        if t["hanh_vi_mong_doi"] == "chay_sql" and old == "sai_ket_qua":
            got = run(cursor, r["sql_sinh_ra"])
            gold = run(cursor, t["sql_chuan"])
            if loose_equal(got, gold):
                new = "dung"
                changed.append(r["id"])
        r["trang_thai_noi"] = new
        total_ok += new == "dung"

    json.dump(data, open(f"results/{round_name}_regraded.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(round_name, "chấm nới:", total_ok, "/", len(data["results"]))
    print("Câu đổi từ sai sang đúng:", changed)


main(sys.argv[1])