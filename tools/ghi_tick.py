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

import urllib.request

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
URL_GIO_SAN = "https://fapi.binance.com/fapi/v1/time"

#: Xả đệm xuống đĩa mỗi ngần này giây.
GIAY_XA = 2.0

#: Không nhận được gói nào trong ngần này giây thì coi như luồng đã chết và nối lại.
#: Binance gửi ping mỗi 3 phút; một symbol thanh khoản thì im 30 giây đã là bất thường.
IM_LANG_TOI_DA = 45.0

#: Chờ bao lâu trước mỗi lần nối lại — tăng dần rồi chặn trần.
CHO_NOI_LAI = (1, 2, 5, 10, 20, 30)

#: Ngó cờ dừng mỗi ngần này giây.
#:
#: TÁCH KHỎI NHỊP TIM (5 s) chứ không gộp: gộp thì dừng mất tới 5 giây, và người bấm
#: nút chỉ thấy một cái nút không phản ứng. Ngó một file có tồn tại không thì rẻ gần
#: như bằng 0, nên ngó dày hơn chẳng mất gì.
GIAY_NGO_CO = 1.0

#: Đo lệch đồng hồ mỗi ngần này giây.
#:
#: 5 phút là đủ dày: đồng hồ máy trôi cỡ vài ms mỗi phút, còn NTP kéo về thì nhảy một
#: phát — lần đo kế bắt được ngay. Dày hơn thì tốn một lời gọi HTTP mà chẳng biết thêm
#: gì; thưa hơn thì một cú NTP kéo giữa chừng bị bỏ sót và cả quãng đó lệch.
GIAY_DO_DONG_HO = 300.0

#: Lấy bao nhiêu mẫu mỗi lần đo. Chọn mẫu có RTT NHỎ NHẤT, không lấy trung bình —
#: xem `do_lech_dong_ho`.
SO_MAU_DONG_HO = 5

#: Đập nhịp tim mỗi ngần này giây để app biết bộ ghi còn sống. Xem
#: `nguon_tick.trang_thai_ghi` — app KHÔNG sở hữu tiến trình này, nó chỉ nhìn.
GIAY_NHIP = 5.0


def do_lech_dong_ho(lan=SO_MAU_DONG_HO):
    """`(lệch_ms, rtt_ms)` — giờ máy trừ giờ sàn. `None` nếu không hỏi được.

    ⚠ LẤY MẪU CÓ RTT NHỎ NHẤT, KHÔNG LẤY TRUNG BÌNH. Đây là cách NTP làm, và lý do
    thì đơn giản: sai số của một lần đo bị chặn bởi ±RTT/2, nên mẫu có RTT nhỏ nhất là
    mẫu chặt nhất. Lấy trung bình là trộn mẫu tốt với mẫu tệ rồi tin vào hỗn hợp đó.
    (Đã đo một lần với RTT 272 ms — sai số ±136 ms, tức con số gần như vô dụng.)

    Cách tính: kẹp lời gọi giữa hai lần đọc đồng hồ máy, lấy điểm giữa. Giả định duy
    nhất là đường đi và đường về mất thời gian bằng nhau — không đúng tuyệt đối, nhưng
    là giả định tốt nhất có thể khi chỉ có một lời gọi."""
    tot = None
    for _ in range(max(1, lan)):
        try:
            t0 = time.time()
            with urllib.request.urlopen(URL_GIO_SAN, timeout=10) as r:
                san = json.loads(r.read())["serverTime"]
            t1 = time.time()
        except Exception:                                        # noqa: BLE001
            continue
        rtt = (t1 - t0) * 1000
        lech = (t0 + t1) / 2 * 1000 - float(san)
        if tot is None or rtt < tot[1]:
            tot = (lech, rtt)
    return tot


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


class _XinDung(Exception):
    """App đặt cờ dừng. Không phải lỗi — là một lối ra sạch."""


