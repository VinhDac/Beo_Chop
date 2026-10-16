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

from cat_studio import core, hoi, lam  # noqa: E402

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
kiem("Vẽ lên bảng trỏ về nhóm Hỏi thị trường",
     lam.VE_BANG["dai_luong_tu"] == hoi.HOI_THI_TRUONG,
     "— hai kho thì sớm muộn lệch nhau")

# ================= 2. Tám loại =================
print("\n▸ Tám loại hành động")
kiem("đủ tám", len(lam.LOAI_LAM) == 8, f"— {list(lam.LOAI_LAM)}")
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
     any("chưa chọn đại lượng" in m for m in loi(v0)), f"— {loi(v0)}")
v0["gia_tri"] = {"ma_dl": "dang_giu"}
kiem("đại lượng của nhóm KHÁC → lỗi", any("không có đại lượng" in m for m in loi(v0)),
     "— `dang_giu` thuộc nhóm Vị thế")
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
print("\n▸ Từ điển gửi được qua cầu nối")
td = lam.tu_dien()
kiem("đóng gói được thành JSON", isinstance(json.dumps(td, ensure_ascii=False), str))
kiem("đủ tám loại", len(td["loai"]) == 8)
kiem("mỗi loại có ô", all(l["o"] for l in td["loai"]))
kiem("mỗi loại khai luôn hàm LEAN cho hộp thoại nói thẳng ra",
     all(l["lean"] for l in td["loai"]))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
