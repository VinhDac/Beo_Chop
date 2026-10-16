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
thieu = [f"{loai}/{dl['ma']}" for (loai, _m), dl in hoi.BANG_DAI_LUONG.items()
         if not str(dl.get("lean") or "").strip()]
kiem("không đại lượng nào thiếu ô `lean`", not thieu, f"— {thieu}" if thieu else
     f"({len(hoi.BANG_DAI_LUONG)} đại lượng)")

print("\n▸ Mấy thứ ĐÃ BỎ vì chúng bắt app tự tính — không được quay lại")
# `ty_trong_hien_tai` = giá trị giữ ÷ tổng danh mục (ta chia), `so_ma_dang_giu` (ta
# đếm), `so_ngay_da_giu` (ta ghi sổ), `so_nen_da_chay` (LEAN không đếm).
for ma in ("ty_trong_hien_tai", "so_ma_dang_giu", "so_ngay_da_giu", "so_nen_da_chay"):
    co = any(m == ma for _loai, m in hoi.BANG_DAI_LUONG)
    kiem(f"`{ma}` không có mặt", not co)

print("\n▸ Phép so chỉ có SÁU — mọi phép «nhìn lại» là chỉ báo, không phải phép")
kiem("đúng sáu phép", len(hoi.PHEP_SO) == 6,
     f"— {[m for m, _ in hoi.PHEP_SO]}")
for cam in ("cat_len", "cat_xuong", "tang", "giam"):
    kiem(f"không có phép `{cam}`", cam not in [m for m, _ in hoi.PHEP_SO])
kiem("nhìn lại quá khứ bằng CHỈ BÁO của LEAN",
     all(hoi.dai_luong("hoi_thi_truong", m) for m in ("max", "min", "delay")),
     "— MAX · MIN · Delay")

# ================= 2. Năm loại =================
print("\n▸ Năm loại câu hỏi")
kiem("đủ năm", len(hoi.LOAI_HOI) == 5, f"— {list(hoi.LOAI_HOI)}")
kiem("chỉ THỊ TRƯỜNG và DOANH NGHIỆP cho so chéo mã",
     {k for k, v in hoi.LOAI_HOI.items() if v["hai_ve_ma"]}
     == {hoi.HOI_THI_TRUONG, hoi.HOI_DOANH_NGHIEP})
kiem("TÀI KHOẢN và LỊCH không có ô mã",
     not hoi.LOAI_HOI[hoi.HOI_TAI_KHOAN]["can_ma"]
     and not hoi.LOAI_HOI[hoi.HOI_LICH]["can_ma"],
     "— chúng hỏi về toàn bộ, không về một mã")
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
kiem("đủ năm loại", len(td["loai"]) == 5)
kiem("mỗi loại có nhóm đại lượng", all(l["nhom"] for l in td["loai"]))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
