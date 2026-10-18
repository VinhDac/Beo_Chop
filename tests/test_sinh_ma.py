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
NL = chr(10)


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


# ================= 9. RỔ ĐỘNG — `set_universe_selection` =================
# Nhánh này KHÁC nhánh gõ-mã-sẵn ở BA chỗ, và cả ba đều hỏng LẶNG nếu làm sai: khai
# mã, khai chỉ báo, và `self._ma` lấy từ đâu. Hình dạng dưới đây đã dò bằng một
# backtest THẬT trước khi viết bộ sinh mã (SPY 12/2020 -> 14 lệnh, khớp hết).
print(NL + "▸ Rổ động — ba chỗ nhánh này khác hẳn nhánh gõ mã sẵn")


def so_do_ro(gt_ro, nhip="ngay", chay_cho="moi_ma", co_cb=True):
    """Sơ đồ chạy trên một RỔ: RSI quá bán thì phát tín hiệu LÊN."""
    bd = core.make_start_step()
    bd["ma"] = gt_ro
    bd["khoang"] = {"tu": "2020-12-01", "den": "2020-12-07"}
    bd["nhip"], bd["chay_cho"], bd["pos"] = nhip, chay_cho, o(0, 0)
    bd["chia_von"] = "EqualWeightingPortfolioConstructionModel"
    bd["dat_lenh"] = "ImmediateExecutionModel"

    th = core.make_lam_step(lam.LAM_TIN_HIEU, "Nên lên")
    th["huong"], th["han"], th["pos"] = "UP", 5, o(400, 0)
    if not co_cb:
        return core.make_process_template("Ro", [bd, th],
                                          [{"from": bd["id"], "to": th["id"]}])
    g = core.make_hoi_step(hoi.HOI_THI_TRUONG, "Quá bán?")
    g["dieu_kien"] = [core.make_dieu_kien("rsi", "<", 30, tham_so={"n": 14})]
    g["pos"] = o(200, 0)
    return core.make_process_template(
        "Ro", [bd, g, th],
        [{"from": bd["id"], "to": g["id"]}, {"from": g["id"], "to": th["id"]}])


r_etf = sinh_ma.sinh(so_do_ro({"ro": "etf", "ma_etf": "SPY", "lay": 8}))
m_etf = r_etf["ma"]
kiem("sinh xong không lỗi", r_etf["ok"],
     f"— {[p['message'][:70] for p in r_etf['van_de'] if p['severity'] == 'error']}")
loi_cp = ""
try:
    compile(m_etf, "<ro>", "exec")
except SyntaxError as e:
    loi_cp = f"dòng {e.lineno}: {e.msg}"
kiem("biên dịch được", not loi_cp, f"— {loi_cp}")

print(NL + "  (1) khai mã — một câu `set_universe_selection`, KHÔNG `add_*` nào")
kiem("có `set_universe_selection`", "self.set_universe_selection(" in m_etf)
kiem("đúng lớp LEAN", "ETFConstituentsUniverseSelectionModel('SPY'" in m_etf)
# KHÔNG được còn một dòng `add_*` nào: thêm `add_equity` cạnh một rổ là đăng ký một
# mã NGOÀI rổ, nó chạy suốt backtest mà sơ đồ không nói tới nó ở đâu cả.
kiem("không còn dòng `add_` nào", "self.add_" not in m_etf)
kiem("không còn `self._ten`", "self._ten" not in m_etf)
# THỨ TỰ: model chụp lấy `universe_settings` ngay lúc dựng, nên đặt độ phân giải SAU
# là rổ lặng lẽ chạy bằng mặc định của LEAN (phút) trong khi sơ đồ nói nến ngày — và
# `self.sma(sym, 200)` thành 200 PHÚT. Cùng sơ đồ, khác hẳn chiến thuật.
kiem("độ phân giải đặt TRƯỚC khi dựng model",
     m_etf.index("universe_settings.resolution")
     < m_etf.index("set_universe_selection"))
kiem("và đúng độ phân giải của nhịp",
     "self.universe_settings.resolution = Resolution.DAILY" in m_etf)

