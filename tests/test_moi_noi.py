"""MỐI NỐI — chỗ hai bảng phải dài bằng nhau, mà không ai đứng so.

VÌ SAO CÓ BÀI NÀY
-----------------
Dựng lại ví dụ 1 lôi ra tám chỗ hỏng trong một buổi. Nhìn riêng từng cái thì tám
lỗi khác nhau; xếp cạnh nhau thì là MỘT lỗi lặp tám lần:

    app ghép từ nhiều BẢNG TRA phải dài bằng nhau,
    mà mỗi chỗ tra đều có một LỐI RƠI VỀ êm ái.

Nên bảng nào tụt lại sau thì không VỠ — nó IM:

    mo_ta_lam        tra theo loại việc   -> rơi về ["?"]        thẻ không nói gì
    _ve_dieu_kien    tra theo khoá của vế -> bỏ qua khoá lạ      THẺ NÓI DỐI
    ICON_HANH_DONG   tra theo `type`      -> `?? ''` -> null     icon biến mất
    CHIA_VON         —                    -> model bỏ mọi insight  0 LỆNH
    _cau_lam         `t == LAM_VE_BANG`   -> không điền ô mới    núm không đi đâu
    Icon             tra theo tên icon    -> `return null`       ô trống
    o_lam            tra theo tên ô       -> mặc định từ điển    hai nơi cùng "đúng"

Mấy lối rơi về ấy VIẾT CÓ CHỦ Ý (xem docstring `core.o_lam`: để file cũ mở được).
Chúng đúng. Nhưng chính độ lượng ấy biến "người viết quên một nhánh" thành "không
có gì xảy ra" — cơ chế chống vỡ cũng là cơ chế giấu lỗi.

Mấy bài kiểm còn lại soi từng bảng với CHÍNH NÓ ("khối này có khai `lean` không?").
Lỗi thì không nằm trong các hộp, nó nằm ở MỐI NỐI giữa hai hộp. Bài này đứng đúng
chỗ ấy: với mỗi cặp bảng phải khớp nhau, nó LẶP QUA CHÍNH TỪ ĐIỂN — thêm một khối,
một đại lượng, một icon là nó biết ngay, không phải sửa bài kiểm.

LỐI THOÁT HỢP LỆ: trường `tat`. "Bày ra nhưng nói rõ chưa dùng được và vì sao" là
cách ĐÚNG để một mối nối còn dở — họ «Hỏi doanh nghiệp» và khối «Báo tin» dùng nó.
Chết lặng thì không.

Không mở cửa sổ, không nối mạng -> chạy được ở bất cứ đâu.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import bat_dau, core, hoi, lam, sinh_ma  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dung = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dung, sai
    if dk:
        dung += 1
        print(f"  ✔ {ten} {chi_tiet}")
    else:
        sai += 1
        print(f"  ✘ {ten} {chi_tiet}")


def doc(*phan):
    return io.open(os.path.join(GOC, *phan), encoding="utf-8").read()


def moi_tsx():
    for r, _d, fs in os.walk(os.path.join(GOC, "webui", "src")):
        for f in fs:
            if f.endswith(".tsx"):
                yield f, io.open(os.path.join(r, f), encoding="utf-8").read()


# ---------------------------------------------------------------------------
# Mỗi LOẠI KHỐI phải đi hết dây: tạo -> thẻ -> soát -> sinh mã -> icon
# ---------------------------------------------------------------------------
print("▸ MỐI NỐI 1 — mỗi loại việc phải đi hết dây, không khâu nào bỏ nó lại")


def _so_do_mot_khoi(ma_loai):
    """Sơ đồ nhỏ nhất CHẠY ĐƯỢC chứa đúng một khối việc. -> (steps, edges)."""
    bd = core.make_start_step()
    bd["ma"] = [{"ma": "SPY", "loai": "equity"}]
    # Khối «Phát tín hiệu» đòi khối Bắt đầu chọn model chia vốn (`soat_day_chuyen`),
    # nên điền sẵn — ở đây ta soi MỐI NỐI, không soi luật ấy.
    bd["chia_von"] = "EqualWeightingPortfolioConstructionModel"
    h = core.make_hoi_step("hoi_thi_truong")
    h["dieu_kien"] = [core.make_dieu_kien("gia", ">", 1)]
    t = core.make_lam_step(ma_loai)
    return ([bd, h, t],
            [{"from": bd["id"], "to": h["id"], "port": "out"},
             {"from": h["id"], "to": t["id"], "port": "out"}])


_thieu_the, _khong_sinh = [], []
for _ma in lam.LOAI_LAM:
    _st, _ed = _so_do_mot_khoi(_ma)
    _the = core.mo_ta_lam(_st[-1])
    if not _the or _the == ["?"] or any(str(x).strip() == "?" for x in _the):
        _thieu_the.append(_ma)
    _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "D",
                        "steps": _st, "edges": _ed})
    # Khối còn ô bắt buộc để trống thì soát kêu — đó là ĐÚNG, không tính là hỏng.
    # Chỉ tính hỏng khi bộ sinh mã nói THẲNG là nó không biết viết gì cho loại này.
    if any("Chưa sinh được khối loại" in v["message"] for v in _kq["van_de"]):
        _khong_sinh.append(_ma)
kiem(f"lặp qua cả {len(lam.LOAI_LAM)} loại việc trong từ điển", len(lam.LOAI_LAM) >= 9)
kiem("không loại nào ra thẻ «?»", not _thieu_the, f"— {_thieu_the}")
kiem("không loại nào bộ sinh mã bó tay", not _khong_sinh, f"— {_khong_sinh}")

print("\n▸ MỐI NỐI 2 — tên ICON Python khai × bộ icon giao diện có")
# ĐÃ DÍNH THẬT: họ «Hỏi lịch» khai icon "delay", mà `Icon.tsx` không có tên ấy —
# `Icon` trả `null`, nên chỗ đó trống trơn. Không lỗi, không cảnh báo.
_icon_src = doc("webui", "src", "components", "Icon.tsx")
_than = _icon_src.split("const HINH", 1)[1].split("\nexport default", 1)[0]
CO_ICON = set(re.findall(r"^\s*'?([A-Za-z][A-Za-z0-9-]*)'?\s*:", _than, re.M))
kiem("đọc được bộ icon", len(CO_ICON) > 20, f"— {len(CO_ICON)} cái")
_khai = {}
for _ten, _d in list(lam.LOAI_LAM.items()) + list(hoi.LOAI_HOI.items()):
    if _d.get("icon"):
        _khai.setdefault(_d["icon"], []).append(_ten)
_ma_icon = {i: c for i, c in _khai.items() if i not in CO_ICON}
kiem("mọi icon Python khai đều có thật", not _ma_icon, f"— {_ma_icon}")
_tsx_icon = set()
for _f, _s in moi_tsx():
    _tsx_icon |= set(re.findall(r"<Icon(?:Net)?\s+name=[\"']([A-Za-z0-9-]+)", _s))
kiem("mọi icon giao diện gọi thẳng cũng có thật",
     not (_tsx_icon - CO_ICON), f"— {sorted(_tsx_icon - CO_ICON)}")

print("\n▸ MỐI NỐI 3 — icon của MỖI loại khối: một chỗ khai, một chỗ bày")
# ĐÃ DÍNH THẬT, và đây là chỗ bẩn nhất. Giao diện từng giữ bảng tra RIÊNG của nó
# (`ICON_HANH_DONG`) với năm khoá từ một THIẾT KẾ CŨ — `check_cond`, `vao_lenh`,
# `sua_lenh`, `dat_co`, `quay_ve`. Loại khối đã đổi tên hết, nên phép tra luôn trượt,
# rơi về `?? ''`, `Icon` trả `null`, và MỌI dòng trong thân thẻ mất icon.
#
# Bản chữa KHÔNG phải sửa lại năm khoá ấy — là BỎ HẲN bảng thứ hai. Nay `core.the_buoc`
# gửi `icon` kèm từng dòng, lấy từ chính từ điển đã khai nó. Nên bài này canh hai thứ:
# mọi loại đều ra được icon CÓ THẬT, và giao diện không dựng lại bảng tra nào nữa.
_moi_loai = (list(lam.LOAI_LAM) + list(hoi.LOAI_HOI)
             + [core.make_quay_ve_step().get("type")])
_khong_icon = [l for l in _moi_loai if not core.icon_cua(l)]
kiem(f"cả {len(_moi_loai)} loại khối đều có icon", not _khong_icon, f"— {_khong_icon}")
_icon_ma = {l: core.icon_cua(l) for l in _moi_loai if core.icon_cua(l) not in CO_ICON}
kiem("và icon nào cũng có thật trong bộ icon", not _icon_ma, f"— {_icon_ma}")
_dong_the = core.the_buoc(core.make_lam_step(lam.LAM_TIN_HIEU))["lines"]
kiem("`the_buoc` gửi icon kèm từng dòng", all("icon" in d for d in _dong_the),
     f"— {_dong_the}")
_bang_hai = {}
for _f, _s in moi_tsx():
    # Một `Record<string, string>` mà khoá là tên loại khối chính là bảng tra thứ hai
    # mọc lại. Tìm tên loại ở BẤT CỨ ĐÂU trong file, không chỉ trong nháy: khoá của
    # một object JS viết trần (`lam_tin_hieu: 'branch'`) thì không có nháy nào, và
    # đúng dạng ấy đã lọt qua bản đầu của bài kiểm này.
    for _l in list(lam.LOAI_LAM) + list(hoi.LOAI_HOI):
        if re.search(r"\b%s\b" % re.escape(_l), _s):
            _bang_hai.setdefault(_f, []).append(_l)
kiem("giao diện KHÔNG gõ tên loại khối ra để tự tra", not _bang_hai,
     f"— {_bang_hai}")

print("\n▸ MỐI NỐI 4 — cả kho ĐẠI LƯỢNG × sinh mã · thẻ · soát")
# 68 đại lượng đi qua ba hàm. Một cái rơi về lối im lặng ở bất kỳ hàm nào thì người
# dùng vẽ ra một điều kiện VÔ NGHĨA mà soát vẫn sạch.
_kho = hoi.tu_dien()["kho"]
_hong = []
for _d in _kho:
    _ve = {"ma_dl": _d["ma"]}
    if _d["tham_so"]:
        _ve["tham_so"] = {t["ten"]: t["mac_dinh"] for t in _d["tham_so"]}
    if _d.get("duong"):
        _ve["duong"] = _d["duong"][0][0]
    _dk = {"trai": _ve, "phep": "la" if _d["kieu"] == hoi.KIEU_CO_KHONG else ">",
           "phai": {"so": 1}}
    _st, _ed = _so_do_mot_khoi(lam.LAM_TIN_HIEU)
    _st[1]["dieu_kien"] = [_dk]
    _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "D",
                        "steps": _st, "edges": _ed})
    _dong = next((l.strip() for l in _kq["ma"].splitlines()
                  if l.strip().startswith("if (")), "")
    _vd = []
    if not _kq["ok"]:
        _vd.append(_kq["van_de"][0]["message"][:60])
    if not _dong:
        _vd.append("không ra biểu thức")
    if "?" in core.mo_ta_dieu_kien(_dk):
        _vd.append(f"thẻ nói «{core.mo_ta_dieu_kien(_dk)}»")
    if core.soat_khoi_hoi(_st[1]):
        _vd.append("soát kêu dù khối điền đủ")
    if _vd:
        _hong.append((_d["ma"], _vd))
kiem(f"lặp qua cả {len(_kho)} đại lượng", len(_kho) >= 60)
kiem("không đại lượng nào rơi về lối im lặng", not _hong, f"— {_hong[:4]}")

print("\n▸ MỐI NỐI 5 — ô người dùng VẶN × câu LEAN thật sự gửi đi")
# Câu `lean` là thứ DUY NHẤT đi sang LEAN. Ô nào không có mặt trong đó là núm giả:
# vặn thoải mái, không đổi gì, không báo gì. Cùng họ với nút «Dừng» không có CSS —
# cái nhìn thấy thì có, cái nối vào thì không.
_nut_gia = []
for _ma, _d in lam.LOAI_LAM.items():
    _theo = _d.get("theo_loai") or {}
    _mau = _d["lean"] + "".join(v["lean"] for v in _theo.values())
    _o_phu = {o["ten"] for v in _theo.values() for o in v["o"]}
    # `ma` đi vào mẫu dưới tên `{sym}`; `tag` do bộ sinh mã tự điền; ô CHỌN cầm lái
    # thì chọn luôn cả câu LEAN (`theo_loai`) nên không nằm trong câu.
    _lai = next((o["ten"] for o in _d["o"] if o["kieu"] == lam.O_CHON), None) if _theo else None
    for _o in _d["o"]:
        _t = _o["ten"]
        if _t in ("tag", "ma") or _t == _lai or _t in _o_phu:
            continue
        if ("{%s}" % _t) not in _mau:
            _nut_gia.append(f"{_ma}.{_t}")
kiem("không ô nào của khối việc là núm giả", not _nut_gia, f"— {_nut_gia}")
_bd_gia = []
_doc_sm = doc("cat_studio", "sinh_ma.py") + doc("cat_studio", "bat_dau.py")
for _o in bat_dau.O_BAT_DAU:
    if f'"{_o["ten"]}"' not in _doc_sm and f"'{_o['ten']}'" not in _doc_sm:
        _bd_gia.append(_o["ten"])
kiem("không ô nào của khối Bắt đầu là núm giả", not _bd_gia, f"— {_bd_gia}")

print("\n▸ MỐI NỐI 6 — lớp CSS giao diện DÙNG × luật CSS thật sự có")
# Bài `test_giao_dien.py` canh BIẾN css ma. Nhưng LỚP ma thì không ai canh — nên nút
# «Dừng backtest» mang lớp `.nut-dung` không có luật nào và trông y hệt nút «Ẩn hộp
# này», trong khi comment ngay trên nó giải thích đúng lý do phải khác nhau: "một cái
# giết tiến trình LEAN còn một cái chỉ cất hộp đi". Lý do viết rồi, cái khác nhau thì
# chưa bao giờ viết.
_css = doc("webui", "src", "app.css") + doc("webui", "src", "theme.css")
CO_LOP = set(re.findall(r"\.([A-Za-z][A-Za-z0-9-]*)", _css))
#: Lớp của @xyflow/react — thư viện tự hiểu, app không được đặt luật cho chúng.
LOP_THU_VIEN = {"nodrag", "nopan", "nowheel"}
def _gia_tri_className(s):
    """Cắt ĐÚNG giá trị của mỗi `className=` -> [chuỗi].

    ⚠ Phải cắt theo ngoặc khớp nhau, không quét tới hết dòng: trên cùng một dòng còn
    `inputMode="decimal"`, `loai === 'equity'`… và bài kiểm sẽ kêu oan vì chúng.
    Bài kiểm kêu oan là bài kiểm sớm muộn bị bỏ qua, mà bỏ qua thì nó hết canh."""
    ra = []
    for m in re.finditer(r"className=", s):
        i = m.end()
        if i >= len(s):
            continue
        if s[i] == '"':
            j = s.find('"', i + 1)
            if j > 0:
                ra.append(s[i + 1:j])
        elif s[i] == "{":
            sau, j = 1, i + 1
            while j < len(s) and sau:
                sau += {"{": 1, "}": -1}.get(s[j], 0)
                j += 1
            ra.append(s[i + 1:j - 1])
    return ra


_lop_ma = {}
for _f, _s in moi_tsx():
    for _gt in _gia_tri_className(_s):
        # Trong biểu thức thì CHỈ chuỗi trong nháy mới là tên lớp (`hien?.ma` không
        # phải), và bỏ chuỗi đứng sau phép so sánh (`=== 'warning'` không phải).
        for _lit in re.finditer(r"(['\"])([^'\"]*)\1", _gt) if "'" in _gt or '"' in _gt \
                else [re.match(r"()(.*)", _gt, re.S)]:
            if re.search(r"[=!]==?\s*$", _gt[:_lit.start()]):
                continue
            for _c in _lit.group(2).split():
                if (re.fullmatch(r"[a-z][a-z0-9-]{2,}", _c)
                        and _c not in CO_LOP and _c not in LOP_THU_VIEN):
                    _lop_ma.setdefault(_c, set()).add(_f)
kiem("không lớp CSS ma nào", not _lop_ma,
     f"— {({k: sorted(v) for k, v in _lop_ma.items()})}")

print("\n▸ MỐI NỐI 7 — thứ BÀY RA mà chưa chạy được phải khai `tat`, không được im")
# Đây là thuốc app đã có sẵn cho cả họ bệnh này: "bày ra nhưng nói rõ chưa dùng được
# và vì sao". Họ «Hỏi doanh nghiệp» và khối «Báo tin» dùng đúng nó. Bảng «Chia vốn»
# thì không, nên nó từng bày ba model chết lặng — chọn vào là 0 lệnh, không một lời.
_tat_rong = [k for k, v in list(lam.LOAI_LAM.items()) + list(hoi.LOAI_HOI.items())
             if v.get("tat") and not str(v["tat"]).strip()]
kiem("`tat` nào cũng kèm LÝ DO, không phải cờ trống", not _tat_rong, f"— {_tat_rong}")
_khong_nuoi = [m for m, _n in bat_dau.CHIA_VON
               if m and m not in bat_dau.CHIA_VON_DOC]
kiem("mọi model chia vốn đang bày đều khai nó đọc khe nào", not _khong_nuoi,
     f"— {_khong_nuoi}")
# CẢ BA TRẠM, một luật: bày ra thì phải khai được nó cần gì. Hai trạm sau chết vì
# THAM SỐ KHỞI TẠO không ai truyền chứ không vì khe `Insight` nào — `Standard
# DeviationExecutionModel()` mặc định `Resolution.MINUTE` nên ném ngoại lệ ngay nến
# đầu của mọi sơ đồ nhịp ngày, mà bảng Kết quả chỉ nói «0 lệnh, lãi 0%».
_ba_bang = ((bat_dau.PHONG_RUI_RO, bat_dau.PHONG_RUI_RO_DOC),
            (bat_dau.DAT_LENH, bat_dau.DAT_LENH_DOC))
_khong_khai = [m for bang, doc in _ba_bang for m, _n, *_ in bang
               if m and m not in doc]
kiem("và mọi model phòng rủi ro / đặt lệnh đang bày cũng khai nó CẦN gì",
     not _khong_khai, f"— {_khong_khai}")
# Bảng khai mà không ai đọc thì nó là một tờ giấy dán tường. `lean_day_chuyen` là
# chỗ duy nhất dựng ba câu ấy, nên nó phải là chỗ duy nhất `sinh_ma` hỏi.
_ma_sinh = io.open(os.path.join(GOC, "cat_studio", "sinh_ma.py"),
                   encoding="utf-8").read()
kiem("và bộ sinh mã hỏi MỘT cửa, không tự ghép ba câu ấy",
     "lean_day_chuyen(" in _ma_sinh
     and "set_portfolio_construction" not in _ma_sinh,
     "— hai bản ghép chữ cho một câu là hai bản để trôi khỏi nhau")

print("\n▸ MỐI NỐI 8 — giao diện BÀY LẠI thứ Python khai, không tự ghép lại")
# Luật nền: Python khai, giao diện chỉ bày. Hai nơi cùng ghép một câu thì sớm muộn
# chúng nói khác nhau, mà cái khác ấy không gây lỗi nào nên không ai thấy.
#: CHỖ CÒN NỢ — khai ra chứ không giấu, vì một hàng rào có lỗ mà không khai thì
#: chính là thứ cả bài này đang chữa. NAY RỖNG, và nó vừa rỗng xong:
#: `HopBatDau.tsx` từng tự dựng lại câu LEAN bằng TypeScript (`add_*(ma,
#: Resolution.X)` / `universe_settings.resolution = …`) trong khi `bat_dau.ham_lean`
#: bên Python làm đúng việc ấy mà CHỈ có bài kiểm gọi — hai bản một luật, không ai
#: đứng so. Nay nó hỏi cửa `khai_bat_dau`, nên hàng rào này không còn ngoại lệ nào.
#:
#: Thêm tên vào đây thì phải kèm lý do, và chiều ngược lại bên dưới sẽ bắt ngay khi
#: chỗ ấy sạch mà quên xoá — một lối miễn trừ không ai thu hồi là lối sẽ bị dùng.
CON_NO = set()
#: Mẩu LEAN nào gõ vào .tsx cũng là một BẢN SỰ THẬT THỨ HAI. Danh sách này chặn cả
#: họ chứ không chặn một chỗ: thêm một hộp thoại mới mà ghép câu LEAN trong đó là
#: bài kiểm kêu ngay, không phải chờ ai đi soi từng file.
MAU_LEAN = ("set_universe_selection", "emit_insights(", "self.set_holdings",
            "PortfolioConstructionModel", "Resolution.", "add_*(", "universe_"
            "settings.", "set_portfolio_construction(", "schedule.on(")


def _khong_chu_thich(s):
    """Bỏ `/* … */` và `// …`.

    NHẮC TÊN một câu LEAN trong chú thích KHÔNG phải là gõ cứng nó — mà chú thích
    nói rõ vì sao chỗ này không được ghép câu chính là thứ ta muốn người sau đọc
    được. Quét cả chú thích thì hàng rào này phạt đúng người đang giữ nó.
    `(?<!:)` để `https://…` trong một chuỗi không bị cắt mất phần sau."""
    return re.sub(r"(?<!:)//[^\n]*", " ", re.sub(r"/\*.*?\*/", " ", s, flags=re.S))


_sach = {f: _khong_chu_thich(s) for f, s in moi_tsx()}
_go_cung = {}
for _f, _s in _sach.items():
    for _dau in MAU_LEAN:
        if _dau in _s and _f not in CON_NO:
            _go_cung.setdefault(_f, []).append(_dau)
kiem("không file giao diện nào gõ cứng một mẩu LEAN", not _go_cung, f"— {_go_cung}")
# Chiều ngược lại: chỗ nợ phải CÒN nợ. Vá xong mà quên xoá khỏi `CON_NO` thì lần sau
# ai đó gõ cứng vào đúng file ấy sẽ lọt — một lối miễn trừ không ai thu hồi.
_no_ao = sorted(f for f in CON_NO
                if not any(d in _sach.get(f, "") for d in MAU_LEAN))
kiem("và chỗ KHAI LÀ NỢ thì phải còn nợ thật", not _no_ao,
     f"— {_no_ao} đã sạch rồi, xoá khỏi `CON_NO` đi")
# ⚠ CHIỀU CÒN LẠI, và nó mới là chiều dễ mất. "Không gõ cứng" một mình thì XOÁ SẠCH
# dòng khai đi là qua — mà hộp thoại không nói câu nào còn tệ hơn nói một câu cũ.
# Nên mỗi hộp phải CÒN chỗ bày, và chỗ ấy phải LẤY TỪ Python.
#: (file, lấy ở đâu bên Python, bày ra bằng cái gì)
BAY_LEAN = (("HopBatDau.tsx", "py.khai_bat_dau(", "<KhaiLean"),
            ("HopHanhDong.tsx", "loai.lean", "<KhaiLean"),
            ("HopDieuKien.tsx", "dl.lean", "bn-lean"))
for _hop, _nguon, _bay in BAY_LEAN:
    _ts = _sach.get(_hop, "")
    kiem(f"{_hop} lấy câu LEAN từ Python (`{_nguon}`) và bày ra (`{_bay}`)",
         _nguon in _ts and _bay in _ts,
         "— bày lại, chứ không ghép lại, và cũng không im")

print("\n▸ MỐI NỐI 10 — NÚM đã ghim × hộp Optimize thấy × mã sinh ra thật sự đọc")
# Ghim một con số làm tham số là nối ba chỗ với nhau: ô số trên sơ đồ, danh sách núm
# hộp Optimize bày, và câu `get_parameter` trong mã sinh ra. Lệch một chỗ là HỎNG
# LẶNG theo kiểu tốn nhất: optimizer chạy đủ N lượt backtest — hàng giờ — mà thuật
# toán không hề đọc tham số nó đang quét, nên N kết quả giống hệt nhau và không một
# dòng lỗi nào. Nên quét CẢ hai đầu: mọi ô số ghim được đều phải đi hết ba chặng.
_hong_ghim = []
_dem_o = 0
for _ma_loai in lam.LOAI_LAM:
    _st, _ed = _so_do_mot_khoi(_ma_loai)
    _khoi = _st[-1]
    for _chu, _ten_o, _nhan, _gt in core._o_so_cua(_khoi):
        _dem_o += 1
        _chu["ghim"] = {_ten_o: "num_thu"}
        _ds = core.ds_tham_so(_st)
        _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                            "steps": _st, "edges": _ed})
        if not any(d["ten"] == "num_thu" for d in _ds):
            _hong_ghim.append(f"{_ma_loai}.{_ten_o}: hộp Optimize KHÔNG thấy")
        elif "get_parameter('num_thu'" not in _kq["ma"]:
            _hong_ghim.append(f"{_ma_loai}.{_ten_o}: mã sinh ra KHÔNG đọc")
        _chu.pop("ghim", None)
# Và cả hai vế của khối Hỏi: con số, chu kỳ chỉ báo, tham số của đại lượng thường.
for _ma_dl in ("rsi", "bb", "max", "delay", "gia"):
    _d = hoi.dai_luong(_ma_dl)
    _dk = core.make_dieu_kien(_ma_dl, ">", 1)
    if _d["tham_so"]:
        _dk["trai"]["tham_so"] = {t["ten"]: t["mac_dinh"] for t in _d["tham_so"]}
    if _d.get("duong"):
        _dk["trai"]["duong"] = _d["duong"][0][0]
    _st, _ed = _so_do_mot_khoi(lam.LAM_TIN_HIEU)
    _st[1]["dieu_kien"] = [_dk]
    for _chu, _ten_o, _nhan, _gt in core._o_so_cua(_st[1]):
        _dem_o += 1
        _chu["ghim"] = {_ten_o: "num_thu"}
        _ds = core.ds_tham_so(_st)
        _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                            "steps": _st, "edges": _ed})
        if not any(d["ten"] == "num_thu" for d in _ds):
            _hong_ghim.append(f"{_ma_dl}.{_ten_o}: hộp Optimize KHÔNG thấy")
        elif "get_parameter('num_thu'" not in _kq["ma"]:
            _hong_ghim.append(f"{_ma_dl}.{_ten_o}: mã sinh ra KHÔNG đọc")
        _chu.pop("ghim", None)
kiem(f"quét {_dem_o} ô số ghim được", _dem_o >= 15)
kiem("ô nào ghim cũng đi hết ba chặng", not _hong_ghim, f"— {_hong_ghim[:4]}")

print("\n▸ Núm GHIM phải được THẺ KHỐI tô sáng — và cái trùng nhau phải GỘP")
# Hai việc, cùng một gốc: cái tên.
# · Thẻ không tô sáng thì «RSI(chu_ky)» trông y hệt «RSI(14)» — ghim xong nhìn cả sơ
#   đồ không biết mình đã ghim những gì. Python phải NÓI RA tên nào nằm ở dòng nào
#   (`DongThe.num`); để giao diện tự đoán là nó tô nhầm hoặc bỏ sót.
# · Gộp theo TÊN: hai chỗ cùng ghim một tên là MỘT núm, và LEAN chỉ dựng MỘT chỉ
#   báo. Không gộp thì optimizer quét hai cột cho cùng một thứ, số lượt nhân đôi vô
#   ích, mà hai cột ấy còn có thể nhận hai giá trị khác nhau — cùng một chu kỳ RSI mà
#   khối Vào dùng 14, khối Ra dùng 30.
_bd = core.make_start_step()
_bd["ma"] = [{"ma": "SPY", "loai": "equity"}]
_bd["chia_von"] = "EqualWeightingPortfolioConstructionModel"
_hs = []
for _ten_khoi in ("Vào", "Ra"):
    _h = core.make_hoi_step("hoi_thi_truong")
    _h["name"] = _ten_khoi
    _d = core.make_dieu_kien("rsi", "<=", 45, tham_so={"n": 14})
    _d["trai"]["ghim"] = {"n": "rsi_chu_ky"}
    _h["dieu_kien"] = [_d]
    _hs.append(_h)
_st = [_bd] + _hs + [core.make_lam_step(lam.LAM_TIN_HIEU)]
_ed = [{"from": _bd["id"], "to": h["id"], "port": "out"} for h in _hs]
_ed += [{"from": _hs[0]["id"], "to": _st[-1]["id"], "port": "out"}]
_ds = core.ds_tham_so(_st)
kiem("hai chỗ cùng tên gộp thành MỘT núm", len(_ds) == 1,
     f"— {[d['ten'] for d in _ds]}")
kiem("và núm ấy nói ra nó nằm ở CẢ HAI chỗ", len(_ds[0]["o_tai"]) == 2,
     f"— {_ds[0]['o_tai']}")
_ma = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                    "steps": _st, "edges": _ed})["ma"]
kiem("LEAN chỉ dựng MỘT chỉ báo cho núm ấy", _ma.count("= self.rsi(") == 1,
     f"— {_ma.count('= self.rsi(')} cái")
_sot = []
for _s in _st:
    _ten_num = core._num_cua(_s)
    _da_bay = {t for d in core.the_buoc(_s)["lines"] for t in (d.get("num") or [])}
    _sot += [f"{core.step_title(_s)}.{t}" for t in _ten_num - _da_bay]
kiem("mọi núm đều được thẻ khối nói ra để tô sáng", not _sot, f"— {_sot}")
_tsx = doc("webui", "src", "components", "StepNode.tsx")
kiem("và giao diện ĐỌC `num` của Python chứ không tự dò chữ",
     "d.num" in _tsx and "num-ghim" in _tsx)

print("\n▸ Và ghim rồi thì BACKTEST THƯỜNG phải chạy y như cũ")
# `get_parameter(ten, mac_dinh)` trả mặc định khi không ai truyền gì vào, nên con số
# cũ phải ở lại làm mặc định. Mất nó thì ghim một ô là đổi luôn kết quả backtest
# thường — người dùng ghim để CHUẨN BỊ quét, chứ không phải để đổi chiến thuật.
_st, _ed = _so_do_mot_khoi(lam.LAM_TIN_HIEU)
_dk = core.make_dieu_kien("rsi", "<=", 45, tham_so={"n": 14})
_st[1]["dieu_kien"] = [_dk]
_truoc = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                       "steps": _st, "edges": _ed})["ma"]
_dk["trai"]["ghim"] = {"n": "chu_ky"}
_dk["phai"]["ghim"] = {"so": "nguong"}
_sau = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                     "steps": _st, "edges": _ed})["ma"]
kiem("mặc định 14 ở lại trong câu get_parameter",
     "get_parameter('chu_ky', 14)" in _sau, f"— {'chu_ky' in _sau}")
kiem("mặc định 45 cũng thế", "get_parameter('nguong', 45)" in _sau)
kiem("và ghim làm mã ĐỔI thật, không phải cái ghim trang trí", _truoc != _sau)

print(f"\n{'=' * 60}\n  {dung} đúng · {sai} sai\n{'=' * 60}")
sys.exit(1 if sai else 0)
