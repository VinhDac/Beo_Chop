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
import inspect
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, core, lam  # noqa: E402
# ⚠ BÀI NÀY CHỐT TIẾNG VIỆT. Nó soát CHỮ do Python dựng — mặt khối, bảng Vấn đề,
# câu lỗi — mà app nay MẶC ĐỊNH TIẾNG ANH. Không chốt thì nó đọc bản dịch và mọi
# câu khẳng định dưới đây thành vô nghĩa. Bản gốc tiếng Việt cũng là KHOÁ của bảng
# dịch, nên khẳng định bằng tiếng Việt là khẳng định đúng thứ lõi sinh ra.
# Bản tiếng Anh có bài canh riêng: `test_ngon_ngu.py`.
from cat_studio import ngon_ngu  # noqa: E402
ngon_ngu.dat("vi")


dung = sai = 0
NL = chr(10)


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
     all(r and c for _m, _n, r, c, _t, _cr in bat_dau.NHIP))
# ⚠ Ô THỨ SÁU của mỗi nhịp — câu lịch cho RỔ ĐỘNG. Thiếu nó thì `sinh_ma` viết
# `self._ma[0]`, mà rổ lúc `initialize` còn RỖNG: `IndexError` ở dòng đầu.
kiem("mỗi nhịp có thêm câu lịch KHÔNG MÃ, cho rổ động",
     all(cr for *_x, cr in bat_dau.NHIP))

print("\n▸ Làm nóng KHÔNG thành ô — bộ sinh mã tự suy từ chỉ báo đã vẽ")
ten_o = {o["ten"] for o in bat_dau.o_cua()}
for cam in ("lam_nong", "warm_up", "warmup"):
    kiem(f"không có ô `{cam}`", cam not in ten_o)
kiem("và lý do được ghi lại trong bat_dau.py", "set_warm_up" in bat_dau.__doc__)

print("\n▸ Cố ý CHƯA có: cửa vào thứ hai")
kiem("nhưng ghi rõ là bỏ có chủ ý",
     "cửa vào thứ hai" in bat_dau.__doc__ and "chủ ý" in bat_dau.__doc__)
# ⚠ BÀI NÀY TỪNG CANH NGƯỢC: nó bắt từ điển KHÔNG được có chữ "universe", vì hồi D-15
# chọn mã động là chỗ "cố ý chưa có". Nay nó có rồi — và nó KHÔNG phải một khối mới,
# nó là kiểu thứ hai của chính ô «Chạy trên mã nào» (`set_universe_selection` gọi một
# lần trong `initialize`, đúng luật của ba ô chính sách). Giữ bài cũ thì nó chặn đúng
# cái việc vừa làm xong, nên đổi chiều: giờ canh rổ phải CÓ.
kiem("và nay ô `ma` nói được RỔ ĐỘNG",
     "universe" in json.dumps(bat_dau.tu_dien()).lower())

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
# ⚠ THIẾU NHỊP THÁNG thì mọi chiến thuật "cân lại danh mục mỗi tháng" không nói
# được — mà đếm trong tập ví dụ thì có tới ba cái dùng nó. Người ta phải lách bằng
# nhịp NGÀY rồi tự đếm ngày trong khối, tức app lại đi đếm hộ LEAN đúng thứ LEAN đã
# có sẵn hàm (`date_rules.month_start` / `month_end`).
kiem("có nhịp THÁNG — cả đầu tháng lẫn cuối tháng",
     {"thang_dau", "thang_cuoi"} <= {n[0] for n in bat_dau.NHIP},
     f"— {sorted(n[0] for n in bat_dau.NHIP)}")
# Mỗi nhịp phải trỏ vào một `date_rules` CÓ THẬT của LEAN, không bịa tên quy tắc.
# ⚠ DANH SÁCH NÀY LÀ MỘT BẢN CHỤP, và nó vừa đổ đúng vì thế: bản trước chỉ kể bốn
# quy tắc, nên thêm quý/năm là nó kêu "bịa tên" — kêu oan. Giữ phép soát ở đây vì nó
# rẻ và chạy ở mọi máy, nhưng chuyện ĐỦ hay THIẾU so với kệ LEAN thì `test_du_lean`
# canh, bằng cách đọc thẳng `Common/Scheduling/DateRules.cs`.
_quy_tac = ("every_day", "week_start", "week_end", "month_start", "month_end",
            "quarter_start", "quarter_end", "year_start", "year_end")
_bia = [n[0] for n in hen_gio
        if not any(f"date_rules.{q}(" in n[3] for q in _quy_tac)]
kiem("nhịp nào cũng dùng một `date_rules` có thật", not _bia, f"— {_bia}")
# Và quy tắc GIỜ cũng vậy — bảng riêng từ 18/10/2026.
_gio_that = ("after_market_open", "before_market_close", "before_market_open",
             "after_market_close", "at")
_gio_bia = [g[0] for g in bat_dau.QUY_TAC_GIO
            if not any(f"time_rules.{q}(" in g[2] for q in _gio_that)]
