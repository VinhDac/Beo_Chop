import { useState } from 'react'
import { py } from '../api'
import type { Bootstrap } from '../types'
import Modal from './Modal'

/** CÀI ĐẶT của app — mã mặc định và màu nhấn.
 *
 * Điều kiện chạy (khoảng ngày, vốn, phí, khớp lệnh) KHÔNG nằm ở đây: mỗi màn chơi tự mang
 * điều kiện của nó, còn chế độ Sáng tạo đặt ngay trong cửa sổ Màn chơi.
 */
export default function SettingsDialog({ boot, doiMauNgay, lamMoiBoot, onDong }: {
  boot: Bootstrap
  doiMauNgay: (mau: string) => void
  /** Nạp lại `boot` sau khi lưu — xem chú thích trong `luu()`. */
  lamMoiBoot: () => Promise<void>
  onDong: () => void
}) {
  const s = boot.settings as Record<string, any>
  const [symbol, setSymbol] = useState(String(s.symbol ?? 'XAUUSD'))
  const [accent, setAccent] = useState(String(s.accent ?? '#ffa657'))

  const [loiLuu, setLoiLuu] = useState('')

  async function luu() {
    setLoiLuu('')
    // ⚠ PHẢI xem kết quả. Trước đây bỏ qua rồi `onDong()` vô điều kiện, nên đĩa đầy hay
    // mất quyền ghi thì hộp thoại vẫn đóng như đã lưu xong — im lặng, không dấu vết.
    const r = await py.save_settings({ symbol, accent })
    if (!r.ok) return setLoiLuu(r.error ?? 'không lưu được cài đặt')
    // ⚠ NẠP LẠI `boot` rồi mới đóng. `boot` vốn chỉ nạp MỘT LẦN lúc mở app, mà hộp thoại
    // này lấy giá trị ban đầu từ đó — nên lưu xong, mở lại là thấy y nguyên số CŨ, và
    // người dùng kết luận "bấm lưu không lưu được" (thật ra đĩa đã ghi đúng). `bootstrap`
    // chỉ 1 ms / 7 KB nên nạp lại là rẻ nhất.
    await lamMoiBoot()
    onDong()
  }

  return (
    <Modal title="Cài đặt" width={620} onClose={onDong}
           footer={
             <>
               {loiLuu && <span className="loi-ghi">{loiLuu}</span>}
               <button className="nut" onClick={onDong}>Huỷ</button>
               <button className="nut chinh" onClick={luu}>Lưu</button>
             </>
           }>
      <label className="hang">
        <span className="nhan-o">Mã mặc định</span>
        <input className="o" value={symbol} spellCheck={false}
               onChange={e => setSymbol(e.target.value.toUpperCase())} />
      </label>

      <label className="hang">
        <span className="nhan-o">Màu nhấn</span>
        <div className="cum-mau">
          {Object.entries(boot.accent_presets).map(([ten, mau]) => (
            <button key={ten} title={ten}
                    className={'o-mau' + (mau === accent ? ' dang-chon' : '')}
                    style={{ background: mau }}
                    /* Đổi ngay lúc bấm chứ không đợi Lưu: chọn màu mà không thấy nó
                       trông thế nào thì chọn bằng gì. */
                    onClick={() => { setAccent(mau); doiMauNgay(mau) }} />
          ))}
        </div>
      </label>

      <div className="chu-dan">
        Cài đặt lưu vào <code>du_lieu/cai_dat.json</code> cạnh app, không nằm trong repo.
        Phiên bản {boot.phien_ban} · {boot.app_dir}
      </div>
    </Modal>
  )
}
