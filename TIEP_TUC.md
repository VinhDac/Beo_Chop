# Tiếp tục — Cat Studio

> Cập nhật 15/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`. Đang làm trên máy local (Windows).

## 1. Đang ở đâu

**D-10 xong cả bảy phần.** App chỉ còn MỘT thế giới: **cỗ máy 5 trạm chạy trên
QuantConnect**. Sơ đồ Entry/Manage, bộ chạy tại máy, cầu nối cũ và giao diện của chúng đã
bị xoá hẳn.

| Phần | Việc | Commit |
|---|---|---|
| 1 | Xoá Strategy Tester | `12afe1e` |
| 2 | Lõi cỗ máy 5 trạm | `6c20b55` |
| 3 | Bộ máy chạy 5 trạm | `9d63c27` `011b7de` `62df375` |
| 4 | Cầu nối QuantConnect | `2714430` `cee465d` |
| 5 | Trình vẽ 5 trạm (6 lát) | `3cb4a61` `099de26` `7b24dad` `a981211` `c1d5081` `40b4a06` |
| 6 | Màn chơi cho cỗ máy (4 lát) | `69e4665` `0cf17f0` `5b758b8` `b6a50f5` |
| 7 | Dọn bộ máy cũ | `d89f9fa` `72436ea` |

Bài kiểm: **12/12 bài qua** (`tools\chay_test.bat`).

**Mở app ra thấy gì:** trình vẽ 5 trạm với một cỗ máy mẫu chạy được — dải ①→⑤ trên đầu,
canvas vẽ sơ đồ của trạm đang mở, bảng Vấn đề ở dưới. Bấm **◆ Màn chơi** để chạy nó trên
QuantConnect: Chiến dịch (3 màn, boss «mua rồi giữ cả rổ», sao, nộp) hoặc Sáng tạo (rổ mã
tuỳ ý).

## 2. Chạy ở máy local (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone: .venv + thư viện + build giao diện
tools\chay_test.bat    REM phải thấy: ✔ 12/12 bài đều qua
tools\chay.bat         REM mở app
```

* Sửa giao diện xong thì `tools\build_ui.bat` mới thấy thay đổi.
* Xem giao diện trong **trình duyệt** (chụp ảnh, đọc console, cho máy bấm thử):
  `.venv\Scripts\python.exe tools\xem_thu.py` → `http://127.0.0.1:8777`, `?qc=1` để xem
  cửa sổ Màn chơi. Gọi `api.py` thật, chỉ thay đường vận chuyển.
* Chạy một cỗ máy bằng dòng lệnh: `tools\chay_qc.bat --man kim-loai-2024` (cần khoá QC).

## 3. Việc kế tiếp — của chủ dự án

**Chạy thật trên QuantConnect.** Đến giờ mọi lượt mới chạy trên bản giả lập QC trong bài
kiểm; chạy trên tài khoản thật là bài nghiệm thu còn lại. Cần gói **Researcher** trở lên
và khoá đặt ở một trong các chỗ an toàn (mục 5).

Cách nhanh nhất: mở app → **◆ Màn chơi** → **Sáng tạo** → điền rổ mã, loại thị trường,
khoảng ngày, vốn → **▶ chạy**. Hoặc **Chiến dịch** → chọn màn → **▶ đầy đủ** → **Nộp ↑**.

Nếu lượt chạy thật lộ ra chỗ nào lệch (tên mã OANDA, dữ liệu cổ phiếu, phí, lô tối
thiểu…), đó là thứ chỉ chạy thật mới biết — xem core.md §21 "một giả định về QC".

## 4. Những việc còn để lại (không gấp)

* **`webui/src/app.css`** vẫn giữ luật của mấy hộp thoại đã xoá (core.md §24). Không dọn
  bằng máy được: class của React Flow nhìn y như class chết. Dọn tay khi sờ tới.
* **Chương 2 của trò chơi**: mới có 3 màn và 4 cỗ máy dựng sẵn.
* **Khối Gom riêng** cho Markowitz / Black-Litterman — chúng cần ma trận hiệp phương sai,
  không diễn tả được bằng một sơ đồ đọc từng mã (xem đầu `mau_tram.py`).

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
