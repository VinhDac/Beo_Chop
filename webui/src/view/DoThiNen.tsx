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
import { useCallback, useEffect, useMemo, useRef } from 'react'
import {
  BarSeries, CandlestickSeries, LineSeries, createChart, createSeriesMarkers,
  type IChartApi, type IPriceLine, type ISeriesApi, type ISeriesMarkersPluginApi,
  type Time, type UTCTimestamp,
} from 'lightweight-charts'
import { tr } from '../ngon_ngu'
import { gopLat, type MachView } from './mach_view'

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

/** NẾN VỀ MÀU XÁM — nút `ve-mau` của cửa sổ Tester cũ.
 *
 *  ⚠ ĐỂ DÀNH XANH/ĐỎ CHO LÃI LỖ. Trên một cái chart đang bày lệnh, xanh và đỏ phải
 *  nói về TIỀN: mũi tên mua, mũi tên bán, lệnh bị sàn từ chối. Mà cây nến cũng xanh
 *  đỏ, nên hai nghĩa ấy tranh nhau đúng một bảng màu — và lúc tìm xem cú mua nào
 *  lỗ thì mắt phải lọc qua chín trăm cây nến cùng màu. Chuyển nến sang hai mức xám
 *  thì vẫn đọc được lên/xuống (nhạt/đậm), mà màu nóng còn lại đúng một nghĩa.
 *
 *  ⚠ HAI MỨC NÀY PHẢI ĐỦ SÁNG TRÊN NỀN. Bản đầu lấy #8d8d8d với #4a4a4a: nến giảm
 *  gần như tan vào nền #0e0e0e, nên bật nút lên là mất hẳn một nửa số nến. Nhìn ảnh
 *  chụp mới thấy — đo bằng JS thì hai màu ấy vẫn «có đặt», vẫn khác nhau, vẫn đúng. */
const XAM_LEN = '#c8c8c8'
const XAM_XUONG = '#6e6e6e'

export interface DoThiNenProps {
  mach: MachView
  /** Mốc thời gian con trỏ đang đứng (giây UNIX) — nến sau đó CHƯA xảy ra.
   *
   *  ⚠ MỐC, KHÔNG PHẢI SỐ THỨ TỰ NẾN. Một lượt chạy trên năm chục mã thì mỗi mã một
   *  dãy nến dài ngắn khác nhau (rổ động: mã vào giữa chừng), nên «nến thứ 42» của
   *  mã này và của mã kia là hai thời điểm khác nhau. Con trỏ phải là MỘT mốc chung,
   *  rồi mã nào tự tìm nến của mình tới mốc ấy. */
  tToi: number
  kieu: KieuVe
  /** KHUNG HIỂN THỊ: gộp bao nhiêu giây vào một cây nến. 0 = nến gốc, không gộp.
   *  Chỉ đổi CÁCH VẼ — xem `mach_view.gopLat`. */
  giay?: number
  /** Nến về hai mức xám — xem `XAM_LEN`. */
  mauThuong?: boolean
  /** Hiện mũi tên lệnh và mức giá lệnh chờ. Tắt để nhìn riêng hình dáng giá. */
  hienLenh?: boolean
  /** ĐẾM SỐ LẦN BẤM «Về nến hiện tại». Tăng lên là kéo màn hình về mép phải.
   *
   *  ⚠ ĐẾM LẦN, KHÔNG PHẢI MỘT CỜ BẬT/TẮT. Bấm nút hai lần liền (kéo lệch, bấm về,
   *  kéo lệch nữa, bấm về) thì một cái cờ `true` không đổi giá trị ở lần thứ hai —
   *  nhìn y như bấm hụt. Cùng lối với `epLan` của bảng dưới cửa sổ Tester cũ. */
  veNay?: number
  /** Người xem đã tự kéo/phóng chưa — để thanh công cụ bật/tắt nút «Về nến hiện tại».
   *  Một nút sáng thường trực là một nút chết. */
  onLech?: (lech: boolean) => void
  /** GỌN = một ô trong lưới: bỏ trục, bỏ khung phụ, bỏ dấu lệnh có chữ. Lưới để
   *  LIẾC, không để đọc; nhét đủ thứ vào một ô 200px thì không còn nhìn ra hình
   *  dáng nào cả — mà nhìn ra hình dáng chính là việc của cái lưới. */
  gon?: boolean
}

