# Cat_Studio — Sổ ghi cốt lõi

> App vẽ pipeline + mô phỏng hành vi chiến lược giao dịch.
> Fork từ **Auto_Clicker** (`C:\Users\Davin\Desktop\Auto_Clicker`), đổi miền từ *click game* sang *trading*.
>
> File này là **nguồn sự thật về Ý ĐỊNH**. Code là nguồn sự thật về hành vi.
> Sửa cơ chế → sửa file này cùng lúc, đừng để hai bên nói khác nhau.

> ⚠ **2026-10-14 — ĐỔI HƯỚNG, xem `DECISIONS.md` D-01, D-09 và D-10.** Động cơ chuyển hẳn
> sang LEAN / QuantConnect; Cat Studio chỉ giữ lớp game (ngôn ngữ sơ đồ + lời giải thích).
> **App chỉ phục vụ QuantConnect (D-09): MT5 đã gỡ sạch** — không cửa sổ Live, không nối
> sàn, không tải nến (§17). **Strategy Tester đã bỏ (D-10)** — không còn chạy tại máy; lối
> chạy duy nhất là ◆ Màn chơi trên QuantConnect (§18). Mục §12 (thiết kế tester) và những
> chỗ nói về `nguon_nen` là LỊCH SỬ; bộ chạy cũ (`bo_chay`, `khop_lenh`) còn sống tới khi
> cỗ máy 5 trạm thay hai sơ đồ Entry/Manage (D-10, phần 7).

Cập nhật: 2026-08-10 · Trạng thái: **P0–P4 + kho/lưu trữ/sổ lệnh xong** · test 332/332 · giao diện tester đã chạy thật
Thiết kế **Strategy Tester chốt xong** → §12. Bộ chạy chưa viết một dòng nào.

---

## 0. Một câu

> Vẽ sơ đồ khối cho một chiến lược giao dịch, mỗi khối mang **một số thứ tự do chính bộ máy tính ra**,
> bấm **◆ Màn chơi** để chạy nó trên QuantConnect và xem nó hành xử ra sao, vì sao.

---

## 1. Nguồn tham chiếu

| Nguồn | Đường dẫn | Lấy gì |
|---|---|---|
| **Auto_Clicker** | `C:\Users\Davin\Desktop\Auto_Clicker` | Toàn bộ kiến trúc, giao diện, cơ chế đánh số, rẽ nhánh, undo, template, khung cửa sổ |
| **Compress EA** | `…\MQL5\Experts\D_02_Compress` | Chiến lược mẫu để tái lập bằng Python và làm **sơ đồ mẫu** |

---

## 2. Kiến trúc kế thừa từ Auto_Clicker — GIỮ NGUYÊN

Ba tầng, mỗi tầng biết đúng việc của mình. Đây là thứ làm app không tự mâu thuẫn — **không được phá.**

```
core.py          lõi — đồ thị, đánh số, soát lỗi. Không phụ thuộc giao diện.
kho/             DANH MỤC mọi thứ app tính được, chia theo NGUỒN
  nen_tang.py      giá · thời gian · tài khoản · lệnh này   (không thuộc engine nào)
  chi_bao.py       ATR · MA · Donchian · Volume MA          (chỉ báo phổ thông)
  engine_d02.py    atr_bps · bảng vùng nén                  (ý tưởng riêng của D_02)
so_lenh.py       bảng `lệnh` + `vùng nén`, id của CHÍNH TA
luu_tru.py       MỘT chỗ duy nhất biết file nằm ở đâu
api.py           bề mặt DUY NHẤT giao diện gọi tới   (JS → api.py → core.py)
app_web.py       khởi động cửa sổ (pywebview + WebView2)
khung_cua_so.py  vá cửa sổ Win32 cho thanh tiêu đề tự vẽ (kéo / giãn / phóng to)
webui/           React + TypeScript + React Flow (@xyflow/react)
```

### Vì sao `kho/` tách khỏi `core.py`

`so_nen_nen` **chỉ có nghĩa khi engine D_02 đang nạp**. Để nó chung một danh sách phẳng
với `close` là nói dối về việc thứ gì luôn có, thứ gì đến từ một chiến lược cụ thể.

- Thêm một chiến lược = thêm **một file** vào `kho/`, không sờ `core.py`.
- Hộp thoại **Kho** (menu File) đọc thẳng `kho.danh_muc()` — không có danh sách nào
  chép tay, nên nó không thể nói khác thực tế.
- **Trùng khoá giữa hai module là lỗi CHẾT NGƯỜI** (hai engine cùng khai `atr` với hai
  nghĩa) → `kho/__init__.py` nổ ngay lúc import, không để nó âm thầm.

### Vì sao `so_lenh.py` dùng id của ta

D_02 **không có** id nối lệnh chờ với vị thế sinh ra từ nó, nên `CheckPendingActivation`
phải ĐOÁN bằng `HasOpenPosition()` — *"có vị thế nào bất kỳ không"*. Lệnh chờ bị huỷ từ
ngoài trong lúc còn vị thế cũ là nó **đọc nhầm thành đã khớp**.

- `L-0001`, `V-0003` — **đếm tăng, không uuid**: đọc log biết ngay thứ tự, và chạy lại
  cùng dữ liệu ra cùng id nên so được hai lần backtest.
- Lệnh mang `vung_id` → *"vùng này đã sinh lệnh"* (thay `COMP_CONSUMED`) chỉ là một
  **phép tra bảng**, không phải cờ ẩn. Và tính cả lệnh đã đóng: một cú nén, một lệnh.
- `sl_o_hoa_von` suy ra từ **vị trí SL so với giá vào**, không phải cờ riêng — y như
  `if(sl >= entry) continue` của bản gốc, và không thể lệch với thực tế.

### Bố cục lưu trữ

```
<cạnh app>/du_lieu/
    cai_dat.json          cài đặt app
    chien_luoc/*.json     chiến lược đã lưu
    nen/                  cache nến tải về      (Strategy Tester dùng sau)
    nhat_ky/              nhật ký lệnh từng lần chạy  (sau)
```

`luu_tru.di_cu()` chuyển `settings.json` + `templates/strategy/` của bản cũ sang, chỉ
CHÉP những gì chưa có — không đè, không xoá bản cũ.

**Luật bất di bất dịch:**

1. **JS không bao giờ biết định dạng file.** Nó gửi/nhận JSON, mọi hiểu biết về schema nằm ở `core.py`.
2. **Nội dung chữ trên hộp do Python sinh** (`core.action_display` → `api.describe`). JS chỉ chọn icon theo `type`. Hai bên không thể nói khác nhau.
3. **Số ở góc khối do Python tính**, bằng **chính phép duyệt** mà bộ chạy dùng. JS không tự đếm.
4. **Không throw qua cầu nối.** Mọi hàm `Api` bọc `@_bat_loi` → luôn trả `{ok, value, error, trace}`.
5. **Mọi thuộc tính không-callable trên `Api` phải bắt đầu bằng `_`.** pywebview duyệt `dir(js_api)`; đọc trúng property của Window là treo UI thread vĩnh viễn ("Not Responding").

### Cầu nối JS ↔ Python

**Không có HTTP, không có route.** Là `window.pywebview.api.<tên>()`.
`webview.start(..., http_server=True)` chỉ để phục vụ file tĩnh (Vite build là ES module,
`file://` cho origin `"null"` → Chromium chặn → màn hình trắng).

**Hệ quả phải nhớ:** cổng là **ephemeral, đổi mỗi lần chạy** → origin đổi → `localStorage` **vô dụng**.
Mọi trạng thái UI cần nhớ phải đi qua Python (`save_ui`).

### Đẩy sự kiện lúc chạy

Không websocket, không SSE, không polling. Python gọi ngược:
`self._window.evaluate_js('window.__su_kien("run", <json>)')`, **gom lô ~150 ms/lần**.
Đẩy từng dòng là ngốn sạch UI thread.

### Vì sao thanh tiêu đề phải tự vẽ

Windows 10 **không cho** đổi màu thanh tiêu đề (`DWMWA_CAPTION_COLOR` là của Win11, Win10 trả `E_INVALIDARG`).
→ `frameless=True` rồi tự vẽ, `khung_cua_so.py` vá lại từng thứ đã mất: viền kéo giãn, phóng to đúng vùng
làm việc (không che taskbar), menu hệ thống.

> **Bài học đắt nhất, chép nguyên:** vá `WM_NCHITTEST` **một mình là vô ích**. WebView2 là cửa sổ con
> (`Chrome_RenderWidgetHostHWND`) phủ kín cửa sổ cha; Windows chỉ hỏi cửa sổ trên cùng dưới con trỏ,
> và nó luôn trả `HTCLIENT`. Cửa sổ cha không bao giờ được hỏi.
> → **Kéo cửa sổ phải do WEB khởi động**: JS gọi `keo_cua_so(ht)` → `PostMessageW(WM_KEO_RIENG)` →
> proc (đang ở UI thread — chỗ duy nhất `ReleaseCapture()` chạy được) làm `ReleaseCapture()` +
> `SendMessageW(WM_NCLBUTTONDOWN)`. **`Post` chứ không `Send`** vì vòng lặp kéo của Windows là modal,
> `Send` sẽ khoá luôn thread Python suốt cú kéo.

---

## 3. ⭐ CƠ CHẾ ĐÁNH SỐ — thứ quan trọng nhất

### 3.1 Luật

> **SỐ = đi được bao xa · CHỮ = đi nhánh nào**

```
1
2
3
4
├── 4A                 ← cổng nhánh A (khối ĐẦU nhánh mang đúng nhãn nhánh)
│   ├── 4A.1
│   ├── 4A.2
│   │   ├── 4A.2A
│   │   └── 4A.2B
│   └── 4A.3
└── 4B
    ├── 4B.1
    └── 4B.2
5                      ← ĐIỂM GỘP: mọi nhánh đều dẫn tới đây → số về lại mức trên
6
```

**Ngữ pháp:** các nhóm ngăn bởi dấu `.`, mỗi nhóm = **SỐ** rồi tới các **CHỮ** (có thể không có).
`4A.2B` tách thành `4A` | `2B`. Chữ **không bao giờ** mở đầu một nhóm, số luôn đứng ngay sau dấu chấm
→ máy tách được, không nhập nhằng.

### 3.2 Ai quyết cái gì

| Thứ | Do đâu quyết | Ghi chú |
|---|---|---|
| **Định danh khối** | `id = "s" + uuid4().hex[:8]` | Bền. Kéo khối / đổi tên không đổi id. **Không bao giờ dùng số thứ tự làm id.** |
| **Nhãn hiện ở góc** | `flow_order(steps, edges)` tính lại mỗi lần | **Không lưu vào file.** Là hàm thuần của (đồ thị + vị trí). |
| **Thứ tự ưu tiên nhánh** | `_khoa_nhanh(step)` → `(y, x, str(id))` | **Lấy từ VỊ TRÍ TRÊN CANVAS**, không phải thứ tự nối dây |
| **Khối bắt đầu** | `flow_entry` = khối đầu tiên trong danh sách **không có đường nối đi vào** | |
| **Điểm gộp** | `diem_gop(cur, ke)` = khối gần nhất mà **MỌI** nhánh đều dẫn tới | Giao các tập BFS, trừ chính nó, lấy gần nhất |

**Vì sao ưu tiên nhánh lấy từ vị trí:** thứ tự nối dây là thứ **vô hình** — kéo khối cách mấy cũng không đổi,
người dùng không có cách nào biết nhánh nào thử trước. Vị trí thì **nhìn thấy**, và nhãn `A`/`B` đổi
**ngay lúc thả chuột** → ưu tiên không bao giờ là thứ ngầm.

**Vì sao nhãn phải do Python tính:** trước khi có rẽ nhánh, lời hứa "số ở góc khối không nói dối" được giữ
bằng cách cho bộ chạy và bộ đánh số đi **chung một phép duyệt**. Có nhánh rồi thì huy hiệu vẽ **CẢ CÂY**
(tĩnh) còn bộ chạy chỉ đi **MỘT đường** (động) — không còn là cùng một phép duyệt nữa.
Chỗ duy nhất nó còn có thể nói dối là **thứ tự ưu tiên nhánh** → nên đó chính là thứ phải dùng chung:
cả hai bên đều chỉ lấy thứ tự từ `flow_map()`.

### 3.3 ⚠ Ba cái bẫy đã đo được trong Auto_Clicker (PHẢI SỬA khi fork)

**Bẫy 1 — cờ `loop` là DƯƠNG TÍNH GIẢ.**
`dat()` bật `vong = True` khi gán nhãn cho khối **đã có nhãn** — mà một đồ thị **hoàn toàn không có vòng**
vẫn kích hoạt được. Ví dụ tái lập: `1 → {A, B, C}`, `A→M`, `B→M`, `C→Z`.
`diem_gop` cần một khối chung cho **cả ba** nhánh, không tìm ra → các nhánh đi độc lập → `B` đụng `M`
(đã được `A` đánh nhãn) → `loop: True` dù **không hề có vòng**.
→ Hậu quả: cảnh báo "VÒNG LẶP" sai, thanh trạng thái báo động, bộ chạy nhắc mỗi 200 bước.
→ **Cách sửa:** thay cờ toàn cục bằng **ngăn xếp đường đi hiện tại**. Chỉ là vòng thật khi khối gặp lại
nằm **trên chính đường đang đi** (ancestor). Đụng nhau ở điểm gộp là *merge*, không phải *cycle*.

**Bẫy 2 — vòng lặp nuốt mất khối bắt đầu là LỖI CHẾT.**
`1→2→3→1` khiến **mọi** khối đều có đường vào → `flow_entry` trả `None` → `order` rỗng →
**mọi huy hiệu hiện `–`**, kèm lỗi "Không tìm được bước bắt đầu".
→ **Cách sửa:** **khối BẮT ĐẦU cố định** (§4.2). Nó không bao giờ nhận được đường vào,
nên mọi vòng lặp ở chỗ khác luôn an toàn.
*(Chính đây là lý do trực giác "tạo sẵn 1 khối bắt đầu" là đúng — nó không chỉ để dễ đánh số.)*

**Bẫy 3 — bảng "Vấn đề" đánh số theo INDEX danh sách, không theo huy hiệu.**
`validate_process` ghi `f"Bước {si + 1}"` từ `enumerate(steps)`.
→ Panel có thể nói *"Bước 7"* về một khối mà huy hiệu ghi `4A.2`.
→ **Cách sửa:** mọi thông báo lỗi phải dùng nhãn từ `flow_order`, không dùng index.

**Bẫy 4 — `diem_gop` nhận nhầm ĐẦU NHÁNH làm điểm gộp khi đồ thị có vòng.**
*(Chỉ lộ ra sau khi vòng lặp thành công dân hạng nhất — Auto_Clicker chưa từng gặp.)*
Đi hết một vòng là "tới được" lại chính các nhánh vừa xuất phát, nên phép giao các tập
tới-được trả về một đầu nhánh. Hậu quả đo được ở sơ đồ mẫu: nhánh MUA mang nhãn `4`
còn nhánh BÁN mang `3B` — **hai nhánh song song mà lệch hẳn một cấp.**
→ **Cách sửa:** truyền `da_nhan` (tập khối đã có nhãn) vào `diem_gop`. Nó làm hai việc:
bỏ hẳn nhánh nào có ĐẦU đã mang nhãn (đó là cạnh quay lại, không đi tới đâu cả), và
dừng phép loang ở mọi khối đã có nhãn. Điểm gộp cũng phải tính **một lần** trong
`re_nhanh` rồi dùng lại — tính lại sau khi các nhánh đã có nhãn là ra kết quả khác.

**Bẫy 5 — `_bat_loi` nuốt mất danh sách tham số.**
pywebview dựng hàm JS bằng `inspect.getfullargspec(attr).args[1:]`, mà `getfullargspec`
**không** lần theo `__wrapped__` của `functools.wraps`. Một decorator `(*a, **kw)` trần
vì thế khai báo ra hàm JS **không tham số nào** → mọi đối số JS gửi đi bị vứt **im
lặng**, lỗi hiện ra ở tận đâu đâu.
→ **Cách sửa:** gán `bao.__signature__ = inspect.signature(fn)`.

**Bẫy 6 — `window.pywebview.api` là object RỖNG nhưng TRUTHY ngay từ đầu.**
pywebview tạo sẵn `api: {}` rồi mới đổ hàm vào sau bằng `_createApi(funcList)`. Chờ
bằng `if (window.pywebview?.api)` là qua ngay lập tức, và lời gọi đầu tiên chết với
*"api.py không có hàm bootstrap"* — trông y như lỗi Python trong khi Python hoàn toàn ổn.
→ **Cách sửa:** chờ một **hàm có thật**: `typeof window.pywebview?.api?.bootstrap === 'function'`.

### 3.4 Vòng lặp: đã hợp lệ sẵn

- Nối ngược lên trên **là hợp lệ**, có chủ ý (App.tsx cố ý **không** loại khối tạo thành vòng khỏi menu "Nối tới").
- Chốt chặn: `MAX_PROCESS_STEPS = 10000` bước cho một lần chạy.
- **Ngoại lệ vẫn là lỗi:** đường nối trỏ về **chính nó** (self-loop).

---

## 4. 🆕 Cơ chế MỚI của Cat_Studio

### 4.1 Ghim số ⟲ — hợp thức hoá vòng lặp

**Yêu cầu:** *"cho tôi khả năng fixed đánh số của 1 khối (chuột phải hiện lên menu) thì được phép loop lại
mà số cũ vẫn hợp lệ."*

**Thiết kế:**

- Mỗi khối có cờ `ghim: bool` (mặc định `false`), **lưu vào file**.
- Bật/tắt bằng **chuột phải → `📌 Ghim số` / `Bỏ ghim số`**.
- Khối đã ghim là một **điểm quay lại hợp lệ**.

**Luật đánh số khi gặp khối đã có nhãn:**

| Trường hợp | Xử lý | Cảnh báo |
|---|---|---|
| Khối **đã ghim** | Dừng đi tiếp trên nhánh đó. **Giữ nguyên nhãn cũ.** Ghi cạnh đó là **cạnh quay lại**. | ❌ không |
| Chưa ghim, nằm **trên đường đang đi** (ancestor) | Vòng lặp ngoài ý muốn | ⚠ *"Vòng lặp chưa ghim — hãy ghim khối `X` để xác nhận đây là vòng cố ý"* |
| Chưa ghim, **không** phải ancestor | Điểm gộp lệch nhánh (Bẫy 1) | ⚠ *"các nhánh của `Y` chụm lại không đều"* — **không** gọi là vòng lặp |

**Hiển thị:**
- Huy hiệu khối ghim đổi sang màu `--ghim` + icon `⟲`, hộp có viền vàng, thẻ chân ghi
  *"⟲ đã ghim số"*.
- **Cạnh quay lại vẽ nét đứt vàng kèm nhãn `⟲`** → nhìn sơ đồ là thấy ngay chỗ nào lặp về đâu.

**Hệ quả kéo theo — cạnh quay lại CHÍNH LÀ nhánh mặc định:**

1. `_khoa_nhanh` xếp mọi nhánh trỏ vào khối đã ghim **xuống cuối**, bất kể vị trí canvas.
   Khối quay về gần như luôn nằm phía TRÊN (đầu vòng lặp), nên xếp theo vị trí sẽ đẩy
   nó lên đầu và **mọi nhánh dưới nó không bao giờ được thử**.
2. Cạnh quay lại **không cần cổng** và được miễn luật "nhánh mặc định phải xếp cuối" —
   nghĩa của nó vốn đã là *"không nhánh nào khớp thì quay về trên"*. Bắt nó viết điều
   kiện phủ định của tất cả các nhánh trên là thừa và dễ sai.
3. **Không còn cảnh báo "nhánh nào cũng có điều kiện".** Đã bỏ hẳn: cả sơ đồ là một
   vòng lặp chạy lại mỗi nến (§6.1), nên không khớp nhánh nào = **hết lượt**, nến sau
   chạy lại từ đầu. Đó là cách "chờ" được diễn tả, và là trường hợp thường gặp nhất.

> **Ghi chú:** sơ đồ mẫu Compress **không dùng ghim số một lần nào** — đúng như nó
> phải vậy sau khi biết cả sơ đồ đã là vòng lặp. Ghim số để dành cho những chiến lược
> thật sự cần quay ngược *trong cùng một lượt*.

### 4.2 Khối BẮT ĐẦU (`kind: "start"`)

**Yêu cầu:** *"mặc định tạo cho tôi 1 khối bắt đầu, mục đích chỉ để đánh số cho dễ."*

- **Đúng một khối** mỗi sơ đồ, **tạo sẵn** khi mở canvas trắng.
- **Không hành động gì cả** — thuần điểm neo đánh số. Nhãn luôn là `1`.
- **Cấm mọi đường nối đi vào.** Giao diện từ chối kéo dây tới, validator báo lỗi nếu file bị sửa tay.
- **Không xoá được** (menu chuột phải mờ đi, có ghi lý do).
- `flow_entry` trả thẳng khối `start` → §3.3 Bẫy 2 biến mất.

Ví dụ đúng ý người dùng — 5 nhánh điều kiện entry từ khối bắt đầu:

```
                    ┌── 1A  Kiểm tra ĐK ──→ 1A.1 Mua  ──→ 1A.2 Kiểm tra ĐK ─┬─ 1A.2A  SL chặt
                    │                                                        └─ 1A.2B  SL rộng
                    ├── 1B  Kiểm tra ĐK ──→ 1B.1 Bán  ──→ …
[1] BẮT ĐẦU ────────┼── 1C  Kiểm tra ĐK ──→ … ──┐
                    ├── 1D  Kiểm tra ĐK ──→ … ──┴──→ quay về khối [3] đã ghim ⟲
                    └── 1E  (mặc định, không cổng — luôn xếp DƯỚI CÙNG)
```

### 4.3 Bấm ▶ Chạy → cửa sổ **Strategy Tester**

- Không chạy thẳng trên canvas như Auto_Clicker.
- Mở **cửa sổ pywebview thứ hai**.
- Bộ khung đã dựng: cửa sổ + `api.mo_tester(doc)` (soát lỗi trước, còn `error` thì không mở)
  + `api.tester_doc()` để cửa sổ đó hỏi ngược lại sơ đồ.

→ **Toàn bộ thiết kế nằm ở §12.** Bộ khung đó hiện còn **ba lỗi chắc chắn** — xem §12.12.

---

## 5. Luật rẽ nhánh (kế thừa nguyên vẹn)

Một khối có **nhiều đường ra** thì phải quyết định được đi đường nào:

1. Các nhánh được **thử lần lượt từ TRÊN xuống DƯỚI** (theo vị trí canvas).
2. Mỗi nhánh phải mở đầu bằng một **CỔNG** = khối mang hành động `check_cond`.
3. Nhiều nhất **MỘT** nhánh được để trống làm **nhánh mặc định** — và nó **bắt buộc xếp cuối cùng**
   (nhánh mặc định luôn khớp, xếp trên thì các nhánh dưới không bao giờ chạy tới).
4. Hai cổng cùng điều kiện y hệt → cảnh báo (cái dưới không bao giờ tới lượt).

**Vì sao cổng phải là `check_cond`:** ở điểm rẽ các nhánh thử lần lượt, nên nhánh trượt phải **lùi lại được**.
Một khối `check_cond` chỉ **đọc** dữ liệu thị trường nên lùi bao nhiêu lần cũng vô hại.
`Vào lệnh` hay `Sửa lệnh` thì không: chúng đã tác động ra thị trường, không rút lại được.

**Ngữ nghĩa ngược nhau — nhớ kỹ:**

| | Khớp | Không khớp |
|---|---|---|
| `check_cond` làm **cổng** | đi tiếp nhánh này | **chết nhánh** này, thử nhánh dưới |

Không nhánh nào khớp thì **hết lượt** — nến sau chạy lại từ khối Bắt đầu. Đó là cách
"chờ" được diễn tả, và là trường hợp thường gặp nhất, KHÔNG phải lỗi.

---

## 6. Bộ khối & hành động của Cat_Studio

### 6.0 ⭐⭐ MỘT CHIẾN LƯỢC = HAI SƠ ĐỒ

```
   ┌── Tab ENTRY ────────────────────┐     ┌── Tab MANAGE ───────────────────┐
   │  con trỏ ĐI SĂN                 │     │  chạy MỘT LƯỢT CHO MỖI LỆNH     │
   │  một lượt mỗi nến               │     │  đang sống, cũng mỗi nến        │
   │  chỉ nó được TẠO lệnh           │     │  chỉ nó được SỬA lệnh           │
   └─────────────────────────────────┘     └─────────────────────────────────┘
```

**Thứ tự trong một nến:**

```
0.  runtime cập nhật vùng nén · xu hướng · chỉ báo      ← không phải khối
1.  với MỖI lệnh đang sống → chạy MANAGE từ khối 1
2.  chạy ENTRY từ khối 1                                ← có thể sinh một lệnh mới
```

**Manage TRƯỚC Entry** — đúng `OnTick`: `CheckPendingActivation` → `ManageBreakEven` →
rồi mới tới phần quyết định. Chạy ngược lại thì lệnh vừa sinh bị quản lý ngay trong
chính nến đẻ ra nó.

**Manage KHÔNG giữ con trỏ giữa các nến.** Nó tính lại từ trạng thái quan sát được, y
như D_02 làm mỗi tick. Nhờ vậy mấy câu guard kiểu `if(sl >= entry) continue` **hiện ra
thành cổng** trên sơ đồ thay vì chôn trong C++.

**Ranh giới khoá được — đây là món quà của việc tách tab:**

| | Entry | Manage |
|---|---|---|
| Kiểm tra ĐK | ✔ | ✔ |
| **Vào lệnh** | ✔ | ✘ |
| **Sửa lệnh** | ✘ | ✔ |
| Toán hạng nhóm **"Lệnh này"** | ✘ **báo lỗi** | ✔ |

> **Entry chỉ TẠO. Manage chỉ SỬA.** Một câu, và `validate_actions(…, tab)` soát tĩnh
> được — chỉ thẳng vào khối sai. Đây là loại lỗi MQL5 không bao giờ bắt.

Ribbon **ẩn hẳn** nút không thuộc tab (không làm mờ): làm mờ thì người dùng vẫn phải
đoán vì sao.

Pill `Entry | Manage` là một **chip nổi ở góc trên-trái CANVAS**, không chiếm dải
ngang riêng. Nó trả lời câu "đang vẽ sơ đồ NÀO", nên nằm ngay trên chính cái đang vẽ
là đúng chỗ — và lấy lại được ~34px chiều cao. Có **chấm đỏ khi tab kia đang lỗi**, để
lỗi không trốn được sau lưng.

### 6.1 ⭐ MỖI SƠ ĐỒ LÀ MỘT VÒNG LẶP

> Sơ đồ chạy lại **từ khối Bắt đầu ở MỖI NẾN MỚI** — đúng như `OnTick` của MQL5 chạy
> lại từ đầu mỗi tick. D_02 không có gì chạy nền cả.

Hệ quả, và nó gỡ được rất nhiều thứ:

- **"Chờ tới khi" KHÔNG phải vẽ.** Không cổng nào khớp → hết lượt → nến sau tự chạy
  lại. Bản vẽ tay đầu tiên của sơ đồ mẫu có **5 vòng tự-lặp + 3 mũi tên "quay lại 1"**;
  cả 8 cạnh đó biến mất.
- **Không cần loại khối "Vòng theo dõi".** Nó chỉ là cái vòng lặp lớn vẽ lại lần nữa
  ở bên trong.
- **Trạng thái không cần khối.** `IDLE / COUNTING / CONFIRMED / PENDING / CONSUMED` của
  `FilterEngine` tồn tại vì MQL5 **không có đồ thị** — mỗi tick nó chạy lại từ đầu nên
  phải tự nhớ đang ở đâu. Ta có đồ thị, và trạng thái vùng nén là **dữ liệu đọc được**
  qua toán hạng (`số_nến_nén`, `đỉnh_vùng`, …), không phải khối.

### 6.2 HAI LOẠI KHỐI — hết

| kind | Nghĩa |
|---|---|
| `start` — **Bắt đầu** | Điểm neo: mỗi nến chạy lại từ đây. Đúng một cái, không xoá được, không nhận đường vào (§4.2). |
| `action` — **Khối** | Đúng một hành động. Mang `check_cond` thì nó là **cổng rẽ nhánh**. |

**Đã bỏ `Vòng theo dõi` và `Nhóm 1 lần`:**

- *Vòng theo dõi* — thừa, xem §6.1.
- *Nhóm* — cấu trúc của một chiến lược đến từ **tách trách nhiệm**, không từ lồng hộp.
  Gộp nhóm chỉ đẻ thêm câu hỏi "nhóm có phải một đơn vị chạy không".
- Kéo theo: **bỏ template cụm khối rời**. Một template phải là thứ **chạy được** —
  cụm khối rời mở ra là một mớ khối lạc không có đường vào, dán xong vẫn phải nối lại
  từ đầu. `TEMPLATE_KINDS` chỉ còn `strategy`.

### 6.3 BA HÀNH ĐỘNG — đọc · tạo · sửa

> **Chốt sau khi bàn lại.** Ban đầu định 8 hành động (3 hiện, 5 ẩn). Khi làm rõ rằng
> SL/TP là thao tác **sửa lệnh đã có** chứ không phải hành động riêng, cả 5 cái định
> ẩn đều tan vào ba việc cơ bản — không cái nào bị mất đi, chỉ là không cần khối riêng.

| key | Nhãn | Việc |
|---|---|---|
| `check_cond` | **Kiểm tra điều kiện** | ĐỌC thị trường + tài khoản rồi quyết đi nhánh nào. **Đây là CỔNG rẽ nhánh.** |
| `vao_lenh` | **Vào lệnh** | TẠO vị thế mới: Mua/Bán · Market/Stop/Limit · lot · **SL & TP ban đầu** |
| `sua_lenh` | **Sửa lệnh** | SỬA lệnh ĐÃ CÓ. Chế độ: `dời SL` · `dời TP` · `hoà vốn` · `trailing` · `đóng một phần` · `đóng hẳn` · `huỷ lệnh chờ` |

**Năm khái niệm cũ đi đâu:**

| Định làm khối riêng | Thật ra là |
|---|---|
| `cầu dao` (chặn rủi ro) | toán hạng `số_lệnh_mở`, `drawdown_%`, `giờ` trong **Kiểm tra điều kiện** |
| `cổng` | chính là **Kiểm tra điều kiện** đứng đầu một nhánh |
| `kích hoạt` (chờ khớp) | không cần gì cả — cả sơ đồ chạy lại mỗi nến (§6.1), nên "chờ" là hết lượt |
| `vào` | **Vào lệnh** |
| `thoát` | chế độ `đóng hẳn` / `huỷ lệnh chờ` của **Sửa lệnh** |

*(Từng có `dat_co` — Đặt cờ — để dành làm bộ nhớ. Bỏ: D_02 không cần, và giữ một cơ
chế không ai dùng chỉ tổ rác. Cần thì thêm lại lúc có ca dùng thật.)*

**Toán hạng của `check_cond`** — 32 cái, 6 nhóm, đủ tái lập Compress EA 100%:

| Nhóm | Toán hạng |
|---|---|
| Giá | `Close[n]`, `Open[n]`, `High[n]`, `Low[n]`, `Bid`, `Ask`, `Spread` |
| Chỉ báo | `ATR(tf, period)`, `MA(tf, period, method)`, `Donchian(tf, period).upper/lower`, `Volume_MA(tf, period)` |
| Chuẩn hoá | `ATR_bps = ATR/Close × 10000`, `X theo bội ATR`, `X theo R` |
| Vùng nén | `số_nến_nén`, `đỉnh_vùng`, `đáy_vùng`, `bề_rộng_vùng÷ATR`, `ATR_TB_vùng`, **`vùng_này_đã_sinh_lệnh`** |
| Tài khoản | `số_vị_thế`, `số_lệnh_chờ`, `số_lệnh_hôm_nay`, `drawdown_%` |
| **Lệnh này** *(chỉ Manage)* | `đã_khớp`, `là_lệnh_Mua`, `SL_đã_ở_hoà_vốn`, `lãi (×R)`, `số_nến_đã_sống`, `giá_vào` |
| Thời gian | `giờ`, `thứ` |

**Phép so dùng KÝ HIỆU, không dùng chữ:**
`<` `≤` `>` `≥` `=` `≠` · `cắt lên ↗` · `cắt xuống ↘` · `trong khoảng`.
Một cổng của Compress mang 4–5 điều kiện; viết *"lớn hơn hoặc bằng"* thì mỗi dòng dài
gấp đôi và mắt phải **đọc chữ** thay vì **liếc thấy quan hệ**.

**`vùng_này_đã_sinh_lệnh` thay cho `COMP_CONSUMED`** — và nó KHÔNG phải cờ ẩn: lệnh
mang `vùng_id`, nên câu hỏi chỉ là một phép tra bảng *"có lệnh nào trỏ về vùng hiện
hành không"*.

Toán hạng vốn đã **đúng/sai** (`đang_có_vị_thế`, `cờ`…) không có vế phải — hộp thoại
đổi sang một ô tick **KHÔNG**. *"Đang có vị thế bằng 1"* là câu không ai đọc được.

**Mọi khoảng cách giá** (SL, TP, đệm vào lệnh, mốc hoà vốn) dùng chung một kiểu
`{tinh, value}`. **Không có đơn vị pip hay đô** — đúng hợp đồng chuẩn hoá của
Compress EA (§7.1):

| `tinh` | Nghĩa |
|---|---|
| `atr` | × **ATR hiện tại** |
| `atr_zone` | × **ATR trung bình của zone** |
| `R` | × R (rủi ro) |
| `bien_zone` | mép zone đối diện |
| `bps` | bps của giá (1 bps = 1/10 000) |
| `gia` | giá tuyệt đối |

⚠ **`pt` ("% của giá") đã bỏ.** Nó là `bps` chia 100 — hai cái tên cho đúng một phép
chuẩn hoá, nên người dùng phải đoán xem chúng khác nhau chỗ nào (không khác). Không có
phép chuyển tự động: đổi sang `bps` phải **nhân giá trị với 100**, mà giá trị có thể là
một *tên tham số* — lúc đó không nhân được. Một phép đổi đúng-một-nửa là loại hỏng tệ
nhất (file vẫn chạy, chỉ sai 100 lần), nên gặp `pt` thì soát tĩnh nói to.

⚠ **`bps` từng được bày ra cho SL/TP/đệm mà `bo_chay._khoang` CHƯA CÀI** — chọn vào là
ném `LoiChay` giữa lúc backtest. Nay đã cài (`v / 10⁴ × neo`), và `tests/test_zone.py`
canh đúng chỗ đó.

⚠ **`bien_zone` KHÔNG dùng con số bạn gõ.** `_khoang` tính `v` rồi vứt — nó trả thẳng
khoảng cách tới mép zone đối diện, nên `SL = 1 [mép zone đối diện]` và `SL = 99 […]` ra y
hệt. Hộp thoại **khoá ô số** khi chọn đơn vị đó, thay vì để một con số vô nghĩa nằm đó.

#### CHỈ BÀY RA THỨ DÙNG ĐƯỢC

Luật chung, đã ghi sẵn trong `core.DON_VI_CHO`: *"bày ra một lựa chọn vô nghĩa rồi soát
tĩnh mắng là tệ hơn không bày — nên lọc ngay tại nguồn."* Bốn nhát cắt:

| Cắt gì | Vì sao | Bảng |
|---|---|---|
| Theo **chỗ dùng** | `R` ở SL là vòng tròn (đo rủi ro bằng chính rủi ro); `bien_zone` ở đệm không có mốc để đo tới | `DON_VI_CHO` |
| Theo **loại đại lượng** | chỉ **bề rộng** giá mới chuẩn hoá được; `close / close × 10⁴` luôn ra 10000 | `TOAN_HANG_LOAI` |
| **Không đo bằng chính nó** | `zone_atr_tb` với `× ATR zone` ⇒ luôn = 1 | `DON_VI_CHINH_NO` |
| Theo **zone** | trước cổng zone thì `× ATR zone` không có mẫu số ⇒ NaN ⇒ cổng luôn trượt | `khoi_sau_cong_zone` |

