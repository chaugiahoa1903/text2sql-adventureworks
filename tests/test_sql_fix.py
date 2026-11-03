import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from sql_fix import fix_sql

CASES = [
    ("SELECT p.Name FROM Production.Product p ORDER BY p.Name LIMIT 1;",
     "SELECT TOP 1 p.Name FROM Production.Product p ORDER BY p.Name;"),
    ("SELECT DISTINCT CustomerID FROM Sales.SalesOrderHeader LIMIT 5",
     "SELECT DISTINCT TOP 5 CustomerID FROM Sales.SalesOrderHeader;"),
    ("SELECT TOP 3 Name FROM Production.Product ORDER BY Name;", None),
    ("SELECT Name FROM Production.Product ORDER BY Name LIMIT 5 OFFSET 10;", None),
    ("SELECT Name FROM Production.Product WHERE Name = 'LIMIT 3'", None),
    ("DELETE FROM Sales.SalesOrderHeader LIMIT 1", None),
    ("SELECT `Name` FROM Production.Product", "SELECT [Name] FROM Production.Product"),
    ("SELECT IFNULL(Color, 'n/a') FROM Production.Product",
     "SELECT ISNULL(Color, 'n/a') FROM Production.Product"),
    ("SELECT EXTRACT(YEAR FROM OrderDate) FROM Sales.SalesOrderHeader",
     "SELECT YEAR(OrderDate) FROM Sales.SalesOrderHeader"),
]

fails = 0
for sql, want in CASES:
    got, _ = fix_sql(sql)
    expected = want if want is not None else sql
    if got != expected:
        fails += 1
        print("SAI:", sql, "\n  ra:", got, "\n  can:", expected)
print("Đạt", len(CASES) - fails, "/", len(CASES))