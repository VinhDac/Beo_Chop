import { memo, type CSSProperties } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { Card, Step, StepKind } from '../types'
import IconNet from './Icon'
import { doanTim } from '../tim'

/** Số dòng hành động hiện tối đa trên một hộp.
 *
 * Yêu cầu là "nhìn hộp phải hiểu Nhóm này làm những gì" — nhưng một Nhóm 40 hành động
 * mà vẽ hết thì hộp cao bằng cả màn hình và sơ đồ hết đọc được. Cắt ở đây rồi ghi rõ
 * còn bao nhiêu; muốn xem hết thì double-click mở hộp thoại.
 *
 * Chép từ Jenifer_Studio.
 */
export const TOI_DA_DONG = 8

const MAU: Record<StepKind, string> = {
  start: 'var(--dim)',
  group: 'var(--group)',
  action: 'var(--action)',
}

const TEN_LOAI: Record<StepKind, string> = {
  start: 'Bắt đầu',
  group: 'Nhóm',
  action: 'Khối lẻ',
}

/** Icon vẽ bằng SVG, KHÔNG dùng emoji — emoji hiện thành ô vuông ở nhiều chỗ vì phụ
 *  thuộc font hệ thống. */
function IconLoaiKhoi({ kind, c }: { kind: StepKind; c: string }) {
  if (kind === 'group') {
    return (
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden>
        <rect x="2.2" y="3" width="11.6" height="10" rx="1.6" stroke={c} strokeWidth="1.5" />
        <path d="M5 6.2h6M5 8.6h6M5 11h3.5" stroke={c} strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    )
  }
  if (kind === 'start') {
    return (
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden>
        <circle cx="8" cy="8" r="5.2" stroke={c} strokeWidth="1.6" />
        <circle cx="8" cy="8" r="1.8" fill={c} />
      </svg>
    )
  }
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M9 1.8 3.4 9.2h3.4l-.8 5 5.6-7.4H8.2z" stroke={c} strokeWidth="1.4"
            strokeLinejoin="round" />
    </svg>
  )
}

/** Chữ có tô đoạn khớp ô tìm khối (`tim` rỗng = chữ trơn). */
function ChuTim({ text, tim }: { text: string; tim: string }) {
  if (!tim) return <>{text}</>
  return <>{doanTim(text, tim).map((d, i) =>
    d.khop ? <mark key={i} className="tim-chu">{d.chu}</mark> : d.chu)}</>
}

/** Một dòng trên thẻ, có TÔ SÁNG TÊN NÚM.
 *
 *  Ghim một con số rồi mà thẻ vẫn vẽ «RSI(chu_ky)» bằng đúng màu chữ thường thì nó
 *  trông y hệt «RSI(14)» — nhìn cả sơ đồ không biết mình đã ghim những gì.
 *
 *  Tên núm do PYTHON gửi sang (`DongThe.num`), giao diện không tự đoán chữ nào là
 *  tên: đoán thì tô nhầm một chữ trùng tên, hoặc bỏ sót một núm. Cắt theo tên trước,
 *  rồi mới chạy tô-sáng-tìm-kiếm trên mấy mẩu còn lại — hai bộ tô sáng lồng vào nhau
 *  thì sinh thẻ `<mark>` trong `<mark>`. */
function DongChu({ text, num, tim }: {
  text: string; num?: string[]; tim: string
}) {
  if (!num?.length) return <ChuTim text={text} tim={tim} />
  // Tên dài trước, để `chu_ky` không bị `chu` cắt mất (Python đã xếp sẵn thế).
  const re = new RegExp(`(${num.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|')})`, 'g')
  return <>{text.split(re).map((m, i) => (num.includes(m)
    ? <span key={i} className="num-ghim">{m}</span>
    : <ChuTim key={i} text={m} tim={tim} />))}</>
}

const SIDES: [string, Position][] = [
  ['top', Position.Top],
  ['right', Position.Right],
  ['bottom', Position.Bottom],
  ['left', Position.Left],
]

