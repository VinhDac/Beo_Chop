import { useEffect, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { cho_cau_noi, py } from '../api'
import { tr, useNgonNgu } from '../ngon_ngu'
import { soTien } from '../so'
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

  const xongCa = ht ? ht.man.filter(m => m.xong).length : 0

  return (
    <div className="ht">
      <TitleBar tieuDe={tr('Hành trình')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={tr('Về màn mở máy')}>←</button>
      } />

      {loi && <div className="mc-bao loi ht-loi">⚠ {loi}</div>}
      {!ht && !loi && (
        <div className="ht-cho"><Icon name="chay" /> {tr('đang mở hành trình…')}</div>
      )}

      {ht && (
        <div className="ht-than">
          {/* ⚠ CON SỐ TO NHẤT MÀN HÌNH LÀ TIẾN TRÌNH CỦA NGƯỜI CHƠI. Bản trước mở đầu
              bằng một dải cam kín bề ngang báo "hành trình mới có bộ khung" — thứ ồn
              nhất màn hình lại là một lời nhắn về chuyện làm app, và nó còn sai từ hôm
              luật chấm xong. Nay chỗ ấy là thành tích: đi được mấy màn, ăn được mấy sao. */}
          <div className="ht-tong">
            <div className="ht-tong-o">
              <span className="ht-tong-so">{xongCa}<i>/{ht.man.length}</i></span>
              <span className="ht-tong-nhan">{tr('màn đã qua')}</span>
            </div>
            <div className="ht-tong-o">
              {/* ⚠ NGÔI SAO PHẢI RA KHỎI CHỮ ĐỀU Ô. Mấy phông đều ô (Consolas…)
                  không có ★, nên hệ thống rơi về phông EMOJI và vẽ một ngôi sao vàng
                  bóng loáng không ăn theo theme — đúng cái bẫy thẻ «khoá» trên bản đồ
                  đã tránh bằng chữ. Trả nó về phông chữ thường thì nó là một ký hiệu
                  đơn sắc, tô được bằng `--warn`, y như màn Chấm. */}
              <span className="ht-tong-so sao">
                <i className="ht-ngoi">★</i> {ht.sao_dang_co}<i>/{ht.sao_toi_da}</i>
              </span>
              <span className="ht-tong-nhan">{tr('sao đã ăn')}</span>
            </div>
            <span className="day" />
            <button className="ht-kho" onClick={onKho}>
              <Icon name="folder" /> {tr('Kho')}
            </button>
          </div>

          {ht.hoi.map(h => {
            const ds = ht.man.filter(m => m.hoi === h.ma)
            if (!ds.length) return null
            const xong = ds.filter(m => m.xong).length
            const du = xong === ds.length
            return (
              <section className="ht-hoi" key={h.ma}>
                <header className="ht-hoi-dau">
                  <h2>{h.ten}</h2>
                  <span className="ht-hoi-cau">{h.cau}</span>
                  <span className="day" />
                  <span className={'ht-hoi-dem' + (du ? ' du' : '')}>{xong}/{ds.length}</span>
                  <span className="ht-vach">
                    <i className={du ? 'du' : ''}
                       style={{ width: `${(xong / ds.length) * 100}%` }} />
                  </span>
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
                       + (m.xong ? ' xong' : '')
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
        {/* Sao đã ăn. `cham_duoc` do PYTHON nói — giao diện mà tự suy "màn 0 thì
            không chấm" là chép lại luật chơi bằng thứ tiếng thứ hai. */}
        {!m.khoa && m.cham_duoc && (
          <span className="ht-sao">
            {[0, 1, 2].map(i => (
              <i key={i} className={i < m.sao ? 'an' : ''}>★</i>
            ))}
          </span>
        )}
      </div>
      <div className="ht-man-day">{m.day}</div>
      {/* SÂN THẬT của màn đang đứng — mã, khoảng ngày, vốn. Chỉ vẽ ở thẻ đang đứng:
          bày trên cả 26 thẻ thì ba dòng chữ đều ô ấy thành một tấm thảm, và chính
          chỗ đáng nhìn lại chìm vào đó.
          ⚠ `thay` là khoảng ĐÃ THẤY. Khoảng ẩn không bao giờ ra tới giao diện — biết
          ngày ẩn là vặn máy cho vừa khít đúng khoảng ấy, và ngôi sao thứ ba mất sạch
          nghĩa mà vẫn sáng lên y như thật. */}
      {dangO && !!m.symbol && (
        <div className="ht-san">
          <span className="ht-san-ma">{m.symbol.toUpperCase()}</span>
          {!!m.thay && <span>{m.thay[0]} → {m.thay[1]}</span>}
          {!!m.von && <span>${soTien(m.von)}</span>}
          {!!m.boss && <span className="ht-san-boss">{tr('boss')} · {m.boss.ten}</span>}
        </div>
      )}
      {/* Màn chưa có sân thì NÓI VÌ SAO ngay trên thẻ — "chưa làm" và "dữ liệu
          miễn phí không đỡ nổi" là hai chuyện khác hẳn nhau. */}
      {m.co_san === false && !!m.vi_sao_chua && (
        <div className="ht-chua">{m.vi_sao_chua}</div>
      )}
      {!!m.mo.length && (
        <div className="ht-mo">
          {/* Chấm màu nói món đồ này nằm ĐÂU: xanh là đại lượng mới trong Kho, cam là
              đồ nghề mới trong Xưởng. `loai` do Python gửi sang, xem `the_mo`. */}
          {m.mo.map(x => (
            <span className={'ht-the ' + x.loai} key={x.nhan}>{x.nhan}</span>
          ))}
        </div>
      )}
      {dangO && <div className="ht-dang-o">{tr('Bạn đang ở đây')}</div>}
    </button>
  )
}
