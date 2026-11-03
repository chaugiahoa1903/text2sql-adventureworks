import re

YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
SPECIFIC_PERIOD_RE = re.compile(r"(quý|q)\s*[1-4]|tháng\s*\d{1,2}", re.IGNORECASE)

GENERIC_METRIC = ["tình hình kinh doanh", "số liệu", "chỉ số"]
VAGUE_TIME = ["dạo này", "gần đây", "hiện nay", "hôm nay", "mới đây"]
GREY = ["tổng tiền", "thu về", "tổng giá trị", "giá trị đơn", "giá trị trung bình", "giá trị lớn nhất"]
CLEAR_PAY = ["tổng thanh toán", "khách phải trả", "gồm thuế"]
RANK = ["nhiều nhất", "cao nhất", "thấp nhất", "ít nhất", "bán chạy", "tốt nhất", "lớn nhất", "nhỏ nhất"]
METRIC_WORDS = ["doanh thu", "doanh số", "số lượng", "số đơn", "đơn hàng", "đơn", "khách",
                "phí vận chuyển", "thuế", "thanh toán", "giá trị", "tiền"]
FILLERS = ["cho tôi", "cho mình", "cho em", "cho anh", "giúp", "biết", "xem"]

BY_REVENUE = {"label": "Theo doanh thu", "suffix": "theo doanh thu"}
BY_QTY = {"label": "Theo số lượng bán", "suffix": "theo số lượng bán"}
BY_ORDERS = {"label": "Theo số đơn hàng", "suffix": "theo số đơn hàng"}


def _squash(text):
    return re.sub(r"\s+", " ", text).strip(" ,.?!;:")


def _remove(text, phrases):
    for p in phrases:
        text = re.sub(re.escape(p), " ", text, flags=re.IGNORECASE)
    return text


def _entity(s):
    if "sản phẩm" in s:
        return "product"
    if "danh mục" in s:
        return "category"
    if "khách" in s:
        return "customer"
    if "khu vực" in s or "vùng" in s:
        return "region"
    if "kênh" in s or "online" in s or "qua mạng" in s:
        return "channel"
    return "other"


def _rank_group(entity):
    if entity in ("product", "category"):
        options = [BY_REVENUE, BY_QTY]
    elif entity in ("customer", "region", "channel"):
        options = [BY_REVENUE, BY_ORDERS]
    else:
        options = [BY_REVENUE, BY_ORDERS]
    return {"title": "Bạn muốn xếp hạng theo tiêu chí nào?", "options": options}


def _year_group(allow_all):
    options = [
        {"label": "2011 (từ 31/05)", "suffix": "trong năm 2011"},
        {"label": "2012", "suffix": "trong năm 2012"},
        {"label": "2013", "suffix": "trong năm 2013"},
        {"label": "2014 (đến 30/06)", "suffix": "trong năm 2014"},
    ]
    if allow_all:
        options.append({"label": "Tất cả các năm (2011 đến 2014)",
                        "suffix": "trong giai đoạn 2011 đến 2014"})
    return {"title": "Bạn muốn xem khoảng thời gian nào?", "options": options}


MONEY_GROUP = {
    "title": "Bạn muốn tính theo cách nào?",
    "options": [
        {"label": "Tiền hàng (chưa gồm thuế, phí vận chuyển)",
         "suffix": "tính theo doanh thu (tiền hàng)"},
        {"label": "Tổng thanh toán (đã gồm thuế, phí vận chuyển)",
         "suffix": "tính theo tổng thanh toán (đã gồm thuế và phí vận chuyển)"},
    ],
}

METRIC_GROUP = {
    "title": "Bạn muốn xem chỉ tiêu nào?",
    "options": [
        {"label": "Doanh thu", "prefix": "Doanh thu"},
        {"label": "Số đơn hàng", "prefix": "Số đơn hàng"},
        {"label": "Số khách hàng", "prefix": "Số khách hàng"},
        {"label": "Số lượng bán ra", "prefix": "Số lượng bán ra"},
    ],
}


def plan(question):
    """Trả về {'base': ..., 'groups': [...]} hoặc None. Chỉ gợi ý những gì hệ thống thật sự trả lời được."""
    q = question.strip()
    s = q.lower()
    base = _squash(q)
    groups = []

    generic = [g for g in GENERIC_METRIC if g in s]
    vague = [v for v in VAGUE_TIME if v in s]
    money = any(w in s for w in GREY) and not any(w in s for w in CLEAR_PAY)
    has_metric = any(w in s for w in METRIC_WORDS)
    rank = any(w in s for w in RANK) and not has_metric

    if generic:
        text = _remove(q, GENERIC_METRIC)
        text = re.sub(r"\b(" + "|".join(re.escape(f) for f in FILLERS) + r")\b", " ", text,
                      flags=re.IGNORECASE)
        base = _squash(text)
        groups.append(METRIC_GROUP)
    elif money:
        groups.append(MONEY_GROUP)
    elif rank:
        groups.append(_rank_group(_entity(s)))
    elif not has_metric:
        groups.append(METRIC_GROUP)

    if vague:
        base = _squash(_remove(base, vague))

    if not YEAR_RE.search(s):
        groups.append(_year_group(allow_all=not SPECIFIC_PERIOD_RE.search(s)))

    if not groups:
        return None
    return {"base": base, "groups": groups}