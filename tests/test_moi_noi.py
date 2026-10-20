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
import json
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
    # Ô cầm lái hỏi CHÍNH `lam.o_lai`, không dò lại ở đây: khối «Ghi nhớ» có hai ô
    # chọn và ô cầm lái là ô THỨ HAI, nên bản dò "lấy ô chọn đầu tiên" của bài kiểm
    # này từng báo oan `lam_ghi_nho.cach` là núm giả. Một luật, một hàm.
    _o_lai = lam.o_lai(_ma)
    _lai = _o_lai["ten"] if _o_lai else None
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
def _bo_chu_thich(s):
    """Bỏ chú thích `//` và `/* */` khỏi một tệp TSX. -> chuỗi cùng độ dài (thay bằng
    khoảng trắng, nên mọi vị trí giữ nguyên).

    ⚠ VÌ SAO PHẢI CÓ. Hàng rào bên dưới dò chữ `className=` trong NGUYÊN VĂN tệp. Một
    lời chú thích nhắc tới `className={lop}` — viết ra đúng để giải thích vì sao KHÔNG
    nên gom lớp qua biến — làm hàng rào kêu oan, và báo một lớp ma tên «lop». Đã dính
    thật, và nó là loại hỏng tệ nhất: cách chữa dễ nhất là XOÁ LỜI CHÚ THÍCH đi, tức
    hàng rào phá đúng thứ nó định giữ. Cùng một bệnh sẽ gặp lại ở
    bất cứ hàng rào nào dò chữ trong nguyên văn tệp.

    Tôn trọng nháy: `'https://x'` không phải chú thích, và `// "` không mở chuỗi."""
    ra, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "'\"`":
            j = i + 1
            while j < n and s[j] != c:
                j += 2 if s[j] == "\\" else 1
            ra.append(s[i:min(j + 1, n)])
            i = j + 1
        elif c == "/" and i + 1 < n and s[i + 1] == "/":
            j = s.find("\n", i)
            j = n if j < 0 else j
            ra.append(" " * (j - i))
            i = j
        elif c == "/" and i + 1 < n and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            j = n if j < 0 else j + 2
            ra.append(" " * (j - i))
            i = j
        else:
            ra.append(c)
            i += 1
    return "".join(ra)


def _gia_tri_className(s):
    """Cắt ĐÚNG giá trị của mỗi `className=` -> [chuỗi].

    ⚠ Phải cắt theo ngoặc khớp nhau, không quét tới hết dòng: trên cùng một dòng còn
    `inputMode="decimal"`, `loai === 'equity'`… và bài kiểm sẽ kêu oan vì chúng.
    Bài kiểm kêu oan là bài kiểm sớm muộn bị bỏ qua, mà bỏ qua thì nó hết canh."""
    ra = []
    s = _bo_chu_thich(s)
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
        _chu["ghim_num"] = {_ten_o: "num_thu"}
        _ds = core.ds_tham_so(_st)
        _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                            "steps": _st, "edges": _ed})
        if not any(d["ten"] == "num_thu" for d in _ds):
            _hong_ghim.append(f"{_ma_loai}.{_ten_o}: hộp Optimize KHÔNG thấy")
        elif "get_parameter('num_thu'" not in _kq["ma"]:
            _hong_ghim.append(f"{_ma_loai}.{_ten_o}: mã sinh ra KHÔNG đọc")
        _chu.pop("ghim_num", None)
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
        _chu["ghim_num"] = {_ten_o: "num_thu"}
        _ds = core.ds_tham_so(_st)
        _kq = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                            "steps": _st, "edges": _ed})
        if not any(d["ten"] == "num_thu" for d in _ds):
            _hong_ghim.append(f"{_ma_dl}.{_ten_o}: hộp Optimize KHÔNG thấy")
        elif "get_parameter('num_thu'" not in _kq["ma"]:
            _hong_ghim.append(f"{_ma_dl}.{_ten_o}: mã sinh ra KHÔNG đọc")
        _chu.pop("ghim_num", None)
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
    _d["trai"]["ghim_num"] = {"n": "rsi_chu_ky"}
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

print("\n▸ MỐI NỐI 11 — hộp Optimize × config LEAN × bảng kết quả")
from cat_studio import chay_toi_uu, toi_uu  # noqa: E402

# Mọi núm trong hộp phải thành một khoá LEAN nhận, và ngược lại.
_cai = dict(toi_uu.MAC_DINH)
_cai["tham_so"] = {"rsi_chu_ky": {"tu": 10, "den": 30, "buoc": 5}}
_cai["rang_buoc"] = [{"chi_tieu": "Drawdown", "phep": "lessOrEqual", "gia_tri": 0.2}]
_sb = {"goc": "G", "lean_dll": "L.dll"}
_cfg = chay_toi_uu._cau_hinh(_cai, "Lop", "ma.py", "ra", _sb)
for _k in ("optimization-strategy", "optimization-criterion", "constraints",
           "parameters", "lean-binaries-location", "optimizer-close-automatically"):
    kiem(f"config có «{_k}»", _k in _cfg)
kiem("mục tiêu thành đường dẫn vào file kết quả",
     _cfg["optimization-criterion"]["target"] == "Statistics.Sharpe Ratio",
     f'— {_cfg["optimization-criterion"]["target"]}')
kiem("núm thành đúng khuôn {name,min,max,step}",
     _cfg["parameters"] == [{"name": "rsi_chu_ky", "min": 10.0, "max": 30.0,
                             "step": 5.0}], f'— {_cfg["parameters"]}')
kiem("ràng buộc dùng phép so LEAN hiểu",
     _cfg["constraints"][0]["operator"] in {m for m, _n in toi_uu.PHEP_SO})