async def chay(symbols, im_lang=None):
    ghi = {s.upper(): Ghi(s) for s in symbols}
    # ĐỌC CÀI ĐẶT, đừng dùng hằng số. Ngưỡng im lặng và nhịp xả là hai con số người
    # dùng chỉnh được (xem `luu_tru.CAI_DAT_MAC_DINH["nguon"]`), và hằng số ở đầu file
    # chỉ còn là giá trị dự phòng khi file cài đặt hỏng.
    cd = nt.cai_dat()
    if im_lang is None:
        im_lang = float(cd.get("im_lang_giay") or IM_LANG_TOI_DA)
    giay_xa = float(cd.get("giay_xa") or GIAY_XA)
    giu_ngay = int(cd.get("giu_ngay") or 0)
    for s in ghi:
        bo = nt.don_ngay_cu(s, giu_ngay)
        if bo:
            print(f"  ♻ {s}: xoá {len(bo)} ngày cũ ({bo[0]} … {bo[-1]})")
    t_bat_dau = int(time.time() * 1000)
    # Cờ dừng CŨ còn sót lại thì lần chạy này chết ngay khi vừa mở. Dọn trước.
    nt.xoa_co_dung()
    nt.dap_nhip(sorted(ghi), t_bat_dau)
    # IN THỜI GIAN TỪNG BƯỚC KHỞI ĐỘNG. Không phải để gỡ lỗi một lần rồi bỏ: đây là
    # một tiến trình chạy nhiều tháng, và khi nó khởi động chậm bất thường thì dòng log
    # này là thứ duy nhất nói ra chậm ở đâu — đo đồng hồ, hay bắt tay WebSocket.
    t_moc = time.time()

    def _khac(chu):
        print(f"  · {chu} ({time.time() - t_moc:.1f}s)", flush=True)

    # ĐO ĐỒNG HỒ NGAY, trước cả byte dữ liệu đầu tiên. Bản ghi nào không có lần đo
    # nào đứng trước nó thì phải mượn lần đo đầu tiên — mượn được, nhưng đo ngay từ
    # đầu thì khỏi phải mượn.
    _do_va_ghi_dong_ho(ghi)
    _khac("đo đồng hồ xong")
    luong = "/".join(f"{s.lower()}@{k}" for s in symbols
                     for k in ("bookTicker", "trade"))
    url = GOC_WS + luong
    lan = 0
    t_dut = None

    while True:
        try:
            # ⚠ NGÓ CỜ DỪNG Ở CẢ VÒNG NGOÀI, không chỉ trong vòng đọc.
            #
            # Đã đo: bấm Bắt đầu rồi bấm Dừng ngay thì phải chờ hơn 7 giây. Vì giữa hai
            # lúc đó bộ ghi còn đang đo đồng hồ (5 lời gọi HTTP ≈ 1,5 s) rồi bắt tay
            # WebSocket — mà cả quãng ấy không ai ngó cờ. Người bấm nút chỉ thấy một
            # cái nút không phản ứng.
            if nt.da_xin_dung():
                raise _XinDung()
            _khac("bắt đầu bắt tay WebSocket")
            # ⚠ `close_timeout=1` — ĐÃ ĐO, và nó là chỗ mất bảy giây.
            #
            # Thoát `async with` thì thư viện làm BẮT TAY ĐÓNG: gửi frame close rồi chờ
            # sàn xác nhận. Mặc định chờ 10 giây. Đo được: nối xong lúc 3,0 s, xin dừng
            # lúc 2,2 s, mà mãi 10,7 s mới thật sự thoát — bảy giây đó nằm hết ở đây,
            # không phải ở phép ngó cờ.
            #
            # Với một bộ ghi thì lịch sự đóng không đáng một giây nào: dữ liệu đã xả
            # xuống đĩa trước đó rồi, và sàn tự dọn kết nối chết.
            async with websockets.connect(url, ping_interval=20, ping_timeout=20,
                                          close_timeout=1, max_queue=None) as ws:
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
                _khac(f"đã nối · {len(symbols)} symbol · {len(symbols) * 2} luồng")
                await _doc(ws, ghi, im_lang, t_bat_dau, giay_xa)
        except _XinDung:
            for g in ghi.values():
                g.xa()
            nt.xoa_co_dung()
            nt.xoa_nhip()
            print("  ■ dừng theo yêu cầu của app — đã xả hết đệm")
            return
        except asyncio.CancelledError:
            # Ctrl+C. Xả nốt phần đã nhận RỒI mới đi — mất hai giây dữ liệu vì một
            # dòng thiếu thì đúng loại mất mát khó chịu nhất: nhỏ, âm thầm, lặp lại
            # mỗi lần khởi động lại.
            for g in ghi.values():
                g.xa()
            nt.xoa_nhip()
            raise
        except Exception as e:                                       # noqa: BLE001
            if t_dut is None:
                t_dut = int(time.time() * 1000)
            for g in ghi.values():
                g.xa()                       # đừng để mất phần đã nhận
            cho = CHO_NOI_LAI[min(lan, len(CHO_NOI_LAI) - 1)]
            lan += 1
            print(f"  ✘ {type(e).__name__}: {str(e)[:80]} — nối lại sau {cho}s")
            # Vẫn đập nhịp trong lúc chờ nối lại: bộ ghi CÒN SỐNG, chỉ là đang mù.
            # Ngừng đập ở đây thì app báo "đã chết" trong khi nó sắp nối lại được.
            nt.dap_nhip(sorted(ghi), t_bat_dau)
            # Ngủ THÀNH TỪNG GIÂY, không ngủ một mạch 30 giây: đang chờ nối lại mà bấm
            # Dừng thì cũng phải dừng được.
            for _ in range(int(cho)):
                if nt.da_xin_dung():
                    raise _XinDung()
                await asyncio.sleep(1)