print(NL + "  (2) hàm lọc — thân hàm lấy TỪ TỪ ĐIỂN, không do bộ sinh mã nghĩ ra")
kiem("có hàm lọc", "def _loc_ro(self, ds):" in m_etf)
kiem("thân hàm đúng câu của từ điển",
     all(d.format(lay=8) in m_etf for d in bat_dau.LOC_TRONG_SO))
# `weight` NULLABLE (`public decimal? Weight`) — không gạn thì `sort` so None với số
# và ném TypeError giữa lượt chọn rổ. LEAN tự gạn y thế trong ví dụ của họ.
kiem("có gạn `weight` rỗng trước khi xếp", "if c.weight" in m_etf)
r_ca_ro = sinh_ma.sinh(so_do_ro({"ro": "etf", "ma_etf": "SPY", "lay": 0}))
kiem("«lấy 0» = cả rổ, nên KHÔNG sinh hàm lọc",
     "_loc_ro" not in r_ca_ro["ma"] and r_ca_ro["ok"])

# ⚠ CÂU HỘP THOẠI KHAI PHẢI LÀ MỘT KHÚC CỦA MÃ NÀY, không phải một câu tả lại nó.
# `bat_dau.lean_ro` là thứ hộp Bắt đầu bày ra khi chọn rổ, và nó tồn tại ĐÚNG ĐỂ
# người dùng đối chiếu với mã sinh ra — nên nói sai còn tệ hơn không nói. Bản đầu
# bịa một tham số thứ ba tên «lọc theo trọng số» và bỏ chữ `self.` giữa dòng: đọc
# thì hiểu, mà tìm trong mã thì không có. Hai bộ chữ, không ai đứng so.
# LẶP QUA CHÍNH TỪ ĐIỂN: thêm một rổ vào `bat_dau.RO` là phép này canh luôn.
print(NL + "  (2b) câu hộp thoại khai = một KHÚC của mã thật, từng chữ")
for _r in bat_dau.RO:
    _gt = ({"ro": "etf", "ma_etf": "SPY", "lay": 8} if _r[0] == "etf"
           else {"ro": _r[0]})
    _ma_ro = sinh_ma.sinh(so_do_ro(_gt))["ma"]
    _cau = bat_dau.lean_ro(_gt)
    kiem(f"rổ «{_r[0]}» — câu khai nằm nguyên trong mã sinh ra", _cau in _ma_ro,
         f"— khai {_cau!r}")
# «Lấy 0» bỏ hẳn tham số thứ ba, nên câu khai cũng phải bỏ theo.
kiem("«lấy 0» — câu khai bỏ hàm lọc y như mã",
     bat_dau.lean_ro({"ro": "etf", "ma_etf": "SPY", "lay": 0}) in r_ca_ro["ma"],
     f"— khai {bat_dau.lean_ro({'ro': 'etf', 'ma_etf': 'SPY', 'lay': 0})!r}")

# BA TRẠM CỦA DÂY CHUYỀN — cùng luật ấy, và đây là chỗ nó vừa cứu một lỗi đã chạy
# thật. Chỗ này từng tự ghép `self.{ham}({lop}())` ngay trong `sinh_ma`, luôn KHÔNG
# THAM SỐ, nên `StandardDeviationExecutionModel` chạy với `Resolution.MINUTE` mặc
# định và ném ngoại lệ ở nến đầu mọi sơ đồ nhịp ngày — 0 lệnh, và bảng Kết quả không
# nói gì. Nay `bat_dau.lean_day_chuyen` là một bản sự thật cho cả hai bên, và phép
# dưới đây lặp qua CẢ BA BẢNG: thêm một model là nó canh luôn.
print(NL + "  (2c) ba trạm dây chuyền — câu khai cũng là một KHÚC của mã thật")
for _ten_o, _bang in (("chia_von", bat_dau.CHIA_VON),
                      ("phong_rui_ro", bat_dau.PHONG_RUI_RO),
                      ("dat_lenh", bat_dau.DAT_LENH)):
    for _m, _nhan, *_ in _bang:
        if not _m:
            continue
        _bd2 = core.make_start_step()
        _bd2["chia_von"] = "EqualWeightingPortfolioConstructionModel"
        _bd2[_ten_o] = _m
        _th2 = core.make_lam_step(lam.LAM_TIN_HIEU, "Nên lên")
        _th2["huong"], _th2["han"] = "UP", 5
        _d2 = core.make_process_template(
            "Tram", [_bd2, _th2], [{"from": _bd2["id"], "to": _th2["id"]}])
        _ma2 = sinh_ma.sinh(_d2)["ma"]
        _thieu = [c for c in bat_dau.lean_day_chuyen(_bd2) if c not in _ma2]
        kiem(f"«{_m}» — câu khai nằm nguyên trong mã sinh ra", not _thieu,
             f"— {_thieu}")

