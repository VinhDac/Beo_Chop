"""BỘ GHI TICK — chạy 24/7, ghi luồng thị trường của chính ta ra đĩa.

    python tools\\ghi_tick.py TRUMPUSDT PUMPUSDT

Đây là thứ KHỞI ĐỘNG ĐỒNG HỒ. Kho miễn phí của Binance ngừng phát `bookTicker` từ
2024-03-30 (xem `cat_studio/nguon_tick.py`), nên lịch sử sổ lệnh chỉ có một đường: tự
ghi. Chạy càng sớm thì càng sớm có cái để backtest — mọi thứ khác dựng song song được,
riêng cái này thì không rút ngắn được bằng cách viết code nhanh hơn.

HAI LUỒNG, KHÔNG HƠN
--------------------
    <sym>@bookTicker   mọi thay đổi ở ĐỈNH sổ lệnh, thời gian thực
    <sym>@trade        mọi cú khớp, KHÔNG gộp

⚠ `@aggTrade` KHÔNG dùng được: đo ngày 2026-08-28, nó trả 0 gói trong 10 s cho cả
`trumpusdt` lẫn `btcusdt` — im lặng, không lỗi, không đóng kết nối. `@trade` cùng lúc
trả 944 gói. Xem `nguon_tick.DT_KHOP`.

Cố ý KHÔNG lấy `@depth` (độ sâu nhiều mức): nó bị sàn gộp về 100 ms hoặc 250 ms một
ảnh, tức trong mỗi khoảng đó nhiều sự kiện chồng lên nhau và MẤT THỨ TỰ. `bookTicker`
thì bắn theo từng thay đổi thật. Với spread một tick — đo được trên gần như mọi symbol
còn cửa — đỉnh sổ lệnh là toàn bộ cuộc chơi. Xem `nguon_tick.DT_SO`.

BỐN LUẬT CỦA MỘT BỘ GHI CHẠY DÀI NGÀY
--------------------------------------
1. **Không bao giờ chết.** Mọi lỗi đều thành một lần nối lại, không thành traceback.
   Một bản ghi chết lúc 3 giờ sáng là mất cả đêm dữ liệu.

2. **Lỗ hổng phải được GHI RA.** Rớt mạng 40 giây mà không để lại dấu thì bộ chạy sau
   này phát qua chỗ đó như thể thị trường liền mạch — sai mà không có dấu vết. Mỗi lần
   đứt đều ghi một dòng vào `<ngày>.loho`.

3. **Ghi xuống đĩa đều đặn, đừng ôm trong RAM.** Máy mất điện thì mất đúng phần chưa
   ghi. `GIAY_XA` giây một lần là đủ nhỏ để không tiếc, đủ lớn để không mài đĩa.

4. **Cắt file theo NGÀY UTC.** Sàn chạy 24/7 nên không có mốc tự nhiên nào khác, và
   một file hỏng thì chỉ mất một ngày.
"""
import argparse
import asyncio
import io
import json
import os
import sys
import time
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import nguon_tick as nt                                 # noqa: E402

try:
    import websockets
except ImportError:
    print("Thiếu thư viện `websockets`.  pip install websockets")
    raise SystemExit(1)

GOC_WS = "wss://fstream.binance.com/stream?streams="

#: Xả đệm xuống đĩa mỗi ngần này giây.
GIAY_XA = 2.0

#: Không nhận được gói nào trong ngần này giây thì coi như luồng đã chết và nối lại.
#: Binance gửi ping mỗi 3 phút; một symbol thanh khoản thì im 30 giây đã là bất thường.
IM_LANG_TOI_DA = 45.0

#: Chờ bao lâu trước mỗi lần nối lại — tăng dần rồi chặn trần.
CHO_NOI_LAI = (1, 2, 5, 10, 20, 30)


