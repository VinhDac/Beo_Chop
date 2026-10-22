import { useEffect, useState } from 'react'
import TitleBar from '../components/TitleBar'
import { tr, trx, useNgonNgu } from '../ngon_ngu'
import { cho_cau_noi, py } from '../api'
import type { SoLieu } from '../types'

/** MÀN MỞ MÁY — thứ đầu tiên người ta thấy khi bật app.
 *
 *  Trước mốc này, mở app lên là một canvas trống với 164 đại lượng chờ sẵn. Không một
 *  dòng nào nói đây là cái gì, bắt đầu từ đâu. Màn này làm đúng một việc: nói app này
 *  là cái gì, rồi đưa người ta đi đúng một trong hai hướng.
 *
 *  ⚠ CÓ Ô ĐỔI TIẾNG NGAY ĐÂY, và nó không thừa. App mặc định tiếng Anh, mà hộp Cài đặt
 *  lại nằm trong Xưởng — tức người Việt mở app lần đầu phải đi xuyên qua một màn hình
 *  tiếng Anh mới tới được chỗ đổi sang tiếng Việt. Ô này ghi bằng CHÍNH tiếng của nó
 *  ("English" / "Tiếng Việt") nên ai cũng tìm ra chữ của mình.
 */
export default function ManMoMay({ onHanhTrinh, onSangTao }: {
  onHanhTrinh: () => void
  onSangTao: () => void
}) {
  const nn = useNgonNgu()
  /** Có bản nháp dở dang không — để nút đầu tiên nói đúng việc nó làm. */
  const [coNhap, setCoNhap] = useState(false)
  /** Mấy con số khoe ở dải dưới. ĐẾM bên Python (`api.so_lieu`) — xem lời ở đó. */
  const [so, setSo] = useState<SoLieu | null>(null)

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        return                      // không nối được thì vẫn vào được Xưởng, nó tự báo
      }
      const r = await py.doc_ban_nhap()
      setCoNhap(!!(r.ok && r.value && (r.value.steps?.length ?? 0) > 0))
      const t = await py.so_lieu()
      if (t.ok && t.value) setSo(t.value)
    })()
  }, [])



  return (
    <div className="mm" key={nn}>
      <TitleBar tieuDe="Cat Studio" menus={[]} />

      <BieuDoNen />

      <div className="mm-than">
        {/* ⚠ CẢ CỤM NẰM TRONG MỘT HỘP `min-height: 100%`, không căn bằng
            `justify-content` trên chính khung cuộn. Cửa sổ thấp hơn cụm chữ thì cách
            kia để nó TRÀN RA CẢ HAI ĐẦU — con mèo trèo lên đè chữ của thanh tiêu đề —
            và phần tràn lên phía trên thì không cuộn tới được, lỗi kinh điển của
            flexbox. Hộp này thì đủ chỗ là căn giữa, thiếu chỗ là tự cao lên và cuộn. */}
        <div className="mm-giua">
          {/* LOGO THẬT của app, không phải hình vẽ tay nữa.
              Trước đây chỗ này là một con mèo vẽ bằng SVG cộng một cỗ máy bốn khối —
              hình TẠM, dựng lúc app chưa có mặt mũi nào ngoài một file `.ico`. App có
              logo thật rồi thì màn hình đầu tiên phải là nó: một hình vẽ tay cạnh một
              logo khác là hai bộ mặt cho cùng một sản phẩm. */}
          <img className="mm-logo" src="./logo.png" alt="" />

          <h1 className="mm-ten">Cat Studio</h1>
          <p className="mm-cau">{tr('Vẽ một cỗ máy. Thả nó vào thị trường. Xem nó sống được không.')}</p>

          <div className="mm-nut">
            <button className="nut-to chinh" onClick={onHanhTrinh}>
              {tr('Hành trình')}
              {/* ⚠ BỎ CON SỐ KHỎI CÂU NÀY. Trước đây nó viết «26 màn» bằng tay,
                  mà ngay bên dưới dải số đã ĐẾM ra 26 từ `hanh_trinh.MAN` — hai bản
                  của một con số, nằm cách nhau sáu dòng trên cùng một màn hình. Thêm
                  một màn là câu trên sai còn câu dưới đúng. Một con số, một chỗ. */}
              <small>{tr('Học từ cái máy hai khối tới boss cuối')}</small>
            </button>
            <button className="nut-to" onClick={onSangTao}>
              {/* ⚠ TÊN CHẾ ĐỘ KHÔNG ĐỔI THEO VIỆC CÓ BẢN NHÁP HAY KHÔNG. Trước đây
                  nút này lúc thì «Vẽ tiếp», lúc thì «Sáng tạo» — cùng một cánh cửa mà
                  hai cái tên, nên người chơi không bao giờ học được nơi mình sắp vào
                  là gì, và cái tên app vẫn gọi khắp nơi (`che_do:sang_tao`, màn Chạy
                  máy, bản thiết kế §2) thì nửa số lần không hiện ra. Tên đứng yên;
                  chuyện có bản nháp dở hay không là việc của dòng chữ nhỏ bên dưới. */}
              {tr('Chế độ Sáng tạo')}
              <small>{coNhap
                ? tr('Mở lại cỗ máy đang vẽ dở')
                : tr('Mở hết đồ nghề, không chấm điểm')}</small>
            </button>
          </div>

          {/* DẢI SỐ — nửa dưới màn hình trước đây bỏ trống hẳn. Mấy con số này là thứ
              phân biệt app với một bản vẽ sơ đồ, nên chúng đáng đứng ở trang đầu.
              ⚠ CÂU DỊCH NGUYÊN VẸN, không ghép «{số}» với `tr('đại lượng')`. Ghép chữ
              rời thì bản tiếng Anh ra «4 a block» — đã dính một lần rồi; `trx` dịch cả
              câu nên bên kia tự lo số nhiều. */}
          {!!so && (
            <div className="mm-so">
              <span>{trx('{0} đại lượng', <b key="a">{so.dai_luong}</b>)}</span>
              <i />
              <span>{trx('{0} nhóm', <b key="a">{so.nhom}</b>)}</span>
              <i />
              <span>{trx('{0} màn', <b key="a">{so.man}</b>)}</span>
              <i />
              <span>{trx('{0} việc làm được', <b key="a">{so.viec}</b>)}</span>
              <i />
              <span className="mm-lean">{tr('chạy trên LEAN thật')}</span>
            </div>
          )}
        </div>
      </div>

    </div>
  )
}

