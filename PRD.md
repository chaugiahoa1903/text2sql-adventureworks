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
| 1 | "Doanh thu" tính theo cột nào? (SubTotal / TotalDue / tổng LineTotal) | Hướng C: mặc định SubTotal, có nhánh TotalDue theo từ khóa, vùng xám thì hỏi lại. | Ban đầu nghiêng về TotalDue, nhưng TotalDue cao hơn SubTotal khoảng 12.2% (gồm thuế và phí vận chuyển) và không chia được theo sản phẩm. SubTotal trùng LineTotal nên nhất quán mọi nhóm câu hỏi. Vẫn giữ nhánh TotalDue vì người dùng thật có lúc cần số khách phải trả, và ghi chú rõ có/không gồm thuế trong mọi kết quả. |
| 2 | Đơn trạng thái nào được tính? (cột Status có đơn bị hủy/từ chối) | A: chỉ tính đơn Status = 5 (Shipped) | Doanh thu ghi nhận khi hàng đã giao cho khách. Hạn chế: dữ liệu mẫu chỉ có Status = 5 nên bộ test không kiểm tra được việc lọc. |
| 3 | Quý theo lịch hay năm tài chính? | A: quý theo lịch (Q1 = tháng 1-3) | Dự án ưu tiên dễ hình dung, dễ hiểu. Thực tế quý có thể theo năm tài chính, ghi nhận là hạn chế. |
| 4 | Câu thiếu năm ("doanh thu quý 1"): hỏi lại hay lấy năm gần nhất? | Hỏi lại (NHÁP, xét lại sau baseline) | "Năm gần nhất" không ổn định trong dữ liệu 2011-06/2014: Q1 và Q2 gần nhất là 2014, nhưng Q3 và Q4 gần nhất là 2013. Tự đoán dễ ra con số trông hợp lý nhưng sai ý người hỏi. Đổi lại người dùng mất thêm một lượt trả lời, nên đo cả tỉ lệ hỏi lại thừa ở câu đã rõ năm. |
| 5 | Ngưỡng chấp nhận cho story 1 và 4 | Story 1: ≥ 70 %. Story 4: ≥ 80 % hỏi lại đúng, và hỏi lại thừa ≤ 10 % (NHÁP) | Chưa có căn cứ đo. Đặt tạm để có mốc, sẽ xét lại sau baseline. Story 4 cao hơn vì sai kiểu "đoán thay người dùng" nguy hiểm hơn sai cú pháp. Với hệ thống thật, 70 % chưa đủ nếu không có người duyệt. |

Hạn chế: trong AdventureWorks2022, toàn bộ 31,465 đơn đều có Status = 5, nên bộ test không kiểm tra được việc hệ thống có lọc đúng hay không. Quy tắc này dành cho hệ thống thật, nơi có đơn bị hủy hoặc từ chối.

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
| 1 | Tôi hỏi bằng câu tự nhiên và nhận số liệu đúng | Kết quả khớp SQL chuẩn ≥ 70 % trên bộ test |
| 2 | Tôi muốn thấy SQL đã chạy | 100% file Excel có sheet ghi câu hỏi, SQL, thời điểm chạy |
| 3 | Chủ dữ liệu muốn hệ thống không thay đổi dữ liệu | 100% lệnh không phải SELECT bị chặn; kết nối bằng tài khoản chỉ đọc |
| 4 | Khi câu hỏi mơ hồ, tôi muốn được hỏi lại | Với nhóm câu mơ hồ, hỏi lại đúng ≥ 80 % thay vì tự đoán ; hỏi lại thừa ≤ 10 % ở câu đã rõ |
| 5 | Khi không có dữ liệu, tôi muốn biết rõ | 100% trường hợp rỗng trả "không có dữ liệu", không bịa số |
| 6 | Tôi muốn file Excel dùng được ngay | Số có định dạng, tiêu đề rõ, cột đủ rộng, không cần chỉnh tay |

Dữ liệu AdventureWorks2022: từ 2011-05-31 đến 2014-06-30. Q1/2011 và từ Q3/2014 không có dữ liệu; Q2/2011 chỉ có từ 31/05 (thiếu một phần). Số đơn tăng vọt từ Q3/2013 (đặc điểm dữ liệu mẫu).

Quy tắc "không có dữ liệu": khi kết quả là NULL, hoặc kỳ được hỏi nằm ngoài khoảng 2011-05-31 đến 2014-06-30, hệ thống trả "không có dữ liệu cho kỳ này", kể cả khi COUNT ra 0. Chưa quyết định: kỳ có dữ liệu một phần (Q2/2011) có cần ghi chú "dữ liệu chỉ từ 31/05" hay không, sẽ xét sau baseline.

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


## Mô-đun CRM: khuyến mãi và khách mua lại

| # | Câu hỏi | Lựa chọn | Lý do |
|---|---|---|---|
| CRM-1 | "Dòng hàng có khuyến mãi" nghĩa là gì? | C: tách hai loại theo cột Type của Sales.SpecialOffer. "Giảm giá theo số lượng" là Type = Volume Discount. "Khuyến mãi chiến dịch" là các Type còn lại, trừ No Discount. | (NHÁP) Giảm giá theo số lượng là cơ chế tự động theo số lượng mua, chiếm 5.5% doanh thu. Chiến dịch mới là thứ nhóm CRM thiết kế và đo, chỉ chiếm 1.3% doanh thu. Gộp chung thành 6.8% sẽ che mất sự khác biệt này. |

Hạn chế: dữ liệu là khuyến mãi theo dòng hàng, không phải voucher. Không có dữ liệu phát hành hay đổi voucher, và không có nhóm đối chứng nên chỉ phân tích mô tả, không kết luận khuyến mãi làm tăng doanh thu. Còn mở: 2,151 dòng có mã khuyến mãi nhưng UnitPriceDiscount bằng 0, chưa giải thích được.