print(NL + "  (3) chỉ báo — khai ở `on_securities_changed`, KHÔNG ở `initialize`")
# Lúc `initialize` chạy, rổ còn RỖNG: `for sym in self._ma` duyệt số không mã, nên
# chẳng chỉ báo nào được khai, và `self._cb[sym]` ném KeyError ở nến đầu.
kiem("có `on_securities_changed`",
     "def on_securities_changed(self, changes):" in m_etf)
kiem("đọc `added_securities` và `removed_securities`",
     "changes.added_securities" in m_etf and "changes.removed_securities" in m_etf)
kiem("KHÔNG khai chỉ báo trong `initialize`",
     "for sym in self._ma:" not in m_etf.split("def on_data")[0])
# `set_warm_up` VÔ DỤNG với chỉ báo sinh giữa đường — nó chặn N nến ĐẦU, mà mã vào
# rổ ở tháng thứ năm thì nó đã hết tác dụng từ lâu.
kiem("KHÔNG dùng `set_warm_up`", "set_warm_up" not in m_etf)
kiem("dùng `warm_up_indicator` cho từng mã",
     "self.warm_up_indicator(s.symbol, _cb, Resolution.DAILY)" in m_etf)

print(NL + "  (4) `self._ma` đọc lại MỖI NHỊP từ `active_securities`")
kiem("đọc từ `active_securities`", "self.active_securities" in m_etf)
kiem("đọc trong `on_data`, không trong `initialize`",
     "active_securities" not in m_etf.split("def on_data")[0])

print(NL + "  (5) HAI BẪY LẶNG của nhánh này")
# BẪY 1: `self._ma` lọc `if kvp.key in self._cb`, nên `on_securities_changed` PHẢI
# ghi `self._cb[sym] = {}` kể cả khi sơ đồ KHÔNG CÓ chỉ báo nào. Thiếu dòng ấy thì
# `self._cb` rỗng mãi, `_ma` lọc ra rỗng, cỗ máy chạy đủ mọi nến mà không làm gì.
r_kho_cb = sinh_ma.sinh(so_do_ro({"ro": "kim_loai"}, co_cb=False))
m_kho_cb = r_kho_cb["ma"]
kiem("sơ đồ KHÔNG chỉ báo vẫn có `on_securities_changed`",
     "def on_securities_changed(self, changes):" in m_kho_cb)
kiem("và vẫn ghi `self._cb[s.symbol] = {}`",
     "self._cb[s.symbol] = {}" in m_kho_cb,
     "— ĐÃ ÉP: còn dòng ấy 15 lệnh, bỏ nó 0 lệnh, backtest sạch cả hai lần")
kiem("lọc và nguồn khớp nhau", "if kvp.key in self._cb" in m_kho_cb)
# BẪY 2: mã mới vào rổ mà chưa đủ nến thì chỉ báo CHƯA CHÍN, và nó vẫn đọc ra một
# con số. ĐÃ ÉP TÁI HIỆN bằng backtest thật — đây là hàng rào CÓ người vượt:
#   · mã không có dữ liệu trên máy -> `is_ready=False`, giá trị đúng 0.0;
#   · mã có dữ liệu mà lịch sử ngắn hơn chu kỳ -> `is_ready=False`, giá trị ~53,
#     một con số trông bình thường đến mức không ai nghi.
#   · `RSI(20000) < 60`: CÒN chặn = 0 lệnh; BỎ chặn = 17 lệnh khớp hết, trên một
#     chỉ báo chưa bao giờ chín. Backtest sạch cả hai lần.
kiem("có chặn `is_ready` khi sơ đồ CÓ chỉ báo",
     "if not all(x.is_ready for x in self._cb[sym].values()):" in m_etf,
     "— bỏ ra là 17 lệnh trên một chỉ báo chưa chín, đã đo")