kiem("quy tắc giờ nào cũng là một `time_rules` có thật", not _gio_bia,
     f"— {_gio_bia}")
# ⚠ HAI BẢNG PHẢI GHÉP ĐƯỢC VỚI NHAU — 9 × 5 = 45 cách, và không cách nào được hụt
# một nửa. Câu LEAN sinh ra phải có CẢ `date_rules` lẫn `time_rules`; thiếu một bên
# là `schedule.on` cụt tham số, nổ lúc chạy.
for _n in hen_gio:
    for _g in bat_dau.QUY_TAC_GIO:
        for _ro in (None, {"ro": "qc500"}):
            _c = bat_dau.ham_chay({"nhip": _n[0], "quy_tac_gio": _g[0],
                                   "ma": _ro, "so_phut": 30, "gio": 10,
                                   "phut": 0})
            if not ("date_rules." in _c and "time_rules." in _c
                    and "{gio}" not in _c):
                kiem(f"nhịp «{_n[0]}» × giờ «{_g[0]}» ghép đủ", False, f"— {_c}")
kiem(f"mọi cặp nhịp × giờ đều ghép đủ ({len(hen_gio)} × "
     f"{len(bat_dau.QUY_TAC_GIO)} = {len(hen_gio) * len(bat_dau.QUY_TAC_GIO)} cách)",
     True)
# ⚠ FILE CŨ PHẢI MỞ ĐƯỢC. Ba mã nhịp cũ từng là ba dòng riêng; nay chúng đều là
# `every_day` khác quy tắc giờ. Mất bảng `NHIP_CU` thì mọi sơ đồ đã lưu thành "nhịp
# lạ" và `ham_chay` rơi về `on_data` — sơ đồ cân lại mỗi ngày lúc mở cửa lặng lẽ đổi
# thành chạy mỗi nến, không lỗi, không một lời.
for _cu, _mong in (("sau_mo_cua", "after_market_open"),
                   ("truoc_dong_cua", "before_market_close"),
                   ("moi_ngay_luc", "time_rules.at(")):
    _c = bat_dau.ham_chay({"nhip": _cu, "so_phut": 30, "gio": 10, "phut": 0})
    kiem(f"nhịp cũ «{_cu}» vẫn sinh ra đúng câu như trước",
         "date_rules.every_day(" in _c and _mong in _c, f"— {_c}")
# Và câu "không mã" phải khớp câu "có mã": rổ động không gõ được tên mã nào, nên hai
# câu lệch nhau là rổ chạy một nhịp khác hẳn nhịp người dùng chọn.
_lech = [n[0] for n in hen_gio
         if n[3].split("date_rules.")[1].split("(")[0]
         != n[5].split("date_rules.")[1].split("(")[0]]
kiem("câu cho RỔ ĐỘNG dùng cùng quy tắc ngày với câu gõ mã sẵn", not _lech,
     f"— {_lech}")
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
# `o_cua` nay CHỈ trả ô của KHỐI (xem `bat_dau.NHOM_CO_MAY`) — nên đếm theo đúng
# phần ấy của `O_BAT_DAU`, không đếm cả bảng.
_o_khoi = [o for o in bat_dau.O_BAT_DAU if not bat_dau.la_o_co_may(o)]
kiem("nhịp theo nến: không thêm ô nào",
     len(bat_dau.o_cua(st)) == len(_o_khoi), f"— {len(bat_dau.o_cua(st))}/{len(_o_khoi)}")
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
kiem("huy hiệu nói NHỊP", core.the_buoc(st)["badges"] == ["Mỗi nến ngày"],
     f"— {core.the_buoc(st)['badges']}")

# ⚠ ĐƯỜNG RANH CỦA THẺ, và nó đã dời MỘT LẦN nên đáng ghi rõ. Ngày và vốn thì CÓ ở
# lại thẻ: chúng là «sơ đồ này chạy từ bao giờ, bằng bao nhiêu tiền» — của NGƯỜI DÙNG.
# Còn dây chuyền LEAN, phí sàn, ô nhớ, mốc so sánh thì KHÔNG: chúng là việc LEAN lo,
# nay nằm trong hộp Cỗ máy LEAN (`bat_dau.NHOM_CO_MAY`), và thẻ in chúng là làm một
# khối phình ra vì mấy thứ chẳng dính gì tới dòng chảy ngay dưới nó.
_ca = " ".join(d)
kiem("ngày hiện kiểu Việt, không phải kiểu file", "01/01/2010 → 01/01/2019" in _ca,
     f"— {d}")
kiem("tiền có dấu phân nhóm", "vốn 100.000$" in _ca, f"— {d}")
_st_may = core.make_start_step()
_st_may["moc_so_sanh"] = "SPY"          # file CŨ: ô cỗ máy còn nằm trong khối
kiem("thẻ KHÔNG in ô của CỖ MÁY, kể cả khi file cũ còn để nó trong khối",
     not any("SPY" in x for x in core.mo_ta_bat_dau(_st_may)[1:]),
     f"— {core.mo_ta_bat_dau(_st_may)}")

