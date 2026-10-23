import { useCallback, useEffect, useMemo, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import BangDuoi from '../components/BangDuoi'
import { RuotKetQua } from '../components/HopKetQua'
import { cho_cau_noi, py } from '../api'
import type { DongLenh, KetQuaChay } from '../types'
import { tr, trx, useNgonNgu } from '../ngon_ngu'
import DoThiNen from './DoThiNen'
import type { KieuVe } from './DoThiNen'
import NhatKy from './NhatKy'
import SoDoSoi from './SoDoSoi'
import { dungLuot, dungMachView, soLieuTai } from './mach_view'
import type { DongNhatKy, MachView } from './mach_view'

/** CỬA SỔ VIEW — xem lại một lượt đã chạy, nến từng nến.
 *
 *  VÌ SAO CÓ CỬA SỔ NÀY. Bảng Kết quả nói lượt chạy ấy LÃI BAO NHIÊU; nó không nói
 *  được LÚC ẤY MÁY THẤY GÌ. Lệnh mua ngày 2012-05-09 đặt ở 1603 — vì RSI bằng mấy?
 *  giá đang ở đâu? Muốn trả lời thì phải tua lại từng nến và nhìn đúng mấy con số cỗ
 *  máy đọc tại nến đó.
 *
 *  ⚠ KHÔNG TÍNH GÌ. Mọi con số đều do LEAN in ra lúc chạy — `sinh_ma._dong_bay` bảo
 *  nó in nến và đại lượng, `sinh_ma._ham_vet` bảo nó kể mỗi nhịp dừng ở cổng nào, rồi
 *  `mach_view` xếp lại. App vẫn không tính lấy một con số nào về thị trường (D-11).
 *  Cửa sổ Tester cũ làm được chuyện này vì nó có engine riêng; đổi lại, mấy con số nó
 *  bày là số CỦA NÓ, không phải số của cỗ máy sẽ chạy thật.
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

/** KHUNG HIỂN THỊ — `[nhãn, số giây]`. Ô chọn chỉ bày khung LỚN HƠN bước nhịp gốc của
 *  lượt chạy: gộp năm cây nến làm một thì được, chẻ một cây nến ra làm năm thì không
 *  ai làm được, và bày một mục bấm vào chẳng đổi gì là một mục chết. */
const KHUNG: [string, number][] = [
  ['M5', 300], ['M15', 900], ['M30', 1800], ['H1', 3600], ['H4', 14400],
  ['D1', 86400], ['W1', 604800],
]

function RuotView({ kq }: { kq: KetQuaChay }) {
  /* MỘT LƯỢT CHẠY LÀ MỘT, dù nó chạy trên năm chục mã: trục thời gian và nhật ký là
     của CẢ LƯỢT. Chỉ chart mới theo từng mã — xem `mach_view`. */
  const luot = useMemo(() => dungLuot(kq), [kq])
  const het = luot.truc.length - 1

  /* ⚠ MỞ RA LÀ PHÁT LẠI TỪ ĐẦU, đừng thả con trỏ vào cuối. Đó là cả điểm của cửa sổ
     này — nến lớn dần, lệnh hiện ra đúng lúc. Thả vào cuối thì nó chỉ còn là một tấm
     ảnh chụp, và chính bản Tester cũ đã sửa đúng lỗi ấy một lần rồi. */
  const [i, setI] = useState(0)
  const [chay, setChay] = useState(true)
  /* Tốc độ mặc định tính theo ĐỘ DÀI LƯỢT: chọn mức chậm nhất mà vẫn chạy hết trong
     khoảng hai chục giây. Một con số gõ cứng thì 250 nến xong trong chớp mắt còn
     2000 nến ngồi xem hết một phút rưỡi. */
  const [toc, setToc] = useState(() => {
    const n = Math.max(1, luot.truc.length)
    return TOC.find(t => (n / Math.max(1, Math.round(t / 8))) * 40 <= 20000) ?? 64
  })
  const [kieu, setKieu] = useState<KieuVe>('nen')
  /** Khung hiển thị: 0 = nến gốc. */
  const [khung, setKhung] = useState(0)
  const [mauThuong, setMauThuong] = useState(false)
  const [hienLenh, setHienLenh] = useState(true)
  /** Mã đang MỞ TO, hay null = đang nhìn cả lưới. */
  const [to, setTo] = useState<string | null>(null)
  /** Dòng nhật ký đang soi trên sơ đồ — popup. */
  const [soi, setSoi] = useState<DongNhatKy | null>(null)

  /* BẢNG DƯỚI — chiều cao, tab, gập. Giữ ở đây chứ không trong `BangDuoi`: cái vỏ ấy
     là vỏ DÙNG CHUNG với cửa sổ chính, nó nhận trạng thái từ ngoài. */
  const [tab, setTab] = useState('nk')
  const [cao, setCao] = useState(230)
  const [gap, setGap] = useState(false)

  /* «VỀ NẾN HIỆN TẠI»: đếm lần bấm, và nghe chart báo đã lệch chưa — xem
     `DoThiNen.veNay`. `useCallback` vì `DoThiNen` gắn/tháo bộ nghe chuột theo nó. */
  const [veNay, setVeNay] = useState(0)
  const [lech, setLech] = useState(false)
  const onLech = useCallback((v: boolean) => setLech(v), [])

  // TUA. Một nhịp vẽ cho mỗi nến ở ×8; nhanh hơn thì nhảy nhiều nến một nhịp — chứ
  // không phải hẹn giờ ngắn lại, vì dưới ~16ms trình duyệt không chạy nhanh hơn được
  // nữa và ×64 sẽ y hệt ×8.
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

  const tToi = luot.truc[i]
  const ngay = new Date(tToi * 1000).toISOString().slice(0, 10)

  /* NHẢY THEO SỰ KIỆN — hai nút đáng giá nhất của cửa sổ Tester cũ. Ba năm vàng là
     941 nến và chín cái lệnh; kéo thanh đi tìm chín chỗ ấy là việc vô ích mà lại dễ
     trượt. Đây là chỗ người ta muốn tới, nên cho tới thẳng.
     ⚠ CHỈ NHẢY THEO LỆNH, không nhảy theo dòng tường thuật: vết ghi gần như mỗi nhịp
     một dòng, nên ⏭ sẽ thành một cái nút «tới 1 nến» thứ hai. */
  const mocLenh = () => luot.nhatKy.filter(d => d.viec).map(d => d.t)
  const toiMoc = (xuoi: boolean) => {
    setChay(false)
    const moc = mocLenh()
    const t = xuoi ? moc.find(x => x > tToi) : [...moc].reverse().find(x => x < tToi)
    if (t === undefined) return
    const k = luot.truc.findIndex(x => x >= t)
    if (k >= 0) setI(k)
  }
  const coMoc = (xuoi: boolean) =>
    luot.nhatKy.some(d => d.viec && (xuoi ? d.t > tToi : d.t < tToi))

  /** Nhảy tới một mốc, và mở to mã của dòng ấy — bấm một dòng nhật ký là đang hỏi
   *  «cái này ở đâu ra», nên đưa thẳng tới chỗ nó xảy ra. Dòng nói hộ nhiều mã thì
   *  KHÔNG mở to mã nào: nó không thuộc mã nào cả. */
  const nhayToi = (t: number, maDong: string) => {
    setChay(false)
    const k = luot.truc.findIndex(x => x >= t)
    if (k >= 0) setI(k)
    if (maDong && luot.dsMa.includes(maDong)) setTo(maDong)
  }

  /** Khung hiển thị bày được — xem `KHUNG`. */
  const khungDuoc = KHUNG.filter(([, g]) => g > luot.buoc)

  const nutBat = (icon: string, ten: string, on: () => void, bat: boolean, tat = false) => (
    <button className={'view-b' + (bat ? ' bat' : '')} title={ten}
            disabled={tat} onClick={on}><Icon name={icon} size={14} /></button>
  )

  const soLenh = luot.nhatKy.filter(d => d.t <= tToi && d.viec).length

  return (
    <div className="view-ruot">
      {/* THANH ĐIỀU KHIỂN — lấy đúng cụm của cửa sổ Tester cũ. Hai nút «cả lượt»
          (Chạy lại · Về cuối) đứng RIÊNG, rồi mới tới năm nút đi từng bước quanh chỗ
          đang đứng. Trộn vào nhau thì cụm phát lại có hai nút nhảy cóc nằm lẫn giữa
          mấy nút đi bộ. */}
      <div className="view-thanh">
        <button className="view-nut" onClick={() => { setI(0); setChay(true) }}
                title={tr('Chạy lại từ nến đầu')}>
          <Icon name="chay" /> {tr('Chạy lại')}
        </button>
        <button className="view-nut" onClick={() => { setChay(false); setI(het) }}
                title={tr('Nhảy tới cuối lượt chạy')}>⇥ {tr('Về cuối')}</button>
        <span className="view-ngan" />

        <button className="view-b" onClick={() => toiMoc(false)}
                disabled={!coMoc(false)} title={tr('Về lệnh trước')}>⏮</button>
        <button className="view-b" onClick={() => { setChay(false); setI(x => Math.max(0, x - 1)) }}
                disabled={i <= 0} title={tr('Lùi 1 nến')}>◀</button>
        <button className="view-b rong" onClick={() => setChay(c => !c)}
                title={chay ? tr('Dừng') : tr('Phát')}>{chay ? '❚❚' : '▶'}</button>
        <button className="view-b" onClick={() => { setChay(false); setI(x => Math.min(het, x + 1)) }}
                disabled={i >= het} title={tr('Tới 1 nến')}>▶</button>
        <button className="view-b" onClick={() => toiMoc(true)}
                disabled={!coMoc(true)} title={tr('Tới lệnh kế tiếp')}>⏭</button>

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
        {khungDuoc.length > 0 && (
          <select className="view-o" value={khung}
                  title={tr('Khung hiển thị — chỉ đổi CÁCH VẼ')}
                  onChange={e => setKhung(Number(e.target.value))}>
            <option value={0}>{tr('Gốc')}</option>
            {khungDuoc.map(([t, g]) => <option key={t} value={g}>{t}</option>)}
          </select>
        )}
        <span className="view-ngan" />

        {nutBat('ve-mau', mauThuong ? tr('Nến xanh/đỏ như thường')
                                    : tr('Nến về màu xám (để dành xanh/đỏ cho lãi lỗ)'),
                () => setMauThuong(v => !v), mauThuong)}
        {nutBat('an-lenh', hienLenh ? tr('Ẩn mũi tên lệnh và mức giá chờ')
                                    : tr('Hiện lại visual lệnh'),
                () => setHienLenh(v => !v), !hienLenh)}
        {/* Chỉ bấm được khi đã kéo lệch khỏi mép phải — nút sáng thường trực là nút
            chết, và cái nút này không có việc gì làm khi chart vẫn đang bám con trỏ. */}
        {nutBat('ve-nay', tr('Về nến hiện tại'), () => setVeNay(n => n + 1), false, !lech)}
        <span className="view-ngan" />

        <input className="view-keo" type="range" min={0} max={het} value={i}
               onChange={e => { setChay(false); setI(Number(e.target.value)) }} />
        <span className="view-dem">{i + 1}/{het + 1}</span>
        <span className="view-ngay">{ngay}</span>
      </div>

      {/* LƯỚI CHART: mọi mã một lần, bấm một cái là nó mở to.
          ⚠ Lưới để LIẾC, bản to để ĐỌC. Ô trong lưới bỏ trục, bỏ khung phụ, bỏ chữ
          trên dấu lệnh — nhét đủ thứ vào một ô 200px thì không còn nhìn ra hình dáng
          nào, mà nhìn ra hình dáng chính là việc của cái lưới. */}
      <div className="view-san">
        {to === null ? (
          <div className={'view-luoi' + (luot.dsMa.length === 1 ? ' mot' : '')}>
            {luot.dsMa.map(m => (
              <button key={m} type="button" className="view-o-ma"
                      title={tr('Mở to {0}', m)} onClick={() => setTo(m)}>
                <span className="view-o-ten">{m}</span>
                <MotChart kq={kq} ma={m} tToi={tToi} kieu={kieu} giay={khung}
                          mauThuong={mauThuong} hienLenh={hienLenh} />
              </button>
            ))}
          </div>
        ) : (
          <div className="view-mot">
            <div className="view-mot-dau">
              <button className="view-b" onClick={() => setTo(null)}
                      title={tr('Về lưới')}>◀</button>
              <b>{to}</b>
            </div>
            {/* ⚠ MỘT BỘ DỮ LIỆU CHO CẢ HAI. Chart và bảng số liệu cùng đọc `mach`
                của mã này; để mỗi bên tự `dungMachView` thì mỗi lần tua lại xếp lại
                HAI lần cùng một bộ, mà bộ ấy là chỗ nặng nhất của cửa sổ. */}
            <MotMa kq={kq} ma={to} tToi={tToi} kieu={kieu} giay={khung}
                   mauThuong={mauThuong} hienLenh={hienLenh}
                   veNay={veNay} onLech={onLech} />
          </div>
        )}
      </div>

      {/* BẢNG DƯỚI — nhật ký và kết quả, cả hai là của CẢ LƯỢT. «Nó là một mà»:
          cùng một lượt chạy, nên tab Kết quả dùng lại ĐÚNG ruột của cửa sổ Kết quả,
          không dựng bản thứ hai để rồi hai bên nói hai con số.
          ⚠ DÙNG LẠI VỎ `BangDuoi` của cửa sổ chính, không dựng hàng tab thứ hai: kéo
          mép trên chỉnh chiều cao, nhấp đúp hàng tab để cụp, nút ▼/▲ ở góc phải. Bản
          trước tôi dựng tay một hàng tab riêng và mất cả ba thứ ấy — đúng cái lỗi
          cửa sổ Live của bản cũ đã mắc, và lời dặn trong `BangDuoi` kể lại. */}
      <BangDuoi
        tabs={[
          { ma: 'nk', ten: tr('Nhật ký'), so: soLenh,
            noiDung: <NhatKy ds={luot.nhatKy} tToi={tToi} nhay={nhayToi} soi={setSoi} /> },
          { ma: 'kq', ten: tr('Kết quả'), noiDung: <RuotKetQua kq={kq} /> },
        ]}
        tab={tab} onTab={setTab} cao={cao} onCao={setCao} gap={gap} onGap={setGap} />

      {/* POPUP SOI — chuột phải một dòng nhật ký, chọn «Soi trên sơ đồ». */}
      {soi && <SoDoSoi nhan={soi.tag} chu={soi.chu} onDong={() => setSoi(null)} />}
    </div>
  )
}

/** MỘT Ô TRONG LƯỚI. Tách ra để `useMemo` của nó không dính vào mã khác — một lưới
 *  hai chục mã mà mỗi lần tua lại dựng lại cả hai chục bộ dữ liệu thì tua không nổi. */
function MotChart({ kq, ma, tToi, kieu, giay, mauThuong, hienLenh }: {
  kq: KetQuaChay; ma: string; tToi: number; kieu: KieuVe; giay: number
  mauThuong: boolean; hienLenh: boolean
}) {
  const mach = useMemo(() => dungMachView(kq, ma), [kq, ma])
  return <DoThiNen mach={mach} tToi={tToi} kieu={kieu} giay={giay}
                   mauThuong={mauThuong} hienLenh={hienLenh} gon />
}

/** BẢN MỞ TO của một mã: chart bên trái, bảng số liệu bên phải, MỘT bộ dữ liệu. */
function MotMa({ kq, ma, tToi, kieu, giay, mauThuong, hienLenh, veNay, onLech }: {
  kq: KetQuaChay; ma: string; tToi: number; kieu: KieuVe; giay: number
  mauThuong: boolean; hienLenh: boolean
  veNay: number; onLech: (v: boolean) => void
}) {
  const mach = useMemo(() => dungMachView(kq, ma), [kq, ma])
  return (
    <div className="view-than">
      <div className="view-cot-do-thi">
        <DoThiNen mach={mach} tToi={tToi} kieu={kieu} giay={giay}
                  mauThuong={mauThuong} hienLenh={hienLenh}
                  veNay={veNay} onLech={onLech} />
      </div>
      <BangSo mach={mach} ma={ma} tToi={tToi} />
    </div>
  )
}

/** Con số bày cạnh một cái lệnh: giá đặt, hay SỐ LƯỢNG khi lệnh không có giá đặt.
 *
 *  ⚠ LỆNH THỊ TRƯỜNG KHÔNG CÓ GIÁ ĐẶT. LEAN ghi `price` của nó bằng **0**, nên bày
 *  thẳng ra là một thẻ lệnh ghi `0` — trông y như một con bug, và nó che mất con số
 *  DUY NHẤT thật sự có ý nghĩa ở đó: lệnh ấy mua bán bao nhiêu cổ. */
function giaLenh(l: DongLenh) {
  const g = Number(l.gia)
  return g ? String(l.gia) : `${Math.abs(Number(l.so_luong) || 0)}`
}

/** BẢNG SỐ LIỆU bên phải — đúng mấy con số cỗ máy ĐỌC tại nến ấy, và lệnh của mã này.
 *
 *  ⚠ ĐỌC NẾN GỐC, KHÔNG ĐỌC NẾN ĐÃ GỘP — xem `mach_view.soLieuTai`. */
function BangSo({ mach, ma, tToi }: { mach: MachView; ma: string; tToi: number }) {
  const sl = useMemo(() => soLieuTai(mach, tToi), [mach, tToi])

  const so = (v: number | null) => {
    if (v === null || v === undefined || !Number.isFinite(v)) return '—'
    return Number.isInteger(v) ? String(v) : v.toFixed(4).replace(/0+$/, '')
  }

  if (!sl.nhip) {
    return (
      <div className="view-ben">
        <div className="view-nhan-lenh">{tr('Chưa có nến')}</div>
        <div className="view-nk-trong">
          {tr('{0} chưa vào rổ ở nhịp này.', ma)}
        </div>
      </div>
    )
  }

  const cho = sl.nhip.cho
  const lenh = sl.nhip.lenh

  return (
    <div className="view-ben">
      <table className="view-bang-so"><tbody>
        {sl.hang.map((h, k) => (
          <tr key={k} className={h.dauNhom && k > 0 ? 'sang-nhom' : undefined}>
            {/* `title` vì tên rất dài vẫn có thể bị cắt — rê chuột là đọc đủ. */}
            <td className="view-ten" title={h.ten}>{h.ten}</td>
            <td className="view-phu">{h.phu}</td>
            <td className="view-gt">{so(h.gt)}</td>
          </tr>
        ))}
      </tbody></table>

      <div className="view-nhan-lenh">
        {tr('Lệnh còn treo')} <b>{cho.length}</b>
      </div>
      <div className="view-ds-lenh">
        {cho.length === 0 && lenh.length === 0 && (
          <div className="view-nk-trong">{tr('nhịp này không có lệnh nào')}</div>
        )}
        {cho.map((l, k) => (
          <div className="view-mot-lenh" key={'c' + k}>
            <div className="view-lenh-dau">
              <span className={Number(l.so_luong) > 0 ? 'mua' : 'ban'}>
                {Number(l.so_luong) > 0 ? '▲' : '▼'}
              </span>
              <span>{tr(l.loai)}</span>
              <span className="view-lenh-gia">{giaLenh(l)}</span>
            </div>
            <div className="view-lenh-tag">{l.tag}</div>
          </div>
        ))}
        {/* Lệnh KHỚP ở đúng nhịp này — nó vừa biến khỏi danh sách treo, nên nếu không
            bày ra thì cú khớp đi qua mà bảng không nói gì. */}
        {lenh.map((l, k) => (
          <div className={'view-mot-lenh' + (l.hop_le ? ' khop' : ' tu-choi')} key={'k' + k}>
            <div className="view-lenh-dau">
              <span className={Number(l.so_luong) > 0 ? 'mua' : 'ban'}>
                {Number(l.so_luong) > 0 ? '▲' : '▼'}
              </span>
              <span>{l.hop_le ? tr('khớp') : tr(l.trang_thai)}</span>
              <span className="view-lenh-gia">{giaLenh(l)}</span>
            </div>
            <div className="view-lenh-tag">{l.tag}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
