# 03 – PRD DRAFT (Hòa điền các ô ___ )

## Vấn đề
Người làm vận hành/kinh doanh cần số liệu từ database nhưng không biết SQL, phải nhờ người khác viết truy vấn và chờ đợi.

## Mục tiêu
Gõ một câu tiếng Việt → nhận file Excel đã định dạng, kèm SQL đã chạy để kiểm chứng.

## Ngoài phạm vi
Ghi/sửa/xóa dữ liệu; dự báo; biểu đồ phức tạp; phân quyền nhiều người dùng.

## Quyết định nghiệp vụ (Hòa tự chọn và ghi lý do)
| # | Câu hỏi | Lựa chọn của Hòa | Lý do |
|---|---|---|---|
| 1 | "Doanh thu" tính theo cột nào? (SubTotal / TotalDue / tổng LineTotal) | Hướng C: mặc định SubTotal, có nhánh TotalDue theo từ khóa, vùng xám thì hỏi lại. | Hướng này sẽ tiếp cận khái quát những gì diễn ra trong quy trình vận hành thực tế. |
| 2 | Đơn trạng thái nào được tính? (cột Status có đơn bị hủy/từ chối) | ___ | ___ |
| 3 | Quý theo lịch hay năm tài chính? | ___ | ___ |
| 4 | Câu thiếu năm ("doanh thu quý 1"): hỏi lại hay lấy năm gần nhất? | ___ | ___ |
| 5 | Ngưỡng chấp nhận cho story 1 và 4 | ___ % | ___ |

### Quy tắc phân nhánh "doanh thu" (quyết định 1)

| Nhóm | Cách hỏi ví dụ | Hệ thống làm |
|---|---|---|
| SubTotal | "doanh thu", "doanh số", "bán được bao nhiêu", "doanh thu theo sản phẩm/vùng/tháng" | Trả SubTotal (LineTotal khi chia theo sản phẩm), ghi chú "chưa gồm thuế và phí vận chuyển" |
| TotalDue | "tổng thanh toán", "khách phải trả", "tổng giá trị đơn gồm thuế" | Trả TotalDue, ghi chú "đã gồm thuế và phí vận chuyển" |
| Vùng xám | "tổng tiền", "thu về bao nhiêu", "tổng giá trị đơn hàng" | Hỏi lại người dùng, không tự đoán |

Số liệu đo trên AdventureWorks: SubTotal = 109,846,381.40; LineTotal = 109,846,381.40; TotalDue = 123,216,786.12 (cao hơn khoảng 12.2%).

## User story và acceptance criteria (nháp)
| # | User story | Acceptance criteria |
|---|---|---|
| 1 | Tôi hỏi bằng câu tự nhiên và nhận số liệu đúng | Kết quả khớp SQL chuẩn ≥ ___ % trên bộ test |
| 2 | Tôi muốn thấy SQL đã chạy | 100% file Excel có sheet ghi câu hỏi, SQL, thời điểm chạy |
| 3 | Chủ dữ liệu muốn hệ thống không thay đổi dữ liệu | 100% lệnh không phải SELECT bị chặn; kết nối bằng tài khoản chỉ đọc |
| 4 | Khi câu hỏi mơ hồ, tôi muốn được hỏi lại | Với nhóm câu mơ hồ, hỏi lại đúng ≥ ___ % thay vì tự đoán |
| 5 | Khi không có dữ liệu, tôi muốn biết rõ | 100% trường hợp rỗng trả "không có dữ liệu", không bịa số |
| 6 | Tôi muốn file Excel dùng được ngay | Số có định dạng, tiêu đề rõ, cột đủ rộng, không cần chỉnh tay |

## Metric đánh giá
- Đúng theo kết quả: so sánh bảng kết quả với SQL chuẩn (không so sánh chuỗi SQL).
- SQL chạy được (không lỗi cú pháp).
- Xử lý đúng câu mơ hồ.
- Chặn đúng câu nguy hiểm.
- Ổn định: chạy lại cùng câu hỏi 3 lần, kết quả có giống nhau không.

## Bộ test (phân nhóm, tổng 60–80 câu)
Tổng hợp đơn giản; lọc theo thời gian; JOIN nhiều bảng; nhóm theo (theo vùng, sản phẩm, tháng); câu mơ hồ; câu không có dữ liệu; câu nguy hiểm (yêu cầu xóa/sửa); câu diễn đạt theo nhiều cách khác nhau.

## Rủi ro đã biết
Định nghĩa doanh thu sai; nhầm quý; LLM local nhỏ dễ sinh SQL sai cú pháp T-SQL (ví dụ dùng LIMIT thay vì TOP); dữ liệu chỉ có vài năm.
