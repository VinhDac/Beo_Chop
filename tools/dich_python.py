# -*- coding: utf-8 -*-
"""BỘ CÔNG CỤ SONG NGỮ — MỘT LỆNH cho cả app: nửa giao diện web (gọi `webui/dich/chay.mjs`,
đúng thứ `npm run dich` chạy) rồi nửa Python (tệp này; xem `cat_studio/ngon_ngu.py`).

    tools\\dich.bat               bọc câu Việt còn trần vào tr(), thêm / in chỗ trống cho câu
                                 chưa có bản tiếng Anh, rồi soát — cả web lẫn Python
    tools\\dich.bat --don         như trên, rồi bỏ khoá thừa khỏi hai bảng dịch
    tools\\dich.bat --chi-soat    chỉ soát, KHÔNG ghi gì — `tools\\phat_hanh.bat` chạy lối này
                                 ngay bước đầu, bộ bài kiểm cũng thế; đỏ là không phát hành được

Phần dưới đây tả nửa Python.

BỌC THẾ NÀO (chỉ chuỗi nằm TRONG hàm — chạy lúc dùng):
    "câu"                      -> tr("câu")
    f"… {x} … {y:.1f}"         -> tr("… {0} … {1:.1f}", x, y)
    "… %d …" % n               -> tr("… %d …") % n          (chỉ bọc câu, phép % để nguyên)
    f"{TEN_HIEN}: …"           -> tr("{0}: …", tr(TEN_HIEN))  (nhãn bảng hằng chèn vào câu)
Ghi xong mỗi tệp, công cụ GỠ BỌC bản mới rồi so cây cú pháp với bản cũ: phải y hệt, không thì
không ghi. Tức là ở tiếng Việt, tệp sau khi bọc chạy đúng như trước từng chữ — do cấu tạo.

CỐ Ý KHÔNG BỌC:
  · chuỗi NGOÀI mọi hàm (bảng hằng, thân lớp, giá trị mặc định của tham số) — bọc lúc nạp tệp
    là chốt cứng một thứ tiếng. Chúng là NHÃN: phải có bản tiếng Anh, dịch lúc dùng `tr(BIẾN)`;
  · chuỗi đem so sánh, làm khoá dict / chỉ số, làm đối số của phép chuỗi (.startswith, .replace,
    .split…), của `re.*`, của `print` và `help=` của argparse (cho người viết mã), câu của
    `assert`, docstring, chuỗi đứng riêng một câu lệnh, và khối `if __name__ == "__main__"`.
    Bọc mấy thứ ấy là đổi LOGIC chứ không chỉ đổi chữ;
  · dòng có ghi chú `# không dịch` — chuỗi là dữ liệu (đuôi tên tệp, tên khoá trong file…);
  · dòng có ghi chú `# web dịch` — NHÃN của một từ điển mà GIAO DIỆN dịch lúc hiện ra.
    Dấu này riêng của Cat, Jenifer không có, và nó có vì luật nền "Python khai, giao diện chỉ
    bày lại": năm từ điển (`hoi`, `lam`, `bat_dau`, `cai_dat`, `toi_uu`) là nguồn của gần hết
    chữ trong các hộp thoại, mà nhãn của chúng phần lớn nằm NGOÀI hàm nên đã tự miễn. Mấy cái
    còn lại do một hàm DỰNG BẢNG sinh ra (`_o_phut`, `_o_nguong`, `nhan_ro`) — tức chạy một
    lần lúc nạp tệp hay lúc giao diện hỏi từ điển, chứ không phải mỗi lần hiện. Bọc `tr` ở đó
    là CHỐT CỨNG thứ tiếng của lúc ấy: gạt sang tiếng Việt thì đúng mấy nhãn ấy đứng im bằng
    tiếng Anh, mà không lỗi, không cảnh báo. Nên chúng ở lại tiếng Việt và `tr(nhãn)` bên web
    lo — `tools/nhan_python_dich.py` kê chúng ra cho cổng bên ấy đòi bản tiếng Anh.

CỔNG (mọi tệp `cat_studio/*.py`): không còn câu Việt trần; mọi câu trong tr("…") và mọi nhãn
bảng hằng có bản tiếng Anh; ô điền hai bên khớp nhau; bản tiếng Anh không lẫn chữ có dấu; câu
có ở cả bảng web lẫn bảng Python thì hai bản giống hệt; không biến nào tên `tr`; câu đã dịch
không bị đem so sánh; tệp nào gọi tr() cũng có dòng nhập nó.
"""
import ast
import io
import json
import keyword
import os
import re
import string
import subprocess
import sys
import tempfile
import tokenize

sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "cat-studio-pyc")

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MA = os.path.join(GOC, "cat_studio")
BANG = os.path.join(MA, "tieng_anh.py")
RONG = 100                      # cột tối đa của dòng công cụ tự dàn

# MỌI TỆP của `cat_studio/` vào cổng — tệp mới thêm vào gói là tự vào cổng, không phải nhớ khai ở
# đâu. `TEP_XONG` chỉ còn là chỗ cho bài kiểm đặt một danh sách riêng để soát bản sao nhỏ của kho.
TEP_XONG = None
#: `ngon_ngu.py` + `tieng_anh.py` là chính bộ dịch. `__init__.py` chỉ có docstring (mà docstring
#: thì cổng vốn đã bỏ qua) — để ngoài cho rõ, chứ không phải một ngoại lệ phải nhớ.
BO_TEP = {"ngon_ngu.py", "tieng_anh.py", "__init__.py"}
DAU_BO = "# không dịch"
#: Nhãn từ điển — giao diện dịch lúc hiện ra. Xem lời tựa; cổng bên web đòi bản tiếng Anh của
#: nó, nên bỏ qua ở đây KHÔNG phải là bỏ nó ra ngoài song ngữ.
DAU_WEB = "# web dịch"
HAM_DICH = "tr"
NHAP = "from .ngon_ngu import tr"

