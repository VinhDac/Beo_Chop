import { useMemo, useRef, useState } from 'react'
import type { DuongBieuDo } from '../types'

/** MỘT BẢNG BIỂU ĐỒ — tiêu đề trái, nút khoảng phải, dấu ✕ đóng, rồi hình.
 *
 *  ⚠ MỘT CHỖ CỐ Ý LÀM KHÁC BẢN WEB, và đây là lý do: bảng «Strategy Equity» có hai
 *  đại lượng khác thang hẳn nhau — đường vốn tính bằng ĐÔ, lợi suất tính bằng PHẦN
 *  TRĂM. Chồng cả hai lên một khung với hai trục dọc là trò nói dối bằng tỉ lệ: hai
 *  đường cắt nhau ở chỗ do người vẽ chọn thang, chứ không phải chỗ có thật.
 *
 *  Nên mỗi ĐƠN VỊ được một DẢI RIÊNG xếp chồng, dùng chung trục ngang. Nhìn vào gần
 *  như y hệt bản web (họ cũng tách nến lên trên, cột lợi suất xuống dưới), mà không
 *  còn chỗ cho phép so sánh sai.
 *
 *  Màu đã qua sáu phép kiểm của bộ canh bảng màu (dải sáng, sàn sắc độ, tách màu cho
 *  người mù màu, tương phản với nền tối). Đừng đổi bằng mắt.
 */
const MAU = ['#cc7a28', '#4a90d9', '#4fa86a', '#b06fd0']
const MAU_LEN = '#4fa86a'
const MAU_XUONG = '#cc5544'

const KHOANG: [string, number][] = [
  ['1m', 30], ['3m', 90], ['1y', 365], ['All', 0],
]

type Diem = number[]

function gon(n: number, don_vi: string) {
  const a = Math.abs(n)
  let s: string
  if (a >= 1e9) s = (n / 1e9).toFixed(2) + 'B'
  else if (a >= 1e6) s = (n / 1e6).toFixed(2) + 'M'
  else if (a >= 1e3) s = Math.round(n).toLocaleString('vi-VN')
  else s = n.toLocaleString('vi-VN', { maximumFractionDigits: 4 })
  return don_vi === '$' ? '$' + s : don_vi === '%' ? s + '%' : s
}

const ngay = (giay: number) =>
  new Date(giay * 1000).toLocaleDateString('vi-VN',
    { day: '2-digit', month: '2-digit', year: 'numeric' })

/** Mỗi ĐƠN VỊ một dải. Cùng đơn vị thì chung dải — đó mới là so sánh được. */
function chiaDai(duong: DuongBieuDo[]) {
  const theo = new Map<string, DuongBieuDo[]>()
  for (const d of duong) {
    const k = d.don_vi || '·'
    if (!theo.has(k)) theo.set(k, [])
    theo.get(k)!.push(d)
  }
  return [...theo.entries()]
}

