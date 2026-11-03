import os
import tempfile
import threading
import uuid
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Optional

import pyodbc
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pipeline import CONN_STR, MODEL, answer, export_excel
from text2sql import OLLAMA_URL

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = {}
CACHE = {}
OV_CACHE = {}
STATIC_PART = {}
LOCK = threading.Lock()

YEARS = {2011, 2012, 2013, 2014}
GROUPS = {"North America", "Europe", "Pacific"}
CHANNELS = {"online": 1, "direct": 0}

HEADER = """FROM Sales.SalesOrderHeader h
JOIN Sales.SalesTerritory t ON t.TerritoryID = h.TerritoryID"""

DETAIL_P = """FROM Sales.SalesOrderDetail d
JOIN Sales.SalesOrderHeader h ON h.SalesOrderID = d.SalesOrderID
JOIN Sales.SalesTerritory t ON t.TerritoryID = h.TerritoryID
JOIN Production.Product p ON p.ProductID = d.ProductID"""

DETAIL = DETAIL_P + """
JOIN Production.ProductSubcategory ps ON ps.ProductSubcategoryID = p.ProductSubcategoryID
JOIN Production.ProductCategory pc ON pc.ProductCategoryID = ps.ProductCategoryID"""


def cell(v):
    if isinstance(v, Decimal):
        return float(v)
    if v is None or isinstance(v, (int, float, str)):
        return v
    return str(v)


def where(year, group, channel, skip=""):
    parts = ["h.Status = 5"]
    params = []
    if year is not None and skip != "year":
        parts.append("YEAR(h.OrderDate) = ?")
        params.append(year)
    if group is not None and skip != "group":
        parts.append("t.[Group] = ?")
        params.append(group)
    if channel is not None and skip != "channel":
        parts.append("h.OnlineOrderFlag = ?")
        params.append(CHANNELS[channel])
    return " AND ".join(parts), params


def run(cur, sql, params):
    cur.execute(sql, *params)
    return [[cell(v) for v in r] for r in cur.fetchall()]


KPI = ("SELECT COUNT(*), COUNT(DISTINCT h.CustomerID), "
       "SUM(CASE WHEN h.OnlineOrderFlag = 1 THEN 1 ELSE 0 END), SUM(h.SubTotal) ")


def build_static(cur):
    w, p = where(None, None, None)
    return {
        "kpi_all": run(cur, KPI + HEADER + " WHERE " + w, p),
        "qty_all": run(cur, "SELECT SUM(d.OrderQty) " + DETAIL + " WHERE " + w, p),
        "quarters": run(
            cur,
            "SELECT YEAR(h.OrderDate), DATEPART(quarter, h.OrderDate), COUNT(*) " + HEADER +
            " WHERE " + w + " GROUP BY YEAR(h.OrderDate), DATEPART(quarter, h.OrderDate)"
            " ORDER BY YEAR(h.OrderDate), DATEPART(quarter, h.OrderDate)", p),
    }


