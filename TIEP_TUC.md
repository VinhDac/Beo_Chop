# Tiếp tục — Cỗ máy 5 trạm (D-10)

> Cập nhật 15/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`. Đang làm trên máy local (Windows).

## 1. Đang ở đâu

Ta đang thay hai sơ đồ Entry / Manage bằng **cỗ máy 5 trạm**, theo đúng cách QuantConnect chia
một thuật toán: ① Chọn mã → ② Tín hiệu → ③ Chia vốn → ④ Rủi ro → ⑤ Khớp lệnh. **Đã xong 5/7
phần.**

| Phần | Việc | Trạng thái | Commit |
|---|---|---|---|
| 1 | Xoá Strategy Tester | ✅ xong | `12afe1e` |
| 2 | Lõi cỗ máy 5 trạm: từ điển khối, soát lỗi, đánh số, chữ trên khối | ✅ xong | `6c20b55` |
| 3 | Bộ máy chạy 5 trạm: nến, chỉ báo, lịch, chia vốn, rủi ro, khớp lệnh, 22 mẫu, chữ «vì sao» | ✅ xong | `9d63c27` `011b7de` `62df375` |
| 4 | Cầu nối QuantConnect: lớp vỏ, đóng gói, chạy từ app, đọc kết quả | ✅ xong | `2714430` `cee465d` |
| 5 | **Trình vẽ 5 trạm** (6 lát: cửa API · dải ①→⑤ · hộp thoại khối · Bắt đầu + Gom + tham số · lắp mẫu · nối Màn chơi) | ✅ xong | `3cb4a61` `099de26` `7b24dad` `a981211` `c1d5081` `40b4a06` |
| 6 | **Màn chơi chạy cỗ máy 5 trạm** | ⏳ việc kế tiếp, chưa viết dòng nào | — |
| 7 | Dọn bộ máy cũ + tài liệu | ⏳ | — |

Bài kiểm: **24/24 bài qua** (`tools\chay_test.bat`).

**Mở app lúc này** thấy ngay trình vẽ 5 trạm với một cỗ máy mẫu chạy được: dải ①→⑤ trên đầu,
canvas vẽ sơ đồ của trạm đang mở, bảng Vấn đề ở dưới. Sơ đồ cũ Entry / Manage **không còn lối
vào nào** — phần 7 sẽ xoá hẳn phần mã của nó.

## 2. Chạy ở máy local (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone: .venv + thư viện + build giao diện
tools\chay_test.bat    REM phải thấy: ✔ 24/24 bài đều qua
tools\chay.bat         REM mở app
```

- Sửa giao diện xong thì `tools\build_ui.bat` mới thấy thay đổi.
- Muốn **nhìn giao diện trong trình duyệt** (chụp ảnh, đọc console, cho máy bấm thử):
  `.venv\Scripts\python.exe tools\xem_thu.py` → `http://127.0.0.1:8777`, thêm `?qc=1` để xem
  cửa sổ Màn chơi. Nó gọi `api.py` THẬT, chỉ thay đường vận chuyển. Không phải lối chạy của
  app.

Ba cái bẫy của máy mới đã sửa trong commit `befb099`, ghi lại để khỏi gặp lại: Python con in
tiếng Việt bằng cp1252 trong khi cha đọc utf-8 · câu lọc «Python sạch» của bài kiểm gỡ luôn
`site-packages` vì `.venv` nằm trong repo · `requirements.txt` thiếu `numpy`.

## 3. Phần 6 — Màn chơi cho cỗ máy 5 trạm (việc kế tiếp)

**Mục tiêu:** chế độ Chiến dịch mở cho cỗ máy 5 trạm — màn chơi theo RỔ mã, có boss, có sao,
có nộp. Hiện Chiến dịch từ chối cỗ máy 5 trạm bằng câu *"chưa mở — chạy chế độ Sáng tạo"*, và
nút Chiến dịch trong cửa sổ Màn chơi bị khoá kèm đúng lý do đó.

Chia lát. Mỗi lát: nói định làm gì và tiêu chí xong → làm → bài kiểm → `tools\chay_test.bat`
xanh → commit.