st["ma"] = [{"ma": "SPY", "loai": "equity"}, {"ma": "QQQ", "loai": "equity"},
            {"ma": "IWM", "loai": "equity"}]
kiem("nhiều mã thì đếm rồi kể tên",
     dong_the(st)[0] == "3 mã: SPY, QQQ, IWM", f"— {dong_the(st)[0]!r}")
st["ma"] = []
kiem("không mã thì nói rõ", dong_the(st)[0] == "chưa chọn mã nào")

# ================= 4b. CỖ MÁY LEAN =================
# Viên thuốc ở góc phải canvas là CỬA DUY NHẤT vào hộp Cỗ máy, nên nó luôn có mặt —
# nhưng chữ trên nó chỉ kể thứ ĐÃ ĐỔI. Kể cả mặc định thì nó dài bằng cả hộp thoại, và
# ta chỉ dời đống lộn xộn từ khối Bắt đầu sang góc màn hình.
print("\n▸ Cỗ máy LEAN — viên thuốc góc phải chỉ kể thứ ĐÃ ĐỔI")
kiem("chưa đặt gì thì không kể gì", core.tom_tat_co_may({}) == [],
     f"— {core.tom_tat_co_may({})}")
kiem("hồ sơ mặc định cũng vậy", core.tom_tat_co_may(core.co_may_mac_dinh()) == [],
     f"— {core.tom_tat_co_may(core.co_may_mac_dinh())}")

_may = dict(core.co_may_mac_dinh(), moc_so_sanh="SPY")
kiem("đổi một ô -> kể đúng một thứ", core.tom_tat_co_may(_may) == ["Mốc so sánh SPY"],
     f"— {core.tom_tat_co_may(_may)}")
# Ô CHỌN phải hiện NHÃN, không hiện tên lớp LEAN: "InsightWeighting…" đọc trên canvas
# thì không ai biết nó chia vốn kiểu gì.
_may2 = dict(core.co_may_mac_dinh(),
             chia_von="InsightWeightingPortfolioConstructionModel")
kiem("ô CHỌN kể bằng nhãn tiếng Việt, không bằng tên lớp LEAN",
     all("PortfolioConstruction" not in x for x in core.tom_tat_co_may(_may2)),
     f"— {core.tom_tat_co_may(_may2)}")
# Ô nhớ là một DANH SÁCH, kể bằng số chứ đừng đổ cả danh sách ra viên thuốc.
_may3 = dict(core.co_may_mac_dinh(),
             tri_nho=[{"ma": "nho_so_1", "nhan": "a", "ban_dau": 0},
                      {"ma": "nho_so_2", "nhan": "b", "ban_dau": 0}])
kiem("ô nhớ kể bằng SỐ", core.tom_tat_co_may(_may3) == ["2 ô nhớ"],
     f"— {core.tom_tat_co_may(_may3)}")

# ---- Hồ sơ cỗ máy: FILE CŨ phải lôi lên được ----
# ⚠ Trước 18/10/2026 mười một ô này nằm ngay trong khối Bắt đầu. File lưu hồi ấy mở ra
# mà không ai lôi lên thì cỗ máy rơi hết về mặc định — sơ đồ vẫn vẽ, vẫn chạy, chỉ là
# chạy bằng một DÂY CHUYỀN KHÁC với hôm người ta lưu nó. Hỏng lặng, và hỏng vào đúng
# thứ người ta đã chỉnh tay.
print("\n▸ File CŨ — ô cỗ máy nằm trong khối Bắt đầu thì phải lôi lên")
_cu = core.make_start_step()
_cu["chia_von"] = "EqualWeightingPortfolioConstructionModel"
_cu["phi"], _cu["phi_moi_lenh"] = "ConstantFeeModel", 2.5
_cu["moc_so_sanh"] = "QQQ"
_d = core.normalize_process({"name": "cũ", "steps": [_cu], "edges": []})
_m = _d[core.KHOA_CO_MAY]
kiem("lôi được ô thường", _m["chia_von"] == "EqualWeightingPortfolioConstructionModel",
     f"— {_m['chia_von']!r}")
kiem("lôi được cả Ô CON (chỉ mọc khi đã chọn model)", _m.get("phi_moi_lenh") == 2.5,
     f"— {_m.get('phi_moi_lenh')!r}")
kiem("lôi được ô gõ chữ", _m["moc_so_sanh"] == "QQQ")
kiem("và khối Bắt đầu SẠCH sau đó — một nhà, không hai",
     not any(k in _d["steps"][0]
             for k in ("chia_von", "phi", "phi_moi_lenh", "moc_so_sanh")),
     f"— {sorted(_d['steps'][0])}")
# Có hồ sơ mới rồi thì ĐỪNG lôi nữa: lôi thì giá trị cũ đè giá trị mới, và người dùng
# sửa xong lưu lại thấy nó bật về như cũ.
_d2 = core.normalize_process(dict(
    _d, co_may=dict(_m, chia_von="RiskParityPortfolioConstructionModel")))