kiem("không có chỉ báo thì KHÔNG cần chặn", "is_ready" not in m_kho_cb)
# Nhánh gõ mã sẵn KHÔNG cần chặn ấy — `set_warm_up` chặn hộ ở N nến đầu.
kiem("nhánh gõ mã sẵn vẫn dùng `set_warm_up`, không chặn `is_ready`",
     "set_warm_up" in ma and "is_ready" not in ma)

print(NL + "  (6) nhịp HẸN GIỜ cộng rổ — lịch không neo vào mã nào được")
# `self._ma[0]` trên một rổ là IndexError ở dòng đầu `initialize` — rổ lúc ấy rỗng.
r_tuan = sinh_ma.sinh(so_do_ro({"ro": "kim_loai"}, nhip="tuan"))
m_tuan = r_tuan["ma"]
kiem("sinh xong không lỗi", r_tuan["ok"])
kiem("KHÔNG có `self._ma[0]`", "self._ma[0]" not in m_tuan,
     "— rổ lúc `initialize` còn rỗng: IndexError ngay dòng đầu")
kiem("dùng câu lịch KHÔNG MÃ của LEAN",
     "self.date_rules.week_start()" in m_tuan
     and "self.time_rules.after_market_open(30)" in m_tuan)
d_tuan, k_tuan = so_do_rsi(nhip="tuan")
kiem("mà gõ mã sẵn thì vẫn neo vào mã",
     "self._ma[0]" in sinh_ma.sinh(d_tuan)["ma"])

# Nhịp LẠ (file sửa tay): bộ sinh mã vẫn đi tiếp để bày ra phần sinh được, nên câu
# lịch phải rơi về `on_data` chứ không được là chuỗi RỖNG — chuỗi rỗng đi qua
# `hen[:-1]` thành một câu `schedule.on` cụt đầu, và file sinh ra không biên dịch nổi.
d_la, k_la = so_do_rsi()
k_la[0]["nhip"] = "nhip_bia_ra"
r_la = sinh_ma.sinh(core.make_process_template("x", k_la, d_la["edges"]))
kiem("nhịp LẠ thì báo lỗi, không sinh câu lịch cụt",
     not r_la["ok"] and "schedule" not in r_la["ma"])
loi_la = ""
try:
    compile(r_la["ma"], "<la>", "exec")
except SyntaxError as e:
    loi_la = f"dòng {e.lineno}: {e.msg}"
kiem("và phần sinh được vẫn biên dịch nổi", not loi_la, f"— {loi_la}")

print(NL + "  (7) rổ thì KHÔNG khối nào gõ được tên mã")
# Rổ gồm mã nào là chuyện LEAN quyết lại mỗi ngày, nên app không có danh sách ấy để
# đối chiếu. Báo LỖI, và câu báo phải nói đúng chuyện đó — chứ bảo "thêm mã ấy vào
# khối Bắt đầu" là bảo người chơi làm một việc hộp thoại không có chỗ để làm.
d_ma = so_do_ro({"ro": "etf", "ma_etf": "SPY", "lay": 8})
for s in d_ma["steps"]:
    if s.get("type") == lam.LAM_TIN_HIEU:
        s["ma"] = "AAPL"
r_ma = sinh_ma.sinh(d_ma)
kiem("gõ tên mã trên một rổ -> LỖI", not r_ma["ok"])
kiem("và câu báo nói đúng VÌ SAO",
     any("LEAN quyết lại mỗi ngày" in p["message"] for p in r_ma["van_de"]),
     f"— {[p['message'][:60] for p in r_ma['van_de'] if p['severity'] == 'error']}")

# ---------------------------------------------------------------------------
print(NL + "▸ ⚠ TRÍ NHỚ — ô nhớ phải DỰNG SẴN, và rổ động cũng phải có")
# ---------------------------------------------------------------------------
# Đọc một ô nhớ trước khi ghi lần đầu xảy ra ngay nến ĐẦU TIÊN của mọi sơ đồ có trí
# nhớ. Dựng thiếu thì `KeyError` giữa lượt chạy, hoặc tệ hơn một `None` lọt vào phép
# so rồi ném `TypeError` — cả hai đều ĐỨT backtest chứ không phải sai số.


