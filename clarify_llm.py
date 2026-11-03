import requests
import os

from text2sql import OLLAMA_URL

CLASSIFY_PROMPT = """Bạn kiểm tra câu hỏi về dữ liệu bán hàng trước khi truy vấn.
Trả lời đúng một từ: RO hoặc HOI.

Trả lời HOI nếu câu hỏi thuộc một trong các trường hợp:
1. Không nói rõ chỉ tiêu cần xem (doanh thu, số đơn, số lượng, phí vận chuyển...) hoặc chỉ nói chung chung.
2. Thiếu năm cụ thể, hoặc nói thời gian tương đối/không xác định (nay, ngoái, mùa, đầu năm, cuối năm, dạo này...).
3. Dùng từ về tiền mà không rõ tính chưa thuế (SubTotal) hay đã gồm thuế và vận chuyển (TotalDue).
4. Dùng từ so sánh hoặc xếp hạng như "tốt nhất", "nhiều nhất" mà không nói theo chỉ tiêu nào hoặc trong khoảng thời gian nào.

Trả lời RO nếu câu hỏi đã nói rõ chỉ tiêu, khoảng thời gian cụ thể và không có chỗ nào mơ hồ về cách tính tiền.

Câu hỏi: {question}
Trả lời (RO hoặc HOI):"""


def llm_needs_clarification(question, model):
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": CLASSIFY_PROMPT.format(question=question),
            "stream": False,
            "keep_alive": os.getenv("OLLAMA_KEEP_ALIVE", "10m"),
            "options": {"temperature": 0, "num_predict": 5},
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip().upper().startswith("HOI")