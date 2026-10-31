import re

# Quyết định 1: từ khóa vùng xám -> phải hỏi lại SubTotal hay TotalDue
GREY_WORDS = ["tổng tiền", "thu về", "tổng giá trị", "giá trị đơn", "giá trị trung bình", "giá trị lớn nhất"]
# Quyết định 4: thiếu năm -> hỏi lại
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
TIME_WORDS = ["quý", "tháng", "q1", "q2", "q3", "q4"]
VAGUE_TIME = ["dạo này", "gần đây", "hiện nay", "hôm nay", "mới đây"]
# Nhóm chỉ tiêu quá chung
VAGUE_METRIC = ["số liệu", "bán chạy nhất"]
# Câu hỏi đã nói rõ chỉ tiêu nên không phải vùng xám
CLEAR_PAY = ["tổng thanh toán", "khách phải trả", "gồm thuế"]


def needs_clarification(q):
    s = q.lower()
    # Có chỉ tiêu rõ ràng thì không hỏi vùng xám
    if any(w in s for w in GREY_WORDS) and not any(w in s for w in CLEAR_PAY):
        return True, "Bạn muốn tính theo SubTotal (chưa gồm thuế, vận chuyển) hay TotalDue (đã gồm)?"
    if any(w in s for w in VAGUE_TIME):
        return True, "Bạn muốn xem khoảng thời gian nào (năm, quý, tháng)?"
    if any(w in s for w in VAGUE_METRIC):
        return True, "Bạn muốn xem chỉ tiêu nào (doanh thu, số đơn, số lượng) và trong khoảng thời gian nào?"
    if any(w in s for w in TIME_WORDS) and not YEAR_RE.search(s):
        return True, "Bạn muốn xem năm nào? (dữ liệu có từ 2011-05-31 đến 2014-06-30)"
    return False, ""