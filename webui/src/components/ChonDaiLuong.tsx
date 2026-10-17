import { useMemo, useState } from 'react'
import BangNoi from './BangNoi'
import Icon from './Icon'
import type { DaiLuong, TuDienHoi } from '../types'

/** BẢNG CHỌN ĐẠI LƯỢNG — cửa DUY NHẤT vào kho 68 đại lượng.
 *
 *  ⭐ BÀY ĐÚNG `td.kho`, không lọc bớt theo họ. Đó là cả lời hứa "với tới được tất
 *  cả": `test_hoi` chốt rằng `kho` chứa đủ từ điển, `test_giao_dien` chốt rằng chỗ
 *  này đọc `kho` — nối hai đầu thì không có đại lượng nào khai ra mà người chơi
 *  không tìm thấy. Bản trước mỗi khối chỉ thấy họ của nó, nên 33 trong 68 cái là
 *  vô hình.
 *
 *  LỌC DẦN, HAI TẦNG KHÁC HẲN NHAU:
 *
 *  · CỨNG — biến mất hẳn. Vế phải không bao giờ bày đại lượng ĐÚNG/SAI: `giá > Đang
 *    giữ mã này` không phải câu khó hiểu, nó là câu không tồn tại.
 *  · MỀM — xếp trước, KHÔNG giấu. Cùng đơn vị với vế kia thì lên đầu; khác đơn vị
 *    gập lại bên dưới, mở ra một cái là thấy. LEAN cho so, chỉ là hiếm khi có nghĩa
 *    — nên không chặn, chỉ không để nó chen vào tầm mắt.
 *
 *  Họ bị TẮT (Hỏi doanh nghiệp — cần mua dữ liệu) thì bày MỜ KÈM LÝ DO, không giấu:
 *  giấu đi thì người chơi không bao giờ biết nó có, mà bày rồi để họ bấm vào mới báo
 *  lỗi thì đúng thứ phải tránh. Lý do đọc được TRƯỚC khi bấm.
 */
