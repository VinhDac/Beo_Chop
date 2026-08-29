import { useState } from 'react'
import { py } from '../api'
import type { CaiDatKhop } from '../types'

/** MÔ HÌNH KHỚP — bốn con số quyết định backtest thật hay ảo tưởng.
 *
 *  ⚠ TAB NÀY LÀ MẶT KIA CỦA TAB "NGUỒN DỮ LIỆU". Ở đó luật là *"đo được thì đừng
 *  hỏi"* — độ trễ, spread, lệch đồng hồ đều app tự đo, hỏi là mời gõ sai rồi tin nó.
 *  Ở đây luật ngược lại và cũng bắt buộc y như vậy: **không đo được thì đừng giấu.**
 *
 *  Ba trong bốn ô dưới đây là thứ dữ liệu L1 KHÔNG BAO GIỜ trả lời được. Chôn chúng
 *  thành hằng số trong `khop_lenh.py` thì chúng vẫn quyết định toàn bộ bảng lãi lỗ —
 *  chỉ khác là không ai biết chúng tồn tại để mà nghi ngờ.
 *
 *  Vì thế mỗi ô đi kèm một câu nói rõ **vặn sai về phía nào thì mất tiền**, chứ không
 *  chỉ là một cái nhãn. Một con số không có ngữ cảnh thì không chỉnh được.
 */

/** Một ô số + câu giải thích. `ĐO ĐƯỢC` / `PHẢI ĐOÁN` là nhãn quan trọng nhất trên
 *  màn hình này — nó nói cho người dùng biết con số nào đáng tin. */
function O({ nhan, don_vi, gt, dat, doan, the, mo_ta, buoc, min, max }: {
  nhan: string; don_vi: string; gt: number; dat: (v: number) => void
  doan?: boolean; the?: string; mo_ta: React.ReactNode
  buoc?: number; min?: number; max?: number
}) {
  return (
    <div className="k-o">
      <div className="hang">
        <span className="nhan-o k-nhan">{nhan}</span>
        <input className="o o-so" type="number" value={gt}
               step={buoc ?? 0.1} min={min} max={max}
               onChange={e => {
                 const v = Number(e.target.value)
                 if (Number.isFinite(v)) dat(v)
               }} />
        <span className="chu-mo">{don_vi}</span>
        {/* BA nhãn, không hai. Bản trước chỉ có "đoán / tra được", nên một núm
            CHỈ đỡ phần dữ liệu không với tới cũng bị đóng dấu là phỏng đoán y như
            một núm không có gì đo được — hai chuyện khác hẳn nhau. */}
        <span className={'k-the' + (doan ? ' doan' : '')}>
          {the || (doan ? 'A GUESS' : 'LOOK IT UP')}
        </span>
      </div>
      <div className="k-mo-ta">{mo_ta}</div>
    </div>
  )
}

export default function KhopPanel({ khop, dat }: {
  khop: CaiDatKhop
  dat: (k: keyof CaiDatKhop, v: number) => void
}) {
  const [dangTra, setDangTra] = useState(false)

  async function veMacDinh() {
    setDangTra(true)
    const r = await py.khop_mac_dinh()
    setDangTra(false)
    if (r.ok && r.value) {
      const k = (r.value as Record<string, any>).khop as CaiDatKhop
      for (const t of Object.keys(k) as (keyof CaiDatKhop)[]) dat(t, k[t])
    }
  }

  return (
    <div className="khop-panel">
      <div className="chu-dan">
        The question the fill model has to answer is <b>“where does our order sit in
        the queue?”</b> — and top-of-book data <b>does not contain the answer</b>. The
        four fields below are everything the app has to guess. They are printed
        alongside every backtest result.
      </div>

      <O nhan="Maker fee" don_vi="bps" gt={khop.phi_maker_bps} buoc={0.1}
         dat={v => dat('phi_maker_bps', v)}
         mo_ta={<>
           2.0 bps = 0.02%, the standard schedule on Binance · Bybit · OKX. <b>A
           NEGATIVE number is a rebate</b> — the exchange pays you, and that is often
           the only thing that makes market making profitable; it comes from a Market
           Maker programme, not from an ordinary VIP tier. Compare against the real
           spread with <code>tools/do_spread.py</code>: the spread must beat <b>twice</b>
           this number.
         </>} />

      <O nhan="Outbound latency" don_vi="ms" gt={khop.tre_ra_ms} buoc={0.5} min={0} doan
         dat={v => dat('tre_ra_ms', v)}
         mo_ta={<>
           From the moment the strategy decides to the moment the order <b>rests at
           the exchange</b>. It cannot be measured until you have sent real orders.
           Everything that happens in that window is an opportunity out of reach —
           setting it too low grants yourself reflexes you do not have.
         </>} />

      <O nhan="Cancels AHEAD of us" don_vi="ratio 0–1" gt={khop.phan_huy_truoc}
         buoc={0.1} min={0} max={1} doan
         dat={v => dat('phan_huy_truoc', v)}
         mo_ta={<>
           <b>The dial that matters most.</b> When size vanishes from our price level
           with no trade to explain it, someone cancelled — were they ahead of us or
           behind us?
           <br />
           <b>0</b> pessimistic: every cancel is behind us, our position never
           improves on its own · <b>0.5</b> evenly spread · <b>1</b> optimistic: we
           advance to the front of the queue quickly.
           <br />
           Run all three and look at the gap — <b>that gap is exactly what the
           backtest does not know</b>. Turning it optimistic means paying the tuition
           with real money.
         </>} />

      <O nhan="Deep level ahead of us" don_vi="ratio 0–1" gt={khop.phan_muc_sau}
         buoc={0.1} min={0} max={1} doan the="FALLBACK ONLY"
         dat={v => dat('phan_muc_sau', v)}
         mo_ta={<>
           Resting <b>deeper than the touch</b>, how much of that level sits ahead of
           us? A strategy quoting half a spread away from fair value lands here
           constantly.
           <br />
           <b>This is now measured, not guessed</b> — the depth stream sees 20 levels
           per side, and the whole level is ahead of you because you just arrived. The
           dial only covers what depth cannot answer: deeper than 20 levels, or days
           recorded before the depth stream was switched on. Every result says how much
           of it had to fall back.
           <br />
           So the way to retire this dial is not to tune it — it is to{' '}
           <b>record depth</b>.
         </>} />

      <div className="hang">
        <button className="nut" onClick={veMacDinh} disabled={dangTra}>
          Reset to defaults (pessimistic)
        </button>
        <span className="chu-mo">
          Turn a dial to try something, forget to turn it back, and every result
          after that is rosier than the truth.
        </span>
      </div>
    </div>
  )
}
