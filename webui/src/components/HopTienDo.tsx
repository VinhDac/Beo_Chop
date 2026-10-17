import Modal from './Modal'
import Icon from './Icon'
import type { TienDoChay } from '../types'

/** HỘP TIẾN ĐỘ — hiện trong lúc LEAN chạy backtest.
 *
 *  ⚠ KHÔNG CÓ PHẦN TRĂM, và đó là cố ý. LEAN **không in tiến độ ra màn hình**:
 *  `BacktestProgressMonitor` chỉ đẩy con số ấy vào gói kết quả gửi lên đám mây. Bịa
 *  một con số còn tệ hơn không có — thanh chạy tới 90% rồi đứng im hai phút là lời
 *  hứa không ai giữ được.
 *
 *  Nên ở đây nói ba thứ CÓ THẬT: đang ở giai đoạn nào, chạy được bao lâu, và dòng
 *  LEAN vừa in ra. Ba thứ ấy đủ để biết nó còn sống và đang làm gì.
 */
const GIAI_DOAN = ['Khởi động LEAN', 'Khởi động Python', 'Nạp thuật toán Python',
                   'Chuẩn bị thuật toán', 'Chạy backtest', 'Dựng kết quả']

export default function HopTienDo({ td, onHuy, onDung }: {
  td: TienDoChay
  onHuy: () => void
  /** Dừng hẳn lượt chạy — khác «Ẩn hộp này», thứ chỉ cất cái hộp đi. */
  onDung: () => void
}) {
  const i = GIAI_DOAN.indexOf(td.giai_doan)
  return (
    <Modal title="Backtest" width={560} onClose={onHuy}
           footer={<>
             {/* DỪNG đứng BÊN TRÁI, tách khỏi «Ẩn hộp này»: hai nút nghe giống nhau
                 mà một cái giết tiến trình LEAN còn một cái chỉ cất hộp đi. Đặt sát
                 nhau cùng một bên là mời người ta bấm nhầm. */}
             <button className="nut nut-dung" onClick={onDung}>
               <Icon name="dung" /> Dừng backtest
             </button>
             <span className="day" />
             <button className="nut" onClick={onHuy}>Ẩn hộp này</button>
           </>}>
      <div className="hop-td">
        <div className="td-dau">
          <b>{td.giai_doan || 'Đang khởi động…'}</b>
          <span className="day" />
          <span className="td-giay">{td.giay.toFixed(1)}s</span>
        </div>

        {/* Thanh CHẠY QUA LẠI, không phải thanh phần trăm — nó nói "còn sống", chứ
            không hứa "còn ngần này nữa". */}
        <div className="td-thanh"><i /></div>

        <div className="td-buoc">
          {GIAI_DOAN.map((g, j) => (
            <span key={g} className={j < i ? 'qua' : j === i ? 'dang' : ''}>{g}</span>
          ))}
        </div>

        <div className="td-dong">{td.dong_cuoi || '…'}</div>
        <div className="td-chan">
          {td.so_dong} dòng từ LEAN · đóng hộp này thì backtest VẪN chạy tiếp
        </div>
      </div>
    </Modal>
  )
}
