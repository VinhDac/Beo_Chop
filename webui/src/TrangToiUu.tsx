import { useEffect, useMemo, useState } from 'react'
import TitleBar from './components/TitleBar'
import Icon from './components/Icon'
import { cho_cau_noi, pyTu } from './api'
import type { LuotToiUu, TuDienToiUu } from './types'

/** CỬA SỔ OPTIMIZE — đúng HAI phần, không hơn.
 *
 *    1. PLOT 2D: tìm đang tốt lên hay xấu đi.
 *    2. BẢNG XẾP HẠNG: bấm đầu cột để sắp xuôi/ngược.
 *
 *  TRỤC NGANG LÀ LƯỢT THỨ MẤY, không phải giá trị tham số — và đó là một quyết
 *  định, không phải tiện tay. Vẽ tham số lên trục ngang chỉ đúng khi có ĐÚNG MỘT
 *  núm; hai núm trở lên là phải heatmap, ba núm thì chịu. Còn câu hỏi thật —
 *  "đang tốt lên hay xấu đi" — thì đường "tốt nhất đến giờ" trả lời thẳng, bao
 *  nhiêu núm cũng được.
 *
 *  CỘT GIÁ TRỊ NÚM ĐỨNG TRƯỚC CÁC CHỈ TIÊU. «Sharpe 2.1» mà không biết `rsi_chu_ky`
 *  bằng mấy thì xem để làm gì — màn Optimize của QC không có mấy cột này.
 */

/** Chỉ tiêu LEAN ghi dạng chuỗi («-1.374%», «$362.20») -> số để sắp và để vẽ. */
function so(v: unknown): number | null {
  if (typeof v === 'number') return v
  const s = String(v ?? '').replace(/[$,%\s]/g, '')
  if (!s) return null
  const n = Number(s)
  return Number.isFinite(n) ? n : null
}

