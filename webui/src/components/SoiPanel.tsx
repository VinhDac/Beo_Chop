import type { KetQuaSoi } from '../types'

/** SOI MỘT LƯỢT — thẻ nổi trên canvas: sơ đồ NHÌN THẤY gì, và nó ra báo giá nào.
 *
 *  Sơ đồ bên dưới đã sáng lên đúng đường đã đi (`StepNode`), nhưng hai đầu của lượt
 *  chạy thì không nằm trên khối nào: **đầu vào** (sổ lệnh + tồn kho lúc đó) và **đầu
 *  ra** (báo giá đã làm tròn về tick). Thẻ này chở đúng hai thứ đó.
 *
 *  ⚠ HIỆN GIÁ ĐÃ LÀM TRÒN, không hiện con số trong đầu sơ đồ. Hai cái lệch nhau tới
 *  nửa tick, và chỗ lệch ấy đúng là chỗ đáng nhìn: sơ đồ tính ra `9,4985` mà lệnh gửi
 *  đi là `9,498`. Muốn xem số thô thì mở khối ra — nó nằm trong dòng của từng số hạng.
 *
 *  Nằm ở góc trên-PHẢI: góc trên-trái đã có pill sơ đồ, và mắt đọc sơ đồ từ trái sang
 *  nên góc phải là chỗ ít che nhất.
 */

const so = (v: number | null | undefined, le?: number) => {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  const a = Math.abs(v)
  const n = le ?? (a >= 100 ? 2 : a >= 1 ? 3 : a >= 0.01 ? 5 : 7)
  return v.toLocaleString('en-US', { maximumFractionDigits: n }).replace('-', '−')
}

/** `1 lot` / `2 lots` — số nhiều đúng. Nghe vụn vặt, nhưng thẻ này chỉ có mấy dòng và
 *  một chữ sai ngữ pháp trên đó thì mắt vấp ngay. */
const dv = (v: number, ten: string) => `${so(v, v % 1 ? 2 : 0)} ${ten}${v === 1 ? '' : 's'}`

export default function SoiPanel({ soi, luc, onDong }: {
  soi: KetQuaSoi
  /** Mốc thời gian đang soi, đã định dạng. */
  luc: string
  onDong: () => void
}) {
  const n = soi.nhin
  const q = soi.bao_gia
  return (
    <div className="soi-the">
      <div className="soi-dau-the">
        <span className="soi-tieu-de">Inspect one turn</span>
        <span className="soi-luc">{luc}</span>
        <button className="soi-dong" onClick={onDong} title="Stop inspecting (Esc)">✕</button>
      </div>

      {!n.co_so && (
        <div className="soi-mu">ORDER BOOK LOST — every price is missing, so every
          arithmetic gate fails</div>
      )}

      {/* ---- ĐẦU VÀO ---- */}
      <div className="soi-muc">What the diagram saw</div>
      <div className="soi-luoi">
        <span>bid</span><b>{so(n.bid)}</b>
        <span className="soi-kl">{so(n.bid_kl, 0)}</span>
        <span>ask</span><b>{so(n.ask)}</b>
        <span className="soi-kl">{so(n.ask_kl, 0)}</span>
        <span>mid</span><b>{so(n.mid)}</b><span />
        <span>spread</span><b>{so(n.spread)}</b>
        <span className="soi-kl">
          {n.spread !== null && soi.tick ? dv(Math.round(n.spread / soi.tick), 'tick') : ''}
        </span>
        <span>inventory</span>
        <b className={n.ton_kho ? 'soi-nong' : ''}>{so(n.ton_kho, 2)}</b><span />
      </div>

      {/* ---- ĐẦU RA ---- */}
      <div className="soi-muc">Quote sent out</div>
      <div className="soi-luoi soi-bao-gia">
        <span>BUY</span>
        <b>{q.mua_lot > 0 ? so(q.mua_gia) : '—'}</b>
        <span className="soi-kl">{q.mua_lot > 0 ? dv(q.mua_lot, 'lot') : 'not resting'}</span>
        <span>SELL</span>
        <b>{q.ban_lot > 0 ? so(q.ban_gia) : '—'}</b>
        <span className="soi-kl">{q.ban_lot > 0 ? dv(q.ban_lot, 'lot') : 'not resting'}</span>
      </div>

      {q.mua_lot <= 0 && q.ban_lot <= 0 && (
        <div className="soi-rut">This turn rests NOTHING at all</div>
      )}
    </div>
  )
}
