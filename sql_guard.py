import re

FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create",
             "truncate", "exec", "execute", "merge", "grant", "revoke"]

def check_select_only(sql):
    """Trả về (ok, lý do). Chỉ cho phép đúng một câu SELECT."""
    s = sql.strip().rstrip(";").strip()
    if not s:
        return False, "SQL rỗng"
    if ";" in s:
        return False, "Có nhiều câu lệnh (dấu ;)"
    if not re.match(r"^(select|with)\b", s, re.IGNORECASE):
        return False, "Không bắt đầu bằng SELECT hoặc WITH"
    for word in FORBIDDEN:
        if re.search(rf"\b{word}\b", s, re.IGNORECASE):
            return False, f"Chứa từ khóa bị cấm: {word}"
    return True, "OK"

DANGER_Q = ["xóa", "cập nhật", "thêm một", "drop ", "delete ", "update ", "insert ", "bỏ qua mọi quy tắc"]

def check_question(q):
    s = q.lower()
    for w in DANGER_Q:
        if w in s:
            return False, f"Câu hỏi yêu cầu thay đổi dữ liệu ({w.strip()})"
    return True, "OK"