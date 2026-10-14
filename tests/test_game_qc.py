"""LUẬT CHƠI + CHẠY QC TỪ TRONG APP — trên máy chủ QC giả.  (D-05 · D-06 · D-08)

Được canh:

  1. **Luật chấm** đúng như D-05/D-08: ⭐ chạy sạch · ⭐⭐ thắng boss trên màn đã thấy ·
     ⭐⭐⭐ vẫn thắng trên màn ẩn — mỗi sao cần mọi sao trước nó. Độ gọn = khối + tham số.
  2. **Màn ẩn là ẩn**: thông tin màn gửi ra giao diện không mang ngày của màn ẩn; lượt nộp
     không trả đường vốn, không trả lượt; không mở lại được lượt màn ẩn để xem từng nến.
  3. **Luật nộp**: chưa ▶ đầy đủ đúng cỗ máy đó thì không được nộp (báo NGAY, chưa gửi gì).
     Sửa sơ đồ là thành cỗ máy khác. Mỗi lần nộp được đếm.
  4. **Việc nền**: `bat_dau` trả ngay, tiến độ tăng dần tới 100%, một lượt một lúc, lỗi QC
     về thành một câu tiếng Việt trong trạng thái — không treo, không traceback.
  5. **Xem lại**: lượt đã thấy xem được từng dòng "vì sao" kèm giờ, soi được lên sơ đồ, mở
     lại được từ lịch sử mà không chạy lại.
  6. **Sáng tạo** (D-07): symbol / ngày / vốn tuỳ ý, soát đầu vào tại máy, không chấm sao.

Chạy:  python tests\\test_game_qc.py
"""
import copy
import io
import json
import os
import sys
import tempfile
import time

TESTS = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(TESTS)
sys.path.insert(0, GOC)
sys.path.insert(0, os.path.join(GOC, "lean"))
sys.path.insert(0, TESTS)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

import gia_lap_qc as gl  # noqa: E402
import qc_gia  # noqa: E402
from cat_studio import bo_chay as bc  # noqa: E402
from cat_studio import core  # noqa: E402
from cat_studio import game  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import mau  # noqa: E402
from cat_studio import qc_chay  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def bat(f, *a, **k):
    try:
        f(*a, **k)
    except Exception as e:  # noqa: BLE001
        return e
    return None


DOC = mau.so_do_mau()
SPREAD = bc.CaiDat(spread_diem=20.0, point=0.01).spread_gia
_NEN = {}


def chon_nen(ch):
    """"QC" chạy trên nến khác nhau theo năm của khoảng ngày — màn đã thấy và màn ẩn ra hai
    kết quả khác nhau như thật. Cùng năm → cùng nến (để kết quả tất định)."""
    nam = int((ch.get("tu") or "2025")[:4])
    if nam not in _NEN:
        _NEN[nam] = gl.du_lieu(np, seed=nam % 97, ngay=4)
    return _NEN[nam]


# Sổ game và nhật ký vào thư mục tạm — bài kiểm không đụng du_lieu/ thật.
TD = tempfile.mkdtemp()
luu_tru.goc = lambda: TD
gia = qc_gia.QCGia(chon_nen({}), SPREAD, chon_nen=chon_nen)
qc = qc_gia.qc_cho(gia)


def viec_moi(tao_qc=None):
    return qc_chay.ViecQC(tao_qc=tao_qc or (lambda: qc), thu_muc_nhat_ky=TD)


def chay(v, *a, **k):
    """Bắt đầu một lượt, chờ xong, trả trạng thái cuối."""
    v.bat_dau(*a, **k)
    v.cho(600)
    return v.trang_thai()


# ================= 1. luật chấm =================
print("\n▸ Luật chấm (D-05 · D-08)")
M = {"thong_ke": {"lai_pt": 12.5, "so_dong": 3}, "mua_giu_pt": 10.0}
c = game.cham(M)
kiem("cham: lãi %, % boss, thắng boss, số lệnh đóng, sạch",
     c == {"lai_pt": 12.5, "mua_giu_pt": 10.0, "thang_boss": True, "so_dong": 3, "sach": True})