def build(year, group, channel):
    conn = pyodbc.connect(CONN_STR)
    cur = conn.cursor()
    if not STATIC_PART:
        STATIC_PART.update(build_static(cur))

    w, p = where(year, group, channel)
    data = {}
    data["kpi"] = run(cur, KPI + HEADER + " WHERE " + w, p)
    data["months"] = run(
        cur,
        "SELECT YEAR(h.OrderDate), MONTH(h.OrderDate), SUM(h.SubTotal) " + HEADER +
        " WHERE " + w + " GROUP BY YEAR(h.OrderDate), MONTH(h.OrderDate)"
        " ORDER BY YEAR(h.OrderDate), MONTH(h.OrderDate)", p)

    wy, py = where(year, group, channel, skip="year")
    data["years"] = run(
        cur,
        "SELECT YEAR(h.OrderDate), SUM(h.SubTotal) " + HEADER + " WHERE " + wy +
        " GROUP BY YEAR(h.OrderDate) ORDER BY YEAR(h.OrderDate)", py)

    wg, pg = where(year, group, channel, skip="group")
    data["groups"] = run(
        cur,
        "SELECT t.[Group], SUM(h.SubTotal), COUNT(*) " + HEADER + " WHERE " + wg +
        " GROUP BY t.[Group] ORDER BY SUM(h.SubTotal) DESC", pg)

    wc, pc_ = where(year, group, channel, skip="channel")
    data["channels"] = run(
        cur,
        "SELECT CASE WHEN h.OnlineOrderFlag = 1 THEN 'Online' ELSE 'Direct' END, "
        "SUM(h.SubTotal), COUNT(*) " + HEADER + " WHERE " + wc +
        " GROUP BY CASE WHEN h.OnlineOrderFlag = 1 THEN 'Online' ELSE 'Direct' END", pc_)

    data["categories"] = run(
        cur,
        "SELECT pc.Name, SUM(d.LineTotal), SUM(d.OrderQty) " + DETAIL + " WHERE " + w +
        " GROUP BY pc.Name ORDER BY SUM(d.LineTotal) DESC", p)
    data["territories"] = run(
        cur,
        "SELECT t.Name, SUM(h.SubTotal), COUNT(*) " + HEADER + " WHERE " + w +
        " GROUP BY t.Name ORDER BY SUM(h.SubTotal) DESC", p)
    data["top"] = run(
        cur,
        "SELECT TOP 5 p.Name, SUM(d.LineTotal) " + DETAIL_P + " WHERE " + w +
        " GROUP BY p.Name ORDER BY SUM(d.LineTotal) DESC", p)
    data["buckets"] = run(
        cur,
        "SELECT b, COUNT(*), SUM(sub) FROM (SELECT CASE WHEN h.SubTotal < 1000 THEN 0 "
        "WHEN h.SubTotal < 5000 THEN 1 WHEN h.SubTotal < 20000 THEN 2 ELSE 3 END AS b, "
        "h.SubTotal AS sub " + HEADER + " WHERE " + w + ") x GROUP BY b ORDER BY b", p)
    conn.close()
    data.update(STATIC_PART)
    return data


def warm_up():
    try:
        data = build(None, None, None)
        with LOCK:
            OV_CACHE[(None, None, None)] = data
    except Exception:
        pass
    try:
        requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": "", "stream": False, "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "10m")},
            timeout=600,
        )
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=warm_up, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan)


class Ask(BaseModel):
    question: str
    confirmed: bool = False


@app.get("/")
def index():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


@app.get("/api/overview")
def overview(year: Optional[int] = None, group: Optional[str] = None, channel: Optional[str] = None):
    if year is not None and year not in YEARS:
        raise HTTPException(status_code=400, detail="Năm không hợp lệ")
    if group is not None and group not in GROUPS:
        raise HTTPException(status_code=400, detail="Nhóm khu vực không hợp lệ")
    if channel is not None and channel not in CHANNELS:
        raise HTTPException(status_code=400, detail="Kênh không hợp lệ")
    key = (year, group, channel)
    with LOCK:
        if key in OV_CACHE:
            return OV_CACHE[key]
    data = build(year, group, channel)
    with LOCK:
        OV_CACHE[key] = data
    return data

@app.get("/api/status")
def status():
    try:
        r = requests.get(OLLAMA_URL.replace("/api/generate", "/api/ps"), timeout=2)
        names = [m.get("name", "") for m in r.json().get("models", [])]
        return {"ollama": True, "model_loaded": any(MODEL in n for n in names)}
    except Exception:
        return {"ollama": False, "model_loaded": False}

@app.post("/api/ask")
def ask(body: Ask):
    q = body.question.strip()
    if not q:
        return {"status": "clarify", "message": "Bạn chưa nhập câu hỏi."}
    key = (q.lower(), body.confirmed)
    if key in CACHE:
        return CACHE[key]

    res = answer(q, confirmed=body.confirmed)
    out = {
        "status": res["status"],
        "message": res.get("message"),
        "sql": res.get("sql"),
        "fixes": res.get("fixes"),
        "detail": res.get("detail"),
        "plan": res.get("plan"),
        "columns": res.get("columns"),
        "rows": [[cell(v) for v in r] for r in res.get("rows", [])],
    }
    if res["status"] == "ok":
        rid = uuid.uuid4().hex
        RESULTS[rid] = (q, res)
        out["id"] = rid
    if res["status"] != "error":
        CACHE[key] = out
    return out


@app.get("/api/excel/{rid}")
def excel(rid: str):
    if rid not in RESULTS:
        raise HTTPException(status_code=404, detail="Không tìm thấy kết quả")
    q, res = RESULTS[rid]
    path = os.path.join(tempfile.gettempdir(), f"ket_qua_{rid}.xlsx")
    export_excel(q, res, path)
    return FileResponse(
        path,
        filename="ket_qua.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )