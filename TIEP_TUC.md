# Tiếp tục ở máy local — Cỗ máy 5 trạm (D-10)

> Cập nhật 15/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`.

## 1. Đang ở đâu

Ta đang thay hai sơ đồ Entry / Manage bằng **cỗ máy 5 trạm**, theo đúng cách QuantConnect chia
một thuật toán: ① Chọn mã → ② Tín hiệu → ③ Chia vốn → ④ Rủi ro → ⑤ Khớp lệnh. Kế hoạch 7 phần đã
được duyệt (*"đồng ý cả 3, xoá luôn tester, xây 5 trạm đi"*). **Đã xong 4/7 phần.**

| Phần | Việc | Trạng thái | Commit |
|---|---|---|---|
| 1 | Xoá Strategy Tester | ✅ xong | `12afe1e` |
| 2 | Lõi cỗ máy 5 trạm: từ điển khối, soát lỗi, đánh số, chữ trên khối | ✅ xong | `6c20b55` |
| 3 | Bộ máy chạy 5 trạm: nến, chỉ báo, lịch, chia vốn, rủi ro, khớp lệnh, 22 mẫu dựng sẵn, chữ «vì sao» | ✅ xong | `9d63c27` `011b7de` `62df375` |
| 4 | Cầu nối QuantConnect: lớp vỏ, đóng gói, chạy từ app, đọc kết quả | ✅ xong | `2714430` `cee465d` |
| 5 | **Trình vẽ 5 trạm** | ⏳ việc kế tiếp, chưa viết dòng nào | — |
| 6 | Màn chơi chạy cỗ máy 5 trạm | ⏳ | — |
| 7 | Dọn bộ máy cũ + tài liệu | ⏳ | — |

Bài kiểm: **22/22 bài qua**.

**Lưu ý khi mở app lúc này:** màn hình vẽ vẫn là sơ đồ cũ (Entry / Manage). Bộ máy 5 trạm đã
chạy được, nhưng chưa có màn hình để vẽ nó, cũng chưa có nút để chạy nó — đó chính là phần 5.

## 2. Lấy code về máy (Windows)

```bat
cd duong\dan\toi\Cat_studio
git fetch origin
git checkout claude/affectionate-thompson-8hqazr
git pull origin claude/affectionate-thompson-8hqazr
tools\setup.bat
tools\chay_test.bat
tools\chay.bat
```

- `tools\setup.bat`: cài lại thư viện và build lại giao diện. Cần chạy, vì giao diện đã đổi ở
  phần 1 (bỏ tester, bỏ thư viện biểu đồ của nó).
- `tools\chay_test.bat`: phải thấy dòng **✔ 22/22 bài đều qua**.
- `tools\chay.bat`: mở app.
- Sửa giao diện xong thì chạy `tools\build_ui.bat` mới thấy thay đổi.

## 3. Phần 5 — Trình vẽ 5 trạm (việc kế tiếp)

**Mục tiêu:** trong app, người chơi tự vẽ được một cỗ máy 5 trạm, thấy lỗi ngay trên khối,
lưu và mở lại được, rồi bấm ▶ trong Màn chơi (chế độ Sáng tạo) để chạy nó trên QuantConnect.

Chia lát. Mỗi lát: nói định làm gì và tiêu chí xong → chờ duyệt → làm → bài kiểm → commit.

| Lát | Việc | Xong khi |
|---|---|---|
| 5a | Cửa API cho trình vẽ (phía Python): cỗ máy mới; danh mục khối, đại lượng, tham số theo từng trạm; soát lỗi; đánh số và chữ trên khối; danh sách mẫu; lắp mẫu vào một trạm; lưu và mở cỗ máy | Bài kiểm gọi đủ các cửa; cỗ máy lưu rồi mở lại y hệt (cùng vân tay) |
| 5b | Dải 5 trạm ①→⑤ trên đầu canvas, trạm nào lỗi thì có chấm đỏ; bấm trạm nào thì canvas hiện sơ đồ của trạm đó; khối Bắt đầu hiện lịch chạy và khung nến | Mở app thấy 5 trạm của cỗ máy mẫu, bấm qua lại được, số thứ tự đúng |
| 5c | Hộp thoại khối theo trạm: mỗi trạm chỉ thấy khối "Làm" của nó; khối Hỏi chỉ cho chọn đại lượng hợp với trạm (vd. "tín hiệu" chỉ ở ③, "khớp lệnh" chỉ ở ⑤); tham số có tên | Thêm, sửa, xoá khối ở cả 5 trạm; lỗi hiện đúng khối |
| 5d | Chỉnh khối Bắt đầu (lịch, khung) và bảng Gom: ① giữ N mã và xếp theo gì; ③ giữ tiền mặt %, trần mỗi mã %, chỉ mua | Đổi lịch hoặc Gom thì soát lỗi và chữ cập nhật ngay |
| 5e | Nút "Lắp mẫu" cho từng trạm (22 mẫu, giữ núm đã vặn); nút mở cỗ máy mẫu "Theo EMA 4 mã" | Từ cỗ máy trắng, lắp 5 mẫu thì sạch lỗi |
| 5f | Nối sang Màn chơi: ô rổ mã, loại thị trường, ngày, vốn ở chế độ Sáng tạo; ▶ gửi cỗ máy 5 trạm; xem lô «vì sao»; soi một lượt thì tô đúng trạm, đúng khối | Chạy được trên máy chủ QC giả trong bài kiểm, và mở app thật thấy đủ các bước |
| 5.0 (tuỳ chọn, làm sớm được) | Lệnh dòng lệnh chạy cỗ máy mẫu trên QC thật. `tools\chay_qc` hiện chỉ biết sơ đồ cũ | Chủ dự án thử thật trên tài khoản QC ngay, không phải chờ trình vẽ |

## 4. Phần 6 và 7 (sau phần 5)

- **Phần 6 — Màn chơi cho cỗ máy 5 trạm:** màn chơi theo RỔ mã (thay vì một mã); boss = mua và
  giữ chia đều cả rổ; màn ẩn, chấm sao, nộp bài; kết quả hiện «vì sao» theo từng trạm, soi lên sơ
  đồ; thêm vài cỗ máy mẫu cho chương 1. Hiện chế độ Chiến dịch từ chối cỗ máy 5 trạm bằng câu
  "chưa mở — chạy chế độ Sáng tạo".
- **Phần 7 — Dọn bộ máy cũ:** bỏ hẳn sơ đồ Entry / Manage và sơ đồ mẫu Compress; bộ chạy cũ
  (`bo_chay.py`, `khop_lenh.py`, `so_lenh.py`, `kho/engine_d02.py`); cầu nối cũ
  (`lean/cat_lean.py`, `lean/vo_qc.py`, `lean/do_nhip.py`); đường đóng gói cũ; các bài kiểm của
  chúng. Viết lại README (README hiện vẫn tả hai sơ đồ Entry / Manage, đã cũ), `core.md`,
  `DECISIONS.md`.

## 5. Luật phải giữ (với cả Claude ở máy local)

1. **Khoá API QuantConnect là BÍ MẬT.** Không dán vào chat, không commit, không in ra. Đặt ngoài
   repo: hai biến môi trường `QC_USER_ID` / `QC_API_TOKEN`, hoặc file `du_lieu\qc_khoa.json`
   (thư mục `du_lieu\` đã bị chặn trong `.gitignore`), hoặc gõ vào hộp Khoá trong app. Khoá có
   toàn quyền tài khoản, kể cả giao dịch thật, nên chỉ dùng để chạy backtest.
2. Mỗi lần một lát nhỏ: nói trước định làm gì và tiêu chí xong; mọi thay đổi có bài kiểm;
   `tools\chay_test.bat` xanh rồi mới commit.
3. Commit message tiếng Việt, ngắn. Giải thích cho chủ dự án bằng tiếng Việt đời thường, không
   dán code.
4. Dữ liệu không được nhìn trước (point-in-time). Lõi không import giao diện hay mạng.
5. Quyết định lớn ghi vào `DECISIONS.md`. Mỗi phần xong thì ghi một mục trong
   `tai_lieu/core.md` (mục §18–§21 là của D-10, phần 6 trở đi tiếp từ §22).
6. Không tự đổi bộ công cụ đã chọn: Python + pywebview, React + @xyflow/react + Vite.
7. Đẩy lên nhánh `claude/affectionate-thompson-8hqazr`. Không tạo pull request khi chưa được
   bảo.

## 6. Bản đồ cho Claude (kỹ thuật)

**Python — `cat_studio/`**

- `tram.py`: từ điển 5 trạm — khối Làm `KHOI_LAM` (14 khối), đại lượng `TOAN_HANG` (42), tham
  số `THAM_SO_TH`, lịch và khung mặc định, `GOM`, `CAN_CO`.
- `may.py`: cỗ máy (`DANG = "may5"`) — `may_moi`, `la_may`, `chuan_hoa` (chạy lại không đổi
  gì), `soat` → `[{severity, tram, step, index, message}]`, `danh_so`, `kem_the`, `the_khoi`,
  `dong_khoi`, `van_tay`, `bang_tham_so`.
- `chuoi_nen.py`: gộp nến M1 lên khung lớn + chỉ báo tính dần, không nhìn trước.
- `bo_may.py`: `BoMay.buoc(t, nen_m1, tk)` → ý định lệnh; `nhan_khop`, `nhan_tu_choi`,
  `thong_ke`; `can_khoi_dong`, `giay_lich_khoi_dong`.
- `mau_tram.py`: 22 mẫu `MAU`, `ap_mau(may, tram, mau_key)`, `may_tu_mau`, `MAY_MAU`.
- `nhat_ky_may.py`: chữ «vì sao» (`DocNhatKy`).
- `ket_qua_may.py`: đọc kết quả tải về (`KetQuaMay`: `tom_tat`, `lo`, `lenh`, `soi`).
- `goi_qc.py`: `dong_goi_may(may, cau_hinh)` → bộ file `main.py` gửi lên QC.
- `qc_chay.py`: `ViecQC.bat_dau(may, "tu_do", tu_do={"ma": [...], "loai": "forex" | "cfd" |
  "co_phieu" | "crypto", "tu", "den", "von"})`; `soat_tu_do_may`; `mo_lai`.
- `qc_api.py`: nói chuyện với API của QC.
- `api.py`: các cửa cho giao diện (pywebview). Các cửa `qc_*` đã chạy được cỗ máy 5 trạm. Các
  cửa vẽ (`validate`, `describe`, `save_process`…) vẫn phục vụ sơ đồ cũ — lát 5a thêm cửa mới
  cho cỗ máy.

**QuantConnect — `lean/vo_may.py`**: lớp vỏ chạy trên QC, không chứa luật nào.

**Giao diện — `webui/src/`**: `App.tsx` (canvas @xyflow/react, sơ đồ cũ),
`components/StepNode.tsx` (vẽ khối), `components/ActionDialog.tsx` (hộp thoại khối cũ),
`components/ThamSoDialog.tsx`, `components/TemplatePicker.tsx`, `components/KhoDialog.tsx`,
`qc/ManChoi.tsx` (cửa sổ Màn chơi), `api.ts`, `types.ts`.

**Bài kiểm — `tests/`**: `chay_tat_ca.py` là danh sách 22 bài. Của D-10: `test_may`,
`test_chuoi_nen`, `test_bo_may`, `test_mau_tram`, `test_vo_may`, `test_qc_may`. Đồ giả:
`san_gia.py` (sàn giá giả), `lean_gia.py` (LEAN giả), `qc_gia.py` (máy chủ QC giả).

**Tài liệu**: `DECISIONS.md` mục D-10; `tai_lieu/core.md` §18 (bỏ tester), §19 (lõi), §20 (bộ
máy chạy), §21 (cầu nối QC).

## 7. Câu lệnh dán cho Claude Code ở máy local

```text
Đọc TIEP_TUC.md ở gốc repo, rồi DECISIONS.md mục D-10 và tai_lieu/core.md §19–§21.
Tôi không đọc code. Ta đang ở phần 5/7: trình vẽ 5 trạm. Làm lát 5a:
nói định làm gì + tiêu chí xong bằng tiếng Việt đời thường, chờ tôi duyệt,
rồi code + bài kiểm + chạy tools\chay_test.bat + commit tiếng Việt.
Khoá QuantConnect là bí mật: không bao giờ bảo tôi dán khoá vào chat.
```

## 8. Việc chỉ chủ dự án làm được

**Thử thật trên QuantConnect.** Cần gói Researcher trở lên, và khoá đặt ở một trong các chỗ an
toàn nói ở mục 5. Đến giờ, mọi lượt chạy cỗ máy 5 trạm mới chạy trên bản giả lập QC trong bài
kiểm. Thử thật được khi có lát 5.0 (dòng lệnh) hoặc lát 5f (nút ▶ trong app).
