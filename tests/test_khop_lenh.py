"""MÔ HÌNH KHỚP — thứ quyết định backtest thật hay ảo tưởng.

Bài này canh đúng một loại lỗi, nhưng là loại đắt nhất trong cả repo: **lãi khống**.
Một mô hình khớp rộng tay không nổ, không cảnh báo, không sai cú pháp — nó chỉ cho ra
một đường vốn đẹp, và cái giá phải trả bằng tiền thật.

Sáu chỗ dễ cho lãi khống nhất, và cả sáu đều có phép kiểm riêng ở đây:

  1. **Chạm là khớp.** Đúng cho lệnh Stop, SAI cho limit — trước ta còn cả một hàng.
  2. **Đổi báo giá miễn phí.** Đổi giá treo = về CUỐI hàng. Không tính thì mọi chiến
     lược nhấp nháy liên tục đều trông tuyệt vời.
  3. **Lệnh sống ngay lập tức.** Có độ trễ ra; mọi thứ trong quãng đó ta không với tới.
  4. **Bỏ qua khớp NGHỊCH.** Thị trường bán tháo ngay dưới lệnh mua của ta mà ta không
     khớp — vẽ ra một sự an toàn không có thật, đúng chỗ thua lỗ thật xảy ra.
  5. **Hàng đợi tự tiến lên.** Khối lượng biến mất chưa chắc là ở TRƯỚC ta.
  6. **Post-only âm thầm thành taker.** Chiến lược hỏng biến thành một chiến lược khác
     đang ăn phí gấp mấy lần.

⚠ Bài này KHÔNG chứng minh mô hình ĐÚNG — không có gì chứng minh được điều đó khi dữ
liệu L1 vốn không chứa câu trả lời. Nó chứng minh mô hình **sai theo hướng bi quan**,
và mọi giả định đều **vặn được và nhìn thấy được**.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

from cat_studio import khop_lenh as K  # noqa: E402
from cat_studio import phat_lai  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


class SK:
    """Một sự kiện giả — cùng hình dạng với `PhatLai`, không cần file nào."""

    __slots__ = ("loai", "t", "bid", "bid_kl", "ask", "ask_kl",
                 "gia", "kl", "mua_chu_dong")

    def __init__(self, loai, t, **kw):
        self.loai, self.t = loai, t
        self.bid = self.ask = K.NAN
        self.bid_kl = self.ask_kl = 0.0
        self.gia = self.kl = K.NAN
        self.mua_chu_dong = False
        for k, v in kw.items():
            setattr(self, k, v)


def so(t, bid, bkl, ask, akl):
    return SK(phat_lai.SO, t, bid=bid, bid_kl=bkl, ask=ask, ask_kl=akl)


def khop(t, gia, kl, mua_chu_dong):
    return SK(phat_lai.KHOP, t, gia=gia, kl=kl, mua_chu_dong=mua_chu_dong)


def moi(**kw):
    """Một sổ khớp mới, đã thấy sổ lệnh 100/101 với 500 lot mỗi bên.

    `tre_ra_ms=0` cho hầu hết phép kiểm: độ trễ có bài riêng, trộn vào mọi bài khác
    chỉ làm mỗi bài phải giải thích hai chuyện."""
    kw.setdefault("tre_ra_ms", 0.0)
    # Bước giá 0,1 chứ không phải 1,0: với tick 1,0 thì giữa bid 100 và ask 101 KHÔNG
    # CÒN mức nào, nên không diễn tả nổi ca "treo tốt hơn đỉnh" — mọi giá 100,5 đều bị
    # làm tròn về đúng đỉnh. Bài kiểm đầu tiên viết tick 1,0 và ba phép im lặng đo
    # nhầm thứ khác.
    s = K.SoKhop(K.MoHinh(0.1, **kw))
    s.buoc(so(0, 100.0, 500.0, 101.0, 500.0))
    return s


# ================= 1. ĐO BƯỚC GIÁ =================
print("\n▸ Bước giá — ĐO ĐƯỢC thì đừng hỏi")
for gia, mong in ((np.array([65432.0, 65432.1, 65432.3]), 0.1),
                  (np.array([1.23, 1.25, 1.24]), 0.01),
                  (np.array([0.00001234, 0.00001235]), 1e-8),
                  (np.array([100.0, 102.5, 105.0]), 2.5)):
    d = K.do_buoc_gia(gia)
    kiem(f"đo ra {mong:g}", d == mong, f"— {d!r}")
kiem("không đủ dữ liệu thì trả nan, KHÔNG bịa một tick",
     np.isnan(K.do_buoc_gia(np.array([5.0]))) and np.isnan(K.do_buoc_gia()))

m = K.MoHinh(0.1)
kiem("mua tròn XUỐNG (ít hung hăng hơn)", m.lam_tron(65432.17, K.MUA) == 65432.1)
kiem("bán tròn LÊN (ít hung hăng hơn)", m.lam_tron(65432.13, K.BAN) == 65432.2)
kiem("giá đã đúng bội tick thì KHÔNG bị đẩy đi một tick",
     m.lam_tron(65432.1, K.MUA) == 65432.1 and m.lam_tron(65432.1, K.BAN) == 65432.1,
     f"— {m.lam_tron(65432.1, K.MUA)!r}")
# Phép so `== 65432.1` ngay trên đã đủ tách `65432.1` khỏi rác `65432.100000000006` —
# chúng là hai `double` KHÁC NHAU. (`65432.1` trong float64 vốn là `65432.09999999999`;
# không có biểu diễn nào sạch hơn, nên đòi chuỗi thập phân tròn trịa là đòi thứ không
# tồn tại.) Cái đáng canh là TRÔI DẦN: báo giá được làm tròn lại ở mỗi lượt phát biểu,
# hàng triệu lượt một ngày, nên rác cộng dồn sẽ đẩy giá đi cả một tick mà không ai thấy.
troi = [g for g in (65432.17, 65432.13, 0.00001234, 1.005, 99.999)
        for r in (m.lam_tron(g, K.MUA),)
        if m.lam_tron(r, K.MUA) != r or m.lam_tron(r, K.BAN) != r]
kiem("làm tròn LẠI một giá đã tròn thì đứng yên — không trôi qua hàng triệu lượt",
     not troi, f"— trôi ở {troi}")


# ================= 2. CHẠM ≠ KHỚP =================
print("\n▸ Chạm ≠ khớp — cái bẫy lớn nhất")

s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)             # treo mua ĐÚNG đỉnh, sau 500 lot
kiem("treo đúng đỉnh → cả khối lượng đang hiện đứng TRƯỚC ta",
     s.mua.hang_doi == 500.0, f"— {s.mua.hang_doi}")
r = s.buoc(khop(1, 100.0, 300.0, False))    # bán chủ động 300 lot vào bid
kiem("giá CHẠM mức của ta mà chưa tới lượt ta → KHÔNG khớp", r == () and s.ton_kho == 0)
kiem("nhưng hàng đợi đã ngắn đi đúng bằng phần vừa khớp",
     s.mua.hang_doi == 200.0, f"— {s.mua.hang_doi}")
r = s.buoc(khop(2, 100.0, 250.0, False))    # 200 nốt hàng đợi, còn 50 — mà ta chỉ có 10
kiem("hết hàng đợi rồi mới tới ta, và chỉ được phần THỪA RA",
     len(r) == 1 and r[0]["kl"] == 10.0 and s.ton_kho == 10.0, f"— {r}")
kiem("không khớp quá số lot đang treo, dù phần thừa còn nhiều",
     s.mua is None and s.kl_da_khop == 10.0)

s = moi()
s.dong_bo(0, 100.5, 10.0, 0, 0)             # treo CAO HƠN đỉnh → thành đỉnh mới
kiem("treo TỐT HƠN đỉnh → hàng đợi 0, chắc chắn, không giả định gì",
     s.mua.hang_doi == 0.0)
r = s.buoc(khop(1, 100.5, 4.0, False))
kiem("và khớp ngay từ lot đầu tiên", len(r) == 1 and r[0]["kl"] == 4.0)
kiem("khớp một phần thì lệnh CÒN NẰM ĐÓ với phần còn lại",
     s.mua is not None and s.mua.con_lai == 6.0)


# ================= 3. KHỚP XUYÊN QUA =================
print("\n▸ Khớp XUYÊN QUA mức của ta — mặt trái đắt nhất của market making")
s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
kiem("hàng đợi 500 lot đứng trước", s.mua.hang_doi == 500.0)
r = s.buoc(khop(1, 99.0, 1.0, False))       # khớp ở mức THẤP HƠN mức ta treo
kiem("khớp ở mức XẤU HƠN ⇒ mức của ta đã sạch ⇒ ta khớp TRỌN, bất kể hàng đợi",
     len(r) == 1 and r[0]["kl"] == 10.0 and s.ton_kho == 10.0, f"— {r}")
kiem("và khớp ở ĐÚNG giá ta treo, không phải giá thị trường",
     r[0]["gia"] == 100.0)

s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
r = s.buoc(khop(1, 100.5, 999.0, False))    # khớp ở mức TỐT HƠN
kiem("khớp ở mức TỐT HƠN thì chưa xuống tới ta — không khớp gì",
     r == () and s.ton_kho == 0)


# ================= 4. KHỚP NGHỊCH =================
print("\n▸ Khớp NGHỊCH — sổ lệnh vượt qua ta mà không có lệnh khớp nào")
s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
r = s.buoc(so(1, 98.0, 400.0, 99.0, 400.0))  # ask tụt XUỐNG DƯỚI giá mua của ta
kiem("ask tụt xuống dưới giá MUA của ta → phải khớp cho ta",
     len(r) == 1 and s.ton_kho == 10.0, f"— {r} tồn kho {s.ton_kho}")
kiem("bỏ qua ca này là vẽ ra sự an toàn không có thật", r[0]["gia"] == 100.0)

s = moi()
s.dong_bo(0, 0, 0, 101.0, 10.0)
r = s.buoc(so(1, 102.0, 400.0, 103.0, 400.0))
kiem("gương lại: bid vọt lên trên giá BÁN của ta → cũng khớp",
     len(r) == 1 and s.ton_kho == -10.0)


# ================= 5. GIÁ CỦA VIỆC ĐỔI BÁO GIÁ =================
print("\n▸ Đổi báo giá = về CUỐI hàng")
s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(khop(1, 100.0, 400.0, False))        # ăn bớt hàng đợi: 500 → 100
kiem("đã bò lên gần đầu hàng", s.mua.hang_doi == 100.0)

s.dong_bo(2, 100.0, 10.0, 0, 0)             # phát biểu Y HỆT
kiem("phát biểu LẠI Y HỆT là hành động RỖNG — giữ nguyên vị trí hàng đợi",
     s.mua.hang_doi == 100.0 and s.so_dat == 1 and s.so_huy == 0,
     f"— hàng đợi {s.mua.hang_doi}, đặt {s.so_dat}, huỷ {s.so_huy}")

s.dong_bo(3, 99.0, 10.0, 0, 0)              # đổi GIÁ
kiem("đổi GIÁ thì mất sạch chỗ đã bò được",
     s.so_huy == 1 and s.so_dat == 2 and s.mua.gia == 99.0)

s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(khop(1, 100.0, 450.0, False))
s.dong_bo(2, 100.0, 4.0, 0, 0)              # GIẢM khối lượng
kiem("GIẢM khối lượng giữ được chỗ — sàn coi vẫn là lệnh cũ",
     s.mua.hang_doi == 50.0 and s.so_huy == 0 and s.mua.kl == 4.0)
s.dong_bo(3, 100.0, 40.0, 0, 0)             # TĂNG khối lượng
kiem("TĂNG khối lượng thì mất chỗ — phần thêm là lệnh đến sau",
     s.mua.hang_doi == 500.0 and s.so_huy == 1, f"— {s.mua.hang_doi}")

s = moi()
s.dong_bo(0, 100.0, 10.0, 101.0, 10.0)
kiem("khối lượng 0 = rút, không cần động từ riêng",
     (s.dong_bo(1, 100.0, 0.0, 101.0, 10.0) or True)
     and s.mua is None and s.ban is not None)


# ================= 6. ĐỘ TRỄ RA =================
print("\n▸ Độ trễ ra — quãng ta không với tới")
s = K.SoKhop(K.MoHinh(0.1, tre_ra_ms=5.0))
s.buoc(so(0, 100.0, 500.0, 101.0, 500.0))
s.dong_bo(100, 100.5, 10.0, 0, 0)           # hàng đợi 0, đáng lẽ khớp ngay
r = s.buoc(khop(102, 100.5, 5.0, False))    # 2 ms sau — lệnh CHƯA tới sàn
kiem("lệnh chưa tới sàn thì không khớp được, dù hàng đợi trống",
     r == () and s.ton_kho == 0)
r = s.buoc(khop(106, 100.5, 5.0, False))    # 6 ms sau — đã sống
kiem("qua độ trễ rồi mới khớp", len(r) == 1 and s.ton_kho == 5.0)


# ================= 7. NÚM VẶN HÀNG ĐỢI =================
print("\n▸ Núm vặn — khi người ta HUỶ, họ đứng trước hay sau ta?")


def sau_huy(phan):
    """Treo đúng đỉnh (hàng đợi 500), rồi 200 lot BIẾN MẤT mà không lệnh khớp nào."""
    s = moi(phan_huy_truoc=phan)
    s.dong_bo(0, 100.0, 10.0, 0, 0)
    s.buoc(so(1, 100.0, 300.0, 101.0, 500.0))
    return s.mua.hang_doi


kiem("0,0 bi quan — huỷ ở SAU ta, vị trí không đổi (MẶC ĐỊNH)", sau_huy(0.0) == 500.0)
kiem("1,0 lạc quan — huỷ ở TRƯỚC ta, tiến lên đủ 200", sau_huy(1.0) == 300.0)
kiem("0,5 — tiến nửa chừng", sau_huy(0.5) == 400.0)
kiem("mặc định của `MoHinh` là BI QUAN", K.MoHinh(1.0).phan_huy_truoc == 0.0)

s = moi(phan_huy_truoc=1.0)
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(khop(1, 100.0, 200.0, False))        # 200 lot KHỚP (không phải huỷ)
s.buoc(so(2, 100.0, 300.0, 101.0, 500.0))   # sổ giảm đúng 200 — đã giải thích hết
kiem("phần giảm đã có lệnh khớp giải thích thì KHÔNG tính hai lần",
     s.mua.hang_doi == 300.0, f"— {s.mua.hang_doi}")

s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(so(1, 100.0, 900.0, 101.0, 500.0))
kiem("khối lượng TĂNG = người mới xếp SAU ta, không đổi gì", s.mua.hang_doi == 500.0)

s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(so(1, 99.0, 400.0, 101.0, 500.0))    # đỉnh bỏ qua mức của ta
kiem("đỉnh TỤT QUA mức của ta ⇒ mọi người ở đó đã đi hết ⇒ ta ra đầu hàng",
     s.mua.hang_doi == 0.0)

s = moi(phan_muc_sau=1.0)
s.dong_bo(0, 99.0, 10.0, 0, 0)              # treo SÂU HƠN đỉnh — vùng mù
kiem("treo sâu hơn đỉnh: hàng đợi là con số MƯỢN TẠM, bi quan 100%",
     s.mua.hang_doi == 500.0)
s2 = moi(phan_muc_sau=0.0)
s2.dong_bo(0, 99.0, 10.0, 0, 0)
kiem("vặn về 0 thì lạc quan hết cỡ — và đó là LỰA CHỌN, không phải mặc định",
     s2.mua.hang_doi == 0.0 and K.MoHinh(1.0).phan_muc_sau == 1.0)


# ================= 8. POST-ONLY =================
print("\n▸ Post-only — hỏng thì phải NHÌN THẤY")
s = moi()
s.dong_bo(0, 101.0, 10.0, 0, 0)             # mua bằng ask → lấn qua phía kia
kiem("báo giá lấn qua phía đối diện → TỪ CHỐI, không âm thầm thành taker",
     s.mua is None and s.so_tu_choi == 1)
s.dong_bo(1, 0, 0, 100.0, 10.0)             # bán bằng bid
kiem("gương lại cũng vậy", s.ban is None and s.so_tu_choi == 2)
s.dong_bo(2, 100.0, 10.0, 101.0, 10.0)
kiem("đúng ở hai đỉnh thì nhận cả hai",
     s.mua is not None and s.ban is not None and s.so_tu_choi == 2)


# ================= 9. TIỀN VÀ PHÍ =================
print("\n▸ Tiền · phí · tồn kho")
s = moi(phi_maker_bps=2.0)
s.dong_bo(0, 100.5, 10.0, 0, 0)
s.buoc(khop(1, 100.5, 10.0, False))
phi = 10.0 * 100.5 * 2.0 / 10000.0
kiem("mua: tồn kho tăng, tiền giảm ĐÚNG bằng giá trị CỘNG phí",
     s.ton_kho == 10.0 and abs(s.tien - (-10.0 * 100.5 - phi)) < 1e-9,
     f"— tiền {s.tien:.6f}")
kiem("phí được đếm riêng — cả luận điểm là spread phải hơn HAI LẦN phí",
     abs(s.phi_da_tra - phi) < 1e-12, f"— {s.phi_da_tra:.6f}")

# Ô khớp là BIÊN của vòng lặp nóng: `PhatLai` cố ý trả số của numpy, mà `np.float64`
# thì `json.dumps` nghẹn. Dọn ở đây một lần, thay vì bắt mọi chỗ đọc sau nhớ tự dọn.
import json  # noqa: E402
s3 = moi()
s3.dong_bo(0, 100.5, 10.0, 0, 0)
o = s3.buoc(khop(1, 100.5, 10.0, False))[0]
try:
    json.dumps(o)
    kiem("ô khớp JSON hoá được ngay — không sót kiểu numpy nào", True)
except TypeError as e:
    kiem("ô khớp JSON hoá được ngay — không sót kiểu numpy nào", False, f"— {e}")

s = moi(phi_maker_bps=0.0)
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(khop(1, 99.0, 1.0, False))           # mua 10 @ 100 (khớp xuyên)
s.dong_bo(2, 0, 0, 102.0, 10.0)
s.buoc(khop(3, 103.0, 1.0, True))           # bán 10 @ 102 (khớp xuyên)
kiem("ăn trọn hai chân: tồn kho về 0, lãi = bề rộng × khối lượng",
     s.ton_kho == 0.0 and abs(s.tien - 20.0) < 1e-9, f"— {s.tien}")
kiem("`gia_tri` khi tồn kho = 0 là con số DUY NHẤT không cần dè dặt",
     s.gia_tri(101.0) == s.tien)

s = moi()
s.buoc(khop(1, 100.0, 5.0, False))
kiem("không có lệnh nào thì lệnh khớp của thị trường không đụng gì tới ta",
     s.ton_kho == 0.0 and s.so_khop == 0)


# ================= 10. LỖ HỔNG =================
print("\n▸ Lỗ hổng — nói ra chỗ mình không biết")
s = moi()
s.dong_bo(0, 100.0, 10.0, 0, 0)
s.buoc(SK(phat_lai.MO_LO_HONG, 1000))
r = s.buoc(khop(3000, 99.0, 1.0, False))
kiem("mù thì KHÔNG khớp — ta không có quyền đoán là đã khớp", r == ())
s.buoc(SK(phat_lai.DONG_LO_HONG, 5000))
kiem("nhưng ĐẾM thời gian mù có lệnh treo, thay vì im lặng coi như không có gì",
     s.giay_mu_co_lenh == 4.0, f"— {s.giay_mu_co_lenh}")

s2 = moi()
s2.buoc(SK(phat_lai.MO_LO_HONG, 1000))
s2.buoc(SK(phat_lai.DONG_LO_HONG, 5000))
kiem("không treo lệnh nào thì lỗ hổng không phải là nợ", s2.giay_mu_co_lenh == 0.0)


# ================= 11. GIẢ ĐỊNH PHẢI ĐI KÈM KẾT QUẢ =================
print("\n▸ Giả định phải in kèm MỌI kết quả")
t = moi(phi_maker_bps=1.5, tre_ra_ms=7.0, phan_huy_truoc=0.5).tom_tat(100.5)
kiem("`tom_tat` mang theo cả bốn núm vặn",
     set(t["gia_dinh"]) == {"buoc_gia", "phi_maker_bps", "tre_ra_ms",
                            "phan_huy_truoc", "phan_muc_sau"},
     f"— {sorted(t['gia_dinh'])}")
kiem("và mang đúng giá trị đang dùng",
     t["gia_dinh"]["phan_huy_truoc"] == 0.5 and t["gia_dinh"]["tre_ra_ms"] == 7.0)
kiem("núm vặn bị kẹp về [0, 1], không nhận số vô nghĩa",
     K.MoHinh(1.0, phan_huy_truoc=5.0).phan_huy_truoc == 1.0
     and K.MoHinh(1.0, phan_huy_truoc=-2.0).phan_huy_truoc == 0.0)


# ================= 12. BI QUAN LÀ MỘT THỨ TỰ =================
print("\n▸ Ba núm vặn phải CÙNG CHIỀU — lạc quan hơn thì không bao giờ khớp ít hơn")


def chay(phan_huy):
    """CÙNG MỘT dòng sự kiện, chỉ đổi giả định.

    Kịch bản cố ý tách bạch hai nguồn làm hàng đợi ngắn đi: 400 lot BIẾN MẤT không có
    lệnh khớp nào (tức huỷ — chỗ núm vặn có tiếng nói), rồi mới tới hai lệnh khớp."""
    s = K.SoKhop(K.MoHinh(0.1, tre_ra_ms=0.0, phi_maker_bps=0.0,
                          phan_huy_truoc=phan_huy))
    s.buoc(so(0, 100.0, 500.0, 101.0, 500.0))
    s.dong_bo(0, 100.0, 50.0, 0, 0)                     # hàng đợi 500
    s.buoc(so(10, 100.0, 100.0, 101.0, 500.0))          # 400 lot huỷ
    s.buoc(khop(20, 100.0, 200.0, False))
    s.buoc(khop(30, 100.0, 200.0, False))
    return s.ton_kho


bi, giua, lac = chay(0.0), chay(0.5), chay(1.0)
kiem("bi quan ≤ giữa ≤ lạc quan, và KHÔNG bằng nhau — núm vặn có tác dụng thật",
     bi <= giua <= lac and bi < lac, f"— {bi} · {giua} · {lac}")
kiem("mặc định của app CHÍNH LÀ đầu bi quan nhất — 0 lot, không khớp gì",
     K.MoHinh(1.0).phan_huy_truoc == 0.0 and bi == 0.0)


print("\n" + "=" * 56)
print(f"  {dung} đúng, {sai} sai")
print("=" * 56)
sys.exit(1 if sai else 0)
