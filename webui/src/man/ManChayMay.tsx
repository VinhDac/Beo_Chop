import {
  createContext, memo, useContext, useEffect, useMemo, useRef, useState,
} from 'react'
import {
  BaseEdge, Background, BackgroundVariant, Handle, Position, ReactFlow,
  ReactFlowProvider, getBezierPath, useReactFlow,
  type Edge as RfEdge, type EdgeProps, type Node as RfNode, type NodeProps,
} from '@xyflow/react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { py } from '../api'
import { tr, trx, useNgonNgu } from '../ngon_ngu'
import { keu } from '../am_thanh'
import type {
  Card, CoMay, Edge, KetQuaChay, KetQuaSoat, Step, TienDoChay,
} from '../types'
import { dungMach, idDay, type MachChay, type NhipChay, type TrangThaiVan }
  from './mach_chay'

/** MÀN CHẠY MÁY — vai thứ tư của vỏ trò chơi, và là màn hình BÁN CẢ SẢN PHẨM.
 *
 *  Hôm qua bấm Backtest xong chỉ có một thanh tiến độ và mấy con số. Nay cái máy CHẠY
 *  trước mắt: dòng điện đi trong dây, van mở van đóng ở từng cổng Hỏi, lệnh nổ một
 *  cái, tiền giật, đường vốn mọc dần ở mép dưới — tua nhanh được, dừng lại soi được.
 *  Xem `tai_lieu/thiet_ke_tro_choi.md` §5.
 *
 *  ⚠ MÀN HÌNH THẬT, KHÔNG PHẢI HỘP THOẠI ĐÈ LÊN XƯỞNG. Luật cứng ở đầu `TroChoi.tsx`:
 *  ĐÚNG MỘT màn hình sống tại một lúc, vì `TitleBar` mang `useKhungCuaSo` nghe chuột ở
 *  mức `document` — hai cái cùng sống là hai bộ cùng bảo Windows "bắt đầu kéo". Nên
 *  bấm Chạy là RỜI Xưởng: `SoDo` bị tháo (ngăn Hoàn tác mất theo, sơ đồ thì không —
 *  nó ghi bản nháp trước khi đi), và màn này lắp vào.
 *
 *  ⚠ VÀ VÌ THẾ, RỜI MÀN NÀY GIỮA LÚC LEAN ĐANG CHẠY LÀ DỪNG HẲN LƯỢT. Không giấu
 *  chuyện ấy: chỗ duy nhất nhận kết quả là màn này, nên để lượt chạy tiếp sau khi màn
 *  bị tháo là để một tiến trình LEAN cày máy mà kết quả không rơi vào đâu cả.
 *
 *  Bộ máy ĐỌC KẾT QUẢ nằm ở `mach_chay.ts`, không ở đây: tệp này chỉ vẽ.
 */

/** Việc chuyển từ Xưởng sang: sơ đồ, hồ sơ cỗ máy, và LƯỢT SOÁT vừa xong.
 *
 *  Lượt soát đi kèm chứ không soát lại ở đây, mà cũng không lấy bản cũ Xưởng đang
 *  giữ: số khối (`thu_tu`) là thứ duy nhất nối nhãn trên lệnh của LEAN về đúng khối
 *  trên sơ đồ, nên nó phải là bản soát của ĐÚNG sơ đồ sắp sinh mã. */
export interface ViecChayMay {
  ten: string
  steps: Step[]
  edges: Edge[]
  coMay: CoMay
  soat: KetQuaSoat
  /** Mã màn đang chơi. Rỗng = chế độ Sáng tạo, không ép sân và không chấm.
   *
   *  ⚠ Chỉ GỬI mã màn, không gửi mã/ngày của màn: Python tự ép sân lên sơ đồ
   *  (`luat_choi.ap_man`). Để giao diện gửi khoảng ngày lên là mở đúng cái cửa mà cả
   *  trò chơi dựa vào để đóng — ai sửa gói tin là chơi màn ẩn lúc nào cũng được. */
  man?: string
}

/** Một nhịp dài bao nhiêu ở ×1 (ms). 380ms ≈ hai nhịp rưỡi mỗi giây: đủ chậm để
 *  thấy van đóng mở và lệnh nổ, đủ nhanh để 30 giây đầu có chuyện xảy ra. */
const NHIP_MS = 380

/** Ba nấc tua. ×64 là nấc «xem cho hết»: backtest 6 năm theo ngày ≈ 1.500 nhịp, tức
 *  khoảng 9 giây. Thiết kế §5.6 khai đúng ba nấc này. */
const CAC_TOC = [1, 8, 64]

/* ------------------------------- nền của một nhịp ------------------------------- */

