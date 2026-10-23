"""TRANG GIỚI THIỆU — thứ hỏng LẶNG, không ai thấy cho tới khi trang đã lên mạng.

`site/` không có bộ dựng, không có kiểu, không có gì chạy nó cả: sai một chữ trong
`class`, trỏ nhầm một đường dẫn ảnh, hay khai sai cỡ ảnh — trang vẫn mở ra, chỉ là
hỏng. Và nó là mặt tiền, chỗ duy nhất người lạ nhìn vào.

Bài này canh bốn thứ KHÔNG mắt nào bắt kịp:

  · tệp trang trỏ tới có thật không
  · cỡ `width`/`height` khai trên `<img>` có đúng cỡ ảnh thật không
  · mỗi `class` trong HTML có luật nào trong CSS không, và ngược lại
  · mỗi bộ chọn `querySelector` trong JS có tìm thấy gì trong HTML không
  · và CON SỐ trang khoe có khớp với con số APP đếm được không

Chỗ cuối là chỗ đau nhất: trang viết «26 levels, 66 stars» bằng tay thì hôm nào thêm
một màn là trang nói dối, mà không có gì kêu.

⚠ KHÔNG CANH «CÓ BAO NHIÊU LUẬT». Canh số lượng là canh một con số gõ tay thứ hai.
"""
import io
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANG = os.path.join(GOC, "site")
HTML = io.open(os.path.join(TRANG, "index.html"), encoding="utf-8").read()
CSS = io.open(os.path.join(TRANG, "assets", "site.css"), encoding="utf-8").read()

# ⚠ BỎ LỜI CHÚ THÍCH TRƯỚC ĐÃ. Bài này dò chữ trong tệp, nên một dòng chú viết
# «trước đây là `.khoi/.bade/.dinh/.than`» bị nó đọc thành bốn luật CSS có thật — và
# nó kêu oan vào đúng lời giải thích vì sao mấy luật ấy đã bị xoá. Dự án này đã dính
# đúng kiểu ấy ba lần ở chỗ khác; đừng để lần thứ tư.
_KHONG_CHU = re.compile(r'/\*.*?\*/', re.S)
_KHONG_CHU_HTML = re.compile(r'<!--.*?-->', re.S)
CSS_SACH = _KHONG_CHU.sub(" ", CSS)
HTML_SACH = _KHONG_CHU_HTML.sub(" ", HTML)
JS = io.open(os.path.join(TRANG, "assets", "mach.js"), encoding="utf-8").read()

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def co_anh(duong):
    """Cỡ thật của một ảnh JPEG/PNG. -> (rộng, cao) hoặc None.

    Đọc tay, không cần thư viện ngoài: bài kiểm phải chạy được ở mọi chỗ."""
    with open(duong, "rb") as f:
        d = f.read()
    if d[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", d[16:24])
    if d[:2] == b"\xff\xd8":
        i = 2
        while i < len(d) - 9:
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                i += 2
                continue
            n = struct.unpack(">H", d[i + 2:i + 4])[0]
            # SOF0..SOF15, trừ mấy mã không phải khung ảnh
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                cao, rong = struct.unpack(">HH", d[i + 5:i + 9])
                return rong, cao
            i += 2 + n
    return None


# ================= 1. Tệp trang trỏ tới phải có thật =================
print("\n▸ Mọi đường dẫn nội bộ đều trỏ vào một tệp có thật")
duong = set()
for m in re.finditer(r'(?:src|href)="([^"]+)"', HTML):
    u = m.group(1)
    if u.startswith(("http:", "https:", "#", "data:", "mailto:")) or u == "./":
        continue
    duong.add(u.split("?")[0].split("#")[0])
thieu = sorted(u for u in duong if not os.path.isfile(os.path.join(TRANG, u)))
kiem(f"{len(duong)} đường dẫn", not thieu, f"— thiếu: {thieu}" if thieu else "")

# ⚠ VÀ NGƯỢC LẠI: ảnh nào trong `assets/anh/` cũng phải có chỗ dùng. Dựng lại một
# khúc là ảnh cũ thành mồ côi — nằm im trong một kho CÔNG KHAI, không ai thấy để xoá.
# Lần này có hai cái: `xuong.jpg` bị `4-xuong.jpg` thay, và `kho.jpg` rơi ra lúc khúc
# giữa dựng lại — mà trang thì vẫn đang nói về cái Kho bằng chữ.
print("\n▸ Ảnh nào trong kho cũng có chỗ dùng")
# Thư mục ảnh chụp đã bỏ hẳn — trang nay VẼ cả sáu màn hình. Nếu nó quay lại thì
# vẫn soát như cũ; không có thì không có gì phải soát, và nói thẳng ra thế.
thu_muc_anh = os.path.join(TRANG, "assets", "anh")
co_tren_dia = {f for f in (os.listdir(thu_muc_anh) if os.path.isdir(thu_muc_anh) else ())
               if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))}
