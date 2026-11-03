import os
from datetime import datetime
from decimal import Decimal

import pyodbc
import requests
import xlsxwriter
from dotenv import load_dotenv

from clarify import needs_clarification
from clarify_llm import llm_needs_clarification
from scope import unsupported_topic
from sql_fix import fix_sql
from sql_guard import check_select_only, check_question
from suggest import plan as make_plan
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

# Các lỗi cho thấy SQL nhắc tới cột hoặc bảng không có trong schema của hệ thống
UNSUPPORTED_HINTS = ("Invalid column name", "Invalid object name", "could not be bound")


def _clarify(question, message):
    return {"status": "clarify", "message": message, "plan": make_plan(question)}


def answer(question, confirmed=False):
    """Trả về dict: status (blocked / clarify / no_data / unsupported / ok / error), message, sql, detail, fixes, columns, rows, plan.
    confirmed=True: người dùng đã chọn cách hiểu bằng nút, bỏ qua bước hỏi lại."""
    ok_q, why = check_question(question)
    if not ok_q:
        return {"status": "blocked", "message": f"Từ chối: {why}. Hệ thống chỉ đọc dữ liệu."}

    topic = unsupported_topic(question)
    if topic:
        return {"status": "unsupported",
                "message": f"Câu hỏi về {topic} nằm ngoài phạm vi hiện tại của hệ thống."}

    if not confirmed:
        ask, msg = needs_clarification(question)
        if ask:
            return _clarify(question, msg)
    try:
        if not confirmed and llm_needs_clarification(question, MODEL):
            return _clarify(question, "Câu hỏi chưa rõ chỉ tiêu hoặc thời gian. Bạn nói rõ hơn được không?")
        sql = generate_sql(question, MODEL)
    except requests.exceptions.ConnectionError:
        return {"status": "error",
                "message": "Chưa kết nối được Ollama. Hãy mở ứng dụng Ollama rồi hỏi lại."}

    sql, fixes = fix_sql(sql)
    extra = {"fixes": fixes} if fixes else {}

    ok, why = check_select_only(sql)
    if not ok:
        return {"status": "blocked", "message": f"Từ chối: {why}.", "sql": sql, **extra}

    try:
        conn = pyodbc.connect(CONN_STR)
        cur = conn.cursor()
        cur.execute(sql)
        columns = [c[0] for c in cur.description]
        rows = [list(r) for r in cur.fetchmany(1000)]
        conn.close()
    except Exception as e:
        detail = str(e)
        if any(h in detail for h in UNSUPPORTED_HINTS):
            return {"status": "unsupported",
                    "message": "Có thể dữ liệu hiện có không chứa thông tin này, hoặc câu hỏi cần diễn đạt lại.",
                    "sql": sql, "detail": detail, **extra}
        if "Incorrect syntax" in detail:
            return {"status": "error",
                    "message": "Hệ thống viết câu truy vấn chưa đúng cú pháp. Bạn thử diễn đạt khác đi, ví dụ nêu thêm khoảng thời gian hoặc tên chỉ tiêu.",
                    "sql": sql, "detail": detail, **extra}
        return {"status": "error",
                "message": "Hệ thống chưa chạy được câu này. Bạn thử nêu rõ chỉ tiêu và khoảng thời gian.",
                "sql": sql, "detail": detail, **extra}

    empty = (not rows) or all(v is None or v == 0 for v in rows[0])
    if empty:
        return {"status": "no_data", "message": "Không có dữ liệu cho kỳ này.", "sql": sql, **extra}
    return {"status": "ok", "sql": sql, "columns": columns, "rows": rows, **extra}


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
    if result.get("fixes"):
        info.write(4, 0, "Tự sửa cú pháp", head)
        info.write(4, 1, "; ".join(result["fixes"]), wrap)
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