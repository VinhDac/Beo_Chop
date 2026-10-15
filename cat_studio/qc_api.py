"""NỐI QUANTCONNECT QUA API — chỗ DUY NHẤT trong app biết QuantConnect tồn tại.  (slice 3 · D-06)

Lõi (`core`, `bo_chay`) KHÔNG import file này. Chỉ dùng thư viện chuẩn (`urllib`) — không thêm gì vào requirements.

CÁCH GỌI API — đối chiếu với LEAN CLI, công cụ dòng lệnh chính thức của QC, mã nguồn mở
(`lean/components/api/*.py`), không đoán:

  * xác thực: header `Timestamp` + Basic(user_id, sha256("token:timestamp"))
  * trả JSON `{success, errors | messages}`; lỗi 5xx thử lại đúng một lần
  * projects/read|create · files/read|create|update|delete · compile/create|read ·
    backtests/create|read · object/get (trả LINK tải một file zip, có khi phải chờ job)
  * hỏi lại trạng thái thưa dần: 0,25 s → 1 s → 2 s → 5 s → 10 s, như CLI

KHOÁ LÀ BÍ MẬT (D-06): đọc từ biến môi trường `QC_USER_ID` / `QC_API_TOKEN`, hoặc
`du_lieu/qc_khoa.json`. Không bao giờ in khoá ra, không đưa vào câu lỗi hay nhật ký.

MỌI LỖI LÀ MỘT CÂU TIẾNG VIỆT nói phải làm gì (`LoiQC`) — người dùng không đọc traceback.
"""
import base64
import gzip
import hashlib
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API_GOC = "https://www.quantconnect.com/api/v2/"
NGON_NGU_PY = "Py"
FILE_KHOA = "qc_khoa.json"
THU_MUC_QC = "Cat Studio"

#: Lịch hỏi lại (giây, số lần) — y `TaskManager.poll` của LEAN CLI.
LICH_HOI = [(0.25, 4), (1, 9), (2, 10), (5, 54), (10, 10 ** 9)]


class LoiQC(Exception):
    """Lỗi nói được thành lời: đọc câu này là biết phải làm gì."""


class LoiKhoa(LoiQC):
    """Thiếu khoá, hoặc QC không nhận khoá."""


def doc_khoa(moi_truong=None, thu_muc=None):
    """`(user_id, token)` từ biến môi trường, rồi tới `du_lieu/qc_khoa.json`. Thiếu → `LoiKhoa`."""
    mt = os.environ if moi_truong is None else moi_truong
    uid, tok = (mt.get("QC_USER_ID") or "").strip(), (mt.get("QC_API_TOKEN") or "").strip()
    if uid and tok:
        return uid, tok
    if thu_muc is None:
        from . import luu_tru
        thu_muc = luu_tru.goc()
    duong = os.path.join(thu_muc, FILE_KHOA)
    try:
        # utf-8-sig: Notepad đời cũ lưu "UTF-8" kèm BOM ở đầu file — json đọc thẳng là vỡ.
        with open(duong, encoding="utf-8-sig") as f:
            d = json.load(f)
        uid, tok = str(d.get("user_id") or "").strip(), str(d.get("token") or "").strip()
    except FileNotFoundError:
        uid = tok = ""
    except (OSError, ValueError) as e:
        raise LoiKhoa(f"Đọc không được {duong}: {e}. File phải là JSON dạng "
                      f'{{"user_id": "...", "token": "..."}}.')
    if uid and tok:
        return uid, tok
    raise LoiKhoa(
        "Chưa có khoá QuantConnect. Lấy User ID và API token ở trang tài khoản QC, rồi "
        "đặt hai biến môi trường QC_USER_ID và QC_API_TOKEN, hoặc tạo file "
        f'{duong} với nội dung {{"user_id": "...", "token": "..."}}. '
        "Đừng đưa khoá vào git hay dán vào chat.")