# ⚠ Optimizer KHÔNG tự chạy backtest, nó đẻ tiến trình LEAN — và gọi qua file .DLL.
kiem("trỏ vào .dll của launcher backtest, không phải .exe",
     str(_cfg["lean-binaries-location"]).endswith(".dll"))
kiem("có cờ đóng tự động — thiếu là cả mẻ đứng chờ một phím",
     _cfg["optimizer-close-automatically"] is True)
_mo_ra = {c for c, _n in toi_uu.CACH_TIM}
kiem("cách tìm là một lớp có thật của LEAN", _cfg["optimization-strategy"] in _mo_ra)

print("\n▸ Cột BÀY SẴN của bảng xếp hạng phải là chỉ tiêu CÓ THẬT")
# Bày cả 27 cột thì bảng rộng gấp ba màn hình, phải kéo ngang mới thấy cột mình cần
# — đã thấy trên ảnh người dùng gửi. Nhưng danh sách rút gọn mà gõ sai một tên thì
# cột ấy VĨNH VIỄN rỗng và không có lỗi nào kêu lên.
_la = [c for c in toi_uu.CHI_TIEU_CHINH if c not in toi_uu.CHI_TIEU]
kiem("mọi cột bày sẵn đều nằm trong 27 chỉ tiêu thật", not _la, f"— {_la}")
kiem("và nó GỌN thật, không phải bày lại cả nắm",
     3 <= len(toi_uu.CHI_TIEU_CHINH) <= 8, f"— {len(toi_uu.CHI_TIEU_CHINH)} cột")
kiem("từ điển gửi danh sách ấy sang giao diện",
     len(toi_uu.tu_dien()["chi_tieu_chinh"]) == len(toi_uu.CHI_TIEU_CHINH))
_tu_tsx = doc("webui", "src", "TrangToiUu.tsx")
kiem("giao diện ĐỌC `chi_tieu_chinh` chứ không tự chọn cột",
     "chi_tieu_chinh" in _tu_tsx)
kiem("và chỉ tiêu ĐANG TÌM luôn có cột, kể cả khi nó ngoài danh sách",
     "mucTieu, ...chinh" in _tu_tsx,
     "— quét tìm Sortino mà bảng không có cột Sortino thì xếp hạng theo gì")
kiem("vẫn mở xem được CẢ 27 cột — gọn chứ không giấu",
     "hetCot" in _tu_tsx and "tất cả" in _tu_tsx)

print("\n▸ Hộp tiến độ Optimize — phần trăm phải là SỐ THẬT")
# Backtest KHÔNG có phần trăm, cố ý: LEAN không in tiến độ một lượt ra màn hình, nên
# bịa một con số là hứa một cái mốc không ai giữ được. Mẻ Optimize thì khác — biết
# trước bao nhiêu lượt, và đếm được bao nhiêu file kết quả đã ghi ra đĩa.
_td = chay_toi_uu.trang_thai()
for _k in ("so_luot", "xong_may", "ma_id", "giay"):
    kiem(f"`trang_thai` nói «{_k}»", _k in _td)
_hop = doc("webui", "src", "components", "HopTienDoToiUu.tsx")
kiem("hộp đếm theo xong/tổng, không phải thanh chạy suông",
     "xong_may" in _hop and "so_luot" in _hop)
kiem("còn-bao-lâu tính theo NHỊP THẬT của mấy lượt đã xong",
     "giay / xong" in _hop,
     "— lấy con số ước lượng lúc bấm Chạy thì máy bận là nói sai")
_sodo = doc("webui", "src", "SoDo.tsx")
kiem("mở cửa sổ bằng `ma_id` của Python, không tự bẻ đường dẫn",
     "ma_id" in _sodo and "replace(/" not in _sodo)

print("\n▸ ⚠ Bảng xếp hạng chỉ được bày NÚM CỦA MẺ, không bày tham số của LEAN")
# ĐÃ DÍNH THẬT, và chỉ lộ ra khi nhìn ảnh chụp: `algorithmConfiguration.parameters`
# mang cả `ema-fast` · `ema-slow` · `intrinio-username` · `intrinio-password` của
# chính LEAN, vì config ta ghi kế thừa từ `config.json` gốc. Mã vẫn chạy, bảng vẫn
# hiện — chỉ là nó mọc bốn cột vô nghĩa lẫn vào giữa mấy cột núm thật.
import inspect  # noqa: E402
_nguon = inspect.getsource(chay_toi_uu.doc_luot)
kiem("`doc_luot` nhận danh sách núm để lọc", "ten_num" in _nguon)
kiem("và nó LỌC thật, không chỉ chép cả nắm", "if k in loc" in _nguon,
     "— comment nói lọc mà mã chép hết thì đúng là cái hàng rào không ai gác")
for _ham in (chay_toi_uu.doc_me, chay_toi_uu.trang_thai):
    kiem(f"`{_ham.__name__}` truyền danh sách ấy xuống",
         "doc_luot(" in inspect.getsource(_ham)
         and inspect.getsource(_ham).count("doc_luot(") ==
             inspect.getsource(_ham).count("doc_luot(d,")
             + inspect.getsource(_ham).count('doc_luot(t.get'))

print("\n▸ ⚠ GHIM phải sống qua LƯU/MỞ — ở CẢ HAI chỗ, không chỉ chỗ dễ nhớ")
# ĐÃ DÍNH THẬT, và dính vì TRÙNG TÊN KHOÁ. `ghim` vốn đã là khoá CŨ của canvas
# («ghim khối tại chỗ», một BOOLEAN) và nó nằm trong `KHOA_CANVAS`, nên khi ta đặt
# một DICT cùng tên lên khối thì `chuan_hoa_khoi` gỡ sạch — ghim trên ô số của khối
# Làm không sống qua lưu/mở, trong khi ghim trong vế điều kiện thì sống (vế không
# phải khối, `KHOA_CANVAS` không với tới). Hỏng ĐÚNG MỘT NỬA, nên nhìn qua vẫn chạy.
#
# Bài kiểm cũ của tôi mù đúng chỗ ấy: nó đặt `ghim` rồi đọc lại NGAY, không đi qua
# lưu/mở lần nào. Nay quét CẢ HAI chỗ và BẮT BUỘC qua `chuan_hoa_khoi`.
kiem("khoá ghim KHÔNG trùng khoá canvas", "ghim_num" not in core.KHOA_CANVAS,
     f"— {core.KHOA_CANVAS}")