kiem("cham: thiếu giá boss → không ai thắng ai",
     game.cham({"thong_ke": {"lai_pt": 5, "so_dong": 1}, "mua_giu_pt": None})["thang_boss"]
     is False)
kiem("cham: không lệnh nào đóng → KHÔNG sạch (không giao dịch thì chẳng chứng minh gì)",
     game.cham({"thong_ke": {"lai_pt": 0, "so_dong": 0}, "mua_giu_pt": -3})["sach"] is False)
thang, thua = {"sach": True, "thang_boss": True}, {"sach": True, "thang_boss": False}
kiem("sao: 0 · 1 · 2 · 3 đúng bậc thang",
     [game.sao(None), game.sao({"sach": False, "thang_boss": True}), game.sao(thua),
      game.sao(thang), game.sao(thang, thua), game.sao(thang, thang)] == [0, 0, 1, 2, 2, 3])
kiem("sao: thắng màn ẩn mà THUA màn đã thấy vẫn chỉ ⭐ — mỗi sao cần mọi sao trước nó",
     game.sao(thua, thang) == 1)
g = game.do_gon(DOC)
kiem("độ gọn = số khối (trừ khối Bắt đầu) + số tham số", g == {"so_khoi": 11, "so_tham_so": 11,
                                                             "tong": 22}, f"({g})")
m0 = game.danh_sach_man()[0]
kiem("thông tin màn cho giao diện KHÔNG mang ngày màn ẩn (D-06: app giữ màn ẩn)",
     "an" not in m0 and "2025" not in json.dumps(m0) and m0["an_mo_ta"]
     and m0["boss"]["ten"] == "Mua rồi giữ", f"({m0['ten']})")
kiem("khoảng ngày: ▶ nhanh nằm trong màn đã thấy; màn ẩn nằm SAU màn đã thấy",
     all(m["thay"][0] <= m["nhanh"][0] <= m["nhanh"][1] <= m["thay"][1] < m["an"][0]
         for m in game.MAN))
kiem("màn không có / kiểu chạy lạ → LoiGame", isinstance(bat(game.man, "xx"), game.LoiGame)
     and isinstance(bat(game.khoang, "vang-2024", "tu_do"), game.LoiGame))

# ================= 3. luật nộp — trước khi chạy gì =================
print("\n▸ Luật nộp")
v = viec_moi()
gia.nhat.clear()
e = bat(v.bat_dau, DOC, "nop", "vang-2024")
kiem("chưa ▶ đầy đủ mà nộp → báo NGAY bằng lời, chưa gửi gì lên QC",
     isinstance(e, game.LoiGame) and "▶ đầy đủ" in str(e) and gia.nhat == []
     and not v.trang_thai()["dang_chay"])

# ================= 4–5. ▶ nhanh =================
print("\n▸ ▶ nhanh — việc nền, tiến độ, kết quả xem được")
ti_le = []
v.bat_dau(DOC, "nhanh", "vang-2024")
kiem("bat_dau trả ngay, trạng thái đang chạy", v.trang_thai()["dang_chay"] is True)
e = bat(v.bat_dau, DOC, "nhanh", "vang-2024")
kiem("một lượt một lúc — bấm lần hai khi đang chạy → LoiGame",
     isinstance(e, game.LoiGame) and "Đang có một lượt" in str(e))
while v.trang_thai()["dang_chay"]:
    ti_le.append(v.trang_thai()["ti_le_chung"])
    time.sleep(0.02)
v.cho(600)
tt = v.trang_thai()
x = tt["xong"] or {}
kiem("xong không lỗi", tt["loi"] is None and bool(x), f"({tt['loi']})" if tt["loi"] else "")
kiem("tiến độ chung tăng dần, kết thúc ở 100%",
     ti_le == sorted(ti_le) and tt["ti_le_chung"] == 1.0, f"({len(ti_le)} lần hỏi)")
up = gia.files[gia.projects[0]["projectId"]]["main.py"]
kiem("▶ nhanh chạy đúng khoảng ngày của màn (app đặt, không phải người chơi)",
     '"tu": "2024-10-01"' in up and '"den": "2024-12-31"' in up)
