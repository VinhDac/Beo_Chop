"""CỖ MÁY 5 TRẠM — lõi: định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên khối.  (D-10)

Canh những chỗ hỏng mà vẫn "trông có vẻ chạy":

  1. **Từ điển nhất quán** — năm trạm đúng thứ tự QC, mỗi khối Làm thuộc đúng một trạm,
     mọi đại lượng khai đủ nhãn/đơn vị/ô.
  2. **Chuẩn hoá bất biến** — chạy hai lần bằng một lần, qua JSON không đổi; khối lạ được
     GIỮ để soát lỗi gọi tên (vứt đi là cắt đôi chuỗi nối dây trong im lặng).
  3. **Mỗi loại lỗi nói đúng chỗ**: khối sai trạm, đại lượng sai trạm, khác đơn vị, hai
     quyết định trên một đường, trạm không ra được kết quả, Gom sai, tham số không có.
  4. **Cỗ máy đủ năm trạm thì SẠCH** — không một lỗi, không một cảnh báo.
  5. **Đánh số + chữ trên khối** do Python dựng, đúng từng chữ.

Chạy:  python tests\\test_may.py
"""
import copy
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import core  # noqa: E402
from cat_studio import may as M  # noqa: E402
from cat_studio import tram as T  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def loi(ds, tram=None):
    return [p for p in ds if p["severity"] == "error" and (tram is None or p["tram"] == tram)]


def canh(ds, tram=None):
    return [p for p in ds if p["severity"] == "warning" and (tram is None or p["tram"] == tram)]


def noi(*ids):
    """Chuỗi thẳng a → b → c."""
    return [{"from": a, "to": b, "port": "out"} for a, b in zip(ids, ids[1:])]


def dk(trai, phep, phai):
    return {"trai": trai, "phep": phep, "phai": phai}


def _doi_nhanh(m):
    """Hoán vị vị trí hai khối Hỏi đầu nhánh ở trạm ②: nhánh nào NẰM TRÊN được thử trước,
    nên đây là đổi luật chứ không phải đổi cách bày."""
    hoi = [s for s in m["tram"][T.TIN_HIEU]["steps"] if s.get("type") == T.HOI]
    hoi[0]["pos"], hoi[1]["pos"] = hoi[1]["pos"], hoi[0]["pos"]


# ---------------------------------------------------------------------------
# Một cỗ máy ĐỦ năm trạm, dựng tay — mọi mục sau đều sửa từ bản này.
# ---------------------------------------------------------------------------
def may_du():
    m = M.may_moi("Theo EMA")
    m["tham_so"] = [core.make_tham_so("nguong_rsi", "", 70, "so")]

    def tram(k, *khoi, canh_=None):
        bd = m["tram"][k]["steps"][0]
        steps = [bd] + list(khoi)
        for i, s in enumerate(steps):
            s["pos"] = [80.0, 300.0 + 120 * i]
        m["tram"][k]["steps"] = steps
        m["tram"][k]["edges"] = canh_ if canh_ is not None else noi(*[s["id"] for s in steps])
        return steps

    tram(T.CHON_MA, M.khoi_lam("vao_ro"))
    # ② rẽ hai nhánh: EMA nhanh trên chậm → LÊN; RSI quá mua → ĐỨNG NGOÀI.
    bd2 = m["tram"][T.TIN_HIEU]["steps"][0]
    h_len = M.khoi_hoi([dk({"ten": "ema", "chu_ky": 20}, ">", {"ten": "ema", "chu_ky": 50})],
                       "Xu hướng lên?")
    b_len = M.khoi_lam("bao", huong="len", thoi_han=24)
    h_qm = M.khoi_hoi([dk({"ten": "rsi"}, ">", {"value": "nguong_rsi"})], "Quá mua?")
    b_ngoai = M.khoi_lam("bao", huong="dung_ngoai", thoi_han=24)
    bd2["pos"] = [80.0, 300.0]
    h_len["pos"], b_len["pos"] = [80.0, 420.0], [80.0, 540.0]
    h_qm["pos"], b_ngoai["pos"] = [300.0, 460.0], [300.0, 580.0]
    m["tram"][T.TIN_HIEU]["steps"] = [bd2, h_len, b_len, h_qm, b_ngoai]
    m["tram"][T.TIN_HIEU]["edges"] = (noi(bd2["id"], h_len["id"], b_len["id"])
                                      + noi(bd2["id"], h_qm["id"], b_ngoai["id"]))
    tram(T.CHIA_VON, M.khoi_lam("dat_ty_trong", cach="chia_deu"))
    tram(T.RUI_RO, M.khoi_hoi([dk({"ten": "lai_lo_pt"}, "<=", {"value": -5})], "Lỗ quá 5%?"),
         M.khoi_lam("dua_ve_0"), M.khoi_lam("cam_vao_lai", so_nen=10))
    tram(T.KHOP_LENH, M.khoi_lam("lenh_thi_truong"))
    return m


