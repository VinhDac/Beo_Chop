"""NGUỒN TICK — chỗ DUY NHẤT biết dữ liệu thị trường nằm ở đâu và có hình dạng gì.

Thay `nguon_nen.py` cũ (nến M1 từ MT5). Mọi module khác chỉ thấy một mảng numpy.

VÌ SAO PHẢI TỰ GHI, KHÔNG TẢI VỀ
---------------------------------
Đã đo kho miễn phí của Binance (`data.binance.vision`) ngày 2026-08-28:

    aggTrades    996 symbol · 2019-12-31 → 2026-08-27      ✔ hiện hành
    trades       996 symbol                                ✔ hiện hành
    bookTicker   315 symbol · 2023-05-16 → 2024-03-30      ✘ NGỪNG HẲN
    bookDepth    hiện hành, nhưng KHÔNG phải sổ lệnh — nó là thanh khoản ở
                 ±1…5 % quanh mid, lấy mẫu 2,5 s/lần

Và 315 symbol có sổ lệnh đúng là nhóm BTC/ETH/SOL mà `tools/do_spread.py` đã loại
(spread 1 tick, tỉ lệ 0.00). Nhóm còn cửa thì `bookTicker` RỖNG HOÀN TOÀN.

Nên không có đường nào khác: **ta tự ghi luồng của chính mình** (`tools/ghi_tick.py`).
Đổi lại được thứ đắt hơn cả dữ liệu — **backtest và live đọc CÙNG MỘT LUỒNG BYTE từ
cùng một ổ cắm**, tức "test như nào thì live như thế" thành chuyện của kiến trúc chứ
không phải của kỷ luật. Đúng lời hứa mà `bo_chay.mot_nhip` cũ đánh đổi mọi thứ để giữ.

BA MỐC THỜI GIAN, KHÔNG PHẢI MỘT
---------------------------------
Mỗi bản ghi mang ba con số, và tách ra là CÓ CHỦ Ý:

    T      sàn ĐỔI sổ lệnh lúc nào      → sự thật của thị trường, backtest phát lại cái này
    E      sàn GỬI đi lúc nào           → trễ trong nội bộ sàn
    t_ta   TA NHẬN được lúc nào         → thứ chiến lược thật sự nhìn thấy

`t_ta − T` chính là ĐỘ TRỄ, đo được trên từng gói, miễn phí, ngay trong lúc ghi. Nhờ
vậy ngân sách độ trễ không còn là một ô người dùng gõ bừa vào Cài đặt — nó là một phân
bố đã đo. Backtest trung thực phải cho chiến lược thấy dữ liệu ở `t_ta`, không phải ở
`T`; nhìn ở `T` là cho nó thấy tương lai.

MẤT GÓI PHẢI NÓI RA, KHÔNG ĐƯỢC IM
-----------------------------------
Cả hai luồng đều mang số thứ tự của sàn (`u` cho sổ lệnh, `a` cho khớp lệnh). Nhảy số
= mất gói. Mạng rớt = mất một quãng. **Một lỗ hổng không được ghi lại là một lời nói
dối**: bộ chạy sẽ phát qua nó như thể thị trường liền mạch, và mọi con số sau đó sai mà
không có dấu vết. Nên lỗ hổng nằm trong một file riêng `.loho` cạnh dữ liệu.

⚠ `doc()` ở đây KHÔNG kiểm lỗ hổng — nó chỉ đọc byte. Việc bắt bộ chạy nhìn thấy lỗ
hổng thuộc về `phat_lai.py`, chỗ biến mỗi lỗ hổng thành một cặp sự kiện `MO_LO_HONG` /
`DONG_LO_HONG`. Tách như vậy vì đọc và diễn giải là hai việc: ai muốn xem dữ liệu thô
thì cứ xem, còn ai chạy chiến lược thì bắt buộc đi qua `phat_lai` và không thể bỏ sót.
"""
import json
import os

import numpy as np

from . import luu_tru

#: THƯ MỤC gốc của dữ liệu tick, cạnh `du_lieu/`.
THU_MUC_TICK = "tick"

