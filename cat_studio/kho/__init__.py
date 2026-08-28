"""KHO — danh mục mọi thứ app tính được, gom từ các module con.

⚠ KHO ĐANG RỖNG, và đó là trạng thái CÓ CHỦ Ý (đợt 3 của lần dọn sang HFT market
maker). Ba module con đã đi cùng thế giới nến:

    nen_tang.py     giá · thời gian · tài khoản · lệnh này        (75 dòng)
    chi_bao.py      ATR · MA — tính thẳng từ nến                  (46)
    engine_d02.py   atr_bps · bảng vùng nén — ý tưởng riêng D_02  (191)

Mọi toán hạng trong đó đều đọc từ một cây nến (`close(M5)`, `atr(M15, 50)`,
`zone_dem`) hoặc từ sổ lệnh của một bộ chạy không còn tồn tại. Giữ lại một danh mục
mà không gì tính ra được giá trị cho nó thì hộp thoại "Kho" vẫn bày ra đủ thứ, và mỗi
dòng trong đó là một lời hứa suông.

CƠ CHẾ THÌ Ở LẠI NGUYÊN VẸN, vì nó không dính chiến lược nào:

  · `_gom` gắn `nguon` = mã module vào từng mục, nên hộp thoại chia mục được mà không
    ai phải chép tay một danh sách thứ hai;
  · `_soat_trung` chặn NGAY LÚC IMPORT nếu hai module cùng khai một khoá. Đây là loại
    lỗi im lặng tệ nhất — hai engine cùng khai `atr` với hai nghĩa khác nhau thì mọi
    chiến lược dùng nó đều sai mà không báo gì.

CẮM LẠI: thêm module vào `MODULE` là xong, không sửa `core.py`, không sửa `api.py`,
không sửa hộp thoại. Mỗi module khai `TEN` · `MA_SO` · `MO_TA` và tuỳ ý
`CHI_BAO` / `TOAN_HANG` / `BANG_TRANG_THAI`. Một market maker sẽ cần ít nhất:

    nen_tang.py      bid · ask · mid · spread · TỒN KHO CÓ DẤU · tuổi quote
    vi_cau_truc.py   biến động thực · nhịp tick · trôi mid
    engine_mm.py     nửa-spread mục tiêu · lệch báo giá theo tồn kho

Xem `tai_lieu/o_cam_trong.md`. Bản cũ: `git show f1c90fb:cat_studio/kho/`.
"""

#: Thứ tự CÓ Ý NGHĨA: dropdown toán hạng xổ ra theo đúng thứ tự này.
MODULE = []

#: Module nào là ENGINE (mang ý tưởng chiến lược) — dùng để chia mục trong hộp thoại Kho.
ENGINE = []


def _gom(ten_thuoc_tinh):
    """Gom một danh sách từ mọi module, gắn thêm `nguon` = mã module."""
    ra = []
    for m in MODULE:
        for x in getattr(m, ten_thuoc_tinh, []):
            ra.append(dict(x, nguon=m.MA_SO))
    return ra


def _soat_trung(ds, ten):
    """Trùng khoá giữa hai module là lỗi im lặng tệ nhất — chặn ngay lúc import."""
    thay = {}
    for x in ds:
        k = x["key"]
        if k in thay:
            raise RuntimeError(
                f"kho: trùng khoá {ten} \"{k}\" giữa module \"{thay[k]}\" và "
                f"\"{x['nguon']}\". Mỗi khoá phải thuộc về đúng một nơi.")
        thay[k] = x["nguon"]
    return ds


TOAN_HANG = _soat_trung(_gom("TOAN_HANG"), "toán hạng")
CHI_BAO = _soat_trung(_gom("CHI_BAO"), "chỉ báo")
BANG_TRANG_THAI = _soat_trung(_gom("BANG_TRANG_THAI"), "bảng trạng thái")

# ---- tra cứu nhanh, để `core.py` khỏi quét lại mỗi lần ----
TOAN_HANG_KEYS = [t["key"] for t in TOAN_HANG]
THEO_KEY = {t["key"]: t for t in TOAN_HANG}


def nhan(key):
    return (THEO_KEY.get(key) or {}).get("nhan", key)


def tham_so(key):
    return (THEO_KEY.get(key) or {}).get("tham_so", [])


def danh_muc():
    """Toàn bộ kho, đã chia mục — hộp thoại "Kho" vẽ thẳng từ cái này.

    Kho rỗng thì trả về đúng ba danh sách rỗng; hộp thoại phải chịu được điều đó và
    nói ra, chứ không được vẽ một bảng trống không giải thích."""
    return {
        "module": [{
            "ma_so": m.MA_SO,
            "ten": m.TEN,
            "mo_ta": m.MO_TA,
            "la_engine": m in ENGINE,
            "nguon": getattr(m, "NGUON", ""),
            "so_chi_bao": len(getattr(m, "CHI_BAO", [])),
            "so_toan_hang": len(getattr(m, "TOAN_HANG", [])),
            "so_bang": len(getattr(m, "BANG_TRANG_THAI", [])),
        } for m in MODULE],
        "chi_bao": CHI_BAO,
        "toan_hang": TOAN_HANG,
        "bang_trang_thai": BANG_TRANG_THAI,
    }