/** NỀN TRANG CHỦ — một đường thị trường TỰ VẼ RA từ trái sang phải.
 *
 *  Câu đầu tiên của app là «Thả nó vào thị trường». Trước đây nền trang chủ là một
 *  mảng đen phẳng, nên câu ấy không có gì đỡ. Nay thị trường có mặt ngay sau lưng cỗ
 *  máy: lưới mờ, một đường đi lên có hai cú sụt, và một vệt quét chạy qua một lần như
 *  lúc tua lại một đoạn lịch sử.
 *
 *  ⚠ ĐÂY LÀ HOA VĂN, KHÔNG PHẢI SỐ LIỆU — và chỗ này phải ghi rõ vì nó rất dễ bị hiểu
 *  nhầm thành một kết quả backtest. Không trục, không mốc, không một con số nào, và
 *  đậm chưa tới hai phần mười. Ai sau này định gắn trục hay nhãn giá vào đây thì dừng
 *  lại: app hứa mọi con số đều do LEAN tính ra (D-11), mà một đường cong vẽ tay có
 *  nhãn giá là lời hứa ấy gãy ngay ở màn hình đầu tiên.
 *
 *  `pathLength="1"` để hoạt ảnh vẽ-dần đo bằng PHẦN, không bằng pixel: khung nhìn co
 *  giãn theo cửa sổ nên độ dài thật của đường đổi liên tục, gõ cứng một con số
 *  `stroke-dasharray` là ở cửa sổ rộng thì đường vẽ xong sớm rồi đứng im nửa giây. */
const DUONG = 'M0 300 L60 288 L120 302 L180 270 L240 282 L300 244 L360 256 '
  + 'L420 210 L480 232 L540 300 L600 322 L660 286 L720 252 L780 264 L840 206 '
  + 'L900 176 L960 198 L1020 140 L1080 158 L1140 104 L1200 86'

function BieuDoNen() {
  return (
    <svg className="mm-bieu-do" viewBox="0 0 1200 420"
         preserveAspectRatio="none" aria-hidden>
      <defs>
        <linearGradient id="mm-to" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity=".11" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
        <linearGradient id="mm-quet" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity=".35" />
        </linearGradient>
      </defs>
      {/* Lưới: dựng bằng vòng lặp chứ không gõ tay 20 thẻ — gõ tay thì sửa khoảng
          cách một cái là phải đếm lại cả hai mươi. */}
      <g className="mm-luoi">
        {Array.from({ length: 11 }, (_, i) => (
          <path key={'d' + i} d={`M${i * 120} 0 V420`} />
        ))}
        {Array.from({ length: 6 }, (_, i) => (
          <path key={'n' + i} d={`M0 ${i * 70} H1200`} />
        ))}
      </g>
      <path className="mm-to" d={`${DUONG} L1200 420 L0 420 Z`} fill="url(#mm-to)" />
      <path className="mm-duong" d={DUONG} pathLength={1} />
      <rect className="mm-vet" x="-180" y="0" width="180" height="420"
            fill="url(#mm-quet)" />
    </svg>
  )
}