dung_toi = {os.path.basename(u) for u in duong if "/anh/" in u}
mo_coi = sorted(co_tren_dia - dung_toi)
kiem(f"{len(co_tren_dia)} ảnh", not mo_coi, f"— mồ côi: {mo_coi}" if mo_coi else "")

# ================= 2. Cỡ ảnh khai phải đúng cỡ ảnh thật =================
# Khai sai là trình duyệt chừa sai chỗ: trang nhảy một nhát lúc ảnh tải xong, hoặc
# ảnh bị bóp méo. Mà nhìn bằng mắt thì khó thấy — ảnh nào cũng "trông bình thường".
print("\n▸ `width`/`height` trên <img> khớp cỡ ảnh thật")
lech = []
dem = 0
for m in re.finditer(r'<img[^>]*>', HTML):
    the = m.group(0)
    src = re.search(r'src="([^"]+)"', the)
    w = re.search(r'width="(\d+)"', the)
    h = re.search(r'height="(\d+)"', the)
    if not (src and w and h):
        continue
    p = os.path.join(TRANG, src.group(1))
    if not os.path.isfile(p):
        continue
    that = co_anh(p)
    dem += 1
    if that and that != (int(w.group(1)), int(h.group(1))):
        lech.append(f"{src.group(1)} khai {w.group(1)}×{h.group(1)} mà thật là "
                    f"{that[0]}×{that[1]}")
kiem(f"{dem} ảnh", not lech, "— " + "; ".join(lech) if lech else "")

# ================= 3. Tên lớp: HTML và CSS phải gặp nhau =================
# ⚠ ĐÂY LÀ CHỖ ĐÃ HỎNG HAI LẦN. `.so` của bảng số đè lên `<span class="so">` trong
# mẫu mã, và `.ray` của cuộn phim đè lên `.ray` của mạch cuộn — mà `.ray` lại nằm
# trong luật `display:none` ở màn hẹp, nên cả dải sáu bước BIẾN MẤT. Cả hai lần chỉ
# ẢNH CHỤP mới thấy, vì CSS không báo lỗi bao giờ.
#   Bài này không đọc nổi CSS như trình duyệt, nên nó canh hai chiều rẻ mà chắc:
#   lớp nào HTML dùng thì CSS phải có luật, lớp nào CSS tạo luật thì HTML phải dùng.
#   Lớp thừa trong CSS chính là dấu một lần đổi tên làm nửa chừng.
print("\n▸ Mỗi lớp trong HTML có luật trong CSS")
trong_html = set()
for m in re.finditer(r'class="([^"]+)"', HTML_SACH):
    trong_html |= set(m.group(1).split())
# Lớp do JS gắn vào lúc chạy, không có trong HTML tĩnh.
JS_GAN = {"hien"}
khong_luat = sorted(c for c in trong_html
                    if not re.search(r'\.' + re.escape(c) + r'(?![\w-])', CSS_SACH))
kiem(f"{len(trong_html)} lớp", not khong_luat, f"— không luật: {khong_luat}"
     if khong_luat else "")

