import { useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { Hang } from './ORuot'
import type { Step } from '../types'
import { tr, trx } from '../ngon_ngu'

/** HỘP KHỐI QUAY VỀ — nhảy ngược lên một khối phía trước, mấy vòng thì dừng.
 *
 *  ⚠ VÌ SAO KHỐI NÀY CẦN HỘP RIÊNG. Nó không thuộc từ điển Hỏi lẫn từ điển Làm (nó
 *  không hỏi thị trường, cũng không ra lệnh nào — nó là NGỮ PHÁP của hình vẽ), nên nó
 *  rơi qua kẽ giữa hai hộp kia: bấm đúp vào nó không ra gì, và menu chuột phải chỉ
 *  đặt được ĐÍCH.
 *      «Số vòng» thì KHÔNG đặt được ở đâu cả — đếm cả mã nguồn: `so_vong` của một
 *  khối chỉ được ĐỌC (vẽ đường ↻, sinh mã), chưa một chỗ nào ghi. Tức là một ô có
 *  thật trong file, có thật trong bộ sinh mã, mà người dùng không có cửa nào chạm
 *  tới. (Ô số vòng trên ĐƯỜNG ↻ là thứ khác: đó là lối khai vòng thứ hai, bằng dây.)
 */
export default function HopQuayVe({ step, dsKhoi, onLuu, onDong }: {
  step: Step
  /** Mấy khối quay về được — mọi khối khác, kèm số thứ tự để gọi tên. */
  dsKhoi: { id: string; nhan: string }[]
  onLuu: (s: Step) => void
  onDong: () => void
}) {
  const [ten, setTen] = useState(step.name ?? '')
  const [ve, setVe] = useState(String(step.ve ?? ''))
  // Rỗng = LẶP MÃI, đúng nghĩa `core.khoi_quay_ve` đã chốt. Giữ dạng chuỗi để người
  // dùng xoá trắng được — ép về số ngay thì ô nhảy về 0 giữa lúc đang gõ.
  const [soVong, setSoVong] = useState(
    step.so_vong == null ? '' : String(step.so_vong))

  function luu() {
    const n = Number(soVong)
    const s: Record<string, unknown> = { ...step, name: ten.trim() || tr('Quay về'), ve }
    // KHÔNG ghi khoá khi lặp mãi, đúng lối `core.make_quay_ve_step`: có khoá mà giá
    // trị rỗng là một thứ `khoi_quay_ve` phải đoán, mà đoán thì sớm muộn đoán khác.
    if (soVong.trim() && Number.isFinite(n) && n >= 1) s.so_vong = Math.floor(n)
    else delete s.so_vong
    onLuu(s as unknown as Step)
  }

  return (
    <Modal title={tr('Quay về')} width={520} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>{tr('Huỷ')}</button>
             <button className="nut chinh" onClick={luu}>{tr('Lưu')}</button>
           </>}>
      <div className="hop-lam">
        <div className="mo-ta-loai">
          {trx('{0} nhảy ngược lên một khối phía trước — vẽ ra cái vòng '
          + 'lặp, thay vì để nó ngầm', <Icon name="quay-ve" />)}</div>

        <label className="o-hang">
          <span className="nhan-o">{tr('Tên khối')}</span>
          <input className="o day" value={ten} spellCheck={false}
                 placeholder={tr('Quay về')} onChange={e => setTen(e.target.value)} />
        </label>

        <Hang o={{ ten: 've', nhan: tr('Quay về khối'), kieu: 'chon', mac_dinh: '',
                   don_vi: '', goi_y: tr('Để trống thì sơ đồ báo lỗi: một khối '
                   + 'Quay về không có đích thì chạy tới đây là hết đường.'),
                   bat_buoc: true, chon: [] }}>
          <select className="o day" value={ve} onChange={e => setVe(e.target.value)}>
            <option value="">{tr('— chưa chọn khối nào —')}</option>
            {dsKhoi.map(k => (
              <option key={k.id} value={k.id}>{k.nhan}</option>
            ))}
          </select>
        </Hang>

        <Hang o={{ ten: 'so_vong', nhan: tr('Số vòng'), kieu: 'so', mac_dinh: '',
                   don_vi: tr('vòng'),
                   goi_y: tr('Để TRỐNG là lặp mãi — hết lượt thì nến sau tự chạy lại từ '
                   + 'khối Bắt đầu. Điền số thì quay ngần ấy vòng rồi đi tiếp.'),
                   bat_buoc: false, chon: [] }}>
          <input className="o" type="number" min={1} step={1} value={soVong}
                 placeholder={tr('lặp mãi')}
                 onChange={e => setSoVong(e.target.value)} />
        </Hang>
      </div>
    </Modal>
  )
}
