import Modal from './Modal'
import Icon from './Icon'

/** HỘP TIẾN ĐỘ CỦA MỘT MẺ OPTIMIZE.
 *
 *  Cùng vai với `HopTienDo` của Backtest — và cùng lý do tồn tại: một mẻ chạy hàng
 *  phút tới hàng giờ, không có cái hộp này thì người dùng bấm Chạy xong nhìn sơ đồ
 *  im lìm và không biết nó còn sống hay đã treo.
 *
 *  KHÁC BACKTEST ĐÚNG MỘT ĐIỂM, và nó quan trọng: mẻ ĐẾM ĐƯỢC. LEAN không in tiến
 *  độ của một lượt backtest (nên hộp kia chỉ có thanh chạy qua lại, cố ý — bịa một
 *  con số phần trăm là hứa một cái mốc không ai giữ được). Nhưng một mẻ thì biết
 *  trước nó có bao nhiêu lượt, và đếm được bao nhiêu lượt đã ghi ra kết quả. Phần
 *  trăm ở đây là SỐ THẬT, đếm từ file trên đĩa.
 */
export default function HopTienDoToiUu({ td, onHuy, onDung, onXem }: {
  td: { giay: number; so_luot?: number; xong_may?: number; dong_cuoi?: string }
  onHuy: () => void
  /** Giết tiến trình optimizer — khác «Ẩn hộp này», thứ chỉ cất cái hộp đi. */
  onDung: () => void
  /** Mở cửa sổ kết quả: bảng và plot trong đó đầy dần ngay trong lúc chạy. */
  onXem: () => void
}) {
  const tong = td.so_luot ?? 0
  const xong = td.xong_may ?? 0
  const pt = tong ? Math.min(100, Math.round((xong / tong) * 100)) : 0
  const giay = td.giay || 0
  // Còn bao lâu: lấy nhịp THỰC TẾ của mấy lượt đã xong, không lấy con số ước lượng
  // lúc bấm Chạy — máy đang bận thì nhịp thật chậm hơn, và nói sai còn tệ hơn im.
  const conLai = xong > 0 && tong > xong
    ? ((giay / xong) * (tong - xong))
    : 0
  const docConLai = conLai < 90 ? `${Math.round(conLai)} giây`
    : conLai < 5400 ? `${Math.round(conLai / 60)} phút`
      : `${(conLai / 3600).toFixed(1)} tiếng`

  return (
    <Modal title="Optimize" width={560} onClose={onHuy}
           footer={<>
             {/* DỪNG bên trái, tách khỏi «Ẩn hộp này» — cùng lý do như hộp Backtest:
                 hai nút nghe giống nhau mà một cái giết cả mẻ. */}
             <button className="nut nut-dung" onClick={onDung}>
               <Icon name="dung" /> Dừng mẻ này
             </button>
             <span className="day" />
             <button className="nut" onClick={onXem}>Xem kết quả</button>
             <button className="nut" onClick={onHuy}>Ẩn hộp này</button>
           </>}>
      <div className="hop-td">
        <div className="td-dau">
          <b>{tong ? `${xong} / ${tong} lượt` : 'Đang khởi động…'}</b>
          <span className="day" />
          <span className="td-giay">{giay.toFixed(0)}s</span>
        </div>

        {/* THANH PHẦN TRĂM THẬT — đếm từ file kết quả trên đĩa. */}
        <div className="td-thanh that">
          <i style={{ width: `${pt}%` }} />
        </div>

        <div className="td-buoc">
          <span className="dang">{pt}%</span>
          {conLai > 0 && <span>còn chừng {docConLai}</span>}
        </div>

        <div className="td-dong">{td.dong_cuoi || '…'}</div>
        <div className="td-chan">
          mỗi lượt là một tiến trình LEAN riêng · đóng hộp này thì mẻ VẪN chạy tiếp
        </div>
      </div>
    </Modal>
  )
}
