import Modal from './Modal'
import Icon from './Icon'
import type { KetQuaSinh } from '../types'

/** HỘP SINH MÃ — bày ra thuật toán LEAN mà sơ đồ vừa thành.
 *
 *  Đây là chỗ lời hứa của cả dự án hiện ra mắt thường: *cái script và cái ta vẽ phải
 *  ra cùng một thứ, chỉ khác cách trình bày*. Nên hộp này không tóm tắt, không giấu —
 *  nó bày nguyên file, có số khối ghi trong chú thích, để người chơi soi được từng
 *  khối mình vẽ đã thành câu gì.
 *
 *  CÓ LỖI THÌ VẪN BÀY MÃ, nhưng nói rõ là đừng chạy: nhìn thấy chỗ sơ đồ diễn đạt
 *  chưa hết dễ hơn nhiều so với đọc một dòng lỗi rồi đoán.
 */
export default function HopSinhMa({ kq, onDong, onGhi }: {
  kq: KetQuaSinh
  onDong: () => void
  onGhi: () => void
}) {
  const loi = kq.van_de.filter(v => v.severity === 'error')
  const canh = kq.van_de.filter(v => v.severity === 'warning')

  return (
    <Modal title={`Mã LEAN — ${kq.ten_lop}`} width={860} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Đóng</button>
             <button className="nut chinh" onClick={onGhi} disabled={!kq.ma}>
               <Icon name="save" /> Lưu file .py
             </button>
           </>}>
      <div className="hop-ma">
        {loi.length > 0 && (
          <div className="mc-bao loi">
            ⚠ Sơ đồ còn {loi.length} chỗ chưa diễn đạt hết — <b>đừng chạy file này</b>.
            <ul>{loi.map((v, i) => <li key={i}>{v.message}</li>)}</ul>
          </div>
        )}
        {canh.length > 0 && (
          <div className="mc-bao">
            {canh.length} điều đáng để ý:
            <ul>{canh.map((v, i) => <li key={i}>{v.message}</li>)}</ul>
          </div>
        )}
        {kq.duong && <div className="mc-bao">Đã lưu: <code>{kq.duong}</code></div>}
        <pre className="ma-lean">{kq.ma || '(chưa sinh được gì)'}</pre>
      </div>
    </Modal>
  )
}