#: Một thay đổi ở đỉnh sổ lệnh. 64 byte.
#:
#: CHỈ GHI ĐỈNH (best bid/ask), không ghi cả cuốn sổ — và đó là quyết định, không phải
#: cắt giảm. `tools/do_spread.py` đo được: trên gần như mọi symbol còn cửa, spread ĐÚNG
#: MỘT TICK. Không có chỗ nào để chen vào giữa; ta chỉ xếp hàng ở đỉnh. Mà xếp hàng ở
#: đỉnh thì cần đúng hai thứ — khối lượng đang đứng trước ta (`bid_kl`/`ask_kl`) và
#: những cú khớp ăn dần vào đó (luồng kia). Ghi cả 20 mức là gấp mười dung lượng để
#: trả lời một câu hỏi ta không hỏi.
#:
#: ⚠ Ngày nào spread rộng ra nhiều tick thì quyết định này phải xem lại — lúc đó cải
#: thiện giá mới có nghĩa, và cần độ sâu thật.
DT_SO = np.dtype([
    ("T", "<i8"),        # sàn đổi sổ lệnh (ms)
    ("E", "<i8"),        # sàn gửi đi (ms)
    ("t_ta", "<i8"),     # ta nhận được (ms) — `t_ta - T` là độ trễ
    ("u", "<i8"),        # số thứ tự của sàn — nhảy số là mất gói
    ("bid", "<f8"), ("bid_kl", "<f8"),
    ("ask", "<f8"), ("ask_kl", "<f8"),
])

#: Một cú khớp lệnh. 56 byte.
#:
#: `mua_chu_dong` = bên MUA là bên chủ động (taker). Binance gửi `m = is_buyer_maker`,
#: tức ngược lại — đảo ngay lúc ghi để không ai phải nhớ dấu về sau. Đây là trường
#: quyết định hàng đợi: khớp chủ động MUA thì ăn vào hàng ở ASK, và ngược lại.
#:
#: ⚠ DÙNG `@trade`, KHÔNG DÙNG `@aggTrade` — và đây là chuyện ĐO ĐƯỢC, không phải sở
#: thích. Ngày 2026-08-28, `@aggTrade` trên `fstream.binance.com` trả về **0 gói trong
#: 10 giây** cho cả `trumpusdt` lẫn `btcusdt`, trong khi cùng lúc `@trade` trả 944 gói
#: và `@bookTicker` trả 1.259. Không lỗi, không đóng kết nối — chỉ im lặng.
#:
#: Hoá ra lại hợp hơn: `aggTrade` GỘP những cú khớp liên tiếp cùng giá của một lệnh
#: taker thành một dòng, mà thứ ta cần là ĐÚNG CHUỖI khớp để trừ dần hàng đợi. Và
#: `trades` cũng là luồng có trong kho lịch sử, nên ngày muốn nhét lịch sử cũ vào thì
#: cùng một định dạng.
#:
#: `id` tăng đúng từng đơn vị → đếm được chính xác số cú khớp đã mất.
#:
#: ⚠ ĐỆM CHO TRÒN 56 BYTE. Xếp tự nhiên ra 49 — bốn `i8` + hai `f8` + một `bool` —
#: và 49 là số lẻ, nên mỗi bản ghi bắt đầu ở một độ lệch khác nhau, không bao giờ
#: thẳng hàng 8 byte. Quét một trăm triệu bản ghi thì cái đó đo được. Bảy byte thừa
#: đổi lấy đúng hàng, và còn chỗ cho một trường nữa sau này mà không phải đổi định
#: dạng file. `DT_SO` thì tự nó đã tròn 64.
DT_KHOP = np.dtype({
    "names": ["T", "E", "t_ta", "id", "gia", "kl", "mua_chu_dong"],
    "formats": ["<i8", "<i8", "<i8", "<i8", "<f8", "<f8", "?"],
    "offsets": [0, 8, 16, 24, 32, 40, 48],
    "itemsize": 56,
})

#: Tên luồng → dtype. Thêm một luồng là thêm một dòng ở đây, không sửa chỗ nào khác.
LUONG = {"so": DT_SO, "khop": DT_KHOP}