kiem("có hồ sơ mới thì file cũ KHÔNG đè lên",
     _d2[core.KHOA_CO_MAY]["chia_von"] == "RiskParityPortfolioConstructionModel",
     f"— {_d2[core.KHOA_CO_MAY]['chia_von']!r}")
kiem("tài liệu nào cũng mang hồ sơ cỗ máy",
     isinstance(core.make_process_template("x", [], [])[core.KHOA_CO_MAY], dict))

# ================= 4c. Rổ kén ngày =================
# ⚠ CÂU CẢNH BÁO NÀY TỪNG LÀ MỘT CÁI NHÃN. Nó dán cứng trong tên rổ — *"(cần dữ liệu
# doanh nghiệp: chỉ có 24/03–07/04/2014)"* — nên chiếm ba dòng của thẻ, mãi mãi, kể cả
# khi khoảng ngày nằm đúng trong vùng có dữ liệu. Cảnh báo luôn bật thì người ta học
# cách không nhìn nó. Nay nó kêu ĐÚNG LÚC sắp hỏng, mà hỏng thì hỏng LẶNG: LEAN chạy
# hết mọi nến, rổ rỗng, 0 lệnh, không báo gì.
print("\n▸ Rổ đọc dữ liệu doanh nghiệp — kêu ĐÚNG LÚC khoảng ngày trật")


def _canh_ro(ro, tu, den):
    x = core.make_start_step()
    x["ma"] = {"ro": ro, "giu_n": 10}
    x["khoang"] = {"tu": tu, "den": den}
    return [p for p in core.soat_khoi_bat_dau(x)
            if "dữ liệu doanh nghiệp" in p["message"]]


_kh = bat_dau.KHOANG_DOANH_NGHIEP
for _ro in [r[0] for r in bat_dau.RO if len(r) >= 6 and r[5]]:
    kiem(f"«{_ro}» trùm đúng khoảng -> IM", not _canh_ro(_ro, _kh[0], _kh[1]))
    kiem(f"«{_ro}» trật hẳn ra ngoài -> KÊU",
         len(_canh_ro(_ro, "2015-01-01", "2020-12-31")) == 1)
    kiem(f"«{_ro}» chỉ chạm MỘT đầu cũng đủ -> IM",
         not _canh_ro(_ro, "2014-01-01", _kh[0]))
# Rổ ETF không kén ngày thì đừng kêu — kêu bừa là dạy người ta bỏ qua bảng Vấn đề.
kiem("rổ KHÔNG kén ngày thì không kêu bao giờ",
     not _canh_ro("kim_loai", "2015-01-01", "2020-12-31"))
# Và câu cảnh báo ấy KHÔNG được quay lại làm nhãn.
kiem("nhãn rổ trên THẺ là tên trần, không kèm câu cảnh báo",
     all("cần dữ liệu" not in r[1] for r in bat_dau.RO),
     f"— {[r[1] for r in bat_dau.RO if 'cần dữ liệu' in r[1]]}")
# Nhưng Ô CHỌN thì vẫn phải nhắc: đó là chỗ người ta đang quyết định chọn rổ nào.
kiem("ô CHỌN vẫn nhắc, vì đó là lúc người ta chọn rổ",
     all("cần dữ liệu" in bat_dau.nhan_ro(r)
         for r in bat_dau.RO if len(r) >= 6 and r[5]))

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
# ⚠ HAI Ô NÀY KHÔNG CÒN Ở TRONG KHỐI, và đó mới là điều phải canh: chúng SANG hồ sơ
# cỗ máy, không BIẾN MẤT. Chỉ canh "khối sạch" thì một lượt chuyển nhà làm rơi mất
# giá trị vẫn qua tuốt — người dùng mở lại thấy mốc so sánh trống mà chẳng gì báo.
kiem("mốc so sánh RỜI khối", "moc_so_sanh" not in ra)
kiem("sàn RỜI khối", "san" not in ra)
kiem("...và SANG hồ sơ cỗ máy, không rơi mất",
     doc[core.KHOA_CO_MAY]["moc_so_sanh"] == "SPY"
     and doc[core.KHOA_CO_MAY]["san"] == "OANDA_BROKERAGE",
     f"— {doc[core.KHOA_CO_MAY]['moc_so_sanh']!r} · {doc[core.KHOA_CO_MAY]['san']!r}")

print("\n▸ Và khoá rác thì KHÔNG sống sót")
g["rac_tu_file_sua_tay"] = 123
ra2 = core.make_process_template("t", [g])["steps"][0]
kiem("khoá lạ bị bỏ", "rac_tu_file_sua_tay" not in ra2,
     "— khối Bắt đầu dựng lại từ danh sách ô cố định")

