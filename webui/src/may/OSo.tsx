import { useState } from 'react'
import { chotSo, locSo } from '../so'
import type { ThamSo } from '../types'

/** Ô SỐ của cỗ máy — con số, hoặc TÊN một tham số.  (D-10, phần 5)
 *
 *  Luật xuyên suốt app: chỗ nào nhận số thì cũng nhận tên tham số, vì một ngưỡng dùng ở
 *  hai khối mà gõ tay hai lần thì sửa một chỗ là hai vế lệch nhau ÂM THẦM.
 *
 *  ⚠ BẢN NHÁP khi đang gõ — ép về số ngay từng phím là NUỐT dấu chấm: `"1."` ra `1`,
 *  state không đổi, React ghi đè ô về `"1"`, phím kế cho `"15"`. Dán `1.5` một phát thì
 *  lọt, nên bài kiểm phải gõ từng phím: `webui/kiem/o_so.mjs`.
 */
export default function OSo({ v, dat, thamSo, nguyen, title, lop }: {
  v: number | string | undefined
  dat: (x: number | string) => void
  thamSo: ThamSo[]
  nguyen?: boolean
  title?: string
  lop?: string
}) {
  const [nhap, datNhap] = useState<string | null>(null)
  const laTen = typeof v === 'string' && v !== ''
  const ts = laTen ? thamSo.find(t => t.ten === v) : undefined
  const hop = thamSo.filter(t => t.ten !== v)

  if (laTen) {
    return (
      <span className={'chip-ts' + (ts ? '' : ' mat') + (lop ? ' ' + lop : '')}
            title={ts
              ? `Tham số "${v}" = ${ts.gia_tri}${ts.don_vi ? ` (${ts.don_vi})` : ''}`
              : `Không còn tham số nào tên "${v}" trong bảng — bấm ✕ để gõ lại một số.`}>
        <span className="chip-ten">{v}</span>
        <button className="chip-x" title="Bỏ tên, quay lại gõ số"
                onClick={() => dat(ts ? Number(ts.gia_tri) : 0)}>✕</button>
      </span>
    )
  }
  return (
    <span className={'cum-so' + (lop ? ' ' + lop : '')}>
      <input className="o so nho" inputMode="decimal" spellCheck={false}
             value={nhap ?? (v ?? '')} title={title}
             onChange={e => {
               const { chu, so } = locSo(e.target.value, nguyen)
               datNhap(chu)
               if (so !== null) dat(so)
             }}
             onBlur={() => {
               // Rời ô thì bản nháp hết nhiệm vụ; còn dở dang thì chốt về con số gần
               // nhất đọc được, chứ không để ô trống mang nghĩa mơ hồ.
               if (nhap !== null && locSo(nhap, nguyen).so === null) dat(chotSo(nhap))
               datNhap(null)
             }} />
      {/* Chỉ hiện khi cỗ máy CÓ tham số — không có thì ô sạch như cũ. */}
      {hop.length > 0 && (
        <select className="chon-ts" value=""
                title="Dùng một tham số đã có thay cho con số này"
                onChange={e => e.target.value && dat(e.target.value)}>
          <option value="">▾</option>
          {hop.map(t => (
            <option key={t.ten} value={t.ten}>
              {t.ten} = {t.gia_tri}{t.don_vi ? ` ${t.don_vi}` : ''}
            </option>
          ))}
        </select>
      )}
    </span>
  )
}
