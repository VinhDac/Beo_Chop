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
NL = chr(10)


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


def bo_chu_thich_ts(s):
    """Bỏ `/* … */` và `// …` — nhắc tên một hàm trong chú thích KHÔNG phải là gọi nó.

    `(?<!:)` để `https://…` trong chuỗi không bị cắt mất phần sau."""
    return re.sub(r"(?<!:)//[^\n]*", " ", re.sub(r"/\*.*?\*/", " ", s, flags=re.S))

print("\n▸ Mọi `var(--x)` phải có một `--x:` ở đâu đó")
theme, app = doc("theme.css"), doc("app.css")
khai = set(re.findall(r"(--[a-z0-9-]+)\s*:", bo_chu_thich(theme + app)))
# ⚠ QUÉT CẢ TSX, không chỉ .css. `var(--khoi-do)` … `var(--khoi-tim)` được gọi từ
# `SoDo.tsx` (bảng `MAU_KHOI`), và NĂM trong sáu biến ấy không hề tồn tại — chọn màu
# khối là gán một biến rỗng, chẳng màu nào hiện ra. Phép kiểm này đứng ngay đây suốt
# thời gian ấy mà không thấy, vì nó chỉ đọc hai file .css.
tsx_all = ""
for _goc, _tm, _tep in os.walk(CSS):
    for _f in _tep:
        if _f.endswith((".tsx", ".ts")):
            with io.open(os.path.join(_goc, _f), encoding="utf-8") as _fh:
                tsx_all += _fh.read()
# ⚠ VÀ PHẢI BẮT CẢ TÊN BIẾN VIẾT RỜI, không chỉ dạng `var(--x)`. `MAU_KHOI` của
# `SoDo.tsx` giữ tên trần (`'--khoi-do'`) rồi mới ghép `var(${bien})` lúc chạy — nên
# chuỗi `var(--khoi-do)` KHÔNG HỀ CÓ trong mã nguồn. Bản đầu của phép kiểm này quét
# thêm TSX mà vẫn mù đúng chỗ ấy: xoá hẳn `--khoi-do` khỏi theme.css nó vẫn báo xanh.
tsx_sach = bo_chu_thich_ts(tsx_all)
dung_bien = set(re.findall(r"var\((--[a-z0-9-]+)", bo_chu_thich(app + theme)))
dung_bien |= set(re.findall(r"var\((--[a-z0-9-]+)", tsx_sach))
dung_bien |= set(re.findall(r"['\"`](--[a-z0-9-]+)['\"`]", tsx_sach))
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

sodo = bo_chu_thich_ts(doc("SoDo.tsx"))
api_py = io.open(os.path.join(GOC, "cat_studio", "api.py"), encoding="utf-8").read()
print("\n▸ Cửa sổ Kết quả: biểu đồ LẤP ĐẦY, cụm tab dưới KÉO ĐƯỢC")
# Trước đây `.kq-giua` cao theo nội dung, nên biểu đồ dừng giữa chừng và dưới nó là
# một mảng trống — cửa sổ càng cao, mảng trống càng to.
# ⚠ `.than-tab` là `0 1 auto` chứ KHÔNG phải `0 0 auto`, và đây là lần đổi luật thứ
# hai: `0 0 auto` giữ đúng chiều cao đã kéo (tốt) nhưng KHÔNG BAO GIỜ nhường, nên ở
# cửa sổ nhỏ nhất biểu đồ biến mất. Sàn `min-height` của `.kq-giua` mới là chỗ quyết
# ai nhường trước — có sàn rồi thì `0 1 auto` vẫn giữ đúng chiều cao khi còn chỗ.
for lop, luat in ((r"\.cua-so-kq \.kq-giua", "flex: 1 1 auto"),
                  (r"\.cua-so-kq \.than-tab", "flex: 0 1 auto")):
    kh = re.search(lop + r"[^}]*\}", bo_chu_thich(app))
    kiem(f"`{lop.replace(chr(92), '')}` khai `{luat}`",
         kh is not None and luat in kh.group(0), f"— {kh.group(0)[:70] if kh else '?'}")