# ⚠ TIỀN TỐ `c-` CHO MỌI LỚP TRONG CẢNH VẼ. Đây là hàng rào bắt được cái mà hai
# phép soát trên KHÔNG bắt được: trùng tên. Trùng tên thì cả hai chiều đều hợp lệ —
# HTML có lớp, CSS có luật — mà luật ăn vào là luật của người khác.
#
# Ba lần trong hai ngày, và lần nào cũng chỉ ảnh chụp mới thấy:
#   `.so`    bảng thống kê (display:grid) đè `<span class="so">` trong mẫu mã;
#   `.ray`   cuộn phim đè thanh tiến độ mạch cuộn — mà `.ray` nằm trong một luật
#            `display:none`, nên cả dải sáu bước BIẾN MẤT ở màn hẹp;
#   `.xuong` dòng tiền đang giảm đè cái mũi tên «cuộn xuống» đầu trang (display:flex
#            + một thanh gradient 30px), nên bảng tiền tự xếp chồng lên chính nó.
# Cùng lượt ấy còn `.boss` (nhãn đồ thị) và `.mo` (CHÍNH LÀ `<section class="mo">`).
#
# Một tiền tố là hết. Trừ đúng bốn lớp cố ý dùng chung bảng màu ngữ nghĩa của khối —
# vì khối trong cảnh vẽ CHÍNH LÀ khối trong mạch cuộn, tô cùng một luật mới đúng.
print("\n▸ Lớp trong cảnh vẽ đều mang tiền tố `c-`")
DUNG_CHUNG = {"ma", "so", "dl", "phep"}
vung = (re.findall(r'<div class="c-canh".*?\n        </div>', HTML, re.S)
        + re.findall(r'<div class="c-kho">.*?\n  </div>', HTML, re.S))
trong_canh = set()
for v in vung:
    for m in re.finditer(r'class="([^"]+)"', v):
        trong_canh |= set(m.group(1).split())
khong_tien_to = sorted(c for c in trong_canh
                       if not c.startswith("c-") and c not in DUNG_CHUNG)
kiem(f"{len(vung)} cảnh · {len(trong_canh)} lớp", bool(vung) and not khong_tien_to,
     f"— thiếu tiền tố: {khong_tien_to}" if khong_tien_to
     else ("" if vung else "— KHÔNG THẤY CẢNH NÀO, bài này đang soát rỗng"))

# ⚠ VÀ TIỀN TỐ KHÔNG CỨU ĐƯỢC MỌI CHUYỆN. Hai lớp đụng nhau NGAY TRONG vùng `c-`:
#   `.c-day`  vừa là <svg> dây nối, vừa là dòng dẫn <p> của màn Giao việc — luật của
#             SVG (`position:absolute; inset:0`) ăn vào đoạn văn, nó nhảy lên đè tiêu đề;
#   `.c-mo`   vừa là khung giữa màn chờ, vừa là món «Live» mờ trên thanh đồ nghề.
# Cái đụng nhau là NGHĨA, không phải vùng tên — nên soi bằng dấu hiệu khác: một lớp
# gắn lên hai LOẠI THẺ khác nhau thì gần như chắc là nó đang gánh hai việc.
# Thẻ cùng họ (b/strong, i/em, u/span) không tính, chúng chỉ là chữ.
print("\n▸ Không lớp nào trong cảnh gánh hai nghĩa")
HO_CHU = {"b", "strong", "i", "em", "u", "small", "span"}
tren_the = {}
for v in vung:
    for m in re.finditer(r'<([a-z0-9]+)[^>]*class="([^"]+)"', v):
        the = "chu" if m.group(1) in HO_CHU else m.group(1)
        for t in m.group(2).split():
            tren_the.setdefault(t, set()).add(the)
hai_nghia = sorted(f"{t} ({'/'.join(sorted(v))})"
                   for t, v in tren_the.items() if len(v) > 1)
kiem(f"{len(tren_the)} lớp", not hai_nghia, f"— {hai_nghia}" if hai_nghia else "")