export default function ChonDaiLuong({ neo, td, dangChon, donViKia, chiSo, choSo,
                                      onChon, onChonSo, onDong }: {
  neo: DOMRect
  td: TuDienHoi
  dangChon?: string
  /** Đơn vị của vế BÊN KIA — có thì cùng đơn vị được xếp lên trước. */
  donViKia?: string
  /** Chỉ bày đại lượng trả SỐ (vế phải, và ô «giá trị vẽ» của Plot). */
  chiSo?: boolean
  /** Vế này được phép là một con số — ô gõ số ghim trên đầu bảng. */
  choSo?: { gia_tri: number }
  onChon: (d: DaiLuong) => void
  onChonSo?: (n: number) => void
  onDong: () => void
}) {
  const [tim, setTim] = useState('')
  /** Rổ «cần mua dữ liệu» GẬP SẴN, rổ «khác đơn vị» thì KHÔNG.
   *
   *  ⚠ Bản đầu làm ngược: 7 mục chạy-không-ra-số bày hết ra, còn 60 mục dùng được
   *  thì giấu sau một nhát bấm. Nhìn mới thấy. Luật đúng là: thứ KHÔNG DÙNG ĐƯỢC
   *  mới đáng gập — khác đơn vị vẫn chạy ngon, chỉ là hiếm khi có nghĩa, nên nó chỉ
   *  cần đứng SAU chứ không cần biến mất. */
  const [moMua, setMoMua] = useState(false)
  const [roi, setRoi] = useState<DaiLuong | null>(null)

  const hoCua = useMemo(
    () => Object.fromEntries(td.loai.map(l => [l.ma, l])), [td.loai])

  /** Lọc theo chữ tìm. Tìm cả NHÃN TIẾNG VIỆT lẫn MÃ LEAN: người làm quant gõ "macd"
   *  chứ không gõ "đường trung bình hội tụ phân kỳ". */
  const hop = useMemo(() => {
    const q = tim.trim().toLowerCase()
    return td.kho.filter(d => {
      if (chiSo && d.kieu === 'co_khong') return false
      if (!q) return true
      return d.nhan.toLowerCase().includes(q) || d.ma.includes(q)
        || d.lean.toLowerCase().includes(q)
    })
  }, [td.kho, tim, chiSo])

  // Ba rổ: cùng đơn vị · khác đơn vị · cần mua dữ liệu. Thứ ba tách ra vì nó không
  // phải "ít liên quan" mà là "chạy không ra số" — hai chuyện khác nhau.
  const { cung, khac, mua } = useMemo(() => {
    const cung: DaiLuong[] = [], khac: DaiLuong[] = [], mua: DaiLuong[] = []
    for (const d of hop) {
      if (hoCua[d.ho]?.tat) mua.push(d)
      else if (donViKia && d.don_vi === donViKia) cung.push(d)
      else khac.push(d)
    }
    return { cung, khac, mua }
  }, [hop, donViKia, hoCua])

  const muc = (d: DaiLuong, tat?: string) => (
    <button key={d.ma} type="button" className={`dl-muc${tat ? ' tat' : ''}`
      + (d.ma === dangChon ? ' dang' : '')}
            title={tat || d.lean}
            onMouseEnter={() => setRoi(d)}
            onClick={() => { if (!tat) { onChon(d); onDong() } }}>
      <span className="dl-ten">{d.nhan}</span>
      <span className="dl-dv">{d.don_vi || (d.kieu === 'co_khong' ? 'đúng/sai' : '')}</span>
    </button>
  )

  /** Một mục đầu nhóm — chỉ hiện khi nhóm đổi, để danh sách còn đọc được theo cụm. */
  const theoNhom = (ds: DaiLuong[], tat?: (d: DaiLuong) => string | undefined) => {
    const ra: JSX.Element[] = []
    let nhom = ''
    for (const d of ds) {
      if (d.nhom !== nhom) {
        nhom = d.nhom
        ra.push(<div key={`h${d.ma}`} className="dl-nhom">
          <Icon name={hoCua[d.ho]?.icon ?? 'motSo'} /> {nhom}
        </div>)
      }
      ra.push(muc(d, tat?.(d)))
    }
    return ra
  }

  return (
    <BangNoi neo={neo} rong={320} cao={420} onDong={onDong}>
      <div className="bn-tim">
        <Icon name="tim" />
        <input autoFocus value={tim} spellCheck={false}
               placeholder="tìm: rsi, giá, macd, tiền mặt…"
               onChange={e => setTim(e.target.value)} />
      </div>

      {choSo && onChonSo && (
        <div className="bn-so">
          <span>hoặc một con số</span>
          <input className="o so" inputMode="decimal" defaultValue={choSo.gia_tri}
                 onChange={e => onChonSo(e.target.value as unknown as number)} />
        </div>
      )}

      <div className="bn-ds">
        {cung.length > 0 && (<>
          <div className="dl-tang">cùng đơn vị «{donViKia}» — {cung.length} cái</div>
          {theoNhom(cung)}
        </>)}

        {khac.length > 0 && (<>
          {cung.length > 0 &&
            <div className="dl-tang mo">khác đơn vị — {khac.length} cái</div>}
          {theoNhom(khac)}
        </>)}

        {mua.length > 0 && (<>
          <button type="button" className="dl-gap" onClick={() => setMoMua(v => !v)}
                  title={mua.map(d => hoCua[d.ho]?.tat).find(Boolean) || ''}>
            {moMua ? '▾' : '▸'} cần mua dữ liệu — {mua.length} cái
          </button>
          {moMua && theoNhom(mua, d => hoCua[d.ho]?.tat || undefined)}
        </>)}

        {!hop.length && <div className="bn-rong">không có đại lượng nào khớp «{tim}»</div>}
      </div>

      {/* Nói thẳng hàm LEAN đứng sau — cùng lời hứa như `.lean-khai` của hộp Hành
          động: mỗi mục ở đây là MỘT thứ có thật, và đây là chỗ kiểm được. */}
      <div className="bn-lean">{roi ? roi.lean : `${td.kho.length} đại lượng`}</div>
    </BangNoi>
  )
}
