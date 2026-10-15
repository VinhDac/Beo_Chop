"""CỬA API CỦA TRÌNH VẼ 5 TRẠM — những gì giao diện gọi tới.  (D-10, phần 5, lát 5a)

Canh đúng chỗ cầu nối Python ↔ JS hay hỏng LẶNG:

  1. **Gửi qua được cầu** — mọi cửa trả về thứ `json.dumps` nổi. Một hàm dựng sơ đồ lọt
     vào danh mục mẫu là promise bên JS treo vĩnh viễn, không báo gì.
  2. **Tham số khai đúng** — pywebview dựng hàm JS bằng `getfullargspec`, nên một cửa
     khai thiếu tham số thì JS gửi đi mà Python không nhận, lỗi hiện ra ở tận đâu đâu.
  3. **Từ điển đủ cho trình vẽ** — năm trạm, khối Làm theo trạm, đại lượng theo trạm,
     mẫu dựng sẵn: giao diện không được viết cứng danh sách nào.
  4. **Soát lỗi tới từng trạm** — chấm đỏ của dải 5 trạm lấy từ đây.
  5. **Lưu rồi mở lại Y HỆT** — cùng vân tay. Và mở lầm file chiến lược cũ thì BÁO, chứ
     không ra một cỗ máy trắng rồi lưu đè mất chiến lược.
  6. **Không cửa nào ném** — gọi với rác vẫn ra `{ok: false, error: câu tiếng Việt}`.

Chạy:  python tests\\test_may_api.py
"""
import inspect
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import luu_tru  # noqa: E402

#: Kho cỗ máy đi vào thư mục TẠM — bài kiểm không được đẻ file vào `du_lieu/` của người
#: dùng, cũng không được thấy cỗ máy thật của họ. Phải đặt TRƯỚC khi dựng `Api()`: hàm
#: khởi tạo đọc cài đặt, tức là đã gọi `luu_tru.goc()`.
_TMP = tempfile.TemporaryDirectory()
luu_tru._GOC_MA_NGUON = _TMP.name

from cat_studio import api  # noqa: E402
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


a = api.Api()


def gt(r):
    """Giá trị của một cửa, và nổ ngay nếu cửa báo lỗi — bài kiểm không đoán."""
    assert r.get("ok"), r
    return r["value"]


# ===========================================================================
print("\n▸ 1. Từ điển 5 trạm (may_boot)")
# ===========================================================================
b = gt(a.may_boot())
kiem("gửi qua cầu nối được: cả từ điển là JSON", isinstance(json.dumps(b), str),
     f"({len(json.dumps(b))} ký tự)")
kiem("năm trạm, đúng thứ tự QC",
     [t["key"] for t in b["tram"]] == T.TRAM_KEYS == b["tram_keys"],
     f"({' → '.join(t['so'] for t in b['tram'])})")
kiem("mỗi trạm mang câu hỏi, chạy cho ai, ra cái gì",
     all(t.get("hoi") and t.get("cho_ai") and t.get("ra") and t.get("qc")
         for t in b["tram"]))
kiem("mọi khối Làm nằm trong đúng MỘT trạm",
     sorted(k for ds in b["khoi_lam_cua_tram"].values() for k in ds)
     == sorted(T.KHOI_LAM) and all(
         b["khoi_lam"][k]["tram"] == tr
         for tr, ds in b["khoi_lam_cua_tram"].items() for k in ds),
     f"({len(T.KHOI_LAM)} khối)")
kiem("đại lượng theo trạm: «tín hiệu» chỉ ở ③, «khớp lệnh» chỉ ở ⑤",
     "huong_tin_hieu" in b["toan_hang_cua_tram"][T.CHIA_VON]
     and "huong_tin_hieu" not in b["toan_hang_cua_tram"][T.TIN_HIEU]
     and "lech_muc_tieu_pt" in b["toan_hang_cua_tram"][T.KHOP_LENH]
     and "lech_muc_tieu_pt" not in b["toan_hang_cua_tram"][T.RUI_RO])