# ---------------------------------------------------------------------------
# Đường dẫn — MỘT chỗ duy nhất
# ---------------------------------------------------------------------------
def goc_tick():
    """Thư mục gốc của dữ liệu tick.

    Đọc `cai_dat["nguon"]["thu_muc"]` mỗi lần thay vì nhớ vào một hằng số lúc import:
    đổi thư mục trong app phải có tác dụng NGAY, không đợi khởi động lại. Rẻ — đọc một
    file JSON vài trăm byte.

    Đường dẫn TƯƠNG ĐỐI thì tính từ `du_lieu/`; tuyệt đối thì dùng nguyên. Nhờ vậy
    `D:/tick` và `tick_ngoai` đều viết được, và không ai phải nhớ luật nào."""
    d = ((luu_tru.doc_cai_dat().get("nguon") or {}).get("thu_muc") or "").strip()
    if not d:
        return os.path.join(luu_tru.goc(), THU_MUC_TICK)
    return d if os.path.isabs(d) else os.path.join(luu_tru.goc(), d)


def thu_muc(symbol):
    d = os.path.join(goc_tick(), luu_tru._ten_an_toan(symbol.upper()))
    os.makedirs(d, exist_ok=True)
    return d


def duong(symbol, ngay, luong):
    """File dữ liệu của MỘT ngày UTC. `ngay` dạng `"2026-08-28"`.

    Cắt theo NGÀY UTC chứ không theo phiên: sàn crypto chạy 24/7, không có phiên. Và
    cắt theo ngày thì một file hỏng chỉ mất một ngày, không mất cả dải."""
    if luong not in LUONG:
        raise ValueError(f'Luồng "{luong}" không có. Chỉ có: {", ".join(LUONG)}.')
    return os.path.join(thu_muc(symbol), f"{ngay}.{luong}.bin")


def duong_lo_hong(symbol, ngay):
    """Sổ ghi LỖ HỔNG của một ngày — JSON Lines, mỗi dòng một quãng mất dữ liệu."""
    return os.path.join(thu_muc(symbol), f"{ngay}.loho")


# ---------------------------------------------------------------------------
# Đọc
# ---------------------------------------------------------------------------
def doc_ngay(symbol, ngay, luong):
    """Mảng của MỘT ngày. Chưa có thì trả mảng RỖNG đúng dtype, không trả None.

    Trả mảng rỗng chứ không None vì chỗ gọi cứ `len()` và cắt lát như thường, không
    phải rải `if is None` khắp bộ chạy — cùng lý lẽ `nguon_nen.doc` cũ."""
    dt = LUONG[luong]
    p = duong(symbol, ngay, luong)
    try:
        a = np.fromfile(p, dtype=dt)
    except (OSError, ValueError):
        return np.empty(0, dtype=dt)
    return a


def doc(symbol, tu_ngay, den_ngay, luong):
    """Ghép nhiều ngày liền nhau. `tu_ngay`/`den_ngay` dạng `"2026-08-28"`, gồm cả hai đầu."""
    ds = [doc_ngay(symbol, n, luong) for n in _dai_ngay(tu_ngay, den_ngay)]
    ds = [a for a in ds if len(a)]
    return np.concatenate(ds) if ds else np.empty(0, dtype=LUONG[luong])


def _dai_ngay(tu, den):
    """Danh sách ngày UTC từ `tu` tới `den`, gồm cả hai đầu. Chuỗi thuần, không datetime:
    ngày ở đây chỉ là một cái NHÃN FILE, đưa nó qua múi giờ là mời gọi lệch một ngày."""
    from datetime import date, timedelta
    a = date.fromisoformat(tu)
    b = date.fromisoformat(den)
    ra = []
    while a <= b:
        ra.append(a.isoformat())
        a += timedelta(days=1)
    return ra


# ---------------------------------------------------------------------------
# Lỗ hổng
# ---------------------------------------------------------------------------
def doc_lo_hong(symbol, ngay):
    """Lỗ hổng ĐÃ GHI của một ngày. Rỗng nghĩa là bộ ghi không thấy đứt quãng nào —
    KHÔNG có nghĩa là không có: bộ ghi không chạy thì không ai ghi gì cả."""
    ra = []
    try:
        with open(duong_lo_hong(symbol, ngay), encoding="utf-8") as f:
            for dong in f:
                dong = dong.strip()
                if dong:
                    try:
                        ra.append(json.loads(dong))
                    except ValueError:
                        continue          # một dòng hỏng không được giết cả sổ
    except OSError:
        pass
    return ra


