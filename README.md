# Hỏi dữ liệu bán hàng (Text-to-SQL cho AdventureWorks)

Dự án cá nhân: người dùng gõ một câu tiếng Việt, hệ thống sinh SQL (T-SQL) bằng một model chạy local, chạy trên SQL Server bằng tài khoản chỉ đọc, rồi trả số liệu kèm file Excel và câu SQL đã chạy để kiểm chứng.

**Đây là sản phẩm mẫu trên dữ liệu mẫu.** Chưa có người dùng vận hành thật, chưa qua kiểm thử với người dùng (UAT), chưa triển khai lên server.

## Mục tiêu của dự án

Tự trải qua quy trình của một người làm sản phẩm với LLM: viết yêu cầu, đặt tiêu chí nghiệm thu, xây bộ test, đo, cải tiến theo vòng, và nói rõ chỗ còn sai. Bài toán: người làm kinh doanh cần số liệu nhưng không biết SQL.

## Kiến trúc

Trình duyệt (FastAPI, một trang tĩnh) → `pipeline.py` → Ollama (model chạy local) → bộ sửa cú pháp → bộ lọc chỉ SELECT → SQL Server (AdventureWorks2022, tài khoản `db_datareader`) → Excel (xlsxwriter).

Không cần API key nào để chạy.

## Cách chạy lại từ đầu

1. Cài Python 3.11, SQL Server (Developer hoặc Express), ODBC Driver 18, Ollama.
2. Tải AdventureWorks2022 từ trang chính thức của Microsoft (`https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure?view=sql-server-ver17&tabs=ssms`) và khôi phục vào SQL Server. Không commit file `.bak`.
3. Tạo tài khoản đăng nhập chỉ đọc (`db_datareader`) cho database.
4. Tải model: `ollama pull qwen2.5-coder:7b` (`https://ollama.com/download/windows` ghi phiên bản chính xác từ `ollama list`).
5. Sao chép `.env.example` thành `.env` rồi điền thông tin kết nối. Không commit `.env`.
6. Cài thư viện: `pip install -r requirements.txt`
7. Chạy: `uvicorn server:app --port 8000`, mở `http://localhost:8000`.

Lần đầu sau khi bật, model cần nạp vào RAM nên câu hỏi đầu có thể mất 1 đến 3 phút. Khi model đã nạp, một câu đơn giản khoảng 13 đến 16 giây trên laptop i5-1340P 16GB, chạy chủ yếu bằng CPU.

## Dữ liệu

AdventureWorks2022 (dữ liệu mẫu của Microsoft, ___ ghi giấy phép sau khi kiểm tra trang tải). Đơn hàng từ 31/05/2011 đến 30/06/2014, 31,465 đơn đều có trạng thái 5. Vì vậy câu hỏi về năm 2026 là một test case "không có dữ liệu".

## Quyết định nghiệp vụ (ghi trong PRD.md)

- Doanh thu tính theo `SubTotal` (theo sản phẩm hoặc danh mục thì dùng `LineTotal`). Chỉ dùng `TotalDue` khi người dùng hỏi tổng thanh toán, tức gồm thuế và phí vận chuyển. Toàn bộ dữ liệu: `TotalDue` cao hơn `SubTotal` khoảng 12.2%.
- Chỉ tính đơn có `Status = 5`.
- Quý theo lịch.
- Câu thiếu năm hoặc dùng từ tiền mơ hồ ("tổng tiền", "thu về") thì hỏi lại thay vì đoán.

## Bộ test và cách đo

- 70 câu hỏi, 9 nhóm. Câu hỏi do AI soạn nháp, **SQL chuẩn do tôi tự chạy và đối chiếu số liệu** trên SQL Server.
- Đo theo **kết quả**: so sánh bảng kết quả với SQL chuẩn, không so sánh chuỗi SQL. Chấm "lenient" (bỏ qua tên cột, thứ tự cột, cột thừa) và "strict", báo cả hai.
- Hai bộ holdout, 12 câu mỗi bộ (id 101 đến 112 và 201 đến 212), dùng để kiểm tra việc học thuộc. Lưu ý: vòng 5 được sửa sau khi tôi thấy câu q111 của holdout 1 bị sai, nên kết quả holdout 1 của vòng 5 và 6 không còn độc lập hoàn toàn. Holdout 2 do AI soạn nên cũng kém độc lập hơn.
- Model chạy ở `temperature = 0`. Chạy lại vòng 5 và vòng 6 cho kết quả giống hệt vòng đầu.

## Kết quả theo vòng (70 câu, đúng strict / lenient)

| Vòng | Thay đổi | Strict | Lenient |
|---|---|---|---|
| 1 | Chỉ có schema (baseline) | 30/70 | 30/70 |
| 2 | Thêm quy tắc nghiệp vụ | 38/70 | 43/70 |
| 3 | Sửa quy tắc khoảng ngày, không JOIN thừa | 46/70 | 51/70 |
| 4 | Hỏi lại theo từ khóa, chặn câu nguy hiểm | 60/70 | 65/70 |
| 5 | Schema có chú thích giá trị thật của cột | 60/70 | 66/70 |
| 6 | Bộ phân loại hỏi lại bằng LLM (bản chính) | 58/70 | 64/70 |