# ⚠⚠ BA LUẬT NÀY ĐI VỚI NHAU, thiếu một là ĐÈ LÊN NHAU — đã hỏng thật một lần, và
# tôi không bắt được vì chỉ ĐO BẰNG SỐ mà không nhìn lại ảnh:
#   1. `align-items: stretch` — `.kq-giua` khai `flex-start` (đúng cho bản trong hộp
#      thoại). Trong cửa sổ thì hai cột tự cao theo NỘI DUNG, cột phải tràn ra và đè
#      lên hàng tab lẫn bảng thống kê. `overflow` đặt cho cột KHÔNG cứu được: cột có
#      tràn khỏi chính nó đâu, nó tràn khỏi CHA.
#   2. `min-height` cho `.kq-giua` — không có thì ở cửa sổ nhỏ nhất (1020×660) cụm
#      tab giữ nguyên chiều cao đã kéo và biểu đồ còn 90px.
#   3. `.kq-ben > .kq-hop { flex: 0 0 auto }` — không có thì ba cái hộp tự bóp rồi
#      CẮT CỤT bên trong (`overflow: hidden`), «Chọn biểu đồ» mất ba dòng cuối mà
#      không có thanh cuộn nào báo. Đo `scrollHeight` cũng tưởng vừa khít.
for lop, luat in ((r"\.cua-so-kq \.kq-giua", "align-items: stretch"),
                  (r"\.cua-so-kq \.kq-giua", "min-height: 170px"),
                  (r"\.cua-so-kq \.kq-ben > \.kq-hop", "flex: 0 0 auto")):
    kh = re.search(lop + r"[^}]*\}", bo_chu_thich(app))
    kiem(f"`{lop.replace(chr(92), '')}` khai `{luat}`",
         kh is not None and luat in kh.group(0))
bd_ = bo_chu_thich_ts(doc("components/BangDuoi.tsx"))
kq_ = bo_chu_thich_ts(doc("components/HopKetQua.tsx"))
kiem("bộ kéo cao tách ra dùng chung", "export function useKeoCao" in bd_)
kiem("và CẢ HAI bảng dưới đều dùng nó",
     "useKeoCao(" in kq_ and bd_.count("useKeoCao(") >= 2,
     "— chép tay lần hai thì hai bảng có hai cảm giác kéo khác nhau")
kiem("không còn bản chép tay nào", kq_.count("addEventListener('mousemove'") == 0)

print("\n▸ ⭐ Thanh tiêu đề tự vẽ và BỘ BẮT KÉO là MỘT thứ")
# ⚠ ĐÃ HỎNG THẬT. `useKhungCuaSo` chỉ được gọi trong `SoDo` — cửa sổ CHÍNH. Cửa sổ
# Kết quả riêng dựng `TitleBar` y hệt nhưng không ai lắp bộ kéo cho nó, nên dải tiêu
# đề của nó CHẾT: không kéo, không giãn, không Aero Snap. Không lỗi, không cảnh báo.
# Để hai thứ ở hai nơi là để lại một luật phải nhớ — và cửa sổ thứ ba sẽ quên y như
# cửa sổ thứ hai đã quên.
tb_ = bo_chu_thich_ts(doc("components/TitleBar.tsx"))
kiem("`TitleBar` tự lắp `useKhungCuaSo`", "useKhungCuaSo(" in tb_)
kiem("và KHÔNG chỗ nào khác gọi nó nữa",
     not any("useKhungCuaSo(" in bo_chu_thich_ts(doc(f))
             for f in ("SoDo.tsx", "TrangKetQua.tsx")),
     "— gọi hai nơi là hai listener, mỗi cú bấm gửi hai lần")
kiem("vá khung hụt thì NÓI, không im", "KHÔNG vá được khung" in api_py,
     "— cửa sổ chết mà nhìn y hệt cửa sổ thường")

print("\n▸ Màu khối — chấm màu, dấu màu đang dùng, và ô chọn nằm NGOÀI menu")
cm = bo_chu_thich_ts(doc("components/ContextMenu.tsx"))
kiem("mục menu có chấm màu", "cham-mau" in cm and "m.mau" in cm,
     "— tên «Lục», «Lam» thì phải bấm thử mới biết ra màu gì, mà bấm thử là một "
     "bước hoàn tác")