| Lát | Việc | Xong khi |
|---|---|---|
| 6a | Màn chơi theo RỔ mã trong `game.py`: mỗi màn một rổ + loại thị trường + khoảng ngày (thấy / ẩn); boss = mua và giữ chia đều cả rổ từ lúc hết khởi động | Bài kiểm: danh sách màn mới, boss tính đúng trên rổ nhiều mã |
| 6b | Chấm sao + nộp cho cỗ máy 5 trạm: vé nộp theo vân tay cỗ máy, màn ẩn là ẩn (không lộ ngày), lịch sử ghi rổ | Chạy ▶ đầy đủ rồi Nộp trên máy chủ QC giả: ra sao, ra điểm, không lộ gì của màn ẩn |
| 6c | Cửa sổ Màn chơi: thẻ màn hiện rổ mã và boss, kết quả «vì sao» theo từng trạm, soi lên sơ đồ | Mở app thật: chọn màn → ▶ đầy đủ → Nộp → thấy sao và bảng điểm |
| 6d | Vài cỗ máy mẫu cho chương 1 (mỗi cái một ý tưởng, đều sạch lỗi) | Mở từ menu, chạy được ngay |

**Lưu ý cho phần 6:** vân tay cỗ máy (`may.van_tay`) hiện TÍNH CẢ `id` của khối, nên dựng lại
đúng một cỗ máy bằng tay vẫn ra vân tay khác. Nộp bài chấm theo vân tay, nên phải quyết: giữ
nguyên (vé nộp gắn với đúng file đó) hay bỏ `id` ra khỏi vân tay (hai cỗ máy giống hệt nhau về
luật thì là một). Chưa chốt — chốt trong 6b.

## 4. Phần 7 — Dọn bộ máy cũ (sau phần 6)

Bỏ hẳn: sơ đồ Entry / Manage và sơ đồ mẫu Compress · bộ chạy cũ (`bo_chay.py`,
`khop_lenh.py`, `so_lenh.py`, `tinh_toan.py`, `kho/engine_d02.py`) · cầu nối cũ
(`lean/cat_lean.py`, `lean/vo_qc.py`, `lean/do_nhip.py`) · đường đóng gói cũ · giao diện cũ
(`webui/src/App.tsx`, `components/ActionDialog.tsx`, `Ribbon.tsx`, `TemplatePicker.tsx`,
`ThamSoDialog.tsx`, biến `--khoi-sua`) · các bài kiểm của chúng. Bỏ `numpy` khỏi
`requirements.txt` (chỉ bộ chạy cũ cần). Viết lại README (vẫn đang tả hai sơ đồ Entry /
Manage, đã cũ), `core.md`, `DECISIONS.md`.

## 5. Luật phải giữ