DAU = re.compile("[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", re.I)
# Tiếng Việt KHÔNG DẤU mà không trùng chữ tiếng Anh — cùng bảng với `webui/dich/chung.mjs`.
KHONG_DAU = {"sau", "cao", "xong", "mua", "trong", "ngay", "qua", "khung", "chung", "sang", "cam",
             "lam", "khi", "nhanh", "thanh", "xanh", "trang", "tay", "chia", "giao", "kho", "cho",
             "sao", "theo", "xem", "bao", "doanh",
             "gom"}
PHEP_CHUOI = {"startswith", "endswith", "find", "rfind", "index", "rindex", "replace", "split",
              "rsplit", "partition", "rpartition", "count", "strip", "lstrip", "rstrip",
              "removeprefix", "removesuffix"}
HAM_BO = {"print", "getattr", "hasattr", "setattr", "isinstance", "open"}
HAM = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def tep_xong():
    """Tên các tệp cổng soát: mọi `cat_studio/*.py` trừ chính bộ dịch (`BO_TEP`)."""
    if TEP_XONG is not None:
        return list(TEP_XONG)
    return sorted(f for f in os.listdir(MA) if f.endswith(".py") and f not in BO_TEP)


def la_viet(s):
    """Chuỗi này là câu tiếng Việt (cần dịch) không — cùng luật với `laViet` bên web: có dấu là
    chắc; không dấu thì phải trông như câu chữ (có dấu cách, hay viết hoa chữ đầu) và có một từ
    trong `KHONG_DAU`, bỏ qua từ trông như mã (`ket_qua`, tên tệp)."""
    if DAU.search(s):
        return True
    g = s.strip()
    if not (" " in g or re.match(r"[A-Z]", g)):
        return False
    return any(not re.search(r"[_\-./:=]", tu)
               and any(t in KHONG_DAU for t in re.split(r"[^a-z]+", tu.lower()))
               for tu in g.split())


def chuoi(s):
    """`s` thành một chuỗi Python trong ngoặc kép, chữ có dấu / emoji giữ nguyên."""
    return json.dumps(s, ensure_ascii=False)


# ------------------------------------------------------------------ gỡ bọc, để so cây cú pháp
def _chuan(n):
    """f-string về dạng chuẩn: gộp mảnh chữ kề nhau, bỏ mảnh rỗng; không còn ô nào thì là chuỗi."""
    ra = []
    for v in n.values:
        if isinstance(v, ast.Constant):
            if not v.value:
                continue
            if ra and isinstance(ra[-1], ast.Constant):
                ra[-1] = ast.Constant(ra[-1].value + v.value)
                continue
            v = ast.Constant(v.value)
        ra.append(v)
    if all(isinstance(v, ast.Constant) for v in ra):
        return ast.Constant("".join(v.value for v in ra))
    return ast.JoinedStr(ra)


class _GoBoc(ast.NodeTransformer):
    """Bản TIẾNG VIỆT của một cây: `tr("câu")` -> "câu"; `tr("… {0} …", x)` -> f"… {x} …";
    `tr(BIẾN)` -> BIẾN. Hai tệp gỡ ra giống nhau thì chạy ở tiếng Việt giống nhau."""

    def visit_Call(self, n):
        self.generic_visit(n)
        if not (isinstance(n.func, ast.Name) and n.func.id == HAM_DICH and n.args
                and not n.keywords):
            return n
        dau = n.args[0]
        if len(n.args) == 1:
            return dau
        if not (isinstance(dau, ast.Constant) and isinstance(dau.value, str)):
            return n
        ra = []
        for chu, o, kieu, doi in string.Formatter().parse(dau.value):
            if chu:
                ra.append(ast.Constant(chu))
            if o is not None:
                ra.append(ast.FormattedValue(
                    value=n.args[1 + int(o)], conversion=ord(doi) if doi else -1,
                    format_spec=_chuan(ast.JoinedStr([ast.Constant(kieu)])) if kieu else None))
        return _chuan(ast.JoinedStr(ra))

    def visit_JoinedStr(self, n):
        self.generic_visit(n)
        return _chuan(n)

    def visit_Constant(self, n):
        return ast.Constant(n.value)


def ban_viet(nguon):
    """Dấu vân của `nguon` ở tiếng Việt: cây cú pháp đã gỡ bọc, bỏ dòng nhập `tr`."""
    cay = ast.parse(nguon)
    cay.body = [n for n in cay.body
                if not (isinstance(n, ast.ImportFrom) and n.module == "ngon_ngu")]
    return ast.dump(_GoBoc().visit(cay))


