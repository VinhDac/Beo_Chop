import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { py } from '../api'
import type { TheLuotChay, TheMeToiUu } from '../types'
import { tr, trx } from '../ngon_ngu'

/** KHO — mọi lượt BACKTEST và mọi mẻ OPTIMIZE đã chạy, mới nhất trước.
 *
 *  Mỗi dòng mở ra một CỬA SỔ RIÊNG, và mở được nhiều cùng lúc: đó là cả lý do kho
 *  này tồn tại. Đổi chu kỳ từ 60 sang 90, chạy lại, rồi xếp hai cửa sổ cạnh nhau —
 *  so hai con số bằng mắt, không phải nhớ cái cũ rồi đoán.
 *
 *  HAI TAB, KHÔNG PHẢI HAI HỘP. Backtest và Optimize là hai lối chạy của CÙNG một
 *  sơ đồ, và người ta mở kho ra với cùng một câu hỏi — "lần trước ra bao nhiêu".
 *  Hai hộp riêng thì phải nhớ cái nào nằm ở đâu, mà mỗi hộp lại là một chỗ để quên
 *  không cập nhật.
 *
 *  ⚠ Trước đây mỗi lượt chạy XOÁ SẠCH lượt trước (`ket_qua/<tên lớp>/` ghi đè). Lý
 *  do hồi ấy đúng — còn file cũ thì một lượt hỏng vẫn đọc ra số của lượt trước —
 *  nhưng cách chữa làm mất luôn lịch sử, mà lịch sử chính là thứ cần để so. Nay kho
 *  giữ lại, và Cài đặt quyết giữ bao nhiêu (mặc định 20); quá thì lượt CŨ NHẤT rụng.
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
  const [tab, setTab] = useState<'bt' | 'tu'>('bt')
  const [ds, setDs] = useState<TheLuotChay[] | null>(null)
  const [me, setMe] = useState<TheMeToiUu[] | null>(null)
  const [loi, setLoi] = useState('')

  const nap = async () => {
    const [a, b] = await Promise.all([py.ds_luot_chay(), py.ds_me_toi_uu()])
    if (a.ok && a.value) setDs(a.value)
    else setLoi(a.error ?? tr('không đọc được kho lượt chạy'))
    if (b.ok && b.value) setMe(b.value)
  }
  useEffect(() => { void nap() }, [])

  const dangDoc = tab === 'bt' ? !ds : !me
  const rong = tab === 'bt' ? ds?.length === 0 : me?.length === 0

  return (
    <Modal title={tr('Kho lượt chạy')} width={700} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>{tr('Đóng')}</button>
           </>}>
      <div className="kho-luot">
        {loi && <div className="mc-bao loi">⚠ {loi}</div>}

        <div className="hang-tab kho-tab">
          <button className={'tab' + (tab === 'bt' ? ' dang' : '')}
                  onClick={() => setTab('bt')}>
            Backtest{ds?.length ? ` (${ds.length})` : ''}
          </button>
          <button className={'tab' + (tab === 'tu' ? ' dang' : '')}
                  onClick={() => setTab('tu')}>
            Optimize{me?.length ? ` (${me.length})` : ''}
          </button>
        </div>

        <div className="dau-dk">{trx('Mỗi dòng mở ra một {0} — mở nhiều cái rồi xếp cạnh nhau để '
        + 'so hai phiên bản của cùng một chiến thuật.', <b>{tr('cửa sổ riêng')}</b>)}</div>

        {dangDoc && !loi && <div className="kq-cho">{tr('đang đọc…')}</div>}
        {rong && (
          <div className="kq-cho">
            {tab === 'bt'
              ? <>{trx('chưa có lượt nào — bấm {0} một lần', <b>Backtest</b>)}</>
              : <>{trx('chưa có mẻ nào — ghim một ô số rồi bấm {0}', <b>Optimize</b>)}</>}
          </div>
        )}

        {tab === 'bt' && (ds ?? []).map(t => (
          <div className="luot" key={t.id}>
            <button className="luot-mo" onClick={() => void py.mo_cua_so_ket_qua(t.id)}
                    title={tr('Mở trong một cửa sổ riêng')}>
              <span className="luot-ten">{t.ten_lop}</span>
              <span className="luot-luc">{doc(t.ma_luot)}</span>
              <span className="luot-so">
                {Object.entries(t.so).map(([k, v]) => (
                  <i key={k}><b>{CHU[k] ? tr(CHU[k]) : k}</b> {v}</i>
                ))}
              </span>
            </button>
            <button className="nut-nho" title={tr('Xoá hẳn lượt này')}
                    onClick={() => void (async () => {
                      const r = await py.xoa_luot_chay(t.id)
                      if (!r.ok) { setLoi(r.error ?? tr('không xoá được')); return }
                      void nap()
                    })()}><Icon name="trash" /></button>
          </div>
        ))}

        {tab === 'tu' && (me ?? []).map(t => (
          <div className="luot" key={t.id}>
            <button className="luot-mo" onClick={() => void py.mo_cua_so_toi_uu(t.id)}
                    title={tr('Mở trong một cửa sổ riêng')}>
              <span className="luot-ten">{t.ten_lop}</span>
              <span className="luot-luc">{doc(t.ma_luot ?? '')}</span>
              <span className="luot-so">
                {/* Một mẻ thì con số đáng đọc KHÁC một lượt: không phải lãi bao
                    nhiêu, mà QUÉT CÁI GÌ và quét bao nhiêu lượt. Lãi của từng lượt
                    nằm trong bảng xếp hạng bên trong, mở ra là thấy. */}
                <i><b>{tr('Tìm')}</b> {t.cai?.muc_tieu ?? '—'}</i>
                <i><b>{tr('Núm')}</b> {Object.keys(t.cai?.tham_so ?? {}).join(', ') || '—'}</i>
                <i><b>{tr('Lượt')}</b> {t.so_xong ?? 0}{t.so_luot ? ` / ${t.so_luot}` : ''}</i>
              </span>
            </button>
            <button className="nut-nho" title={tr('Xoá hẳn mẻ này, kể cả mọi lượt bên trong')}
                    onClick={() => void (async () => {
                      const r = await py.xoa_me_toi_uu(t.id)
                      if (!r.ok) { setLoi(r.error ?? tr('không xoá được')); return }
                      void nap()
                    })()}><Icon name="trash" /></button>
          </div>
        ))}
      </div>
    </Modal>
  )
}
