# Cat_Studio — Sổ ghi cốt lõi

> App vẽ pipeline + mô phỏng hành vi chiến lược giao dịch.
> Fork từ **Auto_Clicker** (`C:\Users\Davin\Desktop\Auto_Clicker`), đổi miền từ *click game* sang *trading*, nối MT5 về sau.
>
> File này là **nguồn sự thật về Ý ĐỊNH**. Code là nguồn sự thật về hành vi.
> Sửa cơ chế → sửa file này cùng lúc, đừng để hai bên nói khác nhau.

> ⚠ **FILE NÀY ĐÃ BỊ CẮT MỘT NỬA** (2.403 → ~1.000 dòng) trong lần dọn Cat_Studio sang
> HFT market maker. Mọi chỗ cắt đều để lại một dòng `<!-- ĐÃ CẮT (đợt 4): … -->` nói rõ
> mất gì; đọc bản đầy đủ bằng `git show f1c90fb:tai_lieu/core.md`.
>
> Cái đi: §7 chiến lược mẫu D_02 · §12 toàn bộ thiết kế Strategy Tester · §6.4 bảng
> tham số · §11 kế hoạch cũ, cùng mấy mục nhật ký về MT5.
>
> **Cái ở lại là phần KHÔNG dính sàn nào và cũng KHÔNG dính chiến lược nào** — và đó
> đúng là phần đã sống sót qua cả D_02 lẫn MT5:
> §3 cơ chế đánh số · §4 ghim số ⟲ và khối Bắt đầu · §5 luật rẽ nhánh · §6.1 mỗi sơ đồ
> là một vòng lặp · §6.2 hai loại khối · §8 giao diện · §9 định dạng file · §10 môi
> trường.
>
> **§6.0 và §6.3 thì viết lại hẳn**, không phải cắt: hai sơ đồ Entry/Manage thành MỘT sơ
> đồ Báo giá, ba động từ thành HAI (`check_cond` · `so_hang`), và từ vựng nến/ATR/R
> thành từ vựng spread/tồn kho. Bản cũ đọc ở cùng chỗ.
>
> Ổ cắm nào đang trống thì xem `tai_lieu/o_cam_trong.md`.

Cập nhật: 2026-08-28 · Trạng thái: **vẽ và soát được chiến lược MM, chưa chạy được** ·
test 7 bài

---

## 0. Một câu

> Vẽ sơ đồ khối cho một chiến lược giao dịch, mỗi khối mang **một số thứ tự do chính bộ máy tính ra**,
> bấm ▶ Chạy thì mở **Strategy Tester** để xem chiến lược đó hành xử ra sao.

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
- `ticket` của MT5 chỉ là **một cột phụ**, để trống khi backtest.
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
   vòng lặp chạy lại mỗi sự kiện (§6.1), nên không khớp nhánh nào = **hết lượt**, lượt sau
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

<!-- ĐÃ CẮT (đợt 4): §4.3 Bấm ▶ Chạy → cửa sổ Strategy Tester. -->

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

Không nhánh nào khớp thì **hết lượt** — sự kiện sau chạy lại từ khối Bắt đầu. Đó là cách
"chờ" được diễn tả, và là trường hợp thường gặp nhất, KHÔNG phải lỗi.

---

## 6. Bộ khối & hành động của Cat_Studio

### 6.0 ⭐⭐ MỘT CHIẾN LƯỢC = MỘT SƠ ĐỒ

```
   ┌── Sơ đồ BÁO GIÁ ────────────────────────────────────┐
   │  chạy MỘT LƯỢT mỗi SỰ KIỆN sổ lệnh                  │
   │  phát biểu lại TOÀN BỘ báo giá: bid · ask · lot     │
   │  chốt ở cuối lượt, không phát biểu gì thì giữ nguyên │
   └─────────────────────────────────────────────────────┘
```

