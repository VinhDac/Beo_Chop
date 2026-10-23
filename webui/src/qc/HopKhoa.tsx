import { useState } from 'react'
import Modal from '../components/Modal'
import { pyQC } from '../api'
import type { KhoaQC } from '../types'
import { tr, trx } from '../ngon_ngu'

/** HỘP KHOÁ QUANTCONNECT — đặt User ID + API token ngay trong app.  (D-06)
 *
 * Khoá có TOÀN QUYỀN tài khoản QC, kể cả giao dịch thật. Nên:
 *   · ô token là ô mật khẩu; lưu xong thì xoá khỏi ô, Python không bao giờ trả nó lại;
 *   · khoá nằm ở `du_lieu/qc_khoa.json` trên máy này (trong .gitignore), không đi đâu khác;
 *   · biến môi trường QC_USER_ID / QC_API_TOKEN (nếu đặt) THẮNG file — hộp này nói rõ khi
 *     đang như vậy, vì sửa file lúc đó là sửa mà không có tác dụng.
 */
export default function HopKhoa({ khoa, dong, doi }: {
  khoa: KhoaQC
  dong: () => void
  /** Báo trạng thái khoá mới cho cửa sổ. */
  doi: (k: KhoaQC) => void
}) {
  const [uid, setUid] = useState(khoa.user_id ?? '')
  const [tok, setTok] = useState('')
  const [bao, setBao] = useState<{ chu: string; tot: boolean } | null>(null)
  const [ban, setBan] = useState(false)
  const tuMoiTruong = khoa.nguon === 'bien_moi_truong'

  const luu = async () => {
    setBan(true); setBao(null)
    const r = await pyQC.qc_luu_khoa(uid, tok)
    setBan(false)
    if (!r.ok || !r.value) { setBao({ chu: r.error ?? tr('không lưu được'), tot: false }); return }
    setTok('')
    doi(r.value)
    setBao({ chu: tr('Đã lưu khoá. Bấm «Kiểm với QC» để chắc nó dùng được.'), tot: true })
  }

  const kiem = async () => {
    setBan(true); setBao(null)
    const r = await pyQC.qc_kiem_khoa()
    setBan(false)
    setBao(r.ok ? { chu: tr('QuantConnect nhận khoá — sẵn sàng chạy.'), tot: true }
                : { chu: r.error ?? tr('không kiểm được'), tot: false })
  }

  const xoa = async () => {
    const r = await pyQC.qc_xoa_khoa()
    if (r.ok && r.value) { doi(r.value); setUid(''); setTok('') }
    setBao({ chu: tr('Đã xoá file khoá trên máy này.'), tot: true })
  }

  return (
    <Modal title={tr('Khoá QuantConnect')} width={560} onClose={dong}
           footer={<>
             {khoa.co && <button className="nut" disabled={ban} onClick={kiem}>{tr('Kiểm với QC')}</button>}
             {khoa.nguon === 'file' && <button className="nut do" disabled={ban} onClick={xoa}>{tr('Xoá khoá')}</button>}
             <span style={{ flex: 1 }} />
             <button className="nut" onClick={dong}>{tr('Đóng')}</button>
             {!tuMoiTruong && <button className="nut chinh" disabled={ban || !uid || !tok}
                                      onClick={luu}>{tr('Lưu')}</button>}
           </>}>
      <div className="mc-hop-khoa">
        <p>{trx('App gửi Strategy lên QuantConnect bằng {0} — cần gói {1} trở lên '
        + '(gói Free không có API). Lấy {2} và {3} ở trang tài khoản QC, '
        + 'mục API.', <b>API</b>, <b>Researcher</b>, <b>User ID</b>, <b>API token</b>)}</p>
        <p className="mc-canh-khoa">{trx('Khoá có {0}, kể cả giao dịch thật. Nó chỉ nằm trên máy này '
        + '({1}) — đừng gửi cho ai, đừng dán vào chat.', <b>{tr('toàn quyền tài khoản')}</b>, khoa.duong)}</p>
        <div className="mc-trang-khoa">{trx('Hiện tại: {0}',
          khoa.co
            ? <b>{trx('có khoá · User {0} · {1}', khoa.user_id, tuMoiTruong ? tr('từ biến môi trường') : tr('từ file trên máy'))}</b>
            : <b>{tr('chưa có khoá')}</b>)}
        </div>
        {tuMoiTruong ? (
          <p className="mc-mo">
            {tr('Khoá đang lấy từ biến môi trường QC_USER_ID / QC_API_TOKEN — chúng thắng file, nên '
            + 'muốn đổi khoá thì đổi hai biến đó.')}
          </p>
        ) : (
          <>
            <label className="mc-o">User ID
              <input className="o" value={uid} spellCheck={false} inputMode="numeric"
                     onChange={e => setUid(e.target.value.trim())} placeholder="vd. 123456" /></label>
            <label className="mc-o">API token
              <input className="o" type="password" value={tok} spellCheck={false}
                     autoComplete="off" onChange={e => setTok(e.target.value.trim())}
                     placeholder={khoa.co ? tr('(đã lưu — nhập để thay)') : tr('dán token vào đây')} /></label>
          </>
        )}
        {bao && <div className={'mc-bao ' + (bao.tot ? 'tot' : 'loi')}>{bao.chu}</div>}
      </div>
    </Modal>
  )
}
