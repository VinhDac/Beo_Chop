"""CỖ MÁY 5 TRẠM CHẠY TỪ APP QUA API QUANTCONNECT — trọn đường.  (D-10, 4b)

`ViecQC` (việc nền của cửa sổ Màn chơi) → đóng gói → đẩy file lên MÁY CHỦ QC GIẢ qua đúng giao
thức API → máy chủ chạy CHÍNH bộ file đó (lớp vỏ `vo_may` trên LEAN giả) → nhật ký vào Object
Store → app tải về, xoá khỏi cloud, đọc ra kết quả, dựng chữ, ghi lịch sử. Canh:

  1. Cỗ máy lỗi / đầu vào Sáng tạo sai → báo NGAY bằng câu tiếng Việt, chưa gửi gì lên QC.
  2. Lượt chạy xong: tóm tắt mang đủ (rổ, loại thị trường, ngày, thống kê, boss, link QC).
  3. Nhật ký trên máy đọc được: lô "vì sao", soi một lượt lên sơ đồ (đúng trạm, đủ nhãn).
  4. Khoá Object Store riêng của lượt được XOÁ sau khi tải về; lịch sử ghi lượt đó.

Chạy:  python tests\\test_qc_may.py
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import game  # noqa: E402
from cat_studio import luu_tru  # noqa: E402
from cat_studio import may as M  # noqa: E402
from cat_studio import mau_tram as MT  # noqa: E402
from cat_studio import qc_chay  # noqa: E402
from cat_studio import tram as T  # noqa: E402
import qc_gia  # noqa: E402
import san_gia as SG  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def bat(f, *a, **k):
    try:
        f(*a, **k)
    except Exception as e:  # noqa: BLE001
        return e
    return None


XU = {"EURUSD": 6.0, "GBPUSD": -6.0, "USDJPY": 1.0, "AUDUSD": 3.0}


def du_lieu_may(ch):
    """"QC" có dữ liệu cho bất kỳ rổ nào: mỗi mã một xu hướng cố định, đủ dài cho khởi động.

    Seed theo KHOẢNG NGÀY: màn đã thấy và màn ẩn phải ra hai kết quả khác nhau, không thì
    bài kiểm ⭐⭐⭐ chẳng chứng minh được gì (hai lượt y hệt thì thắng cái này là thắng cái
    kia)."""
    dl = SG.du_lieu({m: XU.get(m, 0.0) for m in ch["ma"]}, 13,
                    seed=31 + sum(ord(c) for c in str(ch.get("tu"))), nhieu=0.0005)
    return {m: [list(n) + [0.0002 * n[4]] for n in ds] for m, ds in dl.items()}


TD = tempfile.mkdtemp()
luu_tru.goc = lambda: TD                  # sổ game + nhật ký vào thư mục tạm
gia = qc_gia.QCGia(du_lieu_may=du_lieu_may)
qc = qc_gia.qc_cho(gia)


def viec_moi():
    return qc_chay.ViecQC(tao_qc=lambda: qc, thu_muc_nhat_ky=TD)


MAY = MT.may_tu_mau("Theo EMA 4 mã")
MAN = "ro-ngoai-hoi-2024"       # màn Chiến dịch của cỗ máy 5 trạm
TU_DO = {"ma": ["eurusd", "GBPUSD", "USDJPY", "AUDUSD", "EURUSD"], "loai": "forex",
         "tu": "2024-01-08", "den": "2024-01-12", "von": 10000}

# ================= 1. soát trước khi gửi =================
print("\n▸ Soát NGAY tại máy, chưa gửi gì lên QC")
v = viec_moi()
e = bat(v.bat_dau, M.may_moi(), "tu_do", tu_do=TU_DO)
kiem("cỗ máy trắng → câu «còn 4 lỗi» kèm lỗi đầu", isinstance(e, game.LoiGame)
     and "còn 4 lỗi" in str(e), f"— {e}")
e = bat(v.bat_dau, MAY, "nhanh", "vang-2024")
kiem("màn của SƠ ĐỒ CŨ → từ chối, nói rõ vì sao (hai dạng không dùng chung màn)",
     isinstance(e, game.LoiGame) and "sơ đồ cũ" in str(e), f"— {e}")
e = bat(v.bat_dau, MAY, "nop", MAN)
kiem("chưa ▶ đầy đủ mà nộp → báo NGAY, chưa gửi gì lên QC",
     isinstance(e, game.LoiGame) and "▶ đầy đủ" in str(e), f"— {e}")
for sai_, cau in (({"ma": []}, "chưa có mã"), ({"ma": ["EUR USD"]}, "không hợp lệ"),
                  ({"loai": "vang"}, "loại thị trường"), ({"ma": [f"M{i:03d}" for i in range(25)]},
                                                         "tối đa 20 mã"),
                  ({"tu": "2024-02-01", "den": "2024-01-01"}, "SAU ngày kết thúc")):
    e = bat(v.bat_dau, MAY, "tu_do", tu_do=dict(TU_DO, **sai_))
    kiem(f"đầu vào sai {list(sai_)} → «{cau}»", isinstance(e, game.LoiGame) and cau in str(e),
         f"— {e}")
kiem("chưa có yêu cầu nào tới QC", not gia.nhat)

# ================= 2. chạy trọn =================
print("\n▸ Chạy trọn: đóng gói → API → chạy thật trên LEAN giả → tải về")
v = viec_moi()
v.bat_dau(MAY, "tu_do", tu_do=TU_DO)
v.cho(600)
tt = v.trang_thai()
x = tt.get("xong") or {}
kiem("lượt xong, không lỗi", not tt["dang_chay"] and not tt["loi"] and x,
     f"— {(tt.get('loi') or '')[:300]}")
kiem("tóm tắt: dạng cỗ máy 5 trạm, rổ 4 mã (viết hoa, bỏ trùng), ngoại hối, đúng ngày",
     x.get("dang") == "may5" and x.get("ma") == ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
     and x.get("loai_thi_truong") == "forex" and x.get("tu") == "2024-01-08",
     f"— {x.get('ma')}")
tk = x.get("thong_ke") or {}
kiem("thống kê có lãi %, boss %, số lệnh", "lai_pt" in tk and tk.get("boss_pt") is not None
     and tk.get("so_lenh", 0) > 0, f"— lãi {tk.get('lai_pt', 0):+.2f}%, boss "
     f"{tk.get('boss_pt') or 0:+.2f}%, {tk.get('so_lenh')} lệnh")
kiem("có link backtest trên quantconnect.com", (x.get("url") or "").startswith(
    "https://www.quantconnect.com/project/"))
kiem("đường vốn mỗi ngày một điểm", len(x.get("duong_von") or []) >= 4)

print("\n▸ Đọc lại nhật ký trên máy")
k = v.ket_qua
lo = k.lo(0, 40, True)
kiem("lô «vì sao»: dòng có việc, mỗi dòng có chữ", lo["tong"] > 0 and lo["dong"]
     and all(d["chu"] and d["co_viec"] for d in lo["dong"]), f"— {lo['tong']} dòng có việc")
kiem("dòng đặt lệnh mang id lệnh (để tra sang bảng Lệnh)",
     any(d["lenh_id"] for d in lo["dong"]))
i2 = next(i for i, r in enumerate(k.nhat_ky) if r.get("tram") == T.TIN_HIEU and "duong" in r)
s2 = k.soi(i2)
kiem("soi một lượt ②: đúng trạm, đường đi, cổng kèm vết, nhãn mọi khối",
     s2["tram"] == T.TIN_HIEU and s2["duong"] and s2["cong"]
     and all(x_ in s2["nhan"] for x_ in s2["duong"]) and s2["chu"], f"— {s2['chu'][:70]}")
kiem("lệnh mang giờ đặt và các lần khớp", k.lenh and all("t_dat" in l for l in k.lenh)
     and any(l["khop"] for l in k.lenh))

print("\n▸ Dọn cloud, ghi lịch sử")
kiem("khoá Object Store riêng của lượt đã bị XOÁ sau khi tải về",
     gia.goi("object/delete") and not [kk for kk in gia.object_store if "may-" in kk])
ls = game.lich_su()
kiem("lịch sử ghi lượt cỗ máy 5 trạm: rổ, ngày, lãi, link",
     ls and ls[0].get("dang") == "may5" and "EURUSD" in ls[0]["symbol"]
     and ls[0]["lai_pt"] == round(tk.get("lai_pt"), 2) and ls[0]["url"] == x.get("url"))

print("\n▸ Mở lại lượt cũ từ lịch sử (không chạy lại)")
v2 = viec_moi()
n_goi = len(gia.nhat)
m = v2.mo_lai(ls[0]["duong"])
kiem("mở lại: đọc đúng nhật ký cỗ máy 5 trạm, cùng rổ, cùng thống kê, cùng link",
     m.get("dang") == "may5" and m.get("ma") == x.get("ma")
     and m.get("thong_ke") == tk and m.get("url") == x.get("url"))
kiem("mở lại: lô «vì sao» y hệt lúc vừa chạy xong",
     v2.ket_qua.lo(0, 40, True) == lo)
kiem("mở lại không gửi gì lên QC", len(gia.nhat) == n_goi)
x_hong = dict(ls[0], duong=os.path.join(TD, "khong_co.jsonl"))
game.ghi_lan(x_hong)
e = bat(v2.mo_lai, x_hong["duong"])
kiem("file nhật ký đã mất → câu tiếng Việt", isinstance(e, game.LoiGame)
     and "không còn trên máy" in str(e), f"— {e}")

# ================= 6. Chiến dịch: ▶ đầy đủ → vé → Nộp =================
print("\n▸ Chiến dịch — ▶ đầy đủ ghi vé, Nộp chạy màn ẩn rồi chấm sao")
m_may = next(m for m in game.danh_sach_man(dang=M.DANG) if m["id"] == MAN)
kiem("màn của cỗ máy mang rổ mã và boss cả rổ",
     m_may["ro"] == ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
     and m_may["boss"]["id"] == "mua_giu_deu", f"({m_may['ten']})")

v = viec_moi()
v.bat_dau(MAY, "day_du", MAN)
v.cho(600)
dd = (v.trang_thai().get("xong") or {})
kiem("▶ đầy đủ chạy đúng RỔ CỦA MÀN và đúng khoảng ngày của màn",
     dd.get("ma") == m_may["ro"] and dd.get("tu") == m_may["thay"][0]
     and dd.get("den") == m_may["thay"][1] and dd.get("man") == MAN,
     f"— {dd.get('ma')} {dd.get('tu')} → {dd.get('den')}")
kiem("▶ đầy đủ chấm được: lãi, boss cả rổ, sạch hay không — tối đa ⭐⭐",
     dd.get("cham") and dd["cham"]["mua_giu_pt"] is not None
     and dd.get("sao") in (0, 1, 2),
     f"— lãi {dd['cham']['lai_pt']:+.2f}% · boss {dd['cham']['mua_giu_pt']:+.2f}%"
     f" · {dd.get('sao')}⭐")
ve = game.ve_nop(MAN, M.van_tay(MAY))
kiem("… và để lại VÉ NỘP cho đúng cỗ máy đó", ve and ve["lai_pt"] == dd["cham"]["lai_pt"])
kiem("cỗ máy KHÁC thì không có vé (vé theo vân tay, không theo tên)",
     game.ve_nop(MAN, M.van_tay(MT.may_tu_mau("Tên khác", chon={T.RUI_RO: "cat_lo"})))
     is None)

n_truoc = len(game.lich_su())
v.bat_dau(MAY, "nop", MAN)
v.cho(600)
nop = (v.trang_thai().get("xong") or {})
kiem("Nộp chạy xong, có sao và số lần nộp",
     nop.get("an") is True and nop.get("sao") in (0, 1, 2, 3) and nop.get("lan_nop") == 1,
     f"— {nop.get('sao')}⭐, lần nộp {nop.get('lan_nop')}")
kiem("⭐⭐⭐ chỉ khi THẮNG BOSS cả ở màn đã thấy lẫn màn ẩn",
     nop["sao"] == game.sao(dd["cham"], nop["cham"])
     and (nop["sao"] == 3) == bool(dd["cham"]["thang_boss"] and nop["cham"]["thang_boss"]),
     f"— thấy {dd['cham']['thang_boss']} · ẩn {nop['cham']['thang_boss']}")
kiem("màn ẩn là ẨN: không ngày, không link QC, không đường vốn, không lượt",
     nop.get("tu") is None and nop.get("den") is None and nop.get("url") is None
     and nop.get("duong_von") == [] and nop.get("so_luot") is None
     and "2025" not in json.dumps(nop))
kiem("… nhưng vẫn trả phần chấm của màn đã thấy để so",
     nop.get("thay") and nop["thay"]["lai_pt"] == dd["cham"]["lai_pt"])
kiem("lượt nộp KHÔNG thay kết quả đang xem (vẫn là lượt ▶ đầy đủ)",
     v.ket_qua is not None and v.ket_qua.them.get("loai") == "day_du")
ls2 = game.lich_su()
kiem("lịch sử ghi lượt nộp: có màn, có sao, KHÔNG ngày, KHÔNG link",
     len(ls2) == n_truoc + 1 and ls2[0]["an"] is True and ls2[0]["man"] == MAN
     and ls2[0]["sao"] == nop["sao"] and ls2[0]["tu"] is None and ls2[0]["url"] is None)
e = bat(v.mo_lai, ls2[0]["duong"])
kiem("không mở lại được lượt màn ẩn để xem từng nến",
     isinstance(e, game.LoiGame) and "màn ẩn" in str(e), f"— {e}")
td = game.tien_do_man(MAN)
kiem("tiến độ màn: đếm lần nộp, giữ sao cao nhất",
     td["so_lan_nop"] == 1 and td["sao"] == nop["sao"])

# Vân tay là LOGIC: dựng lại y hệt cỗ máy đó thì vé vẫn dùng được.
kiem("dựng lại cỗ máy y hệt (id khối mới toanh) → VẪN đúng vé nộp",
     game.ve_nop(MAN, M.van_tay(MT.may_tu_mau("Dựng lại"))) is not None)

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
gia.dong()
sys.exit(1 if sai else 0)