> ⚠ **Bản D_02 có HAI sơ đồ: ENTRY đi săn và MANAGE quản từng lệnh đang sống**, với
> luật *Entry chỉ TẠO · Manage chỉ SỬA* soát tĩnh được — món quà lớn nhất của việc
> tách tab, và là loại lỗi MQL5 không bao giờ bắt.
>
> **Nó không bị bỏ vì lười — nó mất ĐỐI TƯỢNG.** Market maker không "vào lệnh" rồi
> "quản lệnh" ở hai nhịp khác nhau: mỗi sự kiện, cả sơ đồ chạy lại và phát biểu lại
> báo giá từ đầu. Cái vừa treo bị huỷ, cái mới treo lên — không có "lệnh đang sống"
> nào để chạy một vòng riêng cho nó.
>
> Cơ chế nhiều sơ đồ thì **giữ nguyên ở cả hai đầu** (`core.TABS` · `ACTION_TABS` ·
> `PillTab`, và pill tự ẩn khi chỉ có một). §3 — lớp khớp lệnh — có thể cần sơ đồ thứ
> hai; lúc đó không phải dựng lại.

**MỘT LƯỢT PHÁT BIỂU = MỘT TRẠNG THÁI ĐẦY ĐỦ.** Sơ đồ dựng dần năm ô rồi chốt:

```
   cong_bang                giá công bằng — gốc để đo mọi thứ khác
   bien_mua · bien_ban      treo cách công bằng bao xa, mỗi phía
   lech                     dịch CẢ HAI phía để đẩy tồn kho về 0
   lot_mua  · lot_ban       khối lượng mỗi phía

   bid = cong_bang − lech − bien_mua       (lot_mua)
   ask = cong_bang − lech + bien_ban       (lot_ban)
```

**KHỚP LỆNH KHÔNG CẦN XỬ LÝ RIÊNG** — và đây là chỗ mô hình này gọn hơn hẳn bản cũ.
Lệnh khớp thì tồn kho đổi; sự kiện kế tiếp chạy lại sơ đồ, `lệch` đọc tồn kho mới và
báo giá tự dịch theo. Không có "sau khi khớp thì làm gì" để vẽ, vì không có trạng thái
nào cần nhớ giữa hai lượt.

### 6.0b ⭐ TẦNG CỔNG VÀ TẦNG TÍNH — vì sao KHÔNG phải cây quyết định

Đây là quyết định thiết kế đắt nhất của cả phần từ vựng, nên phải ghi rõ.

Một cây quyết định sạch (rẽ nhánh cho từng tình huống) **không mở rộng được**: k yếu tố
độc lập cần **2^k nhánh**. Chợ động thì giãn biên · đang ôm hàng thì lệch · sổ lệnh mất
cân thì dịch công bằng — ba yếu tố đã là tám nhánh, mà chúng có gì loại trừ nhau đâu.

Chuỗi số hạng cộng dồn thì cần **k dòng**:

```
   [2]  công bằng  =   mid
   [3]  biên       =   1 × spread
   [4]  lệch      +=   tồn kho × 0,5 tick/lot
   [5]  lot        =   500
```

Nên chia làm hai tầng, theo đúng bản chất của thứ đang hỏi:

| tầng | dùng khi | hình dạng |
|---|---|---|
| **cổng** | trạng thái **loại trừ nhau**, hiếm — mù thì rút, không tính gì nữa | rẽ nhánh |
| **tính** | thứ **chồng lên nhau**, đường thường | chuỗi số hạng |

Và điều kiện gắn lên **chính khối số hạng** (ô `khi`) chứ không thành cổng riêng: hai
hạn mức tồn kho làm bằng cổng là bốn nhánh, làm bằng `khi` là hai dòng và chuỗi vẫn
thẳng.

**Cái giá phải trả, ghi ra để không quên:** thứ tự trong chuỗi **LÀ ngữ nghĩa** — đổi
chỗ hai khối là đổi kết quả.

```
   biên = 1 × spread   rồi   biên += 2 tick     → 1 spread + 2 tick
   biên += 2 tick      rồi   biên = 1 × spread  → 1 spread. Hai tick BỐC HƠI.
```

