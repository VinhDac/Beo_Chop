"""ĐÓNG GÓI SANG QUANTCONNECT — bộ luật Cat Studio + cầu nối + một sơ đồ → vài file Python.

Dùng ở hai chỗ: app (nút ▶ trên QuantConnect, qua `qc_chay`) và `tools/dong_goi_lean.py`
(đóng gói ra đĩa để dán tay). Ra `{tên file: nội dung}`: `main.py` + `nguon_1.py`…

VÌ SAO NHƯ VẬY
--------------
* QC giới hạn MỖI FILE theo gói: Free 32 KB, Researcher 64 KB, Team 128 KB. Riêng
  `core.py` đã 113 KB, nên chép từng module lên là không lọt.
* Nên nguồn các module được làm GỌN rồi NÉN, nhúng vào vài file dưới giới hạn. Một bộ nạp
  nhỏ trong `main.py` phục vụ `import cat_studio…` từ đó — bộ luật chạy trên QC là ĐÚNG
  bộ luật trong repo, không phải một bản chép tay.

"GỌN" chỉ bỏ comment và thay docstring bằng `pass`, làm trên TỪNG TOKEN — không đụng một
token code nào, và SỐ DÒNG của mọi câu lệnh giữ nguyên: lỗi báo trên QC ở `core.py` dòng
1234 là đúng dòng 1234 trong repo. `tests/test_cat_lean.py` kiểm cả hai điều đó.

Sơ đồ được SOÁT ở đây trước khi đóng gói: lỗi biên dịch (thiếu tham số, khung chưa hỗ
trợ…) nổ ra trên máy kèm nhãn khối, chứ không nổ sau 15 giây dựng máy trên cloud.
"""
import ast
import base64
import hashlib
import importlib.util
import io
import json
import lzma
import os
import sys
import tokenize
from datetime import datetime, timezone

#: Module nhúng cho CỖ MÁY 5 TRẠM: bộ máy thuần + lớp vỏ. `core` (và `luu_tru` mà nó
#: nạp) đi theo vì cỗ máy dùng lại bộ đồ thị của nó.
#: Tên nào trong gói nhúng là một GÓI (có `__init__`) chứ không phải module lẻ — bộ nạp
#: trong `main.py` phải biết để `import cat_studio.may` hoạt động trên QC.
GOI = ("cat_studio",)

NGUON_MAY = [
    ("cat_studio", "cat_studio/__init__.py"),
    ("cat_studio.luu_tru", "cat_studio/luu_tru.py"),
    ("cat_studio.core", "cat_studio/core.py"),
    ("cat_studio.tram", "cat_studio/tram.py"),
    ("cat_studio.may", "cat_studio/may.py"),
    ("cat_studio.chuoi_nen", "cat_studio/chuoi_nen.py"),
    ("cat_studio.bo_may", "cat_studio/bo_may.py"),
    ("vo_may", "lean/vo_may.py"),
]
#: Trần mỗi file, tính bằng BYTE UTF-8. Gói Free cho 32 KB — chừa lề cho chắc.
GIOI_HAN = 30_000
#: Trần của gói Researcher (64 KB) — đường API (app, `tools/chay_qc.py`) dùng trần này.
GIOI_HAN_RESEARCHER = 62_000
_RONG_DONG = 100


def _goc():
    """Gốc chứa nguồn để nhúng: gốc repo khi chạy từ mã nguồn, thư mục giải nén của bản
    đóng gói (`Cat_Studio.spec` mang theo các file `.py` này làm dữ liệu)."""
    from . import luu_tru
    return luu_tru.thu_muc_goi()


def doc_nguon(ds=None):
    ra = {}
    for ten, duong in ds or NGUON:
        with open(os.path.join(_goc(), duong), encoding="utf-8") as f:
            ra[ten] = f.read()
    return ra


