# Tiếp tục — Cat Studio

> Cập nhật 16/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`. Đang làm trên máy local (Windows).

## 1. Đang ở đâu

**Hai lần dọn liền nhau, kho đang ở trạng thái SẠCH ĐỂ LÀM LẠI.**

* **D-11 (16/10)** — app chỉ là **VỎ** của QuantConnect. Bộ mô phỏng tại máy (bộ máy chạy,
  chuỗi nến, chỉ báo, lớp vỏ LEAN, bộ đóng gói, ba đồ giả) đã xoá: ≈ 5.800 dòng.
* **D-12 (16/10)** — xoá **toàn bộ bộ khối cũ**: `tram.py` · `may.py` · `mau_tram.py` ·
  cả `webui/src/may/` · `ManChoi.tsx` · `webui/src/chung/` và sáu bài kiểm của chúng:
  ≈ 3.200 dòng nữa. Lý do: bộ khối ấy nghĩ ra TRƯỚC D-11 nên mỗi khối là một phép tính
  của riêng app — đúng cái D-11 cấm.

**Trạng thái thật:**

| Việc | Được chưa |
|---|---|
| Mở app, thanh tiêu đề, menu, hộp thoại | ✅ |
| Đặt / xoá / kiểm **khoá QuantConnect** | ✅ |
| Xem **app lưu file ở đâu** (hộp Kho) | ✅ |
| Đánh số phân cấp + soát nối dây (`core.py`) | ✅ còn nguyên, chưa có khối để dùng |
| Luật chơi (màn, boss, sao, sổ nộp) | ✅ còn nguyên, chưa nối vào đâu |
| Nói chuyện với QuantConnect (`qc_api.py`) | ✅ còn nguyên |
| **Vẽ một cỗ máy** | ❌ **chưa** — bộ khối mới chưa thiết kế |
| **Chạy một cỗ máy** | ❌ **chưa** — đường chạy mới chưa dựng |

Bài kiểm: **3/3 qua** (`test_danh_so` · `test_giao_dien` · `test_o_so`).
`tsc --noEmit` sạch, `npm run build` sạch.

Mở app lúc này thấy: một câu giữa màn hình nói app đang dựng lại, cộng hai hộp thoại còn
thật. Cố ý không để lại trình vẽ rỗng — canvas trống kèm thanh công cụ chết trông như app
hỏng, chứ không như app đang được làm lại.

## 2. Chạy ở máy local (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone
tools\chay_test.bat    REM phải thấy: ✔ 3/3 bài đều qua
tools\chay.bat         REM mở app
```

Xem giao diện trong trình duyệt: `.venv\Scripts\python.exe tools\xem_thu.py` →
`http://127.0.0.1:8777`. Chỉ còn MỘT bề mặt, đúng như app thật (xem §3, bài học D-12).

## 3. Việc kế tiếp — thiết kế lại khối và cách tương tác

Chủ dự án chỉ đường lối. Bắt đầu từ **danh sách những gì QuantConnect thật sự cho**, rồi
mới nghĩ khối.

> **Luật bắt buộc của bộ khối mới:** mỗi khối phải ứng với một món **CÓ THẬT** của
> QuantConnect — một hàm API, một loại lệnh, một chỉ báo, một bước trong khung 5 phần
> (Universe Selection · Alpha · Portfolio Construction · Risk Management · Execution).
> Cách kiểm nhanh: hỏi *"QC làm việc này bằng gì?"* — không trả lời được bằng một dòng
> code QC thì khối đó đang là phép tính của riêng ta, và nó không được có.

Ba bài học phải mang theo:

1. **Đừng để app tính hộ.** Nến, chỉ báo, số lượng, ký quỹ, phí, trượt giá, lãi lỗ, thống
   kê — của QC hết. Hai nơi cùng tính một thứ thì ra hai số.
