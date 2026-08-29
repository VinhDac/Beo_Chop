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
LUẬT BA — HIỆU CHỈNH ĐỒNG HỒ, VÀ CHƯA ĐO THÌ KHÔNG ĐOÁN
════════════════════════════════════════════════════════════════════════════
`t_ta` đóng dấu bằng đồng hồ MÁY, `T` đến từ SÀN. Hai đồng hồ đó lệch nhau (đo được
−121 ms ngày 2026-08-28), nên trừ thẳng `t_ta − T` là ra một độ trễ sai đúng chừng ấy.

    thời điểm THẬT  =  t_ta − lệch          (`lệch` = giờ máy − giờ sàn)

Bộ ghi đo độ lệch vài phút một lần và cất cạnh dữ liệu (`nguon_tick.bang_lech`). Ở đây
tra bảng đó và trừ ra — dùng lần đo GẦN NHẤT TRƯỚC mỗi sự kiện, không nội suy: giữa hai
lần đo, đồng hồ trôi từ từ chứ không nhảy, mà nội suy thì giả vờ biết một thứ không đo.

⚠ SỬA CẢ CỘT MỘT LẦN, không sửa từng sự kiện. Bản đầu gọi một hàm tra bảng trong
`buoc()` và tốc độ tụt từ 1,97 xuống 1,42 triệu/s — 28 % chỉ để trừ một con số. Giờ
`np.searchsorted` chạy một phát trên cả cột lúc dựng, và `buoc()` không tốn thêm gì.
Đúng bài học `a[k]["bid"]`: chỗ nào lặp mười triệu lần thì phải nằm trong numpy.

Sửa cả cột còn ĐÚNG HƠN: thứ tự trộn cũng phải theo mốc ĐÃ hiệu chỉnh, không thì hai
luồng xếp theo một trục thời gian mà chính nó đang lệch.

⚠ **CHƯA ĐO LẦN NÀO → KHÔNG HIỆU CHỈNH GÌ**, và `co_dong_ho = False` nói ra điều đó.
Không lấy 0 làm mặc định: "đo được là 0" nghĩa là đồng hồ đúng, còn "chưa đo" nghĩa là
ta không biết — gộp hai thứ đó là biến một chỗ không biết thành một lời khẳng định.

════════════════════════════════════════════════════════════════════════════
LUẬT BỐN — TẤT ĐỊNH
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

#: "Không còn ảnh độ sâu nào nữa" — một `int` LỚN, KHÔNG phải `float("inf")`.
#:
#: ⚠ ĐÃ ĐO, và chênh lệch không nhỏ chút nào. `self.t` là `np.int64`, và phép so nó
#: với một số của Python đi qua bộ máy vô hướng của numpy:
#:
#:     np.int64 >= float      1210 ns      ← `float("inf")`
#:     np.int64 >= int          46 ns      ← rẻ hơn 26 lần
#:     np.int64 >= np.int64     31 ns
#:
#: Phép so đó chạy MỖI SỰ KIỆN. Bản đầu dùng `float("inf")` cho gọn và kéo lớp phát
#: lại từ 1,83 xuống 0,53 triệu sự kiện/giây — chậm gấp ba, vì đúng một hằng số.
#: `1 << 62` lớn hơn mọi mốc mili-giây trong vài chục triệu năm tới.
VO_HAN = 1 << 62

#: Loại sự kiện. Số nguyên nhỏ, không phải chuỗi — bộ chạy so hàng triệu lần.
SO = 1            #: sổ lệnh đổi ở đỉnh
KHOP = 2          #: có người khớp
MO_LO_HONG = 3    #: mất dữ liệu từ đây
DONG_LO_HONG = 4  #: dữ liệu trở lại — nhưng sổ lệnh CHƯA BIẾT tới bản ghi `so` kế

