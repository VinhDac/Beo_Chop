import { useEffect, useState } from 'react'
import { pyMay } from '../api'
import Icon from '../components/Icon'
import Modal from '../components/Modal'

/** Chọn / xoá một CỖ MÁY đã lưu.  (D-10, phần 5)
 *
 *  Bản của chiến lược cũ (`TemplatePicker`) gọi thẳng `py.list_templates`, tức là kho
 *  CHIẾN LƯỢC. Cỗ máy có kho riêng (`du_lieu/co_may/`), nên nó cần cửa riêng — bày lẫn
 *  hai kho vào một danh sách là mời người chơi mở một thứ không mở được.
 */
export default function MayPicker({ tieuDe, onChon, onDong, onDuyetFile }: {
  tieuDe: string
  onChon: (ten: string) => void
  onDong: () => void
  /** "Duyệt file khác…" — cỗ máy nằm NGOÀI kho. */
  onDuyetFile?: () => void
}) {
  const [ds, setDs] = useState<string[]>([])
  const [chon, setChon] = useState<string | null>(null)
  const [dangTai, setDangTai] = useState(true)

  const nap = () => {
    setDangTai(true)
    pyMay.may_ds().then(r => {
      setDs(r.ok ? (r.value ?? []) : [])
      setDangTai(false)
    })
  }
  useEffect(nap, [])

  async function xoa() {
    if (!chon) return
    if (!window.confirm(`Xoá cỗ máy "${chon}"?`)) return
    await pyMay.may_xoa(chon)
    setChon(null)
    nap()
  }

  return (
    <Modal title={tieuDe} width={460} onClose={onDong}
           footer={<>
             <button className="nut" disabled={!chon} onClick={xoa}>
               <Icon name="trash" /> Xoá
             </button>
             {onDuyetFile && (
               <button className="nut" onClick={onDuyetFile}>Duyệt file khác…</button>
             )}
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" disabled={!chon}
                     onClick={() => chon && onChon(chon)}>Mở</button>
           </>}>
      <div className="danh-sach cao-10">
        {dangTai && <div className="muc mo">đang đọc…</div>}
        {!dangTai && ds.length === 0 && (
          <div className="muc mo">
            Chưa có cỗ máy nào được lưu — dựng một cái rồi bấm Lưu cỗ máy.
          </div>
        )}
        {ds.map(t => (
          <div key={t} className={'muc' + (t === chon ? ' chon' : '')}
               onClick={() => setChon(t)} onDoubleClick={() => onChon(t)}>{t}</div>
        ))}
      </div>
    </Modal>
  )
}