def ghi_lo_hong(symbol, ngay, tu_ms, den_ms, vi_sao):
    """Ghi thêm MỘT lỗ hổng. Nối thêm chứ không ghi đè: bộ ghi có thể khởi động lại
    nhiều lần trong một ngày, và mỗi lần đều phải để lại dấu."""
    with open(duong_lo_hong(symbol, ngay), "a", encoding="utf-8") as f:
        f.write(json.dumps({"tu": int(tu_ms), "den": int(den_ms),
                            "ms": int(den_ms - tu_ms), "vi_sao": vi_sao},
                           ensure_ascii=False) + "\n")


def do_mat_goi(a, cot):
    """Mất gói suy ra từ SỐ THỨ TỰ của sàn, không từ thời gian.

    Trả `[(chi_so, số_gói_mất), …]`. Đây là phép kiểm mà thời gian không làm được: hai
    bản ghi cách nhau 3 giây có thể là thị trường lặng (bình thường) hoặc là ta rớt mất
    9.000 gói (thảm hoạ). Chỉ số thứ tự phân biệt được hai ca đó.

    ⚠ `u` của `bookTicker` KHÔNG tăng đều từng đơn vị — nó là `updateId` chung của cả
    sổ lệnh, nên nhảy quãng là BÌNH THƯỜNG khi có thay đổi ở mức sâu hơn. Với luồng
    `so` thì hàm này chỉ bắt được ca `u` GIẢM (sai thứ tự / nối lại nhầm). Với `khop`
    thì `a` tăng đúng từng đơn vị nên đếm được chính xác số cú khớp đã mất."""
    if len(a) < 2:
        return []
    d = np.diff(a[cot].astype(np.int64))
    ra = []
    if cot == "id":
        for i in np.nonzero(d != 1)[0]:
            ra.append((int(i) + 1, int(d[i]) - 1))
    else:
        for i in np.nonzero(d < 0)[0]:
            ra.append((int(i) + 1, int(d[i])))
    return ra


def tom_tat(symbol, ngay):
    """Một ngày trông thế nào — để nhìn là biết dữ liệu có dùng được không."""
    ra = {"symbol": symbol.upper(), "ngay": ngay, "lo_hong": doc_lo_hong(symbol, ngay)}
    for ten in LUONG:
        a = doc_ngay(symbol, ngay, ten)
        mat = do_mat_goi(a, "id" if ten == "khop" else "u")
        ra[ten] = {
            "so_ban_ghi": int(len(a)),
            "mb": round(len(a) * LUONG[ten].itemsize / 1e6, 2),
            "tu": int(a["T"][0]) if len(a) else None,
            "den": int(a["T"][-1]) if len(a) else None,
            "so_cho_mat_goi": len(mat),
            "so_goi_mat": int(sum(n for _, n in mat)) if ten == "khop" else None,
            # Độ trễ ĐO ĐƯỢC, không phải ước lượng. Trung vị chịu được vài gói lệch
            # đồng hồ; trung bình thì không.
            "tre_ms_trung_vi": (float(np.median(a["t_ta"] - a["T"])) if len(a) else None),
            "tre_ms_p99": (float(np.percentile(a["t_ta"] - a["T"], 99)) if len(a) else None),
        }
    return ra


# ---------------------------------------------------------------------------
# NHỊP TIM của bộ ghi — app nhìn vào đây để biết nó còn sống không
# ---------------------------------------------------------------------------
#
# Bộ ghi là một TIẾN TRÌNH RIÊNG, không nằm trong app, và đó là quyết định chứ không
# phải tiện tay: nó phải chạy 24/7 kể cả khi app đóng. Cùng bài học mà cửa sổ Live cũ
# đã trả giá — "đóng cửa sổ không được dừng phiên".
#
# Nên app không SỞ HỮU bộ ghi, nó chỉ NHÌN. Cách nhìn: một file nhịp tim ghi lại mỗi
# vài giây. Chọn file chứ không chọn socket hay pid: file đọc được từ bất cứ tiến
# trình nào, sống qua lần khởi động lại của app, và xem bằng mắt cũng được.

FILE_NHIP = "_dang_ghi.json"

#: Nhịp tim cũ hơn ngần này giây thì coi như bộ ghi đã chết. Bộ ghi đập mỗi 5 s, nên
#: 20 s là đã lỡ bốn nhịp — đủ để chắc, đủ nhanh để hữu ích.
NHIP_QUA_HAN = 20.0