function StepNode({ data, selected }: NodeProps) {
  const card = (data as { card: Card }).card
  const thuTu = (data as { thuTu?: string }).thuTu
  /** Đang bấm vào một khối "Quay về" và khối này nằm TRONG vòng ấy — tô màu vòng.
   *  Nhìn thấy cái vòng, không phải tự dò theo dây. */
  const trongVong = !!(data as { trongVong?: boolean }).trongVong
  /** Chính khối "Quay về": nhãn khối nó trỏ về, để đọc sơ đồ khỏi phải mở hộp thoại. */
  const veNhan = (data as { veNhan?: string }).veNhan
  const buoc = (data as { step?: Step }).step
  /** Màu NGƯỜI DÙNG tự đặt (menu chuột phải), để phân loại bằng mắt trên sơ đồ dài.
   *  Bộ chạy KHÔNG đọc nó. */
  const mauTay = buoc?.mau
  /** Khối KHỚP ô tìm (chữ hay lọc nhanh) — sáng viền; và chữ để tô bên trong. */
  const timThay = !!(data as { timThay?: boolean }).timThay
  const tim = (data as { tim?: string }).tim ?? ''
  const hien = card.lines.slice(0, TOI_DA_DONG)
  const con = card.lines.length - hien.length
  const mau = mauTay ?? MAU[card.kind]
  const toDam = !!mauTay

  return (
    <>
      {/* 4 cổng ở giữa 4 cạnh — mỗi cạnh phải có CẢ source LẪN target.
          Chỉ đặt source thì kéo nối vẫn được (nhờ ConnectionMode.Loose) nhưng React
          Flow không phân giải nổi đầu ĐÍCH của một đường nối đã có, và vẽ ra mấy mẩu
          cụt bên cạnh hộp. Cái target trùng id, trùng vị trí, ẩn đi và không bắt
          chuột — nó chỉ cần TỒN TẠI để đường nối bám vào. */}
      {SIDES.map(([id, pos]) => (
        <Handle key={id} type="source" id={id} position={pos} />
      ))}
      {SIDES.map(([id, pos]) => (
        <Handle key={'t-' + id} type="target" id={id} position={pos}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}

      <div className={'hop' + (selected ? ' dang-chon' : '') + (thuTu ? '' : ' khong-toi')
                      + (toDam ? ' mau-item' : '') + (trongVong ? ' trong-vong' : '')
                      + (timThay ? ' tim-thay' : '')}
           style={toDam ? { '--mau': mau } as CSSProperties : undefined}>
        {/* Số THỨ TỰ CHẠY THẬT, do Python tính bằng chính phép duyệt của bộ máy.
            Không có số = đường nối không dẫn tới khối này, nó sẽ KHÔNG chạy —
            phải nhìn thấy được ngay, không thì lại rơi vào cảnh sơ đồ nói dối. */}
        <div className={'so-thu-tu' + (thuTu ? '' : ' trong')}
             title={thuTu ? `Bước ${thuTu} — số = đi được bao xa, chữ = đi nhánh nào`
                          : 'Không có đường nối dẫn tới — sẽ không chạy'}>
          {thuTu ? <ChuTim text={thuTu} tim={tim} /> : '–'}
        </div>
        <div className="dau">
          <span className="dai-mau" style={{ background: mau }} />
          <IconLoaiKhoi kind={card.kind} c={mau} />
          <span className="ten" title={card.title}><ChuTim text={card.title} tim={tim} /></span>
          {/* KHỐI QUAY VỀ: nhãn đích ngay trên đầu hộp — đọc sơ đồ là biết nó nhảy đi
              đâu, khỏi phải mở hộp thoại hay dò theo đường ↻. */}
          {veNhan && (
            <span className="ve-nhan" title={`Quay về khối ${veNhan}`}>↻ {veNhan}</span>
          )}
          <span className="loai">{TEN_LOAI[card.kind]}</span>
        </div>

        {(hien.length > 0 || card.kind === 'group') && (
          <div className="than">
            {hien.length === 0 && <div className="dong rong">chưa có hành động nào</div>}
            {hien.map((d, i) => (
              <div key={i} className="dong" title={d.text}>
                <span className="danh">{card.kind === 'group' ? '·' : ''}</span>
                <IconNet name={d.icon ?? ''} size={12} />
                <span><DongChu text={d.text} num={d.num} tim={tim} /></span>
              </div>
            ))}
            {con > 0 && (
              <div className="dong con-nua">
                <span className="danh" /><span>… còn {con} hành động</span>
              </div>
            )}
          </div>
        )}

        {card.badges.length > 0 && (
          <div className="chan">
            {card.badges.map((b, i) => <span key={i} className="the">{b}</span>)}
          </div>
        )}
      </div>
    </>
  )
}

/* BỌC `memo`, và đó là một nửa của phép làm mượt canvas.
 *
 * Không bọc thì mỗi lần React Flow vẽ lại lớp bọc khối là thẻ này dựng lại TOÀN BỘ —
 * mà kéo MỘT khối thì React Flow vẽ lại lớp bọc của MỌI khối, 60 lần mỗi giây. Sơ đồ
 * cỡ `trial chaos 30` có 1.170 khối, nên một cú kéo là 1.170 × 60 lần dựng thẻ/giây.
 *
 * `memo` một mình chưa đủ: nó so `data` bằng THAM CHIẾU, mà bên dựng node lại tạo
 * object `data` mới cho mọi khối mỗi khi `nodes` đổi. Hai chỗ phải đi cùng nhau.
 */
export default memo(StepNode)