def trang_thai_khoa(moi_truong=None, thu_muc=None):
    """Khoá đang đặt ở đâu — cho giao diện. KHÔNG BAO GIỜ trả token, chỉ nói có hay không."""
    mt = os.environ if moi_truong is None else moi_truong
    if thu_muc is None:
        from . import luu_tru
        thu_muc = luu_tru.goc()
    duong = os.path.join(thu_muc, FILE_KHOA)
    if (mt.get("QC_USER_ID") or "").strip() and (mt.get("QC_API_TOKEN") or "").strip():
        return {"co": True, "nguon": "bien_moi_truong", "user_id": mt["QC_USER_ID"].strip(),
                "duong": duong}
    try:
        uid, _ = doc_khoa({}, thu_muc)
    except LoiKhoa as e:
        return {"co": False, "nguon": None, "user_id": None, "duong": duong, "loi": str(e)}
    return {"co": True, "nguon": "file", "user_id": uid, "duong": duong}


def luu_khoa(user_id, token, thu_muc=None):
    """Ghi khoá vào `du_lieu/qc_khoa.json` (nằm trong .gitignore) — cho ô nhập trong app.
    Trả `trang_thai_khoa`. Sai dạng → `LoiKhoa` nói rõ, không nhắc lại token."""
    uid, tok = str(user_id or "").strip(), str(token or "").strip()
    if not uid.isdigit():
        raise LoiKhoa("User ID của QuantConnect là một dãy số — xem ở trang tài khoản QC.")
    if not tok or any(ch.isspace() for ch in tok) or len(tok) < 16:
        raise LoiKhoa("API token trông không đúng (rỗng, quá ngắn, hoặc có khoảng trắng). "
                      "Chép lại nguyên chuỗi token ở trang tài khoản QC.")
    from . import luu_tru
    if thu_muc is None:
        thu_muc = luu_tru.goc()
    luu_tru.ghi_json_nguyen_tu(os.path.join(thu_muc, FILE_KHOA),
                               {"user_id": uid, "token": tok})
    return trang_thai_khoa({}, thu_muc)


def xoa_khoa(thu_muc=None):
    """Xoá file khoá (không đụng biến môi trường). Trả `trang_thai_khoa`."""
    from . import luu_tru
    if thu_muc is None:
        thu_muc = luu_tru.goc()
    try:
        os.remove(os.path.join(thu_muc, FILE_KHOA))
    except FileNotFoundError:
        pass
    return trang_thai_khoa(None, thu_muc)


def _mo_mac_dinh(req, timeout):
    return urllib.request.urlopen(req, timeout=timeout)