kiem("và dấu ✓ cho màu đang dùng", "m.dang" in cm and "dang-muc" in cm)
kiem("menu dựng từ bảng màu, kèm màu tự chọn đang có trên sơ đồ",
     "bangMau" in sodo and "mauTuChon" in sodo)
# ⚠ BẪY JENIFER ĐÃ GHI: menu đóng ngay khi bấm, còn bảng màu thì vẫn mở — ô nằm
# TRONG menu là bị gỡ theo menu, chọn xong không còn ai nhận màu.
kiem("ô chọn màu nằm NGOÀI menu",
     re.search(r"o-mau-an[\s\S]{0,260}<ContextMenu", sodo) is not None)
kiem("và tô khi bảng ĐÓNG, không theo từng nhích kéo",
     "o.onchange" in sodo and "o.oninput" not in sodo,
     "— một lần chọn là MỘT bước hoàn tác, không phải ba chục")
kiem("«Bỏ màu» mờ kèm lý do khi chưa có màu", "tat: !coMau" in sodo)

print("\n▸ ⚙ ở GÓC TRÁI DƯỚI — chỗ quen thuộc cho cài đặt (VSCode cũng vậy)")
# ⚠ Chú thích cỡ chữ trong `app.css` đã tính chỗ cho nút này từ lâu — «nút ⚙ 24→26»
# — mà nút thì chưa bao giờ có. Lại một hàng rào không ai gác.
kiem("thanh trạng thái có nút ⚙",
     re.search(r'className="nut-tt"[\s\S]{0,200}setMoCaiDat\(true\)', sodo) is not None)
kiem("và nó đứng ĐẦU hàng, trước mấy con số",
     # `nodes.length` nay là đối số của `trx('{0} khối · {1} dây', …)` — bộ dịch bọc câu
     # lại, nên khuôn cũ `{nodes.length}` không còn. Bắt theo CHÍNH TÊN BIẾN, hình nào
     # cũng khớp: thứ bài này canh là THỨ TỰ, không phải cách viết câu.
     re.search(r'thanh-trang-thai"[\s\S]{0,500}?nut-tt[\s\S]{0,320}?nodes\.length', sodo)
     is not None)
kiem("có luật CSS cho nó", ".nut-tt {" in bo_chu_thich(app))

print("\n▸ Menu thanh tiêu đề — đường LUÔN CÓ, khác ribbon (ribbon ẩn bớt khi hẹp)")
# ⚠ Trước đây chỉ MỘT nhóm «Cat Studio» với bốn mục, không mục nào hiện phím tắt và
# không mục nào mờ được. Hậu quả: ở cửa sổ 1020px (sàn của app) ribbon ẩn mất nhóm
# Sửa, Hoàn tác và Strategy — lúc ấy Hoàn tác, Nhân bản, Xoá, Lưu KHÔNG còn chỗ nào
# bấm được. Jenifer_Studio có File/Edit/View/Help đúng vì lẽ ấy.
# Tên nhóm đi qua bộ dịch (`ten: tr('Sửa')`) trừ «File» — tên ấy giống nhau cả hai
# tiếng nên không có khoá nào. Khuôn phải nhận CẢ HAI hình, không thì bài này chỉ còn
# đếm được một nhóm và nó kêu oan.
nhom_menu = re.findall(r"\{ ten: (?:tr\()?'(\w+)'\)?, muc: \[", sodo)
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

