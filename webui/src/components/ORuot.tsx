import { useState, type ReactNode } from 'react'
import { locSo, chotSo } from '../so'
import Icon from './Icon'
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

/** Nhãn tiếng Việt -> tên núm hợp khuôn LEAN: `"Chu kỳ"` -> `"chu_ky"`.
 *
 *  Đặt tên hộ để người dùng không phải gõ. Khuôn phải khớp `core._RE_TEN_THAM_SO`
 *  bên Python (chữ thường không dấu, số, gạch dưới, bắt đầu bằng chữ) — tên sai
 *  khuôn thì config optimizer của LEAN không khai nổi, và nó quét một tên khác
 *  trong khi thuật toán đọc tên này: N lượt backtest ra y hệt nhau, không lỗi. */
export function tenNum(nhan: string): string {
  const s = nhan.normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/đ/g, 'd').replace(/Đ/g, 'D')
    .toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
  return (/^[a-z]/.test(s) ? s : 'num_' + s).slice(0, 32)
}

/** NÚT GHIM một ô số làm tham số Optimize.
 *
 *  Ghim rồi thì ô ĐỔI SANG GÕ TÊN, còn con số lùi về sau thành "mặc định 14" — vì
 *  sau khi ghim, thứ người ta cần đọc là cái tên, còn con số chỉ là giá trị dùng khi
 *  chạy backtest thường.
 *
 *  Dùng chung một bản cho cả ba chỗ có ô số (tham số chỉ báo, con số của vế, ô số
 *  khối Hành động) — ba bản thì sớm muộn một bên đặt tên theo khuôn khác. */
export function OGhim({ chu, tenO, nhan, so, onDoi, children }: {
  /** Cái DICT đang giữ ô ấy — vế điều kiện, hay chính khối. */
  chu: Record<string, unknown>
  tenO: string
  nhan: string
  so: unknown
  onDoi: (chuMoi: Record<string, unknown>) => void
  /** Ô số thật, hiện khi CHƯA ghim. */
  children: ReactNode
}) {
  const ghim = (chu.ghim_num ?? {}) as Record<string, string>
  const ten = ghim[tenO] ?? ''
  const dat = (v: string | null) => {
    const m = { ...ghim }
    if (v === null) delete m[tenO]
    else m[tenO] = v
    onDoi({ ...chu, ghim_num: Object.keys(m).length ? m : undefined })
  }
  return (<>
    {ten
      ? <input className="o ten-num" spellCheck={false} value={ten}
               placeholder="tên núm" onChange={e => dat(tenNum(e.target.value))} />
      : children}
    <button type="button"
            className={'nut-nho nut-ghim' + (ten ? ' dang' : '')}
            title={ten ? `Bỏ ghim — ô này đang là núm «${ten}»`
                       : 'Ghim làm tham số để Optimize quét'}
            onClick={() => dat(ten ? null : tenNum(nhan))}>
      <Icon name="ghim" />
    </button>
    {ten && <span className="doc-them">mặc định {String(so ?? '')}</span>}
  </>)
}

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

/** CHỈ cái widget của một ô, không nhãn không gợi ý.
 *
 *  Tách ra khỏi `Hang` vì ô CON của một rổ cần đúng phần này: `Hang` dựng một
 *  `<label>`, mà `<label>` lồng trong `<label>` là HTML sai — bấm vào nhãn con sẽ
 *  nhảy focus sang ô cha, và trình duyệt không báo gì cả. Một chỗ duy nhất quyết
 *  `kieu` nào ra widget nào, hai chỗ dùng. */
export function OTheoKieu({ o, gt, onDoi }: {
  o: OLam; gt?: unknown; onDoi?: (v: unknown) => void
}) {
  if (o.kieu === 'chon') {
    return (
      <select className="o day" value={String(gt ?? '')}
              onChange={e => onDoi?.(e.target.value)}>
        {o.chon.map(([m, n]) => <option key={m} value={m}>{n}</option>)}
      </select>
    )
  }
  if (o.kieu === 'co_khong') {
    return (
      <input type="checkbox" className="o-tich" checked={gt === true}
             onChange={e => onDoi?.(e.target.checked)} />
    )
  }
  if (o.kieu === 'so') {
    return <ONhapSo gt={gt} nguyen={o.nguyen} onDoi={n => onDoi?.(n)} />
  }
  // Placeholder nói ĐÚNG MỘT điều: ô này không bắt buộc. Để trống rồi thì sao là
  // chuyện của từng ô, và `goi_y` bên cạnh đã nói — nhồi vào đây thì ô Mốc so sánh
  // hiện câu "bộ sinh mã tự điền", mà nó có tự điền mốc nào đâu.
  return (
    <input className="o day" spellCheck={false} value={String(gt ?? '')}
           placeholder={o.bat_buoc ? '' : 'không bắt buộc'}
           onChange={e => onDoi?.(e.target.value)} />
  )
}

/** Đơn vị / cách đọc thêm của một ô — dùng chung với `OTheoKieu`. */
export function DocThem({ o, gt }: { o: OLam; gt?: unknown }) {
  // Tỷ trọng lưu ĐÚNG DẠNG LEAN NHẬN (0.3), nên bày thêm "= 30%" ngay cạnh — một
  // dòng ĐỌC, không phải một phép đổi giấu trong giao diện.
  if (o.don_vi === 'phần') {
    return <span className="doc-them">= {Math.round(Number(gt ?? 0) * 1000) / 10}%</span>
  }
  // Mọi đơn vị KHÁC hiện nguyên văn. Trước đây chỉ `$` được viết riêng một dòng, nên
  // ô nào khai "phút", "lần", "ngày"… là đơn vị ấy biến mất — từ điển nói mà giao
  // diện không nghe.
  return o.don_vi ? <span className="doc-them">{o.don_vi}</span> : null
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
      {children ?? <OTheoKieu o={o} gt={gt} onDoi={onDoi} />}
      <DocThem o={o} gt={gt} />
      {o.goi_y && <span className="goi-y-o">{o.goi_y}</span>}
    </label>
  )
}

/** Câu LEAN khối này sẽ gọi, bày thẳng ra cho người chơi thấy.
 *
 *  Không phải trang trí: cả bộ khối dựng trên một lời hứa — mỗi khối chỉ ra được MỘT
 *  thứ có thật của LEAN, app không tự đẻ backend nào (D-11). Bày cái hàm ra là cách
 *  kiểm được lời hứa ấy, chứ không phải tin suông. */
/** Dòng «LEAN sẽ gọi» — BÀY LẠI câu Python khai, không ghép lại câu nào.
 *
 *  Nhận CẢ MỘT DANH SÁCH vì một khối có thể khai nhiều câu: khối Bắt đầu chạy trên
 *  rổ động nói một câu về nhịp và một câu `set_universe_selection`, mà bản trước
 *  chỉ có chỗ cho một — nên câu quan trọng nhất của cái rổ không có chỗ nào để hiện
 *  ra. Chỗ này không biết trong danh sách có mấy câu, và đó là cả ý: thêm một câu
 *  khai bên Python là nó hiện ra ngay. */
export function KhaiLean({ ham }: { ham: string | string[] }) {
  const ds = (Array.isArray(ham) ? ham : [ham]).filter(Boolean)
  return (
    <div className="lean-khai">
      <span>LEAN sẽ gọi</span>
      <div className="lean-cau">{ds.map((c, i) => <code key={i}>{c}</code>)}</div>
    </div>
  )
}