def _so_do_nho(ro=False, ban_dau=False):
    b = core.make_start_step()
    b["ma"] = {"ro": "qc500"} if ro else [{"ma": "SPY", "loai": "equity"}]
    b["nhip"] = "ngay"
    b["chay_cho"] = "moi_ma"
    b["tri_nho"] = [{"ma": "nho_ma_co_1", "nhan": "đang chờ", "ban_dau": ban_dau},
                    {"ma": "nho_so_1", "nhan": "đếm", "ban_dau": 7}]
    h = core.make_hoi_step("hoi_tri_nho")
    h["name"] = "dang cho?"
    h["dieu_kien"] = [core.make_dieu_kien("nho_ma_co_1", "la")]
    a = core.make_lam_step(lam.LAM_GHI_NHO)
    a["name"] = "cong"
    a["o_nho"], a["cach"] = "nho_so_1", "cong"
    a["gia_tri"] = {"so": 1}
    st = [b, h, a]
    for i, x in enumerate(st):
        x["pos"] = [[-220, 0], [160, 0], [540, 0]][i]
    return sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "nho",
                         "steps": st,
                         "edges": [{"from": b["id"], "to": h["id"], "port": "out"},
                                   {"from": h["id"], "to": a["id"], "port": "out"}]})


_kq = _so_do_nho()
kiem("dựng đủ 6 ô nhớ CHUNG + 6 ô MẪU theo mã",
     _kq["ma"].count("'co_3':") == 2 and "self._nho_mau = {" in _kq["ma"],
     "— thiếu là `KeyError` giữa lượt chạy")
kiem("giá trị ban đầu người dùng khai đi vào mã", "'so_1': 7" in _kq["ma"],
     f"— {[l.strip() for l in _kq['ma'].splitlines() if '_nho =' in l]}")
# ⚠ RỔ ĐỘNG: lúc `initialize` chưa mã nào có mặt. Dựng ô nhớ theo `self._ma` là dựng
# một dict RỖNG, rồi mã đầu tiên vào rổ là `KeyError`. Nên phải qua `_nho_cua`.
_kq_ro = _so_do_nho(ro=True)
kiem("rổ ĐỘNG cũng có `_nho_cua` tự đẻ ô nhớ cho mã mới vào rổ",
     "def _nho_cua(self, sym):" in _kq_ro["ma"]
     and "self._nho_ma = {}" in _kq_ro["ma"], "— rổ động mà dựng theo `self._ma`"
     " thì mã đầu tiên vào rổ là KeyError")
kiem("và KHÔNG dựng ô nhớ theo `self._ma`",
     "for sym in self._ma}" not in _kq_ro["ma"].split("def _nho_cua")[0],
     "— `self._ma` lúc initialize của rổ động là RỖNG")
# Chỗ ĐỌC và chỗ GHI phải trỏ vào CÙNG một biểu thức — hai chuỗi khác nhau thì ghi
# một nơi đọc một nẻo, và backtest chạy trơn tru với một cờ không bao giờ bật.
_doc = [l for l in _kq["ma"].splitlines() if "if (" in l and "_nho" in l]
_ghi = [l for l in _kq["ma"].splitlines() if "_nho" in l and "] =" in l
        and "self._nho =" not in l and "_nho_mau" not in l and "_nho_ma[sym]" not in l]
kiem("chỗ ĐỌC và chỗ GHI dùng cùng một biểu thức ô nhớ",
     bool(_doc) and bool(_ghi)
     and "self._nho_cua(sym)['co_1']" in _doc[0]
     and "self._nho['so_1']" in _ghi[0],
     f"— đọc {_doc[:1]} · ghi {_ghi[:1]}")
# ⚠ SỐNG QUA LƯU/MỞ — cùng bài học với `ghim` và chuỗi ghép.
_bd = core.make_start_step()
_bd["tri_nho"] = [{"ma": "nho_co_1", "nhan": "đang chờ", "ban_dau": False}]
kiem("ô nhớ khai ở khối Bắt đầu SỐNG qua `chuan_hoa_khoi`",
     len(bat_dau.tri_nho_cua(core.chuan_hoa_khoi(_bd))) == 1,
     f"— {bat_dau.tri_nho_cua(core.chuan_hoa_khoi(_bd))}")