def gon(code):
    """Bỏ comment, thay docstring bằng `pass`. Chỉ đụng token CHỮ, không đụng token code.

    Token `pass` thay docstring được cho kết thúc ngay sau 4 ký tự của nó: `untokenize`
    khi đó tự nối những dòng docstring cũ bằng dấu `\\` xuống dòng, nên số dòng của mọi
    câu lệnh phía sau giữ nguyên. Thay bằng `pass` chứ không xoá hẳn: hàm có thân CHỈ là
    docstring (`Engine.moi_nen`) xoá đi là thân rỗng, lỗi cú pháp."""
    doc = set()
    for n in ast.walk(ast.parse(code)):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                doc.add((b[0].value.lineno, b[0].value.col_offset))
    ra = []
    for t in tokenize.generate_tokens(io.StringIO(code).readline):
        if t.type == tokenize.COMMENT:
            continue
        if t.type == tokenize.STRING and t.start in doc:
            t = tokenize.TokenInfo(tokenize.NAME, "pass", t.start,
                                   (t.start[0], t.start[1] + 4), t.line)
        ra.append(t)
    return tokenize.untokenize(ra)


def nen_goi(doc, ds=None, khoa="so_do"):
    """`{nguon: các module đã gọn, so_do: sơ đồ}` → JSON → lzma → base85.

    Trả chuỗi ASCII không có `"`, `'`, `\\` — nhét thẳng vào chuỗi Python được. Sơ đồ đi
    CÙNG khối nén chứ không nằm trần trong `main.py`: nén còn ~1/4, đủ để cả gói vừa
    hai file dưới trần 32 KB của gói Free."""
    goi = {"nguon": {ten: gon(code) for ten, code in doc_nguon(ds).items()}, khoa: doc}
    tho = json.dumps(goi, ensure_ascii=False).encode("utf-8")
    return base64.b85encode(lzma.compress(tho, preset=9 | lzma.PRESET_EXTREME)).decode("ascii")


def _dong_khoi(chu):
    return [f'    "{chu[i:i + _RONG_DONG]}",' for i in range(0, len(chu), _RONG_DONG)]


def _byte(dong):
    return len(("\n".join(dong) + "\n").encode("utf-8"))


def khoa_mac_dinh(may):
    """Khoá Object Store mặc định của một cỗ máy. MỘT công thức duy nhất, dùng cả lúc
    đóng gói lẫn lúc tải về: hai công thức là hai cái tên, và lượt chạy sẽ ghi một nơi
    còn app đi tìm một nơi khác."""
    from . import may as M
    return f"cat_studio/may-{M.van_tay(may)}.jsonl.gz"


def dong_goi_may(may, cau_hinh, gioi_han=GIOI_HAN_RESEARCHER):
    """Đóng gói CỖ MÁY 5 TRẠM (D-10). `cau_hinh = {ma: [...], loai, tu, den, von[, khoa]}`.

    Cỗ máy còn lỗi thì từ chối NGAY tại máy, kèm câu báo lỗi đầu tiên — đừng để nó đi một
    vòng lên cloud rồi mới nổ."""
    from . import may as M
    loi = [p for p in M.soat(may) if p["severity"] == "error"]
    if loi:
        raise ValueError(f"Cỗ máy còn {len(loi)} lỗi, chưa đóng gói được: {loi[0]['message']}")
    may = M.chuan_hoa(may)
    ch = dict(cau_hinh)
    # Thiếu khoá thì lớp vỏ trên QC không biết ghi nhật ký vào đâu và chết giữa lượt —
    # điền sẵn khoá mặc định thay vì để nó nổ ở nơi xa nhất.
    ch.setdefault("khoa", khoa_mac_dinh(may))
    dong_ch = [f"    {json.dumps(k)}: {json.dumps(ch[k], ensure_ascii=False)},"
               for k in ("ma", "loai", "tu", "den", "von", "khoa") if k in ch]
    duoi = [
        "# ── THUẬT TOÁN · thân nằm ở lean/vo_may.py (trong khối nén) ───────────────────",
        "import vo_may as _vo",
        "",
        "_vo.CAU_HINH = CAU_HINH_NHUNG",
        "_vo.MAY = _GOI_NEN[\"may\"]",
        "",
        "",
        "class CatStudioMay(_vo.CatStudioMay):",
        '    """Lớp QuantConnect nhìn thấy. Toàn bộ thân ở lean/vo_may.py — đây chỉ là tên."""',
    ]
    return _dong_goi(nen_goi(may, NGUON_MAY, "may"), may.get("name"), M.van_tay(may),
                     "cỗ máy", dong_ch, "# ── CẤU HÌNH · mã của màn, khoảng ngày, vốn (D-10)",
                     "Muốn đổi cỗ máy: đóng gói lại.", duoi, gioi_han)


