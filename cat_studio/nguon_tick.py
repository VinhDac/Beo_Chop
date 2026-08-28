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
không có dấu vết. Nên lỗ hổng nằm trong một file riêng `.loho` cạnh dữ liệu, và
`doc()` từ chối trả về một dải có lỗ hổng nếu không được nói rõ là chấp nhận.
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
def thu_muc(symbol):
    d = os.path.join(luu_tru.goc(), THU_MUC_TICK, luu_tru._ten_an_toan(symbol.upper()))
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
