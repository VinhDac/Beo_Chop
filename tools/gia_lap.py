"""Sinh dữ liệu tick GIẢ rồi đổ mọi phản hồi `api` ra `webui/gia_lap.json`.

VÌ SAO CẦN
----------
Giao diện chạy trong pywebview (WebView2), không chụp màn hình được từ dòng lệnh, và
cầu nối `window.pywebview.api` chỉ tồn tại trong cửa sổ đó. Nên muốn SOI một panel —
đo chiều cao, xem có phải cuộn không, kiểm chữ có đúng quy ước số Việt không — thì phải
mở `npm run dev` trong một trình duyệt thường và **tiêm một cầu nối giả**.

`api.ts` chờ cầu nối bằng vòng lặp 40 ms suốt 10 giây (xem `cho_cau_noi`), nên tiêm SAU
khi trang đã tải vẫn kịp. Dán vào console:

    const kho = await (await fetch('/gia_lap.json')).json()
    const tra = n => () => Promise.resolve(kho[n] ?? {ok: true, value: null})
    window.pywebview = {api: Object.fromEntries(
        Object.keys(kho).map(k => [k, tra(k)]).concat([
            ['describe', () => Promise.resolve({ok: true, value: []})],
            ['save_ui',  () => Promise.resolve({ok: true})],
            ['soi_luot', (doc, n) => Promise.resolve(
                (kho._soi_mau.find(x => x.nhin.bid === n.bid
                    && x.nhin.ask === n.ask && x.nhin.ton_kho === n.ton_kho) || {})
                .kq ?? {ok: false, error: 'mốc này chưa sinh sẵn'})]]))}

⚠ PHẢN HỒI LÀ THẬT, chỉ dữ liệu là giả. Mọi bảng số đi qua đúng `bo_chay` · `khop_lenh`
· `core` như lúc chạy thật — nên soi được cả những thứ chỉ lộ ra ở dữ liệu lớn (bảng
phải cuộn, chuỗi số dài làm vỡ cột, cảnh báo dài xuống mấy dòng).

⚠ KHÔNG ĐỤNG DỮ LIỆU NGƯỜI DÙNG: ghi vào một thư mục tạm, trỏ `cai_dat["nguon"]
["thu_muc"]` sang đó, rồi TRẢ LẠI nguyên trạng trong `finally` — kể cả khi nổ giữa
chừng.

Chạy:  python tools\\gia_lap.py
"""
import io
import json
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import api as A  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import nguon_tick as NT  # noqa: E402

SYMBOL = "TRUMPUSDT"
TICK = 0.001
NGAY = ("2025-08-18", "2025-08-19")
MOI_NGAY = 260_000
#: 330 ms/sự kiện — thưa hơn thật khá nhiều, cố ý: đủ để hai ngày dữ liệu vẫn chạy
#: trong vài giây mà vẫn ra hàng trăm nghìn sự kiện, tức vẫn chạm được mọi đường đi.
NHIP_MS = 330


def _mot_ngay(r, i):
    n = MOI_NGAY
    gia = np.round(np.round(
        (np.cumsum(r.normal(0, TICK * 0.8, n)) + 9.5 + i * 0.1) / TICK) * TICK, 10)
    sp = r.integers(1, 3, n) * TICK
    t = np.arange(n, dtype="i8") * NHIP_MS + 1_755_475_200_000 + i * 86_400_000
    la_khop = r.random(n) < 0.28

    so = np.zeros(int((~la_khop).sum()), dtype=NT.DT_SO)
    so["T"] = so["t_ta"] = t[~la_khop]
    so["bid"] = gia[~la_khop]
    so["ask"] = np.round(gia[~la_khop] + sp[~la_khop], 10)
    so["bid_kl"] = r.gamma(2, 900, len(so))
    so["ask_kl"] = r.gamma(2, 900, len(so))

    kh = np.zeros(int(la_khop.sum()), dtype=NT.DT_KHOP)
    kh["T"] = kh["t_ta"] = t[la_khop]
    mua = r.random(len(kh)) < 0.5
    kh["gia"] = np.where(mua, np.round(gia[la_khop] + sp[la_khop], 10), gia[la_khop])
    kh["kl"] = r.gamma(1.5, 120, len(kh))
    kh["mua_chu_dong"] = mua

    # ĐỘ SÂU — mỗi 3 sự kiện một ảnh (~1 ảnh/giây ở nhịp này). Thật thì tỉ lệ là ~1
    # ảnh trên 9 bản ghi sổ; ở đây thưa hơn để file giả không phình, vẫn đủ để mọi
    # lần treo sâu đều có một ảnh đứng trước nó.
    #
    # ⚠ DỰNG TỪ CHÍNH `gia`, không dựng độc lập. Độ sâu mà không khớp đỉnh với luồng
    # `so` thì `phan_muc_sau` đo ra một cuốn sổ khác với cuốn đang phát lại — bài kiểm
    # xanh mà con số vô nghĩa.
    ld = np.zeros(n, dtype=bool)
    ld[::3] = True
    m = int(ld.sum())
    sa = np.zeros(m, dtype=NT.DT_SAU)
    sa["T"] = sa["t_ta"] = t[ld]
    b0, a0 = gia[ld], np.round(gia[ld] + sp[ld], 10)
    muc = np.arange(NT.SO_MUC)
    # Các mức liền nhau theo tick. Sổ thật có chỗ trống, nhưng chỗ trống chỉ làm
    # `kl_tai_muc` trả 0.0 — vẫn là ĐO ĐƯỢC, nên không mất đường đi nào.
    sa["bid"] = np.round(b0[:, None] - muc[None, :] * TICK, 10)
    sa["ask"] = np.round(a0[:, None] + muc[None, :] * TICK, 10)
    sa["bid_kl"] = r.gamma(2, 900, (m, NT.SO_MUC))
    sa["ask_kl"] = r.gamma(2, 900, (m, NT.SO_MUC))
    return so, kh, sa, t


