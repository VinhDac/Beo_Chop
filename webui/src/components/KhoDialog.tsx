import { useEffect, useState } from 'react'
import { py } from '../api'
import type { KhoDanhMuc } from '../types'
import Modal from './Modal'

/** KHO — "app đang có những gì".  (D-10, phần 7)
 *
 *  Không phải trang trí: người chơi cần biết mình có bao nhiêu khối, đại lượng nào đọc
 *  được ở trạm nào, và file của mình nằm ở đâu trên đĩa. Toàn bộ danh mục do Python gom
 *  thẳng từ TỪ ĐIỂN 5 TRẠM (`tram.py`), nên thêm một khối Làm ở đó là hộp thoại này có
 *  ngay — không có danh sách thứ hai để quên cập nhật.
 */
export default function KhoDialog({ onDong }: { onDong: () => void }) {
  const [d, setD] = useState<KhoDanhMuc | null>(null)
  const [muc, setMuc] = useState<'tram' | 'khoi' | 'dai_luong' | 'may' | 'file'>('tram')

  useEffect(() => {
    py.kho_danh_muc().then(r => setD(r.ok ? (r.value ?? null) : null))
  }, [])

  if (!d) {
    return (
      <Modal title="Kho — app đang có những gì" width={820} onClose={onDong}
             footer={<><span className="day" />
                       <button className="nut" onClick={onDong}>Đóng</button></>}>
        <div className="trong">đang đọc…</div>
      </Modal>
    )
  }

  const TAB: [typeof muc, string, number][] = [
    ['tram', 'Năm trạm', d.tram.length],
    ['khoi', 'Khối Làm', d.khoi_lam.length],
    ['dai_luong', 'Đại lượng', d.toan_hang.length],
    ['may', 'Cỗ máy dựng sẵn', d.may_san.length],
    ['file', 'File trên đĩa', d.luu_tru.muc.length],
  ]

  return (
    <Modal title="Kho — app đang có những gì" width={880} onClose={onDong}
           footer={<><span className="day" />
                     <button className="nut" onClick={onDong}>Đóng</button></>}>
      <div className="hang-tab kho-dau">
        {TAB.map(([k, ten, n]) => (
          <button key={k} className={'tab' + (muc === k ? ' dang' : '')}
                  onClick={() => setMuc(k)}>{ten} ({n})</button>
        ))}
      </div>

      <div className="kho">
        {muc === 'tram' && d.tram.map(t => (
          <div className="kho-muc" key={t.so}>
            <div className="kho-dau2"><b>{t.so} {t.ten}</b>
              <span className="the">{t.qc}</span></div>
            <div className="kho-mota">{t.hoi} Chạy cho {t.cho_ai}, ra {t.ra}.</div>
            <div className="kho-phu">
              {t.so_khoi_lam} khối Làm · {t.so_dai_luong} đại lượng đọc được ·
              {' '}{t.so_mau} mẫu dựng sẵn
            </div>
          </div>
        ))}

        {muc === 'khoi' && (
          <table className="kho-bang"><thead><tr>
            <th>Khối</th><th>Trạm</th><th>Vai</th><th>Làm gì</th>
          </tr></thead><tbody>
            {d.khoi_lam.map(k => (
              <tr key={k.key}>
                <td><b>{k.nhan}</b></td>
                <td className="mono">{k.tram}</td>
                <td>{k.vai === 'phu' ? 'khối phụ' : 'quyết định'}</td>
                <td className="kho-mota">{k.mo_ta}</td>
              </tr>
            ))}
          </tbody></table>
        )}

        {muc === 'dai_luong' && (
          <table className="kho-bang"><thead><tr>
            <th>Đại lượng</th><th>Nhóm</th><th>Đơn vị</th><th>Đọc được ở</th><th>Ghi chú</th>
          </tr></thead><tbody>
            {d.toan_hang.map(t => (
              <tr key={t.key}>
                <td><b>{t.nhan}</b></td>
                <td>{t.nhom}</td>
                <td className="mono">{t.don_vi}</td>
                <td className="mono">{t.tram}</td>
                <td className="kho-mota">{t.mo_ta}</td>
              </tr>
            ))}
          </tbody></table>
        )}

        {muc === 'may' && d.may_san.map(m => (
          <div className="kho-muc" key={m.ten}>
            <div className="kho-dau2"><b>{m.ten}</b></div>
            <div className="kho-mota">{m.mo_ta}</div>
          </div>
        ))}

        {muc === 'file' && (
          <>
            <div className="kho-mota">Mọi thứ app ghi ra nằm dưới <b>{d.luu_tru.goc}</b></div>
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
          </>
        )}
      </div>
    </Modal>
  )
}
