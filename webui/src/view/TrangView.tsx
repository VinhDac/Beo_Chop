import { useEffect, useMemo, useRef, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { cho_cau_noi, py } from '../api'
import type { KetQuaChay } from '../types'
import { tr, trx, useNgonNgu } from '../ngon_ngu'
import DoThiNen from './DoThiNen'
import NhatKy from './NhatKy'
import type { KieuVe } from './DoThiNen'
import { dsMaCuaLuot, dungMachView } from './mach_view'

/** CỬA SỔ VIEW — xem lại một lượt đã chạy, nến từng nến.
 *
 *  VÌ SAO CÓ CỬA SỔ NÀY. Bảng Kết quả nói lượt chạy ấy LÃI BAO NHIÊU; nó không nói
 *  được LÚC ẤY MÁY THẤY GÌ. Lệnh mua ngày 2012-05-09 đặt ở 1583 — vì RSI bằng mấy?
 *  giá đang ở đâu trong cái nêm ấy? Muốn trả lời thì phải tua lại từng nến, và nhìn
 *  đúng mấy con số cỗ máy đọc tại nến đó. Đó là cả nội dung cửa sổ này.
 *
 *  ⚠ KHÔNG TÍNH GÌ. Mọi con số ở đây đều do LEAN in ra lúc chạy — `sinh_ma._dong_bay`
 *  bảo nó in, `mach_view` xếp lại. App vẫn không tính lấy một con số nào về thị
 *  trường (D-11). Cửa sổ Strategy Tester cũ làm được chuyện này vì nó có engine
 *  riêng; đổi lại, mấy con số nó bày là số CỦA NÓ, không phải số của cỗ máy sẽ chạy
 *  thật. Cửa sổ này bày đúng số LEAN đã dùng để ra quyết định.
 */
export default function TrangView({ ma }: { ma: string }) {
  useNgonNgu()
  const [kq, setKq] = useState<KetQuaChay | null>(null)
  const [loi, setLoi] = useState('')

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        setLoi(tr('Không kết nối được tới Python.'))
        return
      }
      const r = await py.doc_luot_chay(ma)
      // ⚠ ĐỪNG gọi `set_title` ở đây — Python đặt tiêu đề lúc dựng cửa sổ và
      // `_va_khung` tìm cửa sổ THEO TIÊU ĐỀ trong bốn giây. Đổi đúng lúc nó đang
      // tìm là cửa sổ mở ra không khung, không kéo được.
      if (r.ok && r.value) setKq(r.value)
      else setLoi(r.error ?? tr('không đọc được lượt chạy này'))
    })()
  }, [ma])

  return (
    <div className="cua-so-view">
      <TitleBar tieuDe={kq ? tr('View — {0}', kq.ten_lop ?? '') : tr('View')}
                menus={[]} />
      {loi && <div className="mc-bao loi kq-loi">⚠ {loi}</div>}
      {!kq && !loi && (
        <div className="kq-cho">{trx('{0} đang mở lượt chạy…', <Icon name="chay" />)}</div>
      )}
      {kq && <RuotView kq={kq} />}
    </div>
  )
}

/** Tốc độ phát. Ô CHỌN chứ không ba cái nút: cửa sổ Tester cũ cho bảy mức, và cái
 *  khác nhau giữa ×16 với ×32 là có nhìn kịp một đoạn hay không. */
const TOC = [1, 2, 4, 8, 16, 32, 64]

