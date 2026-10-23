import { useEffect, useState } from 'react'
import { py } from '../api'
import type { KhoDanhMuc } from '../types'
import Modal from './Modal'
import { tr, trx } from '../ngon_ngu'

/** KHO — app lưu file ở đâu.  (D-12)
 *
 *  Trước đây hộp này còn liệt kê cả từ điển khối; từ điển đã xoá cùng khối cũ, nên giờ
 *  nó nói đúng phần còn thật: thư mục trên đĩa và những gì đang nằm trong đó.
 */
export default function KhoDialog({ onDong }: { onDong: () => void }) {
  const [d, setD] = useState<KhoDanhMuc | null>(null)

  useEffect(() => {
    py.kho_danh_muc().then(r => setD(r.ok ? (r.value ?? null) : null))
  }, [])

  return (
    <Modal title={tr('Kho — app lưu file ở đâu')} width={700} onClose={onDong}
           footer={<><span className="day" />
                     <button className="nut" onClick={onDong}>{tr('Đóng')}</button></>}>
      {!d ? <div className="trong">{tr('đang đọc…')}</div> : (
        <div className="kho">
          <div className="kho-mota">{trx('Mọi thứ app ghi ra nằm dưới {0}', <b>{d.luu_tru.goc}</b>)}</div>
          {d.luu_tru.muc.map(m => (
            <div className="kho-muc" key={m.ten}>
              <div className="kho-dau2"><b>{m.ten}</b>
                <span className="the">{m.so_luong}</span></div>
              <div className="kho-nguon mono">{m.duong_dan}</div>
              {m.danh_sach.length > 0 && (
                <div className="kho-phu">{m.danh_sach.join(' · ')}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
