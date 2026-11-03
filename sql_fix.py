import re

_LIMIT_END = re.compile(r"\s+LIMIT\s+(\d+)\s*;?\s*$", re.IGNORECASE)
_SELECT_START = re.compile(r"^SELECT\s+(DISTINCT\s+)?", re.IGNORECASE)


def _outside_quotes(text, pos):
    return text[:pos].count("'") % 2 == 0


def _limit_to_top(s, notes):
    m = _LIMIT_END.search(s)
    if not m or not _outside_quotes(s, m.start()):
        return s
    if len(re.findall(r"\bLIMIT\b", s, re.IGNORECASE)) != 1:
        return s
    if re.search(r"\b(TOP|OFFSET|UNION)\b", s, re.IGNORECASE) or re.match(r"WITH\b", s, re.IGNORECASE):
        return s
    sm = _SELECT_START.match(s)
    if not sm:
        return s
    n = m.group(1)
    notes.append(f"LIMIT {n} thành TOP {n}")
    return "SELECT " + (sm.group(1) or "") + "TOP " + n + " " + s[sm.end():m.start()] + ";"


def fix_sql(sql):
    """Trả về (sql_moi, danh_sach_sua). Chỉ sửa câu bắt đầu bằng SELECT hoặc WITH."""
    notes = []
    s = sql.strip()
    if not re.match(r"(SELECT|WITH)\b", s, re.IGNORECASE):
        return sql, notes

    s = _limit_to_top(s, notes)

    t = re.sub(r"`([^`]+)`", r"[\1]", s)
    if t != s:
        notes.append("dấu ` thành [ ]")
        s = t

    t = re.sub(r"\bIFNULL\s*\(", "ISNULL(", s, flags=re.IGNORECASE)
    if t != s:
        notes.append("IFNULL thành ISNULL")
        s = t

    t = re.sub(r"\bEXTRACT\s*\(\s*(YEAR|MONTH|DAY)\s+FROM\s+([^()]+?)\s*\)",
               lambda m: m.group(1).upper() + "(" + m.group(2) + ")", s, flags=re.IGNORECASE)
    if t != s:
        notes.append("EXTRACT thành YEAR, MONTH hoặc DAY")
        s = t

    return (s if notes else sql), notes