export default function DoThiNen({ mach, tToi, kieu, giay = 0, mauThuong, hienLenh = true,
                                   veNay = 0, onLech, gon }: DoThiNenProps) {
  const boc = useRef<HTMLDivElement>(null)
  const chart = useRef<IChartApi | null>(null)
  const nen = useRef<ISeriesApi<'Candlestick' | 'Bar' | 'Line'> | null>(null)
  const dau = useRef<ISeriesMarkersPluginApi<Time> | null>(null)
  const chong = useRef<ISeriesApi<'Line'>[]>([])
  const phu = useRef<ISeriesApi<'Line'>[]>([])
  const mucCho = useRef<IPriceLine[]>([])
  /** Người xem đã tự kéo/phóng chưa. Rồi thì đừng kéo màn hình theo con trỏ nữa —
   *  giật cái nhìn của người đang soi là cách chắc nhất làm họ mất chỗ.
   *
   *  ⚠ ĐO BẰNG CHUỘT THẬT, KHÔNG NGHE `subscribeVisibleLogicalRangeChange`. Bản đầu
   *  nghe cái đó, mà nó nổ cả khi CHÍNH TA đổ dữ liệu vào (`setData`) — nên ngay
   *  nhịp đầu nó đã tưởng người xem vừa kéo, và từ đó chart không bao giờ chạy theo
   *  con trỏ nữa: tua thì nến mọc dần ở ngoài mép phải, màn hình đứng im. Cú nhấn
   *  chuột và cú cuộn trên chính cái khung thì không nhập nhằng được với ai. */
  const daKeo = useRef(false)
  /** Số nhịp lượt vẽ gần nhất bày ra — nút «Về nến hiện tại» cần nó để xếp lại. */
  const soNhip = useRef(0)

  const soKhungPhu = mach.so.length

  // ---------------- dựng chart: một lần cho mỗi bộ (kiểu vẽ, số khung phụ) --------
  useEffect(() => {
    const el = boc.current
    if (!el) return
    const c = createChart(el, {
      layout: { background: { color: mau('--bg', '#0e0e0e') }, textColor: mau('--muted'),
                // Logo thư viện: giữ ở bản TO (ghi công đúng chỗ nhìn thấy được),
                // bỏ ở ô lưới — hai chục ô là hai chục cái logo, che mất chính cái
                // hình dáng mà lưới sinh ra để cho thấy.
                attributionLogo: !gon,
                panes: { separatorColor: mau('--border'), separatorHoverColor: mau('--raised') } },
      grid: { vertLines: { color: mau('--border-soft') },
              horzLines: { color: mau('--border-soft') } },
      rightPriceScale: { borderColor: mau('--border'), visible: !gon },
      timeScale: { borderColor: mau('--border'), timeVisible: false, rightOffset: 6,
                   visible: !gon },
      crosshair: { mode: 0 },
      handleScroll: !gon, handleScale: !gon,
      autoSize: true,
    })
    chart.current = c

    const s = kieu === 'line'
      ? c.addSeries(LineSeries, { lineWidth: 2, priceLineVisible: false })
      : kieu === 'bar' ? c.addSeries(BarSeries, {})
                       : c.addSeries(CandlestickSeries, {})
    nen.current = s
    dau.current = createSeriesMarkers<Time>(s, [])

    chong.current = mach.chong.map((_, k) =>
      c.addSeries(LineSeries, { color: MAU_CHONG[k % MAU_CHONG.length], lineWidth: 1,
                                priceLineVisible: false, lastValueVisible: false }))

    // Mỗi đại lượng THANG KHÁC một khung riêng bên dưới — `addPane` dùng chung trục
    // thời gian, nên kéo một khung là cả chồng khung chạy theo.
    phu.current = gon ? [] : mach.so.map((h, k) => {
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
  }, [kieu, soKhungPhu, mach, gon])

  /* MÀU NẾN — đổi bằng `applyOptions`, KHÔNG dựng lại chart.
   *
   * ⚠ ĐÃ HỎNG THẬT MỘT LẦN THEO LỐI KIA. Bản đầu nhét `mauThuong` vào danh sách phụ
   * thuộc của lượt DỰNG chart: bấm nút là chart bị tháo và lắp lại, mà lượt ĐỔ DỮ
   * LIỆU thì không nghe `mauThuong` nên nó không chạy lại — kết quả là một cái chart
   * TRẮNG TRƠN. Nhìn ảnh chụp mới thấy; đo bằng JS thì phần tử vẫn còn, cỡ vẫn đúng,
   * màu vẫn đặt. Và dựng lại chart còn ném mất cả mức phóng người xem vừa kéo. */
  useEffect(() => {
    const s = nen.current
    if (!s) return
    if (kieu === 'line') {
      s.applyOptions({ color: mauThuong ? XAM_LEN : mau('--muted') })
      return
    }
    const len = mauThuong ? XAM_LEN : mau('--ok', '#22ab94')
    const xuong = mauThuong ? XAM_XUONG : mau('--err', '#f23645')
    s.applyOptions(kieu === 'bar'
      ? { upColor: len, downColor: xuong }
      : { upColor: len, downColor: xuong,
          borderUpColor: len, borderDownColor: xuong,
          wickUpColor: len, wickDownColor: xuong })
  }, [mauThuong, kieu])

  /* NGƯỜI XEM ĐÃ CHẠM VÀO CHƯA. Ô lưới không bắt (nó đã tắt kéo/phóng), nên một cú
     bấm để mở to không bị tính là «đã kéo». */
  useEffect(() => {
    const el = boc.current
    if (!el || gon) return
    const cham = () => {
      if (daKeo.current) return
      daKeo.current = true
      onLech?.(true)
    }
    el.addEventListener('mousedown', cham)
    el.addEventListener('wheel', cham, { passive: true })
    return () => {
      el.removeEventListener('mousedown', cham)
      el.removeEventListener('wheel', cham)
    }
  }, [gon, onLech])

  /** BỀ RỘNG MỘT CÂY NẾN rồi ghim mép phải — cách chart tự xếp lại khi nó còn đang
   *  bám con trỏ.
   *
   *  ⚠ KHÔNG ĐỂ `lightweight-charts` TỰ LO. Nó giữ bề rộng nến cố định (6px) rồi ghim
   *  mép phải, nên một lượt 42 nến trên chart rộng 900px bày ra đúng 250px nến và BA
   *  PHẦN TƯ MÀN HÌNH TRỐNG bên trái — nhìn như chart hỏng. Đã thấy tận mắt.
   *
   *  ⚠ VÀ KHÔNG DÙNG `fitContent` THAY. Nó ép CẢ dãy vào bề ngang, nên một lượt 941
   *  nến ra những cây nến mỏng 1px — còn tệ hơn. Nên: lấp đầy bề ngang, nhưng không
   *  bao giờ mỏng hơn 2px hay dày hơn 16px một cây; vượt ngưỡng dưới thì nến cũ trôi
   *  ra khỏi mép trái, đúng cảm giác tua lại của cửa sổ Tester cũ. */
  const xepLai = useCallback((n: number) => {
    const c = chart.current
    if (!c) return
    const rong = boc.current?.clientWidth ?? 0
    if (rong > 0 && n > 0) {
      c.timeScale().applyOptions({ barSpacing: Math.min(16, Math.max(2, rong / (n + 8))) })
    }
    c.timeScale().scrollToRealTime()
  }, [])

  /* «VỀ NẾN HIỆN TẠI» — thôi bám tay người xem, bám lại mép phải.
   *
   * ⚠ PHẢI XẾP LẠI CẢ BỀ RỘNG NẾN, không chỉ kéo về mép phải. Bản đầu chỉ gọi
   * `scrollToRealTime`: bấm nút xong thì nút tắt đi (đúng) mà cái chart vẫn y nguyên
   * mức phóng vừa cuộn (sai) — tức một cái nút báo đã làm xong một việc nó chưa làm.
   * Nhìn ảnh chụp trước/sau mới thấy.
   *
   * Bỏ qua lần dựng đầu (`veNay` 0) để nó không đè lên lượt vẽ đầu tiên. */
  useEffect(() => {
    if (!veNay) return
    daKeo.current = false
    onLech?.(false)
    xepLai(soNhip.current)
  }, [veNay, onLech, xepLai])

  // ---------------- đổ dữ liệu TỚI NHỊP ĐANG ĐỨNG -------------------------------
  const lat = useMemo(() => gopLat(mach, tToi, giay), [mach, tToi, giay])

  useEffect(() => {
    const s = nen.current
    if (!s) return
    const t = (x: number) => x as UTCTimestamp
    s.setData(kieu === 'line'
      ? lat.nhip.map(n => ({ time: t(n.t), value: n.nen[3] })) as never
      : lat.nhip.map(n => ({ time: t(n.t), open: n.nen[0], high: n.nen[1],
                             low: n.nen[2], close: n.nen[3] })) as never)

    chong.current.forEach((ds, k) => {
      const gt = lat.chong[k] ?? []
      ds.setData(lat.nhip.map((n, i) => ({ time: t(n.t), value: gt[i] }))
        .filter(p => p.value !== null && p.value !== undefined) as never)
    })
    phu.current.forEach((ds, k) => {
      const gt = lat.so[k] ?? []
      ds.setData(lat.nhip.map((n, i) => ({ time: t(n.t), value: gt[i] }))
        .filter(p => p.value !== null && p.value !== undefined) as never)
    })

    // DẤU LỆNH — ở đúng nến và đúng phía. Mua thì tam giác dưới nến, bán thì trên:
    // đọc hướng từ phía mũi tên nhắm tới, thẳng hơn một cái nhãn chữ.
    dau.current?.setMarkers(!hienLenh ? [] : lat.nhip.flatMap(n => n.lenh.map(l => ({
      time: t(n.t),
      position: Number(l.so_luong) > 0 ? 'belowBar' as const : 'aboveBar' as const,
      color: l.hop_le ? (Number(l.so_luong) > 0 ? mau('--ok', '#22ab94')
                                                : mau('--err', '#f23645'))
                      : mau('--dim', '#636363'),
      shape: Number(l.so_luong) > 0 ? 'arrowUp' as const : 'arrowDown' as const,
      text: gon ? '' : (l.tag || String(l.gia)),
    }))))

    // MỨC GIÁ LỆNH CÒN TREO. Cam, và cam chỉ làm đúng việc này: mức duy nhất chưa
    // có tốt hay xấu. Dựng lại mỗi nhịp vì lệnh treo rồi hết treo.
    for (const m of mucCho.current) { try { s.removePriceLine(m) } catch { /* đã gỡ */ } }
    mucCho.current = !hienLenh ? []
      : (lat.nhip[lat.nhip.length - 1]?.cho ?? []).map(l => s.createPriceLine({
          price: Number(l.gia), color: mau('--accent', '#ffa657'),
          lineWidth: 1, lineStyle: 2, axisLabelVisible: true,
          title: tr(l.loai),
        }))

    // Số nhịp đang bày, giữ lại cho nút «Về nến hiện tại» — nó bấm ngoài lượt này.
    soNhip.current = lat.nhip.length
    if (!daKeo.current) xepLai(lat.nhip.length)
  }, [lat, kieu, mach, gon, hienLenh, xepLai])

  return <div className="view-khung-chart" ref={boc} />
}
