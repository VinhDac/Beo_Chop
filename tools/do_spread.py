"""ĐO MỘT CON SỐ DUY NHẤT:  spread có lớn hơn hai lần phí maker không?

    python tools\\do_spread.py

Market maker mua ở bid, bán ở ask, ăn phần chênh — và trả phí HAI LẦN. Nên trước mọi
thứ khác có đúng một điều kiện:

    bề rộng spread  >  2 × phí maker × giá

Sai dấu ở đây thì hàng đợi, độ trễ, mô hình khớp đều vô nghĩa. Script này đo nó trên
mọi sàn ứng viên, bằng dữ liệu CÔNG KHAI — không cần tài khoản, không cần API key.

BA CÁI BẪY, và script xử lý cả ba
---------------------------------
1. **Spread rộng trên một symbol chết KHÔNG phải cơ hội, nó là vắng mặt thị trường.**
   Một con số không kèm ngữ cảnh là một lời nói dối, nên mọi dòng đều in KHỐI LƯỢNG
   24 h bên cạnh, và có ngưỡng lọc (`--kl`).

2. **Spread 1 tick nghĩa là không chen vào giữa được.** Bạn chỉ xếp hàng, không cải
   thiện giá được. Cột `tick` nói ra điều đó — spread 1 tick là một cuộc chơi khác hẳn
   spread 8 tick.

3. **Bảng phí không lấy được nếu không đăng nhập.** Nên nó nằm gõ tay ở `PHI_MAKER`
   ngay dưới đây, và script IN RA con số nó đã dùng ở MỌI DÒNG. Một bảng phí sai mà
   giấu đi thì cả bài đo thành rác im lặng; in ra thì nhìn là thấy.

TỈ LỆ > 1 LÀ ĐIỀU KIỆN CẦN, KHÔNG PHẢI ĐỦ
------------------------------------------
Nó giả định bạn ăn TRỌN spread — tức cả hai chân đều khớp. Thực tế chân này khớp lúc
giá đang chạy về phía kia, nên phần ăn được luôn nhỏ hơn. Tỉ lệ 1,2 là chưa đủ sống;
tỉ lệ 0,3 thì khỏi bàn tiếp. Script này để LOẠI, không để chọn.
"""
import argparse
import io
import json
import sys
import urllib.error
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

#: ⚠ PHÍ MAKER BẬC THƯỜNG (VIP0 / LV1), tính bằng phần trăm notional. GÕ TAY vì không
#: sàn nào cho đọc bảng phí khi chưa đăng nhập.
#:
#: PHẢI ĐỐI CHIẾU LẠI trước khi tin bất kỳ con số nào ở dưới — phí đổi theo bậc khối
#: lượng, theo chương trình khuyến mãi, và theo cả loại tài sản. Sai một chữ số ở đây
#: là cả bảng sai đúng chừng ấy lần.
#:
#: Đây cũng là chỗ đáng thử "nếu": hạ phí xuống 0 rồi chạy lại, xem bảng đổi thế nào —
#: nó cho biết bậc VIP đáng giá bao nhiêu.
PHI_MAKER = {
    "binance-perp": 0.0200,
    "bybit-perp": 0.0200,
    "okx-perp": 0.0200,
    "hyperliquid": 0.0150,
}

TIMEOUT = 20