# ⚠ VÀ CẢ TIỀN TỐ LẪN «MỘT LOẠI THẺ» VẪN CHƯA ĐỦ. Hai lớp nữa đụng nhau ngay trong
# vùng `c-`, mà cả hai bên đều là <div> nên phép trên cho qua:
#   `.c-hoi`  vừa là hàng tiêu đề hồi ở màn Hành trình (`display:flex`), vừa là biến
#             thể «khối Xác nhận» — năm cái khối hoá thành flex hàng ngang, thân khối
#             nhảy sang nằm cạnh cái đỉnh và chữ `RSI(14) < 30` thò ra ngoài hộp;
#   `.c-nhan` vừa là nhãn nhỏ trong hộp («ARENA»), vừa là vòng sáng quanh nút Backtest.
# Dấu hiệu chung: một lớp VỪA đứng một mình, VỪA đi kèm sau một lớp khác — tức là nó
# vừa là TÊN của một thứ, vừa là BIẾN THỂ của thứ khác. Biến thể thì phải mang tên
# cái nó sửa (`c-khoi-hoi`, `c-mon-nhan`).
print("\n▸ Không lớp nào vừa là tên, vừa là biến thể")
mot_minh, di_kem = set(), {}
for v in vung:
    for m in re.finditer(r'class="([^"]+)"', v):
        t = m.group(1).split()
        if len(t) == 1:
            mot_minh.add(t[0])
        else:
            for x in t[1:]:
                di_kem.setdefault(x, set()).add(t[0])
hai_viec = sorted(f"{c} (cũng là biến thể của {sorted(di_kem[c])})"
                  for c in mot_minh & set(di_kem))
kiem(f"{len(mot_minh)} lớp đứng một mình · {len(di_kem)} biến thể", not hai_viec,
     f"— {hai_viec}" if hai_viec else "")

print("\n▸ Mỗi lớp trong CSS được HTML dùng tới")
trong_css = set(re.findall(r'(?<![\w-])\.([a-z][\w-]*)', CSS_SACH))
thua = sorted(trong_css - trong_html - JS_GAN)
kiem(f"{len(trong_css)} lớp", not thua,
     f"— CSS tạo luật mà HTML không dùng: {thua}" if thua else "")

# ================= 4. Bộ chọn trong JS phải tìm thấy =================
# Đổi tên một lớp mà quên sửa JS thì trang vẫn mở, chỉ là bấm không ăn — thứ hỏng
# lặng nhất trong cả tệp này.
print("\n▸ Mỗi `querySelector` trong JS bắt được thứ gì đó trong HTML")
hut = []
bo_chon = set(re.findall(r"querySelector(?:All)?\('([^']+)'\)", JS))
for bc in bo_chon:
    # ⚠ SOI MỌI TỪ, không phải mỗi từ cuối. `'.sau-ray button'` có từ cuối là
    # `button` — một tên thẻ, lúc nào chẳng có — nên bản đầu đổi `.sau-ray` thành
    # một lớp không tồn tại mà bài vẫn xanh. Cái tên bị đổi nằm ở TỪ ĐẦU.
    for tu in bc.replace(',', ' ').split():
        for lop in re.findall(r'\.([\w-]+)', tu):
            if lop not in trong_html:
                hut.append(f"{bc} → .{lop}")
        for ma_id in re.findall(r'#([\w-]+)', tu):
            if f'id="{ma_id}"' not in HTML:
                hut.append(f"{bc} → #{ma_id}")
        for tt in re.findall(r'\[([\w-]+)', tu):
            if tt not in HTML:
                hut.append(f"{bc} → [{tt}]")
kiem(f"{len(bo_chon)} bộ chọn", not hut, f"— không bắt được: {hut}" if hut else "")

# ================= 5. Con số trang khoe = con số APP đếm =================
# ⚠ MỘT KHO DUY NHẤT. Trang viết «26 levels · 66 stars · 164 quantities» thì ba con
# số ấy phải là ba con số app đếm được, không phải ba con số gõ tay cách chỗ sinh ra
# chúng bốn thư mục. Thêm một màn vào `hanh_trinh.MAN` là trang nói dối ngay.
print("\n▸ Con số trên trang = con số app đếm được")
from cat_studio import hanh_trinh, hoi, ngon_ngu  # noqa: E402
ngon_ngu.dat("en")
d = hanh_trinh.tu_dien()
so_man, so_sao = len(d["man"]), d["sao_toi_da"]
so_dai_luong = len(hoi.tu_dien()["kho"])