# ⚠ DÂY PHẢI NGẮT ĐƯỢC TỪNG SỢI. Trước đây chỉ có «Ngắt hết kết nối» trên một KHỐI —
# cắt sạch mọi dây chạm tới nó. Trên một chỗ rẽ ba nhánh, muốn bỏ đúng một nhánh thì
# phải cắt cả ba rồi nối lại hai. Mà `deleteKeyCode={null}` nên chọn dây rồi bấm
# Delete cũng không ra gì: dây là thứ vẽ ra được, bấm được, mà không gỡ được.
# ⚠ BA THỨ GIẾT KHỐI MỜ, CẢ BA ĐỀU LẶNG — đã mất một buổi dò từng cái:
#   · `visibility: hidden`: React Flow ẩn nút nó CHƯA ĐO ĐƯỢC cỡ, mà đã ẩn thì không
#     có hộp bố cục nên không bao giờ đo được. Khai sẵn `width`/`height` là hết.
#   · `pointer-events: none`: nút khai `selectable/draggable/connectable: false` thì
#     React Flow tắt chuột của nó. Phải đặt lại trong `style` của CHÍNH nút — một
#     luật trong tệp CSS thua, vì React Flow đặt nội tuyến.
#   · cú bấm nằm ở `mousedown`, không ở `click`: chuột nhấn xuống làm bỏ chọn khối,
#     khối mờ tính theo khối ấy nên biến mất trước khi `click` kịp bắn.
# Cả ba đều cho ra CÙNG một triệu chứng: con trỏ là bàn tay, bấm vào không ra gì.
# ⚠ KHỐI QUAY VỀ RƠI QUA KẼ GIỮA HAI TỪ ĐIỂN. Nó không hỏi thị trường, cũng không ra
# lệnh nào — nó là NGỮ PHÁP của hình vẽ — nên không thuộc từ điển Hỏi lẫn từ điển Làm,
# và bấm đúp vào nó không ra gì. Tệ hơn: ô «số vòng» của nó không đặt được Ở ĐÂU CẢ.
# Đếm cả mã nguồn thì `so_vong` của một KHỐI chỉ được ĐỌC (vẽ đường ↻, sinh mã), chưa
# một chỗ nào ghi — một ô có thật trong file, có thật trong bộ sinh mã, mà người dùng
# không có cửa nào chạm tới. (Ô số vòng trên ĐƯỜNG ↻ là lối khai vòng thứ hai, khác.)
print("\n▸ Khối Quay về có hộp sửa, và sửa được SỐ VÒNG")
_qv = doc("components/HopQuayVe.tsx")
kiem("có hộp riêng cho Quay về", bool(_qv))
kiem("sửa được ĐÍCH", "setVe(" in _qv)
kiem("và sửa được SỐ VÒNG", "so_vong" in _qv and "setSoVong(" in _qv,
     "— ô có thật trong file và trong bộ sinh mã mà không có cửa nào chạm tới")
kiem("để TRỐNG là lặp mãi, và KHÔNG ghi khoá",
     "delete s.so_vong" in _qv,
     "— có khoá mà giá trị rỗng là thứ `khoi_quay_ve` phải đoán")
kiem("bấm đúp vào Quay về mở được hộp",
     "quay_ve" in doc("SoDo.tsx") and "HopQuayVe" in doc("SoDo.tsx"))

print("\n▸ Khối mờ của nối thông minh — ba chỗ chết LẶNG")
_sd_mo = doc("SoDo.tsx")
kiem("khối mờ khai sẵn CỠ", re.search(r"width: 296, height: \d+", _sd_mo) is not None,
     "— không khai thì React Flow ẩn nó, mà ẩn rồi thì không bao giờ đo được")
kiem("và bật lại chuột cho nó", "pointerEvents: 'all'" in _sd_mo,
     "— nút không chọn/kéo/nối được thì React Flow tắt chuột của nó")
kiem("cú bấm ở mousedown, không ở click",
     "onMouseDown" in doc("components/KhoiMo.tsx")
     and "onClick" not in doc("components/KhoiMo.tsx"),
     "— click bắn sau khi nhả chuột, lúc ấy khối mờ đã bị gỡ khỏi cây")
kiem("và mang `nopan` để bộ KÉO MÀN nhả cú nhấn ra",
     "className: 'nopan'" in _sd_mo,
     "— d3-zoom bắt mousedown ở pha capture trên cả vùng vẽ; khối THẬT được React "
     "Flow tự gắn nopan vì nó kéo được, khối mờ thì không")
kiem("ngữ pháp gợi ý do PYTHON nói", "py.goi_y_ke(" in _sd_mo,
     "— viết lại luật rẽ nhánh bằng TS là bản sự thật thứ hai")

