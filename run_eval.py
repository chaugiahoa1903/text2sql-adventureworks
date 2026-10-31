import json
import os
import sys
import time
from collections import Counter, defaultdict
from decimal import Decimal

import pyodbc
from dotenv import load_dotenv

from clarify import needs_clarification
from sql_guard import check_select_only, check_question
from text2sql import generate_sql

load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL")
ROUND = sys.argv[1] if len(sys.argv) > 1 else "round1"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else None

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


def norm(rows):
    out = []
    for r in rows:
        out.append(tuple(
            round(float(v), 2) if isinstance(v, (Decimal, float, int)) and not isinstance(v, bool) else v
            for v in r
        ))
    return sorted(out, key=lambda t: [str(x) for x in t])


def is_empty(rows):
    if not rows:
        return True
    return all(v is None or v == 0 for v in rows[0])


def evaluate(t, cursor):
    hv = t["hanh_vi_mong_doi"]
    q = t["cau_hoi"]

    ok_q, _ = check_question(q)
    if not ok_q:
        return "", ("dung" if hv == "chan" else "bi_chan_nham")

    ask, _ = needs_clarification(q)
    if ask:
        return "", ("dung" if hv == "hoi_lai" else "hoi_lai_thua")

    sql = generate_sql(q, MODEL)
    ok, reason = check_select_only(sql)
    if hv == "chan":
        return sql, ("dung" if not ok else "khong_chan")
    if hv == "hoi_lai":
        return sql, "khong_hoi_lai"
    if not ok:
        return sql, "bi_chan_nham"
    try:
        got = run(cursor, sql)
    except Exception:
        return sql, "loi_sql"
    if hv == "khong_co_du_lieu":
        return sql, ("dung" if is_empty(got) else "sai_ket_qua")
    gold = run(cursor, t["sql_chuan"])
    return sql, ("dung" if norm(got) == norm(gold) else "sai_ket_qua")


def main():
    with open("tests/test_set.json", encoding="utf-8") as f:
        tests = json.load(f)
    if LIMIT:
        tests = tests[:LIMIT]

    os.makedirs("results", exist_ok=True)
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    results = []
    for t in tests:
        start = time.time()
        try:
            sql, status = evaluate(t, cursor)
        except Exception as e:
            print("   LOI:", repr(e))
            sql, status = "", "loi_he_thong"
        secs = round(time.time() - start, 1)
        results.append({
            "id": t["id"], "nhom": t["nhom"], "cau_hoi": t["cau_hoi"],
            "hanh_vi_mong_doi": t["hanh_vi_mong_doi"],
            "sql_sinh_ra": sql, "trang_thai": status, "giay": secs,
        })
        print(t["id"], t["nhom"], "->", status, f"({secs}s)")
        with open(f"results/{ROUND}.json", "w", encoding="utf-8") as f:
            json.dump({"model": MODEL, "results": results}, f, ensure_ascii=False, indent=1)

    conn.close()

    per_group = defaultdict(Counter)
    for r in results:
        per_group[r["nhom"]][r["trang_thai"]] += 1
    print("\n=== TOM TAT", ROUND, "- model", MODEL, "===")
    total_ok = 0
    for g, c in per_group.items():
        n = sum(c.values())
        total_ok += c["dung"]
        print(f"{g}: {c['dung']}/{n} dung  {dict(c)}")
    print(f"TONG: {total_ok}/{len(results)} dung")


main()