"""MÔ HÌNH KHỚP — lệnh THỤ ĐỘNG của ta khớp lúc nào, và bao nhiêu.

Đây là chỗ quyết định backtest thật hay ảo tưởng, nên đọc kỹ đoạn này trước khi tin
bất cứ con số nào file này sinh ra.

VÌ SAO KHÔNG BÊ ĐƯỢC MÔ HÌNH CŨ
-------------------------------
`khop_lenh.py` của D_02 (220 dòng, đợt 2) biến mỗi nến M1 thành **đường đi 4 điểm** rồi
quy mọi thứ về một luật: *"giá chạm mức X ở bước k"*. Sạch, và ĐÚNG cho lệnh chủ động —
lệnh Stop, SL, TP đều khớp ngay khi giá chạm tới.

Với lệnh **limit thì CHẠM ≠ KHỚP**. Giá về đúng mức ta treo mà ta vẫn không được gì,
vì trước ta còn cả một hàng người đến sớm hơn. Bê nguyên luật "chạm là khớp" sang
market making sẽ cho **lãi khống một cách có hệ thống**: mỗi lần giá quét qua là ăn
trọn cả hai chân, trong khi thực tế phần lớn thời gian ta đứng cuối hàng và chỉ khớp
đúng lúc không nên khớp.

CÂU HỎI TRUNG TÂM, VÀ VÌ SAO NÓ KHÔNG CÓ ĐÁP ÁN
-----------------------------------------------
    Lệnh của ta xếp thứ mấy trong hàng đợi ở mức giá đó?

Dữ liệu `bookTicker` chỉ cho biết **tổng khối lượng ở đỉnh**, không cho biết nó gồm
những lệnh nào, đến lúc nào, và khi khối lượng giảm thì phần giảm nằm trước hay sau ta.
Muốn biết chắc phải có dữ liệu MBO (từng lệnh một) — không sàn lớn nào phát miễn phí.

Nên file này KHÔNG giả vờ biết. Nó tách đôi rành mạch:

  * **SUY RA ĐƯỢC** — treo cao hơn đỉnh thì hàng đợi = 0 (chắc chắn, không giả định);
    treo đúng đỉnh thì hàng đợi = khối lượng đang hiện (cũng chắc chắn — ta vừa tới);
    có lệnh khớp ở mức ta thì phần khớp đó chắc chắn ăn từ ĐẦU hàng.
  * **PHẢI GIẢ ĐỊNH** — khối lượng biến mất mà không có lệnh khớp nào giải thích thì
    là người ta HUỶ, và huỷ ở trước hay sau ta thì không ai biết.

Mọi giả định nằm gọn trong `MoHinh` — bốn con số, đặt ở Cài đặt, in ra cùng kết quả.
Không có hằng số nào giấu trong mã.

BỐN THIÊN LỆCH CÒN LẠI, GHI RA ĐỂ KHÔNG AI QUÊN
-----------------------------------------------
1. **Không mô hình hoá tác động.** Ta phát lại sổ lệnh như thể lệnh của ta VÔ HÌNH với
   người khác. Thật ra một lệnh đủ lớn ở đỉnh sẽ làm người khác đổi hành vi. Đây là
   thiên lệch cố hữu của mọi backtest phát lại, không sửa được bằng dữ liệu này.
2. **Mức treo SÂU HƠN đỉnh là vùng mù.** `bookTicker` không thấy tầng dưới, nên khối
   lượng trước ta ở đó là một con số bịa — `phan_muc_sau` chọn bịa theo hướng nào.
3. **Độ trễ ra không đo được** nếu chưa từng gửi lệnh thật. `tre_ra_ms` là ước lượng.
4. **Lỗ hổng dữ liệu là vùng mù thật sự.** Lệnh vẫn nằm ở sàn và sàn vẫn khớp, ta chỉ
   không nhìn thấy. File này KHÔNG cho khớp trong lỗ hổng, nhưng ĐẾM thời gian mù có
   lệnh treo (`giay_mu_co_lenh`) — để kết quả nói ra chỗ nó không biết, thay vì im lặng
   coi như không có gì xảy ra.

TỐC ĐỘ ĐÃ ĐO (2 triệu sự kiện giả, đã trừ chi phí dựng sự kiện)
---------------------------------------------------------------
    buoc() thôi                      3,44 tr/s   ← nhanh hơn cả lớp phát lại (1,97)
    + phát biểu báo giá mỗi 100 sk   1,90 tr/s
    + phát biểu mỗi 4 sk             0,86 tr/s
    + phát biểu MỖI sự kiện          0,41 tr/s   ← xấu nhất có thể

Một ngày (~10 triệu sự kiện) mất 12–25 giây tuỳ chiến lược requote dày hay thưa. Đủ để
lặp lại nhiều lần trong một buổi.

`dong_bo` đắt hơn `buoc` khoảng 5 lần, và đó là ĐÚNG BẢN CHẤT chứ không phải chỗ cần
vặn: nó là chỗ làm tròn giá, so với báo giá cũ, huỷ và đặt lại. Chiến lược nào requote
mỗi sự kiện thì trả giá cả trong backtest lẫn ngoài đời thật — ngoài đời còn đắt hơn,
vì mỗi lần requote là mất chỗ trong hàng đợi.
"""
import math

