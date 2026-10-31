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
RULES = """
Quy tắc nghiệp vụ BẮT BUỘC:
1. "Doanh thu", "doanh số", "bán được bao nhiêu tiền" = SUM(SalesOrderHeader.SubTotal).
   Khi chia theo sản phẩm hoặc danh mục thì dùng SUM(SalesOrderDetail.LineTotal).
2. Chỉ dùng TotalDue khi câu hỏi nói rõ "tổng thanh toán", "khách phải trả", "gồm thuế".
3. Luôn thêm điều kiện SalesOrderHeader.Status = 5 (nếu dùng SalesOrderDetail thì JOIN SalesOrderHeader để lọc).
4. Quý theo lịch: Q1 = tháng 1-3, Q2 = 4-6, Q3 = 7-9, Q4 = 10-12.
5. Lọc ngày bằng: OrderDate >= 'ngày đầu kỳ' AND OrderDate < 'ngày đầu kỳ kế tiếp'. Không dùng BETWEEN.
6. Đây là SQL Server (T-SQL): dùng TOP, KHÔNG dùng LIMIT.
7. Khoảng dữ liệu 2011-05-31 đến 2014-06-30 chỉ để tham khảo. KHÔNG thêm điều kiện lọc ngày nếu câu hỏi không nói đến thời gian.
8. "Trung bình mỗi tháng" = trung bình của tổng từng tháng (dùng truy vấn con), không phải AVG theo đơn.
9. Khi đếm đơn hàng hoặc tính theo khu vực chỉ dùng bảng SalesOrderHeader (và SalesTerritory nếu cần), KHÔNG JOIN SalesOrderDetail.
"""

def build_prompt(question):
    return (
        "Bạn là chuyên gia SQL Server (T-SQL). Dựa vào schema và quy tắc dưới đây, "
        "viết MỘT câu SELECT trả lời câu hỏi. Chỉ trả về câu SQL, không giải thích.\n"
        f"Schema:\n{SCHEMA}\n"
        f"{RULES}\n"
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