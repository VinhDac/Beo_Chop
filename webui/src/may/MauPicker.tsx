import { useState } from 'react'
import Modal from '../components/Modal'
import type { BootMay, TramKey } from './mayTypes'

/** LẮP MẪU DỰNG SẴN vào trạm đang mở.  (D-10, phần 5, lát 5e)
 *
 *  22 mẫu, chia theo trạm, mô phỏng các mô hình có sẵn của QuantConnect. Mỗi mẫu là một
 *  SƠ ĐỒ dựng từ đúng những khối người chơi có trong tay — không có khối bí mật nào —
 *  nên lắp xong mở ra xem được, sửa được như sơ đồ tự vẽ.
 *
 *  Nói thẳng hai điều, vì cả hai đều bất ngờ nếu không nói:
 *   · lắp mẫu THAY CẢ sơ đồ của trạm này (bốn trạm kia không đụng tới);
 *   · núm vặn của mẫu thành THAM SỐ có tên, và tên nào đã có thì giữ nguyên giá trị
 *     người chơi đã chỉnh.
 */
export default function MauPicker({ tram, boot, onChon, onDong }: {
  tram: TramKey
  boot: BootMay
  onChon: (mauKey: string) => void
  onDong: () => void
}) {
  const [chon, setChon] = useState<string | null>(null)
  const t = boot.tram.find(x => x.key === tram)
  const ds = boot.mau[tram] ?? []

  return (
    <Modal title={`Lắp mẫu vào ${t?.so ?? ''} ${t?.ten ?? ''}`} width={620} onClose={onDong}
           footer={<>
             <div className="xem-truoc">
               Lắp mẫu <b>thay cả sơ đồ</b> của trạm này — bốn trạm kia giữ nguyên.
             </div>
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" disabled={!chon}
                     onClick={() => { if (chon) { onChon(chon); onDong() } }}>Lắp</button>
           </>}>
      <div className="chu-dan">
        {t?.hoi} Núm vặn của mẫu (chu kỳ, ngưỡng) thành <b>tham số có tên</b> của cỗ máy;
        tên nào bảng đã có thì giữ nguyên giá trị bạn đã chỉnh.
      </div>
      <div className="ds-hanh-dong">
        {ds.map(m => (
          <button key={m.key}
                  className={'danh-hd' + (m.key === chon ? ' chon' : '')}
                  onClick={() => setChon(m.key)}
                  onDoubleClick={() => { onChon(m.key); onDong() }}>
            <div className="dong-hd">
              <b>{m.ten}</b>
              {/* Tên mô hình bên QuantConnect — để người chơi tra tài liệu của họ, và
                  để thấy cỗ máy này không phải một thế giới riêng. */}
              {m.qc && m.qc !== '—' && <span className="the">{m.qc}</span>}
            </div>
            <div className="kho-mota">{m.mo_ta}</div>
          </button>
        ))}
      </div>
    </Modal>
  )
}