Không chỗ nào khác lộ ra điều đó: sơ đồ nhìn vẫn hợp lý, chỉ có một số hạng lặng lẽ
không bao giờ có tác dụng, mà bảng lãi lỗ thì không biết kêu. Nên `core._soat_ghi_de`
**cảnh báo** (không chặn — đặt lại giữa chừng vẫn có thể là cố ý).

### 6.1 ⭐ MỖI SƠ ĐỒ LÀ MỘT VÒNG LẶP

> Sơ đồ chạy lại **từ khối Bắt đầu ở MỖI SỰ KIỆN SỔ LỆNH** — không có gì chạy nền cả.
>
> ⚠ Bản D_02 nói "mỗi NẾN MỚI", đúng như `OnTick` của MQL5 chạy lại từ đầu mỗi tick.
> Đổi nhịp chứ không đổi cơ chế: nhịp giờ là một bản ghi `bookTicker` hoặc một lệnh
> khớp (`cat_studio/phat_lai.py`), tức nhanh hơn nhiều bậc, nhưng luật *chạy lại từ
> đầu, không nhớ gì giữa hai lượt* thì y nguyên. Đó là lý do cả §6.1 này sống sót.

Hệ quả, và nó gỡ được rất nhiều thứ:

- **"Chờ tới khi" KHÔNG phải vẽ.** Không cổng nào khớp → hết lượt → sự kiện sau tự chạy
  lại. Bản vẽ tay đầu tiên của sơ đồ mẫu D_02 có **5 vòng tự-lặp + 3 mũi tên "quay lại
  1"**; cả 8 cạnh đó biến mất.
- **Không cần loại khối "Vòng theo dõi".** Nó chỉ là cái vòng lặp lớn vẽ lại lần nữa
  ở bên trong.
- **Trạng thái không cần khối.** `IDLE / COUNTING / CONFIRMED / PENDING / CONSUMED` của
  `FilterEngine` tồn tại vì MQL5 **không có đồ thị** — mỗi tick nó chạy lại từ đầu nên
  phải tự nhớ đang ở đâu. Ta có đồ thị, và trạng thái vùng nén là **dữ liệu đọc được**
  qua toán hạng (`số_nến_nén`, `đỉnh_vùng`, …), không phải khối.

### 6.2 HAI LOẠI KHỐI — hết

| kind | Nghĩa |
|---|---|
| `start` — **Bắt đầu** | Điểm neo: mỗi sự kiện chạy lại từ đây. Đúng một cái, không xoá được, không nhận đường vào (§4.2). |
| `action` — **Khối** | Đúng một hành động. Mang `check_cond` thì nó là **cổng rẽ nhánh**. |

**Đã bỏ `Vòng theo dõi` và `Nhóm 1 lần`:**

- *Vòng theo dõi* — thừa, xem §6.1.
- *Nhóm* — cấu trúc của một chiến lược đến từ **tách trách nhiệm**, không từ lồng hộp.
  Gộp nhóm chỉ đẻ thêm câu hỏi "nhóm có phải một đơn vị chạy không".
- Kéo theo: **bỏ template cụm khối rời**. Một template phải là thứ **chạy được** —
  cụm khối rời mở ra là một mớ khối lạc không có đường vào, dán xong vẫn phải nối lại
  từ đầu. `TEMPLATE_KINDS` chỉ còn `strategy`.

### 6.3 HAI ĐỘNG TỪ — hỏi · góp một số hạng

> **Bản D_02 có BA:** `check_cond` · `vao_lenh` (tạo vị thế: Mua/Bán · Market/Stop/Limit
> · lot · SL & TP ban đầu) · `sua_lenh` (dời SL · dời TP · hoà vốn · trailing · đóng một
> phần · đóng hẳn · huỷ chờ). Cả hai động từ sau nói về một thế giới có **LỆNH RỜI mang
> SL/TP riêng**, nên chúng không dịch sang market maker được — không phải đổi tên.
> Bảng đối chiếu đầy đủ: `git show f1c90fb:tai_lieu/o_cam_trong.md` §11.

