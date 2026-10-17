# Tiếp tục — Cat Studio

> Cập nhật 16/10/2026 · Nhánh `claude/affectionate-thompson-8hqazr` · Chưa tạo pull request,
> chưa gộp vào `main`. Đang làm trên máy local (Windows).

## 1. Đang ở đâu

**VẼ → SINH → CHẠY đã thông. Một sơ đồ vàng + RSI đã backtest thật: +16,376%.**

Ba quyết định liền nhau:

* **D-11 (16/10)** — app chỉ là **VỎ** của QuantConnect. Bộ mô phỏng tại máy đã xoá
  (≈5.800 dòng).
* **D-12 (16/10)** — xoá **toàn bộ bộ khối cũ** (≈3.200 dòng nữa). Nó nghĩ ra TRƯỚC
  D-11 nên mỗi khối là một phép tính của riêng app.
* **D-13 (16/10)** — **chép hạ tầng trình vẽ từ `Jenifer_Studio`**, bộ tự động hoá game
  của chính chủ dự án. Không phải tham khảo một thư viện đẹp: template `trial chaos 30`
  ở đó là một sơ đồ THẬT **1.170 khối · 1.468 dây · canvas 19.367×16.055**.
* **D-14 (16/10)** — **bộ khối**: khối **HỎI** (5 loại, 68 đại lượng) và khối **LÀM**
  (8 loại việc). Mỗi mục khai ra MỘT hàm có thật của LEAN trong ô `lean`, và bài kiểm
  canh đúng chuyện đó.
* **D-15 (16/10)** — **khối BẮT ĐẦU**, sau khi đọc **444 thuật toán Python thật** của
  LEAN. Một script có HAI nửa: `initialize` nói một lần, `on_data` chạy lại mỗi nhịp.
  Sơ đồ ta vẽ là nửa dưới; **sáu ô của khối Bắt đầu là nửa trên**.
* **D-16 (16/10)** — **bộ sinh mã**. Sơ đồ thành một file Python chạy được trên LEAN,
  và nó **không tự nghĩ ra câu LEAN nào** — mọi câu lấy từ ô `lean` của ba từ điển.
  Đã chạy thật: XAUUSD 2015–2018, **15 lệnh, +16,376%**.

**Trạng thái thật:**

| Việc | Được chưa |
|---|---|
| Vẽ sơ đồ: thêm khối, nối dây, kéo, xoá, nhân bản | ✅ |
| **Đánh số phân cấp** `1 · 2 · 2A · 2A.1 · 2B · 2B.1 · 3 · 4` | ✅ |
| **Nhóm** — gập một chuỗi hành động vào một hộp | ✅ |
| **Quay về** — vòng lặp vẽ ra, có đích, thấy cả vòng khi bấm | ✅ |
| **Hạt nhân** — gói một mảng sơ đồ, bấm đúp vào trong sửa | ✅ |
| **Ô tìm** không dấu + bốn lọc hỏi theo dây | ✅ |
| Menu chuột phải · phím tắt (F2) · bảng Vấn đề · Nhật ký | ✅ |
| Lưu / mở / bản nháp / bản tự lưu / hoàn tác | ✅ |
| **Khối HỎI** — 5 loại, hộp điều kiện, soát ruột | ✅ |
| **Khối LÀM** — 8 loại, hộp ô theo loại, soát ruột | ✅ |
| **Khối BẮT ĐẦU** — mã, khoảng ngày, vốn, nhịp, mốc, sàn | ✅ |
| **Bộ sinh mã** — sơ đồ → thuật toán LEAN Python | ✅ |
| **Chạy LEAN TỪ TRONG APP** | ❌ **chưa** — hiện phải chạy tay |
| **Vòng lặp** trong mã sinh ra | ❌ **chưa** — báo rõ, không đoán |
| **Chọn mã động** (universe) — ô «Chạy trên mã nào» nhận một RỔ | ✅ |
| Lớp game | ❌ **chưa** |

Bài kiểm: **9/9 qua** · `tsc --noEmit` sạch · `npm run build` sạch.

**Mã sinh ra nằm ở** `du_lieu\ma_sinh\<TênLớp>.py` — bấm *Sinh mã* trên ribbon.

## 2. Chạy ở máy local (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone
tools\chay_test.bat    REM phải thấy: ✔ 5/5 bài đều qua
tools\chay.bat         REM mở app
```

Xem giao diện trong trình duyệt: `.venv\Scripts\python.exe tools\xem_thu.py` →
`http://127.0.0.1:8777`.

> ⚠ **Khung xem thử không vẽ thì phép đo nói dối.** `ResizeObserver` chỉ bắn trong nhịp
> vẽ; cửa sổ bị che là trình duyệt bỏ nhịp ấy, và đọc DOM sẽ thấy đủ khối mà KHÔNG một
> đường nối nào. Chụp ảnh một nhát rồi mới tin phép đo. (Chi tiết ở đầu `xem_thu.py`.)