# ================= 7. Từ điển gửi qua cầu nối =================
print("\n▸ Từ điển gửi được qua cầu nối")
td = bat_dau.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
# ⚠ HAI BỘ Ô, và PHẢI ĐỦ CẢ HAI. Từ điển chia `o` (khối Bắt đầu) với `o_co_may`
# (hộp Cỗ máy LEAN) — xem `NHOM_CO_MAY`. Chỉ đếm một bộ thì hôm một ô đi lạc sang
# bộ kia, hay rơi khỏi cả hai, phép này vẫn xanh.
kiem("gửi đủ ô, chia đúng HAI bộ",
     len(td["o"]) + len(td["o_co_may"]) == len(bat_dau.O_BAT_DAU)
     and not ({o["ten"] for o in td["o"]} & {o["ten"] for o in td["o_co_may"]}),
     f"— {len(td[chr(111)])} + {len(td[chr(111)+chr(95)+chr(99)+chr(111)+chr(95)+chr(109)+chr(97)+chr(121)])} / {len(bat_dau.O_BAT_DAU)}")
kiem("và nhóm cũng chia đôi, không nhóm nào ở cả hai bên",
     not ({n["ma"] for n in td["nhom"]} & {n["ma"] for n in td["nhom_co_may"]})
     and len(td["nhom"]) + len(td["nhom_co_may"]) == len(bat_dau.NHOM_O))
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
# Dây chuyền nay nằm ở HỒ SƠ CỖ MÁY, nên phép soát nhận nó làm tham số thứ hai.
_may_chia = {"chia_von": "EqualWeightingPortfolioConstructionModel"}
kiem("chọn rồi thì sạch", not core.soat_day_chuyen([_bd, _th], _may_chia))
kiem("chọn Chia vốn mà không khối tín hiệu nào → CẢNH BÁO",
     [v["severity"] for v in core.soat_day_chuyen([_bd], _may_chia)] == ["warning"])
kiem("trộn tín hiệu với lệnh tay → LỖI",
     len(_nang(core.soat_day_chuyen(
         [_bd, _th, core.make_lam_step(lam.LAM_DAT_TY_TRONG)], _may_chia))) == 1,
     "— model chia vốn cân lại danh mục, lệnh tay bị gỡ ngay nhịp sau")
kiem("phòng rủi ro mà không có chia vốn → CẢNH BÁO",
     any(v["severity"] == "warning" for v in core.soat_day_chuyen(
         [core.make_start_step()],
         {"phong_rui_ro": "TrailingStopRiskManagementModel"})),
     "— nó chạy SAU chia vốn, không có chia vốn thì không tới lượt")

print("\n▸ ⚠ Ô NGƯỠNG của trạm phòng rủi ro — có mới hiện, và 0 là CẮT NGAY")
# Cả bốn model nhận một ngưỡng phần trăm làm tham số đầu, mà bộ sinh mã trước đây
# gọi chúng KHÔNG THAM SỐ — tức chúng chạy ở 5% mặc định của LEAN trong khi nhãn hứa
# «theo %» và hộp thoại không có ô % nào. Ngưỡng là CẢ cái phanh; đóng cứng rồi không
# nói ra là một kiểu nói dối lặng.
_bdn = core.make_start_step()
kiem("chưa chọn model thì KHÔNG có ô ngưỡng nào thừa ra",
     "nguong" not in {o["ten"] for o in bat_dau.o_cua(_bdn)})
_bdn["chia_von"] = "EqualWeightingPortfolioConstructionModel"
for _m, _nhan, _th2 in bat_dau.PHONG_RUI_RO:
    if not _m:
        continue
    _bdn["phong_rui_ro"] = _m
    _hien = {o["ten"]: o for o in bat_dau.o_co_may(_bdn)}
    kiem(f"«{_nhan}» → ô ngưỡng hiện ra", "nguong" in _hien)
    # Nhãn phải nói ĐÚNG PHANH NÀO: cùng một con số 0.05 nghĩa «lỗ 5%» ở model này
    # và «lãi 5%» ở model kia. Một nhãn chung cho cả bốn là một nhãn nói sai ba lần.
    kiem("  và nhãn ô nói đúng model ấy đo cái gì",
         _hien["nguong"]["nhan"] == _th2[0]["nhan"])
_bdn["phong_rui_ro"] = "MaximumDrawdownPercentPerSecurity"
kiem("mặc định sạch", not [v for v in core.soat_khoi_bat_dau(core.make_start_step(), _bdn)
                          if v["severity"] == "error"])
_bdn["nguong"] = 0
kiem("ngưỡng 0 → LỖI", any(v["severity"] == "error" and "ngưỡng" in v["message"]
                           for v in core.soat_khoi_bat_dau(core.make_start_step(), _bdn)),
     "— LEAN lấy `-abs(0)` = 0 rồi so `pnl < 0`: cắt ngay khi mã chớm lỗ một xu")
_bdn["nguong"] = ""
kiem("ngưỡng để trống → LỖI, không lặng rơi về 5%",
     any(v["severity"] == "error" for v in core.soat_khoi_bat_dau(core.make_start_step(), _bdn)),
     "— hộp trống trơn mà mã sinh ra mang một con số là hai đằng nói khác nhau")
