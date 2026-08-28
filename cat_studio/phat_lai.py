"""PHÁT LẠI — biến hai luồng đã ghi thành MỘT dòng sự kiện cho bộ chạy.

    nguon_tick   hai mảng rời: sổ lệnh · khớp lệnh
    file này     một dòng sự kiện, đúng thứ tự CHIẾN LƯỢC ĐÃ THẤY
    bộ chạy      chỉ thấy `buoc()` — không biết dữ liệu từ file hay từ WebSocket

Đây là chỗ giữ lời hứa "test như nào thì live như thế": live sẽ có một lớp cùng bề mặt
(`buoc()` + mấy thuộc tính trạng thái), nên bộ chạy không phân biệt được hai đường. Đó
đúng là thứ `bo_chay.mot_nhip` cũ đánh đổi mọi thứ để giữ.

════════════════════════════════════════════════════════════════════════════
LUẬT MỘT — TRỤC THỜI GIAN LÀ `t_ta`, KHÔNG PHẢI `T`
════════════════════════════════════════════════════════════════════════════
`T` là lúc SÀN đổi sổ lệnh. `t_ta` là lúc TA nhận được. Chênh nhau ~207 ms (đo được,
xem `nguon_tick`). Chiến lược chỉ quyết định được bằng thứ nó ĐÃ THẤY, nên dòng sự
kiện phải xếp theo `t_ta`.

Xếp theo `T` là **cho chiến lược thấy tương lai** — nó sẽ phản ứng với một cú khớp
trước khi gói tin về cú khớp đó tới nơi. Backtest đẹp lên, live thì không. Đây là lỗi
nhìn trước tương lai ở dạng tinh vi nhất: mọi con số đều có thật, chỉ thứ tự là bịa.

Và hai luồng ĐẢO THỨ TỰ ĐƯỢC so với `T`: một cú khớp ở `T=1000` có thể tới lúc
`t_ta=1210`, trong khi một thay đổi sổ ở `T=1005` tới lúc `t_ta=1190`. Ta thấy cái sau
trước. Xếp theo `T` là dựng lại một trật tự chưa từng xảy ra với ta.

`T` vẫn giữ trong từng sự kiện — để ĐO (độ trễ, đối chiếu với sàn), không để quyết định.

════════════════════════════════════════════════════════════════════════════
LUẬT HAI — LỖ HỔNG LÀ MỘT SỰ KIỆN, KHÔNG PHẢI MỘT KHOẢNG TRỐNG
════════════════════════════════════════════════════════════════════════════
Mất kết nối 40 giây mà phát lại cứ nhảy qua thì backtest tin rằng thị trường liền
mạch, còn ngoài đời thì lệnh của ta nằm chơ vơ trên sàn suốt 40 giây đó với một cái sổ
lệnh ta không nhìn thấy.

Nên lỗ hổng được bắn ra thành `MO_LO_HONG` / `DONG_LO_HONG`. Bộ chạy phản ứng đúng như
ngoài đời: mất feed thì rút báo giá. Và sau `DONG_LO_HONG`, **sổ lệnh trở lại trạng
thái CHƯA BIẾT** (`co_so = False`) cho tới bản ghi `so` kế tiếp — vì trong lúc mù, giá
đã đi đâu thì ta không biết.

════════════════════════════════════════════════════════════════════════════
LUẬT BA — TẤT ĐỊNH
════════════════════════════════════════════════════════════════════════════
Cùng dữ liệu vào thì cùng thứ tự ra, mọi lần. Hoà `t_ta` thì phá hoà bằng `(T, loại,
chỉ số trong luồng)` — cả ba đều có sẵn, không cái nào phụ thuộc thứ tự dict hay tốc
độ máy.

⚠ Trong cùng một mili giây ta KHÔNG biết thứ tự thật. `t_ta` chỉ mịn tới ms, mà 115
bản ghi/giây thì đụng nhau thường xuyên. Phá hoà bằng `T` là phỏng đoán TỐT NHẤT có
thể — không phải sự thật. Ai đọc kết quả backtest phải biết điều đó.
"""
import numpy as np

