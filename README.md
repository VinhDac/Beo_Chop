# Cat Studio

Vẽ một **cỗ máy giao dịch** bằng sơ đồ khối, rồi thả nó vào thị trường thật trong quá khứ
trên **QuantConnect**. Không gõ code, không công thức — kéo khối, nối dây, bấm ▶.

App chỉ phục vụ đúng một vòng: **lắp cỗ máy → chạy trên QC → xem vì sao → sửa → nộp**.

---

## Một cỗ máy = năm trạm

Đúng năm phần mà QuantConnect chia một thuật toán ra. Mỗi trạm là một sơ đồ khối RIÊNG,
chạy lại từ khối Bắt đầu của nó cho TỪNG đối tượng trong phạm vi, theo lịch của nó.

| Trạm | QuantConnect gọi là | Hỏi câu gì | Chạy cho ai | Ra cái gì |
|---|---|---|---|---|
| ① Chọn mã | Universe Selection | Mã nào đáng để mắt tới? | mỗi mã của màn | rổ mã |
| ② Tín hiệu | Alpha | Mã này sắp lên, xuống, hay nên đứng ngoài? | mỗi mã trong rổ | tín hiệu có thời hạn |
| ③ Chia vốn | Portfolio Construction | Mỗi mã được bao nhiêu phần vốn? | mỗi mã có tín hiệu hoặc đang giữ | tỷ trọng mục tiêu |
| ④ Rủi ro | Risk Management | Có gì phải cắt bớt ngay không? | mỗi mã đang giữ | mục tiêu đã chỉnh |
| ⑤ Khớp lệnh | Execution | Đưa vị thế về mục tiêu bằng lệnh gì, lúc nào? | mỗi mã còn lệch | lệnh gửi sang QC |

**Khớp lệnh là việc của QuantConnect.** Cỗ máy chỉ ra *tỷ trọng mục tiêu* và *ý định
lệnh*; số lượng, lô tối thiểu, ký quỹ, phí, trượt giá do QC tính — đúng như một quỹ thật
chia việc.

## Ba loại khối, không hơn

* **Bắt đầu** — điểm neo của trạm: lịch chạy, khung nến, và (ở ①) phạm vi mã.
* **Hỏi** — một hay nhiều điều kiện nối nhau bằng VÀ. Qua thì đi tiếp, trượt thì thử
  nhánh kế bên dưới. Nhiều nhánh từ một khối = HOẶC, **thử từ trên xuống theo vị trí trên
  canvas** — nên thứ tự ưu tiên luôn nhìn thấy được.
* **Làm** — 14 khối, mỗi trạm một bộ riêng: *Cho vào rổ · Báo tín hiệu · Đặt tỷ trọng ·
  Giảm về · Cấm vào lại · Lệnh thị trường · Lệnh giới hạn…* Đây là chỗ DUY NHẤT năm trạm
  khác nhau về hành động.

Mỗi trạm còn có **Gom** — bước chạy một lần cho cả trạm sau khi mọi mã đã đi qua sơ đồ:
① giữ N mã điểm cao nhất · ③ giữ tiền mặt %, trần mỗi mã %, chỉ mua.

## Đánh số và soát lỗi

Huy hiệu trên mỗi khối: **số = đi được bao xa, chữ = đi nhánh nào** (`1 · 1A · 1A.1`).
Khối không có đường nối dẫn tới thì không có số — nó sẽ không bao giờ chạy, và nhìn là
thấy. Mỗi trạm đánh số riêng.

Soát lỗi chạy sau MỖI thay đổi, trên cả năm trạm: khối đặt sai trạm, đại lượng không đọc
được ở trạm này, hai vế khác đơn vị, hai quyết định trên một đường, trạm không ra được
kết quả, Gom sai khoảng, ô số dùng tham số không có trong bảng… Trạm nào có lỗi thì chấm
đỏ ngay trên dải ①→⑤.

## Trò chơi

