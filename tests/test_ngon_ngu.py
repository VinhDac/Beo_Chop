"""SONG NGỮ — mặc định tiếng Anh, bật lại tiếng Việt được, và KHÔNG SÓT CHỮ NÀO.

Cái hỏng mà bài này gác là cái hỏng LẶNG NHẤT của việc dịch: thêm một câu vào giao
diện rồi quên dịch. App vẫn chạy, build vẫn sạch, `tsc` vẫn sạch — chỉ có bản tiếng
Anh hiện một câu tiếng Việt, ở đúng cái màn ít người mở nhất. Không có cổng thì thứ
duy nhất bắt được nó là mắt của một người đọc được cả hai tiếng.

Năm việc:
  1. `core.ngon_ngu`: mặc định "en", "vi" khi chọn, giá trị lạ (gõ tay vào
     `cai_dat.json`, file của bản cũ) rơi về "en" chứ không làm giao diện hỏng.
  2. Ô chọn ngôn ngữ do PYTHON KHAI như mọi cài đặt khác (`cai_dat.NHOM`) và SỐNG SÓT
     qua một vòng ghi–đọc. Nhãn của nó ghi CẢ HAI TIẾNG và KHÔNG đi qua bộ dịch: ai
     lỡ chọn tiếng mình không đọc được vẫn phải tìm ra đường về.
  3. `khoi_dong` — cửa cả BA cửa sổ gọi trước khi vẽ khung hình đầu — có mang ngôn ngữ.
  4. Python đổi tiếng là mặt khối và bảng Vấn đề đổi theo, NGAY, không đợi mở lại app.
  5. CỔNG: `tools/dich_python.py --chi-soat` — chạy cả hai nửa (web rồi Python), đúng
     lối `npm run build` và `tools\\dich.bat` dùng. Thiếu một câu là bài này đỏ.

⚠ Bài này KHÔNG chốt tiếng Việt như tám bài kia — nó đi qua CẢ HAI tiếng, nên nó phải
tự đặt tiếng trước mỗi phép kiểm và trả về mặc định khi xong.

Ghi vào THƯ MỤC TẠM, không đụng `cai_dat.json` thật.

Chạy:  python tests\\test_ngon_ngu.py
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import cai_dat, core, hoi, lam, luu_tru, ngon_ngu  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# --------------------------------------------------------------- 1. đọc cài đặt
print("\n▸ core.ngon_ngu — APP CHỈ NÓI TIẾNG ANH, và không ngả nào về được tiếng Việt")
# ⚠ BỎ CHẾ ĐỘ TIẾNG VIỆT KHỎI APP — chốt 22/10/2026. Bài này trước đây đi khẳng định
# điều NGƯỢC LẠI («chọn tiếng Việt» phải ra "vi"), nên nó không còn là lưới nữa mà là
# bản ghi của một thiết kế đã bỏ. Nay nó canh đúng cái người dùng đòi: không đường nào
# — cài đặt cũ, file gõ tay, giá trị lạ — đưa app về tiếng Việt được.
kiem("mặc định là TIẾNG ANH", core.ngon_ngu({}) == "en")
kiem("cài đặt cũ còn ghi «vi» thì VẪN ra tiếng Anh",
     core.ngon_ngu({"ngon_ngu": "vi"}) == "en",
     "— bỏ mỗi ô chọn mà để nấc «vi» ở lại là chế độ ấy vẫn sống")
kiem("giá trị lạ cũng thế",
     core.ngon_ngu({"ngon_ngu": "fr"}) == "en" and core.ngon_ngu({"ngon_ngu": None}) == "en")
# Mặc định KHÔNG được gõ tay lần thứ hai: `cai_dat.NGON_NGU` khai, mọi nơi đọc nó.
kiem("mặc định lấy từ `cai_dat.NGON_NGU`, không gõ lại",
     core.ngon_ngu({}) == cai_dat.NGON_NGU[0][0])
kiem("và bảng ấy chỉ còn MỘT nấc", len(cai_dat.NGON_NGU) == 1,
     f"— {cai_dat.NGON_NGU}")
ngon_ngu.dat("fr")
kiem("`ngon_ngu.dat` cũng rơi về mặc định khi nhận giá trị lạ", ngon_ngu.hien() == "en")

# --------------------------------------------- 2. không còn ô chọn tiếng ở Cài đặt
print("\n▸ Hộp Cài đặt KHÔNG còn ô chọn tiếng")
# Một ô chọn có đúng một nấc thì vừa vô dụng vừa hứa hão: người dùng cứ mở Cài đặt ra
# tìm tiếng của mình mãi. Bỏ cả nhóm, không bỏ mỗi nấc.
kiem("từ điển Cài đặt không còn ô ngôn ngữ",
     cai_dat.BANG_O.get(cai_dat.KHOA_NGON_NGU) is None)
kiem("và không nhóm nào còn ô ấy",
     not [o for _m, _n, ds in cai_dat.NHOM for o in ds
          if o["ten"] == cai_dat.KHOA_NGON_NGU])

# ⚠ NHƯNG CÔNG TẮC `vi` PHẢI CÒN SỐNG TRONG `ngon_ngu.dat`, và đó là cố ý. Mục 5 dưới
# đây dựng CÙNG một sơ đồ ở hai tiếng rồi so: chỗ nào hai bản giống hệt mà có dấu thì
# đó là nhãn app chưa ai dịch. Lưới ấy đã tìm ra CHÍN chỗ sót, và nó là thứ duy nhất
# canh được chuyện chữ Việt lọt vào bản tiếng Anh. Giết công tắc là giết lưới.
ngon_ngu.dat("vi")
kiem("công tắc `vi` còn sống cho BÀI KIỂM (app không gọi tới)",
     ngon_ngu.hien() == "vi",
     "— mất nó là mất lưới dò chữ Việt lọt vào bản tiếng Anh")
ngon_ngu.dat("en")

# ------------------------------------------- 3. ba cửa sổ biết tiếng trước khung đầu
print("\n▸ `khoi_dong` — cửa cả ba cửa sổ gọi TRƯỚC khi vẽ, phải mang ngôn ngữ")
tam = tempfile.mkdtemp(prefix="cat-ngon-ngu-")
goc_cu = luu_tru.thu_muc_app
luu_tru.thu_muc_app = lambda: tam
try:
    from cat_studio import api  # noqa: E402
    # Ghi THẲNG "vi" vào file như một bản cài đặt cũ còn sót — và nó vẫn phải ra
    # tiếng Anh ở cả ba cửa sổ.
    s = luu_tru.doc_cai_dat()
    s[cai_dat.KHOA_NGON_NGU] = "vi"
    luu_tru.ghi_cai_dat(s)
    for ten, ap in (("cửa sổ sơ đồ", api.Api()),
                    ("cửa sổ Kết quả", api.ApiKetQua("x")),
                    ("cửa sổ Optimize", api.ApiToiUu("x"))):
        r = ap.khoi_dong()
        kiem(ten, r.get("ok") and (r.get("value") or {}).get("ngon_ngu") == "en",
             str(r.get("error", ""))[:80])
    # Dựng `Api` là chốt ngôn ngữ theo cài đặt — đường chính, không phải lưới an toàn.
    kiem("dựng `Api` thì Python chốt theo cài đặt luôn", ngon_ngu.hien() == "en")
    # Và lưu cài đặt mới là Python đổi NGAY, không đợi mở lại app.
    a = api.Api()
    gt = dict(cai_dat.doc(luu_tru.doc_cai_dat()))
    gt[cai_dat.KHOA_NGON_NGU] = "vi"
    r = a.cai_dat_ghi(gt)
    kiem("lưu Cài đặt mang «vi» cũng KHÔNG đổi được tiếng",
         r.get("ok") and ngon_ngu.hien() == "en", str(r.get("error", ""))[:80])
finally:
    luu_tru.thu_muc_app = goc_cu
    shutil.rmtree(tam, ignore_errors=True)

# ----------------------------------- 4. chữ Python dựng phải ĐỔI THEO, không đứng im
print("\n▸ Chữ do Python dựng — mặt khối và bảng Vấn đề đổi theo tiếng")
# ⚠ Loại khối lấy từ HẰNG của từ điển, không gõ lại chuỗi: gõ lại thì một ngày đổi
# tên loại là bài này lặng lẽ đi qua nhánh «khối lạ» và chẳng kiểm được gì nữa.
BUOC = [{"id": "s1", "kind": "start", "nhip": "ngay"},
        {"id": "a1", "kind": "action", "type": lam.LAM_DAT_TY_TRONG, "ty_trong": 0.3},
        {"id": "h1", "kind": "action", "type": hoi.HOI_THI_TRUONG, "dieu_kien": []}]


def theo_tieng(tieng, lay):
    """`lay()` chạy ở tiếng `tieng`. Trả kết quả."""
    ngon_ngu.dat(tieng)
    return lay()


def mat_khoi(b):
    t = core.the_buoc(b)
    return [t["title"], *t["badges"], *[d["text"] for d in t["lines"]]]


def huy_hieu(b):
    return core.the_buoc(b)["badges"]


def van_de():
    return [v["message"] for v in core.validate_flow_graph(BUOC[:2], []) or []]


kiem("mặt khối đổi theo tiếng",
     theo_tieng("vi", lambda: mat_khoi(BUOC[1])) != theo_tieng("en", lambda: mat_khoi(BUOC[1])),
     f"— {theo_tieng('en', lambda: mat_khoi(BUOC[1]))}")
# HUY HIỆU là chỗ dễ sót nhất: nó lấy NGUYÊN nhãn từ điển, nên bọc `tr` phải làm ở chỗ
# IN RA, mà bộ công cụ không với tới được — nó chỉ thấy một BIẾN. Đã sót thật một lượt:
# bản tiếng Anh có mặt khối nói «Mỗi nến ngày» và «Hỏi thị trường».
for _ten, _b in (("nhịp của khối Bắt đầu", BUOC[0]), ("họ của khối Hỏi", BUOC[2]),
                 ("loại việc của khối Hành động", BUOC[1])):
    _vi = theo_tieng("vi", lambda: huy_hieu(_b))
    _en = theo_tieng("en", lambda: huy_hieu(_b))
    kiem(f"huy hiệu «{_ten}» cũng đổi", bool(_vi) and _vi != _en, f"— {_vi} → {_en}")
vi_vd = theo_tieng("vi", van_de)
en_vd = theo_tieng("en", van_de)
kiem("bảng Vấn đề đổi theo tiếng", bool(vi_vd) and vi_vd != en_vd)
# DẤU NGHÌN: "100.000" người Anh đọc là một trăm phẩy không — sai một nghìn lần, mà
# không có gì trông như lỗi. Bảng dịch không với tới được chỗ này: nó dịch CÂU, không SỐ.
ngon_ngu.dat("vi")
kiem("dấu nghìn tiếng Việt là dấu CHẤM", core._tien(100000) == "100.000")
ngon_ngu.dat("en")
kiem("dấu nghìn tiếng Anh là dấu PHẨY", core._tien(100000) == "100,000")
# Câu chưa có bản dịch thì `tr` ghi lại vào `ngon_ngu.thieu` — lưới cuối, bắt cả câu
# mà cổng tĩnh không thấy (câu dựng từ một biến).
ngon_ngu.thieu.clear()
for b in BUOC:
    core.the_buoc(b)
core.validate_flow_graph(BUOC, [])
kiem("chạy hết một lượt mà không câu nào thiếu bản dịch",
     not ngon_ngu.thieu, f"— {sorted(ngon_ngu.thieu)[:3]}")
ngon_ngu.dat(cai_dat.NGON_NGU[0][0])

# ------------------------------- 4b. LƯỚI THỨ HAI: nhãn đi qua một BIẾN
print("\n▸ Nhãn đi qua một BIẾN — chỗ cổng tĩnh KHÔNG thấy nổi")
# ⚠ VÌ SAO CẦN LƯỚI NÀY. Cổng chỉ thấy chuỗi VIẾT THẲNG trong mã. Nhãn lấy ra từ từ
# điển rồi ghép vào câu — `dl["nhan"]`, `o["nhan"]`, `ten_loai[...]` — thì nó chỉ thấy
# một BIẾN, nên thiếu `tr` ở đấy là cổng vẫn xanh mà thẻ khối nói tiếng Việt giữa bản
# tiếng Anh. Đã sót thật CHÍN chỗ, và chỉ lưới này tìm ra.
#
# Cách nhận ra chữ của APP giữa chữ của NGƯỜI DÙNG: dựng CÙNG một sơ đồ ở hai tiếng
# rồi so. Tên Strategy, tên khối, tên ô nhớ, mã chứng khoán giống nhau ở cả hai bản —
# nhưng chúng không có dấu tiếng Việt do app sinh ra. Chỗ nào hai bản GIỐNG HỆT mà
# CÓ DẤU thì đó là nhãn của app chưa ai dịch.
import re  # noqa: E402

DAU = re.compile("[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]",
                 re.I)
# Mỗi khối dưới đây đóng MỘT lối nhãn-qua-biến đã từng sót:
#   rổ có ô con   -> nhãn ô con  ·  một mã  -> nhãn loại tài sản
#   điều kiện     -> nhãn đại lượng          ·  cỗ máy -> nhãn ô và nấc đang chọn
SOI = [
    {"id": "r1", "kind": "start", "ma": {"ro": "gtgd", "giu_n": 10},
     "khoang": {"tu": "2014-03-25", "den": "2014-04-07"}, "von": 100000, "nhip": "ngay"},
    {"id": "r2", "kind": "start", "ma": [{"ma": "XAUUSD", "loai": "cfd"}],
     "khoang": {"tu": "2019-01-01", "den": "2020-01-01"}, "von": 100000, "nhip": "ngay"},
    {"id": "h2", "kind": "action", "type": hoi.HOI_THI_TRUONG, "dieu_kien": [
        {"trai": {"ma_dl": "gia"}, "phep": "<",
         "phai": {"ma_dl": "sma", "tham_so": {"n": 200}}}]},
]
SOI_MAY = {"chia_von": "InsightWeightingPortfolioConstructionModel",
           "dat_lenh": "ImmediateExecutionModel", "san": "InteractiveBrokersBrokerageModel"}


def chu_app(tieng):
    """Mọi chữ APP DỰNG cho `SOI` ở tiếng `tieng` — mặt khối và thẻ cỗ máy."""
    ngon_ngu.dat(tieng)
    ra = []
    for b in SOI:
        t = core.the_buoc(b)
        ra += list(t["badges"]) + [d["text"] for d in t["lines"]]
    ra += list(core.tom_tat_co_may(SOI_MAY) or [])
    return ra


_vi, _en = chu_app("vi"), chu_app("en")
_sot = sorted({b for a, b in zip(_vi, _en) if a == b and DAU.search(b)})
kiem("không nhãn nào còn nguyên tiếng Việt ở bản tiếng Anh", not _sot, f"— {_sot[:3]}")
# Và quét luôn mấy Strategy THẬT trên máy này nếu có — chúng dùng tới những lối mà
# một bộ mẫu viết tay không nghĩ ra hết. `du_lieu/` không nằm trong kho nên máy nào
# chưa có thì bỏ qua, không phải đỏ oan.
_kho = os.path.join(GOC, "du_lieu", "strategy")
_tep = sorted(f for f in os.listdir(_kho) if f.endswith(".json")) \
    if os.path.isdir(_kho) else []
if _tep:
    import json  # noqa: E402
    _sot2 = {}
    for _t in _tep:
        _d = json.load(io.open(os.path.join(_kho, _t), encoding="utf-8"))
        _s, _e = _d.get("steps") or [], _d.get("edges") or []

        def _chu():
            ra = []
            for b in _s:
                t = core.the_buoc(b)
                ra += list(t["badges"]) + [d["text"] for d in t["lines"]]
            ra += [v["message"] for v in core.validate_flow_graph(_s, _e) or []]
            return ra
        ngon_ngu.dat("vi")
        _a = _chu()
        ngon_ngu.dat("en")
        _b = _chu()
        for _x, _y in zip(_a, _b):
            if _x == _y and DAU.search(_y or ""):
                _sot2[_y.strip()] = _t
    kiem(f"…kể cả {len(_tep)} Strategy thật trên máy này", not _sot2,
         f"— {list(_sot2)[:3]}")
else:
    print("  · bỏ qua phần quét Strategy thật — máy này chưa có du_lieu/strategy")
ngon_ngu.dat(cai_dat.NGON_NGU[0][0])

# ------------------------------ 4b. TÊN KHỐI — chỗ lưới trên KHÔNG BAO GIỜ thấy
print("\n▸ TÊN khối vừa tạo — chữ GÕ CỨNG, lưới so hai bản không thấy nổi")
# ⚠ ĐÂY LÀ LỖ ĐEN CỦA CHÍNH LƯỚI NGAY TRÊN. Lưới ấy dựng cùng một sơ đồ ở hai tiếng rồi
# bắt chỗ nào GIỐNG HỆT mà có dấu. Nhưng một chuỗi GÕ CỨNG thì giống hệt nhau ở cả hai
# bản đúng theo định nghĩa — nên lưới tưởng đó là chữ của NGƯỜI DÙNG và bỏ qua.
#
# Đã dính thật, và dính ở BỐN trong năm xưởng đẻ khối: `make_start_step` gõ "Bắt đầu",
# `make_group_step` gõ "Nhóm mới", còn `make_hoi_step` với `make_lam_step` lấy thẳng
# `d["nhan"]` của từ điển. Tên khối được GHI VÀO TÀI LIỆU rồi bày lại nguyên xi
# (`step_title`), nên mọi khối người dùng thả ra đều mang tên tiếng Việt giữa một app
# chỉ nói tiếng Anh. Chỉ ảnh chụp mới thấy. `make_quay_ve_step` vốn làm đúng từ đầu.
ngon_ngu.dat("en")
_xuong = [("start", core.make_start_step), ("group", core.make_group_step),
          ("quay_ve", core.make_quay_ve_step)]
_xuong += [(f"hoi:{_l}", (lambda _l=_l: core.make_hoi_step(_l))) for _l in hoi.LOAI_HOI]
_xuong += [(f"lam:{_l}", (lambda _l=_l: core.make_lam_step(_l))) for _l in lam.LOAI_LAM]
_ten_khoi = {}
for _ten, _tao in _xuong:
    _t = core.the_buoc(_tao())["title"]
    if DAU.search(_t or ""):
        _ten_khoi[_ten] = _t
kiem(f"cả {len(_xuong)} xưởng đẻ khối đặt tên bằng TIẾNG ANH", not _ten_khoi,
     f"— {list(_ten_khoi.items())[:3]}")
ngon_ngu.dat(cai_dat.NGON_NGU[0][0])

# ------------------------------------------------------------------- 5. CỔNG
print("\n▸ CỔNG song ngữ — cả hai nửa, đúng lối `npm run build` và `tools\\dich.bat` dùng")
# Gọi CHÍNH công cụ, không viết lại phép soát ở đây: hai bộ luật thì sớm muộn lệch
# nhau, và cái lệch ấy làm cổng xanh oan.
p = subprocess.run([sys.executable, os.path.join(GOC, "tools", "dich_python.py"),
                    "--chi-soat"], capture_output=True, text=True,
                   encoding="utf-8", errors="replace", cwd=GOC,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8"})
kiem("không sót chữ chưa bọc, không thiếu câu nào, ô điền khớp, hai bảng không lệch",
     p.returncode == 0, "\n" + ((p.stdout or "") + (p.stderr or "")).strip()[-1200:])

print(f"\n{'─' * 60}\n  {dung} đúng · {sai} sai\n{'─' * 60}")
sys.exit(1 if sai else 0)