class QC:
    """Phiên làm việc với API của QuantConnect.

    `mo`, `ngu`, `gio` để thay được trong bài kiểm (máy chủ giả, không ngủ thật). `gio`
    chỉ đo hạn chờ — dấu thời gian xác thực luôn lấy giờ thật, QC so nó với giờ của QC."""

    def __init__(self, user_id, token, goc=API_GOC, mo=None, ngu=time.sleep,
                 gio=time.time, timeout=60):
        self._uid, self._tok = str(user_id), str(token)
        self.goc = goc if goc.endswith("/") else goc + "/"
        self._mo = mo or _mo_mac_dinh
        self._ngu, self._gio, self._timeout = ngu, gio, timeout

    def __repr__(self):                     # đừng bao giờ để khoá lọt ra repr
        return f"QC(user_id={self._uid!r}, goc={self.goc!r})"

    # ------------------------------------------------------------------ gửi một yêu cầu
    def _yeu_cau(self, phuong_thuc, diem, tham_so=None):
        moc = str(int(time.time()))
        bam = hashlib.sha256(f"{self._tok}:{moc}".encode("utf-8")).hexdigest()
        tieu_de = {
            "Timestamp": moc,
            "Authorization": "Basic " + base64.b64encode(
                f"{self._uid}:{bam}".encode("utf-8")).decode("ascii"),
            "User-Agent": "Cat Studio",
            "Accept": "application/json",
        }
        url = urllib.parse.urljoin(self.goc, diem)
        du_lieu = None
        if phuong_thuc == "GET":
            if tham_so:
                url += "?" + urllib.parse.urlencode(tham_so)
        else:
            du_lieu = json.dumps(tham_so or {}).encode("utf-8")
            tieu_de["Content-Type"] = "application/json"
        return urllib.request.Request(url, data=du_lieu, headers=tieu_de, method=phuong_thuc)

    def _goi(self, phuong_thuc, diem, tham_so=None, thu_lai=True):
        try:
            with self._mo(self._yeu_cau(phuong_thuc, diem, tham_so), self._timeout) as r:
                ma, chu = r.status, r.read()
        except urllib.error.HTTPError as e:
            ma, chu = e.code, e.read()
        except (urllib.error.URLError, OSError) as e:
            raise LoiQC(f"Không kết nối được QuantConnect ({diem}): {getattr(e, 'reason', e)}. "
                        "Kiểm mạng / proxy, rồi chạy lại.")
        if 500 <= ma < 600 and thu_lai:
            return self._goi(phuong_thuc, diem, tham_so, thu_lai=False)
        if ma == 500:
            # LEAN CLI coi 500 lặp lại là lỗi xác thực — QC trả 500 khi băm khoá sai.
            raise LoiKhoa("QuantConnect trả lỗi 500 hai lần liền — thường là khoá sai "
                          "(User ID hoặc API token), đôi khi là QC đang trục trặc.")
        if not 200 <= ma < 300:
            raise LoiQC(f"QuantConnect trả mã HTTP {ma} cho {diem}.")
        try:
            d = json.loads(chu.decode("utf-8"))
        except ValueError:
            raise LoiQC(f"QuantConnect trả về thứ không phải JSON cho {diem}.")
        if d.get("success"):
            return d
        loi = d.get("errors") or d.get("messages") or ([d["Message"]] if d.get("Message") else [])
        loi = [str(x) for x in loi]
        if loi and loi[0].startswith("Hash doesn't match"):
            raise LoiKhoa("Khoá QuantConnect SAI: API token không khớp. Lấy lại token ở "
                          "trang tài khoản QC rồi cập nhật QC_API_TOKEN / qc_khoa.json.")
        if loi and loi[0].startswith("UserID not valid"):
            raise LoiKhoa("User ID QuantConnect không đúng. Xem lại số User ID ở trang tài "
                          "khoản QC rồi cập nhật QC_USER_ID / qc_khoa.json.")
        raise LoiQC(f"QuantConnect từ chối {diem}: " + ("; ".join(loi) or "không nói lý do."))

    def get(self, diem, tham_so=None):
        return self._goi("GET", diem, tham_so)

    def post(self, diem, tham_so=None):
        return self._goi("POST", diem, tham_so)

    def _hoi_toi_khi(self, hoi, xong, han_giay, viec):
        """Gọi `hoi()` thưa dần cho tới khi `xong(kq)`; quá `han_giay` → `LoiQC`."""
        bat_dau = self._gio()
        kq = hoi()
        for nghi, so_lan in LICH_HOI:
            lan = 0
            while lan < so_lan:
                if xong(kq):
                    return kq
                if self._gio() - bat_dau > han_giay:
                    raise LoiQC(f"Chờ {viec} quá {han_giay // 60} phút — QC có thể đang quá "
                                "tải. Xem trên web QC rồi chạy lại.")
                self._ngu(nghi)
                kq = hoi()
                lan += 1
        return kq

    # ------------------------------------------------------------------ từng việc
    def tim_project(self, ten):
        for p in self.get("projects/read").get("projects") or []:
            if p.get("name") == ten:
                return p
        return None

    def tao_project(self, ten):
        return self.post("projects/create", {"name": ten, "language": NGON_NGU_PY})["projects"][0]

    def ten_file(self, project_id):
        return {f.get("name") for f in self.get("files/read", {"projectId": project_id})
                .get("files") or []}

    def ghi_file(self, project_id, ten, noi_dung, da_co):
        diem = "files/update" if ten in da_co else "files/create"
        self.post(diem, {"projectId": project_id, "name": ten, "content": noi_dung})

    def xoa_file(self, project_id, ten):
        self.post("files/delete", {"projectId": project_id, "name": ten})

    def bien_dich(self, project_id, han_giay=600):
        tao = self.post("compile/create", {"projectId": project_id})
        cid = tao["compileId"]
        kq = self._hoi_toi_khi(
            lambda: self.get("compile/read", {"projectId": project_id, "compileId": cid}),
            lambda d: d.get("state") in ("BuildSuccess", "BuildError"), han_giay, "biên dịch")
        if kq.get("state") != "BuildSuccess":
            nhat = "\n".join(str(x) for x in (kq.get("logs") or [])[-12:])
            raise LoiQC("QuantConnect biên dịch KHÔNG được. Vài dòng cuối của QC:\n" + nhat)
        return cid

    def chay_backtest(self, project_id, compile_id, ten, tien_do=None, han_giay=1800):
        bt = self.post("backtests/create", {"projectId": project_id, "compileId": compile_id,
                                            "backtestName": ten})["backtest"]
        bid = bt["backtestId"]

        def hoi():
            d = self.get("backtests/read", {"projectId": project_id,
                                            "backtestId": bid})["backtest"]
            if tien_do:
                tien_do(float(d.get("progress") or 0.0))
            return d

        return self._hoi_toi_khi(hoi, _backtest_xong, han_giay, "backtest")

    def xoa_object(self, org_id, khoa):
        """Xoá một khoá khỏi Object Store. Không có khoá đó thì thôi — không phải lỗi."""
        try:
            self.post("object/delete", {"organizationId": org_id, "key": khoa})
        except LoiKhoa:
            raise
        except LoiQC:
            pass

    def kiem_khoa(self):
        """Hỏi QC khoá có dùng được không (`authenticate`, y LEAN CLI). Sai → `LoiKhoa`."""
        self.get("authenticate")
        return True

    def tai_object(self, org_id, khoa, han_giay=300):
        """Bytes của một khoá trong Object Store; zip QC gửi về không có file đó → `None`.

        QC từ chối hẳn (chẳng hạn khoá chưa có) → `LoiQC` mang lời của QC."""
        d = self.post("object/get", {"organizationId": org_id, "keys": [khoa]})
        if not d.get("url"):
            job = d.get("jobId")
            if not job:
                return None
            d = self._hoi_toi_khi(
                lambda: self.post("object/get", {"organizationId": org_id, "jobId": job}),
                lambda x: bool(x.get("url")), han_giay, "Object Store chuẩn bị file")
        try:
            # Link tải là link ký sẵn — KHÔNG gửi khoá kèm.
            with self._mo(urllib.request.Request(d["url"]), self._timeout) as r:
                goi = r.read()
        except (urllib.error.URLError, OSError) as e:
            raise LoiQC(f"Tải nhật ký từ Object Store hỏng: {getattr(e, 'reason', e)}.")
        try:
            with zipfile.ZipFile(io.BytesIO(goi)) as z:
                for ten in z.namelist():
                    if ten.replace("\\", "/").rstrip("/").endswith(khoa.split("/")[-1]):
                        return z.read(ten)
        except zipfile.BadZipFile:
            raise LoiQC("Object Store gửi về một file không phải zip — thử chạy lại.")
        return None

    def tai_nhat_ky(self, org_id, khoa, cho=(0, 2, 4, 8)):
        """Nhật ký gzip mà cầu nối ghi lúc backtest kết thúc. Trả `(bytes | None, lời QC)`.

        Thử cả bản chữ `<khoá>.b64` — lớp vỏ (`vo_qc._cat`) ghi bản đó khi `save_bytes`
        hỏng. File vừa ghi có khi cần vài giây mới hiện ở Object Store, nên hỏi lại sau
        `cho` giây trước khi chịu thua."""
        loi = ""
        for nghi in cho:
            if nghi:
                self._ngu(nghi)
            for k in (khoa, khoa + ".b64"):
                try:
                    b = self.tai_object(org_id, k, han_giay=120)
                except LoiKhoa:
                    raise
                except LoiQC as e:
                    loi = loi or str(e)
                    continue
                if b is not None:
                    return (b if k == khoa else base64.b64decode(b)), ""
        return None, loi