| key | Nhãn | Việc |
|---|---|---|
| `check_cond` | **Kiểm tra điều kiện** | ĐỌC thị trường + tồn kho rồi quyết đi nhánh nào. **Đây là CỔNG rẽ nhánh.** |
| `so_hang` | **Số hạng** | Góp MỘT số hạng vào báo giá: `đích` · `phép` · `lượng` · `khi` (tuỳ chọn) |

**KHÔNG CÓ động từ "rút" hay "tắt một phía"** — chúng chỉ là `lot = 0` và `lot_mua = 0`.
Đây chính là lãi của việc tách `lot_mua`/`lot_ban` ngay từ đầu: hai động từ nữa biến
mất, và hộp vẫn nói rõ hậu quả (`→ rút hết báo giá`) nên không ai phải nhớ luật.

**Động từ thứ ba CÒN THIẾU và nó có thật:** tồn kho chạm hạn mức CỨNG thì phải đóng
chủ động bằng lệnh taker, không chờ ai lấy hàng. Nó không nhét vào ngữ pháp số hạng
được — một số hạng *góp vào* báo giá, còn cái này *vứt* báo giá đi và bắn một lệnh ăn
ngay. Xem `o_cam_trong.md` §12; phải đợi §3 mô hình khớp.

#### Bốn trường của một số hạng

| trường | nhận gì |
|---|---|
| `đích` | `công bằng` · `biên` (tách được `biên mua`/`biên bán`) · `lệch` · `lot` (tách được `lot mua`/`lot bán`) |
| `phép` | `=` · `+=` · `×=` — `×=` **chỉ** cho `lot` |
| `lượng` | `hệ_số × toán_hạng`, kèm thước đo |
| `khi` | một điều kiện, cùng hình dạng với điều kiện của cổng |

**`×=` chỉ cho `lot`** vì nhân một mức giá hay một bề rộng với hệ số không có nghĩa vật
lý nào — *"gấp đôi giá công bằng"* là gì?

**Tách mua/bán NGAY TỪ ĐẦU** dù chiến lược sơ cấp chưa dùng: miễn phí bây giờ, đắt về
sau. Ngày muốn biên lệch hai phía thì không phải đổi mô hình.

#### Toán hạng — 8 cái, và vì sao đúng 8

Suy thẳng từ bản chất một market maker, không thêm cái nào cho đẹp
(`cat_studio/kho/nen_tang.py`):

| Nhóm | Toán hạng |
|---|---|
| Sổ lệnh | `bid` · `ask` · `bid_kl` · `ask_kl` · `mid` · `spread` |
| Của ta | **`ton_kho` (±lot, CÓ DẤU)** |
| Sức khoẻ | `co_so` — có nhìn thấy sổ lệnh không |

`bid_kl`/`ask_kl` **chính là hàng đợi** — khối lượng đang đứng TRƯỚC ta ở đỉnh, thứ
duy nhất quyết định có được khớp hay không. Dấu của `ton_kho` là toàn bộ ý nghĩa của
nó: bỏ dấu đi thì không lệch báo giá được, mà lệch theo tồn kho là thứ quan trọng nhất
của quản trị rủi ro market making.

⚠ **KHÔNG có SL, TP, R, ATR, zone.** Market maker quản rủi ro ở mức **TỒN KHO**, không
ở từng lệnh — nên cả cụm từ vựng đó không có chỗ đứng, không phải "chưa làm".

Bốn cái đáng thêm ngay sau (`microprice` · `bien_dong` · `tuoi_bao_gia` · `lech_luong`):
`o_cam_trong.md` §11.

#### Đơn vị — ba thước, và một thước GHÉP được suy ra

| `tinh` | Nghĩa |
|---|---|
| `tick` | bước giá NHỎ NHẤT của sàn. Bắt buộc phải có: không treo được lệnh ở giá tuỳ ý |
| `spread` | thước TỰ NHIÊN của nửa biên — đúng nghĩa trên mọi symbol, mọi thang giá |
| `bps` | phổ quát, để so giữa các symbol khác thang giá |
| `gia` | số tuyệt đối. Giữ vì đôi khi cần gõ thẳng, nhưng nó KHÔNG chuẩn hoá |