TEN_LOAI = {SO: "book", KHOP: "trade", MO_LO_HONG: "gap opens",
            DONG_LO_HONG: "gap closes"}

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

    __slots__ = ("so", "khop", "sau", "lo_hong", "_nguon", "_ki", "_n", "_i",
                 "t", "T", "loai", "bid", "bid_kl", "ask", "ask_kl", "co_so",
                 "gia", "kl", "mua_chu_dong", "_trong_lo_hong",
                 "_s_t", "_s_T", "_s_bid", "_s_bkl", "_s_ask", "_s_akl",
                 "_k_t", "_k_T", "_k_gia", "_k_kl", "_k_mua", "_lh_moc",
                 "_d_t", "_d_bid", "_d_bkl", "_d_ask", "_d_akl", "_d_n", "_d_i",
                 "_d_ke", "_d_gb", "_d_vb", "_d_ga", "_d_va",
                 "_dh_moc", "_dh_lech", "co_dong_ho", "lech_ms")

    def __init__(self, so, khop, lo_hong=(), dong_ho=None, sau=None):
        self.so = so
        self.khop = khop
        #: ⚠ ĐỘ SÂU KHÔNG PHẢI MỘT SỰ KIỆN — nó là một BẢNG TRA, và đó là quyết định.
        #:
        #: Nhét `sau` vào dòng sự kiện thì mỗi ảnh chụp lại làm chiến lược chạy thêm
        #: một lượt: +10 % số lượt (6 ảnh/s so với 56 bản ghi sổ/s), tức ĐỔI HÀNH VI
        #: của mọi chiến lược đã viết, để đổi lấy một thứ chỉ cần tra cứu.
        #:
        #: Mà thứ cần tra là "lúc ta đặt lệnh, mức giá đó đang có bao nhiêu" — một câu
        #: hỏi tại MỘT thời điểm. Nên giữ một con trỏ chạy theo dòng sự kiện, luôn trỏ
        #: vào ảnh chụp cuối cùng có `t_ta` không vượt quá hiện tại. Xem `kl_tai_muc`.
        self.sau = sau
        self.lo_hong = list(lo_hong)

        # HIỆU CHỈNH ĐỒNG HỒ TRƯỚC KHI TRỘN. Thứ tự phát phải theo mốc ĐÃ sửa, không
        # thì hai luồng được xếp theo một trục thời gian mà chính nó đang lệch.
        moc, lech = dong_ho if dong_ho else ([], [])
        self.co_dong_ho = bool(moc)
        #: Lệch đồng hồ TRUNG VỊ đã áp, tính bằng ms. `co_dong_ho` mới là thứ phân
        #: biệt "đo được đúng 0" với "chưa đo" — hai chuyện khác hẳn nhau.
        self.lech_ms = float(np.median(lech)) if moc else 0.0
        s_t = _sua_dong_ho(so["t_ta"], moc, lech)
        k_t = _sua_dong_ho(khop["t_ta"], moc, lech)
        self._lh_moc = [(int(l["tu"]), int(l["den"])) for l in self.lo_hong]

        self._nguon, self._ki = _tron(s_t, so["T"], k_t, khop["T"], self._lh_moc)
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
        self._s_t, self._s_T = s_t, so["T"]
        self._s_bid, self._s_bkl = so["bid"], so["bid_kl"]
        self._s_ask, self._s_akl = so["ask"], so["ask_kl"]
        self._k_t, self._k_T = k_t, khop["T"]
        self._k_gia, self._k_kl = khop["gia"], khop["kl"]
        self._k_mua = khop["mua_chu_dong"]

        # ĐỘ SÂU — cùng phép hiệu chỉnh đồng hồ với hai luồng kia, không thì con trỏ
        # chạy theo một trục thời gian khác với trục đang phát.
        if sau is not None and len(sau):
            self._d_t = _sua_dong_ho(sau["t_ta"], moc, lech)
            self._d_bid, self._d_bkl = sau["bid"], sau["bid_kl"]
            self._d_ask, self._d_akl = sau["ask"], sau["ask_kl"]
            self._d_n = len(self._d_t)
        else:
            self._d_t = self._d_bid = self._d_bkl = None
            self._d_ask = self._d_akl = None
            self._d_n = 0
        #: −1 = CHƯA có ảnh nào ở hoặc trước hiện tại. Khác hẳn 0 (đã có ảnh đầu tiên).
        self._d_i = -1
        #: Mốc của ảnh KẾ TIẾP, ép sẵn về `int` của Python. Xem `VO_HAN`.
        #:
        #: Vòng lặp chính chạm cái này mười triệu lần một ngày, và `self._d_t[j+1]` là
        #: một phép đọc numpy — dựng một `np.int64` mỗi lần. Giữ sẵn một `int` thì ca
        #: thường (chưa tới ảnh kế) chỉ còn đúng một phép so.
        self._d_ke = int(self._d_t[0]) if self._d_n else VO_HAN
        #: ẢNH CHỤP ĐANG NGỰ TRỊ, đã đổ sang list của Python.
        #:
        #: ĐỔI MỘT LẦN MỖI ẢNH, không đổi mỗi lần tra: `kl_tai_muc` được gọi mỗi lần
        #: đặt lệnh (nửa triệu lần cho hai ngày), còn ảnh chỉ đổi ~6 lần/giây. Đúng
        #: dòng `.tolist()` ở bảng đo đầu file, chỉ khác là mỗi lần 20 phần tử nên
        #: không tốn bộ nhớ gì.
        #:
        #: ⚠ Đo rồi: chỗ này KHÔNG phải chỗ tốn. Phép tra chỉ chạy khi treo sâu hơn
        #: đỉnh, còn phần chậm nằm hết ở con trỏ trong `buoc` — xem `VO_HAN`. Giữ lại
        #: vì nó đúng và rẻ, nhưng đừng ghi công cho nó.
        self._d_gb = self._d_vb = self._d_ga = self._d_va = None


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
        """Đọc từ đĩa — dữ liệu, sổ lỗ hổng, VÀ bảng lệch đồng hồ.

        Gom cả ba của MỌI ngày trong dải. Quên sổ lỗ hổng thì phát lại chạy êm qua chỗ
        mù; quên bảng đồng hồ thì mọi mốc thời gian lệch đi mà không ai thấy."""
        so = nt.doc(symbol, tu_ngay, den_ngay, "so")
        khop = nt.doc(symbol, tu_ngay, den_ngay, "khop")
        # ĐỘ SÂU CÓ THỂ RỖNG, và đó là chuyện thường: luồng này bật sau hai luồng kia,
        # nên mọi ngày ghi trước đó không có nó. Rỗng thì `phan_muc_sau` quay về làm
        # núm đoán như cũ — và bảng Kết quả nói ra là nó đã phải đoán bao nhiêu lần.
        sau = nt.doc(symbol, tu_ngay, den_ngay, "sau")
        lh = []
        for n in nt._dai_ngay(tu_ngay, den_ngay):
            lh += nt.doc_lo_hong(symbol, n)
        return cls(so, khop, lh, nt.bang_lech(symbol, tu_ngay, den_ngay), sau=sau)

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

        # CON TRỎ ĐỘ SÂU — luôn trỏ vào ảnh chụp CUỐI CÙNG có `t_ta` ≤ hiện tại.
        #
        # ⚠ `<=`, không phải `<`, và không bao giờ nhìn tới ảnh phía trước: ảnh chụp ở
        # tương lai là thứ ta chưa thấy lúc đặt lệnh. Cùng nguyên tắc "báo giá đang ngự
        # trị" mà `bo_chay` dùng để chốt markout.
        #
        # Vòng `while` chứ không phải tìm nhị phân: con trỏ chỉ tiến, và mỗi sự kiện
        # trung bình tiến 0,1 bước (6 ảnh/s so với 56 bản ghi sổ/s), nên phép so ở đây
        # gần như luôn hỏng ngay lần đầu.
        # CON TRỎ TIẾN. Ca thường là một phép so số nguyên rồi thôi — xem `VO_HAN`
        # cho lý do mốc kết thúc là `int` chứ không phải `float("inf")`.
        if self.t >= self._d_ke:
            j, t, n = self._d_i, self.t, self._d_n
            while j + 1 < n and self._d_t[j + 1] <= t:
                j += 1
            self._d_i = j
            self._d_ke = int(self._d_t[j + 1]) if j + 1 < n else VO_HAN
            self._d_gb = self._d_bid[j].tolist()
            self._d_vb = self._d_bkl[j].tolist()
            self._d_ga = self._d_ask[j].tolist()
            self._d_va = self._d_akl[j].tolist()
        return self.loai

    def kl_tai_muc(self, ben_mua, gia):
        """Khối lượng ĐANG ĐỨNG ở đúng mức `gia`. `None` nghĩa là KHÔNG BIẾT.

        Đây là thứ biến `phan_muc_sau` từ một núm ĐOÁN thành một con số ĐO. Treo sâu
        hơn đỉnh mà mức đó đang có Q lot thì **toàn bộ Q** đứng trước ta — ta vừa mới
        tới, mọi người ở đó đều tới trước. Không có tỉ lệ nào phải đoán.

        BA CÂU TRẢ LỜI KHÁC NHAU, và gộp chúng lại là mất hết ý nghĩa:

            Q > 0     mức đó đang có Q lot                    ← đo được
            0.0       mức đó TRỐNG, ta sẽ đứng đầu hàng       ← cũng đo được
            None      mức đó nằm NGOÀI tầm nhìn 20 mức, hoặc
                      chưa có ảnh chụp nào                    ← không biết, phải đoán

        ⚠ Ảnh chụp cũ tối đa ~100 ms (sàn gộp `@depth20@100ms`). Trong quãng đó mức có
        thể đã đổi. Đây là phép đo có sai số, không phải sự thật tuyệt đối — nhưng một
        phép đo cũ 100 ms vẫn hơn hẳn một con số bịa."""
        g = self._d_gb if ben_mua else self._d_ga
        if g is None:
            return None
        v = self._d_vb if ben_mua else self._d_va
        # Bid xếp GIẢM dần, ask xếp TĂNG dần — nên quét từ đỉnh xuống và dừng ngay khi
        # đi quá mức cần tìm. Giá 0 là chỗ đệm khi sổ mỏng hơn 20 mức (xem `DT_SAU`).
        for i in range(len(g)):
            gi = g[i]
            if gi == 0.0:
                return None            # hết mức thật → sâu hơn tầm nhìn
            if gi == gia:
                return float(v[i])
            if (gi < gia) if ben_mua else (gi > gia):
                return 0.0             # đi quá rồi mà không gặp → mức này TRỐNG
        return None                    # sâu hơn cả mức thứ 20 → không nhìn thấy

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