async def _doc(ws, ghi, im_lang, t_bat_dau, giay_xa=GIAY_XA):
    t_xa = time.time()
    t_in = time.time()
    t_nhip = 0.0
    t_co = 0.0
    t_dh = time.time()
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
        if gio - t_xa >= giay_xa:
            for g in ghi.values():
                g.xa()
            t_xa = gio
        if gio - t_co >= GIAY_NGO_CO:
            if nt.da_xin_dung():
                raise _XinDung()
            t_co = gio
        if gio - t_dh >= GIAY_DO_DONG_HO:
            _do_va_ghi_dong_ho(ghi)
            t_dh = gio
        if gio - t_nhip >= GIAY_NHIP:
            nt.dap_nhip(sorted(ghi), t_bat_dau)
            t_nhip = gio
        if gio - t_in >= 60:
            _in_trang_thai(ghi)
            t_in = gio


def _do_va_ghi_dong_ho(ghi):
    """Đo một lần rồi ghi cho MỌI symbol đang ghi.

    Ghi vào từng symbol chứ không một chỗ chung: dữ liệu của một symbol phải TỰ ĐỦ để
    hiệu chỉnh. Chép nó vào thư mục khác, hay xoá một symbol khác đi, thì phần còn lại
    vẫn đọc được. Vài chục byte một ngày — rẻ hơn nhiều so với một phụ thuộc ngầm."""
    kq = do_lech_dong_ho()
    if kq is None:
        return
    lech, rtt = kq
    t = int(time.time() * 1000)
    ngay = _ngay_utc(t)
    for s in ghi:
        nt.ghi_lech_dong_ho(s, ngay, t, lech, rtt)
    print(f"  ⏱ lệch đồng hồ {lech:+.0f} ms (rtt {rtt:.0f} ms)")


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
    p.add_argument("--im-lang", type=float, default=None,
                   help="im bao nhiêu giây thì coi là chết (mặc định: lấy từ Cài đặt)")
    a = p.parse_args()

    syms = [s.upper() for s in a.symbol]
    print(f"  ghi vào  {nt.thu_muc(syms[0])}")
    print(f"  symbol   {', '.join(syms)}")
    print("  Ctrl+C để dừng — phần đã nhận vẫn được xả xuống đĩa\n")
    try:
        asyncio.run(chay(syms, a.im_lang))
    except KeyboardInterrupt:
        # ⚠ KHÔNG xả lại ở đây. `chay` là chỗ DUY NHẤT còn giữ tham chiếu tới đệm, và
        # nó đã xả trong nhánh `CancelledError` của chính nó. Bản trước có một khối
        # `finally: if ghi: …` ở đây với `ghi = None` — tức một đoạn mã trông như đang
        # bảo vệ dữ liệu nhưng KHÔNG BAO GIỜ chạy. Đó là loại tệ nhất: đọc thì yên tâm,
        # thực tế thì không.
        print("\n  dừng theo yêu cầu")


if __name__ == "__main__":
    main()
