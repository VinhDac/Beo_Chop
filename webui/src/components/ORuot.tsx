import { useState, type ReactNode } from 'react'
import { locSo, chotSo } from '../so'
import type { OLam } from '../types'

/** Ô RUỘT KHỐI — mấy widget hộp thoại nào cũng cần.
 *
 *  Ở riêng một file vì BA hộp dùng chung: Hành động, Bắt đầu, và hộp nào sau này cũng
 *  dựng ô theo danh sách Python gửi sang. Để `Hang` nằm trong `HopHanhDong` rồi hộp
 *  khác import sang thì sớm muộn một bên sửa, bên kia vỡ mà không ai thấy.
 *
 *  Hình thức một ô do `kieu` quyết, mà `kieu` thì PYTHON khai — giao diện không tự
 *  nghĩ ra ô nào.
 */

/** Ô SỐ có BẢN NHÁP riêng.
 *
 *  Ép `Number()` ngay từng phím thì `"1."` ra `1`, state không đổi, React ghi đè ô về
 *  `"1"` — dấu chấm biến mất và phím kế cho `"15"`: 1,5 lặng lẽ thành 15. Đã xảy ra
 *  thật, nên luật lọc nằm riêng ở `src/so.ts` để `webui/kiem/o_so.mjs` canh được. */
export function ONhapSo({ gt, onDoi, nguyen }: {
  gt: unknown
  onDoi: (n: number) => void
  /** Chỉ nhận số nguyên (giờ, phút) — `locSo` sẽ gạt luôn dấu chấm. */
  nguyen?: boolean
}) {
  const [nhap, setNhap] = useState<string | null>(null)
  return (
    <input className="o so" inputMode={nguyen ? 'numeric' : 'decimal'}
           spellCheck={false} value={nhap ?? String(gt ?? 0)}
           onChange={e => {
             const { chu, so } = locSo(e.target.value, nguyen)
             setNhap(chu)
             // Chuỗi còn dở dang (`""`, `"-"`, `"1."`) thì giữ trong ô, CHƯA lên khối.
             if (so !== null) onDoi(so)
           }}
           onBlur={() => {
             if (nhap !== null) { onDoi(chotSo(nhap)); setNhap(null) }
           }} />
  )
}

/** Một hàng = một ô.
 *
 *  `children` thay chỗ ô mặc định, cho mấy kiểu chỉ MỘT hộp thoại cần (danh sách mã,
 *  khoảng ngày) — chúng vẫn được cái nhãn và lời gợi ý xếp thẳng cột như mọi hàng
 *  khác, mà file này không phải biết chúng tồn tại. */
export function Hang({ o, gt, onDoi, children }: {
  o: OLam; gt?: unknown; onDoi?: (v: unknown) => void; children?: ReactNode
}) {
  return (
    <label className="o-hang" title={o.goi_y || o.nhan}>
      <span className="nhan-o">{o.nhan}</span>
      {children ?? (o.kieu === 'chon' ? (
        <select className="o day" value={String(gt ?? '')}
                onChange={e => onDoi?.(e.target.value)}>
          {o.chon.map(([m, n]) => <option key={m} value={m}>{n}</option>)}
        </select>
      ) : o.kieu === 'co_khong' ? (
        <input type="checkbox" className="o-tich" checked={gt === true}
               onChange={e => onDoi?.(e.target.checked)} />
      ) : o.kieu === 'so' ? (
        <ONhapSo gt={gt} nguyen={o.nguyen} onDoi={n => onDoi?.(n)} />
      ) : (
        // Placeholder nói ĐÚNG MỘT điều: ô này không bắt buộc. Để trống rồi thì sao
        // là chuyện của từng ô, và `goi_y` bên cạnh đã nói — nhồi vào đây thì ô Mốc
        // so sánh hiện câu "bộ sinh mã tự điền", mà nó có tự điền mốc nào đâu.
        <input className="o day" spellCheck={false} value={String(gt ?? '')}
               placeholder={o.bat_buoc ? '' : 'không bắt buộc'}
               onChange={e => onDoi?.(e.target.value)} />
      ))}
      {/* Tỷ trọng lưu ĐÚNG DẠNG LEAN NHẬN (0.3), nên bày thêm "= 30%" ngay cạnh — một
          dòng ĐỌC, không phải một phép đổi giấu trong giao diện. */}
      {o.don_vi === 'phần' ? (
        <span className="doc-them">= {Math.round(Number(gt ?? 0) * 1000) / 10}%</span>
      // Mọi đơn vị KHÁC hiện nguyên văn. Trước đây chỉ `$` được viết riêng một dòng,
      // nên ô nào khai "phút", "lần", "ngày"… là đơn vị ấy biến mất — từ điển nói mà
      // giao diện không nghe.
      ) : o.don_vi ? (
        <span className="doc-them">{o.don_vi}</span>
      ) : null}
      {o.goi_y && <span className="goi-y-o">{o.goi_y}</span>}
    </label>
  )
}

/** Câu LEAN khối này sẽ gọi, bày thẳng ra cho người chơi thấy.
 *
 *  Không phải trang trí: cả bộ khối dựng trên một lời hứa — mỗi khối chỉ ra được MỘT
 *  thứ có thật của LEAN, app không tự đẻ backend nào (D-11). Bày cái hàm ra là cách
 *  kiểm được lời hứa ấy, chứ không phải tin suông. */
export function KhaiLean({ ham }: { ham: string }) {
  return (
    <div className="lean-khai"><span>LEAN sẽ gọi</span><code>{ham}</code></div>
  )
}
