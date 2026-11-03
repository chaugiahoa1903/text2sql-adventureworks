import unicodedata

TOPICS = [
    ("nhân viên bán hàng", ["nhân viên", "nhân sự", "salesperson", "sales person"]),
    ("lợi nhuận và giá vốn", ["lợi nhuận", "lãi gộp", "giá vốn", "biên lợi nhuận", "profit"]),
    ("tồn kho", ["tồn kho", "hàng tồn", "inventory"]),
    ("thông tin cá nhân của khách hàng", ["tên khách", "số điện thoại", "email", "địa chỉ khách"]),
]


def unsupported_topic(question):
    s = unicodedata.normalize("NFC", question).lower()
    for name, words in TOPICS:
        if any(w in s for w in words):
            return name
    return None