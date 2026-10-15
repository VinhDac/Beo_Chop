import { useState } from 'react'
import Icon from '../components/Icon'
import Modal from '../components/Modal'
import { chotSo, locSo } from '../so'
import type { ThamSo } from '../types'
import type { BootMay } from './mayTypes'

/** BẢNG THAM SỐ của cỗ máy — hằng số CÓ TÊN.  (D-10, phần 5, lát 5d)
 *
 *  Vì sao cần: cùng một ngưỡng thường được hỏi ở hai trạm — ② hỏi "EMA nhanh trên chậm
 *  chưa", ④ hỏi "đã rơi quá bao nhiêu phần trăm". Gõ số thẳng vào từng khối thì sửa một
 *  chỗ là hai vế lệch nhau ÂM THẦM. Mẫu dựng sẵn cũng mang núm vặn của nó vào đây, nên
 *  chỉnh một mẫu không phải lục từng khối.
 *
 *  Xoá một tham số đang được dùng KHÔNG bị chặn ở đây: soát lỗi sẽ gọi đúng tên khối
 *  đang hỏng («ô % dùng tham số "x" không có trong bảng»), và đó là chỗ sửa đúng.
 */
export default function ThamSoMayDialog({ dsGoc, boot, onLuu, onDong }: {
  dsGoc: ThamSo[]
  boot: BootMay
  onLuu: (ds: ThamSo[]) => void
  onDong: () => void
}) {
  const [ds, setDs] = useState<ThamSo[]>(() => JSON.parse(JSON.stringify(dsGoc)))
  /** Bản nháp đang gõ ở ô GIÁ TRỊ, theo chỉ số dòng — xem `OSo`/`src/so.ts`. */
  const [nhap, datNhap] = useState<Record<number, string>>({})

  const sua = (i: number, k: keyof ThamSo, v: string | number) =>
    setDs(x => x.map((t, j) => (j === i ? { ...t, [k]: v } : t)))
  const trung = (i: number) =>
    ds.some((t, j) => j !== i && t.ten.trim() === ds[i].ten.trim())

  return (
    <Modal title="Tham số của cỗ máy" width={780} onClose={onDong}
           footer={<>
             <div className="xem-truoc">
               {ds.length} tham số · sửa ở đây là mọi khối dùng nó đổi theo
             </div>
             <button className="nut" onClick={onDong}>Huỷ</button>
             {/* Trùng tên vẫn lưu được thì chuẩn hoá giữ dòng ĐẦU và vứt phần sau, trong
                 khi người vẽ nhìn thấy dòng CUỐI — chặn ngay ở nút. */}
             <button className="nut chinh" disabled={ds.some((_, i) => trung(i))}
                     title={ds.some((_, i) => trung(i))
                       ? 'Còn tham số trùng tên — mỗi tên chỉ được xuất hiện một lần'
                       : undefined}
                     onClick={() => onLuu(ds)}>Lưu</button>
           </>}>
      <div className="chu-dan">
        Ô số nào trong cỗ máy cũng nhận <b>tên tham số</b> thay cho con số. Đơn vị chỉ là
        chữ để đọc ({Object.values(boot.don_vi).join(' · ')}) — chính <b>con số</b> mới là
        thứ bộ máy chạy dùng.
      </div>

      <div className="bang-tham-so">
        <div className="hang dau">
          <span>Tên (không dấu, không khoảng trắng)</span>
          <span>Nhãn</span>
          <span>Giá trị</span>
          <span>Đơn vị</span>
          <span />
        </div>
        {ds.map((t, i) => (
          <div className={'hang' + (trung(i) ? ' loi' : '')} key={i}>
            <input className="o" spellCheck={false} value={t.ten}
                   title={trung(i) ? 'Trùng tên với một tham số khác' : undefined}
                   onChange={e => sua(i, 'ten', e.target.value.replace(/\s+/g, '_'))} />
            <input className="o" spellCheck={false} value={t.nhan}
                   placeholder="để người đọc hiểu"
                   onChange={e => sua(i, 'nhan', e.target.value)} />
            <input className="o so" inputMode="decimal" spellCheck={false}
                   value={nhap[i] ?? t.gia_tri}
                   onChange={e => {
                     const { chu, so } = locSo(e.target.value)
                     datNhap(n => ({ ...n, [i]: chu }))
                     if (so !== null) sua(i, 'gia_tri', so)
                   }}
                   onBlur={() => {
                     if (nhap[i] !== undefined && locSo(nhap[i]).so === null) {
                       sua(i, 'gia_tri', chotSo(nhap[i]))
                     }
                     datNhap(n => { const m = { ...n }; delete m[i]; return m })
                   }} />
            <input className="o nho" spellCheck={false} value={t.don_vi}
                   placeholder="nến · % · giá"
                   onChange={e => sua(i, 'don_vi', e.target.value)} />
            <button className="nut nho" title="Xoá tham số này"
                    onClick={() => setDs(x => x.filter((_, j) => j !== i))}>
              <Icon name="trash" />
            </button>
          </div>
        ))}
        {ds.length === 0 && (
          <div className="trong">
            Chưa có tham số nào — lắp một mẫu dựng sẵn là có ngay vài cái.
          </div>
        )}
      </div>

      <button className="nut nho" onClick={() => setDs(x => [...x, {
        ten: `thamso_${x.length + 1}`, nhan: '', gia_tri: 0, don_vi: '', ghi_chu: '',
      }])}>
        <Icon name="plus" /> Thêm tham số
      </button>
    </Modal>
  )
}
