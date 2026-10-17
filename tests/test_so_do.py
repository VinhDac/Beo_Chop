"""SƠ ĐỒ — Nhóm, Quay về, và bộ nhớ của cái nút.

Ba thứ này chép từ Jenifer_Studio, nơi một sơ đồ thật đã dùng chúng ở quy mô 1.170
khối. Bài này canh đúng chỗ chúng có thể hỏng LẶNG:

  · Nhóm gói một chuỗi hành động — mất `actions` là hộp rỗng mà không ai báo.
  · Quay về trỏ sai (chưa chọn / trỏ chính nó / đích đã xoá) — lúc chạy khối lặng lẽ
    không nhảy, lượt chạy kết thúc như thể đã đi hết đường.
  · Vòng KHÔNG KHÉP — máy nhảy thật, người vẽ tưởng mình vừa vẽ một vòng.
  · Khoá "cách nhìn" (pos, màu, ghim, hạt nhân) bị chuẩn hoá ăn mất — mở lại file là
    sơ đồ tự xếp khác đi, màu bay sạch, hạt nhân tan ra.

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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


def loi(steps, edges, sev="error"):
    return [p for p in core.validate_flow_graph(steps, edges)
            if p["severity"] == sev]


def noi(*cap):
    return [{"from": a["id"], "to": b["id"]} for a, b in cap]


# ================= 1. Nhóm =================
print("\n▸ Nhóm — một chuỗi hành động gói vào một hộp")
g = core.make_group_step("Vào lệnh")
g["actions"] = [{"type": "mua"}, {"type": "dat_sl"}, {"type": "dat_tp"}]
kiem("là Nhóm", core.is_group_step(g))
kiem("đọc được hành động bên trong", len(core.hanh_dong_cua(g)) == 3)
kiem("khối thường KHÔNG phải Nhóm", not core.is_group_step(core.make_start_step()))
kiem("Nhóm KHÔNG được làm cổng rẽ nhánh", not core.is_branch_gate(g),
     "— nhánh trượt phải lùi được, mà Nhóm có thể đã đặt lệnh rồi")

# ================= 2. Quay về =================
print("\n▸ Quay về")
bd = core.make_start_step()
a = core.make_action_step({"type": "bao", "name": "A"})
qv = core.make_quay_ve_step(ve=bd["id"])
kiem("đọc ra đích + lặp mãi", core.khoi_quay_ve(qv) == (bd["id"], None))
qv5 = core.make_quay_ve_step(ve=bd["id"], so_vong=5)
kiem("đọc ra số vòng", core.khoi_quay_ve(qv5) == (bd["id"], 5))
kiem("khối thường trả None", core.khoi_quay_ve(a) is None)

print("\n▸ Quay về KHÔNG có lối đi tiếp")
b = core.make_action_step({"type": "bao", "name": "B"})
# cố tình nối thêm một dây RA TỪ khối Quay về — nó phải bị bỏ qua
_, ke = core.flow_map([bd, a, qv, b], noi((bd, a), (a, qv)) + noi((qv, b)))
kiem("dây ra từ Quay về bị bỏ qua", qv["id"] not in ke,
     "— chạy tới đó là nhảy về, hết nhánh")

print("\n▸ Đường ↻ không phải một nhánh đi tiếp")
day_vong = [{"from": a["id"], "to": bd["id"], "so_vong": 3}]
_, ke2 = core.flow_map([bd, a], noi((bd, a)) + day_vong)
kiem("↻ không nằm trong bảng kế tiếp", ke2.get(a["id"]) is None)
kiem("nhưng canh_vong thấy nó",
     core.canh_vong(day_vong, [bd, a]) == {a["id"]: (bd["id"], 3)})
kiem("số 0 = lặp mãi",
     core.canh_vong([{"from": a["id"], "to": bd["id"], "so_vong": 0}], [])
     == {a["id"]: (bd["id"], None)})

print("\n▸ Hai cách khai đổ vào MỘT bảng")
kiem("khối Quay về cũng vào canh_vong",
     core.canh_vong([], [qv5]) == {qv5["id"]: (bd["id"], 5)})

# ================= 3. Quay về trỏ hỏng =================
print("\n▸ Ba cách Quay về trỏ hỏng — cả ba đều im lặng lúc chạy")
chua = core.make_quay_ve_step()
ds = loi([bd, a, chua], noi((bd, a), (a, chua)))
kiem("chưa chọn đích → lỗi", any("chưa chọn khối" in p["message"] for p in ds))

tu = core.make_quay_ve_step()
tu["ve"] = tu["id"]
ds = loi([bd, a, tu], noi((bd, a), (a, tu)))
kiem("quay về CHÍNH NÓ → lỗi", any("CHÍNH NÓ" in p["message"] for p in ds))

mat = core.make_quay_ve_step(ve="skhong-co-that")
ds = loi([bd, a, mat], noi((bd, a), (a, mat)))
kiem("đích đã bị xoá → lỗi", any("KHÔNG CÒN" in p["message"] for p in ds))

print("\n▸ Vòng phải KHÉP")
# a → b, rồi b "quay về" một khối KHÔNG dẫn tới b được: đó là cú nhảy ngang
le = core.make_action_step({"type": "bao", "name": "lẻ"})
nhay = core.make_quay_ve_step(ve=le["id"])
ds = loi([bd, a, nhay, le], noi((bd, a), (a, nhay)))
kiem("vòng không khép → lỗi", any("không khép" in p["message"] for p in ds))

ok = core.make_quay_ve_step(ve=a["id"])
ds = loi([bd, a, ok], noi((bd, a), (a, ok)))
kiem("vòng khép đúng → KHÔNG lỗi", not ds, f"— {[p['message'][:40] for p in ds]}")

print("\n▸ Một khối chỉ quay lại được MỘT chỗ")
hai = [{"from": a["id"], "to": bd["id"], "so_vong": 2},
       {"from": a["id"], "to": le["id"], "so_vong": 2}]
ds = loi([bd, a, le], noi((bd, a), (a, le)) + hai)
kiem("hai đường ↻ ra từ một khối → lỗi",
     any("đường ↻ đi ra" in p["message"] for p in ds))

# ================= 4. Bộ nhớ của cái nút =================
print("\n▸ Khoá «cách nhìn» phải sống sót qua chuẩn hoá")
g2 = core.make_group_step("N")
g2.update({"actions": [{"type": "x"}], "pos": [12.5, -3], "mau": "#ffa657",
           "ghim": True, "hat_nhan": {"id": "hn1", "ten": "Vòng 1", "x": -9, "y": 4,
                                      "rac": "phải bị bỏ"}})
doc = core.make_process_template("thử", [core.make_start_step(), g2])
ra = doc["steps"][1]
kiem("pos giữ nguyên", ra.get("pos") == [12.5, -3.0])
kiem("màu giữ nguyên", ra.get("mau") == "#ffa657")
kiem("ghim giữ nguyên", ra.get("ghim") is True)
kiem("hạt nhân giữ nguyên", (ra.get("hat_nhan") or {}).get("ten") == "Vòng 1")
kiem("khoá rác trong hạt nhân bị bỏ", "rac" not in (ra.get("hat_nhan") or {}))
kiem("hành động bên trong Nhóm giữ nguyên", len(ra.get("actions") or []) == 1)
kiem("tài liệu có schema + loại", doc["schema"] == core.SCHEMA
     and doc["type"] == core.LOAI_TAI_LIEU)

print("\n▸ File cũ không có edges → nối thành chuỗi thẳng")
d2 = core.normalize_process({"name": "cũ", "steps": [core.make_start_step(),
                                                     core.make_action_step({"type": "x"})]})
kiem("tự nối chuỗi", len(d2["edges"]) == 1)

print("\n▸ Số vòng trên đường ↻ phải sống sót")
d3 = core.normalize_process({"name": "v", "steps": [bd, a],
                             "edges": noi((bd, a)) + day_vong})
kiem("clean_edges giữ so_vong",
     any(e.get("so_vong") == 3 for e in d3["edges"]),
     "— mất nó là vòng lặp thành cú nhảy ngang")

print("\n▸ Gom thành Nhóm (Ctrl+G) và Tách Nhóm (Ctrl+Shift+G)")
from cat_studio import hoi, lam  # noqa: E402

def _hd(ma, phan):
    s = core.make_lam_step(lam.LAM_DAT_TY_TRONG)
    s["ma"], s["ty_trong"], s["pos"] = ma, phan, [10, 20]
    return s

g, loi = core.gom_nhom([_hd("QQQ", 0.4), _hd("XLE", 0.35)])
kiem("gom được hai khối Hành động", not loi and core.is_group_step(g), f"— {loi}")
kiem("tên gợi sẵn là mấy mã nó đụng tới", g["name"] == "QQQ · XLE", f'— "{g["name"]}"')
# ⚠ Khối trong Nhóm KHÔNG được mang `kind`/`id`/`pos`: chúng là khoá của một KHỐI
# trên canvas. Sót lại thì file phình ra những id chết, và tách ra là hai khối cùng id.
thua = [k for a in g["actions"] for k in ("kind", "id", "pos", "hat_nhan") if k in a]
kiem("hành động trong Nhóm không còn khoá của khối", not thua, f"— còn {thua}")

ds, loi = core.ra_nhom(g)
kiem("tách lại ra đúng hai khối", not loi and len(ds) == 2, f"— {loi}")
kiem("mỗi khối tách ra có id RIÊNG",
     len({s["id"] for s in ds}) == 2 and all(s["kind"] == core.KIND_ACTION for s in ds))
kiem("gom rồi tách không mất gì",
     [(s["ma"], s["ty_trong"]) for s in ds] == [("QQQ", 0.4), ("XLE", 0.35)])

# ⚠ LỌC THEO `type`, KHÔNG THEO `kind`. Khối Hỏi và Quay về cũng mang
# `kind = "action"` — chặn bằng `kind` là lọt cả hai, và một cổng rẽ nhánh nằm trong
# `actions` thì bộ sinh mã duyệt qua mà không sinh ra gì. Đã hụt thật ở bản đầu.
for ten, st in (("Xác nhận", core.make_hoi_step(hoi.HOI_THI_TRUONG)),
                ("Quay về", core.make_quay_ve_step()),
                ("Nhóm", core.make_group_step()),
                ("Bắt đầu", core.make_start_step())):
    _g, _l = core.gom_nhom([_hd("QQQ", 0.4), st])
    kiem(f"chối khối {ten}", _g is None and "HÀNH ĐỘNG" in _l, f"— {_l or 'KHÔNG CHỐI'}")
kiem("chối Nhóm rỗng", core.ra_nhom(core.make_group_step())[1] != "")
kiem("chối tách một khối không phải Nhóm",
     core.ra_nhom(_hd("QQQ", 0.4))[1] != "")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