kiem("kết quả mang thống kê, boss, đường vốn, độ gọn; ▶ nhanh không chấm sao",
     x.get("thong_ke", {}).get("so_lenh") is not None and x.get("mua_giu_pt") is not None
     and x.get("duong_von") and x.get("do_gon", {}).get("tong") == 22
     and x.get("sao") is None and x.get("an") is False)
k = v.ket_qua
lo = k.lo(0, 50, True) if k else {"dong": []}
kiem("xem được nhật ký «vì sao»: dòng có việc, mang giờ thật (không phải «—»)",
     lo["dong"] and all(d["co_viec"] for d in lo["dong"])
     and not lo["dong"][0]["chu"].startswith("—"), f"({lo['dong'][0]['chu'][:60]}…)"
     if lo["dong"] else "")
lo_het = k.lo(0, 10, False) if k else {"tong": 0}
kiem("… bật «mọi lượt» thì thấy cả lượt không có việc, có giải thích vì sao dừng",
     lo_het["tong"] > lo["tong"] and any("hết lượt" in d["chu"] for d in lo_het["dong"]))
soi = k.soi(lo["dong"][0]["i"]) if lo["dong"] else {}
kiem("soi một lượt lên sơ đồ: đường đi, cổng, nhãn khối, câu chữ",
     soi.get("duong") and soi.get("nhan") and soi.get("chu") and "tab" in soi)

# ================= 3. ▶ đầy đủ rồi nộp =================
print("\n▸ ▶ đầy đủ → nộp")
tt = chay(v, DOC, "day_du", "vang-2024")
xd = tt["xong"] or {}
kiem("▶ đầy đủ: cả năm của màn đã thấy, chấm tối đa ⭐⭐",
     tt["loi"] is None and xd.get("tu") == "2024-01-01" and xd.get("den") == "2024-12-31"
     and xd.get("sao") == game.sao(xd.get("cham")) and xd["sao"] <= 2, f"(⭐×{xd.get('sao')})")
ve = game.ve_nop("vang-2024", game.van_tay(DOC))
kiem("sổ ghi «vé nộp» cho đúng cỗ máy này", ve is not None and ve["lai_pt"] == xd["cham"]["lai_pt"])
sua = copy.deepcopy(DOC)
sua["tham_so"][0]["gia_tri"] = 8.0
e = bat(v.bat_dau, sua, "nop", "vang-2024")
kiem("sửa sơ đồ (đổi một tham số) là thành cỗ máy khác → phải ▶ đầy đủ lại mới nộp được",
     isinstance(e, game.LoiGame))
xem_truoc = v.ket_qua
tt = chay(v, DOC, "nop", "vang-2024")
xn = tt["xong"] or {}
up = gia.files[gia.projects[0]["projectId"]]["main.py"]
kiem("nộp: chạy trên MÀN ẨN (khoảng ngày app giữ)",
     tt["loi"] is None and '"tu": "2025-01-01"' in up and xn.get("an") is True)
kiem("nộp: sao = luật chấm trên (màn đã thấy, màn ẩn); lần nộp thứ 1",
     xn.get("sao") == game.sao(ve, xn.get("cham")) and xn.get("lan_nop") == 1,
     f"(⭐×{xn.get('sao')} · thấy {ve['lai_pt']}% vs boss {ve['mua_giu_pt']}% · ẩn "
     f"{xn.get('cham', {}).get('lai_pt')}% vs boss {xn.get('cham', {}).get('mua_giu_pt')}%)")
kiem("màn đã thấy và màn ẩn là hai đoạn thị trường khác nhau (boss khác nhau)",
     ve["mua_giu_pt"] != xn.get("cham", {}).get("mua_giu_pt"))
kiem("nộp: KHÔNG trả đường vốn, không trả lượt — chỉ con số tổng",
     xn.get("duong_von") == [] and xn.get("so_luot") is None)