def sua(m, tram, i, **o):
    """Sửa khối thứ `i` của trạm `tram` (0 = Bắt đầu)."""
    m["tram"][tram]["steps"][i].update(o)
    return m


# ================= 1. từ điển =================
print("\n▸ Từ điển 5 trạm")
kiem("đúng năm trạm, đúng thứ tự khung QC (Universe → Alpha → Portfolio → Risk → Execution)",
     [t["qc"] for t in T.TRAM] == ["Universe Selection", "Alpha", "Portfolio Construction",
                                   "Risk Management", "Execution"]
     and [t["key"] for t in T.TRAM] == T.TRAM_KEYS)
kiem("mỗi trạm có lịch mặc định nằm trong danh sách lịch của nó",
     all(t["lich_mac_dinh"] in t["lich"] and all(x in T.LICH for x in t["lich"]) for t in T.TRAM))
kiem("mỗi khối Làm thuộc đúng một trạm có thật, có nhãn, vai hợp lệ",
     all(v["tram"] in T.TRAM_KEYS and v["nhan"] and v["vai"] in ("quyet_dinh", "phu")
         for v in T.KHOI_LAM.values()))
kiem("trạm ④ là trạm DUY NHẤT không bắt buộc có khối Làm (không quản rủi ro là một lựa chọn)",
     set(T.CAN_CO) == set(T.TRAM_KEYS) - {T.RUI_RO})
kiem("khối bắt buộc của mỗi trạm đúng là khối của trạm đó",
     all(T.KHOI_LAM[x]["tram"] == k for k, ds in T.CAN_CO.items() for x in ds))
_xau = [t["key"] for t in T.TOAN_HANG
        if not t["nhan"] or t["don_vi"] not in T.DON_VI
        or any(k not in T.THAM_SO_TH for k in t["tham_so"])
        or (t["tram"] is not None and any(x not in T.TRAM_KEYS for x in t["tram"]))
        or ("dong" in t["tham_so"]) != bool(t["dong"])]
kiem("mọi đại lượng: có nhãn, đơn vị có thật, ô có thật, trạm có thật", not _xau, f"— {_xau}")
kiem("khoá đại lượng không trùng", len(T.TOAN_HANG_THEO_KEY) == len(T.TOAN_HANG))
kiem("vị thế/lãi lỗ KHÔNG đọc được ở ① ② (chưa có gì để giữ), tín hiệu chỉ ở ③",
     not T.doc_duoc_o("lai_lo_pt", T.CHON_MA) and not T.doc_duoc_o("lai_lo_pt", T.TIN_HIEU)
     and T.doc_duoc_o("lai_lo_pt", T.RUI_RO) and T.doc_duoc_o("huong_tin_hieu", T.CHIA_VON)
     and not T.doc_duoc_o("huong_tin_hieu", T.TIN_HIEU))

# ================= 2. tạo mới + chuẩn hoá =================
print("\n▸ Cỗ máy mới và chuẩn hoá")
mm = M.may_moi()
kiem("cỗ máy mới: năm trạm, mỗi trạm ĐÚNG một khối Bắt đầu, ① ③ có Gom",
     list(mm["tram"]) == T.TRAM_KEYS
     and all(len(mm["tram"][k]["steps"]) == 1
             and mm["tram"][k]["steps"][0]["kind"] == core.KIND_START for k in T.TRAM_KEYS)
     and "gom" in mm["tram"][T.CHON_MA] and "gom" in mm["tram"][T.CHIA_VON]
     and "gom" not in mm["tram"][T.TIN_HIEU])