# ------------------------------------------------------------------ một tệp mã
class Tep:
    def __init__(self, duong, nguon=None):
        self.duong, self.ten = duong, os.path.basename(duong)
        if nguon is None:
            with open(duong, encoding="utf-8", newline="") as f:
                nguon = f.read()
        self.nguon = nguon
        self.eol = "\r\n" if "\r\n" in nguon else "\n"
        self.cay = ast.parse(nguon)
        self.dau_dong = [0] + [m.end() for m in re.finditer(r"\r\n|\r|\n", nguon)]
        self.cha = {}
        for n in ast.walk(self.cay):
            for c in ast.iter_child_nodes(n):
                self.cha[id(c)] = n
        self.loi = []            # việc công cụ không tự làm được — người viết phải sửa tay
        self.dai = []            # dòng tràn cột sau khi bọc
        # Vị trí mọi ghi chú `# …`: chuỗi nối qua nhiều dòng mà có ghi chú xen giữa thì dựng lại
        # chuỗi là mất ghi chú — chỗ ấy giữ nguyên hình.
        self.ghi_chu = [self._vt(t.start[0], len(t.line[:t.start[1]].encode("utf-8")))
                        for t in tokenize.generate_tokens(io.StringIO(nguon).readline)
                        if t.type == tokenize.COMMENT]
        self._xep()

    # ---- vị trí
    def _vt(self, dong, cot):
        d = self.dau_dong[dong - 1]
        c = self.dau_dong[dong] if dong < len(self.dau_dong) else len(self.nguon)
        return d + len(self.nguon[d:c].encode("utf-8")[:cot].decode("utf-8"))

    def khoang(self, n):
        return self._vt(n.lineno, n.col_offset), self._vt(n.end_lineno, n.end_col_offset)

    def noi(self, n):
        return f"{self.ten}:{n.lineno}"

    def _dong(self, vt):
        """(đầu dòng, cuối dòng không kể xuống dòng) của dòng chứa vị trí `vt`."""
        d = max(x for x in self.dau_dong if x <= vt)
        m = re.compile(r"\r\n|\r|\n").search(self.nguon, vt)
        return d, m.start() if m else len(self.nguon)

    # ---- xếp loại từng chuỗi
    def _xep(self):
        """`self.chu` = [(nút, loại)]: "boc" (câu trong hàm, chưa bọc), "da" (câu đã nằm trong
        tr), "nhan" (chuỗi ngoài hàm — nhãn, dịch lúc dùng). Chuỗi khác thì không ghi lại."""
        doc, trong_f = set(), set()
        for n in ast.walk(self.cay):
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                b = n.body
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant):
                    doc.add(id(b[0].value))
            # Chuỗi đứng riêng thành một câu lệnh (không gán, không gọi) là ghi chú, như docstring.
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant):
                doc.add(id(n.value))
            if isinstance(n, ast.JoinedStr):
                trong_f.update(id(v) for v in n.values if isinstance(v, ast.Constant))
            if isinstance(n, ast.FormattedValue) and n.format_spec is not None:
                trong_f.update(id(x) for x in ast.walk(n.format_spec))
        self.chu = []
        for n in ast.walk(self.cay):
            if id(n) in doc or id(n) in trong_f:
                continue
            if isinstance(n, ast.JoinedStr):
                chu = "".join(v.value for v in n.values if isinstance(v, ast.Constant))
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                chu = n.value
            else:
                continue
            if not la_viet(chu):
                continue
            loai = self._loai(n)
            if loai:
                self.chu.append((n, loai))

    def _lam_tin_hieu(self, x):
        """Nút `x` (một chuỗi, hay lời gọi tr bọc nó) có bị đem làm TÍN HIỆU không: so sánh,
        `in (…)`, đối số của phép chuỗi / `re.*` — kể cả khi nằm trong một bộ `("a", "b")`.
        Chuỗi trần ở chỗ ấy thì không bọc; câu ĐÃ bọc mà ở chỗ ấy là lỗi: so chữ đã dịch thì
        đổi ngôn ngữ là lệch."""
        con, cha = x, self.cha.get(id(x))
        while isinstance(cha, (ast.Tuple, ast.List, ast.Set)):
            con, cha = cha, self.cha.get(id(cha))
        if isinstance(cha, (ast.Compare, ast.MatchValue)):
            return True
        if isinstance(cha, ast.Call) and con in cha.args:
            f = cha.func
            return isinstance(f, ast.Attribute) and (
                f.attr in PHEP_CHUOI or (isinstance(f.value, ast.Name) and f.value.id == "re"))
        return False

    def _loai(self, n):
        cha = self.cha.get(id(n))
        if isinstance(cha, ast.Call):
            f = cha.func
            if isinstance(f, ast.Name) and f.id == HAM_DICH and cha.args and cha.args[0] is n:
                return "da"
            if n in cha.args and isinstance(f, ast.Name) and f.id in HAM_BO:
                return None
        if self._lam_tin_hieu(n):
            return None
        if isinstance(cha, ast.Dict) and any(k is n for k in cha.keys):
            return None
        if isinstance(cha, ast.Subscript) and cha.slice is n:
            return None
        if isinstance(cha, ast.Assert) and cha.msg is n:
            return None
        # Lời giải thích tham số dòng lệnh (argparse) là cho người viết mã, như `print`.
        if isinstance(cha, ast.keyword) and cha.arg in ("help", "description", "epilog"):
            return None
        if isinstance(cha, (ast.arg, ast.AnnAssign)) and getattr(cha, "annotation", None) is n:
            return None
        d, c = self.khoang(n)
        vung = self.nguon[self._dong(d)[0]:self._dong(c)[1]]
        if DAU_BO in vung or DAU_WEB in vung:
            return None
        return self._noi_chay(n)

    def _noi_chay(self, n):
        """Nút `n` chạy lúc DÙNG — trong thân một hàm ("boc") — hay lúc NẠP TỆP — ngoài hàm,
        thân lớp, giá trị mặc định / decorator của một hàm cấp ngoài cùng ("nhan")? None = nằm
        trong khối `if __name__ == "__main__"`."""
        con, x = n, self.cha.get(id(n))
        while x is not None:
            if isinstance(x, HAM):
                than = x.body if isinstance(x.body, list) else [x.body]
                if any(con is b for b in than):
                    return "boc"
            if isinstance(x, ast.If) and self.cha.get(id(x)) is self.cay \
                    and "__main__" in ast.unparse(x.test) and "__name__" in ast.unparse(x.test):
                return None
            con, x = x, self.cha.get(id(x))
        return "nhan"

    # ---- nhãn bảng hằng
    def bang_hang(self):
        """{TÊN: [nhãn tiếng Việt]} — mỗi biến cấp tệp mang chuỗi loại "nhan"."""
        if not hasattr(self, "_bh"):
            cua = {}
            for n, loai in self.chu:
                if loai != "nhan" or not isinstance(n, ast.Constant):
                    continue
                x = n
                while self.cha.get(id(x)) is not self.cay:
                    x = self.cha[id(x)]
                dich = (x.targets if isinstance(x, ast.Assign)
                        else [x.target] if isinstance(x, ast.AnnAssign) else [])
                for t in dich:
                    if isinstance(t, ast.Name):
                        cua.setdefault(t.id, []).append(n.value)
            self._bh = cua              # gán trước: hai tệp trỏ lẫn nhau thì không xoay vòng
            # Nhãn MƯỢN của tệp khác — `ACTION_LABELS = {DANG_BAN: dang_ban.TEN_HIEN, …}`: dịch
            # `tr(ACTION_LABELS[t])` là dịch cả nhãn ấy, nên bảng này cũng phải kể nó.
            nhap = self._ten_tep_nhap()
            for x in self.cay.body:
                dich = [t.id for t in (x.targets if isinstance(x, ast.Assign) else [])
                        if isinstance(t, ast.Name)]
                for e in (ast.walk(x.value) if dich else []):
                    if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name) \
                            and e.value.id in nhap:
                        t = tep_cua(nhap[e.value.id])
                        for k in (t.bang_hang().get(e.attr, []) if t and t is not self else []):
                            for ten in dich:
                                cua.setdefault(ten, []).append(k)
        return self._bh

    def _ten_tep_nhap(self):
        """{bí danh: tên module} của các lệnh nhập cấp tệp.

        ⚠ Cat_Studio gói mọi module vào `cat_studio/`, nên nó nhập anh em bằng
        `from . import hoi` — một `ImportFrom` KHÔNG CÓ tên module, chứ không phải
        `import hoi` như Jenifer. Thiếu nhánh ấy thì `goc_nhan` không nhận ra
        `hoi.PHEP_SO` là bảng hằng của tệp khác, và `tr(hoi.PHEP_SO[i][1])` đi qua cổng
        mà chẳng ai đòi bản tiếng Anh của mấy nhãn ấy."""
        ra = {}
        for n in ast.walk(self.cay):
            if isinstance(n, ast.Import):
                for a in n.names:
                    ra[a.asname or a.name] = a.name
            elif isinstance(n, ast.ImportFrom) and n.module is None and n.level == 1:
                for a in n.names:
                    ra[a.asname or a.name] = a.name
        return ra

    def goc_nhan(self, e):
        """Biểu thức `e` có phải một NHÃN bảng hằng không — `TÊN`, `TÊN[k]`, `TÊN.get(k)`,
        `TÊN.get(k, mặc_định)`, `module.TÊN[k]`. Trả (Tep chứa bảng, TÊN) hay None."""
        while True:
            if isinstance(e, ast.Subscript):
                e = e.value
            elif isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) \
                    and e.func.attr == "get" and len(e.args) in (1, 2):
                e = e.func.value
            else:
                break
        if isinstance(e, ast.Name):
            return (self, e.id) if e.id in self.bang_hang() else None
        if isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name):
            mod = self._ten_tep_nhap().get(e.value.id)
            t = tep_cua(mod) if mod else None
            return (t, e.attr) if t and e.attr in t.bang_hang() else None
        return None

    # ---- bọc
    def _thay(self, d, c, thay):
        """Nguồn [d, c) sau khi áp các chỗ thay nằm trong nó."""
        s, tru = self.nguon[d:c], 0
        for a, b, moi in sorted(x for x in thay if d <= x[0] and x[1] <= c):
            s = s[:a - d + tru] + moi + s[b - d + tru:]
            tru += len(moi) - (b - a)
        return s

    def _doi_so(self, e, thay):
        d, c = self.khoang(e)
        s = self._thay(d, c, thay)
        if isinstance(e, (ast.Tuple, ast.NamedExpr, ast.Yield, ast.YieldFrom)) \
                and not s.startswith("("):
            s = f"({s})"
        # Nhãn bảng hằng làm ô thì dịch lúc dùng — trừ khi `_nhan_chen` đã lo đúng chỗ ấy rồi.
        da_lo = any(a <= d and c <= b for a, b, _m in thay)
        da_boc = (isinstance(e, ast.Call) and isinstance(e.func, ast.Name)
                  and e.func.id == HAM_DICH)
        return f"{HAM_DICH}({s})" if self.goc_nhan(e) and not da_boc and not da_lo else s

    @staticmethod
    def _ruot(e):
        """`NHÃN.lower()` / `.upper()` / `.capitalize()`… -> chính `NHÃN`: đổi hoa thường là việc
        làm SAU khi dịch (`tr(NHÃN).lower()`)."""
        if isinstance(e, ast.Call) and not e.args and not e.keywords \
                and isinstance(e.func, ast.Attribute) \
                and e.func.attr in ("lower", "upper", "title", "capitalize", "strip"):
            return e.func.value
        return e

    def _cau(self, n, thay):
        """(câu mẫu, [đối số]) của nút chuỗi `n`, hay None nếu không tự bọc được."""
        if isinstance(n, ast.Constant):
            return n.value, []
        mau, ds = [], []
        for v in n.values:
            if isinstance(v, ast.Constant):
                mau.append(v.value.replace("{", "{{").replace("}", "}}"))
                continue
            kieu = ""
            if v.format_spec is not None:
                if not all(isinstance(x, ast.Constant) for x in v.format_spec.values):
                    return None
                kieu = ":" + "".join(x.value for x in v.format_spec.values)
            doi = {-1: "", 115: "!s", 114: "!r", 97: "!a"}[v.conversion]
            mau.append("{%d%s%s}" % (len(ds), doi, kieu))
            ds.append(self._doi_so(v.value, thay))
        return "".join(mau), ds

    def _dan(self, cot, mau, ds, duoi):
        """Lời gọi tr(…) dàn cho vừa `RONG` cột: câu dài cắt thành nhiều chuỗi kề nhau, thẳng
        hàng dưới chuỗi đầu. `cot` None = nằm giữa một biểu thức khác: để một dòng."""
        if cot is None:
            return f"{HAM_DICH}({', '.join([chuoi(mau)] + ds)})"
        thut = " " * (cot + len(HAM_DICH) + 1)
        cho = max(30, RONG - len(thut))
        dong, hien = [], ""
        for tu in re.findall(r"\S+\s*|\s+", mau) or [""]:
            if hien and len(chuoi(hien + tu)) > cho:
                dong.append(hien)
                hien = ""
            hien += tu
        dong.append(hien)
        ra = [chuoi(x) for x in dong]
        if ds:
            mot = ", " + ", ".join(ds)
            if len(thut) + len(ra[-1]) + len(mot) + 1 + len(duoi) <= RONG:
                ra[-1] += mot
            else:
                ra[-1] += ","
                if len(thut) + len(mot) - 1 + len(duoi) <= RONG:
                    ra.append(", ".join(ds))
                else:
                    ra += [x + "," for x in ds[:-1]] + [ds[-1]]
        return f"{HAM_DICH}(" + (self.eol + thut).join(ra) + ")"

    def _nhan_chen(self):
        """Nhãn bảng hằng CHÈN VÀO MỘT CHUỖI dựng trong hàm mà chưa dịch: bọc `tr(NHÃN)`. Mọi lối
        chèn — đối số của `tr("…{0}…", NHÃN)`, ô của f-string, `"… %s …" % NHÃN`,
        `"…{}…".format(NHÃN)` — và cả khi chuỗi ấy KHÔNG có chữ Việt nào
        (`f"{ACTION_LABELS[t]} @ ({x}, {y})"`, `"⛔ %s: %s" % (TEN_HIEN, ly)`): nhãn chèn vào chuỗi
        là để hiện ra. Nhãn là dữ liệu thì ghi `# không dịch` trên dòng ấy.
        Trả [(nút, đầu, cuối, nguồn mới)]."""
        cho = []                                    # [(nút chuỗi, [biểu thức chèn vào])]
        for n in ast.walk(self.cay):
            if isinstance(n, ast.JoinedStr):
                cho.append((n, [v.value for v in n.values
                                if isinstance(v, ast.FormattedValue)]))
            elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and (
                    self._la_chuoi(n.left)):
                cho.append((n, n.right.elts if isinstance(n.right, ast.Tuple) else [n.right]))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "format" and self._la_chuoi(n.func.value):
                cho.append((n, list(n.args) + [k.value for k in n.keywords]))
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id == HAM_DICH and len(n.args) > 1:
                cho.append((n, list(n.args[1:])))
        ra, da = [], set()
        for n, ds in cho:
            if self._noi_chay(n) != "boc":
                continue
            d0, c0 = self.khoang(n)
            vung = self.nguon[self._dong(d0)[0]:self._dong(c0)[1]]
            if DAU_BO in vung or DAU_WEB in vung:
                continue
            for e in ds:
                e = self._ruot(e)
                da_boc = (isinstance(e, ast.Call) and isinstance(e.func, ast.Name)
                          and e.func.id == HAM_DICH)
                d, c = self.khoang(e)
                if self.goc_nhan(e) and not da_boc and (d, c) not in da:
                    da.add((d, c))
                    ra.append((e, d, c, f"{HAM_DICH}({self.nguon[d:c]})"))
        return ra

    @staticmethod
    def _la_chuoi(x):
        """Chuỗi viết thẳng, hay chuỗi đã bọc `tr("…")`."""
        if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == HAM_DICH \
                and x.args:
            x = x.args[0]
        return isinstance(x, ast.Constant) and isinstance(x.value, str)

    def boc(self):
        """Nguồn mới với mọi câu "boc" đã bọc (chưa ghi). Trả (nguồn, [nơi đã bọc])."""
        ung = sorted(((n, self.khoang(n)) for n, loai in self.chu if loai == "boc"),
                     key=lambda x: x[1][1] - x[1][0])
        chen = self._nhan_chen()
        thay, noi = [x[1:] for x in chen], [self.noi(x[0]) for x in chen]
        for n, (d, c) in ung:
            # nằm trong một câu khác cũng sắp bọc, hay giữa một f-string không phải câu Việt
            trong = any(a <= d and c <= b and (a, b) != (d, c) for _n, (a, b) in ung) \
                or self._trong_f(n)
            cau = self._cau(n, thay)
            if cau is None:
                self.loi.append(f"{self.noi(n)}  f-string có ô định dạng lồng biểu thức — bọc tay")
                continue
            goc = self.nguon[d:c]
            co_ghi_chu = any(d <= g < c for g in self.ghi_chu)
            if isinstance(n, ast.Constant) and (
                    co_ghi_chu or re.match(r'[a-zA-Z]*("""|\'\'\')', goc)):
                moi = f"{HAM_DICH}({goc})"      # khối ba nháy, ghi chú xen giữa: giữ nguyên hình
            elif co_ghi_chu:
                self.loi.append(f"{self.noi(n)}  f-string có ghi chú xen giữa các dòng — bọc tay")
                continue
            else:
                d, c = self._ngoac_thua(d, c)
                dd, dc = self._dong(d)
                moi = self._dan(None if trong else d - dd, cau[0], cau[1],
                                self.nguon[c:self._dong(c)[1]])
            thay = [x for x in thay if not (d <= x[0] and x[1] <= c)] + [(d, c, moi)]
            noi.append(self.noi(n))
        moi = self._thay(0, len(self.nguon), thay) if thay else self.nguon
        # Tệp có gọi tr() thì phải có dòng nhập nó — kể cả khi lượt này không bọc thêm câu nào
        # (ai đó xoá mất dòng nhập thì tệp chết lúc chạy, không phải lúc nạp).
        goi_tr = thay or any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                             and n.func.id == HAM_DICH for n in ast.walk(self.cay))
        if goi_tr and not re.search(r"^from \.ngon_ngu import .*\btr\b", moi, re.M):
            moi = self._them_nhap(moi)
            noi.append(f"{self.ten}:1")
        if moi == self.nguon:
            return self.nguon, []
        if ban_viet(moi) != ban_viet(self.nguon) \
                or ast.get_docstring(ast.parse(moi)) != ast.get_docstring(self.cay):
            raise RuntimeError(f"{self.ten}: bản đã bọc KHÁC bản gốc ở tiếng Việt — không ghi")
        # Hai câu bọc trên cùng một dòng thì dòng ấy có thể tràn: công cụ không tự dàn cả câu lệnh.
        cu = set(re.split(r"\r\n|\r|\n", self.nguon))
        self.dai = [f"{self.ten}:{i}" for i, l in enumerate(re.split(r"\r\n|\r|\n", moi), 1)
                    if len(l) > RONG and l not in cu]
        return moi, sorted(noi, key=lambda x: int(x.split(":")[1]))

    def _ngoac_thua(self, d, c):
        """Khoảng [d, c) nới ra ôm cặp ngoặc đơn bao SÁT chuỗi — loại chỉ để nối chuỗi qua nhiều
        dòng, bọc xong là thừa. Ngoặc của một lời gọi `f(…)` thì không đụng: trước nó là tên
        (mà không phải từ khoá như `return`, `or`). Đoán sai cũng không lọt: bản mới phải qua
        phép so cây cú pháp mới được ghi."""
        s = self.nguon
        a, b = d - 1, c
        while a >= 0 and s[a] in " \t":
            a -= 1
        while b < len(s) and s[b] in " \t\r\n":
            b += 1
        if a < 0 or s[a] != "(" or b >= len(s) or s[b] != ")":
            return d, c
        truoc = re.search(r"(\w+|\S)?[ \t]*$", s[:a]).group(1) or ""
        la_goi = bool(re.match(r"[\w\])\"']", truoc[-1:])) and not keyword.iskeyword(truoc)
        return (d, c) if la_goi else (a, b + 1)

    def _trong_f(self, n):
        x = self.cha.get(id(n))
        while x is not None and not isinstance(x, ast.stmt):
            if isinstance(x, ast.FormattedValue):
                return True
            x = self.cha.get(id(x))
        return False

    def _them_nhap(self, nguon):
        """Thêm dòng nhập `tr` sau lệnh nhập cuối của khối nhập đầu tệp. Tệp không có lệnh nhập
        nào thì thêm ngay SAU docstring của tệp (không có docstring: trước câu lệnh đầu) — chèn
        lên trước docstring là tệp mất docstring."""
        than = ast.parse(nguon).body
        cuoi = None
        for n in than:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                cuoi = n
            elif cuoi is not None and not (isinstance(n, ast.Expr)
                                           and isinstance(n.value, ast.Constant)):
                break
        dau = [0] + [m.end() for m in re.finditer(r"\r\n|\r|\n", nguon)]
        if cuoi is None and than:
            co_doc = isinstance(than[0], ast.Expr) and isinstance(than[0].value, ast.Constant)
            dong = than[0].end_lineno if co_doc else than[0].lineno - 1
        else:
            dong = cuoi.end_lineno if cuoi is not None else 0
        vt = dau[dong] if dong < len(dau) else len(nguon)
        return nguon[:vt] + NHAP + self.eol + nguon[vt:]

    # ---- soát
    def can(self):
        """Câu tệp này CẦN bản tiếng Anh: {câu: nơi}. Kèm lỗi cổng vào `self.loi`."""
        ra = {}

        def them(k, noi):
            k = k.strip()
            if k and re.search(r"\w", k):
                ra.setdefault(k, noi)

        for n, loai in sorted(self.chu, key=lambda x: self.khoang(x[0])):
            if loai == "da" and self._lam_tin_hieu(self.cha[id(n)]):
                self.loi.append(f"{self.noi(n)}  câu đã dịch bị đem so sánh / làm đối số phép "
                                f"chuỗi — đổi ngôn ngữ là lệch; dùng tín hiệu không phải chữ")
            if loai == "da" and isinstance(n, ast.JoinedStr):
                self.loi.append(f"{self.noi(n)}  tr(f\"…\") — viết ô điền {{0}} và đưa giá trị "
                                f"vào sau, đừng để f-string trong tr")
            elif loai in ("da", "nhan") and isinstance(n, ast.Constant):
                them(n.value, self.noi(n))
        for n in ast.walk(self.cay):
            # tr(BIẾN): nhãn của bảng hằng ấy — kể cả bảng nằm ở tệp chưa chuyển
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id == HAM_DICH and n.args:
                g = self.goc_nhan(n.args[0])
                for k in (g[0].bang_hang()[g[1]] if g else []):
                    them(k, f"{g[0].ten}:{g[1]}")
            ten = (n.id if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
                   else n.arg if isinstance(n, ast.arg) else None)
            if ten == HAM_DICH:
                self.loi.append(f"{self.ten}:{n.lineno}  biến tên `{HAM_DICH}` che mất hàm dịch "
                                f"— đổi tên biến")
        return ra