# ⚠ ĐÒI MỌI CHỖ, không phải «có một chỗ đúng». Bản đầu hỏi «chuỗi "26 levels" có
# trong trang không» — trang nói «26 levels» ở khúc này và «30 levels» ở khúc kia thì
# nó vẫn xanh, vì chỗ đúng vẫn còn. Mà lệch nhau giữa hai khúc mới đúng là cái sẽ xảy
# ra: sửa một chỗ, quên chỗ còn lại.
def moi_con_so(danh_tu, that):
    co = [int(x) for x in re.findall(r'(\d+)\s+' + danh_tu, HTML)]
    return co, [x for x in co if x != that]


for danh_tu, that in (("levels", so_man), ("stars", so_sao),
                      ("quantities", so_dai_luong)):
    co, lech = moi_con_so(danh_tu, that)
    kiem(f"«{danh_tu}» — app đếm {that}", bool(co) and not lech,
         f"— trang nói {co}" if lech else (f"— {len(co)} chỗ, đều đúng" if co
                                           else "— TRANG KHÔNG NÓI CHỖ NÀO"))

# TÊN TỆP BẢN CÀI mang số hiệu bản — một con số gõ tay nữa, cách `core.PHIEN_BAN`
# bốn thư mục. Lên 0.3 mà quên sửa trang là nút Tải trỏ vào một tệp không còn tồn tại.
from cat_studio import core  # noqa: E402
ten_tep = re.findall(r'Cat_Studio-([\d.]+)-windows-x64', HTML)
kiem(f"tên bản cài mang số hiệu {core.PHIEN_BAN}",
     bool(ten_tep) and all(v == core.PHIEN_BAN for v in ten_tep),
     f"— trang nói {sorted(set(ten_tep))}" if ten_tep else "— trang không nhắc tệp nào")

# CỠ BẢN CÀI. Trang khoe «13.7 MB» — một lời hứa cụ thể, và nó đổi mỗi lần dựng lại:
# dựng nhầm bằng Python hệ thống thay vì `.venv` là nhảy lên 18.0 MB trong một lượt.
#
# ⚠ KHÔNG ĐƯỢC KÊU «✔» KHI KHÔNG SOÁT GÌ. `dist/` bị `.gitignore` chặn nên ở một bản
# sao mới tinh thì không có tệp nào mà đo — mà một dấu ✔ cho một phép so không hề
# chạy đúng là cái bệnh «hàng rào khẳng định cái sai» của dự án này. Nên ở đây in ra
# dấu «○ chưa soát được», không tính đúng cũng không tính sai.
cho_khoe = re.findall(r'<b>([\d.]+)&nbsp;MB</b>', HTML)
ban_cai = os.path.join(GOC, "dist",
                       f"Cat_Studio-{core.PHIEN_BAN}-windows-x64-setup.exe")
if not cho_khoe:
    print("  ○ trang không khoe cỡ bản cài — không có gì phải soát")
elif not os.path.isfile(ban_cai):
    print(f"  ○ trang khoe {cho_khoe[0]} MB — CHƯA SOÁT ĐƯỢC, chưa dựng bản cài "
          f"({os.path.relpath(ban_cai, GOC)})")
else:
    # MB THẬP PHÂN (1e6), đúng công thức `tools/dong_goi.py` in ra và đúng cách
    # GitHub ghi cỡ tệp đính kèm. Lấy MiB (1024²) thì cùng một tệp ra 13.1 thay vì
    # 13.7 — hàng rào đỏ oan, mà trang thì không sai chữ nào.
    that_mb = os.path.getsize(ban_cai) / 1e6
    kiem(f"cỡ bản cài — trang khoe {cho_khoe[0]} MB",
         all(abs(float(x) - that_mb) < 0.1 for x in cho_khoe),
         f"— tệp thật {that_mb:.1f} MB")

# Và từng màn một: đủ 26 cái tên, đúng chữ app bày ra.
sot = [m["ten"] for m in d["man"] if m["ten"] not in HTML]
kiem("đủ tên 26 màn trên trang", not sot, f"— sót: {sot}" if sot else "")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
