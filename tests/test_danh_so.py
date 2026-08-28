"""Đánh số phân cấp, ghim số, và ba trường hợp "gặp lại khối đã có nhãn".

ĐÁNH SỐ: SỐ = đi được bao xa, CHỮ = đi nhánh nào.

    1
    2
    3
    4
    ├── 4A            <- cổng nhánh A
    │   ├── 4A.1
    │   ├── 4A.2
    │   │   ├── 4A.2A
    │   │   └── 4A.2B
    │   └── 4A.3
    └── 4B
        ├── 4B.1
        └── 4B.2
    5                 <- điểm gộp: mọi nhánh đều dẫn tới đây nên số về lại mức trên
    6

Bài này canh đúng ba chỗ Auto_Clicker làm sai (core.md §3.3):
  Bẫy 1 — cờ "có vòng lặp" bật cả khi đồ thị KHÔNG có vòng
  Bẫy 2 — vòng lặp nuốt mất khối bắt đầu -> mọi huy hiệu biến thành "–"
  Bẫy 3 — thông báo lỗi đánh số theo index danh sách chứ không theo huy hiệu

Không mở cửa sổ, không nối MT5 -> chạy được ở bất cứ đâu.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Console Windows mặc định cp1252, và khi stdout là PIPE thì Python cũng lấy bảng mã
# đó — in một dấu ✔ là chết ngay, bài test "hỏng" mà không có lấy một dòng lý do.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import core  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


# ---------------- tiện ích dựng sơ đồ ----------------
def cong(nguong, x, y, ten=None):
    """Khối HĐ lẻ "Kiểm tra điều kiện" — đây chính là cái cổng của một nhánh."""
    s = core.make_action_step({
        "type": core.CHECK_COND,
        "name": ten or f"ĐK {nguong}",
        "conditions": [{"trai": {"ten": "spread"}, "phep": "<",
                        "phai": {"value": nguong, "tinh": "tick"}}],
    })
    s["pos"] = [x, y]
    return s


def viec(ten, x, y):
    """Một khối KHÔNG phải cổng — dùng làm mắt xích thường trên chuỗi."""
    s = core.make_action_step({
        "type": core.SO_HANG, "dich": "lech", "phep": "+=",
        "luong": {"he_so": 1, "don_vi": "tick"}, "name": ten})
    s["pos"] = [x, y]
    return s


def noi_day(b, cap):
    return [{"from": b[x]["id"], "to": b[y]["id"]} for x, y in cap]


def nhan_cua(b, cap):
    """{tên biến: nhãn} — để so với sơ đồ mong đợi bằng mắt thường."""
    kq = core.flow_order(list(b.values()), noi_day(b, cap))
    nguoc = {v["id"]: k for k, v in b.items()}
    return {nguoc[s]: n for s, n in kq["order"].items()}, kq


def loi(steps, edges, sev=None):
    ds = core.validate_flow_graph(steps, edges)
    return [p for p in ds if sev is None or p["severity"] == sev]


def loi_hd_tab(a, tab):
    ra = []
    core.validate_actions([a], lambda m, i=None: ra.append(m), tab)
    return ra


# ================= 1. Đánh số phân cấp =================
print("\n▸ Đánh số phân cấp")
b = {t: viec(t, 0, 0) for t in ("1", "2", "3", "4", "5", "6")}
b["4A"] = cong(7, 300, 0)
b["4B"] = cong(8, 300, 400)
b["4A.1"] = viec("a1", 600, 0)
b["4A.2"] = viec("a2", 900, 0)
b["4A.2A"] = cong(9, 1200, -50)
b["4A.2B"] = cong(10, 1200, 150)
b["4A.3"] = viec("a3", 1500, 0)
b["4B.1"] = viec("b1", 600, 400)
b["4B.2"] = viec("b2", 900, 400)
CAP = [("1", "2"), ("2", "3"), ("3", "4"),
       ("4", "4A"), ("4", "4B"),
       ("4A", "4A.1"), ("4A.1", "4A.2"),
       ("4A.2", "4A.2A"), ("4A.2", "4A.2B"),
       ("4A.2A", "4A.3"), ("4A.2B", "4A.3"),
       ("4A.3", "5"), ("4B", "4B.1"), ("4B.1", "4B.2"), ("4B.2", "5"),
       ("5", "6")]
nhan, kq = nhan_cua(b, CAP)
lech = [f"{k}→{v}" for k, v in nhan.items() if k != v]
kiem("mọi khối mang đúng nhãn trong sơ đồ", not lech, f"— lệch: {lech or 'không'}")
kiem("điểm gộp kéo số về lại mức trên cùng", nhan.get("5") == "5" and nhan.get("6") == "6")
kiem("không khối nào bị bỏ sót", not kq["unreachable"])
kiem("không báo nhầm là có vòng lặp", kq["loop"] is False)

# nhánh không gộp lại -> đơn giản là không có số ở mức trên nữa
b2 = {"1": viec("1", 0, 200), "A": cong(7, 300, 0), "B": cong(8, 300, 400),
      "A1": viec("a", 600, 0), "B1": viec("b", 600, 400)}
CAP2 = [("1", "A"), ("1", "B"), ("A", "A1"), ("B", "B1")]
n2, _ = nhan_cua(b2, CAP2)
kiem("nhánh không gộp → mỗi nhánh tự kết thúc, không có số mức trên",
     n2 == {"1": "1", "A": "1A", "B": "1B", "A1": "1A.1", "B1": "1B.1"}, f"— {n2}")

# không có edges -> chuỗi thẳng như từ trước tới nay
bs = [viec("x", 0, 0), viec("y", 0, 0), viec("z", 0, 0)]
cu = core.flow_order(bs, core.default_edges(bs))
kiem("không rẽ nhánh thì vẫn là 1, 2, 3",
     sorted(cu["order"].values()) == ["1", "2", "3"], f"— {sorted(cu['order'].values())}")

# ================= 2. Ưu tiên nhánh lấy từ VỊ TRÍ =================
print("\n▸ Thứ tự ưu tiên nhánh")
n3, _ = nhan_cua(b2, CAP2)
kiem("cổng nằm TRÊN là nhánh A", n3["A"] == "1A" and n3["B"] == "1B")
b2["B"]["pos"] = [300, -300]                      # kéo cổng B lên trên cổng A
n4, _ = nhan_cua(b2, CAP2)
kiem("kéo cổng lên trên thì nhãn đổi ngay → ưu tiên không bao giờ là thứ ngầm",
     n4["B"] == "1A" and n4["A"] == "1B", f"— B={n4['B']}, A={n4['A']}")
b2["B"]["pos"] = [300, 400]

# ================= 3. Khối Bắt đầu =================
print("\n▸ Khối Bắt đầu")
bd = core.make_start_step()
bd["pos"] = [0, 200]
b3 = {"BD": bd, "A": cong(7, 300, 0), "B": cong(8, 300, 400),
      "A1": viec("a", 600, 0), "B1": viec("b", 600, 400)}
CAP3 = [("BD", "A"), ("BD", "B"), ("A", "A1"), ("B", "B1")]
n5, kq5 = nhan_cua(b3, CAP3)
kiem("khối Bắt đầu mang số 1, các nhánh là 1A/1B",
     n5 == {"BD": "1", "A": "1A", "B": "1B", "A1": "1A.1", "B1": "1B.1"}, f"— {n5}")

# Bẫy 2: vòng lặp nuốt mất điểm bắt đầu.
b4 = {"1": viec("1", 0, 0), "2": viec("2", 300, 0), "3": viec("3", 600, 0)}
kq6 = core.flow_order(list(b4.values()), noi_day(b4, [("1", "2"), ("2", "3"), ("3", "1")]))
kiem("KHÔNG có khối Bắt đầu + vòng khép kín → mất hết nhãn (đúng bệnh của bản cũ)",
     kq6["entry"] is None and not kq6["order"])

b5 = {"BD": core.make_start_step(), "1": viec("1", 300, 0),
      "2": viec("2", 600, 0), "3": viec("3", 900, 0)}
b5["BD"]["pos"] = [0, 0]
b5["1"]["ghim"] = True
n7, kq7 = nhan_cua(b5, [("BD", "1"), ("1", "2"), ("2", "3"), ("3", "1")])
kiem("CÓ khối Bắt đầu → vòng khép kín vẫn giữ đủ nhãn",
     n7 == {"BD": "1", "1": "2", "2": "3", "3": "4"}, f"— {n7}")

# khối Bắt đầu không được nhận đường vào
b6 = {"BD": core.make_start_step(), "1": viec("1", 300, 0)}
b6["BD"]["pos"] = [0, 0]
ds = loi(list(b6.values()), noi_day(b6, [("BD", "1"), ("1", "BD")]), "error")
kiem("nối ngược vào khối Bắt đầu → báo LỖI",
     any("Start" in p["message"] and "INCOMING" in p["message"] for p in ds),
     f"— {[p['message'][:60] for p in ds]}")

# ================= 4. GHIM SỐ =================
print("\n▸ Ghim số ⟲")
b7 = {"BD": core.make_start_step(), "1": viec("một", 300, 0),
      "2": viec("hai", 600, 0), "3": viec("ba", 900, 0)}
b7["BD"]["pos"] = [0, 0]
CAP7 = [("BD", "1"), ("1", "2"), ("2", "3"), ("3", "1")]

# chưa ghim -> cảnh báo, nhưng nhãn vẫn còn đủ
n8, kq8 = nhan_cua(b7, CAP7)
kiem("chưa ghim: nhãn vẫn đủ, nhưng ghi nhận là vòng CHƯA GHIM",
     n8 == {"BD": "1", "1": "2", "2": "3", "3": "4"} and len(kq8["vong_ho"]) == 1
     and not kq8["quay_lai"], f"— {n8}, vong_ho={len(kq8['vong_ho'])}")
w = loi(list(b7.values()), noi_day(b7, CAP7), "warning")
kiem("chưa ghim → cảnh báo có gợi ý bấm chuột phải → Pin number",
     any("Pin number" in p["message"] for p in w),
     f"— {[p['message'][:70] for p in w]}")

# ghim rồi -> hết cảnh báo, số cũ vẫn nguyên
b7["1"]["ghim"] = True
n9, kq9 = nhan_cua(b7, CAP7)
kiem("ghim rồi: SỐ CŨ VẪN HỢP LỆ, không đổi tí nào",
     n9 == n8, f"— {n9}")
kiem("ghim rồi: cạnh quay lại được ghi nhận, không còn là vòng hở",
     len(kq9["quay_lai"]) == 1 and not kq9["vong_ho"],
     f"— quay_lai={kq9['quay_lai']}, vong_ho={kq9['vong_ho']}")
w2 = loi(list(b7.values()), noi_day(b7, CAP7), "warning")
kiem("ghim rồi → KHÔNG còn cảnh báo vòng lặp nào",
     not any("LOOP" in p["message"] or "Pin number" in p["message"] for p in w2),
     f"— {[p['message'][:60] for p in w2]}")

# quay lại từ trong một nhánh
b8 = {"BD": core.make_start_step(), "M": viec("mua", 300, 200),
      "A": cong(7, 600, 0), "B": cong(8, 600, 400), "A1": viec("a", 900, 0)}
b8["BD"]["pos"] = [0, 200]
b8["M"]["ghim"] = True
CAP8 = [("BD", "M"), ("M", "A"), ("M", "B"), ("A", "A1"), ("B", "M")]
n10, kq10 = nhan_cua(b8, CAP8)
kiem("nhánh B quay về khối đã ghim → giữ nguyên số, không cảnh báo",
     n10.get("M") == "2" and not kq10["vong_ho"] and len(kq10["quay_lai"]) == 1,
     f"— {n10}")

# ================= 5. Bẫy 1 — dương tính giả =================
print("\n▸ Bẫy 1: nhánh chụm không đều KHÔNG phải vòng lặp")
# 1 rẽ 3 nhánh A,B,C; A và B cùng về M; C đi đường riêng.
# `diem_gop` cần khối chung cho CẢ BA nhánh -> không có -> B đụng M do A đánh nhãn.
# Auto_Clicker báo "VÒNG LẶP" ở đây. Đồ thị này KHÔNG có vòng nào.
b9 = {"1": viec("1", 0, 200), "A": cong(7, 300, 0), "B": cong(8, 300, 200),
      "C": viec("c", 300, 400), "M": viec("m", 600, 100), "Z": viec("z", 600, 400)}
CAP9 = [("1", "A"), ("1", "B"), ("1", "C"), ("A", "M"), ("B", "M"), ("C", "Z")]
n11, kq11 = nhan_cua(b9, CAP9)
kiem("DAG không vòng → loop phải là False (bản cũ trả True)",
     kq11["loop"] is False, f"— loop={kq11['loop']}")
kiem("nhận diện đúng là 'nhánh chụm không đều'",
     len(kq11["lech_nhanh"]) == 1 and not kq11["vong_ho"],
     f"— lech_nhanh={len(kq11['lech_nhanh'])}, vong_ho={len(kq11['vong_ho'])}")
# Chỉ xét cảnh báo GẮN VỚI MỘT KHỐI. Cảnh báo "chưa có khối Bắt đầu" (step=None)
# có nhắc chữ "vòng lặp" trong câu khuyên — đó là lời khuyên, không phải chẩn đoán sai.
w3 = [p for p in loi(list(b9.values()), noi_day(b9, CAP9), "warning") if p["step"]]
kiem("không cảnh báo nào GẮN VỚI KHỐI gọi đây là vòng lặp",
     not any("loop" in p["message"].lower() for p in w3),
     f"— {[p['message'][:70] for p in w3]}")

# ================= 6. Bẫy 3 — thông báo dùng nhãn =================
print("\n▸ Bẫy 3: thông báo lỗi dùng NHÃN, không dùng index")
b10 = {"BD": core.make_start_step(), "1": viec("1", 300, 0),
       "A": cong(7, 600, 0), "B": viec("mặc định", 600, 200),
       "C": viec("thừa", 600, 400)}
b10["BD"]["pos"] = [0, 200]
CAP10 = [("BD", "1"), ("1", "A"), ("1", "B"), ("1", "C")]
e10 = loi(list(b10.values()), noi_day(b10, CAP10), "error")
kiem("hai nhánh không cổng → báo lỗi",
     any("have no gate" in p["message"] for p in e10),
     f"— {[p['message'][:60] for p in e10]}")
kiem("thông báo có nhãn dạng [2] / [2A] chứ không phải \"Bước 3\"",
     any("[2]" in p["message"] for p in e10) and
     not any("Bước " in p["message"] for p in e10),
     f"— {[p['message'][:80] for p in e10]}")

# ================= 7. Luật rẽ nhánh =================
print("\n▸ Luật rẽ nhánh")
b11 = {"1": viec("1", 0, 200), "A": cong(7, 300, 0), "MD": viec("mặc định", 300, 400)}
kiem("nhánh mặc định xếp DƯỚI CÙNG → không lỗi",
     not loi(list(b11.values()), noi_day(b11, [("1", "A"), ("1", "MD")]), "error"))
b11["MD"]["pos"] = [300, -300]        # kéo nhánh mặc định lên trên
kiem("nhánh mặc định xếp TRÊN → báo lỗi",
     any("lowest" in p["message"]
         for p in loi(list(b11.values()), noi_day(b11, [("1", "A"), ("1", "MD")]), "error")))

b12 = {"1": viec("1", 0, 200), "A": cong(7, 300, 0), "A2": cong(7, 300, 400)}
# ⚠ "hai cổng TRÙNG điều kiện → cảnh báo" đã đi ở đợt 3: không còn điều kiện thì mọi
# cổng có vân tay rỗng, phép so sẽ tố cáo mọi cặp cổng trên cùng một ngã rẽ.

b13 = {"1": viec("1", 0, 0)}
kiem("đường nối trỏ về CHÍNH NÓ → lỗi",
     any("ITSELF" in p["message"]
         for p in loi(list(b13.values()), noi_day(b13, [("1", "1")]), "error")))

# ================= 8. Chuẩn hoá giữ cờ ghim =================
print("\n▸ Chuẩn hoá & nhân bản")
st = viec("x", 10, 20)
st["ghim"] = True
kiem("normalize_step giữ cờ ghim", core.normalize_step(st).get("ghim") is True)
kiem("normalize_step giữ pos", core.normalize_step(st).get("pos") == [10.0, 20.0])
moi, tra = core.clone_steps([st])
kiem("nhân bản KHÔNG chép cờ ghim (hai điểm quay lại là gần như chắc chắn sai ý)",
     "ghim" not in moi[0] and moi[0]["id"] != st["id"])
kiem("nhân bản trả bảng tra cũ→mới", tra.get(st["id"]) == moi[0]["id"])

d = core.new_process()
kiem("chiến lược mới có HAI sơ đồ, mỗi cái một khối Bắt đầu",
     set(core.TABS) <= set(d)
     and all(len(d[t]["steps"]) == 1 and core.is_start_step(d[t]["steps"][0])
             for t in core.TABS))

# ================= 8b. Chỉ còn HAI loại khối =================
print("\n▸ Bộ từ vựng khối")
kiem("chỉ còn 2 loại khối: Bắt đầu + Khối",
     set(core.KIND_LABELS) == {core.KIND_START, core.KIND_ACTION},
     f"— {sorted(core.KIND_LABELS)}")
kiem("lõi không còn biết Vòng theo dõi / Nhóm",
     not any(hasattr(core, t) for t in
             ("KIND_LOOP", "KIND_GROUP", "make_loop_step", "make_group_step",
              "has_actions", "is_loop_step", "is_group_step")))
kiem("khối kiểu cũ trong file cũ bị bỏ qua, không làm hỏng cả sơ đồ",
     core.normalize_step({"kind": "loop", "id": "sxxx", "actions": []}) is None)
kiem("template chỉ còn loại 'chiến lược', không lưu cụm khối rời",
     list(core.TEMPLATE_KINDS) == ["strategy"], f"— {list(core.TEMPLATE_KINDS)}")
kiem("đúng HAI động từ: hỏi, và góp một số hạng",
     core.ACTION_TYPES == [core.CHECK_COND, core.SO_HANG], f"— {core.ACTION_TYPES}")
kiem("lõi không còn biết Vào lệnh / Sửa lệnh — market maker không có lệnh RỜI",
     not any(hasattr(core, t)
             for t in ("VAO_LENH", "SUA_LENH", "TAB_ENTRY", "TAB_MANAGE")))

# ================= 8d. MỘT sơ đồ =================
print("\n▸ Một sơ đồ Báo giá")
# Ranh giới **Entry chỉ TẠO · Manage chỉ SỬA** từng là luật quan trọng nhất của app,
# và bốn phép kiểm nó từng nằm đúng chỗ này. Nó KHÔNG bị bỏ vì lười — nó mất ĐỐI
# TƯỢNG: market maker không "vào lệnh" rồi "quản lệnh" ở hai nhịp khác nhau, mỗi sự
# kiện phát biểu lại TOÀN BỘ báo giá. Một sơ đồ, một nhịp.
#
# Cơ chế `ACTION_TABS` thì giữ nguyên và vẫn được canh ở đây: ngày có sơ đồ thứ hai
# là nó chặn được ngay, không phải dựng lại từ đầu.
kiem("đúng MỘT sơ đồ", core.TABS == [core.TAB_BAO_GIA], f"— {core.TABS}")
kiem("cả hai động từ đều dùng được ở sơ đồ đó",
     all(set(core.ACTION_TABS[t]) == set(core.TABS) for t in core.ACTION_TYPES))
kiem("khối lạc sang sơ đồ không nhận nó → báo lỗi",
     any("belongs only to" in m for m in loi_hd_tab(
         {"type": core.SO_HANG, "dich": "lech", "phep": "+=",
          "luong": {"he_so": 1, "don_vi": "tick"}}, "so_do_chua_co")))

# ================= Ổ CẮM TRỐNG — năm mục cuối =================
#
# ~160 dòng đã đi ở đợt 3 cùng từ vựng bên `core.py`:
#
#   ▸ Hợp đồng chuẩn hoá   hai chữ ATR là HAI THỨ khác nhau (`atr` đo đệm ·
#                          `atr_zone` đo rủi ro), và KHÔNG cách tính nào theo pip /
#                          điểm / tiền — hợp đồng làm nên D_02
#   ▸ Phép so              dùng KÝ HIỆU `< ≤ > ≥ = ≠`, không dùng chữ
#   ▸ Mô tả hành động      câu do Python sinh phải đọc được, và phải phân biệt
#                          "ATR hiện tại" với "ATR vùng"
#   ▸ Soát hành động       thiếu SL · thiếu mốc neo · lệnh chờ neo giá hiện tại mà
#                          không đệm · chế độ cũ tự chuyển
#   ▸ Cơ chế so sánh       một cờ cho CẢ khối, không phải chip trên từng dòng
#
# Không phép nào còn đối tượng để kiểm. Đây là NỢ ĐỘ PHỦ khi từ vựng quay lại —
# ghi ở `tai_lieu/o_cam_trong.md`. Lấy lại: `git show f1c90fb:tests/test_danh_so.py`.


print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