_TEP = {}


def tep_cua(module):
    """Tep của `cat_studio/<module>.py` (đọc một lần), hay None nếu không phải module của app."""
    if module not in _TEP:
        p = os.path.join(MA, module + ".py")
        _TEP[module] = Tep(p) if os.path.exists(p) and module + ".py" not in BO_TEP else None
    return _TEP[module]


# ------------------------------------------------------------------ bảng dịch
def doc_bang(duong=None):
    """(bảng {câu: bản Anh}, {câu: số dòng}, các dòng của tệp, kiểu xuống dòng)."""
    with open(duong or BANG, encoding="utf-8", newline="") as f:
        nguon = f.read()
    eol = "\r\n" if "\r\n" in nguon else "\n"
    bang, dong = {}, {}
    for n in ast.parse(nguon).body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Dict):
            for k, v in zip(n.value.keys, n.value.values):
                bang[k.value], dong[k.value] = v.value, k.lineno
    return bang, dong, nguon.split(eol), eol


def o_dien(s):
    """Ô điền của một câu, để so hai bên: tập chỉ số `{n}` và dãy `%d`-kiểu-cũ theo thứ tự."""
    ngoac = sorted(set(re.findall(r"(?<!\{)\{(\d*)[^{}]*\}(?!\})", s)))
    return ngoac, re.findall(r"%[-+#0]*\d*(?:\.\d+)?[sdrfxXgeEi]", s)