**Chiến dịch** — mỗi màn là một RỔ mã và một khoảng ngày. Boss của màn là **«Mua rồi giữ
cả rổ»**: chia đều vốn cho mọi mã rồi để yên.

* ⭐ chạy sạch — chạy trọn màn đã thấy, có ít nhất một lệnh khớp
* ⭐⭐ thắng boss trên màn đã thấy
* ⭐⭐⭐ **Nộp** rồi vẫn thắng boss trên **màn ẩn** — đoạn thị trường cỗ máy chưa từng thấy,
  app giữ ngày, người chơi không chọn được

Muốn nộp thì phải ▶ đầy đủ ĐÚNG cỗ máy đó trước: vé nộp tính theo **vân tay logic** của
cỗ máy (đổi một ngưỡng, một dây nối, một ô Gom là thành cỗ máy khác — còn kéo khối đi chỗ
khác hay đổi tên thì không).

**Sáng tạo** — không màn, không boss, không sao: rổ mã nào, khoảng ngày nào, vốn bao
nhiêu cũng được. Chỗ để thử ý tưởng.

> **Đang dựng lại đường chạy.** App vẽ và soát cỗ máy được; **chạy thì chưa** — từ
> 16/10/2026 mọi phép tính giao dịch giao hết cho QuantConnect (D-11), và phần dịch sơ đồ
> thành thuật toán QC chưa dựng xong. Phần dưới về trò chơi mô tả luật đã có, chưa chạy
> được.

## Chạy từ mã nguồn (Windows)

```bat
tools\setup.bat        REM một lần sau khi clone: .venv + thư viện + build giao diện
tools\chay_test.bat    REM phải thấy: ✔ 7/7 bài đều qua
tools\chay.bat         REM mở app
```

* Sửa giao diện (`webui/`) xong thì `tools\build_ui.bat` mới thấy thay đổi.
* Muốn xem giao diện trong trình duyệt (chụp ảnh, mở DevTools, cho máy bấm thử):
  `.venv\Scripts\python.exe tools\xem_thu.py` → `http://127.0.0.1:8777`, thêm `?qc=1` để
  xem cửa sổ Màn chơi. Nó gọi `api.py` thật, chỉ thay đường vận chuyển.

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
  tram.py             TỪ ĐIỂN 5 trạm: khối Làm · đại lượng · tham số · Gom
  may.py              cỗ máy: định dạng, chuẩn hoá, soát lỗi, đánh số, chữ trên khối
  chuoi_nen.py        nến + chỉ báo tính dần (thuần Python)
  mau_tram.py         22 mẫu dựng sẵn từng trạm + 4 cỗ máy dựng sẵn
  qc_api.py           nói chuyện với API của QC
  game.py             luật chơi: màn, boss, sao, sổ nộp
  qc_chay.py          soát đầu vào một lượt chạy (rổ mã, ngày, vốn)
  core.py             đồ thị, đánh số, soát lỗi đồ thị, bảng tham số
  api.py              bề mặt DUY NHẤT giao diện gọi tới
webui/src/may/        trình vẽ 5 trạm (React + @xyflow/react)
webui/src/qc/         cửa sổ Màn chơi
tests/                7 bài kiểm, chạy bằng `tools\chay_test.bat`
tai_lieu/core.md      nhật ký kỹ thuật: vì sao từng thứ như hiện tại
DECISIONS.md          quyết định lớn, kèm phương án đã cân nhắc
```

## Lưu ý

* **Chữ trên khối do Python dựng**, giao diện không ghép một mẩu nào — nên thứ hiện trên
  màn hình luôn đúng bằng thứ bộ máy thật sự hiểu.
* **Không nhìn trước dữ liệu**: `lui = 0` là nến VỪA ĐÓNG; bộ máy chạy lúc đóng nến nên
  không có nến đang chạy nào để nhìn trộm tương lai.
* **Mọi thứ app ghi ra** nằm trong `du_lieu/` (cỗ máy, nhật ký chạy, sổ game, khoá QC) —
  thư mục này nằm trong `.gitignore`.
