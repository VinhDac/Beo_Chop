import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { Hang } from './ORuot'
import { py } from '../api'
import type { LeanSanSang, OLam } from '../types'
import { datNgonNgu, tr, trx } from '../ngon_ngu'
import { dat_tieng } from '../am_thanh'

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
      else setLoi(td.error ?? tr('không nạp được từ điển Cài đặt'))
      if (v.ok && v.value) setGt(v.value)
      if (sb.ok && sb.value) setLean(sb.value)
    })()
  }, [])

  async function luu() {
    setDangLuu(true)
    const r = await py.cai_dat_ghi(gt)
    setDangLuu(false)
    if (!r.ok || !r.value) { setLoi(r.error ?? tr('không lưu được')); return }
    // Lấy lại giá trị ĐÃ ĐỌC LẠI, không giữ thứ vừa gửi lên: ô gõ bậy đã rơi về mặc
    // định bên Python, và người dùng phải thấy điều đó ngay chứ không phải ở lần mở
    // sau. Trạng thái LEAN cũng tới cùng lượt — đổi thư mục xong là biết đúng chưa.
    setGt(r.value.gia_tri)
    setLean(r.value.lean)
    // ĐỔI TIẾNG NGAY, không đợi mở lại app. Python đã tự chốt bên nó trong `cai_dat_ghi`
    // (mặt khối, bảng Vấn đề do nó dựng); đây là nửa còn lại.
    datNgonNgu(r.value.gia_tri.ngon_ngu)
    // Tắt tiếng phải im NGAY, không đợi mở lại app.
    dat_tieng(r.value.gia_tri.am_thanh)
    if (r.value.lean.ok) onDong()
    else setLoi(r.value.lean.loi)
  }

  return (
    <Modal title={tr('Cài đặt')} width={620} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>{tr('Huỷ')}</button>
             <button className="nut chinh" onClick={() => void luu()} disabled={dangLuu}>
               {dangLuu ? tr('Đang lưu…') : tr('Lưu')}
             </button>
           </>}>
      <div className="hop-lam">
        {loi && <div className="mc-bao loi">⚠ {loi}</div>}
        {!nhom && !loi && <div className="mc-mo">{tr('đang nạp…')}</div>}

        {(nhom ?? []).map(n => (
          <div key={n.ma} className="cd-nhom">
            <div className="cd-dau">{tr(n.nhan)}</div>
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
            <b>{lean.ok ? tr('LEAN đã sẵn sàng') : tr('LEAN chưa dùng được')}</b>
            {lean.ok ? '' : ` — ${lean.loi}`}
          </div>
        )}

        <div className="cd-chu">
          {trx('{0} Strategy, mã sinh ra và kết quả backtest đều nằm '
          + 'trong thư mục {1} cạnh app. Khoá QuantConnect để riêng '
          + 'và không bao giờ nằm trong Strategy.', <Icon name="folder" />, <code>du_lieu\</code>)}</div>
      </div>
    </Modal>
  )
}
