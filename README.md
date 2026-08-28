<h1 align="center">
  <img src="assets/logo.png" width="88"><br>
  Cat Studio
</h1>

<p align="center">
  Vẽ sơ đồ khối cho một chiến lược giao dịch, mỗi khối mang <b>một số thứ tự do chính
  bộ máy tính ra</b>.
</p>

---

> ## ⚠ Đang dọn dẹp — chưa chạy được gì
>
> Repo đang chuyển từ một app backtest chiến lược theo **nến trên MT5** sang một app cho
> **market maker tần suất cao**. MT5 không phải nền tảng hợp cho việc đó, nên nó bị gỡ
> hẳn chứ không "để tạm".
>
> Bốn đợt dọn đã bỏ **hơn hai phần ba mã**: nguồn dữ liệu, kết nối sàn, mô hình khớp, bộ
> chạy, sổ lệnh, nhật ký, cửa sổ Strategy Tester, cửa sổ Live, và toàn bộ từ vựng của
> khối hành động.
>
> **Cái còn lại là trình soạn thảo sơ đồ** — và nó chạy: vẽ, nối, đánh số, ghim số ⟲,
> soát cấu trúc, lưu/mở. Nhưng một khối chỉ mang được **tên** và **động từ**; nó chưa
> hỏi được điều kiện nào, chưa đặt được lệnh nào.
>
> Chỗ nào đang trống và phải cắm gì vào: **[`tai_lieu/o_cam_trong.md`](tai_lieu/o_cam_trong.md)**.
> Lấy lại bất cứ thứ gì đã xoá: `git show f1c90fb:<đường dẫn>`.

---

## Một chiến lược = hai sơ đồ

```
   ┌── Tab ENTRY ────────────────┐     ┌── Tab MANAGE ───────────────────┐
   │  con trỏ ĐI SĂN             │     │  chạy MỘT LƯỢT CHO MỖI LỆNH     │
   │  một lượt mỗi nhịp          │     │  đang sống, cũng mỗi nhịp       │
   │  chỉ nó được TẠO lệnh       │     │  chỉ nó được SỬA lệnh           │
   └─────────────────────────────┘     └─────────────────────────────────┘
```

Mỗi nhịp: **Manage** cho từng lệnh → **Entry**. Manage trước — chạy ngược lại thì lệnh
vừa sinh bị quản lý ngay trong nhịp đẻ ra nó.

**Mỗi sơ đồ tự nó đã là một vòng lặp**: nó chạy lại từ khối Bắt đầu ở mỗi nhịp. Nên
*"chờ tới khi"* không phải vẽ — không cổng nào khớp thì hết lượt, nhịp sau chạy lại.
Không cần khối "vòng lặp", không cần mũi tên quay ngược.

**Ranh giới khoá được:**

| | Entry | Manage |
|---|---|---|
| Kiểm tra ĐK | ✔ | ✔ |
| Vào lệnh | ✔ | ✘ |
| Sửa lệnh | ✘ | ✔ |

> **Entry chỉ TẠO. Manage chỉ SỬA.** App soát tĩnh được, chỉ thẳng vào khối sai —
> loại lỗi MQL5 không bao giờ bắt.

Pill `Entry | Manage` là chip nổi ở góc trên-trái canvas, có **chấm đỏ khi tab kia
đang lỗi**.

## Luật đánh số

> **SỐ = đi được bao xa · CHỮ = đi nhánh nào**

```
[1] Bắt đầu
[2] Còn chỗ cho lệnh mới?
      ├─[2A] Điều kiện A?  → [2A.1] Vào lệnh Mua
      └─[2B] Điều kiện B?  → [2B.1] Vào lệnh Bán
[3] …mọi nhánh gộp lại thì số về mức trên
```

Số do **bộ máy tính ra**, không phải người gõ: kéo một khối lên trên là nhãn đổi ngay,
nên thứ tự ưu tiên nhánh không bao giờ là thứ ngầm.

## Ghim số ⟲

Chuột phải vào khối → **Ghim số** (hoặc `Ctrl+G`).

Khối đã ghim là **điểm quay lại hợp lệ**: mọi đường nối ngược về nó vẫn giữ nguyên số
cũ, không còn bị báo là vòng lặp ngoài ý muốn. Cạnh quay lại được vẽ **nét đứt vàng**
kèm nhãn `⟲`.

Cạnh quay lại cũng chính là **nhánh mặc định**: nó luôn được thử cuối cùng và không cần
cổng điều kiện — nghĩa của nó vốn đã là *"không nhánh nào khớp thì quay về trên"*.

## Bộ khối

**Hai loại khối:** `Bắt đầu` (điểm neo, đúng một cái mỗi sơ đồ, không xoá được) và `Khối`.

**Ba hành động — đọc · tạo · sửa:**

| Hành động | Việc |
|---|---|
| **Kiểm tra điều kiện** | Đọc thị trường + tài khoản rồi quyết đi nhánh nào. Đây cũng là **cổng rẽ nhánh**. |
| **Vào lệnh** | Mở vị thế mới. Hiện chỉ còn trường **Hướng** (Mua/Bán). |
| **Sửa lệnh** | Tác động lên lệnh đã có. |

