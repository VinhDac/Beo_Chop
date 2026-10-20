import { useEffect, useState, type CSSProperties } from 'react'
import TitleBar from '../components/TitleBar'
import { CAC_NGON_NGU, datNgonNgu, tr, trx, useNgonNgu } from '../ngon_ngu'
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

  /** Đổi tiếng — đi qua ĐÚNG cửa mà hộp Cài đặt đi, không gọi thẳng `datNgonNgu`.
   *
   *  ⚠ ĐÃ HỎNG THẬT, và hỏng hai kiểu cùng lúc. Gọi thẳng `datNgonNgu` chỉ đổi ngôn ngữ
   *  TRONG BỘ NHỚ CỦA WEB:
   *    · Python không nghe thấy — mà tên hồi, tên màn, câu dạy đều do Python dựng. Đổi
   *      sang tiếng Việt xong, bản đồ hành trình vẫn nguyên tiếng Anh.
   *    · Không ghi vào Cài đặt, nên `cho_cau_noi` ở lần nối sau đọc lại cài đặt CŨ rồi
   *      `datNgonNgu` ĐẶT NGƯỢC về tiếng Anh (xem `api.ts`). Người dùng đổi tiếng, đi
   *      sang màn khác, và nó tự nhảy về — trông y như app không nhận.
   *  Một cửa duy nhất thì không có chỗ nào để lệch. */
  async function doiTieng(n: string) {
    const r = await py.cai_dat_ghi({ ngon_ngu: n })
    if (r.ok && r.value) datNgonNgu(r.value.gia_tri.ngon_ngu)
  }

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
          <div className="mm-canh">
            <Meo />
            <MayChay />
          </div>

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
              {coNhap ? tr('Vẽ tiếp') : tr('Sáng tạo')}
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

      <div className="mm-chan">
        <select className="o mm-tieng" value={nn}
                onChange={e => void doiTieng(e.target.value)}>
          {CAC_NGON_NGU.map(n => (
            <option key={n.ma} value={n.ma}>{n.nhan}</option>
          ))}
        </select>
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

/** CON MÈO — kỹ sư của cái xưởng này.
 *
 *  ⚠ ĐÂY LÀ BẢN TẠM, và cố ý vẽ tối giản để dễ thay. Tên app đã là Cat Studio nhưng
 *  trước mốc này "con mèo" là đúng một file `favicon.ico`; app không có mặt mũi nào.
 *  Hình thật là việc của chủ dự án (thiết kế §10.1) — chỗ này chỉ giữ sẵn khoảng
 *  trống đúng kích thước, đúng bảng màu, và đúng TÍNH CÁCH: thợ máy, không phải linh
 *  vật. Nó ngồi CẠNH cái máy vì chính nó lắp ra cái máy ấy.
 *
 *  Chớp mắt bằng CSS, không bằng JS: một thuộc tính chạy trên GPU, không tốn khung
 *  hình nào, và tắt được bằng `prefers-reduced-motion` như mọi hoạt ảnh khác. */
function Meo() {
  return (
    <svg className="mm-meo" viewBox="0 0 96 104" aria-hidden>
      {/* tai */}
      <path className="mm-meo-net" d="M20 40 L24 12 L46 30" />
      <path className="mm-meo-net" d="M76 40 L72 12 L50 30" />
      {/* đầu */}
      <path className="mm-meo-net" d="M48 26 C72 26 84 42 84 60 C84 80 68 92 48 92
                                      C28 92 12 80 12 60 C12 42 24 26 48 26 Z" />
      {/* mắt — hai vạch, nheo lại chứ không tròn xoe: nó đang NHÌN cái máy */}
      <g className="mm-meo-mat">
        <path d="M30 58 h12" /><path d="M54 58 h12" />
      </g>
      {/* mũi và ria */}
      <path className="mm-meo-net" d="M48 68 l-5 5 h10 Z" />
      <g className="mm-meo-ria">
        <path d="M18 64 h14" /><path d="M64 64 h14" />
        <path d="M18 72 h14" /><path d="M64 72 h14" />
      </g>
    </svg>
  )
}