def them_vao_bang(thieu, goi_y, duong=None):
    """Thêm câu còn thiếu vào đúng nhóm `# ── tệp` của nó, bản Anh để trống (hay lấy sẵn từ
    bảng web khi câu ấy có bên đó). `thieu` = [(câu, nơi)]."""
    duong = duong or BANG
    _b, _d, dong, eol = doc_bang(duong)
    dong_cuoi = max(i for i, l in enumerate(dong) if l.strip() == "}")
    for k, noi in thieu:
        nhom = f"    # ── {noi.split(':')[0]}"
        if nhom in dong:
            i = dong.index(nhom) + 1
            while i < dong_cuoi and not dong[i].startswith("    # ── "):
                i += 1
        else:
            dong.insert(dong_cuoi, nhom)
            dong_cuoi += 1
            i = dong_cuoi
        dong.insert(i, f"    {chuoi(k)}: {chuoi(goi_y.get(k, ''))},")
        dong_cuoi += 1
    with open(duong, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(dong))


def don_bang(thua, duong=None):
    """Bỏ khoá thừa — cả dòng của nó, và dòng nhóm nào bỏ xong thì trống trơn."""
    duong = duong or BANG
    _b, so_dong, dong, eol = doc_bang(duong)
    bo = {so_dong[k] - 1 for k in thua}
    dong = [l for i, l in enumerate(dong) if i not in bo]
    ra = []
    for i, l in enumerate(dong):
        sau = dong[i + 1] if i + 1 < len(dong) else ""
        if l.startswith("    # ── ") and (sau.startswith("    # ── ") or sau.strip() == "}"):
            continue
        ra.append(l)
    with open(duong, "w", encoding="utf-8", newline="") as f:
        f.write(eol.join(ra))
    return len(bo)


