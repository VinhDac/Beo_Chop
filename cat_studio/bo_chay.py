"""BỘ CHẠY — nối sơ đồ với thị trường, và đóng vòng phản hồi.

Đây là mảnh ghép cuối của một backtest chạy được. Hai đầu đã sẵn: `phat_lai.PhatLai`
phát ra dòng sự kiện, `khop_lenh.SoKhop` biết một lệnh thụ động khớp lúc nào. File này
làm bốn việc mỗi sự kiện, và **thứ tự bốn việc đó là toàn bộ phần khó**.

MỘT NHỊP — VÀ VÌ SAO THỊ TRƯỜNG PHẢI ĐI TRƯỚC
----------------------------------------------
    1. `khop.buoc(sk)`   thị trường đi qua: lệnh đang treo của ta khớp hoặc không
    2. chạy sơ đồ        chiến lược nhìn trạng thái MỚI (kể cả tồn kho vừa đổi)
    3. chốt báo giá      bid = công_bằng − lệch − biên_mua   ·   ask = … + biên_bán
    4. `khop.dong_bo()`  báo giá mới gửi đi

Đảo thứ tự 1 và 2 là **nhìn trộm tương lai**: chiến lược sẽ ra quyết định dựa trên một
sự kiện mà nó chưa thể biết, rồi lệnh vừa đặt được khớp bởi chính sự kiện đó. Độ trễ ra
(`tre_ra_ms`) chặn ca tệ nhất, nhưng không nên dựa vào một con số cấu hình để giữ đúng
một luật nhân quả — luật ấy phải nằm ở THỨ TỰ, chỗ không ai vặn được.

VÒNG PHẢN HỒI, VÀ VÌ SAO NÓ LÀ PHÉP THỬ THẬT CỦA NGỮ PHÁP
----------------------------------------------------------
Bước 1 đổi `ton_kho`; bước 2 đọc `ton_kho` qua toán hạng; số hạng `lệch += tồn kho × …`
đẩy báo giá đi; bước 4 gửi báo giá ấy ra; vòng sau lại khớp. Đó là toàn bộ cơ chế quản
trị rủi ro của một market maker, và nó chỉ tồn tại được nhờ vòng này khép kín.

Cũng chính vòng này trả lời câu **"mô hình hai tầng cổng + chuỗi có đủ dùng không"**.
Trước khi có nó, ngữ pháp mới chỉ là một thứ vẽ ra được.

LUẬT LÙI — thừa kế nguyên vẹn, nhưng an toàn hơn hẳn
-----------------------------------------------------
Ở một ngã rẽ, các nhánh được thử LẦN LƯỢT theo vị trí trên canvas (`core.flow_map`).
Nhánh nào trượt thì lùi về ngã rẽ gần nhất còn nhánh chưa thử.

Với D_02, lùi chỉ an toàn khi nhánh đó **chưa kịp bắn lệnh ra thị trường** — lùi sau
khi đã đặt lệnh là đẻ ra lệnh thứ hai. Ở đây điều kiện ấy KHÔNG CẦN nữa, vì không có
động từ nào chạm thị trường giữa chừng: số hạng chỉ cộng vào một bản nháp báo giá, và
báo giá chỉ được gửi đi ở CUỐI lượt.

Đổi lại phải **chụp lại bản nháp ở mỗi ngã rẽ và khôi phục khi lùi**. Không chụp thì
mấy số hạng của nhánh đã bỏ vẫn nằm trong báo giá — sơ đồ nói một đằng, kết quả một
nẻo, và không có gì trên màn hình lộ ra chuyện đó. Sáu số thực mỗi ngã rẽ, quá rẻ.

BIÊN DỊCH TRƯỚC
---------------
`bien_dich()` đổi sơ đồ thành một danh sách lệnh phẳng: tên toán hạng → hàm tính, tên
đơn vị → mã số, đích → chỉ số ô. Chạy xong không đụng một chuỗi nào.

Hai cái lợi, và cái thứ hai mới là cái đáng giá: (1) nhanh; (2) **mọi lỗi "không hiểu"
nổ ra lúc biên dịch, kèm nhãn khối** — chứ không nổ ở sự kiện thứ bốn triệu.

TỐC ĐỘ ĐÃ ĐO
------------
**0,08 triệu sự kiện/giây** với sơ đồ mẫu 9 khối — tức ~12 µs mỗi sự kiện, và một ngày
(~10 triệu sự kiện) mất khoảng **2 phút**. Chậm hơn `PhatLai` (1,97 tr/s) và
`SoKhop.buoc` (3,44 tr/s) hai bậc, vì mỗi sự kiện phải đi hết sơ đồ.

Chia ra: `mot_luot` ~37%, `dong_bo` ~30%, còn lại là khớp lệnh và phát lại. Không có
chỗ nào phình bất thường — đây là cái giá của việc chạy một đồ thị bằng Python.

Đủ để lặp trong một buổi, không đủ để quét tham số hàng trăm lần. Ngày nào cần nhanh
hơn thì chỗ sửa là **đưa vòng lặp ra khỏi Python**, không phải vặn thêm ở đây; hoặc
**bỏ chạy sơ đồ khi không có gì nó đọc bị đổi** — bộ biên dịch vốn đã biết chương
trình đọc những toán hạng nào, nên phép so đó dựng được mà không phải đoán.

HAI ĐIỀU BỘ CHẠY NÓI RA VỀ CHÍNH SƠ ĐỒ MẪU
-------------------------------------------
Chạy 400.000 sự kiện giả, sơ đồ mẫu treo ĐÚNG ở bid/ask:

1. **Nó requote gần như mỗi sự kiện** — 399.000 lần đặt trên 400.000 sự kiện. Vì
   `công bằng = mid`, mà `mid` nhúc nhích là báo giá đổi, mà đổi giá là **về cuối hàng
   đợi**. Hệ quả đo được: ba mức `phan_huy_truoc` (0 · 0,5 · 1) chỉ chênh nhau ~2,5%
   số lần khớp — vị trí hàng đợi chưa kịp có ý nghĩa thì đã bị vứt đi rồi.

   Một market maker thật giữ báo giá cho tới khi nó lệch quá N tick. Muốn diễn tả điều
   đó cần một toán hạng mà kho CHƯA CÓ (`tuoi_bao_gia`, hoặc giá báo hiện tại) — xem
   `tai_lieu/o_cam_trong.md`. Đây là ổ cắm đầu tiên do chính bộ chạy chỉ ra.

2. **~0,9% số lần bị post-only từ chối, và đó là chiến lược đang KÊU CỨU.** Khi tồn
   kho chạm hạn mức, `lệch` đẩy báo giá đi 2,5 tick trong khi spread chỉ 1–3 tick —
   ask rơi xuống dưới bid thị trường, sàn từ chối. Nói đúng nghĩa: *"tôi muốn thoát
   hàng bằng mọi giá"*, mà lệnh thụ động thì không thoát bằng mọi giá được.

   Đó chính là chỗ cần **động từ thứ ba (lệnh chủ động)**, và giờ ta có con số chứ
   không phải suy đoán.
"""
import math
from collections import deque

