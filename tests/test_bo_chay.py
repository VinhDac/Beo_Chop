"""BỘ CHẠY — nối sơ đồ với thị trường, và đóng vòng phản hồi.

Bốn nhóm, theo đúng thứ tự rủi ro:

  1. **THỨ TỰ MỘT NHỊP** — thị trường đi trước, chiến lược đi sau. Đảo lại là nhìn trộm
     tương lai, và nó KHÔNG tự lộ ra: kết quả vẫn hợp lý, chỉ đẹp hơn sự thật.
  2. **LUẬT LÙI** — nhánh bị bỏ thì số hạng của nó cũng phải bị bỏ. Không hoàn nguyên
     bản nháp thì sơ đồ nói một đằng, báo giá một nẻo, mà màn hình không lộ gì.
  3. **BIÊN DỊCH** — mọi lỗi "không hiểu" nổ ra lúc biên dịch, KÈM NHÃN KHỐI. Nổ ở sự
     kiện thứ bốn triệu với một dòng `KeyError` thì không ai lần ra khối nào gây chuyện.
  4. **VÒNG PHẢN HỒI** — tồn kho khớp xong phải quay lại làm lệch báo giá. Đây là toàn
     bộ cơ chế quản trị rủi ro của market maker; đứt vòng này thì mọi thứ khác vô nghĩa.

⚠ Bài này KHÔNG kiểm "chiến lược có lãi không" — đó là việc của người dùng, không phải
của app. Nó kiểm app có **kể đúng chuyện đã xảy ra** hay không.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np  # noqa: E402

from cat_studio import api  # noqa: E402
from cat_studio import bo_chay as B  # noqa: E402
from cat_studio import core  # noqa: E402
from cat_studio import khop_lenh as K  # noqa: E402
from cat_studio import nguon_tick as NT  # noqa: E402
from cat_studio import phat_lai  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


TICK = 0.01


def nhin(bid=99.99, ask=100.01, bkl=500.0, akl=500.0, ton_kho=0.0, co_so=True):
    nh = B.Nhin()
    nh.bid, nh.ask, nh.bid_kl, nh.ask_kl = bid, ask, bkl, akl
    nh.ton_kho, nh.co_so = ton_kho, co_so
    return nh


def sh(sid, y, dich, phep, he_so, toan_hang=None, don_vi=None, khi=None, x=300.0):
    luong = {"he_so": he_so}
    if toan_hang:
        luong["toan_hang"] = toan_hang
    if don_vi:
        luong["don_vi"] = don_vi
    ra = {"id": sid, "kind": core.KIND_ACTION, "type": core.SO_HANG,
          "dich": dich, "phep": phep, "luong": luong, "pos": [x, y]}
    if khi:
        ra["khi"] = khi
    return ra


def cong(sid, y, dk, x=300.0):
    return {"id": sid, "kind": core.KIND_ACTION, "type": core.CHECK_COND,
            "conditions": dk, "pos": [x, y]}


def so_do(steps, canh):
    return {"schema": core.SCHEMA, "type": "strategy", "name": "t", "symbol": "X",
            "tham_so": [], core.TAB_BAO_GIA: {
                "steps": [dict(core.make_start_step("BĐ"), id="s0", pos=[0.0, 300.0])]
                         + steps,
                "edges": [{"from": a, "to": b, "port": "out"} for a, b in canh]}}


def chay_mot_luot(doc, nh):
    """Biên dịch rồi chạy đúng MỘT lượt — trả bản nháp báo giá."""
    lenh, dau, _ = B.bien_dich(doc)
    nhap = list(B.NHAP_GOC)
    B.mot_luot(lenh, dau, nh, TICK, nhap)
    return nhap


# ================= 1. MỘT LƯỢT: đích · phép · đơn vị =================
print("\n▸ Một lượt — đích · phép · đơn vị quy đổi đúng chưa")

d = so_do([sh("a", 300, "cong_bang", "=", 1, "mid")], [("s0", "a")])
kiem("`công bằng = mid`", chay_mot_luot(d, nhin())[B.CONG_BANG] == 100.0)

d = so_do([sh("a", 300, "bien", "=", 1, "spread")], [("s0", "a")])
n = chay_mot_luot(d, nhin())
kiem("`biên = spread` đặt CẢ HAI phía cùng lúc",
     abs(n[B.BIEN_MUA] - 0.02) < 1e-9 and n[B.BIEN_MUA] == n[B.BIEN_BAN],
     f"— {n[B.BIEN_MUA]}")

d = so_do([sh("a", 300, "bien_mua", "=", 3, don_vi="tick")], [("s0", "a")])
n = chay_mot_luot(d, nhin())
kiem("`biên mua = 3 tick` chỉ chạm MỘT phía",
     abs(n[B.BIEN_MUA] - 0.03) < 1e-9 and n[B.BIEN_BAN] == 0.0)

d = so_do([sh("a", 300, "lech", "=", 5, don_vi="bps")], [("s0", "a")])
kiem("`bps` quy theo mid: 5 bps của 100 = 0,05",
     abs(chay_mot_luot(d, nhin())[B.LECH] - 0.05) < 1e-9)

d = so_do([sh("a", 300, "lech", "+=", 0.5, "ton_kho", "tick")], [("s0", "a")])
kiem("đơn vị GHÉP: `tồn kho × 0,5 tick/lot`, tồn kho 4 → 2 tick",
     abs(chay_mot_luot(d, nhin(ton_kho=4))[B.LECH] - 0.02) < 1e-9)
kiem("và tồn kho ÂM cho lệch âm — dấu là toàn bộ ý nghĩa",
     chay_mot_luot(d, nhin(ton_kho=-4))[B.LECH] < 0)

d = so_do([sh("a", 300, "lot", "=", 10, don_vi="lot"),
           sh("b", 400, "lot_mua", "*=", 0.5, don_vi="lot")],
          [("s0", "a"), ("a", "b")])
n = chay_mot_luot(d, nhin())
kiem("`×=` chỉ dành cho lot, và chỉ chạm phía nó nhắm",
     n[B.LOT_MUA] == 5.0 and n[B.LOT_BAN] == 10.0)

# THỨ TỰ LÀ NGỮ NGHĨA — bài kiểm này chốt điều `_soat_ghi_de` cảnh báo.
xd = [sh("a", 300, "bien", "+=", 2, don_vi="tick"),
      sh("b", 400, "bien", "=", 1, "spread")]
n1 = chay_mot_luot(so_do(xd, [("s0", "a"), ("a", "b")]), nhin())
n2 = chay_mot_luot(so_do(xd, [("s0", "b"), ("b", "a")]), nhin())
kiem("đổi chỗ hai khối là ĐỔI KẾT QUẢ — thứ tự trong chuỗi là ngữ nghĩa",
     abs(n1[B.BIEN_MUA] - 0.02) < 1e-9 and abs(n2[B.BIEN_MUA] - 0.04) < 1e-9,
     f"— `+=` rồi `=` → {n1[B.BIEN_MUA]:.4f} · ngược lại → {n2[B.BIEN_MUA]:.4f}")


# ================= 2. `khi` và CỔNG là hai thứ khác nhau =================
print("\n▸ `khi` trượt thì BỎ QUA · cổng trượt thì LÙI")

dk = {"trai": {"ten": "ton_kho"}, "phep": ">=", "phai": {"value": 5, "tinh": "lot"}}
d = so_do([sh("a", 300, "cong_bang", "=", 1, "mid"),
           sh("b", 400, "lot_mua", "=", 0, don_vi="lot", khi=dk),
           sh("c", 500, "lot_ban", "=", 7, don_vi="lot")],
          [("s0", "a"), ("a", "b"), ("b", "c")])
n = chay_mot_luot(d, nhin(ton_kho=0))
kiem("`khi` trượt → bỏ qua số hạng đó, CHUỖI ĐI TIẾP",
     n[B.LOT_BAN] == 7.0, f"— lot bán {n[B.LOT_BAN]}")
n = chay_mot_luot(d, nhin(ton_kho=9))
kiem("`khi` khớp → áp dụng, và chuỗi vẫn đi tiếp",
     n[B.LOT_MUA] == 0.0 and n[B.LOT_BAN] == 7.0)

d = so_do([cong("g", 300, [dk]),
           sh("b", 400, "lot_ban", "=", 7, don_vi="lot")],
          [("s0", "g"), ("g", "b")])
kiem("CỔNG trượt và không còn nhánh nào → HẾT LƯỢT, khối sau không chạy",
     chay_mot_luot(d, nhin(ton_kho=0))[B.LOT_BAN] == 0.0)


# ================= 3. LUẬT LÙI =================
print("\n▸ Luật lùi — nhánh bị bỏ thì SỐ HẠNG của nó cũng phải bị bỏ")

# Nhánh A (nằm TRÊN, thử trước): đặt biên 9 tick rồi mới gặp cổng trượt.
# Nhánh B (dưới): đặt biên 2 tick.
d = so_do([sh("a1", 200, "bien", "=", 9, don_vi="tick"),
           cong("a2", 200, [dk], x=600.0),
           sh("b1", 400, "bien", "=", 2, don_vi="tick")],
          [("s0", "a1"), ("a1", "a2"), ("s0", "b1")])
n = chay_mot_luot(d, nhin(ton_kho=0))
kiem("lùi khỏi nhánh A phải HOÀN NGUYÊN số hạng nhánh A đã ghi",
     abs(n[B.BIEN_MUA] - 0.02) < 1e-9,
     f"— {n[B.BIEN_MUA]:.4f} (0,02 = nhánh B · 0,09 = rác nhánh A còn sót)")
n = chay_mot_luot(d, nhin(ton_kho=9))
kiem("nhánh A qua được thì lấy số của nhánh A", abs(n[B.BIEN_MUA] - 0.09) < 1e-9)

# Nhánh nào cũng trượt → hết lượt, bản nháp giữ nguyên phần TRƯỚC ngã rẽ.
d = so_do([sh("g", 300, "cong_bang", "=", 1, "mid"),
           cong("a", 200, [dk], x=600.0),
           cong("b", 400, [dk], x=600.0)],
          [("s0", "g"), ("g", "a"), ("g", "b")])
n = chay_mot_luot(d, nhin(ton_kho=0))
kiem("mọi nhánh đều trượt → hết lượt, phần TRƯỚC ngã rẽ vẫn còn",
     n[B.CONG_BANG] == 100.0)


# ================= 4. NaN — mù thì mọi cổng SỐ HỌC phải TRƯỢT =================
print("\n▸ Mất sổ lệnh — NaN phải làm cổng số học TRƯỢT, không khớp bừa")

d = so_do([cong("g", 300, [{"trai": {"ten": "spread"}, "phep": "<",
                            "phai": {"value": 9, "tinh": "tick"}}]),
           sh("b", 400, "lot", "=", 5, don_vi="lot")],
          [("s0", "g"), ("g", "b")])
kiem("`spread < 9 tick` khi có sổ → khớp",
     chay_mot_luot(d, nhin())[B.LOT_MUA] == 5.0)
kiem("cùng cổng đó khi MẤT sổ → TRƯỢT (NaN so với gì cũng sai)",
     chay_mot_luot(d, nhin(bid=B.NAN, ask=B.NAN, co_so=False))[B.LOT_MUA] == 0.0)

d = so_do([cong("g", 300, [{"trai": {"ten": "co_so"}, "phep": "la_sai"}]),
           sh("b", 400, "lot", "=", 5, don_vi="lot")],
          [("s0", "g"), ("g", "b")])
kiem("`có thấy sổ lệnh là SAI` VẪN trả lời được lúc mù — đúng cổng duy nhất phải vậy",
     chay_mot_luot(d, nhin(bid=B.NAN, ask=B.NAN, co_so=False))[B.LOT_MUA] == 5.0)

d = so_do([sh("a", 300, "bien", "=", 1, "spread"),
           sh("b", 400, "lot", "=", 5, don_vi="lot")], [("s0", "a"), ("a", "b")])
n = chay_mot_luot(d, nhin(bid=B.NAN, ask=B.NAN, co_so=False))
gm, lm, gb, lb = B.chot_bao_gia(n)
kiem("sơ đồ KHÔNG đặt giá công bằng → báo giá là NaN, tức RÚT",
     gm != gm and gb != gb, f"— {gm} / {gb}")


# ================= 5. BIÊN DỊCH — lỗi phải kèm NHÃN KHỐI =================
print("\n▸ Biên dịch — mọi lỗi nổ RA ĐÂY, kèm nhãn khối")


def loi_bien_dich(doc):
    try:
        B.bien_dich(doc)
        return ""
    except B.LoiChay as e:
        return str(e)


m = loi_bien_dich(so_do([cong("g", 300, [{"trai": {"ten": "atr"}, "phep": ">",
                                          "phai": {"value": 1}}])], [("s0", "g")]))
kiem("toán hạng không có trong kho → nổ lúc biên dịch",
     "not in the library" in m, f"— {m!r}")
kiem("và câu nói ra mang NHÃN KHỐI, không phải một dòng KeyError",
     m.startswith("[") and "]" in m[:8], f"— {m[:24]!r}")

m = loi_bien_dich(so_do([sh("a", 300, "bien", "=", 2)], [("s0", "a")]))
kiem("lượng thiếu thước đo → nổ, không đoán hộ một đơn vị",
     "no unit selected" in m, f"— {m!r}")

m = loi_bien_dich(so_do([sh("a", 300, "bien", "*=", 2, don_vi="tick")], [("s0", "a")]))
kiem("phép không hợp với đích → nổ (chuẩn hoá GIỮ phép sai để chỗ này còn tố cáo được)",
     "does not take" in m, f"— {m!r}")

kiem("sơ đồ mẫu biên dịch sạch", not loi_bien_dich(api.Api().demo_process()["value"]))
kiem("sơ đồ chỉ có khối Bắt đầu cũng chạy được, và cho báo giá RỖNG",
     chay_mot_luot(so_do([], []), nhin())[B.LOT_MUA] == 0.0)


# ================= 6. CHỐT BÁO GIÁ =================
print("\n▸ Chốt báo giá — `lệch` trừ ở CẢ HAI vế")
n = list(B.NHAP_GOC)
n[B.CONG_BANG], n[B.BIEN_MUA], n[B.BIEN_BAN] = 100.0, 0.02, 0.02
n[B.LOT_MUA] = n[B.LOT_BAN] = 3.0
gm, lm, gb, lb = B.chot_bao_gia(n)
kiem("lệch 0: treo đối xứng quanh công bằng", gm == 99.98 and gb == 100.02)
n[B.LECH] = 0.05
gm, _, gb, _ = B.chot_bao_gia(n)
kiem("lệch dương (đang ôm hàng) → CẢ HAI chân dịch XUỐNG",
     abs(gm - 99.93) < 1e-9 and abs(gb - 99.97) < 1e-9, f"— {gm:.4f} / {gb:.4f}")
kiem("bề rộng báo giá KHÔNG đổi khi lệch — lệch là DỜI, không phải GIÃN",
     abs((gb - gm) - 0.04) < 1e-9)


# ================= 7. TOÀN BỘ VÒNG LẶP =================
print("\n▸ Vòng lặp đầy đủ — trên `PhatLai` thật")


def du_lieu(n=30_000, seed=5):
    r = np.random.default_rng(seed)
    b = np.round((np.cumsum(r.normal(0, TICK * 0.7, n)) + 100.0) / TICK) * TICK
    b = np.round(b, 10)
    sp = r.integers(1, 4, n) * TICK
    t = np.arange(n, dtype="i8") * 3 + 1_700_000_000_000
    lk = r.random(n) < 0.25
    so = np.zeros(int((~lk).sum()), dtype=NT.DT_SO)
    so["T"] = so["t_ta"] = t[~lk]
    so["bid"] = b[~lk]
    so["ask"] = np.round(b[~lk] + sp[~lk], 10)
    so["bid_kl"] = r.gamma(2, 300, len(so))
    so["ask_kl"] = r.gamma(2, 300, len(so))
    kh = np.zeros(int(lk.sum()), dtype=NT.DT_KHOP)
    kh["T"] = kh["t_ta"] = t[lk]
    mua = r.random(len(kh)) < 0.5
    kh["gia"] = np.where(mua, np.round(b[lk] + sp[lk], 10), b[lk])
    kh["kl"] = r.gamma(1.5, 40, len(kh))
    kh["mua_chu_dong"] = mua
    return so, kh


SO, KH = du_lieu()
MAU = api.Api().demo_process()["value"]


def chay(doc=None, **kw):
    return B.chay(doc or MAU, phat_lai.PhatLai(SO, KH), K.MoHinh(TICK, **kw))


kiem("bước giá ĐO ĐƯỢC từ chính dữ liệu, không phải hỏi",
     K.do_buoc_gia(SO["bid"], SO["ask"], KH["gia"]) == TICK,
     f"— {K.do_buoc_gia(SO['bid'], SO['ask'], KH['gia'])}")

kq = chay(tre_ra_ms=5.0)
b = kq.bang()
kiem("chạy hết dòng sự kiện", kq.so_su_kien == len(SO) + len(KH))
kiem("mỗi sự kiện chạy sơ đồ đúng MỘT lượt", kq.so_luot == kq.so_su_kien)
kiem("có khớp thật", b["so_lan_khop"] > 0, f"— {b['so_lan_khop']:,} lần")
kiem("số lần khớp trong bảng khớp với danh sách khớp",
     b["so_lan_khop"] == len(kq.khop) == b["so_khop"])
kiem("bảng mang theo CẢ BỐN giả định — kết quả không được rời khỏi giả định của nó",
     set(b["gia_dinh"]) == {"buoc_gia", "phi_maker_bps", "tre_ra_ms",
                            "phan_huy_truoc", "phan_muc_sau"})
kiem("mẫu có LẤY THƯA, không phải mỗi sự kiện một điểm",
     0 < len(kq.mau) < kq.so_su_kien, f"— {len(kq.mau)} điểm")
# MỘT ĐIỂM MẪU = MỘT ẢNH CHỤP ĐỦ DÙNG: năm số để VẼ, năm số để SOI. Nhờ năm số sau
# mà `soi_luot` thành hàm THUẦN — không phát lại, không đọc file. Xem `KetQua.mau`.
kiem("mỗi điểm mẫu mang đủ MƯỜI số trên CÙNG một trục thời gian",
     all(len(x) == 10 for x in kq.mau))
kiem("và ảnh chụp thị trường trong mẫu KHỚP với thứ sơ đồ đã nhìn — soi mới đúng được",
     all(m[5] == m[5] or not m[9] for m in kq.mau))

# MARKOUT — con số nói ra ta có đang bị chọn ngược hay không.
kiem("markout đo được, và chỉ đo phần khớp ĐỦ TUỔI",
     0 < kq.markout_kl <= kq.tom_tat_khop["kl_da_khop"],
     f"— đo {kq.markout_kl:.0f}/{kq.tom_tat_khop['kl_da_khop']:.0f} lot")
kiem("markout quy ra TICK để đọc được bằng mắt",
     abs(b["markout_tick"] - b["markout_tong"] / b["markout_kl"] / TICK) < 1e-9,
     f"— {b['markout_tick']:+.3f} tick/lot sau {b['markout_ms']} ms")
kiem("chiến lược ngây thơ treo ở đúng đỉnh thì BỊ CHỌN NGƯỢC — markout âm",
     b["markout_tick"] < 0, f"— {b['markout_tick']:+.3f} tick/lot")

# TÍNH XÁC ĐỊNH — chạy lại ra kết quả Y HỆT. Không có gì ngẫu nhiên trong cả đường đi,
# nên bất kỳ khác biệt nào cũng là một trạng thái rò rỉ giữa hai lượt chạy.
a1, a2 = chay(tre_ra_ms=5.0).bang(), chay(tre_ra_ms=5.0).bang()
a1.pop("giay_chay"), a2.pop("giay_chay")
kiem("chạy lại ra kết quả Y HỆT — không có gì ngẫu nhiên, không có gì rò rỉ", a1 == a2)

# ---- VÒNG PHẢN HỒI CÓ THẬT KHÔNG ----
#
# ⚠ Bản đầu của phép này so thẳng sơ đồ mẫu với chính nó đã bỏ `lệch`, đo được 4,0 lot
# với 5,0 lot — gần như không khác gì. KHÔNG PHẢI vì vòng phản hồi hỏng, mà vì nó đo
# nhầm đối tượng: hai khối HẠN MỨC CỨNG (`lot mua = 0 khi tồn kho ≥ 5`) đã chặn tồn kho
# ở ±5 rồi, nên bỏ `lệch` đi cũng chẳng đi xa hơn được.
#
# Muốn thấy `lệch` làm gì thì phải GỠ HẠN MỨC ra, để nó thành thứ DUY NHẤT còn điều
# khiển tồn kho. Bài học chung: một phép kiểm xanh vì đối tượng đo bị che thì tệ hơn
# không có phép kiểm nào — nó còn phát cho ta một niềm tin sai.
import copy  # noqa: E402


def bo_khoi(doc, *ids, noi=None):
    """Gỡ vài khối khỏi sơ đồ rồi nối lại chỗ đứt."""
    d = copy.deepcopy(doc)
    g = d[core.TAB_BAO_GIA]
    g["steps"] = [x for x in g["steps"] if x.get("id") not in ids]
    g["edges"] = [e for e in g["edges"]
                  if e["from"] not in ids and e["to"] not in ids]
    if noi:
        g["edges"].append({"from": noi[0], "to": noi[1], "port": "out"})
    return d


#: Cả hai bản đều KHÔNG có hạn mức cứng — chỉ khác đúng một khối `lệch`.
CO_LECH = bo_khoi(MAU, "s_tran", "s_san")
KHONG_LECH = bo_khoi(CO_LECH, "s_lech", noi=("s_bien", "s_lot"))


def dinh_ton_kho(doc):
    """|tồn kho| lớn nhất trong cả lượt chạy."""
    p = phat_lai.PhatLai(SO, KH)
    s = K.SoKhop(K.MoHinh(TICK, tre_ra_ms=5.0))
    lenh, dau, _ = B.bien_dich(doc)
    nh, nhap, dinh = B.Nhin(), list(B.NHAP_GOC), 0.0
    while p.buoc() is not None:
        s.buoc(p)
        nh.bid, nh.ask, nh.bid_kl, nh.ask_kl = p.bid, p.ask, p.bid_kl, p.ask_kl
        nh.co_so, nh.ton_kho = p.co_so, s.ton_kho
        B.mot_luot(lenh, dau, nh, TICK, nhap)
        gm, lm, gb, lb = B.chot_bao_gia(nhap)
        s.dong_bo(int(p.t), gm, lm, gb, lb)
        dinh = max(dinh, abs(s.ton_kho))
    return dinh


co, khong = dinh_ton_kho(CO_LECH), dinh_ton_kho(KHONG_LECH)
kiem("gỡ hạn mức ra thì `lệch` là thứ DUY NHẤT giữ tồn kho — bỏ nó là nó chạy hoang",
     khong > co * 1.5, f"— có lệch {co:.0f} lot · không lệch {khong:.0f} lot")
kiem("và hạn mức cứng CÓ tác dụng: sơ đồ mẫu đầy đủ không vượt quá ±5",
     abs(chay(tre_ra_ms=5.0).tom_tat_khop["ton_kho"]) <= 5)


kiem("chạy sơ đồ RỖNG thì không khớp gì, và không nổ",
     chay(so_do([], [])).bang()["so_lan_khop"] == 0)


# ================= 8. NÓI RA CHỖ MÌNH KHÔNG BIẾT =================
print("\n▸ Kết quả phải nói ra chỗ nó không chắc")
kq = chay(tre_ra_ms=5.0)
kiem("còn tồn kho thì PHẢI cảnh báo — lãi lỗ chỉ chắc khi tồn kho về 0",
     ("inventory left" in kq.loi) == bool(kq.tom_tat_khop["ton_kho"]),
     f"— tồn kho {kq.tom_tat_khop['ton_kho']:.2f} · lời: {kq.loi[:60]!r}")
kiem("bị post-only từ chối thì phải nói — chiến lược đang muốn thoát mà không thoát được",
     ("rejection" in kq.loi or "STUCK" in kq.loi)
     == bool(kq.tom_tat_khop["so_tu_choi"]),
     f"— {kq.tom_tat_khop['so_tu_choi']:,} lần")

import json  # noqa: E402
try:
    json.dumps(kq.bang())
    json.dumps(kq.khop[:5])
    kiem("bảng kết quả JSON hoá được ngay — không sót kiểu numpy nào", True)
except TypeError as e:
    kiem("bảng kết quả JSON hoá được ngay — không sót kiểu numpy nào", False, f"— {e}")


print("\n" + "=" * 58)
print(f"  {dung} đúng, {sai} sai")
print("=" * 58)
sys.exit(1 if sai else 0)