kiem("nhận ra cỗ máy 5 trạm, KHÔNG nhận nhầm sơ đồ Entry/Manage cũ",
     M.la_may(mm) and not M.la_may(core.new_process()))
d0 = may_du()
c1 = M.chuan_hoa(d0)
c2 = M.chuan_hoa(c1)
kiem("chuẩn hoá BẤT BIẾN: hai lần bằng một lần", c1 == c2)
kiem("qua JSON rồi chuẩn hoá lại vẫn y nguyên", M.chuan_hoa(json.loads(json.dumps(c1))) == c1)
_goc = copy.deepcopy(d0)
M.chuan_hoa(d0)
kiem("chuẩn hoá KHÔNG sửa vào dict truyền vào", d0 == _goc)
_ema = c1["tram"][T.TIN_HIEU]["steps"][1]["conditions"][0]["trai"]
kiem("ô bỏ trống của đại lượng nhận MẶC ĐỊNH, khung = khung của khối Bắt đầu trạm đó",
     _ema == {"ten": "ema", "khung": "H1", "chu_ky": 20.0, "lui": 0},
     f"— {_ema}")
_rsi = c1["tram"][T.TIN_HIEU]["steps"][3]["conditions"][0]
kiem("tên tham số ở vế phải được GIỮ là tên (không đổi thành số)",
     _rsi["phai"] == {"value": "nguong_rsi"})
_c = M.chuan_hoa(sua(may_du(), T.CHIA_VON, 1, cach="co_dinh"))
_k = _c["tram"][T.CHIA_VON]["steps"][1]
kiem("đổi cách chia sang «cố định» → ô % hiện ra với mặc định, ô của cách khác biến mất",
     _k.get("pt") == 10 and "chu_ky" not in _k, f"— {_k}")
_c = M.chuan_hoa(sua(may_du(), T.CHIA_VON, 1, cach="rui_ro_ngang", pt=33))
_k = _c["tram"][T.CHIA_VON]["steps"][1]
kiem("«rủi ro ngang nhau» mang khung + chu kỳ, KHÔNG mang ô % bỏ lại từ cách cũ",
     _k.get("khung") == "D1" and _k.get("chu_ky") == 20 and "pt" not in _k, f"— {_k}")
_l = M.may_moi()
_l["tram"][T.TIN_HIEU]["steps"].append({"kind": "action", "id": "lala", "type": "khoi_tuong_lai",
                                        "pos": [0, 0], "x": 1})
_cl = M.chuan_hoa(_l)
kiem("khối LẠ được giữ nguyên (không biến mất trong im lặng)",
     any(s.get("type") == "khoi_tuong_lai" and s.get("x") == 1
         for s in _cl["tram"][T.TIN_HIEU]["steps"]))
_t = M.chuan_hoa({"dang": "may5", "tram": {}})
kiem("file thiếu trạm → trạm đó được dựng khối Bắt đầu", all(
    _t["tram"][k]["steps"][0]["kind"] == core.KIND_START for k in T.TRAM_KEYS))
try:
    M.chuan_hoa({"dang": "may5", "phien_ban": 99})
    kiem("cỗ máy của bản MỚI HƠN → từ chối, không mở rồi làm mất khối", False)
except ValueError as e:
    kiem("cỗ máy của bản MỚI HƠN → từ chối, không mở rồi làm mất khối", "bản mới hơn" in str(e))
_lich = M.chuan_hoa(sua(may_du(), T.TIN_HIEU, 0, lich="dau_thang", khung="Q7"))
_bd2 = _lich["tram"][T.TIN_HIEU]["steps"][0]
kiem("lịch không hợp trạm (② không chạy 'đầu tháng') → về lịch mặc định của trạm",
     _bd2["lich"] == "moi_nen" and _bd2["khung"] == "H1", f"— {_bd2}")
_pv = M.chuan_hoa(sua(may_du(), T.CHON_MA, 0,
                      pham_vi={"loai": "danh_sach", "ma": [" eurusd", "GBPUSD", "eurusd", ""]}))
kiem("danh sách mã riêng của ①: viết HOA, bỏ trống, bỏ trùng",
     _pv["tram"][T.CHON_MA]["steps"][0]["pham_vi"] == {"loai": "danh_sach",
                                                      "ma": ["EURUSD", "GBPUSD"]})

