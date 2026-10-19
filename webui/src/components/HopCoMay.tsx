import { useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import RuotBatDau, { locOAnHien } from './RuotBatDau'
import type { CoMay, TuDienBatDau } from '../types'
import { tr, trx } from '../ngon_ngu'

/** HỘP CỖ MÁY LEAN — thứ LEAN lo hộ, quanh cái sơ đồ.
 *
 *  Bốn trạm dây chuyền · sàn và chi phí · dữ liệu và sức mua · ô nhớ · mốc so sánh.
 *
 *  ⚠ NÓ KHÔNG PHẢI MỘT KHỐI, VÀ KHÔNG DÍNH VÀO KHỐI BẮT ĐẦU. Mười một ô này từng
 *  nằm ngay trong khối Bắt đầu — tiện lúc viết, sai lúc đọc: một khối lẽ ra nói
 *  "sơ đồ chạy trên cái gì" lại cõng cả bộ máy của LEAN, và mỗi lần cần thêm khả
 *  năng thì nhét thêm một ô vào đó. Luật nay là *một khối một việc*: vẽ được thì
 *  làm khối mới, không vẽ được mà là việc LEAN lo thì vào đây.
 *      Nên hồ sơ này nằm trong TÀI LIỆU chiến thuật, ngang hàng `steps` và `edges`,
 *  không nằm trong một khối nào (`core.KHOA_CO_MAY`).
 *
 *  Ruột vẽ ô dùng chung với hộp Bắt đầu: xem `RuotBatDau`.
 */
export default function HopCoMay({ coMay, tuDien, maSoDo, onLuu, onDong }: {
  coMay: CoMay
  tuDien: TuDienBatDau
  /** Mã khối Bắt đầu đang khai — ô «Mốc so sánh» gợi ý chúng. Hộp này không
   *  đọc được chúng từ hồ sơ của nó: «Mã» ở hộp kia. */
  maSoDo: string[]
  onLuu: (v: CoMay) => void
  onDong: () => void
}) {
  const [gt, setGt] = useState<Record<string, unknown>>(() => ({ ...coMay }))

  return (
    <Modal title={tr('Cỗ máy LEAN')} width={660} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>{tr('Huỷ')}</button>
             <button className="nut chinh"
                     onClick={() => onLuu(locOAnHien(gt, tuDien) as CoMay)}>
               {tr('Lưu')}
             </button>
           </>}>
      <div className="hop-lam">
        <div className="mo-ta-loai">
          {trx('{0} những thứ LEAN lo hộ quanh sơ đồ — không phải một '
          + 'bước nào trong sơ đồ', <Icon name="gear" />)}</div>

        <RuotBatDau dsO={tuDien.o_co_may} nhom={tuDien.nhom_co_may} gt={gt}
                    setGt={setGt} tuDien={tuDien} maSoDo={maSoDo} />
      </div>
    </Modal>
  )
}