/** CỖ MÁY ĐANG CHẠY — hình nền sống của màn mở.
 *
 *  Vẽ bằng SVG ngay tại đây chứ không nhét một file ảnh: đây CHÍNH LÀ thứ app làm ra —
 *  mấy khối nối nhau và dòng điện chạy trong dây — nên nó phải sống, không phải một bức
 *  hình chết. Và nó là bản xem trước của màn «Chạy máy» ở mốc sau.
 *
 *  ⚠ MỖI SỢI DÂY LÀ HAI ĐƯỜNG CHỒNG NHAU, và đây là chỗ bản đầu làm sai. Một đường
 *  không thể vừa là sợi dây vừa là vệt sáng chạy trên nó: muốn vệt sáng thì phải đặt
 *  `stroke-dasharray`, mà đặt lên chính sợi dây thì gần hết sợi dây thành KHOẢNG TRỐNG.
 *  Nhìn ảnh chụp mới thấy — bốn cái khối rời nhau với mấy mẩu dây cụt 8 pixel, không ra
 *  cái máy nào cả. Nay: một đường NỀN liền nét lúc nào cũng có, một đường SÁNG đứt nét
 *  chạy đè lên.
 *
 *  Dòng chảy làm bằng `stroke-dashoffset` chạy vòng: một thuộc tính, chạy trên GPU,
 *  không tốn một khung hình JS nào và không bao giờ giật khi máy đang bận. */
function MayChay() {
  /** Ba chặng dây, viết một lần dùng hai lần (nền + vệt sáng) — chép tay hai bản là
   *  sớm muộn sửa toạ độ một bên mà quên bên kia. */
  const day = ['M96 64 H176', 'M232 64 H312', 'M368 64 H440']
  /** Nhịp của cả cụm, giây. Mỗi khối mọc lên sau khối trước một nhịp; sợi dây nối
   *  chúng mọc xen vào giữa. Một con số, sửa một chỗ. */
  const n = 0.26
  /** Mốc thời gian của từng món, truyền xuống CSS bằng `--d`.
   *
   *  ⚠ MỘT BIẾN CSS, KHÔNG PHẢI `animationDelay`. Mỗi món nay chạy HAI hoạt ảnh — một
   *  lượt MỌC LÊN chạy đúng một lần, rồi một lượt SÁNG lặp mãi — mà `animationDelay`
   *  viết thẳng thì phải ghi hai giá trị dính nhau và đếm tay cái thứ hai. Đưa mốc vào
   *  biến rồi để CSS tự cộng (`calc(var(--d) + …)`) thì sửa nhịp là xong. */
  const d = (i: number) => ({ '--d': `${0.5 + i * n}s` } as CSSProperties)
  return (
    <svg className="mm-may" viewBox="0 0 520 128" aria-hidden>
      <g className="mm-nen">
        {day.map((x, i) => <path key={x} d={x} pathLength={1} style={d(i * 2 + 1)} />)}
      </g>
      <g className="mm-dong">
        {day.map((x, i) => <path key={x} d={x} style={d(i * 2 + 1)} />)}
      </g>
      <g className="mm-khoi">
        <rect x="30" y="40" width="66" height="48" rx="9" style={d(0)} />
        <rect x="176" y="40" width="56" height="48" rx="9" style={d(2)} />
        <rect x="312" y="40" width="56" height="48" rx="9" style={d(4)} />
        {/* KHỐI CUỐI là chỗ trả lời «nó sống được không», nên nó không sáng màu
            thương hiệu như ba khối kia mà LOÉ XANH — đúng màu app dùng cho «được»
            ở mọi nơi khác. Cả câu quảng cáo gói trong một nhịp sáng. */}
        <circle className="mm-ket" cx="462" cy="64" r="22" style={d(6)} />
      </g>
    </svg>
  )
}