print("\n▸ Ngắt được MỘT dây — và có cả lối không cần trúng đích")
_sd_day = doc("SoDo.tsx")
kiem("bấm đúp vào dây là ngắt nó", "onEdgeDoubleClick" in _sd_day)
kiem("và chuột phải vào dây mở menu", "onEdgeContextMenu" in _sd_day,
     "— dây mảnh, trượt vài pixel là trúng nền; phép nhanh phải có phép chậm đi kèm")
kiem("menu ấy có mục ngắt", "Ngắt dây này" in _sd_day)
kiem("và ngắt dây CHỤP một bước hoàn tác",
     re.search(r"ngatMotDay = useCallback[\s\S]{0,160}chup\(\)", _sd_day) is not None,
     "— gỡ nhầm một dây mà không lùi lại được thì phải vẽ lại tay")

print("\n▸ Hộp Bắt đầu KHÔNG được khai lại thứ Python đã khai")
from cat_studio import bat_dau  # noqa: E402
# ⚠ MỘT RUỘT, HAI HỘP. Hộp «Bắt đầu» và hộp «Cỗ máy LEAN» bày ô theo CÙNG một luật
# (xếp theo nhóm Python khai, ô con đi ngay sau ô cha, đổi ô cha thì điền mặc định cho
# ô con, lưu thì bỏ ô của lựa chọn đã tắt), nên bộ vẽ ô nằm trong `RuotBatDau.tsx` và
# cả hai hộp gọi nó. Chép ra hai bản là hai bản sẽ lệch — mà lệch ở đây nghĩa là một
# hộp mất ô con, model chạy ở mặc định của LEAN trong khi nhãn hứa một đằng.
bd = bo_chu_thich_ts(doc("components/RuotBatDau.tsx"))
kiem("hai hộp dùng CHUNG một ruột, không chép ra hai bản",
     all("RuotBatDau" in doc(f"components/{_x}.tsx")
         for _x in ("HopBatDau", "HopCoMay")),
     "— chép ra hai bản thì sớm muộn một bên mất ô con")
# ⚠ ĐÃ HỎNG THẬT, ba cái một lúc. Hộp thoại dựng lại object cho mấy ô THÊM của nhịp:
#   kieu: 'so' đóng cứng  -> «Độ phân giải dữ liệu» (ô CHỌN năm mức) hiện ra như ô gõ
#   chon: []              -> năm lựa chọn bị vứt
#   goi_y tự chế từ `o.nho_nhat`/`o.lon_nhat` — hai khoá KHÔNG HỀ CÓ trong từ điển
#                         -> in ra đúng chữ "Từ undefined đến undefined", đè mất câu
#                            gợi ý thật. Không lỗi, không cảnh báo, build sạch.
kiem("không còn đọc khoá `nho_nhat` (từ điển không có khoá ấy)", "nho_nhat" not in bd)
kiem("không còn đóng cứng `kieu: 'so'`", "kieu: 'so'" not in bd)
kiem("ô con đưa thẳng `o` của Python vào, không dựng lại",
     re.search(r"function veOVaCon\([\s\S]{0,400}<Hang[^>]*o=\{o\b", bd)
     is not None)
# ⚠ VÀ PHẢI VẼ LỒNG NHIỀU TẦNG. Chuỗi thật sâu hai tầng rồi: «Nhịp» mở ra «Lúc nào
# trong ngày», ô ấy lại mở ra «Số phút sau khi mở» hay «Giờ» + «Phút». Bản vẽ một
# tầng thì tầng thứ hai biến mất, và lịch chạy ở mặc định — không lỗi, không một lời.
kiem("và vẽ ĐỆ QUY, không dừng ở một tầng",
     re.search(r"function veOVaCon\([\s\S]{0,700}veOVaCon\(c,", bd) is not None,
     "— `veOVaCon` phải gọi lại chính nó cho ô con")