**Đơn vị ghép thì SUY RA, không bảng nào khai nó.** Khi lượng nhân với một toán hạng,
hệ số mang đơn vị `<đơn vị đích>/<đơn vị toán hạng>`:

```
   lệch += tồn kho × 0,5 tick/lot     ← "mỗi lot tồn kho thì dịch nửa tick"
```

Suy chứ không khai vì một bảng đơn vị ghép sẽ phình theo **tích số** của hai danh sách,
và mỗi lần thêm một toán hạng lại phải nhớ thêm mấy dòng vào đó.

#### CHỈ BÀY RA THỨ DÙNG ĐƯỢC — luật cũ, đối tượng mới

Luật chung giữ nguyên từ bản D_02: *"bày ra một lựa chọn vô nghĩa rồi soát tĩnh mắng là
tệ hơn không bày — nên lọc ngay tại nguồn."* Bốn nhát cắt của D_02 (theo chỗ dùng · theo
loại đại lượng · không đo bằng chính nó · theo zone) rút còn ba, và cả ba đều bắt loại
lỗi **CHẠY ĐƯỢC MÀ SAI** — thứ backtest không tố cáo, vì backtest chỉ biết lãi hay lỗ
chứ không biết câu lệnh có nghĩa hay không:

| Cắt gì | Vì sao | Bảng |
|---|---|---|
| **MỨC giá ⟷ BỀ RỘNG giá** | `công bằng = spread` là đặt giá công bằng bằng bề rộng spread. `mid / mid × 10⁴` luôn ra 10000 | `TOAN_HANG_LOAI` · `DICH_KIEU` |
| Theo **loại đại lượng** | `tồn kho ≥ 2 tick` — so một số ĐẾM với một bề rộng GIÁ | `TOAN_HANG_DON_VI` |
| **Đại lượng giá tự mang đơn vị** | `spread × 2 tick` không quy được về đâu | `_soat_luong` |

Đúng/sai là **một PHÉP SO** (`là ĐÚNG` / `là SAI`), không phải một ô tick riêng — nhờ
vậy mọi điều kiện có cùng một hình dạng `[đại lượng] [phép] [lượng]`, hết ngoại lệ.
*"Có thấy sổ lệnh bằng 1"* là câu không ai đọc được.

#### CHUẨN HOÁ ĐƯỢC SỬA, KHÔNG ĐƯỢC ĐOÁN

Ranh giới này dễ trôi nhất về sau, nên chốt ở đây và chốt bằng bài kiểm
(`tests/test_ngu_phap.py`):

| tình huống | chuẩn hoá làm gì | vì sao |
|---|---|---|
| `lot = 500 tick` | **SỬA** → đơn vị `lot` | lot không đo bằng gì khác được — không có gì để chọn nhầm |
| `biên = spread × 2 tick` | **SỬA** → bỏ thước thừa | `spread` đã tự mang đơn vị |
| `biên ×= 2` | **GIỮ NGUYÊN** | phép sai, và câu lỗi đã có sẵn. Lặng lẽ đổi thành `biên = 2` là đổi Ý NGHĨA rồi bày ra như thể người dùng viết vậy |
| `biên = 2` (thiếu thước) | **GIỮ TRỐNG** | 2 tick và 2 bps là hai lượng khác nhau — điền hộ là tự chọn một con số khác |
| điều kiện trỏ vào đại lượng đã biến mất | **GIỮ** | vứt đi thì cổng thành rỗng và app nói "chưa có điều kiện nào" — đúng hình thức, lạc đề. Gỡ một module trong `kho/` sẽ lặng lẽ ăn mất điều kiện của MỌI chiến lược |

> Một câu: **sửa khi chỉ có đúng MỘT khả năng, giữ nguyên khi có nhiều hơn một.**

<!-- ĐÃ CẮT (đợt 4): §6.4 BẢNG THAM SỐ — hằng số có tên, cảnh báo "số gõ tay hai chỗ", nút đặt tên. -->