def bang_web():
    """Bảng dịch của giao diện web {câu: bản Anh} — đọc bằng chính bộ công cụ bên ấy. Trả
    (bảng, None) hay (None, vì sao không đọc được)."""
    try:
        r = subprocess.run(["node", os.path.join("dich", "bang.mjs")], capture_output=True,
                           cwd=os.path.join(GOC, "webui"), encoding="utf-8", timeout=120)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    if r.returncode:
        return None, (r.stderr or "").strip()[-400:] or f"mã thoát {r.returncode}"
    try:
        return json.loads(r.stdout), None
    except ValueError as e:
        return None, f"đầu ra không phải JSON: {e}"


# ------------------------------------------------------------------ chạy
def chay(chi_soat=False, don=False, in_=print):
    """Trả True nếu song ngữ đủ."""
    loi = False
    tep = []
    for ten in tep_xong():
        t = Tep(os.path.join(MA, ten))
        moi, noi = t.boc()
        if noi and chi_soat:
            loi = True
            in_(f"✘ {t.ten}: {len(noi)} câu Việt CHƯA bọc tr() — chạy `tools\\dich.bat` để bọc:")
        elif noi:
            with open(t.duong, "w", encoding="utf-8", newline="") as f:
                f.write(moi)
            in_(f"✔ {t.ten}: đã bọc {len(noi)} câu Việt mới:")
            dai = t.dai
            t = Tep(t.duong)
            if dai:
                in_(f"⚠ {t.ten}: {len(dai)} dòng dài quá {RONG} cột sau khi bọc — dàn lại tay: "
                    + ", ".join(d.split(":")[1] for d in dai))
        for n in noi:
            in_("    " + n)
        tep.append(t)
    _TEP.update({t.ten[:-3]: t for t in tep})

    can = {}
    for t in tep:
        for k, noi in t.can().items():
            can.setdefault(k, noi)
        if t.loi:
            loi = True
            in_(f"✘ {t.ten}: {len(t.loi)} chỗ phải sửa tay:")
            for l in t.loi:
                in_("    " + l)

    web, loi_web = bang_web()
    if web is None:
        in_("✘ không đọc được bảng dịch của web (webui/dich/bang.mjs) — không soát được hai "
            "bảng có khớp nhau không:")
        in_("    " + loi_web)
        return False
    bang = doc_bang()[0]
    thieu = [(k, noi) for k, noi in can.items() if k not in bang]
    if thieu and not chi_soat:
        them_vao_bang(thieu, web)
        in_(f"✔ đã thêm {len(thieu)} câu vào cat_studio/tieng_anh.py")
        bang = doc_bang()[0]
    trong = [(k, noi) for k, noi in can.items() if not bang.get(k)]
    if trong:
        loi = True
        in_(f"✘ {len(trong)} câu chưa có bản tiếng Anh — điền vào cat_studio/tieng_anh.py:")
        for k, noi in trong:
            in_(f"    {noi}  {k[:90]}")
    lech = [(k, noi) for k, noi in can.items() if bang.get(k) and o_dien(k) != o_dien(bang[k])]
    if lech:
        loi = True
        in_(f"✘ {len(lech)} câu có ô điền hai bên lệch nhau:")
        for k, noi in lech:
            in_(f"    {noi}  {k[:90]}")
    con_dau = [k for k, v in bang.items() if DAU.search(v)]
    if con_dau:
        loi = True
        in_(f"✘ {len(con_dau)} bản tiếng Anh còn lẫn chữ có dấu:")
        for k in con_dau:
            in_(f"    {k[:90]}")
    khac = [k for k, v in bang.items() if v and k in web and web[k] != v]
    if khac:
        loi = True
        in_(f"✘ {len(khac)} câu có ở cả hai bảng mà bản tiếng Anh KHÁC nhau "
            f"(cat_studio/tieng_anh.py ↔ webui/src/tieng_anh.ts):")
        for k in khac:
            in_(f"    {k[:60]}  →  Python: {bang[k][:50]!r}  ·  web: {web[k][:50]!r}")
    thua = [k for k in bang if k not in can]
    if thua and don and not chi_soat:
        in_(f"✔ đã bỏ {don_bang(thua)} khoá thừa khỏi bảng dịch")
    elif thua:
        in_(f"⚠ {len(thua)} khoá trong bảng dịch không còn dùng — `tools\\dich.bat --don` để bỏ:")
        for k in thua[:20]:
            in_("    " + k[:90])
    if not loi:
        in_(f"✔ song ngữ đủ: mọi câu tiếng Việt của {len(tep)} tệp Python đều có bản tiếng "
            f"Anh")
    return not loi