_mat = []
for _ma_loai in lam.LOAI_LAM:
    _k = core.make_lam_step(_ma_loai)
    _o_so = [t for t in core._o_so_cua(_k)]
    if not _o_so:
        continue
    _chu, _ten_o = _o_so[0][0], _o_so[0][1]
    _chu["ghim_num"] = {_ten_o: "num_thu"}
    _lai = core.chuan_hoa_khoi(json.loads(json.dumps(_k)))
    if "num_thu" not in {d["ten"] for d in core.ds_tham_so([_lai])}:
        _mat.append(f"khối {_ma_loai}")
_h = core.make_hoi_step("hoi_thi_truong")
_d = core.make_dieu_kien("rsi", "<=", 45, tham_so={"n": 14})
_d["trai"]["ghim_num"] = {"n": "num_ve"}
_d["phai"]["ghim_num"] = {"so": "num_so"}
_h["dieu_kien"] = [_d]
_lai_h = core.chuan_hoa_khoi(json.loads(json.dumps(_h)))
for _t in ("num_ve", "num_so"):
    if _t not in {d["ten"] for d in core.ds_tham_so([_lai_h])}:
        _mat.append(f"vế {_t}")
kiem("ghim sống qua lưu/mở ở MỌI chỗ ghim được", not _mat, f"— mất: {_mat}")

print("\n▸ BẤM ĐÚP một dòng xếp hạng → sơ đồ nhận luôn bộ số ấy")
# `dat_tham_so` phải là GƯƠNG của `_o_so_cua`: đọc ở đâu thì ghi vào đúng đấy. Lệch
# một chỗ là đặt số vào hư không — sơ đồ không đổi gì mà cũng chẳng báo gì.
_st2 = [_lai_h, _lai]
_truoc = core.ds_tham_so(_st2)
kiem("sơ đồ thử có núm để đặt", len(_truoc) >= 2, f"— {[d['ten'] for d in _truoc]}")
_moi, _dat = core.dat_tham_so(_st2, {d["ten"]: "7" for d in _truoc})
kiem("đặt được ĐÚNG mọi núm đang ghim",
     set(_dat) == {d["ten"] for d in _truoc}, f"— {_dat}")
kiem("và đọc lại đúng con số vừa đặt",
     all(str(d["mac_dinh"]) == "7" for d in core.ds_tham_so(_moi)),
     f'— {[(d["ten"], d["mac_dinh"]) for d in core.ds_tham_so(_moi)]}')
kiem("chuỗi của LEAN («7») thành SỐ, không phải chuỗi",
     all(isinstance(d["mac_dinh"], (int, float))
         for d in core.ds_tham_so(_moi)),
     "— nhét chuỗi vào thì thẻ đọc «RSI('7')» và bộ sinh mã viết một chuỗi")
_moi2, _dat2 = core.dat_tham_so(_st2, {"num_khong_co": "9"})
kiem("núm sơ đồ KHÔNG còn ghim thì bỏ qua, không đoán bừa", not _dat2)

print("\n▸ MỐI NỐI 12 — cửa sổ Optimize × cửa sổ sơ đồ (hai cửa sổ, hai js_api)")
# Bấm đúp một dòng xếp hạng phải đi hết ba chặng: cửa sổ Optimize gọi `ap_num` ->
# Python đẩy sự kiện sang JS của cửa sổ CHÍNH -> cửa sổ chính gọi `dat_num_so_do`.
# Đứt chặng nào cũng im: bấm đúp, không có gì xảy ra, không lỗi nào.
#
# ⚠ Cơ chế đẩy sự kiện (`Api._ban` + `window.__su_kien`) khai từ lâu ở CẢ HAI đầu mà
# KHÔNG AI gọi, KHÔNG AI nghe — một hàng rào không ai gác, trông như đang chạy cho
# tới ngày đầu tiên cần tới. Nay nó là đường sống của tính năng này, nên phải canh.
_api_src = doc("cat_studio", "api.py")
kiem("`ApiToiUu` có cửa `ap_num`", "def ap_num(" in _api_src)
kiem("cửa sổ Optimize nhận một HÀM GỌI NGƯỢC, không nhận cả `Api`",
     "ApiToiUu(ma_id, _bao)" in _api_src,
     "— đưa cả `Api` là đưa luôn `xoa_strategy` vào một cửa sổ chẳng cần tới nó")
kiem("`_bao` đẩy sự kiện rồi ĐƯA CANVAS LÊN TRƯỚC",
     '_ban("mo_so_do"' in _api_src and "self._window.restore()" in _api_src,
     "— mở đúng sơ đồ mà cửa sổ ấy vẫn nằm dưới thì người dùng không thấy gì đổi")
# ⚠ `restore()` CHỈ bỏ thu nhỏ. Cửa sổ sơ đồ nằm DƯỚI cửa sổ Optimize thì nó chẳng
# đổi gì — bấm đúp, sơ đồ đổi thật, mà người dùng vẫn đang nhìn bảng xếp hạng nên
# tưởng không có gì xảy ra. Phải nâng bằng Win32.
kiem("và nâng hẳn bằng Win32, không chỉ `restore()`",
     "dua_len_truoc(" in _api_src)