def _duong_nhip():
    return os.path.join(goc_tick(), FILE_NHIP)


def dap_nhip(symbols, t_bat_dau):
    """Bộ ghi gọi. KHÔNG BAO GIỜ ném — một cái đĩa đầy không được giết bộ ghi."""
    import time
    try:
        os.makedirs(os.path.dirname(_duong_nhip()), exist_ok=True)
        luu_tru.ghi_json_nguyen_tu(_duong_nhip(), {
            "pid": os.getpid(),
            "symbols": list(symbols),
            "bat_dau": int(t_bat_dau),
            "nhip": time.time(),
        })
    except Exception:                                            # noqa: BLE001
        pass


def trang_thai_ghi():
    """Bộ ghi còn sống không, đang ghi gì.

    `song` suy từ TUỔI NHỊP TIM, không từ việc pid có tồn tại hay không: pid bị hệ
    điều hành cấp lại cho tiến trình khác là chuyện thường, và lúc đó câu trả lời sẽ
    là "còn sống" trên một tiến trình chẳng ghi gì cả."""
    import time
    try:
        with open(_duong_nhip(), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:                                            # noqa: BLE001
        return {"song": False, "symbols": [], "pid": None,
                "tuoi_nhip": None, "bat_dau": None}
    tuoi = time.time() - float(d.get("nhip") or 0)
    return {
        "song": tuoi < NHIP_QUA_HAN,
        "symbols": d.get("symbols") or [],
        "pid": d.get("pid"),
        "tuoi_nhip": round(tuoi, 1),
        "bat_dau": d.get("bat_dau"),
    }


# ---------------------------------------------------------------------------
# LỆCH ĐỒNG HỒ — thứ hỏng VĨNH VIỄN nếu ghi chậm
# ---------------------------------------------------------------------------
#
# `t_ta` được đóng dấu bằng ĐỒNG HỒ MÁY. Đo ngày 2026-08-28: máy chậm hơn sàn 121 ms.
# Mà `t_ta` là TRỤC THỜI GIAN CỦA CẢ BACKTEST (xem `phat_lai`), nên sai số đó chui
# thẳng vào mọi kết quả — và nó lệch một chiều, không tự triệt tiêu.
#
# Cụ thể: gói tới ở thời điểm thật X được máy đóng dấu `t_ta = X + lệch`. Nên
#
#     thời điểm THẬT  =  t_ta − lệch          (`lệch` = giờ máy − giờ sàn)
#     độ trễ THẬT     =  (t_ta − lệch) − T
#
# Với lệch = −121 ms thì độ trễ đo được 207 ms hoá ra là **328 ms** thật. Không nhỏ.
#
# ⚠ VÌ SAO PHẢI GHI CÙNG LÚC VỚI DỮ LIỆU: độ lệch thay đổi theo thời gian (đồng hồ
# trôi, NTP kéo về, máy ngủ dậy). Không ghi lại thì dữ liệu của hôm nay VĨNH VIỄN không
# hiệu chỉnh được — không còn gì để suy ngược. Đây là lý do nó phải làm trước mọi thứ
# khác trong phần cài đặt.
#
# Cất cạnh dữ liệu, một file mỗi ngày, JSON Lines — cùng hình dạng với sổ lỗ hổng.

FILE_DONG_HO = ".dongho"


def duong_dong_ho(symbol, ngay):
    return os.path.join(thu_muc(symbol), f"{ngay}{FILE_DONG_HO}")


def ghi_lech_dong_ho(symbol, ngay, t_ms, lech_ms, rtt_ms):
    """Ghi thêm MỘT lần đo. Nối thêm, không đè: một ngày có nhiều lần đo, và chính
    chuỗi đó cho biết đồng hồ có trôi hay không."""
    try:
        with open(duong_dong_ho(symbol, ngay), "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": int(t_ms), "lech": round(float(lech_ms), 1),
                                "rtt": round(float(rtt_ms), 1)}) + "\n")
    except OSError:
        pass


def doc_lech_dong_ho(symbol, ngay):
    """Mọi lần đo của một ngày, theo thứ tự thời gian."""
    ra = []
    try:
        with open(duong_dong_ho(symbol, ngay), encoding="utf-8") as f:
            for dong in f:
                dong = dong.strip()
                if dong:
                    try:
                        ra.append(json.loads(dong))
                    except ValueError:
                        continue
    except OSError:
        pass
    return sorted(ra, key=lambda x: x.get("t", 0))