Nhãn của vòng 1 đến 3 được chấm lại sau khi tôi đổi nhãn hai câu (q3, q4) thành "hỏi lại". Vòng 6 thấp hơn vòng 5 vì bộ phân loại hỏi lại thừa một câu, và một câu khác chuyển thành lỗi SQL mà tôi chưa giải thích được nguyên nhân.

### Holdout (đúng / 12)

| Vòng | Holdout 1 | Holdout 2 |
|---|---|---|
| 4 | 6/12 | chưa chạy |
| 5 | 7/12 | 7/12 |
| 6 | 8/12 | 9/12 |

Hỏi lại đúng cho câu mơ hồ: holdout 1 vòng 6 được 2/6, holdout 2 vòng 6 được 4/6 (kèm 1 lần hỏi thừa).

## Kết quả thử tay trên giao diện (10 câu, ngày 03/11/2026)

Mười câu tôi tự nghĩ ra để thử trên giao diện sau khi hoàn thành các vòng đo: đúng 3, đúng sau khi hỏi lại 1, sai 3, báo lỗi kỹ thuật thô 1, trả lời sai ý 1, hỏi lại thừa 1. Chi tiết trong `results/manual_trials.md`.

Ba lỗi đáng chú ý:
- "doanh thu quy 1 nam 2013" (gõ không dấu) và "Hồi đầu năm 2013 bán được bao nhiêu" đều trả về doanh thu cả năm 2013 (43,622,479.05) thay vì quý 1 (7,816,863.58): model lặng lẽ lấy cả năm thay vì hỏi lại. Đây là loại lỗi nguy hiểm vì con số trông hợp lý.
- Trung bình mỗi đơn qua mạng và trực tiếp ra 1,031.03 và 2,884.97, trong khi đúng là khoảng 1,061 và 21,148.
- "Quý nào nhiều đơn nhất" bị hỏi lại dù đã đủ thông tin.

## Hạn chế và những điều chưa chứng minh

- **Dữ liệu mẫu, không có người dùng thật.** Không nên suy ra hiệu quả khi dùng ở môi trường thật.
- **Nhãn do tôi tự gán**, chưa có người thứ hai kiểm. Độ nhất quán nhãn của chính tôi (gán lại 15 đến 20 câu sau vài ngày): ___ (chưa đo).
- Các nhóm "mơ hồ", "định nghĩa", "nguy hiểm" đạt 100% là do **học thuộc**: các quy tắc được viết sau khi tôi đã thấy đáp án. Holdout mới là phép đo gần thực tế hơn.
- Mỗi nhóm trong holdout chỉ có 6 câu, quá nhỏ để kết luận chắc. Holdout 2 do AI soạn nên kém độc lập hơn holdout 1.
- Mục tiêu hỏi lại đúng từ 80% trở lên **chưa đạt** (tốt nhất 4/6 trên holdout 2).
- Model local nhỏ vẫn sinh lệnh DELETE, UPDATE, DROP, INSERT khi được yêu cầu. Bộ lọc chỉ cho SELECT và tài khoản chỉ đọc là bắt buộc, không phải phần phụ.
- Chưa thể kết luận cải thiện từ vòng này sang vòng khác là do thay đổi đó hay do ngẫu nhiên: mỗi vòng chạy một lần ở `temperature = 0`.

## Các lớp bổ sung ở giao diện (chưa được đo)

Các lớp sau nằm trong `pipeline.py` và giao diện, **không** nằm trong `run_eval.py`, nên các số ở trên không tính chúng:
- Nút gợi ý khi hỏi lại (chọn năm, chọn tiêu chí xếp hạng, chọn tiền hàng hay tổng thanh toán).
- Báo sớm chủ đề ngoài phạm vi (nhân viên bán hàng, lợi nhuận, giá vốn, tồn kho) bằng danh sách từ khóa nhỏ. Danh sách này có thể bỏ sót hoặc bắt thừa với cách hỏi thật.
- Tự sửa phương ngữ SQL (`LIMIT n` thành `TOP n`, dấu huyền, `IFNULL`, `EXTRACT`). Phát lại SQL đã lưu của vòng 6 cho thấy bộ sửa không đổi câu nào, nhưng đó là kiểm bằng SQL cũ, chưa đo trên câu hỏi mới. Ca kiểm tự động: `python tests/test_sql_fix.py`.

## Vai trò của AI trong dự án

- AI (Claude) soạn nháp mã nguồn, 70 câu hỏi test, hai bộ holdout, và hướng dẫn từng bước.
- Tôi tự quyết các lựa chọn nghiệp vụ và ngưỡng đánh giá, tự chạy SQL chuẩn cho từng câu và đối chiếu số liệu (theo tổng), tự chạy toàn bộ các vòng, và tự chọn hướng cải tiến.
- Chưa dùng Jira, Confluence hay Figma. PRD viết bằng Markdown trong Git.

## Cấu trúc thư mục

- `PRD.md`: yêu cầu, quyết định nghiệp vụ, user story
- `text2sql.py`: schema, quy tắc, sinh SQL
- `clarify.py`, `clarify_llm.py`, `suggest.py`: hỏi lại và gợi ý
- `sql_guard.py`, `sql_fix.py`, `scope.py`: kiểm tra an toàn, sửa cú pháp, báo chủ đề ngoài phạm vi
- `pipeline.py`, `server.py`, `static/index.html`: luồng xử lý và giao diện
- `run_eval.py`, `regrade.py`, `tests/`, `results/`: bộ đo và kết quả