from . import core
from . import kho
from . import khop_lenh
from . import phat_lai

NAN = float("nan")

# ---- ô của bản nháp báo giá. Chỉ số chứ không phải tên: truy cập list nhanh hơn dict,
#      và vòng lặp này chạy mười triệu lần một ngày.
CONG_BANG = 0
BIEN_MUA = 1
BIEN_BAN = 2
LECH = 3
LOT_MUA = 4
LOT_BAN = 5
SO_O = 6

#: đích (chuỗi, do `core.DICH`) → những ô nó ghi vào. `bien` và `lot` chạm CẢ HAI phía.
O_CUA_DICH = {
    "cong_bang": (CONG_BANG,),
    "bien": (BIEN_MUA, BIEN_BAN), "bien_mua": (BIEN_MUA,), "bien_ban": (BIEN_BAN,),
    "lech": (LECH,),
    "lot": (LOT_MUA, LOT_BAN), "lot_mua": (LOT_MUA,), "lot_ban": (LOT_BAN,),
}

#: Bản nháp lúc BẮT ĐẦU mỗi lượt.
#:
#: ⚠ `cong_bang` là NaN chứ không phải 0, và đó là chủ ý: sơ đồ nào không đặt giá công
#: bằng thì KHÔNG CÓ báo giá, chứ không phải có một báo giá quanh mốc 0. NaN lan qua
#: mọi phép tính rồi `dong_bo` thấy giá không hữu hạn và rút — đúng thứ phải xảy ra.
#: Đặt 0 thì bid = −biên, một con số vô nghĩa mà vẫn gửi đi được.
NHAP_GOC = (NAN, 0.0, 0.0, 0.0, 0.0, 0.0)

# ---- mã đơn vị. Số chứ không phải chuỗi, cùng lý do với chỉ số ô.
DV_TRAN = 0        # không quy đổi (giá tuyệt đối · lot · đại lượng tự mang đơn vị)
DV_TICK = 1
DV_SPREAD = 2
DV_BPS = 3
MA_DON_VI = {"tick": DV_TICK, "spread": DV_SPREAD, "bps": DV_BPS}

# ---- loại lệnh trong chương trình đã biên dịch
LENH_CONG = 0      # cổng: rẽ nhánh
LENH_SO_HANG = 1


def _so_vi(x, le=0):
    """Số theo kiểu Việt: `.` ngăn nghìn, `,` thập phân.

    ⚠ Python mặc định `f"{x:,}"` cho ra kiểu Anh — và trong một giao diện tiếng Việt
    thì `2,970 giây` đọc thành *hai phẩy chín bảy giây*, sai đúng một nghìn lần. Chuỗi
    này do Python sinh rồi hiện thẳng lên màn hình, nên phải đúng quy ước ngay tại đây.

    Không dùng `locale`: nó là trạng thái TOÀN CỤC của tiến trình, đổi một chỗ là đổi
    mọi chỗ, và trên Windows thì tên locale còn khác hệ khác."""
    return f"{x:,.{le}f}".translate(str.maketrans(",.", ".,")).replace("-", "−")


def _khoang(giay):
    """Quãng thời gian → chữ đọc được. `2970` → `49 phút`, không phải `2.970 giây`."""
    if giay < 90:
        return f"{_so_vi(giay, 1)} giây"
    if giay < 5400:
        return f"{_so_vi(giay / 60)} phút"
    return f"{_so_vi(giay / 3600, 1)} giờ"


class LoiChay(Exception):
    """Sơ đồ không chạy được. Câu nói ra PHẢI mang nhãn khối (`[1B.2]`).

    Một dòng "KeyError: 'atr'" giữa lúc backtest thì người dùng không có cách nào lần
    ra khối nào gây chuyện — mà sơ đồ có thể đang có hai mươi khối."""


class Nhin:
    """Ảnh chụp thị trường + sổ của ta tại MỘT thời điểm — thứ toán hạng đọc vào.

    Một đối tượng dùng lại suốt cả lượt chạy, không đẻ mới mỗi sự kiện: mười triệu
    object một ngày là mười triệu lần cho bộ gom rác làm việc thay cho chiến lược.

    Nó KHÔNG bọc `PhatLai` bằng cách giữ tham chiếu rồi đọc xuyên qua, mà chép sáu con
    số sang. Lý do: `ton_kho` đến từ `SoKhop` chứ không từ `PhatLai`, nên đằng nào cũng
    phải có một chỗ gộp hai nguồn — và gộp ở đây thì `kho/` chỉ cần biết đúng một hình
    dạng, không phải biết luồng dữ liệu đến từ đâu."""

    __slots__ = ("bid", "ask", "bid_kl", "ask_kl", "co_so", "ton_kho")

    def __init__(self):
        self.bid = self.ask = NAN
        self.bid_kl = self.ask_kl = 0.0
        self.co_so = False
        self.ton_kho = 0.0


# ---------------------------------------------------------------------------
# Biên dịch
# ---------------------------------------------------------------------------


def _nhan(doc_nhan, sid):
    return doc_nhan.get(sid) or "?"