from . import nguon_tick as nt

#: Loại sự kiện. Số nguyên nhỏ, không phải chuỗi — bộ chạy so hàng triệu lần.
SO = 1            #: sổ lệnh đổi ở đỉnh
KHOP = 2          #: có người khớp
MO_LO_HONG = 3    #: mất dữ liệu từ đây
DONG_LO_HONG = 4  #: dữ liệu trở lại — nhưng sổ lệnh CHƯA BIẾT tới bản ghi `so` kế

TEN_LOAI = {SO: "sổ lệnh", KHOP: "khớp", MO_LO_HONG: "mở lỗ hổng",
            DONG_LO_HONG: "đóng lỗ hổng"}

NAN = float("nan")


class PhatLai:
    """Một dòng sự kiện, đọc bằng `buoc()`.

        p = PhatLai.tu_file("TRUMPUSDT", "2026-08-28", "2026-08-28")
        while (loai := p.buoc()) is not None:
            if loai is SO and p.co_so:
                ...  # p.bid, p.bid_kl, p.ask, p.ask_kl
            elif loai is KHOP:
                ...  # p.gia, p.kl, p.mua_chu_dong

    Trạng thái nằm trên đối tượng chứ không gói vào một dict trả về: mỗi sự kiện mà đẻ
    một dict là mười triệu dict một ngày, và bộ gom rác sẽ ăn hết phần thời gian mà lẽ
    ra dành cho chiến lược.

    ⚠ `t` · `T` · `bid` · … là SỐ CỦA NUMPY (`np.int64` / `np.float64`), không phải
    `int`/`float` của Python — cố ý, vì ép kiểu mười triệu lần một ngày là tốn thật.
    Tính toán và so sánh thì y hệt; chỉ có `json.dumps` là nghẹn. Chỗ nào đưa ra ngoài
    (nhật ký, cầu nối JS) phải `int()` / `float()` tại đó.

    TỐC ĐỘ đã đo: **1,95 triệu sự kiện/giây** → một ngày (~10 triệu) mất ~5 s, một
    tháng ~2,5 phút. Đủ để lặp; nếu có ngày thành nút cổ chai thì chỗ sửa là đưa vòng
    lặp ra khỏi Python, không phải vặn thêm ở đây.
    """

    __slots__ = ("so", "khop", "lo_hong", "_nguon", "_ki", "_n", "_i",
                 "t", "T", "loai", "bid", "bid_kl", "ask", "ask_kl", "co_so",
                 "gia", "kl", "mua_chu_dong", "_trong_lo_hong",
                 "_s_t", "_s_T", "_s_bid", "_s_bkl", "_s_ask", "_s_akl",
                 "_k_t", "_k_T", "_k_gia", "_k_kl", "_k_mua", "_lh_moc")

    def __init__(self, so, khop, lo_hong=()):
        self.so = so
        self.khop = khop
        self.lo_hong = list(lo_hong)
        self._nguon, self._ki = _tron(so, khop, self.lo_hong)
        self._n = len(self._nguon)
        self._i = 0

        # ⚠ TÁCH CỘT MỘT LẦN, và đây là chỗ đo được 5 lần chênh lệch.
        #
        # Bản đầu viết `r = self.so[k]` rồi `float(r["bid"])` — mỗi lần như vậy numpy
        # dựng một `np.void` trung gian cho cả bản ghi. Đo trên 400.000 vòng:
        #
        #     a[k]["bid"]         1,18 triệu/s
        #     bid[k]  (cột sẵn)   6,17 triệu/s      ← nhanh gấp 5
        #     bid[k]  (.tolist()) 11,6 triệu/s      ← nhanh gấp 10, nhưng ~160 MB/cột
        #                                            cho một ngày → cả GB, không đáng
        #
        # `so["bid"]` là một VIEW, không chép byte nào, nên tách cột không tốn bộ nhớ.
        self._s_t, self._s_T = so["t_ta"], so["T"]
        self._s_bid, self._s_bkl = so["bid"], so["bid_kl"]
        self._s_ask, self._s_akl = so["ask"], so["ask_kl"]
        self._k_t, self._k_T = khop["t_ta"], khop["T"]
        self._k_gia, self._k_kl = khop["gia"], khop["kl"]
        self._k_mua = khop["mua_chu_dong"]
        self._lh_moc = [(int(l["tu"]), int(l["den"])) for l in self.lo_hong]

        self.t = self.T = 0
        self.loai = 0
        # SỔ LỆNH CHƯA BIẾT cho tới bản ghi `so` đầu tiên. Trả 0 hay NaN mà không nói
        # gì là mời chiến lược báo giá quanh một cái giá không tồn tại — nên có hẳn
        # một lá cờ, và mọi chỗ đọc phải hỏi nó trước.
        self.co_so = False
        self.bid = self.bid_kl = self.ask = self.ask_kl = NAN
        self.gia = self.kl = NAN
        self.mua_chu_dong = False
        self._trong_lo_hong = False

    # ------------------------------------------------------------------ dựng
    @classmethod
    def tu_file(cls, symbol, tu_ngay, den_ngay):
        """Đọc từ đĩa. Gom cả sổ lỗ hổng của MỌI ngày trong dải — quên nó thì phát lại
        chạy êm qua chỗ mù và không ai biết."""
        so = nt.doc(symbol, tu_ngay, den_ngay, "so")
        khop = nt.doc(symbol, tu_ngay, den_ngay, "khop")
        lh = []
        for n in nt._dai_ngay(tu_ngay, den_ngay):
            lh += nt.doc_lo_hong(symbol, n)
        return cls(so, khop, lh)

    # ------------------------------------------------------------------ đi
    def buoc(self):
        """Sự kiện kế tiếp. Trả LOẠI, hoặc `None` khi hết.

        Cập nhật trạng thái TRƯỚC khi trả về, nên đọc thuộc tính ngay sau `buoc()` là
        thấy thế giới ở đúng thời điểm đó."""
        i = self._i
        if i >= self._n:
            return None
        self._i = i + 1
        nguon = self._nguon[i]
        k = self._ki[i]

        if nguon == 0:
            self.t, self.T, self.loai = self._s_t[k], self._s_T[k], SO
            self.bid, self.bid_kl = self._s_bid[k], self._s_bkl[k]
            self.ask, self.ask_kl = self._s_ask[k], self._s_akl[k]
            # Một bản ghi `so` là thứ DUY NHẤT dựng lại được sổ lệnh sau lúc mù.
            self.co_so = True
        elif nguon == 1:
            self.t, self.T, self.loai = self._k_t[k], self._k_T[k], KHOP
            self.gia, self.kl = self._k_gia[k], self._k_kl[k]
            self.mua_chu_dong = self._k_mua[k]
        else:
            tu, den = self._lh_moc[k >> 1]
            mo = (k & 1) == 0
            self.t = self.T = tu if mo else den
            self.loai = MO_LO_HONG if mo else DONG_LO_HONG
            self._trong_lo_hong = mo
            if not mo:
                # Ra khỏi vùng mù: giá đã đi đâu trong lúc đó thì ta không biết. Giữ
                # con số cũ mà không hạ cờ là để chiến lược báo giá quanh một cái sổ
                # lệnh của 40 giây trước.
                self.co_so = False
                self.bid = self.bid_kl = self.ask = self.ask_kl = NAN
        return self.loai

    # ------------------------------------------------------------------ đọc thêm
    @property
    def mid(self):
        """Giữa bid và ask. NaN khi chưa có sổ — và NaN thì mọi phép so đều False, nên
        một cổng đọc nhầm lúc mù sẽ TRƯỢT chứ không khớp bừa. Cùng kỷ luật `tinh_toan`
        cũ dùng cho chỉ báo chưa đủ dữ liệu."""
        return (self.bid + self.ask) / 2 if self.co_so else NAN

    @property
    def spread(self):
        return (self.ask - self.bid) if self.co_so else NAN

    @property
    def tre_ms(self):
        """Gói vừa rồi đi mất bao lâu. Đây là con số biến ngân sách độ trễ từ một ô
        người dùng gõ bừa thành một đại lượng đo được."""
        return self.t - self.T

    def con_lai(self):
        return self._n - self._i

    def tom_tat(self):
        """Dòng sự kiện này gồm những gì — nhìn trước khi chạy, khỏi backtest mù."""
        return {
            "so_su_kien": self._n,
            "so": int(len(self.so)),
            "khop": int(len(self.khop)),
            "lo_hong": len(self.lo_hong),
            "ms_lo_hong": int(sum(l["den"] - l["tu"] for l in self.lo_hong)),
            "tu": int(self.so["t_ta"][0]) if len(self.so) else None,
            "den": int(self.so["t_ta"][-1]) if len(self.so) else None,
        }


