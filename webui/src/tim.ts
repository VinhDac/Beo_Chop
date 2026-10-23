/** TÌM KHỐI trên canvas — so chữ KHÔNG phân biệt hoa thường, KHÔNG dấu: gõ "lenh" ra
 *  "VÀO LỆNH". Ô tìm (`OTimKhoi`) và phần tô chữ trong khối (`StepNode`) đi qua đúng
 *  mấy hàm này, nên khối nào sáng viền thì trong nó có chữ được tô.
 *
 *  Chép từ Jenifer_Studio — cùng một bài toán: một sơ đồ nghìn khối thì tìm bằng mắt
 *  là không nổi.
 */
import type { Card } from './types'

/** Bỏ dấu + hạ chữ thường, TỪNG KÝ TỰ một — nên chuỗi ra DÀI ĐÚNG BẰNG chuỗi vào: vị
 *  trí khớp tìm trên bản bỏ dấu dùng thẳng để cắt bản gốc ra tô, khỏi dò lại. */
export function boDau(s: string): string {
  return s.normalize('NFC').split('').map(c => {
    const b = c.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
    return b === 'đ' ? 'd' : (b[0] ?? c)
  }).join('')
}

/** Khối có chữ khớp không: tên, các dòng trên khối, và số thứ tự (`4A.2`). */
export function khoiKhop(card: Card, thuTu: string | undefined, tim: string): boolean {
  const q = boDau(tim.trim())
  if (!q) return false
  return [card.title, ...card.lines.map(d => d.text), thuTu ?? '']
    .some(t => boDau(t).includes(q))
}

/** Cắt `text` thành từng đoạn để tô: đoạn khớp `tim` có `khop` = true. */
export function doanTim(text: string, tim: string): { chu: string; khop: boolean }[] {
  const goc = text.normalize('NFC')
  const q = boDau(tim.trim())
  if (!q) return [{ chu: goc, khop: false }]
  const t = boDau(goc)
  const ra: { chu: string; khop: boolean }[] = []
  let i = 0
  for (let j = t.indexOf(q); j >= 0; j = t.indexOf(q, j + q.length)) {
    if (j > i) ra.push({ chu: goc.slice(i, j), khop: false })
    ra.push({ chu: goc.slice(j, j + q.length), khop: true })
    i = j + q.length
  }
  if (i < goc.length) ra.push({ chu: goc.slice(i), khop: false })
  return ra
}