_kcs = doc("cat_studio", "khung_cua_so.py")
kiem("`dua_len_truoc` gọi cả BringWindowToTop lẫn SetForegroundWindow",
     "BringWindowToTop" in _kcs and "SetForegroundWindow" in _kcs,
     "— Windows có thể từ chối cái sau, nên cái trước là lối dự phòng")
_krong = doc("cat_studio", "khung_rong.py")
kiem("bản rỗng ngoài Windows cũng có hàm ấy", "def dua_len_truoc(" in _krong,
     "— thiếu là `api.py` không nạp nổi trên Linux/CI")

print("\n▸ ⚠ Cửa sổ nào tự vẽ thanh tiêu đề thì PHẢI được vá khung")
# ĐÃ DÍNH HAI LẦN. Cửa sổ Kết quả dính trước; nay cửa sổ Optimize dính lại y hệt,
# chỉ khác cách: `_va_khung` đòi tham số `chua_chuoi`, mà chỗ mở cửa sổ Optimize gọi
# `threading.Thread(target=phu._va_khung)` KHÔNG tham số. Luồng nền ném `TypeError`
# rồi chết IM, nên khung không bao giờ được vá — thanh tiêu đề không kéo, không
# giãn, không Aero Snap, mà nhìn vào thì y hệt một cửa sổ bình thường.
kiem("không chỗ nào giao THẲNG `_va_khung` cho một luồng",
     all("_va_khung(" in d for d in _api_src.splitlines()
         if "target=" in d and "_va_khung" in d),
     "— `_va_khung` đòi `chua_chuoi`; giao trần là TypeError chết im trong luồng nền")
_so_cua = _api_src.count("frameless=True")
_so_va = _api_src.count("_va_khung(tieu_de)")
kiem(f"mỗi cửa sổ frameless phụ đều có một lượt vá khung ({_so_va} vá)",
     _so_va >= 2, f"— {_so_cua} cửa sổ frameless, {_so_va} lượt vá")
kiem("và VÁ HỤT THÌ NÓI, không im",
     _api_src.count("KHÔNG vá được khung") >= 2,
     "— im lặng là để người dùng ngồi thử đi thử lại một dải tiêu đề đã chết")
_tu_tsx_tb = doc("webui", "src", "TrangToiUu.tsx")
kiem("trang Optimize tự vẽ `TitleBar`", "<TitleBar" in _tu_tsx_tb)
_tb = doc("webui", "src", "components", "TitleBar.tsx")
kiem("và `TitleBar` tự gắn `useKhungCuaSo`", "useKhungCuaSo(" in _tb,
     "— gắn ở SoDo thôi thì cửa sổ phụ có thanh tiêu đề chết, đã dính thật")

print("\n▸ ⚠ Mẻ phải NHỚ CẢ SƠ ĐỒ — không chỉ nhớ mấy con số")
# Bấm đúp một dòng phải mở ra ĐÚNG SƠ ĐỒ ẤY, kể cả khi canvas đang trống, đang vẽ
# một chiến thuật khác, hay mẻ ấy chạy từ tuần trước. Chỉ nhớ bộ số thì không đủ:
# biết `sma_chu_ky = 240` mà không biết nó nằm trong sơ đồ nào thì đặt vào đâu.
_ct_src = doc("cat_studio", "chay_toi_uu.py")
kiem("thẻ mẻ giữ khoá `so_do`", '"so_do"' in _ct_src)
kiem("`chay` nhận sơ đồ để lưu", "def chay(ma, ten_lop, cai, so_do=None)" in _ct_src)
kiem("và `api.chay_toi_uu` TRUYỀN sơ đồ xuống",
     "cai or {}, doc)" in _api_src,
     "— không truyền thì thẻ mẻ rỗng và bấm đúp chẳng mở được gì")
kiem("`ap_num` lấy sơ đồ TỪ MẺ, không hỏi canvas đang vẽ gì",
     "chay_toi_uu.doc_me(self._ma_id)" in _api_src)
kiem("và nó ĐẶT SỐ ngay bên Python trước khi đẩy sang",
     "core.dat_tham_so(" in _api_src,
     "— cửa sổ chính chỉ việc nạp một tài liệu đã sẵn sàng")
kiem("mẻ CŨ chưa lưu sơ đồ thì DÒ NGƯỢC trong kho Strategy",
     "_so_do_theo_ten_lop(" in _api_src,
     "— phép tên-chiến-thuật -> tên-lớp xác định, nên dò ngược là tìm đúng, không đoán")
kiem("dò không ra thì NÓI RA, không im", "chạy từ bản cũ nên không lưu sơ đồ"
     in _api_src)
# ⚠ ĐẶT ĐƯỢC 0 NÚM cũng là HỎNG, chỉ là hỏng êm: mở ra một sơ đồ y hệt rồi để người
# dùng ngồi tìm xem con số nào vừa đổi — mà chẳng con nào đổi cả. Gặp thật khi sơ đồ
# dò được từ kho Strategy chưa ghim núm nào.
kiem("đặt được 0 núm cũng phải nói, và KHÔNG ghi đè sơ đồ đang vẽ",
     "if not dat:" in _api_src and "không còn ô nào ghim" in _api_src)
_tu_tsx_bd = doc("webui", "src", "TrangToiUu.tsx")
# Bỏ dòng COMMENT ra trước khi dò — chính chỗ này vừa kêu oan vì trong file có một
# comment nhắc lại dạng hỏng. Bài kiểm đọc lời văn rồi báo đỏ là bài kiểm sớm muộn
# bị bỏ qua, mà bỏ qua thì nó hết canh.
_tu_ma = " ".join(d for d in _tu_tsx_bd.splitlines()
                  if not d.strip().startswith(("//", "*", "/*")))
