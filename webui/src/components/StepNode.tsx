import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { Card, StepKind } from '../types'
import IconNet, { ICON_HANH_DONG } from './Icon'

/** Số dòng hiện tối đa trên một hộp.
 *
 * Yêu cầu là "nhìn hộp phải hiểu khối này kiểm tra gì" — nhưng một cổng 6 điều kiện mà
 * vẽ hết thì hộp cao gấp đôi và sơ đồ hết đọc được. Cắt ở đây rồi ghi rõ còn bao nhiêu;
 * muốn xem hết thì double-click mở hộp thoại.
 */
const TOI_DA_DONG = 6

/** Khoá màu (do Python suy, xem `api._mau_khoi`) → biến CSS.
 *
 * Trước đây chỉ có hai màu: xanh cho Bắt đầu, **cam cho MỌI khối hành động** — nên nhìn
 * xa thì Kiểm tra ĐK, Vào lệnh, Sửa lệnh giống hệt nhau.
 *
 * Một cái lợi kèm theo: cam đang mang hai nghĩa cùng lúc — "khối hành động" và "đang
 * chọn / số thứ tự". Đẩy khối hành động sang màu riêng thì cam chỉ còn nghĩa *của ta ·
 * đang chọn*, và viền chọn nổi hẳn lên.
 *
 * Khoá lạ rơi về `hoi` chứ không mất màu: thêm một khoá bên Python mà quên bảng này
 * thì hộp vẫn vẽ ra, chỉ sai màu. */
const MAU: Record<string, string> = {
  start: 'var(--action)',
  hoi: 'var(--khoi-hoi)',
  gia: 'var(--khoi-gia)',
  lot: 'var(--khoi-lot)',
}

const SIDES: [string, Position][] = [
  ['top', Position.Top],
  ['right', Position.Right],
  ['bottom', Position.Bottom],
  ['left', Position.Left],
]

/** SOI MỘT LƯỢT — bốn trạng thái một khối có thể mang, và ký hiệu của từng cái.
 *
 *  Ký hiệu CHỨ KHÔNG CHỈ MÀU: bốn trạng thái mà phân biệt bằng bốn sắc độ thì mù màu
 *  đọc không ra, mà sơ đồ hai mươi khối thì cũng chẳng ai đối chiếu nổi bảng màu.
 *
 *  `bo-qua` là ca tinh nhất và cũng dễ hiểu nhầm nhất: khối CÓ chạy tới, nhưng ô `khi`
 *  của nó trượt nên số hạng không được cộng vào. Khác hẳn `bo` (nhánh bị lùi, số hạng
 *  đã cộng rồi bị hoàn nguyên) và khác hẳn "không chạy tới". */
const SOI_KY_HIEU: Record<string, string> = {
  qua: '✓', truot: '✗', bo: '↩', 'bo-qua': '⊘',
}
const SOI_GIAI_THICH: Record<string, string> = {
  qua: 'This turn ran through this block',
  truot: 'Gate FAILED — the condition did not match, so it backed out to try another branch',
  bo: 'This branch was tried then ABANDONED — its terms were rolled back',
  'bo-qua': 'It was reached, but the "when" field failed so the term was NOT applied',
}

