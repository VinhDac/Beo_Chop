# Cat Studio

Vẽ một **cỗ máy giao dịch** bằng sơ đồ khối, rồi thả nó vào thị trường thật trong quá khứ
trên **QuantConnect**. Không gõ code, không công thức — kéo khối, nối dây, bấm ▶.

> ## ⚠ Đang làm lại từ đầu (16/10/2026)
>
> App **chưa vẽ được và chưa chạy được**. Hai quyết định liền nhau đã dọn sạch phần ruột:
>
> * **D-11 — app chỉ là VỎ của QuantConnect.** Mọi phép tính về thị trường (nến, chỉ báo,
>   số lượng, lệnh, lãi lỗ) là việc của QC. App giữ đúng ba việc: **vẽ · soát lỗi · dịch
>   sơ đồ ra thuật toán QC**, cộng luật chơi. Bộ mô phỏng tại máy đã xoá.
> * **D-12 — xoá toàn bộ bộ khối cũ.** Bộ khối ấy được nghĩ ra trước D-11 nên mỗi khối là
>   một phép tính của riêng app. Khối, từ điển, mẫu dựng sẵn, trình vẽ và màn chơi đã xoá
>   hết (≈ 9.000 dòng). Bộ khối mới và cách tương tác mới đang được thiết kế.
>
> **Luật của bộ khối mới:** mỗi khối phải ứng với một món **có thật** của QuantConnect —
> một hàm API, một loại lệnh, một chỉ báo, một bước trong khung 5 phần của họ. Khối nào
> không chỉ ra được món QC đứng sau nó thì không được có.
>
> Mở app lúc này: đặt được **khoá QuantConnect**, xem được **app lưu file ở đâu**. Hết.

---

## QuantConnect chia một thuật toán ra năm phần

Đây là khung của *họ*, không phải của ta — bộ khối mới sẽ phải sống trong đó:

| Phần | Hỏi câu gì | Ra cái gì |
|---|---|---|
| Universe Selection | Mã nào đáng để mắt tới? | rổ mã |
| Alpha | Mã này sắp lên, xuống, hay nên đứng ngoài? | tín hiệu có thời hạn |
| Portfolio Construction | Mỗi mã được bao nhiêu phần vốn? | tỷ trọng mục tiêu |
| Risk Management | Có gì phải cắt bớt ngay không? | mục tiêu đã chỉnh |
| Execution | Đưa vị thế về mục tiêu bằng lệnh gì, lúc nào? | lệnh thật |

Số lượng, lô tối thiểu, ký quỹ, phí, trượt giá: QC tính. App không đụng vào.

## Thứ sống sót qua hai lần dọn

* **Đánh số phân cấp** (`core.py`) — huy hiệu trên mỗi khối: **số = đi được bao xa, chữ =
  đi nhánh nào** (`1 · 1A · 1A.1`). Khối không có đường nối dẫn tới thì không có số: nó
  sẽ không bao giờ chạy, và nhìn là thấy.
* **Thứ tự ưu tiên nhánh theo VỊ TRÍ trên canvas**, không theo thứ tự tạo dây — thứ tự
  tạo dây là thứ vô hình, người chơi không có cách nào biết nhánh nào được thử trước.
* **Soát nối dây** — vòng hở, nhánh chụm không đều, nhánh mặc định xếp sai chỗ, hai cổng
  trùng điều kiện, dây trỏ về chính nó. Thông báo lỗi gọi khối bằng **huy hiệu** (`[4A.2]`)
  chứ không bằng số thứ tự trong danh sách.
* **Luật chơi** (`game.py`) — màn, boss «Mua rồi giữ cả rổ», ba mức sao, sổ nộp.
* **Cầu nối QuantConnect** (`qc_api.py`) — khoá, project, file, biên dịch, backtest,
  Object Store.

## Chạy từ mã nguồn (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone: .venv + thư viện + build giao diện
tools\chay_test.bat    REM phải thấy: ✔ 3/3 bài đều qua
tools\chay.bat         REM mở app
```

* Sửa giao diện (`webui/`) xong thì `tools\build_ui.bat` mới thấy thay đổi.
* Muốn xem giao diện trong trình duyệt (chụp ảnh, mở DevTools, cho máy bấm thử):
  `.venv\Scripts\python.exe tools\xem_thu.py` → `http://127.0.0.1:8777`. Nó gọi `api.py`
  THẬT, chỉ thay đường vận chuyển — và chỉ phục vụ **một** bề mặt, đúng như app thật
  (xem D-12: bản cũ phục vụ hai bề mặt và đã che mất một lỗi).

### Cần gì để chạy thật trên QuantConnect

* Gói **Researcher** trở lên (gói Free không có API).
* Khoá API đặt **ngoài repo**: biến môi trường `QC_USER_ID` / `QC_API_TOKEN`, hoặc file
  `du_lieu\qc_khoa.json`, hoặc gõ vào hộp Khoá trong app. **Khoá có toàn quyền tài
  khoản, kể cả giao dịch thật** — app chỉ dùng nó để chạy backtest, và không bao giờ in
  nó ra.

## Cấu trúc

```
app_web.py            điểm khởi động (pywebview + webui/dist)
cat_studio/
  core.py             đồ thị, đánh số, soát lỗi đồ thị, bảng tham số, cài đặt
  luu_tru.py          chỗ DUY NHẤT biết file nằm ở đâu
  game.py             luật chơi: màn, boss, sao, sổ nộp
  qc_api.py           nói chuyện với API của QC
  qc_chay.py          soát đầu vào một lượt chạy (rổ mã, ngày, vốn)
  khung_cua_so.py     vá khung cửa sổ Win32 cho thanh tiêu đề tự vẽ
  api.py              bề mặt DUY NHẤT giao diện gọi tới
webui/src/
  TrangTrong.tsx      trang tạm — nói thẳng là đang dựng lại
  components/         thanh tiêu đề, hộp thoại, menu chuột phải, icon, hộp Kho
  qc/HopKhoa.tsx      hộp Khoá QuantConnect
  so.ts               đọc số khi gõ TỪNG PHÍM
tests/                3 bài kiểm, chạy bằng `tools\chay_test.bat`
tai_lieu/core.md      nhật ký kỹ thuật: vì sao từng thứ như hiện tại
DECISIONS.md          quyết định lớn, kèm phương án đã cân nhắc
TIEP_TUC.md           đang ở đâu, làm gì tiếp
```

## Lưu ý

* **Chữ trên khối do Python dựng**, giao diện không ghép một mẩu nào — nên thứ hiện trên
  màn hình luôn đúng bằng thứ lõi thật sự hiểu. Luật này giữ nguyên cho bộ khối mới.
* **Mọi thứ app ghi ra** nằm trong `du_lieu/` (cỗ máy, nhật ký chạy, sổ game, khoá QC) —
  thư mục này nằm trong `.gitignore`.
* File cỗ máy cũ trong `du_lieu\co_may\` **app không đọc được nữa**: chúng viết bằng bộ
  khối đã xoá. Cố ý không tự xoá chúng — đó là công người chơi bỏ ra.
