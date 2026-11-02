import json

tests = {t["id"]: t for t in json.load(open("tests/test_set.json", encoding="utf-8"))}

for name in ("round1", "round2", "round3"):
    strict = json.load(open(f"results/{name}.json", encoding="utf-8"))["results"]
    loose = json.load(open(f"results/{name}_regraded.json", encoding="utf-8"))["results"]
    s_ok = l_ok = 0
    for rs, rl in zip(strict, loose):
        new_hv = tests[rs["id"]]["hanh_vi_mong_doi"]
        s, l = rs["trang_thai"], rl["trang_thai_noi"]
        if new_hv == "hoi_lai" and rs["hanh_vi_mong_doi"] != "hoi_lai":
            s = l = "khong_hoi_lai"
        s_ok += s == "dung"
        l_ok += l == "dung"
    print(name, "nghiêm:", s_ok, "/ 70   nới:", l_ok, "/ 70")