kiem("mẫu dựng sẵn: đủ 22, chỉ phần nhãn — hàm dựng Ở LẠI Python",
     sum(len(v) for v in b["mau"].values()) == 22
     and all(set(m) == {"key", "ten", "qc", "mo_ta"}
             for ds in b["mau"].values() for m in ds),
     f"({ {k: len(v) for k, v in b['mau'].items()} })".replace("'", ""))
kiem("có bộ mẫu của cỗ máy mẫu, đủ năm trạm",
     set(b["may_mau"]) == set(T.TRAM_KEYS))

# ===========================================================================
print("\n▸ 2. Cửa JS khai đúng tham số (bẫy `getfullargspec`)")
# ===========================================================================
CAN = {
    "may_boot": [], "may_moi": ["ten"], "may_mo_mau": ["chon", "ma"],
    "may_kem_the": ["doc"], "may_soat": ["doc"],
    "may_khoi_moi": ["tram", "kind", "loai", "tham_so"],
    "may_luu_khoi": ["tram", "draft", "tham_so"],
    "may_ap_mau": ["doc", "tram", "mau_key", "ma"],
    "may_ds": [], "may_luu": ["doc"], "may_mo": ["ten"], "may_xoa": ["ten"],
    "may_mo_file": [], "may_luu_file": ["doc"],
}
lech = {ten: inspect.getfullargspec(getattr(a, ten)).args[1:]
        for ten, args in CAN.items()
        if inspect.getfullargspec(getattr(api.Api, ten)).args[1:] != args}
kiem("14 cửa may_* khai đúng tham số thật", not lech, f"({lech})" if lech else "")
cua = [n for n in dir(api.Api) if n.startswith("may_")]
kiem("không cửa may_* nào bị bỏ ngoài bài kiểm", sorted(cua) == sorted(CAN),
     f"({len(cua)} cửa)")

# ===========================================================================
print("\n▸ 3. Cỗ máy mới và cỗ máy mẫu")
# ===========================================================================
m0 = gt(a.may_moi())
kiem("cỗ máy mới: năm trạm, mỗi trạm đúng một thẻ Bắt đầu",
     M.la_may(m0) and all(len(m0["tram"][k]["cards"]) == 1
                          and m0["tram"][k]["cards"][0]["kind"] == "start"
                          for k in T.TRAM_KEYS))
kiem("thẻ Bắt đầu đã mang chữ do Python dựng (lịch + cho ai)",
     all(m0["tram"][k]["cards"][0]["lines"] for k in T.TRAM_KEYS),
     f"(① {m0['tram'][T.CHON_MA]['cards'][0]['lines'][0]['text']})")
s0 = a.may_soat(m0)
kiem("cỗ máy trắng: ①②③⑤ báo lỗi «chưa ra được kết quả», ④ thì KHÔNG",
     all(s0["tram"][k]["so_loi"] >= 1 for k in (T.CHON_MA, T.TIN_HIEU, T.CHIA_VON,
                                                T.KHOP_LENH))
     and s0["tram"][T.RUI_RO]["so_loi"] == 0,
     f"({s0['so_loi']} lỗi)")
kiem("mỗi vấn đề nói rõ trạm nào, khối nào",
     all(p["tram"] in T.TRAM_KEYS and "step" in p for p in s0["value"]))

mm = gt(a.may_mo_mau())
smm = a.may_soat(mm)
kiem("cỗ máy mẫu: SẠCH — không lỗi, không cảnh báo",
     smm["so_loi"] == 0 and smm["so_canh_bao"] == 0,
     f"({smm['so_loi']} lỗi · {smm['so_canh_bao']} cảnh báo)")
kiem("… và mọi trạm đều có số thứ tự cho từng khối",
     all(len(smm["tram"][k]["order"]) == len(mm["tram"][k]["steps"])
         for k in T.TRAM_KEYS),
     f"(② {sorted(smm['tram'][T.TIN_HIEU]['order'].values())})")
kiem("vân tay đi kèm mỗi lần soát", len(smm["van_tay"]) == 12)
kiem("gửi qua cầu nối được: cả cỗ máy kèm thẻ là JSON",
     isinstance(json.dumps(mm), str))

