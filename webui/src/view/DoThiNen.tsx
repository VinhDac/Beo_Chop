/* BIỂU ĐỒ của cửa sổ View — dựng trên `lightweight-charts`, đúng thư viện cửa sổ
 * Strategy Tester cũ đã dùng.
 *
 * ⚠ VÌ SAO KHÔNG TỰ VẼ SVG. Bản đầu tôi vẽ tay: nến thì ra, nhưng CUỘN CHUỘT ĐỂ
 * PHÓNG không có, kéo ngang không có, crosshair không có, trục thời gian không có.
 * Mấy thứ ấy không phải phần trang trí — chúng LÀ cách người ta đọc một cái chart
 * giá. Thư viện này cho cả cụm, và nó vốn đã nằm sẵn trong dự án; viết lại một bản
 * mỏng hơn là vứt đi thứ có sẵn rồi làm ra một cái chart không dùng được.
 *
 * ⚠ KHUNG PHỤ LÀ `pane` CỦA CHÍNH NÓ, không phải một cái chart thứ hai. Chart thứ
 * hai thì trục thời gian hai bên trôi khác nhau, và phải tự đồng bộ — mà đồng bộ
 * trục thời gian của hai chart là một trong những chỗ dễ lệch nhất. `addPane` thì
 * cùng một trục, miễn phí.
 */
import { useEffect, useMemo, useRef } from 'react'
import {
  BarSeries, CandlestickSeries, LineSeries, createChart, createSeriesMarkers,
  type IChartApi, type IPriceLine, type ISeriesApi, type ISeriesMarkersPluginApi,
  type Time, type UTCTimestamp,
} from 'lightweight-charts'
import type { MachView } from './mach_view'

/** Ba kiểu vẽ của cửa sổ Tester cũ — nến, thanh, đường. */
export type KieuVe = 'nen' | 'bar' | 'line'

/** Màu cho đại lượng vẽ chồng lên nến. Cố ý KHÔNG dùng xanh/đỏ: hai màu ấy đã mang
 *  nghĩa lên/xuống trên chính cây nến, mượn lại là một đường trung bình trượt trông
 *  như đang nói điều gì đó về lãi lỗ. */
const MAU_CHONG = ['#6aa5f5', '#ffa657', '#c792ea', '#80cbc4']

/** Lấy màu từ biến CSS của app — để chart không có bảng màu thứ hai. */
function mau(ten: string, dp = '#888') {
  return getComputedStyle(document.documentElement).getPropertyValue(ten).trim() || dp
}

export interface DoThiNenProps {
  mach: MachView
  /** Nến đang đứng — nến sau đó CHƯA xảy ra, nên chưa vẽ. */
  chiSo: number
  kieu: KieuVe
}

