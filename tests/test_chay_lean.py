"""BỘ CHẠY LEAN — bấm một nút là có kết quả backtest.

⚠ BÀI NÀY KHÔNG CHẠY LEAN THẬT. Nó canh mấy LUẬT quanh việc chạy — thứ hỏng lặng và
hỏng ở máy người khác, chứ không phải bản thân phép backtest (đã chạy tay nhiều lần,
xem `tai_lieu/core.md` §31).

Ba cái bẫy đã cắn thật, cả ba đều im:

  1. **Đọc mã thoát thay vì đọc file.** pythonnet ném *"GIL must always be released"*
     lúc tắt, SAU khi kết quả ghi xong xuôi. Tin mã thoát là báo hỏng một lượt chạy
     hoàn hảo.
  2. **Để sót biến môi trường của venv.** App chạy trong `.venv` (không có pandas);
     LEAN nạp Python qua `PYTHONNET_PYDLL`, mà `VIRTUAL_ENV`/`PYTHONHOME` còn sót thì
     nó trỏ vào venv rồi chết vì thiếu pandas — thông báo chẳng nhắc gì tới venv.
  3. **Bảng mã số đoán theo trí nhớ.** `OrderStatus` của LEAN **không có số 4**
     (Canceled nhảy thẳng lên 5). Đoán thì mọi lệnh huỷ hiện sai tên.

Và một cái thứ tư thuộc về sự thật: **để trống ô Mốc so sánh KHÔNG phải là không có
mốc** — LEAN lặng lẽ lấy SPY, tức cỗ máy vàng bị đem so với cổ phiếu Mỹ.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, chay_lean, core  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# ================= 1. Không đoán chỗ đặt LEAN =================
print("\n▸ Chưa trỏ LEAN thì nói rõ, KHÔNG đoán hộ")
sb = chay_lean.san_sang()
kiem("có trả lời dứt khoát", isinstance(sb.get("ok"), bool))
if not sb["ok"]:
    kiem("và kèm lý do đọc được", bool(sb["loi"]), f"— {sb['loi'][:60]}")
kiem("tìm được python3xx.dll cho LEAN", bool(sb["dll"]), f"— {sb['dll'][-24:]}")

print("\n▸ Thư mục sai thì nói sai ở đâu")
cu = chay_lean.KHOA_LEAN
from cat_studio import luu_tru  # noqa: E402
goc_cu = luu_tru.doc_cai_dat().get(cu, "")
try:
    s = luu_tru.doc_cai_dat()
    s[cu] = os.path.join(os.path.dirname(__file__), "khong_co_that")
    luu_tru.ghi_cai_dat(s)
    r = chay_lean.san_sang()
    kiem("thư mục không có → báo đúng chỗ ấy",
         not r["ok"] and "Không có thư mục" in r["loi"], f"— {r['loi'][:48]}")
    s[cu] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    luu_tru.ghi_cai_dat(s)
    r = chay_lean.san_sang()
    kiem("có thư mục mà không phải LEAN → báo thiếu Launcher",
         not r["ok"] and "Launcher" in r["loi"], f"— {r['loi'][:48]}")
finally:
    s = luu_tru.doc_cai_dat()
    s[cu] = goc_cu
    luu_tru.ghi_cai_dat(s)

# ================= 2. ⚠ Môi trường con phải SẠCH dấu vết venv =================
print("\n▸ ⚠ Tiến trình LEAN KHÔNG được mang theo biến môi trường của venv")
e, dll = chay_lean._moi_truong()
for k in ("VIRTUAL_ENV", "PYTHONHOME", "PYTHONPATH"):
    kiem(f"`{k}` đã gột sạch", k not in e)
kiem("có `PYTHONNET_PYDLL`", "PYTHONNET_PYDLL" in e)
kiem("và nó trỏ tới một file CÓ THẬT",
     os.path.isfile(e.get("PYTHONNET_PYDLL", "")), f"— {e.get('PYTHONNET_PYDLL')}")
v = os.environ.get("VIRTUAL_ENV")
if v:
    kiem("PATH không còn thư mục venv",
         not any(x.lower().startswith(v.lower())
                 for x in e.get("PATH", "").split(os.pathsep) if x))
else:
    print("  · không chạy trong venv — bỏ qua phép kiểm PATH")

# ================= 3. config.json của LEAN gột được =================
print("\n▸ `config.json` của LEAN có chú thích `//` và dấu phẩy thừa")
import json  # noqa: E402
tho = '''{
  // một chú thích
  "a": 1,          // chú thích cuối dòng
  "b": "https://co-hai-gach-trong-chuoi",
  "c": [1, 2,],
}'''
d = json.loads(chay_lean._got_json(tho))
kiem("gột xong vẫn đọc được", d["a"] == 1)
kiem("KHÔNG cắt nhầm `//` nằm TRONG chuỗi",
     d["b"] == "https://co-hai-gach-trong-chuoi", f"— {d['b']}")
kiem("bỏ được dấu phẩy thừa", d["c"] == [1, 2])

# ================= 4. ⚠ Bảng mã số đọc từ LEAN, không đoán =================
print("\n▸ ⚠ `OrderStatus` của LEAN KHÔNG có số 4")
kiem("không khai số 4", 4 not in chay_lean.TRANG_THAI_LENH)
kiem("5 là «Đã huỷ»", chay_lean.TRANG_THAI_LENH[5] == "Đã huỷ")
kiem("7 là KHÔNG HỢP LỆ", "KHÔNG HỢP LỆ" in chay_lean.TRANG_THAI_LENH[7])
kiem("đủ 12 loại lệnh", len(chay_lean.LOAI_LENH) == 12)
kiem("số 5 là «khớp lúc đóng» — đúng thứ nến NGÀY sinh ra",
     chay_lean.LOAI_LENH[5] == "Khớp lúc đóng")

print("\n▸ Lệnh bị từ chối phải lộ ra, không lẫn vào đám đã khớp")
l = chay_lean._lenh_gon({"id": 9, "symbol": {"value": "XAUUSD"}, "type": 5,
                         "quantity": 85.0, "price": 1166.9, "status": 7,
                         "tag": "[1A.1] RSI(14) < 30",
                         "time": "2015-03-08T23:00:00Z"})
kiem("`hop_le` là False", l["hop_le"] is False)
kiem("mã đọc ra chuỗi, không phải object", l["ma"] == "XAUUSD")
kiem("thời gian cắt gọn", l["luc"] == "2015-03-08 23:00:00", f"— {l['luc']!r}")
kiem("tag mang số khối và điều kiện", l["tag"].startswith("[1A.1]"))
kiem("lệnh đã khớp thì hợp lệ",
     chay_lean._lenh_gon({"status": 3, "symbol": "X"})["hop_le"] is True)

# ================= 5. ⚠ Mốc so sánh để trống KHÔNG phải là không có mốc =======
print("\n▸ ⚠ Để trống Mốc so sánh thì LEAN lặng lẽ lấy SPY")
o = next(x for x in bat_dau.O_BAT_DAU if x["ten"] == "moc_so_sanh")
kiem("câu gợi ý nói thẳng ra SPY", "SPY" in o["goi_y"], f"— {o['goi_y'][:56]}")
kiem("và ô ấy không bắt buộc", not o["bat_buoc"])

# ================= 6. Đọc được mọi kiểu LEAN ghi điểm =======================
print("\n▸ LEAN ghi điểm biểu đồ bằng hai kiểu khác nhau")
kiem("đọc kiểu điểm thường", chay_lean._diem({"x": 10, "y": 1.5}) == [10, 1.5])
kiem("đọc kiểu NẾN giữ đủ 5 số",
     chay_lean._diem([20, 9, 11, 8, 10]) == [20, 9, 11, 8, 10])
kiem("điểm thiếu giá trị → bỏ", chay_lean._diem({"x": 30, "y": None}) is None)
kiem("rác → bỏ", chay_lean._diem("rác") is None)

print("\n▸ Bảng kiểu đường đọc từ `BaseSeries.cs`, không đoán")
kiem("2 là NẾN", chay_lean.KIEU_DUONG[2] == "nen")
kiem("3 là CỘT", chay_lean.KIEU_DUONG[3] == "cot")
kiem("7 là TREEMAP", chay_lean.KIEU_DUONG[7] == "o_vuong")

print("\n▸ ⚠ Bớt điểm phải GỘP, không được nhảy cách")
# Nhảy cách (lấy 1 trong mỗi N) làm MẤT ĐỈNH VÀ ĐÁY: một cú sụt gọn trong vài nến
# biến mất khỏi biểu đồ mà người xem không hề biết.
n = chay_lean.TRAN_DIEM * 3
duong = [[i, 1.0] for i in range(n)]
duong[7] = [7, 999.0]                       # một đỉnh nhọn, lọt giữa một rổ
duong[8] = [8, -999.0]                      # và một đáy nhọn ngay cạnh
ra = chay_lean._thua(duong, False)
kiem("bớt được xuống dưới trần", len(ra) <= chay_lean.TRAN_DIEM * 2, f"— {len(ra)}")
kiem("ĐỈNH nhọn vẫn còn", any(p[1] == 999.0 for p in ra))
kiem("ĐÁY nhọn vẫn còn", any(p[1] == -999.0 for p in ra))
kiem("và thứ tự thời gian không loạn",
     all(ra[i][0] <= ra[i + 1][0] for i in range(len(ra) - 1)))
nen = [[i, 1.0, 1.0, 1.0, 1.0] for i in range(n)]
nen[7] = [7, 1.0, 50.0, 0.5, 1.0]
ra_n = chay_lean._thua(nen, True)
kiem("nến gộp giữ CAO NHẤT của rổ", any(p[2] == 50.0 for p in ra_n))
kiem("nến gộp giữ THẤP NHẤT của rổ", any(p[3] == 0.5 for p in ra_n))
kiem("ít điểm thì để nguyên", chay_lean._thua([[1, 2], [3, 4]], False) == [[1, 2], [3, 4]])

print("\n▸ Gửi TOÀN BỘ biểu đồ LEAN dựng, không cắt bớt bảng nào")
_cap = {"series": {"C": {"seriesType": 0, "unit": "$",
                         "values": [{"x": 1, "y": 2}]}}}
_eq = {"series": {
    "Equity": {"seriesType": 2, "unit": "$", "values": [[1, 1, 2, 0, 1]]},
    "Return": {"seriesType": 3, "unit": "%", "values": [{"x": 1, "y": 0.5}]}}}
bd = chay_lean._bieu_do({"charts": {"Capacity": _cap, "Strategy Equity": _eq}})
kiem("đủ hai bảng", len(bd) == 2)
kiem("ĐƯỜNG VỐN xếp TRƯỚC", bd[0]["ten"] == "Strategy Equity",
     "— người đọc luôn muốn thấy nó đầu tiên")
kiem("và nó bày sẵn lúc mở", bd[0]["hien"] is True)
kiem("Capacity thì không bày sẵn", bd[1]["hien"] is False,
     "— tám bảng cùng lúc thì không ai nhìn cái nào")
kiem("nhận đúng kiểu từng đường",
     [x["kieu"] for x in bd[0]["duong"]] == ["nen", "cot"])
kiem("đường rỗng thì không gửi", not chay_lean._bieu_do(
    {"charts": {"X": {"series": {"S": {"seriesType": 0, "values": []}}}}}))

# ================= 7. Gói kết quả: đúng phần màn Kết quả cần =================
print("\n▸ Gói kết quả gửi đi đúng phần cần, không gửi cả file")
g = chay_lean._gon({"statistics": {"Net Profit": "16%"},
                    "orders": {"1": {"status": 3, "symbol": "X", "type": 0}},
                    "totalPerformance": {"closedTrades": [
                        {"symbols": [{"value": "XAUUSD"}], "profitLoss": 5.0,
                         "isWin": True}]},
                    "charts": {}}, "nhật ký")
kiem("có đủ khoá màn Kết quả cần",
     {"o_so", "bieu_do", "thong_ke", "cuon", "may_chu", "lenh", "giao_dich",
      "nhat_ky"} <= set(g), f"— thiếu {{'o_so','bieu_do','thong_ke','cuon',"
                            f"'may_chu','lenh','giao_dich','nhat_ky'}} - {set(g)}")
kiem("lệnh đã dịch sẵn chữ", g["lenh"][0]["trang_thai"] == "Đã khớp")
kiem("giao dịch đã dịch sẵn", g["giao_dich"][0]["ma"] == "XAUUSD")
kiem("KHÔNG gửi cả 8 biểu đồ của LEAN", "charts" not in g,
     "— giao diện chỉ vẽ ba đường")

# ================= 8. Chưa trỏ LEAN thì chay() dừng NGAY =================
print("\n▸ Chưa trỏ LEAN thì `chay()` dừng ngay, không đẻ file rác")
s = luu_tru.doc_cai_dat()
s[cu] = ""
luu_tru.ghi_cai_dat(s)
try:
    r = chay_lean.chay("x = 1\n", "KhongBaoGioChay")
    kiem("→ ok False", not r["ok"])
    kiem("và nói rõ thiếu gì", "LEAN" in r["loi"])
    kiem("không ghi file nào",
         not os.path.isdir(os.path.join(luu_tru.thu_muc_ket_qua(),
                                        "KhongBaoGioChay")))
finally:
    s = luu_tru.doc_cai_dat()
    s[cu] = goc_cu
    luu_tru.ghi_cai_dat(s)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