def bang_lech(symbol, tu_ngay, den_ngay):
    """Gom mọi lần đo trong dải → `(mốc_ms, lệch_ms)` đã sắp, để `phat_lai` tra.

    Trả `([], [])` khi chưa đo lần nào — và lúc đó `phat_lai` KHÔNG hiệu chỉnh gì, chứ
    không đoán 0. Hai chuyện khác nhau: "đo được là 0" nghĩa là đồng hồ đúng, còn
    "chưa đo" nghĩa là ta không biết, và phải nói ra."""
    moc, lech = [], []
    for n in _dai_ngay(tu_ngay, den_ngay):
        for d in doc_lech_dong_ho(symbol, n):
            moc.append(int(d["t"]))
            lech.append(float(d["lech"]))
    return moc, lech


#: CỜ DỪNG. App ghi file này, bộ ghi thấy thì xả đệm rồi thoát sạch.
#:
#: Vì sao không giết bằng pid: `taskkill /F` cắt ngang giữa chừng, mất đúng phần đệm
#: chưa xả (tới 2 giây dữ liệu). Còn tín hiệu Ctrl+Break thì phụ thuộc tiến trình được
#: sinh ra kiểu gì — có console hay không, cùng nhóm hay không — tức là một thứ đúng
#: trên máy này và sai trên máy khác. Một file thì luôn đúng, và đọc bằng mắt cũng được.
#:
#: Giá phải trả: dừng mất tối đa `GIAY_NHIP` giây. Rẻ.
FILE_DUNG = "_dung"


def _duong_dung():
    return os.path.join(goc_tick(), FILE_DUNG)


def xin_dung():
    """App gọi. Đặt cờ để bộ ghi tự thoát sạch."""
    os.makedirs(os.path.dirname(_duong_dung()), exist_ok=True)
    with open(_duong_dung(), "w", encoding="utf-8") as f:
        f.write("dung\n")


def da_xin_dung():
    """Bộ ghi gọi mỗi nhịp."""
    return os.path.exists(_duong_dung())


def xoa_co_dung():
    """Gọi lúc bộ ghi KHỞI ĐỘNG và lúc nó thoát — cờ cũ còn sót lại sẽ làm lần chạy
    sau chết ngay khi vừa mở, và không ai hiểu vì sao."""
    try:
        os.remove(_duong_dung())
    except OSError:
        pass


def xoa_nhip():
    """Gọi lúc bộ ghi thoát — để app biết ngay là đã dừng, khỏi chờ hết hạn nhịp."""
    try:
        os.remove(_duong_nhip())
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Liệt kê — app hỏi "đang có dữ liệu gì"
# ---------------------------------------------------------------------------
#: Lấy mẫu bao nhiêu bản ghi khi đo độ trễ. ĐỌC MẪU chứ không đọc cả file: một ngày là
#: ~640 MB, mà `liet_ke` chạy mỗi lần mở hộp thoại. Trung vị trên 20.000 mẫu rải đều đã
#: sát tới mức không ai phân biệt được.
SO_MAU_TRE = 20_000


def _ngay_co_san(symbol):
    """Ngày nào đã có file, suy từ TÊN FILE — không mở một byte nào."""
    ra = set()
    try:
        for f in os.listdir(thu_muc(symbol)):
            if f.endswith(".bin") and "." in f:
                ra.add(f.split(".")[0])
    except OSError:
        pass
    return sorted(ra)