# Hai ô cùng mã là hai cái tên cho MỘT chỗ nhớ — ghi vào cái này, đọc ra ở cái kia.
_bd2 = core.make_start_step()
_bd2["tri_nho"] = [{"ma": "nho_co_1", "nhan": "A"}, {"ma": "nho_co_1", "nhan": "B"},
                   {"ma": "khong_co_that", "nhan": "C"}]
kiem("mã TRÙNG và mã LẠ bị gạt khỏi danh sách ô nhớ",
     [x["nhan"] for x in bat_dau.tri_nho_cua(_bd2)] == ["A"],
     f"— {[x['nhan'] for x in bat_dau.tri_nho_cua(_bd2)]}")

# ---------------------------------------------------------------------------
print(NL + "▸ ⚠ GHÉP NHIỀU THÀNH PHẦN — tổng có trọng số, nối TRÁI→PHẢI")
# ---------------------------------------------------------------------------
# Ba ví dụ trong tập mẫu chấm điểm bằng một TỔNG CÓ TRỌNG SỐ:
#     0,25×ROC(63) + 0,35×ROC(126) + 0,40×ROC(252) − 0,20×biến_động
# Bản trước ghép đúng MỘT phép (hai vế), nên câu ấy không nói được.


def _ve_chuoi():
    d = core.make_dieu_kien("roc", ">", 0, tham_so={"n": 63})
    d["trai"]["he_so"] = 0.25
    d["trai"]["ghep"] = [
        {"phep": "+", "he_so": 0.35, "ma_dl": "roc", "tham_so": {"n": 126}},
        {"phep": "+", "he_so": 0.40, "ma_dl": "roc", "tham_so": {"n": 252}},
        {"phep": "-", "he_so": 0.20, "ma_dl": "std", "tham_so": {"n": 20}},
    ]
    return d


def _ma_cua(dk):
    b = core.make_start_step()
    b["ma"] = [{"ma": "SPY", "loai": "equity"}]
    b["nhip"] = "ngay"
    b["chay_cho"] = "moi_ma"
    h = core.make_hoi_step("hoi_thi_truong")
    h["name"] = "dk"
    h["dieu_kien"] = [dk]
    a = core.make_lam_step(lam.LAM_DAT_TY_TRONG)
    a["name"] = "mua"
    a["ty_trong"] = 0.3
    st = [b, h, a]
    for i, x in enumerate(st):
        x["pos"] = [[-220, 0], [160, 0], [540, 0]][i]
    return sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "ghep",
                         "steps": st,
                         "edges": [{"from": b["id"], "to": h["id"], "port": "out"},
                                   {"from": h["id"], "to": a["id"], "port": "out"}]})


_kq = _ma_cua(_ve_chuoi())
_dong = next((l.strip() for l in _kq["ma"].splitlines() if "if (" in l), "")
kiem("bốn thành phần đều có mặt trong mã",
     all(x in _dong for x in ("roc_63", "roc_126", "roc_252", "std_20")),
     f"— {_dong[:120]}")
# ⚠ HỆ SỐ PHẢI NHÂN VÀO TỪNG THÀNH PHẦN, không thành một phép `*` riêng trong chuỗi.
# Nối trái→phải không có thứ tự ưu tiên, nên `0,25 × a + 0,35 × b` viết thành bốn
# thành phần sẽ ra `((0,25×a)+0,35)×b` — sai, và sai LẶNG vì vẫn ra một con số.
for _h, _k in ((0.25, "roc_63"), (0.35, "roc_126"), (0.4, "roc_252"),
               (0.2, "std_20")):
    kiem(f"hệ số {_h} nhân THẲNG vào {_k}",
         f"({_h} * self._cb[sym][{_k!r}].current.value)" in _dong,
         f"— {_dong[:150]}")