def main():
    tam = tempfile.mkdtemp(prefix="cat_gia_lap_")
    goc = luu_tru.doc_cai_dat()
    cd = json.loads(json.dumps(goc))
    cd["nguon"] = dict(cd.get("nguon") or {}, thu_muc=tam)
    luu_tru.ghi_cai_dat(cd)
    try:
        r = np.random.default_rng(21)
        for i, ngay in enumerate(NGAY):
            so, kh, sa, t = _mot_ngay(r, i)
            # Một lỗ hổng THẬT ở ngày thứ hai — để soi được dải mù đỏ trên biểu đồ và
            # câu cảnh báo đi kèm. Không có nó thì đúng cái phần "nói ra chỗ mình không
            # biết" lại là phần không bao giờ được nhìn.
            #
            # ⚠ PHẢI KHOÉT BẢN GHI ĐI, không chỉ ghi một dòng vào sổ lỗ hổng. Bản trước
            # khai lỗ hổng mà vẫn để nguyên dữ liệu trong quãng đó — nên dải đỏ trên
            # biểu đồ là GIẢ: chiến lược vẫn nhìn thấy giá và vẫn giao dịch suốt quãng
            # "mù". Một fixture nói dối đúng về cái mà nó được dựng ra để minh hoạ.
            if i == 1:
                k = MOI_NGAY // 3
                tu, den = int(t[k]), int(t[k + 9000])
                so = so[(so["T"] < tu) | (so["T"] > den)]
                kh = kh[(kh["T"] < tu) | (kh["T"] > den)]
                sa = sa[(sa["T"] < tu) | (sa["T"] > den)]
                NT.ghi_lo_hong(SYMBOL, ngay, tu, den, "simulated")
            so.tofile(NT.duong(SYMBOL, ngay, "so"))
            kh.tofile(NT.duong(SYMBOL, ngay, "khop"))
            # ⚠ NGÀY ĐẦU CỐ Ý KHÔNG CÓ ĐỘ SÂU. Luồng `sau` bật sau hai luồng kia, nên
            # dữ liệu thật của ai cũng sẽ có một quãng đầu không có nó — và giao diện
            # phải nói ra điều đó thay vì im lặng đoán. Bản giả không dựng ca ấy thì ca
            # ấy không bao giờ được nhìn.
            if i:
                sa.tofile(NT.duong(SYMBOL, ngay, "sau"))

        a = A.Api()
        doc = a.demo_process()["value"]
        kho = {
            "bootstrap": a.bootstrap(),
            "new_process": a.new_process(),
            "demo_process": a.demo_process(),
            "validate": a.validate(doc),
            "mo_tester": a.mo_tester(doc, symbol=SYMBOL),
            "list_templates": a.list_templates(),
            "nguon_liet_ke": a.nguon_liet_ke(),
            "kho_danh_muc": a.kho_danh_muc(),
        }

        # SOI MỘT LƯỢT không gọi giả được — nó cần Python thật. Nên sinh sẵn vài lượt
        # rải đều dải thời gian, khoá theo chính bộ số `nhin` mà giao diện sẽ gửi lên.
        # Kèm cả một mốc ĐANG MÙ nếu tìm được: đó là ca hiển thị khác hẳn, và cũng là
        # ca dễ quên nhất khi soi bằng mắt.
        v = kho["mo_tester"]["value"]
        mau = v["mau"]
        tick = v["bang"]["gia_dinh"]["buoc_gia"]
        chon = [k * len(mau) // 9 for k in range(1, 9)]
        chon += [i for i, m in enumerate(mau) if not m[9]][:2]
        # ⚠ Là DANH SÁCH, khoá tra bằng SO SỐ — không phải dict khoá bằng chuỗi.
        # Đã thử khoá chuỗi `"%s|%s|%s"` và trượt sạch: Python cho `1.0`, JavaScript
        # cho `1`, nên không mốc nào tra ra. Cùng một con số, hai cách viết.
        soi = []
        for i in sorted(set(chon)):
            m = mau[i]
            nhin = {"bid": m[5], "ask": m[6], "bid_kl": m[7], "ask_kl": m[8],
                    "co_so": m[9], "ton_kho": m[2]}
            soi.append({"nhin": nhin, "kq": a.soi_luot(doc, nhin, tick), "mau": i})
        kho["_soi_mau"] = soi
        duong = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "webui", "gia_lap.json")
        with io.open(duong, "w", encoding="utf-8") as f:
            json.dump(kho, f, ensure_ascii=False)

        b = v["bang"]
        print(f"\n  {duong}   {os.path.getsize(duong) / 1024:,.0f} KB")
        print(f"  {b['so_su_kien']:,} events · {len(v['mau']):,} samples · "
              f"{len(v['lo_hong'])} gap(s)")
        print(f"  {b['so_lan_khop']:,} fills · net {b['gia_tri']:.2f} · "
              f"fees {b['phi_da_tra']:.2f} · markout {b['markout_tick']:+.3f} tick/lot")
        print(f"  {len(soi)} inspect snapshots pre-baked")
        print(f"  ⚠ {b['loi']}\n")
    finally:
        luu_tru.ghi_cai_dat(goc)
        shutil.rmtree(tam, ignore_errors=True)


if __name__ == "__main__":
    main()