def _sua_dong_ho(t_may, moc, lech):
    """Cột mốc máy → cột mốc THẬT, hiệu chỉnh bằng lần đo gần nhất TRƯỚC mỗi mốc.

    `np.searchsorted(..., "right") - 1` cho chỉ số của lần đo lớn nhất ≤ mốc. Mốc nào
    nằm TRƯỚC lần đo đầu tiên thì kẹp về lần đo đầu — không có gì tốt hơn để dùng, và
    bỏ trống thì cột thời gian thủng lỗ.

    Chưa đo lần nào → trả nguyên cột, KHÔNG chép: không hiệu chỉnh thì cũng không tốn
    80 MB một ngày để giữ một bản sao y hệt."""
    if not moc or not len(t_may):
        return t_may
    i = np.searchsorted(np.asarray(moc, dtype=np.int64), t_may, side="right") - 1
    np.clip(i, 0, None, out=i)
    return t_may - np.rint(np.asarray(lech, dtype=np.float64)[i]).astype(np.int64)


def _tron(s_t, s_T, k_t, k_T, lh_moc):
    """Thứ tự phát lại — tính MỘT LẦN bằng numpy, rồi đi tuần tự.

    Nhận thẳng bốn CỘT chứ không nhận hai mảng bản ghi: `s_t`/`k_t` là mốc ĐÃ hiệu
    chỉnh đồng hồ, không còn nằm trong mảng gốc nữa.

    Trả mảng `(nguồn, chỉ_số)`: nguồn 0 = sổ, 1 = khớp, 2 = lỗ hổng (chỉ số chẵn là mở,
    lẻ là đóng).

    Sắp bằng `lexsort` chứ không trộn bằng vòng lặp Python: mười triệu sự kiện một ngày
    thì phép sắp phải nằm trong C. Khoá xếp từ YẾU tới MẠNH, nên đọc ngược từ dưới lên:

        t_ta     ← mạnh nhất: thứ tự TA THẤY
        T        ← hoà `t_ta` thì tin vào thứ tự ở sàn
        nguồn    ← hoà cả hai thì sổ lệnh trước khớp lệnh (thấy giá mới rồi mới thấy ai ăn)
        chỉ số   ← chốt cuối, để KHÔNG BAO GIỜ có hai cách sắp cho cùng một bộ dữ liệu
    """
    n_so, n_khop = len(s_t), len(k_t)
    n_lh = len(lh_moc) * 2

    t = np.empty(n_so + n_khop + n_lh, dtype=np.int64)
    T = np.empty_like(t)
    nguon = np.empty_like(t)
    chi_so = np.empty_like(t)

    a, b = 0, n_so
    t[a:b], T[a:b], nguon[a:b] = s_t, s_T, 0
    chi_so[a:b] = np.arange(n_so)

    a, b = b, b + n_khop
    t[a:b], T[a:b], nguon[a:b] = k_t, k_T, 1
    chi_so[a:b] = np.arange(n_khop)

    if n_lh:
        a, b = b, b + n_lh
        moc = np.empty(n_lh, dtype=np.int64)
        for i, (tu, den) in enumerate(lh_moc):
            moc[2 * i], moc[2 * i + 1] = tu, den
        t[a:b] = T[a:b] = moc
        nguon[a:b] = 2
        chi_so[a:b] = np.arange(n_lh)

    thu_tu = np.lexsort((chi_so, nguon, T, t))
    # HAI DANH SÁCH SONG SONG, không phải một danh sách tuple: `buoc()` chạy mười
    # triệu lần một ngày, và mỗi lần tháo một tuple là một lần cấp phát thừa.
    # `.tolist()` ở đây rẻ — chỉ hai cột số nguyên nhỏ.
    return nguon[thu_tu].tolist(), chi_so[thu_tu].tolist()
