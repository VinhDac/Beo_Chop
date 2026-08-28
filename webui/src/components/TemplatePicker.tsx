import { useEffect, useState } from 'react'
import { py } from '../api'
import Modal from './Modal'
import Icon from './Icon'

/** Chọn / xoá template đã lưu — thay cho `window.prompt` gõ tay tên.
 *
 *  Bản tkinter có hộp thoại riêng làm đúng việc này (liệt kê theo TÊN, có nút xoá,
 *  có trạng thái rỗng kèm gợi ý). Gõ tay tên file là cách chắc chắn gõ sai.
 */
export default function TemplatePicker({ tieuDe, choPhepXoa = true, onChon, onDong, onDuyetFile }: {
  tieuDe: string
  choPhepXoa?: boolean
  onChon: (ten: string) => void
  onDong: () => void
  /** "📂 Duyệt file khác…" — mở template nằm NGOÀI thư mục templates/. */
  onDuyetFile?: () => void
}) {
  const [ds, setDs] = useState<string[]>([])
  const [chon, setChon] = useState<string | null>(null)
  const [dangTai, setDangTai] = useState(true)

  const nap = () => {
    setDangTai(true)
    py.list_templates().then(r => {
      setDs(r.ok ? (r.value ?? []) : [])
      setDangTai(false)
    })
  }
  useEffect(nap, [])

  async function xoa() {
    if (!chon) return
    if (!window.confirm(`Delete template "${chon}"?`)) return
    await py.delete_template(chon)
    setChon(null)
    nap()
  }

  return (
    <Modal title={tieuDe} width={460} onClose={onDong}
           footer={<>
             {choPhepXoa && <button className="nut" disabled={!chon} onClick={xoa}><Icon name="trash" /> Delete</button>}
             {onDuyetFile && <button className="nut" onClick={onDuyetFile}>Browse for a file…</button>}
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" disabled={!chon}
                     onClick={() => chon && onChon(chon)}>Open</button>
           </>}>
      <div className="danh-sach cao-10">
        {dangTai && <div className="muc mo">loading…</div>}
        {!dangTai && ds.length === 0 && (
          <div className="muc mo">
            No strategies saved yet — save one from the Save ▾ menu first.
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