def chay_web(chi_soat=False, don=False, in_=print):
    """Nửa GIAO DIỆN WEB của cùng việc ấy — `webui/dich/chay.mjs`, đúng thứ `npm run dich` chạy.
    Trả True nếu song ngữ đủ."""
    co = (["--chi-soat"] if chi_soat else []) + (["--don"] if don else [])
    try:
        r = subprocess.run(["node", os.path.join("dich", "chay.mjs")] + co, capture_output=True,
                           cwd=os.path.join(GOC, "webui"), encoding="utf-8", timeout=600)
    except Exception as e:
        in_(f"✘ không chạy được bộ công cụ song ngữ của web (node): {type(e).__name__}: {e}")
        return False
    for dong in ((r.stdout or "") + (r.stderr or "")).splitlines():
        in_(dong)
    return r.returncode == 0


def chay_het(chi_soat=False, don=False, in_=print):
    """MỘT LỆNH cho cả hai nửa: giao diện web rồi Python. Trả True nếu cả hai cùng đủ."""
    in_("— Giao diện web (webui/src) —")
    web = chay_web(chi_soat, don, in_)
    in_("— Python (cat_studio) —")
    py = chay(chi_soat, don, in_)
    return web and py


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(0 if chay_het("--chi-soat" in sys.argv, "--don" in sys.argv) else 1)