import numpy as np

from . import phat_lai

# ⚠ `math` chứ không phải `numpy` trong vòng lặp nóng, và đây là chuyện ĐO ĐƯỢC chứ
# không phải sở thích: `np.floor`/`np.isfinite` gọi trên MỘT con số mất ~1 µs, vì mỗi
# lần là một chuyến đi vào tầng ufunc. Bản đầu dùng numpy và `dong_bo` tốn ~2,2 µs mỗi
# lượt — cả mô hình tụt còn **0,40 triệu sự kiện/giây**, chậm hơn lớp phát lại 5 lần,
# tức nó thành nút cổ chai của cả backtest. `math` làm đúng việc đó trên số vô hướng
# nhanh hơn khoảng hai bậc.
#
# `numpy` vẫn giữ cho `do_buoc_gia` — chỗ đó xử lý MẢNG, đúng việc của nó.
_floor = math.floor
_ceil = math.ceil
_huu_han = math.isfinite

#: Hai phía. Số chứ không phải chuỗi — so sánh trong vòng lặp mười triệu lần.
MUA = 1
BAN = -1
TEN_BEN = {MUA: "BUY", BAN: "SELL"}

#: Vì sao lệnh rời sổ — cho nhật ký, và cho việc đếm xem chiến lược đang hỏng kiểu gì.
KHOP_HET = "filled"
BI_HUY = "cancelled"
TU_CHOI = "rejected"

NAN = float("nan")
RONG = ()


def _so_le_cua(buoc):
    """Bước giá có mấy chữ số thập phân. `0.1` → 1 · `1e-8` → 8 · `2.5` → 1 · `10` → 0."""
    if not (buoc > 0):
        return 8
    s = f"{buoc:.10f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


def do_buoc_gia(*mang_gia):
    """Bước giá NHỎ NHẤT của symbol, ĐO TỪ DỮ LIỆU — không hỏi người dùng.

    "Đo được thì đừng hỏi": tick là một sự thật của sàn, hỏi là mời gõ sai rồi tin nó.

    Cách đo: gom mọi mức giá đã từng xuất hiện, sắp lại, lấy hiệu NHỎ NHẤT khác 0. Qua
    một ngày giao dịch thì chắc chắn có hai mức cạnh nhau đúng một tick, nên hiệu nhỏ
    nhất CHÍNH LÀ tick.

    ⚠ PHẢI DỌN SAI SỐ FLOAT, và dọn theo CHỮ SỐ CÓ NGHĨA chứ không theo số chữ số thập
    phân. `65432.1 - 65432.0` trong float64 ra `0.09999999999417923`; làm tròn 12 chữ số
    thập phân vẫn còn `0.099999999994`, và cái "tick" rác đó sẽ kéo mọi phép làm tròn
    giá sau nó lệch theo. Sáu chữ số có nghĩa thì ra đúng `0.1` — an toàn vì bước giá
    của sàn luôn là số tròn (`1e-8` · `0.001` · `0.5` · `2.5` · `10`), không bao giờ là
    một con số 6 chữ số lẻ.

    ⚠ VÀ PHẢI VỨT RÁC FLOAT TRƯỚC KHI LẤY MIN. Hai giá lẽ ra bằng nhau mà lệch nhau
    `1,4e-14` (chuyện thường gặp khi giá đi qua một phép tính nào đó) sẽ thành "bước
    giá" — đúng ca đã xảy ra ngay lần chạy thử đầu tiên của bộ chạy, và nó hỏng LẶNG:
    tick `1,4e-14` khiến `lam_tron` không làm gì cả, `_so_le_cua` trả 8, và mọi báo giá
    trôi tự do giữa các mức hợp lệ mà không ai thấy gì bất thường.

    Ngưỡng `giá × 1e-9`: lớn hơn sai số float khoảng nghìn lần (ULP của một giá 65.000
    là ~7e-12), nhỏ hơn bước giá thật của mọi sàn khoảng trăm lần. Rộng cả hai phía.

    Trả `nan` nếu không đủ dữ liệu — người gọi phải xử lý, chứ đừng nhận một tick bịa."""
    gom = [np.asarray(m, dtype="f8").ravel() for m in mang_gia if len(m)]
    if not gom:
        return NAN
    g = np.unique(np.concatenate(gom))
    g = g[np.isfinite(g)]  # MẢNG — numpy đúng chỗ
    if len(g) < 2:
        return NAN
    d = np.diff(g)
    d = d[d > abs(g).max() * 1e-9]
    return float(f"{d.min():.6g}") if len(d) else NAN


