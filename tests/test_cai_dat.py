"""CÀI ĐẶT APP — cái núm phải NỐI VÀO ĐÂU ĐÓ.

Một hộp Cài đặt dễ thành hộp trang trí: bày ra mấy cái núm, người dùng vặn, lưu
xuống file, rồi chẳng ai đọc. Lúc ấy nó tệ hơn là không có hộp — người ta vặn xong
ngồi đợi một thứ không bao giờ đổi, và đi tìm lỗi ở chỗ khác.

Hai chuyện đã xảy ra THẬT, cả hai đều lặng:
  · `cai_dat.json` mang sẵn `symbol`, `accent`, `ui.panel_cao`, `ui.panel_gap` —
    bốn khoá không một dòng nào trong `cat_studio/` lẫn `webui/src/` đọc tới;
  · lúc dựng hộp, `han_gio_phut` ghi xuống file rồi BIẾN MẤT ở lần đọc kế tiếp, vì
    `luu_tru.doc_cai_dat` chỉ giữ khoá có trong `CAI_DAT_MAC_DINH` mà bảng ấy được
    gõ tay lần thứ hai. Không lỗi, không cảnh báo, cái núm cứ nhảy về mặc định.

Chạy:  python tests\\test_cai_dat.py
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import cai_dat, chay_lean, luu_tru  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


print("\n▸ ⭐ Mỗi cài đặt phải SỐNG SÓT qua một vòng ghi–đọc")
# Nếu `CAI_DAT_MAC_DINH` thiếu một khoá thì khoá ấy bị `doc_cai_dat` lọc mất, và cái
# núm tương ứng là núm giả. Đây là phép kiểm duy nhất bắt được chuyện đó.
thieu = [t for t in cai_dat.BANG_O if t not in luu_tru.CAI_DAT_MAC_DINH]
kiem("khoá nào cũng có mặt trong bảng mặc định", not thieu, f"— thiếu {thieu}")
kiem("bảng mặc định DỰNG TỪ `cai_dat`, không gõ tay lần hai",
     all(luu_tru.CAI_DAT_MAC_DINH[t] == o["mac_dinh"]
         for t, o in cai_dat.BANG_O.items()))

print("\n▸ Giới hạn KHO: cái núm phải thật sự xoá lượt cũ")
# Cùng họ với núm Hạn giờ dưới đây. Một con số "giữ 20 lượt" mà không ai dọn thì
# nó chỉ là chữ trang trí — và cái hỏng ấy chỉ lộ ra sau vài ngày, khi đĩa đầy.
for _hang, _mod, _ten in (("KHOA_KHO_BACKTEST", "chay_lean.py", "lượt backtest"),
                          ("KHOA_KHO_TOI_UU", "chay_toi_uu.py", "mẻ Optimize")):
    _k = getattr(cai_dat, _hang)
    kiem(f"có núm giữ mấy {_ten}", _k in cai_dat.BANG_O)
    _ng = io.open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "cat_studio", _mod), encoding="utf-8").read()
    kiem(f"`{_mod}` có hàm dọn kho", "def don_kho(" in _ng)
    # Tìm tên HẰNG, không tìm chuỗi khoá: gõ lại `"kho_backtest"` ra chữ là mở đường
    # cho một ngày đổi tên khoá ở `cai_dat` mà chỗ này vẫn đọc tên cũ, lặng lẽ.
    kiem(f"`{_mod}` đọc qua hằng `cai_dat.{_hang}`, không gõ lại chuỗi khoá",
         f"cai_dat.{_hang}" in _ng and f'"{_k}"' not in _ng)
    kiem(f"`{_mod}` hỏi `gioi_han_kho`, không gõ số cứng",
         "gioi_han_kho(" in _ng)
    kiem(f"`{_mod}` gọi dọn SAU KHI chạy xong", "    don_kho()" in _ng,
         "— dọn lúc mở app thì lượt vừa thấy biến mất mà chẳng vì hành động nào")
kiem("mặc định giữ 20", cai_dat.BANG_O[cai_dat.KHOA_KHO_BACKTEST]["mac_dinh"] == 20
     and cai_dat.BANG_O[cai_dat.KHOA_KHO_TOI_UU]["mac_dinh"] == 20)
kiem("đặt 0 thì CHẶN còn 1, không xoá sạch",
     cai_dat.gioi_han_kho(cai_dat.KHOA_KHO_BACKTEST,
                          {cai_dat.KHOA_KHO_BACKTEST: 0}) == 1)

print("\n▸ Mấy khoá CHẾT đã bị bỏ")
for k in ("symbol", "accent", "ui"):
    kiem(f"`{k}` không còn trong bảng mặc định", k not in luu_tru.CAI_DAT_MAC_DINH,
         "— không một dòng nào trong app đọc tới")

print("\n▸ Hạn giờ: cái núm phải thật sự ăn vào bộ chạy")
cu = luu_tru.doc_cai_dat()
try:
    s = dict(cu)
    s[cai_dat.KHOA_HAN_GIO] = 45
    luu_tru.ghi_cai_dat(s)
    kiem("ghi 45 phút thì đọc lại vẫn là 45",
         luu_tru.doc_cai_dat().get(cai_dat.KHOA_HAN_GIO) == 45)
    kiem("và bộ chạy lấy đúng 2700 giây", chay_lean._han_gio() == 2700,
         f"— đang là {chay_lean._han_gio()}")
    # ⚠ Hằng số `HAN_GIO` chỉ là MẶC ĐỊNH. Đọc thẳng nó trong `chay()` thì đặt 60
    # phút trong Cài đặt mà vẫn bị giết ở phút 15 — đúng nghĩa núm giả.
    nguon = io.open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "cat_studio", "chay_lean.py"),
        encoding="utf-8").read()
    kiem("`chay()` gọi `_han_gio()`, không đọc thẳng hằng số",
         "time.time() + han" in nguon and "time.time() + HAN_GIO" not in nguon)
finally:
    luu_tru.ghi_cai_dat(cu)

print("\n▸ File cài đặt hỏng thì rơi về mặc định, KHÔNG nổ")
kiem("số gõ thành chữ", cai_dat.doc({cai_dat.KHOA_HAN_GIO: "bốn lăm"})[
     cai_dat.KHOA_HAN_GIO] == cai_dat.BANG_O[cai_dat.KHOA_HAN_GIO]["mac_dinh"])
kiem("hạn giờ không bao giờ dưới một phút",
     cai_dat.han_gio_giay({cai_dat.KHOA_HAN_GIO: 0}) >= 60,
     "— đặt 0 rồi tự hỏi sao lượt nào cũng chết ngay là bẫy tự giăng")
kiem("thiếu khoá thì vẫn đủ bộ", set(cai_dat.doc({})) == set(cai_dat.BANG_O))

print("\n▸ Từ điển gửi được qua cầu nối")
import json  # noqa: E402
td = cai_dat.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
kiem("nhóm nào cũng có ô", all(n["o"] for n in td["nhom"]))
kiem("ô nào cũng khai đủ thứ giao diện cần",
     all(all(k in o for k in ("ten", "nhan", "kieu", "mac_dinh", "goi_y", "chon",
                              "nguyen", "don_vi", "bat_buoc"))
         for n in td["nhom"] for o in n["o"]),
     "— hộp Cài đặt dựng bằng chính `Hang` của hộp khối")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