# ⚠ ĐÓNG NGOẶC TỪNG BƯỚC, không nhờ Python tự ưu tiên: thứ người dùng ĐỌC trên hàng
# điều kiện và thứ LEAN CHẠY phải là một.
#
# Canh bằng cách TÍNH THỬ RA SỐ, không bằng cách dò chuỗi ký tự. Dò chuỗi thì giòn:
# đổi một dấu cách là phép soát đỏ, mà đổi cả cách tính thì nó vẫn xanh. Dựng một vế
# toàn SỐ rồi `eval` cái biểu thức sinh ra, so với kết quả nối trái→phải tính tay.
_so = {"so": 2, "he_so": 3, "ghep": [        # 3×2 = 6
    {"phep": "+", "he_so": 5, "so": 4},      # 6 + 5×4 = 26
    {"phep": "*", "he_so": 1, "so": 2},      # 26 × 2  = 52
    {"phep": "-", "he_so": 1, "so": 2},      # 52 − 2  = 50
]}
# So bằng `==` rồi `eval` CẢ CÂU: khỏi phải cắt chuỗi để lấy riêng vế trái, mà cắt
# chuỗi thì lại là dò ký tự — đúng cái vừa muốn tránh.
# Nối trái→phải ra 50. Theo thứ tự ưu tiên của Python thì `3*2 + 5*4 * 2 - 2` = 44.
# Hai số khác nhau, nên phép này phân biệt được đúng cái cần phân biệt.
_dk_so = {"trai": _so, "phep": "==", "phai": {"so": 50}}
_bt = next((l.strip() for l in _ma_cua(_dk_so)["ma"].splitlines()
            if "if (" in l), "")
_bt = _bt[len("if "):].rstrip(":").strip()
kiem("tính ra ĐÚNG kết quả nối trái→phải (50)",
     eval(_bt) is True,          # noqa: S307 — biểu thức do CHÍNH TA sinh ra
     f"— {_bt[:130]}")
# THẺ phải tả ĐÚNG cái mã làm — kể cả dấu ngoặc.
_chu = core.mo_ta_dieu_kien(_ve_chuoi())
kiem("thẻ nói đủ bốn thành phần",
     all(x in _chu for x in ("0.25", "0.35", "0.4", "0.2", "ROC(63)",
                             "ROC(126)", "ROC(252)")),
     f"— {_chu}")
kiem("và thẻ KHÔNG in hệ số hai lần", "0.35 × 0.35" not in _chu, f"— {_chu}")
# ⚠ FILE CŨ: `ghep` là một DICT. Mất nhánh này là mọi sơ đồ đã lưu mất nửa điều kiện
# — thẻ vẫn vẽ, mã vẫn sinh, chỉ thiếu mất phần chia.
_cu = core.make_dieu_kien("gia", "<=", 0.97)
_cu["trai"]["ghep"] = {"phep": "/", "ma_dl": "max", "tham_so": {"n": 60}}
_dong_cu = next((l.strip() for l in _ma_cua(_cu)["ma"].splitlines()
                 if "if (" in l), "")
kiem("ghép kiểu CŨ (một dict) vẫn sinh ra đúng phép chia",
     "max_60" in _dong_cu and "else 0" in _dong_cu, f"— {_dong_cu[:130]}")
kiem("và thẻ của nó vẫn như cũ, không thừa dấu ngoặc",
     core.mo_ta_dieu_kien(_cu).startswith("Giá hiện tại / Cao nhất"),
     f"— {core.mo_ta_dieu_kien(_cu)}")

# ⚠ CHUỖI PHẢI SỐNG QUA LƯU/MỞ — và phép soát này tồn tại vì đã dính một lần rồi.
# `ghim` từng là một dict đặt trên khối, mà `ghim` lại là khoá CŨ của canvas nằm
# trong `KHOA_CANVAS`, nên `chuan_hoa_khoi` gỡ sạch: ghim sống trong hộp thoại, chết
# lúc lưu. Hàng rào hồi ấy mù vì nó đặt rồi đọc lại NGAY, không đi qua chuẩn hoá.
# Nên lần này: đẩy nguyên khối qua `chuan_hoa_khoi` rồi mới đếm.
_khoi = core.make_hoi_step("hoi_thi_truong")
_khoi["name"] = "diem"
_khoi["dieu_kien"] = [_ve_chuoi()]
_sau = core.chuan_hoa_khoi(_khoi)
_ve_sau = (_sau.get("dieu_kien") or [{}])[0].get("trai") or {}
kiem("chuỗi ghép SỐNG qua `chuan_hoa_khoi` — đủ ba thành phần",
     len(hoi.ds_ghep(_ve_sau)) == 3, f"— còn {len(hoi.ds_ghep(_ve_sau))}")
