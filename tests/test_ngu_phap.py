"""NGỮ PHÁP báo giá — chuỗi số hạng, điều kiện gắn trên khối, luật kiểu.

Bài này canh thứ mà chạy vẫn ra số nhưng SỐ ĐÓ VÔ NGHĨA — loại lỗi backtest không tố
cáo, vì backtest chỉ biết có lãi hay lỗ chứ không biết câu lệnh có nghĩa hay không.

    `tồn kho ≥ 2 tick`         so một số đếm với một bề rộng giá
    `công bằng = spread`       đặt giá công bằng bằng bề rộng spread
    `biên ×= 2`                nhân một bề rộng giá với hệ số
    `biên += 2 tick` rồi `biên = spread`   → hai tick BỐC HƠI, sơ đồ nhìn vẫn hợp lý

Ba mục:

  1. CHỮ TRÊN HỘP   `core.dong_khoi` / `action_display` — người dùng tin vào chữ này,
                    nên nó sai là mọi thứ sau đó sai theo.
  2. LUẬT KIỂU      `validate_actions` — bắt bốn câu ở trên.
  3. THỨ TỰ         `_soat_ghi_de` — cái giá của việc chọn CHUỖI thay vì CÂY.

⚠ KHÔNG canh nội dung kho (đúng tám toán hạng, đúng những đích này): thêm `microprice`
vào là bài đỏ dù chẳng có gì hỏng. Canh cơ chế. Cùng lý lẽ với `test_kho_va_lenh.py`.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from cat_studio import api  # noqa: E402
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


def sh(dich, phep, he_so, toan_hang=None, don_vi=None, khi=None):
    luong = {"he_so": he_so}
    if toan_hang:
        luong["toan_hang"] = toan_hang
    if don_vi:
        luong["don_vi"] = don_vi
    ra = {"type": core.SO_HANG, "dich": dich, "phep": phep, "luong": luong}
    if khi:
        ra["khi"] = khi
    return ra


def loi(a):
    """Soát MỘT hành động — đi qua ĐÚNG đường hộp thoại đi: chuẩn hoá rồi mới soát.

    ⚠ Bản đầu của bài này gọi thẳng `validate_actions` trên dict thô, và nó BÁO XANH
    trong khi đường thật hỏng: `normalize_action` lặng lẽ sửa `biên ×= 2` thành
    `biên = 2` trước khi soát, nên câu lỗi "không nhận ×=" không bao giờ hiện. Bài kiểm
    thì vẫn xanh vì nó không đi qua chỗ sửa hộ ấy.

    Bài học chung: **kiểm trên đúng đường mà người dùng đi**, không kiểm trên một
    đường tắt trông giống nó."""
    ra = []
    core.validate_actions([core.normalize_action(a) or a],
                          lambda m, i=None: ra.append(m), core.TAB_BAO_GIA)
    return ra


# ================= 1. CHỮ TRÊN HỘP =================
print("\n▸ Chữ trên hộp — người dùng tin vào đúng dòng này")

kiem("hệ số 1 KHÔNG hiện: `biên = spread`, không phải `biên = 1 × spread`",
     core.action_display(sh("bien", "=", 1, "spread")) == "biên = spread",
     f"— {core.action_display(sh('bien', '=', 1, 'spread'))!r}")
kiem("hệ số khác 1 thì HIỆN — giấu đi là mất thông tin thật",
     core.action_display(sh("bien", "=", 2, "spread")) == "biên = spread × 2")

# ĐƠN VỊ GHÉP: hệ số mang đơn vị `<đích>/<toán hạng>`. Không bảng nào khai nó, nó được
# SUY RA — nên đây là chỗ duy nhất chứng minh phép suy ấy đúng.
kiem("đơn vị ghép suy ra được: `lệch += tồn kho × 0,5 tick/lot`",
     core.action_display(sh("lech", "+=", 0.5, "ton_kho", "tick"))
     == "lệch += tồn kho × 0,5 tick/lot",
     f"— {core.action_display(sh('lech', '+=', 0.5, 'ton_kho', 'tick'))!r}")

kiem("dấu phẩy thập phân kiểu Việt", "0,5" in core.action_display(
    sh("lech", "+=", 0.5, "ton_kho", "tick")))
# Gạch nối `-` ở cỡ chữ nhỏ trông như dấu nối số. Dấu trừ thật (U+2212) thì không.
ds = core.dong_khoi(sh("lot_ban", "=", 0, don_vi="lot", khi={
    "trai": {"ten": "ton_kho"}, "phep": "<=", "phai": {"value": -2000, "tinh": "lot"}}))
kiem("số âm dùng dấu TRỪ thật, không phải gạch nối",
     any("−2000" in x for x in ds), f"— {ds}")

kiem("`khi` hiện thành DÒNG RIÊNG trên hộp, không nhét chung một dòng",
     len(ds) >= 2 and ds[0].startswith("lot bán =") and ds[1].startswith("khi "),
     f"— {ds}")

# HẬU QUẢ phải hiện ra, không bắt nhớ luật trong đầu: `lot = 0` nghĩa là RÚT HẾT.
kiem("`lot = 0` nói thẳng là rút hết báo giá",
     any("rút hết" in x for x in core.dong_khoi(sh("lot", "=", 0, don_vi="lot"))))
kiem("`lot mua = 0` nói thẳng là bỏ một phía",
     any("bỏ phía MUA" in x for x in core.dong_khoi(sh("lot_mua", "=", 0, don_vi="lot"))))
kiem("`lot = 500` KHÔNG kèm câu hậu quả nào",
     len(core.dong_khoi(sh("lot", "=", 500, don_vi="lot"))) == 1)

kiem("hộp dùng tên NGẮN, dropdown dùng tên đầy đủ",
     core.TOAN_HANG_NGAN["ton_kho"] != core.TOAN_HANG_LABELS["ton_kho"]
     and core.TOAN_HANG_NGAN["ton_kho"] in core.action_display(
         sh("lech", "+=", 1, "ton_kho", "tick")))
kiem("toán hạng thiếu `ngan` thì rơi về tên đầy đủ, không vỡ",
     all(core.TOAN_HANG_NGAN.get(k) for k in core.TOAN_HANG_KEYS))

kiem("khối chưa đặt tên lấy ĐÍCH làm tiêu đề, không đề trơ 'Số hạng'",
     core.step_title(sh("cong_bang", "=", 1, "mid")) == "công bằng")


# ================= 2. LUẬT KIỂU =================
print("\n▸ Luật kiểu — bắt câu CHẠY ĐƯỢC MÀ VÔ NGHĨA")

kiem("câu đúng thì im lặng", not loi(sh("lech", "+=", 0.5, "ton_kho", "tick")))
kiem("`công bằng = mid` đúng", not loi(sh("cong_bang", "=", 1, "mid")))
kiem("`biên = spread` đúng", not loi(sh("bien", "=", 1, "spread")))

kiem("`công bằng = spread` → lỗi: một MỨC không nhận một BỀ RỘNG",
     any("MỨC giá" in m for m in loi(sh("cong_bang", "=", 1, "spread"))),
     f"— {loi(sh('cong_bang', '=', 1, 'spread'))}")
kiem("`biên = mid` → lỗi: một BỀ RỘNG không nhận một MỨC",
     any("KHOẢNG CÁCH" in m for m in loi(sh("bien", "=", 1, "mid"))))
kiem("`công bằng += spread` thì ĐƯỢC — cộng một bề rộng vào một mức là hợp lệ",
     not loi(sh("cong_bang", "+=", 1, "spread")))

kiem("`biên ×= 2` → lỗi: nhân một bề rộng giá không có nghĩa vật lý",
     any("chỉ nhận" in m for m in loi(sh("bien", "*=", 2, don_vi="tick"))))
kiem("`lot ×= 2` thì ĐƯỢC — khối lượng nhân được", not loi(sh("lot", "*=", 2)))
# Chuẩn hoá KHÔNG được sửa hộ một phép sai: sửa hộ là đổi ý nghĩa của khối rồi bày ra
# như thể người dùng viết vậy, mà câu lỗi đã có sẵn thì không bao giờ hiện được.
kiem("phép sai được GIỮ NGUYÊN qua chuẩn hoá, để soát còn tố cáo được",
     core.normalize_action(sh("bien", "*=", 2, don_vi="tick"))["phep"] == "*=")
kiem("phép KHÔNG PHẢI phép gán nào thì mới rơi về mặc định",
     core.normalize_action(sh("bien", "???", 2, don_vi="tick"))["phep"] == "=")

kiem("`lot = 2 × mid` → lỗi: khối lượng chỉ nhân được với đại lượng ĐẾM",
     any("ĐẾM" in m for m in loi(sh("lot", "=", 2, "mid"))))
kiem("`lot = 0,5 × KL bid` thì ĐƯỢC", not loi(sh("lot", "=", 0.5, "bid_kl")))
kiem("`biên = 2` thiếu thước đo → lỗi",
     any("thước đo" in m for m in loi(sh("bien", "=", 2))))

# ---- RANH GIỚI GIỮA "SỬA" VÀ "ĐOÁN" ----
# Chuẩn hoá được phép SỬA khi chỉ có đúng một khả năng, và bị CẤM đoán khi có nhiều
# hơn một. Ranh giới ấy là thứ dễ trôi nhất về sau, nên chốt bằng bốn phép ở đây.
kiem("SỬA: `lot = 500 tick` → đơn vị lot, vì lot không đo bằng gì khác được",
     core.normalize_action(sh("lot", "=", 500, don_vi="tick"))["luong"]["don_vi"] == "lot")
kiem("SỬA: `biên = spread × 2 tick` → bỏ thước thừa, spread đã tự mang đơn vị",
     "don_vi" not in core.normalize_action(sh("bien", "=", 2, "spread", "tick"))["luong"])
kiem("ĐOÁN: `biên = 2` KHÔNG được tự điền tick — 2 tick và 2 bps là hai lượng khác nhau",
     "don_vi" not in core.normalize_action(sh("bien", "=", 2))["luong"])
kiem("ĐOÁN: điều kiện trỏ vào đại lượng đã biến mất thì GIỮ, không nuốt cả điều kiện",
     (core.normalize_action({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "atr"}, "phep": ">", "phai": {"value": 1}}]})
      ["conditions"] or [{}])[0].get("trai", {}).get("ten") == "atr")

kiem("`công bằng = 65000 tick` → lỗi: đặt một MỨC thì phải là giá tuyệt đối",
     any("tuyệt đối" in m for m in loi(sh("cong_bang", "=", 65000, don_vi="tick"))))
kiem("`công bằng = 65000 giá` thì ĐƯỢC",
     not loi(sh("cong_bang", "=", 65000, don_vi="gia")))

# ---- điều kiện: cùng bộ luật ở CẢ cổng lẫn ô `khi` ----
dk_sai = {"trai": {"ten": "ton_kho"}, "phep": ">=", "phai": {"value": 2, "tinh": "tick"}}
kiem("`tồn kho ≥ 2 tick` → lỗi ở ô `khi`",
     any("không so được" in m for m in loi(sh("lot_mua", "=", 0, khi=dk_sai))))
kiem("cùng điều kiện ấy trong CỔNG cũng lỗi — một bộ luật, không phải hai",
     any("không so được" in m
         for m in loi({"type": core.CHECK_COND, "conditions": [dk_sai]})))

kiem("`có thấy sổ lệnh ≥ 5` → lỗi: đại lượng đúng/sai dùng phép riêng",
     any("đúng/sai" in m for m in loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "co_so"}, "phep": ">=", "phai": {"value": 5}}]})))
kiem("`spread là ĐÚNG` → lỗi ngược lại",
     any("đúng/sai" in m for m in loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "spread"}, "phep": "la_dung"}]})))
kiem("`có thấy sổ lệnh là SAI` thì ĐÚNG",
     not loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "co_so"}, "phep": "la_sai"}]}))

kiem("`spread > tồn kho` → lỗi: hai loại đại lượng khác nhau",
     any("không cùng loại" in m for m in loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "spread"}, "phep": ">", "phai": {"ten": "ton_kho"}}]})))
kiem("`bid ≥ mid` thì ĐÚNG — hai mức giá so được với nhau",
     not loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "bid"}, "phep": ">=", "phai": {"ten": "mid"}}]}))

kiem("cổng RỖNG → cảnh báo: nó luôn khớp",
     any("LUÔN khớp" in m for m in loi({"type": core.CHECK_COND, "conditions": []})))
kiem("toán hạng không có trong kho → lỗi, không im lặng bỏ qua",
     any("không có trong kho" in m for m in loi({"type": core.CHECK_COND, "conditions": [
         {"trai": {"ten": "atr"}, "phep": ">", "phai": {"value": 1}}]})))


# ================= 3. THỨ TỰ LÀ NGỮ NGHĨA =================
print("\n▸ Thứ tự — cái giá của việc chọn CHUỖI thay vì CÂY")


def chuoi(*hd):
    """Nối các số hạng thành một chuỗi thẳng, khối Bắt đầu ở đầu."""
    steps = [dict(core.make_start_step("BĐ"), id="s0", pos=[0.0, 0.0])]
    for i, a in enumerate(hd):
        steps.append(dict(a, id=f"s{i + 1}", kind=core.KIND_ACTION,
                          pos=[200.0, 100.0 * (i + 1)]))
    canh = [{"from": f"s{i}", "to": f"s{i + 1}", "port": "out"}
            for i in range(len(hd))]
    return core.validate_so_do(steps, canh, core.TAB_BAO_GIA)


ds = chuoi(sh("bien", "+=", 2, don_vi="tick"), sh("bien", "=", 1, "spread"))
kiem("`biên += 2 tick` rồi `biên = spread` → CẢNH BÁO hai tick bốc hơi",
     any(p["severity"] == "warning" and "gán ĐÈ" in p["message"] for p in ds),
     f"— {[p['message'] for p in ds]}")
kiem("cảnh báo chỉ đúng KHỐI gây ra, để bấm vào là nhảy tới",
     any(p.get("step") == "s2" for p in ds if "gán ĐÈ" in p["message"]))
kiem("thứ tự NGƯỢC LẠI thì sạch — đó mới là cách viết đúng",
     not chuoi(sh("bien", "=", 1, "spread"), sh("bien", "+=", 2, don_vi="tick")))
kiem("cảnh báo chứ KHÔNG chặn: không có lỗi `error` nào",
     not [p for p in ds if p["severity"] == "error"])

# `biên` đặt cả `biên mua` lẫn `biên bán`, nên đè lên một trong hai cũng là đè.
kiem("`biên mua += …` rồi `biên = …` cũng bị bắt — `biên` chạm cả hai phía",
     any("gán ĐÈ" in p["message"] for p in chuoi(
         sh("bien_mua", "+=", 2, don_vi="tick"), sh("bien", "=", 1, "spread"))))
kiem("đè lên đích KHÁC thì không kêu",
     not chuoi(sh("lech", "+=", 2, don_vi="tick"), sh("bien", "=", 1, "spread")))


# ================= 4. SƠ ĐỒ MẪU =================
print("\n▸ Sơ đồ mẫu — market maker sơ cấp phải SẠCH")
r = api.Api().demo_process()
kiem("`▶ Mẫu` chạy được", r.get("ok"), "" if r.get("ok") else f"— {r.get('error')}")
if r.get("ok"):
    g = r["value"][core.TAB_BAO_GIA]
    ds = core.validate_so_do(g["steps"], g["edges"], core.TAB_BAO_GIA)
    kiem("không một lỗi, không một cảnh báo", not ds,
         f"— {[p['message'] for p in ds]}")
    # Mẫu phải đi qua ĐÚNG cái đường mà người dùng sẽ đi: mở file → chuẩn hoá → lưu.
    # Lệch một trường là "▶ Mẫu" hết dùng được làm chuẩn đối chiếu.
    d1 = core.normalize_process(api._so_do_mau())
    kiem("chuẩn hoá BẤT BIẾN — chạy hai lần bằng đúng một lần",
         core.normalize_process(d1) == d1)
    kiem("mẫu dựng sẵn đã ở dạng chuẩn, không cần ai sửa hộ",
         d1[core.TAB_BAO_GIA]["steps"]
         == core.normalize_process(api._so_do_mau())[core.TAB_BAO_GIA]["steps"])
    kiem("mọi hộp đều có chữ — không hộp nào trống trơn",
         all(c["lines"] or c["kind"] == core.KIND_START for c in g["cards"]))
    kiem("có đúng MỘT cổng, và nó hỏi về sức khoẻ dữ liệu",
         [c["id"] for c in g["cards"] if c["la_cong"]] == ["s_mu"])


# ================= 5. MỞ FILE CŨ =================
print("\n▸ File của thế giới nến — CHẶN, không mở ra sơ đồ trống")
# Mở được nhưng rỗng là cái bẫy tệ nhất: canvas trắng mang tên chiến lược cũ, Ctrl+S
# một cái là mất bản gốc. Đúng cái bẫy mà phép chặn file MỚI HƠN dựng lên để tránh.
try:
    core.normalize_process({"schema": 4, "name": "D_02", "entry": {"steps": []}})
    kiem("file schema cũ bị chặn", False, "— mở được, không nổ")
except ValueError as e:
    kiem("file schema cũ bị chặn", "market maker" in str(e))
    kiem("và NÓI RA chỗ lấy lại bản app đọc được nó", "f1c90fb" in str(e))
try:
    core.normalize_process({"schema": core.SCHEMA + 1})
    kiem("file schema mới hơn cũng bị chặn", False, "— mở được, không nổ")
except ValueError as e:
    kiem("file schema mới hơn cũng bị chặn", "mới hơn" in str(e))
kiem("file KHÔNG có schema (mới toanh / chép tay) thì vẫn mở được",
     core.normalize_process({"name": "x"})["schema"] == core.SCHEMA)


print("\n" + "=" * 52)
print(f"  {dung} đúng, {sai} sai")
print("=" * 52)
sys.exit(1 if sai else 0)
