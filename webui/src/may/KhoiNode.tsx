import { Handle, Position, type NodeProps } from '@xyflow/react'
import Icon from '../components/Icon'
import type { SoiKhoiMay, TheKhoi } from './mayTypes'

/** Một khối của cỗ máy 5 trạm trên canvas.  (D-10, phần 5)
 *
 *  Cùng khuôn hộp với sơ đồ cũ (`StepNode`) — cùng class, cùng luật 4 cổng, cùng huy
 *  hiệu số — nhưng đọc THẺ của cỗ máy: ở đây chỉ có ba loại khối (Bắt đầu · Hỏi · Làm)
 *  và mỗi khối Làm mang một VAI.
 */

/** Số dòng hiện tối đa trên một hộp. Một cổng 6 điều kiện vẽ hết thì hộp cao gấp đôi
 *  và sơ đồ hết đọc được; cắt rồi ghi rõ còn bao nhiêu, nhấp đúp xem đủ. */
const TOI_DA_DONG = 6

/** Khoá màu ngữ nghĩa (do `may.the_khoi` suy) → biến CSS. Ba loại khối, ba màu:
 *  · Bắt đầu — xám `--action`: nó là ĐIỂM NEO, không phải hành động.
 *  · Hỏi — lam `--khoi-hoi`: một CÂU HỎI, y như cổng của sơ đồ cũ.
 *  · Làm — tím `--khoi-lam`: thứ DUY NHẤT đổi kết quả của trạm. */
const MAU: Record<string, string> = {
  start: 'var(--action)',
  hoi: 'var(--khoi-hoi)',
  lam: 'var(--khoi-lam)',
}

const ICON: Record<string, string> = { start: 'start', hoi: 'branch', lam: 'action' }

const SIDES: [string, Position][] = [
  ['top', Position.Top],
  ['right', Position.Right],
  ['bottom', Position.Bottom],
  ['left', Position.Left],
]

export default function KhoiNode({ data, selected }: NodeProps) {
  const card = (data as { card: TheKhoi }).card
  const so = (data as { so?: string | null }).so ?? null
  /* SOI một lượt đã chạy: khối này có nằm trên đường đi không, và nếu là cổng thì trượt
     ở điều kiện nào. `moSoi` = đang soi nhưng khối này không dính gì. */
  const soi = (data as { soiKhoi?: SoiKhoiMay }).soiKhoi
  const moSoi = (data as { moSoi?: boolean }).moSoi
  const hien = card.lines.slice(0, TOI_DA_DONG)
  const con = card.lines.length - hien.length
  const laStart = card.kind === 'start'
  const mau = card.mau || (laStart ? 'start' : 'hoi')
  /* Khối PHỤ đi kèm một quyết định, nó không tự chốt gì — nói ra trên hộp, vì nhìn hai
     hộp cạnh nhau thì không có gì phân biệt "đưa về 0" (quyết định) với "cấm vào lại"
     (phụ), mà đặt một mình thì khối phụ chẳng có tác dụng nào. */
  const laPhu = card.vai === 'phu'

  return (
    <>
      {/* 4 cổng ở giữa 4 cạnh, mỗi cạnh có CẢ source LẪN target — xem `StepNode`: chỉ
          đặt source thì React Flow không phân giải nổi đầu đích của dây đã có. */}
      {SIDES.map(([id, pos]) => (
        <Handle key={id} type="source" id={id} position={pos} />
      ))}
      {!laStart && SIDES.map(([id, pos]) => (
        <Handle key={'t-' + id} type="target" id={id} position={pos}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}

      <div className={'hop'
        + (selected ? ' dang-chon' : '')
        + (so ? '' : ' khong-toi')
        + (laStart ? ' la-start' : '')
        + (card.ghim ? ' da-ghim' : '')
        + (card.la_cong ? ' la-cong' : '')
        + (laPhu ? ' khoi-phu' : '')
        + (soi?.truot ? ' soi-truot' : soi?.daChay ? ' soi-chay' : '')
        + (moSoi ? ' soi-mo' : '')}>

        {/* Số thứ tự của CHÍNH trạm này, do Python tính bằng phép duyệt của bộ máy.
            Không có số = không đường nối nào dẫn tới, khối sẽ KHÔNG chạy. */}
        <div className={'so-thu-tu' + (so ? '' : ' trong') + (card.ghim ? ' ghim' : '')}
             title={so
               ? (card.ghim
                 ? `Bước ${so} — SỐ ĐÃ GHIM: mọi đường nối quay về đây vẫn giữ số này`
                 : `Bước ${so} — số = đi được bao xa, chữ = đi nhánh nào`)
               : 'Không có đường nối dẫn tới — sẽ không chạy'}>
          {so ?? '–'}
          {card.ghim && <span className="dau-ghim" aria-hidden>⟲</span>}
        </div>

        <div className={'dau mau-' + mau}
             style={{ '--mau-khoi': MAU[mau] ?? MAU.hoi } as React.CSSProperties}>
          <span className="dai-mau" />
          <Icon name={ICON[mau] ?? 'action'} size={13} />
          <span className="ten" title={card.title}>{card.title}</span>
        </div>

        {hien.length > 0 && (
          /* Trên hộp để dòng ngắn, tooltip là câu đầy đủ. Khối Bắt đầu CŨNG có thân:
             lịch chạy và khung nến là dòng do Python sinh, không phải chữ gõ tay trong
             tên khối — nên đổi lịch là hộp đổi theo. */
          <div className="than" title={card.mo_ta}>
            {hien.map((d, i) => (
              <div key={i} className={'dong'
                   + (soi?.dieuKien.length ? (soi.dieuKien[i] ? ' dk-dat' : ' dk-truot') : '')}>
                {/* "và" CHỈ đúng ở khối Hỏi: mỗi dòng một điều kiện, nối nhau bằng VÀ.
                    Ở khối Làm mỗi dòng là một Ô, dán "và" vào là nói sai. */}
                <span className="danh">{card.la_cong && i > 0 ? 'và' : ''}</span>
                <span>{d.text}</span>
              </div>
            ))}
            {con > 0 && (
              <div className="dong con-nua">
                <span className="danh" /><span>… còn {con} dòng nữa</span>
              </div>
            )}
          </div>
        )}

        {(laPhu || card.ghim) && (
          <div className="chan">
            {laPhu && (
              <span className="the"
                    title="Đi kèm một khối quyết định — tự nó không chốt gì cho mã đang xét">
                khối phụ
              </span>
            )}
            {card.ghim && <span className="the the-ghim">⟲ đã ghim số</span>}
          </div>
        )}
      </div>
    </>
  )
}