kiem("và giao diện KHÔNG nuốt câu lỗi ấy",
     "void pyTu.ap_num(" not in _tu_ma and "setLoi(kq.error" in _tu_ma,
     "— `void` vứt luôn cả lỗi, nên bấm đúp ra đúng không gì cả")
kiem("và cửa `dat_num_so_do` đã bỏ — không ai gọi nữa",
     "def dat_num_so_do(" not in _api_src,
     "— để lại một cửa không ai gọi là lại một hàng rào không ai gác")

_api_ts = doc("webui", "src", "api.ts")
kiem("giao diện có hàm `nghe` để nhận sự kiện", "export function nghe(" in _api_ts)
kiem("và nó giữ DANH SÁCH người nghe, không ghi đè `window.__su_kien`",
     "_nguoi_nghe" in _api_ts,
     "— ghi đè thì chỗ gắn sau giết chỗ gắn trước, lặng lẽ")
_tu_ts = doc("webui", "src", "TrangToiUu.tsx")
kiem("bảng xếp hạng bấm đúp được", "onDoubleClick" in _tu_ts
     and "ap_num" in _tu_ts)
_sd_ts = doc("webui", "src", "SoDo.tsx")
kiem("cửa sổ sơ đồ NGHE `mo_so_do`", "nghe('mo_so_do'" in _sd_ts)
kiem("và nó NẠP THẲNG tài liệu nhận được, không tự dò ô trong TypeScript",
     "await nap({" in _sd_ts and "dat_num_so_do" not in _sd_ts,
     "— viết lại luật «con số nằm ở đâu» bằng TS là bản sự thật thứ hai")
_than_mo = _sd_ts.split("nghe('mo_so_do'")[1][:1400]
kiem("đẩy một bước Hoàn tác trước khi nạp đè lên sơ đồ đang vẽ",
     "chong.current.push" in _than_mo)
# Đưa cửa sổ lên trước mà cái hộp Kho vẫn mở thì nó che đúng thứ người dùng vừa bấm
# để xem — công cốc. Quét theo DANH SÁCH state thật, nên thêm một hộp mới mà quên
# đóng nó là bài này kêu.
_hop_che = [d.split("const [")[1].split(",")[0].strip()
            for d in _sd_ts.splitlines()
            if d.strip().startswith("const [mo") and "useState(false)" in d]
_quen = [h for h in _hop_che if f"set{h[0].upper()}{h[1:]}(false)" not in _than_mo]
kiem(f"đóng CẢ {len(_hop_che)} hộp đang che sơ đồ", not _quen, f"— quên: {_quen}")
kiem("nhưng KHÔNG đóng hộp tiến độ — chúng cầm nút Dừng",
     "setTienDo(null)" not in _than_mo and "setTdToiUuChay(null)" not in _than_mo)

print("\n▸ MỐI NỐI 13 — VỎ TRÒ CHƠI: Mở máy × Hành trình × Xưởng")
# Mốc M1: canvas thôi làm Home. App mở ra là màn MỞ MÁY, canvas thành MỘT màn hình
# (Xưởng) trong ba. Đứt chỗ nào ở đây cũng im: hoặc app lại mở thẳng vào canvas, hoặc
# bấm một màn mà không đi đâu cả.
_ht_py = doc("cat_studio", "hanh_trinh.py")
_tc = doc("webui", "src", "TroChoi.tsx")
_mm = doc("webui", "src", "man", "ManMoMay.tsx")
_mht = doc("webui", "src", "man", "ManHanhTrinh.tsx")
_main = doc("webui", "src", "main.tsx")
_sd = doc("webui", "src", "SoDo.tsx")

kiem("app mở ra là TRÒ CHƠI, không phải thẳng canvas",
     "<TroChoi />" in _main and "<SoDo />" not in _main,
     "— canvas là MỘT màn hình trong trò chơi, không còn là cả cửa sổ")
kiem("vỏ có đủ ba màn hình", all(x in _tc for x in
     ("<ManMoMay", "<ManHanhTrinh", "<SoDo")))
kiem("và có màn che chuyển cảnh", "man-che" in _tc)

# ⚠ ĐÚNG MỘT MÀN HÌNH SỐNG TẠI MỘT LÚC. `TitleBar` mang `useKhungCuaSo` — bộ bắt kéo
# cửa sổ, nghe chuột ở mức `document`. Hai `TitleBar` cùng sống là hai bộ cùng bảo
# Windows "bắt đầu kéo". Nên vỏ phải rẽ bằng `&&` loại trừ nhau, không được giấu màn
# này rồi chồng màn kia lên.
kiem("ba màn hình LOẠI TRỪ nhau, không chồng lên nhau",
     _tc.count("man === '") >= 3 and "display: none" not in _tc
     and "visibility" not in _tc,
     "— hai `TitleBar` cùng sống là hai bộ bắt kéo cửa sổ đánh nhau")
for _m in ("ManMoMay", "ManHanhTrinh"):
    kiem(f"`{_m}` tự vẽ thanh tiêu đề",
         "<TitleBar" in doc("webui", "src", "man", _m + ".tsx"),
         "— cửa sổ frameless mà màn hình không có `TitleBar` là một dải chết")

# ⚠ RỜI XƯỞNG PHẢI GHI NỐT BẢN NHÁP. `SoDo` ghi nháp TRỄ 1,2 giây; rời Xưởng là nó bị
# tháo và hàm dọn HUỶ luôn bộ đếm giờ đang chờ — nên nét sửa cuối cùng, đúng cái nét
# vừa làm xong rồi bấm ra, là nét DUY NHẤT không bao giờ được ghi.
kiem("rời Xưởng thì GHI NỐT bản nháp trước khi đi",
     "async function raXuong()" in _sd and "luu_ban_nhap" in _sd.split(
         "async function raXuong()")[1].split("onRa?.()")[0],
     "— không ghi nốt thì mất đúng một thao tác, mỗi lần, và không lỗi nào báo")
