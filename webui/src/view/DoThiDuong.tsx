/* MỘT KHUNG RIÊNG cho một đại lượng không cùng thang với giá.
 *
 * RSI chạy 0–100, MACD chạy quanh 0, vàng chạy quanh 1250. Nhét chung một trục thì
 * một trong hai thành đường thẳng dính mép — nên mỗi cái một khung, mỗi khung một
 * thang của riêng nó.
 *
 * ⚠ THANG ĐO DO TỪ ĐIỂN QUYẾT, không phải chỗ này. `sinh_ma` đọc `hoi.DON_VI_GIA`
 * rồi in đại lượng cùng thang giá vào thẳng bảng `Price` (vẽ chồng lên nến), còn lại
 * vào bảng `Quantities` — tức việc «vẽ ở đâu» đã xong trước khi dữ liệu tới đây.
 *
 * ⚠ KHOẢNG TRỐNG LÀ KHOẢNG TRỐNG. Chỉ báo chưa chín thì LEAN không in nhịp ấy, và ở
 * đây nó là `null`. Nối thẳng qua chỗ trống là vẽ một đoạn chưa từng có; cắt đường ra
 * làm mấy khúc mới đúng.
 */
import { memo, useMemo } from 'react'

const L = 8, R = 72, T = 8, B = 6

export interface DoThiDuongProps {
  ten: string
  gt: (number | null)[]
  chiSo: number
  cua: number
  rong: number
}

function DoThiDuong({ ten, gt, chiSo, cua, rong }: DoThiDuongProps) {
  const H = 76
  const d = useMemo(() => {
    const het = Math.min(gt.length, chiSo + 1)
    const dau = Math.max(0, het - cua)
    const lat = gt.slice(dau, het)
    let thap = Infinity, cao = -Infinity
    for (const v of lat) {
      if (v === null) continue
      if (v < thap) thap = v
      if (v > cao) cao = v
    }
    if (!Number.isFinite(thap)) { thap = 0; cao = 1 }
    if (cao - thap < 1e-9) { cao = thap + 1 }
    return { lat, thap, cao }
  }, [gt, chiSo, cua])

  const W = Math.max(240, rong)
  const buoc = (W - L - R) / Math.max(1, d.lat.length)
  const px = (i: number) => L + (i + 0.5) * buoc
  const py = (v: number) => T + (d.cao - v) / (d.cao - d.thap) * (H - T - B)

  // Cắt thành nhiều khúc ở mỗi chỗ trống — xem chú thích đầu tệp.
  const khuc: string[] = []
  let cur = ''
  d.lat.forEach((v, i) => {
    if (v === null) { if (cur) { khuc.push(cur); cur = '' } return }
    cur += `${cur ? 'L' : 'M'}${px(i).toFixed(1)} ${py(v).toFixed(1)} `
  })
  if (cur) khuc.push(cur)

  const cuoi = [...d.lat].reverse().find(v => v !== null)

  return (
    <div className="view-khung-duong">
      <svg className="view-do-thi" viewBox={`0 0 ${W} ${H}`} width={W} height={H}>
        <line x1={L} y1={py(d.cao)} x2={W - R} y2={py(d.cao)} className="view-luoi" />
        <line x1={L} y1={py(d.thap)} x2={W - R} y2={py(d.thap)} className="view-luoi" />
        <text x={W - R + 6} y={py(d.cao) + 4} className="view-nhan-truc">
          {d.cao.toFixed(2)}
        </text>
        <text x={W - R + 6} y={py(d.thap) + 4} className="view-nhan-truc">
          {d.thap.toFixed(2)}
        </text>
        {khuc.map((k, i) => <path key={i} d={k.trim()} className="view-duong" />)}
      </svg>
      <span className="view-ten-duong">
        {ten}
        {cuoi !== undefined && cuoi !== null && (
          <b>{cuoi.toFixed(3)}</b>
        )}
      </span>
    </div>
  )
}

export default memo(DoThiDuong)