# ================= 3. cỗ máy đủ thì sạch =================
print("\n▸ Cỗ máy đủ năm trạm")
ds = M.soat(may_du())
kiem("KHÔNG một lỗi, KHÔNG một cảnh báo", not ds, f"— {[p['message'][:60] for p in ds]}")

ds = M.soat(M.may_moi())
_tr = sorted({p["tram"] for p in loi(ds)})
kiem("cỗ máy TRẮNG: lỗi đúng ở ① ② ③ ⑤ (thiếu khối ra kết quả), ④ không lỗi",
     _tr == sorted([T.CHON_MA, T.TIN_HIEU, T.CHIA_VON, T.KHOP_LENH]), f"— {_tr}")
_m = next((p["message"] for p in loi(ds, T.TIN_HIEU)), "")
kiem("câu báo nói rõ thiếu gì và hậu quả", "Báo tín hiệu" in _m and "không mã nào có tín hiệu" in _m
     and "② Tín hiệu" in _m, f"— {_m[:90]}")

# ================= 4. từng loại lỗi =================
print("\n▸ Mỗi loại lỗi nói đúng chỗ")
m = may_du()
m["tram"][T.CHIA_VON]["steps"][1] = M.khoi_lam("bao", huong="len", thoi_han=5,
                                               id=m["tram"][T.CHIA_VON]["steps"][1]["id"],
                                               pos=[80.0, 420.0])
ds = M.soat(m)
_m = [p for p in loi(ds, T.CHIA_VON) if "là khối của trạm" in p["message"]]
kiem("khối Làm đặt SAI trạm («Báo tín hiệu» ở ③) → lỗi gọi tên trạm đúng của nó",
     _m and "② Tín hiệu" in _m[0]["message"] and _m[0]["step"], f"— {_m[:1]}")
kiem("…và ③ mất khối chia vốn → thêm lỗi «không mã nào được chia vốn»",
     any("không mã nào được chia vốn" in p["message"] for p in loi(ds, T.CHIA_VON)))

m = may_du()
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"] = [dk({"ten": "lai_lo_pt"}, ">", {"value": 0})]
ds = M.soat(m)
kiem("đại lượng không đọc được ở trạm này (lãi/lỗ vị thế ở ②) → lỗi, nói chỗ nào đọc được",
     any("chỉ đọc được ở" in p["message"] and "④ Rủi ro" in p["message"] for p in loi(ds)))

m = may_du()
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"] = [dk({"ten": "rsi"}, ">", {"ten": "ema"})]
ds = M.soat(m)
kiem("so hai đại lượng KHÁC LOẠI (RSI với EMA) → lỗi đơn vị",
     any("khác loại" in p["message"] for p in loi(ds, T.TIN_HIEU)))
m = may_du()
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"] = [
    dk({"ten": "gia_dong"}, ">", {"ten": "sma", "chu_ky": 200, "he_so": 1.02})]
kiem("so hai đại lượng CÙNG loại, có hệ số nhân → sạch", not M.soat(m))

m = may_du()
m["tram"][T.TIN_HIEU]["steps"][3]["conditions"] = [dk({"ten": "rsi"}, ">", {"value": "khong_co"})]
ds = M.soat(m)
kiem("tham số không có trong bảng → lỗi gọi tên tham số",
     any('"khong_co"' in p["message"] for p in loi(ds)))
m = may_du()
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"][0]["trai"]["chu_ky"] = 0
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"][0]["phai"]["chu_ky"] = 2.5
ds = M.soat(m)
kiem("chu kỳ 0 → lỗi «không được nhỏ hơn 1»; chu kỳ 2.5 → lỗi «cần số nguyên»",
     any("nhỏ hơn 1" in p["message"] for p in loi(ds))
     and any("số nguyên" in p["message"] for p in loi(ds)))
m = may_du()
m["tham_so"].append(core.make_tham_so("ck", "", 7.5))
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"][0]["trai"]["chu_ky"] = "ck"
ds = M.soat(m)
kiem("tên tham số trong ô chu kỳ → soát GIÁ TRỊ của tham số (7.5 không nguyên)",
     any('tham số "ck" = 7.5' in p["message"] for p in loi(ds)))