def _dong_goi(khoi, ten, van_tay, goi_la, dong_ch, dau_ch, doi_gi, duoi, gioi_han):
    """Chia khối nén vào `main.py` + các `nguon_k.py` dưới trần mỗi file."""
    # Mã gói phải đổi khi CHỖ CHIA đổi, không chỉ khi khối nén đổi: `main.py` dài ra một
    # dòng là ranh giới dịch đi — `nguon_1.py` cũ ghép với `main.py` mới sẽ lọt qua phép
    # so mã rồi mới vỡ lúc giải nén, với một câu lỗi chẳng ai đọc nổi. Giữ chỗ đúng 10 ký
    # tự lúc đo, tính mã thật sau khi chia (hai hàm dựng file đọc `ma` lúc được gọi).
    ma = "0" * 10
    luc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ten = (ten or "").replace("\n", " ")

    def tao_main(phan_main, so_phu):
        phu = [f"nguon_{k}.py" for k in range(1, so_phu + 1)]
        dong = [
            "# region imports",
            "from AlgorithmImports import *",
            "# endregion",
            "# " + "═" * 78,
            f"#  CAT STUDIO TRÊN QUANTCONNECT · {goi_la} «{ten}» · vân tay {van_tay}",
            f"#  sinh lúc {luc} bởi Cat Studio (cat_studio/goi_qc.py) — FILE SINH TỰ ĐỘNG · mã gói {ma}",
            f"#  Project cần ĐỦ {so_phu + 1} file cùng lần đóng gói: main.py"
            + "".join(f", {p}" for p in phu) + ".",
            f"#  Chỉ sửa khối CẤU HÌNH ngay dưới. {doi_gi}",
            "# " + "═" * 78,
            "",
            dau_ch,
            "CAU_HINH_NHUNG = {",
            *dong_ch,
            "}",
            "",
            "# ── BỘ LUẬT CAT STUDIO + CẦU NỐI — nguồn gọn, nén, nhúng. ĐỪNG SỬA. ──────────",
            "import base64 as _b64",
            "import importlib.abc as _iabc",
            "import importlib.util as _iutil",
            "import json as _json",
            "import sys as _sys",
            "try:",
            "    import lzma as _lzma",
            "except ImportError as _e:",
            "    raise ImportError('Python trên QuantConnect thiếu module lzma — báo lại để "
            "đóng gói bằng zlib.') from _e",
            *(["try:"]
              + [f"    from nguon_{k} import KHOI as _K{k}, MA as _M{k}"
                 for k in range(1, so_phu + 1)]
              + ["except ImportError as _e:",
                 "    raise ImportError('Project THIẾU file "
                 + ", ".join(phu) + " — ở cây file bên trái (nơi có main.py) tạo file "
                 "mới, đặt tên ĐÚNG như vậy (chữ thường, có đuôi .py, không nằm trong "
                 "thư mục con), dán TOÀN BỘ nội dung file cùng tên đã gửi kèm, rồi "
                 "chạy lại.') from _e"] if so_phu else []),
            "",
            f'_MA = "{ma}"',
            "for _k, _m in enumerate([" + ", ".join(f"_M{k}" for k in range(1, so_phu + 1))
            + "], 1):",
            "    if _m != _MA:",
            "        raise ImportError(f'nguon_{_k}.py không cùng lần đóng gói với main.py "
            "— dán lại CẢ BỘ file.')",
            "_KHOI_0 = (",
            *_dong_khoi(phan_main),
            ")",
            "_GOI_NEN = _json.loads(_lzma.decompress(_b64.b85decode(\"\".join(_KHOI_0"
            + "".join(f" + _K{k}" for k in range(1, so_phu + 1)) + "))).decode(\"utf-8\"))",
            "_NGUON = _GOI_NEN[\"nguon\"]",
            f"_GOI = {set(GOI)!r}",
            "",
            "",
            "class _NapNhung(_iabc.MetaPathFinder, _iabc.Loader):",
            '    """Phục vụ `import cat_studio…` / `import cat_lean` từ nguồn nhúng ở trên."""',
            "",
            "    def find_spec(self, ten, path=None, target=None):",
            "        if ten in _NGUON:",
            "            return _iutil.spec_from_loader(ten, self, is_package=ten in _GOI)",
            "        return None",
            "",
            "    def create_module(self, spec):",
            "        return None",
            "",
            "    def exec_module(self, mod):",
            "        duong = \"<cat_studio>/\" + mod.__name__.replace(\".\", \"/\") + \".py\"",
            "        mod.__file__ = duong",
            "        exec(compile(_NGUON[mod.__name__], duong, \"exec\"), mod.__dict__)",
            "",
            "",
            "_sys.meta_path.insert(0, _NapNhung())",
            "",
            *duoi,
        ]
        return "\n".join(dong) + "\n"

    def tao_phu(k, so_phu, phan):
        return "\n".join([
            f"# nguon_{k}.py — phần {k}/{so_phu} bộ luật Cat Studio đã nén.",
            f"# FILE SINH TỰ ĐỘNG bởi Cat Studio (cat_studio/goi_qc.py) · mã gói {ma} · ĐỪNG SỬA.",
            "# Phải đi cùng main.py của CÙNG lần đóng gói.",
            f'MA = "{ma}"',
            "KHOI = (",
            *_dong_khoi(phan),
            ")",
        ]) + "\n"

    # Chia khối: `main.py` chứa phần đầu tới khi đầy, phần còn lại chia đều các file phụ.
    for so_phu in range(0, 20):
        trong_main = gioi_han - len(tao_main("", so_phu).encode("utf-8")) - 200
        cho_moi = (_RONG_DONG * (gioi_han - 400)) // (_RONG_DONG + 8)
        if trong_main < 0:
            continue
        n_main = max(0, (trong_main * _RONG_DONG) // (_RONG_DONG + 8))
        con = len(khoi) - n_main
        if con <= so_phu * cho_moi and (so_phu > 0 or con <= 0):
            break
    else:
        raise RuntimeError("Gói quá to so với giới hạn file — nâng `gioi_han`.")
    n_main = min(n_main, len(khoi))
    ma = hashlib.sha1(f"{khoi}|{n_main}|{so_phu}".encode("ascii")).hexdigest()[:10]
    phan = [khoi[:n_main]]
    con = khoi[n_main:]
    if so_phu:
        co = -(-len(con) // so_phu)
        phan += [con[i:i + co] for i in range(0, len(con), co)]
    ra = {"main.py": tao_main(phan[0], so_phu)}
    for k in range(1, so_phu + 1):
        ra[f"nguon_{k}.py"] = tao_phu(k, so_phu, phan[k])
    for ten_file, noi_dung in ra.items():
        n = len(noi_dung.encode("utf-8"))
        if n > gioi_han:
            raise RuntimeError(f"{ten_file} {n} byte vượt giới hạn {gioi_han}.")
    return ra