export default function TrangToiUu({ ma }: { ma: string }) {
  const [me, setMe] = useState<LuotToiUu | null>(null)
  const [loi, setLoi] = useState('')
  const [dangChay, setDangChay] = useState(false)
  const [sap, setSap] = useState<{ cot: string; xuoi: boolean }>(
    { cot: '', xuoi: false })
  const [td, setTd] = useState<TuDienToiUu | null>(null)
  /** Bày cả 27 cột. KHÔNG giấu gì — chỉ là mặc định gọn, mở ra một nút là thấy hết. */
  const [hetCot, setHetCot] = useState(false)

  useEffect(() => {
    let song = true
    const doc = async () => {
      const r = await pyTu.doc_me()
      if (!song) return
      if (!r.ok || !r.value) { setLoi(r.error ?? 'Không mở được mẻ này.'); return }
      setMe(r.value)
      // CÒN CHẠY THÌ ĐỌC LẠI: lượt nào xong là file của nó đã nằm đó, nên bảng và
      // plot đầy dần. Bắt nhìn màn trống tới lúc hết mẻ thì không ai biết nó còn
      // sống hay đã treo.
      const t = await pyTu.tien_do()
      const dc = !!t.value?.dang_chay
      if (!song) return
      setDangChay(dc)
      if (dc) window.setTimeout(() => void doc(), 1500)
    }
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        setLoi('Không kết nối được tới Python.')
        return
      }
      const t = await pyTu.tu_dien_toi_uu()
      if (song && t.ok && t.value) setTd(t.value)
      await doc()
    })()
    return () => { song = false }
  }, [ma])

  const ds: LuotToiUu['ket_qua'] = me?.ket_qua ?? []
  const mucTieu = me?.cai?.muc_tieu ?? 'Sharpe Ratio'
  const lon = (me?.cai?.huong ?? 'max') === 'max'
  const tenNum = useMemo(
    () => [...new Set(ds.flatMap(r => Object.keys(r.tham_so)))].sort(), [ds])
  /* SÁU CỘT, KHÔNG PHẢI 27. Bày hết thì bảng rộng gấp ba màn hình và phải kéo
     ngang mới thấy cột mình cần. Danh sách do PYTHON khai (`chi_tieu_chinh`) —
     giao diện không tự chọn hộ chỉ tiêu nào là quan trọng.
     Chỉ tiêu ĐANG TÌM luôn đứng đầu, kể cả khi nó không nằm trong sáu cột ấy: quét
     để tìm Sortino mà bảng không có cột Sortino thì xếp hạng theo cái gì. */
  const coSan = useMemo(() => {
    const d = new Set<string>()
    for (const r of ds) for (const k of Object.keys(r.chi_tieu)) d.add(k)
    return d
  }, [ds])
  const tenChiTieu = useMemo(() => {
    if (hetCot) return [...coSan]
    const chinh = td?.chi_tieu_chinh ?? []
    return [...new Set([mucTieu, ...chinh])].filter(c => coSan.has(c))
  }, [coSan, td, hetCot, mucTieu])


  /* PLOT: mỗi lượt một chấm theo thứ tự chạy xong, cộng đường TỐT NHẤT ĐẾN GIỜ. */
  const diem = useMemo(() => {
    const v = ds.map(r => so(r.chi_tieu[mucTieu]))
    const tot: (number | null)[] = []
    let t: number | null = null
    for (const x of v) {
      if (x !== null) t = t === null ? x : (lon ? Math.max(t, x) : Math.min(t, x))
      tot.push(t)
    }
    const co = v.filter((x): x is number => x !== null)
    const min = co.length ? Math.min(...co) : 0
    const max = co.length ? Math.max(...co) : 1
    return { v, tot, min, max: max === min ? min + 1 : max }
  }, [ds, mucTieu, lon])

  const bang = useMemo(() => {
    if (!sap.cot) return ds
    return [...ds].sort((a, b) => {
      const x = so(a.chi_tieu[sap.cot] ?? a.tham_so[sap.cot])
      const y = so(b.chi_tieu[sap.cot] ?? b.tham_so[sap.cot])
      if (x === null && y === null) return 0
      if (x === null) return 1
      if (y === null) return -1
      return sap.xuoi ? x - y : y - x
    })
  }, [ds, sap])

  const bamCot = (c: string) =>
    setSap(s => s.cot === c ? { cot: c, xuoi: !s.xuoi } : { cot: c, xuoi: false })

  const W = 1000, H = 220, L = 52, R = 14, T = 12, B = 26
  const x = (i: number) => L + (ds.length < 2 ? 0
    : (i * (W - L - R)) / (ds.length - 1))
  const y = (v: number) => T + (H - T - B) * (1 - (v - diem.min)
    / (diem.max - diem.min))

  return (
    <div className="cua-so-kq">
      <TitleBar tieuDe={me ? `Optimize · ${me.ten_lop ?? ''}` : 'Optimize'}
                menus={[]} />
      {loi && <div className="mc-bao loi kq-loi">⚠ {loi}</div>}
      {!me && !loi && <div className="kq-cho"><Icon name="chay" /> đang mở mẻ…</div>}

      {me && (
        <div className="tu-than">
          <div className="tu-dau">
            <b>{ds.length}</b> lượt xong
            {me.so_luot ? <> / {me.so_luot}</> : null}
            <span className="tu-cham">·</span>
            tìm <b>{mucTieu}</b> {lon ? 'lớn nhất' : 'nhỏ nhất'}
            {dangChay && <span className="tu-dang"><Icon name="chay" /> đang chạy…</span>}
            <button className="nut-nho tu-cot-nut" onClick={() => setHetCot(v => !v)}>
              {hetCot ? 'cột chính' : `tất cả ${coSan.size} cột`}
            </button>
          </div>

          {/* ───── 1. PLOT ───── */}
          <div className="tu-plot">
            <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
              <line x1={L} y1={T} x2={L} y2={H - B} className="tu-truc" />
              <line x1={L} y1={H - B} x2={W - R} y2={H - B} className="tu-truc" />
              <text x={L - 7} y={T + 9} className="tu-so" textAnchor="end">
                {diem.max.toFixed(2)}</text>
              <text x={L - 7} y={H - B} className="tu-so" textAnchor="end">
                {diem.min.toFixed(2)}</text>
              {diem.tot.some(v => v !== null) && (
                <polyline className="tu-duong-tot" points={diem.tot
                  .map((v, i) => v === null ? '' : `${x(i)},${y(v)}`)
                  .filter(Boolean).join(' ')} />
              )}
              {diem.v.map((v, i) => v === null ? null : (
                <circle key={i} cx={x(i)} cy={y(v)} r={3} className="tu-cham-diem">
                  <title>{`lượt ${i + 1} · ${mucTieu} ${v}`}</title>
                </circle>
              ))}
            </svg>
            <div className="tu-chu-thich">
              <span className="tu-ky-hieu diem" /> mỗi lượt
              <span className="tu-ky-hieu duong" /> tốt nhất đến giờ
            </div>
          </div>

          {/* ───── 2. BẢNG XẾP HẠNG ───── */}
          <div className="tu-bang">
            <table>
              <thead>
                <tr>
                  <th className="tu-stt">#</th>
                  {tenNum.map(c => (
                    <th key={c} className={'tu-cot-num'
                      + (sap.cot === c ? ' sap' : '')}
                        onClick={() => bamCot(c)}>
                      {c}{sap.cot === c && (sap.xuoi ? ' ▲' : ' ▼')}
                    </th>
                  ))}
                  {tenChiTieu.map(c => (
                    <th key={c} className={sap.cot === c ? 'sap' : ''}
                        onClick={() => bamCot(c)}>
                      {c}{sap.cot === c && (sap.xuoi ? ' ▲' : ' ▼')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {bang.map((r, i) => (
                  <tr key={r.id}>
                    <td className="tu-stt">{i + 1}</td>
                    {tenNum.map(c => (
                      <td key={c} className="tu-cot-num">{r.tham_so[c] ?? ''}</td>
                    ))}
                    {tenChiTieu.map(c => (
                      <td key={c}>{r.chi_tieu[c] ?? ''}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
