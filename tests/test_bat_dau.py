"""KHỐI BẮT ĐẦU — nửa «thiết lập» của thuật toán, và mấy chỗ nó hỏng LẶNG.

VÌ SAO BÀI NÀY PHẢI CÓ
----------------------
Một script QuantConnect có hai nửa: `initialize` (nói một lần) và `on_data` (chạy lại
mỗi nhịp). Sơ đồ ta vẽ là nửa dưới; khối Bắt đầu LÀ nửa trên. Đọc từ 444 thuật toán
Python thật của LEAN: `set_start_date` có ở 395 cái, `set_cash` 250, `add_equity` 244 —
nên nửa trên gần như bắt buộc, và nó phải sống sót qua lưu/mở.

Mấy chỗ hỏng LẶNG bài này canh:

  · **`chuan_hoa_khoi` DỰNG LẠI khối Bắt đầu từ đầu.** Bản cũ chỉ giữ cái tên, nên sáu
    ô mới bay sạch mỗi lần lưu — hộp thoại điền xong, thẻ hiện đúng, lưu rồi mở lại là
    về mặc định. Không lỗi, không cảnh báo.
  · **Mặc định là list/dict dùng chung.** Không chép sâu thì mọi khối Bắt đầu xài
    chung MỘT danh sách mã: sửa khối này là khối kia đổi theo. Bẫy cũ của Python, im
    lặng cho tới lúc có hai khối.
  · Không có mã (cỗ máy chạy đủ mọi nến mà không mua bán gì) · ngày ngược (LEAN không
    chạy nến nào) · vốn 0 (mọi lệnh bị từ chối, backtest vẫn chạy hết) · mã khai hai
    lần (LEAN đăng ký trùng).

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, core  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def loi(step, sev="error"):
    return [p["message"] for p in core.soat_khoi_bat_dau(step) if p["severity"] == sev]


def dong_the(step):
    return [d["text"] for d in core.the_buoc(step)["lines"]]


# ================= 1. Luật gốc: không bịa =================
print("\n▸ MỌI ô phải khai được câu LEAN đứng sau nó")
thieu = [o["ten"] for o in bat_dau.O_BAT_DAU if not str(o.get("lean") or "").strip()]
kiem("không ô nào thiếu `lean`", not thieu,
     f"— {thieu}" if thieu else f"({len(bat_dau.O_BAT_DAU)} ô)")
# ⚠ KHÔNG canh SỐ Ô. Bản trước viết `== 6` và phải sửa ngay lần đầu một chiến
# thuật thật đòi thêm ô — mà thêm ô theo ví dụ thật chính là cách làm đã chốt.
# Canh CẤU TRÚC thì không phải sửa mỗi lần, mà vẫn chặn đúng thứ đáng chặn.
ten_o = [o["ten"] for o in bat_dau.O_BAT_DAU]
kiem("không ô nào trùng tên", len(set(ten_o)) == len(ten_o), f"— {ten_o}")
kiem("có đủ năm ô cốt lõi",
     {"ma", "khoang", "von", "nhip", "san"} <= set(ten_o), f"— {ten_o}")
kiem("mỗi loại tài sản một hàm `add_*` RIÊNG",
     len({h for _m, _n, h in bat_dau.LOAI_TAI_SAN}) == len(bat_dau.LOAI_TAI_SAN),
     "— hai loại cùng một hàm là một loại bịa")
kiem("mỗi nhịp khai rõ độ phân giải và lối chạy",
     all(r and c for _m, _n, r, c, _t in bat_dau.NHIP))

print("\n▸ Làm nóng KHÔNG thành ô — bộ sinh mã tự suy từ chỉ báo đã vẽ")
ten_o = {o["ten"] for o in bat_dau.o_cua()}
for cam in ("lam_nong", "warm_up", "warmup"):
    kiem(f"không có ô `{cam}`", cam not in ten_o)
kiem("và lý do được ghi lại trong bat_dau.py", "set_warm_up" in bat_dau.__doc__)

print("\n▸ Cố ý CHƯA có: chọn mã động, và cửa vào thứ hai")
kiem("chưa có universe", "universe" not in json.dumps(bat_dau.tu_dien()).lower())
kiem("nhưng ghi rõ là bỏ có chủ ý",
     "add_universe" in bat_dau.__doc__ and "chủ ý" in bat_dau.__doc__)

# ================= 2. Nhịp giải quyết cái hack "một lần mỗi ngày" =================
print("\n▸ Nhịp — thứ xoá hẳn cái hack «chỉ một lần mỗi ngày»")
theo_nen = [n for n in bat_dau.NHIP if n[3] == "on_data"]
hen_gio = [n for n in bat_dau.NHIP if n[3] != "on_data"]
kiem("đủ năm nhịp theo NẾN — đúng năm `Resolution` của LEAN",
     {n[2] for n in theo_nen} == {"TICK", "SECOND", "MINUTE", "HOUR", "DAILY"},
     f"— {[n[2] for n in theo_nen]}")
kiem("và có nhịp HẸN GIỜ", len(hen_gio) >= 1, f"— {len(hen_gio)} nhịp")
kiem("nhịp hẹn giờ đều qua `schedule.on`",
     all("schedule.on" in n[3] for n in hen_gio), f"— {len(hen_gio)} nhịp")
# ⚠ TỪNG CANH NGƯỢC: bản D-15 bắt nhịp hẹn giờ phải là PHÚT, "vì dữ liệu ngày không
# có giờ nào trong đó mà hẹn". Sai — `schedule.on` chạy theo đồng hồ thuật toán, nên
# dữ liệu ngày vẫn hẹn giờ được (vd2 làm đúng thế). Ép phút thì SMA(200) thành 200
# phút chứ không phải 200 ngày: cùng sơ đồ, khác hẳn chiến thuật.
kiem("nhịp hẹn giờ cho CHỌN độ phân giải",
     all(any(o["ten"] == "do_phan_giai" for o in n[4]) for n in hen_gio))
_st = core.make_start_step()
_st["nhip"] = "sau_mo_cua"
kiem("và mặc định là NGÀY, không tự ép xuống phút",
     bat_dau.do_phan_giai(_st) == "DAILY", f"— {bat_dau.do_phan_giai(_st)}")
_st["do_phan_giai"] = "MINUTE"
kiem("chọn phút thì mới ra phút", bat_dau.do_phan_giai(_st) == "MINUTE")
_st["nhip"] = "ngay"
kiem("nhịp theo nến thì nhịp CHÍNH LÀ độ phân giải",
     bat_dau.do_phan_giai(_st) == "DAILY", "— ô chọn không đè lên nó")

print("\n▸ Ô thêm chỉ hiện theo nhịp đã chọn")
st = core.make_start_step()
kiem("nhịp theo nến: không thêm ô nào",
     len(bat_dau.o_cua(st)) == len(bat_dau.O_BAT_DAU))
st["nhip"] = "moi_ngay_luc"
ten_o = [o["ten"] for o in bat_dau.o_cua(st)]
kiem("«mỗi ngày đúng giờ» thêm ô Giờ và Phút",
     {"gio", "phut"} <= set(ten_o), f"— {ten_o}")
st["nhip"] = "sau_mo_cua"
kiem("«sau khi mở cửa» thêm ô Số phút",
     "so_phut" in [o["ten"] for o in bat_dau.o_cua(st)])
kiem("và câu LEAN đổi theo",
     "after_market_open" in bat_dau.ham_lean(st), f"— {bat_dau.ham_lean(st)}")

# ================= 3. Khối mới đã điền sẵn =================
print("\n▸ Khối vừa thả ra đã chạy được ngay")
st = core.make_start_step()
thieu_o = [o["ten"] for o in bat_dau.o_cua() if o["ten"] not in st]
kiem("có đủ ô mặc định", not thieu_o, f"— {thieu_o}" if thieu_o else "")
kiem("khối mới KHÔNG báo lỗi gì", not core.soat_khoi_bat_dau(st),
     f"— {[p['message'][:45] for p in core.soat_khoi_bat_dau(st)]}")
kiem("mặc định chạy trên vàng — dữ liệu miễn phí có sẵn",
     st["ma"] == [{"ma": "XAUUSD", "loai": "cfd"}], f"— {st['ma']}")

print("\n▸ ⚠ Hai khối Bắt đầu KHÔNG được dùng chung một danh sách mã")
a, b = core.make_start_step(), core.make_start_step()
a["ma"].append({"ma": "EURUSD", "loai": "forex"})
kiem("sửa khối này không đụng khối kia", len(b["ma"]) == 1, f"— {b['ma']}")
a["khoang"]["tu"] = "2015-06-01"
kiem("khoảng ngày cũng vậy", b["khoang"]["tu"] == "2010-01-01",
     f"— {b['khoang']['tu']}")

print("\n▸ File cũ (khối Bắt đầu trống ruột) mở ra vẫn chạy")
cu = {"kind": core.KIND_START, "id": "x", "name": "Bắt đầu"}
kiem("ô thiếu rơi về mặc định của từ điển", core.o_bat_dau(cu, "von") == 100000)
kiem("và soát ra sạch", not core.soat_khoi_bat_dau(cu),
     f"— {[p['message'][:45] for p in core.soat_khoi_bat_dau(cu)]}")

# ================= 4. Chữ trên thẻ =================
print("\n▸ Chữ trên thẻ do Python dựng")
st = core.make_start_step()
d = dong_the(st)
kiem("một mã thì nói luôn loại tài sản",
     d[0] == "XAUUSD · CFD — vàng, dầu, chỉ số", f"— {d[0]!r}")
kiem("ngày hiện kiểu Việt, không phải kiểu file",
     d[1] == "01/01/2010 → 01/01/2019", f"— {d[1]!r}")
kiem("tiền có dấu phân nhóm", d[2] == "vốn 100.000$", f"— {d[2]!r}")
kiem("huy hiệu nói NHỊP", core.the_buoc(st)["badges"] == ["Mỗi nến ngày"],
     f"— {core.the_buoc(st)['badges']}")

st["ma"] = [{"ma": "SPY", "loai": "equity"}, {"ma": "QQQ", "loai": "equity"},
            {"ma": "IWM", "loai": "equity"}]
kiem("nhiều mã thì đếm rồi kể tên",
     dong_the(st)[0] == "3 mã: SPY, QQQ, IWM", f"— {dong_the(st)[0]!r}")
st["moc_so_sanh"] = "SPY"
kiem("mốc so sánh hiện thêm một dòng", "mốc so sánh: SPY" in dong_the(st))
st["ma"] = []
kiem("không mã thì nói rõ", dong_the(st)[0] == "chưa chọn mã nào")

print("\n▸ Bắt đầu KHÔNG phải cổng rẽ nhánh")
kiem("không phải cổng", not core.is_branch_gate(core.make_start_step()))

# ================= 5. Soát ruột: toàn thứ hỏng LẶNG =================
print("\n▸ Không có mã — cỗ máy chạy đủ mọi nến mà không mua bán gì")
x = core.make_start_step()
x["ma"] = []
kiem("→ lỗi", any("chưa chọn mã nào" in m for m in loi(x)))

print("\n▸ Mã khai hai lần — LEAN đăng ký trùng")
x["ma"] = [{"ma": "SPY", "loai": "equity"}, {"ma": "SPY", "loai": "equity"}]
kiem("→ lỗi", any("hai lần" in m for m in loi(x)))
x["ma"] = [{"ma": "SPY", "loai": "khong_co_that"}]
kiem("loại tài sản lạ → lỗi", any("loại tài sản" in m for m in loi(x)))
x["ma"] = [{"ma": "  ", "loai": "equity"}]
kiem("mã để trống → lỗi", any("để trống" in m for m in loi(x)))

print("\n▸ Ngày ngược — LEAN không chạy nến nào")
y = core.make_start_step()
y["khoang"] = {"tu": "2019-01-01", "den": "2010-01-01"}
kiem("→ lỗi", any("không trước ngày kết thúc" in m for m in loi(y)))
y["khoang"] = {"tu": "2019-01-01", "den": "2019-01-01"}
kiem("cùng một ngày cũng lỗi", any("không trước" in m for m in loi(y)))
y["khoang"] = {"tu": "01/01/2010", "den": "2019-01-01"}
kiem("ngày sai khuôn → lỗi", any("sai khuôn" in m for m in loi(y)))

print("\n▸ Vốn 0 — mọi lệnh bị từ chối, mà backtest vẫn chạy hết")
z = core.make_start_step()
z["von"] = 0
kiem("→ lỗi", any("lớn hơn 0" in m for m in loi(z)))
z["von"] = "một trăm nghìn"
kiem("vốn không phải số → lỗi", any("không phải một con số" in m for m in loi(z)))

print("\n▸ Nhịp lạ → lỗi")
w = core.make_start_step()
w["nhip"] = "moi_khi_vui"
kiem("→ lỗi", any("không có nhịp" in m for m in loi(w)))

print("\n▸ Khối Bắt đầu và khối khác không soát lẫn nhau")
from cat_studio import hoi, lam  # noqa: E402
kiem("soat_khoi_bat_dau bỏ qua khối Hỏi",
     not core.soat_khoi_bat_dau(core.make_hoi_step(hoi.HOI_VI_THE)))
kiem("soat_khoi_lam bỏ qua khối Bắt đầu",
     not core.soat_khoi_lam(core.make_start_step()))
kiem("soat_khoi_hoi bỏ qua khối Bắt đầu",
     not core.soat_khoi_hoi(core.make_start_step()))

# ================= 6. ⚠ Sống sót qua lưu/mở =================
print("\n▸ ⚠ SÁU Ô PHẢI SỐNG SÓT QUA LƯU/MỞ")
# `chuan_hoa_khoi` dựng lại khối Bắt đầu từ đầu. Bản cũ chỉ giữ cái tên — tức điền
# xong, lưu, mở lại là về mặc định. Không lỗi, không cảnh báo.
g = core.make_start_step("Cỗ máy vàng")
g["ma"] = [{"ma": "XAUUSD", "loai": "cfd"}, {"ma": "EURUSD", "loai": "forex"}]
g["khoang"] = {"tu": "2015-06-01", "den": "2018-12-31"}
g["von"] = 5000
g["nhip"] = "moi_ngay_luc"
g["gio"] = 14
g["phut"] = 30
g["moc_so_sanh"] = "SPY"
g["san"] = "OANDA_BROKERAGE"
doc = core.make_process_template("t", [g, core.make_lam_step(lam.LAM_DONG)])
ra = doc["steps"][0]
kiem("tên khối còn", ra["name"] == "Cỗ máy vàng")
kiem("danh sách mã còn nguyên hai dòng", len(ra.get("ma") or []) == 2, f"— {ra.get('ma')}")
kiem("khoảng ngày còn", (ra.get("khoang") or {}).get("tu") == "2015-06-01")
kiem("vốn còn", ra.get("von") == 5000)
kiem("nhịp còn", ra.get("nhip") == "moi_ngay_luc")
kiem("ô thêm của nhịp còn", ra.get("gio") == 14 and ra.get("phut") == 30)
kiem("mốc so sánh còn", ra.get("moc_so_sanh") == "SPY")
kiem("sàn còn", ra.get("san") == "OANDA_BROKERAGE")

print("\n▸ Và khoá rác thì KHÔNG sống sót")
g["rac_tu_file_sua_tay"] = 123
ra2 = core.make_process_template("t", [g])["steps"][0]
kiem("khoá lạ bị bỏ", "rac_tu_file_sua_tay" not in ra2,
     "— khối Bắt đầu dựng lại từ danh sách ô cố định")

# ================= 7. Từ điển gửi qua cầu nối =================
print("\n▸ Từ điển gửi được qua cầu nối")
td = bat_dau.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
kiem("gửi đủ ô", len(td["o"]) == len(bat_dau.O_BAT_DAU))
kiem("có bảng loại tài sản", len(td["loai_tai_san"]) == len(bat_dau.LOAI_TAI_SAN))
kiem("có bảng nhịp", len(td["nhip"]) == len(bat_dau.NHIP))
kiem("gợi ý mã miễn phí có XAUUSD", "XAUUSD" in td["co_san"]["cfd"])

print("\n▸ Mỗi ô phải TỰ KHAI đủ, giao diện không được đoán hộ")
_o_them = [(n["ma"], o) for n in td["nhip"] for o in n["o_them"]]
# ⚠ Ô CHỌN phải có danh sách chọn. «Độ phân giải dữ liệu» khai năm mức, nhưng hộp
# thoại dựng lại object với `kieu: 'so'` đóng cứng và `chon: []` — nên nó hiện ra như
# một ô gõ chữ và năm lựa chọn biến mất. Từ điển đúng, giao diện tự chế mới sai.
hong = [f"{k}/{o['ten']}" for k, o in _o_them if o["kieu"] == "chon" and not o["chon"]]
kiem("ô chọn nào cũng có danh sách chọn", not hong, f"— {hong}")

# ⚠ VỊ TRÍ THỨ SÁU CỦA `_o` LÀ `don_vi`, KHÔNG PHẢI `goi_y`. Truyền chay thì câu
# "Từ 0 đến 390." nằm ở ô ĐƠN VỊ — hiện ra cạnh ô số như một đơn vị đo, còn ô gợi ý
# thì trống. Đã sai thế suốt với `so_phut`, `gio`, `phut`.
lac = [f"{o['ten']}={o['don_vi']!r}"
       for _k, o in _o_them + [("", x) for x in td["o"]]
       if re.search(r"[Tt]ừ .* đến ", str(o.get("don_vi") or ""))]
kiem("không câu «Từ … đến …» nào lạc sang ô đơn vị", not lac, f"— {lac}")

thieu = [f"{k}/{o['ten']}" for k, o in _o_them
         if o["kieu"] == "so" and not o["goi_y"]]
kiem("ô số nào cũng nói khoảng hợp lệ", not thieu, f"— {thieu}")
kiem("ô giờ/phút khai là SỐ NGUYÊN",
     all(o["nguyen"] for _k, o in _o_them if o["kieu"] == "so"),
     "— giao diện từng tự quyết chuyện này")

print("\n▸ Nhịp HẸN GIỜ: độ phân giải là của người dùng, không phải của nhịp")
# D-15: `schedule.on` chạy theo ĐỒNG HỒ nên dữ liệu ngày vẫn hẹn giờ được. Cột `res`
# của mấy nhịp hẹn giờ là chữ "MINUTE" còn sót lại từ trước — thứ quyết định thật là
# ô `do_phan_giai`. Hộp thoại từng in `Resolution.MINUTE` trong khi ô ghi DAILY và
# bộ sinh mã viết DAILY: dòng khai LEAN nói dối đúng chỗ nó sinh ra để nói thật.
hen = [n for n in bat_dau.NHIP if n[3] != "on_data"]
kiem("nhịp hẹn giờ nào cũng có ô độ phân giải",
     all(any(o["ten"] == "do_phan_giai" for o in n[4]) for n in hen),
     f"— {len(hen)} nhịp")
_hen = {"nhip": "tuan"}            # nhịp HẸN GIỜ, cột `res` của nó là "MINUTE"
kiem("với nhịp hẹn giờ, ô người dùng quyết — không phải cột `res`",
     bat_dau.do_phan_giai({**_hen, "do_phan_giai": "DAILY"}) == "DAILY"
     and bat_dau.do_phan_giai({**_hen, "do_phan_giai": "HOUR"}) == "HOUR",
     "— `res` của nhịp «tuan» là MINUTE, nhưng nó KHÔNG được thắng")
kiem("giá trị rác thì rơi về mặc định, không nổ",
     bat_dau.do_phan_giai({**_hen, "do_phan_giai": "rác"}) == "DAILY"
     and bat_dau.do_phan_giai({**_hen}) == "DAILY")
# Nhịp THEO NẾN thì ngược lại: nhịp CHÍNH LÀ độ phân giải, ô kia không có mặt.
kiem("với nhịp theo nến, nhịp mới là độ phân giải",
     bat_dau.do_phan_giai({"nhip": "phut"}) == "MINUTE"
     and bat_dau.do_phan_giai({"nhip": "gio", "do_phan_giai": "DAILY"}) == "HOUR",
     "— ô `do_phan_giai` không hiện ra ở mấy nhịp này nên không được thắng")

print("\n▸ ⭐ DÂY CHUYỀN của LEAN — ba chính sách, cắm ở `initialize`")
# ⚠ Chúng là Ô chứ không phải KHỐI, và đó là quyết định có lý kiểm được: cả ba gọi
# MỘT LẦN trong `initialize` (ví dụ `BaseFrameworkRegressionAlgorithm.py` của LEAN —
# năm cái `set_*` đều nằm trong đó). Thả một khối "Chia vốn đều" vào cuối một nhánh
# thì nó nghĩa là gì — "chỉ đặt cách chia vốn khi RSI < 30"? Không nghĩa nào.
#   Đường ranh: xảy ra MỖI NHỊP → khối Hành động; đặt MỘT LẦN → ô ở đây.
for _ten, _ham in (("chia_von", "set_portfolio_construction"),
                   ("phong_rui_ro", "set_risk_management"),
                   ("dat_lenh", "set_execution")):
    _o2 = bat_dau.O_THEO_TEN[_ten]
    kiem(f"có ô `{_ten}`", _o2["kieu"] == bat_dau.O_CHON and not _o2["bat_buoc"])
    kiem("  mặc định là KHÔNG dùng", _o2["mac_dinh"] == "",
         "— không cắm trạm nào thì sơ đồ chạy y như trước")
    kiem("  khai đúng hàm LEAN", _ham in _o2["lean"])

print("\n▸ Dây chuyền phải khớp đầu khớp đuôi")
_bd = core.make_start_step()
_th = core.make_lam_step(lam.LAM_TIN_HIEU)


def _nang(ds):
    return [v for v in ds if v["severity"] == "error"]


kiem("phát tín hiệu mà chưa chọn Chia vốn → LỖI",
     len(_nang(core.soat_day_chuyen([_bd, _th]))) == 1,
     "— insight bay vào hư không, backtest chạy xong không một lệnh nào")
_bd["chia_von"] = "EqualWeightingPortfolioConstructionModel"
kiem("chọn rồi thì sạch", not core.soat_day_chuyen([_bd, _th]))
kiem("chọn Chia vốn mà không khối tín hiệu nào → CẢNH BÁO",
     [v["severity"] for v in core.soat_day_chuyen([_bd])] == ["warning"])
kiem("trộn tín hiệu với lệnh tay → LỖI",
     len(_nang(core.soat_day_chuyen(
         [_bd, _th, core.make_lam_step(lam.LAM_DAT_TY_TRONG)]))) == 1,
     "— model chia vốn cân lại danh mục, lệnh tay bị gỡ ngay nhịp sau")
_bd2 = core.make_start_step()
_bd2["phong_rui_ro"] = "TrailingStopRiskManagementModel"
kiem("phòng rủi ro mà không có chia vốn → CẢNH BÁO",
     any(v["severity"] == "warning" for v in core.soat_day_chuyen([_bd2])),
     "— nó chạy SAU chia vốn, không có chia vốn thì không tới lượt")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
