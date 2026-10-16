"""CỬA SƠ ĐỒ của `api.py` — một cửa soát duy nhất, và ba tầng lưu.

Giao diện gọi `soat` sau MỖI thay đổi rồi vẽ lại cái nhận về: nó không tự tính số thứ
tự, không tự ghép chữ trên thẻ, không tự soát luật nào. Bài này canh đúng lời hứa ấy,
cộng ba chỗ việc-đang-dở có thể bốc hơi:

  · bản nháp  — việc dở của cửa sổ, kể cả cỗ máy CHƯA TỪNG lưu
  · bản tự lưu — chỉ đẻ ra khi nội dung THẬT SỰ khác bản trên đĩa
  · lưu thật  — xong là bản tự lưu phải biến mất, không để hai bản cạnh nhau

Ghi vào một thư mục TẠM, không đụng `du_lieu/` thật.
"""
import io
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import core, luu_tru  # noqa: E402

TAM = tempfile.mkdtemp(prefix="catso-")
luu_tru._GOC_MA_NGUON = TAM          # mọi thứ app ghi ra sẽ rơi vào đây

from cat_studio import api  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def val(r):
    assert r["ok"], r.get("error")
    return r["value"]


A = api.Api()


def so_do():
    """Sơ đồ nhỏ: Bắt đầu → Nhóm → Quay về (khép vòng)."""
    bd = val(A.khoi_moi("start"))["step"]
    g = val(A.khoi_moi("group"))["step"]
    g["actions"] = [{"type": "mua"}]
    qv = val(A.khoi_moi("action", core.QUAY_VE))["step"]
    qv["ve"] = bd["id"]
    return [bd, g, qv], [{"from": bd["id"], "to": g["id"]},
                         {"from": g["id"], "to": qv["id"]}]


# ================= 1. Một cửa soát =================
print("\n▸ `soat` trả đủ thứ giao diện cần, trong MỘT lượt")
steps, edges = so_do()
r = val(A.soat(steps, edges))
kiem("có số thứ tự", r["thu_tu"] == {steps[0]["id"]: "1", steps[1]["id"]: "2",
                                     steps[2]["id"]: "3"})
kiem("có thẻ cho MỌI khối", set(r["the"]) == {s["id"] for s in steps})
kiem("thẻ do Python dựng chữ",
     r["the"][steps[1]["id"]]["lines"][0]["text"].startswith("mua"))
kiem("có bảng vòng", r["vong"] == {steps[2]["id"]: [steps[0]["id"], None]})
kiem("sơ đồ đúng thì không lỗi", not r["van_de"], f"— {[p['message'][:40] for p in r['van_de']]}")
kiem("trả lại edges đã dọn", len(r["edges"]) == 2)

print("\n▸ Khối không ai dẫn tới thì KHÔNG có số")
le = val(A.khoi_moi("action"))["step"]
r2 = val(A.soat(steps + [le], edges))
kiem("khối lẻ không có số", le["id"] not in r2["thu_tu"])
kiem("và bảng Vấn đề nói ra",
     any("không bao giờ chạy tới" in p["message"] for p in r2["van_de"]))

# ================= 2. Nhân bản =================
print("\n▸ Nhân bản không được dính vào bản gốc")
n = val(A.nhan_ban(steps, edges))
kiem("id đều mới", not ({s["id"] for s in n["steps"]} & {s["id"] for s in steps}))
kiem("dây chép theo", len(n["edges"]) == 2)
kiem("Quay về trỏ sang bản CHÉP",
     n["steps"][2]["ve"] == n["steps"][0]["id"])
n2 = val(A.nhan_ban([steps[2]], []))
kiem("chép mỗi khối Quay về → đích để TRỐNG", n2["steps"][0]["ve"] == "",
     "— bản dán không được nhảy về chỗ của bản gốc")

# ================= 3. Ba tầng lưu =================
print("\n▸ Bản nháp — việc dở của cỗ máy CHƯA TỪNG lưu")
val(A.luu_ban_nhap("", steps, edges))
d = val(A.doc_ban_nhap())
kiem("đọc lại được", d and len(d["steps"]) == 3)
kiem("không đẻ ra file cỗ máy nào", luu_tru.liet_ke_co_may() == [])

print("\n▸ Lưu thật")
val(A.luu_co_may("máy thử", steps, edges))
kiem("có trong kho", "máy thử" in luu_tru.liet_ke_co_may())
mo = val(A.mo_co_may("máy thử"))
kiem("mở lại đủ khối", len(mo["steps"]) == 3)
kiem("mở lại đủ dây", len(mo["edges"]) == 2)

print("\n▸ Bản tự lưu chỉ đẻ ra khi nội dung THẬT SỰ khác")
kiem("không sửa gì → không đẻ file", val(A.tu_luu_co_may("máy thử", steps, edges)) is None)
steps[1]["actions"].append({"type": "dat_sl"})
tl = val(A.tu_luu_co_may("máy thử", steps, edges))
kiem("sửa rồi → có bản tự lưu", tl and tl["ten"] == "máy thử (tự lưu)")
kiem("nằm cạnh bản gốc", "máy thử (tự lưu)" in luu_tru.liet_ke_co_may())

print("\n▸ Lưu thật xong thì bản tự lưu phải BIẾN MẤT")
val(A.luu_co_may("máy thử", steps, edges))
kiem("bản tự lưu đã xoá", "máy thử (tự lưu)" not in luu_tru.liet_ke_co_may())
kiem("bản gốc còn nguyên", "máy thử" in luu_tru.liet_ke_co_may())

print("\n▸ Tên bản tự lưu không chồng đuôi")
kiem("đã là bản tự lưu thì giữ nguyên",
     luu_tru.ten_tu_luu("x (tự lưu)") == "x (tự lưu)")
kiem("lần về tên gốc", luu_tru.ten_goc_cua("x (tự lưu)") == "x")

# ================= 4. Khoá «cách nhìn» đi trọn vòng =================
print("\n▸ pos / màu / hạt nhân sống sót qua lưu → mở")
steps[1].update({"pos": [7.5, -2], "mau": "#ffa657",
                 "hat_nhan": {"id": "hn1", "ten": "Vòng 1", "x": 3, "y": 4}})
val(A.luu_co_may("máy hn", steps, edges))
g2 = val(A.mo_co_may("máy hn"))["steps"][1]
kiem("pos còn", g2.get("pos") == [7.5, -2.0])
kiem("màu còn", g2.get("mau") == "#ffa657")
kiem("hạt nhân còn", (g2.get("hat_nhan") or {}).get("ten") == "Vòng 1")

shutil.rmtree(TAM, ignore_errors=True)
print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
