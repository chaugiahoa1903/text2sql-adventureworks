import os
from datetime import datetime
from decimal import Decimal

import pyodbc
import xlsxwriter
from dotenv import load_dotenv

from clarify import needs_clarification
from clarify_llm import llm_needs_clarification
from sql_guard import check_select_only, check_question
from text2sql import generate_sql

load_dotenv()
MODEL = os.getenv("OLLAMA_MODEL")

CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER')};"
    f"DATABASE={os.getenv('DB_NAME')};"
    f"UID={os.getenv('DB_USER')};"
    f"PWD={os.getenv('DB_PASSWORD')};"
    "TrustServerCertificate=yes;"
)


def answer(question):
    """Trả về dict: status (blocked / clarify / no_data / ok / error), message, sql, columns, rows."""
    ok_q, why = check_question(question)
    if not ok_q:
        return {"status": "blocked", "message": f"Từ chối: {why}. Hệ thống chỉ đọc dữ liệu."}

    ask, msg = needs_clarification(question)
    if ask:
        return {"status": "clarify", "message": msg}
    if llm_needs_clarification(question, MODEL):
        return {"status": "clarify",
                "message": "Câu hỏi chưa rõ chỉ tiêu hoặc thời gian. Bạn nói rõ hơn được không?"}

    sql = generate_sql(question, MODEL)
    ok, why = check_select_only(sql)
    if not ok:
        return {"status": "blocked", "message": f"Từ chối: {why}.", "sql": sql}

    try:
        conn = pyodbc.connect(CONN_STR)
        cur = conn.cursor()
        cur.execute(sql)
        columns = [c[0] for c in cur.description]
        rows = [list(r) for r in cur.fetchmany(1000)]
        conn.close()
    except Exception as e:
        return {"status": "error", "message": f"SQL chạy lỗi: {e}", "sql": sql}

    empty = (not rows) or all(v is None or v == 0 for v in rows[0])
    if empty:
        return {"status": "no_data", "message": "Không có dữ liệu cho kỳ này.", "sql": sql}
    return {"status": "ok", "sql": sql, "columns": columns, "rows": rows}


def export_excel(question, result, path):
    wb = xlsxwriter.Workbook(path)
    head = wb.add_format({"bold": True, "bg_color": "#DDEBF7", "border": 1, "valign": "top"})
    money = wb.add_format({"num_format": "#,##0.00"})
    integer = wb.add_format({"num_format": "#,##0"})
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})

    ws = wb.add_worksheet("Kết quả")
    for c, name in enumerate(result["columns"]):
        ws.write(0, c, name, head)
        width = max(len(str(name)), *(len(str(r[c])) for r in result["rows"])) + 3
        ws.set_column(c, c, min(width, 40))
    for r, row in enumerate(result["rows"], start=1):
        for c, v in enumerate(row):
            if isinstance(v, Decimal):
                ws.write_number(r, c, float(v), money)
            elif isinstance(v, int) and not isinstance(v, bool):
                ws.write_number(r, c, v, integer)
            else:
                ws.write(r, c, v)
    ws.freeze_panes(1, 0)

    info = wb.add_worksheet("Thông tin truy vấn")
    info.set_column(0, 0, 18)
    info.set_column(1, 1, 100)
    sql_text = result["sql"].strip()
    info.write(0, 0, "Câu hỏi", head)
    info.write(0, 1, question, wrap)
    info.write(1, 0, "SQL đã chạy", head)
    info.write(1, 1, sql_text, wrap)
    info.set_row(1, 15 * (sql_text.count("\n") + 2))
    info.write(2, 0, "Thời điểm chạy", head)
    info.write(2, 1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), wrap)
    info.write(3, 0, "Model", head)
    info.write(3, 1, MODEL, wrap)
    wb.close()


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Doanh thu quý 1 năm 2013"
    res = answer(q)
    print(res["status"], res.get("message", ""))
    if res["status"] == "ok":
        os.makedirs("outputs", exist_ok=True)
        out = "outputs/demo.xlsx"
        export_excel(q, res, out)
        print("Đã ghi", out)