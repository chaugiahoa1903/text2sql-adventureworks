import re
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

SCHEMA = """
Sales.SalesOrderHeader(SalesOrderID, OrderDate, Status, OnlineOrderFlag, CustomerID, TerritoryID, SubTotal, TaxAmt, Freight, TotalDue)
Sales.SalesOrderDetail(SalesOrderID, SalesOrderDetailID, OrderQty, ProductID, UnitPrice, LineTotal)
Sales.SalesTerritory(TerritoryID, Name, CountryRegionCode, [Group])
Production.Product(ProductID, Name, ProductSubcategoryID, ListPrice)
Production.ProductSubcategory(ProductSubcategoryID, ProductCategoryID, Name)
Production.ProductCategory(ProductCategoryID, Name)
"""

def build_prompt(question):
    return (
        "Bạn là chuyên gia SQL Server (T-SQL). Dựa vào schema dưới đây, "
        "viết MỘT câu SELECT trả lời câu hỏi. Chỉ trả về câu SQL, không giải thích.\n"
        f"Schema:\n{SCHEMA}\n"
        f"Câu hỏi: {question}\nSQL:"
    )

def extract_sql(text):
    m = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    sql = m.group(1) if m else text
    return sql.strip()

def generate_sql(question, model):
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": build_prompt(question),
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return extract_sql(resp.json()["response"])

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    model = os.getenv("OLLAMA_MODEL")
    print(generate_sql("Tổng doanh thu năm 2013", model))