> ⚠ Hai hành động sau **chưa có nội dung**. Toán hạng, phép so, đơn vị, mốc neo, loại
> lệnh và chế độ sửa đã gỡ cùng MT5 — chúng quay lại khi chọn xong sàn. Thước mới sẽ là
> **spread** và **tồn kho**, không phải ATR và bội R; xem
> [`o_cam_trong.md §11`](tai_lieu/o_cam_trong.md).

## Luật rẽ nhánh

Một khối nhiều đường ra thì các nhánh được **thử lần lượt từ trên xuống**:

1. Mỗi nhánh phải mở đầu bằng một **cổng** = khối *Kiểm tra điều kiện*.
2. Nhiều nhất **một** nhánh được để trống làm **nhánh mặc định**, và nó phải xếp **cuối**.
3. Cạnh quay lại (trỏ vào khối đã ghim) được miễn cả hai luật trên.

Không nhánh nào khớp thì **hết lượt** — nhịp sau chạy lại từ đầu. Đó là cách "chờ" được
diễn tả, không phải lỗi.

Cổng phải là *Kiểm tra điều kiện*: nhánh trượt phải **lùi lại được**, mà một khối chỉ
*đọc* dữ liệu thì lùi bao nhiêu lần cũng vô hại — còn *Vào lệnh* / *Sửa lệnh* đã tác
động ra thị trường rồi, không rút lại được.

## Chạy từ mã nguồn

Cần **Python 3.10+** và **Node.js 18+** trên Windows.

```bash
tools\setup.bat          # dựng .venv + npm install + build giao diện
tools\tao_shortcut.bat   # tạo shortcut "Cat Studio" ra Desktop (icon con mèo)
tools\chay.bat           # mở app từ dòng lệnh
tools\chay_test.bat      # chạy test
```

Shortcut chạy bằng `pythonw.exe` nên **không kèm cửa sổ console đen**. Đổi lại nó
không có stderr để nhìn, nên `app_web.py` báo mọi lỗi khởi động (thiếu .NET, thiếu
WebView2, chưa build giao diện) bằng **hộp thoại Windows** chứ không in ra màn hình.

Sửa giao diện xong phải `tools\build_ui.bat` mới thấy đổi — `app_web.py` chỉ nạp
`webui\dist`, không nạp mã nguồn.

## Cấu trúc

```
app_web.py         ĐIỂM KHỞI ĐỘNG — thứ duy nhất còn ở gốc (pywebview + WebView2)
cat_studio/        toàn bộ lõi app
  core.py            đồ thị, đánh số, soát cấu trúc, chuẩn hoá tài liệu
  kho/               danh mục mọi thứ app tính được — ĐANG RỖNG, còn nguyên cơ chế
  luu_tru.py         MỘT chỗ duy nhất biết file nằm ở đâu
  api.py             bề mặt DUY NHẤT giao diện gọi tới  (JS → api.py → core.py)
  khung_cua_so.py    vá cửa sổ Win32 cho thanh tiêu đề tự vẽ (kéo/giãn/phóng to)
tai_lieu/
  core.md            VÌ SAO mọi thứ như vậy. Đọc file này trước.
  o_cam_trong.md     ⚠ chỗ nào đang TRỐNG và phải cắm gì vào. Đọc ngay sau core.md.
webui/             giao diện: React + TypeScript + React Flow
tests/             bộ test — không mở cửa sổ, không cần sàn nào
du_lieu/           dữ liệu của bạn (sinh ra lúc chạy, không nằm trong repo)
tools/             kịch bản: chạy · build giao diện · chạy test · ĐÓNG GÓI
dist/              sản phẩm đóng gói + bản .zip phát hành (không nằm trong repo)
```

Ba tầng, mỗi tầng biết đúng việc của mình:

- `core.py` giữ toàn bộ logic và **không import webview** — test được mà không mở cửa sổ.
- `api.py` là chỗ duy nhất giao diện gọi tới. Giao diện **không bao giờ tự biết định
  dạng file**; nó chỉ gửi/nhận JSON.
- `webui/` chỉ lo hiển thị. Ngay cả dòng mô tả hành động cũng do Python sinh
  (`core.action_display`), để hai bên không thể nói khác nhau.

Menu **File → Kho** liệt kê mọi thứ app tính được, chia theo nguồn. Danh sách do Python
**tự gom** từ `kho/`, nên thêm một module là hộp thoại có ngay — không có danh sách nào
chép tay. Hiện nó rỗng, và nói ra điều đó.

## Lưu ý

- Chỉ chạy trên **Windows** (dùng API riêng của Windows cho thanh tiêu đề tối).
- Cần **.NET Framework 4.7.2+** và **Microsoft Edge WebView2 Runtime** — app tự kiểm
  lúc mở và báo bằng tiếng Việt nếu thiếu.
- Cài `pywebview` trong **`.venv` riêng**: nếu Python global có gói `quantconnect-stubs`
  thì nó chiếm namespace `Microsoft` và pywebview chết ngay lúc khởi động.
- Dữ liệu của bạn nằm trong `du_lieu/` cạnh app, không nằm trong repo.
