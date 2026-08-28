"""ĐO MỘT CON SỐ DUY NHẤT:  spread có lớn hơn hai lần phí maker không?

    python tools\\do_spread.py --kl 200

Market maker mua ở bid, bán ở ask, ăn phần chênh — và trả phí HAI LẦN. Nên trước mọi
thứ khác có đúng một điều kiện:

    bề rộng spread  >  2 × phí maker × giá

Sai dấu ở đây thì hàng đợi, độ trễ, mô hình khớp đều vô nghĩa.

⚠ File này chỉ còn là VỎ DÒNG LỆNH. Lõi nằm ở `cat_studio/do_thi_truong.py` vì hộp
thoại Cài đặt → Nguồn dữ liệu cũng gọi nó — bảng in ra màn hình và bảng hiện trong app
phải là cùng con số, cùng phép tính. Hai bản chép tay thì sớm muộn lệch nhau, và cái
lệch thì im lặng.

TỈ LỆ > 1 LÀ ĐIỀU KIỆN CẦN, KHÔNG PHẢI ĐỦ
------------------------------------------
Nó giả định bạn ăn TRỌN spread — tức cả hai chân đều khớp. Thực tế chân này khớp lúc
giá đang chạy về phía kia, nên phần ăn được luôn nhỏ hơn. Tỉ lệ 1,2 là chưa đủ sống;
tỉ lệ 0,3 thì khỏi bàn tiếp. Bảng này để LOẠI, không để chọn.
"""
import argparse
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import do_thi_truong as dtt  # noqa: E402

#: Đối chiếu với hàng lớn. Đầu bảng bao giờ cũng là symbol thanh khoản mỏng — spread
#: rộng vì KHÔNG AI báo giá, chứ không phải vì có chỗ cho ta. Nhìn BTC/ETH bên cạnh
#: mới thấy đầu bảng đang nói gì.
LON = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BTC-USDT-SWAP", "ETH-USDT-SWAP",
       "SOL-USDT-SWAP", "BTC", "ETH", "SOL")


def _dong(d, dau_hieu=True):
    dau = ("✔" if d["ti_le"] > 1 else ("✘" if not dau_hieu else " "))
    tick = f"{d['tick']:.0f}" if d["tick"] else "—"
    return (f"{d['san']:<13}{d['ma']:<18}{d['spread_bps']:>8.2f}{d['phi_bps']:>7.1f}"
            f"{d['ti_le']:>7.2f}{dau}{tick:>7}{d['kl_trieu']:>12,.0f}")


def main():
    p = argparse.ArgumentParser(
        description="is the spread wider than twice the maker fee?")
    p.add_argument("--kl", type=float, default=50.0,
                   help="24h volume floor, MILLIONS of USD (default 50)")
    p.add_argument("--top", type=int, default=25, help="how many rows to print")
    p.add_argument("--san", default=",".join(dtt.SAN),
                   help="which venues, comma-separated")
    p.add_argument("--phi", type=float, default=None,
                   help="FORCE the maker fee (%%) on every venue — use it to ask "
                        "'what if the fee were 0', i.e. what a VIP tier is worth")
    a = p.parse_args()

    if a.phi is not None:
        print(f"  ⚠ FORCING maker fee = {a.phi} % on every venue — this is an "
              f"assumption, not a real number")
    print("  … asking the venues", flush=True)
    du, hong = dtt.do([s.strip() for s in a.san.split(",")], a.kl, a.phi)
    tat_ca, _ = du, None

    print(f"\n{'=' * 84}")
    print(f"  spread ÷ (2 × maker fee)   ·   volume ≥ ${a.kl:g}M/day")
    print(f"  {len(du)} symbols clear the volume floor")
    print("=" * 84)
    print(f"{'venue':<13}{'symbol':<18}{'spread':>8}{'fee':>7}{'RATIO':>8}"
          f"{'tick':>7}{'24h vol':>12}")
    print(f"{'':<13}{'':<18}{'(bps)':>8}{'(bps)':>7}{'':>8}{'':>7}{'($M)':>12}")
    print("-" * 84)
    for d in du[:a.top]:
        print(_dong(d))
    print("-" * 84)

    lon = sorted((d for d in tat_ca if d["ma"] in LON), key=lambda d: -d["kl_trieu"])[:9]
    if lon:
        print("\n  FOR REFERENCE — the most liquid names:")
        for d in lon:
            print(_dong(d, dau_hieu=False))
        print("-" * 84)

    qua = [d for d in du if d["ti_le"] > 1]
    if qua:
        print(f"  {len(qua)} symbols have a RATIO > 1 — the door is open, but that is "
              f"only the NECESSARY condition.")
    else:
        print("  NO symbol has a ratio > 1. At this fee tier, capturing the spread has "
              "the wrong sign.")
        print("  Three ways out: lower the fee (VIP tier / MM programme) · change "
              "instrument · change venue.")
        print("  Try again with a zero fee:  --phi 0")
    if hong:
        print("\n  venues that did not answer:", ", ".join(hong))


if __name__ == "__main__":
    main()