/** NHỊP ĐANG CHIẾU, truyền xuống khối và dây bằng context chứ không bằng `data` của
 *  node, và đây là chuyện tốc độ chứ không phải gọn mã.
 *
 *  Nhồi vào `data` thì mỗi nhịp phải dựng lại CẢ MẢNG node và mảng edge rồi đẩy sang
 *  React Flow — ở ×64 là chừng 60 lượt mỗi giây, mỗi lượt một mảng mới, và React Flow
 *  đo lại khung mọi khối theo. Context thì chỉ mấy thành phần thật sự đọc nó vẽ lại,
 *  còn mảng node/edge dựng MỘT LẦN rồi đứng im. */
interface NenMach {
  nhip: NhipChay | null
  /** `nhip.day` dạng Set — mỗi sợi dây tự hỏi "có tôi không", mà `Array.includes`
   *  trên mỗi sợi mỗi nhịp là phép nhân hai con số đều lớn dần theo sơ đồ. */
  daySet: Set<string>
  chiSo: number
  /** LEAN còn đang chạy, chưa có cuộn phim nào: cả máy chạy không tải, mọi dây sáng. */
  khongTai: boolean
}

const Ctx = createContext<NenMach>({
  nhip: null, daySet: new Set(), chiSo: -1, khongTai: false,
})

/* ---------------------------------- cái VAN ---------------------------------- */

/** VAN của một cổng Hỏi — thứ làm nên cả màn hình này.
 *
 *  Hai cánh trượt vào nhau là đóng, trượt ra là mở. Tiếng *cạch* nằm trong chính phép
 *  chuyển: `cubic-bezier` nhún quá đà một nhịp, nên nó chỉ đánh ĐÚNG LÚC ĐỔI trạng
 *  thái — không phải mỗi nhịp. Đóng suốt 95% số nến mà nhịp nào cũng đánh *cạch* thì
 *  cả màn hình thành một cái đèn nháy.
 *
 *  BA trạng thái, không phải hai, và cái thứ ba không phải để cho đẹp: xem lời dặn
 *  «VAN ĐÓNG: SUY RA ĐƯỢC TỚI ĐÂU» ở đầu `mach_chay.ts`. Chữ ở đây nói về DÒNG, không
 *  nói về điều kiện — câu "điều kiện sai" là câu app không chứng minh được. */
const CHU_VAN: Record<TrangThaiVan, string> = {
  mo: 'Dòng qua — nhịp này có lệnh ra từ dưới cổng',
  dong: 'Dòng dừng ở đây — dưới cổng không lệnh nào ra',
  lang: 'Chưa rõ — dòng dừng ở khúc này, mà đúng cổng nào thì không suy ra được',
}

function Van({ tt }: { tt: TrangThaiVan }) {
  return (
    // ⚠ LỚP VIẾT NGUYÊN CHUỖI, không ghép `'van van-' + tt`. Hàng rào lớp CSS ma dò
    // chữ trong nguyên văn tệp, nên bản ghép chỉ cho nó thấy một lớp tên «van-» —
    // vừa báo oan một lớp không có thật, vừa bỏ lọt ba lớp có thật.
    <span className={tt === 'mo' ? 'van van-mo'
                     : tt === 'dong' ? 'van van-dong' : 'van van-lang'}
          title={tr(CHU_VAN[tt])}>
      {/* ⚠ HAI CÁNH KHÔNG BAO GIỜ RA KHỎI THÂN VAN, và đó là lý do nó vẽ được mà không
          cần `clipPath`. Mỗi cánh cao 10 trong cái thân cao 28: khép lại thì chúng gặp
          nhau ở giữa (đóng), mở ra thì lùi sát hai mép thân và CHỪA MỘT KHE Ở GIỮA —
          đúng hình một cái van cửa thật, và cái khe chính là chỗ dòng điện chui qua.
          `clipPath` thì phải có id riêng cho từng khối, mà id trùng nhau trong một
          trang SVG là cả màn hình cắt theo một cái khuôn. */}
      <svg viewBox="0 0 48 34" aria-hidden>
        <path className="van-ong" d="M0 17 H48" />
        <rect className="van-than" x="12" y="3" width="24" height="28" rx="4" />
        <rect className="van-canh tren" x="12" y="7" width="24" height="10" />
        <rect className="van-canh duoi" x="12" y="17" width="24" height="10" />
      </svg>
    </span>
  )
}

/* --------------------------------- một KHỐI --------------------------------- */

/** MỘT MÔ-ĐUN của cỗ máy.
 *
 *  ⚠ CHỮ TRÊN MẶT KHỐI LẤY NGUYÊN `Card` CỦA PYTHON, y như `StepNode` của Xưởng —
 *  cùng một `card.title`, `card.lines`, `card.badges`, cùng `thu_tu`. Không có chỗ
 *  nào trong đây tự ghép lại một dòng chữ nào: ghép ở đây là bản sự thật thứ hai, và
 *  hôm nào mặt khối ở Xưởng nói khác mặt khối lúc chạy thì không ai biết bên nào đúng.
 *  Lớp CSS cũng dùng chung (`.hop`, `.dau`, `.than`, `.so-thu-tu`) nên nhìn vào là
 *  nhận ra ngay cái khối mình vừa vẽ.
 */