kiem("nộp: KHÔNG lộ ngày màn ẩn — trong kết quả, trong lịch sử, trong tên backtest trên QC; "
     "không link QC",
     "2025-01" not in json.dumps(xn) and "2025-01" not in json.dumps(game.lich_su())
     and xn.get("url") is None and game.lich_su()[0]["url"] is None
     and any("màn ẩn" in (x.get("backtestName") or "") for x in gia.goi("backtests/create"))
     and all("2025" not in (x.get("backtestName") or "") for x in gia.goi("backtests/create")
             if "màn ẩn" in (x.get("backtestName") or "")))
kiem("nộp không thay lượt đang xem — màn ẩn không bao giờ hiện từng nến",
     v.ket_qua is xem_truoc)
tdm = game.tien_do_man("vang-2024")
kiem("tiến độ màn: 1 lần nộp, sao cao nhất, độ gọn ghi kèm",
     tdm["so_lan_nop"] == 1 and tdm["sao"] == xn["sao"]
     and tdm["tot_nhat"]["do_gon"]["tong"] == 22)
chay(v, DOC, "nop", "vang-2024")
kiem("nộp lần nữa → được đếm (lần 2)", game.tien_do_man("vang-2024")["so_lan_nop"] == 2
     and v.trang_thai()["xong"]["lan_nop"] == 2)

# ================= 5. lịch sử =================
print("\n▸ Lịch sử — mở lại không chạy lại")
ls = game.lich_su()
kiem("lịch sử ghi mọi lượt, mới nhất trước",
     [x["loai"] for x in ls] == ["nop", "nop", "day_du", "nhanh"])
gia.nhat.clear()
tom = v.mo_lai(ls[3]["duong"])
kiem("mở lại lượt ▶ nhanh từ file nhật ký — KHÔNG gửi gì lên QC",
     tom["tu"] == "2024-10-01" and v.ket_qua.lo(0, 5)["dong"] and gia.nhat == [])
e = bat(v.mo_lai, ls[0]["duong"])
kiem("lượt màn ẩn KHÔNG mở lại được để xem từng nến",
     isinstance(e, game.LoiGame) and "màn ẩn" in str(e))
kiem("đường lạ → LoiGame", isinstance(bat(v.mo_lai, os.path.join(TD, "x.jsonl")), game.LoiGame))

# ================= 6. sáng tạo =================
print("\n▸ Sáng tạo — mọi symbol, mọi khoảng ngày, không chấm")
for sai_vao, chu in ((({"symbol": "xa", "tu": "2024-01-01", "den": "2024-02-01"}), "Symbol"),
                     (({"symbol": "XAUUSD", "tu": "2024-13-01", "den": "2024-02-01"}), "YYYY"),
                     (({"symbol": "XAUUSD", "tu": "2024-03-01", "den": "2024-02-01"}), "SAU"),
                     (({"symbol": "XAUUSD", "tu": "2024-01-01", "den": "2024-02-01",
                        "von": -5}), "lớn hơn 0")):
    e = bat(v.bat_dau, DOC, "tu_do", tu_do=sai_vao)
    kiem(f"đầu vào sai ({chu}) → báo ngay", isinstance(e, game.LoiGame) and chu in str(e))
tt = chay(v, DOC, "tu_do", tu_do={"symbol": "xagusd", "tu": "2023-05-01", "den": "2023-06-30",
                                  "von": 2500})
xt = tt["xong"] or {}
up = gia.files[gia.projects[0]["projectId"]]["main.py"]
kiem("chạy đúng symbol (viết hoa), ngày, vốn đã chọn; không sao, không màn",
     tt["loi"] is None and '"symbol": "XAGUSD"' in up and '"tu": "2023-05-01"' in up
     and '"von": 2500.0' in up and xt.get("sao") is None and xt.get("man") is None)

# ================= 4. lỗi thành lời =================
print("\n▸ Lỗi QC thành một câu trong trạng thái")
v2 = viec_moi(lambda: qc_gia.qc_cho(gia, tok="tok-sai-123"))
tt = chay(v2, DOC, "nhanh", "vang-2024")
kiem("khoá sai → trạng thái mang câu tiếng Việt, không treo, không lộ khoá",
     tt["dang_chay"] is False and tt["xong"] is None and "Khoá QuantConnect SAI" in tt["loi"]
     and "tok-sai-123" not in tt["loi"])