m = may_du()
m["tram"][T.TIN_HIEU]["steps"][1]["conditions"] = [
    dk({"ten": "macd", "nhanh": 30, "cham": 26}, ">", {"value": 0})]
kiem("MACD nhanh ≥ chậm → lỗi", any("MACD" in p["message"] for p in loi(M.soat(m))))

m = may_du()
_r = m["tram"][T.RUI_RO]
_cam = _r["steps"][3]
_r["steps"][3] = M.khoi_lam("giam_ve", id=_cam["id"], pos=_cam["pos"], pt=3)
ds = M.soat(m)
_m = [p for p in loi(ds, T.RUI_RO) if "cùng một đường" in p["message"]]
kiem("hai khối QUYẾT ĐỊNH nối tiếp (Đưa về 0 → Giảm về) → lỗi, báo ở khối SAU",
     len(_m) == 1 and _m[0]["step"] == _cam["id"], f"— {len(_m)}")
kiem("còn «Đưa về 0 → Cấm vào lại» (quyết định + phụ) là chuỗi hợp lệ",
     not [p for p in loi(M.soat(may_du()), T.RUI_RO)])

m = may_du()
_g = m["tram"][T.TIN_HIEU]
_g["steps"][3]["type"] = "bao"            # nhánh thứ hai mất cổng → hai nhánh không cổng
_g["steps"][3].update(huong="xuong", thoi_han=5)
_g["steps"][1]["type"] = "bao"
_g["steps"][1].update(huong="len", thoi_han=5)
ds = M.soat(m)
kiem("luật rẽ nhánh của sơ đồ dùng lại nguyên vẹn: hai nhánh không cổng → lỗi gọi khối «Hỏi»",
     any("không có cổng" in p["message"] and '"Hỏi"' in p["message"] for p in loi(ds, T.TIN_HIEU)))

m = may_du()
m["tram"][T.KHOP_LENH]["edges"] = []
ds = M.soat(m)
kiem("khối không nối vào → cảnh báo «không bao giờ chạy tới» + lỗi trạm ⑤ không ra lệnh",
     any("không bao giờ chạy tới" in p["message"] for p in canh(ds, T.KHOP_LENH))
     and any("không bao giờ thành lệnh" in p["message"] for p in loi(ds, T.KHOP_LENH)))
m = may_du()
m["tram"][T.KHOP_LENH]["steps"] = m["tram"][T.KHOP_LENH]["steps"][1:]
ds = M.soat(m)
kiem("trạm mất khối Bắt đầu → MỘT lỗi rõ «không biết chạy lúc nào, cho ai»",
     len([p for p in loi(ds, T.KHOP_LENH) if "chưa có khối Bắt đầu" in p["message"]]) == 1)

m = may_du()
m["tram"][T.CHON_MA]["gom"] = {"top_n": 0, "xep": "giua"}
ds = M.soat(m)
kiem("Gom ①: giữ 0 mã, xếp «giữa» → hai lỗi Gom",
     len([p for p in loi(ds, T.CHON_MA) if "Gom" in p["message"]]) == 2)
m = may_du()
m["tram"][T.CHON_MA]["gom"] = {"top_n": 5}
ds = M.soat(m)
kiem("Gom ① giữ 5 mã mà «Cho vào rổ» không có điểm → cảnh báo (mã đó luôn xếp cuối)",
     any("không có điểm" in p["message"] for p in canh(ds, T.CHON_MA)))
m["tram"][T.CHON_MA]["steps"][1]["diem"] = {"ten": "roc_pt", "chu_ky": 60}
kiem("…có điểm (Đổi giá % 60 nến) → sạch", not M.soat(m))
m = may_du()
m["tram"][T.CHIA_VON]["gom"] = {"giu_tien_pt": 100, "tran_moi_ma_pt": 0}
kiem("Gom ③: giữ 100% tiền mặt, trần 0% → lỗi",
     len([p for p in loi(M.soat(m), T.CHIA_VON) if "Gom" in p["message"]]) == 2)

m = may_du()
sua(m, T.CHON_MA, 0, pham_vi={"loai": "danh_sach", "ma": []})
kiem("① danh sách riêng mà rỗng → lỗi «rổ luôn rỗng»",
     any("rổ luôn rỗng" in p["message"] for p in loi(M.soat(m), T.CHON_MA)))