Nhát cuối cũng lọc **danh sách toán hạng**: khối chưa đi qua cổng zone thì không thấy
`Zone — số nến / đỉnh / đáy / bề rộng / ATR trung bình / đã sinh lệnh` — thay vì thấy rồi
bị `_soat_cong_zone` báo lỗi đỏ. Cùng một luật mà dropdown toán hạng vốn đã áp cho nhóm
*"Lệnh này"* ở Entry; đây là áp nốt cho zone.

`core.khoi_sau_cong_zone()` là **một** phép duyệt, dùng chung cho cả soát tĩnh lẫn giao
diện (gửi kèm `validate.luong[tab].sau_cong_zone`). TypeScript **không** tự đi lại đồ
thị — hai đoạn mã duyệt cùng một sơ đồ là hai luật, và chúng sẽ lệch nhau.

> ⚠ **`atr` và `atr_zone` là HAI THỨ KHÁC NHAU, tách ra là có chủ ý.**
> Đệm vào lệnh đo bằng ATR *hiện tại* — tấm khiên mỏng ngoài mép zone, đủ lọc một nhịp
> phá giả. Rủi ro đo bằng ATR *trung bình cả cú nén* — lấy mức nhiễu thật suốt đợt nén,
> nên mỗi lệnh rủi ro một R tương đương bất kể zone rộng hẹp. Gộp làm một là mất đúng
> cái làm cho 1R nhất quán giữa các tín hiệu.

**Toán hạng giá không còn `shift`.** Nó là ô số **thứ ba** trên hàng điều kiện — cùng
chỗ, cùng hình dạng với ô *chu kỳ* của ATR/MA, nhưng nghĩa khác hẳn; một ô trắng không
nhãn mang hai nghĩa tuỳ toán hạng thì không ai đọc ra. Bỏ được vì nó chưa từng khác 1
(mẫu, cả 10 file đã lưu), và `doc_cot` hiểu *thiếu shift* **đúng bằng** `shift = 1`
(`i -= max(0, shift - 1)`) — `tests/test_bo_chay.py` canh chuyện đó bằng backtest, không
bằng đọc lại công thức. Giờ ô thứ ba chỉ còn **một** nghĩa (chu kỳ) và nghĩa đó được viết
ra thành chữ. Với D_02 thì đây là bám sát **hơn**: EA luôn dùng `iClose(tf, 1)` và không
có tuỳ chọn nào khác.

**Neo lệnh chờ:** lệnh Stop **luôn** neo vào mép vùng nén thuận chiều (đỉnh cho Mua,
đáy cho Bán) — đó là chỗ duy nhất Compress EA đặt lệnh. Nên **không có tham số "neo
vào đâu"**; `dem` chỉ là khoảng đẩy ra ngoài mép đó.

### 6.4 ⭐ BẢNG THAM SỐ — **bản ghi**, không phải bước setup

> **LÕI: ở đâu chờ một con số, một CHUỖI nghĩa là tên tham số.**
> Áp đều cho chu kỳ chỉ báo, khối lượng, ngưỡng so sánh, khoảng cách SL/TP.
>
> **GIAO DIỆN: gõ = số · chọn = tham số. Tên không bao giờ gõ được.**
>
> **ĐƠN VỊ THUỘC VỀ CÁI Ô. Ai điền vào ô đó cũng phải mang đúng đơn vị ấy.**

#### Vì sao giao diện hẹp hơn lõi

Lõi nhận cả hai. Giao diện thì cố ý **chỉ cho gõ chữ số**, và đây là lý do.

Trước đây năm ô số trong app chạy **hai luật trái nhau**: chỉ ô "vế phải điều kiện" thật
sự nhận được một cái tên (nó có `<datalist>` và placeholder *"số hoặc tên tham số"*).
Bốn ô còn lại — chu kỳ, chỉ số nến, SL/TP/đệm, lot — chạy `parseInt`/`parseFloat`, nên
**hiện ra một cái tên mà gõ vào là nuốt mất**: `chu_ky_atr` → `0`. Tức app dạy *"chỗ này
gõ tên được"* ở một ô rồi phá lời dạy đó ở bốn ô kia. Nhìn ô chu kỳ đang hiện
`chu_ky_atr`, người dùng tưởng đó là chỗ **đặt tên**. Không trách được.

Nên `ActionDialog.OSo` là **một** ô dùng cho **cả năm chỗ**, và nó bỏ hẳn khả năng gõ
chữ — không phải dán nhãn giải thích, mà làm cho việc gõ tên **bất khả thi**. Khi ô đang
giữ một cái tên, nó vẽ thành **chip** (không sửa được, có `✕` để về số, đỏ + gạch ngang
nếu cái tên đó không còn trong bảng).

Tên vào ô bằng **hai** đường, và cả hai đều là CHỌN, không phải gõ:

1. nút *"Đặt tên cho số này"* ở bảng Vấn đề — đường chính, xuất hiện khi một số lặp;
2. nút `▾` ngay trong ô số — mời những tham số **đã có**.

> ⚠ Bản đầu **không có** nút `▾`, và đó là một cửa một chiều: bấm `✕` trên một chip là
> tham số biến mất khỏi ô, mà cảnh báo đặt tên chỉ đếm **số gõ tay** — còn đúng một số
> thì không đủ hai, không có cảnh báo, không có nút, **không đường nào lấy lại**.

Hệ quả: cả app còn **đúng một** ô để gõ chữ đặt tên — cột **Tên** của bảng Tham số.

#### Đơn vị thuộc về cái ô

Mỗi ô số có một đơn vị (`core.don_vi_cua_o`) — hoặc **chọn được** (khoảng cách: bps ·
× ATR · × ATR zone…), hoặc **cố định** (chu kỳ luôn `nến`, lot luôn `lot`, `zone_dem`
luôn `nến`, `so_vi_the` luôn `lệnh`). Mỗi tham số khai một đơn vị bằng **khoá** trong
cùng bảng đó. Từ đó:

- nút `▾` **chỉ mời tham số đúng đơn vị của ô** — `chu_ky_atr` (nến) không bao giờ hiện
  ra ở ô Stop Loss;
- chọn tham số xong thì **ô đơn vị khoá** (vẫn hiện, có 🔒): một cái tên chỉ mang một
  nghĩa. Cần `7 bps` và `7 × ATR` thì đặt **hai** tham số;
- soát tĩnh so đơn vị khai với đơn vị ở chỗ dùng: dùng hai đơn vị → **lỗi**; khai một
  đằng dùng một nẻo → **cảnh báo**.

⚠ `loai = "dem"` **không đủ** để suy ra đơn vị: `zone_dem` đếm **nến** còn `so_vi_the`
đếm **lệnh**. Gộp chung thì nút `▾` mời `so_vi_the_toi_da = 3 lệnh` vào ô *"zone cần bao
nhiêu nến"*. Nên toán hạng tự khai `don_vi` (`kho/*.py`) — bài kiểm bắt đúng chỗ này ngay
lần chạy đầu.

⚠ Cột `don_vi` của bảng tham số **từng là chữ tự do**, và nó âm thầm mục: sơ đồ mẫu mang
`"× ATR vùng"` — một chuỗi không tồn tại ở đâu, rác từ lần đổi tên vùng→zone, không ai
bắt được vì chưa có gì đọc nó. File cũ đi qua `DON_VI_THAM_SO_CU`; chữ lạ thì **để trống
rồi suy từ chỗ dùng**, chứ không đoán.

#### Cơ chế so sánh — MỘT cờ cho cả khối

Một ô tích cạnh ô **Tên**: `☑ So hai đại lượng`. Nó quyết hình dạng **mọi dòng** trong
khối đó:

| Cờ | Mỗi dòng | Lưới |
|---|---|---|
| tắt | `[đại lượng ⚙] [phép] [số ▾] [đơn vị]` — kèm cả dòng đúng/sai | 6 cột |
| bật | `[đại lượng ⚙] [phép] [đại lượng ⚙]` | 5 cột — **bỏ hẳn** cột đơn vị |

Cột đơn vị bị **bỏ**, không phải làm mờ: hai vế cùng chia một mẫu số nên nó triệt tiêu,
giữ một cột rỗng là chiếm 118px mà chẳng nói gì, trong khi hai ô chọn toán hạng đang
chật. Cả khối cùng một cơ chế nên mọi dòng vẫn thẳng cột.

⚠ Ô **⚙ luôn chiếm chỗ**, kể cả khi toán hạng chưa chọn hoặc không có tham số nào — mà
11/17 toán hạng đúng là không có. Chỉ *vẽ* bánh răng khi thật sự có tham số; còn lại để
trống. Bản đầu ẩn hẳn ô đó, nên ngay trong một khối, dòng `ATR` có ⚙ mà dòng `Zone — số
nến` không → hai ô chọn rộng khác nhau → cột lệch.

⚠ Trước đây lựa chọn này là một **chip trên từng dòng** (`số` / `đ.lượng`). Chip ấy chỉ
tồn tại vì **một hàng phải gánh hai hình dạng** — hậu quả là hai dòng cùng khối trông
khác nhau, cột lệch, và mắt phải đọc lại hình dạng ở mỗi dòng. Nâng lựa chọn lên mức
KHỐI thì mọi dòng trong đó giống hệt nhau, và cái chip tự thừa.

Cùng lý lẽ app đã viết cho phép HOẶC: *"tách ra thành hai nhánh riêng trên sơ đồ — nhìn
sơ đồ là thấy được, còn chữ hoặc giấu trong hộp thoại thì không."* Muốn một cổng vừa so
số vừa so đại lượng thì **nối hai cổng** — nối tiếp chính là VÀ.

**Là CƠ CHẾ, không phải LOẠI KHỐI.** Hai kiểu dùng chung bộ soát, chung phép chuẩn hoá,
chung hàm dựng chữ trên thẻ — chỉ khác đúng cái vế phải. Tách thành loại khối riêng là
chẻ ba đoạn mã đáng lẽ chỉ có một.

Ba luật đi kèm:

- **Cờ được LƯU trên khối**, không suy ra được: khối vừa tạo chưa có điều kiện nào để
  suy, mà vẫn phải biết thêm dòng kiểu nào. File cũ (không có cờ) thì suy từ chính các
  điều kiện — đã đo, không sơ đồ nào từng trộn hai kiểu trong một khối, nên phép suy này
  không có ca mập mờ.
- **Đổi cờ viết lại vế phải của mọi dòng**, giữ vế trái và phép so. Có mất dữ liệu, và
  đó là chủ ý: hình dạng do cờ quyết. Hộp thoại là bản nháp — Huỷ là xong, lưu rồi vẫn
  còn Hoàn tác.
- **Toán hạng đúng/sai + cờ bật → LỖI, không sửa lén.** `lệnh này đã khớp > zone_HH`
  không phải một câu; nhưng đổi hộ toán hạng là vứt mất thứ người dùng đã chọn mà họ
  không hề biết. Chuẩn hoá ép HÌNH DẠNG, soát tĩnh nói về NGHĨA.

⚠ `đúng/sai` ở lại cùng `số`, không tách ra cơ chế thứ ba — đo sơ đồ mẫu thì ba cổng
(`Zone đã đủ điều kiện`, hai cổng Manage) **thật sự trộn** `số` với `đúng/sai`. Tách là
gãy ba cổng có thật.

#### ⚙ Tham số của toán hạng nằm trong menu riêng

Khung thời gian · chu kỳ · kiểu trung bình **không** nằm trên hàng điều kiện nữa. Trước
đây chúng nằm inline nên vế trái phình từ **1 ô** (`zone_dem`) tới **4 ô** (MA) tuỳ toán
hạng — hàng nào cũng lệch hàng nào, và thêm một chỉ báo 4 tham số là hỏng bố cục.

Gom vào menu `⚙` thì hàng **luôn bốn cột**: `[đại lượng ⚙] [phép] [lượng] [đơn vị]`.

Không mất thông tin: **thẻ trên canvas vẫn ghi đủ** `ATR(M5, 14) < nguong_nen_bps = 7 bps
của giá` mà không phải bấm gì. Sơ đồ được **đọc** ở canvas, hộp thoại chỉ để **sửa**. Và
`method` (SMA/EMA) là chuyện riêng của MA — để mỗi chỉ báo giữ núm vặn của chính nó thì
hàng ở ngoài mới generic được.

**Bảng này KHÔNG bắt buộc.** Gõ thẳng `7` vào ô là hợp lệ, và với một con số dùng đúng
một chỗ thì gõ thẳng còn **rõ hơn** — bắt khai `nguong = 7` trước rồi mới được dùng chỉ
là một vòng thừa. Hai màn hình "gõ số 7" và "chọn tham số bằng 7" trông y hệt nhau; nếu
đó là toàn bộ lợi ích thì bảng tham số không đáng tồn tại.

Nó đáng tồn tại vì **một** lý do: khi cùng một con số nằm ở **hai nơi**. Sửa một chỗ
quên chỗ kia thì chiến lược lệch **âm thầm** — không lỗi, không báo, chỉ là kết quả
backtest khác đi mà không ai biết vì sao. Sơ đồ mẫu trước đây có **4 hằng số viết cứng
hai lần**, trong đó `7.0` nằm ở **cả hai sơ đồ**: Entry hỏi *"còn nén không"*, Manage
hỏi *"nén tan chưa"*.

Nên chỗ duy nhất ép người dùng nghĩ tới bảng tham số là **dòng cảnh báo** —
`core._soat_so_lap`:

> ▲ Số 7 được gõ tay ở 2 chỗ, cùng là ngưỡng so với ATR (bps của giá). Sửa một chỗ mà
> quên chỗ kia thì chiến lược lệch âm thầm. **[ Đặt tên cho số này ]**

Nút thay số bằng tên ở **cả hai chỗ** cùng lúc và thêm dòng vào bảng. Để lại một chỗ gõ
tay thì cảnh báo biến mất mà cái bẫy vẫn còn — và lần này còn khó thấy hơn.

**Gom nhóm theo `(VAI, ĐƠN VỊ, GIÁ TRỊ)`, không chỉ theo giá trị.** `chu_ky_atr = 14`
và `chu_ky_ma = 14` bằng nhau chỉ vì **trùng hợp**; gộp lại là đặt tên sai, và sau này
đổi một cái sẽ kéo theo cái kia. Tương tự `SL = 1.5 × ATR zone` và `TP = 1.5 R`. Trùng
số không phải là quan hệ.

Python trả kèm `dat_ten.cho` — **đường dẫn tới đúng từng ô số**. Giao diện chỉ đi theo
đường dẫn mà thay, cố ý **không quét lại sơ đồ**: hai đoạn mã quét cùng một thứ là hai
luật, và sớm muộn chúng sẽ lệch nhau. `tests/test_dat_ten.py` chứng minh đường dẫn đúng
bằng cách chạy backtest trước và sau khi đặt tên — kết quả phải **giống hệt**.

Đụng tên thì phân hai ca: **cùng giá trị → dùng lại** dòng đã có (`chu_ky_atr` engine
luôn đòi phải có, đẻ thêm `chu_ky_atr_2 = 14` chính là thứ rác đang dọn); **khác giá
trị → thêm hậu tố**, vì đè lên là âm thầm đổi một thứ người dùng không hỏi.

```jsonc
"tham_so": [
  {"ten": "nguong_nen_bps", "nhan": "Ngưỡng nén", "gia_tri": 7.0, "don_vi": "bps"},
  …
]
// rồi khối gọi bằng TÊN — cùng chỗ, cùng hình dạng với một con số:
{"trai": {"ten": "atr", "tf": "M5", "period": "chu_ky_atr"},
 "phep": "<", "phai": {"value": "nguong_nen_bps", "tinh": "bps"}}
```

⚠ `tinh` trong `phai` mới là thứ **bộ chạy quy đổi** — đơn vị nằm ở CHỖ DÙNG. Còn
`don_vi` trong bảng tham số là một **khoá** (`NHAN_DON_VI`) quyết định tham số ấy được
mời vào ô nào, và khi bạn chọn nó thì `tinh` bị **khoá** theo nó. Hai thứ luôn khớp —
soát tĩnh báo lỗi nếu lệch. (Trước đây cột đó là chữ tự do chỉ để đọc; xem §6.4.)

**Hiển thị có phân biệt, và đó là chủ ý:**

| Chỗ | Hiện gì | Vì sao |
|---|---|---|
| Vế phải điều kiện · khoảng cách · lot | `nguong_nen_bps = 7` | đây là **núm vặn** — tên nói ý nghĩa, số nói thực tế |
| Tham số của toán hạng (chu kỳ, nến) | `ATR(M5, 14)` | đây là **"đọc chuỗi số nào"**, không phải thứ người ta tinh chỉnh |

Soát tự động bắt ba chuyện: tham chiếu tới tham số **không tồn tại** → lỗi; tham số
khai ra mà **không khối nào dùng** → cảnh báo; và **số gõ tay hai chỗ cùng vai** →
cảnh báo kèm nút đặt tên.

Bộ mặc định lấy thẳng từ `kho/engine_d02.py::THAM_SO_MAC_DINH` — cùng một nguồn với
mặc định của EA, nên không có chuyện tài liệu nói một đằng mẫu chạy một nẻo.

---

## 7. Chiến lược mẫu — Compress EA, dịch sang sơ đồ

### 7.1 Ý tưởng một câu

> Biến động co lại như lò xo nén → đặt sẵn **lệnh chờ stop** ngay mép vùng → giá phá ra là khớp.
> **Mọi khoảng cách đều là bội của ATR hoặc của R, không bao giờ là pip/đô cố định**
> → tín hiệu mang **cùng một ý nghĩa** trên vàng, forex, crypto, chỉ số.

### 7.2 Bốn bước

| # | Việc | Công thức |
|---|---|---|
| 1 · **Phát hiện** | Đọc ATR ở **nến đã đóng `[1]`**, chuẩn hoá ra bps | `atr_bps = ATR/Close × 10000` · nén khi `atr_bps < N` |
| 2 · **Xác nhận** | Đếm **K** nến nén liên tiếp, và vùng chúng tạo ra không rộng quá | `bar_count ≥ K` **và** `zone_range/ATR ≤ Range_Max_ATR` |
| 3 · **Vũ trang** | MA khung lớn quyết hướng, đặt lệnh chờ ngoài mép vùng | xem §7.3 |
| 4 · **Quản lý** | Khớp → khoá tín hiệu. Lãi đủ `BE_RR × R` → dời SL về hoà vốn | |

### 7.3 Hình học vào lệnh

```
buf     = Entry_Buffer_ATR × ATR(hiện tại)        ← lá chắn chống phá giả
R       = SL_ATR_Avg       × ATR(trung bình vùng)  ← khoảng cách SL = 1R

MUA  STOP : entry = đỉnh_vùng + buf ,  SL = entry − R ,  TP = entry + RR × R
BÁN  STOP : entry = đáy_vùng  − buf ,  SL = entry + R ,  TP = entry − RR × R
```

**Hai ATR làm hai việc khác nhau, cố ý:**
- `ATR(hiện tại)` → **đệm vào lệnh**, lọc phá giả một nhịp.
- `ATR(trung bình cả đợt nén)` → **kích thước rủi ro**, để mỗi lệnh rủi ro một `R` tương đương
  bất kể vùng rộng hẹp ra sao.

> ⚠ SL là `SL_ATR_Avg × ATR_avg` — **KHÔNG phải mép vùng bên kia** (tài liệu cũ ghi sai).

### 7.4 Luật hướng

- `MUA` chỉ khi `Close > MA` trên khung Trend **và** `Allow_Buy`.
- `BÁN` chỉ khi `Close < MA` trên khung Trend **và** `Allow_Sell`.
- Bật cả hai thì **MUA được xét trước** → mỗi đợt nén chỉ ra đúng một hướng.
- `Close == MA` → `TREND_SIDEWAY` → **không vào lệnh nào cả**.

### 7.5 Máy trạng thái nén

| Trạng thái | Nghĩa |
|---|---|
| `IDLE` | Biến động bình thường (`ATR ≥ N`). Chờ đợt nén mới. |
| `COUNTING` | Đang đếm nến nén tới **K**. |
| `CONFIRMED` | Đủ **K** nến **và** vùng vừa khổ → sẵn sàng vũ trang. |
| `PENDING` | Lệnh chờ đang sống. **Vùng bị đóng băng** — đỉnh/đáy không đổi nữa. |
| `CONSUMED` | Lệnh đã khớp. Khoá chu kỳ mới **cho tới khi `ATR ≥ N` trở lại** → một lò xo chỉ giao dịch một lần. |

`ATR ≥ N` khi đang `COUNTING` / `CONFIRMED` / `PENDING` → đợt nén **tan** → về `IDLE` và **huỷ lệnh chờ**.

> Máy trạng thái này tồn tại để trả lời đúng một câu hỏi tinh tế:
> *làm sao một đợt nén chỉ đẻ ra đúng một lệnh, chứ không bắn lại mỗi tick khi giá vẫn còn im?*

### 7.6 Tham số (mặc định code · giá trị XAU)

| Input | Code | XAU | Nghĩa | Tinh chỉnh? |
|---|---|---|---|---|
| `ATR_Period` | 14 | 42 | Cửa sổ ATR | ❌ cấu trúc lõi |
| `ATR_Threshold_Bps` | 7.0 | 8 | Ngưỡng nén `N` (bps). **Nhỏ hơn ⇒ chặt hơn ⇒ ít nhưng chất** | ✅✅ chính |
| `Comp_Bars` | 10 | 15 | Số nến nén liên tiếp `K` | ✅✅ chính |
| `Entry_Buffer_ATR` | 0.10 | 0.15 | Đệm vào lệnh (× ATR hiện tại) | ✅ |
| `Range_Max_ATR` | 4.0 | 6 | Loại vùng rộng quá (× ATR) — **luôn bật, không tắt được** | ✅ |
| `Trend_TF` / `MA_Period` / `MA_Method` | M15 / 50 / SMA | M30 / 200 / EMA | Bộ lọc xu hướng | ✅ vừa |
| `RR_Ratio` | 2.0 | 4.5 | TP = × R | ✅ |
| `SL_ATR_Avg` | 1.5 | 7 | SL = × ATR trung bình. **Định nghĩa 1R** | ✅ |
| `BE_Enabled` / `BE_RR_Trigger` | true / 1.0 | true / 3 | Dời SL về hoà vốn khi lãi × R | ✅ |
| `Fixed_Lot` | 0.01 | 0.01 | Khối lượng cố định | ❌ **không bao giờ tối ưu** |
| `Max_Positions` | 0 | 3 | Trần lệnh mở đồng thời (0 = vô hạn) | ❌ |

### 7.7 Những thứ EA **KHÔNG** có — đừng mô hình hoá thừa

Trailing stop · đóng một phần · lệnh chờ hết hạn theo thời gian · lọc phiên/giờ · lọc spread ·
lọc tin · sizing theo % vốn · martingale · sửa lệnh chờ sau khi đặt.

### 7.8 Lỗi có thật trong EA — biết để không chép theo

- `CalcLot(entry, sl)` **bỏ qua cả hai tham số**, luôn trả `fixed_lot`.
- `IsTrendOk()` **không kiểm** `ma_trend.result` — trước khi nến Trend đầu tiên đóng, trạng thái là
  `SIDEWAY` (=0) nên chặn cả hai hướng. Vô tình thành cổng khởi động, nhưng là **ngẫu nhiên chứ không cố ý**.
- `CheckPendingActivation()` khớp **bất kỳ** vị thế nào cùng symbol+magic → lệnh chờ bị huỷ từ bên ngoài
  trong lúc đang có lệnh khác mở sẽ bị **đọc nhầm là đã khớp**.
- Giá entry/SL/TP **không** `NormalizeDouble`, **không** kiểm `stops_level`/`freeze_level`, không trừ spread.
- `ChartView.mqh` là **code chết** — tham chiếu struct `STradeState` không tồn tại, biên dịch sẽ hỏng.
- **Bề rộng vùng chỉ được kiểm ĐÚNG MỘT LẦN** lúc chuyển `COUNTING`→`CONFIRMED`. Đã `CONFIRMED`
  rồi thì vùng vẫn nới rộng mỗi nến mà không bị kiểm lại — nên khi `Max_Positions` hoặc `SIDEWAY`
  chặn, entry của nến sau trôi ra xa và lệnh vẫn được đặt dù vùng đã rộng hơn `Range_Max_ATR`.
  Phép kiểm nằm lọt trong nhánh `cur == COMP_COUNTING` nên trông giống sơ suất hơn là chủ ý.
  **Ta không chép** — xem §12.6a.

---

## 8. Giao diện — chép nguyên, chỉ đổi nhãn

### 8.1 Bảng màu (`theme.css`) — **giữ y hệt**

Accent `#ffa657` là **cam**, trùng luôn màu logo mèo → không phải đổi gì.

```css
--bg / --chrome : #202020   /* = ĐÚNG màu thanh tiêu đề Windows, đã lấy mẫu pixel */
--surface       : #2b2b2b   /* bề mặt đồ vật nổi: hộp trên canvas, hộp thoại */
--field         : #2d2d2d
--raised        : #383838      --raised-hover : #454545
--border        : #3f3f3f      --border-soft  : #353535
--text          : #e8e8e8      --muted : #9a9a9a      --dim : #7a7a7a
--ok   : #4ec96a   --err : #e5534b   --warn : #d9a441
--accent: #ffa657  --accent-soft : rgba(255,166,87,.16)
--loop : #ffa657   --group : #6cb6ff   --action : #a8a8a8
--canvas-bg : #1a1a1a   --canvas-dot : #333333
--radius : 8px   --radius-sm : 6px
--font : "Segoe UI", system-ui, sans-serif      --mono : Consolas, "Cascadia Mono", monospace
```

Cat_Studio thêm: `--start: #4ec96a` (khối Bắt đầu) · `--ghim: #d9a441` (khối ghim số) ·
`--day-quay-lai: #d9a441` nét đứt (cạnh quay lại).

### 8.2 Canvas

- **React Flow (`@xyflow/react`)**, `ConnectionMode.Loose`.
- Mỗi khối có **4 cổng ở giữa 4 cạnh**, mỗi cạnh phải có **cả `source` lẫn `target`**.
  Chỉ đặt `source` thì kéo nối vẫn được nhưng React Flow không phân giải nổi đầu **đích** của một
  đường nối đã có → vẽ ra mấy mẩu cụt bên cạnh hộp. Cái `target` trùng id, trùng vị trí,
  `opacity: 0` + `pointerEvents: none` — nó chỉ cần **tồn tại** để đường nối bám vào.
- Đường nối: **bezier** (`type: 'default'`). Cố ý **không** `smoothstep` — hộp cao thấp khác nhau nên
  hai đầu hiếm khi cùng độ cao, đường bậc thang gãy khúc trông như lỗi vẽ.
- Mũi tên `ArrowClosed` 10×10 `#6a6a6a`. To hơn thì nó nặng hơn cả cái cổng nó cắm vào.
- Mặc định nối **phải → trái** (luồng chạy trái sang phải).
- **Double-click lên dây = huỷ kết nối** (cùng quy ước với khối: nhấp đúp lên thứ gì thì tác động lên chính nó).
- **Ngắt hết kết nối** của một khối = cách "tắt tạm" nó mà vẫn giữ trên canvas — huy hiệu về `–`,
  panel Vấn đề báo "không bao giờ chạy tới". Không cần thêm cờ bật/tắt riêng.

### 8.3 Ribbon (kiểu Paint: nhãn nhóm nằm **dưới**)

| Nhóm | Auto_Clicker | → Cat_Studio |
|---|---|---|
| **Thêm khối** | Loop · Nhóm · HĐ lẻ · Rẽ nhánh · Delay | **Kiểm tra ĐK** + (**Vào lệnh** ở Entry / **Sửa lệnh** ở Manage) |
| **Template** | Lưu ▾ (Process/Loop/Nhóm) · Mở ▾ | Lưu ▾ · Mở ▾ — **chỉ cả chiến lược**, không lưu cụm khối rời |
| **Sửa** | Sửa · Nhân bản · Xoá | *(y hệt)* |
| **Luồng** | Đặt số ① · Xem điểm | Đặt số ① · **Ghim số ⟲** · Vừa khung |
| **Hoàn tác** | Hoàn tác · Làm lại | *(y hệt)* |
| **Template** | Lưu ▾ · Mở ▾ | *(y hệt)* |
| *(mép phải)* | Tên Process · Chờ Ns · ▶ Chạy / ■ Dừng | Tên chiến lược · Symbol · TF · **▶ Chạy → Strategy Tester** |

### 8.4 Menu chuột phải

Hỗ trợ sẵn: menu con (`con`), vạch ngăn (`ngan`), mục mờ **kèm lý do** (`tat` + `viSao`).
> Mục bị tắt vẫn **HIỆN** kèm lý do — giấu đi thì người dùng tưởng tính năng không tồn tại.
> Mờ mà không nói vì sao là bực nhất.

| Bấm phải vào | Mục |
|---|---|
| **Nền** | Dán · ─ · Thêm Kiểm tra ĐK + (Vào lệnh **hoặc** Sửa lệnh, theo tab) |
| **Khối** | Sửa · Đổi tên… · ─ · **Ghim số ⟲** 🆕 · Nối tới ▸ · Ngắt hết kết nối · ─ · Chép · Dán · Nhân bản · ─ · Xoá |
| **Dây** | Xoá kết nối |

Khối **Bắt đầu** làm mờ đúng những mục vô nghĩa với nó (Sửa, Ghim, Nhân bản, Xoá) —
**kèm lý do**, không im lặng.

Menu **"Nối tới ▸"** liệt kê mọi khối còn lại **sắp theo nhãn** (`1`, `1A`, `1A.1`, `2`…) → thứ tự đọc
trong menu trùng thứ tự chạy trên canvas. **Cố ý KHÔNG loại khối tạo thành vòng.**

Mục menu **dựng lúc render**, không nhét sẵn vào state: mục menu là closure đọc `nodes`/`edges`/`dangChon`;
đóng băng chúng lúc bấm phải sẽ khiến "Chép" chép nhầm cái đang chọn **trước đó**.

**Bấm phải vào khối phải CHỌN khối đó trước** — trừ khi nó đã nằm trong nhóm đang chọn (người dùng
cố ý chọn nhiều rồi mới bấm phải, phá nhóm đi là làm hỏng ý định của họ).

### 8.5 Phím tắt

`Ctrl+Z` hoàn tác · `Ctrl+Y` làm lại · `Ctrl+D` nhân bản · `Ctrl+C`/`Ctrl+V` chép/dán khối ·
`Ctrl+S` lưu · **`Ctrl+G` ghim số** · `Delete` xoá · `F2` đổi tên.
Hộp thoại đang mở (`.lop-phu` tồn tại) thì phím tắt canvas **phải im** — nếu không, `Delete` trong hộp
thoại vừa xoá hành động vừa xoá luôn cả khối phía sau.

### 8.6 Undo

Chụp **ảnh nguyên khối** (`{nodes, edges, ten}`), không tính diff — tài liệu chỉ vài chục KB, mà diff sai
thì undo hỏng theo kiểu rất khó tìm. Tối đa **60** bước.
Kéo khối: chụp **một lần** lúc bắt đầu kéo, không phải mỗi frame — nếu không một cú kéo tạo 60 bước undo
và `Ctrl+Z` thành vô dụng.

---

## 9. Định dạng file

```jsonc
{
  "schema": 3,
  "type": "strategy",
  "name": "Compress",
  "symbol": "XAUUSD",
  "timeframe": "M5",

  // Hằng số CÓ TÊN — khối gọi bằng tên, không gõ số hai nơi.
  "tham_so": [
    {"ten": "nguong_nen_bps", "nhan": "Ngưỡng nén", "gia_tri": 7.0,
     "don_vi": "bps", "ghi_chu": "Nhỏ hơn ⇒ nén chặt hơn ⇒ ít nhưng chất."}
  ],

  // HAI sơ đồ. File schema 1/2 mở ra vẫn được — `steps` ở gốc nhận làm `entry`.
  "entry":  { "steps": [ … ], "edges": [ … ] },
  "manage": { "steps": [ … ], "edges": [ … ] }
}

// một khối trông thế này:
{ "kind": "action", "id": "s…", "type": "check_cond", "pos": [400, 120],
  "conditions": [
    { "trai": {"ten": "atr", "tf": "M5", "period": "chu_ky_atr"},
      "phep": "<", "phai": {"value": "nguong_nen_bps", "tinh": "bps"} }
  ] }
```

- **`id` bền, nhãn KHÔNG lưu.** Nhãn là hàm thuần của `(steps, edges)` → tính lại mỗi lần mở.
- `from_side`/`to_side` thuần thị giác **nhưng phải lưu** — không thì mở lại file là sơ đồ tự vẽ khác đi.
- **Không có `edges`** ≡ **chuỗi thẳng `1→2→3`** (`default_edges`) → file cũ mở ra vẫn đúng, không phải di cư.
- `clean_edges` bỏ dây trỏ tới khối đã xoá và bỏ trùng — **không tự ý sửa ý người dùng thành thứ khác.**

---

## 10. Môi trường

| | |
|---|---|
| Python | 3.14.2 |
| Node | v20.19.0 · npm 10.8.2 |
| Cần thêm | `pywebview` — xem ghi chú ngay dưới bảng |
| **Bỏ** so với Auto_Clicker | `pyautogui`, `keyboard`, `pyperclip`, `pillow`, toàn bộ `winrt-*` (OCR), `overlay_ui.py`, `overlays.py`, `update_mods.py`, `data/mods_*.txt` |
| Máy | Windows 10 Pro 19045 — cần .NET ≥ 4.7.2 và WebView2 Runtime |
| WebView2 (đo được) | **151.0.4129.72 → Chromium 151**. Đáng ghi vì nó quyết định dùng được tính năng CSS nào; đừng đoán là bản cũ rồi tự né. |

**✅ `quantconnect-stubs` không còn giết pywebview nữa.** Gói đó ship một thư mục `Microsoft/` ở
`site-packages`, mà pywebview (backend WinForms) cần `Microsoft.Win32.SystemEvents` — một
**namespace .NET**. pythonnet gắn bộ tìm của nó vào **cuối** `sys.meta_path`, tức sau bộ tìm đọc
`site-packages`, nên gói Python cướp mất tên và app chết ngay lúc mở cửa sổ với
`FileNotFoundException: Could not load … 'Microsoft'` — một câu **không liên quan gì tới lỗi
thật**. Trước đây phải né bằng một `.venv` riêng; giờ `app_web._uu_tien_namespace_dotnet()` đẩy
`DotNetFinder` lên đầu `meta_path` **trước** `import webview`. Bộ tìm đó chỉ nhận namespace .NET
có thật nên không nuốt nhầm gói Python nào.

---

## 11. Kế hoạch

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| **P0 · Khung** | Fork Auto_Clicker → Cat_studio, gỡ sạch phần game/OCR/overlay. Đổi logo + tiêu đề. | ✅ `python app_web.py` mở cửa sổ Cat Studio |
| **P1 · Đồ thị** | `core.py`: khối/cạnh, `flow_map`, `flow_order`, `diem_gop`, soát lỗi — kèm sửa Bẫy 1, 3, 4 | ✅ 41/41 test |
| **P2 · Số 🆕** | Khối `start` + cờ `ghim` + cạnh quay lại + huy hiệu ⟲ + menu chuột phải + `Ctrl+G` | ✅ vẽ vòng lặp không còn cảnh báo sai |
| **P3 · Hành động** | 3 hành động. 32 toán hạng / 6 nhóm, 9 phép so (ký hiệu), 7 chế độ Sửa lệnh. | ✅ |
| **P4 · Canvas** | React Flow, ribbon, **pill Entry/Manage**, undo 60 bước (gom cả hai tab), template, chép/dán, phím tắt | ✅ |
| **P4b · Kho + lưu trữ** | `kho/` chia theo engine · `so_lenh.py` id của ta · `du_lieu/` · bảng tham số · hộp thoại **Kho** (menu File) | ✅ |
| **P6 · Mẫu** | Sơ đồ mẫu Compress EA, khớp §7 | ✅ **Entry 7 khối · Manage 5 khối · KHÔNG một mũi tên ngược**, soát sạch |
| **P5 · Tester** | Cửa sổ Strategy Tester — thiết kế đầy đủ ở **§12** | 🔨 **thiết kế chốt xong**, khung có 3 lỗi phải sửa (§12.12) |
| **P7 · Bộ chạy** | `nguon_nen` → `tinh_toan` → `khop_lenh` → `bo_chay`. Kho nến M1, backtest thật | ⬜ *(đang tới)* |