hong = copy.deepcopy(DOC)
for st in hong["entry"]["steps"]:
    if core.is_start_step(st):
        st["nhip"] = "D1"
gia.nhat.clear()
e = bat(v2.bat_dau, hong, "nhanh", "vang-2024")
kiem("sơ đồ không chạy được trên QC (khung D1) → báo NGAY lúc bấm, CHƯA gửi gì",
     isinstance(e, bc.LoiChay) and "D1" in str(e) and gia.nhat == []
     and not v2.trang_thai()["dang_chay"])


def no(*a):
    raise ValueError("hỏng giữa chừng")


tt = chay(viec_moi(no), DOC, "nhanh", "vang-2024")
kiem("lỗi lập trình bất ngờ → vẫn thành câu, việc nền không chết treo",
     tt["dang_chay"] is False and "Lỗi không lường trước" in (tt["loi"] or ""))

# ================= 7. vỏ API cho giao diện =================
print("\n▸ Vỏ API của cửa sổ Màn chơi (api.ApiQC)")
from cat_studio import api  # noqa: E402
from cat_studio import qc_api  # noqa: E402

for k in ("QC_USER_ID", "QC_API_TOKEN"):
    os.environ.pop(k, None)
cha = api.Api()
cha._doc_qc = core.normalize_process(DOC)
cha._viec_qc = viec_moi()
aq = api.ApiQC(cha)
ban = []
cha._ban = lambda ten, d: ban.append((ten, d))
QC_GOC = qc_api.QC
qc_api.QC = lambda uid, tok, **k: QC_GOC(uid, tok, goc=gia.goc, mo=qc_gia.mo,   # không ra mạng
                                         ngu=lambda s: None, timeout=300)

b = aq.qc_boot()
kiem("qc_boot: sơ đồ, màn (không ngày màn ẩn), độ gọn, trạng thái khoá",
     b["ok"] and b["value"]["doc"]["name"] == DOC["name"] and b["value"]["do_gon"]["tong"] == 22
     and "2025-01-01" not in json.dumps(b["value"]["man"]) and b["value"]["khoa"]["co"] is False)
kiem("qc_boot: chế độ Sáng tạo mặc định theo «Mã mặc định» ở Cài đặt, vốn 10.000",
     b["value"]["tu_do"]["symbol"] == cha._cai_dat["symbol"] and b["value"]["tu_do"]["von"] == 10_000)
kiem("Strategy Tester đã bỏ: không lớp ApiTester, không đường mở, không cài đặt «test»",
     not hasattr(api, "ApiTester") and "test" not in cha._cai_dat
     and not [x for x in ("mo_tester", "save_test_settings", "nguon_xoa") if hasattr(cha, x)]
     and "nguon" not in cha.bootstrap()["value"])
r = aq.qc_chay("nhanh", "vang-2024")
kiem("chưa có khoá → bấm ▶ là báo NGAY cách đặt khoá", not r["ok"]
     and "Chưa có khoá QuantConnect" in r["error"])
r = aq.qc_luu_khoa("abc", "x" * 20)
kiem("lưu khoá: User ID không phải số → lời nhắc, không lưu", not r["ok"] and "dãy số" in r["error"])
r = aq.qc_luu_khoa("424242", "ngan")
kiem("lưu khoá: token quá ngắn → lời nhắc, không nhắc lại token",
     not r["ok"] and "token" in r["error"] and "ngan" not in r["error"])
r = aq.qc_luu_khoa(" 424242 ", qc_gia.QCGia.TOK)
kiem("lưu khoá đúng → vào du_lieu/qc_khoa.json; câu trả KHÔNG mang token",
     r["ok"] and r["value"]["co"] and r["value"]["nguon"] == "file"
     and r["value"]["user_id"] == "424242" and qc_gia.QCGia.TOK not in json.dumps(r)
     and os.path.isfile(os.path.join(TD, "qc_khoa.json")))
kiem("kiểm khoá với QC: đúng → được", aq.qc_kiem_khoa()["ok"] is True)
os.environ["QC_USER_ID"], os.environ["QC_API_TOKEN"] = "424242", "tok-sai-0000000000000"
r = aq.qc_kiem_khoa()
kiem("… khoá sai (biến môi trường thắng file) → câu tiếng Việt, không lộ token",
     not r["ok"] and "SAI" in r["error"] and "tok-sai" not in r["error"]
     and aq.qc_khoa()["value"]["nguon"] == "bien_moi_truong")
