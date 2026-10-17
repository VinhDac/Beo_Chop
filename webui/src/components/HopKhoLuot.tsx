import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { py } from '../api'
import type { TheLuotChay } from '../types'

/** KHO LƯỢT BACKTEST — mọi lượt đã chạy, mới nhất trước.
 *
 *  Mỗi dòng mở ra một CỬA SỔ RIÊNG, và mở được nhiều cùng lúc: đó là cả lý do kho
 *  này tồn tại. Đổi chu kỳ từ 60 sang 90, chạy lại, rồi xếp hai cửa sổ cạnh nhau —
 *  so hai con số bằng mắt, không phải nhớ cái cũ rồi đoán.
 *
 *  ⚠ Trước đây mỗi lượt chạy XOÁ SẠCH lượt trước (`ket_qua/<tên lớp>/` ghi đè). Lý
 *  do hồi ấy đúng — còn file cũ thì một lượt hỏng vẫn đọc ra số của lượt trước —
 *  nhưng cách chữa làm mất luôn lịch sử, mà lịch sử chính là thứ cần để so.
 */
const CHU: Record<string, string> = {
  'Net Profit': 'Lãi ròng',
  'Compounding Annual Return': 'Lãi/năm',
  Drawdown: 'Sụt sâu nhất',
  'Sharpe Ratio': 'Sharpe',
  'Total Orders': 'Số lệnh',
  'Win Rate': 'Tỷ lệ thắng',
}

function doc(ma: string) {
  // `20261017-131737` -> `17/10/2026 13:17`
  return ma.length === 15 && ma[8] === '-'
    ? `${ma.slice(6, 8)}/${ma.slice(4, 6)}/${ma.slice(0, 4)} ${ma.slice(9, 11)}:${ma.slice(11, 13)}`
    : ma
}

export default function HopKhoLuot({ onDong }: { onDong: () => void }) {
  const [ds, setDs] = useState<TheLuotChay[] | null>(null)
  const [loi, setLoi] = useState('')

  const nap = async () => {
    const r = await py.ds_luot_chay()
    if (r.ok && r.value) setDs(r.value)
    else setLoi(r.error ?? 'không đọc được kho lượt chạy')
  }
  useEffect(() => { void nap() }, [])

  async function xoa(t: TheLuotChay) {
    const r = await py.xoa_luot_chay(t.id)
    if (!r.ok) { setLoi(r.error ?? 'không xoá được'); return }
    void nap()
  }

  return (
    <Modal title="Kho lượt backtest" width={700} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Đóng</button>
           </>}>
      <div className="kho-luot">
        {loi && <div className="mc-bao loi">⚠ {loi}</div>}
        <div className="dau-dk">
          Mỗi dòng mở ra một <b>cửa sổ riêng</b> — mở nhiều cái rồi xếp cạnh nhau để
          so hai phiên bản của cùng một chiến thuật.
        </div>

        {ds && ds.length === 0 && (
          <div className="kq-cho">chưa có lượt nào — bấm <b>Backtest</b> một lần</div>
        )}
        {!ds && !loi && <div className="kq-cho">đang đọc…</div>}

        {(ds ?? []).map(t => (
          <div className="luot" key={t.id}>
            <button className="luot-mo" onClick={() => void py.mo_cua_so_ket_qua(t.id)}
                    title="Mở trong một cửa sổ riêng">
              <span className="luot-ten">{t.ten_lop}</span>
              <span className="luot-luc">{doc(t.ma_luot)}</span>
              <span className="luot-so">
                {Object.entries(t.so).map(([k, v]) => (
                  <i key={k}><b>{CHU[k] ?? k}</b> {v}</i>
                ))}
              </span>
            </button>
            <button className="nut-nho" title="Xoá hẳn lượt này"
                    onClick={() => void xoa(t)}><Icon name="trash" /></button>
          </div>
        ))}
      </div>
    </Modal>
  )
}