class MoHinh:
    """BỐN NÚM VẶN — và ba trong bốn là thứ dữ liệu KHÔNG BAO GIỜ trả lời được.

    Đây là toàn bộ phần "ta đoán" của backtest. Gom về một chỗ, đặt tên tiếng người, in
    kèm mọi kết quả. Rải chúng thành hằng số trong mã thì sáu tháng nữa không ai đọc ra
    con số nào là đo được, con số nào là đoán.

    ┌───────────────────┬──────────────────────────────────────────────────────────────┐
    │ `buoc_gia`        │ ĐO ĐƯỢC — `do_buoc_gia()`. Ở đây chỉ để mang theo.           │
    │ `phi_maker_bps`   │ TRA ĐƯỢC ở biểu phí sàn, nhưng phụ thuộc hạng VIP và chương  │
    │                   │ trình Market Maker nên vẫn phải khai. Xem `do_thi_truong`.   │
    │ `tre_ra_ms`       │ ĐOÁN — không đo được nếu chưa gửi lệnh thật.                 │
    │ `phan_huy_truoc`  │ ĐOÁN, và là núm QUAN TRỌNG NHẤT của cả file.                 │
    │ `phan_muc_sau`    │ ĐOÁN — chỉ dùng khi treo sâu hơn đỉnh.                       │
    └───────────────────┴──────────────────────────────────────────────────────────────┘

    `phan_huy_truoc` — KHI NGƯỜI TA HUỶ, HỌ ĐỨNG TRƯỚC HAY SAU TA?

        0,0  bi quan  mọi lệnh huỷ đều ở SAU ta → vị trí của ta không bao giờ tự tốt
                      lên, chỉ có lệnh khớp mới đẩy ta lên. Đây là MẶC ĐỊNH.
        1,0  lạc quan mọi lệnh huỷ đều ở TRƯỚC ta → ta tiến lên đầu hàng rất nhanh.
        0,5  đều      giả định huỷ rải đều — nghe hợp lý nhất, nhưng KHÔNG có gì chứng
                      minh, và nó cho lãi cao hơn 0,0 một cách có hệ thống.

    Mặc định 0,0 vì một backtest sai theo hướng BI QUAN thì tệ nhất là bỏ lỡ một chiến
    lược tốt; sai theo hướng lạc quan thì đem tiền thật ra trả học phí. Muốn biết kết
    quả nhạy đến đâu thì chạy lại với 0,0 · 0,5 · 1,0 — khoảng cách giữa ba lần chạy
    CHÍNH LÀ phần backtest không biết, và nó phải được nhìn thấy.

    `phan_muc_sau` — treo SÂU HƠN đỉnh thì bao nhiêu phần của mức đó nằm trước ta? Mặc
    định 1,0 (cả mức đứng trước ta), cùng lý lẽ bi quan. Chiến lược sơ cấp treo cách
    công bằng nửa spread nên rơi vào đúng ca này thường xuyên.
    """

    __slots__ = ("buoc_gia", "phi_maker_bps", "tre_ra_ms",
                 "phan_huy_truoc", "phan_muc_sau", "_so_le")

    def __init__(self, buoc_gia, phi_maker_bps=2.0, tre_ra_ms=5.0,
                 phan_huy_truoc=0.0, phan_muc_sau=1.0):
        self.buoc_gia = float(buoc_gia)
        # Bước giá có mấy chữ số thập phân — để làm tròn xong còn ra một con số ĐỌC
        # ĐƯỢC. `floor(65432.17 / 0.1) × 0.1` cho `65432.100000000006`; sai số vô hại
        # về mặt số học nhưng nó lọt vào nhật ký, vào JSON, vào mắt người dùng.
        self._so_le = _so_le_cua(self.buoc_gia)
        self.phi_maker_bps = float(phi_maker_bps)
        self.tre_ra_ms = float(tre_ra_ms)
        self.phan_huy_truoc = min(1.0, max(0.0, float(phan_huy_truoc)))
        self.phan_muc_sau = min(1.0, max(0.0, float(phan_muc_sau)))

    def lam_tron(self, gia, ben):
        """Giá về bội của tick, LÀM TRÒN VỀ PHÍA ÍT HUNG HĂNG HƠN.

        Mua tròn XUỐNG, bán tròn LÊN. Tròn ngược lại là tự ý đẩy báo giá vào sát thị
        trường hơn ý chiến lược — tức backtest chạy một chiến lược khác cái đang vẽ, mà
        chiến lược đó thì khớp nhiều hơn và trông đẹp hơn."""
        b = self.buoc_gia
        if not (b > 0) or not _huu_han(gia):
            return gia
        n = gia / b
        # `+ 1e-9` chống một ca thật: giá ĐÃ đúng bội của tick nhưng phép chia ra
        # `654321.9999999999`, và `floor` cắt mất đúng một tick. Dung sai nhỏ hơn nửa
        # tick rất nhiều nên không bao giờ nhảy sang bội khác.
        n = _floor(n + 1e-9) if ben == MUA else _ceil(n - 1e-9)
        return round(n * b, self._so_le)

    def tom_tat(self):
        """In kèm MỌI kết quả. Một bảng lãi lỗ không nói rõ nó giả định gì thì không
        đọc được — và tệ hơn, nó trông như một sự thật."""
        return {
            "buoc_gia": self.buoc_gia,
            "phi_maker_bps": self.phi_maker_bps,
            "tre_ra_ms": self.tre_ra_ms,
            "phan_huy_truoc": self.phan_huy_truoc,
            "phan_muc_sau": self.phan_muc_sau,
        }