_bdn["nguong"] = 5
kiem("gõ 5 (tưởng là 5%) → CẢNH BÁO",
     any(v["severity"] == "warning" and "PHẦN" in v["message"]
         for v in core.soat_khoi_bat_dau(core.make_start_step(), _bdn)),
     "— 5 nghĩa là 500%, tức trạm ấy gần như không bao giờ cắn")
_bdn["nguong"] = 0.08
kiem("ngưỡng hợp lệ đi THẲNG vào câu LEAN",
     "MaximumDrawdownPercentPerSecurity(0.08)" in
     " ".join(bat_dau.lean_day_chuyen(_bdn)),
     f"— {bat_dau.lean_day_chuyen(_bdn)}")
_bdn["phong_rui_ro"] = ""
kiem("bỏ model thì ô ngưỡng cũng thôi hiện",
     "nguong" not in {o["ten"] for o in bat_dau.o_cua(_bdn)},
     "— hộp thoại lọc theo đúng danh sách này lúc lưu, nên file không mang ô mồ côi")


# ================= 7. RỔ ĐỘNG — kiểu thứ hai của ô «Chạy trên mã nào» ==========
print(NL + "▸ Rổ động — mỗi rổ phải là MỘT lớp có thật của LEAN")
kiem("mỗi rổ khai một lớp LEAN",
     all(lop for _m, _n, lop, *_ in bat_dau.RO), f"— {len(bat_dau.RO)} rổ")
kiem("không lớp nào trùng",
     len({lop for _m, _n, lop, *_ in bat_dau.RO}) == len(bat_dau.RO),
     "— hai rổ cùng một lớp là một rổ bịa")
kiem("không mã rổ nào trùng",
     len({m for m, *_ in bat_dau.RO}) == len(bat_dau.RO))
# ⚠ `ManualUniverseSelectionModel` CÓ THẬT mà CỐ Ý không khai: nó nhận danh sách mã
# gõ sẵn, tức đúng câu mà kiểu LIST của ô `ma` đã nói. Bày cả hai là bày hai cách nói
# một thứ. Canh ở đây để lần sau ai thấy "thiếu" thì đọc được lý do.
kiem("cố ý KHÔNG có ManualUniverseSelectionModel",
     not any("Manual" in lop for _m, _n, lop, *_ in bat_dau.RO)
     and "ManualUniverseSelectionModel" in inspect.getsource(bat_dau),
     "— và lý do ghi ngay cạnh `RO`, chỗ người sửa sẽ đọc")

print(NL + "▸ HAI KIỂU MỘT Ô — phân biệt bằng HÌNH DẠNG, một chỗ duy nhất")
kiem("list = mã gõ sẵn", bat_dau.ro_cua([{"ma": "SPY", "loai": "equity"}]) is None)
kiem("dict = một rổ", bat_dau.ro_cua({"ro": "qc500"})[2]
     == "QC500UniverseSelectionModel")
kiem("mã rổ lạ thì KHÔNG nhận", bat_dau.ro_cua({"ro": "bia_ra"}) is None)
kiem("None cũng không phải rổ", bat_dau.ro_cua(None) is None)
# ⚠ HỎNG LẶNG: `gt_ro` chỉ rơi về mặc định khi khoá VẮNG, không khi nó RỖNG. Bản đầu
# coi "" như vắng, nên xoá trắng ô «Mã ETF» là nó lặng lẽ thành "SPY" — hộp thoại
# trống trơn mà cỗ máy chạy rổ SPY, và phép soát không có gì để bắt.
kiem("khoá VẮNG thì rơi về mặc định", bat_dau.gt_ro({"ro": "etf"}, "ma_etf") == "SPY")
kiem("khoá RỖNG thì GIỮ rỗng, để soát bắt được",
     bat_dau.gt_ro({"ro": "etf", "ma_etf": ""}, "ma_etf") == "")

print(NL + "▸ Soát rổ — ba chỗ hỏng LẶNG")
_r = core.make_start_step()
_r["ma"] = {"ro": "khong_co_that"}
kiem("mã rổ lạ → LỖI", len(_nang(core.soat_khoi_bat_dau(_r))) == 1,
     "— không thì bộ sinh mã đi nhánh gõ-mã-sẵn với danh sách rỗng, lặng lẽ")
_r["ma"] = {"ro": "etf", "ma_etf": "", "lay": 8}
kiem("rổ ETF mà trống mã ETF → LỖI", _nang(core.soat_khoi_bat_dau(_r)),
     "— LEAN dựng một mã rỗng, chọn ra 0 mã, backtest chạy hết báo 0 lệnh")
_r["ma"] = {"ro": "etf", "ma_etf": "SPY", "lay": -3}
kiem("«lấy mấy mã» ÂM → LỖI", _nang(core.soat_khoi_bat_dau(_r)),
     "— `co[:-3]` cắt từ đuôi nên rổ ra gần như rỗng, không lỗi nào")
