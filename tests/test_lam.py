"""TỪ ĐIỂN HÀNH ĐỘNG — tám loại việc, và luật «không bịa gì của LEAN».

Cùng luật như `test_hoi.py`: **mỗi khối phải chỉ ra được MỘT hàm có thật của LEAN**
(ô `lean`). Thêm vào đó, bài này canh ĐƯỜNG RANH đã vạch ở đầu `lam.py`:

  · ĐẶT lệnh và HUỶ HẾT lệnh của một mã thì được — mỗi cái là MỘT câu gọi, app không
    phải nhớ gì giữa hai nến;
  · SỬA một lệnh cụ thể (`ticket.Update…`) thì KHÔNG — phải giữ cái ticket qua nhiều
    nến, tức app lại có backend để mà gỡ lỗi (D-11).

Và mấy chỗ hỏng LẶNG: lệnh số lượng 0 hay giá 0 thì LEAN nhận rồi bỏ / nằm trên sàn
mãi không khớp, mà lúc vẽ chẳng ai thấy gì.

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, cai_dat, core, hoi, lam  # noqa: E402

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
    return [p["message"] for p in core.soat_khoi_lam(step) if p["severity"] == sev]


def dong_the(step):
    return [d["text"] for d in core.the_buoc(step)["lines"]]


# ================= 1. Luật gốc: không bịa =================
print("\n▸ MỌI loại hành động phải khai được hàm LEAN đứng sau nó")
thieu = [ma for ma, d in lam.LOAI_LAM.items() if not str(d.get("lean") or "").strip()]
kiem("không loại nào thiếu ô `lean`", not thieu,
     f"— {thieu}" if thieu else f"({len(lam.LOAI_LAM)} loại)")

thieu_ll = [ll for ll, d in lam.LENH_CHO["theo_loai"].items()
            if not str(d.get("lean") or "").strip()]
kiem("từng LOẠI LỆNH CHỜ cũng khai hàm riêng", not thieu_ll, f"— {thieu_ll}")
ds_lean = [d["lean"] for d in lam.LENH_CHO["theo_loai"].values()]
kiem("bảy loại lệnh là BẢY hàm khác nhau", len(set(ds_lean)) == len(ds_lean),
     "— hai loại cùng một hàm là một loại bịa")

print("\n▸ MẪU `lean` phải CHẠY ĐƯỢC, không phải lời khai cho người đọc")
# Bộ sinh mã viết ra ĐÚNG chuỗi này, chỉ thay ô bằng giá trị. Nếu nó chỉ là lời khai
# thì phải có một bộ chuyển đổi ở giữa — và bộ đó sai thì sai ÂM THẦM.
for _ma, _d in lam.LOAI_LAM.items():
    _st = core.make_lam_step(_ma)
    _h = lam.ham_lean(_ma, _st)
    kiem(f"`{_ma}` có mẫu gọi thật", _h.startswith("self.") and _h.endswith(")"),
         f"— {_h}")
    _o_co = {o["ten"] for o in lam.o_cua(_ma, _st)} | {"sym", "gia_tri"}
    _dung = set(re.findall(r"\{(\w+)\}", _h))
    kiem(f"`{_ma}` chỉ điền ô CÓ THẬT", _dung <= _o_co, f"— thừa {_dung - _o_co}")

print("\n▸ ĐƯỜNG RANH: sửa một lệnh cụ thể thì KHÔNG, vì phải nhớ ticket qua nhiều nến")
ca_bo = json.dumps(lam.tu_dien(), ensure_ascii=False).lower()
# ⚠ Viết ĐÚNG KHUÔN snake_case của LEAN. Bản trước canh "cancelorder" liền nhau, nên
# từ ngày ô `lean` đổi sang `cancel_order` là phép kiểm qua tuốt mà chẳng canh gì.
for cam in ("ticket", "update_stop", "update_limit", "update_quantity",
            "cancel_order(", "remove_order"):
    kiem(f"không có `{cam}`", cam not in ca_bo)
kiem("HUỶ HẾT của một mã thì CÓ — một câu, không nhớ gì",
     "cancel_open_orders" in ca_bo)

print("\n▸ Cố ý bỏ: lệnh quyền chọn nhiều chân")
for cam in ("combo", "exerciseoption"):
    kiem(f"không có `{cam}`", cam not in ca_bo)
kiem("và lý do bỏ được ghi lại trong lam.py",
     "ComboMarketOrder" in lam.__doc__ and "chủ ý" in lam.__doc__)

print("\n▸ Ô `tag` là THAM SỐ CỦA LEAN, không phải sáng kiến của ta")
# LEAN có `tag` trên mọi hàm ĐẶT LỆNH, nhưng `Debug`/`Plot`/`Notify` thì không.
co_tag = {ma for ma in lam.LOAI_LAM
          if any(o["ten"] == "tag" for o in lam.o_cua(ma))}
kiem("có `tag` ở đúng năm khối đụng tới lệnh",
     co_tag == {lam.LAM_DAT_TY_TRONG, lam.LAM_LENH_THI_TRUONG, lam.LAM_DONG,
                lam.LAM_LENH_CHO, lam.LAM_HUY_LENH_CHO}, f"— {sorted(co_tag)}")
kiem("KHÔNG có `tag` ở Ghi chú / Vẽ bảng / Báo tin",
     not (co_tag & {lam.LAM_GHI_CHU, lam.LAM_VE_BANG, lam.LAM_BAO_TIN}),
     "— Debug/Plot/Notify của LEAN không nhận tham số ấy")
kiem("`tag` không bắt buộc", not lam.O_TAG["bat_buoc"],
     "— để trống thì bộ sinh mã điền số khối + điều kiện vừa khớp")

print("\n▸ Giá trị vẽ dùng lại ĐÚNG kho đại lượng của khối Hỏi")
# ⚠ Dòng cũ chốt `dai_luong_tu == HOI_THI_TRUONG`: vẽ được RSI mà KHÔNG vẽ được
# «Tổng giá trị danh mục» — thứ ai cũng muốn nhìn. Nay chỉ còn một kho, nên ô này
# chỉ khai "có chọn đại lượng", không khai chọn trong họ nào.
kiem("Vẽ lên bảng có ô chọn đại lượng", lam.VE_BANG["co_dai_luong"] is True)
# ⚠ `>= 68` CHỨ KHÔNG `== 68`. Dòng cũ đóng cứng con số 68, và nó đổ ngay lần đầu
# có người bày thêm chỉ báo — đổ vì bảng DÀI RA, tức đổ vì việc đúng. Một bài kiểm
# đổ khi người ta làm đúng thì lần sau người ta sửa con số cho nó im, chứ không đọc.
# Thứ bài này canh là «ô ấy với tới CẢ NĂM họ», không phải kho dài đúng mấy dòng.
# Còn chuyện kho bị RÚT NGẮN thì `test_du_lean` canh bằng `MOC`, đúng chỗ của nó.
kiem("và nó với tới CẢ kho, không riêng một họ",
     len({d["ho"] for d in hoi.KHO}) == 5 and len(hoi.KHO) >= 68,
     f"— {len(hoi.KHO)} đại lượng, {len({d['ho'] for d in hoi.KHO})} họ")

# ================= 2. Chín loại =================
print("\n▸ Chín loại hành động")
# ⚠ Con số đổi từ 8 lên 9 khi thêm «Phát tín hiệu» — khối mở ra DÂY CHUYỀN của LEAN
# (Universe → Alpha → Portfolio → Risk → Execution) thay cho lối tự đặt lệnh.
kiem("đủ chín", len(lam.LOAI_LAM) == 9, f"— {list(lam.LOAI_LAM)}")
kiem("Ghi chú và Báo tin KHÔNG cần mã",
     not lam.GHI_CHU["can_ma"] and not lam.BAO_TIN["can_ma"],
     "— chúng không đụng vào một mã nào")
kiem("Báo tin bị gắn CẢNH BÁO kèm lý do",
     isinstance(lam.BAO_TIN.get("tat"), str), "— backtest không gửi gì")
kiem("huy hiệu trên thẻ nói luôn «chỉ chạy thật»",
     "chỉ chạy thật" in core.the_buoc(core.make_lam_step(lam.LAM_BAO_TIN))["badges"])

print("\n▸ Hành động KHÔNG phải cổng rẽ nhánh")
for ma in lam.LOAI_LAM:
    kiem(f"`{ma}` không phải cổng", not core.is_branch_gate(core.make_lam_step(ma)),
         "" if ma != lam.LAM_DAT_TY_TRONG else "— nó đã đặt lệnh rồi, trượt lùi là sai")

# ================= 3. Khối mới đã điền sẵn =================
print("\n▸ Khối vừa thả ra đã đọc được thành câu")
for ma in lam.LOAI_LAM:
    st = core.make_lam_step(ma)
    thieu_o = [o["ten"] for o in lam.o_cua(ma) if o["ten"] not in st]
    kiem(f"`{ma}` có đủ ô mặc định", not thieu_o, f"— {thieu_o}" if thieu_o else "")

print("\n▸ Ô thêm chỉ hiện theo loại lệnh đã chọn")
st = core.make_lam_step(lam.LAM_LENH_CHO)
ten_o = [o["ten"] for o in lam.o_cua(lam.LAM_LENH_CHO, st)]
kiem("Giới hạn có ô giá giới hạn, KHÔNG có giá kích hoạt",
     "gia_gh" in ten_o and "gia_kh" not in ten_o, f"— {ten_o}")
st["loai_lenh"] = "stop_limit"
ten_o = [o["ten"] for o in lam.o_cua(lam.LAM_LENH_CHO, st)]
kiem("Dừng giới hạn có CẢ HAI giá", {"gia_gh", "gia_kh"} <= set(ten_o), f"— {ten_o}")
st["loai_lenh"] = "moo"
kiem("Khớp lúc mở cửa không có ô giá nào",
     not [o for o in lam.o_cua(lam.LAM_LENH_CHO, st) if o["ten"].startswith("gia")])
kiem("và hàm LEAN đổi theo",
     lam.ham_lean(lam.LAM_LENH_CHO, st).startswith("self.market_on_open_order"),
     f"— {lam.ham_lean(lam.LAM_LENH_CHO, st)}")

print("\n▸ File cũ thiếu một ô thì rơi về mặc định, không phải di cư gì")
cu = {"kind": core.KIND_ACTION, "id": "x", "type": lam.LAM_DAT_TY_TRONG}
kiem("ô thiếu lấy mặc định của từ điển", core.o_lam(cu, "ty_trong") == 0.3)
kiem("ô có thì lấy của khối", core.o_lam({**cu, "ty_trong": 0.75}, "ty_trong") == 0.75)

# ================= 4. Chữ trên thẻ do Python dựng =================
print("\n▸ Chữ trên thẻ")
p = core.make_lam_step(lam.LAM_DAT_TY_TRONG)
kiem("tỷ trọng in ra PHẦN TRĂM, không in 0.3",
     dong_the(p)[0] == "Đặt tỷ trọng 30%", f"— {dong_the(p)[0]!r}")
p["ty_trong"] = -0.45
p["ban_sach_truoc"] = True
p["tag"] = "vào khống theo RSI"
d = dong_the(p)
kiem("tỷ trọng âm nói rõ là bán khống", d[0] == "Đặt tỷ trọng -45% — bán khống",
     f"— {d[0]!r}")
kiem("bán sạch mã khác là MỘT DÒNG riêng", d[1] == "bán sạch mọi mã KHÁC trước")
kiem("ghi chú lệnh hiện trên thẻ", d[2] == "ghi chú lệnh: «vào khống theo RSI»")
p["ty_trong"] = 0
kiem("tỷ trọng 0 nói rõ là thoát sạch",
     dong_the(p)[0] == "Đặt tỷ trọng 0% — thoát sạch mã này")

q = core.make_lam_step(lam.LAM_LENH_THI_TRUONG)
q["so_luong"] = -100
kiem("số lượng âm đọc thành «Bán»", dong_the(q)[0] == "Bán 100 đơn vị, khớp ngay",
     f"— {dong_the(q)[0]!r}")

dg = core.make_lam_step(lam.LAM_DONG)
dg["pham_vi"] = "tat_ca"
kiem("Đóng tất cả khác Đóng mã này", dong_the(dg)[0] == "Đóng TẤT CẢ mã đang giữ")

mong = {
    "limit": "Giới hạn: mua 100 @ 95.5",
    "stop": "Dừng: mua 100, chạm 90",
    "stop_limit": "Dừng giới hạn: mua 100, chạm 90 -> giới hạn 95.5",
    "lit": "Chạm rồi giới hạn: mua 100, chạm 92 -> giới hạn 95.5",
    "moo": "Khớp lúc MỞ cửa: mua 100",
    "moc": "Khớp lúc ĐÓNG cửa: mua 100",
}
for ll, cau in mong.items():
    c = core.make_lam_step(lam.LAM_LENH_CHO)
    c["loai_lenh"] = ll
    c["so_luong"] = 100
    c.update({"gia_gh": 95.5, "gia_kh": 90, "gia_cham": 92})
    kiem(f"lệnh `{ll}` đọc đủ giá", dong_the(c)[0] == cau, f"— {dong_the(c)[0]!r}")

tr = core.make_lam_step(lam.LAM_LENH_CHO)
tr["loai_lenh"] = "trailing"
tr["so_luong"] = 100
kiem("trượt theo % in ra phần trăm",
     dong_the(tr)[0] == "Dừng trượt: mua 100, trượt 5%", f"— {dong_the(tr)[0]!r}")
tr["truot_theo_pt"] = False
tr["khoang_truot"] = 2.5
kiem("trượt theo tiền in ra tiền",
     dong_the(tr)[0] == "Dừng trượt: mua 100, trượt 2.5 tiền", f"— {dong_the(tr)[0]!r}")

v = core.make_lam_step(lam.LAM_VE_BANG)
v["gia_tri"] = {"ma_dl": "rsi", "tham_so": {"n": 14}}
v["ten_duong"] = "RSI 14"
kiem("Vẽ bảng dùng lại đúng cách đọc đại lượng của khối Hỏi",
     dong_the(v)[0] == "Vẽ RSI(14)", f"— {dong_the(v)[0]!r}")
kiem("tên bảng và tên đường ở dòng sau",
     dong_the(v)[1] == "bảng «Chỉ báo» · đường «RSI 14»", f"— {dong_the(v)[1]!r}")

g = core.make_lam_step(lam.LAM_GHI_CHU)
kiem("Ghi chú trống nói rõ bộ sinh mã sẽ điền",
     dong_the(g)[0] == "Debug — câu để bộ sinh mã điền", f"— {dong_the(g)[0]!r}")
g["muc"] = "quit"
g["cau"] = "hết vốn"
kiem("DỪNG HẲN đọc ra đúng chữ ấy", dong_the(g)[0] == "DỪNG HẲN: «hết vốn»",
     f"— {dong_the(g)[0]!r}")

print("\n▸ Hành động nằm TRONG một Nhóm cũng đọc được")
n = core.make_group_step("Vào lệnh")
n["actions"] = [core.make_lam_step(lam.LAM_DAT_TY_TRONG),
                core.make_lam_step(lam.LAM_HUY_LENH_CHO)]
kiem("mỗi hành động một dòng",
     dong_the(n) == ["Đặt tỷ trọng 30%", "Huỷ hết lệnh chờ của mã này"],
     f"— {dong_the(n)}")

# ================= 5. Soát ruột: mấy chỗ hỏng LẶNG =================
print("\n▸ Số lượng 0 — LEAN nhận rồi bỏ, sơ đồ chạy mà chẳng có lệnh nào")
z = core.make_lam_step(lam.LAM_LENH_THI_TRUONG)
z["so_luong"] = 0
kiem("→ lỗi", any("số lượng 0" in m for m in loi(z)))
z["so_luong"] = "ba trăm"
kiem("số lượng không phải số → lỗi", any("không phải một con số" in m for m in loi(z)))

print("\n▸ Giá 0 — lệnh nằm trên sàn mãi không khớp, mà không ai báo")
c = core.make_lam_step(lam.LAM_LENH_CHO)
c["so_luong"] = 100
kiem("giá giới hạn 0 → lỗi", any("Giá giới hạn phải lớn hơn 0" in m for m in loi(c)))
c["gia_gh"] = 95.5
kiem("điền giá rồi thì sạch", not core.soat_khoi_lam(c),
     f"— {[x['message'][:50] for x in core.soat_khoi_lam(c)]}")
c["loai_lenh"] = "khong_co_that"
kiem("loại lệnh lạ → lỗi", any("không có loại lệnh" in m for m in loi(c)))

print("\n▸ Vẽ lên bảng mà chưa chọn đại lượng → bộ sinh mã không biết viết gì")
v0 = core.make_lam_step(lam.LAM_VE_BANG)
kiem("khối mới → lỗi, và nói đúng là CHƯA CHỌN",
     any("chưa chọn" in m for m in loi(v0)), f"— {loi(v0)}")
# Và nó gọi ĐÚNG TÊN ô, lấy từ từ điển — không phải "đại lượng" chung chung, vì giờ
# có hai khối mang ô đại lượng và hai ô ấy tên khác nhau.
kiem("gọi đúng tên ô «Giá trị vẽ»",
     any("giá trị vẽ" in m for m in loi(v0)), f"— {loi(v0)}")
# ⚠ ĐỔI LUẬT: trước đây đại lượng của HỌ khác bị chối thẳng. Nay chỉ còn một kho,
# nên `dang_giu` được nhận — và bị chối vì LÝ DO THẬT: nó trả ĐÚNG/SAI, mà `Plot`
# của LEAN cần một con số. Lý do đúng thì người đọc còn biết phải làm gì.
v0["gia_tri"] = {"ma_dl": "dang_giu"}
kiem("đại lượng ĐÚNG/SAI → lỗi, và nói đúng vì sao",
     any("ĐÚNG/SAI" in m for m in loi(v0)), f"— {loi(v0)}")
v0["gia_tri"] = {"ma_dl": "tong_gia_tri"}
kiem("vẽ «Tổng giá trị danh mục» → KHÔNG còn lỗi", not loi(v0),
     "— họ Tài khoản, trước đây không vẽ được")
v0["gia_tri"] = {"ma_dl": "bb", "tham_so": {"n": 20, "k": 2}}
kiem("chỉ báo nhiều đường chưa chọn đường → lỗi",
     any("nhiều đường" in m for m in loi(v0)))
v0["gia_tri"] = {"ma_dl": "rsi"}
kiem("thiếu tham số → lỗi", any("thiếu ô" in m for m in loi(v0)))

print("\n▸ Báo tin: cảnh báo backtest + ô gửi tới để trống")
b = core.make_lam_step(lam.LAM_BAO_TIN)
kiem("cảnh báo «backtest KHÔNG gửi gì»",
     any("Backtest KHÔNG gửi gì" in m for m in loi(b, "warning")))
kiem("thiếu nơi gửi → lỗi", any("Gửi tới còn trống" in m for m in loi(b)))

print("\n▸ DỪNG HẲN phải nói rõ hậu quả")
gq = core.make_lam_step(lam.LAM_GHI_CHU)
gq["muc"] = "quit"
kiem("→ cảnh báo", any("thôi chạy" in m for m in loi(gq, "warning")))
kiem("Ghi chú thường KHÔNG báo gì",
     not core.soat_khoi_lam(core.make_lam_step(lam.LAM_GHI_CHU)),
     "— câu để trống là chuyện bình thường")

print("\n▸ Đòn bẩy: LEAN từ chối mà không báo")
dp = core.make_lam_step(lam.LAM_DAT_TY_TRONG)
dp["ty_trong"] = 1.5
kiem("tỷ trọng 150% → cảnh báo", any("vượt 100%" in m for m in loi(dp, "warning")))

print("\n▸ Đúng thì KHÔNG báo gì")
for ma in (lam.LAM_DAT_TY_TRONG, lam.LAM_DONG, lam.LAM_HUY_LENH_CHO):
    kiem(f"`{ma}` khối mới đã sạch", not core.soat_khoi_lam(core.make_lam_step(ma)),
         f"— {[x['message'][:40] for x in core.soat_khoi_lam(core.make_lam_step(ma))]}")

print("\n▸ Khối Hỏi và khối Làm không soát lẫn nhau")
kiem("soat_khoi_lam bỏ qua khối Hỏi",
     not core.soat_khoi_lam(core.make_hoi_step(hoi.HOI_VI_THE)))
kiem("soat_khoi_hoi bỏ qua khối Làm",
     not core.soat_khoi_hoi(core.make_lam_step(lam.LAM_DONG)))

# ================= 6. Sống sót qua lưu/mở =================
print("\n▸ Ô của khối Làm sống sót qua chuẩn hoá")
doc = core.make_process_template("t", [core.make_start_step(), v, p])
ra_v, ra_p = doc["steps"][1], doc["steps"][2]
kiem("giá trị vẽ còn nguyên", (ra_v.get("gia_tri") or {}).get("ma_dl") == "rsi")
kiem("tham số của nó còn nguyên",
     (ra_v["gia_tri"].get("tham_so") or {}).get("n") == 14)
kiem("tên đường còn nguyên", ra_v.get("ten_duong") == "RSI 14")
kiem("ô tích False không bị mất", ra_p.get("ban_sach_truoc") is True)

# ================= 7. Từ điển gửi qua cầu nối =================
print("\n▸ ⭐ «Phát tín hiệu» — khối mở ra nửa kia của LEAN")
# Dây chuyền `Alpha → PortfolioConstruction → Risk → Execution` BẮT ĐẦU từ insight.
# Khối này là chỗ cây quyết định đổ ra insight, và nhờ nó mà ba thứ ta từng từ chối
# (thoát theo hạn, chia đều 1/N, trailing stop) thành khai báo của LEAN chứ không
# phải sổ sách của app.
th = lam.LOAI_LAM[lam.LAM_TIN_HIEU]
kiem("nằm ở nhóm riêng", th["nhom"] == lam.NHOM_TIN_HIEU,
     "— nó KHÔNG đặt lệnh, nên không thuộc nhóm Lệnh")
kiem("cần mã", th["can_ma"])
kiem("có ô hướng và ô hạn",
     {"huong", "han"} <= {o["ten"] for o in th["o"]},
     f"— {sorted(o['ten'] for o in th['o'])}")
# ⚠ HƯỚNG phải đi qua `theo_loai`: mọi ô đều qua `_lit()` thành literal Python, nên
# nhét `InsightDirection.{huong}` vào mẫu sinh ra `InsightDirection.'UP'` — sai cú
# pháp, và chỉ lộ ra lúc LEAN nạp file. Đã dính thật.
kiem("mỗi hướng một câu LEAN riêng", set(th["theo_loai"]) == {"UP", "DOWN", "FLAT"})
hong = [h for h, v in th["theo_loai"].items()
        if f"InsightDirection.{h}" not in v["lean"] or "{huong}" in v["lean"]]
kiem("và không câu nào còn nhét `{huong}` vào mẫu", not hong, f"— {hong}")
kiem("dùng `emit_insights`, không dựng lớp Alpha nào",
     all("self.emit_insights(" in v["lean"] for v in th["theo_loai"].values()),
     "— `EmitInsights` là phương thức công khai của QCAlgorithm, gọi thẳng từ on_data")

print("\n▸ Từ điển gửi được qua cầu nối")
td = lam.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
kiem("đủ chín loại", len(td["loai"]) == 9)
kiem("mỗi loại có ô", all(l["o"] for l in td["loai"]))
kiem("mỗi loại khai luôn hàm LEAN cho hộp thoại nói thẳng ra",
     all(l["lean"] for l in td["loai"]))

print("\n▸ ⚠ TRỌNG SỐ — khe thứ bảy của `Insight.Price`, bỏ trống là 0 LỆNH lặng thinh")
# ĐÃ DÍNH THẬT, và dính TỪ TRƯỚC: bảng «Chia vốn» đã bày `InsightWeighting...` trong
# khi KHÔNG khối nào đặt được `weight`. Model ấy hỏi `insight.weight is not None` để
# quyết có dựng mục tiêu hay không, nên weight rỗng = nó bỏ qua MỌI tín hiệu =
# backtest chạy hết, không lỗi, không một lệnh nào.
kiem("khe `weight` đứng thứ 7 trong chữ ký thật của Insight.Price",
     lam.INSIGHT_THAM_SO.index("weight") == 6,
     f"— {lam.INSIGHT_THAM_SO}")
_th = lam.TIN_HIEU
kiem("khối Phát tín hiệu có ô đại lượng", _th.get("co_dai_luong") is True)
kiem("ô ấy tên «Trọng số»", _th.get("nhan_dai_luong") == "Trọng số")
kiem("và nó NHẬN được một con số", _th.get("dai_luong_so") is True,
     "— không thì mọi sơ đồ buộc phải xếp hạng")
kiem("mặc định là SỐ 1, không phải rỗng", _th.get("gia_tri_mac_dinh") == {"so": 1},
     "— rỗng thì `_ve_py` ra 0, mà trọng số 0 là không vị thế nào")
_moi = core.make_lam_step(lam.LAM_TIN_HIEU)
kiem("khối vừa thả ra đã có trọng số 1", _moi.get("gia_tri") == {"so": 1})
kiem("và khối mới KHÔNG bị soát bắt lỗi", not core.soat_khoi_lam(_moi),
     f"— {[v['message'][:60] for v in core.soat_khoi_lam(_moi)]}")
# ⚠ CANH VỊ TRÍ KHE, KHÔNG CANH SỐ CHỮ `None`. Dòng cũ chốt `count("None") == 3`,
# tức nó canh ĐÚNG MỘT hình: ba khe trống rồi tới trọng số. Thế là lần đầu có người
# điền hai khe ấy (magnitude · confidence, để mở ba model chia vốn) thì nó đổ — đổ
# vì việc đúng, và lời nó nói («điền tới khe trọng số») thì vẫn đang đúng.
#
# Thứ cần canh là TỪNG KHE RƠI ĐÚNG CHỖ theo `INSIGHT_THAM_SO` — chữ ký thật của
# `Insight.price`. Khe lệch một bậc là LEAN nhận confidence làm magnitude: không nổ,
# không báo, chỉ ra tỷ trọng sai.
for _h, _v in _th["theo_loai"].items():
    _args = [x.strip() for x in
             _v["lean"].split("Insight.price(", 1)[1].rsplit("))", 1)[0].split(",")]
    _cho = {t: i for i, t in enumerate(lam.INSIGHT_THAM_SO)}
    kiem(f"câu LEAN hướng {_h} — đủ bảy khe của Insight.price",
         len(_args) == 7, f"— {len(_args)}: {_args}")
    for _khe, _dau in (("magnitude", "{do_lon}"), ("confidence", "{do_tin}"),
                       ("weight", "{gia_tri}")):
        _i = _cho[_khe]
        kiem(f"   hướng {_h}: khe {_khe} (thứ {_i + 1}) = {_dau}",
             _i < len(_args) and _args[_i] == _dau,
             f"— đang là {_args[_i] if _i < len(_args) else '(thiếu)'}")

print("\n▸ ⚠ Mọi loại việc phải ĐỌC RA ĐƯỢC trên thẻ khối — không loại nào là dấu «?»")
# ĐÃ DÍNH THẬT, và người dùng thấy trước tôi: `mo_ta_lam` là BẢNG TRA, mỗi loại một
# câu viết tay. Thêm loại thứ chín («Phát tín hiệu») mà quên thêm nhánh cho nó, thế là
# cả ba khối trên sơ đồ vd1 hiện đúng một dấu hỏi — không lỗi, không cảnh báo, chỉ là
# thẻ không nói gì. Bảng tra nào cũng có bẫy này, nên phải quét CẢ bảng.
_cham_hoi = []
for _ma in lam.LOAI_LAM:
    _d = core.mo_ta_lam(core.make_lam_step(_ma))
    if not _d or _d == ["?"] or any("?" == str(x).strip() for x in _d):
        _cham_hoi.append(_ma)
kiem(f"quét cả {len(lam.LOAI_LAM)} loại việc", len(lam.LOAI_LAM) == 9)
kiem("không loại nào ra dấu «?»", not _cham_hoi, f"— {_cham_hoi}")
# Và mấy ô cầm lái phải ĐỔI được câu, không thì câu ấy chỉ là chữ trang trí.
_f = core.make_lam_step(lam.LAM_TIN_HIEU)
_f["huong"] = "FLAT"
kiem("đổi hướng là đổi câu",
     core.mo_ta_lam(_f) != core.mo_ta_lam(core.make_lam_step(lam.LAM_TIN_HIEU)),
     f"— {core.mo_ta_lam(_f)}")
_h15 = core.mo_ta_lam(core.make_lam_step(lam.LAM_TIN_HIEU))[0]
kiem("«giữ tối đa 15 ngày» chứ không phải 1500",
     "15 ngày" in _h15, f"— {_h15}")

print("\n▸ Nhãn ô đại lượng do TỪ ĐIỂN nói, giao diện không gõ cứng")
# ĐÃ DÍNH THẬT: `HopHanhDong.tsx` gõ cứng "Giá trị vẽ", nên khối Phát tín hiệu vừa
# thêm ô «Trọng số» là hộp thoại gọi nó bằng tên của khối khác. Cùng họ với chỗ
# `sinh_ma` gõ cứng `LAM_VE_BANG` — một tên khối nằm trong mã dùng chung.
_co_dl = [d for d in lam.LOAI_LAM.values() if d.get("co_dai_luong")]
kiem("có từ hai khối mang ô đại lượng — nên nhãn KHÔNG thể là một", len(_co_dl) >= 2)
kiem("khối nào cũng khai nhãn riêng",
     all(d.get("nhan_dai_luong") for d in _co_dl),
     f"— {[d['nhan'] for d in _co_dl if not d.get('nhan_dai_luong')]}")
kiem("hai nhãn khác nhau",
     len({d["nhan_dai_luong"] for d in _co_dl}) == len(_co_dl))
_hhd = io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "webui", "src", "components", "HopHanhDong.tsx"),
    encoding="utf-8").read()
kiem("giao diện đọc `nhan_dai_luong`", "nhan_dai_luong" in _hhd)
_go_cung = [d["nhan_dai_luong"] for d in _co_dl
            if f"\"{d['nhan_dai_luong']}\"" in _hhd
            or f"'{d['nhan_dai_luong']}'" in _hhd]
kiem("và KHÔNG gõ cứng nhãn nào", not _go_cung, f"— {_go_cung}")
kiem("bộ sinh mã cũng theo từ điển, không theo tên khối",
     "co_dai_luong" in io.open(os.path.join(os.path.dirname(os.path.dirname(
         os.path.abspath(__file__))), "cat_studio", "sinh_ma.py"),
         encoding="utf-8").read())

print("\n▸ ⚠ Bảng «Chia vốn» chỉ được bày model mà khối VẼ ĐƯỢC nuôi")
# Hàng rào cho cả họ: ai thêm một model chia vốn vào bảng mà khe nó đọc chưa ai điền
# thì bài này đổ — chứ không phải người dùng chọn vào rồi ngồi đoán vì sao 0 lệnh.
_khe_dien = set()
for _i, _ten in enumerate(lam.INSIGHT_THAM_SO):
    for _v in _th["theo_loai"].values():
        _args = _v["lean"].split("Insight.price(", 1)[-1]
        # Tách thô theo dấu phẩy ở tầng ngoài là đủ: mẫu không có dấu phẩy lồng nào
        # ngoài `timedelta(days=…)`, mà cái ấy không có phẩy.
        _ds = [x.strip() for x in _args.rsplit("))", 1)[0].split(",")]
        if _i < len(_ds) and _ds[_i] not in ("None", ""):
            _khe_dien.add(_ten)
kiem("khe đã có người điền", "weight" in _khe_dien, f"— {sorted(_khe_dien)}")
_nuoi_duoc = _khe_dien | {""}      # "" = model không đọc khe nào, luôn chạy được
_chua_nuoi = [m for m, _n in bat_dau.CHIA_VON
              if m and bat_dau.CHIA_VON_DOC.get(m, "?") not in _nuoi_duoc]
kiem("mọi model đang bày đều có khe được nuôi", not _chua_nuoi,
     f"— {_chua_nuoi} đọc khe chưa ai điền")
kiem("và mỗi model đang bày đều khai nó đọc khe nào",
     all(m in bat_dau.CHIA_VON_DOC for m, _n in bat_dau.CHIA_VON if m))

print("\n▸ ⚠ Hai trạm kia — «Phòng rủi ro» và «Đặt lệnh» — mắc bệnh KHÁC")
# Cùng một hậu quả (chọn vào, chạy xong, không tác dụng, không một lời), khác nguyên
# nhân. `CHIA_VON` chết vì ĐỌC một khe của `Insight` mà không khối nào đặt. Hai trạm
# này không đọc khe nào — chúng đọc trạng thái danh mục, thứ LEAN tự giữ. Chúng chết
# vì THAM SỐ KHỞI TẠO không ai truyền:
#   · `StandardDeviationExecutionModel()` mặc định `resolution=Resolution.MINUTE`,
#     mà sơ đồ nhịp NGÀY thì `CreateConsolidator` ném ngay nến đầu. ĐÃ CHẠY THẬT:
#     0 lệnh (câu lỗi chỉ nằm trong nhật ký, bảng Kết quả nói «0 lệnh, lãi 0%»);
#     truyền đúng độ phân giải thì 6 lệnh.
#   · Bốn model phòng rủi ro đều có một ngưỡng; không truyền thì chúng chạy ở 5%
#     mặc định của LEAN, trong khi nhãn hứa «theo %» mà hộp không có ô % nào.
_khong_khai = [m for m, _n, *_ in bat_dau.PHONG_RUI_RO
               if m and m not in bat_dau.PHONG_RUI_RO_DOC]
_khong_khai += [m for m, _n in bat_dau.DAT_LENH
                if m and m not in bat_dau.DAT_LENH_DOC]
kiem("mỗi model đang bày đều khai nó ĐỌC/CẦN cái gì", not _khong_khai,
     f"— {_khong_khai}")
# ⚠ ĐỌC CỜ, KHÔNG DÒ CHỮ. Bản đầu của phép này dò chuỗi «CHƯA ai nuôi» trong dòng
# khai, và lúc tôi ép thử bằng cách bày `SpreadExecutionModel` ra thì bài kiểm XANH —
# dòng khai của nó nói lý do bằng chữ khác. Nay phần đầu của mỗi dòng khai là một
# `bool`, nên không có cách nào nói lý do mà lọt.
_chua_ai_nuoi = [m for m, _n, *_ in bat_dau.PHONG_RUI_RO
                 if m and not bat_dau.PHONG_RUI_RO_DOC[m][0]]
_chua_ai_nuoi += [m for m, _n in bat_dau.DAT_LENH
                  if m and not bat_dau.DAT_LENH_DOC[m][0]]
kiem("và không model nào tự khai «chưa nuôi được» mà vẫn bày", not _chua_ai_nuoi,
     f"— {_chua_ai_nuoi}")
_co_ly_do = all(str(v[1]).strip() for v in list(bat_dau.PHONG_RUI_RO_DOC.values())
                + list(bat_dau.DAT_LENH_DOC.values()))
kiem("và dòng khai nào cũng kèm LÝ DO, không phải cờ trống", _co_ly_do)
_thieu_nguong = [m for m, _n, th in bat_dau.PHONG_RUI_RO
                 if m and "nguong" not in {o["ten"] for o in th}]
kiem("model phòng rủi ro nào cũng có Ô NGƯỠNG của riêng nó", not _thieu_nguong,
     f"— {_thieu_nguong} bày ra mà không có ô nào điền ngưỡng, tức chạy ở 5% ngầm")

# ⚠ HÀNG RÀO CHO CẢ HỌ: con số NGẦM. Mọi con số trong câu LEAN một trạm sinh ra phải
# nói được ở chỗ người dùng THẤY — hoặc nằm trong nhãn của model, hoặc là giá trị một
# ô. Thêm một model rồi gọi nó với `20000` gõ cứng là bài này đổ, chứ không phải chờ
# ai đi đọc mã nguồn LEAN mới biết con số ấy từ đâu ra.
_so = re.compile(r"\d+(?:\.\d+)?")
_ngam = []
for _bang, _ten_o in ((bat_dau.CHIA_VON, "chia_von"),
                      (bat_dau.PHONG_RUI_RO, "phong_rui_ro"),
                      (bat_dau.DAT_LENH, "dat_lenh")):
    for _m, _nhan, *_th in _bang:
        if not _m:
            continue
        _gt = {_ten_o: _m}
        _noi_ra = {_nhan} | {str(o["mac_dinh"]) for o in bat_dau.o_cua(_gt)}
        for _cau in bat_dau.lean_day_chuyen(_gt):
            for _s in _so.findall(_cau):
                if not any(_s in x for x in _noi_ra):
                    _ngam.append((_m, _s))
kiem("không con số NGẦM nào trong câu LEAN của ba trạm", not _ngam,
     f"— {_ngam} không nằm trong nhãn model, cũng không là giá trị ô nào")

# ĐÚNG CÁI LỖI ĐÃ CHẠY THẬT: độ phân giải phải đi theo NHỊP của sơ đồ, không đóng
# cứng. Đổi nhịp mà câu LEAN đứng yên thì nó lại là `Resolution.MINUTE` trên dữ liệu
# ngày — tức ném ngoại lệ ở nến đầu, mà bảng Kết quả chỉ nói «0 lệnh».
_gt_std = {"dat_lenh": "StandardDeviationExecutionModel", "nhip": "ngay"}
_cau_std = " ".join(bat_dau.lean_day_chuyen(_gt_std))
kiem("câu `set_execution` mang độ phân giải THẬT của sơ đồ",
     "Resolution.DAILY" in _cau_std, f"— {_cau_std}")
_gt_std["nhip"] = "phut"
kiem("và đổi nhịp là nó đổi theo",
     "Resolution.MINUTE" in " ".join(bat_dau.lean_day_chuyen(_gt_std)),
     "— đóng cứng một độ phân giải là chết lặng trên mọi nhịp khác")
_gt_ng = {"phong_rui_ro": "TrailingStopRiskManagementModel", "nguong": 0.17}
kiem("ngưỡng người dùng gõ đi THẲNG vào câu LEAN",
     "(0.17)" in " ".join(bat_dau.lean_day_chuyen(_gt_ng)),
     f"— {bat_dau.lean_day_chuyen(_gt_ng)}")
_ma_sinh = io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(
    __file__))), "cat_studio", "sinh_ma.py"), encoding="utf-8").read()
kiem("và bộ sinh mã KHÔNG tự ghép lại ba câu ấy",
     "set_risk_management" not in _ma_sinh and "set_execution" not in _ma_sinh,
     "— chỗ tự ghép `{ham}({lop}())` chính là chỗ hai lỗi trên mọc ra")

print("\n▸ ⚠ Ô `chon` không được là một CHUỖI bị xé thành từng chữ")
# ĐÃ DÍNH THẬT, hai lần, cùng một kiểu: `_o(ten, nhan, kieu, mac_dinh, don_vi,
# goi_y, chon)` — đếm nhầm một chỗ trống là câu gợi ý trôi sang khe `chon`, rồi
# `list(chon)` xé nó thành ['H','ế','t',...]. Đơn vị mất, gợi ý mất, mà build
# vẫn sạch và hộp thoại vẫn mở — hỏng LẶNG. Ô «Giữ tối đa» của «Phát tín hiệu»
# đã nằm nguyên như thế. Quét ĐỆ QUY cả bốn từ điển, nên bẫy này không mọc lại
# được ở bất cứ khối nào, kể cả ô con trong `theo_loai` hay trong rổ.
def _moi_chon(x, duong=""):
    """Mọi khoá `chon` ở BẤT CỨ độ sâu nào -> (đường dẫn, giá trị)."""
    if isinstance(x, dict):
        for k, v in x.items():
            if k == "chon":
                yield f"{duong}.{k}", v
            else:
                yield from _moi_chon(v, f"{duong}.{k}")
    elif isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            yield from _moi_chon(v, f"{duong}[{i}]")


_xau = []
_dem = 0
for _ten_td, _td in (("HÀNH ĐỘNG", lam.tu_dien()), ("XÁC NHẬN", hoi.tu_dien()),
                     ("BẮT ĐẦU", bat_dau.tu_dien()), ("CÀI ĐẶT", cai_dat.tu_dien())):
    for _duong, _chon in _moi_chon(_td, _ten_td):
        _dem += 1
        for _c in _chon:
            if isinstance(_c, str) and len(_c) <= 1:
                _xau.append(f"{_duong} = {_chon[:6]}…")
                break
kiem(f"quét {_dem} ô `chon` trong bốn từ điển", _dem > 20)
kiem("không ô nào là chuỗi bị xé thành chữ", not _xau, f"— {_xau}")

print("\n▸ Ô số của «Phát tín hiệu» — đơn vị và gợi ý phải về ĐÚNG khe của nó")
_han = [o for o in lam.TIN_HIEU["o"] if o["ten"] == "han"][0]
kiem("đơn vị là «ngày»", _han["don_vi"] == "ngày")
kiem("gợi ý nói LEAN tự bỏ tín hiệu", "LEAN" in _han["goi_y"])
kiem("ô số thì KHÔNG có danh sách chọn", not _han["chon"])

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
