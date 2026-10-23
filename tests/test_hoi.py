"""TỪ ĐIỂN XÁC NHẬN — năm loại câu hỏi, và luật «không bịa gì của LEAN».

LUẬT GỐC của từ điển này: **mỗi đại lượng phải chỉ ra được MỘT thứ có thật của LEAN**
(ô `lean`). Không khai được thì không được có mặt — đó là cách chặn app tự đẻ ra một
bộ máy tính toán thứ hai (D-11). Bài này canh đúng luật ấy, cộng mấy chỗ hỏng LẶNG:

  · cổng KHÔNG có điều kiện thì LUÔN khớp — mọi nhánh dưới nó không bao giờ được thử;
  · đại lượng lạ / thiếu tham số / chỉ báo nhiều đường chưa chọn đường — bộ sinh mã
    không biết viết gì, mà lúc vẽ thì chẳng ai thấy;
  · đại lượng ĐÚNG/SAI đem so lớn-nhỏ — một câu vô nghĩa.

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import core, hoi  # noqa: E402
# ⚠ BÀI NÀY CHỐT TIẾNG VIỆT. Nó soát CHỮ do Python dựng — mặt khối, bảng Vấn đề,
# câu lỗi — mà app nay MẶC ĐỊNH TIẾNG ANH. Không chốt thì nó đọc bản dịch và mọi
# câu khẳng định dưới đây thành vô nghĩa. Bản gốc tiếng Việt cũng là KHOÁ của bảng
# dịch, nên khẳng định bằng tiếng Việt là khẳng định đúng thứ lõi sinh ra.
# Bản tiếng Anh có bài canh riêng: `test_ngon_ngu.py`.
from cat_studio import ngon_ngu  # noqa: E402
ngon_ngu.dat("vi")


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
    return [p["message"] for p in core.soat_khoi_hoi(step) if p["severity"] == sev]


# ================= 1. Luật gốc: không bịa =================
print("\n▸ MỌI đại lượng phải khai được thứ của LEAN đứng sau nó")
thieu = [dl["ma"] for dl in hoi.KHO if not str(dl.get("lean") or "").strip()]
kiem("không đại lượng nào thiếu ô `lean`", not thieu, f"— {thieu}" if thieu else
     f"({len(hoi.KHO)} đại lượng)")

print("\n▸ Mấy thứ ĐÃ BỎ vì chúng bắt app tự tính — không được quay lại")
# `ty_trong_hien_tai` = giá trị giữ ÷ tổng danh mục (ta chia), `so_ma_dang_giu` (ta
# đếm), `so_ngay_da_giu` (ta ghi sổ), `so_nen_da_chay` (LEAN không đếm).
for ma in ("ty_trong_hien_tai", "so_ma_dang_giu", "so_ngay_da_giu", "so_nen_da_chay"):
    co = ma in hoi.BANG_DAI_LUONG
    kiem(f"`{ma}` không có mặt", not co)

print("\n▸ Phép so chỉ có SÁU — mọi phép «nhìn lại» là chỉ báo, không phải phép")
kiem("đúng sáu phép", len(hoi.PHEP_SO) == 6,
     f"— {[m for m, _ in hoi.PHEP_SO]}")
for cam in ("cat_len", "cat_xuong", "tang", "giam"):
    kiem(f"không có phép `{cam}`", cam not in [m for m, _ in hoi.PHEP_SO])
kiem("nhìn lại quá khứ bằng CHỈ BÁO của LEAN",
     all(hoi.dai_luong(m) for m in ("max", "min", "delay")),
     "— MAX · MIN · Delay")

# ================= 2. Năm loại =================
print("\n▸ Năm loại câu hỏi")
kiem("đủ sáu họ", len(hoi.LOAI_HOI) == 6, f"— {list(hoi.LOAI_HOI)}")
# ⚠ ĐÃ ĐỔI LUẬT, và hai dòng kiểm cũ ở đây từng khoá chặt luật cũ: "chỉ THỊ TRƯỜNG
# và DOANH NGHIỆP cho so chéo mã" và "TÀI KHOẢN với LỊCH không có ô mã". Cả hai đều
# là cờ `can_ma`/`hai_ve_ma` viết tay cho CẢ HỌ, mà một cờ cho cả họ thì luôn chỉ là
# xấp xỉ — xem phép kiểm ngay dưới, nó bắt được «Phiên đang mở» nằm trong họ khai
# "không cần mã" trong khi đoạn code của nó là `self.is_market_open(sym)`.
print("\n▸ «Cần mã» suy từ ô `lean`, không phải cờ viết tay")
lech = [d["ma"] for d in hoi.KHO
        if d["can_ma"] != ("sym" in d["lean"] or "sym" in d["lean_dk"])]
kiem("mọi đại lượng khai `can_ma` đúng với đoạn code của nó", not lech, f"— {lech}")
kiem("«Phiên đang mở» CẦN mã", hoi.dai_luong("phien_mo")["can_ma"],
     "— `self.is_market_open(sym)`; họ «Hỏi lịch» từng khai là không cần")
kiem("«Giờ» KHÔNG cần mã", not hoi.dai_luong("gio")["can_ma"])
kiem("«Giá trị N nến TRƯỚC» cần mã", hoi.dai_luong("delay")["can_ma"],
     "— `sym` nằm ở dòng đăng ký chứ không ở biểu thức")
kiem("họ không còn giữ cờ `can_ma`/`hai_ve_ma` nào",
     not any(k in d for d in hoi.LOAI_HOI.values() for k in ("can_ma", "hai_ve_ma")),
     "— bức tường nằm ở chính mấy cờ ấy")
kiem("DOANH NGHIỆP bị tắt kèm LÝ DO",
     isinstance(hoi.LOAI_HOI[hoi.HOI_DOANH_NGHIEP]["tat"], str),
     "— dữ liệu miễn phí chỉ có coarse")

# ================= 3. Khối Hỏi là CỔNG =================
print("\n▸ Khối Hỏi là cổng rẽ nhánh")
for loai in hoi.LOAI_HOI:
    kiem(f"`{loai}` là cổng", core.is_branch_gate(core.make_hoi_step(loai)))
kiem("Nhóm KHÔNG phải cổng", not core.is_branch_gate(core.make_group_step()),
     "— nó có thể đã đặt lệnh rồi mới tới chỗ kiểm")
kiem("Quay về KHÔNG phải cổng", not core.is_branch_gate(core.make_quay_ve_step()))

# ================= 4. Chữ trên thẻ do Python dựng =================
print("\n▸ Chữ trên thẻ")
k = core.make_hoi_step(hoi.HOI_THI_TRUONG, "Tín hiệu mua")
k["dieu_kien"] = [
    core.make_dieu_kien("rsi", "<", 30, tham_so={"n": 14}),
    {"trai": {"ma_dl": "gia"}, "phep": ">",
     "phai": {"ma_dl": "ema", "tham_so": {"n": 20}}},
    {"trai": {"ma_dl": "roc", "ma": "SPY", "tham_so": {"n": 20}}, "phep": ">",
     "phai": {"ma_dl": "roc", "ma": "QQQ", "tham_so": {"n": 20}}},
]
the = core.the_buoc(k)
dong = [d["text"] for d in the["lines"]]
kiem("mỗi điều kiện MỘT dòng", len(dong) == 3,
     "— nhồi một chuỗi dài là thẻ cắt cụt mất vế phải")
kiem("số nguyên không in đuôi .0", dong[0] == "RSI(14) < 30", f"— {dong[0]!r}")
kiem("vế phải là ĐẠI LƯỢNG đọc được", dong[1] == "Giá hiện tại > EMA(20)",
     f"— {dong[1]!r}")
kiem("SO CHÉO MÃ đọc được", dong[2] == "SPY·ROC(20) > QQQ·ROC(20)", f"— {dong[2]!r}")
kiem("huy hiệu nói số điều kiện", "3 điều kiện · VÀ" in the["badges"])

v = core.make_hoi_step(hoi.HOI_VI_THE)
v["dieu_kien"] = [core.make_dieu_kien("dang_giu", "khong")]
kiem("đại lượng ĐÚNG/SAI đọc thành câu",
     core.the_buoc(v)["lines"][0]["text"] == "Đang giữ mã này là SAI")

kiem("khối rỗng nói rõ là rỗng",
     core.the_buoc(core.make_hoi_step(hoi.HOI_LICH))["lines"][0]["text"]
     == "chưa có điều kiện nào")

# ================= 5. Soát ruột =================
print("\n▸ Cổng KHÔNG có điều kiện thì LUÔN khớp")
kiem("khối rỗng → cảnh báo",
     any("LUÔN khớp" in m for m in loi(core.make_hoi_step(hoi.HOI_LICH), "warning")))

print("\n▸ Bốn kiểu hỏng, cả bốn đều im lặng lúc chạy")
x = core.make_hoi_step(hoi.HOI_THI_TRUONG)
x["dieu_kien"] = [{"trai": {"ma_dl": "khong_co_that"}, "phep": ">", "phai": {"so": 1}}]
kiem("đại lượng lạ → lỗi", any("không có đại lượng" in m for m in loi(x)))

x["dieu_kien"] = [{"trai": {"ma_dl": "rsi"}, "phep": ">", "phai": {"so": 30}}]
kiem("thiếu tham số → lỗi", any("thiếu ô" in m for m in loi(x)))

x["dieu_kien"] = [{"trai": {"ma_dl": "bb", "tham_so": {"n": 20, "k": 2}},
                   "phep": ">", "phai": {"so": 1}}]
kiem("chỉ báo nhiều đường chưa chọn đường → lỗi",
     any("nhiều đường" in m for m in loi(x)))

x["dieu_kien"] = [{"trai": {"ma_dl": "gia"}, "phep": "la", "phai": {"so": 1}}]
kiem("phép ĐÚNG/SAI dùng cho đại lượng SỐ → lỗi",
     any("không có" in m for m in loi(x)))

y = core.make_hoi_step(hoi.HOI_VI_THE)
y["dieu_kien"] = [{"trai": {"ma_dl": "dang_giu"}, "phep": ">", "phai": {"so": 1}}]
kiem("đại lượng ĐÚNG/SAI đem so lớn-nhỏ → lỗi",
     any("chỉ trả ĐÚNG/SAI" in m for m in loi(y)))

z = core.make_hoi_step(hoi.HOI_THI_TRUONG)
z["dieu_kien"] = [{"trai": {"so": 5}, "phep": ">", "phai": {"so": 1}}]
kiem("vế trái là con số → lỗi", any("vế trái phải là một đại lượng" in m for m in loi(z)))

print("\n▸ Đúng thì KHÔNG báo gì")
ok = core.make_hoi_step(hoi.HOI_THI_TRUONG)
ok["dieu_kien"] = [core.make_dieu_kien("rsi", "<", 30, tham_so={"n": 14})]
kiem("khối sạch, không lỗi không cảnh báo", not core.soat_khoi_hoi(ok),
     f"— {[p['message'][:40] for p in core.soat_khoi_hoi(ok)]}")

# ================= 6. Sống sót qua lưu/mở =================
print("\n▸ Điều kiện sống sót qua chuẩn hoá")
doc = core.make_process_template("t", [core.make_start_step(), ok])
ra = doc["steps"][1]
kiem("còn nguyên điều kiện", len(ra.get("dieu_kien") or []) == 1)
kiem("còn nguyên tham số",
     (ra["dieu_kien"][0]["trai"].get("tham_so") or {}).get("n") == 14)

# ================= 7. Từ điển gửi qua cầu nối =================
print("\n▸ Từ điển gửi được qua cầu nối")
import json  # noqa: E402
td = hoi.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
kiem("đủ sáu họ", len(td["loai"]) == 6)

# ⚠ LỜI HỨA "với tới được TẤT CẢ". Cái bẫy ở đây không phải quên khai một đại lượng —
# mà khai rồi, nó nằm trong `hoi.py`, bài kiểm nào cũng xanh, nhưng bảng chọn không
# bao giờ bày nó ra, nên với người chơi nó KHÔNG TỒN TẠI. Bản trước đúng như thế: 33
# đại lượng của bốn họ kia không cách nào vào được một dòng điều kiện của họ này.
#
# Nên chốt bằng một cửa DUY NHẤT: `kho`. Bảng chọn bày đúng mảng này (xem
# `test_giao_dien`), nên mọi thứ khai trong từ điển đều tới được tay người dùng.
print("\n▸ ⭐ MỌI đại lượng phải với tới được — không cái nào kẹt lại trong file")
tat_ca = {dl["ma"] for d in hoi.LOAI_HOI.values()
          for _t, ds in d["nhom"] for dl in ds}
trong_kho = {d["ma"] for d in td["kho"]}
ket = sorted(tat_ca - trong_kho)
kiem("kho gửi đi đủ CẢ từ điển", not ket,
     f"— kẹt lại: {ket}" if ket else f"({len(trong_kho)} đại lượng)")
kiem("không cái nào thừa ra ngoài từ điển", not (trong_kho - tat_ca))
thieu_cho = [d["ma"] for d in td["kho"] if not d.get("ho") or not d.get("nhom")]
kiem("cái nào cũng biết chỗ nó đứng trong bảng chọn", not thieu_cho, f"— {thieu_cho}")
la = [d["ho"] for d in td["kho"] if d["ho"] not in {l["ma"] for l in td["loai"]}]
kiem("không cái nào trỏ về một họ không có mặt", not la, f"— {la}")
thieu_dv = [d["ma"] for d in td["kho"]
            if d["kieu"] == hoi.KIEU_SO and not d["don_vi"]]
kiem("đại lượng SỐ nào cũng khai đơn vị", not thieu_dv,
     f"— {thieu_dv}" if thieu_dv else "— để bảng chọn xếp «cùng đơn vị» lên trước")

print("\n▸ GHÉP hai đại lượng — đúng bốn phép LEAN có, và ĐÚNG MỘT TẦNG")
# Vì sao có phép ghép: ví dụ 1 cần «rơi 3% từ đỉnh 60 nến», mà một đại lượng đơn lẻ
# không nói nổi. LEAN khai sẵn bốn phép trong `IndicatorExtensions` — ta bày đúng bốn
# cái ấy, không bịa thêm.
from cat_studio import sinh_ma  # noqa: E402

kiem("đúng bốn phép", len(hoi.PHEP_GHEP) == 4)
kiem("và chúng là Plus · Minus · Times · Over của LEAN",
     {m for m, _n in hoi.PHEP_GHEP} == {"+", "-", "*", "/"})
kiem("từ điển gửi được sang giao diện", len(hoi.tu_dien()["phep_ghep"]) == 4,
     "— không có thì giao diện phải gõ cứng bốn phép, thành hai bản sự thật")


def _ghep(trai_dl, phep, phai, **kw):
    """Một khối Hỏi một dòng, vế trái có ghép. -> (lời soát, dòng mã sinh ra)."""
    h = core.make_hoi_step("hoi_thi_truong")
    dk = core.make_dieu_kien(trai_dl, kw.pop("phep_so", "<="), kw.pop("so", 0.97))
    dk["trai"]["ghep"] = dict(phai, phep=phep)
    h["dieu_kien"] = [dk]
    loi = [v["message"] for v in core.soat_khoi_hoi(h)]
    bd = core.make_start_step()
    bd["ma"] = [{"ma": "SPY", "loai": "equity"}]
    t = core.make_lam_step("lam_tin_hieu")
    st, ed = [bd, h, t], [{"from": bd["id"], "to": h["id"], "port": "out"},
                          {"from": h["id"], "to": t["id"], "port": "out"}]
    kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "Do",
                       "steps": st, "edges": ed})
    dong = next((l.strip() for l in kq["ma"].splitlines()
                 if l.strip().startswith("if (")), "")
    return loi, dong


_loi, _dong = _ghep("gia", "/", {"ma_dl": "max", "tham_so": {"n": 60}})
kiem("«giá / đỉnh 60 nến ≤ 0,97» soát SẠCH", not _loi, f"— {_loi}")
kiem("và sinh ra đúng phép chia ấy",
     "price / self._cb[sym]['max_60'].current.value" in _dong, f"— {_dong}")
# CHIA CHO 0 — LEAN tự quy định: `GetOverIndicatorComposer` trả 0 chứ không nổ. Nếu
# ta sinh phép chia trần thì một nến khối lượng 0 là đứt cả lượt backtest.
kiem("chia có chốt 0 đúng như LEAN làm", "else 0)" in _dong, f"— {_dong}")
_loi2, _dong2 = _ghep("gia", "*", {"ma_dl": "khoi_luong"})
kiem("phép nhân thì KHÔNG chốt gì thêm",
     "else 0" not in _dong2 and " * " in _dong2, f"— {_dong2}")

print("\n▸ Mấy lối ghép SAI phải bị chặn, và nói đúng lý do")
_loi3, _ = _ghep("dang_giu", "+", {"ma_dl": "gia"}, phep_so="la")
kiem("ĐÚNG/SAI không cộng trừ được",
     any("ĐÚNG/SAI" in m and "cộng" in m for m in _loi3), f"— {_loi3}")
_loi4, _ = _ghep("gia", "+", {"ma_dl": "dang_giu"})
kiem("và cũng không cộng ĐÚNG/SAI vào",
     any("ĐÚNG/SAI" in m for m in _loi4), f"— {_loi4}")
_loi5, _dong5 = _ghep("gia", "/", {"so": 0})
kiem("chia cho hằng số 0 → CẢNH BÁO, vì cả vế thành 0 cứng",
     any("chia cho 0" in m for m in _loi5), f"— {_loi5}")
_loi6, _ = _ghep("gia", "?", {"ma_dl": "max", "tham_so": {"n": 60}})
kiem("phép lạ → lỗi", any("phép ghép" in m for m in _loi6), f"— {_loi6}")
# ⚠ MỘT TẦNG. Bộ sinh mã chỉ dịch một tầng, nên tầng thứ hai mà nhận ở đây là nó
# BIẾN MẤT khỏi mã sinh ra — soát sạch mà chạy sai, đúng kiểu hỏng lặng.
_loi7, _dong7 = _ghep("gia", "/", {"ma_dl": "max", "tham_so": {"n": 60},
                                   "ghep": {"phep": "-", "so": 1}})
kiem("ghép hai tầng → lỗi", any("hai tầng" in m for m in _loi7), f"— {_loi7}")
kiem("và bộ sinh mã thật sự BỎ tầng thứ hai — nên lỗi kia không phải cấm vô cớ",
     "- 1" not in _dong7, f"— {_dong7}")

print("\n▸ ⚠ THẺ KHỐI phải NÓI RA phép ghép — bỏ nó đi là thẻ nói dối")
# Nguy hơn một dấu «?», vì nó vẫn đọc trôi chảy: bộ sinh mã viết `giá / đỉnh 60 nến
# ≤ 0,97`, mà thẻ đọc "Giá hiện tại ≤ 0,97" — một câu VÔ LÝ (giá nào dưới 1 đô) nhưng
# không sai cú pháp nào, nên nhìn qua chẳng ai thấy gì. Đúng điều `mo_ta_lam` cảnh báo
# ngay ở đầu: chữ trên thẻ phải tả ĐÚNG thứ bộ sinh mã thật sự viết ra.
for _p, _ten_p in hoi.PHEP_GHEP:
    _dk = core.make_dieu_kien("gia", "<=", 0.97)
    _dk["trai"]["ghep"] = {"phep": _p, "ma_dl": "max", "tham_so": {"n": 60}}
    _chu = core.mo_ta_dieu_kien(_dk)
    kiem(f"thẻ nói ra phép «{_ten_p}»", _p in _chu and "Cao nhất" in _chu, f"— {_chu}")
# Ghép với một CON SỐ cũng phải hiện — và cả khi nó nằm ở vế PHẢI.
_dk = core.make_dieu_kien("gia", ">", 0)
_dk["phai"] = {"ma_dl": "sma", "tham_so": {"n": 200}, "ghep": {"phep": "*", "so": 1.05}}
_chu = core.mo_ta_dieu_kien(_dk)
kiem("vế phải có ghép cũng hiện", "* 1.05" in _chu, f"— {_chu}")

print("\n▸ Ghép phải SỐNG qua lưu/mở — `chuan_hoa_khoi` dựng lại khối từ đầu")
_h = core.make_hoi_step("hoi_thi_truong")
_dk = core.make_dieu_kien("gia", "<=", 0.97)
_dk["trai"]["ghep"] = {"phep": "/", "ma_dl": "max", "tham_so": {"n": 60}}
_h["dieu_kien"] = [_dk]
_lai = core.chuan_hoa_khoi(json.loads(json.dumps(_h)))
kiem("cả phép ghép còn nguyên",
     (_lai["dieu_kien"][0]["trai"] or {}).get("ghep")
     == {"phep": "/", "ma_dl": "max", "tham_so": {"n": 60}},
     f'— {(_lai["dieu_kien"][0]["trai"] or {}).get("ghep")}')

print("\n▸ Giao diện ĐỌC bốn phép từ từ điển, không gõ cứng")
_goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tsx = io.open(os.path.join(_goc, "webui", "src", "components", "HopDieuKien.tsx"),
               encoding="utf-8").read()
kiem("bày `td.phep_ghep`", "td.phep_ghep" in _tsx)
kiem("không gõ cứng nhãn phép nào",
     not any(f"'{n}'" in _tsx for _m, n in hoi.PHEP_GHEP),
     "— thêm phép bên Python là giao diện có ngay, không phải sửa hai chỗ")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