_r["ma"] = {"ro": "etf", "ma_etf": "SPY", "lay": 8}
kiem("rổ điền đủ thì sạch", not core.soat_khoi_bat_dau(_r))
# Mấy phép của kiểu LIST (trống, trùng mã, chưa chọn loại) KHÔNG được áp lên rổ —
# rổ không có dòng mã nào để mà trống hay trùng.
kiem("rổ KHÔNG bị báo «chưa chọn mã nào»",
     not any("chưa chọn mã nào" in v["message"]
             for v in core.soat_khoi_bat_dau(_r)))

print(NL + "▸ Soát chéo — rổ cộng cái gì thì vô nghĩa")
_r2 = core.make_start_step()
_r2["ma"] = {"ro": "kim_loai"}
_r2["chia_von"] = "EqualWeightingPortfolioConstructionModel"
_th2 = core.make_lam_step(lam.LAM_TIN_HIEU)
kiem("rổ + «chia danh mục» → CẢNH BÁO",
     any("chống nhau" in v["message"] for v in core.soat_ro_dong(
         [dict(_r2, chay_cho="ca_danh_muc"), _th2])),
     "— chia danh mục cần gõ rõ tên mã, mà rổ đổi theo ngày")
kiem("rổ mà KHÔNG có «Phát tín hiệu» → CẢNH BÁO",
     any("Phát tín hiệu" in v["message"] for v in core.soat_ro_dong([_r2])))
kiem("rổ + sàng từng mã + có tín hiệu thì sạch",
     not core.soat_ro_dong([_r2, _th2]))
kiem("gõ mã sẵn thì phép này không chạm vào",
     not core.soat_ro_dong([core.make_start_step()]))

print(NL + "▸ Thẻ khối phải NÓI RA rổ, không nói chung chung")
_r3 = core.make_start_step()
_r3["ma"] = {"ro": "etf", "ma_etf": "QQQ", "lay": 5}
kiem("thẻ nói mã ETF và số mã lấy", "QQQ" in dong_the(_r3)[0]
     and "5" in dong_the(_r3)[0], f"— {dong_the(_r3)[0]}")
_r3["ma"] = {"ro": "etf", "ma_etf": "QQQ", "lay": 0}
kiem("lấy 0 = cả rổ", "cả rổ" in dong_the(_r3)[0], f"— {dong_the(_r3)[0]}")
_r3["ma"] = {"ro": "bien_dong"}
kiem("rổ có sẵn thì nói tên rổ", "biến động" in dong_the(_r3)[0],
     f"— {dong_the(_r3)[0]}")

print(NL + "▸ Rổ phải SỐNG qua lưu/mở — `chuan_hoa_khoi` dựng lại khối từ đầu")
_r4 = core.make_start_step()
_r4["ma"] = {"ro": "etf", "ma_etf": "QQQ", "lay": 3}
_mo = core.normalize_process({"name": "x", "steps": [_r4]})["steps"][0]
kiem("cả dict rổ còn nguyên", _mo["ma"] == {"ro": "etf", "ma_etf": "QQQ", "lay": 3},
     f"— {_mo['ma']}")
# ⚠ Ô CON của rổ nằm TRONG dict, không thành khoá riêng của khối: đổi sang gõ mã tay
# thì cả câu trả lời cũ đi theo, không để lại một `lay = 3` lơ lửng trong file.
kiem("ô con không rò ra thành khoá của khối",
     "lay" not in _mo and "ma_etf" not in _mo)

print("\n▸ ⚠ Rổ ETF không có dữ liệu trong khoảng → nói TRƯỚC, đừng để chạy rồi đoán")
# ĐÃ DÍNH THẬT. Rổ ETF miễn phí chỉ có đúng mấy NGÀY lẻ (`Data/equity/usa/universes/
# etf/`): SPY hai ngày cuối 2020, QQQ MỘT ngày năm 2011. Backtest không trùm qua
# ngày nào trong đó thì LEAN chọn ra rỗng — chạy xong, không lỗi, không cảnh báo,
# KHÔNG MỘT LỆNH NÀO. Chọn QQQ cho 2020 ra đúng 0 lệnh; đổi sang SPY đúng khoảng
# thì ra 37 lệnh trên FB · GOOGL · GOOG · AAPL, mã do LEAN tự chọn.
kiem("QQQ chỉ có dữ liệu rổ năm 2011",
     bat_dau.ro_etf_trum_khoang("QQQ", "2020-01-01", "2021-03-01")[0] is False)
kiem("SPY trùm được khoảng cuối 2020",
     bat_dau.ro_etf_trum_khoang("SPY", "2020-11-25", "2021-02-01")[0] is True)
kiem("ETF lạ thì KHÔNG BIẾT, không phải không có",
     bat_dau.ro_etf_trum_khoang("ARKK", "2020-01-01", "2021-01-01")[0] is None,
     "— người dùng có thể tự tải dữ liệu rổ về")
