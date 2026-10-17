"""BIẾN CSS MA — `var(--khong-ton-tai)` hỏng LẶNG, và nó vừa hỏng thật hai lần.

VÌ SAO BÀI NÀY PHẢI CÓ
----------------------
CSS không có lỗi biên dịch. Viết `background: var(--panel)` mà `--panel` không tồn tại
thì trình duyệt coi như KHÔNG ĐẶT thuộc tính đó — nền thành trong suốt, chữ phía sau
xuyên thẳng qua. Không lỗi, không cảnh báo, `tsc` sạch, `vite build` sạch. Chỉ có nhìn
vào mới thấy sai, mà nhìn thì phải mở đúng cái menu đó ra.

Hai ca có thật, tìm ra bằng mắt chứ không bằng máy:
  · `--panel`  — nền menu ⚙ trong suốt, chữ dưới xuyên qua;
  · `--line`   — viền nét đứt rơi về `currentColor`, đậm hơn hẳn ý định.

Ngoại lệ HỢP LỆ: biến do JS đặt lúc chạy (`style={{ '--mau-khoi': … }}`). Chúng không có
trong `theme.css` và không thể có — nên khai ra ở đây, có tên có tuổi, thay vì nới lỏng
phép kiểm.

Chạy:  python tests\\test_giao_dien.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(GOC, "webui", "src")

#: Biến do JS đặt trên chính phần tử lúc chạy, không khai trong stylesheet — nên không
#: có cách nào tìm thấy chúng ở `theme.css`, và cũng KHÔNG NÊN có.
#:
#:   --mau   màu người dùng tự đặt cho một khối; `StepNode` gắn thẳng lên thẻ. Bộ chạy
#:           không đọc — nó chỉ để phân loại bằng mắt trên một sơ đồ dài.
DAT_LUC_CHAY = {"--mau"}

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def doc(ten):
    with io.open(os.path.join(CSS, ten), encoding="utf-8") as f:
        return f.read()


def bo_chu_thich(s):
    """Bỏ `/* … */` — chú thích NÓI VỀ một biến ma không phải là dùng nó."""
    return re.sub(r"/\*.*?\*/", " ", s, flags=re.S)


print("\n▸ Mọi `var(--x)` phải có một `--x:` ở đâu đó")
theme, app = doc("theme.css"), doc("app.css")
khai = set(re.findall(r"(--[a-z0-9-]+)\s*:", bo_chu_thich(theme + app)))
dung_bien = set(re.findall(r"var\((--[a-z0-9-]+)", bo_chu_thich(app + theme)))
ma = sorted(dung_bien - khai - DAT_LUC_CHAY)
kiem("không còn biến ma nào", not ma, f"— {ma}" if ma else f"({len(dung_bien)} biến)")

# Chốt riêng cho hai ca đã hỏng thật: chúng phải KHÔNG quay lại.
for ten in ("--panel", "--line"):
    kiem(f"`{ten}` (từng hỏng lặng) không còn được dùng",
         ten not in dung_bien)

print("\n▸ Menu ⚙ phải có nền ĐẶC  (ngủ từ D-12 — chưa có menu nổi nào)")
# Menu nổi trên hộp thoại mà nền trong suốt thì vô dụng — canh thẳng thuộc tính đó.
kh = re.search(r"\.menu-th-noi\s*\{(.*?)\}", app, flags=re.S)
if kh is None:
    print("  · chưa có `.menu-th-noi` — bỏ qua")
else:
    than = kh.group(1)
    m = re.search(r"background:\s*var\((--[a-z0-9-]+)\)", than)
    kiem("nền lấy từ một biến CÓ KHAI",
         m is not None and m.group(1) in khai,
         f"— {m.group(1) if m else 'không có background'}")
    kiem("có đổ bóng — menu phải NỔI LÊN, không dán phẳng vào nền",
         "box-shadow" in than)
    kiem("có z-index — hàng dưới không được vẽ đè lên",
         "z-index" in than)

# Toán hạng VẾ PHẢI: bánh răng của nó nằm sát mép phải hộp thoại (787→813 trong vùng nội
# dung 0→850), nên menu 240px mở sang phải là chạy tới 1027 — tràn 177px. Và nó bị CẮT
# thật chứ không chỉ thò ra, vì `.ht-than` có `overflow: auto` nên là một khung cắt.
if kh is not None:
    kh2 = re.search(r"\.ve-phai \.menu-th-noi\s*\{([^}]*)\}", bo_chu_thich(app))
    kiem("menu ⚙ của vế PHẢI lật sang trái",
         kh2 is not None and "right: 0" in kh2.group(1) and "left: auto" in kh2.group(1),
         "" if kh2 else "— không có luật lật nào")
    kh3 = re.search(r"\.ve-phai \.menu-th-noi::before\s*\{([^}]*)\}", bo_chu_thich(app))
    kiem("mũi tên cũng lật theo, không thì nó trỏ vào chỗ trống",
         kh3 is not None and "right:" in kh3.group(1))

print("\n▸ Ô lưới không được tự đặt bề rộng RIÊNG  (ngủ từ D-12 — chưa có hàng lưới nào)")
# ⚠ Bẫy có thật: `.o.phep { width: 128px }` — rác từ hồi hàng điều kiện dựng bằng flex.
# Khi hàng chuyển sang LƯỚI, cột phép rộng 88px, nên ô 128px tràn 40px sang cột vế phải
# và ĐÈ LÊN nó. Không lỗi, không cảnh báo. Mà phép đo canh cột cũng không bắt được, vì
# nó so MÉP TRÁI — mép trái vẫn thẳng tăm tắp, chỉ phần đuôi thò sang ô bên cạnh.
luoi = re.search(r"\.dong-dk\s*\{(.*?)\}", bo_chu_thich(app), flags=re.S)
if luoi is None:
    print("  · chưa có `.dong-dk` — bỏ qua")
else:
    kiem("`.dong-dk` là một LƯỚI có cột cố định",
         "grid-template-columns" in luoi.group(1))
for lop in (r"\.o\.phep", r"\.o\.nho\.don-vi"):
    kh = re.search(lop + r"\s*\{([^}]*)\}", bo_chu_thich(app))
    if kh is None:
        continue
    px = re.search(r"width:\s*(\d+)px", kh.group(1))
    kiem(f"`{lop.replace(chr(92), '')}` không tự đặt width bằng px — phải vừa cột của nó",
         px is None, f"— đang là {px.group(0)}" if px else "")

print("\n▸ Lệnh @media `hien-tu-*` phải có THẬT — lớp ma cũng hỏng LẶNG")
# `<Nhom hienTu={1250}>` sinh ra lớp `hien-tu-1250`, và lớp ấy chỉ ẩn được nhóm nếu CSS
# có một @media tương ứng. Thiếu thì KHÔNG LỖI, không cảnh báo, `tsc` sạch, build sạch —
# nhóm cứ nằm đó, ribbon tràn ngang và nhãn các nút đè lên nhau ở cửa sổ hẹp.
#
# ⚠ ĐÃ HỎNG THẬT: `hien-tu-1090` và `hien-tu-1250` nằm trong `Ribbon.tsx` ngay từ đầu
# mà `app.css` không hề có dòng nào — hai nhóm "Hoàn tác" và "Strategy" chưa bao giờ ẩn.
# @media không nhận biến CSS nên không có cách nào sinh các lớp này ra: chúng là một
# bảng tra viết tay, mà bảng tra viết tay thì phải có người canh.
tsx = ""
for goc, _thu_muc, tep in os.walk(CSS):
    for f in tep:
        if f.endswith((".tsx", ".ts")):
            with io.open(os.path.join(goc, f), encoding="utf-8") as fh:
                tsx += fh.read()
kiem("Ribbon vẫn sinh lớp theo mẫu `hien-tu-${hienTu}`", "hien-tu-${hienTu}" in tsx)
# Đọc BẢNG NGƯỠNG của Ribbon, không quét cả file: `hienTu={i === 0 ? undefined : 1460}`
# thì một phép quét sẽ vừa bỏ sót 1460 vừa nhặt lấy số 0.
bang = re.search(r"const HIEN_TU = \{([^}]*)\}", tsx)
kiem("ngưỡng ẩn nhóm nằm trong MỘT bảng ở Ribbon.tsx", bang is not None)
so_dung = set(re.findall(r":\s*(\d+)", bang.group(1) if bang else ""))
so_khai = set(re.findall(r"\.hien-tu-(\d+)\s*\{", bo_chu_thich(app)))
thieu = sorted(so_dung - so_khai, key=int)
kiem("mọi số `hienTu` đều có @media đi kèm", not thieu,
     f"— thiếu {thieu}" if thieu else f"({sorted(so_dung, key=int)})")
thua = sorted(so_khai - so_dung, key=int)
kiem("không có @media nào bỏ không", not thua, f"— dư {thua}" if thua else "")
# Và ngưỡng phải là SỐ ĐÓ TRỪ 1: `max-width: 1250px` thì đúng ở 1250 nhóm vẫn ẩn, trong
# khi `hienTu={1250}` nghĩa là "hiện TỪ 1250".
for n in sorted(so_khai, key=int):
    kh = re.search(r"@media \(max-width: (\d+)px\) \{ \.hien-tu-" + n + r"\b", app)
    kiem(f"`hien-tu-{n}` ẩn đến đúng {int(n) - 1}px",
         kh is not None and kh.group(1) == str(int(n) - 1),
         f"— đang là {kh.group(1)}px" if kh else "— không đúng khuôn một dòng")

print("\n▸ Cửa trong `api.ts` phải có người dùng  (hàng rào không ai đứng gác)")
# ⚠ ĐÃ HỎNG THẬT. `cho_cau_noi` — hàm chờ cầu nối pywebview — được viết ra kèm nguyên
# một đoạn chú thích giải thích cái bẫy nó canh ("pywebview tạo sẵn `api: {}` RỖNG mà
# TRUTHY"), rồi KHÔNG CHỖ NÀO GỌI. Thành ra `SoDo` hỏi Python ngay khung hình đầu tiên:
# cả ba từ điển trượt, mọi khối mất hộp sửa, bản nháp không mở lên — và suốt mấy lượt
# chạy không ai biết vì sao. `tsc` sạch: TypeScript không coi một export thừa là lỗi.
#
# Luật: cửa nào trong `api.ts` cũng phải có ít nhất một chỗ NGOÀI `api.ts` gọi tới.
# Không ai cần thì xoá đi, còn hơn để nằm đó trông như đã có người canh.


def bo_chu_thich_ts(s):
    """Bỏ `/* … */` và `// …` — nhắc tên một hàm trong chú thích KHÔNG phải là gọi nó.

    `(?<!:)` để `https://…` trong chuỗi không bị cắt mất phần sau."""
    return re.sub(r"(?<!:)//[^\n]*", " ", re.sub(r"/\*.*?\*/", " ", s, flags=re.S))


ngoai = ""
for goc, _thu_muc, tep in os.walk(CSS):
    for f in tep:
        if f.endswith((".tsx", ".ts")) and f != "api.ts":
            with io.open(os.path.join(goc, f), encoding="utf-8") as fh:
                ngoai += fh.read()
ngoai = bo_chu_thich_ts(ngoai)
cua = sorted({a or b for a, b in re.findall(
    r"export (?:async )?function (\w+)|export const (\w+)", doc("api.ts"))})
chet = [c for c in cua if not re.search(r"\b" + re.escape(c) + r"\b", ngoai)]
kiem("không cửa nào bỏ không", not chet,
     f"— {chet} khai ra mà không ai gọi" if chet else f"({len(cua)} cửa: {cua})")
# Chốt riêng cho ca đã hỏng: nó phải được gọi ở ĐÚNG chỗ khởi động, không phải đâu đó.
kiem("`cho_cau_noi` được chờ trước khi hỏi từ điển",
     re.search(r"await cho_cau_noi\(.*?\)[\s\S]{0,900}?await py\.tu_dien_hoi\(",
               bo_chu_thich_ts(doc("SoDo.tsx"))) is not None)

print("\n▸ ⭐ Bảng chọn phải bày CẢ kho — nửa còn lại của lời hứa «với tới được tất cả»")
# `test_hoi` chốt đầu Python: `tu_dien()["kho"]` chứa đủ 68 đại lượng. Chốt ấy chỉ có
# giá nếu giao diện thật sự BÀY mảng đó ra. Nối hai đầu thì không còn khe nào cho một
# đại lượng khai trong `hoi.py` mà người chơi không tìm thấy.
#
# ⚠ ĐÃ HỎNG THẬT, và hỏng LẶNG đúng kiểu: bản trước mỗi khối chỉ đọc họ của CHÍNH nó
# (`loai.nhom[*].dai_luong`), nên 33 trong 68 đại lượng không cách nào vào được một
# dòng điều kiện. Không lỗi, không cảnh báo — chúng chỉ đơn giản không có ở đó.
chon = doc("components/ChonDaiLuong.tsx")
kiem("bảng chọn đọc `td.kho`", "td.kho" in chon)
cu = [m for m in ("loai.nhom", "nhom[0].dai_luong", "dai_luong_tu")
      if m in bo_chu_thich_ts(tsx)]
kiem("không chỗ nào còn đi theo đường cũ của HỌ", not cu, f"— còn {cu}")
# Lọc CỨNG chỉ được một luật: vế phải không nhận đại lượng ĐÚNG/SAI. Lọc theo HỌ thì
# là dựng lại bức tường.
kiem("chỉ lọc theo KIỂU, không lọc theo họ",
     "d.kieu === 'co_khong'" in chon and ".ho ===" not in chon)

print("\n▸ Ô mã là ô CHỌN — không cho gõ một mã khối Bắt đầu chưa khai")
for ten in ("HopDieuKien.tsx", "HopHanhDong.tsx"):
    kiem(f"`{ten}` dùng ChonMa", "ChonMa" in doc(f"components/{ten}"))
go_tay = [t for t in ("HopDieuKien.tsx", "HopHanhDong.tsx")
          if 'className="o ma"' in doc(f"components/{t}")]
kiem("không còn ô gõ mã nào", not go_tay, f"— {go_tay}")
kiem("danh sách mã lấy từ KHỐI BẮT ĐẦU",
     "s.kind === 'start'" in doc("SoDo.tsx") and "dsMa" in doc("SoDo.tsx"),
     "— một nguồn duy nhất")

print("\n▸ Menu thanh tiêu đề — đường LUÔN CÓ, khác ribbon (ribbon ẩn bớt khi hẹp)")
# ⚠ Trước đây chỉ MỘT nhóm «Cat Studio» với bốn mục, không mục nào hiện phím tắt và
# không mục nào mờ được. Hậu quả: ở cửa sổ 1020px (sàn của app) ribbon ẩn mất nhóm
# Sửa, Hoàn tác và Strategy — lúc ấy Hoàn tác, Nhân bản, Xoá, Lưu KHÔNG còn chỗ nào
# bấm được. Jenifer_Studio có File/Edit/View/Help đúng vì lẽ ấy.
sodo = bo_chu_thich_ts(doc("SoDo.tsx"))
api_py = io.open(os.path.join(GOC, "cat_studio", "api.py"), encoding="utf-8").read()
nhom_menu = re.findall(r"\{ ten: '(\w+)', muc: \[", sodo)
kiem("có bốn nhóm menu", len(nhom_menu) == 4, f"— {nhom_menu}")
# Phím tắt hiện cạnh mục là cách DUY NHẤT người dùng học được chúng.
kiem("mục menu có hiện phím tắt", sodo.count("phim: phimCua(") >= 10,
     f"— {sodo.count('phim: phimCua(')} mục")
# Mờ mà không nói vì sao là thứ bực nhất trong một cái menu.
mo = re.findall(r"tat: [^,\n]+,\s*\n?\s*viSao:", sodo)
kiem("mục nào mờ cũng kèm lý do", len(mo) >= 6, f"— {len(mo)} mục")
kiem("có cửa mở thư mục dữ liệu", "mo_thu_muc" in sodo and "mo_thu_muc" in api_py,
     "— thả một Strategy ai gửi vào, hay chép file kết quả cho người khác")
# Jenifer có `truocKhiDong`; Cat_Studio CỐ Ý không — xem chú thích trong TitleBar.
# (bỏ chú thích trước khi tìm: chính câu GIẢI THÍCH vì sao không có nó lại nhắc tên
#  nó, và một phép kiểm bắt nhầm lời kể của mình thì đỏ mãi mà chẳng có gì sai)
tb = bo_chu_thich_ts(doc("components/TitleBar.tsx"))
kiem("không thêm prop `truocKhiDong` không ai dùng", "truocKhiDong" not in tb,
     "— app tự lưu bản nháp 1,2s/lần nên ✕ không mất gì; hỏi là nhát bấm thừa")

print("\n▸ ⚠ MỖI CỬA SỔ MỘT js_api — dùng chung là bốn lỗi cùng lúc")
# Docstring `NenCuaSo` kể ba, và cả ba đã xảy ra thật: ✕ của cửa sổ thứ hai đóng CỬA
# SỔ CHÍNH; kéo thanh tiêu đề của nó kéo nhầm cửa sổ; hai cửa sổ ghi đè vùng-cấm của
# nhau. Cái thứ tư tìm ra hôm nay, nặng nhất: `KhungTuVe` dùng chung giữ đúng MỘT
# `_proc_cu`, nên vá cửa sổ thứ hai là đè mất WndProc gốc của cửa sổ thứ nhất —
# pywebview dọn một cửa sổ hai lần và ném thẳng một hộp thoại .NET vào mặt người dùng
# («Unhandled exception … 'child_fa351807'»). Tái hiện được, và bản vá thì sạch.
api_py = io.open(os.path.join(GOC, "cat_studio", "api.py"), encoding="utf-8").read()
kiem("có lớp js_api riêng cho cửa sổ kết quả", "class ApiKetQua(NenCuaSo)" in api_py)
# ⚠ Tìm DẠNG GỌI `js_api=self,` chứ không tìm chuỗi trần: `js_api=self` còn nằm trong
# chính mấy câu chú thích KỂ VỀ lỗi này, và một phép kiểm bắt nhầm lời kể của mình
# thì nó đỏ mãi mà chẳng có gì sai.
kiem("cửa sổ mới KHÔNG dùng `js_api=self`",
     "js_api=self," not in api_py and "js_api=phu," in api_py)
kiem("mỗi cửa sổ vá KHUNG CỦA MÌNH", "phu._va_khung" in api_py)
# Bề mặt hẹp: cửa sổ kết quả chỉ đọc, không được chạm vào Strategy hay khoá QC.
# Đo BỀ MẶT THẬT bằng `dir()`, không đọc chữ trong file: docstring của lớp ấy có nhắc
# tên mấy cửa nó cố tình KHÔNG nhận, và đọc chữ thì vấp ngay vào đó.
from cat_studio import api as _api  # noqa: E402
_cua = {m for m in dir(_api.ApiKetQua) if not m.startswith("_")}
xau = sorted(_cua & {"xoa_strategy", "qc_luu_khoa", "chay_backtest", "luu_strategy",
                     "sinh_ma", "soat"})
kiem("bề mặt của nó hẹp", not xau, f"— lọt {xau}" if xau else f"({len(_cua)} cửa)")
kiem("nhưng đủ để tự lo cửa sổ của mình",
     {"cua_so_dong", "cua_so_thu_nho", "keo_cua_so", "vung_khong_keo"} <= _cua)
# Trang kết quả KHÔNG được đổi tiêu đề: `_va_khung` tìm cửa sổ THEO TIÊU ĐỀ trong
# bốn giây, đổi ngay lúc ấy là nó tìm hụt và cửa sổ mở ra không kéo được.
kiem("trang kết quả không gọi `set_title`",
     "set_title" not in bo_chu_thich_ts(doc("TrangKetQua.tsx")))

print("\n▸ Cửa sổ kết quả riêng: MỘT bundle, hai vai — không dựng trang thứ hai")
# Mỗi lượt backtest mở ra một cửa sổ thật để xếp cạnh nhau mà so. Cửa sổ ấy nạp
# CHÍNH trang này với `?kq=<mã lượt>`. Dựng một trang HTML thứ hai thì sớm muộn một
# bên có thứ bên kia không, và cái lệch ấy chỉ lộ ra ở màn ít người mở nhất.
mt = bo_chu_thich_ts(doc("main.tsx"))
kiem("`main.tsx` chọn vai theo `?kq=`",
     "URLSearchParams" in mt and "'kq'" in mt and "TrangKetQua" in mt)
import glob as _glob  # noqa: E402
html = [os.path.basename(p) for p in _glob.glob(os.path.join(GOC, "webui", "*.html"))]
kiem("chỉ có MỘT trang html", html == ["index.html"], f"— {html}")
# Ruột màn Kết quả phải DÙNG CHUNG cho hộp thoại và cửa sổ riêng.
kq = doc("components/HopKetQua.tsx")
kiem("ruột tách ra dùng chung", "export function RuotKetQua" in kq)
kiem("và cả hai vỏ đều gọi nó",
     kq.count("<RuotKetQua") == 1 and "RuotKetQua" in doc("TrangKetQua.tsx"),
     "— hai bản chép tay thì sớm muộn một bên có tab mà bên kia không")
kiem("trang đứng riêng tự vẽ thanh tiêu đề", "TitleBar" in doc("TrangKetQua.tsx"),
     "— cửa sổ frameless như cửa sổ chính")

print("\n▸ Hộp Bắt đầu KHÔNG được khai lại thứ Python đã khai")
bd = bo_chu_thich_ts(doc("components/HopBatDau.tsx"))
# ⚠ ĐÃ HỎNG THẬT, ba cái một lúc. Hộp thoại dựng lại object cho mấy ô THÊM của nhịp:
#   kieu: 'so' đóng cứng  -> «Độ phân giải dữ liệu» (ô CHỌN năm mức) hiện ra như ô gõ
#   chon: []              -> năm lựa chọn bị vứt
#   goi_y tự chế từ `o.nho_nhat`/`o.lon_nhat` — hai khoá KHÔNG HỀ CÓ trong từ điển
#                         -> in ra đúng chữ "Từ undefined đến undefined", đè mất câu
#                            gợi ý thật. Không lỗi, không cảnh báo, build sạch.
kiem("không còn đọc khoá `nho_nhat` (từ điển không có khoá ấy)", "nho_nhat" not in bd)
kiem("không còn đóng cứng `kieu: 'so'`", "kieu: 'so'" not in bd)
kiem("ô thêm của nhịp đưa thẳng `o` của Python vào",
     re.search(r"o_them[\s\S]{0,200}<Hang[^>]*o=\{o\b", bd) is not None)
# Dòng khai LEAN tồn tại ĐÚNG ĐỂ kiểm lời hứa — nó nói sai thì tệ hơn không có nó.
kiem("dòng khai LEAN đọc độ phân giải NGƯỜI DÙNG chọn", "gt.do_phan_giai" in bd,
     "— không phải cột `res` của nhịp, thứ còn sót lại từ trước D-15")
kiem("Mốc so sánh là ô CHỌN", re.search(r"moc_so_sanh[\s\S]{0,400}<select", bd) is not None)
kiem("mã không có dữ liệu miễn phí thì NÓI ra", "ma-khong-co" in bd,
     "— nói, chứ không chặn: ai có dữ liệu riêng vẫn chạy được")

print("\n▸ Ribbon: ẩn một nhóm KHÔNG được lấy mất việc gì  (luật của Jenifer_Studio)")
rib = doc("components/Ribbon.tsx")
# 13 nút «thêm khối» rải thành ba nhóm nay gộp thành hai nút THỂ LOẠI có menu xổ.
# Mỗi loại một nút riêng là lối cũ — và lời biện hộ của nó («chọn loại quyết luôn hộp
# thoại bày ra cái gì») đã hết hiệu lực từ khi 68 đại lượng về chung một kho.
kiem("Xác nhận và Hành động là nút có menu, không phải năm với tám nút",
     rib.count("<NutMenu") >= 2 and "v.loaiHoi.map" in rib and "v.loaiLam.map" in rib)
kiem("mục tắt vẫn hiện kèm LÝ DO", "tat: l.tat" in rib,
     "— giấu đi thì người chơi tưởng tính năng không tồn tại")
kiem("mỗi hành động bày hàm LEAN nó gọi", "phu: l.lean" in rib)
# THỨ TỰ ẨN đi theo "còn đường nào khác không". Hạt nhân từ khi mất Ctrl+G thì chỉ
# còn ribbon và menu chuột phải, nên nó phải là nhóm ẩn SAU CÙNG — tức ngưỡng NHỎ NHẤT.
bang = re.search(r"const HIEN_TU = \{([^}]*)\}", rib)
nguong = dict((k, int(v)) for k, v in
              re.findall(r"(\w+):\s*(\d+)", bang.group(1) if bang else ""))
kiem("có đủ bốn ngưỡng", len(nguong) == 4, f"— {nguong}")
kiem("Hạt nhân ẩn SAU CÙNG — nó không còn cụm phím nào",
     bool(nguong) and nguong.get("hatNhan") == min(nguong.values()),
     f"— {nguong}")
kiem("Hoàn tác ẩn TRƯỚC TIÊN — Ctrl+Z vẫn còn đó",
     bool(nguong) and nguong.get("hoanTac") == max(nguong.values()))
# SÀN: nhóm luôn hiện phải lọt vào cửa sổ hẹp nhất app cho phép.
aw = io.open(os.path.join(GOC, "app_web.py"), encoding="utf-8").read()
mi = re.search(r"min_size=\((\d+),", aw)
kiem("ngưỡng nhỏ nhất vẫn dưới sàn cửa sổ",
     mi is not None and bool(nguong) and min(nguong.values()) <= int(mi.group(1)),
     f"— sàn {mi.group(1) if mi else '?'}px, ngưỡng nhỏ nhất "
     f"{min(nguong.values()) if nguong else '?'}")

print("\n▸ Ctrl+G là của NHÓM, không phải của Hạt nhân  (như Jenifer_Studio)")
pt = doc("phim_tat.ts")
for ma, cum in (("gom-nhom", "ctrl+g"), ("ra-nhom", "ctrl+shift+g")):
    kiem(f"`{ma}` giữ {cum}",
         re.search(r"ma: '" + ma + r"'[^}]*phim: \['" + re.escape(cum) + r"'\]", pt)
         is not None)
# Hạt nhân chỉ là CÁCH NHÌN; cụm phím quen tay phải thuộc về việc đổi sơ đồ thật.
for ma in ("gom-hat-nhan", "ta-hat-nhan"):
    kiem(f"`{ma}` không giữ cụm nào",
         re.search(r"ma: '" + ma + r"'[^}]*phim: \[\]", pt) is not None)
sodo = bo_chu_thich_ts(doc("SoDo.tsx"))
kiem("hai lệnh có nối vào bảng phím",
     "'gom-nhom': gomNhom" in sodo and "'ra-nhom': raNhom" in sodo)
kiem("lõi gom/tách ở Python, không ở giao diện",
     "py.gom_nhom(" in sodo and "py.ra_nhom(" in sodo,
     "— «một khối khác một hành động ở chỗ nào» là kiến thức của lõi")

print("\n▸ ⚠ Lượt soát KHÔNG được tự huỷ mình  (cuộc đua đã cắn thật)")
# React chạy hàm dọn của effect TRƯỚC MỖI lần effect chạy lại, kể cả lần không đổi gì.
# Dọn bằng `clearTimeout` ngay trong effect soát thì một lượt vẽ lại bất kỳ rơi vào
# 60ms đang chờ sẽ nuốt mất lượt soát: khối mới mang số "–" mãi, bảng Vấn đề đứng ở
# lượt cũ, mà không có lỗi nào. Giữ hẹn trong ref, bỏ kết quả cũ bằng SỐ LƯỢT.
kiem("hẹn soát giữ trong ref", "henSoat" in sodo and "luotSoat" in sodo)
kiem("không còn cờ `huy` của closure đã chết", "let huy = false" not in sodo)
kiem("hiệu ứng soát không tự dọn hẹn của mình",
     re.search(r"py\.soat\([\s\S]{0,900}?return \(\) => \{[^}]*clearTimeout", sodo)
     is None)

print(f"\n{'─' * 60}\n  {dung} đúng · {sai} sai\n{'─' * 60}")
sys.exit(1 if sai else 0)