# ⚠ MỌI BẢNG CÓ Ô CON PHẢI ĐƯỢC TRA — và đây là hàng rào quan trọng nhất của mục
# này. Python gửi sáu bảng mang `o_them` (`nhip` · `quy_tac_gio` · `phong_rui_ro` ·
# `phat_tin_hieu` · `phi` · `truot_gia`). Thêm bảng thứ bảy mà quên khai trong
# `bangOThem` thì ô ấy chọn xong KHÔNG núm nào hiện ra, và model chạy ở mặc định của
# LEAN — nhãn hứa một đằng, mã sinh ra một nẻo, không một lời nào.
#
# Bệnh ấy đã dính ba lần trong một ngày: `StandardDeviationExecutionModel` chạy ở
# `Resolution.MINUTE` ngầm; rổ `ema_cheo` chạy ở 500 mã trong khi hộp hứa 20;
# `add_security_initializer` đặt sai chỗ nên phí/trượt giá không có tác dụng gì.
# LẶP QUA CHÍNH TỪ ĐIỂN: Python thêm một bảng là phép này canh luôn.
_co_o_con = [k for k, v in bat_dau.tu_dien().items()
             if isinstance(v, list) and v
             and all(isinstance(x, dict) and "o_them" in x for x in v)]
kiem("Python gửi đủ sáu bảng có ô con", len(_co_o_con) >= 6, f"— {_co_o_con}")
# ⚠ `ro` KHÔNG đi qua `bangOThem`, CỐ Ý: ô con của rổ («Mã ETF», «Lấy mấy mã») nằm
# trong widget `OChayTrenMa` của ô «Chạy trên mã nào», vì «rổ nào» và «rổ ấy lấy mấy
# mã» là MỘT câu trả lời cho MỘT câu hỏi (xem `bat_dau._o_ro`). Widget ấy cũng bày
# thẳng `o_them` của Python — phép soi nhãn gõ cứng ngay dưới canh cả nó.
_O_CON_CHO_KHAC = {
    "ro": "ô con của rổ nằm trong widget OChayTrenMa của ô «Chạy trên mã nào»",
}
_quen = [k for k in _co_o_con
         if f"{k}: td.{k}" not in bd and f"{k}: tuDien.{k}" not in bd
         and k not in _O_CON_CHO_KHAC]
kiem("bảng nào có ô con thì `bangOThem` phải tra được", not _quen,
     f"— {_quen} gửi sang mà hộp thoại không tra, nên ô con của chúng KHÔNG hiện")
# Và danh sách ngoại lệ không được mục: tên nào trong đó mà Python không còn gửi,
# hay nay đã đi qua `bangOThem`, thì phải xoá khỏi đây.
_muc = [k for k in _O_CON_CHO_KHAC
        if k not in _co_o_con or f"{k}: td.{k}" in bd
        or f"{k}: tuDien.{k}" in bd]
kiem("danh sách ngoại lệ ô con không mục", not _muc, f"— {_muc}")

# Nhãn ô con khác nhau ở từng model («cắt khi lỗ» / «chốt khi lãi» / «tụt khỏi
# đỉnh»), nên dựng lại ô ấy bên TypeScript là nói sai gần hết — mà con số vẫn chạy,
# nên không ai thấy. Soi CẢ SÁU bảng, không riêng phòng rủi ro.
_go_cung = sorted({o["nhan"] for k in _co_o_con
                   for muc in bat_dau.tu_dien()[k] for o in muc["o_them"]
                   if f'"{o["nhan"]}"' in bd or f"'{o['nhan']}'" in bd})
kiem("và không gõ cứng nhãn ô con nào", not _go_cung, f"— {_go_cung}")
# Lưu thì phải BỎ ô của lựa chọn không còn hiện — không thì file mang theo một ngưỡng
# cắt lỗ của trạm đã tắt, rồi mở lại là nó lặng lẽ sống lại.
kiem("lưu có lọc ô của lựa chọn đã tắt, cho MỌI bảng",
     re.search(r"function locOAnHien\([\s\S]{0,500}bangOThemCua\(", bd)
     is not None,
     "— lọc theo tên bảng gõ tay thì thêm bảng thứ bảy là nó lọt")
kiem("và CẢ HAI hộp gọi đúng hàm lọc ấy",
     all("locOAnHien" in doc(f"components/{_x}.tsx")
         for _x in ("HopBatDau", "HopCoMay")),
     "— hộp nào tự lọc lấy là hộp ấy quên một bảng")