def _bien_dich_dieu_kien(c, nhan):
    """Một điều kiện → `(hàm_trái, mã_phép, hàm_phải_hoặc_None, hằng_số, mã_đơn_vị)`.

    Vế phải có hai dạng và chúng loại trừ nhau: so với một ĐẠI LƯỢNG khác (`hàm_phải`),
    hoặc so với một CON SỐ (`hằng_số` + `mã_đơn_vị`). Biên dịch cả hai thành cùng một
    hình dạng để vòng lặp chỉ có một nhánh `if`."""
    ten = (c.get("trai") or {}).get("ten")
    f = kho.TINH.get(ten)
    if f is None:
        raise LoiChay(f'[{nhan}] không tính được "{ten}" — toán hạng này không có '
                      f"trong kho. Mở lại khối và chọn một đại lượng đang có.")
    phep = c.get("phep")
    if phep not in core.PHEP_SO:
        raise LoiChay(f"[{nhan}] chưa chọn phép so sánh.")

    p = c.get("phai") or {}
    g = kho.TINH.get(p["ten"]) if p.get("ten") else None
    if p.get("ten") and g is None:
        raise LoiChay(f'[{nhan}] không tính được vế phải "{p["ten"]}".')
    try:
        hang = float(p.get("value", 0.0))
    except (TypeError, ValueError):
        hang = 0.0
    return (f, phep, g, hang, MA_DON_VI.get(p.get("tinh"), DV_TRAN))


def _bien_dich_luong(l, dich, nhan):
    """`{he_so, toan_hang, don_vi}` → `(hệ_số, hàm_toán_hạng_hoặc_None, mã_đơn_vị)`."""
    l = l or {}
    try:
        he = float(l.get("he_so", 0.0))
    except (TypeError, ValueError):
        he = 0.0
    th = l.get("toan_hang")
    f = kho.TINH.get(th) if th else None
    if th and f is None:
        raise LoiChay(f'[{nhan}] không tính được "{th}" — toán hạng này không có '
                      f"trong kho.")
    dv = MA_DON_VI.get(l.get("don_vi"), DV_TRAN)
    # `khoang_cach`/`muc_gia` mà không khai thước đo thì lượng KHÔNG quy đổi được sang
    # giá. Chặn ở đây chứ không đoán: `validate_actions` đã nói câu này rồi, nhưng file
    # lưu tay hoặc sơ đồ cũ vẫn lọt tới đây được.
    if dv == DV_TRAN and f is None and core.DICH_KIEU.get(dich) != "lot":
        if l.get("don_vi") != "gia":
            raise LoiChay(f'[{nhan}] "{core.DICH_NGAN.get(dich, dich)}" nhận một khoảng '
                          f"cách giá, mà lượng chưa chọn thước đo (tick · spread · bps).")
    return (he, f, dv)


def bien_dich(doc, tab=None):
    """Sơ đồ → chương trình phẳng. Mọi lỗi "không hiểu" nổ RA ĐÂY, kèm nhãn khối.

    Trả `(lenh, dau, khoi)`:
      `lenh[i]`  = `(loại, dữ_liệu, [chỉ_số_nhánh…])` — nhánh đã theo đúng thứ tự ưu tiên
      `dau`      = chỉ số khối đầu tiên (`-1` nếu sơ đồ rỗng)
      `khoi[i]`  = `{"id", "nhan"}` — để câu lỗi lúc chạy chỉ đúng khối, và để `soi_luot`
                   trỏ được về đúng khối trên canvas"""
    doc = core.normalize_process(doc)
    tab = tab if tab in core.TABS else core.TAB_BAO_GIA
    g = doc.get(tab) or {}
    steps = g.get("steps") or []
    edges = g.get("edges") or []

    theo_id, ke = core.flow_map(steps, edges)
    doc_nhan = core.flow_order(steps, edges)["order"]
    ds = [s for s in steps if isinstance(s, dict) and s.get("id")]
    chi_so = {s["id"]: i for i, s in enumerate(ds)}

    lenh = []
    for s in ds:
        nhan = _nhan(doc_nhan, s["id"])
        nhanh = [chi_so[x] for x in ke.get(s["id"], ()) if x in chi_so]
        t = s.get("type")
        if core.is_start_step(s):
            # Khối Bắt đầu không làm gì — nó là ĐIỂM NEO. Biên dịch thành một cổng
            # không điều kiện: luôn qua, rồi đi tiếp. Rẻ hơn một loại lệnh thứ ba.
            lenh.append((LENH_CONG, (), nhanh))
        elif t == core.CHECK_COND:
            lenh.append((LENH_CONG,
                         tuple(_bien_dich_dieu_kien(c, nhan)
                               for c in (s.get("conditions") or [])),
                         nhanh))
        elif t == core.SO_HANG:
            dich = s.get("dich")
            o = O_CUA_DICH.get(dich)
            if o is None:
                raise LoiChay(f'[{nhan}] chưa chọn sửa cái gì.')
            phep = s.get("phep")
            if phep not in core.PHEP_CHO_DICH[core.DICH_KIEU[dich]]:
                raise LoiChay(
                    f'[{nhan}] "{core.DICH[dich]}" không nhận phép '
                    f'"{core.PHEP_GAN.get(phep, phep)}".')
            khi = s.get("khi")
            lenh.append((LENH_SO_HANG,
                         (o, phep, _bien_dich_luong(s.get("luong"), dich, nhan),
                          _bien_dich_dieu_kien(khi, nhan) if khi else None),
                         nhanh))
        else:
            raise LoiChay(f'[{nhan}] loại khối "{t}" không chạy được.')

    dau = core.flow_entry(steps, edges)
    return lenh, chi_so.get(dau, -1), [{"id": s["id"], "nhan": _nhan(doc_nhan, s["id"])}
                                       for s in ds]


# ---------------------------------------------------------------------------
# Chạy MỘT LƯỢT của sơ đồ
# ---------------------------------------------------------------------------


def _gia_tri_phai(dk, nh, mid, spread, tick):
    """Vế phải của một điều kiện, đã quy về cùng thước với vế trái."""
    _, _, g, hang, dv = dk
    if g is not None:
        return g(nh)
    if dv == DV_TICK:
        return hang * tick
    if dv == DV_SPREAD:
        return hang * spread
    if dv == DV_BPS:
        return hang * mid * 1e-4
    return hang