kiem("và nút ra gọi ĐÚNG hàm ấy, không gọi thẳng `onRa`",
     "onClick={raXuong}" in _sd)

# ⚠ ĐỔI TIẾNG PHẢI ĐI QUA CỬA CÀI ĐẶT. Gọi thẳng `datNgonNgu` chỉ đổi trong bộ nhớ
# của web: Python không nghe (mà tên hồi, tên màn do Python dựng), và lần nối sau
# `api.ts` đọc lại cài đặt CŨ rồi đặt ngược về tiếng Anh. Đã hỏng thật, cả hai kiểu.
kiem("ô đổi tiếng ở màn Mở máy đi qua cửa Cài đặt",
     "cai_dat_ghi" in _mm,
     "— gọi thẳng `datNgonNgu` thì Python không nghe và lần nối sau đặt ngược lại")

# ⚠ KHÔNG KHAI LẠI MỘT MÀN NÀO BÊN TYPESCRIPT. Danh sách hồi và màn chỉ có một chỗ.
kiem("hành trình do PYTHON giữ, giao diện chỉ hỏi rồi vẽ",
     "py.hanh_trinh()" in _mht and "'m00'" not in _mht and '"m00"' not in _mht,
     "— hai nơi cùng giữ danh sách màn thì lệch nhau ở đúng hồi ít người tới nhất")
kiem("`api.py` có cửa `hanh_trinh`", "def hanh_trinh(self)" in _api_src)
kiem("và `api.ts` khai cửa ấy", "hanh_trinh: () =>" in doc("webui", "src", "api.ts"))

# Đếm thật, không tin lời chú thích.
import importlib  # noqa: E402
_ht = importlib.import_module("cat_studio.hanh_trinh")
kiem(f"đủ 26 màn ({len(_ht.MAN)})", len(_ht.MAN) == 26)
kiem(f"đủ 10 hồi ({len(_ht.HOI)})", len(_ht.HOI) == 10,
     "— 9 hồi cộng khúc dạo đầu")
_ma_hoi = {h["ma"] for h in _ht.HOI}
kiem("mọi màn đều thuộc một hồi có thật",
     all(m["hoi"] in _ma_hoi for m in _ht.MAN))
kiem("mọi hồi đều có ít nhất một màn",
     _ma_hoi == {m["hoi"] for m in _ht.MAN})
kiem("mã màn không trùng nhau",
     len({m["ma"] for m in _ht.MAN}) == len(_ht.MAN))
kiem("màn nào cũng có câu DẠY", all(str(m.get("day") or "").strip() for m in _ht.MAN))

_td = _ht.tu_dien()
# ⚠ KIỂM HÀM THUẦN, không kiểm `tu_dien()`. `tu_dien` đọc SỔ ĐIỂM THẬT trên đĩa, nên
# bài kiểm sẽ đỏ hay xanh tuỳ người chạy nó đã chơi tới màn nào — một bài kiểm như thế
# thì sớm muộn bị coi là nhiễu rồi bỏ qua. Luật mở khoá nằm trong `_mo_toi_man`.
kiem("sổ trống thì CHỈ màn đầu mở",
     _ht._mo_toi_man(set()) == {_ht.MAN[0]["ma"]})
kiem("xong màn đầu thì mở thêm ĐÚNG một màn",
     _ht._mo_toi_man({_ht.MAN[0]["ma"]})
     == {_ht.MAN[0]["ma"], _ht.MAN[1]["ma"]},
     "— bản trước có HAI sổ: sổ điểm ghi xong mà bản đồ vẫn khoá màn kế, mãi mãi")
# ⚠ NHẮM VÀO MÃ, ĐỪNG NHẮM VÀO CHỮ. Bản đầu dò `"hanh_trinh.json" not in` cả tệp và
# kêu oan ngay vào LỜI CHÚ THÍCH kể lại chính cái lỗi ấy — lần thứ ba trong dự án này
# một hàng rào dò nguyên văn vấp phải chú thích (xem `_bo_chu_thich` bên trên). Cái
# đọc sổ thứ hai là hàm `_so()`; không còn hàm ấy là không còn sổ thứ hai.
kiem("và tiến trình chỉ có MỘT sổ — sổ điểm",
     "def _so()" not in doc("cat_studio", "hanh_trinh.py"),
     "— hai nơi cùng giữ một sự thật thì sớm muộn chúng lệch nhau")
# Luật chấm sao là mốc sau. Im lặng ở đây là vẽ sẵn ô sao rỗng, và người chơi tưởng
# mình chơi mãi không ăn được sao nào.
kiem("và NÓI RÕ là chưa có luật chấm", _td["co_luat_cham"] is False)
kiem("bản đồ bày lời ấy ra", "co_luat_cham" in _mht)


print("\n▸ MỐI NỐI 14 — LUẬT CHƠI: màn ẩn, boss, ba sao, màn Chấm")
# ⚠ NGÀY CỦA MÀN ẨN LÀ CẢ TRÒ CHƠI. Ngôi sao thứ ba nói "cỗ máy còn chạy được trên
# khoảng ngày nó chưa từng thấy". Người chơi biết ngày ấy là vặn máy cho vừa khít đúng
# khoảng ấy — và ngôi sao thứ ba mất sạch nghĩa mà vẫn sáng lên y như thật. Nên mọi cửa
# đi ra giao diện phải được soát: không cửa nào được mang ngày màn ẩn theo.
import importlib  # noqa: E402
import json as _json  # noqa: E402
_ht = importlib.import_module("cat_studio.hanh_trinh")
_lc = importlib.import_module("cat_studio.luat_choi")
_apip = importlib.import_module("cat_studio.api")

