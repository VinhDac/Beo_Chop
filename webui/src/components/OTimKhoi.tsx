import { useState } from 'react'
import IconNet from './Icon'
import { boDau } from '../tim'

/** Một lọc nhanh — hỏi theo DÂY thay vì theo chữ (xem `SoDo.dsLoc`). */
export interface LocTim { ma: string; ten: string; goiY: string; so: number }
/** Một khối khớp, bày trong danh sách xổ. `hn` = tên hạt nhân chứa nó. */
export interface KhoiGoiY { id: string; nhan: string; ten: string; hn?: string }

/** Ô TÌM KHỐI.
 *
 *  Gõ là tô: khối có chữ khớp sáng viền, đoạn chữ khớp tô nền vàng. Enter kéo màn tới
 *  khối khớp kế tiếp và chọn nó; Esc xoá. Chỉ để NHÌN lúc sửa sơ đồ: không đổi gì của
 *  sơ đồ, không lưu gì.
 *
 *  DANH SÁCH XỔ khi bấm vào ô (hay ↓):
 *    · LỌC NHANH — khối chia nhánh, gộp nhánh, khối cuối, khối không chạy tới. Chọn một
 *      cái là tô cả loạt, rồi Enter đi lần lượt y như tìm chữ. Lọc đang bật nằm thành
 *      một thẻ trong ô; Backspace hay Esc là bỏ.
 *    · KHỐI KHỚP — số · tên, bấm là tới (khối trong hạt nhân thì tự vào hạt nhân ấy).
 *  ↑↓ đi trong danh sách, Enter lấy dòng đang sáng; không dòng nào sáng thì Enter vẫn
 *  là tới khối khớp kế tiếp.
 *
 *  Vì sao phải có: một sơ đồ nghìn khối thì tìm bằng mắt là không nổi, và câu hỏi hay
 *  gặp nhất lại không phải "khối tên gì" mà "chỗ nào rẽ", "chỗ nào không ai tới".
 *
 *  Chép từ Jenifer_Studio.
 */
export default function OTimKhoi({ giaTri, onDoi, soKhop, dangO, onToi, loc, dsLoc, onLoc,
                                   goiY, onChon }: {
  giaTri: string
  onDoi: (v: string) => void
  soKhop: number
  dangO: number            // đang đứng ở khối khớp thứ mấy (từ 0); -1 = chưa Enter lần nào
  onToi: () => void
  loc: string | null
  dsLoc: LocTim[]
  onLoc: (ma: string | null) => void
  goiY: KhoiGoiY[]
  onChon: (id: string) => void
}) {
  const [mo, setMo] = useState(false)
  const [sang, setSang] = useState(-1)

  const dangLoc = dsLoc.find(l => l.ma === loc)
  const coChu = giaTri.trim() !== ''
  const q = boDau(giaTri.trim())
  const muc: ({ l: LocTim } | { k: KhoiGoiY })[] = [
    ...(dangLoc ? [] : dsLoc.filter(l => !q || boDau(l.ten).includes(q)).map(l => ({ l }))),
    ...(coChu || dangLoc ? goiY.map(k => ({ k })) : []),
  ]

  function lay(i: number) {
    const m = muc[i]
    if (!m) return
    if ('l' in m) onLoc(m.l.ma)
    else { onChon(m.k.id); setMo(false) }
    setSang(-1)
  }

  return (
    <div className="o-tim-khoi">
      <IconNet name="tim" size={13} />
      {dangLoc && (
        <span className="chip-loc" title={dangLoc.goiY}>
          {dangLoc.ten}
          <button onMouseDown={e => { e.preventDefault(); onLoc(null) }} title="Bỏ lọc">×</button>
        </span>
      )}
      <input value={giaTri} spellCheck={false}
             placeholder={dangLoc ? 'Enter: khối kế tiếp' : 'Tìm khối…'}
             onChange={e => { onDoi(e.target.value); setSang(-1); setMo(true) }}
             onFocus={() => setMo(true)}
             onBlur={() => { setMo(false); setSang(-1) }}
             onKeyDown={e => {
               if (e.key === 'ArrowDown') {
                 e.preventDefault()
                 setMo(true)
                 setSang(i => Math.min(i + 1, muc.length - 1))
               } else if (e.key === 'ArrowUp') {
                 e.preventDefault()
                 setSang(i => Math.max(i - 1, -1))
               } else if (e.key === 'Enter') {
                 e.preventDefault()
                 if (mo && sang >= 0) lay(sang)
                 else onToi()
               } else if (e.key === 'Escape') {
                 e.preventDefault()
                 onDoi('')
                 onLoc(null)
                 setSang(-1)
               } else if (e.key === 'Backspace' && !giaTri && dangLoc) {
                 onLoc(null)
               }
             }} />
      {(coChu || dangLoc) && (
        <span className="dem">
          {soKhop === 0 ? 'không thấy'
            : dangO >= 0 ? `${dangO + 1}/${soKhop}` : `${soKhop} khối`}
        </span>
      )}
      {mo && muc.length > 0 && (
        <div className="goi-y-khoi">
          {muc.map((m, i) => (
            // `onMouseDown` + preventDefault: bấm vào dòng không làm ô mất focus trước
            // khi kịp lấy — `onClick` thì ô đã blur, danh sách đã đóng mất rồi.
            <div key={'l' in m ? 'loc:' + m.l.ma : m.k.id}
                 className={'muc' + ('l' in m ? ' loc' : '') + (i === sang ? ' sang' : '')}
                 ref={i === sang ? el => el?.scrollIntoView({ block: 'nearest' }) : undefined}
                 onMouseDown={e => { e.preventDefault(); lay(i) }}>
              {'l' in m
                ? <><b>{m.l.ten}</b><span className="mo">{m.l.goiY}</span>
                    <span className="so">{m.l.so}</span></>
                : <><b>{m.k.nhan}</b> · {m.k.ten}
                    {m.k.hn && <span className="mo"> — trong {m.k.hn}</span>}</>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