class Lenh:
    """MỘT lệnh đang nằm ở sàn.

    `hang_doi` là **ước lượng khối lượng đứng TRƯỚC ta** ở mức giá này. Nó là trái tim
    của cả file, và là con số duy nhất không quan sát được."""

    __slots__ = ("ben", "gia", "gia_tho", "kl", "con_lai", "hang_doi",
                 "song_luc", "dat_luc")

    def __init__(self, ben, gia, kl, hang_doi, dat_luc, song_luc, gia_tho=None):
        self.ben = ben
        self.gia = gia
        #: Giá chiến lược ĐÒI, trước khi làm tròn về tick. Giữ lại chỉ để `_dong_bo_mot`
        #: nhận ra "vẫn đúng câu vừa nói" mà khỏi làm tròn lại — xem chỗ dùng.
        self.gia_tho = gia if gia_tho is None else gia_tho
        self.kl = kl
        self.con_lai = kl
        self.hang_doi = hang_doi
        self.dat_luc = dat_luc
        self.song_luc = song_luc          # chưa tới mốc này thì lệnh CHƯA ở sàn

    def __repr__(self):
        return (f"<{TEN_BEN[self.ben]} {self.con_lai:g}/{self.kl:g} @ {self.gia:g} "
                f"queue {self.hang_doi:g}>")