def _backtest_xong(d):
    """Y LEAN CLI (`is_backtest_done` + `QCBacktest.is_complete`): có lỗi hay vết lỗi là
    xong; không thì phải `completed` VÀ đã có cả hai bảng thống kê (QC đánh dấu xong
    trước khi ghi xong thống kê)."""
    if d.get("error") or d.get("stacktrace"):
        return True
    if not d.get("completed"):
        return False
    tk = d.get("statistics")
    return d.get("runtimeStatistics") is not None and isinstance(tk, dict)


def ten_project(doc):
    """`Cat Studio/<tên sơ đồ>` — dấu `/` làm QC xếp mọi cỗ máy vào một thư mục."""
    ten = " ".join(str(doc.get("name") or "so do").replace("/", "-").split())
    return f"{THU_MUC_QC}/{ten}"


def ma_luot():
    """Mã riêng của một lượt chạy: giờ UTC + 4 ký tự ngẫu nhiên — đặt vào khoá nhật ký."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-") + os.urandom(2).hex()


def chay(qc, doc, files, ten_backtest, thu_muc_nhat_ky, tien_do=None, khoa=None):
    """MỘT lượt ▶ trên QuantConnect, trọn vẹn. Trả dict kết quả.

    `files`: `{tên file: nội dung}` do `goi_qc.dong_goi` sinh ra cho `doc`.
    `tien_do(viec, ti_le)`: báo tiến độ — `ti_le` là None khi không đo được.
    `khoa`: khoá Object Store RIÊNG của lượt này — phải trùng `CAU_HINH["khoa"]` đã nhúng
    trong `files`. Có khoá riêng thì tải xong app XOÁ nó đi, Object Store không đầy dần."""
    from . import may as M

    def bao(viec, ti_le=None):
        if tien_do:
            tien_do(viec, ti_le)

    doc = M.chuan_hoa(doc)
    ten = ten_project(doc)
    bao(f"Tìm project «{ten}»")
    project = qc.tim_project(ten) or qc.tao_project(ten)
    pid, org = project["projectId"], project.get("organizationId")

    bao("Tải file lên QC")
    da_co = qc.ten_file(pid)
    for ten_f, noi_dung in files.items():
        qc.ghi_file(pid, ten_f, noi_dung, da_co)
    # File phụ của lần đóng gói trước mà lần này không còn → xoá, để project không mang
    # một `nguon_2.py` cũ nằm im lặng cạnh bộ mới.
    for cu in sorted(da_co):
        if cu.startswith("nguon_") and cu.endswith(".py") and cu not in files:
            qc.xoa_file(pid, cu)

    bao("Biên dịch")
    cid = qc.bien_dich(pid)

    bao("Chạy backtest", 0.0)
    bt = qc.chay_backtest(pid, cid, ten_backtest, lambda x: bao("Chạy backtest", x))
    url = f"https://www.quantconnect.com/project/{pid}/{bt.get('backtestId')}"
    if bt.get("error") or bt.get("stacktrace"):
        dau = str(bt.get("error") or "thuật toán dừng giữa chừng").strip()
        vet = "\n".join(str(bt.get("stacktrace") or "").strip().splitlines()[-8:])
        raise LoiQC(f"Backtest LỖI trên QuantConnect: {dau}\n{vet}\nXem đủ ở: {url}")

    bao("Tải nhật ký về")
    rieng = bool(khoa)
    if not khoa:
        from . import goi_qc
        khoa = goi_qc.khoa_mac_dinh(doc)
    du_lieu, loi = qc.tai_nhat_ky(org, khoa)
    if du_lieu is None:
        raise LoiQC("Backtest chạy XONG nhưng không lấy được nhật ký từ Object Store "
                    f"(khoá {khoa})" + (f" — QC nói: {loi}" if loi else "") + ". Dòng "
                    f"«lỗi Object Store» trên log của backtest nói lý do: {url}")
    try:
        chu = gzip.decompress(du_lieu)
    except (OSError, EOFError):
        raise LoiQC(f"Nhật ký tải về bị hỏng (không giải nén được) — chạy lại. {url}")
    os.makedirs(thu_muc_nhat_ky, exist_ok=True)
    duong = os.path.join(thu_muc_nhat_ky, khoa.split("/")[-1][:-len(".gz")])
    with open(duong, "wb") as f:
        f.write(chu)
    from . import ket_qua_may
    meta, _, _ = ket_qua_may.doc_file(duong, lay_luot=False)
    if rieng:                                   # đã nằm trên máy — dọn khỏi cloud
        for k in (khoa, khoa + ".b64"):
            qc.xoa_object(org, k)
    return {"url": url, "project_id": pid, "backtest_id": bt.get("backtestId"),
            "thong_ke_qc": bt.get("statistics") or {}, "duong_nhat_ky": duong, "meta": meta}
