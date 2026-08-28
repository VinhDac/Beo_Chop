"""ĐO THỊ TRƯỜNG — spread có lớn hơn hai lần phí maker không?

Lõi dùng chung cho `tools/do_spread.py` (dòng lệnh) và hộp thoại Cài đặt → Nguồn dữ
liệu. MỘT nguồn sự thật: bảng in ra màn hình và bảng hiện trong app phải là cùng con
số, cùng phép tính. Hai bản chép tay thì sớm muộn lệch nhau.

Đọc `tools/do_spread.py` để hiểu VÌ SAO phép này là điều kiện CẦN của cả hệ.
"""
import json
import urllib.error
import urllib.request


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




def do(san=None, kl_toi_thieu=0.0, phi=None):
    """Quét mọi sàn, trả `(danh sách dòng đã sắp, danh sách sàn hỏng)`.

    `phi` khác None thì ÉP phí maker cho mọi sàn — dùng để hỏi "nếu phí bằng 0 thì
    sao", tức bậc VIP đáng giá bao nhiêu."""
    if phi is not None:
        for k in PHI_MAKER:
            PHI_MAKER[k] = float(phi)
    ra, hong = [], []
    for ten in (san or list(SAN)):
        if ten not in SAN:
            continue
        try:
            ra += SAN[ten]()
        except Exception as e:                                   # noqa: BLE001
            hong.append(f"{ten}: {type(e).__name__}")
    ra = [d for d in ra if d["kl_trieu"] >= kl_toi_thieu]
    ra.sort(key=lambda d: -d["ti_le"])
    return ra, hong
