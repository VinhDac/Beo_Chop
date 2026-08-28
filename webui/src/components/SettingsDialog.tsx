import { useState } from 'react'
import { py } from '../api'
import type { Bootstrap, CaiDatKhop } from '../types'
import KhopPanel from './KhopPanel'
import Modal from './Modal'
import NguonPanel from './NguonPanel'

/** CÀI ĐẶT của app — ba tab: **Chung** · **Nguồn dữ liệu** · **Mô hình khớp**.
 *
 * ⚠ MỤC "STRATEGY TEST" ĐÃ ĐI HẲN (đợt 2 của lần dọn sang HFT market maker). Nó mang
 * bảng nguồn nến M1, nút kiểm kết nối MT5, và năm ô điều kiện chạy backtest — spread
 * tính bằng point, vốn, phí round-turn, đòn bẩy, nhịp phát lại. Cả năm ô đó là tham số
 * của một BỘ CHẠY THEO NẾN đã bị gỡ, nên để lại thì chúng cấu hình cho hư không.
 *
 * Tab **Nguồn dữ liệu** thay chỗ ấy — nhưng nói về thứ khác hẳn: không phải "tải bao
 * nhiêu nến" mà "bộ ghi còn sống không, dữ liệu dày lên tới đâu". Xem `NguonPanel`.
 *
 * Tab **Mô hình khớp** là MẶT KIA của tab Nguồn, và cặp đôi ấy là một ý duy nhất:
 * *đo được thì đừng hỏi · không đo được thì đừng giấu*. Xem `KhopPanel`.
 *
 * ⚠ CHÂN HỘP THOẠI ĐỔI THEO TAB, và đó là chủ ý. Chung và Mô hình khớp có Huỷ/Lưu vì
 * chúng sửa một bản nháp; tab Nguồn thì mọi nút đều tác động NGAY (bật ghi, dừng, xoá)
 * nên một cái nút "Lưu" ở đó là lời hứa hão — không có gì để lưu, và nó gợi ý rằng bấm
 * Huỷ sẽ hoàn tác được cái vừa xoá.
 */
export default function SettingsDialog({ boot, doiMauNgay, lamMoiBoot, onDong }: {
  boot: Bootstrap
  doiMauNgay: (mau: string) => void
  /** Nạp lại `boot` sau khi lưu — xem chú thích trong `luu()`. */
  lamMoiBoot: () => Promise<void>
  onDong: () => void
}) {
  const s = boot.settings as Record<string, any>
  const [tab, setTab] = useState<'chung' | 'nguon' | 'khop'>('chung')
  const [symbol, setSymbol] = useState(String(s.symbol ?? 'XAUUSD'))
  const [accent, setAccent] = useState(String(s.accent ?? '#ffa657'))
  const [khop, setKhop] = useState<CaiDatKhop>(() => ({ ...(s.khop as CaiDatKhop) }))
  const [loiLuu, setLoiLuu] = useState('')
  /* Tab nào sửa một BẢN NHÁP thì có Huỷ/Lưu; tab Nguồn tác động ngay nên chỉ có Đóng. */
  const banNhap = tab !== 'nguon'

  async function luu() {
    setLoiLuu('')
    // ⚠ PHẢI xem kết quả. Trước đây bỏ qua rồi `onDong()` vô điều kiện, nên đĩa đầy hay
    // mất quyền ghi thì hộp thoại vẫn đóng như đã lưu xong — im lặng, không dấu vết.
    const r = await py.save_settings({ symbol, accent, khop })
    if (!r.ok) return setLoiLuu(r.error ?? 'không lưu được cài đặt')
    // ⚠ NẠP LẠI `boot` rồi mới đóng. `boot` vốn chỉ nạp MỘT LẦN lúc mở app, mà hộp thoại
    // này lấy giá trị ban đầu từ đó — nên lưu xong, mở lại là thấy y nguyên số CŨ, và
    // người dùng kết luận "bấm lưu không lưu được" (thật ra đĩa đã ghi đúng).
    await lamMoiBoot()
    onDong()
  }

  return (
    <Modal title="Cài đặt" width={tab === 'chung' ? 620 : 740} onClose={onDong}
           footer={banNhap ? (
             <>
               {loiLuu && <span className="loi-ghi">{loiLuu}</span>}
               <button className="nut" onClick={onDong}>Huỷ</button>
               <button className="nut chinh" onClick={luu}>Lưu</button>
             </>
           ) : (
             <button className="nut" onClick={onDong}>Đóng</button>
           )}>

      <div className="hang-tab cd-tab">
        <button className={'tab' + (tab === 'chung' ? ' dang' : '')}
                onClick={() => setTab('chung')}>Chung</button>
        <button className={'tab' + (tab === 'nguon' ? ' dang' : '')}
                onClick={() => setTab('nguon')}>Nguồn dữ liệu</button>
        <button className={'tab' + (tab === 'khop' ? ' dang' : '')}
                onClick={() => setTab('khop')}>Mô hình khớp</button>
      </div>

      {tab === 'chung' ? (
        <>
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
            Cài đặt lưu vào <code>du_lieu/cai_dat.json</code> cạnh app, không nằm trong
            repo. Phiên bản {boot.phien_ban} · {boot.app_dir}
          </div>
        </>
      ) : tab === 'nguon' ? <NguonPanel /> : (
        <KhopPanel khop={khop} dat={(k, v) => setKhop(x => ({ ...x, [k]: v }))} />
      )}
    </Modal>
  )
}