def _ngay_utc(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


class Ghi:
    """Đệm + xả cho MỘT symbol. Tự cắt file khi sang ngày UTC mới."""

    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.dem = {ten: [] for ten in nt.LUONG}
        self.ngay = {ten: None for ten in nt.LUONG}
        self.tong = {ten: 0 for ten in nt.LUONG}
        self.t_cuoi = 0.0

    def them(self, luong, ban_ghi):
        self.dem[luong].append(ban_ghi)
        self.t_cuoi = time.time()

    def xa(self):
        """Ghi đệm xuống đĩa. Mở lại file mỗi lần thay vì giữ handle: rẻ hơn nhiều so
        với một handle mở suốt ngày trỏ vào file của HÔM QUA sau lúc nửa đêm."""
        for luong, ds in self.dem.items():
            if not ds:
                continue
            dt = nt.LUONG[luong]
            # Cắt theo ngày của TỪNG bản ghi, không theo đồng hồ máy: gói tới sát nửa
            # đêm phải rơi vào đúng file của nó.
            theo_ngay = {}
            for b in ds:
                theo_ngay.setdefault(_ngay_utc(b[0]), []).append(b)
            for ngay, phan in theo_ngay.items():
                a = np.array(phan, dtype=dt)
                with open(nt.duong(self.symbol, ngay, luong), "ab") as f:
                    a.tofile(f)
                self.tong[luong] += len(a)
                if self.ngay[luong] != ngay:
                    self.ngay[luong] = ngay
            ds.clear()


async def chay(symbols, im_lang=IM_LANG_TOI_DA):
    ghi = {s.upper(): Ghi(s) for s in symbols}
    luong = "/".join(f"{s.lower()}@{k}" for s in symbols
                     for k in ("bookTicker", "trade"))
    url = GOC_WS + luong
    lan = 0
    t_dut = None

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20,
                                          max_queue=None) as ws:
                if t_dut is not None:
                    # ĐỨT QUÃNG — ghi vào sổ lỗ hổng của MỌI symbol. Không biết symbol
                    # nào mất gì, nên nói ra cho tất cả: thà thừa một dòng còn hơn để
                    # bộ chạy tin vào một dải liền mạch không có thật.
                    gio = int(time.time() * 1000)
                    for s in ghi:
                        nt.ghi_lo_hong(s, _ngay_utc(gio), t_dut, gio, "mất kết nối")
                    print(f"  ⚠ lỗ hổng {(gio - t_dut) / 1000:.1f}s — đã ghi vào sổ")
                    t_dut = None
                lan = 0
                print(f"  ● đã nối · {len(symbols)} symbol · {len(symbols) * 2} luồng")
                await _doc(ws, ghi, im_lang)
        except asyncio.CancelledError:
            # Ctrl+C. Xả nốt phần đã nhận RỒI mới đi — mất hai giây dữ liệu vì một
            # dòng thiếu thì đúng loại mất mát khó chịu nhất: nhỏ, âm thầm, lặp lại
            # mỗi lần khởi động lại.
            for g in ghi.values():
                g.xa()
            raise
        except Exception as e:                                       # noqa: BLE001
            if t_dut is None:
                t_dut = int(time.time() * 1000)
            for g in ghi.values():
                g.xa()                       # đừng để mất phần đã nhận
            cho = CHO_NOI_LAI[min(lan, len(CHO_NOI_LAI) - 1)]
            lan += 1
            print(f"  ✘ {type(e).__name__}: {str(e)[:80]} — nối lại sau {cho}s")
            await asyncio.sleep(cho)


async def _doc(ws, ghi, im_lang):
    t_xa = time.time()
    t_in = time.time()
    while True:
        try:
            tho = await asyncio.wait_for(ws.recv(), timeout=im_lang)
        except asyncio.TimeoutError:
            raise ConnectionError(f"im lặng quá {im_lang:g}s")
        t_ta = int(time.time() * 1000)
        try:
            goi = json.loads(tho)
            d = goi["data"]
            s = d["s"]
            g = ghi.get(s)
            if g is None:
                continue
            if d["e"] == "bookTicker":
                g.them("so", (int(d.get("T", d["E"])), int(d["E"]), t_ta, int(d["u"]),
                              float(d["b"]), float(d["B"]),
                              float(d["a"]), float(d["A"])))
            elif d["e"] == "trade":
                # `m` = is_buyer_maker. ĐẢO NGAY để về `mua_chu_dong` — xem DT_KHOP.
                g.them("khop", (int(d["T"]), int(d["E"]), t_ta, int(d["t"]),
                                float(d["p"]), float(d["q"]), not d["m"]))
        except (KeyError, ValueError, TypeError):
            # Một gói lạ không được giết cả bộ ghi. Bỏ qua, đi tiếp.
            continue

        gio = time.time()
        if gio - t_xa >= GIAY_XA:
            for g in ghi.values():
                g.xa()
            t_xa = gio
        if gio - t_in >= 60:
            _in_trang_thai(ghi)
            t_in = gio


def _in_trang_thai(ghi):
    gio = datetime.now(timezone.utc).strftime("%H:%M:%S")
    phan = []
    for s, g in sorted(ghi.items()):
        phan.append(f"{s} {g.tong['so']:,}/{g.tong['khop']:,}")
    print(f"  {gio}Z  " + "  ·  ".join(phan) + "   (sổ/khớp)")


def main():
    p = argparse.ArgumentParser(
        description="ghi luồng sổ lệnh + khớp lệnh Binance USDⓈ-M ra đĩa")
    p.add_argument("symbol", nargs="+", help="ví dụ TRUMPUSDT PUMPUSDT")
    p.add_argument("--im-lang", type=float, default=IM_LANG_TOI_DA,
                   help=f"im bao nhiêu giây thì coi là chết (mặc định {IM_LANG_TOI_DA:g})")
    a = p.parse_args()

    syms = [s.upper() for s in a.symbol]
    print(f"  ghi vào  {nt.thu_muc(syms[0])}")
    print(f"  symbol   {', '.join(syms)}")
    print("  Ctrl+C để dừng — phần đã nhận vẫn được xả xuống đĩa\n")
    ghi = None
    try:
        asyncio.run(chay(syms, a.im_lang))
    except KeyboardInterrupt:
        print("\n  dừng theo yêu cầu")
    finally:
        if ghi:
            for g in ghi.values():
                g.xa()


if __name__ == "__main__":
    main()