class SoKhop:
    """Sổ lệnh CỦA TA + tồn kho + tiền, chạy theo dòng sự kiện.

    Hai lời gọi, và chúng tách bạch đúng hai việc:

        dong_bo(t, bid, bid_kl, ask, ask_kl)   ← chiến lược nói: báo giá phải thành thế này
        buoc(sk)                               ← một sự kiện thị trường đi qua

    `dong_bo` là chỗ **GIÁ CỦA VIỆC ĐỔI BÁO GIÁ** được tính. Đổi giá treo = huỷ + đặt
    lại = **về cuối hàng**. Đây là lý do một market maker không requote mỗi tick, và
    nếu mô hình không tính cái giá đó thì mọi chiến lược nhấp nháy liên tục đều trông
    tuyệt vời trong backtest và cháy trong thực tế.

    Ngược lại, báo giá KHÔNG ĐỔI thì không đụng gì — giữ nguyên vị trí hàng đợi. Đó
    chính là lý do ngữ pháp "một lượt phát biểu = trạng thái đầy đủ" hoạt động được:
    phát biểu lại y hệt là một hành động RỖNG, không phải một lần đặt lại lệnh.
    """

    __slots__ = ("mo_hinh", "mua", "ban", "ton_kho", "tien", "phi_da_tra",
                 "so_khop", "kl_da_khop", "so_dat", "so_huy", "so_tu_choi",
                 "giay_mu_co_lenh", "_mu_tu", "_dang_mu",
                 "_bid", "_bkl", "_ask", "_akl", "_khop_bid", "_khop_ask", "_t")

    def __init__(self, mo_hinh):
        self.mo_hinh = mo_hinh
        self.mua = None                   # đúng MỘT lệnh mỗi phía — xem `dong_bo`
        self.ban = None
        self.ton_kho = 0.0
        self.tien = 0.0                   # tiền mặt đã thực nhận/chi, ĐÃ trừ phí
        self.phi_da_tra = 0.0
        self.so_khop = 0
        self.kl_da_khop = 0.0
        self.so_dat = 0
        self.so_huy = 0
        self.so_tu_choi = 0
        self.giay_mu_co_lenh = 0.0
        self._mu_tu = 0
        self._dang_mu = False
        # Sổ lệnh lần trước — để BIẾT khối lượng ở mức của ta vừa giảm bao nhiêu.
        self._bid = self._ask = NAN
        self._bkl = self._akl = 0.0
        # Khối lượng đã khớp ở mức của ta KỂ TỪ bản ghi sổ gần nhất. Phần giảm nào có
        # lệnh khớp giải thích thì là khớp thật; phần còn lại mới là huỷ.
        self._khop_bid = 0.0
        self._khop_ask = 0.0
        self._t = 0

    # ---------------------------------------------------------------- báo giá

    def dong_bo(self, t, bid, bid_kl, ask, ask_kl):
        """Đưa sổ của ta về đúng báo giá chiến lược vừa phát biểu.

        `bid_kl`/`ask_kl` = 0 nghĩa là KHÔNG treo phía đó. Không cần động từ "rút".

        Trả về số lệnh phải đặt lại (0 = lượt này không mất vị trí hàng đợi nào)."""
        return (self._dong_bo_mot(MUA, t, bid, bid_kl)
                + self._dong_bo_mot(BAN, t, ask, ask_kl))

    def _dong_bo_mot(self, ben, t, gia, kl):
        cu = self.mua if ben == MUA else self.ban
        if not (kl > 0) or not _huu_han(gia):
            if cu is not None:
                self._go(ben, BI_HUY)
            return 0

        # ĐƯỜNG TẮT: vẫn đúng câu vừa nói lượt trước, và lệnh vẫn đang nằm đó.
        #
        # "Phát biểu lại y hệt là hành động RỖNG" vốn đã là ngữ nghĩa; chỗ này chỉ làm
        # nó RỖNG THẬT — khỏi làm tròn, khỏi so, khỏi gì cả. Đáng làm vì sổ lệnh thật
        # đổi KHỐI LƯỢNG thường xuyên hơn đổi GIÁ rất nhiều, nên phần lớn sự kiện sẽ
        # sinh ra đúng cái báo giá cũ.
        #
        # ⚠ So `gia_tho` (giá THÔ chiến lược đòi) chứ không so giá đã làm tròn: hai giá
        # thô khác nhau có thể tròn về cùng một mức, và lúc đó ta muốn đi đường tắt —
        # nhưng phải chắc chắn là cùng một phép tính cho ra cùng một bit.
        #
        # Điều kiện "lệnh vẫn đang nằm đó" (`cu is not None`) là phần bắt buộc: nếu
        # lượt trước bị post-only TỪ CHỐI thì không có lệnh nào, và sổ lệnh đã đổi
        # (chính vì thế mới có sự kiện này) nên lần này có thể đặt được. Đi tắt lúc đó
        # là bỏ luôn cơ hội đặt lại, vĩnh viễn.
        if cu is not None and cu.gia_tho == gia and cu.kl == kl:
            return 0

        gia_tho, gia = gia, self.mo_hinh.lam_tron(gia, ben)
        if cu is not None and cu.gia == gia:
            # ---- CÙNG GIÁ: giữ vị trí hàng đợi, và đây là ca đáng giá nhất ----
            if kl <= cu.kl:
                cu.gia_tho = gia_tho
                # GIẢM khối lượng giữ được thứ tự ưu tiên ở gần như mọi sàn — lệnh vẫn
                # là lệnh cũ, chỉ bớt số. Không đụng `hang_doi`.
                cu.kl = kl
                cu.con_lai = min(cu.con_lai, kl)
                return 0
            # TĂNG khối lượng thì MẤT ưu tiên: sàn coi phần thêm là lệnh mới đến sau, và
            # phần lớn sàn (Binance trong đó) không có amend giữ chỗ — sửa = huỷ + đặt.
            # Mô hình theo hướng nghiêm khắc hơn: đặt lại cả lệnh.
            self._go(ben, BI_HUY)
            cu = None

        if cu is not None:
            self._go(ben, BI_HUY)         # đổi giá = về cuối hàng, không có đường tắt
        return 1 if self._dat(ben, t, gia, kl, gia_tho) else 0

    def _dat(self, ben, t, gia, kl, gia_tho=None):
        """Đặt một lệnh POST-ONLY.

        ⚠ TỪ CHỐI chứ không âm thầm thành lệnh chủ động. Báo giá lấn qua phía đối diện
        thì sàn từ chối thẳng (post-only), và một chiến lược bị từ chối liên tục là
        chiến lược HỎNG — phải nhìn thấy được (`so_tu_choi`), không phải lặng lẽ biến
        thành một chiến lược khác ăn phí taker."""
        if ben == MUA:
            lan = _huu_han(self._ask) and gia >= self._ask
        else:
            lan = _huu_han(self._bid) and gia <= self._bid
        if lan:
            self.so_tu_choi += 1
            return False

        hang_doi = self._hang_doi_ban_dau(ben, gia)
        lenh = Lenh(ben, gia, kl, hang_doi, t, t + self.mo_hinh.tre_ra_ms, gia_tho)
        if ben == MUA:
            self.mua = lenh
        else:
            self.ban = lenh
        self.so_dat += 1
        return True

    def _hang_doi_ban_dau(self, ben, gia):
        """Bao nhiêu khối lượng đứng TRƯỚC ta ngay lúc đặt — BA CA, và chỉ ca thứ ba
        cần giả định:

          1. treo TỐT HƠN đỉnh → ta thành đỉnh mới → hàng đợi **0**. Chắc chắn.
          2. treo ĐÚNG đỉnh    → cả khối lượng đang hiện đứng trước ta. Cũng chắc chắn:
             ta vừa mới tới, nên mọi người đang ở đó đều tới trước.
          3. treo SÂU HƠN đỉnh → `bookTicker` không thấy tầng đó. Không biết, và không
             có cách nào biết. `phan_muc_sau` × khối lượng đỉnh là một con số MƯỢN TẠM
             — mượn của tầng trên vì không có gì gần hơn để mượn."""
        dinh, dinh_kl = (self._bid, self._bkl) if ben == MUA else (self._ask, self._akl)
        if not _huu_han(dinh):
            return 0.0
        tot_hon = gia > dinh if ben == MUA else gia < dinh
        if tot_hon:
            return 0.0
        if gia == dinh:
            return float(dinh_kl)
        return float(dinh_kl) * self.mo_hinh.phan_muc_sau

    def _go(self, ben, ly_do):
        if ben == MUA:
            self.mua = None
        else:
            self.ban = None
        if ly_do == BI_HUY:
            self.so_huy += 1

    # ------------------------------------------------------------- sự kiện

    def buoc(self, sk):
        """Một sự kiện đi qua. Trả tuple các lần khớp (rỗng là chuyện thường)."""
        loai = sk.loai
        self._t = sk.t
        if loai == phat_lai.KHOP:
            # ⚠ Chặn khớp trong lỗ hổng. `PhatLai` không bao giờ phát sự kiện giữa hai
            # mốc lỗ hổng, nên nhánh này gần như không chạy — nhưng docstring đầu file
            # HỨA "không cho khớp trong lỗ hổng", và một lời hứa mà mã không giữ thì
            # sớm muộn có người dựa vào nó. Một phép so mỗi sự kiện là giá quá rẻ để
            # câu ấy thành sự thật thay vì thành ý định.
            return RONG if self._dang_mu else self._an_lenh_khop(sk)
        if loai == phat_lai.SO:
            return self._doc_so(sk)
        if loai == phat_lai.MO_LO_HONG:
            self._dang_mu = True
            self._mu_tu = sk.t
            self._bid = self._ask = NAN
            return RONG
        if loai == phat_lai.DONG_LO_HONG:
            if self._dang_mu:
                # ĐẾM thời gian mù CÓ LỆNH TREO. Trong khoảng đó sàn vẫn khớp, ta chỉ
                # không nhìn thấy — nên kết quả phải nói ra chỗ nó không biết. Im lặng
                # coi như không có gì xảy ra là nói dối theo hướng có lợi.
                if self.mua is not None or self.ban is not None:
                    self.giay_mu_co_lenh += (sk.t - self._mu_tu) / 1000.0
                self._dang_mu = False
            return RONG
        return RONG

    def _an_lenh_khop(self, sk):
        """Có người khớp — ăn dần hàng đợi, rồi mới tới lượt ta.

        `mua_chu_dong` = bên MUA là bên chủ động, tức nó ăn vào phía BÁN của sổ. Lệnh
        BÁN của ta bị nó chạm; lệnh MUA của ta không liên quan."""
        gia, kl = sk.gia, sk.kl
        if sk.mua_chu_dong:
            self._khop_ask += kl
            return self._cham(self.ban, BAN, gia, kl, sk.t)
        self._khop_bid += kl
        return self._cham(self.mua, MUA, gia, kl, sk.t)

    def _cham(self, lenh, ben, gia, kl, t):
        if lenh is None or t < lenh.song_luc:
            # CHƯA SỐNG thì không khớp được. Đây chính là chỗ độ trễ ra tốn tiền thật:
            # ta quyết ở thời điểm này nhưng lệnh chỉ tới sàn sau `tre_ra_ms`, và mọi
            # thứ xảy ra trong quãng đó là cơ hội ta không với tới.
            return RONG

        if ben == MUA:
            if gia > lenh.gia:
                return RONG               # khớp ở mức mua TỐT HƠN — chưa xuống tới ta
            xuyen = gia < lenh.gia
        else:
            if gia < lenh.gia:
                return RONG
            xuyen = gia > lenh.gia

        if xuyen:
            # ĐÃ KHỚP XUYÊN QUA MỨC CỦA TA. Sàn khớp theo giá tốt trước, nên để chạm
            # tới một mức xấu hơn thì mọi thứ ở mức của ta đã phải hết sạch — kể cả ta.
            # Đây là mặt trái đắt nhất của market making: ta được khớp ĐÚNG LÚC giá
            # đang chạy khỏi ta.
            return self._khop(lenh, ben, lenh.con_lai)

        # Cùng mức: ăn hàng đợi trước đã. Phần khớp CHẮC CHẮN đi từ đầu hàng — đây là
        # điều duy nhất về hàng đợi mà dữ liệu L1 nói chắc được.
        if lenh.hang_doi > 0:
            an = min(lenh.hang_doi, kl)
            lenh.hang_doi -= an
            kl -= an
            if kl <= 0:
                return RONG
        return self._khop(lenh, ben, min(kl, lenh.con_lai))

    def _khop(self, lenh, ben, kl):
        if not (kl > 0):
            return RONG
        gia = lenh.gia
        phi = kl * gia * self.mo_hinh.phi_maker_bps / 10000.0
        self.ton_kho += kl * ben
        self.tien -= kl * gia * ben + phi
        self.phi_da_tra += phi
        self.so_khop += 1
        self.kl_da_khop += kl
        lenh.con_lai -= kl
        if lenh.con_lai <= 0:
            self._go(ben, KHOP_HET)
        # ⚠ ÉP VỀ SỐ CỦA PYTHON TẠI ĐÂY. Giá và khối lượng vào từ numpy (`PhatLai` cố
        # ý giữ `np.float64` để khỏi ép kiểu mười triệu lần một ngày), mà `np.float64`
        # thì `json.dumps` nghẹn. Ô khớp CHÍNH LÀ chỗ dữ liệu rời vòng lặp nóng — mỗi
        # lần khớp một phép ép, không phải mỗi sự kiện — nên đây đúng là biên phải dọn,
        # thay vì bắt nhật ký, cầu nối JS và mọi chỗ đọc sau đó nhớ tự dọn lấy.
        return ({"t": int(self._t), "ben": ben, "gia": float(gia), "kl": float(kl),
                 "phi": float(phi), "ton_kho": float(self.ton_kho)},)

    def _doc_so(self, sk):
        """Sổ lệnh đổi ở đỉnh — ba việc, theo đúng thứ tự này.

        Thứ tự có ý nghĩa: phải suy hàng đợi TRƯỚC khi ghi đè sổ cũ, và phải kiểm tra
        khớp-nghịch SAU khi đã có sổ mới."""
        bid, bkl, ask, akl = sk.bid, sk.bid_kl, sk.ask, sk.ask_kl
        self._suy_hang_doi(self.mua, MUA, bid, bkl)
        self._suy_hang_doi(self.ban, BAN, ask, akl)
        self._bid, self._bkl, self._ask, self._akl = bid, bkl, ask, akl
        self._khop_bid = self._khop_ask = 0.0
        return self._khop_nghich(sk.t)

    def _suy_hang_doi(self, lenh, ben, dinh_moi, kl_moi):
        """Khối lượng ở mức của ta vừa giảm — do khớp hay do huỷ, và huỷ ở đâu?

        Chỉ suy được khi lệnh của ta nằm ĐÚNG ở đỉnh — chỗ duy nhất `bookTicker` nhìn
        thấy."""
        if lenh is None or not _huu_han(dinh_moi):
            return
        dinh_cu, kl_cu = (self._bid, self._bkl) if ben == MUA else (self._ask, self._akl)
        if not _huu_han(dinh_cu):
            return

        # ĐỈNH BỎ QUA MỨC CỦA TA → mọi người ở mức đó đã đi hết. Ta còn lại một mình ở
        # đầu hàng. (Trong sổ THẬT ta sẽ là đỉnh mới — nhưng bản ghi không biết ta tồn
        # tại, xem "không mô hình hoá tác động" ở đầu file.)
        bo_qua = dinh_moi < lenh.gia if ben == MUA else dinh_moi > lenh.gia
        if bo_qua and (dinh_cu >= lenh.gia if ben == MUA else dinh_cu <= lenh.gia):
            lenh.hang_doi = 0.0
            return

        if dinh_cu != lenh.gia or dinh_moi != lenh.gia:
            return                        # không ở đỉnh: không thấy gì để mà suy

        giam = float(kl_cu) - float(kl_moi)
        if giam <= 0:
            return                        # tăng = người mới xếp SAU ta, không đổi gì
        da_khop = self._khop_bid if ben == MUA else self._khop_ask
        huy = giam - da_khop              # phần không có lệnh khớp nào giải thích
        if huy > 0:
            # ⚠ ĐÂY LÀ NÚM VẶN. Huỷ ở trước ta thì ta tiến lên; ở sau ta thì không đổi
            # gì. Dữ liệu L1 không phân biệt được, và sẽ không bao giờ phân biệt được.
            lenh.hang_doi = max(0.0, lenh.hang_doi - huy * self.mo_hinh.phan_huy_truoc)

    def _khop_nghich(self, t):
        """Sổ lệnh vượt qua mức của ta mà KHÔNG có lệnh khớp nào — vẫn phải khớp cho ta.

        Ask tụt xuống bằng hoặc thấp hơn giá MUA của ta nghĩa là có người sẵn sàng bán
        ở mức đó. Trong một sàn thật thì hai lệnh ấy đã khớp nhau rồi — bản ghi thấy
        ngược lại chỉ vì lệnh của ta không có trong bản ghi.

        Bỏ qua ca này là để chiến lược ôm một lệnh mua trong khi thị trường bán tháo
        ngay dưới mũi mà không khớp gì — tức backtest vẽ ra một sự an toàn không có
        thật, đúng chỗ thua lỗ thật sự xảy ra."""
        ra = RONG
        m = self.mua
        if m is not None and t >= m.song_luc and _huu_han(self._ask) \
                and self._ask <= m.gia:
            ra = self._khop(m, MUA, m.con_lai)
        b = self.ban
        if b is not None and t >= b.song_luc and _huu_han(self._bid) \
                and self._bid >= b.gia:
            ra = ra + self._khop(b, BAN, b.con_lai)
        return ra

    # -------------------------------------------------------------- kết quả

    def gia_tri(self, mid):
        """Vốn hiện tại = tiền mặt + tồn kho định giá theo `mid`.

        ⚠ Định giá theo `mid` là LẠC QUAN khi còn tồn kho: xả thật thì phải trả spread
        và phí. Con số duy nhất không cần dè dặt là con số ở thời điểm tồn kho = 0."""
        return self.tien + self.ton_kho * mid if _huu_han(mid) else self.tien

    def tom_tat(self, mid=NAN):
        return {
            "ton_kho": self.ton_kho,
            "tien": self.tien,
            "gia_tri": self.gia_tri(mid),
            "phi_da_tra": self.phi_da_tra,
            "so_khop": self.so_khop,
            "kl_da_khop": self.kl_da_khop,
            "so_dat": self.so_dat,
            "so_huy": self.so_huy,
            "so_tu_choi": self.so_tu_choi,
            "giay_mu_co_lenh": self.giay_mu_co_lenh,
            "gia_dinh": self.mo_hinh.tom_tat(),
        }