2. **Cầu nối giả không được nói dối.** `tools/xem_thu.py` từng phục vụ hai bề mặt và tự
   định tuyến `qc_*` sang `ApiQC`, che mất lỗi "cửa sổ chính không có `qc_khoa`". Bản
   xem thử phải giống app thật từng chi tiết, nếu không thì kiểm bằng mắt là vô nghĩa.
3. **Giao diện không tự ghép chữ trên khối.** Python dựng chữ, giao diện vẽ lại — thứ
   hiện trên màn hình luôn đúng bằng thứ lõi hiểu.

## 4. Những việc còn để lại (không gấp)

* Hai phép kiểm CSS đang **ngủ** (`.menu-th-noi`, `.dong-dk`): chúng tự thức khi trình vẽ
  mới dựng lại một menu nổi hoặc một hàng dạng lưới. Xem `tests/test_giao_dien.py`.
* `game.py` còn nguyên luật chơi nhưng chưa nối vào đâu — màn, boss, sao, sổ nộp.
* File cỗ máy cũ trong `du_lieu\co_may\` app không đọc được nữa. Cố ý không tự xoá.

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
   `tai_lieu/core.md` (§18–§24 của D-10 · §25 của D-11 · §26 của D-12; phần sau tiếp từ §27).
6. Không tự đổi bộ công cụ đã chọn: Python + pywebview, React + @xyflow/react + Vite.
7. Đẩy lên nhánh `claude/affectionate-thompson-8hqazr`. Không tạo pull request khi chưa
   được bảo.
8. Giao diện không tự ghép chữ trên khối, không tự tính số thứ tự, không tự soát luật
   nào: gửi sang Python rồi vẽ lại cái nhận về.

## 6. Bản đồ

**Python — `cat_studio/`**: `core.py` (đồ thị, đánh số, soát nối dây) · `luu_tru.py` (chỗ
duy nhất biết file nằm ở đâu) · `game.py` (màn, boss, sao, sổ) · `qc_api.py` (khoá,
project, file, biên dịch, backtest, Object Store) · `qc_chay.py` (soát đầu vào một lượt) ·
`khung_cua_so.py` (vá khung Win32) · `api.py` (**một** bề mặt duy nhất cho giao diện).

**Giao diện — `webui/src/`**: `TrangTrong.tsx` (trang tạm) · `components/` (TitleBar,
Modal, ContextMenu, Icon, KhoDialog) · `qc/HopKhoa.tsx` (hộp Khoá QC) · `so.ts` (đọc số
khi gõ từng phím) · `api.ts` · `types.ts` · `theme.css` + `app.css` (336 dòng, chỉ còn
phần khung dùng chung).

**Bài kiểm — `tests/`** (3): `test_danh_so` (đánh số phân cấp, ghim số, ba bẫy của
Auto_Clicker) · `test_giao_dien` (biến CSS ma) · `test_o_so` (ô số gõ từng phím, qua
`webui/kiem/o_so.mjs`).

**Tài liệu**: `README.md` (app là gì, đang ở đâu) · `DECISIONS.md` (quyết định lớn, D-01→D-12) ·
`tai_lieu/core.md` §25–§26 (hai lần dọn gần nhất).

## 7. Câu lệnh dán cho Claude Code

```text
Đọc TIEP_TUC.md ở gốc repo, rồi DECISIONS.md mục D-11 và D-12, và tai_lieu/core.md §25–§26.
Tôi không đọc code. App vừa bị dọn sạch: không còn khối nào, không chạy được gì.
Luật: app chỉ là VỎ của QuantConnect — mỗi khối phải là một món có thật của QC.
Việc tôi muốn làm tiếp: <viết ở đây>.
Nói định làm gì + tiêu chí xong bằng tiếng Việt đời thường, rồi code + bài kiểm
+ chạy tools\chay_test.bat + commit tiếng Việt.
Khoá QuantConnect là bí mật: không bao giờ bảo tôi dán khoá vào chat.
```