## 3. Việc kế tiếp — CHẠY LEAN TỪ TRONG APP

Vẽ → sinh đã thông. Còn thiếu đoạn cuối: bấm một nút trong app là nó chạy backtest
rồi bày kết quả ra, thay vì phải tự gõ lệnh.

**Cách chạy tay hiện nay** (đã làm được, ghi lại để khỏi mò):

1. Bấm *Sinh mã* → *Lưu file .py* → file nằm ở `du_lieu\ma_sinh\`.
2. Trỏ `Launcher/bin/Release/config.json` của LEAN vào file ấy
   (`algorithm-type-name`, `algorithm-location`, `data-folder`).
3. `set PYTHONNET_PYDLL=…\python314.dll` rồi chạy `QuantConnect.Lean.Launcher.exe`.

⚠ Lỗi *"GIL must always be released"* lúc tắt là **vô hại** — kết quả đã ghi xong.
**Đọc file kết quả, đừng tin mã thoát.**

**Việc cần làm:** gói ba bước ấy vào một cửa `api.chay_backtest`, rồi một nút *Chạy*
cạnh nút *Sinh mã*, và một bảng bày thống kê trả về.

Dữ liệu để thử: **XAUUSD giá ngày 2006–2019 (3.948 ngày) có sẵn miễn phí** trong
`Data/cfd/oanda/` của LEAN.

> **Luật bắt buộc (vẫn nguyên):** mỗi khối phải ứng với một món **CÓ THẬT** của
> QuantConnect. Cách kiểm nhanh: hỏi *"QC làm việc này bằng gì?"* — không trả lời được
> bằng một dòng code QC thì khối đó đang là phép tính của riêng ta, và nó không được có.
> Với bộ sinh mã, luật ấy thành: **nó chỉ được viết ra thứ đã khai trong ô `lean`.**

### Lịch sử phần này (đã xong)

> **Luật bắt buộc:** mỗi khối phải ứng với một món **CÓ THẬT** của QuantConnect — một
> hàm API, một loại lệnh, một chỉ báo, một bước trong khung 5 phần (Universe Selection ·
> Alpha · Portfolio Construction · Risk Management · Execution). Cách kiểm nhanh: hỏi
> *"QC làm việc này bằng gì?"* — không trả lời được bằng một dòng code QC thì khối đó
> đang là phép tính của riêng ta, và nó không được có.

Từ vựng chỉ có bốn thứ, và ba trong số đó đã dựng xong:

| Jenifer | Cat_Studio | Xong chưa |
|---|---|---|
| **HỎI** (`xac_nhan_chu`, `xac_dinh_map`…) | **HỎI** — thị trường · vị thế · tài khoản · lịch · doanh nghiệp | ✅ `cat_studio/hoi.py` |
| **LÀM** (`left_click`, `key_press`…) | **LÀM** — tỷ trọng · lệnh thị trường · đóng · lệnh chờ · huỷ · ghi chú · vẽ bảng · báo tin | ✅ `cat_studio/lam.py` |
| **NHÓM** | **NHÓM** | ✅ |
| **QUAY VỀ** | **QUAY VỀ** | ✅ |

**⚠ Đường ranh đã vạch (D-14):** ĐẶT lệnh và HUỶ HẾT lệnh chờ của một mã thì được —
mỗi cái là MỘT câu gọi. SỬA một lệnh cụ thể (`ticket.UpdateStopPrice`) thì KHÔNG: phải
giữ ticket qua nhiều nến, tức app lại có backend để mà gỡ lỗi. Muốn dời cắt lỗ thì
huỷ hết → đặt lại.

Còn lại không phải từ vựng mà là **hình học**: N làn cạnh nhau, mỗi làn một cổng, nhánh
thoát xếp dưới cùng, mở ra bao nhiêu gộp lại bấy nhiêu.

**Mấy chỗ CÒN LẠI:**

* `core.chuan_hoa_khoi` — khối **Bắt đầu** đã dựng lại từ danh sách ô cố định (D-15),
  nhưng khối **Hành động** thì vẫn giữ nguyên xi mọi khoá. Nay đã có đủ ba từ điển
  nên làm nốt được — đó mới là chỗ chặn file rác.
* **Vòng lặp trong mã sinh ra** — hiện báo "chưa sinh được". Cần nghĩ kỹ vòng lặp
  TRONG MỘT NẾN có nghĩa gì với giao dịch trước khi dựng.
* **Ghép đại lượng** (đã xác minh là khả thi, chưa làm): sáu phép so không viết nổi
  `fast > slow * 1.00015`, mà `IndicatorExtensions` của LEAN có sẵn
  `Plus/Minus/Times/Over` (vế phải là một số hoặc một chỉ báo khác) và kết quả là một
  chỉ báo do LEAN tự tính — nên cho phép ghép KHÔNG phá luật "không đẻ backend".
  Xem `tai_lieu/core.md` §30.

## 4. Những việc còn để lại (không gấp)

* Một phép kiểm CSS còn **ngủ** (`.menu-th-noi`) — tự thức khi trình vẽ có menu nổi.
  Xem `tests/test_giao_dien.py`. (`.dong-dk` đã thức từ D-13.)
* Phím tắt chưa cho người dùng đặt lại (bảng F2 mới là bảng TRA). Jenifer có phần ấy.
* `game.py` còn nguyên luật chơi nhưng chưa nối vào đâu.
* File cỗ máy cũ trong `du_lieu\co_may\` app không đọc được nữa. Cố ý không tự xoá.

## 5. Luật phải giữ

1. **Khoá API QuantConnect là BÍ MẬT.** Không dán vào chat, không commit, không in ra.
   Đặt ngoài repo: `QC_USER_ID` / `QC_API_TOKEN`, hoặc `du_lieu\qc_khoa.json` (thư mục
   `du_lieu\` đã bị chặn trong `.gitignore`), hoặc gõ vào hộp Khoá trong app. Khoá có
   toàn quyền tài khoản, kể cả giao dịch thật, nên chỉ dùng để chạy backtest.
2. Mỗi lần một lát nhỏ: nói trước định làm gì và tiêu chí xong; mọi thay đổi có bài kiểm;
   `tools\chay_test.bat` xanh rồi mới commit. **Soát MÃ THOÁT, đừng soát qua ống dẫn** —
   `chay_test.bat | tail` trả mã thoát của `tail`, nên cổng chặn không chặn gì cả.
3. Commit message tiếng Việt, ngắn. Giải thích cho chủ dự án bằng tiếng Việt đời thường,
   không dán code.
4. Dữ liệu không được nhìn trước (point-in-time). Lõi không import giao diện hay mạng.
5. Quyết định lớn ghi vào `DECISIONS.md`; mỗi phần xong ghi một mục trong
   `tai_lieu/core.md` (§25 của D-11 · §26 của D-12 · §27 của D-13 · §28 của D-14 ·
   §29 của D-15 · §30 của D-16; phần sau tiếp từ §31).
6. Không tự đổi bộ công cụ đã chọn: Python + pywebview, React + @xyflow/react + Vite.
7. Đẩy lên nhánh `claude/affectionate-thompson-8hqazr`. Không tạo pull request khi chưa
   được bảo.
8. **Giao diện không tự ghép chữ trên khối, không tự tính số thứ tự, không tự soát luật
   nào**: gửi sơ đồ sang Python (`api.soat`) rồi vẽ lại đúng cái nhận về.

## 6. Bản đồ

**Python — `cat_studio/`**: `core.py` (đồ thị, đánh số, Nhóm, Quay về, thẻ khối, chuẩn
hoá) · `luu_tru.py` (chỗ duy nhất biết file nằm ở đâu, + bản nháp/bản tự lưu) ·
`game.py` · `qc_api.py` · `qc_chay.py` · `khung_cua_so.py` · `api.py` (**một** bề mặt).

**Giao diện — `webui/src/`**: `SoDo.tsx` (canvas, hạt nhân, ô tìm, menu, bàn phím) ·
`components/` (StepNode, HatNhan, DuongVong, Ribbon, OTimKhoi, BangDuoi, BangPhimTat,
ContextMenu, Modal, TitleBar, Icon, KhoDialog, HopDoiTen) · `qc/HopKhoa.tsx` ·
`tim.ts` · `phim_tat.ts` · `so.ts` · `api.ts` · `types.ts` · `theme.css` + `app.css`.

**Bài kiểm — `tests/`** (5): `test_danh_so` · `test_so_do` (Nhóm, Quay về, vòng phải
khép, bộ nhớ của cái nút) · `test_so_do_api` (một cửa soát, ba tầng lưu) ·
`test_giao_dien` (biến CSS ma) · `test_o_so`.

**Tài liệu**: `README.md` · `DECISIONS.md` (D-01→D-13) · `tai_lieu/core.md` §25–§27.

## 7. Câu lệnh dán cho Claude Code

```text
Đọc TIEP_TUC.md ở gốc repo, rồi DECISIONS.md mục D-11, D-12, D-13 và tai_lieu/core.md §25–§27.
Tôi không đọc code. Trình vẽ sơ đồ đã chạy; bộ khối thì chưa có nội dung gì.
Luật: app chỉ là VỎ của QuantConnect — mỗi khối phải là một món có thật của QC.
Việc tôi muốn làm tiếp: <viết ở đây>.
Nói định làm gì + tiêu chí xong bằng tiếng Việt đời thường, rồi code + bài kiểm
+ chạy tools\chay_test.bat + commit tiếng Việt.
Khoá QuantConnect là bí mật: không bao giờ bảo tôi dán khoá vào chat.
```
