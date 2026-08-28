"""CSS HỎNG LẶNG — hai chiều: biến không tồn tại, và lớp không có luật.

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

#: Biến do JS đặt trên chính phần tử lúc chạy — xem `components/StepNode.tsx`.
DAT_LUC_CHAY = {"--mau-khoi"}

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

print("\n▸ Mọi `className` phải có một luật CSS")
# CHIỀU NGƯỢC LẠI của phép trên, và nó hỏng lặng y hệt: viết `className="nut do"` mà
# không có luật `.do` nào thì nút hiện ra bình thường — chỉ là không đỏ. Không lỗi,
# không cảnh báo, và không ai phát hiện cho tới khi nhìn đúng cái nút đó.
#
# Đã bắt được ba ca thật ngay lần đầu chạy:
#   · `.nut.do`    nút ● Live — cái nút "tiêu tiền thật" trông y hệt mọi nút khác, đúng
#                  thứ mà chú thích ngay cạnh nó bảo là KHÔNG được phép;
#   · `.chu-dan.canh`  mọi lời cảnh báo hiện ra xám nhạt như chú thích thường;
#   · `.cd-rong`   chỗ trống có lời giải thích, không có luật nào.
#
# HAI THỨ PHẢI LỌC RA, và cả hai đều sinh báo giả — mà một bài kiểm báo giả thì sớm
# muộn bị tắt đi, nên phải lọc cho sạch:
#
#   · VẾ PHẢI CỦA PHÉP SO. `className={'tab' + (tab === 'chung' ? ' dang' : '')}` có ba
#     chuỗi, nhưng `'chung'` là một GIÁ TRỊ đem ra so, không phải tên lớp. Bỏ hẳn cụm
#     `=== '…'` trước khi moi.
#   · TIỀN TỐ GHÉP LÚC CHẠY. `'dau mau-' + mau` cho ra `mau-`, một cái tên chưa hoàn
#     chỉnh. Nhận ra bằng dấu `-` ở cuối.
#
# Sau hai phép lọc đó thì MỌI chuỗi còn lại trong `className` đều là tên lớp thật, kể
# cả hai nhánh của một tam nguyên (`… ? 'loi' : 'canh-bao'`) — nên bài kiểm không bỏ
# sót nhánh nào.
VE_PHAI_PHEP_SO = re.compile(r"[=!]==?\s*[\"'][^\"']*[\"']")
LOP_GHEP = re.compile(r"className=[\"']([^\"'{}]+)[\"']")
tsx = []
for goc, _, ds in os.walk(CSS):
    tsx += [os.path.join(goc, t) for t in ds if t.endswith(".tsx")]

co_luat = set(re.findall(r"\.([a-zA-Z][\w-]*)", bo_chu_thich(theme + app)))
dang_dung = set()
for duong in tsx:
    with io.open(duong, encoding="utf-8") as f:
        noi_dung = f.read()
    for cum in LOP_GHEP.findall(noi_dung):
        dang_dung |= set(cum.split())
    # `className={'hop' + (x ? ' da-ghim' : '')}` — moi từng chuỗi con trong biểu thức.
    for cum in re.findall(r"className=\{([^}]*)\}", noi_dung):
        for chuoi in re.findall(r"[\"']([^\"'{}]*)[\"']", VE_PHAI_PHEP_SO.sub(" ", cum)):
            dang_dung |= {x for x in chuoi.split() if x and not x.endswith("-")}

# React Flow tự vẽ phần của nó và mang CSS riêng — không phải việc của `app.css`.
thieu = sorted(x for x in dang_dung - co_luat if not x.startswith("react-flow"))
kiem("mọi lớp đang dùng đều có luật", not thieu, f"— {thieu}" if thieu else "")

# ⚠ HAI MỤC ĐÃ ĐI ở đợt 4, cùng đám CSS chúng canh:
#
#   ▸ Menu ⚙ phải có nền ĐẶC   — menu tham số của toán hạng: nền đặc (nền trong là
#     chữ dưới xuyên qua), và phải LẬT sang trái khi mở ở vế phải, mũi tên lật theo,
#     nếu không nó trỏ vào chỗ trống.
#   ▸ Ô lưới không tự đặt bề rộng RIÊNG — `.dong-dk` phải là LƯỚI cột cố định chứ
#     không phải flex-wrap, để bốn năm điều kiện trong một cổng quét dọc được.
#
# Luật thứ hai đã chép vào chính chỗ CSS bị cắt (`app.css`), để lần dựng lại đọc thấy.
#
# Mục CÒN LẠI mới là mục quan trọng nhất, và nó không dính từ vựng: `var(--khong-ton-tai)`
# hỏng LẶNG — không lỗi biên dịch, `tsc` sạch, `vite build` sạch, chỉ có nhìn mới thấy.
# Nó đã bắt được hai ca thật (`--panel`, `--line`).


print(f"\n{'─' * 60}\n  {dung} đúng · {sai} sai\n{'─' * 60}")
sys.exit(1 if sai else 0)