<!-- ĐÃ CẮT (đợt 4): §7 Chiến lược mẫu Compress (D_02) — ý tưởng, bốn bước, hình học vào lệnh, luật hướng, máy trạng thái nén, bộ tham số, hai lỗi có thật trong EA. -->

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
| **Thêm khối** | Loop · Nhóm · HĐ lẻ · Rẽ nhánh · Delay | **Kiểm tra ĐK** · **Số hạng** |
| **Template** | Lưu ▾ (Process/Loop/Nhóm) · Mở ▾ | Lưu ▾ · Mở ▾ — **chỉ cả chiến lược**, không lưu cụm khối rời |
| **Sửa** | Sửa · Nhân bản · Xoá | *(y hệt)* |
| **Luồng** | Đặt số ① · Xem điểm | Đặt số ① · **Ghim số ⟲** · Vừa khung |
| **Hoàn tác** | Hoàn tác · Làm lại | *(y hệt)* |
| **Template** | Lưu ▾ · Mở ▾ | *(y hệt)* |
| *(mép phải)* | Tên Process · Chờ Ns · ▶ Chạy / ■ Dừng | Tên chiến lược · Symbol · **● Live** · **▶ Test** |

### 8.4 Menu chuột phải

Hỗ trợ sẵn: menu con (`con`), vạch ngăn (`ngan`), mục mờ **kèm lý do** (`tat` + `viSao`).
> Mục bị tắt vẫn **HIỆN** kèm lý do — giấu đi thì người dùng tưởng tính năng không tồn tại.
> Mờ mà không nói vì sao là bực nhất.

| Bấm phải vào | Mục |
|---|---|
| **Nền** | Dán · ─ · Thêm Kiểm tra ĐK · Thêm Số hạng |
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
| MetaTrader5 (pip) | 5.0.5735 ✔ đã có |
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

<!-- ĐÃ CẮT (đợt 4): §11 Kế hoạch + "Sơ đồ mẫu ra đúng thế này". -->

<!-- ĐÃ CẮT (đợt 4): §12 STRATEGY TESTER (~795 dòng) — hai đồng hồ · đường đi 4 điểm · spread/phí · vùng nén · dòng thời gian bất biến · nhật ký · bảng số liệu · chart · phát lại · bảng màu chart, cùng nhật ký đối chiếu với D_02 và MT5. -->

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
- **Chỉ nhập CÙNG SƠ ĐỒ** — một khối chỉ soát nổi trong sơ đồ nhận nó (`ACTION_TABS`). Đây là
  luật, không phải làm cho gọn. Hiện chỉ có một sơ đồ nên nó chưa lọc gì; giữ vì cơ chế nhiều sơ
  đồ còn nguyên, và ngày có sơ đồ thứ hai thì nó chặn được ngay.
  *(Ca thật của bản D_02: toán hạng nhóm "Lệnh này" chỉ tồn tại ở Manage, nên bê một khối Manage
  sang Entry là tạo ra khối không soát nổi.)*

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

`api._mau_khoi(st)` gắn vào thẻ một **khoá ngữ nghĩa**, không phải mã màu: `start · hoi · gia ·
lot`. Suy từ `type` + `đích` — phạm trù của chính app, không phải khái niệm riêng của một chiến
lược, nên chiến lược nào sau này cũng ra màu đúng. Giao diện ánh xạ khoá → biến CSS, nên đổi bảng
màu là việc của CSS.

| khối | màu | vì sao |
|---|---|---|
| Bắt đầu | xám `--action` | ĐIỂM NEO, không phải hành động |
| Kiểm tra ĐK | lam `--khoi-hoi` | một câu hỏi |
| Số hạng · giá | tím `--khoi-gia` + `$` | dựng MỨC TREO |
| Số hạng · khối lượng | lục lam `--khoi-lot` + `≡` | dựng CỠ LỆNH |