# ===========================================================================
print("\n▸ 4. Khối mới · soát một khối trong hộp thoại")
# ===========================================================================
r = a.may_khoi_moi(T.TIN_HIEU, "action", None)
kiem("khối Hỏi mới: SẠCH ngay, không phải khối đỏ chờ gõ",
     r["ok"] and not r["loi"] and r["value"]["card"]["la_cong"],
     f"({r['value']['card']['lines'][0]['text']})")
r = a.may_khoi_moi(T.TIN_HIEU, "action", "bao")
st = r["value"]["step"]
kiem("khối Làm mới mang MẶC ĐỊNH của từ điển, không phải 0",
     st["huong"] == "len" and st["thoi_han"] == 24 and not r["loi"],
     f"({r['value']['card']['lines'][0]['text']})")
r = a.may_khoi_moi(T.CHON_MA, "action", "bao")
kiem("khối Làm sai trạm bị chặn NGAY trong hộp thoại",
     r["ok"] and len(r["loi"]) == 1 and "trạm ② Tín hiệu" in r["loi"][0]["message"])
r = a.may_luu_khoi(T.TIN_HIEU, M.khoi_hoi(
    [{"trai": {"ten": "rsi"}, "phep": ">", "phai": {"ten": "gia_dong"}}]))
kiem("hai vế khác đơn vị → hộp thoại biết ngay, nói rõ hai đại lượng",
     len(r["loi"]) == 1 and "khác" in r["loi"][0]["message"])
r = a.may_luu_khoi(T.RUI_RO, M.khoi_lam("giam_ve", pt="nguong_x"))
kiem("ô số dùng tên tham số không có trong bảng → báo tên đó",
     len(r["loi"]) == 1 and "nguong_x" in r["loi"][0]["message"])
r = a.may_luu_khoi(T.RUI_RO, M.khoi_lam("giam_ve", pt="nguong_x"),
                   tham_so=[{"ten": "nguong_x", "nhan": "", "gia_tri": 7}])
kiem("… có tham số ấy thì sạch, và chữ trên khối HIỆN cả tên lẫn số",
     not r["loi"] and "nguong_x = 7" in r["value"]["card"]["lines"][0]["text"],
     f"({r['value']['card']['lines'][0]['text']})")
r = a.may_khoi_moi(T.TIN_HIEU, "start")
kiem("khối Bắt đầu mới: lịch và khung mặc định của chính trạm",
     r["value"]["step"]["lich"] == "moi_nen" and r["value"]["step"]["khung"] == "H1")

# ===========================================================================
print("\n▸ 5. Lắp mẫu vào một trạm")
# ===========================================================================
m = gt(a.may_moi("Thử lắp mẫu"))
for k, mau_key in gt(a.may_boot())["may_mau"].items():
    m = gt(a.may_ap_mau(m, k, mau_key))
s = a.may_soat(m)
kiem("cỗ máy trắng + lắp năm mẫu → SẠCH",
     s["so_loi"] == 0 and s["so_canh_bao"] == 0,
     f"({s['so_loi']} lỗi · {s['so_canh_bao']} cảnh báo)")
kiem("tên cỗ máy không bị mẫu ghi đè", m["name"] == "Thử lắp mẫu")
ts = {t["ten"]: t["gia_tri"] for t in m["tham_so"]}
kiem("mẫu mang theo tham số có tên", len(ts) >= 2, f"({sorted(ts)})")
ten_ts = sorted(ts)[0]
m2 = json.loads(json.dumps(m))
for t in m2["tham_so"]:
    if t["ten"] == ten_ts:
        t["gia_tri"] = 999.0
m2 = gt(a.may_ap_mau(m2, T.TIN_HIEU, gt(a.may_boot())["may_mau"][T.TIN_HIEU]))
kiem("lắp lại mẫu KHÔNG đặt lại núm đã vặn",
     {t["ten"]: t["gia_tri"] for t in m2["tham_so"]}[ten_ts] == 999.0,
     f"({ten_ts} = 999)")
def chi_tram(doc, k):
    """Một trạm đã chuẩn hoá, thành chữ để so. KHÔNG dùng `van_tay` cho việc này: vân tay
    chạy trên CẢ cỗ máy, mà cỗ máy thiếu trạm thì chuẩn hoá tự dựng khối Bắt đầu với id
    MỚI mỗi lần — so hai lần là lệch, trong khi chẳng có gì đổi."""
    return json.dumps(M.chuan_hoa(doc)["tram"][k], sort_keys=True, ensure_ascii=False)