def _tron(so, khop, lo_hong):
    """Thứ tự phát lại — tính MỘT LẦN bằng numpy, rồi đi tuần tự.

    Trả mảng `(nguồn, chỉ_số)`: nguồn 0 = sổ, 1 = khớp, 2 = lỗ hổng (chỉ số chẵn là mở,
    lẻ là đóng).

    Sắp bằng `lexsort` chứ không trộn bằng vòng lặp Python: mười triệu sự kiện một ngày
    thì phép sắp phải nằm trong C. Khoá xếp từ YẾU tới MẠNH, nên đọc ngược từ dưới lên:

        t_ta     ← mạnh nhất: thứ tự TA THẤY
        T        ← hoà `t_ta` thì tin vào thứ tự ở sàn
        nguồn    ← hoà cả hai thì sổ lệnh trước khớp lệnh (thấy giá mới rồi mới thấy ai ăn)
        chỉ số   ← chốt cuối, để KHÔNG BAO GIỜ có hai cách sắp cho cùng một bộ dữ liệu
    """
    n_so, n_khop = len(so), len(khop)
    n_lh = len(lo_hong) * 2

    t = np.empty(n_so + n_khop + n_lh, dtype=np.int64)
    T = np.empty_like(t)
    nguon = np.empty_like(t)
    chi_so = np.empty_like(t)

    a, b = 0, n_so
    t[a:b], T[a:b], nguon[a:b] = so["t_ta"], so["T"], 0
    chi_so[a:b] = np.arange(n_so)

    a, b = b, b + n_khop
    t[a:b], T[a:b], nguon[a:b] = khop["t_ta"], khop["T"], 1
    chi_so[a:b] = np.arange(n_khop)

    if n_lh:
        a, b = b, b + n_lh
        moc = np.empty(n_lh, dtype=np.int64)
        for i, lh in enumerate(lo_hong):
            moc[2 * i], moc[2 * i + 1] = int(lh["tu"]), int(lh["den"])
        t[a:b] = T[a:b] = moc
        nguon[a:b] = 2
        chi_so[a:b] = np.arange(n_lh)

    thu_tu = np.lexsort((chi_so, nguon, T, t))
    # HAI DANH SÁCH SONG SONG, không phải một danh sách tuple: `buoc()` chạy mười
    # triệu lần một ngày, và mỗi lần tháo một tuple là một lần cấp phát thừa.
    # `.tolist()` ở đây rẻ — chỉ hai cột số nguyên nhỏ.
    return nguon[thu_tu].tolist(), chi_so[thu_tu].tolist()