_co_an = [m for m in _ht.MAN if m.get("an")]
kiem(f"có màn khai màn ẩn ({len(_co_an)} màn)", bool(_co_an))
# ⚠ SOÁT THEO TỪNG MÀN, không soát cả bảng một lượt. Hai màn khác nhau trùng ngày là
# chuyện bình thường — khoảng ĐÃ THẤY của màn sau hay trùng đầu khoảng ẨN của màn
# trước, vì chúng nằm trên cùng một dòng thời gian. Soát cả bảng thì mọi màn đều "rò",
# mà thứ thật sự phải cấm là: phần công khai của MỘT màn mang ngày ẩn của CHÍNH nó.
_ro = [m["ma"] for m in _co_an
       if any(d in _json.dumps(_ht.cong_khai(m), ensure_ascii=False) for d in m["an"])]
kiem("không màn nào bày ngày ẩn CỦA CHÍNH NÓ", not _ro,
     f"— biết ngày màn ẩn là ngôi sao thứ ba hết nghĩa · rò: {_ro}")
# ⚠ VÀ KHÔNG ĐƯỢC SUY RA. Nói "12 tháng ngay sau màn đã thấy" là tử tế, nhưng cộng với
# khoảng đã thấy (bày công khai) thì người chơi tính ra ngày ẩn rồi sang Sáng tạo vặn
# máy cho khít đúng khoảng ấy.
# ⚠ KIỂM DỮ LIỆU, KHÔNG KIỂM CHỮ TRONG TỆP. Bản đầu dò hai cụm từ ấy trong nguyên văn
# `hanh_trinh.py` và kêu oan ngay vào LỜI CHÚ THÍCH dặn đừng viết thế — lần thứ năm
# trong dự án này một hàng rào dò nguyên văn vấp phải chú thích. Thứ phải đúng là GIÁ
# TRỊ `an_mo_ta`, nên đọc thẳng giá trị ấy.
_cong_thuc = [m["ma"] for m in _co_an
              if any(t in str(m.get("an_mo_ta") or "")
                     for t in ("12 tháng", "ngay sau"))]
kiem("và lời tả màn ẩn KHÔNG cho suy ra ngày", not _cong_thuc,
     f"— tả được bằng công thức thì tính ra được · {_cong_thuc}")
for _m in _co_an[:3]:
    _ck = _json.dumps(_ht.cong_khai(_m), ensure_ascii=False)
    kiem(f"`cong_khai({_m['ma']})` cũng sạch",
         not any(d in _ck for d in _m["an"]) and "an" not in _ht.cong_khai(_m))
kiem("màn ẩn tả bằng LỜI, không bằng ngày",
     all(_ht.cong_khai(m).get("an_mo_ta") for m in _co_an))

print("\n▸ Ba sao — và mỗi sao cần mọi sao trước nó")
_sach = {"sach": True, "thang_boss": False}
_thang = {"sach": True, "thang_boss": True}
kiem("không chạy sạch -> 0 sao", _lc.sao({"sach": False, "thang_boss": True}) == 0,
     "— thua boss mà còn thắng thì cũng không tính")
kiem("chạy sạch -> 1 sao", _lc.sao(_sach) == 1)
kiem("thắng boss màn đã thấy -> 2 sao", _lc.sao(_thang) == 2)
kiem("nộp mà thua trên màn ẩn -> vẫn 2 sao",
     _lc.sao(_thang, {"sach": True, "thang_boss": False}) == 2)
kiem("thắng cả màn ẩn -> 3 sao", _lc.sao(_thang, _thang) == 3)
# Cỗ máy không bao giờ giao dịch thì "không thua" chẳng nói lên điều gì.
kiem("không lệnh đóng nào thì KHÔNG sạch",
     _lc.cham({"ok": True, "giao_dich": [], "thong_ke": {"Net Profit": "5%"}})["sach"]
     is False)
# Thiếu số của boss thì KHÔNG AI THẮNG AI — chứ không phải người chơi thắng.
kiem("thiếu đường Benchmark -> không ai thắng ai",
     _lc.cham({"ok": True, "giao_dich": [1], "thong_ke": {"Net Profit": "5%"},
               "bieu_do": []})["thang_boss"] is False)

print("\n▸ ⚠ Màn 0 KHÔNG CHẤM — hệ quả bắt buộc của luật sao")
_m0 = _ht.MAN[0]
kiem("màn 0 khai `khong_cham`", bool(_m0.get("khong_cham")),
     "— nó bảo dựng «Mua rồi giữ», mà mua rồi giữ không đóng lệnh nào, nên ⭐ "
     "không bao giờ ăn được; chấm nó là phạt người chơi vì đã làm ĐÚNG lời dặn")
kiem("và cửa `cham_man` nói thẳng ra", '"khong_cham": True' in _api_src)

print("\n▸ ⚠ BOSS LÀ ĐƯỜNG BENCHMARK CỦA CHÍNH LEAN")
# Chạy một lượt backtest THỨ HAI chỉ để biết mua-giữ lãi bao nhiêu là làm lại việc
# LEAN đã làm sẵn — và là một bản sự thật thứ hai về con số ấy.
kiem("mỗi màn có sân ép `moc_so_sanh` về mã của nó",
     'may["moc_so_sanh"] = man.get("moc") or _ds_ma(man)[0]'
     in doc("cat_studio", "luat_choi.py"),
     "— thiếu nó thì LEAN lặng lẽ lấy SPY, và người chơi vàng bị đem so với cổ phiếu Mỹ")
kiem("và `boss_pt` đọc đúng đường ấy",
     'bang.get("ten") != "Benchmark"' in doc("cat_studio", "luat_choi.py"))

