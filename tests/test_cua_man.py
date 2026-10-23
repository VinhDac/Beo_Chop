"""CỬA MÀN — chơi xong một màn thì màn kế phải mở ra.

Bài này sinh ra từ một lỗi đã ship: **chơi hết Khúc dạo đầu mà màn 01 vẫn khoá.**

Màn 00 khai `khong_cham` (nó dựng chính con boss, nên không có gì để chấm), nên
`cham_man` trả về `{khong_cham: True}` rồi đi luôn — sổ điểm KHÔNG có lấy một dòng.
Mà bản đồ lại hỏi sổ điểm xem màn nào đã qua. Không dòng nào → không màn nào đã qua →
25 màn còn lại khoá VĨNH VIỄN, không có đường nào gỡ được từ trong app.

Không bài nào bắt được, vì không bài nào đi hết một vòng: ghi sổ ở `luat_choi`, luật
mở ở `hanh_trinh`, còn chỗ quên ghi ở `api`. Mỗi hộp tự nó đều đúng.

Nên bài này đi ĐÚNG ĐƯỜNG NGƯỜI CHƠI ĐI, qua cửa `api` thật, và hỏi bản đồ thật.
Ghi vào thư mục TẠM, không đụng `du_lieu/` thật.
"""
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import luu_tru  # noqa: E402

TAM = tempfile.mkdtemp(prefix="catcua-")
luu_tru._GOC_MA_NGUON = TAM

from cat_studio import api, hanh_trinh, luat_choi  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def ban_do():
    r = A.hanh_trinh()
    assert r["ok"], r.get("error")
    return {m["ma"]: m for m in r["value"]["man"]}


A = api.Api()

# ================= 1. Lúc mới tinh =================
print("\n▸ Sổ trắng: đúng MỘT màn mở")
bd = ban_do()
mo = [m for m in bd.values() if not m["khoa"]]
kiem("chỉ màn đầu mở", [m["ma"] for m in mo] == [hanh_trinh.MAN[0]["ma"]],
     f"— đang mở: {[m['ma'] for m in mo]}")
kiem("màn 01 khoá", bd["m01"]["khoa"])

# ================= 2. Màn KHÔNG CHẤM vẫn phải mở được màn kế =================
# Đây là chỗ lỗi đã nằm. Màn 00 không chấm, nên nó là màn DỄ bị quên ghi sổ nhất,
# mà nó lại đứng chắn ngay cửa vào cả hành trình.
print("\n▸ Chơi xong Khúc dạo đầu (màn KHÔNG chấm)")
m00 = hanh_trinh.MAN[0]
kiem("màn đầu đúng là màn không chấm", bool(m00.get("khong_cham")),
     "— nếu màn đầu đổi thành màn có chấm thì bài này phải viết lại")

# Gọi ĐÚNG cửa giao diện gọi khi người chơi bấm «Chấm».
r = A.cham_man(m00["ma"], "khong-co-luot-nao", steps=[])
kiem("cửa chấm nhận", r["ok"], f"— {r.get('error')}")
kiem("và nói rõ là màn không chấm", (r.get("value") or {}).get("khong_cham") is True)

bd = ban_do()
kiem("màn 00 đánh dấu XONG", bd[m00["ma"]]["xong"],
     "— bản đồ không biết thì nó khoá màn kế mãi mãi")
kiem("➜ MÀN 01 MỞ RA", not bd["m01"]["khoa"],
     "— đây chính là lỗi đã ship: chơi hết màn 0 mà không đi tiếp được")
kiem("«bạn đang ở đây» nhảy sang màn 01", A.hanh_trinh()["value"]["dang_o"] == "m01")
kiem("nhưng KHÔNG cho sao nào", bd[m00["ma"]]["sao"] == 0,
     "— không chấm thì không có sao, chỉ có «đã qua»")
kiem("màn 02 vẫn khoá", bd["m02"]["khoa"], "— mở từng bậc, không mở toang")

# ================= 3. Đồ nghề của màn 01 cũng phải mở theo =================
# `da_mo` là CÔNG THỨC THỨ HAI cùng hỏi «màn nào đã qua». Hai công thức thì hôm nào
# lệch nhau: bản đồ mở màn 01 mà Kho vẫn khoá đúng mấy đại lượng màn 01 cần.
print("\n▸ Kho mở theo cùng một nhịp với bản đồ")
khoa_m01 = set(hanh_trinh.MAN[1].get("mo") or ())
mo_tu_kho = hanh_trinh.da_mo(luat_choi.doc_so()["man"])
kiem("khoá của màn 01 đã mở trong Kho", khoa_m01 <= mo_tu_kho,
     f"— còn thiếu: {sorted(khoa_m01 - mo_tu_kho)}")
khoa_m02 = set(hanh_trinh.MAN[2].get("mo") or ()) - khoa_m01 - set(m00.get("mo") or ())
if khoa_m02:
    kiem("đồ của màn 02 CHƯA mở", not (khoa_m02 & mo_tu_kho),
         f"— lọt ra: {sorted(khoa_m02 & mo_tu_kho)}")

# ================= 4. Chơi lại không được lấy mất gì =================
print("\n▸ Chơi lại màn 00")
A.cham_man(m00["ma"], "khong-co-luot-nao", steps=[])
bd = ban_do()
kiem("màn 01 vẫn mở", not bd["m01"]["khoa"])
kiem("màn 00 vẫn xong", bd[m00["ma"]]["xong"])

# ================= 5. Dấu «đã qua» phải sống qua lưu/đọc =================
# Sổ điểm là MỘT TỆP JSON. Thêm một trường mà quên ghi xuống đĩa thì mở lại app là
# cả hành trình khoá lại từ đầu — đúng lỗi cũ, chỉ chậm hơn một lần khởi động.
print("\n▸ Đóng app, mở lại")
so = luat_choi.doc_so()
dong = so["man"].get(m00["ma"]) or {}
kiem("sổ trên đĩa có dòng màn 00", bool(dong))
kiem("và dòng ấy mang dấu «đã qua»", bool(dong.get("qua")))
kiem("đọc lại từ đĩa vẫn tính là đã qua",
     m00["ma"] in hanh_trinh.da_qua(so["man"]))

shutil.rmtree(TAM, ignore_errors=True)
print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
