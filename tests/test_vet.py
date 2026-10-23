"""VẾT TỪNG NHỊP — cỗ máy tự kể mỗi nhịp nó chạy tới cổng nào, cổng cho ra gì.

VÌ SAO CÓ CHUYỆN NÀY. Nhật ký cửa sổ View trước đây chỉ kể mấy CÁI LỆNH, nên một lượt
chạy ba tháng không ra lệnh nào bày ra một bảng trống — đúng lúc người ta mở cửa sổ ra
để hỏi *"vì sao nó không mua"*. `mach_chay` suy được một phần chuyện ấy từ chỗ LEAN im
lặng, nhưng lời dặn đầu tệp ấy kể rõ chỗ suy có thể OAN: `set_holdings` không sinh lệnh
khi tỷ trọng đang đúng, nên cổng mở, hành động chạy, LEAN im — nhìn y hệt cổng đóng.
Nay cỗ máy TỰ NÓI, nên không còn phải suy.

Đường đi của một dòng vết, và bài này canh từng mắt:

    sinh_ma._bao_vet   bọc điều kiện mỗi cổng -> `self._vet(sym, '1A', (...))`
    sinh_ma._ham_vet   sinh ba phương thức: `_vet`, `_vet_ra`, `on_end_of_algorithm`
    (LEAN chạy)        mỗi nhịp một dòng `CAT|<giờ>|<mã>|-1A,1B` trong nhật ký
    chay_lean._doc_vet tách lại thành `{luc, ma, cong}`
    mach_view.dungVet  thành dòng «dòng dừng ở [1B]» trên nhật ký cửa sổ View

MẤY CHỖ HỎNG LẶNG bài này gác:

  1. **Hai hằng `DAU_VET` lệch nhau.** `sinh_ma` ghi dấu, `chay_lean` dò dấu, mà hai
     mô-đun cố ý KHÔNG import nhau. Lệch một ký tự thì mọi dòng vết bị bỏ, và cửa sổ
     View bày một lượt chạy im lặng — không lỗi, không cảnh báo.
  2. **Xả vết ở nhịp SAU mà mượn dấu giờ của `self.log`.** LEAN đóng dấu giờ LÚC GỌI,
     nên mọi dòng sẽ lệch đúng một nhịp — và lệch lặng, vì nhật ký vẫn đầy và vẫn
     trông đúng. Nên `_vet_ra` phải tự ghi giờ nó đã CẤT, không phải giờ bây giờ.
  3. **Nhịp CUỐI không ai xả.** Vết của nhịp cuối cùng còn treo trong `_vet_cho` —
     thiếu `on_end_of_algorithm` thì nó mất, và mất đúng cái nhịp người ta tua tới.
  4. **`_vet` trả sai giá trị.** Nó nằm TRONG điều kiện mỗi cổng, nên trả lệch một
     chút là cỗ máy rẽ sai đường — backtest vẫn chạy trơn, ra một kết quả khác.

Không mở cửa sổ, không chạy LEAN -> chạy được ở bất cứ đâu.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import chay_lean, core, hoi, lam, sinh_ma  # noqa: E402
# ⚠ BÀI NÀY CHỐT TIẾNG VIỆT — cùng lý do với mấy bài kia: nó soát CHỮ do Python dựng.
from cat_studio import ngon_ngu  # noqa: E402
ngon_ngu.dat("vi")

NL = "\n"
dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet if not dk else ''}".rstrip())
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}".rstrip())


# ---------------------------------------------------------------------------
# 1. HAI HẰNG `DAU_VET` — bẫy số 1
# ---------------------------------------------------------------------------
print("\n▸ Dấu đầu dòng vết: hai mô-đun khai riêng, phải KHỚP nhau")
kiem("`sinh_ma.DAU_VET` == `chay_lean.DAU_VET`",
     sinh_ma.DAU_VET == chay_lean.DAU_VET,
     f"— sinh_ma {sinh_ma.DAU_VET!r} · chay_lean {chay_lean.DAU_VET!r}")
kiem("và nó KHÔNG rỗng", bool(sinh_ma.DAU_VET.strip()))
# Dấu phải lạ đủ để không trùng chữ LEAN tự in ra. `CAT|` có dấu `|` nên một câu
# tiếng Anh bình thường không chứa nó.
kiem("dấu có ký tự ngăn, không phải một từ trần", "|" in sinh_ma.DAU_VET)


# ---------------------------------------------------------------------------
# 2. SINH MÃ — cổng được bọc, và ba phương thức có mặt
# ---------------------------------------------------------------------------
def _so_do(co_cong=True):
    """Sơ đồ nhỏ nhất: Bắt đầu -> (Hỏi) -> Phát tín hiệu."""
    bd = core.make_start_step()
    bd["ma"] = [{"ma": "SPY", "loai": "equity"}]
    bd["nhip"] = "ngay"
    bd["chay_cho"] = "moi_ma"
    # ⚠ ĐẶT TỶ TRỌNG, không phải «Phát tín hiệu»: tín hiệu chỉ có người nhận khi khối
    # Bắt đầu chọn «Chia vốn theo tín hiệu», mà `soat_day_chuyen` chặn đúng chuyện ấy
    # — dùng nó ở đây là bài đỏ vì một lý do chẳng dính gì tới vết.
    a = core.make_lam_step(lam.LAM_DAT_TY_TRONG)
    a["name"] = "mua"
    a["ty_trong"] = 0.3
    st = [bd, a]
    ed = [{"from": bd["id"], "to": a["id"], "port": "out"}]
    if co_cong:
        h = core.make_hoi_step("hoi_thi_truong")
        h["name"] = "quá bán?"
        h["dieu_kien"] = [core.make_dieu_kien("rsi", "<", 30,
                                              tham_so={"n": 14})]
        st = [bd, h, a]
        ed = [{"from": bd["id"], "to": h["id"], "port": "out"},
              {"from": h["id"], "to": a["id"], "port": "out"}]
    for i, x in enumerate(st):
        x["pos"] = [-220 + i * 380, 0]
    return sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "Vết",
                         "steps": st, "edges": ed})


print("\n▸ Bộ sinh mã gài vết vào mỗi cổng Hỏi")
_kq = _so_do()
kiem("sơ đồ có cổng thì sinh sạch", _kq["ok"],
     f"— {[v['message'] for v in _kq['van_de'] if v['severity'] == 'error'][:1]}")
_ma = _kq["ma"]
# Khối Bắt đầu mang số `1`, nên cổng Hỏi đứng sau nó là `2`.
kiem("cổng bọc trong `self._vet(sym, '<số khối>', (...))`",
     "if self._vet(sym, '2', ((" in _ma,
     f"— {[l.strip()[:90] for l in _ma.splitlines() if '_vet(sym' in l][:1]}")
for _ten in ("def _vet(self, sym, so, v):", "def _vet_ra(self, k):",
             "def on_end_of_algorithm(self):"):
    kiem(f"sinh ra `{_ten.split('(')[0][4:]}`", _ten in _ma)
kiem("`initialize` dựng sẵn hai ô chứa vết",
     "self._vet_cho = {}" in _ma and "self._vet_so = 0" in _ma,
     "— thiếu là `AttributeError` ở cổng đầu tiên, giữa lượt chạy")
# ⚠ XẢ VỚI GIỜ ĐÃ CẤT, không phải giờ bây giờ — bẫy số 2. `strftime` phải gọi trên
# mốc trong `_r`, chứ không phải trên `self.time`.
kiem("`_vet_ra` tự ghi giờ ĐÃ CẤT vào dòng, không mượn dấu của `self.log`",
     "_r[0].strftime(" in _ma and "self.time.strftime(" not in _ma,
     "— mượn dấu của `log` thì mọi dòng lệch đúng một nhịp, và lệch LẶNG")
kiem("và nó dò trần trước khi ghi",
     f"self._vet_so >= {sinh_ma.VET_TOI_DA}" in _ma)

print("\n▸ Sơ đồ KHÔNG cổng nào thì khỏi sinh phương thức vô dụng")
_kq0 = _so_do(co_cong=False)
kiem("sinh sạch", _kq0["ok"])
kiem("không có `_vet`", "def _vet(" not in _kq0["ma"])
kiem("không có `on_end_of_algorithm`",
     "def on_end_of_algorithm(" not in _kq0["ma"])
kiem("và `initialize` cũng không dựng ô chứa vết",
     "self._vet_cho" not in _kq0["ma"])


# ---------------------------------------------------------------------------
# 3. CHẠY THẬT BA PHƯƠNG THỨC — bẫy 2, 3, 4
# ---------------------------------------------------------------------------
print("\n▸ ⭐ Chạy thật `_vet` / `_vet_ra` / `on_end_of_algorithm`")


class _Luc:
    """Mốc thời gian giả — chỉ cần so được và `strftime` được, y `datetime` của LEAN."""

    def __init__(self, n):
        self.n = n

    def __eq__(self, o):
        return isinstance(o, _Luc) and o.n == self.n

    def strftime(self, _m):
        return f"2020-01-{self.n:02d} 16:00:00"


class _Sym:
    def __init__(self, v):
        self.value = v


def _lop_vet():
    """Lôi ba phương thức sinh ra vào một lớp giả rồi trả về MỘT thực thể.

    ⚠ CHẠY ĐÚNG MÃ SINH RA, không chép lại thân nó vào đây. Chép thì bài này canh bản
    chép của mình, còn thứ LEAN thật sự chạy thì không ai gác — đúng kiểu hàng rào
    đứng cạnh một cánh cổng khác."""
    than = []
    giu = False
    for d in _ma.splitlines():
        if d.startswith("    def "):
            giu = d.strip().startswith(("def _vet(", "def _vet_ra(",
                                        "def on_end_of_algorithm("))
        if giu:
            than.append(d)
    assert than, "khong lay duoc phuong thuc nao"
    mt = {}
    exec(compile("class G:" + NL + NL.join(than), "vet", "exec"), mt)  # noqa: S102
    g = mt["G"]()
    g._vet_cho = {}
    g._vet_so = 0
    g.nhat_ky = []
    g.time = _Luc(1)
    g.log = g.nhat_ky.append
    return g


_g = _lop_vet()
kiem("lôi được đúng ba phương thức ra khỏi mã sinh",
     all(hasattr(_g, k) for k in ("_vet", "_vet_ra", "on_end_of_algorithm")))

_A = _Sym("AAPL")
_B = _Sym("MSFT")

# --- bẫy 4: TRẢ NGUYÊN giá trị nhận được ---
kiem("`_vet` trả nguyên True", _g._vet(_A, "1A", True) is True)
kiem("`_vet` trả nguyên False", _g._vet(_A, "1B", False) is False)
# Cổng có thể ra một thứ chỉ TRUTHY (`self.portfolio[sym].invested` là bool, nhưng
# mấy đại lượng số thì ra `0.0`/`1.0`), nên hàm không được ép sang bool.
_tra = _g._vet(_A, "1C", 0.0)
kiem("và không ép kiểu — số vào thì số ra",
     _tra == 0.0 and isinstance(_tra, float) and not isinstance(_tra, bool),
     f"— {_tra!r} ({type(_tra).__name__}); ép sang bool thì cổng vẫn rẽ đúng,"
     " nhưng nó thôi là con số và chỗ nào đọc lại giá trị ấy sẽ đọc một thứ khác")

# --- nhịp 1 chưa xả: vết còn treo ---
kiem("nhịp đang chạy thì CHƯA xả ra nhật ký", _g.nhat_ky == [],
     f"— {_g.nhat_ky}")

# --- bẫy 2: sang nhịp sau mới xả, mà dòng mang giờ của nhịp CŨ ---
_g.time = _Luc(2)
_g._vet(_A, "1A", True)
kiem("sang nhịp sau thì xả nhịp cũ — đúng MỘT dòng", len(_g.nhat_ky) == 1,
     f"— {_g.nhat_ky}")
kiem("dòng mang GIỜ CỦA NHỊP CŨ (01), không phải giờ bây giờ (02)",
     _g.nhat_ky[0] == f"{sinh_ma.DAU_VET}2020-01-01 16:00:00|AAPL|1A,-1B,-1C",
     f"— {_g.nhat_ky[0]!r}")

# --- hai mã trong cùng một nhịp: mỗi mã một dòng, không lẫn vào nhau ---
_g._vet(_B, "1A", False)
_g._vet(_B, "1B", False)
kiem("mã khác trong cùng nhịp KHÔNG xả lây mã này", len(_g.nhat_ky) == 1,
     f"— {_g.nhat_ky}")

# --- bẫy 3: nhịp cuối phải có ai xả ---
_g.on_end_of_algorithm()
kiem("`on_end_of_algorithm` xả HẾT nhịp cuối còn treo", len(_g.nhat_ky) == 3,
     f"— {_g.nhat_ky}")
kiem("và mỗi mã đúng một dòng, giờ của nhịp 02",
     sorted(_g.nhat_ky[1:]) == sorted([
         f"{sinh_ma.DAU_VET}2020-01-02 16:00:00|AAPL|1A",
         f"{sinh_ma.DAU_VET}2020-01-02 16:00:00|MSFT|-1A,-1B"]),
     f"— {_g.nhat_ky[1:]}")
kiem("xả rồi thì không còn gì treo — gọi lại không ra thêm dòng nào",
     (_g.on_end_of_algorithm(), len(_g.nhat_ky))[1] == 3,
     f"— {_g.nhat_ky}")

# --- trần: hết trần thì DỪNG ghi, không ghi tiếp một nhật ký khổng lồ ---
_g2 = _lop_vet()
_g2._vet_so = sinh_ma.VET_TOI_DA
_g2.time = _Luc(5)
_g2._vet(_A, "1A", False)
_g2.on_end_of_algorithm()
kiem("hết trần thì thôi ghi", _g2.nhat_ky == [], f"— {_g2.nhat_ky}")


# ---------------------------------------------------------------------------
# 4. ĐỌC LẠI — `chay_lean._doc_vet`
# ---------------------------------------------------------------------------
print("\n▸ Tách vết ra khỏi nhật ký LEAN")
_nk = NL.join([
    "2020-01-01 16:00:00 Launching analysis for V with LEAN Engine v2.5.0.0",
    f"2020-01-02 16:00:00 {sinh_ma.DAU_VET}2020-01-01 16:00:00|AAPL|-1A,1B,-1C",
    f"2020-01-03 16:00:00 {sinh_ma.DAU_VET}2020-01-02 16:00:00||1A",
    f"{sinh_ma.DAU_VET}thieu-phan",                      # dòng cụt — phải bỏ
    f"{sinh_ma.DAU_VET}||1A",                            # thiếu giờ — phải bỏ
    "2020-01-04 16:00:00 Algorithm Id:(V) completed",
])
_ds, _cat = chay_lean._doc_vet(_nk)
kiem("lấy đúng hai dòng vết, bỏ hai dòng cụt", len(_ds) == 2, f"— {_ds}")
kiem("không bị cắt", _cat is False)
kiem("đọc đúng GIỜ CỦA CỖ MÁY, không phải dấu giờ của LEAN",
     _ds[0]["luc"] == "2020-01-01 16:00:00", f"— {_ds[0]}")
kiem("đọc đúng mã", _ds[0]["ma"] == "AAPL")
kiem("dấu trừ = cổng ĐÓNG, không dấu = cổng MỞ",
     _ds[0]["cong"] == [["1A", False], ["1B", True], ["1C", False]],
     f"— {_ds[0]['cong']}")
kiem("mã rỗng (sơ đồ chia danh mục) vẫn đọc được",
     _ds[1]["ma"] == "" and _ds[1]["cong"] == [["1A", True]], f"— {_ds[1]}")
kiem("nhật ký rỗng thì ra danh sách rỗng, không nổ",
     chay_lean._doc_vet("") == ([], False)
     and chay_lean._doc_vet(None) == ([], False))

print("\n▸ Trần của cầu nối")
_qua = NL.join(
    f"{sinh_ma.DAU_VET}2020-01-01 16:00:00|A{i}|1A"
    for i in range(chay_lean.TRAN_VET + 50))
_ds2, _cat2 = chay_lean._doc_vet(_qua)
kiem("không gửi quá trần", len(_ds2) == chay_lean.TRAN_VET, f"— {len(_ds2)}")
kiem("và NÓI RA là đã cắt", _cat2 is True,
     "— cắt lặng thì cửa sổ bày một nhật ký cụt mà trông như đầy")
kiem("trần của cầu nối không vượt trần của bộ sinh mã",
     chay_lean.TRAN_VET <= sinh_ma.VET_TOI_DA,
     f"— cầu nối {chay_lean.TRAN_VET} · sinh mã {sinh_ma.VET_TOI_DA}")


# ---------------------------------------------------------------------------
# 5. BẢN CHỤP SƠ ĐỒ cạnh kết quả — nền của «Soi trên sơ đồ»
# ---------------------------------------------------------------------------
print("\n▸ Chụp sơ đồ cạnh kết quả, rồi đọc lại được")
import tempfile  # noqa: E402

with tempfile.TemporaryDirectory() as _d:
    _doc = {"name": "Vết", "steps": [{"id": "a", "type": lam.LAM_TIN_HIEU}],
            "edges": [], "co_may": {"x": 1}}
    chay_lean._ghi_so_do(_d, _doc)
    kiem("ghi ra đúng tên file", os.path.isfile(os.path.join(_d, chay_lean.TEN_SO_DO)))
    # Hỏng thì THÔI, không được làm hỏng cả lượt chạy — sơ đồ rỗng thì khỏi ghi.
    chay_lean._ghi_so_do(_d + "-khong-co", {})
    kiem("sơ đồ rỗng thì không ghi, và không nổ", True)

_mo = chay_lean.doc_so_do_luot("khong/co/thu/muc/nao")
kiem("lượt không có thì trả `{}`, không nổ", _mo == {}, f"— {_mo}")

# ⚠ VÀ PHẢI CÓ AI GỌI NÓ. Mấy phép trên chỉ nói «hàm ghi chạy đúng» — ÉP VỠ bằng cách
# bỏ hẳn câu gọi `_ghi_so_do` trong `chay()` thì bài này vẫn XANH, tức hàng rào đứng
# cạnh một cánh cổng khác. Nên gác bằng CÁCH GỌI THẬT `chay()`: cắm một con mắt vào
# chỗ ghi, cắm một bộ giả vào chỗ chạy LEAN, rồi xem con mắt có thấy gì.
print(NL + "▸ Và `chay()` có THẬT SỰ gọi chỗ chụp ấy không")
_thay = {}
_goc = {"_ghi_so_do": chay_lean._ghi_so_do, "san_sang": chay_lean.san_sang,
        "Popen": chay_lean.subprocess.Popen}
try:
    chay_lean._ghi_so_do = lambda d, sd: _thay.update(thu_muc=d, so_do=sd)
    # LEAN không phải có thật để gác chuyện này: `chay()` chụp sơ đồ TRƯỚC khi nó
    # chạm tới LEAN, nên một bộ giả vừa đủ để đi qua `san_sang` là xong.
    import tempfile as _tf
    _goc_lean = _tf.mkdtemp()
    os.makedirs(os.path.join(_goc_lean, "Launcher"), exist_ok=True)
    io.open(os.path.join(_goc_lean, "Launcher", "config.json"),
            "w", encoding="utf-8").write("{}")
    chay_lean.san_sang = lambda: {"ok": True, "goc": _goc_lean,
                                  "launcher": os.path.join(_goc_lean, "x.exe")}

    def _popen_gia(*_a, **_k):
        raise OSError("bo gia: khong chay LEAN that")

    chay_lean.subprocess.Popen = _popen_gia
    _sd = {"name": "V", "steps": [{"id": "a"}], "edges": []}
    chay_lean.chay("# ma", "BaiKiemVet", _sd)
    kiem("`chay()` gọi chỗ chụp sơ đồ, với ĐÚNG sơ đồ nhận được",
         _thay.get("so_do") == _sd, f"— {_thay.get('so_do')}")
    kiem("và chụp vào ĐÚNG thư mục của lượt ấy",
         str(_thay.get("thu_muc", "")).endswith(os.path.join("BaiKiemVet", ""))
         or os.path.basename(os.path.dirname(_thay.get("thu_muc", ""))) == "BaiKiemVet",
         f"— {_thay.get('thu_muc')}")
finally:
    chay_lean._ghi_so_do = _goc["_ghi_so_do"]
    chay_lean.san_sang = _goc["san_sang"]
    chay_lean.subprocess.Popen = _goc["Popen"]

# `bat_dau_chay` là cửa giao diện gọi — nó phải CHUYỂN TIẾP sơ đồ xuống `chay`, chứ
# không lặng lẽ bỏ rơi tham số thứ ba.
_bat = {}
_chay_goc = chay_lean.chay
try:
    chay_lean.chay = lambda ma, lop, sd=None: (_bat.update(sd=sd),
                                               {"ok": True, "loi": ""})[1]
    chay_lean.bat_dau_chay("# ma", "BaiKiemVet2", {"steps": [{"id": "z"}]})
    import time as _time
    for _ in range(200):                  # luồng nền, chờ nó chạm tới `chay`
        if "sd" in _bat:
            break
        _time.sleep(0.01)
    kiem("`bat_dau_chay` chuyển tiếp sơ đồ xuống `chay`",
         (_bat.get("sd") or {}).get("steps") == [{"id": "z"}], f"— {_bat}")
finally:
    chay_lean.chay = _chay_goc


# ---------------------------------------------------------------------------
# 6. MỘT CỬA SOÁT cho cả hai cửa sổ
# ---------------------------------------------------------------------------
print("\n▸ Cửa sổ View soi bằng CHÍNH phép soát của cửa sổ chính")
from cat_studio import api  # noqa: E402

_st = [core.make_start_step()]
_st[0]["ma"] = [{"ma": "SPY", "loai": "equity"}]
_s1 = api._soat(_st, None, None)
_s2 = api.Api.soat(object.__new__(api.Api), _st, None, None)
kiem("`Api.soat` chỉ bọc `_soat` lại, không dựng bản thứ hai",
     _s2["ok"] and _s2["value"]["thu_tu"] == _s1["thu_tu"]
     and _s2["value"]["entry"] == _s1["entry"],
     "— hai phép đánh số thì «Soi trên sơ đồ» sáng lên một khối khác")
kiem("và `_soat` trả đủ thứ `doDuong` cần",
     all(k in _s1 for k in ("thu_tu", "entry", "the", "edges")),
     f"— {sorted(_s1)}")

# ⚠ VÀ CỬA `chay_backtest` PHẢI ĐƯA SƠ ĐỒ XUỐNG. Ép vỡ bằng cách bỏ tham số thứ ba ở
# đúng cú gọi ấy thì mọi phép trên vẫn XANH — `chay_lean` nhận `so_do=None` và lặng lẽ
# không chụp gì, nên «Soi trên sơ đồ» của mọi lượt chạy mới rơi về lối dò ngược.
print(NL + "▸ Cửa `chay_backtest` đưa sơ đồ ĐÃ ÁP MÀN xuống bộ chạy")
_bat2 = {}
_bd_goc = chay_lean.bat_dau_chay
try:
    chay_lean.bat_dau_chay = lambda ma, lop, sd=None: (_bat2.update(sd=sd),
                                                       {"ok": True, "loi": ""})[1]
    _st2 = [core.make_start_step(), core.make_lam_step(lam.LAM_DAT_TY_TRONG)]
    _st2[0]["ma"] = [{"ma": "SPY", "loai": "equity"}]
    _st2[1]["ty_trong"] = 0.3
    for _i, _x in enumerate(_st2):
        _x["pos"] = [-220 + _i * 380, 0]
    _ed2 = [{"from": _st2[0]["id"], "to": _st2[1]["id"], "port": "out"}]
    api.Api.chay_backtest(object.__new__(api.Api), "Vet", _st2, _ed2)
    _sd2 = _bat2.get("sd") or {}
    kiem("sơ đồ đi xuống, và nó mang đủ khối lẫn dây",
         len(_sd2.get("steps") or []) == 2 and len(_sd2.get("edges") or []) == 1,
         f"— {sorted(_sd2)} · {len(_sd2.get('steps') or [])} khối")
finally:
    chay_lean.bat_dau_chay = _bd_goc

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
