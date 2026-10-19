/** BẢNG DỊCH TIẾNG ANH: câu tiếng Việt → câu tiếng Anh. Xem `ngon_ngu.ts`.
 *
 *  KHOÁ là câu tiếng Việt đúng từng chữ như trong mã, bỏ khoảng trắng hai đầu. Không
 *  phải gõ tay: `npm run dich` in sẵn những câu còn thiếu, chỉ việc dán vào đúng nhóm
 *  rồi điền bản tiếng Anh. Câu tiếng Việt trong mã đổi thì khoá cũ thành thừa —
 *  `npm run dich -- --don` bỏ đi. Xếp theo tệp của lần dùng ĐẦU; nhóm "python" là nhãn
 *  Python gửi sang (`tools/nhan_python_dich.py`).
 *
 *  Bản tiếng Anh được dùng `{0|one|other}` cho số ít / số nhiều — tiếng Việt không cần.
 *  Viết hoa, chấm câu theo đúng câu gốc: câu gốc viết thường (dòng nhật ký, lý do) thì
 *  bản Anh cũng viết thường.
 *
 *  THUẬT NGỮ — giữ một chữ cho một khái niệm, giao diện mới đọc ra một hệ thống:
 *    khối → block              sơ đồ → diagram            dây / đường nối → wire
 *    Bắt đầu → Start           Xác nhận → Check           Hành động → Action
 *    Nhóm → Group              Quay về → Loop back        Hạt nhân → Core
 *    Cỗ máy → Engine           cổng → gate                thẻ (khối) → card
 *    vế → side                 đại lượng → quantity       phép so → comparison
 *    phép ghép → combination    hệ số → weight            chu kỳ → period
 *    chỉ báo → indicator       mã (chứng khoán) → symbol  rổ → universe
 *    mã (sinh ra) → code       nhịp chạy → schedule       sàn → brokerage
 *    vốn → capital             khoảng ngày → date range   độ phân giải → resolution
 *    lượt chạy → run           mẻ → batch                 kho → library
 *    núm → knob                ghim → pin                 quét → sweep
 *    bảng Vấn đề → Problems    nhật ký → log              thanh trạng thái → status bar
 *    hạn giờ → time limit      hoàn tác → undo            làm lại → redo
 *    Lưu → Save                Huỷ → Cancel               Đóng → Close
 *    Lưu thành… → Save as…     Xoá → Delete               Nhân bản → Duplicate
 *  TÊN RIÊNG CỦA NGHỀ GIỮ NGUYÊN, không dịch và cũng không cần khoá ở đây: Build,
 *  Backtest, Optimize, Live, Results, Strategy, LEAN, QuantConnect, và tên chỉ báo
 *  (RSI, MACD, EMA, Bollinger…).
 */
const TIENG_ANH: Record<string, string> = {
}

export default TIENG_ANH