kiem("và hệ số của vế gốc cũng sống", _ve_sau.get("he_so") == 0.25,
     f"— {_ve_sau.get('he_so')}")
kiem("hệ số của từng thành phần cũng sống",
     [hoi.he_so_cua(t) for t in hoi.ds_ghep(_ve_sau)] == [0.35, 0.4, 0.2],
     f"— {[hoi.he_so_cua(t) for t in hoi.ds_ghep(_ve_sau)]}")

# ---------------------------------------------------------------------------
print(NL + "▸ ⚠ LÀM NÓNG phải tính cả LỊCH SỬ MÀ MODEL CHIA VỐN ĐÒI")
# ---------------------------------------------------------------------------
# Làm nóng trước nay chỉ đếm chu kỳ CHỈ BÁO. Một sơ đồ không chỉ báo nào thì không
# làm nóng gì, nên chặn `if self.is_warming_up: return` luôn mở — và nhịp HẸN GIỜ có
# thể bắn ngay nến đầu, lúc chưa có lịch sử nào.
#
# ĐÃ ÉP TÁI HIỆN: BTCUSD · nhịp THÁNG · RiskParity ném
#     ArgumentException: Argument "numberOfVariables" must be a positive integer
# rồi ĐỨT cả lượt. Cùng sơ đồ ấy đổi sang nhịp NGÀY thì chạy 396 lệnh — tức lỗi không
# nằm ở model, nó nằm ở chỗ ta để model chạy trước khi có dữ liệu.
#
# LẶP QUA CHÍNH TỪ ĐIỂN: thêm một model đọc lịch sử vào `CHIA_VON_LAM_NONG` là phép
# này canh luôn.
def _so_do_chia_von(model):
    """Sơ đồ KHÔNG chỉ báo nào, nhịp hẹn giờ — ca mỏng nhất."""
    b = core.make_start_step()
    b["ma"] = [{"ma": "SPY", "loai": "equity"}, {"ma": "QQQ", "loai": "equity"}]
    b["nhip"] = "thang_dau"
    b["quy_tac_gio"] = "sau_mo"
    b["so_phut"] = 30
    b["chay_cho"] = "moi_ma"
    b["chia_von"] = model
    b["dat_lenh"] = "ImmediateExecutionModel"
    h = core.make_hoi_step("hoi_thi_truong")
    h["name"] = "co gia"
    h["dieu_kien"] = [core.make_dieu_kien("gia", ">", 0)]
    t = core.make_lam_step(lam.LAM_TIN_HIEU)
    t["name"] = "len"
    t["huong"], t["han"] = "UP", 31
    st = [b, h, t]
    for i, x in enumerate(st):
        x["pos"] = [[-220, 0], [160, 0], [540, 0]][i]
    return {"schema": 1, "type": "strategy", "name": "lam nong", "steps": st,
            "edges": [{"from": b["id"], "to": h["id"], "port": "out"},
                      {"from": h["id"], "to": t["id"], "port": "out"}]}


for _m, _n in sorted(bat_dau.CHIA_VON_LAM_NONG.items()):
    _kq = sinh_ma.sinh(_so_do_chia_von(_m))
    _w = re.search(r"self\.set_warm_up\((\d+)\)", _kq["ma"] if _kq["ok"] else "")
    kiem(f"«{_m[:30]}» đòi {_n} nến -> có làm nóng đủ",
         bool(_w) and int(_w.group(1)) >= _n,
         f"— {_w.group(0) if _w else 'KHÔNG có set_warm_up'}")
# Và model KHÔNG đọc lịch sử thì đừng làm nóng thừa: chờ 252 nến cho một sơ đồ chia
# đều là cắt mất một năm đầu của backtest mà chẳng vì cái gì.
_kq = sinh_ma.sinh(_so_do_chia_von("EqualWeightingPortfolioConstructionModel"))
kiem("model không đọc lịch sử thì KHÔNG làm nóng thừa",
     "set_warm_up" not in _kq["ma"],
     "— chia đều mà chờ 252 nến là cắt mất một năm đầu")

print(f"\n{'=' * 52}\n  {dung} đúng, {sai} sai\n{'=' * 52}")
sys.exit(1 if sai else 0)