> ⚠ **Bản D_02 chia theo MUA/BÁN** — xanh `--ok` + ▲ cho Mua, đỏ `--err` + ▼ cho Bán, tím cho Sửa
> lệnh. Bỏ vì market maker **đứng cả hai phía cùng lúc**: "khối này mua hay bán" là câu hỏi không
> có câu trả lời, mọi khối đều làm cả hai.
>
> Thứ đáng phân biệt bằng mắt bây giờ là số hạng động vào GIÁ hay động vào KHỐI LƯỢNG — liếc cả
> chuỗi là thấy ngay đoạn nào lo mức treo, đoạn nào lo cỡ lệnh. `--ok`/`--err` vì thế rút về đúng
> nghĩa gốc (xanh là ổn, đỏ là hỏng) và không còn dính ngữ nghĩa giao dịch nào.

**Nền dải tiêu đề nhuộm 10% mới là thứ quyết định, không phải cái thanh.** Ở mức thu phóng 67% —
mức hay dùng để nhìn cả sơ đồ — thanh 3px chỉ còn 2px và gần như biến mất; một dải nhuộm thì vẫn
quét mắt ra được. Thanh cũng được kéo cao hết dải tiêu đề thay vì 15px giữa chừng.

**Dùng KÝ HIỆU chứ không chỉ dùng màu** (`$` / `≡`) — đọc được cả khi mù màu. Cùng lý lẽ với cặp
▲/▼ của bản cũ, chỉ đổi thứ nó phân biệt.

Cái lợi kèm theo: cam đang mang hai nghĩa cùng lúc — "khối hành động" và "đang chọn · số thứ tự".
Đẩy khối hành động sang màu riêng thì **cam chỉ còn nghĩa *của ta · đang chọn***, viền chọn nổi hẳn.

Thân khối, viền, phông chữ, huy hiệu: **không đổi một pixel**.

<!-- ĐÃ CẮT (đợt 4): §12.23 Bỏ nút "Tải thêm" — nguồn nến MT5. -->

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
không kéo cả cây. Nạp `api` là kéo theo numpy và MetaTrader5, mà `tests/test_danh_so` chỉ cần
`core`.

`.spec` chỉ đổi `hiddenimports` thành `cat_studio.kho.*`; `tools/*.bat` không phải sửa gì vì tất cả
đều trỏ vào `app_web.py` ở gốc.

Kiểm: **9/9 bài qua**, đóng gói lại, giải nén sang thư mục khác chạy ra **547 lệnh · −10,50 R ·
DD 0,91 % · vốn cuối 9955,04** — trùng từng con số với trước khi gom.

<!-- ĐÃ CẮT (đợt 4): §13.4 "Máy mới không tự tải được" — chuỗi rỗng bị hiểu là "đã đủ" trong nguồn nến MT5. -->

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
gói (numpy + cây DLL .NET của pythonnet + MetaTrader5) vào thư mục tạm ở MỖI lần mở: vài giây chờ
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

<!-- ĐÃ CẮT (đợt 4): §12.22 · 12.21 · 12.20 · 12.19 · 12.18 · 12.14 — nhật ký hoàn thiện cửa sổ tester. -->

## 13. Việc còn treo

⚠ Danh sách cũ đã đi ở đợt 4. Nó tổng kết một app khác: mọi mục đã xong đều nói về
`nguon_nen` · `tinh_toan` · `khop_lenh` · `bo_chay` · `nhat_ky` và giao diện tester —
tất cả đã bị gỡ. Ba mục còn treo cũng vậy (chồng lệnh kiểu D_02, đóng gói .exe đã làm
xong từ lâu, và câu hỏi `HOẶC`).

Một câu trong đó đáng giữ vì nó là LUẬT chứ không phải việc, và đã được chốt:

> **KHÔNG có `HOẶC` giữa các điều kiện.** Muốn "hoặc" thì tách thành hai nhánh riêng
> trên sơ đồ — nhìn sơ đồ là thấy được, còn chữ "hoặc" giấu trong hộp thoại thì không.
> Nối tiếp hai cổng chính là VÀ.

Việc còn lại của lần dọn nằm ở `tai_lieu/o_cam_trong.md`, không ở đây: sổ đó liệt kê
từng ổ cắm đang trống, và nó cạn dần tới rỗng.
