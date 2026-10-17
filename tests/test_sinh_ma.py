"""BỘ SINH MÃ — sơ đồ thành thuật toán LEAN Python.

LUẬT GỐC: bộ sinh mã **không tự nghĩ ra một câu LEAN nào**. Mọi câu nó viết đều lấy từ
ô `lean` của ba từ điển, chỉ thay chỗ trống bằng giá trị. Bài này canh đúng luật ấy —
và canh cả mấy chỗ hỏng LẶNG của bản thân mã sinh ra:

  · cú pháp Python sai (file không chạy, mà `soat` thì bảo sơ đồ sạch);
  · chỉ báo khai HAI LẦN khi hai khối cùng dùng RSI(14);
  · quên `set_warm_up` → N nến đầu quyết trên số rác;
  · nhánh sinh thành mấy câu `if` rời thay vì `if/elif` → nhiều nhánh cùng chạy;
  · điều kiện trỏ tới mã chưa khai ở khối Bắt đầu;
  · vòng lặp sinh bừa thành thứ sơ đồ không nói.

⚠ BÀI NÀY KHÔNG CHẠY LEAN. Nó kiểm chuỗi sinh ra và CÚ PHÁP Python. Việc chạy thật đã
làm tay một lần (xem `tai_lieu/core.md` §30: XAUUSD 2015–2018, 15 lệnh, +16,376%).

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, core, hoi, lam, sinh_ma  # noqa: E402

dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def o(x, y):
    return [x, y]


def so_do_rsi(nhip="gio", san="DEFAULT"):
    """Sơ đồ mẫu: vàng, RSI(14) — quá bán thì vào hết, quá mua thì thoát."""
    bd = core.make_start_step()
    bd["ma"] = [{"ma": "XAUUSD", "loai": "cfd"}]
    bd["khoang"] = {"tu": "2015-01-01", "den": "2018-12-31"}
    bd["nhip"], bd["san"], bd["pos"] = nhip, san, o(0, 0)

    mua = core.make_hoi_step(hoi.HOI_THI_TRUONG, "Quá bán?")
    mua["dieu_kien"] = [core.make_dieu_kien("rsi", "<", 30, tham_so={"n": 14})]
    mua["pos"] = o(200, -100)
    vao = core.make_lam_step(lam.LAM_DAT_TY_TRONG, "Vào hết")
    vao["ty_trong"], vao["pos"] = 1.0, o(400, -100)

    ban = core.make_hoi_step(hoi.HOI_THI_TRUONG, "Quá mua?")
    ban["dieu_kien"] = [core.make_dieu_kien("rsi", ">", 70, tham_so={"n": 14})]
    ban["pos"] = o(200, 100)
    ra_ = core.make_lam_step(lam.LAM_DONG, "Thoát")
    ra_["pos"] = o(400, 100)

    steps = [bd, mua, vao, ban, ra_]
    edges = [{"from": bd["id"], "to": mua["id"]}, {"from": mua["id"], "to": vao["id"]},
             {"from": bd["id"], "to": ban["id"]}, {"from": ban["id"], "to": ra_["id"]}]
    return core.make_process_template("Vàng RSI", steps, edges), steps


doc, khoi = so_do_rsi()
kq = sinh_ma.sinh(doc)
ma = kq["ma"]

# ================= 1. Chạy được =================
print("\n▸ File sinh ra phải là Python HỢP LỆ")
kiem("sinh xong không lỗi", kq["ok"],
     f"— {[p['message'][:60] for p in kq['van_de'] if p['severity'] == 'error']}")
loi_cu_phap = ""
try:
    compile(ma, "<sinh>", "exec")
except SyntaxError as e:
    loi_cu_phap = f"dòng {e.lineno}: {e.msg}"
kiem("biên dịch được", not loi_cu_phap, f"— {loi_cu_phap}")
kiem("là một lớp QCAlgorithm", "class VangRSI(QCAlgorithm):" in ma)
kiem("có `initialize` và `on_data`",
     "def initialize(self):" in ma and "def on_data(self, data):" in ma)
kiem("tên lớp bỏ dấu tiếng Việt", kq["ten_lop"] == "VangRSI", f"— {kq['ten_lop']}")
kiem("tên lạ vẫn ra tên lớp hợp lệ",
     sinh_ma.ten_lop("cỗ máy 2 — thử!") == "CoMay2Thu",
     f"— {sinh_ma.ten_lop('cỗ máy 2 — thử!')}")
kiem("tên rỗng không ra lớp vô danh", sinh_ma.ten_lop("") == "CoMay")

# ================= 2. Không bịa câu LEAN nào =================
print("\n▸ MỌI câu LEAN phải lấy từ từ điển, không tự nghĩ")
kiem("đặt tỷ trọng viết đúng mẫu của từ điển",
     "self.set_holdings(sym, 1.0, False, tag=" in ma)
kiem("đóng viết đúng mẫu", "self.liquidate(sym, tag=" in ma)
kiem("chỉ báo dựng đúng mẫu", "self.rsi(sym, 14)" in ma)
kiem("đọc chỉ báo qua `.current.value`", ".current.value" in ma)

print("\n▸ Khối Bắt đầu thành `initialize`")
for cau in ("self.set_start_date(2015, 1, 1)", "self.set_end_date(2018, 12, 31)",
            "self.set_cash(100000)", "self.add_cfd('XAUUSD', Resolution.HOUR)",
            "self.set_brokerage_model(BrokerageName.DEFAULT)"):
    kiem(f"có `{cau[:46]}`", cau in ma)

# ================= 3. Ba thứ bộ sinh mã TỰ LO =================
print("\n▸ ① Chỉ báo NÂNG lên `initialize`, và dùng CHUNG")
kiem("khai trong initialize, không khai trong on_data",
     ma.index("self.rsi(sym, 14)") < ma.index("def on_data"))
kiem("hai khối cùng RSI(14) chỉ khai MỘT chỉ báo",
     ma.count("self.rsi(sym, 14)") == 1,
     "— khai hai lần là LEAN nuôi hai bộ đếm y hệt nhau")
kiem("cả hai khối đọc cùng một khoá",
     ma.split("def _mot_ma")[1].count("self._cb[sym]['rsi_14']") == 2)

print("\n▸ ② Làm nóng tự suy từ chu kỳ dài nhất")
m = re.search(r"self\.set_warm_up\((\d+)\)", ma)
kiem("có `set_warm_up`", m is not None,
     "— thiếu nó thì N nến đầu cỗ máy quyết trên số rác")
kiem("đúng bằng chu kỳ dài nhất đã vẽ", m and m.group(1) == "14", f"— {m and m.group(1)}")

print("\n▸ ③ Vòng lặp nhiều mã do khối Bắt đầu lo")
kiem("có vòng mỗi mã", "for sym in self._ma:" in ma)
kiem("và chặn lúc đang làm nóng", "if self.is_warming_up:" in ma)

# ================= 4. Nhánh: thử LẦN LƯỢT =================
print("\n▸ Nhánh sinh thành `if / elif`, không phải mấy câu `if` rời")
than = ma.split("def _mot_ma")[1]
kiem("có `elif`", "elif " in than,
     "— mấy câu `if` rời là NHIỀU nhánh cùng chạy trong một nến")
# Đếm ở ĐẦU DÒNG: `elif (` có chứa `if (`, nên đếm cả chuỗi sẽ ra 2 mà tưởng là sai.
_if = len(re.findall(r"^\s*if \(", than, re.M))
_elif = len(re.findall(r"^\s*elif \(", than, re.M))
kiem("đúng một `if` mở đầu, một `elif` nối theo", _if == 1 and _elif == 1,
     f"— if={_if}, elif={_elif}")
kiem("điều kiện đọc được", "< 30" in than and "> 70" in than)

print("\n▸ Ô `tag` tự điền số khối + điều kiện vừa khớp")
kiem("tag mang số khối", "[1A.1]" in ma and "[1B.1]" in ma, "— lời hứa D-11")
kiem("tag mang điều kiện đã khớp", "RSI(14) < 30" in ma and "RSI(14) > 70" in ma)

# ================= 5. Nhịp hẹn giờ =================
print("\n▸ Nhịp HẸN GIỜ sinh ra `schedule.on`, không chạy theo nến")
d2, _k = so_do_rsi(nhip="sau_mo_cua")
m2 = sinh_ma.sinh(d2)["ma"]
kiem("có `schedule.on`", "self.schedule.on(" in m2)
kiem("dùng đúng luật ngày và luật giờ của LEAN",
     "self.date_rules.every_day(" in m2 and "self.time_rules.after_market_open(" in m2)
# ⚠ PHÉP KIỂM NÀY TỪNG CANH NGƯỢC. Bản D-15 khẳng định nhịp hẹn giờ PHẢI đăng ký dữ
# liệu phút, "vì dữ liệu ngày không có giờ nào trong đó mà hẹn" — và đóng cứng điều
# ấy thành luật. Sai: `schedule.on` chạy theo ĐỒNG HỒ của thuật toán, không theo lúc
# dữ liệu về. Một chiến thuật thật (vd2) dùng `Resolution.Daily` cộng
# `AfterMarketOpen(spy, 30)` và chạy bình thường.
#   Cái sai ấy không nhỏ: ép phút thì `self.sma(sym, 200)` thành 200 PHÚT chứ không
#   phải 200 NGÀY — cùng một sơ đồ, khác hẳn chiến thuật.
kiem("nhịp hẹn giờ mặc định lấy dữ liệu NGÀY", "Resolution.DAILY" in m2,
     "— lịch chạy theo đồng hồ, không theo dữ liệu")
kiem("và KHÔNG tự ép xuống phút", "Resolution.MINUTE" not in m2)
d2b, k2b = so_do_rsi(nhip="sau_mo_cua")
k2b[0]["do_phan_giai"] = "MINUTE"
m2b = sinh_ma.sinh(core.make_process_template("x", k2b, d2b["edges"]))["ma"]
kiem("chọn phút thì mới ra phút", "Resolution.MINUTE" in m2b)
kiem("ruột chạy ở `_nhip`", "def _nhip(self):" in m2)
kiem("và lấy nến mới nhất của LEAN, không tự nhớ",
     "data = self.current_slice" in m2)
kiem("`on_data` để trống", "# Nhịp hẹn giờ" in m2)
try:
    compile(m2, "<sinh2>", "exec")
    kiem("bản hẹn giờ cũng biên dịch được", True)
except SyntaxError as e:
    kiem("bản hẹn giờ cũng biên dịch được", False, f"— {e.msg}")

# ================= 6. Chỗ nó BÁO chứ không đoán =================
print("\n▸ Mã chưa khai ở khối Bắt đầu → báo, KHÔNG tự `add_*` thêm")
d3, k3 = so_do_rsi()
k3[1]["dieu_kien"] = [{"trai": {"ma_dl": "rsi", "ma": "SPY", "tham_so": {"n": 14}},
                       "phep": "<", "phai": {"so": 30}}]
r3 = sinh_ma.sinh(core.make_process_template("x", k3, d3["edges"]))
kiem("→ lỗi", any("chưa khai" in p["message"] for p in r3["van_de"]))
kiem("và KHÔNG tự đăng ký mã ấy", "'SPY'" not in r3["ma"].split("def on_data")[0],
     "— tự add_* là tự quyết hộ một đăng ký dữ liệu")

print("\n▸ Vòng lặp → báo chưa sinh được, không đoán")
d4, k4 = so_do_rsi()
qv = core.make_quay_ve_step(ve=k4[1]["id"], so_vong=3)
qv["pos"] = o(600, -100)
k4.append(qv)
e4 = list(d4["edges"]) + [{"from": k4[2]["id"], "to": qv["id"]}]
r4 = sinh_ma.sinh(core.make_process_template("x", k4, e4))
kiem("→ lỗi, nói rõ là chưa sinh được",
     any("QUAY VỀ" in p["message"] or "VÒNG LẶP" in p["message"]
         for p in r4["van_de"]), f"— {[p['message'][:48] for p in r4['van_de']]}")
kiem("và `ok` là False", not r4["ok"])

print("\n▸ Sơ đồ không có khối Bắt đầu → báo rõ")
r5 = sinh_ma.sinh({"steps": [core.make_lam_step(lam.LAM_DONG)], "edges": []})
kiem("→ lỗi", any("Bắt đầu" in p["message"] for p in r5["van_de"]))
kiem("và không sinh file nào", not r5["ma"])

print("\n▸ Khối không nối vào sơ đồ → cảnh báo, không lặng lẽ bỏ")
d6, k6 = so_do_rsi()
roi = core.make_lam_step(lam.LAM_DONG, "Khối rơi")
roi["pos"] = o(900, 400)
r6 = sinh_ma.sinh(core.make_process_template("x", k6 + [roi], d6["edges"]))
kiem("→ cảnh báo", any("không nối vào sơ đồ" in p["message"] for p in r6["van_de"]))

# ================= 7. Bẫy sàn + nhịp ngày =================
print("\n▸ ⚠ Nhịp NGÀY + sàn không nhận «khớp lúc đóng cửa» = mọi lệnh bị từ chối")
# Đã gặp thật: 111 lệnh, tất cả `invalid`, backtest báo lãi 0%, không một dòng lỗi.
for san in bat_dau.SAN_KHONG_NHAN_MOC:
    s = core.make_start_step()
    s["nhip"], s["san"] = "ngay", san
    kiem(f"`{san}` + nhịp ngày → cảnh báo",
         any("MỌI LỆNH BỊ TỪ CHỐI" in p["message"]
             for p in core.soat_khoi_bat_dau(s)))
s = core.make_start_step()
s["nhip"], s["san"] = "ngay", "DEFAULT"
kiem("sàn Mặc định thì không sao", not core.soat_khoi_bat_dau(s))
s["nhip"], s["san"] = "gio", "OANDA_BROKERAGE"
kiem("nhịp giờ thì cũng không sao", not core.soat_khoi_bat_dau(s))

# ================= 8. Hai cổng khác nhau KHÔNG bị báo trùng =================
print("\n▸ Hai cổng khác điều kiện không được báo là trùng")
# ⚠ Bản trước đọc khoá `conditions` đã chết từ D-12, nên MỌI cặp cổng đều băm ra `[]`
# và bị báo "trùng điều kiện". Cảnh báo sai thì người ta học cách bỏ qua nó.
kiem("sơ đồ RSI không có cảnh báo trùng",
     not any("giống hệt" in p["message"] for p in kq["van_de"]),
     f"— {[p['message'][:50] for p in kq['van_de']]}")
d7, k7 = so_do_rsi()
k7[3]["dieu_kien"] = list(k7[1]["dieu_kien"])      # cho trùng THẬT
r7 = sinh_ma.sinh(core.make_process_template("x", k7, d7["edges"]))
kiem("mà trùng THẬT thì vẫn báo",
     any("giống hệt" in p["message"] for p in r7["van_de"]))

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