### Sơ đồ mẫu ra đúng thế này

**Tab ENTRY** — 7 khối
```
[1] Mỗi nến M5 — tìm tín hiệu
[2] Vùng nén đã xác nhận?
        atr_bps < 7 · số nến nén ≥ 10 · rộng vùng ÷ ATR ≤ 4 · KHÔNG vùng này đã sinh lệnh
[3] Còn chỗ cho lệnh mới?
        số lệnh chờ = 0 · số vị thế < 3
      ├─[3A] Xu hướng LÊN?   (close M15 nến[1] > MA M15 50) → [3A.1] Buy Stop trên đỉnh vùng
      └─[3B] Xu hướng XUỐNG? (close M15 nến[1] < MA M15 50) → [3B.1] Sell Stop dưới đáy vùng
```

**Tab MANAGE** — 5 khối, chạy một lượt cho MỖI lệnh đang sống.
Nhịp **M1** chứ không phải M5 — xem §12.4 (hoà vốn của bản gốc chạy mỗi tick).
```
[1] Mỗi nến M1 — với TỪNG lệnh đang sống
      ├─[1A] Chưa khớp mà nén đã tan?          → [1A.1] Huỷ lệnh chờ
      │         KHÔNG lệnh này đã khớp · atr_bps ≥ 7
      └─[1B] Đã khớp, đủ 1R, SL chưa hoà vốn?  → [1B.1] Dời SL về giá vào
                lệnh này đã khớp · KHÔNG SL đã ở hoà vốn · lãi (×R) ≥ 1
```

Bốn chỗ dễ làm sai, ghi lại để khỏi trượt về:

1. **`ManageBreakEven` = MỘT cổng + MỘT hành động, không tách "ĐK đạt 1R" thành khối
   riêng trên đường chính.** Tách ra là sai hành vi: chưa đủ 1R sẽ chặn luôn phần sau.
   Ba dòng guard của bản gốc (`entry>0 && tp>0`, `sl >= entry`, `bid < trigger`) gói
   đúng vào cổng `[1B]`.
2. **Vế "SL chưa ở hoà vốn" KHÔNG được thiếu.** Manage chạy lại mỗi nến, thiếu nó thì
   lệnh sửa SL bắn lại hoài.
3. **`COMP_CONSUMED` không cần khối** — `KHÔNG vùng này đã sinh lệnh` là một phép tra
   bảng trên `vùng_id` của các lệnh.
4. **`< Max_Positions` chứ không phải `≤`** — bản gốc `if(pos_count >= max) skip`.
   Bằng nhau là đã đầy.

---

## 12. ⭐⭐ STRATEGY TESTER — thiết kế đã chốt  ⛔ ĐÃ BỎ (D-10, §18) — giữ làm lịch sử

> Chốt ngày 2026-08-10 sau một đợt đọc lại toàn bộ `core.py` / `api.py` / `kho/` và cả 6 file
> MQL5 của D_02. Mười một quyết định dưới đây **quyết định kết quả backtest**, không phải chi
> tiết kỹ thuật. Sửa sau là vứt sạch mọi kết quả đã chạy — nên ghi lại kèm lý do ở đây.

### 12.0 Một câu

**Tính một lần, đọc mãi mãi.** Chạy hết backtest một lượt, sinh ra một dòng thời gian bất
biến; giao diện chỉ là đầu đọc trượt trên đó. Tua lại = dời con trỏ, không có cơ chế thứ hai.

### 12.1 ⭐ HAI ĐỒNG HỒ

| Đồng hồ | Là gì | Nhịp |
|---|---|---|
| **M1** | đồng hồ của **thị trường** — giá đi tới đâu, lệnh khớp lúc nào | mỗi nến M1 |
| **M5** | đồng hồ của **chiến lược** — bao lâu thức dậy nhìn một lần | mỗi nến M5 |

Bộ mô phỏng bước từng nến M1: cập nhật giá → xét lệnh chờ có khớp không → xét SL/TP có bị
chạm không. Chỉ khi nến M1 đóng đúng biên M5 thì process mới chạy một vòng.

**Vì sao tách:** nhìn lén tương lai bị chặn bởi *cấu trúc* chứ không bởi sự cẩn thận. Process
chỉ được gọi lúc M5 khép, và tại đó nến M5 vừa đóng là nến mới nhất nó thấy. MA M15 chỉ đổi
giá trị khi biên M15 khép — ba lần một giờ, không phải mỗi lần process chạy. Đúng bản gốc:
`FilterEngine.mqh:316-318` chỉ tính lại MA khi có nến Trend TF mới.

**Chỉ tải MỘT bộ dữ liệu.** M5, M15, H1 gộp từ M1.

### 12.2 ⭐ ĐƯỜNG ĐI 4 ĐIỂM trong một nến M1

Đừng xử lý SL/TP như trường hợp đặc biệt. Biến mỗi nến M1 thành một đường đi rồi bước qua nó:

| Nến | Đường đi |
|---|---|
| C ≥ O (tăng) | O → **L** → **H** → C |
| C < O (giảm) | O → **H** → **L** → C |

Giá nhúng xuống trước rồi mới đẩy lên, hoặc ngược lại — suy từ chính chiều của nến. Đây là
cách dựng giá trong nến quen thuộc của các bộ backtest chỉ có dữ liệu M1.

Rồi mọi thứ còn lại thành **một luật duy nhất**: *"giá chạm mức X ở bước thứ k của đường đi"*.
Lệnh chờ khớp, SL bị chạm, TP bị chạm — cùng một phép kiểm, chỉ khác mức giá.

Cho không hai ca khó:

- **Nến mở cửa đã nhảy qua mức** → điểm đầu đường đi là O, nên khớp **tại O**, không phải tại
  mức đặt. Đúng bản chất gap cuối tuần của XAUUSD. Chiến lược này *chỉ* dùng lệnh stop nên gap
  qua entry là ca thường gặp, không phải ngoại lệ.
- **Khớp rồi chết ngay trong cùng nến M1** → hai sự kiện ở hai bước liền nhau, tự nhiên.

Không còn "trường hợp SL và TP cùng nến" — đường đi đã trả lời cái nào tới trước. Nhưng khi cả
hai mức nằm trong biên độ một nến M1 thì **nhật ký vẫn ghi một dòng riêng**: không phải để cảnh
báo, mà để **đếm được**. Chạy một năm mà con số đó bằng 0 nghĩa là kết quả không phụ thuộc vào
giả định đường đi — đó là bằng chứng, không phải niềm tin.

### 12.3 Spread · phí · tiền

OHLC là giá **Bid**. Quy mọi mức về Bid **một lần**, rồi vẫn chỉ một đường đi chạy trên Bid:

| Mức | Sàn so với | Quy về Bid |
|---|---|---|
| Mua — giá vào (khớp ở Ask) | Ask | `P − spread` |
| Mua — SL/TP (đóng ở Bid) | Bid | `P` |
| Bán — giá vào (khớp ở Bid) | Bid | `P` |
| Bán — SL/TP (đóng ở Ask) | Ask | `P − spread` |

Chi phí spread vì thế hiện ra **đúng chỗ nó phát sinh** — lúc vào lệnh — chứ không phải một
khoản trừ bịa ra ở cuối.

- `spread`: ô nhập, **mặc định 20 points**. Hiện quy đổi ra USD ngay cạnh ô, vì "20 points" chỉ
  có nghĩa khi biết `point` của symbol (XAUUSD 2 chữ số → 0.20 USD; EURUSD 5 chữ số → 2 pip).
- `commission (USD/lot)`: tính **round-turn**, trừ một lần khi lệnh đóng, nhật ký ghi thành dòng riêng.
- `deposit` / `margin (1:…)`: **chỉ để hiển thị** một cột trong bảng phải. Không chặn lệnh, không
  stop-out — với lot 0.01 thì chặn thật là luật thừa.
- D_02 **hoàn toàn không xử lý spread** (grep `spread` trong toàn EA = 0 kết quả) nhưng sàn thì
  kích hoạt Buy Stop theo Ask trên một mức giá tính từ nến Bid. Spread = 0 cho kết quả lãi hơn
  thực tế **một cách có hệ thống**.

### 12.4 ✅ NHỊP THUỘC VỀ KHỐI BẮT ĐẦU

**Entry nhịp M5 · Manage nhịp M1.**

- Entry là **quyết định** — 5 phút xem một lần là đúng.
- Manage là **phản ứng** — càng nhanh càng đúng, và M1 là nhanh nhất dữ liệu cho phép.

**Vì sao Manage không thể là M5:** `ManageBreakEven()` của D_02 nằm **ngoài mọi guard nến**
(`Compress.mq5:128`), chạy mỗi tick. Một nến M5 quét lên đủ 1R rồi quay đầu về SL: EA thật đã
kịp dời SL nên thoát ~0R, còn ta chạy Manage mỗi M5 thì thoát −1R. Lệch **có hệ thống**, và lệch
về phía bản mô phỏng lỗ nhiều hơn thực tế.

**Nhịp ghi trên khối Bắt đầu, KHÔNG phải dropdown trên ribbon.** Hiện chữ "M5" trên khối là một
cái tên gõ tay (`'Mỗi nến M5 — tìm tín hiệu'`) không nối với `doc.timeframe` bằng gì cả — đổi
dropdown thì khối vẫn ghi M5, sơ đồ nói dối. Đúng lỗi `7.0` viết cứng hai chỗ mà §6.4 đã dọn.

→ Chữ trên khối do Python sinh · bỏ dropdown trên ribbon · đổi tên trường `timeframe` → `nhip`
(giờ có bốn thứ đều gọi là timeframe, để tên chung chung là mời gọi nhầm).

**Đã làm** — `schema` lên **4**: `nhip` là khoá trên chính khối Bắt đầu của từng sơ đồ, không
còn `doc["timeframe"]`. `normalize_process` di cư file cũ (nhịp cũ → Entry, Manage → M1) nên
không cần script riêng. Sửa nhịp bằng chuột phải vào khối → **Nhịp chạy** → chọn khung; hộp đổi
chữ ngay vì `core.dong_khoi` sinh nó từ khoá đó. Bỏ luôn `timeframe` khỏi `cai_dat.json` và
`SettingsDialog` — mặc định giờ nằm ở `core.NHIP_MAC_DINH`, một nguồn sự thật.

Thêm một phép soát: **Manage chạy chậm hơn Entry → cảnh báo.** Lệnh vừa sinh mà phải chờ qua
vài nhịp mới được quản lý thì dời SL và huỷ lệnh chờ đều phản ứng trễ hơn cả lúc vào lệnh.

Hai chỗ suýt sót, ghi lại: `luu_tru.doc_cai_dat` giờ **vứt khoá lạ** — bỏ một cài đặt mà không
vứt thì khoá cũ nằm lại trong file vĩnh viễn và người đọc sau tưởng nó còn tác dụng. Và
`StepNode` trước đây ẩn hẳn thân hộp với khối `start` (`{!laStart && …}`), nên dòng nhịp sinh ra
rồi mà không hiện — điều kiện phải là "có dòng nào không", không phải "có phải khối Bắt đầu không".

| Khung | Là gì | Ở đâu |
|---|---|---|
| M5 / M1 | nhịp sơ đồ thức dậy | **khối Bắt đầu** — sự thật của logic |
| M15 (MA), M5 (ATR) | chỉ báo đọc khung nào | từng điều kiện — tuyệt đối, không dính nhịp |
| M1 | nền mô phỏng | cài đặt Strategy Test |
| M1…D1 trên toolbar | nhìn cho thoáng | chỉ là cách vẽ, không đụng kết quả |

### 12.5 ⭐ LUẬT ĐI TRONG SƠ ĐỒ

Ba luật, phải chốt trước dòng code đầu tiên của bộ chạy.

**a) Cổng trượt thì lùi về đâu.** Không chỗ nào trong đồ thị đánh dấu nhánh "đúng/sai" — cạnh
chỉ có `{from, to, port, from_side, to_side}`, ngữ nghĩa nằm ở *thứ tự* nhánh. Nên:

> Cổng trượt → lùi về **ngã rẽ gần nhất còn nhánh chưa thử**.
> **Trừ khi** lượt này đã chạy `vao_lenh` hoặc `sua_lenh` → **hết lượt ngay**.

Vế sau là chỗ quan trọng: đã bắn lệnh ra thị trường thì không rút lại được, nên không được quay
lui thử nhánh khác — nếu không một lượt Entry đẻ ra hai lệnh, trong khi cổng `số lệnh chờ = 0`
chỉ được hỏi một lần ở đầu lượt. D_02 chốt cứng đúng một lệnh chờ (`TradeManager.mqh:330-334`).

Luật này **không có biệt lệ**: cổng chỉ có một đường ra ([2], [3] của sơ đồ mẫu) mà trượt thì tự
rơi vào "không còn nhánh nào chưa thử → hết lượt".

**b) Cổng LUÔN tính đủ mọi điều kiện, không ngắt ở cái sai đầu tiên.** Ngắt sớm thì nhật ký
*vĩnh viễn* không trả lời được "ba điều kiện kia lúc đó thế nào" — chúng chưa từng được tính.
Mà đó đúng là câu cần khi debug: *"cổng trượt vì ATR, nhưng số nến nén đã tới đâu rồi?"*
Chi phí: vài phép so số thực. Ngoại lệ duy nhất được ngắt là điều kiện **không có nguồn dữ
liệu** — khi đó ghi lý do chứ không ghi số.

**c) Thứ tự nhánh mà mơ hồ thì BÁO LỖI.** `_khoa_nhanh` xếp nhánh theo `(ghim, y, x, id)`; hai
khối trùng `y` và `x` thì phân định bằng **uuid** — thứ người dùng không nhìn thấy và không đổi
được. Kéo một khối lên vài pixel là đổi chiến lược trong khi sơ đồ trông y hệt.

> Hai đầu nhánh của cùng một ngã rẽ lệch nhau **dưới 8 px** → `validate_process` báo **lỗi**.

✅ **Đã làm** — `core.LECH_TOI_THIEU = 8.0`, soát trong `validate_so_do` ngay cạnh luật nhánh mặc
định. Báo **lỗi** chứ không cảnh báo: sửa chỉ tốn một cú kéo, còn để nguyên thì cái sai không bao
giờ lộ ra vì sơ đồ trông vẫn đúng. Cạnh quay lại (trỏ vào khối đã ghim) được miễn — nó luôn xếp
cuối bất kể toạ độ, nên không có gì mơ hồ.

### 12.6 Vùng nén

**a) Kiểm bề rộng MỖI NẾN, không chốt một lần.** D_02 kiểm `rong_vung_atr ≤ 4` đúng một lần lúc
chuyển COUNTING→CONFIRMED (`FilterEngine.mqh:268-291`), sau đó vùng vẫn nới rộng mỗi nến mà
**không bị kiểm lại** (`:249-266`). Nên khi bị Max_Positions / SIDEWAY / đang có lệnh chờ chặn,
vùng cứ phình và nến sau vẫn vào lệnh dù đã rộng 6–7×ATR — entry lúc đó xa hẳn chỗ giá thật sự nén.

Ta kiểm lại mỗi nến ở cổng [2]. **Ra ít lệnh hơn**, và những lệnh mất đi đúng là loại entry đã
trôi xa. Đây là chỗ duy nhất trong danh sách khác biệt thật sự đổi *số lệnh*.

> Lý do chọn bản sạch: bản gốc kiểm một lần rồi cấp cho vùng một **giấy phép vĩnh viễn**, trong
> khi thứ nó cấp phép cho vẫn tiếp tục biến dạng. Cấp phép cho một trạng thái rồi để trạng thái
> đó tự do đổi là mâu thuẫn. Bản của ta không có giấy phép nào: điều kiện đúng ở thời điểm nào
> thì vào lệnh ở thời điểm đó, không có trạng thái ẩn nào phải nhớ.
> Khớp 100% thì phải thêm một toán hạng `vung_da_xac_nhan` — tức mang trở lại đúng cái máy trạng
> thái 5 giá trị mà §7.5 đã cố tình bỏ đi.

**b) Khoảng trống dữ liệu > 2 bước nến → VÙNG NÉN CHẾT, đếm lại từ đầu.** Cổng [2] hỏi 10 nến
nén *liên tiếp*, nhưng trên mảng nến thì nến cuối chiều thứ Sáu và nến đầu chiều Chủ nhật nằm
sát nhau — máy sẽ đếm xuyên qua 48 giờ chợ đóng cửa.

Hậu quả cụ thể: vùng bắc cầu cuối tuần → đặt lệnh chờ → lệnh nằm đó suốt weekend (lệnh chờ của
ta **không có hạn**, đúng `ORDER_TIME_GTC` của bản gốc) → gap mở cửa Chủ nhật khớp nó cách xa
entry. Đúng loại lệnh cho kết quả cực đoan nhất và làm lệch hẳn thống kê.

> "Nén" nghĩa là giá đứng yên trong một quãng **liền mạch**. 48 giờ chợ đóng không phải giá đứng
> yên — không có giá nào cả.

### 12.7 ⭐ DÒNG THỜI GIAN BẤT BIẾN · con trỏ

Không lưu "khung hình". Một lần chạy sinh ra ba hình dạng dữ liệu, đóng băng sau khi tính xong:

1. **mảng nến M1** — trục thời gian;
2. **các CỘT** — mỗi chỉ báo/metric là một mảng `float64` trên **trục M5**, đọc từ con trỏ M1
   bằng một phép chia nguyên;
3. **hai danh sách thưa** — sổ lệnh và nhật ký, mỗi bản ghi tự mang chỉ số nến của nó.

**Trạng thái sổ lệnh tại nến i là một PHÉP LỌC, không phải một ảnh chụp** — `so_lenh.Lenh` vốn
đã mang sẵn `nen_dat` / `nen_khop` / `nen_dong`. Chỗ này thiết kế cũ đã vô tình làm đúng.

> **Luật chọn chỗ cất:** thứ gì biến đổi theo nến mà không tự mang dấu thời gian thì thành một
> **cột**; thứ gì đã mang chỉ số nến thì để nguyên trong danh sách thưa.

Áp vào ca khó nhất — `VungNen` mutate liên tục nên trạng thái vùng tại nến i không suy ra được
từ đối tượng cuối cùng → 6 toán hạng vùng nén thành 6 cột. Đường vốn cũng chỉ là một cột nữa.

**Bộ nhớ (1 năm XAUUSD):** nến M1 ~374k dòng ≈ **18 MB** · mỗi cột M5 (71.760 dòng) 0,55 MB ·
~25 cột ≈ **14 MB** · nhật ký vài MB → **tổng ~40 MB**. Nếu chụp ảnh trạng thái mỗi nến thay vì
cột thì 150–350 MB, và con số đó phình theo mọi thứ ta thêm vào trạng thái. Thêm một metric ở
thiết kế cột = thêm 0,55 MB, cố định.

**CON TRỎ = một ĐIỂM trên đường đi giá** (nến M1 × 4 điểm). Không phải "một cây nến", cũng không
phải "một dòng nhật ký".

- **Xem** → trượt liên tục qua từng điểm. Nến đang chạy **lớn dần** ở mép phải đúng như thật:
  một cây nến M5 mọc qua 5 nến M1 × 4 điểm = **20 nhịp**. `delay(ms)` là khoảng cách giữa hai nhịp.
- **Debug** → bấm một dòng nhật ký, con trỏ **nhảy** tới đúng điểm đó.

Cùng một con trỏ, hai cách di chuyển. Và vì replay đúng nghĩa nên **nến bên phải chưa tồn tại** —
không có gì để che, không thể tự lừa mình bằng "chỗ này lẽ ra nên vào lệnh". Thêm một nút "xem
trọn lệnh" cho lúc muốn tua nhanh xem một lệnh đã đóng kết thúc ra sao.

`delay(ms)` là thứ **duy nhất** đổi mà không phải tính lại. Mọi ô cài đặt khác đổi là dòng thời
gian cũ hết hiệu lực.

### 12.8 Nhật ký — phần quan trọng nhất

Người dùng nói thẳng: *"đây là phần quan trọng nhất, vì người dùng debug, nâng cấp model là ở
hết đây."*

**Một bản ghi = một LƯỢT CHẠY.** Trong một nến có nhiều lượt (Manage cho L-0001, Manage cho
L-0002, rồi Entry). Không ghi từng khối đi qua — 7 khối × 71.760 nến = 500k dòng rác.

```
nen      int      chỉ số nến — khoá để tua
seq      int      thứ tự trong nến
tab      "entry" | "manage"
lenh_id  "L-0007" | None     ← lượt Manage này đang xét lệnh nào
duong    [id khối…]          ← đường đã đi, THEO THỨ TỰ
ket      "het_luot" | "xong"
ve[]     mọi điều kiện của cổng cuối: hai vế + đạt/không từng cái
viec     None | {lenh_dat | lenh_khop | lenh_dong | lenh_sua | vung_mo | vung_dong, …}
```

**Lưu `id` khối, KHÔNG lưu nhãn `[3A.1]`.** Nhãn là hàm thuần của (đồ thị + vị trí) và §9 đã cấm
lưu nó vào file. Ghi nhãn vào nhật ký thì kéo một khối lên 1 px là toàn bộ nhật ký cũ trỏ vào
khối khác. Nhãn được **dựng lại** lúc hiển thị bằng `core.flow_order` trên bản `doc` đã đóng
băng trong `meta`.

**Ghi cả `duong`** chứ không chỉ khối cuối: đồ thị được phép có vòng lặp (§4.1) nên đường từ khối
Bắt đầu tới một khối **không duy nhất**, không suy ngược lại được.

**Chữ do Python dựng, theo lô đang nhìn** (~200 dòng) — đúng luật bất di bất dịch #2. 150k bản
ghi không tốn một byte chữ nào lúc chạy.

```
14:35  ENTRY   [1]→[2]                    hết lượt tại [2] · atr_bps 8.31 ≥ 7.0
14:40  ENTRY   [1]→[2]→[3]→[3A]→[3A.1]    đặt Buy Stop L-0007 @ 2334.12  SL 2330.60  TP 2341.16
14:41  MANAGE  L-0007  [1]→[1A]           hết lượt tại [1A] · lệnh này đã khớp = sai
```

**Danh sách phải ảo hoá.** 150k dòng đổ thẳng vào DOM sẽ treo WebView2 — không phải rủi ro, là
chắc chắn ngay lần chạy một năm đầu tiên. Chỉ dựng ~200 dòng đang nhìn, chiều cao dòng cố định
để tính thanh cuộn bằng phép nhân. Tự viết ~60 dòng, không thêm thư viện.

**Mặc định lọc "chỉ lượt có VIỆC xảy ra"**, có nút bật "mọi lượt". 150k dòng đều đều thì mắt
không bắt được chỗ bất thường.

**Ghi ra đĩa** một file `.jsonl` mỗi lần chạy trong `luu_tru.thu_muc_nhat_ky()`, đầu file là
nguyên bản `normalize_process(doc)` + hash — để mở lại và **so hai lần chạy**.

#### 12.8b ✅ GỘP DÃY LẶP — thứ đáng giá nhất của bảng nhật ký

Chạy thật rồi mới lòi ra: 296 dòng trên màn hình mà 7/9 dòng liên tiếp **giống hệt nhau từng
chữ**. Manage chạy nhịp M1 nên mỗi nến M5 đẻ ra 5 dòng y đúc; người dùng phải cuộn qua một bức
tường chữ trùng lặp để tìm dòng có nghĩa.

Gộp **dãy liền kề** giống hệt lại thành một dòng kèm huy hiệu `×4`. Ba điều:

- gọn ~5 lần (mỗi nến M5: 6 dòng → 3);
- **trả lời thêm** được câu *"cổng đó chặn mấy lượt liền"* — thứ cuộn tay đếm không ra;
- chỉ gộp **liền kề**, không gộp cách quãng: gộp cách quãng là xáo trộn thứ tự thật. Dòng
  **có việc** thì KHÔNG BAO GIỜ bị gộp — hai lần đặt lệnh trùng chữ vẫn là hai việc khác nhau.

Kết quả thật trên một nến M5: `MANAGE ×1 · ENTRY ×1 · MANAGE ×4`. Dòng ENTRY cắt đôi dãy Manage,
và chính chỗ cắt đó làm nhịp M5 hiện ra bằng mắt.

Kèm theo: ô lọc **"chỉ dòng có việc"** (mỗi dòng đã mang sẵn cờ `co_viec`, lọc ở JS, không đụng
backend) và nút **Ghi ra file**.

**Dòng được tô trắng là dòng GẦN NHẤT tính tới con trỏ**, không phải "dòng vừa được thêm" và cũng
không phải "dòng trùng đúng nến hiện tại":

- *"dòng vừa thêm"* sai khi **tua ngược** — tua lùi thì dòng mới nhất không còn là chỗ đang đứng;
- *"trùng đúng nến hiện tại"* thì 4/5 khung hình **chẳng có gì sáng** (Entry chỉ chạy ở biên nến
  M5). Đã dựng thử đúng cách này và chụp màn hình mới thấy — bảng tối om suốt.
- Còn *"gần nhất tính tới con trỏ"* thì **luôn có đáp án**, và đúng cả khi tua tới lẫn tua lui.

Cụp/mở: bê nguyên `.bang-duoi` của cửa sổ chính — thanh kéo ở mép trên để chỉnh chiều cao, hàng
tab bên trái, `▼/▲` ở góc phải hàng tab, nhấp đúp hàng tab cũng cụp. Nút gập nằm trên chính bảng
nhật ký chứ không ở góc thanh công cụ: *tay đang ở đâu thì nút ở đó*. Chữ 12px, bằng bảng số liệu.

### 12.9 Bảng số liệu bên phải

**Nó phải dựng từ chính vết đánh giá của lượt đang xem, không được hỏi lại bộ tra.** Nếu không,
bảng và nhật ký sẽ nói khác nhau *đúng lúc đang debug*: `số lệnh chờ` đầu nến là 1, cuối nến là
0, mà cổng [3] đọc nó ở giữa. Bảng ghi 1 còn nhật ký ghi cổng đọc 0 và khớp → mất một buổi tưởng
là bug chiến lược trong khi đó là bug của công cụ.

Bốn khối, mỗi khối một nguồn rõ ràng:

1. **Toán hạng đang dùng** — suy từ chính `doc`, khoá theo `(tên + tf + period)` nên ATR(M5,14)
   và ATR(M5,42) là hai dòng riêng. Toán hạng chưa được đọc trong lượt đó hiện **dấu gạch**, không hiện 0.
2. **Trạng thái engine** — `VungNen.tom_tat()` (đã có sẵn, chưa ai gọi).
3. **Tài khoản** — equity, drawdown, margin đã dùng, số vị thế, số lệnh chờ.
4. **Bảng theo TỪNG LỆNH đang sống** — mỗi lệnh một hàng, cột là 6 toán hạng nhóm "Lệnh này".
   Thiếu bảng này thì tab Manage vô hình.

#### 12.9b ✅ BẢNG TỰ SINH TỪ SƠ ĐỒ — không một nhóm nào viết tay

Bản đầu chia bốn khối như trên, nhưng khối 2 mang đúng cái tên `Vùng nén (engine)` **viết cứng
trong `BangSoLieu.tsx`**. Hôm nay nó đúng vì chiến lược mẫu là D_02; làm chiến lược khác là bảng
nói dối, và ai đó phải nhớ sửa tay. Nhận xét của người dùng nói thẳng ra điều đó:

> *"không nên có cả vùng nén(engine) … tôi chỉ cần xem số các phép toán đang dùng là được. về sau
> làm chế thuật khác sẽ loạn."*

Nên bảng **không còn khối nào định trước**:

- **Hàng nào có** ← `core.toan_hang_dung(doc)`: quét đúng những toán hạng sơ đồ **thật sự đọc** —
  hai vế của mọi điều kiện, cộng những thứ một *cách tính* ngầm đọc (`TINH_CAN_TOAN_HANG`), cộng
  đỉnh/đáy vùng khi có lệnh chờ **stop** (giá đặt neo vào mép vùng, không điều kiện nào hỏi tới
  nhưng người dùng phải thấy lệnh sắp nằm ở đâu). Dedupe, giữ nguyên thứ tự gặp.
- **Nhóm nào có** ← chính `nhom` mà `kho/` đã khai ở mỗi toán hạng — nhưng xem 12.9c, tên nhóm
  cuối cùng KHÔNG được in ra.
- **Giá trị** ← `ApiTester._cot_toan_hang`, ba nguồn theo thứ tự rẻ dần: cột đã tính sẵn (chỉ báo
  + giá) → cột engine ghi lúc chạy → thứ suy được từ sổ lệnh/thời gian. Không tra được thì trả
  `None` và bảng để trống: **thà bỏ trống còn hơn bịa một con số**.
- `bo_chay` cũng lấy danh sách cột engine cần ghi từ chính `toan_hang_dung` (∩ `ENGINE_TRA_LOI`),
  nên nó chỉ ghi những cột bảng sẽ dùng — bỏ được bộ 6 cột cố định trước đây.

Thêm một engine mới vào `kho/` là bảng có ngay, **không sửa một dòng giao diện nào**.

Nhóm *"Lệnh này"* cố ý ĐỨNG NGOÀI cơ chế trên: nhóm đó không có **một** giá trị tại nến `i` —
Manage chạy một lượt cho **mỗi** lệnh đang sống. Ép thành một con số là bảng lại nói khác nhật ký,
đúng cái bẫy đầu mục này cảnh báo. Nên nó là bảng riêng bên dưới, mỗi lệnh một hàng.

#### 12.9c ✅ BỎ HẲN TÊN NHÓM · ba cột · lệnh hai dòng

Cơ chế 12.9b đã tổng quát, nhưng **kết quả in ra thì không**: `VÙNG NÉN` đứng ngang hàng với
`CHỈ BÁO / TÀI KHOẢN / GIÁ`, mà ba cái kia là phạm trù phổ quát còn nó là khái niệm riêng của một
chiến lược. Người dùng: *"tôi không thích gọi là vùng nén vì đây không tổng quát."* Đây là một
bài học chung: **cơ chế tổng quát vẫn có thể đẻ ra một màn hình không tổng quát.**

Chốt: **tên nhóm không in ra nữa.** `nhom` vẫn về đủ trong payload, nhưng giao diện chỉ dùng nó để
biết **chỗ kẻ một đường mảnh**. Không tiêu đề nào thì không tiêu đề nào sai được — chiến lược nào
sau này cũng đúng, vĩnh viễn. Cấu trúc không mất, vì danh sách vốn xếp theo đúng thứ tự sơ đồ đọc
nên các số cùng loại tự nằm cạnh nhau. Bỏ 4 tiêu đề còn thu lại ~110px chiều cao.

**Ba cột thay vì hai.** Chỗ phí nhất là khe rỗng giữa nhãn trái và số phải, trong khi tên dài lại
bị cắt cụt. Tách nhãn làm đôi ngay ở `api.py` (`ten` + `phu`) rồi đặt `phu` (`M15·50·SMA`, chữ mờ
10.5px) vào đúng cái khe đó: hết phí chỗ, và tên ngắn lại nên thôi bị cắt. Số dùng
`tabular-nums` — thiếu nó thì lúc phát cả cột giật ngang theo từng con số, mắt không quét dọc nổi.

Chữ **12px** — 11px mỏi mắt, 13px chiếm chỗ mà chẳng rõ thêm.

**Mỗi lệnh HAI DÒNG.** Một dòng 5 cột thì ba mức giá bị cắt thành `2643.0…`, đọc ra một con số vô
nghĩa. Dòng trên là *tình trạng* (hướng · id · đã khớp/chờ Stop · R), dòng dưới là *ba mức giá đủ
số*. Chấm hoà vốn chuyển sang nằm cạnh **SL** — nó nói về SL chứ không nói về cái id.

#### 12.9d ⚠ LỖI THẬT: hàng lệnh đọc trạng thái CUỐI backtest

Tìm ra lúc soi ảnh chụp kiểm bố cục mới, không phải lúc tìm lỗi.

`L-0006` **đặt** 17:55 nhưng mãi **19:55** mới khớp — bảng lại hiện *"đã khớp · −1.21R"* ngay ở con
trỏ 17:59. Nguyên nhân: hàng lệnh đọc thẳng `l.da_khop` / `l.gia_khop` / `l.sl` / `l.tp`, mà `Lenh`
là đối tượng của **cuối backtest** và mọi lần *Sửa lệnh* đã ghi đè lên chúng.

Đây đúng là cái bẫy §12.9 dựng cả mục ra để cảnh báo, và **chart đã dính đúng nó một lần rồi**
(§12.16). Một cơ chế cắt lát đã có sẵn không tự lan sang chỗ mới: chỗ nào đọc `Lenh` cũng phải hỏi
lại "trường này là của lúc nào".

Sửa: `bo_chay.lenh_tai_nen(kq, l, i, gia)` cắt **mọi** trường theo `i`. Kèm hai thứ:

- `_moc_muc(kq)` gom mọi mốc SL/TP từ nhật ký (`lenh_dat` + `lenh_sua`), `_muc_tai` tra ngược ra
  mức tại nến `i` — nên **TP cũng hết rò**, không chỉ SL.
- `_sl_lich_su` lấy điểm đầu từ chính bản ghi `lenh_dat` thay vì suy ngược `gia_dat ± R`. Cách suy
  ngược đúng với SL nhưng chịu thua với TP, vì công thức khoảng cách TP không được lưu ở đâu cả.

Kiểm lại: 17:59 → `chờ Stop @2638.965`, `lai_R = None`; 20:05 → `đã khớp`, `−0.37R`.

Khi con trỏ đứng đúng lượt có lệnh được đặt, hiện thêm **phép tính vào lệnh đã dùng số nào**:
`đệm = 0.10 × ATR_hiện_tại = 0.42 · R = 1.5 × ATR_TB_vùng = 4.80`. Đây là chỗ **duy nhất** bắt
được lỗi lẫn hai loại ATR mà §6.3 cảnh báo — validator không bắt được lỗi đó.

### 12.10 Chart — chỉ lệnh, không gì khác

Tuyệt đối không indicator, không vẽ gì thêm. Ép bằng kiểu dữ liệu: component chart nhận đúng
`{nen[], lenh[]}` và **không có đường nào chạm tới `cot`**.

| Trạng thái lệnh | Vẽ |
|---|---|
| chờ | 3 đường ngang: entry · TP · SL |
| đã khớp | mũi tên theo chiều mua/bán |
| đã đóng | mũi tên đầu + mũi tên cuối + vạch nối; rê chuột hiện profit, giờ vào, giờ ra |

Không có thư viện chart nào trong `package.json` → **tự vẽ Canvas 2D**, hợp với bộ icon nét tự
vẽ sẵn có và không phụ thuộc mạng. Cuộn chuột = zoom. Crosshair là một cờ chế độ chuột.

Nút đổi timeframe trên toolbar **chỉ đổi cách vẽ** (gộp M1 lên M5/M15/H1…), không đụng kết quả.

### 12.11 ✅ Cài đặt Strategy Test · nguồn nến

**Nằm trong Cài đặt của APP** (bánh răng ở thanh trạng thái, hoặc File → Cài đặt), thành một mục
riêng "Strategy Test" — **KHÔNG nằm trong cửa sổ tester**.

> Cài đặt là thứ đặt một lần rồi quên. Để nó trong cửa sổ tester thì mỗi lần bấm ▶ lại phải đi
> qua một bảng nữa mới chạy được — một thao tác hoá ba. Giờ **bấm ▶ ở cửa sổ vẽ là tester mở ra
> và CHẠY LUÔN**, cửa sổ đó chỉ còn nút `↻ Chạy lại`.

Khoá riêng `test` trong `du_lieu/cai_dat.json` + hàm `save_test_settings` với danh sách trắng
riêng — **không nhét vào `save_settings`**, hàm đó đang giữ nghĩa "cài đặt của trình soạn thảo";
trộn vào là hai thứ khác hẳn nhau cùng một cửa và sớm muộn giẫm chân nhau.