export default function StepNode({ data, selected }: NodeProps) {
  const card = (data as { card: Card }).card
  const thuTu = (data as { thuTu?: string }).thuTu
  const soi = (data as { soi?: { trang: string; chu: string } | null }).soi
  const dangSoi = (data as { dangSoi?: boolean }).dangSoi
  const hien = card.lines.slice(0, TOI_DA_DONG)
  const con = card.lines.length - hien.length
  const laStart = card.kind === 'start'
  /* Icon lấy theo loại hành động của dòng ĐẦU — một khối chỉ mang một hành động, nên
     dòng nào cũng cùng loại. Khối Bắt đầu thì không có dòng nào. */
  const icon = laStart ? 'start' : (ICON_HANH_DONG[card.lines[0]?.type ?? ''] ?? 'action')
  const laVa = card.lines[0]?.type === 'check_cond'
  const mau = card.mau ?? (laStart ? 'start' : 'hoi')
  /* Ký hiệu ĐỌC ĐƯỢC CẢ KHI MÙ MÀU — cùng lý lẽ với cặp ▲▼ của bản cũ, chỉ đổi thứ nó
     phân biệt: `$` số hạng động vào giá, `≡` động vào khối lượng. */
  const mui = mau === 'gia' ? '$' : mau === 'lot' ? '≡' : ''

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
      {/* Khối Bắt đầu KHÔNG có cổng đích: nó là điểm neo, không bao giờ được chạy tới
          từ chỗ khác. Không cho thả dây vào là chặn lỗi ngay từ lúc kéo, thay vì để
          bảng Vấn đề báo sau. */}
      {!laStart && SIDES.map(([id, pos]) => (
        <Handle key={'t-' + id} type="target" id={id} position={pos}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}

      <div className={'hop'
        + (selected ? ' dang-chon' : '')
        + (thuTu ? '' : ' khong-toi')
        + (laStart ? ' la-start' : '')
        + (card.ghim ? ' da-ghim' : '')
        + (card.la_cong ? ' la-cong' : '')
        // Đang soi mà khối KHÔNG có trong nhật ký = lượt đó không chạy tới nó. Làm mờ
        // hẳn, vì "phần còn lại của sơ đồ" mới là thứ cần biến đi để đường đã đi nổi lên.
        + (dangSoi ? (soi ? ' soi soi-' + soi.trang : ' soi-ngoai') : '')
        }>

        {/* Số THỨ TỰ CHẠY THẬT, do Python tính bằng chính phép duyệt của bộ máy.
            Không có số = đường nối không dẫn tới khối này, nó sẽ KHÔNG chạy — phải
            nhìn thấy được ngay, không thì lại rơi vào cảnh sơ đồ nói dối. */}
        <div className={'so-thu-tu' + (thuTu ? '' : ' trong') + (card.ghim ? ' ghim' : '')}
             title={thuTu
               ? (card.ghim
                 ? `Step ${thuTu} — NUMBER PINNED: any edge looping back here keeps this exact number`
                 : `Step ${thuTu} — digits = how far along, letters = which branch`)
               : 'Nothing wires into this block — it will not run'}>
          {thuTu ?? '–'}
          {card.ghim && <span className="dau-ghim" aria-hidden>⟲</span>}
        </div>

        {/* `--mau-khoi` đặt trên chính dải tiêu đề: cả thanh trái lẫn nền nhuộm đều đọc
            từ nó, nên đổi một chỗ là đổi cả hai. */}
        <div className={'dau mau-' + mau} style={{ '--mau-khoi': MAU[mau] ?? MAU.hoi
                                                 } as React.CSSProperties}>
          <span className="dai-mau" />
          {mui ? <span className="mui-huong" aria-hidden>{mui}</span>
               : <IconNet name={icon} size={13} />}
          <span className="ten" title={card.title}>{card.title}</span>
          {soi && (
            <span className={'soi-dau soi-dau-' + soi.trang}
                  title={SOI_GIAI_THICH[soi.trang]} aria-hidden>
              {SOI_KY_HIEU[soi.trang]}
            </span>
          )}
        </div>

        {hien.length > 0 && (
          /* Tooltip là CÂU ĐẦY ĐỦ. Trên hộp chỉ để dòng ngắn — mỗi trường một dòng —
             vì nhìn hộp là để liếc ra ngay khối làm gì; rê chuột mới cần đủ chi tiết.

             ⚠ Điều kiện là "CÓ DÒNG NÀO KHÔNG", không phải "có phải khối Bắt đầu
             không" — và đó là cố ý. Khối Bắt đầu CŨNG từng có thân (nhịp chạy "Mỗi nến
             M5", một dòng do Python sinh từ khoá `nhip`, đã đi ở đợt 3). Nhịp sẽ quay
             lại dưới một dạng khác; viết theo "có dòng nào không" thì lúc đó không phải
             sửa gì ở đây. */
          <div className="than" title={card.mo_ta}>
            {hien.map((d, i) => (
              <div key={i} className="dong">
                {/* "và" CHỈ đúng với khối kiểm tra: ở đó mỗi dòng là một điều kiện nối
                    nhau bằng VÀ, phải ghi ra để không ai đoán là HOẶC. Ở khối vào/sửa
                    lệnh, mỗi dòng là một TRƯỜNG (lot, đệm, SL, TP) — dán "và" vào là
                    nói sai. */}
                <span className="danh">{laVa && i > 0 ? 'and' : ''}</span>
                <span>{d.text}</span>
              </div>
            ))}
            {con > 0 && (
              <div className="dong con-nua">
                <span className="danh" /><span>… {con} more line{con > 1 ? 's' : ''}</span>
              </div>
            )}
            {/* CON SỐ THẬT của lượt đang soi, ngay dưới câu mô tả của khối. Đây mới là
                thứ trả lời "vì sao": biết cổng trượt thì chưa đủ, phải thấy tồn kho lúc
                đó bằng bao nhiêu so với ngưỡng nào. */}
            {soi?.chu && (
              <div className={'dong soi-so soi-so-' + soi.trang}>
                <span className="danh" /><span>{soi.chu}</span>
              </div>
            )}
          </div>
        )}

        {card.badges.length > 0 && (
          <div className="chan">
            {card.badges.map((b, i) => <span key={i} className="the">{b}</span>)}
            {card.ghim && <span className="the the-ghim">⟲ pinned</span>}
          </div>
        )}
      </div>
    </>
  )
}