m = may_du()
sua(m, T.CHON_MA, 0, pham_vi={"loai": "danh_sach", "ma": ["EURUSD", "XAU USD!"]})
kiem("① mã viết sai → lỗi gọi tên mã", any("XAU USD!" in p["message"]
                                           for p in loi(M.soat(m), T.CHON_MA)))

m = may_du()
sua(m, T.CHIA_VON, 1, cach="theo_tin_cay")
ds = M.soat(m)
kiem("③ chia theo độ tin cậy mà ② không khối Báo nào đặt tin cậy → cảnh báo giữa hai trạm",
     any("độ tin cậy" in p["message"] for p in canh(ds, T.CHIA_VON)))
sua(m, T.TIN_HIEU, 2, tin_cay=0.8)
kiem("…đặt tin cậy ở một khối Báo → hết cảnh báo", not M.soat(m))

m = may_du()
m["tram"][T.TIN_HIEU]["steps"].append({"kind": "action", "id": "lala", "type": "khoi_tuong_lai",
                                       "pos": [600.0, 900.0]})
kiem("khối lạ → lỗi gọi tên loại khối", any("khoi_tuong_lai" in p["message"]
                                           for p in loi(M.soat(m), T.TIN_HIEU)))
kiem("sơ đồ Entry/Manage cũ đưa nhầm vào → một lỗi, không nổ",
     len(M.soat(dict(core.new_process(), dang="cu"))) == 1)

# ================= 5. đánh số + chữ =================
print("\n▸ Đánh số và chữ trên khối")
ds_so = M.danh_so(may_du())
_s2 = ds_so[T.TIN_HIEU]["order"]
kiem("mỗi trạm đánh số riêng; ② rẽ hai nhánh → 1 · 1A · 1A.1 · 1B · 1B.1",
     sorted(_s2.values()) == ["1", "1A", "1A.1", "1B", "1B.1"], f"— {sorted(_s2.values())}")
kiem("đánh số là việc riêng của từng trạm: ⑤ trạm khác vẫn bắt đầu từ 1",
     list(ds_so[T.KHOP_LENH]["order"].values()) == ["1", "2"])

may_the = M.kem_the(may_du())
the = {k: may_the["tram"][k]["cards"] for k in T.TRAM_KEYS}


def chu(k, i):
    return [x["text"] for x in the[k][i]["lines"]]


kiem("Bắt đầu ①", chu(T.CHON_MA, 0) == ["Một lần, lúc bắt đầu", "cho mỗi mã của màn chơi"],
     f"— {chu(T.CHON_MA, 0)}")
kiem("Bắt đầu ②", chu(T.TIN_HIEU, 0) == ["Mỗi nến H1", "cho mỗi mã trong rổ"],
     f"— {chu(T.TIN_HIEU, 0)}")
kiem("Bắt đầu ③", chu(T.CHIA_VON, 0) == ["Khi tín hiệu đổi",
                                         "cho mỗi mã đang có tín hiệu hoặc đang giữ"])
kiem("Hỏi: điều kiện viết bằng ký hiệu, đủ khung + chu kỳ",
     chu(T.TIN_HIEU, 1) == ["EMA(H1, 20) > EMA(H1, 50)"], f"— {chu(T.TIN_HIEU, 1)}")
kiem("Hỏi: tham số hiện cả TÊN lẫn GIÁ TRỊ",
     chu(T.TIN_HIEU, 3) == ["RSI(H1, 14) > nguong_rsi = 70"], f"— {chu(T.TIN_HIEU, 3)}")
kiem("Báo tín hiệu", chu(T.TIN_HIEU, 2) == ["LÊN · hạn 24 nến"], f"— {chu(T.TIN_HIEU, 2)}")
kiem("Rủi ro: Hỏi → Đưa về 0 → Cấm vào lại",
     chu(T.RUI_RO, 1) == ["Lãi/lỗ vị thế % ≤ -5"] and chu(T.RUI_RO, 2) == ["bán sạch mã này"]
     and chu(T.RUI_RO, 3) == ["cấm vào lại 10 nến"], f"— {chu(T.RUI_RO, 1)}")