def _khop_dk(dk, nh, mid, spread, tick):
    f, phep, _, _, _ = dk
    a = f(nh)
    if phep == "la_dung":
        return bool(a)
    if phep == "la_sai":
        return not a
    b = _gia_tri_phai(dk, nh, mid, spread, tick)
    # ⚠ NaN so với gì cũng ra False — và đó ĐÚNG là thứ ta muốn. Mất sổ lệnh thì `mid`
    # là NaN, nên mọi cổng số học đều TRƯỢT thay vì khớp bừa. Cổng duy nhất còn trả lời
    # được lúc đó là `co_so là SAI`, tức đúng cái cổng phải trả lời.
    if phep == ">=":
        return a >= b
    if phep == ">":
        return a > b
    if phep == "<=":
        return a <= b
    if phep == "<":
        return a < b
    if phep == "==":
        return a == b
    return a != b


def _luong(lg, nh, mid, spread, tick):
    he, f, dv = lg
    v = he * f(nh) if f is not None else he
    if dv == DV_TICK:
        return v * tick
    if dv == DV_SPREAD:
        return v * spread
    if dv == DV_BPS:
        return v * mid * 1e-4
    return v


def mot_luot(lenh, dau, nh, tick, nhap):
    """Chạy sơ đồ MỘT lượt, đổ kết quả vào `nhap` (list 6 ô). Trả `nhap`.

    Nhận `nhap` từ ngoài chứ không tự tạo: một list mới mỗi sự kiện là mười triệu list
    một ngày.

    ⚠ Hàm này KHÔNG chạm `SoKhop` và KHÔNG chạm `PhatLai` — nó chỉ đọc `nh` và ghi vào
    `nhap`. Nhờ vậy nó dùng chung được cho backtest lẫn live: *"test như nào thì live
    như thế"* thành chuyện của kiến trúc chứ không phải của kỷ luật."""
    nhap[:] = NHAP_GOC
    if dau < 0:
        return nhap

    mid = (nh.bid + nh.ask) * 0.5
    spread = nh.ask - nh.bid

    i = dau
    ngan_xep = []                 # [(chỉ_số_khối, nhánh_kế_tiếp, bản_chụp_nháp)]
    while True:
        loai, dl, nhanh = lenh[i]

        if loai == LENH_SO_HANG:
            o, phep, lg, khi = dl
            # `khi` là điều kiện gắn TRÊN khối — trượt thì BỎ QUA số hạng này rồi đi
            # tiếp, KHÔNG lùi. Khác hẳn cổng: cổng trượt là "đường này sai", còn `khi`
            # trượt chỉ là "số hạng này lượt nay không góp gì".
            if khi is None or _khop_dk(khi, nh, mid, spread, tick):
                v = _luong(lg, nh, mid, spread, tick)
                if phep == "=":
                    for k in o:
                        nhap[k] = v
                elif phep == "+=":
                    for k in o:
                        nhap[k] += v
                else:
                    for k in o:
                        nhap[k] *= v
            qua = True
        else:
            # Cổng: MỌI điều kiện phải khớp (VÀ). Không có HOẶC — muốn "hoặc" thì tách
            # thành hai nhánh, vì nhìn sơ đồ mới thấy được, còn chữ "hoặc" giấu trong
            # hộp thoại thì không.
            #
            # ⚠ CHỖ NÀY NGẮT Ở ĐIỀU KIỆN SAI ĐẦU TIÊN, và bản D_02 cố ý làm NGƯỢC LẠI:
            # nó tính đủ mọi điều kiện dù đã biết cổng trượt, để nhật ký còn trả lời
            # được câu *"ba điều kiện kia lúc đó bằng bao nhiêu"*. Không có con số đó
            # thì soi một lượt chạy chỉ thấy "cổng trượt" mà không biết vì sao.
            #
            # Ngắt sớm ở đây vì HIỆN CHƯA CÓ NHẬT KÝ (`o_cam_trong.md`), nên cái mất là
            # số 0 còn cái được là thật — cổng thường trượt ngay ở điều kiện đầu. Ngày
            # làm nhật ký thì thêm một `mot_luot_ghi()` chạy đủ, đừng bỏ hàm này: soi
            # một lượt là việc thỉnh thoảng, chạy mười triệu lượt là việc thường xuyên.
            qua = True
            for c in dl:
                if not _khop_dk(c, nh, mid, spread, tick):
                    qua = False
                    break

        if qua:
            if not nhanh:
                return nhap                       # hết đường — chốt bản nháp ở đây
            if len(nhanh) > 1:
                # Ngã rẽ: chụp bản nháp lại đã. Không chụp thì mấy số hạng của nhánh bị
                # bỏ vẫn nằm trong báo giá — sơ đồ nói một đằng, kết quả một nẻo.
                ngan_xep.append((i, 1, tuple(nhap)))
            i = nhanh[0]
            continue

        # ---- TRƯỢT: lùi về ngã rẽ gần nhất còn nhánh chưa thử ----
        while ngan_xep:
            j, k, chup = ngan_xep[-1]
            _, _, nh_j = lenh[j]
            if k < len(nh_j):
                ngan_xep[-1] = (j, k + 1, chup)
                nhap[:] = chup                    # HOÀN NGUYÊN, xem docstring đầu file
                i = nh_j[k]
                break
            ngan_xep.pop()
        else:
            return nhap                           # không còn nhánh nào — hết lượt


def chot_bao_gia(nhap):
    """Bản nháp → `(giá_mua, lot_mua, giá_bán, lot_bán)`.

    ĐÂY LÀ ĐỊNH NGHĨA CỦA CẢ MÔ HÌNH, viết ra thành hai dòng:

        bid = công_bằng − lệch − biên_mua
        ask = công_bằng − lệch + biên_bán

    `lệch` trừ ở CẢ HAI vế — đó là điều làm nó thành "lệch" chứ không phải "giãn". Ôm
    hàng mua thì `lệch` dương, cả hai chân dịch xuống: giá mua của ta xấu đi nên ít bị
    nhồi thêm, giá bán đẹp lên nên dễ xả bớt.

    Làm tròn về tick thì `khop_lenh.dong_bo` lo — và nó tròn về phía ÍT hung hăng hơn."""
    goc = nhap[CONG_BANG] - nhap[LECH]
    return (goc - nhap[BIEN_MUA], nhap[LOT_MUA],
            goc + nhap[BIEN_BAN], nhap[LOT_BAN])