export default function DoThiNen({ mach, chiSo, kieu }: DoThiNenProps) {
  const boc = useRef<HTMLDivElement>(null)
  const chart = useRef<IChartApi | null>(null)
  const nen = useRef<ISeriesApi<'Candlestick' | 'Bar' | 'Line'> | null>(null)
  const dau = useRef<ISeriesMarkersPluginApi<Time> | null>(null)
  const chong = useRef<ISeriesApi<'Line'>[]>([])
  const phu = useRef<ISeriesApi<'Line'>[]>([])
  const mucCho = useRef<IPriceLine[]>([])
  /** Người xem đã tự kéo/phóng chưa. Rồi thì đừng kéo màn hình theo con trỏ nữa —
   *  giật cái nhìn của người đang soi là cách chắc nhất làm họ mất chỗ. */
  const daKeo = useRef(false)

  const soKhungPhu = mach.so.length

  // ---------------- dựng chart: một lần cho mỗi bộ (kiểu vẽ, số khung phụ) --------
  useEffect(() => {
    const el = boc.current
    if (!el) return
    const c = createChart(el, {
      layout: { background: { color: mau('--bg', '#0e0e0e') }, textColor: mau('--muted'),
                panes: { separatorColor: mau('--border'), separatorHoverColor: mau('--raised') } },
      grid: { vertLines: { color: mau('--border-soft') },
              horzLines: { color: mau('--border-soft') } },
      rightPriceScale: { borderColor: mau('--border') },
      timeScale: { borderColor: mau('--border'), timeVisible: false, rightOffset: 6 },
      crosshair: { mode: 0 },
      autoSize: true,
    })
    chart.current = c
    c.timeScale().subscribeVisibleLogicalRangeChange(() => { daKeo.current = true })

    const s = kieu === 'line'
      ? c.addSeries(LineSeries, { color: mau('--muted'), lineWidth: 2,
                                  priceLineVisible: false })
      : kieu === 'bar' ? c.addSeries(BarSeries, {})
                       : c.addSeries(CandlestickSeries, {})
    nen.current = s
    dau.current = createSeriesMarkers<Time>(s, [])

    chong.current = mach.chong.map((_, k) =>
      c.addSeries(LineSeries, { color: MAU_CHONG[k % MAU_CHONG.length], lineWidth: 1,
                                priceLineVisible: false, lastValueVisible: false }))

    // Mỗi đại lượng THANG KHÁC một khung riêng bên dưới — `addPane` dùng chung trục
    // thời gian, nên kéo một khung là cả chồng khung chạy theo.
    phu.current = mach.so.map((h, k) => {
      c.addPane()
      return c.addSeries(LineSeries, {
        color: MAU_CHONG[k % MAU_CHONG.length], lineWidth: 1, title: h.ten,
        priceLineVisible: false,
      }, k + 1)
    })

    daKeo.current = false
    return () => {
      c.remove()
      chart.current = null; nen.current = null; dau.current = null
      chong.current = []; phu.current = []; mucCho.current = []
    }
  }, [kieu, soKhungPhu, mach])

  // ---------------- đổ dữ liệu TỚI NHỊP ĐANG ĐỨNG -------------------------------
  const lat = useMemo(
    () => mach.nhip.slice(0, Math.max(1, chiSo + 1)), [mach, chiSo])

  useEffect(() => {
    const s = nen.current
    if (!s) return
    const t = (x: number) => x as UTCTimestamp
    s.setData(kieu === 'line'
      ? lat.map(n => ({ time: t(n.t), value: n.nen[3] })) as never
      : lat.map(n => ({ time: t(n.t), open: n.nen[0], high: n.nen[1],
                        low: n.nen[2], close: n.nen[3] })) as never)

    chong.current.forEach((ds, k) => {
      const h = mach.chong[k]
      ds.setData(lat.map((n, i) => ({ time: t(n.t), value: h.gt[i] }))
        .filter(p => p.value !== null && p.value !== undefined) as never)
    })
    phu.current.forEach((ds, k) => {
      const h = mach.so[k]
      ds.setData(lat.map((n, i) => ({ time: t(n.t), value: h.gt[i] }))
        .filter(p => p.value !== null && p.value !== undefined) as never)
    })

    // DẤU LỆNH — ở đúng nến và đúng phía. Mua thì tam giác dưới nến, bán thì trên:
    // đọc hướng từ phía mũi tên nhắm tới, thẳng hơn một cái nhãn chữ.
    dau.current?.setMarkers(lat.flatMap(n => n.lenh.map(l => ({
      time: t(n.t),
      position: Number(l.so_luong) > 0 ? 'belowBar' as const : 'aboveBar' as const,
      color: l.hop_le ? (Number(l.so_luong) > 0 ? mau('--ok', '#22ab94')
                                                : mau('--err', '#f23645'))
                      : mau('--dim', '#636363'),
      shape: Number(l.so_luong) > 0 ? 'arrowUp' as const : 'arrowDown' as const,
      text: l.tag || String(l.gia),
    }))))

    // MỨC GIÁ LỆNH CÒN TREO. Cam, và cam chỉ làm đúng việc này: mức duy nhất chưa
    // có tốt hay xấu. Dựng lại mỗi nhịp vì lệnh treo rồi hết treo.
    for (const m of mucCho.current) { try { s.removePriceLine(m) } catch { /* đã gỡ */ } }
    mucCho.current = (lat[lat.length - 1]?.cho ?? []).map(l => s.createPriceLine({
      price: Number(l.gia), color: mau('--accent', '#ffa657'),
      lineWidth: 1, lineStyle: 2, axisLabelVisible: true,
      title: l.loai,
    }))

    if (!daKeo.current) chart.current?.timeScale().scrollToRealTime()
  }, [lat, kieu, mach])

  return <div className="view-khung-chart" ref={boc} />
}
