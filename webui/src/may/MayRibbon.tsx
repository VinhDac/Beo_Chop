import type { ReactNode } from 'react'
import Icon from '../components/Icon'
import type { TramMoTa } from './mayTypes'

/** Thanh công cụ của TRÌNH VẼ 5 TRẠM — cùng khuôn ribbon Paint của sơ đồ cũ: nút gom
 *  nhóm, nhãn nhóm nằm dưới, vạch ngăn giữa các nhóm.  (D-10, phần 5)
 *
 *  Mọi thứ "thêm vào" ở trên; canvas phía dưới chỉ để di chuyển và nối. Cố ý KHÔNG
 *  dùng chung `components/Ribbon.tsx`: nút ở đó là của sơ đồ cũ (Vào lệnh, Sửa lệnh,
 *  symbol của một mã duy nhất), và phần 7 sẽ xoá hẳn file ấy.
 *
 *  Ở đây CHỈ có nút đã chạy được. Một nút bày ra mà bấm không ra gì thì tệ hơn là chưa
 *  có nút: người chơi tưởng mình làm sai.
 */

function Nhom({ ten, children }: { ten: string; children: ReactNode }) {
  return (
    <div className="nhom-ribbon">
      <div className="cac-nut">{children}</div>
      <div className="ten-nhom">{ten}</div>
    </div>
  )
}

function Nut({ ten, icon, onClick, tat, title }: {
  ten: string; icon: ReactNode; onClick?: () => void; tat?: boolean; title?: string
}) {
  return (
    <button className="nut-lon" onClick={onClick} disabled={tat} title={title || ten}>
      <span className="hinh">{icon}</span>
      <span>{ten}</span>
    </button>
  )
}

export default function MayRibbon({
  tramMoTa, ten, datTen, themHoi, xoa, doiGhim, hoanTac, lamLai, vuaKhung,
  coChon, chonDaGhim, coTheHoanTac, coTheLamLai, dang,
}: {
  /** Trạm đang mở — nhãn nhóm "Thêm khối" gọi đúng tên trạm. */
  tramMoTa?: TramMoTa
  ten: string
  datTen: (t: string) => void
  themHoi: () => void
  xoa: () => void
  doiGhim: () => void
  hoanTac: () => void
  lamLai: () => void
  vuaKhung: () => void
  coChon: boolean
  chonDaGhim: boolean
  coTheHoanTac: boolean
  coTheLamLai: boolean
  /** Đã có cỗ máy chưa. */
  dang: boolean
}) {
  return (
    <div className="ribbon">
      <Nhom ten="Cỗ máy">
        <div className="cot-nut">
          <input className="o-ten-process" value={ten} spellCheck={false}
                 title="Tên cỗ máy — cũng là tên file khi lưu"
                 onChange={e => datTen(e.target.value)} />
        </div>
      </Nhom>

      <Nhom ten={tramMoTa ? `Thêm vào ${tramMoTa.so} ${tramMoTa.ten}` : 'Thêm khối'}>
        <Nut ten="Hỏi" icon={<Icon name="branch" size={18} />} onClick={themHoi}
             tat={!dang}
             title="Khối Hỏi — qua thì đi tiếp, trượt thì thử nhánh kế bên dưới" />
      </Nhom>

      <Nhom ten="Khối đang chọn">
        <Nut ten={chonDaGhim ? 'Bỏ ghim' : 'Ghim số'}
             icon={<Icon name={chonDaGhim ? 'bo-ghim' : 'ghim'} size={18} />}
             onClick={doiGhim} tat={!coChon}
             title="Ghim số ⟲ — cho phép nối ngược về khối này mà số thứ tự vẫn giữ" />
        <Nut ten="Xoá" icon={<Icon name="trash" size={18} />} onClick={xoa} tat={!coChon}
             title="Xoá khối đang chọn (Delete)" />
      </Nhom>

      <Nhom ten="Sửa">
        <Nut ten="Hoàn tác" icon={<Icon name="undo" size={18} />} onClick={hoanTac}
             tat={!coTheHoanTac} title="Hoàn tác (Ctrl+Z)" />
        <Nut ten="Làm lại" icon={<Icon name="redo" size={18} />} onClick={lamLai}
             tat={!coTheLamLai} title="Làm lại (Ctrl+Y)" />
        <Nut ten="Vừa khung" icon={<Icon name="fit" size={18} />} onClick={vuaKhung} />
      </Nhom>
    </div>
  )
}
