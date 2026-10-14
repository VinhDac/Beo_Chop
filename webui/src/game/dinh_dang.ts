/** Định dạng số và ngày cho các màn hình game. Một chỗ, để "+1.31 %" ở bản đồ và ở
 *  màn hình kết quả không bao giờ viết hai kiểu. */

export const pt = (x: number | null | undefined, so = 2) =>
  x == null ? '—' : `${x > 0 ? '+' : ''}${x.toFixed(so)} %`

/** Giây UTC → `2021-03-04 10:00` (giờ của nến — QC chạy theo UTC). */
export const gio = (t: number | null | undefined) => {
  if (!t) return '—'
  const d = new Date(t * 1000)
  const s = (n: number) => String(n).padStart(2, '0')
  return `${d.getUTCFullYear()}-${s(d.getUTCMonth() + 1)}-${s(d.getUTCDate())} `
       + `${s(d.getUTCHours())}:${s(d.getUTCMinutes())}`
}

/** `2021-10-01` → `01/10/2021`. */
export const ngay = (s: string | null | undefined) => {
  if (!s) return '—'
  const [y, m, d] = s.split('-')
  return `${d}/${m}/${y}`
}

/** Năm của một khoảng `[từ, đến]` — màn chương 1 luôn trọn một năm. */
export const nam = (k: [string, string] | null | undefined) => (k ? k[0].slice(0, 4) : '—')

export const tien = (x: number | null | undefined) =>
  x == null ? '—' : `${Math.round(x).toLocaleString('en-US')} $`