print("\n▸ ⚠ SÂN CỦA MÀN ÉP Ở PYTHON, LÚC CHẠY")
# Ô khoá trong giao diện chỉ là lời đề nghị: ai mở tệp sơ đồ ra sửa tay cũng qua được.
_than_chay = _api_src.split("def chay_backtest(")[1].split("\n    @_bat_loi")[0]
kiem("`chay_backtest` ép sân TRƯỚC khi sinh mã",
     "luat_choi.ap_man(" in _than_chay
     and _than_chay.find("ap_man(") < _than_chay.find("sinh_ma.sinh("),
     "— ép sau khi sinh mã thì mã đã mang mã và ngày của người chơi rồi")
kiem("và nó nhận `man` + `loai`", "def chay_backtest(self, ten, steps, edges=None, "
     "co_may=None,\n                      man=None, loai=\"thay\")" in _api_src)
kiem("`chay_toi_uu` KHÔNG ép sân — Optimize không thuộc màn nào",
     "ap_man(" not in _api_src.split("def chay_toi_uu(")[1].split(
         "\n    @_bat_loi")[0])

print("\n▸ NỘP chạy KÍN, không phát lại")
_than_nop = _api_src.split("def nop_man(")[1].split("\n    @_bat_loi")[0]
kiem("`nop_man` KHÔNG trả mã lượt về giao diện",
     '"ma_luot"' not in _than_nop and "'ma_luot'" not in _than_nop,
     "— cầm mã lượt là mở được file kết quả, mà trong đó có đủ ngày tháng")
kiem("và nó đòi một lượt SẠCH trên màn đã thấy trước",
     '"sach"' in _than_nop,
     "— nộp một cỗ máy chưa từng chạy trọn màn đã thấy thì hai sao đầu lấy gì mà chấm")

print("\n▸ Màn Chấm — bày lại, không tự tính")
_ch = doc("webui", "src", "man", "ManCham.tsx")
kiem("màn Chấm hỏi Python rồi bày", "py.cham_man(" in _ch and "py.nop_man(" in _ch)
# ⚠ NHẮM VÀO PHÉP GÁN THẬT, không nhắm vào chữ "sao =". Bản đầu cấm cả cụm ấy và kêu
# oan vào `const sao = "★".repeat(d.sao)` — một dòng VẼ LẠI con số Python đưa, không
# phải tính nó. Lần thứ sáu trong dự án này một hàng rào dò chữ bắt nhầm; luật đúng là:
# mọi phép gán cho `sao` phải lấy vế phải TỪ dữ liệu Python trả về (`d.` hay `r.value.`).
import re as _re  # noqa: E402
# ⚠ SO CHUỖI THUẦN, KHÔNG REGEX. Bản regex của luật này từng CHẾT HẲN: `\b` lọt vào
# một chuỗi không-raw và thành ký tự backspace, nên nó không khớp dòng nào — một hàng
# rào không bao giờ kêu, mà nhìn vào thì y hệt một hàng rào đang canh. Chỉ lộ ra vì
# ép hỏng một lượt. Ở đây không cần regex: ba cách khai biến là ba chuỗi cố định.
#
# Luật: mọi phép gán cho `sao` phải lấy vế phải TỪ con số Python trả về (`.sao`).
# `= d.thay?.thang_boss ? 2 : 1` vẫn bắt đầu bằng `d.` nhưng CHÍNH LÀ luật sao viết
# lại bằng TypeScript, nên chỉ xét "có `.sao` ở vế phải hay không".
_gan_sao = [d.strip() for d in _bo_chu_thich(_ch).splitlines()
            if any(d.strip().startswith(t)
                   for t in ("const sao =", "let sao =", "var sao ="))
            and ".sao" not in d.split("=", 1)[1]]
kiem("và KHÔNG tự tính sao", not _gan_sao and "thang_boss =" not in _ch,
     f"— «mấy sao» là luật chơi, mà luật chơi chỉ được có một bản{' · ' + str(_gan_sao) if _gan_sao else ''}")
kiem("sao vẽ bằng ký hiệu ĐƠN SẮC, không emoji",
     "★" in _ch and "⭐" not in _bo_chu_thich(_ch),
     "— emoji không ăn theo màu theme; cùng lý do thẻ «khoá» ở bản đồ dùng chữ")
_tc = doc("webui", "src", "TroChoi.tsx")
kiem("vỏ trò chơi có vai màn Chấm", "<ManCham" in _tc and "'cham'" in _tc)


print("\n▸ Và ghim rồi thì BACKTEST THƯỜNG phải chạy y như cũ")
# `get_parameter(ten, mac_dinh)` trả mặc định khi không ai truyền gì vào, nên con số
# cũ phải ở lại làm mặc định. Mất nó thì ghim một ô là đổi luôn kết quả backtest
# thường — người dùng ghim để CHUẨN BỊ quét, chứ không phải để đổi chiến thuật.
_st, _ed = _so_do_mot_khoi(lam.LAM_TIN_HIEU)
_dk = core.make_dieu_kien("rsi", "<=", 45, tham_so={"n": 14})
_st[1]["dieu_kien"] = [_dk]
_truoc = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                       "steps": _st, "edges": _ed})["ma"]
_dk["trai"]["ghim_num"] = {"n": "chu_ky"}
_dk["phai"]["ghim_num"] = {"so": "nguong"}
_sau = sinh_ma.sinh({"schema": 1, "type": "strategy", "name": "G",
                     "steps": _st, "edges": _ed})["ma"]
kiem("mặc định 14 ở lại trong câu get_parameter",
     "get_parameter('chu_ky', 14)" in _sau, f"— {'chu_ky' in _sau}")
kiem("mặc định 45 cũng thế", "get_parameter('nguong', 45)" in _sau)
kiem("và ghim làm mã ĐỔI thật, không phải cái ghim trang trí", _truoc != _sau)

print(f"\n{'=' * 60}\n  {dung} đúng · {sai} sai\n{'=' * 60}")
sys.exit(1 if sai else 0)