kiem("lắp mẫu chỉ đổi TRẠM đó, bốn trạm kia y nguyên",
     all(chi_tram(m, k) == chi_tram(m2, k) for k in T.TRAM_KEYS if k != T.TIN_HIEU)
     and chi_tram(m, T.TIN_HIEU) != chi_tram(m2, T.TIN_HIEU))

# ===========================================================================
print("\n▸ 6. Lưu và mở lại")
# ===========================================================================
luu = gt(a.may_luu(m))
kiem("lưu xong có đường dẫn thật trong kho cỗ máy",
     os.path.isfile(luu["path"])
     and os.path.dirname(luu["path"]) == luu_tru.thu_muc_co_may())
kiem("tên cỗ máy thấy trong danh sách", luu["name"] in gt(a.may_ds()),
     f"({gt(a.may_ds())})")
lai = gt(a.may_mo(luu["name"]))
kiem("mở lại Y HỆT — cùng vân tay",
     M.van_tay(lai) == M.van_tay(m) == luu["van_tay"], f"({luu['van_tay']})")
kiem("… và y hệt tới từng khối, từng dây, từng ô Gom",
     json.dumps(M.chuan_hoa(lai), sort_keys=True, ensure_ascii=False)
     == json.dumps(M.chuan_hoa(m), sort_keys=True, ensure_ascii=False))
r = a.may_mo("khong-he-co")
kiem("mở cỗ máy không có → ok:false, không traceback lọt ra JS",
     r["ok"] is False and r.get("error"))

# Chiến lược cũ (sơ đồ Entry/Manage) KHÔNG được mở ra thành cỗ máy trắng.
cu = {"name": "Chiến lược cũ", "entry": {"steps": []}, "manage": {"steps": []}}
with open(luu_tru.duong_dan_co_may("ke_lam"), "w", encoding="utf-8") as f:
    json.dump(cu, f, ensure_ascii=False)
r = a.may_mo("ke_lam")
kiem("mở lầm chiến lược cũ → BÁO, không ra cỗ máy trắng",
     r["ok"] is False and "không phải cỗ máy 5 trạm" in r["error"])
kiem("xoá được", gt(a.may_xoa("ke_lam")) is True
     and "ke_lam" not in gt(a.may_ds()))

# Tên thiết bị của Windows: `CON.json` là hố đen ở bất kỳ thư mục nào.
m3 = json.loads(json.dumps(m))
m3["name"] = "CON"
l3 = gt(a.may_luu(m3))
kiem("tên «CON» vẫn lưu được và đọc lại được (bẫy tên thiết bị Windows)",
     os.path.basename(l3["path"]) == "_CON.json"
     and M.van_tay(gt(a.may_mo("CON"))) == M.van_tay(m3))

# ===========================================================================
print("\n▸ 7. Gọi với rác — không cửa nào ném")
# ===========================================================================
RAC = [
    ("may_kem_the", (None,)),
    ("may_kem_the", ({"dang": "may5", "phien_ban": 99},)),
    ("may_soat", ("khong phai dict",)),
    ("may_soat", ({"dang": "so_do_cu"},)),
    ("may_khoi_moi", ("tram-la", "action", "khoi-la")),
    ("may_luu_khoi", (T.TIN_HIEU, None)),
    ("may_ap_mau", (None, T.TIN_HIEU, "khong-co-mau")),
    ("may_ap_mau", (None, "tram-la", "giao_cat_ema")),
    ("may_luu", (None,)),
    ("may_mo", (None,)),
    ("may_xoa", ("../../hack",)),
]
nem, xau = [], []
for ten, args in RAC:
    try:
        r = getattr(a, ten)(*args)
    except Exception as e:                       # cửa NÉM = promise JS treo
        nem.append(f"{ten}{args}: {e}")
        continue
    if not isinstance(r, dict) or "ok" not in r or (not r["ok"] and not r.get("error")):
        xau.append(f"{ten}{args}: {r}")
    try:
        json.dumps(r)
    except Exception as e:
        xau.append(f"{ten}{args}: không JSON hoá nổi ({e})")