Ô nhập: `symbol` · `từ` · `đến` · `spread (points)` · `vốn (USD)` · `phí (USD/lot)` ·
`đòn bẩy 1:…` · `delay (ms)`. Cộng bảng **nguồn dữ liệu** ngay trên đó: mỗi symbol một dòng —
có từ ngày nào đến ngày nào, bao nhiêu nến, **bao nhiêu MB**, nút Xoá, nút Tải thêm.

Quản lý nguồn nến đặt ở `Api` CHÍNH chứ không ở `ApiTester`: nến là tài sản của **app** — tải một
lần rồi mọi chiến lược dùng chung — không phải của một lần chạy.

⚠ **Tester KHÔNG nhớ cài đặt.** `test_chay` đọc lại từ cửa sổ chính mỗi lần chạy. Nhớ ở phía JS
thì sửa Cài đặt xong bấm ▶ lại vẫn ăn bản cũ — mà cửa sổ tester sống lâu hơn một lần chạy, nên
mọi thứ nó "nhớ" đều có nguy cơ cũ.

Ô spread hiện **quy đổi ngay cạnh**: `XAUUSD: 1 point = 0.001 · spread 37 points = 0.037 USD ·
trung vị đo được trên dữ liệu đã tải: 37 points`. Thiếu dòng này thì "20 points" là con số vô
nghĩa — XAUUSD 3 chữ số thì đó chỉ là 0,02 USD, nhỏ hơn spread thật gần hai lần.

**Kho nến** ✅ — `nguon_nen.py` chỉ còn **ĐỌC** những bộ nến M1 đã có trên máy
(`du_lieu/nen/`). App không tải nến nữa (D-09, §17).

- Một symbol giữ đúng **một dải liền**: một file `.npy` + một file meta `.json` cạnh nó, giữ
  `digits` / `point` / `contract_size` / `spread_tb` → tính ra tiền đúng và ô "20 points" quy
  đổi được ra USD.
- Danh sách trong Cài đặt: mỗi symbol một dòng — có dữ liệu từ ngày nào đến ngày nào, bao nhiêu
  nến, **bao nhiêu MB**, nút xoá.
- Bấm ▶ mà thiếu **phần đầu** khoảng đã đặt thì dừng và nói rõ thiếu khoảng nào, máy đang có
  khoảng nào (`api._kiem_du_nen`). Thiếu phần đuôi thì vẫn chạy — bảng Thống kê in khoảng THẬT
  SỰ có nến cạnh khoảng đã đặt.

**Đã đo thật** (XAUUSD, 2025-11): 29.917 nến một tháng = **1,37 MB** → một năm ≈ **16,5 MB**.

⚠ **`spread_tb` là con số phải nhìn.** XAUUSD của Exness có `digits = 3`, nên `20 points` chỉ là
**0,02 USD** — quá nhỏ. Trung vị đo được trên dữ liệu thật là **37 points**. Meta của mỗi bộ nến
giữ con số TRUNG VỊ đó (`spread_tb` — trung vị, không phải trung bình: vài nến tin tức giãn gấp
chục lần sẽ kéo lệch), để ô spread trong Cài đặt gợi ý đúng thay vì bắt người dùng đoán.

**`lo_hong()` — thứ luật vùng nén cần.** Một tháng XAUUSD có **26 lỗ**, dài nhất **3.083 phút
(~51 giờ)**, và bốn cái dài nhất đều là cuối tuần. Đây chính là bằng chứng cụ thể cho §12.6b:
không cắt vùng nén ở lỗ hổng thì máy sẽ đếm "nến liên tiếp" xuyên qua 51 giờ chợ đóng cửa.

### 12.12 ✅ BA LỖI CÓ SẴN của cửa sổ tester — ĐÃ SỬA

Không phải rủi ro. Là lỗi chắc chắn, và chúng sẽ giả dạng thành "Python hỏng" đúng lúc đang
debug bộ chạy. Đã sửa xong và **đo bằng thao tác chuột thật** — xem cuối mục.

1. **`file:///` → trang trắng.** `api.py:366` ghi cứng `url=f"file:///{trang}?tester=1"`.
   pywebview coi mọi url mở đầu `file://` là không-local nên **không dựng http server** cho cửa
   sổ đó, mà `dist/index.html` là `<script type="module" crossorigin>` → origin `null` →
   Chromium chặn. Chính `app_web.py:183-186` đã ghi lại đúng bài học này rồi.
   → truyền đường dẫn cục bộ **trần**, không tiền tố `file://`.
2. **`js_api=self` → bấm ✕ trong tester ĐÓNG CỬA SỔ CHÍNH.** Dùng chung một instance `Api` mà
   `self._window` vẫn trỏ cửa sổ chính. → tách `ApiTester` riêng, có `_window`/`_khung` của nó.
3. **`KhungTuVe` giữ đúng MỘT hwnd** → kéo thanh tiêu đề tester kéo nhầm cửa sổ chính.

Thêm một chỗ nữa cùng loại: **`_mo_cua_so_tester` huỷ rồi tạo lại cửa sổ mỗi lần bấm ▶**
→ mất con trỏ, mất zoom, mất vị trí cuộn nhật ký, mất bộ lọc. Mà vòng lặp debug thật là
*sửa → chạy → so*. → cửa sổ còn sống thì **giữ**, chỉ nạp sơ đồ mới rồi bắn `so_do_moi`
xuống; con trỏ neo theo **thời gian nến**, không theo chỉ số.

**Cách sửa** (`api.py`): tách lớp nền `NenCuaSo` giữ `_window` + `_khung` + 7 hàm cửa sổ; `Api`
và `ApiTester` đều kế thừa. Mỗi cửa sổ MỘT thể hiện là hết cả ba lỗi, không phải nhớ kỷ luật gì.
`ApiTester` cố ý HẸP — không lưu chiến lược, không mở hộp thoại file, không đổi cài đặt.
`TitleBar` bên JS dùng lại nguyên vẹn: cầu nối tra hàm theo TÊN trên api của đúng cửa sổ đang
chạy, nên `cua_so_dong` ở tester rơi vào `ApiTester.cua_so_dong`.

**Hai cái bẫy lòi ra lúc sửa, ghi lại kẻo lần sau vấp tiếp:**

1. **`?tester=1` chưa ai đọc.** `api.py` gắn tham số đó vào url từ lâu nhưng không chỗ nào
   trong `webui/src` đọc `location.search`, nên cửa sổ thứ hai dựng lại y hệt trình soạn thảo.
   → một dòng `if` trong `main.tsx`, không cần entry thứ hai cho Vite.
2. **`useKhungCuaSo` nằm ở TRANG, không nằm trong `TitleBar`.** Trang tester vẽ `TitleBar` là
   ra đúng thanh tiêu đề, trông xong hẳn — nhưng **không kéo được, không giãn được**, vì hook
   gắn handler chuột lại ở `App.tsx`. Triệu chứng giống hệt "vá khung hỏng" nên rất dễ đi sai
   hướng. (Trước đó còn một tầng nữa: `_va_khung` hẹn giờ 0,45 s chạy TRƯỚC khi cửa sổ kịp
   `IsWindowVisible` → không tìm ra hwnd → cũng không kéo được. Giờ nó thử lại tới 4 s.)

**Đã đo bằng chuột thật, không phải suy luận:** bấm ▶ hai lần → vẫn đúng **hai** cửa sổ · kéo
thanh tiêu đề tester 300,200 → 400,300 trong khi cửa sổ chính **đứng yên** ở 20,20 · giãn mép
phải 1180 → 1302 px · bấm ✕ trên tester → tester đóng, **cửa sổ chính còn sống**.

### 12.13 Những thứ backend CHƯA CÓ (kiểm kê 2026-08-10)

Cat_Studio là một bộ soạn thảo hoàn chỉnh và một bộ chạy **bằng không**. Phải viết mới:

| Module | Trách nhiệm |
|---|---|
| ✅ `nguon_nen.py` | kho nến trên máy, CHỈ ĐỌC: đọc · liệt kê · xoá · MB · còn thiếu khoảng nào · `lo_hong()` |
| ✅ `tinh_toan.py` | chỉ báo thuần: mảng nến → mảng `float64`. Warm-up trả **NaN**, không trả 0. Kèm `gop()` (M1 → M5/M15/H1) và `theo_truc()` (đưa cột khung lớn về trục quyết định) |
| ✅ `khop_lenh.py` | mô hình sàn: đường đi 4 điểm, spread, gap. **Tách riêng** vì đây là thứ duy nhất đổi mà đổi cả đường vốn. Hàm THUẦN — không numpy, không sổ lệnh, không đồ thị |
| ✅ `bo_chay.py` | biên dịch sơ đồ → chương trình phẳng, rồi vòng lặp nến |
| ✅ `bo_chay.KetQua` | vật chứa bất biến của một lần chạy (không cần file riêng — nó chỉ là kết quả của `chay()`) |
| ✅ `nhat_ky.py` | bản ghi rỗng chữ + dựng câu theo lô + ghi/đọc `.jsonl` + so hai lần chạy |
| `api_tester.py` | `Api` riêng cho cửa sổ thứ hai |

**Biên dịch sơ đồ MỘT LẦN trước vòng lặp** không phải tối ưu sớm mà là điều kiện sống còn:
`atr_bps(M5, chu_ky_atr)` → "cột số 3", mọi tên tham số → `float`, `flow_map` → danh sách kề
bằng chỉ số nguyên. Vòng chạy sau đó không đụng một chuỗi nào. Không có bước này thì 1–3 triệu
phép đánh giá bằng dict + chuỗi mất 10–30 giây mỗi lần bấm ▶. **Phải đo trên 1 năm thật trước
khi viết giao diện.**

Ngoài ra:

- **Công thức ATR trong `kho/chi_bao.py` đang SAI** — ghi *"theo Wilder"*, nhưng ATR mà D_02
  thật sự dùng là **SMA của True Range**. Sai im lặng và dây chuyền: ATR khác → `atr_bps` khác →
  nến nào là nến nén khác → số nến nén, thời điểm xác nhận, đỉnh/đáy vùng, độ lớn 1R, TP lệch
  hết. **Cài theo công thức D_02** và sửa luôn câu mô tả — ngưỡng 7.0 bps được dò ra trên chính
  công thức đó.
  ✅ **Đã sửa mô tả**: `"SMA của True Range (công thức D_02 dò ngưỡng — KHÔNG phải Wilder)"`, kèm công
  thức cửa sổ trượt `ATR[i] = ATR[i-1] + (TR[i] − TR[i-period]) / period` trong chú thích. Câu
  cảnh báo nằm ngay trong chuỗi hiển thị chứ không chỉ trong comment — hộp thoại Kho là chỗ
  người ta tra công thức, để cảnh báo ở comment thì không ai thấy. Bộ TÍNH thì vẫn chưa có.
- **Sáu toán hạng khai mà không có nguồn**: `drawdown_pt`, `so_lenh_hom_nay`, `bid`, `ask`,
  `spread`, `gio`, `thu`. Chọn được trong hộp thoại → vẽ ra sơ đồ hợp lệ mà bộ chạy không chạy
  nổi; sơ đồ mẫu tình cờ không dùng nên test vẫn xanh và lỗi này đang trốn. → **cài luôn cả
  sáu**, không đánh dấu "chưa hỗ trợ" (nhãn đó để lâu sẽ mục).
- **Toán hạng vùng nén khi chưa có vùng nào** → trả 0 là lời nói dối lọt qua mọi phép so.
  Không có nguồn thì **điều kiện TRƯỢT** và nhật ký ghi lý do.
- **Lệnh còn sống lúc hết dữ liệu** → đóng theo giá đóng nến cuối, ghi `het_du_lieu`, tách riêng
  trong thống kê.
- `so_lenh.Lenh` cần thêm **đúng hai trường**: `phi` và `lai_tien`. **Không** thêm trường thời
  gian thật — `nen_khop` + mảng nến đã cho ra `datetime` bằng một phép tra bảng, thêm nữa là chép
  cùng một sự thật ra hai chỗ.

### 12.13b Bảng đối chiếu D_02 — 9 chỗ cố ý khác, 4 chỗ ĐỔI SỐ

`tests/test_doi_chieu_d02.py` in ra bảng này mỗi lần chạy. Cột quan trọng nhất là **có đổi số
không** — thiếu nó thì chín dòng trông ngang nhau, trong khi chỉ bốn dòng đụng tới kết quả, và
đúng bốn dòng đó mới cần lôi ra xem lại khi số không khớp bản gốc.

| # | Chỗ khác | Đổi gì |
|---|---|---|
| 3 | Kiểm lại bề rộng vùng mỗi nến (bản gốc chỉ kiểm một lần) | **SỐ LỆNH** — ta ra ít hơn |
| 5 | Manage nhịp M1 (bản gốc chạy hoà vốn mỗi tick) | **GIÁ & P&L** — ta lỗ nhiều hơn |
| 6 | Vùng nén chết khi gặp khoảng trống dữ liệu | **SỐ LỆNH** — bỏ vùng bắc cầu cuối tuần |
| 7 | Mô hình khớp: đường đi 4 điểm · spread · gap ở giá mở cửa | **GIÁ & P&L** — bản gốc không có spread |
| 1, 2, 4, 8, 9 | id thay `HasOpenPosition` · `vung_id` thay đóng băng vùng · đồ thị thay máy trạng thái · id thay magic · bỏ `CalcLot` nói dối | không |

Hai bài kiểm neo bảng này vào code thật để nó không trôi thành văn viết cho vui: **R4** đòi nhịp
mẫu đúng M5/M1, **R5** đòi `rong_vung_atr` vẫn nằm trong cổng vào lệnh.

### 12.13c Gộp khung — đã đối chiếu với nến của sàn

Gộp theo **BIÊN THỜI GIAN TUYỆT ĐỐI** (`t // 300`), KHÔNG phải đếm 5 nến một cụm. Dữ liệu M1
thật đầy lỗ hổng, nên đếm cụm thì chỉ cần một nến thiếu là mọi nến M5 sau đó lệch pha khỏi biên
thật của sàn — và không có gì báo cho biết.

**Đã đối chiếu trên một tháng XAUUSD thật** với chính nến mà sàn dựng: 5.994 nến M5 · 1.999 M15
· 501 H1, **lệch OHLC lớn nhất = 0**. Cùng số nến, cùng mốc thời gian, cùng giá.

⚠ **Ô CUỐI CÙNG bị BỎ nếu dữ liệu chưa chạy hết ô.** Đây là thứ phép đối chiếu trên lôi ra:
dữ liệu M1 dừng đúng `2025-12-02 00:00` thì ô M5 `00:00–00:04` chỉ có 1/5 phút, và nến gộp ra
lệch hẳn nến của sàn (close 4225.331 vs 4225.692). Giữ nó là bộ chạy đọc một cây nến **chưa đóng** như
thể đã đóng — đúng loại lỗi nhìn trước tương lai mà cả kiến trúc này dựng lên để tránh.

Bỏ đúng ô CUỐI, không bỏ ô thiếu phút ở giữa: ô giữa thiếu vài phút vẫn là ô đã đóng thật (sàn
cũng dựng vậy), chỉ ở ô cuối ta mới không biết sau đó còn gì. Chart muốn thấy cây nến đang chạy
lớn dần thì xin `giu_nen_do_dang=True`.

### 12.13d Khớp lệnh — bốn luật đã cài

`khop_lenh.py` cố ý **không biết** `digits` là gì, không biết sổ lệnh, không import numpy. Nó
nhận một lệnh + một nến + spread (đơn vị GIÁ) và trả danh sách sự kiện. Nhờ vậy mọi ca đều kiểm
được bằng con số tính tay.

| Luật | Cài thế nào |
|---|---|
| SL/TP cùng nến | đường đi 4 điểm quyết cái nào tới trước; nến tăng → đáy trước, nến giảm → đỉnh trước |
| Spread | quy mọi mức về Bid MỘT lần: Mua-vào và Bán-ra dịch `− spread`, hai cái kia giữ nguyên |
| Gap | chạm mức ở **bước 0** nghĩa là mở cửa đã ở bên kia → khớp tại giá MỞ CỬA |
| Khớp rồi chết cùng nến | chỉ là hai bước liền nhau trên cùng đường đi, không phải ca đặc biệt |

Hai chi tiết dễ bỏ sót, đã có bài kiểm riêng:

- **SL/TP chỉ được xét TỪ bước khớp trở đi.** Nến tăng `O=99 → L=94 → H=101` khớp Buy Stop 100
  ở bước 2; cái đáy 94 đi qua ở bước 1, TRƯỚC khi lệnh tồn tại, nên không được tính là chạm SL.
  Xét cả nến là để một cái SL chưa tồn tại giết một vị thế chưa mở.
- **Gap qua TP thì tốt hơn mức đặt, gap qua SL thì xấu hơn** — đúng như sàn khớp, và bất đối
  xứng đó là thật chứ không phải thiên vị.

`ca_hai_trong_nen()` đếm số nến mà cả SL lẫn TP đều nằm trong biên độ. Không dùng để quyết định
gì — đường đi đã quyết rồi. Chạy một năm mà con số đó bằng 0 thì có **bằng chứng** kết quả không
phụ thuộc vào giả định đường đi.

### 12.13e Bộ chạy — đã đo trên một năm thật

| | |
|---|---|
| Dữ liệu | XAUUSD M1 2025, **354.503 nến** (16,2 MB) · 271 lỗ hổng, dài nhất 4.388 phút |
| Một lần bấm ▶ | **2,9 giây** → 70.795 nến M5 · 134.067 lượt chạy |
| Kết quả | 548 lệnh · 386 đóng · 162 huỷ · thắng 25,6 % · **tổng −7,5R** |
| **`nen_mo_ho`** | **0** |

`nen_mo_ho = 0` suốt một năm là con số quan trọng nhất bảng này: **không một nến M1 nào có cả SL
lẫn TP nằm trong biên độ**. Nghĩa là kết quả trên KHÔNG phụ thuộc vào giả định đường đi 4 điểm —
đó là bằng chứng, không phải niềm tin (§12.13d).

**Lần đo đầu là 11,5 giây.** `cProfile` chỉ thẳng: `so_lenh.dang_song()` ăn **57 %** thời gian —
nó quét TOÀN SỔ mỗi lần gọi, mà bộ chạy gọi nó trên mỗi nến M1: 354.000 × 550 lệnh = **195 triệu**
phép kiểm. Bộ chạy giờ tự nuôi danh sách lệnh đang sống, O(1–3) mỗi nến → **2,9 s**, và kết quả
**giống hệt tới từng con số** (550 lệnh, 99 thắng, 289 thua, −9,5R, 135.010 lượt) — đó mới là bằng
chứng tối ưu không đổi hành vi.

Nuôi danh sách ở BỘ CHẠY chứ không sửa `so_lenh`: đó là chuyện tốc độ của vòng lặp, không phải
chuyện mô hình sổ lệnh.

*(Bảng trên là số SAU khi sửa lỗi khung giờ ở 12.13e-bis. Trước đó là 550 lệnh · −9,5R, và phép
so "giống hệt tới từng con số" của tối ưu `dang_song` được đo trên bộ số cũ đó — nó vẫn đúng: tối
ưu không đổi hành vi, cái đổi số là lỗi dưới đây.)*

#### 12.13e-bis ⚠ LỖI THẬT: toán hạng GIÁ bỏ quên khung thời gian
> **⚠ MỤC NÀY GHI "ĐÃ SỬA" NHƯNG VÁ HỤT — xem §13.0a.** Đợt vá dưới đây mới làm 2/3 bước: dựng
> đúng cột và đúng khoá, nhưng quên sửa chỗ ĐỌC, nên cột dựng ra không ai dùng. Con số 3,48 % và
> bảng §12.13e đều đo trên mã còn lỗi.

Tìm ra lúc dựng bảng số liệu tổng quát, không phải lúc tìm lỗi.

`close(M15, nến[1])` **đọc thẳng `nen5`** — tức nến M5. Nên cổng xu hướng đang so **Close M5 với
MA M15**, trong khi D_02 so `Close[1]` với `MA[1]` **cùng khung Trend** (`FilterEngine.mqh:324`).
Chỉ báo thì đã đúng từ đầu (chúng đi qua `_xin_cot`); riêng bốn toán hạng giá
`close/open/high/low` đi đường tắt.

Hai chỗ sửa, cả hai nằm ở `bo_chay.ChuongTrinh`:

1. `_xin_cot_gia` — toán hạng giá cũng **xin một cột riêng cho khung của nó**, rồi đưa về trục
   quyết định bằng đúng cách chỉ báo vẫn làm (giá trị của nến khung lớn **đã đóng** gần nhất).
2. `khoa()` gán `period=None` cho toán hạng giá. Để mặc định 14 chui vào khoá thì `close(M15)`
   thành `('close','M15',14.0,None)` — vô nghĩa, và đụng ngay nếu sau này có toán hạng giá thật
   sự nhận chu kỳ.

Cùng lúc chốt luôn nghĩa của `shift`: **đếm ngược từ nến ĐÃ ĐÓNG**. Mọi cột ở đây vốn đã là "giá
trị của nến đã đóng gần nhất", nên `nến[1]` (quy ước của D_02) chính là **lệch 0**.

Đo mức lệch: trung bình **1,34**, lớn nhất **56**, và **chiều xu hướng khác nhau trên 3,48 % số
nến**. Thống kê cuối tình cờ không đổi mấy (548 lệnh, 99T/287B, −7,5R) — nhưng "tình cờ không đổi
mấy" không phải là lý do để giữ một phép so sai khung.

### 12.13f Nhật ký — đã chạy trên dữ liệu thật

Dựng chữ cho lô 14 dòng đang nhìn mất **0,6 ms**; 8.020 bản ghi không tốn một byte chữ nào lúc
chạy. Ghi ra `.jsonl` (3,3 MB) mất 0,06 s, đọc ngược lại đủ cả lệnh lẫn lượt.

```
11-05 19:00  ENTRY   [1]→[2]→[3]→[3A]→[3A.1]  đặt Mua L-0001 @3986.33  SL 3982.42  TP 3994.15
11-06 11:45  MANAGE L-0003  [1]→[1B]→[1B.1]   sửa L-0003 · Dời SL về hoà vốn → SL 4013.73
11-07 05:55  MANAGE L-0004  [1]→[1A]→[1A.1]   huỷ lệnh chờ L-0004
11-20 03:00  ENTRY   [1]  hết lượt tại [2] · ATR chuẩn hoá (bps)(M5, 14) = 21.44, không < 7.00
11-02 23:00  ENTRY   [1]  hết lượt tại [2] · ATR chuẩn hoá (bps)(M5, 14) chưa có dữ liệu
```

**Ba chỗ hỏng mà vẫn "trông có vẻ chạy", đã bắt được và có bài kiểm riêng:**

1. **`Lenh.tom_tat()` có sẵn khoá `loai`** (stop/limit/market). Trải phẳng nó vào bản ghi là
   ĐÈ MẤT nhãn dòng, nên đọc ngược file nhận nhầm 29 lệnh thành 29 lượt — mà **ghi thì vẫn báo
   thành công**. Lồng vào `{"loai": "lenh", "lenh": …}` là hết.
2. **"chưa có số" bị đọc thành "so xong thấy không đạt"** — `NaN` hiện ra là `= —, không < 7.00`,
   nghe như một phép so thất bại. Hai chuyện rất khác nhau lúc debug, giờ tách hẳn thành
   `"… chưa có dữ liệu"`.
3. **Vân tay chỉ hash các KHỐI**, không hash cạnh và tham số — hai sơ đồ cùng bộ khối mà nối
   khác nhau lại ra cùng vân tay, tức "so hai lần chạy" sẽ nói "sơ đồ không đổi" trong khi nó đã
   đổi hẳn. Giờ hash cả cạnh lẫn bảng tham số, và vẫn bỏ `pos` (kéo khối không đổi logic).

### 12.15 ✅ Giao diện tester — đã chạy thật trong cửa sổ

```
 thanh công cụ   ⚙ ▶Chạy │ ⏮ ◀ ▶ ▶ ⏭  delay 60ms │ 🔍+ 🔍− ✛ Nến▾ M5▾ │ 2025-01-02 12:45
 dải tóm tắt     550 lệnh · 99T/289B · thắng 25.5% · tổng −9.5R · vốn 9966.93 · nến mơ hồ 0
 ┌──────────────────────────── chart ──────────────────────┬─── bảng số liệu ───┐
 │  nến M5 · CHỈ vẽ lệnh · crosshair                        │ toán hạng đang dùng│
 │  ▲──────▼  lệnh đã xong (hai mũi tên + vạch nối)         │ vùng nén (engine)  │
 │  ▲────    lệnh đang sống                                 │ tài khoản          │
 │  ┄┄┄┄┄┄   lệnh chờ: 3 đường entry · TP · SL              │ lệnh đang sống     │
 ├──────────────────────────── nhật ký (ảo hoá) ────────────┴────────────────────┤
 │ 01-02 12:40 MANAGE L-0003 [1]→[1B]→[1B.1] sửa L-0003 · Dời SL về hoà vốn …    │
 └───────────────────────────────────────────────────────────────────────────────┘
```

**Ba vùng đọc CÙNG MỘT con trỏ `j`** (chỉ số nến M1), nên chúng không thể nói khác nhau. Xem thì
trượt liên tục, debug thì bấm một dòng nhật ký để nhảy mốc — cùng một con trỏ, hai cách di chuyển.

**Đã đối chiếu bằng mắt trên dữ liệu thật**, đúng cái mà bản phản biện lo nhất: bấm dòng
`MANAGE L-0003 · Dời SL về hoà vốn` thì bảng phải hiện `L-0003` gắn chấm *hoà vốn*, `SL = giá vào
= 2643.067`, và `Vùng này đã sinh lệnh = đúng`. **Bảng và nhật ký khớp nhau**, vì bảng dựng từ
CỘT đã ghi lúc chạy chứ không hỏi lại sổ lệnh.

**Ba chi tiết đáng ghi:**

- **Chart nhận đúng `{nen, lenh}`** và không có đường nào chạm tới bảng số liệu — luật "tuyệt đối
  không indicator trên chart" được ép bằng KIỂU DỮ LIỆU, muốn vi phạm phải sửa chữ ký hàm.
- **Gộp M1 → khung vẽ làm ở JS, cố ý và có giới hạn.** Python vẫn là nguồn sự thật cho mọi con số
  đi vào QUYẾT ĐỊNH (`tinh_toan.gop`); JS chỉ gộp OHLC để VẼ. Nhờ vậy kéo con trỏ trong một nến M5
  thì cây nến cuối LỚN DẦN mà không phải hỏi Python 20 lần một giây.
- **Nhật ký ảo hoá tự viết ~40 dòng**, chiều cao dòng cố định (hằng `CAO` trong `Journey.tsx` PHẢI
  khớp `.nk-dong` trong `app.css`). 135.000 dòng đổ thẳng vào DOM là treo hẳn WebView2.

**Một lỗi bố cục bắt được lúc soi ảnh:** bảng "Lệnh đang sống" thiếu `table-layout: fixed` nên bốn
cột số dính liền thành `2643.0672643.0672647.8181.19` — đọc ra một con số vô nghĩa, mà đây lại
đúng là bảng người dùng nhìn để đánh giá. Nhãn "hoà vốn" cũng đổi thành một CHẤM: thêm một chữ
nữa trên hàng là vỡ cả bảng, còn thông tin thì rê chuột vẫn đọc được.

### 12.16 ⭐ PHÁT LẠI — sửa một hiểu sai của tôi

Bản đầu tôi dựng một **trình xem lịch sử**: mở ra là mọi lệnh đã vẽ sẵn đủ hình hài, con trỏ thả
vào giữa. Nhìn thì có vẻ xong. Nhưng người dùng nói thẳng: *"tín hiệu pending, tín hiệu vào vì bạn
vẽ sẵn hết rồi nên tôi cũng không kiểm tra được"* — và đúng.

> **Cốt lõi là KHOẢNH KHẮC**: lệnh chờ hiện ra, giá bò tới, khớp, SL dời về hoà vốn, chốt — với
> nhật ký tự chạy và chỉ báo nhảy số cùng nhịp. Vẽ sẵn là giết đúng thứ đó.

**Vòng đời giờ là:** bấm ▶ ở cửa sổ vẽ → **thanh tiến trình** (backtest chạy trên luồng nền) →
phát lại **từ đầu**, nến hình thành từng cây.

| Việc | Cách làm |
|---|---|
| Nến lớn dần | `series.update()` mỗi nhịp M1 — cây nến khung hiển thị phình ra qua 5 nhịp |
| Trục thời gian · kéo ngang · zoom | `lightweight-charts` của TradingView |
| Lệnh hiện đúng lúc | vẽ theo **trạng thái TẠI CON TRỎ**, không phải trạng thái cuối |
| Nhật ký sống | dòng nảy lên đúng nhịp nó xảy ra, tự cuộn khi đang phát |
| Nhảy tới sự kiện | `test_luot_ke` — không ai xem hết 71.000 nến buồn tẻ để đợi một lệnh |
| Tốc độ | 0,25× → 16× |

**Dùng thư viện ngoài, có cân nhắc.** `lightweight-charts` là dependency đầu tiên ngoài React và
React Flow. Ba thứ thiếu — trục thời gian, kéo ngang, zoom — đều là bài đã có lời giải; tự viết
lại là ~400 dòng để đổi lấy một bản kém hơn. Bundle tăng 583 KB (gzip 189 KB), chấp nhận được.

**KÉO THEO LÔ, không hỏi từng khung hình.** Phát ở 60 ms/nhịp mà mỗi nhịp gọi cầu nối hai lần là
~33 lời gọi/giây; `evaluate_js` đồng bộ và payload mã hoá hai lần, nên phát sẽ giật — mà nhịp đều
mới là thứ quan trọng nhất khi xem nến hình thành. `test_doan(j0, 300)` mang đủ mọi thứ ba vùng
cần cho 300 nhịp: **9 ms, 171 KB**. Lô kế nạp trước khi dùng hết 2/3.

**Ba lỗi bắt được lúc soi ảnh chạy thật:**

1. **Chart lộ tương lai TRONG một lô.** Nó vẽ lệnh theo `trang_thai` cuối cùng, mà lô mang cả sự
   kiện còn ở tương lai (tới 300 nhịp = 5 giờ) — nên bảng nói "L-0006 đang sống, −0,81R" trong khi
   chart đã vẽ nó đóng ở −1,00R. Đúng cái bệnh "vẽ sẵn" vừa chữa, chỉ nhỏ hơn. Giờ chart nhận
   `tBayGio` và tự suy trạng thái tại đó.
2. **Nhật ký dựng lại 400 dòng mỗi nhịp** kéo nhịp phát từ 60 ms xuống ~190 ms. Chỉ dựng lại khi
   CÓ dòng mới — mà lượt mới thì 5 nhịp mới có một lần.
3. **Cài đặt bị JS nhớ** từ lúc mở cửa sổ (xem §12.11).

### 12.17 BẢNG MÀU CỦA CHART — ba tầng, ba nghĩa

Bản trước có **ba thứ dùng chung một cặp màu**: nến xanh/đỏ, hướng lệnh xanh/đỏ, lãi/lỗ xanh/đỏ.
Một cặp màu mang ba nghĩa thì chẳng còn nghĩa nào — người dùng nói thẳng *"màu xanh đỏ đang khó
nhìn vì nến cũng cùng màu đó"*.

| Tầng | Màu | Nghĩa DUY NHẤT |
|---|---|---|
| Nến | **xám** — tăng rỗng viền sáng, giảm đặc tối | bối cảnh. Giá là thứ XẢY RA |
| Mức lệnh (vào · SL · TP) | **cam** `#ffa657` | "chỗ TA đặt" |
| Kết quả (thắng/thua) | **xanh / đỏ** | và chỉ có nghĩa này |

Làm nến im đi không phải để đẹp: để lúc không có lệnh thì chart lặng như tờ, lúc có lệnh thì mắt
bị kéo tới ngay. **Hướng mua/bán không dùng màu nữa — dùng HÌNH:** ▲ mua, ▼ bán.

| Trạng thái | Vẽ gì |
|---|---|
| Chờ | 3 đoạn cam: vào (gạch đứt) · TP, SL (chấm) — **chỉ trong quãng lệnh sống** |
| Khớp | ▲/▼ cam tại nến khớp · SL, TP cam vẫn treo |
| Đóng | **vạch nối vào→ra** xanh/đỏ + ô vuông `L-0007 −1.00R` |
| Huỷ (nén tan) | `✕` **xám** — không thắng không thua, không đụng màu kết quả |

**Hai thứ sửa được nhờ đổi `createPriceLine` → `LineSeries`:**

1. **Đường không còn kéo suốt chart.** `PriceLine` luôn full-width, nên ba đường của một lệnh đặt
   lúc 09:00 cũng chạy ngược về 06:00 — quãng nó chưa tồn tại. Nhiễu, và nói dối.
2. **Vạch nối vào→ra quay lại** (§12.10 có, bản lightweight-charts đầu làm rơi). Nó chính là chỗ
   mang màu kết quả: dốc lên xanh, dốc xuống đỏ, nằm ngang = hoà vốn.

**Đường SL vẽ theo LỊCH SỬ**, dựng từ chính nhật ký (`lenh_sua`), nên lúc `Dời SL về hoà vốn` chạy
thì nó **nhảy bậc** ngay trên chart — khoảnh khắc đáng kiểm chứng nhất, mà bản trước chỉ vẽ SL
cuối cùng nên nó tàng hình. ⚠ Điểm đầu KHÔNG được lấy `Lenh.sl`: đó là SL HIỆN TẠI, đã bị mọi lần
dời ghi đè — lấy nó làm điểm đầu là ra một đường phẳng và cái bậc biến mất. Nay điểm đầu lấy thẳng
từ bản ghi `lenh_dat` trong nhật ký (§12.9d), chính xác và dùng được cho cả TP.

### 4.5 ✅ THÊM KHỐI TỪ CHIẾN LƯỢC KHÁC — nhập chồng, không thay

`Mở ▾ → Thêm khối từ chiến lược khác…` (và mục cùng tên trong menu File). Chữ **thêm** để phân
biệt hẳn với *"Mở chiến lược (thay toàn bộ)"* ngay bên trên — hai thứ này mà lẫn nhau thì một cú
bấm nhầm xoá sạch sơ đồ đang làm dở.

**Nhập = DÁN từ file.** Máy móc đã có sẵn: `Ctrl+V` vốn cấp id mới, giữ nối *giữa những khối được
chép*, thả cả cụm giữ nguyên khoảng cách tương đối, chọn sẵn cả cụm, và `chup()` trước nên **một
Ctrl+Z hoàn tác cả mẻ**. Đã tách phần đó ra thành `thaCum(buoc, canh, taiDay, ts)` dùng chung —
viết hai lần thì sớm muộn một bên quên remap id hoặc quên `chup()`.

**"Không đánh số" không phải thứ phải cài — nó là HỆ QUẢ.** Số do Python tính bằng phép duyệt từ
khối Bắt đầu; khối vừa nhập chưa có đường nối nào dẫn vào nên nằm ngoài phép duyệt và hiện `–`.
Kèm theo, bảng Vấn đề gọi chúng là *"không bao giờ chạy tới"* ở mức **cảnh báo** (không phải lỗi),
nên ▶ Chạy vẫn bấm được. Nối vào là số hiện ra ngay.

**Hai thứ bị lọc, cả hai đều là luật:**

- **Bỏ khối Bắt đầu của nguồn** — sơ đồ đang mở đã có một cái, hai khối Bắt đầu là sơ đồ hỏng.
- **Chỉ nhập CÙNG TAB** — toán hạng nhóm "Lệnh này" chỉ tồn tại ở Manage, nên bê một khối Manage
  sang Entry là tạo ra khối không soát nổi. Đây là luật, không phải làm cho gọn.

**⚠ THAM SỐ PHẢI ĐI THEO.** Khối tham chiếu tham số bằng **TÊN**. Nhập một khối dùng
`nguong_nen_bps` vào chiến lược không có tham số đó thì khối trông vẫn bình thường trên canvas,
nhưng bấm ▶ mới ném `"Bảng tham số thiếu nguong_nen_bps"` — và không ai đoán ra vì sao. Nên
`import_steps` trả kèm đúng những tham số đám khối đó **thật sự đọc**, quét bằng chính
`core._tham_so_dang_dung` mà validator dùng (một `doc` giả chỉ chứa đám khối đó) — viết bộ quét
thứ hai là sớm muộn hai bên hiểu khác nhau.

