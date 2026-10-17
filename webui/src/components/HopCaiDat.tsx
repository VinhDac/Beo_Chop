import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { Hang } from './ORuot'
import { py } from '../api'
import type { LeanSanSang, OLam } from '../types'

/** HỘP CÀI ĐẶT APP.
 *
 *  KHÔNG TỰ KHAI CÓ BAO NHIÊU Ô. Nó hỏi `cai_dat_tu_dien()` rồi dựng, y như
 *  `HopHanhDong` dựng ô của khối Làm — thêm một cài đặt là thêm MỘT dòng trong
 *  `cat_studio/cai_dat.py`, không phải sửa hai nơi. Cùng luật với ba từ điển kia.
 *
 *  ⚠ CHỈ BÀY THỨ CÓ NGƯỜI ĐỌC. `cai_dat.json` xưa nay mang sẵn `symbol`, `accent`,
 *  `ui.panel_cao`, `ui.panel_gap` — bốn khoá không một dòng nào trong app đọc tới.
 *  Bày chúng ra thì người dùng vặn rồi ngồi đợi một thứ không bao giờ đổi; tệ hơn
 *  là không có hộp. Đã bỏ hẳn khỏi bảng mặc định.
 */
interface NhomCD { ma: string; nhan: string; o: OLam[] }

export default function HopCaiDat({ onDong }: { onDong: () => void }) {
  const [nhom, setNhom] = useState<NhomCD[] | null>(null)
  const [gt, setGt] = useState<Record<string, unknown>>({})
  const [lean, setLean] = useState<LeanSanSang | null>(null)
  const [loi, setLoi] = useState('')
  const [dangLuu, setDangLuu] = useState(false)

  useEffect(() => {
    void (async () => {
      const [td, v, sb] = await Promise.all(
        [py.cai_dat_tu_dien(), py.cai_dat_doc(), py.lean_san_sang()])
      if (td.ok && td.value) setNhom(td.value.nhom)
      else setLoi(td.error ?? 'không nạp được từ điển Cài đặt')
      if (v.ok && v.value) setGt(v.value)
      if (sb.ok && sb.value) setLean(sb.value)
    })()
  }, [])

  async function luu() {
    setDangLuu(true)
    const r = await py.cai_dat_ghi(gt)
    setDangLuu(false)
    if (!r.ok || !r.value) { setLoi(r.error ?? 'không lưu được'); return }
    // Lấy lại giá trị ĐÃ ĐỌC LẠI, không giữ thứ vừa gửi lên: ô gõ bậy đã rơi về mặc
    // định bên Python, và người dùng phải thấy điều đó ngay chứ không phải ở lần mở
    // sau. Trạng thái LEAN cũng tới cùng lượt — đổi thư mục xong là biết đúng chưa.
    setGt(r.value.gia_tri)
    setLean(r.value.lean)
    if (r.value.lean.ok) onDong()
    else setLoi(r.value.lean.loi)
  }

  return (
    <Modal title="Cài đặt" width={620} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" onClick={() => void luu()} disabled={dangLuu}>
               {dangLuu ? 'Đang lưu…' : 'Lưu'}
             </button>
           </>}>
      <div className="hop-lam">
        {loi && <div className="mc-bao loi">⚠ {loi}</div>}
        {!nhom && !loi && <div className="mc-mo">đang nạp…</div>}

        {(nhom ?? []).map(n => (
          <div key={n.ma} className="cd-nhom">
            <div className="cd-dau">{n.nhan}</div>
            {n.o.map(o => (
              <Hang key={o.ten} o={o} gt={gt[o.ten]}
                    onDoi={v => setGt(x => ({ ...x, [o.ten]: v }))} />
            ))}
          </div>
        ))}

        {/* TRẠNG THÁI LEAN ngay dưới ô thư mục: câu trả lời «đã đúng chưa» phải tới
            ngay, chứ không bắt người dùng bấm Backtest rồi mới biết. */}
        {lean && (
          <div className={`mc-bao ${lean.ok ? 'tot' : 'loi'}`}>
            <b>{lean.ok ? 'LEAN đã sẵn sàng' : 'LEAN chưa dùng được'}</b>
            {lean.ok ? '' : ` — ${lean.loi}`}
          </div>
        )}

        <div className="cd-chu">
          <Icon name="folder" /> Strategy, mã sinh ra và kết quả backtest đều nằm
          trong thư mục <code>du_lieu\</code> cạnh app. Khoá QuantConnect để riêng
          và không bao giờ nằm trong Strategy.
        </div>
      </div>
    </Modal>
  )
}