function KhoiChayTrong({ id, data }: NodeProps) {
  // `memo` chặn lượt vẽ lại mà gốc cửa sổ phát ra khi đổi tiếng — nên khối tự nghe.
  useNgonNgu()
  const { nhip, chiSo, khongTai } = useContext(Ctx)
  const card = (data as { card: Card }).card
  const thuTu = (data as { thuTu?: string }).thuTu
  const van = nhip?.van[id]
  const no = !!nhip?.no.includes(id)
  const tuChoi = !!nhip?.tuChoi.includes(id)

  /** Nhịp gần nhất khối này nổ. Giữ lại chứ không đọc `no` trực tiếp, vì cú NẢY và
   *  hạt sáng phải chạy cho TRỌN hoạt ảnh của chúng: ở ×64 một nhịp chỉ 6ms, mà đổi
   *  lớp CSS ngay nhịp sau là hoạt ảnh bị cắt ngang và chẳng thấy gì. */
  const [lanNo, setLanNo] = useState(-1)
  useEffect(() => { if (no) setLanNo(chiSo) }, [no, chiSo])

  return (
    // ⚠ `key` ĐỔI MỖI LẦN NỔ là cách duy nhất cho hoạt ảnh CSS chạy LẠI từ đầu: cùng
    // một phần tử thì trình duyệt coi hoạt ảnh ấy đã chạy rồi và không khởi động lại.
    // Khoá chỉ đổi lúc NỔ, nên khối đứng im thì không có lượt tháo-lắp nào.
    <div className={'chay-boc' + (lanNo >= 0 ? ' da-no' : '')} key={lanNo}>
      {/* Bốn cổng ở giữa bốn cạnh, cùng khuôn với `StepNode`: dây của sơ đồ bám vào
          đúng cạnh nó đã bám ở Xưởng. Không bắt chuột — màn này không nối dây. */}
      {([['top', Position.Top], ['right', Position.Right],
         ['bottom', Position.Bottom], ['left', Position.Left]] as const).map(([k, p]) => (
        <Handle key={k} type="source" id={k} position={p}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}
      {([['top', Position.Top], ['right', Position.Right],
         ['bottom', Position.Bottom], ['left', Position.Left]] as const).map(([k, p]) => (
        <Handle key={'t-' + k} type="target" id={k} position={p}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}

      <div className={'hop chay-hop'
                      + (thuTu ? '' : ' khong-toi')
                      + (khongTai ? ' chay-khong-tai' : '')
                      + (no ? ' chay-no' : '')
                      + (tuChoi ? ' chay-tu-choi' : '')
                      + (van === 'mo' ? ' chay-mo'
                         : van === 'dong' ? ' chay-dong'
                         : van === 'lang' ? ' chay-lang' : '')}>
        <div className={'so-thu-tu' + (thuTu ? '' : ' trong')}>{thuTu || '–'}</div>
        <div className="dau">
          <span className="ten" title={card.title}>{card.title}</span>
        </div>
        {card.lines.length > 0 && (
          <div className="than">
            {card.lines.map((d, i) => (
              <div key={i} className="dong" title={d.text}>
                <span className="danh">{card.kind === 'group' ? '·' : ''}</span>
                <Icon name={d.icon ?? ''} size={12} />
                <span>{d.text}</span>
              </div>
            ))}
          </div>
        )}
        {card.badges.length > 0 && (
          <div className="chan">
            {card.badges.map((b, i) => <span key={i} className="the">{b}</span>)}
          </div>
        )}
        {card.la_cong && <Van tt={van ?? 'lang'} />}
      </div>

      {/* HẠT SÁNG bắn ra khi lệnh nổ. Nằm ngoài `.hop` để bay được khỏi mép hộp. */}
      {lanNo >= 0 && <i className="chay-hat" aria-hidden />}
    </div>
  )
}

const KhoiChay = memo(KhoiChayTrong)

/* ---------------------------------- một DÂY ---------------------------------- */

/** DÂY DẪN, và dòng điện trong nó.
 *
 *  ⚠ HAI ĐƯỜNG CHỒNG NHAU, không phải một. Một đường không thể vừa là sợi dây vừa là
 *  vệt sáng chạy trên nó: muốn vệt sáng thì phải đặt `stroke-dasharray`, mà đặt lên
 *  chính sợi dây thì gần hết sợi dây thành KHOẢNG TRỐNG — mấy cái khối rời nhau với
 *  mẩu dây cụt 8 pixel, không ra cái máy nào cả. Đã dính thật ở màn Mở máy, nhìn ảnh
 *  chụp mới thấy. Nay: một đường NỀN liền nét lúc nào cũng có, một đường SÁNG đứt nét
 *  chạy đè lên — và `stroke-dashoffset` chạy trên GPU, không tốn khung hình JS nào.
 */
function DayDien({ id, sourceX, sourceY, targetX, targetY, sourcePosition,
                   targetPosition, markerEnd }: EdgeProps) {
  const { daySet, khongTai } = useContext(Ctx)
  const [d] = getBezierPath({ sourceX, sourceY, sourcePosition,
                              targetX, targetY, targetPosition })
  const co = khongTai || daySet.has(id)
  return (
    <>
      <BaseEdge id={id} path={d} markerEnd={markerEnd} className="day-nen" />
      {co && <path className="day-dong" d={d} />}
    </>
  )
}

const nodeTypes = { chay: KhoiChay }
const edgeTypes = { dien: DayDien }

/** Cách vừa khung. `maxZoom` 1.1: sơ đồ hai khối trên màn 1600 mà phóng hết cỡ thì chữ
 *  to như biển hiệu và cái máy mất hẳn dáng máy. Khai MỘT LẦN ở đây vì có HAI chỗ gọi
 *  — lúc dựng và lúc đổi cỡ cửa sổ — mà hai bộ số khác nhau thì kéo cửa sổ một cái là
 *  sơ đồ tự nhảy sang một mức phóng khác. */
const VUA_KHUNG = { padding: 0.22, maxZoom: 1.1 }

/* -------------------------------- ĐƯỜNG VỐN -------------------------------- */

/** ĐƯỜNG VỐN mọc dần ở mép dưới, theo thời gian thật của lượt chạy (§5.5).
 *
 *  Vẽ cả đường bằng màu mờ rồi tô SÁNG phần đã chạy qua: thấy trước mình đang đi tới
 *  đâu trong cả lượt. Giấu phần chưa tới thì mất hẳn cảm giác dài ngắn, mà cũng không
 *  giấu được gì — đường vốn là của lượt đã chạy xong rồi.
 *
 *  Trục X theo CHỈ SỐ NHỊP chứ không theo giờ: nhịp của LEAN đã bị `_thua` gộp lại
 *  nên khoảng cách giữa chúng không đều, mà vẽ theo giờ thì mấy đoạn gộp co lại thành
 *  một vạch và con trỏ nhảy giật. Theo chỉ số thì mỗi nhịp một bước đều nhau — đúng
 *  với thứ người xem đang đếm. */
function DuongVon({ mach, i }: { mach: MachChay; i: number }) {
  const { cao, nen, sang } = useMemo(() => {
    const n = mach.nhip.length
    const lo = mach.vonMin
    const hi = mach.vonMax
    const dai = hi - lo || 1
    const y = (v: number) => 30 - ((v - lo) / dai) * 28
    const diem = mach.nhip.map((p, j) => `${(j / Math.max(n - 1, 1)) * 100},${y(p.von)}`)
    return {
      cao: y(mach.vonDau),
      nen: diem.join(' '),
      sang: diem.slice(0, i + 1).join(' '),
    }
  }, [mach, i])

  const x = (i / Math.max(mach.nhip.length - 1, 1)) * 100
  return (
    <svg className="cm-von-ve" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden>
      {/* Mốc VỐN BAN ĐẦU — không có nó thì đường vốn chỉ là một nét lượn, không ai
          biết lượt này đang lãi hay đang lỗ. */}
      <line className="cm-von-moc" x1="0" y1={cao} x2="100" y2={cao} />
      <polyline className="cm-von-nen" points={nen} />
      <polyline className="cm-von-sang" points={sang} />
      <line className="cm-von-kim" x1={x} y1="0" x2={x} y2="32" />
    </svg>
  )
}

/* ------------------------------------ màn ------------------------------------ */

/** ⚠ `vi-VN` CHỨ KHÔNG PHẢI `en-US`, và đây là chuyện khớp nhau chứ không phải gu.
 *  Cả app đã định dạng số bằng `vi-VN` (`BangBieuDo`, `HopKetQua`, `HopToiUu`). Đồng
 *  hồ ở đây viết `100,000` còn bảng Kết quả viết `100.000` thì cùng một con số hiện ra
 *  hai kiểu, và người đọc phải tự đoán bên nào là hàng nghìn. Một quy ước, một chỗ. */
const soTien = (v: number) =>
  v.toLocaleString('vi-VN', { maximumFractionDigits: 0 })

/** Giây UNIX -> `2020-03-12`. Giờ UTC, đúng như LEAN ghi, và không theo máy người
 *  dùng: cùng một lượt chạy xem ở hai múi giờ phải ra cùng một ngày. */
const ngayCua = (t: number) =>
  t > 0 ? new Date(t * 1000).toISOString().slice(0, 10) : '—'

function ManChayMayTrong({ viec, onRa, onCham }: {
  viec: ViecChayMay
  onRa: () => void
  /** Chạy xong một lượt của MÀN thì mời đi chấm. Thiếu = đang ở Sáng tạo. */
  onCham?: (maLuot: string) => void
}) {
  const nn = useNgonNgu()
  const { fitView } = useReactFlow()
  const [tienDo, setTienDo] = useState<TienDoChay | null>(null)
  const [kq, setKq] = useState<KetQuaChay | null>(null)
  const [loi, setLoi] = useState('')
  const [mach, setMach] = useState<MachChay | null>(null)
  const [i, setI] = useState(0)
  const [dangPhat, setDangPhat] = useState(true)
  const [toc, setToc] = useState(1)
  /** LEAN còn đang chạy — cần một ref vì hàm dọn của hiệu ứng khởi động đọc nó. */
  const conChay = useRef(false)

  /** DỪNG HẲN lượt LEAN. Chỉ bảo Python giết tiến trình rồi THÔI: vòng hỏi tiến độ
   *  sẽ thấy `xong` ở lượt kế và dọn đúng một lần — dọn cả hai nơi thì nửa giây sau
   *  cái còn lại vẫn bắn. */
  const dung = () => { conChay.current = false; void py.dung_backtest() }

  /** KÊU THEO NHỊP — và CHỈ Ở ×1.
   *
   *  ⚠ Ở ×64 một giây trôi qua mấy chục nhịp; kêu đủ là một tràng tạch tạch không ai
   *  chịu nổi, mà lúc tua thì người ta đang TÌM chỗ chứ không XEM. Nên tiếng chỉ có ở
   *  nấc ×1 — đúng nấc đặt ra để ngồi nhìn cái máy chạy.
   *
   *  Van đóng chỉ kêu khi nó VỪA đóng (nhịp trước còn mở): van đóng suốt mười nhịp mà
   *  kêu mười tiếng thì tiếng ấy hết nghĩa. */
  const vanTruoc = useRef<Record<string, string>>({})
  useEffect(() => {
    const n = mach?.nhip[i]
    if (!n) return
    if (toc !== 1 || !dangPhat) { vanTruoc.current = n.van as never; return }
    if (n.lenh.length) keu.lenh()
    for (const [id, v] of Object.entries(n.van)) {
      const cu = vanTruoc.current[id]
      if (v === cu) continue
      if (v === 'mo') keu.van_mo()
      else if (v === 'dong') keu.van_dong()
    }
    vanTruoc.current = n.van as never
  }, [mach, i, toc, dangPhat])

  /* --------------------------------- chạy LEAN --------------------------------- */
  useEffect(() => {
    let song = true
    let nhip = 0
    void (async () => {
      const r = await py.chay_backtest(viec.ten || 'Co May', viec.steps, viec.edges,
                                       viec.coMay, viec.man || undefined, 'thay')
      if (!song) return
      if (!r.ok || !r.value) { setLoi(r.error ?? tr('không chạy được')); return }
      if (!r.value.ok) { setLoi(r.value.loi); return }
      conChay.current = true
      setTienDo({ dang_chay: true, xong: false, giay: 0, giai_doan: '',
                  dong_cuoi: '', so_dong: 0, da_dung: false })

      // Backtest chạy ở LUỒNG RIÊNG bên Python, nên ở đây chỉ HỎI mỗi nửa giây — chặn
      // thật thì cửa sổ đứng im không vẽ gì, và người dùng tưởng app treo.
      nhip = window.setInterval(() => void (async () => {
        const t = await py.tien_do_backtest()
        if (!song || !t.ok || !t.value) return
        setTienDo(t.value)
        if (!t.value.xong) return
        window.clearInterval(nhip)
        conChay.current = false
        // ⚠ DỪNG KHÔNG PHẢI LỖI. Bấm Dừng thì Python trả `ok: false` kèm câu «Bạn đã
        // dừng lượt chạy này» — đúng với lõi, nhưng ném vào chỗ báo lỗi thì người
        // dùng vừa cố ý dừng xong lại bị mắng.
        if (t.value.da_dung) { setLoi(tr('Bạn đã dừng lượt chạy này.')); return }
        const k = t.value.ket_qua
        if (!k) { setLoi(tr('chạy xong mà không có kết quả')); return }
        if (!k.ok) { setLoi(k.loi); return }
        setKq(k)
        setMach(dungMach(viec.soat, k, viec.steps))
        setI(0)
        setDangPhat(true)
      })(), 500)
    })()
    return () => {
      song = false
      window.clearInterval(nhip)
      // RỜI MÀN GIỮA LÚC ĐANG CHẠY LÀ DỪNG HẲN — xem lời dặn đầu tệp.
      if (conChay.current) { conChay.current = false; void py.dung_backtest() }
    }
    // Chạy ĐÚNG MỘT LẦN cho mỗi lượt vào màn: `viec` là việc của lượt này, đổi tiếng
    // hay tua nhanh không được phép bắt LEAN chạy lại.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* --------------------------------- chiếu phim --------------------------------- */
  useEffect(() => {
    if (!mach || !dangPhat) return
    const het = mach.nhip.length - 1
    let xin = 0
    let truoc = performance.now()
    let du = 0
    const buoc = (nay: number) => {
      du += (nay - truoc) * toc
      truoc = nay
      // Nhảy NHIỀU nhịp mỗi khung hình ở nấc tua cao, chứ không rút ngắn khoảng chờ:
      // ×64 là 6ms một nhịp, dưới hẳn một khung hình, nên `setInterval` không theo nổi
      // và nấc ×64 sẽ chạy đúng bằng ×16 mà không ai biết.
      const them = Math.floor(du / NHIP_MS)
      if (them > 0) {
        du -= them * NHIP_MS
        setI(x => Math.min(het, x + them))
      }
      xin = requestAnimationFrame(buoc)
    }
    xin = requestAnimationFrame(buoc)
    return () => cancelAnimationFrame(xin)
  }, [mach, dangPhat, toc])

  // Tới cuối thì DỪNG, không quay lại đầu: hết phim là hết, và người xem còn muốn
  // soi cái nhịp cuối cùng.
  useEffect(() => {
    if (mach && i >= mach.nhip.length - 1) setDangPhat(false)
  }, [mach, i])

  /* ---- «Xong thì mở luôn bảng kết quả» (Cài đặt) ----
     Mở lúc HẾT PHIM, không mở lúc LEAN xong: cửa sổ kết quả là một cửa sổ Windows
     riêng, nhảy lên trước ngay giây đầu của cuộn phim thì nó che đúng cái màn hình
     vừa dựng ra để xem. Đúng một lần cho mỗi lượt. */
  const daMo = useRef(false)
  useEffect(() => {
    if (!kq?.id || !mach || daMo.current || i < mach.nhip.length - 1) return
    daMo.current = true
    void (async () => {
      const cd = await py.cai_dat_doc()
      if (cd.ok && cd.value?.mo_ket_qua === false) return
      await py.mo_cua_so_ket_qua(kq.id!)
    })()
  }, [kq, mach, i])

  /* ---- ĐỔI CỠ CỬA SỔ thì VỪA KHUNG LẠI ----
     `fitView` của React Flow chỉ chạy lúc dựng. Phóng to cửa sổ giữa lượt chiếu thì sơ
     đồ giữ nguyên khung cũ và NỬA CÁI MÁY nằm ngoài màn hình — mà màn này cố ý không
     có thanh zoom nào để bấm về, nên người xem mắc kẹt. Chỉ ảnh chụp mới thấy: đo bằng
     JavaScript thì mọi khối vẫn "có mặt", chỉ là ở ngoài khung nhìn.

     Hoãn 140ms: kéo mép cửa sổ bắn ra hàng chục sự kiện một giây, mà mỗi lần vừa khung
     là một lượt tính lại cả sơ đồ. */
  useEffect(() => {
    let hen = 0
    const doiCo = () => {
      window.clearTimeout(hen)
      hen = window.setTimeout(() => { void fitView(VUA_KHUNG) }, 140)
    }
    window.addEventListener('resize', doiCo)
    return () => { window.clearTimeout(hen); window.removeEventListener('resize', doiCo) }
  }, [fitView])

  /* ---- PHÍM của màn này ----
     F6 dừng hẳn lượt LEAN, đúng phím Xưởng dùng để dừng — một phím, một nghĩa, ở mọi
     màn hình. Cách dấu và hai mũi tên là phím của bộ chiếu, chỉ có nghĩa ở đây. */
  useEffect(() => {
    const het = (mach?.nhip.length ?? 1) - 1
    const nghe = (ev: KeyboardEvent) => {
      if (ev.key === 'F6') { ev.preventDefault(); dung(); return }
      if (!mach) return
      if (ev.key === ' ') { ev.preventDefault(); setDangPhat(p => !p) }
      else if (ev.key === 'ArrowLeft') {
        ev.preventDefault(); setDangPhat(false); setI(x => Math.max(0, x - 1))
      } else if (ev.key === 'ArrowRight') {
        ev.preventDefault(); setDangPhat(false); setI(x => Math.min(het, x + 1))
      } else if (ev.key === 'End') { ev.preventDefault(); setI(het) }
    }
    window.addEventListener('keydown', nghe)
    return () => window.removeEventListener('keydown', nghe)
  }, [mach])

  /* ------------------------------ sơ đồ: dựng MỘT LẦN ------------------------------ */
  const { nodes, rfEdges } = useMemo(() => {
    const the = viec.soat.the ?? {}
    const ns: RfNode[] = viec.steps.map((s, k) => ({
      id: s.id,
      type: 'chay',
      position: { x: s.pos?.[0] ?? 80 + k * 330, y: s.pos?.[1] ?? 120 },
      data: { card: the[s.id], thuTu: viec.soat.thu_tu?.[s.id] },
      draggable: false,
      selectable: false,
    })).filter(n => (n.data as { card?: Card }).card)
    // ĐƯỜNG ↻ KHÔNG VẼ ở màn này. Nó là đường quay lại, mà bộ sinh mã còn chưa sinh
    // nổi khối Quay về — vẽ một sợi dây không bao giờ có dòng là vẽ một thứ nói dối.
    const es: RfEdge[] = (viec.soat.edges ?? []).filter(e => !('so_vong' in e)).map(e => ({
      id: idDay(e),
      source: e.from,
      target: e.to,
      sourceHandle: e.from_side ?? 'right',
      targetHandle: e.to_side ?? 'left',
      type: 'dien',
    }))
    return { nodes: ns, rfEdges: es }
  }, [viec])

  const nhip = mach?.nhip[i] ?? null
  const nen = useMemo<NenMach>(() => ({
    nhip,
    daySet: new Set(nhip?.day ?? []),
    chiSo: i,
    khongTai: !mach && !loi,
  }), [nhip, i, mach, loi])

  const von = nhip?.von ?? mach?.vonDau ?? 0
  const lai = von - (mach?.vonDau ?? 0)
  const coLenh = !!nhip?.lenh.length

  return (
    <div className="cm" key={nn}>
      <TitleBar tieuDe={viec.ten || tr('Chạy máy')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={mach || loi ? tr('Về Xưởng')
                                   : tr('Về Xưởng — và DỪNG lượt chạy đang dở')}>←</button>
      } />

      <div className="cm-than">
        <Ctx.Provider value={nen}>
          <ReactFlow nodes={nodes} edges={rfEdges}
                     nodeTypes={nodeTypes} edgeTypes={edgeTypes}
                     nodesDraggable={false} nodesConnectable={false}
                     elementsSelectable={false} edgesFocusable={false}
                     proOptions={{ hideAttribution: true }}
                     minZoom={0.1} maxZoom={1.6}
                     fitView fitViewOptions={VUA_KHUNG}>
            <Background variant={BackgroundVariant.Dots} gap={22} size={1}
                        color="var(--canvas-dot)" />
          </ReactFlow>
        </Ctx.Provider>

        {/* ĐỒNG HỒ TIỀN — đầu ra của cái máy. Góc trên phải, nổi trên sơ đồ: thiết kế
            §5.1 cấm bảng và ribbon, nên mọi con số phải nổi chứ không có dải riêng. */}
        {mach && (
          <div className="cm-dongho">
            <div className={'cm-tien' + (coLenh ? ' giat' : '')} key={coLenh ? i : 'im'}>
              ${soTien(von)}
            </div>
            <div className={'cm-lai ' + (lai >= 0 ? 'len' : 'xuong')}>
              {lai >= 0 ? '▲' : '▼'} ${soTien(Math.abs(lai))}
              {mach.vonDau ? ` · ${(lai / mach.vonDau * 100).toFixed(1)}%` : ''}
            </div>
            <div className="cm-ngay">{ngayCua(nhip?.t ?? 0)}</div>
          </div>
        )}

        {/* LEAN CÒN ĐANG CHẠY — máy chạy không tải, và nói ba thứ CÓ THẬT: đang ở giai
            đoạn nào, chạy bao lâu, dòng LEAN vừa in. Không bịa phần trăm: LEAN không
            in tiến độ ra màn hình (xem `HopTienDo`). */}
        {!mach && !loi && (
          <div className="cm-cho">
            <b>{tienDo?.giai_doan ? tr(tienDo.giai_doan) : tr('Đang nạp cỗ máy…')}</b>
            <span className="cm-cho-giay">{(tienDo?.giay ?? 0).toFixed(1)}s</span>
            <div className="cm-cho-dong">{tienDo?.dong_cuoi || '…'}</div>
            <button className="nut nut-dung" onClick={dung}>
              {trx('{0} Dừng', <Icon name="dung" />)}</button>
          </div>
        )}

        {loi && (
          <div className="cm-loi">
            <b>⚠ {tr('Lượt chạy dừng lại')}</b>
            <div className="cm-loi-cau">{loi}</div>
            <button className="nut" onClick={onRa}>{tr('Về Xưởng')}</button>
          </div>
        )}
      </div>

      {mach && (
        <>
          <div className="cm-von">
            {mach.coVon
              ? <DuongVon mach={mach} i={i} />
              : <div className="cm-von-khong">
                  {tr('LEAN không trả về đường vốn cho lượt này — mép dưới để trống, '
                      + 'chứ không vẽ một đường bịa.')}
                </div>}
          </div>

          <ThanhDieu mach={mach} i={i} dangPhat={dangPhat} toc={toc}
                     onPhat={() => setDangPhat(p => !p)}
                     onToc={setToc} onToi={setI}
                     onKetQua={kq?.id ? () => void py.mo_cua_so_ket_qua(kq.id!) : undefined}
                     onCham={viec.man && kq?.id && onCham
                       ? () => onCham(kq.id!) : undefined} />
        </>
      )}
    </div>
  )
}

/* ------------------------------ thanh điều khiển ------------------------------ */

/** Tua nhanh, nhảy tới cuối, và DỪNG LẠI SOI MỘT NHỊP (§5.6 · §5.7).
 *
 *  Hai nút ◀ ▶ chỉ hiện lúc đã dừng, và đó là cả câu trả lời cho "dừng lại được ở
 *  một nến để soi": dừng rồi thì đi từng nhịp một, xem van nào đổi, lệnh nào ra.
 */
function ThanhDieu({ mach, i, dangPhat, toc, onPhat, onToc, onToi, onKetQua,
                    onCham }: {
  mach: MachChay
  i: number
  dangPhat: boolean
  toc: number
  onPhat: () => void
  onToc: (t: number) => void
  onToi: (i: number) => void
  onKetQua?: () => void
  /** Có màn để chấm thì hiện nút; Sáng tạo thì không. */
  onCham?: () => void
}) {
  const het = mach.nhip.length - 1
  const nhip = mach.nhip[i]
  return (
    <div className="cm-dieu">
      <button className="cm-nut chinh" onClick={onPhat}
              title={dangPhat ? tr('Dừng lại soi') : tr('Chạy tiếp')}>
        <Icon name={dangPhat ? 'dung' : 'chay'} />
      </button>

      {/* ◀ ▶ CHỈ HIỆN LÚC ĐÃ DỪNG: đang chạy mà bấm từng nhịp thì nhịp sau của bộ
          chiếu đè lên ngay, và nút trông như hỏng. */}
      {!dangPhat && (
        <>
          <button className="cm-nut" onClick={() => onToi(Math.max(0, i - 1))}
                  disabled={i <= 0} title={tr('Nhịp trước')}>◀</button>
          <button className="cm-nut" onClick={() => onToi(Math.min(het, i + 1))}
                  disabled={i >= het} title={tr('Nhịp sau')}>▶</button>
        </>
      )}

      <div className="cm-toc">
        {CAC_TOC.map(t => (
          <button key={t} className={'cm-nut' + (toc === t ? ' dang' : '')}
                  onClick={() => onToc(t)}>×{t}</button>
        ))}
        <button className="cm-nut" onClick={() => onToi(het)} disabled={i >= het}
                title={tr('Nhảy tới cuối')}><Icon name="cuoi" /></button>
      </div>

      <input className="cm-keo" type="range" min={0} max={het} value={i}
             onChange={e => onToi(Number(e.target.value))}
             title={tr('Kéo tới một nhịp bất kỳ')} />

      <span className="cm-dem">{i + 1}/{het + 1}</span>

      {/* CHÚ GIẢI BA TRẠNG THÁI VAN. Không phải lời xin lỗi dán thêm: nó nói đúng cái
          màn hình này biết và cái nó không biết. Xem `mach_chay.ts`. */}
      <div className="cm-chu">
        <span className="cm-chu-muc mo">{tr('dòng qua')}</span>
        <span className="cm-chu-muc dong">{tr('dòng dừng')}</span>
        <span className="cm-chu-muc lang">{tr('chưa rõ')}</span>
      </div>

      {!!nhip?.lenh.length && (
        <span className="cm-lenh-nay">
          {trx('{0} lệnh', nhip.lenh.length)}
          {nhip.lenh.map(l => (
            <b key={String(l.id)} className={l.hop_le ? '' : 'tu-choi'}>
              {l.ma} {l.so_luong}
            </b>
          ))}
        </span>
      )}

      {/* LỆNH LẠC — nhãn không khớp khối nào trên sơ đồ, tức sơ đồ đã sửa sau lượt
          chạy. Nói ra chứ không nuốt: cuộn phim này đang kể chuyện một sơ đồ khác. */}
      {mach.soLenhLac > 0 && (
        <span className="cm-lac" title={tr('Sơ đồ đã sửa sau lượt chạy này — chạy lại '
                                           + 'để xem đúng đường nó đã đi.')}>
          {trx('⚠ {0} lệnh không khớp khối nào', mach.soLenhLac)}
        </span>
      )}

      <span className="day" />
      {onKetQua && (
        <button className="cm-nut rong" onClick={onKetQua}>{tr('Bảng kết quả…')}</button>
      )}
      {/* CHẤM ĐIỂM chỉ hiện khi đang chơi một MÀN và lượt đã chạy xong. Ở Sáng tạo
          không có gì để chấm, mà bày một nút chết là mời người ta bấm hụt. */}
      {onCham && (
        <button className="cm-nut chinh" onClick={onCham}>{tr('Chấm điểm')}</button>
      )}
    </div>
  )
}

/** `useReactFlow` chỉ chạy được bên trong Provider — nên màn thật nằm ở trong. */
export default function ManChayMay(
  p: { viec: ViecChayMay; onRa: () => void; onCham?: (maLuot: string) => void },
) {
  return <ReactFlowProvider><ManChayMayTrong {...p} /></ReactFlowProvider>
}
