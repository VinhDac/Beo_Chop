/** DÀN DÒNG: lời gọi tr()/trx() làm dòng quá dài -> cắt câu theo chữ, thụt lề theo dòng
 *  chứa lời gọi, xếp đối số xuống dòng. Chỉ đổi khoảng trắng và cách chia chuỗi cộng —
 *  câu (khoá dịch) giữ nguyên từng ký tự.
 */
import fs from 'node:fs'
import { chuoi, docTep, laGoiDich, tenTep, tinh, ts } from './chung.mjs'

const RONG = 100          // bề ngang nhắm tới
const QUA = RONG + 10     // dòng dài hơn thế mới dàn

/** Cắt câu: mảnh đầu không quá w0, các mảnh sau không quá w; cắt SAU dấu cách. */
function catCau(s, w0, w) {
  const ra = []
  let cur = ''
  for (const tu of s.split(/(?<= )/)) {
    if (cur && (cur + tu).length > (ra.length ? w : w0)) { ra.push(cur); cur = tu } else cur += tu
  }
  if (cur) ra.push(cur)
  return ra
}

/** Dàn một tệp. Trả { noi: ['tệp:dòng', …] }. */
export function dan(p, ghi) {
  const { nguon, eol, sf } = docTep(p)
  const dong = (pos) => sf.getLineAndCharacterOfPosition(pos)
  const chuDong = (l) => {
    const a = sf.getPositionOfLineAndCharacter(l, 0)
    const b = nguon.indexOf('\n', a)
    return nguon.slice(a, b < 0 ? nguon.length : b).replace(/\r$/, '')
  }
  const sua = [], noi = []
  const di = (n) => {
    if (laGoiDich(n, sf) && n.arguments.length) {
      const d0 = dong(n.getStart(sf)).line, d1 = dong(n.end).line
      let dai = false
      for (let l = d0; l <= d1; l++) if (chuDong(l).length > QUA) dai = true
      // Gọn rồi — hoặc là lời gọi ngắn nằm trên một dòng dài vì THỨ KHÁC (onClick viết liền).
      if (!dai || (d0 === d1 && n.getText(sf).length < 70)) return
      const k = n.arguments[0]
      const v = tinh(k)
      const le = /^[ \t]*/.exec(chuDong(d0))[0] + '  '
      const c0 = dong(k.getStart(sf)).character
      let ra, cot
      if (v === null) { ra = k.getText(sf); cot = c0 + ra.length }
      else {
        const manh = catCau(v, Math.max(24, RONG - c0 - 2), RONG - le.length - 4)
        ra = manh.map(chuoi).join(eol + le + '+ ')
        cot = (manh.length > 1 ? le.length + 2 : c0) + chuoi(manh[manh.length - 1]).length
      }
      for (const a of n.arguments.slice(1)) {
        const t = a.getText(sf)
        if (cot + 2 + t.length > RONG) { ra += ',' + eol + le + t; cot = le.length + t.length }
        else { ra += ', ' + t; cot += 2 + t.length }
      }
      const cu = sf.text.slice(k.getStart(sf), n.arguments[n.arguments.length - 1].end)
      if (ra !== cu) {
        sua.push([k.getStart(sf), n.arguments[n.arguments.length - 1].end, ra])
        noi.push(tenTep(p) + ':' + (d0 + 1))
      }
      return
    }
    ts.forEachChild(n, di)
  }
  di(sf)
  if (ghi && sua.length) {
    let moi = nguon
    for (const [a, b, t] of sua.sort((x, y) => y[0] - x[0])) moi = moi.slice(0, a) + t + moi.slice(b)
    fs.writeFileSync(p, moi, 'utf8')
  }
  return { noi }
}
