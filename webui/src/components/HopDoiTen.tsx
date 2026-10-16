import { useState } from 'react'
import Modal from './Modal'

/** Hộp đổi tên — một ô chữ, Enter là xong.
 *
 *  Cố ý KHÔNG dùng `window.prompt`: trong WebView2 nó là hộp của hệ điều hành, màu
 *  sáng trắng giữa một app tối, và không theo được thanh tiêu đề tự vẽ.
 */
export default function HopDoiTen({ tieuDe, giaTri, onXong, onHuy }: {
  tieuDe: string
  giaTri: string
  onXong: (v: string) => void
  onHuy: () => void
}) {
  const [v, setV] = useState(giaTri)
  const luu = () => { const t = v.trim(); if (t) onXong(t); else onHuy() }
  return (
    <Modal title={tieuDe} width={420} onClose={onHuy}
           footer={<><span className="day" />
                     <button className="nut" onClick={onHuy}>Huỷ</button>
                     <button className="nut chinh" onClick={luu}>Đổi tên</button></>}>
      <input className="o day" value={v} autoFocus spellCheck={false}
             onChange={e => setV(e.target.value)}
             onKeyDown={e => {
               if (e.key === 'Enter') { e.preventDefault(); luu() }
               if (e.key === 'Escape') { e.preventDefault(); onHuy() }
             }} />
    </Modal>
  )
}
