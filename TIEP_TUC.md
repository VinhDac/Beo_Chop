# Tiếp tục — Cat Studio

> Cập nhật 15/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`. Đang làm trên máy local (Windows).

## 1. Đang ở đâu

**D-10 xong cả bảy phần, rồi D-11 dọn tiếp.** Chốt mới (16/10/2026): **app chỉ là VỎ của
QuantConnect** — không mô phỏng gì tại máy nữa. Bộ máy chạy, chuỗi nến, chỉ báo, lớp vỏ
LEAN, bộ đóng gói và ba đồ giả đã bị xoá (≈5.800 dòng).

**Trạng thái thật:**

| Việc | Được chưa |
|---|---|
| Vẽ cỗ máy 5 trạm, soát lỗi, đánh số | ✅ |
| Lưu / mở cỗ máy, lắp 22 mẫu, 4 cỗ máy dựng sẵn | ✅ |
| Bảng tham số, Gom, hộp thoại khối theo trạm | ✅ |
| Luật chơi (màn theo rổ, boss cả rổ, sao, sổ nộp) | ✅ còn nguyên |
| Nói chuyện với QuantConnect (khoá, project, file, backtest) | ✅ còn nguyên |
| **Chạy một cỗ máy** | ❌ **chưa** — đường chạy mới chưa dựng |

Bài kiểm: **7/7 bài qua**, nhưng đều là bài TĨNH (từ điển, chuẩn hoá, soát lỗi, cửa API,
giao diện). Không còn sàn giả nào để chạy thử.

## 2. Chạy ở máy local (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone
tools\chay_test.bat    REM phải thấy: ✔ 7/7 bài đều qua
tools\chay.bat         REM mở app — vẽ được, chưa chạy được
```

Xem giao diện trong trình duyệt: `.venv\Scripts\python.exe tools\xem_thu.py` →
`http://127.0.0.1:8777`, thêm `?qc=1` để xem cửa sổ Màn chơi.

## 3. Việc kế tiếp — dựng đường chạy mới

Chủ dự án sẽ chỉ đường lối. Nguyên tắc đã chốt ở D-11:

> **Cái gì QuantConnect làm được thì để QC làm. App chỉ giữ phần luật chơi.**

Nghĩa là: sơ đồ 5 trạm phải dịch thành một thuật toán QC dùng CHÍNH bộ khung của họ —
bộ chọn mã, chỉ báo, tín hiệu, mô hình chia vốn, mô hình rủi ro, mô hình khớp lệnh. Và từ
nay mỗi "item" trong game phải là **một món có thật của QC**, không phải một thứ ta tự
nghĩ rồi tự tính.

Hai việc đi kèm, sẽ quyết khi thiết kế:

* **Từ điển 5 trạm (`tram.py`) phải soát lại**: có đại lượng chỉ tồn tại vì bộ máy cũ tự
  tính (vd. «phút từ lúc đổi mục tiêu»). Món nào QC không có thì phải bỏ hoặc đổi.
* **Chữ «vì sao»**: phải do chính đoạn code gửi lên QC tự ghi ra.

## 4. Những việc còn để lại (không gấp)

* `webui/src/app.css` vẫn giữ luật của mấy hộp thoại đã xoá (core.md §24).
* Chương 2 của trò chơi: mới có 3 màn và 4 cỗ máy dựng sẵn.

## 5. Luật phải giữ

1. **Khoá API QuantConnect là BÍ MẬT.** Không dán vào chat, không commit, không in ra.
   Đặt ngoài repo: `QC_USER_ID` / `QC_API_TOKEN`, hoặc `du_lieu\qc_khoa.json` (thư mục
   `du_lieu\` đã bị chặn trong `.gitignore`), hoặc gõ vào hộp Khoá trong app. Khoá có
   toàn quyền tài khoản, kể cả giao dịch thật, nên chỉ dùng để chạy backtest.
2. Mỗi lần một lát nhỏ: nói trước định làm gì và tiêu chí xong; mọi thay đổi có bài kiểm;
   `tools\chay_test.bat` xanh rồi mới commit.
3. Commit message tiếng Việt, ngắn. Giải thích cho chủ dự án bằng tiếng Việt đời thường,
   không dán code.
4. Dữ liệu không được nhìn trước (point-in-time). Lõi không import giao diện hay mạng.
5. Quyết định lớn ghi vào `DECISIONS.md`. Mỗi phần xong ghi một mục trong
   `tai_lieu/core.md` (§18–§24 là của D-10; phần sau tiếp từ §25).
6. Không tự đổi bộ công cụ đã chọn: Python + pywebview, React + @xyflow/react + Vite.
7. Đẩy lên nhánh `claude/affectionate-thompson-8hqazr`. Không tạo pull request khi chưa
   được bảo.
8. Giao diện không tự ghép chữ trên khối, không tự tính số thứ tự, không tự soát luật
   nào: gửi cỗ máy sang Python rồi vẽ lại cái nhận về.

## 6. Bản đồ

**Python — `cat_studio/`**: `tram.py` (từ điển 5 trạm) · `may.py` (định dạng, chuẩn hoá,
soát lỗi, vân tay) · `chuoi_nen.py` · `bo_may.py` · `mau_tram.py` (22 mẫu + 4 cỗ máy dựng
sẵn) · `nhat_ky_may.py` · `goi_qc.py` · `qc_api.py` · `ket_qua_may.py` · `game.py` (màn,
boss, sao, sổ) · `qc_chay.py` · `core.py` (đồ thị, đánh số) · `luu_tru.py` · `api.py` (bề
mặt cho giao diện: `may_*`, `mo_qc`, `kho_danh_muc`, `ApiQC` cho cửa sổ Màn chơi).

**QuantConnect — `lean/vo_may.py`**: lớp vỏ chạy trên QC, không chứa luật nào.

**Giao diện — `webui/src/`**: `may/` (trình vẽ 5 trạm) · `qc/ManChoi.tsx` (cửa sổ Màn
chơi) · `components/` (TitleBar, Modal, ContextMenu, Icon, KhoDialog) · `chung/` (bảng
dưới, Vì sao, Thống kê) · `api.ts` (`py`, `pyQC`, `pyMay`) · `types.ts`.

**Bài kiểm — `tests/`** (12): `test_danh_so` · `test_may` · `test_chuoi_nen` ·
`test_bo_may` · `test_mau_tram` · `test_vo_may` · `test_qc_may` · `test_may_api` ·
`test_trinh_ve` · `test_giao_dien` · `test_o_so` · `test_qc_api`. Đồ giả: `san_gia.py`
(sàn giá), `lean_gia.py` (LEAN), `qc_gia.py` (máy chủ QC).

**Tài liệu**: `README.md` (app là gì, chơi thế nào) · `DECISIONS.md` (quyết định lớn) ·
`tai_lieu/core.md` §18–§24 (nhật ký kỹ thuật của D-10).

## 7. Câu lệnh dán cho Claude Code

```text
Đọc TIEP_TUC.md ở gốc repo, rồi DECISIONS.md mục D-10 và tai_lieu/core.md §19–§24.
Tôi không đọc code. App đã xong D-10 (cỗ máy 5 trạm trên QuantConnect).
Việc tôi muốn làm tiếp: <viết ở đây>.
Nói định làm gì + tiêu chí xong bằng tiếng Việt đời thường, rồi code + bài kiểm
+ chạy tools\chay_test.bat + commit tiếng Việt.
Khoá QuantConnect là bí mật: không bao giờ bảo tôi dán khoá vào chat.
```