def _tre_mau(symbol, ngay, luong):
    """Trung vị độ trễ, đo trên MẪU rải đều cả ngày. None nếu chưa có gì."""
    p = duong(symbol, ngay, luong)
    try:
        n = os.path.getsize(p) // LUONG[luong].itemsize
        if n <= 0:
            return None
        a = np.memmap(p, dtype=LUONG[luong], mode="r")
        buoc = max(1, n // SO_MAU_TRE)
        m = a[::buoc]
        return float(np.median(m["t_ta"].astype(np.int64) - m["T"].astype(np.int64)))
    except (OSError, ValueError):
        return None


def liet_ke():
    """Mọi symbol đã có dữ liệu, kèm số đo — hộp thoại Nguồn vẽ thẳng từ cái này.

    ⚠ RẺ CÓ CHỦ Ý. Số ngày và dung lượng lấy từ hệ thống file; lỗ hổng lấy từ mấy file
    `.loho` (nhỏ xíu); độ trễ đo trên MẪU của ngày mới nhất. Không hàm nào ở đây đọc
    hết một file 640 MB, vì nó chạy mỗi lần người dùng mở hộp thoại."""
    goc = goc_tick()
    ra = []
    try:
        ten = sorted(d for d in os.listdir(goc)
                     if os.path.isdir(os.path.join(goc, d)))
    except OSError:
        return ra
    for symbol in ten:
        ngay = _ngay_co_san(symbol)
        if not ngay:
            continue
        byte = {}
        for luong in LUONG:
            byte[luong] = sum(
                os.path.getsize(duong(symbol, n, luong))
                for n in ngay if os.path.exists(duong(symbol, n, luong)))
        lh = [x for n in ngay for x in doc_lo_hong(symbol, n)]
        ra.append({
            "symbol": symbol,
            "so_ngay": len(ngay),
            "tu_ngay": ngay[0],
            "den_ngay": ngay[-1],
            "mb": round(sum(byte.values()) / 1e6, 1),
            "so_ban_ghi": {k: int(v // LUONG[k].itemsize) for k, v in byte.items()},
            "so_lo_hong": len(lh),
            "ms_lo_hong": int(sum(x.get("ms") or 0 for x in lh)),
            # ⚠ ĐI NGƯỢC TÌM NGÀY CÓ FILE `so`, không cắm đầu vào `ngay[-1]`.
            # Bản đầu lấy thẳng ngày mới nhất và trả `None` khi ngày đó tình cờ chỉ
            # có file `khop` — mà `None` thì hiện ra bảng là một dấu gạch, trông y
            # như "chưa đo được" trong khi dữ liệu đo được nằm ngay ngày hôm trước.
            "tre_ms": next((x for x in (_tre_mau(symbol, n, "so")
                                        for n in reversed(ngay)) if x is not None),
                           None),
        })
    return ra


def cai_dat():
    """Bốn con số của nguồn, đã trộn với mặc định. Thiếu khoá nào thì lấy mặc định —
    file cài đặt của bản cũ không có mục `nguon` nào cả."""
    d = dict(luu_tru.CAI_DAT_MAC_DINH["nguon"])
    d.update(luu_tru.doc_cai_dat().get("nguon") or {})
    return d


def don_ngay_cu(symbol, giu_ngay):
    """Xoá những ngày cũ hơn `giu_ngay` ngày GẦN NHẤT CÓ DỮ LIỆU. Trả danh sách đã xoá.

    ⚠ Đếm theo NGÀY CÓ FILE, không theo lịch. Bộ ghi tắt một tuần rồi bật lại thì
    "giữ 30 ngày" phải nghĩa là 30 ngày có dữ liệu, chứ không phải xoá sạch vì hôm nay
    đã cách ngày cũ nhất hơn 30 hôm.

    `giu_ngay <= 0` → KHÔNG xoá gì. Đó là mặc định, và cố ý: xoá dữ liệu là việc không
    lùi được, app không được tự tiện làm khi chưa ai bảo."""
    if not giu_ngay or giu_ngay <= 0:
        return []
    ngay = _ngay_co_san(symbol)
    bo = ngay[:-int(giu_ngay)] if len(ngay) > giu_ngay else []
    d = thu_muc(symbol)
    for n in bo:
        for f in os.listdir(d):
            if f.startswith(n):
                try:
                    os.remove(os.path.join(d, f))
                except OSError:
                    pass
    return bo


def xoa(symbol):
    """Xoá HẲN dữ liệu của một symbol. Trả số byte đã xoá.

    Tải thì tự động được, xoá thì không — cùng luật `nguon_nen` cũ đã chốt: tải là an
    toàn và đảo ngược được, xoá thì mất là mất. Chỗ gọi phải hỏi người dùng trước."""
    import shutil
    d = thu_muc(symbol)
    n = 0
    for f in os.listdir(d):
        n += os.path.getsize(os.path.join(d, f))
    shutil.rmtree(d, ignore_errors=True)
    return n
