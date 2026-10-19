import Modal from './Modal'
import { LENH, TEN_NHOM, chuPhim, type Nhom } from '../phim_tat'
import { tr } from '../ngon_ngu'

/** BẢNG PHÍM TẮT (F2) — tra, không phải cấu hình.
 *
 *  Mấy lệnh ít dùng CỐ Ý để trống phím: mọi cụm dễ nhớ đều đã có chủ, và gán bừa là
 *  giật phím khỏi một việc người dùng đang quen tay. Chúng vẫn bấm được từ ribbon hay
 *  menu chuột phải.
 */
const NHOM: Nhom[] = ['khoi', 'sua', 'file']

export default function BangPhimTat({ onDong }: { onDong: () => void }) {
  return (
    <Modal title={tr('Phím tắt')} width={560} onClose={onDong}
           footer={<><span className="day" />
                     <button className="nut" onClick={onDong}>{tr('Đóng')}</button></>}>
      <div className="bang-phim">
        {NHOM.map(n => (
          <div key={n} className="nhom-phim">
            <div className="ten-nhom">{tr(TEN_NHOM[n])}</div>
            {LENH.filter(l => l.nhom === n).map(l => (
              <div className="dong-phim" key={l.ma}>
                <span className="ten-lenh">{tr(l.nhan)}</span>
                <span className="phim-hien">
                  {l.phim.length
                    ? l.phim.map(c => <kbd key={c}>{chuPhim(c)}</kbd>)
                    : <span className="mo">{tr('chưa gán')}</span>}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </Modal>
  )
}