> **Tên ĐÃ CÓ thì GIỮ NGUYÊN giá trị hiện tại, không đè.** Đè lên là lặng lẽ đổi hành vi của cả
> chiến lược đang làm dở chỉ vì vừa nhập một khối. Nhật ký ghi rõ đã giữ cái nào và nguồn ghi bao
> nhiêu.

#### 4.5b ⚠ Lỗi có sẵn của Ctrl+V, lộ ra nhờ tính năng này

`clone_steps` dựng thẻ bằng `_the_buoc(s)` — **không có bảng tham số**, nên thẻ ghi
`nguong_nen_bps = ?`. Ctrl+V dính từ đầu, chỉ ít ai để ý vì thường dán ngay trong cùng một sơ đồ
và mắt đã quen con số ở khối gốc. Nhập từ file thì cả cụm 6 khối hiện `?` — trông như hỏng hẳn.

Sửa: `clone_steps(steps, tham_so)`. Với lần **nhập** phải truyền bảng **ĐÃ GỘP**, vì tham số vừa
thêm chưa nằm trong `thamSo` của lần render đang chạy — gộp trước, thả cụm sau.

### 4.6 ✅ MÀU KHỐI THEO MỤC ĐÍCH

Trước đây `dai-mau` chỉ có hai màu: xanh cho Bắt đầu, **cam cho MỌI khối hành động** — nhìn xa thì
Kiểm tra ĐK, Vào lệnh, Sửa lệnh giống hệt nhau.

`api._mau_khoi(st)` gắn vào thẻ một **khoá ngữ nghĩa**, không phải mã màu: `start · hoi · mua ·
ban · sua`. Suy từ `type` + `huong` — phạm trù của chính app, không phải khái niệm riêng của một
chiến lược, nên chiến lược nào sau này cũng ra màu đúng. Giao diện ánh xạ khoá → biến CSS, nên đổi
bảng màu là việc của CSS.

| khối | màu | vì sao |
|---|---|---|
| Bắt đầu | xám `--action` | ĐIỂM NEO, không phải hành động |
| Kiểm tra ĐK | lam `--khoi-hoi` | một câu hỏi |
| Vào lệnh · Mua | xanh `--ok` + ▲ | |
| Vào lệnh · Bán | đỏ `--err` + ▼ | |
| Sửa lệnh | tím `--khoi-sua` | không đụng `--warn`/`--accent` đã có nghĩa khác |

**Khối Bắt đầu phải bỏ màu xanh.** `--start` và `--ok` trùng đúng một mã `#4ec96a`, nên để khối Mua
màu xanh mà giữ nguyên Bắt đầu thì hai loại khối nhìn y hệt nhau. Trả xanh về đúng MỘT nghĩa: mua.

**Nền dải tiêu đề nhuộm 10% mới là thứ quyết định, không phải cái thanh.** Ở mức thu phóng 67% —
mức hay dùng để nhìn cả sơ đồ — thanh 3px chỉ còn 2px và gần như biến mất; một dải nhuộm thì vẫn
quét mắt ra được. Thanh cũng được kéo cao hết dải tiêu đề thay vì 15px giữa chừng.

**Hướng dùng HÌNH ▲/▼ chứ không chỉ dùng màu** — cùng ngôn ngữ với chart (§12.17), và đọc được cả
khi mù màu.

Cái lợi kèm theo: cam đang mang hai nghĩa cùng lúc — "khối hành động" và "đang chọn · số thứ tự".
Đẩy khối hành động sang màu riêng thì **cam chỉ còn nghĩa *của ta · đang chọn***, viền chọn nổi hẳn.

Thân khối, viền, phông chữ, huy hiệu: **không đổi một pixel**.

### 12.23 ⛔ ĐÃ BỎ (D-09) — ▶ Chạy tự tải phần nến còn thiếu

Từng có: thiếu nến thì ▶ tự tải đúng phần thiếu rồi chạy tiếp. Đã bỏ cùng toàn bộ đường tải
nến (§17) — app chỉ phục vụ QuantConnect, mà dữ liệu của QC không được mang về máy. Hai bài học
của mục này vẫn giữ trong `api._kiem_du_nen`: khoảng rỗng phải chặn ngay (§13.4), và thiếu
**phần đầu** khoảng thì DỪNG — chạy tiếp trên khoảng ngắn hơn là người dùng tưởng mình thử từ
2015 trong khi thật ra từ 2016.

### 8.4 ⚠ LỖI: ba nút hộp thoại file đều chết vì một hằng số sai kiểu

*"nút mở từ file khác, duyệt từ file khác đang không dùng được."*

`_LOC` khai là **tuple** `("Chiến lược Cat_Studio (*.json)", "*.json")`, rồi truyền
`file_types=(self._LOC,)`. pywebview đòi mỗi bộ lọc là một **CHUỖI** đúng dạng `Mô tả (*.đuôi)`
và tự tách lấy đuôi — đưa tuple vào thì `parse_file_type` ném `TypeError: expected string, got
'tuple'` **ngay, trước cả khi hộp thoại kịp mở**.

Một hằng số sai kiểu giết **ba** nút cùng lúc, vì cả ba dùng chung nó: *Mở từ file khác…* ·
*Duyệt file khác…* (trong hộp chọn chiến lược) · *Lưu ra file khác…*.

**Vì sao im lặng suốt:** `_bat_loi` bắt gọn ngoại lệ thành `{ok: false, error: …}`, và JS có báo —
nhưng báo vào **bảng Nhật ký ở dưới**, chỗ người dùng đang không mở. Bấm nút thì thấy *không có gì
xảy ra*. Lỗi được xử lý đúng mà vẫn vô hình: chỗ báo lỗi phải nằm nơi người ta đang nhìn.

Sửa: `_LOC` thành một chuỗi. Nhân tiện đổi `webview.OPEN_DIALOG`/`SAVE_DIALOG` sang
`webview.FileDialog.OPEN`/`.SAVE` — pywebview đã in cảnh báo *"will be removed in a future
version"* ngay trên stderr, cùng giá trị 10/30.

Đã bấm thật cả hai: hộp `Open` và hộp `Save As` đều hiện ra, Esc huỷ xong app vẫn chạy.

### 13.0 ✅ ĐỢT SOÁT TRƯỚC ĐÓNG GÓI — 7 chỗ đã sửa

Soát 5 hướng song song (logic sơ đồ · đúng số · dữ liệu · cầu nối · phòng thủ & đóng gói), mỗi
phát hiện nặng qua một vòng phản biện. 25 phát hiện thô → 8 cái nặng nhất đưa đi phản biện → 8
sống sót. Hai cái nặng nhất tự tái hiện lại bằng tay trước khi sửa.

#### ⚠ 13.0a Toán hạng giá — VÁ HỤT LẦN ĐẦU, nay mới xong

§12.13e-bis ghi là "ĐÃ SỬA". **Sai: mới làm 2 trong 3 bước.** Đã dựng đúng cột theo khung
(`_xin_cot_gia`) và đúng khoá (`khoa`) — nhưng **quên sửa chỗ ĐỌC**: `_lay_toan_hang` vẫn gọi
`ctx.gia_nen`, mà `gia_nen` đọc thẳng `ct.nen5`. Cột dựng ra không ai dùng. Thuốc pha xong không
ai uống.

Đo lại trên một tháng thật: **66,5 % số nến trả sai số**, lệch tối đa 11,37 — chứ không phải
3,48 % như §12.13e-bis ghi, vì lần đó tôi đo *chênh lệch giữa hai cột*, không đo *thứ cổng thật sự
đọc*. Và có **hai lỗi chồng nhau**: sai mảng, cộng thêm sai quy ước `shift` (`gia_nen` hiểu là lùi
`shift` nến, `doc_cot` hiểu `nến[1]` là lệch 0).

Sửa: gọi **y hệt đường chỉ báo** — `ct.doc_cot(o, ctx.i, o.get("shift", 0))`. Cùng một dạng gọi thì
hai vế của một cổng mới cùng quy ước. KHÔNG đụng `ctx.gia_nen`: `kho/engine_d02` dùng nó nuôi vùng
nén, mà vùng nén sống trên trục quyết định nên đọc `nen5` ở đó là ĐÚNG.

**Số thật đổi theo:** 548 lệnh · −7,50 R · DD 0,79 % → **547 lệnh · −10,50 R · DD 0,91 %**. Bảng
§12.13e là đo trên mã còn lỗi.

**Vì sao 9/9 vẫn xanh suốt:** không bài nào soát GIÁ TRỊ LÚC CHẠY của một toán hạng giá —
`test_doi_chieu_d02` cố ý chỉ soát *tờ khai* (docstring của nó ghi rõ), còn `test_bo_chay` chưa
chạm tới. Đã thêm mục 7 vào `test_bo_chay`: tự gộp M15 từ mảng M1 thô rồi tra tay nến M15 **đã
đóng** gần nhất — một sự thật ĐỘC LẬP, không mượn gì của bộ chạy. Kèm một phép chốt "giá trị phải
KHÁC close M5 ở phần lớn nến", vì nếu ai đó lại làm cả hai đường cùng đọc `nen5` thì phép so đầu
vẫn khớp.

#### ⚠ 13.0b drawdown_pt bỏ sót lệnh do khối "Đóng hẳn" đóng