def _tai(url, than=None):
    """GET, hoặc POST JSON nếu có `than`. Trả dict/list đã parse."""
    du_lieu = json.dumps(than).encode() if than is not None else None
    yc = urllib.request.Request(
        url, data=du_lieu,
        headers={"User-Agent": "cat-studio/do_spread",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(yc, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def _dong(san, ma, bid, ask, kl_usd, tick):
    """Một dòng kết quả. Trả None nếu số liệu không dùng được.

    Bỏ qua thay vì đoán: bid/ask bằng 0, hoặc ask ≤ bid (sổ lệnh chéo — thường là dữ
    liệu cũ hoặc symbol ngừng giao dịch) đều là số không nói lên điều gì."""
    try:
        bid, ask, kl_usd = float(bid), float(ask), float(kl_usd)
        tick = float(tick) if tick else 0.0
    except (TypeError, ValueError):
        return None
    if bid <= 0 or ask <= bid:
        return None
    mid = (bid + ask) / 2
    spread_bps = (ask - bid) / mid * 10_000
    phi_bps = PHI_MAKER[san] * 100          # phần trăm → bps
    return {
        "san": san, "ma": ma,
        "spread_bps": spread_bps,
        "phi_bps": phi_bps,
        "ti_le": spread_bps / (2 * phi_bps),
        "tick": (ask - bid) / tick if tick else 0.0,
        "kl_trieu": kl_usd / 1e6,
    }


# ---------------------------------------------------------------------------
# Từng sàn — mỗi hàm trả về một danh sách dòng, và KHÔNG BAO GIỜ ném.
# Một sàn chết thì bảng vẫn phải in ra ba sàn còn lại.
# ---------------------------------------------------------------------------
def binance():
    gia = {d["symbol"]: d for d in _tai("https://fapi.binance.com/fapi/v1/ticker/bookTicker")}
    kl = {d["symbol"]: d for d in _tai("https://fapi.binance.com/fapi/v1/ticker/24hr")}
    tt = _tai("https://fapi.binance.com/fapi/v1/exchangeInfo")["symbols"]
    ra = []
    for s in tt:
        ma = s["symbol"]
        if s.get("status") != "TRADING" or s.get("quoteAsset") != "USDT":
            continue
        g, k = gia.get(ma), kl.get(ma)
        if not g or not k:
            continue
        tick = next((f["tickSize"] for f in s["filters"]
                     if f["filterType"] == "PRICE_FILTER"), 0)
        d = _dong("binance-perp", ma, g["bidPrice"], g["askPrice"],
                  k.get("quoteVolume", 0), tick)
        if d:
            ra.append(d)
    return ra


def bybit():
    tk = _tai("https://api.bybit.com/v5/market/tickers?category=linear")["result"]["list"]
    tt = {x["symbol"]: x for x in
          _tai("https://api.bybit.com/v5/market/instruments-info?category=linear&limit=1000")
          ["result"]["list"]}
    ra = []
    for t in tk:
        ma = t["symbol"]
        s = tt.get(ma)
        if not s or not ma.endswith("USDT"):
            continue
        d = _dong("bybit-perp", ma, t.get("bid1Price"), t.get("ask1Price"),
                  t.get("turnover24h", 0),
                  (s.get("priceFilter") or {}).get("tickSize"))
        if d:
            ra.append(d)
    return ra


def okx():
    tk = _tai("https://www.okx.com/api/v5/market/tickers?instType=SWAP")["data"]
    tt = {x["instId"]: x for x in
          _tai("https://www.okx.com/api/v5/public/instruments?instType=SWAP")["data"]}
    ra = []
    for t in tk:
        ma = t["instId"]
        s = tt.get(ma)
        if not s or not ma.endswith("-USDT-SWAP"):
            continue
        # ⚠ ĐÃ SAI MỘT LẦN Ở ĐÂY, và nó nói lên đúng cái bẫy script này sinh ra để
        # tránh: bản đầu nhân thêm `ctVal` nữa, nên `SATS-USDT-SWAP` (ctVal lớn) báo
        # khối lượng 6,7 TRIỆU TỶ USD — vô lý tới mức nhìn là thấy. Nhưng cùng công
        # thức đó trên một symbol ctVal = 1 thì sai LẶNG, không ai bắt được.
        #
        # Đúng: OKX trả `vol24h` bằng số HỢP ĐỒNG, còn `volCcy24h` ĐÃ quy ra đồng cơ
        # sở. Nên chỉ cần nhân giá một lần.
        try:
            kl = float(t.get("volCcy24h", 0)) * float(t["last"])
        except (TypeError, ValueError, KeyError):
            kl = 0
        d = _dong("okx-perp", ma, t.get("bidPx"), t.get("askPx"), kl, s.get("tickSz"))
        if d:
            ra.append(d)
    return ra


def hyperliquid(toi_da=30):
    """⚠ Sàn DUY NHẤT phải hỏi TỪNG coin một (`l2Book`), nên bị chặn ở `toi_da` coin
    theo khối lượng. Ba sàn kia trả cả bảng trong một lời gọi."""
    meta, ctx = _tai("https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"})
    ten = [u["name"] for u in meta["universe"]]
    tick_dp = [u.get("szDecimals") for u in meta["universe"]]
    cap = sorted(zip(ten, ctx, tick_dp),
                 key=lambda x: -float(x[1].get("dayNtlVlm") or 0))[:toi_da]
    ra = []
    for coin, c, _dp in cap:
        try:
            book = _tai("https://api.hyperliquid.xyz/info",
                        {"type": "l2Book", "coin": coin})
            bid = book["levels"][0][0]["px"]
            ask = book["levels"][1][0]["px"]
        except Exception:                                        # noqa: BLE001
            continue
        # Hyperliquid không công bố tick size trong `meta` theo cách đọc thẳng được,
        # nên cột `tick` để trống thay vì bịa một con số.
        d = _dong("hyperliquid", coin, bid, ask, c.get("dayNtlVlm") or 0, 0)
        if d:
            ra.append(d)
    return ra


SAN = {"binance": binance, "bybit": bybit, "okx": okx, "hyperliquid": hyperliquid}


def main():
    p = argparse.ArgumentParser(description="spread có lớn hơn hai lần phí maker không")
    p.add_argument("--kl", type=float, default=50.0,
                   help="ngưỡng khối lượng 24h, TRIỆU USD (mặc định 50)")
    p.add_argument("--top", type=int, default=25, help="in bao nhiêu dòng đầu bảng")
    p.add_argument("--san", default=",".join(SAN), help="sàn nào, cách nhau bằng dấu phẩy")
    p.add_argument("--phi", type=float, default=None,
                   help="ÉP phí maker (%%) cho MỌI sàn — dùng để hỏi 'nếu phí bằng 0 "
                        "thì sao', tức bậc VIP đáng giá bao nhiêu")
    a = p.parse_args()
    if a.phi is not None:
        for k in PHI_MAKER:
            PHI_MAKER[k] = a.phi
        print(f"  ⚠ ÉP phí maker = {a.phi} %% cho mọi sàn — đây là giả định, không phải số thật")

    tat_ca, hong = [], []
    for ten in a.san.split(","):
        ten = ten.strip()
        if ten not in SAN:
            continue
        print(f"  … đang hỏi {ten}", flush=True)
        try:
            ds = SAN[ten]()
            tat_ca += ds
            print(f"    {len(ds)} symbol")
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
            hong.append(f"{ten}: {type(e).__name__}: {e}")
            print(f"    ✘ {type(e).__name__}")

    du = [d for d in tat_ca if d["kl_trieu"] >= a.kl]
    du.sort(key=lambda d: -d["ti_le"])

    print(f"\n{'=' * 84}")
    print(f"  spread ÷ (2 × phí maker)   ·   khối lượng ≥ {a.kl:g} triệu USD/ngày")
    print(f"  {len(du)}/{len(tat_ca)} symbol qua ngưỡng khối lượng")
    print("=" * 84)
    print(f"{'sàn':<13}{'symbol':<18}{'spread':>8}{'phí':>7}{'TỈ LỆ':>8}"
          f"{'tick':>7}{'KL 24h':>12}")
    print(f"{'':<13}{'':<18}{'(bps)':>8}{'(bps)':>7}{'':>8}{'':>7}{'(triệu $)':>12}")
    print("-" * 84)
    for d in du[:a.top]:
        dau = "✔" if d["ti_le"] > 1 else " "
        tick = f"{d['tick']:.0f}" if d["tick"] else "—"
        print(f"{d['san']:<13}{d['ma']:<18}{d['spread_bps']:>8.2f}{d['phi_bps']:>7.1f}"
              f"{d['ti_le']:>7.2f}{dau}{tick:>7}{d['kl_trieu']:>12,.0f}")
    print("-" * 84)

    # ĐỐI CHIẾU VỚI HÀNG LỚN. Đầu bảng bao giờ cũng là symbol thanh khoản mỏng —
    # spread rộng vì KHÔNG AI báo giá, chứ không phải vì có chỗ cho ta. Nhìn BTC/ETH
    # bên cạnh mới thấy đầu bảng đang nói gì.
    LON = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BTC-USDT-SWAP", "ETH-USDT-SWAP",
           "SOL-USDT-SWAP", "BTC", "ETH", "SOL")
    lon = sorted((d for d in tat_ca if d["ma"] in LON), key=lambda d: -d["kl_trieu"])[:9]
    if lon:
        print("\n  ĐỐI CHIẾU — hàng thanh khoản nhất:")
        for d in lon:
            dau = "✔" if d["ti_le"] > 1 else "✘"
            print(f"{d['san']:<13}{d['ma']:<18}{d['spread_bps']:>8.2f}{d['phi_bps']:>7.1f}"
                  f"{d['ti_le']:>7.2f}{dau}{'':>7}{d['kl_trieu']:>12,.0f}")
        print("-" * 84)

    qua = [d for d in du if d["ti_le"] > 1]
    if qua:
        print(f"  {len(qua)} symbol có TỈ LỆ > 1 — cửa còn mở, nhưng đó mới là điều kiện CẦN.")
    else:
        print("  KHÔNG symbol nào có tỉ lệ > 1. Ở bậc phí này, bắt spread là sai dấu.")
        print("  Ba đường: hạ phí (bậc VIP / chương trình MM) · đổi công cụ · đổi sàn.")
        print(f"  Thử lại với phí 0: sửa `PHI_MAKER` trong {__file__}")
    if hong:
        print("\n  sàn không hỏi được:")
        for h in hong:
            print("   ", h)


if __name__ == "__main__":
    main()
