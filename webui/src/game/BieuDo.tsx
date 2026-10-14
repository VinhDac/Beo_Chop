/** BIỂU ĐỒ CỦA GAME — histogram kiểu Opus Magnum và đường vốn thu nhỏ.
 *
 * Opus Magnum chấm mỗi lời giải bằng BA histogram (Cost · Cycles · Area) — không lời giải
 * nào đứng đầu cả ba, nên người chơi tự chọn đánh đổi. Ta có ba cột của mình: Lãi % ·
 * Sụt giảm % · Độ gọn. Chưa có người chơi khác nên đám đông là CÁC LẦN THỬ của chính bạn
 * trên màn đó; vạch "Boss" là Mua rồi giữ. Có cộng đồng thì chỉ đổi nguồn số.
 */

const W = 236, H = 104, LE = 8

function _phamVi(ds: number[]): [number, number] {
  let lo = Math.min(...ds), hi = Math.max(...ds)
  if (lo === hi) { lo -= 1; hi += 1 }
  const dem = (hi - lo) * 0.12
  return [lo - dem, hi + dem]
}

export function Histogram({ ten, donVi, giaTri, cuaBan, boss, tot, so = 3 }: {
  ten: string
  donVi: string
  /** Mọi lần thử (đám đông). */
  giaTri: number[]
  /** Cỗ máy đang xét — vạch sáng. */
  cuaBan: number | null
  /** Vạch boss (chỉ cột Lãi %). */
  boss?: number | null
  /** Bên nào là tốt: 'cao' = càng phải càng tốt. */
  tot: 'cao' | 'thap'
  so?: number
}) {
  const tatCa = [...giaTri, ...(cuaBan != null ? [cuaBan] : []), ...(boss != null ? [boss] : [])]
  if (!tatCa.length) return null
  const [lo, hi] = _phamVi(tatCa)
  const NGAN = 12
  const dem = new Array(NGAN).fill(0)
  const ngan = (v: number) => Math.min(NGAN - 1, Math.max(0, Math.floor((v - lo) / (hi - lo) * NGAN)))
  for (const v of giaTri) dem[ngan(v)] += 1
  const cao = Math.max(1, ...dem)
  const x = (v: number) => LE + (v - lo) / (hi - lo) * (W - 2 * LE)
  const rong = (W - 2 * LE) / NGAN
  const nganBan = cuaBan != null ? ngan(cuaBan) : -1
  /* Nhãn đứng CẠNH vạch, không đè lên đầu vạch: đặt giữa thì dấu nặng của "Bạn" dính
     liền vào đầu vạch cùng màu và đọc ra "Ban". Sát mép phải thì lật sang trái. */
  const vach = (v: number, lop: string, chu: string) => {
    const xv = x(v), trai = xv > W - 44
    return (
      <g className={lop}>
        <line x1={xv} x2={xv} y1={4} y2={H - 16} />
        <text x={trai ? xv - 4 : xv + 4} y={12} textAnchor={trai ? 'end' : 'start'}>{chu}</text>
      </g>
    )
  }
  return (
    <div className="g-histo">
      <div className="g-histo-dau">
        <span>{ten}</span>
        <b>{cuaBan == null ? '—' : `${cuaBan > 0 && donVi === '%' && tot === 'cao' ? '+' : ''}${cuaBan.toFixed(so === 0 ? 0 : 2)}${donVi === '%' ? ' %' : ''}`}</b>
      </div>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <rect x={0} y={0} width={W} height={H} rx={6} className="g-histo-nen" />
        {dem.map((n, k) => n > 0 && (
          <rect key={k} x={LE + k * rong + 1} width={rong - 2}
                y={H - 16 - (n / cao) * (H - 34)} height={(n / cao) * (H - 34)}
                className={'g-histo-cot' + (k === nganBan ? ' ban' : '')} />
        ))}
        <line x1={LE} x2={W - LE} y1={H - 16} y2={H - 16} className="g-histo-day" />
        {boss != null && vach(boss, 'g-vach-boss', 'Boss')}
        {cuaBan != null && vach(cuaBan, 'g-vach-ban', 'Bạn')}
        <text x={LE} y={H - 4} className="g-histo-so">{lo.toFixed(so === 0 ? 0 : 1)}</text>
        <text x={W - LE} y={H - 4} textAnchor="end" className="g-histo-so">{hi.toFixed(so === 0 ? 0 : 1)}</text>
      </svg>
      <div className="g-histo-chan">
        {giaTri.length} lần thử · {tot === 'cao' ? 'càng phải càng tốt →' : '← càng trái càng tốt'}
      </div>
    </div>
  )
}

/** Đường vốn thu nhỏ: trên vốn đầu thì xanh, dưới thì đỏ. `diem` = `[t, vốn, sụt %]`. */
export function DuongVonNho({ diem, vonDau, rong = 260, cao = 54, tDau, tCuoi, viTri }: {
  diem: [number, number, number][]
  vonDau: number
  rong?: number
  cao?: number
  tDau?: number | null
  tCuoi?: number | null
  /** Giờ đang phát lại — vạch dọc. */
  viTri?: number | null
}) {
  if (!diem.length) return <svg width={rong} height={cao} />
  const t0 = tDau ?? diem[0][0], t1 = tCuoi ?? diem[diem.length - 1][0]
  const ds = [vonDau, ...diem.map(d => d[1])]
  let lo = Math.min(...ds), hi = Math.max(...ds)
  if (lo === hi) { lo -= 1; hi += 1 }
  const x = (t: number) => ((t - t0) / Math.max(1, t1 - t0)) * (rong - 4) + 2
  const y = (v: number) => cao - 3 - ((v - lo) / (hi - lo)) * (cao - 6)
  let d = `M ${x(t0)} ${y(vonDau)}`
  for (const [t, v] of diem) d += ` H ${x(t)} V ${y(v)}`
  d += ` H ${x(t1)}`
  const cuoi = diem[diem.length - 1][1]
  return (
    <svg width={rong} height={cao} className="g-von">
      <line x1={2} x2={rong - 2} y1={y(vonDau)} y2={y(vonDau)} className="g-von-moc" />
      <path d={d} className={'g-von-duong ' + (cuoi >= vonDau ? 'lai' : 'lo')} />
      {viTri != null && viTri >= t0 && viTri <= t1 &&
        <line x1={x(viTri)} x2={x(viTri)} y1={0} y2={cao} className="g-von-vach" />}
    </svg>
  )
}

/** Sao đơn sắc ★☆ — dùng chung mọi màn hình game. `nay` = số sao vừa đạt (cho hiệu ứng). */
export function SaoGame({ n, tren = 3, to = false, hieuUng = false }: {
  n: number | null | undefined; tren?: number; to?: boolean; hieuUng?: boolean
}) {
  const k = Math.max(0, Math.min(tren, n ?? 0))
  return (
    <span className={'g-sao' + (to ? ' to' : '')} title={`${k}/${tren} sao`}>
      {Array.from({ length: tren }, (_, i) => (
        <span key={i} className={(i < k ? 'co' : 'khong') + (hieuUng && i < k ? ' bung' : '')}
              style={hieuUng ? { animationDelay: `${0.35 + i * 0.45}s` } : undefined}>
          {i < k ? '★' : '☆'}
        </span>
      ))}
    </span>
  )
}