kiem("11 lời gọi rác: không cửa nào ném", not nem, f"({nem})" if nem else "")
kiem("… và cái trả về luôn đúng hình dạng, luôn JSON hoá được", not xau,
     f"({xau})" if xau else "")
r = a.may_soat({"dang": "so_do_cu"})
kiem("tài liệu dạng khác: nói thẳng không phải cỗ máy 5 trạm",
     r["ok"] and r["so_loi"] == 1 and "không phải cỗ máy 5 trạm" in r["value"][0]["message"])
r = a.may_kem_the({"dang": "may5", "phien_ban": 99})
kiem("cỗ máy của bản MỚI HƠN: từ chối mở, nói cách sửa",
     r["ok"] is False and "Cập nhật app" in r["error"])
r = a.may_ap_mau(None, T.TIN_HIEU, "khong-co-mau")
kiem("mẫu không có: câu tiếng Việt gọi tên trạm",
     r["ok"] is False and "Tín hiệu" in r["error"])

# ===========================================================================
print("\n▸ 8. Khối Bắt đầu và bảng Gom (hộp thoại lát 5d)")
# ===========================================================================
r = a.may_khoi_moi(T.CHON_MA, "start")
st = r["value"]["step"]
kiem("khối Bắt đầu của ① mang phạm vi «mọi mã của màn»",
     st["lich"] == "bat_dau" and st["pham_vi"] == {"loai": "tat_ca"} and not r["loi"])
# Lịch KHÔNG có ở trạm này (① không chạy theo nến) phải rơi về lịch mặc định của trạm,
# chứ không được giữ nguyên rồi chạy sai.
r = a.may_luu_khoi(T.CHON_MA, {"kind": "start", "lich": "moi_nen", "khung": "M5"})
kiem("lịch lạ với trạm → rơi về lịch mặc định của chính trạm đó",
     r["value"]["step"]["lich"] == "bat_dau" and "khung" not in r["value"]["step"])
r = a.may_luu_khoi(T.CHON_MA, {"kind": "start", "lich": "bat_dau", "pham_vi": {
    "loai": "danh_sach", "ma": ["eurusd", " xauusd ", "EURUSD", ""]}})
kiem("danh sách mã: viết HOA, bỏ trùng, bỏ ô rỗng — việc của Python, không của hộp thoại",
     r["value"]["step"]["pham_vi"] == {"loai": "danh_sach", "ma": ["EURUSD", "XAUUSD"]},
     f"({r['value']['step']['pham_vi']['ma']})")
kiem("… và chữ trên khối nói đúng danh sách ấy",
     "EURUSD, XAUUSD" in " ".join(d["text"] for d in r["value"]["card"]["lines"]))
r = a.may_luu_khoi(T.TIN_HIEU, {"kind": "start", "lich": "moi_nen", "khung": "H4"})
kiem("② chạy mỗi nến thì khung đi kèm, và hiện ra trên khối",
     r["value"]["step"]["khung"] == "H4"
     and "H4" in r["value"]["card"]["lines"][0]["text"])

# Gom: đổi một ô Gom làm nổi lên một câu gắn với KHỐI — hộp thoại Gom dựa vào đúng chỗ đó.
mg = json.loads(json.dumps(gt(a.may_mo_mau())))
mg["tram"][T.CHON_MA]["gom"] = {"top_n": 5, "xep": "cao"}
s = a.may_soat(mg)
canh = [p for p in s["value"] if p["tram"] == T.CHON_MA]
kiem("giữ N mã mà khối «Cho vào rổ» không có điểm → cảnh báo, gắn vào CHÍNH khối đó",
     len(canh) == 1 and canh[0]["severity"] == "warning" and canh[0]["step"]
     and "điểm cao nhất" in canh[0]["message"])
mg["tram"][T.CHON_MA]["gom"] = {"top_n": 0, "xep": "cao"}
s = a.may_soat(mg)
kiem("ô Gom ngoài khoảng → LỖI, nói rõ ô nào và khoảng nào",
     any(p["severity"] == "error" and "giữ tối đa" in p["message"]
         for p in s["value"]))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