# Dòng khai LEAN tồn tại ĐÚNG ĐỂ kiểm lời hứa — nó nói sai thì tệ hơn không có nó.
# Nên giao diện KHÔNG ghép câu ấy nữa: nó hỏi `bat_dau.khai()` sau MỖI thay đổi rồi
# bày lại nguyên văn. Trước đây chỗ này tự suy ra độ phân giải thật, tự chọn `add_*`
# hay `universe_settings`, tự ghép với tên hàm lịch — bốn phép Python đã làm rồi, và
# bản TypeScript ấy từng in `Resolution.MINUTE` trong khi bộ sinh mã viết DAILY.
_hbd = bo_chu_thich_ts(doc("components/HopBatDau.tsx"))
kiem("dòng khai LEAN HỎI Python, không tự ghép", "py.khai_bat_dau(" in _hbd,
     "— mọi phép suy ra câu ấy nằm ở `bat_dau.khai`, một bản sự thật")
kiem("và hỏi lại theo giá trị ĐANG gõ, không hỏi một lần lúc mở hộp",
     re.search(r"useEffect\([\s\S]{0,300}khai_bat_dau\([\s\S]{0,200}\[gt\]\)",
               _hbd) is not None,
     "— đổi nhịp hay đổi rổ mà dòng khai đứng yên là nó nói một câu đã cũ")
kiem("Mốc so sánh là ô CHỌN", re.search(r"moc_so_sanh[\s\S]{0,400}<select", bd) is not None)
# ⚠ «Mã» ở hộp Bắt đầu còn «Mốc so sánh» ở hộp Cỗ máy — HAI hồ sơ khác nhau. Nên hộp
# Cỗ máy phải được TRUYỀN mã của sơ đồ vào; đọc bừa từ hồ sơ của nó thì ô mốc chỉ còn
# mấy mã có dữ liệu miễn phí, và người dùng mất cách chọn chính mã mình đang chạy.
kiem("hộp Cỗ máy NHẬN mã của sơ đồ cho ô Mốc so sánh",
     "maSoDo" in doc("components/HopCoMay.tsx")
     and "maSoDo={dsMa}" in doc("SoDo.tsx"),
     "— không truyền thì ô mốc mất đúng mấy dòng đáng chọn nhất, mà vẫn bày ra")
kiem("mã không có dữ liệu miễn phí thì NÓI ra", "ma-khong-co" in bd,
     "— nói, chứ không chặn: ai có dữ liệu riêng vẫn chạy được")

print(NL + "▸ Ô «Chạy trên mã nào» có HAI KIỂU — và kiểu rổ làm vỡ bốn chỗ cũ")
# Ô ấy nay nhận MỘT MẢNG mã gõ sẵn hoặc MỘT OBJECT rổ. Object không có `.map`, nên
# mọi chỗ cũ coi nó là mảng sẽ ném `TypeError` — React bắt được và thay cả cây bằng
# một màn trắng. Không phải lỗi lặng, nhưng nó lặng ở chỗ KHÁC: `tsc` sạch, vì mấy
# chỗ ấy đều `as MaChay[]` — tức tự khai rằng mình biết chắc, mà không biết chắc.
kiem("một chỗ duy nhất quyết «đang nói kiểu nào»", "export function laRo(" in bd,
     "— hai nơi cùng đoán hình dạng là hai nơi để trôi khỏi nhau")
kiem("Mốc so sánh không còn gọi `.map` thẳng trên `gt.ma`",
     "Array.isArray(gt.ma)" in bd)
kiem("danh sách mã của canvas cũng chặn",
     "Array.isArray(khoiBatDau?.ma)" in bo_chu_thich_ts(doc("SoDo.tsx")),
     "— rổ thì KHÔNG có mã nào để bày, đúng như `sinh_ma._sym_py` chối")
# Dòng khai LEAN đổi CẢ HAI NỬA khi chọn rổ (không `add_*` nào, lịch chạy bằng mấy
# hàm KHÔNG MÃ) và mọc thêm một câu `set_universe_selection`. BA phép ấy nay nằm hết
# bên Python — `test_bat_dau` canh chúng, chỗ này chỉ canh hộp có bày RA MẤY CÂU.
oruot = doc("components/ORuot.tsx")
kiem("hộp bày được NHIỀU câu, không chỉ một",
     re.search(r"KhaiLean\(\{ ham \}[\s\S]{0,200}Array\.isArray\(ham\)", oruot)
     is not None,
     "— rổ động khai hai câu; chỉ có chỗ cho một là câu của rổ không hiện ra đâu cả")
