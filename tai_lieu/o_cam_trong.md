# Ổ cắm trống

Sổ này ghi những chỗ đã bị **gỡ có chủ ý** trong lần dọn Cat_Studio sang HFT market
maker, và chưa có gì cắm vào.

Vì sao phải có sổ: một khoảng trống không đánh dấu thì sáu tháng nữa không ai đọc ra
được nó là *chưa làm* hay là *cố tình không có*. Mỗi mục dưới đây trả lời đúng ba câu —
**nằm ở đâu · trước cắm gì · phải cắm gì**.

Luật của sổ: một ổ cắm được cắm xong thì **xoá khỏi đây**, không đánh dấu ✔. Sổ này chỉ
liệt kê cái còn trống; nó cạn dần tới rỗng, và rỗng nghĩa là dọn xong.

Lấy lại bất cứ thứ gì đã xoá: `git checkout f1c90fb -- <đường dẫn>`.

---

## 1. Cửa sổ Strategy Tester

**Nằm ở đâu** — `webui/src/main.tsx`, nhánh `?tester=1` → `<ChuaCo ten="Strategy Tester" />`.
Phía Python, `api.ApiTester` vẫn còn và vẫn mở được cửa sổ; nó sẽ đi trong đợt 3.

**Trước cắm gì** — `webui/src/tester/`, 2.033 dòng: `Chart` (nến + hộp zone),
`BangSoLieu` (cột chỉ báo từng nến), `ThongKe` (bội R, drawdown), `Journey`, `LichSu`,
`BangDuoi`, `NutChart`, `Tester`.

**Phải cắm gì** — chưa biết, và cố ý chưa quyết. Màn hình của một market maker không
dùng chung một dòng nào với chart nến: nó cần thang báo giá hai bên, tồn kho theo thời
gian, khoảng cách quote tới mid, và chất lượng khớp (bị chọn ngược bao nhiêu lần).
Quyết được sau khi chốt sàn.

---

## 2. Cửa sổ Live

**Nằm ở đâu** — `webui/src/main.tsx`, nhánh `?live=1` → `<ChuaCo ten="Live" />`.
`api.ApiLive` vẫn còn, đi trong đợt 3.

**Trước cắm gì** — `webui/src/live/`, 822 dòng: `Live` (sức khoẻ kết nối MT5, độ trễ,
rác lệnh còn lại) và `CongChot` (hộp chốt sơ đồ + symbol trước khi chạy).

**Phải cắm gì** — ý tưởng của `CongChot` (nói TRƯỚC khi chạy, không đóng được bằng Esc)
đáng giữ nguyên và dựng lại; phần đo sức khoẻ phải viết lại theo sàn mới. Bản đặc tả
tốt nhất cho nó là docstring của `cat_studio/ket_noi.py` — **đọc file đó trước khi
viết lại**, nó liệt kê ba kiểu chết im lặng của live mà không tài liệu nào khác có.

---

## Đợt sau sẽ thêm vào đây

Đợt 2 và 3 gỡ tiếp nguồn dữ liệu, kết nối sàn, mô hình khớp, kho toán hạng và từ vựng
hành động. Mỗi thứ gỡ xong thêm một mục vào sổ này ngay trong đợt đó — không để dồn,
vì đúng cái không được ghi ngay là cái sẽ không bao giờ được ghi.
