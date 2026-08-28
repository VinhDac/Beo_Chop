import { useEffect, useState } from 'react'
import { py } from '../api'
import type { Bootstrap, Tab } from '../types'
import Modal from './Modal'

/** Hộp thoại sửa MỘT hành động.
 *
 *  Hộp thoại này KHÔNG tự soát lỗi: nó gửi bản nháp thô sang `api.save_action`, Python
 *  chuẩn hoá rồi trả về câu mô tả + danh sách lỗi. Nhờ vậy luật hợp lệ chỉ nằm ở đúng
 *  một chỗ (`core.validate_actions`), và dòng chữ xem trước ở đây chắc chắn là đúng
 *  cái lõi thực sự hiểu — chứ không phải bản dịch thứ hai do JS ghép. **Luật đó không
 *  đổi**, và nó là lý do file này còn tồn tại thay vì bị xoá hẳn.
 *
 *  ⚠ ~590 DÒNG ĐÃ ĐI ở đợt 3 của lần dọn sang HFT market maker, cùng với từ vựng bên
 *  Python. Cái mất, và cái đáng nhớ về từng thứ:
 *
 *  · **`OSo` — ô số dùng chung cho MỌI chỗ chờ một con số.** Luật của nó: *gõ = số;
 *    tên tham số thì KHÔNG gõ được, chỉ app đặt*. Cố tình "ngu" như vậy vì trước đó
 *    bốn trong năm ô chạy `parseFloat`, nên chúng **hiện ra một cái tên mà gõ vào là
 *    nuốt mất** (`chu_ky_atr` → `0`), trong khi ô thứ năm lại có `<datalist>` mời gõ
 *    tên. App dạy một đằng ở ô này rồi phá lời dạy đó ở bốn ô kia.
 *  · **Hàng điều kiện** — toán hạng · phép so · vế phải · đơn vị, cộng cơ chế
 *    "so hai đại lượng" (MỘT lựa chọn cho CẢ KHỐI, không phải chip trên từng dòng).
 *  · **Ô ẩn theo ngữ cảnh** — thứ thuộc về zone bị GIẤU ĐI khi khối chưa nằm sau cổng
 *    zone, thay vì bày ra rồi báo lỗi đỏ.
 *  · **Ô Hướng · Loại lệnh · Lot · Đặt tại · Đệm · SL · TP · Chế độ sửa.**
 *
 *  Còn lại đúng ba ô, và cả ba là ngữ pháp chứ không phải từ vựng: **Loại · Tên ·
 *  Hướng**. Xem `tai_lieu/o_cam_trong.md`; bản cũ ở
 *  `git show f1c90fb:webui/src/components/ActionDialog.tsx`.
 */

type HD = Record<string, any>

export default function ActionDialog({ action, boot, tab, onLuu, onDong }: {
  action: HD
  boot: Bootstrap
  tab: Tab
  onLuu: (a: HD) => void
  onDong: () => void
}) {
  /** Loại hành động dùng được ở tab này. Entry chỉ TẠO, Manage chỉ SỬA. */
  const loaiChoPhep = boot.action_types.filter(t => boot.action_tabs[t]?.includes(tab))
  const [a, setA] = useState<HD>(() => JSON.parse(JSON.stringify(action)))
  const [xem, setXem] = useState('')
  const [loi, setLoi] = useState<string[]>([])

  const dat = (k: string, v: unknown) => setA(x => ({ ...x, [k]: v }))

  /* Xem trước + soát lỗi do PYTHON trả về, hoãn 200ms để gõ không bắn liên tục qua
     cầu nối. */
  useEffect(() => {
    const h = setTimeout(async () => {
      const r = await py.save_action(a, tab)
      if (r.ok) {
        setXem(r.value?.display ?? '')
        setLoi(((r as any).loi as string[]) ?? [])
      } else {
        setXem(''); setLoi([r.error ?? 'không đọc được hành động'])
      }
    }, 200)
    return () => clearTimeout(h)
  }, [a, tab])

  async function doiLoai(t: string) {
    // Lấy mặc định từ Python chứ không tự nặn ở JS: giá trị khởi điểm của một hành
    // động là kiến thức của lõi, không phải của hộp thoại.
    const r = await py.action_defaults(t)
    setA(r.ok && r.value ? { ...r.value, name: a.name } : { type: t, name: a.name })
  }

  return (
    <Modal title={`Hành động — ${boot.action_labels[a.type] ?? a.type}`} width={620}
           onClose={onDong}
           footer={
             <>
               <div className="xem-truoc" title="Đúng câu mà lõi hiểu về hành động này">
                 {xem || '…'}
               </div>
               <button className="nut" onClick={onDong}>Huỷ</button>
               <button className="nut chinh" onClick={() => onLuu(a)}>Lưu</button>
             </>
           }>

      <div className="hang">
        <span className="nhan-o">Loại</span>
        <select className="o" value={a.type} onChange={e => doiLoai(e.target.value)}>
          {loaiChoPhep.map(t =>
            <option key={t} value={t}>{boot.action_labels[t]}</option>)}
        </select>
        <span className="nhan-o phu">Tên</span>
        <input className="o" value={a.name ?? ''} placeholder="(để trống = dùng tên loại)"
               onChange={e => dat('name', e.target.value)} />
      </div>

      {/* HƯỚNG — trường DUY NHẤT còn lại của một khối hành động. Xem `core.HUONG`. */}
      {a.type === 'vao_lenh' && (
        <div className="hang">
          <span className="nhan-o">Hướng</span>
          {Object.entries(boot.huong).map(([k, v]) => (
            <label key={k} className="tick">
              <input type="radio" name="huong" checked={a.huong === k}
                     onChange={() => dat('huong', k)} />{v}
            </label>
          ))}
        </div>
      )}

      <div className="chu-dan">
        Khối chỉ mang được tên và động từ. Điều kiện, đơn vị, mốc neo, SL/TP và chế độ
        sửa đã gỡ cùng MT5 và mô hình nến — chúng quay lại khi chọn xong sàn.
      </div>

      {loi.length > 0 && (
        <div className="chu-dan canh">
          {loi.map((m, i) => <div key={i}>✖ {m}</div>)}
        </div>
      )}
    </Modal>
  )
}