1. **Khoá API QuantConnect là BÍ MẬT.** Không dán vào chat, không commit, không in ra. Đặt
   ngoài repo: hai biến môi trường `QC_USER_ID` / `QC_API_TOKEN`, hoặc file
   `du_lieu\qc_khoa.json` (thư mục `du_lieu\` đã bị chặn trong `.gitignore`), hoặc gõ vào hộp
   Khoá trong app. Khoá có toàn quyền tài khoản, kể cả giao dịch thật, nên chỉ dùng để chạy
   backtest.
2. Mỗi lần một lát nhỏ: nói trước định làm gì và tiêu chí xong; mọi thay đổi có bài kiểm;
   `tools\chay_test.bat` xanh rồi mới commit.
3. Commit message tiếng Việt, ngắn. Giải thích cho chủ dự án bằng tiếng Việt đời thường,
   không dán code.
4. Dữ liệu không được nhìn trước (point-in-time). Lõi không import giao diện hay mạng.
5. Quyết định lớn ghi vào `DECISIONS.md`. Mỗi phần xong thì ghi một mục trong
   `tai_lieu/core.md` (§18–§22 là của D-10; phần 6 tiếp từ §23).
6. Không tự đổi bộ công cụ đã chọn: Python + pywebview, React + @xyflow/react + Vite.
7. Đẩy lên nhánh `claude/affectionate-thompson-8hqazr`. Không tạo pull request khi chưa được
   bảo.
8. Giao diện không tự ghép chữ trên khối, không tự tính số thứ tự, không tự soát luật nào:
   gửi cỗ máy sang Python rồi vẽ lại cái nhận về.

## 6. Bản đồ (kỹ thuật)

**Python — `cat_studio/`**

- `tram.py`: từ điển 5 trạm — khối Làm `KHOI_LAM` (14), đại lượng `TOAN_HANG` (42), tham số
  `THAM_SO_TH`, lịch, khung, `GOM`, `CAN_CO`.
- `may.py`: cỗ máy (`DANG = "may5"`) — `may_moi`, `la_may`, `chuan_hoa`, `soat`, `soat_khoi`
  (soát MỘT khối cho hộp thoại), `danh_so`, `kem_the`, `the_khoi`, `dong_khoi`, `van_tay`.
- `chuoi_nen.py` · `bo_may.py` · `mau_tram.py` (22 mẫu) · `nhat_ky_may.py` · `ket_qua_may.py`
  · `goi_qc.py` · `qc_chay.py` · `qc_api.py` — xem core.md §19–§21.
- `api.py`: 14 cửa `may_*` cho trình vẽ (`may_boot`, `may_moi`, `may_mo_mau`, `may_kem_the`,
  `may_soat`, `may_khoi_moi`, `may_luu_khoi`, `may_ap_mau`, `may_ds/luu/mo/xoa`,
  `may_mo_file/luu_file`), `mo_qc` nhận cả hai dạng tài liệu, `ApiQC` cho cửa sổ Màn chơi.
- `luu_tru.py`: kho cỗ máy `du_lieu/co_may/`, tách khỏi kho chiến lược cũ.
- `game.py`: `do_gon` / `van_tay` đã hiểu cỗ máy 5 trạm.

**QuantConnect — `lean/vo_may.py`**: lớp vỏ chạy trên QC, không chứa luật nào.

**Giao diện — `webui/src/`**: `may/` là trình vẽ 5 trạm (xem core.md §22) · `qc/ManChoi.tsx`
cửa sổ Màn chơi (có chế độ Sáng tạo theo rổ mã) · `api.ts` (`py`, `pyQC`, `pyMay`) ·
`types.ts`. `App.tsx` và mấy component cũ còn nằm đó nhưng KHÔNG còn ai gọi — phần 7 xoá.

**Bài kiểm — `tests/`**: `chay_tat_ca.py` là danh sách 24 bài. Của D-10: `test_may`,
`test_chuoi_nen`, `test_bo_may`, `test_mau_tram`, `test_vo_may`, `test_qc_may`,
`test_may_api` (cửa API trình vẽ), `test_trinh_ve` (cầu sang `webui/kiem/trinh_ve.mjs`). Đồ
giả: `san_gia.py`, `lean_gia.py`, `qc_gia.py`.

**Tài liệu**: `DECISIONS.md` mục D-10; `tai_lieu/core.md` §18 (bỏ tester), §19 (lõi), §20 (bộ
máy chạy), §21 (cầu nối QC), §22 (trình vẽ + `tools/xem_thu.py`).

## 7. Câu lệnh dán cho Claude Code

```text
Đọc TIEP_TUC.md ở gốc repo, rồi DECISIONS.md mục D-10 và tai_lieu/core.md §19–§22.
Tôi không đọc code. Ta đang ở phần 6/7: Màn chơi cho cỗ máy 5 trạm. Làm lát 6a:
nói định làm gì + tiêu chí xong bằng tiếng Việt đời thường, rồi code + bài kiểm
+ chạy tools\chay_test.bat + commit tiếng Việt.
Khoá QuantConnect là bí mật: không bao giờ bảo tôi dán khoá vào chat.
```

## 8. Việc chỉ chủ dự án làm được

**Thử thật trên QuantConnect.** Cần gói Researcher trở lên, và khoá đặt ở một trong các chỗ an
toàn nói ở mục 5. Đến giờ mọi lượt chạy cỗ máy 5 trạm mới chạy trên bản giả lập QC trong bài
kiểm. Giờ thử thật được rồi: mở app → vẽ hoặc mở cỗ máy mẫu → **◆ Màn chơi** → chế độ **Sáng
tạo** → điền rổ mã, loại thị trường, khoảng ngày, vốn → **▶ chạy**.