for k in ("QC_USER_ID", "QC_API_TOKEN"):
    os.environ.pop(k, None)
r = aq.qc_chay("nop", "vang-2024")
kiem("nộp qua API (cỗ máy đã ▶ đầy đủ ở phần trên) → được", r["ok"])
cha._viec_qc.cho(600)
r = aq.qc_trang_thai()
kiem("qc_trang_thai: xong, có sao, lần nộp 3", r["ok"] and r["value"]["xong"]["lan_nop"] == 3)
r = aq.qc_chay("nhanh", "vang-2024")
cha._viec_qc.cho(600)
kq = aq.qc_ket_qua()["value"]
nk_ = aq.qc_nhat_ky(0, 20, True)["value"]
lenh = aq.qc_lenh()["value"]
kiem("qc_ket_qua / qc_nhat_ky / qc_lenh: tóm tắt, dòng «vì sao», lệnh mang giờ",
     kq["tu"] == "2024-10-01" and nk_["dong"] and lenh and all("t_dat" in x for x in lenh))
kiem("qc_ket_qua mang ĐỦ thông tin lượt (kiểu chạy, phần chấm, link QC) — y bản lúc vừa xong",
     kq["loai"] == "nhanh" and kq["cham"]["mua_giu_pt"] is not None
     and kq["url"].startswith("https://www.quantconnect.com/project/")
     and {k: kq[k] for k in ("loai", "cham", "url")}
     == {k: aq.qc_trang_thai()["value"]["xong"][k] for k in ("loai", "cham", "url")})
r = aq.qc_soi_luot(nk_["dong"][0]["i"])
kiem("qc_soi_luot: bắn «soi_luot» sang cửa sổ vẽ, đúng dạng cửa sổ vẽ tô được",
     r["ok"] and ban and ban[-1][0] == "soi_luot" and {"tab", "duong", "cong", "nhan", "chu"}
     <= set(ban[-1][1]))
kiem("qc_soi_luot ngoài phạm vi → không bắn", aq.qc_soi_luot(10 ** 9)["value"]["da_ban"] is False)
kiem("qc_lich_su / qc_man trả danh sách", aq.qc_lich_su()["ok"] and aq.qc_man()["ok"])
mn = aq.qc_man()["value"][0]
kiem("qc_man mang «vé nộp» của cỗ máy đang mở — giao diện bật nút Nộp theo nó",
     mn["ve_nop"] is not None and mn["ve_nop"]["lai_pt"] == ve["lai_pt"])
cha._doc_qc = core.normalize_process(sua)
kiem("… mở cỗ máy khác (đã sửa) → chưa có vé", aq.qc_man()["value"][0]["ve_nop"] is None)
cha._doc_qc = core.normalize_process(DOC)
kiem("kết quả mang nhịp Entry/Manage và giờ lượt đầu/cuối (cho bảng Thống kê)",
     kq["nhip"] == {"entry": "M5", "manage": "M1"} and kq["t_dau"] and kq["t_cuoi"] >= kq["t_dau"])
hidden = [x for x in aq.qc_lich_su()["value"] if x["an"]][0]["duong"]
r = aq.qc_mo_lai(hidden)
kiem("qc_mo_lai lượt màn ẩn → câu từ chối", not r["ok"] and "màn ẩn" in r["error"])
import webbrowser  # noqa: E402
mo = []
webbrowser.open = lambda u: mo.append(u)
kiem("qc_mo_web: chỉ mở link quantconnect.com",
     not aq.qc_mo_web("https://evil.example/x")["ok"]
     and aq.qc_mo_web("https://www.quantconnect.com/project/1/b")["ok"] and len(mo) == 1)
r = aq.qc_xoa_khoa()
kiem("xoá khoá → hết khoá", r["ok"] and r["value"]["co"] is False
     and not os.path.exists(os.path.join(TD, "qc_khoa.json")))

gia.dong()
print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