def _ghi_dieu_kien(dk, nh, mid, spread, tick):
    """Một điều kiện + CON SỐ hai vế. Vế phải `None` khi phép là đúng/sai.

    Mang theo cả `phep` để giao diện dựng lại được ĐÚNG CÂU với số thật thay vào:
    `3 ≥ 5` đọc ra ngay, còn `3 / 5` thì người đọc phải tự nhớ khối đó so kiểu gì —
    mà lúc soi là lúc đang không nhớ nổi, nếu không đã chẳng phải mở soi."""
    f, phep, _, _, _ = dk
    trai = float(f(nh))
    if phep in core.PHEP_DUNG_SAI:
        return {"trai": trai, "phai": None, "phep": phep,
                "dat": bool(trai) if phep == "la_dung" else not trai}
    return {"trai": trai, "phep": phep,
            "phai": float(_gia_tri_phai(dk, nh, mid, spread, tick)),
            "dat": _khop_dk(dk, nh, mid, spread, tick)}


def mot_luot_ghi(lenh, dau, khoi, nh, tick):
    """Chạy MỘT lượt và GHI LẠI mọi thứ. Trả `(nhap, nhat_ky)`.

    Bản SONG SINH của `mot_luot`, và khác nó đúng hai chỗ — cả hai đều cố ý:

      1. **Tính ĐỦ mọi điều kiện của một cổng**, không ngắt ở cái sai đầu tiên. Ngắt
         sớm thì soi xong vẫn không trả lời được câu *"ba điều kiện kia lúc đó bằng bao
         nhiêu"* — mà đó chính là câu người ta mở soi ra để hỏi.
      2. **Ghi lại cả khối đã THỬ RỒI BỎ.** Nhánh trượt cũng là một phần của câu trả
         lời: không thấy nó thì người dùng tưởng nhánh đó chưa bao giờ được xét tới.

    ⚠ HAI BẢN PHẢI LUÔN CHO CÙNG MỘT KẾT QUẢ. Đây là một nguồn sự thật bị chép làm hai,
    tức đúng thứ file này vẫn cảnh báo ở mọi chỗ khác — nên nó được canh bằng một phép
    kiểm chạy CẢ HAI trên hàng nghìn sơ đồ và trạng thái ngẫu nhiên rồi so từng ô
    (`tests/test_soi.py`). Chép làm hai là cố ý: `mot_luot` chạy mười triệu lần một
    ngày, còn bản này chạy mỗi lần người dùng bấm chuột.
    """
    nhap = list(NHAP_GOC)
    nhat_ky = []
    if dau < 0:
        return nhap, nhat_ky

    mid = (nh.bid + nh.ask) * 0.5
    spread = nh.ask - nh.bid

    i = dau
    ngan_xep = []
    while True:
        loai, dl, nhanh = lenh[i]
        ghi = {"id": khoi[i]["id"], "nhan": khoi[i]["nhan"]}

        if loai == LENH_SO_HANG:
            o, phep, lg, khi = dl
            ghi["loai"] = "so_hang"
            ap_dung = True
            if khi is not None:
                ghi["khi"] = _ghi_dieu_kien(khi, nh, mid, spread, tick)
                ap_dung = ghi["khi"]["dat"]
            ghi["ap_dung"] = ap_dung
            if ap_dung:
                v = _luong(lg, nh, mid, spread, tick)
                ghi["luong"] = float(v)
                ghi["truoc"] = [float(nhap[k]) for k in o]
                if phep == "=":
                    for k in o:
                        nhap[k] = v
                elif phep == "+=":
                    for k in o:
                        nhap[k] += v
                else:
                    for k in o:
                        nhap[k] *= v
                ghi["sau"] = [float(nhap[k]) for k in o]
            qua = True
        else:
            ghi["loai"] = "cong"
            # ⚠ ĐỦ MỌI ĐIỀU KIỆN. Đây là chỗ khác `mot_luot` nhiều nhất.
            ds = [_ghi_dieu_kien(c, nh, mid, spread, tick) for c in dl]
            ghi["dieu_kien"] = ds
            qua = all(c["dat"] for c in ds)

        ghi["qua"] = qua
        nhat_ky.append(ghi)

        if qua:
            if not nhanh:
                return nhap, nhat_ky
            if len(nhanh) > 1:
                ngan_xep.append((i, 1, tuple(nhap)))
            i = nhanh[0]
            continue

        while ngan_xep:
            j, k, chup = ngan_xep[-1]
            _, _, nh_j = lenh[j]
            if k < len(nh_j):
                ngan_xep[-1] = (j, k + 1, chup)
                nhap[:] = chup
                # Đánh dấu khối BỊ BỎ: mọi thứ ghi từ ngã rẽ đó trở đi, TRỪ khối cuối.
                # Không đánh dấu thì nhật ký đọc như thể số hạng của chúng vẫn có tác
                # dụng, trong khi chúng vừa bị hoàn nguyên sạch.
                #
                # ⚠ Trừ khối cuối vì đó chính là khối vừa TRƯỢT — nó là NGUYÊN NHÂN
                # phải lùi, không phải nạn nhân. Gộp nó vào nhóm "bị bỏ" là giấu mất
                # đúng câu trả lời người ta mở soi ra để tìm.
                for g in nhat_ky[_vi_tri(nhat_ky, khoi[j]["id"]) + 1:-1]:
                    g["bo"] = True
                i = nh_j[k]
                break
            ngan_xep.pop()
        else:
            return nhap, nhat_ky


def _vi_tri(nhat_ky, sid):
    """Vị trí GẦN NHẤT của khối `sid` trong nhật ký — điểm rẽ ta vừa lùi về."""
    for k in range(len(nhat_ky) - 1, -1, -1):
        if nhat_ky[k]["id"] == sid:
            return k
    return -1


