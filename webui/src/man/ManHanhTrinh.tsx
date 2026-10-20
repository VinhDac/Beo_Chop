import { useEffect, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { cho_cau_noi, py } from '../api'
import { tr, useNgonNgu } from '../ngon_ngu'
import type { HanhTrinh, ManHT } from '../types'

/** MÀN HÀNH TRÌNH — bản đồ 9 hồi, 26 màn.
 *
 *  ⚠ KHÔNG KHAI LẠI MỘT MÀN NÀO Ở ĐÂY. Danh sách hồi và màn do `cat_studio/hanh_trinh.py`
 *  giữ, trang này chỉ hỏi rồi vẽ — kể cả chuyện màn nào đang khoá. Viết lại danh sách
 *  bằng TypeScript là đẻ bản sự thật thứ hai, và hôm thêm một màn thì bản đồ với luật
 *  chơi nói khác nhau ở đúng cái hồi ít người chơi tới nhất.
 */
export default function ManHanhTrinh({ onVaoMan, onKho, onRa }: {
  onVaoMan: (ma: string) => void
  /** Mở KHO — chỗ tra 164 đại lượng. */
  onKho: () => void
  onRa: () => void
}) {
  const nn = useNgonNgu()
  const [ht, setHt] = useState<HanhTrinh | null>(null)
  const [loi, setLoi] = useState('')

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        setLoi(tr('Không kết nối được tới Python.'))
        return
      }
      const r = await py.hanh_trinh()
      if (r.ok && r.value) setHt(r.value)
      else setLoi(r.error ?? tr('Không đọc được hành trình.'))
    })()
    // Hỏi lại khi đổi tiếng: chữ của hành trình do PYTHON dịch, không phải bảng bên này.
  }, [nn])

  return (
    <div className="ht">
      <TitleBar tieuDe={tr('Hành trình')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={tr('Về màn mở máy')}>←</button>
      } />
      <button className="ht-kho" onClick={onKho}>{tr('Kho')}</button>

      {loi && <div className="mc-bao loi ht-loi">⚠ {loi}</div>}
      {!ht && !loi && (
        <div className="ht-cho"><Icon name="chay" /> {tr('đang mở hành trình…')}</div>
      )}

      {ht && (
        <div className="ht-than">
          {/* ⚠ NÓI THẲNG LÀ CHƯA CHẤM. Vẽ sẵn mấy ô sao rỗng mà chưa có luật chấm thì
              người chơi tưởng mình chơi mãi không ăn được sao nào. */}
          {!ht.co_luat_cham && (
            <div className="ht-nhac">
              {tr('Hành trình mới dựng xong BỘ KHUNG. Luật chấm sao, màn ẩn và boss là '
                  + 'mốc sau — nên chưa màn nào chấm được.')}
            </div>
          )}

          {ht.hoi.map(h => {
            const ds = ht.man.filter(m => m.hoi === h.ma)
            if (!ds.length) return null
            const xong = ds.filter(m => m.xong).length
            return (
              <section className="ht-hoi" key={h.ma}>
                <header className="ht-hoi-dau">
                  <h2>{h.ten}</h2>
                  <span className="ht-hoi-cau">{h.cau}</span>
                  <span className="day" />
                  <span className="ht-hoi-dem">{xong}/{ds.length}</span>
                </header>
                <div className="ht-day">
                  {ds.map(m => (
                    <TheMan key={m.ma} m={m} dangO={m.ma === ht.dang_o}
                            onBam={() => onVaoMan(m.ma)} />
                  ))}
                </div>
              </section>
            )
          })}
        </div>
      )}
    </div>
  )
}

/** Một màn trên bản đồ.
 *
 *  Màn KHOÁ vẫn cho đọc tên và câu dạy, chỉ không vào được. Giấu hẳn thì người chơi
 *  không thấy hành trình dài bao nhiêu, mà biết trước mình đang đi tới đâu chính là
 *  thứ giữ người ta chơi tiếp. */
function TheMan({ m, dangO, onBam }: {
  m: ManHT; dangO: boolean; onBam: () => void
}) {
  return (
    // ⚠ Lớp ghép THẲNG trong `className`, không gom qua một biến. Hàng rào lớp CSS ma
    // dò bằng cách đọc chữ trong tệp, nên `className={lop}` với nó chỉ là lớp tên
    // «lop» — vừa báo nhầm một lớp không có thật, vừa bỏ lọt ba lớp có thật.
    <button className={'ht-man'
                       + (m.khoa ? ' khoa' : '')
                       + (dangO ? ' dang-o' : '')
                       + (m.dau ? ' dau' : '')}
            disabled={m.khoa} onClick={onBam}
            title={m.khoa ? tr('Chưa mở — chơi xong màn trước đã') : m.day}>
      <div className="ht-man-dau">
        <span className="ht-man-so">{String(m.so).padStart(2, '0')}</span>
        <span className="ht-man-ten">{m.ten}</span>
        {/* ⚠ CHỮ, KHÔNG EMOJI. 🔒 ở cỡ 11px ra một ô vuông màu lạc lõng hẳn với
            bảng màu, và nó không ăn theo theme — cùng lý do `Sao` của bản cũ dùng
            ★ ☆ đơn sắc chứ không dùng emoji. Chỉ ảnh chụp mới thấy. */}
        {m.khoa && <span className="ht-khoa">{tr('khoá')}</span>}
      </div>
      <div className="ht-man-day">{m.day}</div>
      {!!m.mo.length && (
        <div className="ht-mo">
          {m.mo.map(x => <span className="ht-the" key={x}>{x}</span>)}
        </div>
      )}
      {dangO && <div className="ht-dang-o">{tr('Bạn đang ở đây')}</div>}
    </button>
  )
}