kiem("Lệnh thị trường 100% → «khớp ngay toàn bộ phần lệch»",
     chu(T.KHOP_LENH, 1) == ["khớp ngay toàn bộ phần lệch"])
kiem("thẻ mang NHÃN đánh số, màu theo vai, đánh dấu cổng",
     the[T.TIN_HIEU][1]["so"] == "1A" and the[T.TIN_HIEU][1]["la_cong"]
     and the[T.TIN_HIEU][1]["mau"] == "hoi" and the[T.TIN_HIEU][2]["mau"] == "lam"
     and the[T.TIN_HIEU][0]["mau"] == "start", f"— {the[T.TIN_HIEU][1]['so']}")
kiem("toán hạng lùi nến + hệ số nhân hiện đúng",
     M.toan_hang_chu({"ten": "gia_dong", "khung": "D1", "lui": 1, "he_so": 1.02})
     == "Giá đóng(D1)[1] × 1.02")
kiem("đại lượng nhiều đường hiện tên đường",
     M.toan_hang_chu(M._chuan_toan_hang({"ten": "macd"}, "H4"))
     == "MACD(H4, 12, 26, 9, đường MACD)",
     f"— {M.toan_hang_chu(M._chuan_toan_hang({'ten': 'macd'}, 'H4'))}")
kiem("mọi khối Làm đều dựng được chữ (không khối nào rơi vào «?»)",
     all("?" not in " ".join(M.dong_khoi(M._chuan_lam(M.khoi_lam(k), v["tram"], "H1"),
                                         v["tram"], {}))
         for k, v in T.KHOI_LAM.items()))

# ---------------------------------------------------------------------------
print("\n▸ Vân tay LOGIC — vé nộp của trò chơi (D-10, phần 6)")
# ---------------------------------------------------------------------------
from cat_studio import mau_tram as MT  # noqa: E402

a = MT.may_tu_mau("A")
b = MT.may_tu_mau("B")          # dựng lại y hệt: cùng luật, id khối mới toàn bộ
kiem("hai cỗ máy cùng LUẬT, id khác nhau → CÙNG vân tay",
     M.van_tay(a) == M.van_tay(b), f"({M.van_tay(a)})")
kiem("lắp lại chính mẫu đang dùng → vân tay không đổi",
     M.van_tay(MT.ap_mau(copy.deepcopy(a), T.TIN_HIEU, "giao_cat_ema")) == M.van_tay(a))

d = copy.deepcopy(a)
d["name"] = "Tên khác hẳn"
d["tram"][T.TIN_HIEU]["steps"][0]["pos"] = [999.0, 999.0]
d["tram"][T.TIN_HIEU]["steps"][0]["name"] = "Khởi hành"
kiem("đổi tên cỗ máy, tên khối, kéo khối đi chỗ khác → vân tay KHÔNG đổi",
     M.van_tay(d) == M.van_tay(a))

e = copy.deepcopy(a)
e["tram"][T.TIN_HIEU]["steps"].append(M.khoi_lam("bao", huong="xuong"))
kiem("thêm một khối KHÔNG nối vào đâu → không đổi (khối không chạy thì không phải luật)",
     M.van_tay(e) == M.van_tay(a))

for ten, sua in (
    ("đổi giá trị một tham số",
     lambda m: m["tham_so"][0].update(gia_tri=999)),
    ("đổi một ô Gom",
     lambda m: m["tram"][T.CHON_MA].update(gom={"top_n": 3, "xep": "cao"})),
    ("bỏ một dây nối",
     lambda m: m["tram"][T.TIN_HIEU].update(edges=m["tram"][T.TIN_HIEU]["edges"][:-1])),
    ("đổi THỨ TỰ NHÁNH (nhánh trên thử trước — đó là luật)",
     lambda m: _doi_nhanh(m)),
):
    m2 = copy.deepcopy(a)
    sua(m2)
    kiem(f"{ten} → vân tay ĐỔI", M.van_tay(m2) != M.van_tay(a))

kiem("vân tay bất biến: chuẩn hoá lại, hay đi qua JSON, vẫn thế",
     M.van_tay(M.chuan_hoa(a)) == M.van_tay(a)
     and M.van_tay(json.loads(json.dumps(a))) == M.van_tay(a))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
