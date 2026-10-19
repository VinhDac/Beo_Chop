"""CỬA SƠ ĐỒ của `api.py` — một cửa soát duy nhất, và ba tầng lưu.

Giao diện gọi `soat` sau MỖI thay đổi rồi vẽ lại cái nhận về: nó không tự tính số thứ
tự, không tự ghép chữ trên thẻ, không tự soát luật nào. Bài này canh đúng lời hứa ấy,
cộng ba chỗ việc-đang-dở có thể bốc hơi:

  · bản nháp  — việc dở của cửa sổ, kể cả Strategy CHƯA TỪNG lưu
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

from cat_studio import core, lam, luu_tru  # noqa: E402
# ⚠ BÀI NÀY CHỐT TIẾNG VIỆT. Nó soát CHỮ do Python dựng — mặt khối, bảng Vấn đề,
# câu lỗi — mà app nay MẶC ĐỊNH TIẾNG ANH. Không chốt thì nó đọc bản dịch và mọi
# câu khẳng định dưới đây thành vô nghĩa. Bản gốc tiếng Việt cũng là KHOÁ của bảng
# dịch, nên khẳng định bằng tiếng Việt là khẳng định đúng thứ lõi sinh ra.
# Bản tiếng Anh có bài canh riêng: `test_ngon_ngu.py`.
from cat_studio import ngon_ngu  # noqa: E402
ngon_ngu.dat("vi")


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
# ⚠ CHỐT LẠI SAU KHI DỰNG `Api`. `Api.__init__` tự chốt ngôn ngữ theo cài đặt — đúng
# việc của nó, nhưng nó ĐÈ mất lời chốt ở đầu file, nên ba câu khẳng định tiếng Việt
# dưới đây đã đỏ thật. Dòng ở đầu file vẫn cần: mấy lời gọi `core` không qua `Api`.
ngon_ngu.dat("vi")


def so_do():
    """Sơ đồ nhỏ: Bắt đầu → Nhóm → Quay về (khép vòng)."""
    bd = val(A.khoi_moi("start"))["step"]
    g = val(A.khoi_moi("group"))["step"]
    # ⚠ LOẠI THẬT, không bịa. Bản trước để `{"type": "mua"}` — một chữ không từ điển
    # nào nhận — và nó qua tuốt vì hồi ấy chưa ai soát loại khối. Mẫu thử mang một
    # loại chết thì mọi phép dựng trên nó đang canh một sơ đồ người dùng không bao
    # giờ vẽ ra được.
    g["actions"] = [{"type": lam.LAM_GHI_CHU, "cau": "x"}]
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
     r["the"][steps[1]["id"]]["lines"][0]["text"].startswith("Debug"),
     f"— {r['the'][steps[1]['id']]['lines'][0]['text']!r}")
kiem("có bảng vòng", r["vong"] == {steps[2]["id"]: [steps[0]["id"], None]})
kiem("sơ đồ đúng thì không lỗi", not r["van_de"], f"— {[p[chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)][:40] for p in r['van_de']]}")
kiem("trả lại edges đã dọn", len(r["edges"]) == 2)
# ⚠ CỖ MÁY ĐI CÙNG CỬA NÀY. Viên thuốc góc phải canvas đọc nó; quên gửi thì viên
# thuốc trống trơn mà không gì kêu — giao diện chỉ thấy một khoá thiếu và vẽ rỗng.
kiem("có hồ sơ cỗ máy", isinstance(r.get("co_may"), dict) and "chia_von" in r["co_may"],
     f"— {r.get('co_may')}")
kiem("có tóm tắt cho viên thuốc", isinstance(r.get("tom_tat_co_may"), list),
     f"— {r.get('tom_tat_co_may')}")
kiem("sơ đồ chưa đặt gì thì tóm tắt rỗng", r["tom_tat_co_may"] == [],
     f"— {r['tom_tat_co_may']}")
_r3 = val(A.soat(steps, edges, {"moc_so_sanh": "SPY"}))
kiem("gửi hồ sơ vào thì tóm tắt kể ra", _r3["tom_tat_co_may"] == ["Mốc so sánh SPY"],
     f"— {_r3['tom_tat_co_may']}")

# ================= Loại khối LẠ =================
# ⚠ BA CHỖ CÙNG IM MỘT LÚC khi mở một sơ đồ lưu từ bộ khối CŨ (D-12: `check_cond`,
# `dat_co`, `vao_lenh`…): bấm đúp vào khối không ra gì (`coHopSua` hỏi ba từ điển,
# không ai nhận), bảng Vấn đề sạch trơn (`soat_khoi_hoi` và `soat_khoi_lam` đều trả
# rỗng cho loại chúng không sở hữu, nên khối rơi qua KẼ GIỮA hai phép), và Build ra
# một file toàn `pass` chạy xong 0 lệnh. Ba triệu chứng, một bệnh, không ai gọi tên.
#     Đã gặp thật: `mẫu RSI` — chính cái mẫu đầu tiên người dùng mở ra.
print("\n▸ Khối mang loại KHÔNG từ điển nào nhận")
_la = val(A.khoi_moi("action"))["step"]
_la["type"] = "check_cond"                       # loại của bộ khối đã chết
_r_la = val(A.soat(steps + [_la], edges))
kiem("bảng Vấn đề gọi tên loại ấy",
     any(v["severity"] == "error" and "check_cond" in v["message"]
         for v in _r_la["van_de"]),
     f"— {[v[chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)][:60] for v in _r_la['van_de']]}")
kiem("và nói rõ sơ đồ lưu từ bộ khối CŨ",
     any("bộ khối CŨ" in v["message"] for v in _r_la["van_de"]))
# Và ĐỪNG kêu oan: mọi loại đang sống phải im.
_sach = val(A.soat(steps, edges))
kiem("sơ đồ toàn loại đang sống thì KHÔNG kêu",
     not any("từ điển nào" in v["message"] for v in _sach["van_de"]),
     f"— {[v[chr(109)+chr(101)+chr(115)+chr(115)+chr(97)+chr(103)+chr(101)][:50] for v in _sach['van_de']]}")

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
print("\n▸ Bản nháp — việc dở của Strategy CHƯA TỪNG lưu")
val(A.luu_ban_nhap("", steps, edges))
d = val(A.doc_ban_nhap())
kiem("đọc lại được", d and len(d["steps"]) == 3)
kiem("không đẻ ra file Strategy nào", luu_tru.liet_ke_strategy() == [])

print("\n▸ Lưu thật")
val(A.luu_strategy("máy thử", steps, edges))
kiem("có trong kho", "máy thử" in luu_tru.liet_ke_strategy())
mo = val(A.mo_strategy("máy thử"))
kiem("mở lại đủ khối", len(mo["steps"]) == 3)
kiem("mở lại đủ dây", len(mo["edges"]) == 2)

print("\n▸ Bản tự lưu chỉ đẻ ra khi nội dung THẬT SỰ khác")
kiem("không sửa gì → không đẻ file", val(A.tu_luu_strategy("máy thử", steps, edges)) is None)
steps[1]["actions"].append({"type": "dat_sl"})
tl = val(A.tu_luu_strategy("máy thử", steps, edges))
kiem("sửa rồi → có bản tự lưu", tl and tl["ten"] == "máy thử (tự lưu)")
kiem("nằm cạnh bản gốc", "máy thử (tự lưu)" in luu_tru.liet_ke_strategy())

print("\n▸ Lưu thật xong thì bản tự lưu phải BIẾN MẤT")
val(A.luu_strategy("máy thử", steps, edges))
kiem("bản tự lưu đã xoá", "máy thử (tự lưu)" not in luu_tru.liet_ke_strategy())
kiem("bản gốc còn nguyên", "máy thử" in luu_tru.liet_ke_strategy())

print("\n▸ Tên bản tự lưu không chồng đuôi")
kiem("đã là bản tự lưu thì giữ nguyên",
     luu_tru.ten_tu_luu("x (tự lưu)") == "x (tự lưu)")
kiem("lần về tên gốc", luu_tru.ten_goc_cua("x (tự lưu)") == "x")

# ================= 4. Khoá «cách nhìn» đi trọn vòng =================
print("\n▸ pos / màu / hạt nhân sống sót qua lưu → mở")
steps[1].update({"pos": [7.5, -2], "mau": "#ffa657",
                 "hat_nhan": {"id": "hn1", "ten": "Vòng 1", "x": 3, "y": 4}})
val(A.luu_strategy("máy hn", steps, edges))
g2 = val(A.mo_strategy("máy hn"))["steps"][1]
kiem("pos còn", g2.get("pos") == [7.5, -2.0])
kiem("màu còn", g2.get("mau") == "#ffa657")
kiem("hạt nhân còn", (g2.get("hat_nhan") or {}).get("ten") == "Vòng 1")

# ================= 5. Kho Strategy =================
print("\n▸ Kho nói ra dòng nào là BẢN TỰ LƯU")
val(A.luu_strategy("máy kho", steps, edges))
steps[1]["actions"].append({"type": "them"})
val(A.tu_luu_strategy("máy kho", steps, edges))
ds = val(A.ds_strategy())
kiem("mỗi dòng có nhãn tuLuu", all("tuLuu" in m for m in ds))
kiem("bản gốc không phải tự lưu",
     any(m["ten"] == "máy kho" and not m["tuLuu"] for m in ds))
kiem("bản tự lưu có nhãn",
     any(m["ten"] == "máy kho (tự lưu)" and m["tuLuu"] for m in ds),
     "— lẫn vào bản gốc là mở nhầm, lưu nhầm")

print("\n▸ Đổi tên")
r = A.doi_ten_strategy("máy kho", "máy mới")
kiem("đổi được", r["ok"] and r["value"]["ten"] == "máy mới")
ten_ds = [m["ten"] for m in val(A.ds_strategy())]
kiem("tên cũ biến mất", "máy kho" not in ten_ds)
kiem("tên mới có mặt", "máy mới" in ten_ds)
kiem("bản tự lưu của tên CŨ bị dọn theo", "máy kho (tự lưu)" not in ten_ds,
     "— không để lại file mồ côi mang tên một Strategy không còn")
kiem("nội dung còn nguyên", len(val(A.mo_strategy("máy mới"))["steps"]) == 3)

print("\n▸ Không được ĐÈ bản đã có")
val(A.luu_strategy("máy B", steps, edges))
r = A.doi_ten_strategy("máy B", "máy mới")
kiem("đổi sang tên đã có → lỗi, không đè", not r["ok"])
kiem("câu lỗi nói rõ phải chọn tên khác", "chọn tên khác" in (r.get("error") or ""))
kiem("bản cũ vẫn còn", "máy B" in [m["ten"] for m in val(A.ds_strategy())])

print("\n▸ Nhân bản — id phải MỚI")
r = val(A.nhan_ban_strategy("máy mới", "máy chép"))
kiem("chép được", r["ten"] == "máy chép")
goc = val(A.mo_strategy("máy mới"))
chep = val(A.mo_strategy("máy chép"))
kiem("đủ khối", len(chep["steps"]) == len(goc["steps"]))
id_goc = {s["id"] for s in goc["steps"]}
id_chep = {s["id"] for s in chep["steps"]}
kiem("KHÔNG trùng id nào với bản gốc", not (id_goc & id_chep),
     "— trùng id thì dán khối bản này sang bản kia là một cái biến mất khỏi sơ đồ")
kiem("dây chép theo", len(chep["edges"]) == len(goc["edges"]))
r = A.nhan_ban_strategy("máy mới", "máy chép")
kiem("nhân bản trùng tên → lỗi, không đè", not r["ok"])

shutil.rmtree(TAM, ignore_errors=True)
print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