export default function BangBieuDo({ ten, duong, onDong }: {
  ten: string
  duong: DuongBieuDo[]
  onDong: () => void
}) {
  const [khoang, setKhoang] = useState(0)
  const [tro, setTro] = useState<number | null>(null)
  const boc = useRef<HTMLDivElement>(null)

  const W = 1000
  const L = 8, R = 86, T = 10, B = 24       // chừa mép: nhãn trục nằm bên PHẢI
  const CAO_DAI = 150

  const d = useMemo(() => {
    const dai = chiaDai(duong)
    const moi = duong.flatMap(x => x.diem)
    if (!moi.length) return null
    const xMax = Math.max(...moi.map(p => p[0]))
    const xMin = khoang
      ? Math.max(Math.min(...moi.map(p => p[0])), xMax - khoang * 86400)
      : Math.min(...moi.map(p => p[0]))

    const loc = (ds: Diem[]) => ds.filter(p => p[0] >= xMin && p[0] <= xMax)
    const H = dai.length * CAO_DAI
    const px = (x: number) => L + ((x - xMin) / (xMax - xMin || 1)) * (W - L - R)

    const bang = dai.map(([don_vi, ds], i) => {
      const loat = ds.map(x => ({ ...x, diem: loc(x.diem) }))
      const gt = loat.flatMap(x => x.diem.flatMap(p =>
        p.length >= 5 ? [p[2], p[3]] : [p[p.length - 1]]))
      let y0 = gt.length ? Math.min(...gt) : 0
      let y1 = gt.length ? Math.max(...gt) : 1
      if (y0 === y1) { y0 -= 1; y1 += 1 }
      const dem = y1 - y0
      y0 -= dem * 0.08; y1 += dem * 0.08
      const top = T + i * CAO_DAI
      const py = (y: number) =>
        top + (CAO_DAI - B) - ((y - y0) / (y1 - y0)) * (CAO_DAI - B - 6)
      const vach = [0, 0.5, 1].map(f => {
        const y = y0 + (y1 - y0) * f
        return { y: py(y), chu: gon(y, don_vi) }
      })
      return { don_vi, loat, py, vach, top, co0: y0 <= 0 && y1 >= 0 ? py(0) : null }
    })
    // Mốc thời gian lấy từ đường DÀY NHẤT — con trỏ bám vào đó.
    const moc = loc([...duong].sort((a, b) => b.diem.length - a.diem.length)[0].diem)
    return { bang, px, H, xMin, xMax, moc }
  }, [duong, khoang])

  if (!d) return null

  function ro(ev: React.MouseEvent) {
    const r = boc.current?.getBoundingClientRect()
    if (!r || !d) return
    const x = ((ev.clientX - r.left) / r.width) * W
    let tot = -1, gap = Infinity
    d.moc.forEach((p, i) => {
      const k = Math.abs(d.px(p[0]) - x)
      if (k < gap) { gap = k; tot = i }
    })
    setTro(tot >= 0 ? tot : null)
  }

  const tx = tro !== null && d.moc[tro] ? d.moc[tro][0] : null
  /** Giá trị của một đường tại thời điểm con trỏ — tìm theo HOÀNH ĐỘ, vì các đường
   *  khác số điểm nên chỉ số mảng không khớp nhau. */
  const taiX = (ds: Diem[]) => {
    if (tx === null || !ds.length) return null
    return ds.reduce((a, b) => Math.abs(b[0] - tx) < Math.abs(a[0] - tx) ? b : a)
  }

  let iMau = 0
  return (
    <div className="bang-bd">
      <div className="bd-dau">
        <b>{ten}</b>
        <span className="day" />
        {KHOANG.map(([n, v]) => (
          <button key={n} className={'nut-nho' + (khoang === v ? ' chon' : '')}
                  onClick={() => setKhoang(v)}>{n}</button>
        ))}
        <button className="nut-nho dong" title="Đóng bảng này" onClick={onDong}>✕</button>
      </div>

      <div className="bd-than" ref={boc}
           onMouseMove={ro} onMouseLeave={() => setTro(null)}>
        <svg viewBox={`0 0 ${W} ${d.H + T + 6}`} preserveAspectRatio="none"
             role="img" aria-label={ten} style={{ height: d.H + T + 6 }}>
          {d.bang.map((b, bi) => (
            <g key={bi}>
              {b.vach.map((v, i) => (
                <g key={i}>
                  <line x1={L} y1={v.y} x2={W - R} y2={v.y} className="luoi" />
                  <text x={W - R + 7} y={v.y + 4} className="nhan-truc">{v.chu}</text>
                </g>
              ))}
              {b.loat.map(x => {
                const mau = x.kieu === 'nen' ? '' : MAU[iMau++ % MAU.length]
                if (x.kieu === 'nen') {
                  const r = Math.max(1, (W - L - R) / (x.diem.length * 2))
                  return x.diem.map((p, i) => {
                    const len = p[4] >= p[1]
                    const c = len ? MAU_LEN : MAU_XUONG
                    const cx = d.px(p[0])
                    return (
                      <g key={i}>
                        <line x1={cx} y1={b.py(p[2])} x2={cx} y2={b.py(p[3])}
                              stroke={c} strokeWidth={1} />
                        <rect x={cx - r} y={b.py(Math.max(p[1], p[4]))} width={r * 2}
                              height={Math.max(1, Math.abs(b.py(p[1]) - b.py(p[4])))}
                              fill={c} />
                      </g>
                    )
                  })
                }
                if (x.kieu === 'cot') {
                  const y0 = b.co0 ?? b.py(0)
                  const r = Math.max(0.6, (W - L - R) / (x.diem.length * 2.6))
                  return x.diem.map((p, i) => {
                    const y = b.py(p[p.length - 1])
                    return <rect key={i} x={d.px(p[0]) - r} y={Math.min(y, y0)}
                                 width={r * 2} height={Math.max(1, Math.abs(y - y0))}
                                 fill={mau} />
                  })
                }
                if (x.kieu === 'o_vuong') {
                  // Treemap của LEAN là một CHUỖI THỜI GIAN khối lượng, không phải
                  // một ô tĩnh — nên vẽ nó thành vùng, đúng thứ dữ liệu thật sự nói.
                  const y0 = b.co0 ?? b.py(0)
                  const dd = x.diem.map(p =>
                    `${d.px(p[0])},${b.py(p[p.length - 1])}`).join(' ')
                  return (
                    <polygon key={x.ten} fill={mau} fillOpacity={0.3} stroke={mau}
                             strokeWidth={1.5} vectorEffect="non-scaling-stroke"
                             points={`${d.px(x.diem[0][0])},${y0} ${dd} `
                                     + `${d.px(x.diem[x.diem.length - 1][0])},${y0}`} />
                  )
                }
                return (
                  <polyline key={x.ten} fill="none" stroke={mau} strokeWidth={2}
                            vectorEffect="non-scaling-stroke"
                            points={x.diem.map(p =>
                              `${d.px(p[0])},${b.py(p[p.length - 1])}`).join(' ')} />
                )
              })}
            </g>
          ))}
          {tx !== null && (
            <line x1={d.px(tx)} y1={T} x2={d.px(tx)} y2={d.H} className="doc-tro" />
          )}
        </svg>

        <div className="bd-truc-duoi">
          <span>{ngay(d.xMin)}</span><span>{ngay(d.xMax)}</span>
        </div>

        {tx !== null && (
          <div className="o-tro" style={{ left: `${(d.px(tx) / W) * 100}%` }}>
            <b>{ngay(tx)}</b>
            {d.bang.flatMap(b => b.loat.map(x => {
              const p = taiX(x.diem)
              if (!p) return null
              return p.length >= 5 ? (
                <span key={x.ten} className="cot-doc">
                  <i>{x.ten}</i>
                  <em>Mở {gon(p[1], b.don_vi)} · Cao {gon(p[2], b.don_vi)}</em>
                  <em>Thấp {gon(p[3], b.don_vi)} · Đóng {gon(p[4], b.don_vi)}</em>
                </span>
              ) : (
                <span key={x.ten}>{x.ten}: {gon(p[p.length - 1], b.don_vi)}</span>
              )
            }))}
          </div>
        )}
      </div>

      {/* Hai đường trở lên thì LUÔN có chú giải — màu không bao giờ là thứ DUY NHẤT
          nói đường nào là đường nào. */}
      {duong.length > 1 && (
        <div className="chu-giai">
          {(() => { let j = 0; return duong.map(x => (
            <span key={x.ten}>
              {x.kieu === 'nen'
                ? <><i style={{ background: MAU_LEN }} /><i style={{ background: MAU_XUONG }} /></>
                : <i style={{ background: MAU[j++ % MAU.length] }} />}
              {x.ten}{x.don_vi ? ` (${x.don_vi})` : ''}
            </span>
          )) })()}
        </div>
      )}
    </div>
  )
}