def _sach(x):
    """Dọn cho JSON nuốt được: `NaN`/`inf` → `None`.

    ⚠ `json.dumps` của Python phun ra `NaN` trần — mà đó KHÔNG phải JSON hợp lệ, và
    `JSON.parse` bên trình duyệt nổ ngay. Cầu nối pywebview đi qua đúng đường đó, nên
    một ô `cong_bang` chưa đặt (khởi điểm là NaN, xem `NHAP_GOC`) là đủ làm vỡ cả lời
    gọi — mà lỗi hiện ra lại là "không đọc được phản hồi", không ai lần ra nổi.

    `None` chứ không phải `0`: giao diện phải phân biệt được *chưa đặt* với *đặt bằng
    không*. Hai chuyện khác hẳn nhau, và với `cong_bang` thì một cái là không có báo
    giá còn cái kia là báo giá quanh mốc 0."""
    if isinstance(x, float):
        return x if x == x and x not in (float("inf"), float("-inf")) else None
    if isinstance(x, dict):
        return {k: _sach(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_sach(v) for v in x]
    return x


def soi_luot(doc, nhin, tick, tab=None):
    """Chụp MỘT lượt chạy tại một trạng thái cho sẵn. HÀM THUẦN — xem `KetQua.mau`.

    `nhin` là dict sáu số (`bid` · `ask` · `bid_kl` · `ask_kl` · `co_so` · `ton_kho`),
    lấy thẳng từ một điểm mẫu. Không phát lại, không đọc file, không giữ trạng thái —
    nên bấm bao nhiêu lần cũng tức thì, và bấm lại đúng mốc đó luôn ra đúng một kết quả.
    """
    lenh, dau, khoi = bien_dich(doc, tab)
    nh = Nhin()
    nh.bid = float(nhin.get("bid", NAN))
    nh.ask = float(nhin.get("ask", NAN))
    nh.bid_kl = float(nhin.get("bid_kl", 0.0))
    nh.ask_kl = float(nhin.get("ask_kl", 0.0))
    nh.co_so = bool(nhin.get("co_so", False))
    nh.ton_kho = float(nhin.get("ton_kho", 0.0))

    nhap, nhat_ky = mot_luot_ghi(lenh, dau, khoi, nh, tick)
    gm, lm, gb, lb = chot_bao_gia(nhap)
    mo_hinh = khop_lenh.MoHinh(tick)
    mid = (nh.bid + nh.ask) * 0.5
    return _sach({
        "nhin": {"bid": nh.bid, "ask": nh.ask, "bid_kl": nh.bid_kl,
                 "ask_kl": nh.ask_kl, "co_so": nh.co_so, "ton_kho": nh.ton_kho,
                 "mid": mid if mid == mid else None,
                 "spread": (nh.ask - nh.bid) if nh.co_so else None},
        "nhap": {"cong_bang": nhap[CONG_BANG], "bien_mua": nhap[BIEN_MUA],
                 "bien_ban": nhap[BIEN_BAN], "lech": nhap[LECH],
                 "lot_mua": nhap[LOT_MUA], "lot_ban": nhap[LOT_BAN]},
        # Giá ĐÃ LÀM TRÒN về tick — đúng con số sẽ gửi đi, không phải con số trong đầu
        # sơ đồ. Hai cái lệch nhau tới nửa tick, và đó đúng là chỗ đáng nhìn.
        "bao_gia": {
            "mua_gia": mo_hinh.lam_tron(gm, khop_lenh.MUA) if lm > 0 and gm == gm else None,
            "mua_lot": lm,
            "ban_gia": mo_hinh.lam_tron(gb, khop_lenh.BAN) if lb > 0 and gb == gb else None,
            "ban_lot": lb,
        },
        "khoi": nhat_ky,
        "tick": tick,
    })


# ---------------------------------------------------------------------------
# Chạy TOÀN BỘ
# ---------------------------------------------------------------------------


class KetQua:
    """Kết quả một lượt backtest. Mọi con số ở đây là số của Python, JSON hoá được."""

    __slots__ = ("so_su_kien", "so_luot", "khop", "mau", "lo_hong", "loi",
                 "tom_tat_khop", "tu_ms", "den_ms", "giay_chay",
                 "markout_tong", "markout_kl", "markout_ms")

    def __init__(self):
        self.so_su_kien = 0
        self.so_luot = 0
        self.khop = []
        #: MỘT ĐIỂM MẪU = MỘT ẢNH CHỤP ĐỦ DÙNG, mười số:
        #:
        #:     t · giá_trị · tồn_kho · phí_đã_trả · số_lần_từ_chối        ← để VẼ
        #:     bid · ask · bid_kl · ask_kl · có_sổ                        ← để SOI
        #:
        #: Năm số đầu cùng một trục thời gian nên biểu đồ chồng được lên nhau: nhìn một
        #: chỗ là thấy vốn tụt lúc nào, tồn kho phình lúc nào, bị từ chối dồn ở đâu.
        #:
        #: ⚠ NĂM SỐ SAU LÀ THỨ LÀM "SOI MỘT LƯỢT" CHẠY ĐƯỢC, và đây là quyết định thiết
        #: kế đắt nhất của mục đó. Cách hiển nhiên là *phát lại tới thời điểm T rồi
        #: chụp* — nhưng bộ chạy đi 0,08 triệu sự kiện/giây, nên một ngày dữ liệu mất
        #: ~2 phút. Bấm vào biểu đồ rồi ngồi chờ một phút thì không ai soi lần thứ hai.
        #:
        #: Mà điểm mẫu vốn được lấy ĐÚNG LÚC sơ đồ vừa chạy xong lượt đó: `ton_kho` ở
        #: đây chính là con số sơ đồ vừa đọc, `bid`/`ask` chính là sổ lệnh nó vừa nhìn.
        #: Cho mẫu chở thêm năm số ấy thì soi thành một HÀM THUẦN — không phát lại,
        #: không đọc file, không giữ trạng thái. Tức thì, và chính xác tuyệt đối tại
        #: những mốc đã lấy mẫu.
        #:
        #: Cái giá: mẫu phình gấp đôi (~160 KB cho hai ngày). Rẻ hơn hai phút chờ rất
        #: nhiều lần. Đổi lại chỉ soi được ĐÚNG những mốc đã lấy mẫu — giao diện bám
        #: vào mốc gần nhất và nói rõ đang xem mốc nào, chứ không giả vờ soi được mọi
        #: mili-giây.
        self.mau = []
        self.lo_hong = []            # [(tu, den)] — quãng MÙ, kết quả không đáng tin
        self.loi = ""
        self.tom_tat_khop = {}
        self.tu_ms = self.den_ms = 0
        self.giay_chay = 0.0
        self.markout_tong = 0.0
        self.markout_kl = 0.0
        self.markout_ms = 0

    def bang(self):
        d = dict(self.tom_tat_khop)
        tick = self.tom_tat_khop.get("gia_dinh", {}).get("buoc_gia") or 1.0
        d.update({"so_su_kien": self.so_su_kien, "so_luot": self.so_luot,
                  "so_lan_khop": len(self.khop), "loi": self.loi,
                  "tu_ms": self.tu_ms, "den_ms": self.den_ms,
                  "giay_chay": round(self.giay_chay, 2),
                  "markout_ms": self.markout_ms,
                  "markout_tong": self.markout_tong,
                  "markout_kl": self.markout_kl,
                  # Trung bình MỖI LOT, quy ra TICK — dạng đọc được bằng mắt: "sau một
                  # giây, mỗi lot khớp lãi/lỗ trung bình bao nhiêu tick".
                  "markout_tick": (self.markout_tong / self.markout_kl / tick
                                   if self.markout_kl else 0.0)})
        return d


#: Lấy mẫu bao lâu một điểm (ms) — mốc BAN ĐẦU, sẽ tự giãn ra. Xem `TOI_DA_MAU`.
NHIP_VON_MS = 1000

#: TRẦN SỐ ĐIỂM MẪU. Chạm trần thì bỏ một nửa số điểm và nhân đôi nhịp lấy mẫu.
#:
#: ⚠ Không có nó thì độ phân giải cố định 1 giây kéo theo số điểm tăng tuyến tính theo
#: độ dài lượt chạy — đo thật: hai ngày cho **130.000 điểm, 10 MB JSON** đi qua cầu
#: nối, cho một biểu đồ rộng 1000 px. Mất vài giây chỉ để chuyển thứ mắt không thấy.
#:
#: Giãn ra thì độ phân giải giảm dần: một ngày ~1 s/điểm, một tuần ~4 s, một tháng
#: ~16 s. Đọc một đường vốn thì chừng đó thừa sức — và giao diện còn nén tiếp về 500
#: nhóm, có GIỮ đỉnh và đáy mỗi nhóm nên cú sụt sâu nhất không bị nuốt.
TOI_DA_MAU = 3000

#: MARKOUT — sau khi khớp bao lâu thì đo lại giá.
#:
#: ⚠ ĐÂY LÀ CON SỐ QUAN TRỌNG NHẤT CỦA MARKET MAKING, và là thứ bảng lãi lỗ không nói
#: ra. Lãi lỗ trộn ba chuyện vào một số: ăn spread, trả phí, và **bị chọn ngược**. Chỉ
#: cái thứ ba mới cho biết chiến lược có đang bị người khác lấy tiền hay không.
#:
#: Cách đo: mua 1 lot ở giá `p`, một giây sau `mid` là `m` thì phần lời tức thời là
#: `(m − p)`. Cộng dồn mọi lần khớp:
#:
#:     markout ÂM  → khớp xong giá đi NGƯỢC. Ta là bên bị chọn — người khớp vào ta biết
#:                   thứ ta không biết. Càng khớp nhiều càng lỗ, và nới spread cũng
#:                   không cứu được nếu nguyên nhân là báo giá đứng im khi chợ đã đi.
#:     markout DƯƠNG → ta đang bắt được đúng phần thưởng của việc cung cấp thanh khoản.
#:                   Nếu vẫn lỗ thì vấn đề là PHÍ, một bài toán khác hẳn.
#:
#: Một giây là mốc thường dùng: đủ dài để nhiễu vi cấu trúc lắng, đủ ngắn để chưa lẫn
#: với xu hướng.
MARKOUT_MS = 1000


def chay(doc, p, mo_hinh, tab=None, gioi_han=0, moc_von_ms=NHIP_VON_MS,
         markout_ms=MARKOUT_MS):
    """Chạy `doc` trên dòng sự kiện `p`. Trả `KetQua`.

    `gioi_han` > 0 thì dừng sau chừng ấy sự kiện — để thử nhanh mà không nạp cả ngày.

    ⚠ THỨ TỰ BỐN VIỆC TRONG VÒNG LẶP LÀ PHẦN KHÓ NHẤT CỦA FILE NÀY. Xem đầu file."""
    import time

    lenh, dau, _ = bien_dich(doc, tab)
    khop = khop_lenh.SoKhop(mo_hinh)
    tick = mo_hinh.buoc_gia
    nh = Nhin()
    nhap = list(NHAP_GOC)
    kq = KetQua()
    kq.markout_ms = markout_ms
    t0 = time.perf_counter()
    moc_sau = 0
    cho_markout = deque()            # [(đáo_hạn, giá, bên, kl)]
    mo_lo_hong = 0

    while True:
        loai = p.buoc()
        if loai is None or (gioi_han and kq.so_su_kien >= gioi_han):
            break
        kq.so_su_kien += 1
        t = int(p.t)
        if not kq.tu_ms:
            kq.tu_ms = t
        kq.den_ms = t

        if loai == phat_lai.MO_LO_HONG:
            mo_lo_hong = t
        elif loai == phat_lai.DONG_LO_HONG and mo_lo_hong:
            kq.lo_hong.append((mo_lo_hong, t))
            mo_lo_hong = 0

        # ---- 1. THỊ TRƯỜNG ĐI TRƯỚC ----
        moi = khop.buoc(p)
        if moi:
            kq.khop.extend(moi)
            for f in moi:
                cho_markout.append((t + markout_ms, f["gia"], f["ben"], f["kl"]))

        # MARKOUT: lần khớp nào đủ tuổi thì chốt sổ với `mid` HIỆN TẠI.
        if cho_markout and cho_markout[0][0] <= t:
            m = (p.bid + p.ask) * 0.5
            if m == m:               # `mid` NaN (đang mù) thì để đó, chờ có sổ lại
                while cho_markout and cho_markout[0][0] <= t:
                    _, gia, ben, kl = cho_markout.popleft()
                    kq.markout_tong += (m - gia) * ben * kl
                    kq.markout_kl += kl

        # ---- 2. chiến lược nhìn trạng thái MỚI ----
        nh.bid = p.bid
        nh.ask = p.ask
        nh.bid_kl = p.bid_kl
        nh.ask_kl = p.ask_kl
        nh.co_so = p.co_so
        nh.ton_kho = khop.ton_kho
        mot_luot(lenh, dau, nh, tick, nhap)
        kq.so_luot += 1

        # ---- 3 & 4. chốt rồi gửi ----
        gm, lm, gb, lb = chot_bao_gia(nhap)
        khop.dong_bo(t, gm, lm, gb, lb)

        if t >= moc_sau:
            moc_sau = t + moc_von_ms
            kq.mau.append((t, khop.gia_tri((nh.bid + nh.ask) * 0.5),
                           khop.ton_kho, khop.phi_da_tra, khop.so_tu_choi,
                           float(nh.bid), float(nh.ask),
                           float(nh.bid_kl), float(nh.ask_kl), bool(nh.co_so)))
            if len(kq.mau) > TOI_DA_MAU:
                # Bỏ một nửa, giãn nhịp gấp đôi. Không cần biết trước lượt chạy dài
                # bao nhiêu — cách này tự thích nghi với mọi độ dài.
                del kq.mau[1::2]
                moc_von_ms *= 2

    kq.giay_chay = time.perf_counter() - t0
    mid_cuoi = (nh.bid + nh.ask) * 0.5
    kq.tom_tat_khop = khop.tom_tat(mid_cuoi)
    kq.mau.append((kq.den_ms, khop.gia_tri(mid_cuoi), khop.ton_kho,
                   khop.phi_da_tra, khop.so_tu_choi,
                   float(nh.bid), float(nh.ask),
                   float(nh.bid_kl), float(nh.ask_kl), bool(nh.co_so)))
    # ⚠ Lần khớp CHƯA ĐỦ TUỔI thì BỎ, không chốt bừa ở giá cuối. Chốt bừa là trộn một
    # phép đo nửa vời vào trung bình rồi không ai biết. Số lot đo được nằm trong
    # `markout_kl` — so với `kl_da_khop` là thấy ngay phần bị bỏ.

    # ⚠ NÓI RA CHỖ KHÔNG BIẾT. Ba con số dưới đây là ba cách một kết quả có thể đẹp mà
    # vô nghĩa, và không cái nào tự lộ ra trên đường vốn.
    canh = []
    if not math.isfinite(mid_cuoi):
        canh.append("kết thúc lúc đang MẤT sổ lệnh — tồn kho còn lại không định giá "
                    "được, `gia_tri` chỉ là tiền mặt")
    if khop.ton_kho:
        canh.append(f"còn {_so_vi(khop.ton_kho, 2)} lot tồn kho — con số lãi lỗ chỉ "
                    f"chắc chắn khi tồn kho về 0, vì xả thật còn phải trả spread và phí")
    if khop.so_tu_choi:
        # NÓI THEO TỈ LỆ, không nói con số trần. "119.188 lần" nghe như nhiều; "99% số
        # sự kiện" thì nói ra đúng bản chất: chiến lược KẸT CỨNG, không phải thỉnh
        # thoảng lỡ nhịp. Hai câu khác nhau dẫn tới hai hành động khác nhau.
        ti = khop.so_tu_choi / max(1, kq.so_su_kien)
        if ti > 0.25:
            canh.append(f"KẸT: {ti:.0%} số sự kiện bị post-only từ chối. Báo giá lấn "
                        f"qua phía đối diện và không thoát ra được — thường là `lệch` "
                        f"quá mạnh so với spread, hoặc hạn mức tồn kho tắt mất phía "
                        f"duy nhất còn đặt được")
        else:
            canh.append(f"{_so_vi(khop.so_tu_choi)} lần ({ti:.1%}) bị từ chối post-only "
                        f"— báo giá có lúc lấn qua phía đối diện")
    if khop.giay_mu_co_lenh:
        canh.append(f"{_khoang(khop.giay_mu_co_lenh)} MÙ mà vẫn treo lệnh — sàn vẫn "
                    f"khớp trong quãng đó, backtest thì không thấy")
    kq.loi = " · ".join(canh)
    return kq


def chay_file(doc, symbol, tu_ngay, den_ngay, mo_hinh=None, **kw):
    """Nạp dữ liệu từ đĩa rồi chạy. `mo_hinh` để trống thì ĐO bước giá từ chính dữ liệu.

    "Đo được thì đừng hỏi" — bước giá là một sự thật của sàn, nằm sẵn trong dữ liệu."""
    from . import luu_tru

    p = phat_lai.PhatLai.tu_file(symbol, tu_ngay, den_ngay)
    if mo_hinh is None:
        tick = khop_lenh.do_buoc_gia(p.so["bid"], p.so["ask"], p.khop["gia"])
        if not math.isfinite(tick):
            raise LoiChay(
                f"Không đo được bước giá của {symbol} từ {tu_ngay}…{den_ngay} — dữ "
                f"liệu quá ít hoặc chỉ có một mức giá duy nhất. Ghi thêm rồi chạy lại.")
        c = (luu_tru.doc_cai_dat().get("khop") or {})
        mo_hinh = khop_lenh.MoHinh(
            tick,
            phi_maker_bps=c.get("phi_maker_bps", 2.0),
            tre_ra_ms=c.get("tre_ra_ms", 5.0),
            phan_huy_truoc=c.get("phan_huy_truoc", 0.0),
            phan_muc_sau=c.get("phan_muc_sau", 1.0))
    return chay(doc, p, mo_hinh, **kw)
