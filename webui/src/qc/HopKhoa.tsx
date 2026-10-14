import { useState } from 'react'
import Modal from '../components/Modal'
import { pyQC } from '../api'
import type { KhoaQC, Reply } from '../types'

/** HỘP KHOÁ QUANTCONNECT — đặt User ID + API token ngay trong app.  (D-06)
 *
 * Khoá có TOÀN QUYỀN tài khoản QC, kể cả live. Nên:
 *   · ô token là ô mật khẩu; lưu xong thì xoá khỏi ô, Python không bao giờ trả nó lại;
 *   · khoá nằm ở `du_lieu/qc_khoa.json` trên máy này (trong .gitignore), không đi đâu khác;
 *   · biến môi trường QC_USER_ID / QC_API_TOKEN (nếu đặt) THẮNG file — hộp này nói rõ khi
 *     đang như vậy, vì sửa file lúc đó là sửa mà không có tác dụng.
 */
/** Ba việc hộp này nhờ Python làm. Mặc định đi qua cửa sổ kỹ thuật (`pyQC`); cửa sổ vẽ
 *  (game) có API riêng nên truyền cầu nối của nó vào — cùng một hộp, hai cửa sổ. */
export interface CauNoiKhoa {
  luu: (userId: string, token: string) => Promise<Reply<KhoaQC>>
  kiem: () => Promise<Reply<boolean>>
  xoa: () => Promise<Reply<KhoaQC>>
}

const CAU_NOI_QC: CauNoiKhoa = {
  luu: (u, t) => pyQC.qc_luu_khoa(u, t),
  kiem: () => pyQC.qc_kiem_khoa(),
  xoa: () => pyQC.qc_xoa_khoa(),
}

export default function HopKhoa({ khoa, dong, doi, cauNoi = CAU_NOI_QC }: {
  khoa: KhoaQC
  dong: () => void
  /** Báo trạng thái khoá mới cho cửa sổ. */
  doi: (k: KhoaQC) => void
  cauNoi?: CauNoiKhoa
}) {
  const [uid, setUid] = useState(khoa.user_id ?? '')
  const [tok, setTok] = useState('')
  const [bao, setBao] = useState<{ chu: string; tot: boolean } | null>(null)
  const [ban, setBan] = useState(false)
  const tuMoiTruong = khoa.nguon === 'bien_moi_truong'

  const luu = async () => {
    setBan(true); setBao(null)
    const r = await cauNoi.luu(uid, tok)
    setBan(false)
    if (!r.ok || !r.value) { setBao({ chu: r.error ?? 'không lưu được', tot: false }); return }
    setTok('')
    doi(r.value)
    setBao({ chu: 'Đã lưu khoá. Bấm «Kiểm với QC» để chắc nó dùng được.', tot: true })
  }

  const kiem = async () => {
    setBan(true); setBao(null)
    const r = await cauNoi.kiem()
    setBan(false)
    setBao(r.ok ? { chu: 'QuantConnect nhận khoá — sẵn sàng chạy.', tot: true }
                : { chu: r.error ?? 'không kiểm được', tot: false })
  }

  const xoa = async () => {
    const r = await cauNoi.xoa()
    if (r.ok && r.value) { doi(r.value); setUid(''); setTok('') }
    setBao({ chu: 'Đã xoá file khoá trên máy này.', tot: true })
  }

  return (
    <Modal title="Khoá QuantConnect" width={560} onClose={dong}
           footer={<>
             {khoa.co && <button className="nut" disabled={ban} onClick={kiem}>Kiểm với QC</button>}
             {khoa.nguon === 'file' && <button className="nut do" disabled={ban} onClick={xoa}>Xoá khoá</button>}
             <span style={{ flex: 1 }} />
             <button className="nut" onClick={dong}>Đóng</button>
             {!tuMoiTruong && <button className="nut chinh" disabled={ban || !uid || !tok}
                                      onClick={luu}>Lưu</button>}
           </>}>
      <div className="mc-hop-khoa">
        <p>
          App gửi cỗ máy lên QuantConnect bằng <b>API</b> — cần gói <b>Researcher</b> trở lên
          (gói Free không có API). Lấy <b>User ID</b> và <b>API token</b> ở trang tài khoản QC,
          mục API.
        </p>
        <p className="mc-canh-khoa">
          Khoá có <b>toàn quyền tài khoản</b>, kể cả giao dịch thật. Nó chỉ nằm trên máy này
          ({khoa.duong}) — đừng gửi cho ai, đừng dán vào chat.
        </p>
        <div className="mc-trang-khoa">
          Hiện tại: {khoa.co
            ? <b>có khoá · User {khoa.user_id} · {tuMoiTruong ? 'từ biến môi trường' : 'từ file trên máy'}</b>
            : <b>chưa có khoá</b>}
        </div>
        {tuMoiTruong ? (
          <p className="mc-mo">
            Khoá đang lấy từ biến môi trường QC_USER_ID / QC_API_TOKEN — chúng thắng file, nên
            muốn đổi khoá thì đổi hai biến đó.
          </p>
        ) : (
          <>
            <label className="mc-o">User ID
              <input className="o" value={uid} spellCheck={false} inputMode="numeric"
                     onChange={e => setUid(e.target.value.trim())} placeholder="vd. 123456" /></label>
            <label className="mc-o">API token
              <input className="o" type="password" value={tok} spellCheck={false}
                     autoComplete="off" onChange={e => setTok(e.target.value.trim())}
                     placeholder={khoa.co ? '(đã lưu — nhập để thay)' : 'dán token vào đây'} /></label>
          </>
        )}
        {bao && <div className={'mc-bao ' + (bao.tot ? 'tot' : 'loi')}>{bao.chu}</div>}
      </div>
    </Modal>
  )
}