kiem("và mấy câu ấy xếp DỌC",
     'className="lean-cau"' in oruot and ".lean-cau {" in doc("app.css"),
     "— để thẳng trong `.lean-khai` là flex xếp ngang, hai câu dính thành một dòng")
# Ô CON của rổ cũng phải đưa thẳng `o` của Python vào — cùng cái bẫy đã cắn ở ô thêm
# của nhịp (ô CHỌN hiện ra như ô gõ, câu gợi ý thật bị đè).
kiem("ô con của rổ đưa thẳng `o` của Python vào",
     re.search(r"muc\?\.o_them[\s\S]{0,300}<OTheoKieu[^>]*o=\{o\b", bd) is not None)
# `Hang` dựng một `<label>`, mà ô con của rổ nằm TRONG `<label>` của hàng «Chạy trên
# mã nào» — label lồng label thì bấm nhãn con nhảy focus sang ô cha, lặng lẽ.
kiem("ô con của rổ KHÔNG lồng `Hang` (label trong label)",
     re.search(r"muc\?\.o_them[\s\S]{0,300}<Hang", bd) is None)
kiem("và `OTheoKieu` là một chỗ duy nhất quyết `kieu` nào ra widget nào",
     "export function OTheoKieu(" in doc("components/ORuot.tsx"))
# Mấy luật CSS canh `:has(.ds-ma)` để nhãn xếp lên đầu hàng — chọn rổ thì `.ds-ma`
# không còn, nên nhãn tụt về giữa. Build vẫn sạch, chỉ nhìn mới thấy.
css_bd = doc("app.css")
kiem("CSS của hàng ấy bắt cả `.o-chay-ma`", ":has(.o-chay-ma)" in css_bd,
     "— chỉ bắt `.ds-ma` thì chọn rổ là cái nhãn tụt về giữa hàng")

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

print("\n▸ ⚠ Bảng nổi là `overflow: hidden` — ruột nó PHẢI cuộn được")
# `.bang-noi` cắt mọi thứ tràn ra (để bo góc và đổ bóng cho gọn). Từ khi ô GHÉP mở
# thêm một tầng núm, trường hợp sâu nhất là MACD ghép MACD: ĐO ĐƯỢC 499px ruột trong
# một bảng cao tối đa 440. Không có hai dòng dưới đây thì 59px cuối bị CẮT — và cái
# bị cắt chính là dòng khai hàm LEAN ở chân, thứ nói cho người dùng biết họ vừa vẽ
# ra câu gì. Không lỗi, không cảnh báo, chỉ là nó không còn ở đó.
_css = io.open(os.path.join(GOC, "webui", "src", "app.css"), encoding="utf-8").read()
_bn = re.search(r"\.bang-noi\s*\{[^}]*\}", _css)
kiem("`.bang-noi` vẫn là overflow:hidden — nên luật dưới mới cần",
     bool(_bn) and "overflow: hidden" in _bn.group(0))
_bc = re.search(r"\.bn-chinh\s*\{[^}]*\}", _css)
kiem("`.bn-chinh` cuộn được", bool(_bc) and "overflow-y: auto" in _bc.group(0),
     f"— {_bc.group(0) if _bc else 'KHÔNG CÓ LUẬT NÀO'}")
kiem("và có `min-height: 0` — thiếu nó thì flex item không co lại để mà cuộn",
     bool(_bc) and "min-height: 0" in _bc.group(0))
_hdk = io.open(os.path.join(GOC, "webui", "src", "components", "HopDieuKien.tsx"),
               encoding="utf-8").read()
kiem("dòng khai LEAN nằm NGOÀI tấm cuộn, nên nó ghim ở chân",
     re.search(r"</div>\s*(?:\{/\*[\s\S]*?\*/\}\s*)?<div className=\"bn-lean\"",
               _hdk) is not None,
     "— để trong `.bn-chinh` là nó cuộn mất")

print(f"\n{'─' * 60}\n  {dung} đúng · {sai} sai\n{'─' * 60}")
sys.exit(1 if sai else 0)