_bdr = core.make_start_step()
_bdr["ma"] = {"ro": "etf", "ma_etf": "QQQ", "lay": 8}
_bdr["khoang"] = {"tu": "2020-01-01", "den": "2021-03-01"}
kiem("và `soat` cảnh báo TRƯỚC khi bấm Backtest",
     any(v["severity"] == "warning" and "rỗng" in v["message"]
         for v in core.soat_day_chuyen([_bdr])))

print(NL + "▸ MỘT CỬA khai câu LEAN — hộp thoại BÀY LẠI, không ghép lại")
# Luật nền: Python khai, giao diện chỉ bày. Hai chỗ cùng ghép một câu thì sớm muộn
# chúng tả khác nhau, mà cái khác ấy không gây lỗi nào nên không ai thấy.
# `HopBatDau.tsx` từng tự dựng lại câu này bằng TypeScript (tự quyết `add_*` hay
# `universe_settings`, tự suy ra độ phân giải thật, tự ghép với tên hàm lịch) trong
# khi `ham_lean` nằm ngay đây làm đúng bốn phép ấy — và bản TypeScript từng in
# `Resolution.MINUTE` trong lúc bộ sinh mã viết DAILY. Mấy phép dưới đây là mấy phép
# bài kiểm giao diện từng canh bên TSX, nay đứng ở ĐÚNG MỘT bên cầu nối.
_k = core.make_start_step()
kiem("gõ mã sẵn: đúng MỘT câu", len(bat_dau.khai(_k)) == 1, f"— {bat_dau.khai(_k)}")
_k["nhip"], _k["do_phan_giai"] = "sau_mo_cua", "MINUTE"
kiem("câu ấy đọc độ phân giải NGƯỜI DÙNG chọn",
     "Resolution.MINUTE" in bat_dau.khai(_k)[0],
     "— không phải cột `res` của nhịp, thứ còn sót lại từ trước D-15")
_k["do_phan_giai"] = "DAILY"
kiem("đổi ô là câu đổi theo", "Resolution.DAILY" in bat_dau.khai(_k)[0],
     f"— {bat_dau.khai(_k)[0]}")
# RỔ ĐỘNG đổi CẢ BA: không `add_*` nào, lịch chạy bằng hàm KHÔNG MÃ, và mọc thêm một
# câu `set_universe_selection` — câu quan trọng nhất, mà hộp thoại từng im.
_k["ma"] = {"ro": "etf", "ma_etf": "SPY", "lay": 8}
_kr = bat_dau.khai(_k)
kiem("chọn rổ: HAI câu, không còn một", len(_kr) == 2, f"— {_kr}")
kiem("câu nhịp bỏ `add_*`, độ phân giải đi qua `universe_settings`",
     "add_*" not in _kr[0] and _kr[0].startswith("universe_settings.resolution"),
     f"— {_kr[0]}")
kiem("và lịch chạy bằng hàm KHÔNG MÃ", "after_market_open(so_phut)" in _kr[0],
     "— `self._ma[0]` trên một rổ là IndexError ở dòng đầu `initialize`")
kiem("câu thứ hai là CÂU CỦA RỔ",
     len(_kr) > 1 and _kr[1].startswith("set_universe_selection("), f"— {_kr}")
kiem("mà gõ mã sẵn thì KHÔNG có câu rổ nào thừa ra",
     len(bat_dau.khai(core.make_start_step())) == 1)

print(NL + "▸ ⚠ Hàm viết CHO HỘP THOẠI mà không ai gọi — hỏng LẶNG, bài kiểm vẫn xanh")
# ĐÃ DÍNH THẬT: `lean_ro` nằm trong file này từ đầu, docstring ghi rõ «để hộp thoại
# nói thẳng ra», và CHỈ có bài kiểm gọi nó. Không lỗi, không cảnh báo — chỉ là người
# dùng chọn rổ động xong, dòng khai trong hộp im đúng câu quan trọng nhất. Canh bằng
# chính câu docstring ấy: khai là viết cho hộp thoại thì phải nối thật tới hộp thoại.
_cho_hop = sorted(t for t, h in inspect.getmembers(bat_dau, inspect.isfunction)
                  if "hộp thoại nói thẳng ra" in (h.__doc__ or ""))
kiem("có hàm tự khai là viết cho hộp thoại", len(_cho_hop) >= 2, f"— {_cho_hop}")
_nguon_khai = inspect.getsource(bat_dau.khai)
_bo_roi = [t for t in _cho_hop if f"{t}(" not in _nguon_khai]
kiem("và cửa `khai()` gọi HẾT, không bỏ sót cái nào", not _bo_roi,
     f"— {_bo_roi} viết cho hộp thoại mà hộp thoại không có đường nào tới")
_api = io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "cat_studio", "api.py"), encoding="utf-8").read()
kiem("và `api.py` mở đúng một cửa ra cho giao diện", "bat_dau.khai(" in _api,
     "— hàm đúng mà không có cửa thì giao diện vẫn phải tự ghép lấy")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