function RuotView({ kq }: { kq: KetQuaChay }) {
  // MỖI MÃ MỘT CUỘN PHIM. LEAN hay chạy cả rổ, nên cửa sổ này phải bày được từng mã
  // — một phiên đang diễn ra trên tám mã thì người xem cần tám cái chart.
  const dsMa = useMemo(() => dsMaCuaLuot(kq), [kq])
  const [ma, setMa] = useState(() => dsMa[0] ?? '')
  const mach = useMemo(() => dungMachView(kq, ma), [kq, ma])
  const het = mach.nhip.length - 1
  /* ⚠ MỞ RA LÀ PHÁT LẠI TỪ ĐẦU, đừng thả con trỏ vào cuối. Đó là cả điểm của cửa sổ
     này — nến lớn dần, lệnh hiện ra đúng lúc. Thả vào cuối thì nó chỉ còn là một
     tấm ảnh chụp, và chính bản Tester cũ đã sửa đúng lỗi ấy một lần rồi. */
  const [i, setI] = useState(0)
  const [chay, setChay] = useState(true)
  /* Tốc độ mặc định tính theo ĐỘ DÀI LƯỢT: chọn mức chậm nhất mà vẫn chạy hết trong
     khoảng hai chục giây. Một con số gõ cứng thì 250 nến xong trong chớp mắt còn
     2000 nến ngồi xem hết một phút rưỡi. */
  const [toc, setToc] = useState(() => {
    const n = Math.max(1, mach.nhip.length)
    return TOC.find(t => (n / Math.max(1, Math.round(t / 8))) * 40 <= 20000) ?? 64
  })
  const [kieu, setKieu] = useState<KieuVe>('nen')
  // TUA. Một nhịp vẽ cho mỗi nến ở ×1; nhanh hơn thì nhảy nhiều nến một nhịp — chứ
  // không phải hẹn giờ ngắn lại, vì dưới ~16ms trình duyệt không chạy nhanh hơn được
  // nữa và tốc độ ×64 sẽ y hệt ×8.
  useEffect(() => {
    if (!chay || het < 0) return
    const id = setInterval(() => {
      setI(x => {
        const sau = x + Math.max(1, Math.round(toc / 8))
        if (sau >= het) { setChay(false); return het }
        return sau
      })
    }, 40)
    return () => clearInterval(id)
  }, [chay, toc, het])

  if (het < 0) {
    return (
      <div className="view-trong">
        {tr('Lượt này không có nến nào. Chạy lại bằng bản mới để LEAN in nến ra.')}
      </div>
    )
  }

  const nhip = mach.nhip[i]
  const ngay = new Date(nhip.t * 1000).toISOString().slice(0, 10)

  /* NHẢY THEO SỰ KIỆN — hai nút đáng giá nhất của cửa sổ Tester cũ.
     Ba năm vàng là 941 nến và chín cái lệnh; kéo thanh đi tìm chín chỗ ấy là việc
     vô ích mà lại dễ trượt. Đây là chỗ người ta muốn tới, nên cho tới thẳng. */
  const moc = useMemo(
    () => mach.nhip.map((n, k) => (n.lenh.length ? k : -1)).filter(k => k >= 0),
    [mach])
  const toiMoc = (xuoi: boolean) => {
    setChay(false)
    const k = xuoi ? moc.find(x => x > i) : [...moc].reverse().find(x => x < i)
    if (k !== undefined) setI(k)
  }
  // Lệnh ĐÃ RA tính tới nhịp này — «đang sống» theo nghĩa người xem đang đứng ở đâu.
  const daRa = mach.lenh.filter(l => {
    const g = Date.parse(String(l.luc).replace(' ', 'T') + 'Z') / 1000
    return g <= nhip.t
  })

  return (
    <div className="view-ruot">
      {/* THANH ĐIỀU KHIỂN — lấy đúng cụm của cửa sổ Tester cũ.
          Hai nút «cả lượt» (Chạy lại · Về cuối) đứng RIÊNG, rồi mới tới năm nút đi
          từng bước quanh chỗ đang đứng. Trộn vào nhau thì cụm phát lại có hai nút
          nhảy cóc nằm lẫn giữa mấy nút đi bộ — chú thích cũ nói đúng chỗ ấy. */}
      <div className="view-thanh">
        <button className="view-nut" onClick={() => { setI(0); setChay(true) }}
                title={tr('Chạy lại từ nến đầu')}>
          <Icon name="chay" /> {tr('Chạy lại')}
        </button>
        <button className="view-nut" onClick={() => { setChay(false); setI(het) }}
                title={tr('Nhảy tới cuối lượt chạy')}>⇥ {tr('Về cuối')}</button>
        <span className="view-ngan" />

        <button className="view-b" onClick={() => toiMoc(false)}
                disabled={!moc.some(x => x < i)}
                title={tr('Về lệnh trước')}>⏮</button>
        <button className="view-b" onClick={() => { setChay(false); setI(x => Math.max(0, x - 1)) }}
                disabled={i <= 0} title={tr('Lùi 1 nến')}>◀</button>
        <button className="view-b rong" onClick={() => setChay(c => !c)}
                title={chay ? tr('Dừng') : tr('Phát')}>{chay ? '❚❚' : '▶'}</button>
        <button className="view-b" onClick={() => { setChay(false); setI(x => Math.min(het, x + 1)) }}
                disabled={i >= het} title={tr('Tới 1 nến')}>▶</button>
        <button className="view-b" onClick={() => toiMoc(true)}
                disabled={!moc.some(x => x > i)}
                title={tr('Tới lệnh kế tiếp')}>⏭</button>

        <select className="view-o" value={toc} title={tr('Tốc độ phát')}
                onChange={e => setToc(Number(e.target.value))}>
          {TOC.map(t => <option key={t} value={t}>{t}×</option>)}
        </select>
        <select className="view-o" value={kieu} title={tr('Kiểu vẽ')}
                onChange={e => setKieu(e.target.value as KieuVe)}>
          <option value="nen">{tr('Nến')}</option>
          <option value="bar">{tr('Thanh')}</option>
          <option value="line">{tr('Đường')}</option>
        </select>
        <span className="view-ngan" />

        <input className="view-keo" type="range" min={0} max={het} value={i}
               onChange={e => { setChay(false); setI(Number(e.target.value)) }} />
        <span className="view-dem">{i + 1}/{het + 1}</span>
        {/* Ô NHẢY TỚI NGÀY. Tách khỏi con số bên cạnh chứ không gộp: lúc phát, chỗ
            kia đổi mấy lần một giây, mà một ô nhập tự đổi dưới tay người đang gõ thì
            không gõ nổi. */}
        <input className="view-o view-ngay-nhay" type="date" value={ngay}
               title={tr('Nhảy tới ngày')}
               onChange={e => {
                 const g = Date.parse(e.target.value + 'T00:00:00Z') / 1000
                 if (!Number.isFinite(g)) return
                 setChay(false)
                 let k = mach.nhip.findIndex(n => n.t >= g)
                 if (k < 0) k = het
                 setI(k)
               }} />
      </div>

      {dsMa.length > 1 && (
        <div className="view-the-ma">
          {dsMa.map(t => (
            <button key={t} className={'view-ma' + (t === ma ? ' chon' : '')}
                    onClick={() => setMa(t)}>{t}</button>
          ))}
        </div>
      )}

      <div className="view-than">
        {/* NẾN + đại lượng cùng thang chồng lên, rồi mỗi đại lượng thang khác
            một KHUNG PHỤ bên dưới — tất cả trong một chart, dùng chung trục thời
            gian. Cuộn chuột để phóng, kéo để đi: của `lightweight-charts`. */}
        <div className="view-cot-do-thi">
          <DoThiNen mach={mach} chiSo={i} kieu={kieu} />
        </div>

        <div className="view-ben">
          <table className="view-bang-so"><tbody>
            <tr><td>{mach.ma}</td>
                <td className="view-gt">{nhip.nen[3].toFixed(2)}</td></tr>
            {mach.so.map(h => (
              <tr key={h.ten}>
                <td title={h.ten}>{h.ten}</td>
                <td className="view-gt">
                  {/* ⚠ «—» KHI LEAN KHÔNG IN. Chỉ báo chưa chín thì LEAN bỏ nhịp ấy;
                      điền đại một con số vào đây là bịa ra thứ cỗ máy chưa từng đọc,
                      đúng ở những nến người ta mở cửa sổ ra để soi. */}
                  {h.gt[i] === null ? '—' : (h.gt[i] as number).toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody></table>

          <NhatKy ds={mach.nhatKy} chiSo={i}
                  nhay={k => { setChay(false); setI(k) }} />
        </div>
      </div>
    </div>
  )
}