`ghi_tien` là closure trong `chay()`, `_sua_lenh` là hàm MODULE nên với không tới. Nhánh `dong_han`
đóng lệnh xong không ghi tiền → `drawdown_pt` **lúc chạy** đọc 0 % trong khi sụt giảm thật đã mấy
chục phần trăm. Toán hạng đó chính là thứ người ta dùng làm **cầu dao** ("sụt giảm > 10 % thì ngừng
vào lệnh") — cầu dao chết im lặng. Bảng thống kê cuối vẫn đúng (`_thong_ke` tự duyệt lại sổ lệnh),
nên hai nơi nói hai con số khác nhau.

Sửa: gắn `ct.ghi_tien = ghi_tien`, gọi trong nhánh `dong_han`. Sơ đồ mẫu dùng `hoa_von`/`huy_cho`
nên bộ số của nó không bị mục này ảnh hưởng.

⚠ Bài kiểm đầu tiên tôi viết **BỎ LỌT** con bọ này: nó dùng lại kịch bản giá phẳng 110, nên cả hai
đường cùng ra 0 % và phép so khớp một cách vô nghĩa. Kịch bản phải **có lỗ thật** (vốn nhỏ, lot
lớn, giá rơi đều) thì hai đường mới buộc phải nói cùng một con số khác 0.

#### 13.0c Ghi nến NGUYÊN TỬ + chốt chặn file cụt

`np.save` ghi thẳng lên file đích, tức **cắt cụt bộ cũ rồi mới ghi lại**. Ngắt giữa chừng để lại
`.npy` cụt còn `.json` meta vẫn mô tả bộ đã mất — rồi `doc()` lặng lẽ trả mảng rỗng trong khi
`khoang_thieu()` (chỉ nhìn meta) khẳng định "đủ rồi", nên app **không bao giờ tải lại**. Tự khoá vào
trạng thái chết; đo được 20/20 lần khi kill đúng lúc `np.save`.

Hai miếng vá, cùng một file, không đổi định dạng:
`_ghi_nguyen_tu` (ghi `.tmp` → `fsync` → `os.replace`, đổi tên trên NTFS là nguyên tử) và
`file_du(symbol, m)` — một lệnh `stat` so kích thước với `so_nen × itemsize`, thiếu thì coi như
chưa có gì và tải lại. Cái thứ hai còn tự chữa những file ĐÃ hỏng sẵn từ trước.

Tách `file_du` ra thành hàm riêng thay vì viết thẳng trong `khoang_thieu`: bộ kiểm mục 2 cố ý thay
tạm `doc_meta` để soát riêng phần số học khoảng, không đụng đĩa — có hàm riêng thì nó thay tạm được
y như vậy.

#### 13.0d Bốn chỗ còn lại

- **Tên thiết bị Windows** (`CON`/`PRN`/`AUX`/`NUL`/`COM1-9`/`LPT1-9`) — `NUL.json` bị ánh xạ vào hố
  đen ở BẤT KỲ thư mục nào: lưu báo THÀNH CÔNG, `os.path.exists` trả True, mà đĩa không có file;
  `AUX` còn treo cứng lúc đọc lại. Thêm gạch dưới. Giữ tính lũy đẳng để tên lấy từ `liet_ke` đưa
  ngược vào không cộng dồn gạch. Đáng lo vì **"con" là từ tiếng Việt rất hay gặp**.
- **Bỏ `limit` khỏi `LOAI_LENH`** — giao diện cho chọn "Chờ Limit" mà `khop_lenh` không đọc trường
  `loai` một lần nào, và `_vao_lenh` đặt Buy Limit CAO HƠN giá thị trường. Bỏ chứ không cài thêm:
  cài là thêm tính năng, mà một ô chọn lặng lẽ làm việc khác mới là thứ phải dọn.
- **Chặn file schema mới hơn** — `normalize_action` trả None cho `type` lạ và `_chuan_so_do` lọc
  `if x`, nên khối BIẾN MẤT kéo theo cả dây, chuỗi bị cắt đôi, rồi Ctrl+S ghi đè vĩnh viễn.
  `validate_actions` có sẵn câu cảnh báo cho tình huống này nhưng không bao giờ hiện được, vì
  normalize đã xoá khối trước khi validator nhìn thấy. Chặn ở đầu `normalize_process`.
- **Tham số trùng tên** — `bang_tham_so` (dict comprehension) lấy dòng CUỐI, `normalize_tham_so`
  giữ dòng ĐẦU: canvas ghi một đằng, bộ chạy chạy một nẻo, **ngay trong cùng một lần chạy**.
  `validate_process` trước đây gom tên vào một `set` nên nuốt mất chuyện đó. Nay báo mức **error**
  (đủ để chặn ▶ Chạy) và nút Lưu của hộp Tham số bị khoá khi còn trùng.

#### 13.0e Dọn nốt — 6 mục "để sau", làm luôn

- **`lich_su.liet_ke()` nhớ tạm bản gọn theo `ma`.** Trước đây mỗi lần gọi phải đọc và parse TOÀN
  BỘ mọi mục (~69 KB/mục, riêng đường vốn 62 KB) mà danh sách không dùng tới, trong khi mỗi lần
  bấm ▶ gọi 2-3 lượt. Đo được **40 mục: 233 ms → 0,5 ms** (nhanh hơn ~450×). An toàn vì `lich_su`
  là nơi DUY NHẤT ghi/xoá file lịch sử, và cả `_ghi_file` lẫn `xoa` đều dọn bộ nhớ tạm; `liet_ke`
  còn tự bỏ mục nào file đã biến mất ngoài app.
- **Mã mục lịch sử không đè nhau nữa.** Mốc GIÂY thì hai lần chạy khép trong cùng một giây ghi đè
  nhau. ⚠ Bản vá đầu của tôi (thêm phần trăm giây) **không sửa được gì** — 20 lần gọi liên tiếp
  vẫn ra 1 mã, vì cả 20 rơi vào cùng một phần trăm giây. Đừng đoán độ phân giải đồng hồ cho đủ
  mịn: cứ HỎI ĐĨA, trùng thì thêm hậu tố. Khử hẳn, không phải giảm xác suất.
- **`lich_su._gon` dùng `.get` cho mọi khoá.** `liet_ke` chỉ canh `m.get("ma")`, nên một mục thiếu
  `t` ném KeyError và kéo sập CẢ danh sách — mất luôn những mục lành.
- **Lãi nổi của lệnh BÁN đo bằng Ask, không phải Bid** (`_gia_thoat`). Đo bằng Bid là báo lãi cao
  hơn thật đúng một spread; với XAUUSD spread 37 điểm thì đủ để một cổng "lãi ≥ 1R" khớp sớm hơn
  một nhịp, và bảng số liệu hiện một con số mà đóng lệnh ra không được. Gom vào MỘT hàm cho ba chỗ
  gọi (toán hạng · bảng số liệu · hàng lệnh sống) khỏi nói ba con số khác nhau. `Lenh.lai_R` vẫn cố
  ý không biết spread là gì — `so_lenh` là mô hình thuần, quy đổi thuộc về chỗ gọi.
- **`ghi_cai_dat` NÉM lỗi thay vì nuốt.** Trước đây `try/except: pass` rồi vẫn `return s`, nên đĩa
  đầy hoặc mất quyền thì nơi gọi tưởng đã lưu; lần mở sau cài đặt lặng lẽ về mặc định.
- **Ghi JSON nguyên tử cho cài đặt · template · lịch sử** (`luu_tru.ghi_json_nguyen_tu`), cùng cách
  với nến ở 13.0c. Ngắt giữa lúc ghi thì mất bản MỚI, không mất bản CŨ.

#### ✅ 13.0f Sơ đồ mẫu phải có ID CỐ ĐỊNH

Phát hiện lúc kiểm bản dọn, không nằm trong danh sách soát: mở "Sơ đồ mẫu Compress" ba lần thì lịch
sử đẻ **ba dòng trùng hệt nhau**, và `so_hai_lan` lần nào cũng nói *"sơ đồ ĐÃ ĐỔI"*.

`_van_tay` băm cả `id` khối, mà `_so_do_mau()` sinh id ngẫu nhiên mỗi lần gọi → cùng một logic ra
ba vân tay khác nhau.

⚠ **Suýt sửa nhầm chỗ.** Tôi định đi chuẩn hoá đồ thị để bỏ `id` khỏi vân tay — việc lớn, và chạm
vào chuyện "thế nào là cùng một chiến lược". Nhìn lại thì lỗi không nằm ở vân tay: **sơ đồ mẫu là
một HẰNG SỐ, nên nó phải ra y hệt nhau mỗi lần mở.** Sinh id ngẫu nhiên cho một hằng số mới là chỗ
bất thường. Sửa đúng chỗ đó: 4 dòng trong `_so_do_mau`, không đụng `_van_tay`.

Id chỉ cần duy nhất TRONG MỘT tài liệu nên đặt cứng hoàn toàn an toàn, và nhập sơ đồ mẫu vào một sơ
đồ khác thì `clone_steps` vẫn cấp id mới như thường.

Kiểm: 3 lần mở lại và chạy → **1 mục lịch sử**, `so_hai_lan` trả *"y hệt"*. Luồng lưu/mở file vốn
đã đúng từ trước (ids nằm trong file), đã kiểm lại luôn.

### 13.2 ✅ Dọn thư mục gốc

- **`settings.json` ở gốc: xoá.** Của bản cũ, `luu_tru.di_cu()` đã chuyển sang
  `du_lieu/cai_dat.json` từ lâu và từ đó nó nằm không — nhưng ai đọc repo vẫn tưởng nó có tác dụng.
- **`logo/` : xoá.** Trùng byte-for-byte với `assets/` (chỉ khác tên file), không một chỗ nào gọi
  tới. `assets/logo.ico` thì `tools/tao_shortcut.ps1` đang dùng thật nên giữ.
- **`tai_lieu/`**: `core.md` + `D02_Compress_ban_giao.md`. `README.md` ở lại gốc theo lệ.
- **Mọi sản phẩm build vào `dist/`**, kể cả bản `.zip` phát hành — thư mục gốc không giữ thứ gì
  sinh ra từ lệnh build. `build/` thì `tools/dong_goi.bat` tự xoá sau khi nén xong.

#### 13.3 ✅ Gom lõi vào gói `cat_studio/`

Thư mục gốc còn đúng **một file `.py`: `app_web.py`** — điểm khởi động. Nhìn vào gốc là thấy ngay
"chạy cái gì"; "gồm những gì" thì mở gói ra xem.

11 module + `kho/` vào `cat_studio/`, và **import trong gói chuyển sang tương đối** (`from . import
core`, `kho/` dùng `from .. import so_lenh`). Ngoài gói — `app_web.py` và 9 bài kiểm — dùng
`from cat_studio import …`.

⚠ **Chỗ vỡ mà đổi tên import không lộ ra:** `luu_tru` xác định gốc dự án bằng
`dirname(__file__)`. File này giờ nằm TRONG gói, nên nó trả về thư mục gói chứ không phải gốc —
`du_lieu/` bị đẻ vào trong `cat_studio/`, và `webui/dist` tìm không thấy. Thêm một bậc `..`
(`_GOC_MA_NGUON`) là xong, nhưng nếu chỉ chạy `import` để kiểm thì không bao giờ thấy: phải chạy
thật mới lộ. Đây là loại lỗi mà "gom file cho gọn" hay kéo theo.

`__init__.py` cố ý **không re-export gì**: `from cat_studio import core` phải nạp đúng một module,
không kéo cả cây. Nạp `api` là kéo theo numpy và cả lớp cửa sổ, mà `tests/test_danh_so` chỉ cần
`core`.

`.spec` chỉ đổi `hiddenimports` thành `cat_studio.kho.*`; `tools/*.bat` không phải sửa gì vì tất cả
đều trỏ vào `app_web.py` ở gốc.

Kiểm: **9/9 bài qua**, đóng gói lại, giải nén sang thư mục khác chạy ra **547 lệnh · −10,50 R ·
DD 0,91 % · vốn cuối 9955,04** — trùng từng con số với trước khi gom.

### 13.4 ⚠ CHUỖI RỖNG bị hiểu là "đã đủ" — máy mới bấm ▶ nhận câu lỗi sai bệnh

Cài bản đóng gói lên máy mới, bấm ▶, nhận:

```
RuntimeError: Không có nến nào cho XAUUSD trong khoảng này.
Kiểm tra lại mã symbol và khoảng From→To ở Cài đặt → Strategy Test.
```

Câu lỗi đổ tội cho **mã symbol**, trong khi symbol hoàn toàn đúng. Chuỗi hỏng:

1. Mặc định `test.tu` và `test.den` là **chuỗi rỗng**;
2. `thoi_diem("")` trả `None`;
3. `khoang_thieu` gặp `None` thì trả `[]` — **mà `[]` nghĩa là "đã đủ, khỏi tải"**;
4. `_tai_neu_thieu` về ngay, KHÔNG tải gì;
5. `doc()` trả mảng rỗng → ném câu lỗi nói về symbol.

Một giá trị rỗng đi qua bốn tầng rồi biến thành một câu lỗi nói về chuyện khác hẳn.

⚠ **Đợt soát §13.0 ĐÃ TÌM RA lỗi này** — nguyên văn *"máy trắng bấm ▶ lần đầu: tính năng tự-tải-nến
KHÔNG chạy, và lỗi đổ tội nhầm cho mã symbol"*, xếp mức `vua`. Nó nằm trong 25 phát hiện nhưng rơi
khỏi danh sách 7 mục phải sửa, và tôi không rà lại. Tìm ra rồi vẫn để lọt thì công soát thành công cốc.

**Hai chỗ sửa** (chỗ thứ ba — một nút nối thử sàn trong Cài đặt — đã bỏ cùng MT5, §17):

- **Mặc định khoảng = một năm gần nhất, tính theo HÔM NAY** (`_khoang_mac_dinh()`), không ghi cứng
  một mốc — ghi cứng thì sang năm người mới cài thấy một khoảng đã lỗi thời.
- **Chặn khoảng rỗng ngay ở `_tai_neu_thieu`** (nay là `_kiem_du_nen`), nói đúng bệnh: *"Chưa
  đặt khoảng thời gian để chạy. Mở Cài đặt → Strategy Test và điền hai ô Từ / Đến."*
### 13.1 ✅ ĐÓNG GÓI — đã build và chạy thật

```bat
tools\dong_goi.bat
```

**MỘT lệnh, sáu bước** — theo đúng nếp `tools/build.bat` của Auto_Clicker, vì nếp đó đã trả lời sẵn
mấy câu hỏi mà làm tay hay quên:

1. đóng app nếu đang chạy (không thì PyInstaller không ghi đè được `.exe`);
2. build giao diện web — quên bước này là gói ra một cửa sổ trắng;
3. **chạy bộ kiểm; đỏ thì DỪNG, không đóng gói** — thêm so với Auto_Clicker;
4. PyInstaller theo `Cat_Studio.spec`;
5. kèm `DOC-TRUOC-KHI-CHAY.txt` vào trong gói;
6. nén `Cat_Studio-windows.zip` rồi **xoá `build/`** — thư mục đó chỉ là chỗ làm việc trung gian
   của PyInstaller, để lại chỉ tổ rác thư mục gốc.

Dùng `.venv\Scripts\python.exe` chứ không Python global — cùng lý do Auto_Clicker ghi: gói
`quantconnect-stubs` ở global chiếm namespace `Microsoft`. Mã nguồn đã tự chữa được
(`_uu_tien_namespace_dotnet`, §10), nhưng đóng gói bằng môi trường sạch thì gói nhẹ hơn và không
kéo theo rác.

Ra `dist/Cat_Studio/` — **66 MB · 211 file** — và `Cat_Studio-windows.zip` để đưa sang máy khác.

**Chọn `onedir` chứ không `onefile`** — quyết định, không phải mặc định. `onefile` giải nén TOÀN BỘ
gói (numpy + cây DLL .NET của pythonnet) vào thư mục tạm ở MỖI lần mở: vài giây chờ
trước khi thấy cửa sổ, lần nào cũng vậy, mà chẳng đổi lại được gì. `onedir` mở gần như tức thì.

**Hai thư mục, không được trộn** — đây là chỗ dễ hỏng nhất và đã tách hẳn thành hai hàm có tên:

| | hàm | khi đóng gói |
|---|---|---|
| Dữ liệu người dùng | `luu_tru.thu_muc_app()` | cạnh `.exe`, sống lâu hơn tiến trình |
| Tài nguyên đi kèm | `luu_tru.thu_muc_goi()` | `sys._MEIPASS`, xoá lúc thoát |

Trộn hai cái là hỏng theo cả hai chiều: để `du_lieu/` trong `_MEIPASS` thì mất sạch sau mỗi lần
chạy; tìm `webui/dist` cạnh `.exe` thì không thấy vì nó nằm trong gói. Trước đây hai chỗ tự ghép
đường dẫn từ `__file__` — nay cùng gọi `luu_tru.trang_giao_dien()`.

**Đã kiểm bằng cách chạy bản đóng gói thật**, không suy luận:

- mở từ thư mục trắng → cửa sổ hiện đủ giao diện, và `du_lieu/` được tạo **cạnh .exe**;
- chép nến vào rồi bấm ▶ → chạy trọn một backtest một năm, ra **547 lệnh · −10,50 R · DD 0,91 % ·
  vốn cuối 9955,04** — **trùng từng con số** với bản chạy từ mã nguồn. Đó mới là bằng chứng gói
  không làm lệch gì, chứ không phải "mở lên thấy cửa sổ là xong".

`console=False` nên mọi lỗi khởi động phải đi qua MessageBox — `app_web` đã làm thế từ trước cho
thiếu .NET / thiếu WebView2 / xung đột namespace. `upx=False`: nén UPX hay bị antivirus báo nhầm,
không đáng đổi lấy vài MB.

### 12.22 ✅ Ba lối vào tester, một hàm

`▶ Chạy` trên ribbon · `File → Mở Strategy Tester` · phím `Ctrl+R`. Cả ba trỏ về **đúng một hàm**
`chay()` — cùng luật với 4 menu tiêu đề (§8): không tạo hành động mới nào cho một lối vào mới, nếu
không hai nơi sớm muộn cũng lệch nhau.

`ContextMenu` nhận thêm trường `phim` để hiện nhãn phím tắt mờ, dạt phải. Nó CHỈ là nhãn — phím
thật vẫn do chỗ nghe bàn phím lo, menu không tự gắn phím nào.

⚠ **`Ctrl+R` bắt buộc `preventDefault()`**: mặc định của Chromium là **nạp lại trang**, tức mất
trắng sơ đồ đang vẽ dở. Chặn nó lại còn là một cái lợi kèm theo. Đã bấm thật để kiểm chứ không
tin suông — cửa sổ tester mở ra và cửa sổ chính vẫn nguyên, không nạp lại.

### 12.21 ✅ LỊCH SỬ CÁC LẦN CHẠY — không lưu kết quả, lưu thứ ĐẺ RA nó

Nút `⏱ Lịch sử` cạnh logo trên thanh tiêu đề tester (`TitleBar` nhận thêm ô cắm `them`).

**Ý chính.** Bộ chạy tất định và một năm mất 2,9 giây, nên một mục lịch sử chỉ cần chứa **đầu vào**
— sơ đồ đã đóng băng + cài đặt + dấu vết dữ liệu nguồn — kèm một **bản tóm tắt** nhỏ để mở ra là
thấy ngay:

| | |
|---|---|
| Lưu cả `KetQua` | riêng nhật ký đã **3,3 MB** một lần chạy |
| Lưu đầu vào + tóm tắt | **~40 KB** |

Mở một mục → tóm tắt hiện **tức thì**. Bấm `▶` → chạy lại 3 giây và ra **nguyên bộ phát lại**
(chart · nhật ký · bảng số liệu · tua đi tua lại), không phải một tấm ảnh chụp chết. Chỉ làm được
thế vì `so_lenh.py` hứa *"chạy lại cùng dữ liệu ra cùng id"* và có bài kiểm cho lời hứa đó. Đã đo:
mở lại mục đã lưu ra đúng **548 lệnh · −7,50 R**, khớp bản gốc từng con số.

**MỀM và ĐÃ LƯU khác nhau ở ĐÚNG MỘT chỗ: có `ten` hay không.**

- `ten = None` → mục mềm, tự ghi mỗi lần bấm ▶, cuốn chiếu khi quá **20**.
- `ten = "…"` → đã lưu, **miễn nhiễm cuốn chiếu**. Cái tên mới là thứ làm nó tìm lại được sau ba
  tháng — `hôm qua 22:41` thì tháng sau chẳng nói lên gì.

Một thư mục, một định dạng, nên `Mở lại` chạy **y hệt nhau** ở cả hai danh sách — không có hai
đường code để lệch nhau. "Lưu" chỉ là ghi một cái tên vào file đã có.

**Chạy lại mà không đổi gì thì KHÔNG đẻ dòng mới.** Cùng vân tay sơ đồ + cùng cài đặt = kết quả
giống hệt (tất định), một dòng nữa mang đúng 0 thông tin. Chỉ dập lại mốc thời gian. `delay_ms` cố
ý **không** nằm trong bộ cài đặt đem so — nó chỉ là tốc độ phát lại, tính nó vào thì lịch sử đầy rác.

**Chỗ cơ chế này có thể nói dối, đã chặn.** `Mở lại` chỉ ra đúng số cũ nếu nến nguồn còn y nguyên.
Mỗi mục ghi `symbol · số nến · nến đầu · nến cuối`; lúc mở, `_soat_nguon` so lại và nếu lệch thì
**từ chối chạy** kèm câu *"dữ liệu nguồn đã đổi (353.129 → 401.664 nến)"* — chứ không lặng lẽ chạy
ra bộ số khác rồi vẫn mang cái tên cũ. Bản tóm tắt thì vẫn còn vĩnh viễn.

**Hai thứ được thêm mà không phải viết mới:**

1. `_tom_tat_chay()` dựng ở **một chỗ** — vừa là thứ tab Thống kê vẽ, vừa là thứ lịch sử cất đi.
   Nên mở mục cũ và xem lần chạy hiện tại đi qua **cùng một đường vẽ**, không có hình dạng thứ hai.
2. `so_hai_lan` giờ **sống qua các phiên**: chưa chạy lần nào trong phiên thì `_tom_tat_lan_truoc`
   lấy mục mới nhất trong lịch sử. Trước đây đóng cửa sổ tester là câu *"so với lần trước thì
   sao"* mất sạch, mà vòng lặp nâng cấp model thì chẳng ai làm gọn trong một phiên.

**Một lỗi `tsc` bắt được, đáng ghi.** `onClick={chay}` — sau khi `chay` nhận thêm tham số `ma` thì
React truyền cả **đối tượng sự kiện** vào đó, và nút `↻ Chạy lại` hoá ra đi *mở lại một mục lịch
sử* với mã là một `MouseEvent`. Phải viết `onClick={() => void chay()}`.

### 12.20 ✅ Tab Thống kê — tổng kết cố định, không tua

Tab thứ hai của **bảng dưới**, cạnh `Nhật ký`, dùng chung thanh kéo và nút gập đã có. Nội dung xếp
**dọc và cuộn được**: khối số → đường vốn → sụt giảm.

**Cố định, không theo con trỏ.** Đây là tổng kết cả lượt chạy, `test_thong_ke()` gọi đúng một lần
lúc mở tab. Ghi rõ **khoảng thật sự có nến** *và* **khoảng đã yêu cầu** trong Cài đặt — hai cái
lệch nhau là chuyện thường, mà đọc số không biết nó tính trên quãng nào thì con số vô nghĩa.

**Đường vốn là VỐN ĐÃ CHỐT**, mỗi nến trục có lệnh đóng một điểm (386 lệnh → 384 điểm cho một
năm). Cố ý KHÔNG vẽ lãi nổi: nó đổi theo từng nến M1 → 353.000 điểm, giật liên tục, và
`drawdown_pt` vốn đã cố tình loại nó ra vì đúng lý do đó (§12.13e).

**Số và cả hai đường ra từ MỘT vòng lặp** trong `_thong_ke`, nên điểm cuối đường vốn *bằng đúng*
`von_cuoi` và đáy đường sụt giảm *bằng đúng* `drawdown_pt` — không có hai nguồn để lệch nhau. Nhiều
lệnh cùng đóng trong một nến trục thì gộp làm một điểm (thư viện vẽ đòi mốc tăng ngặt), giữ `von`
của lệnh cuối nhưng giữ mức sụt **sâu nhất**, để đáy đồ thị vẫn khớp con số.

**KHÔNG có `số vùng nén`** dù `thong_ke` đang mang sẵn — khái niệm riêng của một chiến lược, đúng
cái bẫy đã gỡ ở bảng số liệu bên phải (§12.9c).

#### 12.20c ✅ HAI ĐỒ THỊ VẼ TAY — bỏ lightweight-charts ở tab này

Bản đầu dùng lightweight-charts cho cả hai. Bỏ, vì ba lý do và không lý do nào là "cho vui":

- nó **đóng khung một mảng nền đen** riêng giữa bảng vốn màu xám — người dùng: *"để nó đè lên nền
  xám luôn chứ, lại để nền đen như này"*;
- nó **dán logo TradingView** vào góc mỗi đồ thị;
- nó kéo cả một bộ máy biểu đồ nến chỉ để vẽ một đường gấp khúc 384 điểm.

Chart **phát lại** thì vẫn giữ nó — chỗ đó cần trục thời gian, thu phóng, kéo ngang, marker, tooltip
theo nến. Chỗ này không cần gì trong số đó.

Mẹo để **không phải đo bề ngang bằng JS**: `<svg preserveAspectRatio="none">` với hệ toạ độ cố
định 1000×100, cho nó tự kéo giãn đầy khung; nét không méo theo nhờ `vector-effect:
non-scaling-stroke`. Còn CHỮ thì đứng **ngoài** SVG — nhãn là thẻ HTML đặt theo phần trăm, nên
không dính phép kéo giãn đó. Không `ResizeObserver`, không state kích thước, tự co giãn.

Ba chi tiết làm rồi mới thấy cần:

1. **Mảng tô cắt đôi ở đường mốc** — trên mốc xanh (đang lãi), dưới mốc đỏ (đang lỗ), bằng hai
   `clipPath`. Tô một màu cam duy nhất thì nửa khung thành một khối cam nặng trịch mà chẳng nói
   gì; cắt đôi thì đúng nghĩa xanh/đỏ mà bảng màu đã dành riêng cho lãi/lỗ (§12.17).
   `clipPath` phải mang **id riêng từng đồ thị** (`useId`) — trùng id thì đồ thị này bị cắt theo
   mốc của đồ thị kia.
2. **Bước trục giá phải có 2.5.** Thiếu nó thì biên độ 93 $ nhảy thẳng từ bước 20 lên bước 50 —
   cả đồ thị còn đúng 2 vạch, gần như không có trục. Có 2.5 thì ra bước 25, đủ 4 vạch.
3. **Crosshair tự làm.** Bỏ thư viện là mất cái crosshair đọc số, mà đó là thứ duy nhất đáng giữ
   lại: rê chuột ra vạch dọc + chấm trên đường + ô ghi `9,959.10 $ · 2025-07-25 11:00`. Tìm điểm
   gần nhất **theo thời gian**, không theo chỉ số — các điểm cách nhau không đều (lệnh đóng dày
   thưa tuỳ đoạn), chia đều chỉ số là trỏ sai chỗ.

#### 12.20b ⚠ LỖI THẬT: đường vốn cộng dồn theo thứ tự TẠO lệnh

`_thong_ke` duyệt `so.lenh` — tức thứ tự **đặt** lệnh — rồi cộng dồn vốn theo đó. Tổng thì thứ tự
nào cũng ra một số, nhưng **đường đi** của vốn thì không, mà `drawdown_pt` lại đo trên chính đường
đi đó. Đo trên một năm thật: **9/386 lệnh đóng đảo thứ tự** so với lúc đặt.

Lần này may: cả hai cách đều ra 0.792 %. Nhưng đồ thị vẽ ra sẽ giật ngược thời gian, và một bộ dữ
liệu khác là con số sai hẳn. Sửa: sắp theo `(nen_dong, id)` trước khi cộng dồn.

Nhân tiện `_thong_ke` trả thêm: `von_dau · lai_pt · drawdown_tien · drawdown_luc · R_moi_lenh ·
R_khi_thang · R_khi_thua · he_so_lai · chuoi_thua`. `he_so_lai` trả **`None` khi chưa có lệnh lỗ
nào**, không phải 0 — hai chuyện khác hẳn nhau, và bảng hiện dấu gạch.

### 12.19 ✅ Ô "nhảy tới mốc" trên thanh công cụ

*"thêm phần move to date ở ribbon để tôi muốn test khoảng thời gian cụ thể nếu cần."*

Một ô `datetime-local` (Chromium có sẵn bộ chọn ngày, không thêm thư viện nào), **tách khỏi đồng
hồ bên phải** chứ không gộp làm một: đồng hồ đổi 8 lần/giây lúc phát, mà một ô nhập tự đổi giá trị
dưới tay người đang gõ thì không gõ nổi. Bấm vào ô thì nó nạp mốc hiện tại, nên vẫn "đi tiếp từ
chỗ đang đứng".

**Tìm nến phải hỏi Python** (`ApiTester.test_tim_moc` → `searchsorted`), không nhẩm ở JS: dữ liệu
có 271 lỗ hổng nên `(t − t_đầu) / 60` ra một chỉ số lệch hẳn. Chọn nhằm chiều thứ Bảy thì nhảy
đúng tới phiên mở cửa Chủ nhật; chọn ngoài khoảng thì kẹp về nến đầu/cuối. Đo thật:
`07-04 15:00 → 07-04 15:00` · `07-04 23:05 → 07-06 22:05 (CN)` · `2030-… → nến cuối`.

**Ba cái bẫy, cả ba đều đã cắn:**

1. **Giờ UTC.** Nến trong kho là giờ sàn và cả app hiển thị nguyên như thế. Để `Date` tự định dạng là nó
   cộng lệch múi giờ máy — ô nhập lệch vài tiếng so với chính cái đồng hồ ngay cạnh nó. Dựng và
   đọc chuỗi bằng tay theo UTC.

2. **Ô bắn ra một giá trị HỢP LỆ sau MỖI đoạn gõ** (xong tháng đã là một mốc, xong ngày lại một
   mốc nữa). Không hoãn thì một lần gõ = 5-6 cú nhảy chồng nhau, và cú **về đích sau cùng** mới là
   cái hiển thị. Đo được: gõ `07/04/2025 03:00 PM` mà con trỏ dừng ở `07-06 22:05`, vì mốc dở dang
   `07/04 11:05 PM` rơi vào tối thứ Sáu (chợ đã đóng) nên bị đẩy sang phiên Chủ nhật. → hoãn 350ms
   + một số đếm `lanMoc` để vứt kết quả của cú đã cũ.

3. **⚠ Ô uncontrolled thì IM LẶNG HẲN sau cú nhảy đầu.** Tái hiện chắc chắn: gõ `07/04/2025`, đợi
   cú nhảy chạy xong, gõ tiếp `03:00` — `onChange` không bắn nữa, đồng hồ kẹt ở `07-06 22:05` còn
   ô ghi `03:00 PM`. Cú nhảy gọi `veDau` → dựng lại chart + đặt 6 state, và qua lần re-render lớn
   đó **bộ theo dõi giá trị của React lệch pha với DOM**. Cho ô một state riêng (controlled) là
   hết — React luôn nắm giá trị, không còn chỗ cho lệch.

   Bài học: cái bẫy này **chỉ lộ ra khi gõ có ngắt quãng**. Gõ liền một mạch thì hoãn 350ms gộp
   hết lại thành một cú nhảy và mọi thứ trông đúng. Kiểm bằng "gõ một phát rồi chụp" là bỏ lọt.

### 12.18 Nút "Tới sự kiện kế tiếp" — hai lỗi, một gốc

Người dùng báo: *"nút tới sự kiện kế tiếp bị lỗi, nó xoá luôn đi những sự kiện cũ."* Hai lỗi, và
cả hai đều từ một chỗ: **nhảy = dựng lại chart từ số không**.

1. **Chart trắng bốc sau khi nhảy.** `veDau` nạp đúng MỘT cây nến (`[nenTai(L, 0)]`) rồi để phát
   bồi thêm. Mọi lệnh cũ biến mất, và người xem mất hẳn ngữ cảnh — không biết giá vừa từ đâu tới.
   → Lô giờ bắt đầu **sớm hơn con trỏ `LUI = 720` nhịp** (≈144 nến M5, nửa màn hình) và chart được
   nạp thẳng toàn bộ đoạn quá khứ đó. **Cùng một lời gọi**, không thêm vòng nào.

2. **Bấm ba lần vẫn đứng yên.** Nút nhảy tới *40 nhịp TRƯỚC* sự kiện cho "dễ xem nó xảy ra" —
   nhưng thế thì lần bấm sau lại tìm thấy chính sự kiện đó (nó vẫn nằm phía trước con trỏ) và
   nhảy về đúng chỗ cũ. Một vòng lặp đứng im.
   → Dừng **ĐÚNG NGAY sự kiện**: mũi tên hiện ở mép phải, quá khứ vẫn còn nguyên nhờ đệm, và lần
   bấm sau đi tiếp được. Muốn xem lại khoảnh khắc thì ◀ vài nhịp rồi ▶.

Kèm hai chi tiết nhỏ mà thiếu thì vẫn lạc: nhật ký **luôn cuộn xuống cuối** khi danh sách đổi
(đang dừng thì không có dòng mới nên không sợ giật), và dòng vừa nhảy tới được **tô sáng** — nó
trả lời "tôi đang đứng ở đâu" ngay lúc chart đổi.

### 12.14 So hai lần chạy

Mục đích của bạn là *nâng cấp model*, mà đó là một vòng lặp: sửa → chạy lại → chỗ nào tốt lên,
chỗ nào xấu đi, **lệnh nào biến mất**. Giữ tóm tắt lần chạy trước (vài trăm KB) để bấm ▶ xong
hiện được một dòng:

```
so với lần trước: −3 lệnh · +2 lượt trượt tại [2] · tổng R 18.5 → 21.0
```

---

## 13. Việc còn treo

Thiết kế Strategy Tester đã chốt hết ở §12. Còn lại là **việc làm**, theo đúng thứ tự:

- [x] ~~Sửa 3 lỗi có sẵn của cửa sổ tester (§12.12)~~ — xong, đã đo bằng chuột thật
- [x] ~~`nhip` thay `timeframe`~~ — xong, schema 4, di cư file cũ tự động
- [x] ~~Sửa mô tả ATR trong `kho/chi_bao.py`~~ — xong, và bộ TÍNH cũng đã có (`tinh_toan.atr`)
- [x] ~~Lỗi soát khi hai đầu nhánh lệch dưới 8 px~~ — xong, `core.LECH_TOI_THIEU`
- [x] ~~Cập nhật `test_doi_chieu_d02.py`~~ — giờ **9 chỗ cố ý khác**, mỗi chỗ gắn nhãn có
      ĐỔI SỐ hay không (`SỐ LỆNH` · `GIÁ & P&L` · `không`); 4 chỗ đổi số
- [x] ~~`nguon_nen.py`~~ — xong, chạy thật trên 30k nến XAUUSD (nay chỉ đọc, §17)
- [x] ~~`tinh_toan.py`~~ — xong. **Gộp M1→M5/M15/H1 trùng khít nến của sàn tới từng chữ số** trên
      một tháng dữ liệu thật (5.994 nến M5 · 1.999 M15 · 501 H1, lệch OHLC = 0)
- [x] ~~`khop_lenh.py`~~ — xong, 30 bài kiểm từng ca tính tay được
- [x] ~~`bo_chay.py`~~ — xong: biên dịch, vòng lặp M1, Manage/Entry theo nhịp, nhật ký
- [x] ~~**Đo tốc độ trên 1 năm thật**~~ — **2,9 s** cho 354.503 nến M1 (§12.13e)
- [x] ~~`nhat_ky.py`~~ — xong: dựng 200 dòng mất **0,6 ms**, ghi 8.020 lượt ra 3,3 MB
- [x] ~~Giao diện tester: chart Canvas · bảng 4 khối · nhật ký ảo hoá~~ — xong, đã chạy
      backtest thật trong cửa sổ và đối chiếu bảng ↔ nhật ký (§12.15)

Chưa liên quan tới tester:

- [ ] **Chồng lệnh** — D_02: nhiều VỊ THẾ (`Max_Positions`) nhưng đúng MỘT lệnh chờ. Giữa hai lần vào lệnh bắt buộc có một đợt ATR bung ra (`CONSUMED` chỉ thoát bằng `atr_bps ≥ N`).
- [ ] Có cần `HOẶC` giữa các điều kiện không? *(đang thiết kế: **không** — dùng nhiều nhánh, vì "hoặc" giấu trong hộp thoại thì nhìn sơ đồ không thấy)*
- [ ] Đóng gói `.exe` (PyInstaller) — chưa làm spec.

---

## 14. ⭐ CẦU NỐI QUANTCONNECT (slice 2a) — bộ luật y hệt, chỉ thay ống nước

> Theo `DECISIONS.md` D-01…D-04. Động cơ cũ còn làm Strategy Tester chạy tại máy và làm
> CHUẨN đối chiếu cho cầu nối; MT5 đã gỡ (D-09, §17).

**Một câu:** sơ đồ chạy trên dữ liệu và chỉ báo của QuantConnect mà bộ luật KHÔNG đổi một
dòng — `_chay_so_do`, `_xet_cong`, `_vao_lenh`, `_sua_lenh`, `_nuoi_zone` được GỌI LẠI
nguyên văn từ `bo_chay`. Cầu nối chỉ thay chỗ dữ liệu đi vào.

| | Bộ chạy cũ | Cầu nối (`lean/cat_lean.py`) |
|---|---|---|
| Nến | M1 trong kho trên máy, đọc cả năm | M1 từ QC, tới từng cây |
| Chỉ báo | `tinh_toan` tính trước cả mảng | chỉ báo LEAN, lớp vỏ đẩy vào từng nến |
| Spread | ô nhập cố định | Bid/Ask thật của từng nến (`CaiDatQC.spread_gia`) |
| Khớp lệnh | đường đi 4 điểm | VẪN đường đi 4 điểm — đổi sang LEAN ở slice 2b |

`ChuongTrinhQC` kế thừa `ChuongTrinh`, chỉ thay `_dung_truc` (trục lớn dần) và
`_xin_cot` (ghi danh khoá thay vì tính cột). `doc_cot` của lớp cha chạy nguyên văn trên
list — nên quy ước `shift` không thể lệch với bộ cũ.

**Bằng chứng, không phải niềm tin:** `tests/test_cat_lean.py` cho bộ cũ và cầu nối chạy
trên CÙNG nến, CÙNG giá trị chỉ báo → nhật ký, sổ lệnh, bảng tổng kết trùng khít tới từng
byte, trên ba bộ dữ liệu giả đi đủ mọi nhánh của sơ đồ mẫu (bài tự kiểm độ phủ).

### 14.1 Hai chỗ khác bộ cũ — CỐ Ý

1. **Nến trục xếp hàng.** Dữ liệu nối lại sau lỗ hổng đúng phút CUỐI của một ô (ô trước
   lại mất phút cuối) thì hai nến trục cùng đóng trong một nhịp M1. `la_nhip5` của bộ cũ
   chỉ bật MỘT lần → cây trước không bao giờ được chạy Entry, cổng zone không được xét.
   Trái với chính lời hứa "mỗi nến trục có ĐÚNG MỘT nhịp" ở `_dung_truc`. Cầu nối chạy
   từng cây theo thứ tự. ⚠ **Bộ cũ còn mang lỗi này** — chưa sửa vì nó sắp được thay
   (D-01); bài kiểm ghi lại đúng ca đó để không ai tưởng là trùng khít.
2. **Spread sống** — mọi chỗ đọc spread vẫn đọc qua đúng một cửa, chỉ đổi nguồn.

### 14.2 Gói dán lên QC

Gói Free không có API (D-02) và giới hạn **mỗi file 32 KB** (Researcher 64 · Team 128) —
riêng `core.py` đã 113 KB. `tools/dong_goi_lean.py` vì thế:

- **làm gọn** từng module trên TỪNG TOKEN: bỏ comment, docstring → `pass`. Không đụng một
  token code nào, và **giữ số dòng** mọi câu lệnh — lỗi báo trên QC ở `core.py` dòng N
  là đúng dòng N trong repo;
- nén lzma + base85, chia vào `main.py` + `nguon_*.py` dưới trần (hiện: 2 file);
- **soát sơ đồ tại máy** trước khi đóng gói — lỗi biên dịch nổ ở đây kèm nhãn khối, không
  nổ sau 15 giây dựng máy trên cloud;
- gắn **mã gói** vào mọi file — dán lệch lần đóng gói là báo ngay, chỉ đúng file.

Khung H4/D1 bị chặn: biên nến của chúng đặt theo giờ của sàn đã dựng nến, mà giờ đó và giờ
dữ liệu QC không trùng — chạy là ra nến khác cây, lệch im lặng.

### 14.3 Một giả định về LEAN — tự khai đúng sai mỗi lần chạy

Giả định: consolidator phát nến khung TRƯỚC `on_data` của nến M1 khép nó. Nếu sai, mọi
lượt Entry chạy trễ một nhịp. Dòng tổng kết vì thế in **"lượt Entry … (trễ N)"**: bình
thường N cỡ vài chục (phút cuối ô bị thủng); N xấp xỉ số nến trục là giả định sai.

## 15. ⭐ CHẠY TRÊN QC QUA API (slice 3) — một lệnh, không mở web QC

> Theo `DECISIONS.md` D-06: gói Researcher, app tự gọi API, khoá là bí mật. Chưa có nút
> trong app — slice này là công cụ dòng lệnh. Nút ▶ trên giao diện sẽ gọi ĐÚNG hàm
> `qc_api.chay` này, không viết lại.

`tools\chay_qc.bat [file sơ đồ] [--tu YYYY-MM-DD --den YYYY-MM-DD]` làm trọn một lượt ▶:

| Bước | Làm gì |
|---|---|
| Đóng gói | y §14.2, trần 62 000 byte/file (Researcher 64 KB) → hiện vừa MỘT file `main.py` ~53 KB |
| Project | tìm «Cat Studio/<tên sơ đồ>» trên QC, chưa có thì tạo (Python) — mọi cỗ máy chung một thư mục |
| File | file đã có → ghi đè, chưa có → tạo, `nguon_*.py` thừa của lần đóng gói trước → XOÁ |
| Biên dịch → backtest | hỏi trạng thái thưa dần 0,25 → 1 → 2 → 5 → 10 giây, y LEAN CLI |
| Nhật ký | tải từ Object Store về `du_lieu/nhat_ky/<tên>-<vân tay>.jsonl` — `nhat_ky.doc_file` mở được |
| In | hai dòng tổng kết y log của QC (`cat_lean.dong_ket_qua`, chung một hàm) + vốn + link QC + đường dẫn nhật ký |

`cat_studio/qc_api.py` là chỗ DUY NHẤT trong app biết QuantConnect tồn tại; lõi không
import nó. Chỉ dùng thư viện chuẩn. Từng điểm API (tên,
GET hay POST, tham số, cách đọc lỗi, khi nào coi backtest là xong) đối chiếu với mã nguồn
LEAN CLI — công cụ dòng lệnh chính thức của QC, mã nguồn mở — không đoán.

### 15.1 Khoá

- Đọc từ hai biến môi trường `QC_USER_ID` + `QC_API_TOKEN`; thiếu một trong hai thì đọc
  `du_lieu/qc_khoa.json` (`{"user_id": "...", "token": "..."}`). `du_lieu/` nằm trong
  `.gitignore` — bài kiểm canh đúng dòng đó.
- Khoá có **toàn quyền tài khoản, kể cả giao dịch thật**. App chỉ dùng nó để chạy backtest, và không
  bao giờ: in ra, đưa vào câu lỗi hay `repr`, gửi đi dạng thô (chỉ gửi băm
  `sha256(token:giờ)`, y LEAN CLI), gửi kèm link tải (link Object Store là link ký sẵn).
- Dấu giờ trong băm luôn là giờ THẬT — đồng hồ giả chỉ dùng để đo hạn chờ trong bài kiểm.
  (Lỗi bắt được lúc viết bài kiểm: một đồng hồ dùng cho cả hai việc thì giả hạn chờ là hỏng
  luôn xác thực.)

### 15.2 Một khoá Object Store cho cả hai đầu

Cầu nối trên cloud GHI nhật ký vào khoá `nhat_ky.khoa_qc(doc)`; app ĐỌC về từ chính hàm
đó — hai bên không thể lệch tên. Khoá chỉ có ASCII: nó đi qua URL và thành tên file trong
zip QC gửi về. Lớp vỏ ghi bản chữ `<khoá>.b64` khi `save_bytes` hỏng → app thử cả hai.
File vừa ghi lúc backtest kết thúc có khi vài giây sau mới hiện → hỏi lại sau 2, 4, 8 giây
rồi mới chịu thua.

### 15.3 Hỏng thì nói bằng lời

Mọi lỗi là `LoiQC` (khoá: `LoiKhoa`) — một câu tiếng Việt nói phải làm gì. Công cụ in câu
đó, mã thoát 1, không traceback: ngày gõ sai và thiếu khoá (báo NGAY, chưa đóng gói hay gửi
gì) · khoá sai (QC trả
"Hash doesn't match", hoặc 500 hai lần liền — LEAN CLI cũng coi vậy) · User ID sai · mất
mạng · 5xx khác (thử lại đúng một lần) · biên dịch hỏng (kèm 12 dòng log cuối) · backtest
lỗi (kèm vết lỗi + link) · thiếu nhật ký (kèm lời QC + link log) · chờ quá hạn. Lỗi xảy ra
TRÊN cloud — vd. câu "Project THIẾU file nguon_1.py" của gói — về tới người dùng nguyên văn.

### 15.4 Bằng chứng — và chỗ chưa có bằng chứng

`tests/test_qc_api.py` dựng một **máy chủ QC GIẢ** trên 127.0.0.1, nói đúng giao thức LEAN
CLI nói, và **CHẠY THẬT bộ file được đẩy lên** trong một Python sạch như QC chạy → nhật ký
tải về trùng khít từng lượt, từng lệnh với chạy cầu nối ngay tại máy. Canh cả lượt sau
(dùng lại project, dọn file thừa khi nâng từ Free 2 file lên Researcher 1 file) và mọi đường
hỏng ở §15.3. Đột biến từng chỗ trong `qc_api` / `chay_qc` (bỏ thử lại, bỏ chờ thống kê,
lộ khoá, bỏ dọn file…) → bài kiểm bắt được.

⚠ **Chưa chạy trên QC thật** — môi trường phát triển không ra được quantconnect.com. Ba
điều chỉ QC thật trả lời được: (1) khoá thuật toán ghi có hiện ra Y NGUYÊN ở Object Store
cấp tổ chức không, và `object/get` với khoá chưa có trả về gì (máy giả: báo lỗi → app hỏi
lại; QC trả zip rỗng thì app cũng hỏi lại, cùng kết cục); (2) Object Store của gói
Researcher có nhận một nhật ký cỡ chục MB không (D-03 còn treo); (3) một lượt thật mất bao
lâu — tiêu chí của slice là ~1 phút. Hỏng ở (1) hay (2) thì công cụ in khoá + link log của
backtest, dòng «Object Store» trên log nói lý do.

## 16. ⭐ MÀN CHƠI TRONG APP (slice 4) — vòng chơi D-05 chạy trên QuantConnect

> Theo `DECISIONS.md` D-05 · D-06 · D-07 · **D-08 (đề xuất — luật chấm cụ thể)**.

**Một câu:** nút **◆ Màn chơi** (ribbon, Ctrl+M, File → Mở Màn chơi) mở cửa sổ thứ tư —
Chiến dịch (màn, boss, ▶ nhanh / ▶ đầy đủ / Nộp, sao) và Sáng tạo (mọi symbol, mọi khoảng
ngày). Mọi lượt chạy trên QuantConnect qua API (§15), không mở web QC.

| Lớp | File | Việc |
|---|---|---|
| Luật chơi | `cat_studio/game.py` | màn · boss · `cham` · `sao` · `do_gon` · sổ `du_lieu/game.json` |
| Việc nền | `cat_studio/qc_chay.py` | `ViecQC`: soát → đóng gói → `qc_api.chay` → chấm → ghi sổ; `KetQuaQC` dựng lại từ nhật ký |
| Đóng gói | `cat_studio/goi_qc.py` | chuyển từ `tools/dong_goi_lean.py` (giờ là vỏ dòng lệnh) để app gọi được; `.spec` mang nguồn theo |
| Vỏ API | `api.ApiQC` + `Api.mo_qc` | 15 hàm `qc_*` cho JS — mỏng, không luật nào |
| Giao diện | `webui/src/qc/ManChoi.tsx`, `HopKhoa.tsx` | thẻ màn · tiến độ · kết quả · tab Vì sao / Thống kê / Lệnh / Điểm / Lịch sử · hộp khoá |

### 16.1 Màn ẩn là ẩn (D-06)

`game.man_cong_khai` không mang ngày màn ẩn. Lượt **Nộp** trả về chỉ con số tổng — không
ngày, không link QC, không đường vốn, không lượt, không lệnh; lịch sử ghi nó không ngày;
tên backtest trên QC ghi "màn ẩn" chứ không ghi ngày; không mở lại được để xem từng nến.
Nộp đòi một lượt ▶ đầy đủ của ĐÚNG cỗ máy đó (cùng vân tay `nhat_ky._van_tay`).

### 16.2 Không nến — nhật ký tự mang giờ

Mang chuỗi giá của QC về máy là trái điều khoản dữ liệu của QC, nên cửa sổ này KHÔNG có
chart nến. Bù lại, cầu nối ghi thêm (chỉ lúc ghi, bản ghi trong bộ nhớ vẫn trùng khít bộ
cũ): `t` trên mỗi lượt, `t_dat/t_khop/t_dong` trên mỗi lệnh, và meta có `duong_von`,
`gia_dau/gia_cuoi/mua_giu_pt` (đủ chấm boss — hai con số, không phải chuỗi giá), `tu/den`.
Thuật toán đặt múi giờ **UTC** (`vo_qc.initialize`) — giờ in ra là giờ thật. `nhat_ky.dong_chu`
đọc `t` trên bản ghi khi có, nên tab Vì sao và "Xem trên sơ đồ" dùng lại nguyên văn bộ dựng
chữ của tester; tab Thống kê dùng lại `ThongKe` (thêm prop `du`).

### 16.3 Mỗi lượt một khoá Object Store

App đặt khoá RIÊNG cho từng lượt (`nhat_ky.khoa_qc(doc, ma_luot)`), nhúng vào
`CAU_HINH["khoa"]`; cầu nối ghi đúng khoá đó (`cat_lean.khoa_luu`); app tải về xong thì
XOÁ khỏi Object Store. Lượt nào lưu hỏng thì app không thể nhặt nhầm nhật ký của lượt trước,
và Object Store không đầy dần. Đường dán tay (không có `khoa`) vẫn dùng khoá theo sơ đồ.

### 16.4 Bằng chứng

- `tests/test_game_qc.py` — luật chấm, màn ẩn là ẩn, luật nộp, việc nền (một lượt một lúc,
  tiến độ, lỗi thành lời), xem lại, Sáng tạo, và **vỏ `ApiQC`** — trên máy chủ QC giả
  (`tests/qc_gia.py`, dùng chung với `test_qc_api.py`) chạy THẬT bộ file đẩy lên.
- `webui/kiem/man_choi.mjs` — cửa sổ Màn chơi trong Chromium với bề mặt Python giả, bấm
  trọn vòng chơi (cần Playwright; không có thì tự bỏ qua).
- Lúc làm còn chạy một phép kiểm ĐẦU–CUỐI ngoài repo: Chromium gọi thẳng `api.Api`/`ApiQC`
  THẬT qua một cầu HTTP, Python gọi máy chủ QC giả — cửa sổ vẽ → ◆ Màn chơi → khoá →
  ▶ nhanh → Vì sao → soi → ▶ đầy đủ → Nộp → Lịch sử: 19/19, không lỗi console. Nó bắt được
  hai lỗi thật: cụm nút ribbon rớt dòng đẩy ▶ Test ra ngoài, và kết quả xem lại thiếu thông
  tin lượt.
- `cat_studio/khung_rong.py`: ngoài Windows, `api.py` nạp bản khung rỗng thay
  `khung_cua_so` (vốn gọi `ctypes.windll` lúc nạp) — năm bài kiểm từng chỉ chạy được trên
  Windows giờ chạy được trên Linux/CI. `webui/kiem/o_so.mjs` đổi sang `fileURLToPath` —
  bài ô số cũng chạy được trên Linux.

⚠ **Chưa chạy trên QC thật** — như §15.4. Thêm một điều chỉ QC thật trả lời: `set_time_zone(UTC)`
có đổi gì ngoài giờ in ra không (biên nến M5–H1 thì không, vì lệch nguyên giờ).

## 17. ⛔ BỎ MT5 — app chỉ phục vụ QuantConnect

> Theo `DECISIONS.md` **D-09 (chốt)**. Chủ dự án: *"xóa sạch dấu vết của MT5 ra khỏi app,
> vì bây giờ trò chơi chỉ phục vụ cho QuantConnect"*.

**Đã gỡ:**

| Thứ | Ở đâu (trước) |
|---|---|
| Cửa sổ **Live** — chạy sơ đồ trên tài khoản MT5, đo sức khoẻ kết nối, hiệu chuẩn, đề phòng | `api.ApiLive` · `api.mo_live` · `phien_live.py` · `ket_noi.py` · `gui_lenh.py` · `webui/src/live/` · nút ● Live · Ctrl+L · File → Mở Live |
| **Tải nến** từ terminal MT5 (tự tải khi bấm ▶, ước tính MB, ghép lô, ghi nguyên tử) | `nguon_nen.tai` & cùng họ · `api._tai_neu_thieu` |
| Nút **Kiểm tra kết nối MT5** trong Cài đặt | `nguon_nen.kiem_ket_noi` · `api.nguon_kiem_ket_noi` |
| Thư viện `MetaTrader5` | `requirements.txt` · `Cat_Studio.spec` · hướng dẫn trong gói phát hành |
| Cột `ticket` (mã lệnh của sàn) trong sổ lệnh | `so_lenh.Lenh` |
| Tham số chỉ cửa sổ Live dùng (xin đuôi nến, lấy đoạn cuối, trần nến riêng) | `ApiTester.test_nen_tf` · `test_doan` · `Chart.tranNen` |
| Bài kiểm tầng gửi lệnh trên sàn giả | `tests/test_gui_lenh.py` |

**Còn lại:** Strategy Tester chạy tại máy trên những bộ nến **đã có** trong `du_lieu/nen/`
(kho chỉ đọc: liệt kê · xoá · còn thiếu khoảng nào). Thiếu phần ĐẦU khoảng đã đặt thì ▶ dừng và
nói rõ thiếu khoảng nào, máy đang có khoảng nào; máy chưa có bộ nến nào thì tester không chạy được.
Bộ chạy cũ (`bo_chay`) vẫn là chuẩn đối chiếu của cầu nối QuantConnect (`test_cat_lean`).

Chú thích từng nhắc "khớp MT5" nay nói đúng điều nó canh: **công thức D_02 đã dò** (ATR = SMA của
True Range; MA mồi bằng SMA; `nến[1]` = nến vừa đóng; nến dựng bằng giá Bid).

**Còn trên máy người dùng** (ngoài repo, app không đọc nữa): `du_lieu/ho_so_ket_noi.json` — hồ sơ
kết nối của cửa sổ Live cũ. Xoá tay được, không ảnh hưởng gì.

## 18. ⛔ BỎ STRATEGY TESTER — lối chạy duy nhất là ◆ Màn chơi

> Theo `DECISIONS.md` **D-10 (chốt)**, phần 1 trong 7 phần xây cỗ máy 5 trạm. Chủ dự án:
> *"đồng ý cả 3, xoá luôn tester, xây 5 trạm đi"*.

**Vì sao:** tester chạy tại máy trên nến tại máy, mà nến của QuantConnect không được mang về
(D-08) — giữ nó là giữ một thế giới thứ hai với bộ khớp lệnh riêng, lệch luật với nơi cỗ máy
thật sự chạy. Khớp lệnh từ nay là việc của QC (D-10).

**Đã gỡ:**

| Thứ | Ở đâu (trước) |
|---|---|
| Cửa sổ **Strategy Tester** — chart nến phát lại, bảng số liệu, đường ray lệnh, nút nhảy sự kiện, lịch sử các lần chạy, "so với lần trước" | `api.ApiTester` · `api.mo_tester` · `webui/src/tester/` (`Tester`, `Chart`, `BangSoLieu`, `LichSu`, `NutChart`) · `main.tsx ?tester=1` |
| Nút **▶ Test**, mục **File → Mở Strategy Tester**, việc của **Ctrl+R** | `Ribbon` · `App` — Ctrl+R vẫn bị CHẶN (mặc định Chromium là nạp lại trang, mất sơ đồ đang vẽ) |
| **Cài đặt → Strategy Test** (symbol, khoảng ngày, spread, vốn, phí, đòn bẩy, delay) và bảng **nến trên máy** | `SettingsDialog` · `api.save_test_settings` · `api.nguon_xoa` · `luu_tru.CAI_DAT_MAC_DINH["test"]` |
| **Kho nến trên máy** và **lịch sử chạy** | `cat_studio/nguon_nen.py` · `cat_studio/lich_su.py` · `luu_tru.thu_muc_nen` · mục "Nến đã tải" trong hộp Kho |
| Hàm nhật ký chỉ tester dùng | `nhat_ky.dung_lo_theo_nen` (phát lại) · `nhat_ky.so_hai_lan` |
| Thư viện vẽ chart nến | `lightweight-charts` (package.json) |
| Bài kiểm của những thứ trên | `tests/test_nguon_nen.py` · các mục nhảy sự kiện / đường ray / phát lại trong `test_nhat_ky`, hộp zone trên chart trong `test_zone` |

**Chuyển chứ không bỏ** (Màn chơi đang dùng):

- Ba bảng dưới — vỏ bảng `BangDuoi`, nhật ký «Vì sao» `Journey`, `ThongKe` → `webui/src/chung/`.
  `Journey` bỏ phần theo con trỏ phát lại; `ThongKe` chỉ nhận dữ liệu đưa sẵn.
- Gói **soi một lượt lên sơ đồ** → `nhat_ky.ban_soi` (một chỗ dựng, `KetQuaQC.soi` gọi; bài kiểm
  hợp đồng "một vết cho mỗi điều kiện" nằm ở `test_nhat_ky` mục 6).
- Kiểu **một cây nến** → `tinh_toan.DTYPE` (bộ chạy cũ và bài kiểm của nó cần tới phần 7).
- Chế độ **Sáng tạo** của Màn chơi lấy mã mặc định từ Cài đặt → **Mã mặc định**, vốn 10.000.

Cài đặt cũ trong `du_lieu/cai_dat.json` tự rơi khoá `test` ở lần mở app sau (`doc_cai_dat` chỉ
giữ khoá còn trong bảng mặc định). Lỗi ngày 29/2 của khoảng ngày mặc định biến mất theo.

**Còn trên máy người dùng** (ngoài repo, app không đọc nữa): `du_lieu/nen/` (bộ nến M1 cũ) và
`du_lieu/lich_su/` nếu có. Xoá tay được, không ảnh hưởng gì.

## 19. ⭐ CỖ MÁY 5 TRẠM — lõi (D-10, phần 2)

> Từ điển: `cat_studio/tram.py` (chỉ KHAI). Định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên
> khối: `cat_studio/may.py`. Bài kiểm: `tests/test_may.py`. Chưa có trên giao diện — trình vẽ là
> phần 5, bộ máy chạy là phần 3.

**Một cỗ máy = năm sơ đồ khối**, đúng năm phần trong khung thuật toán của QuantConnect. Luật gốc:
*một sơ đồ = một phạm vi chạy* — mỗi trạm chạy lại từ khối Bắt đầu cho TỪNG đối tượng trong phạm
vi của nó, theo lịch của nó.

| Trạm | QC | Hỏi câu gì | Chạy cho ai | Lịch | Ra cái gì |
|---|---|---|---|---|---|
| ① Chọn mã | Universe Selection | Mã nào đáng để mắt tới? | mỗi mã của màn (hoặc danh sách riêng) | một lần lúc đầu · mỗi ngày · đầu tuần · đầu tháng | rổ mã — Gom giữ N mã điểm cao nhất |
| ② Tín hiệu | Alpha | Lên, xuống, hay đứng ngoài? | mỗi mã trong rổ | mỗi nến (khung) | tín hiệu có thời hạn, độ tin cậy, trọng số |
| ③ Chia vốn | Portfolio Construction | Mỗi mã bao nhiêu phần vốn? | mỗi mã có tín hiệu hoặc đang giữ | khi tín hiệu đổi · mỗi ngày · đầu tuần · đầu tháng | tỷ trọng mục tiêu — Gom chia ngân sách |
| ④ Rủi ro | Risk Management | Có gì phải cắt ngay? | mỗi mã đang giữ | mỗi nến (khung) | mục tiêu đã chỉnh |
| ⑤ Khớp lệnh | Execution | Lệnh gì, lúc nào? | mỗi mã còn lệch mục tiêu | mỗi nến (khung, mặc định M1) | lệnh gửi sang QC |

**Ngữ pháp chung — y hệt sơ đồ cũ, dùng lại nguyên bộ đồ thị của `core`:** khối Bắt đầu (mang
lịch, khung, và ở ① phạm vi) · khối **Hỏi** (`type = check_cond`, nên `core.is_branch_gate` nhận
ra nó là cổng) · khối **Làm**. Hỏi nối tiếp = VÀ; nhiều nhánh = HOẶC, thử từ trên xuống theo vị
trí trên canvas; luật lùi; đánh số `1 · 1A · 1A.1` riêng cho từng trạm. Câu báo lỗi đồ thị gọi
cổng là «Hỏi» (`core.validate_flow_graph(…, nhan_cong=…)`).

**Khối Làm — chỗ DUY NHẤT các trạm khác nhau:**

| Trạm | Khối Làm |
|---|---|
| ① | Cho vào rổ (điểm = một đại lượng, tuỳ chọn) · Loại khỏi rổ |
| ② | Báo tín hiệu: LÊN / XUỐNG / ĐỨNG NGOÀI · hạn N nến · tin cậy 0–1 · trọng số 0–1 |
| ③ | Đặt tỷ trọng: cố định X% / chia đều / theo tin cậy / theo trọng số / rủi ro ngang nhau · Về 0 · Giữ nguyên |
| ④ | Đưa về 0 · Giảm về X% · Cấm vào lại N nến (khối PHỤ) · Dừng cả tài khoản |
| ⑤ | Lệnh thị trường (X% phần lệch — dưới 100% là chia nhỏ) · Lệnh giới hạn / Lệnh chờ stop (cách giá X%, hạn N nến) · Chờ |

Mỗi khối Làm có **vai**: `quyet_dinh` (chốt kết quả cho đối tượng đang xét) hoặc `phu` (đi kèm
một quyết định). Hai quyết định trên CÙNG một đường là lỗi — cái sau lặng lẽ đè cái trước; báo ở
khối sau, gợi ý tách thành hai nhánh.

**Đại lượng khối Hỏi đọc được** (`tram.TOAN_HANG`, 42 cái): giá (mở/cao/thấp/đóng, khối lượng,
giá trị giao dịch) · chỉ báo (SMA, EMA, WMA, RMA, ATR, ATR %, RSI, MACD, Bollinger, Đổi giá %,
Donchian, ADX, Stochastic, độ lệch chuẩn, KL trung bình, giá trị GD trung bình) · thời gian & tài khoản — đọc được ở mọi
trạm; **tín hiệu** chỉ ở ③; **vị thế** (tỷ trọng, lãi/lỗ, rơi từ đỉnh, số nến đã giữ) ở ③④⑤ theo
từng cái; **khớp lệnh** (lệch mục tiêu, spread, lệnh đang chờ) chỉ ở ⑤. Mỗi đại lượng có ĐƠN VỊ
(giá · % · số · nến · tiền); so hai đại lượng khác đơn vị là lỗi. Vế phải là một con số, một
tham số, hoặc một đại lượng nhân hệ số (`Giá đóng(D1) > SMA(D1, 200) × 1.02`). `lui = 0` là nến
VỪA ĐÓNG — bộ máy chạy lúc đóng nến, nên không có nến đang chạy nào để nhìn trộm tương lai.

**Gom** — bước cuối của trạm, chạy một lần cho cả trạm: ① giữ tối đa N mã, điểm cao hay thấp
nhất · ③ giữ tiền mặt X%, trần mỗi mã Y%, chỉ mua (không bán khống). Tỷ trọng cố định lấy trước;
các cách tương đối (chia đều, theo tin cậy, rủi ro ngang nhau) chia nhau phần ngân sách còn lại.

**Soát lỗi** (`may.soat` → `[{severity, tram, step, index, message}]`):

- đồ thị: toàn bộ luật của `core.validate_flow_graph`; trạm thiếu khối Bắt đầu là LỖI (không biết
  chạy lúc nào, cho ai);
- khối Làm đặt sai trạm · đại lượng không đọc được ở trạm này (câu báo nói trạm nào đọc được) ·
  hai vế khác đơn vị · MACD nhanh ≥ chậm · hệ số nhân bằng 0;
- ô số: con số hoặc tên tham số có thật; tên tham số thì soát GIÁ TRỊ của tham số (nguyên? trong
  khoảng?) — chính con số ấy mới là thứ bộ máy dùng;
- ①②③⑤ phải có khối ra kết quả được nối tới từ Bắt đầu, không thì cỗ máy không bao giờ giao dịch;
  ④ được để trống (không quản rủi ro là một lựa chọn — QC cũng mặc định vậy);
- Gom sai khoảng; ① giữ N mã mà «Cho vào rổ» không có điểm → cảnh báo;
- giữa hai trạm: ③ chia theo tin cậy / trọng số mà ② không khối Báo nào đặt thứ đó → cảnh báo.

**Chuẩn hoá BẤT BIẾN** (hai lần bằng một lần, qua JSON không đổi, không sửa dict truyền vào).
Ô bỏ trống của đại lượng nhận mặc định — khung = khung khối Bắt đầu của trạm — và thẻ khối HIỆN
con số đó, nên không có gì bị giấu. Khối LẠ được GIỮ để soát lỗi gọi tên nó (vứt đi là cắt đôi
chuỗi nối dây trong im lặng — đúng lỗi bản Entry/Manage từng dính). Cỗ máy của bản mới hơn thì
từ chối mở.

**Chữ trên khối** do Python dựng (`may.dong_khoi`, `may.kem_the`): `Mỗi nến H1 · cho mỗi mã trong
rổ`, `EMA(H1, 20) > EMA(H1, 50)`, `RSI(H1, 14) > nguong_rsi = 70`, `LÊN · hạn 24 nến`,
`khớp ngay toàn bộ phần lệch`. Thẻ mang nhãn đánh số, màu theo vai (`start` · `hoi` · `lam`).

## 20. ⭐ BỘ MÁY CHẠY CỖ MÁY 5 TRẠM (D-10, phần 3)

> `chuoi_nen.py` (nến + chỉ báo tính dần) · `bo_may.py` (bộ máy) · `mau_tram.py` (mẫu dựng sẵn)
> · `nhat_ky_may.py` (chữ "vì sao"). Bài kiểm: `test_chuoi_nen`, `test_bo_may`, `test_mau_tram`,
> sàn giả `tests/san_gia.py`. Thuần Python, không numpy, không QuantConnect — cùng một file chạy
> trên máy lẫn trong `main.py` gửi lên QC (phần 4).

**Chia việc với QC (D-10 ý 2):** bộ máy chỉ quyết MỤC TIÊU (% vốn từng mã, có dấu) và Ý ĐỊNH
lệnh (loại, bao nhiêu % vốn, giá chờ, hạn). Số lượng, lô tối thiểu, ký quỹ, phí, trượt giá, khớp:
việc của QC. Tài khoản đi VÀO bộ máy mỗi bước (`{von, tien_mat, giu: {mã: {pt, gia_von, sl}},
lenh_cho: {id: {ma, pt}}}`) — nguồn sự thật duy nhất về tiền là QC.

**Một bước (một phút), thứ tự y khung QC:** nạp nến M1 → đóng nến khung lớn tới giờ → tài
khoản → (còn khởi động thì dừng) → lệnh hết hạn → tín hiệu hết hạn → ① → ② → ③ → ④ → mục tiêu
đổi thì huỷ lệnh chờ cũ → ⑤.

**Nến và chỉ báo** (`chuoi_nen`): gộp M1 lên khung lớn theo BIÊN GIỜ UTC TUYỆT ĐỐI (nến H1 là
[10:00, 11:00) dù thiếu phút; giờ trống hẳn thì không bịa nến). Nến chỉ ĐÓNG khi giờ đã qua hẳn
nó; dữ liệu thủng thì nó đóng ở phút đầu tiên có dữ liệu sau đó. Chỉ báo cập nhật lúc đóng nến,
NaN khi chưa đủ dữ liệu (EMA/RMA mồi bằng SMA như QC; RSI, ATR, ADX kiểu Wilder; Bollinger và
độ lệch chuẩn dùng độ lệch TỔNG THỂ; Donchian là N nến TRƯỚC nến đang xét). Hai câu hỏi cùng
chỉ báo cùng ô dùng chung một bản.

**Lịch:** ① chạy lúc bắt đầu, rồi đầu mỗi kỳ (ngày / tuần / tháng) — kỳ đầu tiên chạy ngay, không
đợi tới đầu tháng sau. ② chạy cho mỗi mã trong rổ đúng lúc nến khung của nó vừa đóng. ③ "khi tín
hiệu đổi" chỉ chạy khi hướng / tin cậy / trọng số đổi, hoặc tín hiệu tắt — phát lại y hệt để gia
hạn KHÔNG tính là đổi (không thì ③ cân lại mỗi nến). ④ chạy cho mỗi mã đang giữ lúc nến khung
của nó đóng. ⑤ chạy cho mã có mục tiêu CHƯA KHỚP XONG, lúc nến khung của nó đóng.

**Đi sơ đồ:** đúng luật lùi của bộ chạy cũ — cổng trượt thì lùi về ngã rẽ gần nhất, trừ khi lượt
đã qua một khối Làm. Mỗi cổng ghi vết TỪNG điều kiện (không ngắt ở cái sai đầu).

**① Gom:** mã đi tới «Cho vào rổ» vào rổ; giữ N mã thì xếp theo điểm (không điểm xếp cuối). Mã
rời rổ thì tín hiệu tắt theo — đang giữ thì ③ đưa về 0.

**③ Gom:** mã được xét = có tín hiệu ∪ đang giữ ∪ đang có mục tiêu. Không quyết gì → giữ mục
tiêu cũ. Dấu theo hướng tín hiệu (chỉ mua thì XUỐNG → 0). Cố định X% và theo trọng số lấy
TRƯỚC; chia đều / theo tin cậy / rủi ro ngang (tỉ lệ nghịch ATR %) chia nhau PHẦN CÒN LẠI của
ngân sách (100 − giữ tiền mặt). Rồi chặn trần mỗi mã; tổng vượt ngân sách thì thu nhỏ đều.
Mục tiêu mới THAY HẲN mục tiêu cũ.

**④:** «Đưa về 0» → mục tiêu 0; «Giảm về X%» → |mục tiêu| ≤ X; «Cấm vào lại N nến» → suốt quãng
đó mục tiêu của mã luôn là 0 dù ③ muốn gì; «Dừng cả tài khoản» → mọi mục tiêu 0, ①②③④ thôi
chạy, ⑤ chỉ còn bán ra.

**⑤ và vòng đời lệnh:** lệch = mục tiêu − đang giữ − đang chờ khớp. Dưới 0,1% vốn coi là đã tới
(như `MinimumOrderMarginPortfolioPercentage` của QC) và mã RỜI danh sách cần khớp — ⚠ lỗi thật
đã gặp khi kiểm: thiếu luật này thì tới mục tiêu rồi, giá trôi 0,1% là ⑤ đặt lệnh lắt nhắt ngược
chiều liên tục (208 lệnh thay vì 46 cho cùng một kết quả). Mã vào lại danh sách khi ③/④ phát mục
tiêu, hoặc lệnh của nó bị huỷ. Lệnh giới hạn / chờ stop: mua dưới / trên giá X%, bán ngược lại;
hết hạn (N nến khung ⑤) thì huỷ; mục tiêu đổi thì mọi lệnh chờ của mã đó bị huỷ để ⑤ tính lại.
Chia nhỏ X%: mỗi lượt khớp X% phần CÒN lệch.

**Khởi động:** `can_khoi_dong(cỗ máy)` = chỉ báo dài nhất × khung của nó + một nến (giây giao
dịch liên tục). ⚠ Lỗi thật đã gặp: đặt cứng 3 ngày thì mẫu «Giá trên MA» (SMA 200 nến H1 ≈ 8
ngày) câm suốt lượt. Trước mốc khởi động: chỉ nạp nến, không trạm nào chạy, không lệnh nào.

**Nhật ký:** mỗi lượt chạy sơ đồ một bản ghi `{t, tram, ma, duong, ket, cong[{khoi, khop, ve}],
viec}`; Gom một bản ghi `{t, tram, gom}`; sự kiện (bắt đầu, tắt tín hiệu, huỷ lệnh, khớp, dừng tài
khoản) một bản ghi `{t, tram, ma, su_kien, …}`. Không chữ nào lúc chạy; `DocNhatKy.chu(r)` dựng
chữ khi xem: `01-04 00:00  ② B  [1]  hết lượt tại [1A] · EMA(H1, 20) = 78.77 không > EMA(H1, 50) =
84.02`.

**Bảo đảm, có bài kiểm canh:** cắt dữ liệu ở T thì nhật ký và ý định mọi bước ≤ T y hệt bản chạy
trọn (không nhìn trước); chạy lại cùng dữ liệu ra y hệt (duyệt mã theo thứ tự cố định); mọi lệnh
đều có "cò" ngay trước nó.

**Mẫu dựng sẵn** (`mau_tram.MAU`, 22 mẫu): mỗi mẫu là một sơ đồ thường, dựng từ đúng khối người
chơi có; núm vặn thành tham số có tên (lắp lại mẫu không đặt lại núm đã vặn).
① Mọi mã · N mã thanh khoản nhất · N mã mạnh nhất. ② Giao cắt EMA · RSI · MACD · Động lượng · Giá
trên MA · Phá kênh Donchian. ③ Chia đều · Theo tin cậy · Theo trọng số · Rủi ro ngang nhau. ④ Không
quản · Cắt lỗ · Chốt lời · Trailing · Cầu dao. ⑤ Khớp ngay · Chia lát · Theo độ lệch chuẩn · Theo
spread. Cỗ máy mẫu (`may_tu_mau`): mọi mã + giao cắt EMA + chia đều + trailing + khớp ngay.

## 21. ⭐ CẦU NỐI QUANTCONNECT CHO CỖ MÁY 5 TRẠM (D-10, phần 4)

> `lean/vo_may.py` (lớp vỏ QC) · `goi_qc.dong_goi_may` (đóng gói) · `ket_qua_may.py` (đọc kết
> quả) · `qc_chay.ViecQC` (chạy từ app). Bài kiểm: `test_vo_may` — LEAN giả `tests/lean_gia.py`
> chạy CHÍNH bộ file đóng gói trong một Python sạch; `test_qc_may` — app → máy chủ QC giả
> `tests/qc_gia.py` (đúng giao thức API) → chạy → tải về → đọc.

**Lớp vỏ không chứa luật.** Luật ở `bo_may` — đúng file chạy trong bài kiểm. Lớp vỏ chỉ làm năm
việc: đăng ký mã theo loại thị trường (ngoại hối / CFD qua OANDA, tài khoản ký quỹ · cổ phiếu Mỹ
· crypto Coinbase, tài khoản tiền mặt), độ phân giải phút, KHÔNG lấp nến; khởi động đủ cho chỉ
báo dài nhất theo LỊCH của thị trường (`giay_lich_khoi_dong`: giờ mở cửa mỗi ngày, số ngày mỗi
tuần, dư 50% cho lễ — cổ phiếu Mỹ ~7 nến H1 một ngày nên SMA 50 nến H1 cần ~10 ngày lịch, không
phải 2); mỗi phút gom nến mọi mã (QuoteBar → giá GIỮA, spread = ask − bid), dựng tài khoản từ
`portfolio`, gọi `BoMay.buoc`, đổi ý định thành lệnh QC; báo khớp / từ chối ngược về bộ máy;
hết dữ liệu thì ghi nhật ký nén vào Object Store.

**«% vốn» → số lượng là việc của lớp vỏ:** giá × hệ số hợp đồng × tỉ giá ra giá trị một đơn
vị; làm tròn VỀ PHÍA 0 theo lô của mã (không bao giờ mua lố); dưới cỡ lệnh tối thiểu → 0. Ra 0
thì không đặt, báo bộ máy «từ chối» (đếm vào `bo_qua`) — và bộ máy KHÔNG đặt lại mỗi phút. Giá
chờ làm tròn theo bước giá của mã. Còn khởi động thì không đặt lệnh nào.

**Id lệnh đi bằng nhãn:** id của bộ máy (`L-0001`…) gắn vào lệnh QC làm NHÃN (tag). Lệnh thị
trường khớp ngay trong lúc `market_order` còn chạy — trước khi lớp vỏ kịp cất vé — nên lúc khớp,
id được tra qua nhãn của lệnh, không qua bảng vé.

**Đóng gói** (`dong_goi_may`): một `main.py` mang cỗ máy (đã chuẩn hoá), bộ máy, lớp vỏ và
`CAU_HINH` (rổ, loại thị trường, ngày, vốn, khoá Object Store). Cỗ máy còn lỗi thì không đóng
gói. Đường đóng gói cũ (sơ đồ Entry/Manage) giữ nguyên từng byte.

**Chạy từ app** (`ViecQC`, chế độ Sáng tạo): soát NGAY tại máy, chưa gửi gì lên QC — cỗ máy còn
lỗi · rổ trống, mã sai dạng, quá 20 mã · loại thị trường lạ · ngày ngược — đều báo bằng câu tiếng
Việt. Chiến dịch (màn, boss của màn, nộp) cho cỗ máy 5 trạm chưa mở → nói thẳng thế (phần 6).
Mỗi lượt một khoá Object Store riêng `cat_studio/may-<vân tay>-<mã lượt>.jsonl.gz`, xoá khỏi
cloud ngay sau khi tải về. Lịch sử ghi lượt (rổ, ngày, lãi, boss = mua-giữ chia đều cả rổ từ lúc
hết khởi động, link QC); mở lại từ lịch sử là đọc file trên máy, không chạy lại, không gọi QC.

**Đọc kết quả** (`KetQuaMay`): cùng bề mặt với kết quả cũ (tóm tắt · lô «vì sao» · lệnh · soi
một lượt lên sơ đồ) để cửa sổ Màn chơi gọi cả hai mà không rẽ nhánh. Soi trả: trạm, đường đi,
cổng đã thử kèm vết từng điều kiện, nhãn khối theo đánh số của CHÍNH trạm đó. Dòng đặt lệnh mang
id lệnh để tra sang bảng Lệnh.

**Lô «vì sao» chỉ dòng có việc:** ② phát lại tín hiệu y hệt để gia hạn KHÔNG phải việc — bản ghi
mang `doi = False`, chữ thêm «(giữ nguyên, gia hạn)». ⚠ Gặp khi kiểm: không lọc thì một lượt 5
ngày × 4 mã ra 556 dòng «có việc», gần hết là gia hạn; lọc còn 79 dòng.

**Một giả định về QC, chờ bằng chứng thật:** tên API đã đối chiếu `quantconnect-stubs` (bản
18179); LEAN giả bắt chước những gì đã biết (QuoteBar giá giữa + spread · lệnh thị trường khớp
ĐỒNG BỘ ở giá ask/bid trước khi trả vé · lệnh chờ khớp ở nến sau · cấm đặt lệnh lúc khởi động).
Chạy trên tài khoản QC thật là bài nghiệm thu còn lại — trên máy người chủ, bằng khoá của họ.

**Bằng chứng:** `test_vo_may` 25/25 (ngoại hối · cổ phiếu, đường bị từ chối vì lô · crypto, lô
lẻ); `test_qc_may` 23/23 (soát trước khi gửi, chạy trọn, đọc lại, dọn cloud, lịch sử, mở lại).

## 22. ⭐ TRÌNH VẼ CỖ MÁY 5 TRẠM (D-10, phần 5)

> Giao diện: `webui/src/may/` (`MayApp` · `DaiTram` · `KhoiNode` · `KhoiDialog` ·
> `BatDauDialog` · `GomDialog` · `ThamSoMayDialog` · `MauPicker` · `ChonKhoiLam` ·
> `MayPicker` · `MayRibbon` · `OSo` · `doThi.ts` · `mayTypes.ts`). Python: 14 cửa `may_*`
> trong `api.py`, `may.soat_khoi`, kho cỗ máy trong `luu_tru`. Bài kiểm:
> `tests/test_may_api.py` (58), `webui/kiem/trinh_ve.mjs` qua `tests/test_trinh_ve.py`
> (28). Xem thử giao diện bằng trình duyệt: `tools/xem_thu.py`.

**Cửa sổ vẽ của app GIỜ LÀ trình vẽ 5 trạm.** Sơ đồ cũ Entry/Manage không còn lối vào nào
(`main.tsx` dựng `MayApp`); phần 7 xoá hẳn phần mã của nó.

**Ba luật, y luật sơ đồ cũ nhưng nhân cho năm:**

1. **Tài liệu là của Python.** Mọi thay đổi cấu trúc gửi CẢ cỗ máy sang `may_kem_the` +
   `may_soat`, rồi canvas vẽ lại từ cái nhận về. JS không ghép một mẩu chữ nào trên khối,
   không tự tính số thứ tự, không tự soát một luật nào.
2. **Một canvas = MỘT trạm** (luật gốc: một sơ đồ = một phạm vi chạy). Dải ①→⑤ ở trên để
   đổi trạm. Dải là một DẢI RIÊNG chứ không nổi trên canvas như pill cũ: năm trạm là cấu
   trúc của cỗ máy chứ không phải một lựa chọn thỉnh thoảng, và nổi lên thì nó che đúng
   khối Bắt đầu — khối nằm ở góc trái trên của MỌI trạm.
3. **Soát cả cỗ máy sau mỗi thay đổi.** Chấm đỏ trên từng trạm + bảng Vấn đề có nhãn trạm,
   bấm được để nhảy tới khối. Giấu lỗi của trạm kia thì bấm ▶ mới lòi ra.

**Hộp thoại khối** (`KhoiDialog`): mỗi lần vặn một núm, bản nháp thô bay sang
`may_luu_khoi` và nhận về khối đã chuẩn hoá + CHỮ sẽ hiện trên hộp + vấn đề của chính khối
đó. `may.soat_khoi` soát bằng chính bộ soát của trạm nhưng bỏ phần đồ thị: khối vừa tạo
đương nhiên chưa có gì phía sau, mà câu đó nổi lên trong hộp thoại chỉ làm người vẽ tưởng
mình gõ sai. Chỉ bày thứ dùng được Ở TRẠM NÀY — khối Làm của trạm đó, đại lượng trạm đó
đọc được (② không thấy «tín hiệu», ⑤ mới có «lệch mục tiêu»). Ô số nhận cả tên tham số.

**Khối Bắt đầu** có hộp thoại riêng (lịch — mỗi trạm chỉ mời lịch có nghĩa với nó · khung ·
ở ① là phạm vi: mọi mã của màn hay một danh sách riêng). **Gom** là bảng riêng, và nó hiện
MỌI vấn đề của trạm chứ không riêng vấn đề mang nhãn Gom: câu quan trọng nhất ở đây
(«Cho vào rổ» không có điểm mà Gom giữ N mã điểm cao nhất) gắn vào KHỐI.

**Lắp mẫu** (`MauPicker`): 22 mẫu theo trạm, nói thẳng hai điều bất ngờ nếu không nói —
lắp mẫu THAY CẢ sơ đồ của trạm, và núm vặn của mẫu thành tham số có tên, tên nào đã có thì
giữ giá trị đã chỉnh. Việc ghép vẫn do `mau_tram.ap_mau` làm.

**Nối sang Màn chơi:** ◆ Màn chơi (Ctrl+M) gửi cỗ máy đang trên canvas; `mo_qc` nhận cả hai
dạng tài liệu và soát mỗi dạng bằng bộ luật của CHÍNH nó. Chế độ Sáng tạo của cỗ máy nhận
một RỔ mã + loại thị trường (cỗ máy tự chọn mã ở trạm ①, đưa nó một mã là bỏ phí cả trạm
đó); Chiến dịch khoá lại kèm lý do (phần 6). SOI một lượt bắn ngược về trình vẽ: nhảy đúng
trạm, tô đường đã đi, tô cổng trượt tới tận dòng điều kiện hỏng; khối của lượt mà không còn
trên sơ đồ thì nói «cỗ máy đã đổi từ lúc chạy».

**Kho cỗ máy ở thư mục RIÊNG** `du_lieu/co_may/`, và mở lầm một chiến lược cũ bị CHẶN:
`may.chuan_hoa` của sơ đồ cũ trả về một cỗ máy TRẮNG hợp lệ, nên không chặn thì lưu lại là
mất hẳn chiến lược đó.

### 22.1 Xem thử giao diện bằng trình duyệt — `tools/xem_thu.py`

Cửa sổ pywebview không chụp được ảnh, không đọc được console, không có cách nào cho máy bấm
thử. `tools/xem_thu.py` phục vụ `webui/dist` kèm một vỏ `window.pywebview` giả gọi
`api.py` THẬT qua `fetch` — cùng bundle, cùng luật, chỉ khác đường vận chuyển. Phục vụ cả
`ApiQC` nên `?qc=1` xem được cửa sổ Màn chơi. KHÔNG phải lối chạy của app (lối đó vẫn là
`tools\chay.bat`), và `mo_qc` ở đó chỉ nạp cỗ máy chứ không mở nổi cửa sổ nào.

**Bằng chứng:** `test_may_api` 58/58 (từ điển đủ và JSON hoá nổi · 14 cửa khai đúng tham
số thật — bẫy `getfullargspec` của pywebview · lưu rồi mở lại cùng vân tay · 11 lời gọi rác
không cửa nào ném · lịch lạ rơi về mặc định của trạm · cảnh báo Gom gắn vào khối · qc_boot
dạng may5). `test_trinh_ve` 28/28 (số thứ tự lấy từ thẻ của CHÍNH trạm, vị trí khối không
mất khi đổi trạm, chấm đỏ đếm riêng từng trạm, lọc đại lượng/khối Làm theo trạm, luật ô
`khi`). Toàn bộ 24/24.

**Chỗ CHƯA có bằng chứng:** một lượt chạy THẬT trên tài khoản QuantConnect bằng khoá thật —
vẫn là bài nghiệm thu còn lại, trên máy người chủ (xem §21).

## 23. ⭐ MÀN CHƠI CHO CỖ MÁY 5 TRẠM (D-10, phần 6)

> `game.py` (màn, boss, chấm, sổ) · `qc_chay.ViecQC` (chạy theo màn, ghi vé, nộp) ·
> `mau_tram.MAY_SAN` (bốn cỗ máy dựng sẵn) · `webui/src/qc/ManChoi.tsx`. Bài kiểm:
> `test_qc_may` (cả vòng ▶ đầy đủ → vé → Nộp trên máy chủ QC giả), `test_may` (vân tay),
> `test_mau_tram` (cỗ máy dựng sẵn).

**Màn chia theo DẠNG tài liệu.** Màn của cỗ máy mang một RỔ mã và một loại thị trường;
màn của sơ đồ cũ mang một symbol. Hai dạng không dùng chung màn được: boss của rổ là
«mua giữ chia đều cả rổ», boss của một symbol là «mua giữ đúng symbol ấy» — cùng một màn
mà hai thước đo thì bảng điểm nói dối. (Phần 7 xoá hẳn màn của sơ đồ cũ.)

Chương 1 có ba màn: **Bộ bốn ngoại hối** (EURUSD · GBPUSD · USDJPY · AUDUSD) ·
**Vàng và bạc** (XAUUSD · XAGUSD, CFD) · **Bốn ông lớn** (AAPL · MSFT · GOOGL · AMZN).
Màn đã thấy là cả năm 2024, màn ẩn là 2025 — app giữ ngày, người chơi không chọn được.

**Boss «Mua rồi giữ cả rổ» không phải tính thêm:** bộ máy đã có `boss_pt` — lãi trung
bình của mọi mã kể từ lúc HẾT KHỞI ĐỘNG, đúng bằng lãi của một danh mục chia đều vốn mua
một lần rồi để yên. `game.cham` đọc nó, và đếm «sạch» bằng **lệnh ĐÃ KHỚP**: ở cỗ máy
không còn khái niệm "lệnh đóng", vị thế là một TỶ TRỌNG và đóng chỉ là đưa tỷ trọng về 0.

**Vân tay LOGIC** (chốt trong D-10, lúc làm phần 6). Vé nộp chấm theo vân tay, mà vân tay
cũ băm cả `id` khối — nên lắp lại y hệt một mẫu dựng sẵn (id mới toàn bộ, luật không đổi
một chữ) là MẤT vé, tức app nói dối "anh đã sửa cỗ máy". Nay:

* dây nối ghi bằng **nhãn đánh số** (`1 · 1A · 1A.1`) thay cho id;
* khối không có đường nối tới (không bao giờ chạy) **không vào** vân tay;
* đổi **thứ tự nhánh** VẪN đổi vân tay — nhánh xếp trên được thử trước, đó là luật chứ
  không phải cách bày.

**Nộp giữ nguyên luật của D-06:** lượt nộp chạy trên màn ẩn và chỉ trả con số tổng —
không ngày, không link QC, không đường vốn, không lượt; không mở lại được để xem từng
nến. Xem từng nến của màn ẩn là học thuộc đề thi.

**Bốn cỗ máy dựng sẵn** (`MAY_SAN`): Theo EMA · Bắt đáy RSI · Chọn mã mạnh nhất · Thận
trọng. Bốn Ý TƯỞNG khác nhau, không phải bốn biến thể; mỗi cái chỉ là một bộ năm mẫu nên
mở ra thấy đúng những khối tự vẽ được. ⚠ «Chọn mã mạnh nhất» cố ý KHÔNG chia theo độ tin
cậy: mẫu ② «Động lượng» không đặt độ tin cậy, ghép vào là cỗ máy mẫu mở ra đã có sẵn một
cảnh báo — thứ tệ nhất để đưa người chơi mới, vì họ không biết đó là lỗi của ai.

**Bằng chứng:** `test_qc_may` 38/38 — cả vòng Chiến dịch chạy trên máy chủ QC giả, với
dữ liệu seed theo khoảng ngày nên màn ẩn khác màn đã thấy thật; `test_may` 72/72 (9 kiểm
riêng cho vân tay); `test_game_qc` cũ đã nhập vào các bài trên ở phần 7.

## 24. ⛔ DỌN BỘ MÁY CŨ (D-10, phần 7)

Từ đây app chỉ còn MỘT thế giới: cỗ máy 5 trạm chạy trên QuantConnect.

**Xoá hẳn** (Python): `bo_chay` · `khop_lenh` · `so_lenh` · `tinh_toan` · `mau` (sơ đồ mẫu
Compress) · `nhat_ky` · `kho/` · `lean/cat_lean.py` · `lean/vo_qc.py` · `lean/do_nhip.py`
· `tools/dong_goi_lean.*` và 11 bài kiểm của chúng. **Giao diện**: `App.tsx` ·
`ActionDialog` · `Ribbon` · `TemplatePicker` · `ThamSoDialog` · `SettingsDialog` ·
`StepNode`, cùng toàn bộ kiểu của mô hình cũ trong `types.ts`. Tổng cộng ≈ 13.700 dòng.

**`core.py` 2296 → 673 dòng.** Giữ đúng phần cỗ máy dùng: đồ thị, đánh số, soát lỗi đồ
thị, id khối, bảng tham số, cài đặt. Cách cắt: đọc CÂY CÚ PHÁP, lấy mọi tên cấp cao nhất,
tìm tên nào còn được gọi từ ngoài, rồi giữ đóng truyền của chúng — cắt tay một file 2300
dòng là sớm muộn bỏ sót hoặc cắt nhầm. Hai chỗ phải gỡ bằng tay vì chúng KÉO cả bảng từ
vựng cũ theo: `step_title` (rơi về nhãn hành động cũ) và `_khoa_dieu_kien` (so hai cổng
bằng CHỮ hiển thị của mô hình cũ — nay so bằng chính JSON của điều kiện).

**Một công thức khoá Object Store** (`goi_qc.khoa_mac_dinh`): trước đây lúc đóng gói và
lúc tải về mỗi bên tự ghép tên khoá, mà `dong_goi_may` lại chỉ ghi khoá khi được truyền —
thiếu nó thì lớp vỏ chết GIỮA LƯỢT trên cloud, ở nơi xa nhất để dò.

**`tools/chay_qc.py` viết lại cho cỗ máy:** chạy một cỗ máy dựng sẵn hay một file `.json`
trên rổ mã tự chọn, hoặc `--man <id>` lấy đúng rổ và ngày của một màn Chiến dịch. In cả
boss cả rổ. Không chấm sao, không ghi vé — chấm là việc của app.

**Hộp thoại Kho** giờ gom thẳng từ từ điển 5 trạm: năm trạm · 14 khối Làm · 42 đại lượng
(kèm trạm nào đọc được) · cỗ máy dựng sẵn · file trên đĩa. Thêm một khối ở `tram.py` là
hộp thoại có ngay — không có danh sách thứ hai để quên cập nhật.

**Bỏ `numpy`** khỏi `requirements.txt`: bộ máy 5 trạm cố ý thuần Python, vì cùng một file
phải chạy được cả trên máy lẫn trên QuantConnect, nơi ta không chọn được thư viện.

**CÒN LẠI, cố ý:** `webui/src/app.css` vẫn giữ luật CSS của mấy hộp thoại đã xoá. Không
dọn bằng máy được — class của React Flow (`react-flow__handle`…) nhìn y như class chết vì
không component nào của ta viết ra chúng, xoá nhầm là canvas mất cổng nối. Dọn tay khi
nào sờ tới chính mấy luật đó.

**Bằng chứng:** `tools\chay_test.bat` 12/12 sau khi dọn; giao diện build sạch; app mở lên
vẫn đúng vòng chơi (đã soi bằng `tools/xem_thu.py`: trình vẽ, ◆ Màn chơi, Chiến dịch ba
màn, Sáng tạo theo rổ).

## 25. ⛔ BỎ BỘ MÔ PHỎNG TẠI MÁY — app chỉ là VỎ của QC (D-11)

> Xoá: `bo_may.py` · `chuoi_nen.py` · `nhat_ky_may.py` · `ket_qua_may.py` · `goi_qc.py` ·
> `lean/vo_may.py` · `tests/san_gia.py` · `tests/lean_gia.py` · `tests/qc_gia.py` ·
> `tools/chay_qc.py` và năm bài kiểm của chúng. Khoảng 5.800 dòng.

**Vì sao** (đo trước khi xoá, không phải cảm tính): ta đang tính lại những thứ QC làm
sẵn — gộp nến, 16 chỉ báo, «% vốn» → số lượng, huỷ lệnh hết hạn, trailing stop, lãi lỗ,
boss. Hai nơi cùng tính một thứ thì ra hai số. Rõ nhất: **nến H1 của ta cắt theo giờ UTC
chẵn, nến H1 của QC cho cổ phiếu Mỹ cắt theo giờ mở cửa sàn** — mở chart QC đối chiếu là
thấy lệch, mà ta không có gì để giải thích.

**Còn lại gì:** `tram` (từ điển) · `may` (định dạng + soát lỗi + vân tay) · `mau_tram`
(mẫu) · `core` (đồ thị, đánh số) · `luu_tru` · `game` (màn, boss, sao, sổ) · `qc_api`
(nói chuyện với QC: khoá, project, file, biên dịch, backtest, Object Store) · `qc_chay`
(soát đầu vào một lượt) · `api` + giao diện.

**Trạng thái thật của app:** vẽ được, soát lỗi được, lưu/mở được, lắp mẫu được —
**chưa chạy được**. Mọi cửa chạy trả đúng một câu (`ApiQC._CHUA_NOI`), và cửa sổ Màn chơi
nói nguyên văn câu đó ngay chỗ người chơi định bấm ▶. Cố ý không để nút bấm được rồi hỏng
ở đâu đó.

**Cái mất, đã biết trước:** không còn sàn giả để chạy thử trong vài giây. Bài kiểm còn 7
bài, và tất cả đều là bài kiểm TĨNH (từ điển, chuẩn hoá, soát lỗi, đánh số, cửa API, giao
diện). Từ nay "cỗ máy này giao dịch ra sao" chỉ trả lời được bằng một lượt chạy thật trên
QuantConnect.

**Việc kế tiếp (chưa thiết kế):** dịch sơ đồ 5 trạm thành một thuật toán QC dùng CHÍNH bộ
khung của họ — universe selection, indicator, insight, portfolio construction, risk
management, execution. Từ nay mỗi "item" trong game phải là một món có thật của QC.

## 26. ⛔ XOÁ TOÀN BỘ BỘ KHỐI CŨ (D-12)

> Xoá: `cat_studio/tram.py` · `may.py` · `mau_tram.py` · `tests/test_may.py` ·
> `test_mau_tram.py` · `test_may_api.py` · `test_trinh_ve.py` · cả thư mục
> `webui/src/may/` (14 file) · `webui/src/qc/ManChoi.tsx` · `webui/src/chung/` ·
> `webui/kiem/trinh_ve.mjs` · `webui/kiem/man_choi.mjs`. Khoảng 9.000 dòng.

**Vì sao, một câu:** D-11 chốt app không được tính gì về thị trường nữa, mà bộ khối cũ
chính là một bộ máy tính toán viết bằng hình hộp. Giữ nó thì D-11 không có thật.

**Vì sao, kỹ hơn:** bộ khối ấy trả lời câu hỏi "người chơi muốn vẽ gì" trước, rồi app
nhận phần tính toán về mình — 14 khối Làm, một bảng đại lượng, một bảng tham số, một ô
Gom mỗi trạm, tất cả đều do app định nghĩa và do app thực hiện. Muốn nó chạy được trên
QuantConnect thì phải có một bộ dịch biết mọi ô của mọi khối, và bộ dịch đó chính là bộ
máy thứ hai mà D-11 vừa xoá.

**Luật của bộ khối mới — ghi ở đây để khỏi trôi mất:** mỗi khối phải chỉ ra được MỘT
món có thật của QuantConnect đứng sau nó (một hàm API, một loại lệnh, một chỉ báo, một
bước trong khung 5 phần). Khối nào không chỉ ra được thì không được có. Cách kiểm nhanh:
hỏi "QC làm việc này bằng gì?" — không trả lời được bằng một dòng code QC thì khối đó
đang là phép tính của riêng ta.

**Còn lại gì trong gói:**
- `core` — đồ thị THUẦN: đánh số phân cấp (`1 · 1A · 1A.1`), thứ tự ưu tiên nhánh theo
  vị trí trên canvas, soát nối dây (vòng hở, nhánh chụm không đều, nhánh mặc định xếp
  sai, hai cổng trùng điều kiện). Nó chưa bao giờ biết "khối" là gì — chỉ biết `kind`,
  `type` (để nhận ra cổng rẽ nhánh) và `pos`. Nên nó sống sót nguyên vẹn, và bộ khối
  mới dùng lại được ngay.
- `luu_tru` (ghi/đọc JSON, không mở file ra xem) · `game` (màn, boss, sao, sổ nộp) ·
  `qc_api` (khoá, project, file, biên dịch, backtest, Object Store) · `qc_chay` (soát
  đầu vào) · `khung_cua_so` · khung giao diện.
- `webui/src/so.ts` + `webui/kiem/o_so.mjs` — bài học ô số: ép `Number()` ngay từng phím
  thì `"1."` thành `1`, React ghi đè, dấu chấm biến mất, `1.5` thành `15`. Bộ khối mới
  chắc chắn lại có ô số, nên bài kiểm này ở lại.

**Một lỗi thật mà việc dọn moi ra:** `HopKhoa` (hộp Khoá QC) gọi `qc_khoa`, nhưng hàm đó
nằm ở lớp `ApiQC` — bề mặt của cửa sổ Màn chơi, không phải cửa sổ chính. Trong app thật,
bấm vào là «api.py không có hàm qc_khoa». Không ai thấy, vì bản xem thử
(`tools/xem_thu.py`) phục vụ CẢ HAI bề mặt và tự định tuyến mọi tên `qc_*` sang `ApiQC`.
**Cầu nối giả nói dối một chỗ là cả cách kiểm bằng mắt mất giá trị.** Đã sửa tận gốc:
`api.py` còn đúng một lớp `Api`, `xem_thu.py` cũng chỉ phục vụ một bề mặt.

**Hai bài kiểm CSS chuyển sang chế độ NGỦ, không xoá:** `.menu-th-noi` (menu ⚙ nền đặc,
lật khi ở vế phải) và `.dong-dk` (hàng điều kiện phải là lưới, ô không tự đặt width) canh
ba cái bẫy đã hỏng thật, nhưng trên những thành phần vừa xoá. Mỗi phép kiểm giờ chỉ chạy
NẾU luật CSS tương ứng có mặt — trình vẽ mới dựng lại một menu nổi là nó tự thức dậy.
Xoá đi thì bẫy quay lại mà không ai canh.

**Giao diện hiện tại:** `webui/src/TrangTrong.tsx` — thanh tiêu đề, một câu giữa màn hình
nói app đang dựng lại, thanh trạng thái, và hai hộp thoại còn thật (Khoá QC, Kho). Cố ý
không để lại một trình vẽ rỗng: một canvas trống kèm thanh công cụ không bấm được thì
trông như app hỏng, chứ không như app đang được làm lại.

**Trạng thái:** 3 bài kiểm (`test_danh_so` · `test_giao_dien` · `test_o_so`) đều xanh,
`tsc --noEmit` sạch, `npm run build` sạch (CSS 57 KB → 7,7 KB). App mở lên được, đặt được
khoá, chưa vẽ và chưa chạy được gì.

**Việc kế tiếp:** thiết kế bộ khối mới + cách tương tác, bắt đầu từ danh sách những gì
QuantConnect thật sự cho.

## 27. ⭐ CHÉP HẠ TẦNG TRÌNH VẼ TỪ JENIFER_STUDIO (D-13)

**Nguồn:** `C:\Users\Davin\Desktop\Jenifer_Studio` — bộ tự động hoá Path of Exile 2
của chính chủ dự án. Hai lõi cùng dòng dõi (cùng cách đặt tên, cùng chú thích về bẫy
Auto_Clicker), nên phần lớn việc không phải chép mù mà là **mang lại thứ Cat_Studio đã
bỏ mất**.

**Vì sao tin được nguồn này:** template `trial chaos 30` là một sơ đồ THẬT ở quy mô
1.170 khối / 1.468 dây / canvas 19.367×16.055 — khoảng 60 màn hình ngang, 50 màn hình
dọc. Mọi con số thiết kế dưới đây đều đến từ việc phải sống được với quy mô ấy.

### Bốn hình của ngữ pháp sơ đồ

| Hình | Đo được trên `trial chaos 30` |
|---|---|
| Chuỗi gập thành **Nhóm** | 243 Nhóm ôm 2.253 hành động — không có nó thì canvas 3.180 hộp thay vì 1.170 |
| **Bảng tra vẽ ra** | 45/45 chỗ rẽ ≥3 nhánh ĐỀU đồng loại; nhánh thoát không cổng xếp cuối ở 28/45 |
| **Quay về** | 91 khối, 37 đích, 91/91 trỏ trong cùng một lớp |
| **Hình thoi** | 11 chỗ rẽ 7 nhánh ↔ 11 chỗ gộp 7 dây |

Độ rộng chỗ rẽ thực tế: 2 nhánh (173 chỗ) · 3 (13) · 4 (1) · 5 (8) · 7 (11) · 8 (4) ·
9 (8). **559/610 khối mở đầu nhánh là khối HỎI.**

### Thứ đã chép, và vì sao

- **Nhóm** — `core.py` từng TỪ CHỐI nó: *"gộp nhóm chỉ đẻ thêm câu hỏi nhóm có phải một
  đơn vị chạy không"*. Câu hỏi ấy có câu trả lời: **không**. Nhóm là một hộp ôm một
  chuỗi hành động chạy thẳng một lượt — đúng bằng ngần ấy khối lẻ nối thành hàng.
- **Quay về** — vòng lặp VẼ RA thay vì để ngầm. Vòng ngầm "mỗi nến chạy lại từ khối Bắt
  đầu" chỉ quay về đúng một chỗ; sơ đồ thật cần quay về GIỮA CHỪNG. Hai cách khai
  (đường ↻ mang số vòng, khối Quay về điền đích) đổ vào MỘT bảng `canh_vong`.
- **`KHOA_CANVAS`** (`pos`, `mau`, `ghim`, `hat_nhan`) — khoá tả CÁI NÚT, không tả việc
  khối làm. Bộ chạy, đánh số, bảng Vấn đề đều không đọc. `hat_nhan` ghi trên TỪNG khối
  chứ không thành danh sách riêng, nên lưu / mở / tự lưu / hoàn tác tự mang theo.
- **Hạt nhân** — gói một mảng sơ đồ thành một khung, bấm đúp vào trong. Lối vào / lối
  ra đều SUY RA từ dây, không ai khai. Vào trong rồi huy hiệu vẫn là số của CẢ sơ đồ.
- **Ô tìm** — không dấu, tìm cả số thứ tự, và bốn **lọc hỏi theo DÂY**: chia nhánh ·
  gộp nhánh · khối cuối · không chạy tới. Đây mới là cách soát sơ đồ nghìn khối.
- **Một cửa soát duy nhất** (`api.soat`) — số thứ tự + thẻ + Vấn đề + bảng vòng trong
  một lượt. Tách ba cửa thì ba lượt gọi có thể thấy ba trạng thái khác nhau.
- **Ba tầng lưu** — bản nháp dùng chung / bản tự lưu cạnh bản gốc (CHỈ đẻ khi nội dung
  thật sự khác đĩa) / lưu thật (xong là xoá bản tự lưu).
- **Phím tắt tra BẢNG** — không phải chuỗi `else if` (bản cũ có ba chỗ phải kèm cảnh
  báo cùng một lỗi: `ctrl && key==='g'` nuốt luôn Ctrl+Shift+G).

### Cố ý KHÔNG chép

Bộ song ngữ (Cat chỉ tiếng Việt), hệ chế độ (Cat chỉ một loại tài liệu), và mọi thứ
dính game. Khối "HĐ đặc biệt", "Loop", `--dacbiet` cũng để lại.

### ⚠ Bài học đắt nhất: khung xem thử không vẽ thì phép đo nói dối

`ResizeObserver` — thứ React Flow dùng để đo cỡ từng khối — **chỉ bắn trong nhịp vẽ**,
mà cửa sổ bị che là trình duyệt bỏ nhịp ấy. Hậu quả: đọc DOM bằng JavaScript thì thấy
đủ 8 khối nhưng **không một đường nối nào**, vì chưa đo được cỡ thì chưa tính nổi chỗ
cắm dây. Đã truy nhầm sang bản React Flow, bản React, StrictMode và CSS — rồi gắn máy
đếm vào `ResizeObserver` mới thấy `observe()` gọi 10 lần mà callback chạy 0 lần.
**Luật: chụp ảnh một nhát (ảnh ép trang vẽ) rồi mới tin phép đo.** Đã ghi vào đầu
`tools/xem_thu.py`.

### Một lần nữa, bài kiểm làm đúng việc của nó

`test_giao_dien` bắt được **năm biến CSS ma** theo bản chép vào (`--dacbiet`, `--mau`,
`--vong`, `--vong-soft`, `--surface-2`). Hai cái là màu vòng lặp phải khai thật, một
cái là biến JS đặt lúc chạy, hai cái còn lại đi kèm những luật CSS cho class mà Cat
KHÔNG hề vẽ ra — luật chết mang theo biến ma.

**Trạng thái:** trình vẽ chạy thật. **Bộ khối vẫn chưa có** — `Nhóm` / `Khối lẻ` /
`Quay về` còn trống ruột. Việc kế tiếp: nghĩ nội dung từng khối HỎI và LÀM.

---

## 28. ⭐ BỘ KHỐI: XÁC NHẬN và HÀNH ĐỘNG (D-14)

Bản chất cỗ máy giao dịch, theo đúng lời chủ dự án: **so sánh, rồi ra quyết định**.
Nên bộ khối chỉ có hai nửa — khối **HỎI** đọc thế giới và rẽ nhánh, khối **LÀM** đụng
vào thị trường. Hai từ điển: `cat_studio/hoi.py` và `cat_studio/lam.py`.

### Luật gốc, viết ở đầu cả hai file

> Mỗi mục phải chỉ ra được **MỘT thứ có thật của LEAN**. Ô `lean` chính là lời khai ấy.
> Không khai được thì không được có mặt.

Đây là D-11 ("app chỉ là VỎ của QuantConnect") biến thành một phép kiểm chạy được:
`test_hoi` và `test_lam` quét cả hai từ điển, thiếu một ô `lean` là trượt. Hộp thoại
Hành động còn **bày thẳng hàm LEAN nó sẽ gọi** ra màn hình — để người chơi kiểm được
lời hứa chứ không phải tin suông.

### Đã bỏ, vì chúng bắt app tự tính

`tỷ trọng hiện tại` (ta chia) · `số mã đang giữ` (ta đếm) · `số ngày đã giữ` (ta ghi
sổ) · `số nến đã chạy` (LEAN không đếm) · phép `cắt lên` / `cắt xuống` (so hai nến là
ta nhớ nến trước). `test_hoi` canh cả bốn cái tên ấy không được quay lại.

### Phép so chỉ có SÁU — và vì sao thế là đủ

`> < >= <= == !=`. Mọi phép "nhìn lại quá khứ" tan vào **chỉ báo** nhờ
`IndicatorExtensions` của LEAN (`Plus/Minus/Times/Over/Of/MIN/MAX`) cộng
`Delay/Maximum/Minimum`: "giá cao nhất 20 nến" là `MAX(20)`, không phải một phép so
thứ bảy. Nhờ đó không có toán tử nào do ta nghĩ ra.

### Năm loại HỎI, tám loại LÀM

| HỎI | hỏi về |
|---|---|
| thị trường · vị thế · tài khoản · lịch | giá/chỉ báo · mã đang giữ · cả túi tiền · bây giờ là lúc nào |
| doanh nghiệp | **tắt kèm lý do** — dữ liệu miễn phí chỉ có `fundamental/coarse` |

| LÀM | hàm LEAN |
|---|---|
| Đặt tỷ trọng | `SetHoldings` |
| Lệnh thị trường | `MarketOrder` |
| Đóng | `Liquidate` |
| Lệnh chờ | 7 hàm: `LimitOrder` / `StopMarketOrder` / `StopLimitOrder` / `TrailingStopOrder` / `LimitIfTouchedOrder` / `MarketOnOpenOrder` / `MarketOnCloseOrder` |
| Huỷ lệnh chờ | `Transactions.CancelOpenOrders` |
| Ghi chú | `Debug` / `Log` / `Error` / `Quit` |
| Vẽ lên bảng | `Plot` |
| Báo tin | `Notify.*` — **cảnh báo: backtest không gửi gì** |

Chia nhỏ như vậy vì **chọn loại là quyết định ĐẦU TIÊN**, mà nó cũng quyết luôn hộp
thoại bày ra cái gì: hộp Hỏi tài khoản không có ô mã, hộp Khớp-lúc-mở-cửa không có ô
giá. Một khối "so sánh bất cứ gì" thì hộp thoại phải bày mọi ô cho mọi trường hợp.

### ⚠ Đường ranh: ĐẶT thì được, SỬA thì không

- ✅ **Đặt** lệnh, và **huỷ hết** lệnh chờ của một mã — `CancelOpenOrders(mã)` là MỘT
  câu gọi, app không phải nhớ gì giữa hai nến.
- ❌ **Sửa một lệnh cụ thể** (`ticket.UpdateStopPrice`) — phải giữ cái ticket qua nhiều
  nến, tức sơ đồ sinh ra trạng thái, tức app lại có backend để mà gỡ lỗi.

Muốn dời cắt lỗ thì: **huỷ hết → đặt lại.** Hai khối, không nhớ gì. `test_lam` quét cả
từ điển tìm chữ `ticket` / `UpdateStop…` / `CancelOrder` và trượt nếu thấy.

**Cố ý bỏ:** `ComboMarketOrder` / `ComboLimitOrder` / `ComboLegLimitOrder` /
`ExerciseOption` — lệnh quyền chọn nhiều chân, cần cả một bộ chọn chuỗi quyền chọn.

### Ô `tag` — lời hứa "vì sao" do chính đoạn code tự ghi

LEAN nhận `tag` trên **mọi** hàm đặt lệnh, nên nó không phải sáng kiến của ta. Để
trống thì bộ sinh mã điền số khối + điều kiện vừa khớp. `test_lam` canh `tag` có mặt ở
đúng năm khối đụng tới lệnh và **vắng mặt** ở Ghi chú / Vẽ bảng / Báo tin — vì `Debug`,
`Plot`, `Notify` của LEAN không nhận tham số ấy.

### Soát ruột khối: chỉ bắt thứ hỏng LẶNG

Cổng không điều kiện thì LUÔN khớp (mọi nhánh dưới nó không bao giờ được thử) · số
lượng 0 (LEAN nhận rồi bỏ) · giá 0 (lệnh nằm trên sàn mãi không khớp) · tỷ trọng vượt
100% (LEAN từ chối nếu tài khoản không cho đòn bẩy) · `Quit` (cỗ máy thôi chạy từ đó) ·
đại lượng ĐÚNG/SAI đem vẽ `Plot` (Plot cần một con số). Lời khuyên kiểu "đòn bẩy thế
là cao đấy" KHÔNG thuộc về đây.

### Hai hộp thoại, không gộp

Khối Hỏi là **N dòng điều kiện giống nhau** nối bằng VÀ (muốn HOẶC thì vẽ thành hai
nhánh — ngữ pháp đã chốt ở D-13). Khối Làm là **một bộ ô cố định** do loại quyết định.
Gộp hai hình dạng ấy vào một hộp thì cả hai đều dở.

### ⚠ Ba chỗ hỏng LẶNG bắt được trong lúc làm

1. **Ô của nhánh mới bày số 0 trong khi Python đọc ra 0.05.** Đổi loại lệnh sang Dừng
   trượt thì ô "Khoảng trượt" chưa có giá trị; hộp thoại hiện `0`, còn `core.o_lam` rơi
   về mặc định của từ điển — thẻ khối nói "trượt 5%", hộp thoại nói "trượt 0". Hai nơi
   cùng ĐÚNG theo luật của riêng mình. Sửa: đổi ô cầm lái thì điền luôn mặc định cho
   nhánh mới, và lúc lưu thì BỎ ô của nhánh không chọn.
2. **`--font-mono` là biến CSS ma** — `test_giao_dien` bắt ngay trong lượt chạy đầu.
3. **Lớp `hien-tu-*` cũng là lớp ma.** `Ribbon.tsx` sinh `hien-tu-1090` và
   `hien-tu-1250` từ đầu mà `app.css` **chưa bao giờ có dòng nào** — hai nhóm "Hoàn
   tác" và "Strategy" không hề ẩn ở cửa sổ hẹp, suốt từ D-13. Nay ngưỡng gom vào một
   bảng `HIEN_TU` trong `Ribbon.tsx` và `test_giao_dien` đối chiếu bảng ấy với các lệnh
   `@media` — kể cả ngưỡng phải đúng `số - 1`.

**Trạng thái:** bộ khối đọc/ghi xong. **Bộ sinh mã chưa có** — sơ đồ chưa biến thành
thuật toán LEAN Python. Việc kế tiếp: ô của khối Bắt đầu (nhịp chạy, chạy cho mã nào),
rồi bộ sinh mã.

---

## 29. ⭐ KHỐI BẮT ĐẦU — nửa «thiết lập» của thuật toán (D-15)

**Cách tìm ra:** đọc **444 thuật toán Python thật** trong `Algorithm.Python/` của LEAN
— kho template và strategy mẫu của QuantConnect, bản gốc trên đĩa. Không suy đoán từ
tài liệu web.

### Phát hiện: một script có HAI nửa, sơ đồ ta mới vẽ một nửa

```
def initialize(self):      ← NÓI MỘT LẦN: ngày nào, bao nhiêu tiền, mã nào, nhịp nào
def on_data(self, data):   ← CHẠY LẠI mỗi nhịp: đọc, so, quyết, đặt lệnh
```

Các khối Hỏi/Làm nối dây là nửa dưới. Nửa trên **không có chỗ nào trên canvas** —
khối Bắt đầu trước D-15 có đúng một thứ: cái tên. Mà nửa trên gần như bắt buộc:

| Trong 444 thuật toán | Có mặt ở |
|---|---|
| `set_start_date` / `set_end_date` | **395 / 392** |
| `set_cash` | 250 |
| `add_equity` (+ forex/cfd/crypto/future/index) | 244 |
| `schedule.on` | 55 |
| `set_benchmark` · `set_brokerage_model` | 31 · 28 |

### Ba dòng mở đầu giống hệt nhau ở mọi chiến lược thật

Đọc kỹ hai cái kinh điển — `MACDTrendAlgorithm` và `MovingAverageCrossAlgorithm`. Cả
hai mở đầu `on_data` bằng đúng ba thứ:

1. **`if not slow.is_ready: return`** — chỉ báo chưa đủ dữ liệu *(47/444 file)*. Không
   có nó thì N nến đầu cỗ máy quyết trên số rác.
2. **"chỉ một lần mỗi ngày"**, tự nhớ hôm qua là ngày nào *(8 file)*. **Đây là cái ta
   KHÔNG được chép** — nó là TRẠNG THÁI. Người ta viết vậy vì không có cách khai nhịp;
   LEAN thì có (`Schedule.On`). Nên **ô `nhip` không phải một ô cho tiện: nó xoá hẳn
   một loại hack.**
3. **`fast > slow * (1 + 0.00015)`** — nhân một đại lượng với một số rồi mới so. Sáu
   phép so của ta chưa viết nổi. **Nhưng LEAN có sẵn:** `IndicatorExtensions` cho
   `Plus/Minus/Times/Over` với vế phải là một SỐ hoặc một CHỈ BÁO khác, kết quả là
   `CompositeIndicator` do LEAN tự tính. Nên cho phép ghép **không phá luật "không đẻ
   backend"**. Chưa làm — ghi lại để biết nó khả thi.

### MỘT khối ôm trọn, và nó giải luôn hai thứ tưởng phải đẻ khối mới

| Tưởng cần | Thật ra |
|---|---|
| khối **"Với mỗi mã"** | Không cần. Ô `nhip` + ô `ma` đã khai trọn vòng: *"mỗi nến, cho mỗi mã trong danh sách"*. Cả sơ đồ bên dưới là ruột vòng. Vòng vẫn HIỆN RA (luật D-13), chỉ là hiện ở đúng chỗ nó sinh ra. |
| cửa vào thứ hai (`schedule.on` riêng) | Chưa cần. Một nhịp đủ cho 287/444 thuật toán. Khi nào cần *"mỗi nến xem tín hiệu + cuối tháng cân danh mục"* thì thêm khối Bắt đầu thứ hai — và lúc ấy phải sửa hệ đánh số, vì nó đang neo vào đúng MỘT khối Bắt đầu. |

### Sáu ô

| Ô | LEAN gọi |
|---|---|
| Chạy trên mã nào *(danh sách, mỗi dòng một loại tài sản)* | `add_cfd` / `add_equity` / `add_forex` / `add_crypto` / `add_index` / `add_future` |
| Từ ngày → đến ngày | `set_start_date` · `set_end_date` |
| Vốn | `set_cash` |
| Nhịp *(8 lựa chọn)* | `Resolution.*` + `on_data` hoặc `schedule.on` |
| Mốc so sánh | `set_benchmark` |
| Sàn | `set_brokerage_model` |

**Nhịp gộp hai thứ của LEAN làm một.** Độ phân giải dữ liệu và lúc nào sơ đồ chạy là
hai câu trong script, nhưng với người chơi nó là MỘT câu hỏi: *bao lâu tôi xem một
lần*. Năm nhịp theo nến chạy thẳng trong `on_data`; ba nhịp hẹn giờ qua `schedule.on`
và **đăng ký dữ liệu PHÚT chứ không phải NGÀY** — dữ liệu ngày thì không có giờ nào
trong đó mà hẹn.

### Hai thứ KHÔNG thành ô — bộ sinh mã tự lo

- **Làm nóng** (`set_warm_up`): lấy chu kỳ dài nhất trong các chỉ báo đã vẽ. Đếm trên
  sơ đồ của CHÍNH TA, không tính trên dữ liệu thị trường, nên vẫn trong luật.
- **Khai chỉ báo**: `self.rsi("XAU", 14)` phải nằm trong `initialize`, và LEAN tự cập
  nhật mỗi nến — *"We never need to 'update' our indicators with the data, the engine
  takes care of this for us"* (chú thích trong `MovingAverageCrossAlgorithm`).

### ⚠ Hai chỗ hỏng LẶNG bắt được trong lúc làm

1. **`chuan_hoa_khoi` dựng lại khối Bắt đầu từ đầu, chỉ giữ cái tên** — tức sáu ô mới
   bay sạch mỗi lần lưu: hộp thoại điền xong, thẻ hiện đúng, lưu rồi mở lại là về mặc
   định. Nay nó dựng lại từ DANH SÁCH Ô CỐ ĐỊNH của từ điển — và đó đúng là chỗ chặn
   file rác mà `TIEP_TUC.md` vẫn ghi là còn thiếu.
2. **Mặc định là list/dict dùng chung.** Không chép sâu thì mọi khối Bắt đầu xài chung
   MỘT danh sách mã — sửa khối này là khối kia đổi theo. Bẫy cũ của Python, im lặng
   cho tới lúc có hai khối. `test_bat_dau` canh cả hai.

### Tiện thể: dữ liệu miễn phí có VÀNG

`Data/cfd/oanda/` đi kèm LEAN có **XAUUSD giá ngày từ 20/03/2006 đến 25/02/2019 —
3.948 ngày**, cộng dữ liệu phút/giây/tick vài ngày mẫu. Backtest vàng được ngay, không
trả xu nào. Nên khối Bắt đầu mặc định chạy trên XAUUSD.

**Trạng thái:** cả hai nửa của thuật toán đã khai được trên canvas. **Bộ sinh mã vẫn
chưa có** — sơ đồ chưa biến thành file Python chạy được. Đó là việc kế tiếp.

---

## 30. ⭐ BỘ SINH MÃ — sơ đồ thành thuật toán LEAN chạy được (D-16)

Đây là chỗ cả dự án quy về một câu của chủ dự án: *cái script và cái ta vẽ phải ra
cùng một thứ, chỉ khác cách trình bày*.

### Luật gốc: bộ sinh mã KHÔNG tự nghĩ ra một câu LEAN nào

Mọi câu nó viết đều lấy từ ô `lean` của ba từ điển, chỉ thay chỗ trống bằng giá trị.
Để làm được thế, **ô `lean` phải đổi từ lời khai sang BIỂU THỨC PYTHON CHẠY ĐƯỢC**:

| | trước | nay |
|---|---|---|
| đại lượng | `Securities[sym].Price` | `self.securities[sym].price` |
| chỉ báo | `RSI(sym, n)` | `self.rsi(sym, n)` |
| hành động | `SetHoldings(sym, ty_trong, …)` | `self.set_holdings({sym}, {ty_trong}, …)` |

Vì sao đáng đổi 68 + 8 chuỗi: **nếu `lean` chỉ là lời khai thì phải có một bộ chuyển
đổi ở giữa, và bộ đó sai thì sai ÂM THẦM.** Nay lời khai và đoạn code là MỘT. Thêm một
chỉ báo = thêm một dòng vào từ điển, không đụng bộ sinh mã.

Và bản LEAN này **392/444 thuật toán Python dùng snake_case, PascalCase không còn file
nào** — nên đổi casing cũng là bắt buộc, không phải chuyện thẩm mỹ.

⚠ Đổi xong lộ ra **một mục bịa**: `Delay(n)` khai là chỉ báo, mà grep
`QCAlgorithm.Indicators.cs` ra **0 chữ ký**. Nó là một LỚP dựng tay rồi `register_
indicator`, đúng như `DisplacedMovingAverageRibbon.py` làm — nên nó có thêm ô `lean_dk`
(dòng đăng ký).

### Ba thứ bộ sinh mã TỰ LO

Cả ba đều là đếm trên **sơ đồ của chính ta**, không phải tính trên dữ liệu thị trường:

1. **Nâng chỉ báo lên `initialize`.** Hai khối cùng viết RSI(14) dùng CHUNG một chỉ
   báo — khai hai lần là LEAN nuôi hai bộ đếm y hệt nhau.
2. **Làm nóng.** `set_warm_up(chu kỳ dài nhất)`.
3. **Vòng lặp nhiều mã.** Ô *nhịp* + ô *mã* của khối Bắt đầu đã khai trọn vòng.

### Hình dạng mã sinh ra — cố ý DỄ ĐỌC

Không sinh máy trạng thái, không sinh bảng nhảy. Khối Hỏi thành `if`, nhánh thành
`if/elif` (vì các làn được thử LẦN LƯỢT — ngữ nghĩa `is_branch_gate` đã chốt từ D-13),
khối Làm thành đúng một câu gọi:

```
if (self._cb[sym]['rsi_14'].current.value < 30):   # 1A · Quá bán?
    self.set_holdings(sym, 1.0, False, tag='[1A.1] RSI(14) < 30')
elif (self._cb[sym]['rsi_14'].current.value > 70): # 1B · Quá mua?
    self.liquidate(sym, tag='[1B.1] RSI(14) > 70')
```

Ô `tag` tự điền **số khối + điều kiện vừa khớp** — lời hứa D-11 *"chữ vì sao do chính
đoạn code tự ghi"*, và nó miễn phí vì LEAN nhận sẵn tham số ấy.

### CHƯA sinh được — báo rõ chứ không đoán

- **Vòng lặp** (khối Quay về, đường ↻). Trong một nến thì dữ liệu không đổi, nên chạy
  lại một đoạn chỉ cho đúng kết quả cũ; sinh bừa một `for` là sinh ra thứ sơ đồ không
  nói. Vòng DUY NHẤT có nghĩa trong giao dịch — mỗi nến, mỗi mã — thì khối Bắt đầu lo.
- **Mã lạ**: điều kiện trỏ tới mã chưa khai ở khối Bắt đầu. Tự `add_*` thêm là tự
  quyết hộ người chơi một đăng ký dữ liệu.

### ✅ ĐÃ CHẠY THẬT trên LEAN

Sơ đồ *vàng + RSI(14)*, XAUUSD giá ngày 2015–2018, dữ liệu miễn phí:

| | |
|---|---|
| Tổng lệnh | 15 |
| Lãi ròng | **+16,376%** |
| Tỉ lệ thắng | 71% |
| Sụt sâu nhất | 13,2% |
| Sharpe | 0,219 |

(Python 3.14 + QuantConnect.pythonnet 2.0.66 chạy được; lỗi *"GIL must always be
released"* lúc tắt là vô hại — kết quả đã ghi xong, đừng tin mã thoát, hãy đọc file.)

### ⚠⚠ BẪY LỚN NHẤT TÌM RA — và nó lặng hoàn toàn

Lần chạy ĐẦU ra **111 lệnh, lãi 0%, phí $0**. Mở `order-events.json` mới thấy cả 111
lệnh đều `invalid`:

> *The OandaBrokerageModel does not support MarketOnClose order type.*

Gốc rễ, truy trong `QCAlgorithm.Trading.cs`: nhịp **mỗi nến NGÀY** thì LEAN không có
giá trong ngày để khớp (`IsDailyResolutionOnly`), nên nó **tự đổi lệnh thị trường
thành MarketOnClose**. Mà `_supportedOrderTypes` của Oanda / Binance / Coinbase chỉ có
`[Limit, Market, StopMarket, StopLimit]`.

**Hậu quả:** backtest chạy hết, báo đủ thống kê, lãi 0% — và không một dòng lỗi nào
nổi lên. Nay `soat_khoi_bat_dau` cảnh báo đúng tổ hợp ấy (`bat_dau.SAN_KHONG_NHAN_MOC`,
danh sách đọc thẳng từ `Common/Brokerages/`). Đổi sàn sang Mặc định: **15 lệnh,
+16,376%**.

### Và một cảnh báo SAI đã sống từ D-14

`validate_flow_graph` đọc khoá `conditions` — thứ đã chết cùng bộ khối cũ (D-12). Nên
MỌI cặp cổng đều băm ra `[]` giống nhau và bị báo *"hai nhánh trùng điều kiện"*, kể cả
`RSI < 30` với `RSI > 70`. Cảnh báo sai thì người ta học cách bỏ qua nó, và lần nó
đúng cũng bị bỏ qua nốt.

**Trạng thái:** vẽ → sinh → chạy đã thông. Chưa có: chạy LEAN *từ trong app* (hiện
phải tự chạy tay), vòng lặp, chọn mã động, và lớp game.

---

## 31. ⭐ CHẠY LEAN TỪ TRONG APP, VÀ MÀN KẾT QUẢ (D-17)

Đoạn cuối của vòng *vẽ → sinh → **chạy** → **đọc** → sửa*. Trước nó phải gõ tay ba
bước; nay bấm một nút.

### Cụm nút chính — ghim sát mép phải, tô sáng

`Sinh mã · Chạy · Tối ưu · Chạy thật · Kết quả`, xếp đúng thứ tự việc như thanh của
QuantConnect. Hai nút cuối cùng chưa có thì **bày ra mờ** kèm lý do, không giấu đi —
giấu thì không ai biết còn thiếu gì.

⚠ **Phải GHIM, không được đẩy bằng `margin-left: auto`.** Ribbon có bảy nhóm nên nó
luôn dài hơn cửa sổ; đẩy chỉ ăn khi còn chỗ trống, nên cụm chính trôi hẳn ra ngoài
màn hình. Nay ribbon chia hai vùng: trái tự cuộn, phải đứng im.

### Bộ chạy — ba cái bẫy, cả ba đã cắn thật

1. **ĐỪNG TIN MÃ THOÁT.** pythonnet ném *"GIL must always be released"* lúc tắt, SAU
   khi kết quả ghi xong xuôi. Mã thoát khác 0 mà backtest thì hoàn hảo.
   **Luật: đọc file, đừng đọc mã thoát.**
2. **PHẢI GỘT SẠCH BIẾN MÔI TRƯỜNG CỦA VENV.** App chạy trong `.venv` (không có
   pandas); LEAN nạp Python qua `PYTHONNET_PYDLL`, mà `VIRTUAL_ENV`/`PYTHONHOME`
   còn sót thì nó trỏ vào venv rồi chết vì thiếu pandas — thông báo chẳng nhắc gì
   tới venv.
3. **`config.json` của LEAN có chú thích `//` và dấu phẩy thừa.** Gột phải biết đang
   ở TRONG CHUỖI hay không: một giá trị `https://…` mà cắt từ `//` là mất nửa đường
   dẫn.

Chỗ đặt LEAN là **một cấu hình người dùng phải điền** — không đoán hộ, vì LEAN là
một kho mấy trăm MB.

### Màn Kết quả — dựng theo ảnh chụp, bằng mã của ta

Chủ dự án đưa 11 ảnh chụp trang backtest thật (lưu ở `tai_lieu/backtest/`). **Mã
giao diện của QuantConnect thì không chép** — đó là mã nguồn của họ, và chép cũng vô
dụng: trang ấy là một ứng dụng React, HTML lấy về chỉ là hộp rỗng, biểu đồ do
JavaScript của họ vẽ lúc chạy. Nên bố cục và từng khả năng thì dựng lại, bằng mã của
ta, nền tối của ta.

Và **không phải tính gì cả** — LEAN ghi sẵn mọi thứ:

| Trên ảnh | Trong file LEAN |
|---|---|
| 8 ô số trên đầu | `runtimeStatistics` — đúng 8 mục, đúng tên ấy |
| Select Chart — 8 biểu đồ | `charts` — đúng 8 cái, đúng tên ấy |
| Đường vốn kiểu **nến** | `Equity` seriesType=2, điểm `[giây, mở, cao, thấp, đóng]` |
| Tab Return cạnh Equity | `Return` seriesType=3 (cột) |
| Treemap Assets Sales Volume | seriesType=7 |
| Thống kê trượt 1/3/6/12 tháng | `rollingWindow` — 436 cửa sổ |
| Server Statistics | `serverStatistics` |

**CỐ Ý KHÔNG DỰNG,** và nói rõ chứ không giả vờ quên: **Research Guide** (đếm
backtest còn lại — dịch vụ đám mây của họ) · **Share Results** (chia sẻ lên web của
họ) · **Report** (bản báo cáo có logo và bố cục riêng của họ).

### ⚠ Một chỗ CỐ Ý LÀM KHÁC bản web

Bảng «Strategy Equity» có hai đại lượng khác thang hẳn nhau — vốn tính bằng ĐÔ, lợi
suất tính bằng PHẦN TRĂM. Chồng cả hai lên một khung với **hai trục dọc** là trò nói
dối bằng tỉ lệ: hai đường cắt nhau ở chỗ do người vẽ chọn thang, chứ không phải chỗ
có thật. Nên **mỗi đơn vị một DẢI RIÊNG xếp chồng**, dùng chung trục ngang. Nhìn vào
gần như y hệt (bản web cũng tách nến lên trên, cột lợi suất xuống dưới), mà không
còn chỗ cho phép so sánh sai.

### ⚠ Bớt điểm phải GỘP, không được nhảy cách

Một lượt chạy nhịp PHÚT đẻ ra hàng trăm nghìn điểm mỗi đường. Nhảy cách (lấy 1 trong
mỗi N) làm **mất đỉnh và đáy**: một cú sụt gọn trong vài nến biến mất khỏi biểu đồ mà
người xem không hề biết. Nay gộp theo rổ — nến lấy mở-đầu/cao-nhất/thấp-nhất/đóng-cuối,
đường giữ cả đỉnh lẫn đáy của rổ.

### ⚠ Để trống «Mốc so sánh» KHÔNG phải là không có mốc

`DefaultBrokerageModel.GetBenchmark` trả về **SPY**. Tức cỗ máy vàng bị đem so với cổ
phiếu Mỹ, và không một dòng nào nói ra. Nay câu gợi ý nói thẳng, và biểu đồ ghi đúng
tên mốc thật thay vì «Mốc so sánh» chung chung.

**Trạng thái:** vẽ → sinh → chạy → đọc đã thông trọn vòng. Chưa có: Tối ưu, Chạy
thật, vòng lặp trong mã sinh ra, chọn mã động, lớp game.
