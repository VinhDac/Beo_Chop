import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { cho_cau_noi, py, pyQC } from '../api'
import { useKhungCuaSo } from '../useKhungCuaSo'
import TitleBar, { type NhomMenu } from '../components/TitleBar'
import BangDuoi from '../chung/BangDuoi'
import Journey, { type DongNk } from '../chung/Journey'
import ThongKe from '../chung/ThongKe'
import HopKhoa from './HopKhoa'
import type {
  BootQC, DongNkQC, KetQuaQC, KhoaQC, LenhQC, LoaiChay, ManQC, MucLichSuQC,
  ThongKeChay, TrangThaiQC, TuDoMayQC,
} from '../types'
import type { MayDoc } from '../may/mayTypes'

/** CỬA SỔ MÀN CHƠI — cỗ máy chạy trên QuantConnect.  (DECISIONS.md D-03 · D-05 · D-06 · D-07)
 *
 * Vòng chơi: chọn màn → ▶ nhanh / ▶ đầy đủ trên MÀN ĐÃ THẤY → xem "vì sao" → sửa ở cửa sổ
 * vẽ → NỘP: app chạy cỗ máy trên MÀN ẨN rồi chấm sao. Chế độ Sáng tạo thì mọi symbol, mọi
 * khoảng ngày, không chấm.
 *
 * ⚠ KHÔNG CÓ CHART NẾN, và đó là cố ý: kết quả QC không mang chuỗi giá về máy (điều khoản
 * dữ liệu của QC). Mỗi lượt tự mang giờ của nó, đường vốn nằm sẵn trong nhật ký — nên
 * "vì sao" và Thống kê vẫn đủ; còn muốn xem nến thì có nút mở trang backtest trên QC.
 *
 * Luật chơi KHÔNG nằm ở đây: sao, boss, vé nộp đều do Python tính (`cat_studio/game.py`).
 * Cửa sổ này chỉ hỏi và vẽ — một chỗ định nghĩa điểm, không có bản thứ hai để lệch.
 */

/** Nhịp hỏi tiến độ. Một lượt QC mất cỡ 20–60 giây; 300 ms là mượt mà không dội cầu nối. */
const NHIP_MS = 300
/** Số dòng nhật ký mỗi lần tải. Một năm "mọi lượt" là cả trăm nghìn dòng — tải dần. */
const LO_NK = 400

const pt = (x: number | null | undefined, so = 2) =>
  x == null ? '—' : `${x > 0 ? '+' : ''}${x.toFixed(so)} %`
const gio = (t: number | null | undefined) => {
  if (!t) return '—'
  const d = new Date(t * 1000)
  const s = (n: number) => String(n).padStart(2, '0')
  return `${d.getUTCFullYear()}-${s(d.getUTCMonth() + 1)}-${s(d.getUTCDate())} `
       + `${s(d.getUTCHours())}:${s(d.getUTCMinutes())}`
}

/** Sao bằng ký hiệu ĐƠN SẮC (★ ☆) — không emoji, để ăn theo màu theme. */
function Sao({ n, tren = 3 }: { n: number | null | undefined; tren?: number }) {
  const k = Math.max(0, Math.min(tren, n ?? 0))
  return (
    <span className="mc-sao" title={`${k}/${tren} sao`}>
      <b>{'★'.repeat(k)}</b>{'☆'.repeat(tren - k)}
    </span>
  )
}

/** Ba nấc sao của D-05, đánh dấu nấc nào đã đạt. */
function BacSao({ sao }: { sao: number }) {
  const nac = [
    ['★', 'chạy sạch', 'chạy trọn màn đã thấy, có ít nhất một lệnh đóng'],
    ['★★', 'thắng boss', 'lãi % trên màn đã thấy hơn boss'],
    ['★★★', 'vẫn thắng', 'trên màn ẩn cũng hơn boss'],
  ]
  return (
    <div className="mc-bac">
      {nac.map(([d, ten, giai], k) => (
        <div key={k} className={'mc-nac' + (sao > k ? ' dat' : '')} title={giai}>
          <span className="mc-nac-dau">{d}</span> {ten}
        </div>
      ))}
    </div>
  )
}

export default function ManChoi() {
  /* Kéo + giãn cửa sổ — thiếu là cửa sổ không kéo được (xem `useKhungCuaSo`). */
  useKhungCuaSo(32)

  const [boot, setBoot] = useState<BootQC | null>(null)
  const [loiBoot, setLoiBoot] = useState('')
  const [doc, setDoc] = useState<MayDoc | null>(null)
  const [dsMan, setDsMan] = useState<ManQC[]>([])
  const [manId, setManId] = useState('')
  const [cheDo, setCheDo] = useState<'chien_dich' | 'sang_tao'>('chien_dich')
  /** Chế độ Sáng tạo của CỖ MÁY 5 TRẠM: cả một rổ mã (D-10, phần 5). */
  const [tuDoMay, setTuDoMay] = useState<TuDoMayQC>({ ma: ['XAUUSD'], loai: 'cfd',
                                                      tu: '2025-10-01', den: '2025-12-31',
                                                      von: 10000 })
  const [khoa, setKhoa] = useState<KhoaQC | null>(null)
  const [moKhoa, setMoKhoa] = useState(false)
  const [tt, setTt] = useState<TrangThaiQC | null>(null)
  const [loi, setLoi] = useState('')
  /** Lượt đang XEM (▶ nhanh / ▶ đầy đủ / tự do / mở lại từ lịch sử). */
  const [kq, setKq] = useState<KetQuaQC | null>(null)
  /** Lượt NỘP vừa xong — chỉ có điểm, không bao giờ có nến (màn ẩn). */
  const [nop, setNop] = useState<KetQuaQC | null>(null)
  const [nk, setNk] = useState<DongNkQC[]>([])
  const [nkTong, setNkTong] = useState(0)
  const [chiViec, setChiViec] = useState(true)
  const [lenh, setLenh] = useState<LenhQC[]>([])
  const [lichSu, setLichSu] = useState<MucLichSuQC[]>([])
  const [epTab, setEpTab] = useState<string | undefined>(undefined)
  const [epLan, setEpLan] = useState(0)
  const dangHoi = useRef(false)

  const man = dsMan.find(m => m.id === manId) ?? dsMan[0] ?? null
  const dangChay = !!tt?.dang_chay
  /** Đang chạy CỖ MÁY 5 TRẠM — Python nói, không đoán từ hình dạng `doc`. */
  const laMay = boot?.dang === 'may5'

  /* ------------------------------ nạp ------------------------------ */
  const napBoot = useCallback(async () => {
    const r = await pyQC.qc_boot()
    if (!r.ok || !r.value) { setLoiBoot(r.error ?? 'không nạp được'); return }
    const b = r.value
    setBoot(b)
    setDoc(b.doc)
    setDsMan(b.man)
    setManId(id => id || b.man[0]?.id || '')
    setKhoa(b.khoa)
    if (b.tu_do_may) setTuDoMay(b.tu_do_may)
    setTt(b.trang_thai)
    return b
  }, [])

  const napNk = useCallback(async (tu: number, chi: boolean) => {
    const r = await pyQC.qc_nhat_ky(tu, LO_NK, chi)
    if (!r.ok || !r.value) return
    const lo = r.value
    setNkTong(lo.tong)
    setNk(d => (tu === 0 ? lo.dong : [...d, ...lo.dong]))
  }, [])

  /** Nạp lượt đang xem: tóm tắt, nhật ký trang đầu, lệnh. */
  const napKetQua = useCallback(async () => {
    const r = await pyQC.qc_ket_qua()
    if (!r.ok) return
    setKq(r.value ?? null)
    if (r.value) {
      void napNk(0, chiViec)
      const l = await pyQC.qc_lenh()
      setLenh(l.ok && l.value ? l.value : [])
    } else {
      setNk([]); setNkTong(0); setLenh([])
    }
  }, [napNk, chiViec])

  const napManLichSu = useCallback(async () => {
    const [m, ls] = await Promise.all([pyQC.qc_man(), pyQC.qc_lich_su()])
    if (m.ok && m.value) setDsMan(m.value)
    if (ls.ok && ls.value) setLichSu(ls.value)
  }, [])

  useEffect(() => {
    let song = true
    void (async () => {
      try { await cho_cau_noi('qc_boot') } catch (e) { setLoiBoot(String(e)); return }
      const b = await napBoot()
      if (!song || !b) return
      void napManLichSu()
      if (b.co_ket_qua) void napKetQua()
    })()
    // Cửa sổ vẽ bấm ◆ Màn chơi lần nữa → sơ đồ mới đẩy sang: nạp lại (vé nộp, độ gọn).
    window.__su_kien = (ten: string) => { if (ten === 'so_do_moi') void napBoot().then(() => napManLichSu()) }
    return () => { song = false; window.__su_kien = undefined }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ------------------------------ chạy ------------------------------ */
  /* Hỏi tiến độ khi đang chạy. Xong thì nạp kết quả, sao, lịch sử. */
  useEffect(() => {
    if (!dangChay) return
    const id = window.setInterval(async () => {
      if (dangHoi.current) return
      dangHoi.current = true
      try {
        const r = await pyQC.qc_trang_thai()
        if (!r.ok || !r.value) return
        setTt(r.value)
        if (!r.value.dang_chay) {
          const x = r.value.xong
          if (r.value.loi) setLoi(r.value.loi)
          if (x) {
            if (x.an) { setNop(x) } else { setNop(null); await napKetQua() }
            setEpTab(x.an ? 'diem' : 'nhat-ky'); setEpLan(n => n + 1)
          }
          void napManLichSu()
        }
      } finally { dangHoi.current = false }
    }, NHIP_MS)
    return () => window.clearInterval(id)
  }, [dangChay, napKetQua, napManLichSu])

  const chay = useCallback(async (loai: LoaiChay) => {
    setLoi('')
    const r = await pyQC.qc_chay(loai, loai === 'tu_do' ? null : (man?.id ?? null),
                                 loai === 'tu_do' ? tuDoMay : null)
    if (!r.ok) {
      setLoi(r.error ?? 'không chạy được')
      if ((r.error ?? '').includes('khoá')) setMoKhoa(true)
      return
    }
    setTt({ dang_chay: true, loai, chu: 'Đóng gói cỗ máy', ti_le_chung: 0, xong: null,
            loi: null })
  }, [man, tuDoMay])

  const moLai = useCallback(async (duong: string) => {
    setLoi('')
    const r = await pyQC.qc_mo_lai(duong)
    if (!r.ok) { setLoi(r.error ?? 'không mở được'); return }
    setNop(null)
    await napKetQua()
    setEpTab('nhat-ky'); setEpLan(n => n + 1)
  }, [napKetQua])

  const doiChiViec = useCallback((v: boolean) => {
    setChiViec(v)
    if (kq) void napNk(0, v)
  }, [kq, napNk])

  const soi = useCallback((i: number) => { void pyQC.qc_soi_luot(i) }, [])

  /* ------------------------------ dữ liệu cho bảng ------------------------------ */
  const dongNk: DongNk[] = useMemo(
    () => nk.map(d => ({ i: d.i, co_viec: d.co_viec, lenh_id: d.lenh_id, chu: d.chu })),
    [nk])

  /** Một lượt chạy nói về MỘT symbol (sơ đồ cũ) hay CẢ RỔ (cỗ máy 5 trạm). */
  const roChu = (k: KetQuaQC) => k.symbol || (k.ma ?? []).join(', ')

  const thongKe: ThongKeChay | null = useMemo(() => kq && ({
    tk: kq.thong_ke, duong_von: kq.duong_von, t_dau: kq.t_dau ?? 0, t_cuoi: kq.t_cuoi ?? 0,
    yc_tu: kq.tu, yc_den: kq.den, symbol: roChu(kq), nhip: kq.nhip,
  }), [kq])

  const menuTieuDe: NhomMenu[] = [
    { ten: 'Màn chơi', muc: [
      { ten: 'Khoá QuantConnect…', icon: 'gear', onClick: () => setMoKhoa(true) },
      { ten: 'Xem lượt này trên quantconnect.com', tat: !kq?.url,
        viSao: 'lượt đang xem không có link QC', onClick: () => kq?.url && pyQC.qc_mo_web(kq.url) },
      { ngan: true },
      { ten: 'Đóng cửa sổ', onClick: () => { void py.cua_so_dong() } },
    ] },
  ]

  /* ------------------------------ vẽ ------------------------------ */
  if (loiBoot) return <div className="khung"><div className="tk-trong">{loiBoot}</div></div>

  /** D-11: đường chạy đang dựng lại — Python nói câu này, cửa sổ nói lại nguyên văn. */
  const chuaNoi = boot?.chua_noi || ''
  const chayDuoc = !dangChay && !!doc && !chuaNoi
  const coVe = !!man?.ve_nop

  return (
    <div className="khung">
      <TitleBar tieuDe={`${doc?.name ?? 'Cat Studio'} — Màn chơi`} menus={menuTieuDe}
                them={
                  <button className={'mc-khoa-nut' + (khoa?.co ? ' co' : ' khong')}
                          data-khong-keo onClick={() => setMoKhoa(true)}
                          title={khoa?.co ? `Khoá QuantConnect: User ${khoa.user_id}`
                                          : 'Chưa có khoá QuantConnect — bấm để đặt'}>
                    {khoa?.co ? `QC · ${khoa.user_id}` : 'QC · chưa có khoá'}
                  </button>
                } />

      {/* ---- thanh công cụ: chế độ, nút chạy ---- */}
      <div className="tb mc-tb">
        <div className="mc-che-do" role="tablist">
          <button className={cheDo === 'chien_dich' ? 'bat' : ''} disabled={dangChay}
                  onClick={() => setCheDo('chien_dich')}>Chiến dịch</button>
          <button className={cheDo === 'sang_tao' ? 'bat' : ''} disabled={dangChay}
                  onClick={() => setCheDo('sang_tao')}>Sáng tạo</button>
        </div>
        <span className="tb-ngan" />
        {cheDo === 'chien_dich' ? (
          <>
            <button className="nut" disabled={!chayDuoc || !man} onClick={() => chay('nhanh')}
                    title={man ? `Chạy ${man.nhanh[0]} → ${man.nhanh[1]} — nhanh, để thử ý` : ''}>
              ▶ nhanh</button>
            <button className="nut chinh" disabled={!chayDuoc || !man} onClick={() => chay('day_du')}
                    title={man ? `Chạy trọn màn đã thấy ${man.thay[0]} → ${man.thay[1]}` : ''}>
              ▶ đầy đủ</button>
            <button className="nut mc-nop" disabled={!chayDuoc || !coVe} onClick={() => chay('nop')}
                    title={coVe ? 'Nộp: chạy cỗ máy trên MÀN ẨN rồi chấm sao'
                                : 'Chạy ▶ đầy đủ cỗ máy này trước — rồi mới nộp được'}>
              Nộp ↑</button>
          </>
        ) : (
          <button className="nut chinh" disabled={!chayDuoc} onClick={() => chay('tu_do')}
                  title={laMay
                    ? 'Chạy cỗ máy trên rổ mã và khoảng ngày bạn chọn — không chấm sao'
                    : 'Chạy với symbol và khoảng ngày bạn chọn — không chấm sao'}>
            ▶ chạy</button>
        )}
        <span className="tb-day" />
        {/* Đang hiện điểm màn ẩn thì KHÔNG có nút này: nó trỏ lượt đã thấy, dễ hiểu nhầm
            thành link của lượt nộp — mà lượt nộp thì cố ý không có link (D-06). */}
        {kq?.url && !nop && <button className="tb-nut rong mc-web" title="Mở trang backtest trên quantconnect.com"
                            onClick={() => pyQC.qc_mo_web(kq.url!)}>QC ↗</button>}
      </div>

      {/* ---- thân: thẻ màn (trái) · tiến độ / kết quả (phải) ---- */}
      <div className="mc-than">
        <div className="mc-trai">
          {cheDo === 'chien_dich'
            ? (man ? <TheMan m={man} ds={dsMan} chon={setManId} khoa={dangChay}
                             doGon={boot?.do_gon ?? null} />
                   : <div className="cd-rong">Chưa có màn nào.</div>)
            : <TheTuDoMay v={tuDoMay} dat={setTuDoMay} khoa={dangChay}
                          loaiTT={boot?.loai_thi_truong ?? {}}
                          tran={boot?.tran_so_ma ?? 20} />}
        </div>
        <div className="mc-phai">
          {!doc && <div className="mc-bao">Chưa có sơ đồ — bấm <b>◆ Màn chơi</b> ở cửa sổ vẽ.</div>}
          {/* Nói THẲNG là chưa chạy được, ngay chỗ người chơi định bấm ▶ — chứ không để
              họ bấm rồi nhận một câu lỗi chẳng hiểu từ đâu ra. */}
          {chuaNoi && <div className="mc-bao canh">{chuaNoi}</div>}
          {khoa && !khoa.co && (
            <div className="mc-bao canh">
              Chưa có khoá QuantConnect — cần gói <b>Researcher</b> trở lên (gói Free không có API).
              <button className="nut-nho" onClick={() => setMoKhoa(true)}>Đặt khoá…</button>
            </div>
          )}
          {loi && <div className="mc-bao loi"><b>✕</b> <span className="mc-loi-chu">{loi}</span>
                    <button className="nut-nho" onClick={() => setLoi('')}>đóng</button></div>}
          {dangChay && tt ? <TienDo tt={tt} />
            : nop ? <TheNop x={nop} man={man} />
            : kq ? <TheKetQua x={kq} />
            : <GioiThieu cheDo={cheDo} laMay={laMay} />}
        </div>
      </div>

      <BangDuoi epTab={epTab} epLan={epLan} tabs={[
        { khoa: 'nhat-ky', nhan: 'Vì sao', dem: kq ? nkTong : undefined,
          ve: () => !kq
            ? <div className="cd-rong">Chạy ▶ để xem cỗ máy nghĩ gì ở từng nến.</div>
            : (
              <div className="nk-boc">
                <div className="nk-moc">
                  ▶ {kq.ten} · {roChu(kq)} {kq.tu} → {kq.den} · chuột phải một dòng → «Xem trên sơ đồ»
                </div>
                <Journey dong={dongNk} chiViec={chiViec} soi={soi} />
                {nk.length < nkTong && (
                  <button className="nut-nho mc-them" onClick={() => napNk(nk.length, chiViec)}>
                    tải thêm {Math.min(LO_NK, nkTong - nk.length)} dòng ({nk.length}/{nkTong})
                  </button>
                )}
              </div>
            ),
          nut: <label className="nk-loc">
                 <input type="checkbox" checked={chiViec}
                        onChange={e => doiChiViec(e.target.checked)} />
                 chỉ dòng có việc
               </label> },
        { khoa: 'thong-ke', nhan: 'Thống kê',
          ve: () => thongKe ? <ThongKe d={thongKe} />
                            : <div className="cd-rong">Chưa có lượt nào.</div> },
        { khoa: 'lenh', nhan: 'Lệnh', dem: kq ? lenh.length : undefined,
          ve: () => <BangLenh ds={lenh} /> },
        { khoa: 'diem', nhan: 'Điểm', dem: man?.tien_do.so_lan_nop || undefined,
          ve: () => <BangDiem m={man} /> },
        { khoa: 'lich-su', nhan: 'Lịch sử', dem: lichSu.length || undefined,
          ve: () => <BangLichSu ds={lichSu} mo={moLai} web={u => pyQC.qc_mo_web(u)} /> },
      ]} />

      {moKhoa && khoa && (
        <HopKhoa khoa={khoa} dong={() => setMoKhoa(false)}
                 doi={k => setKhoa(k)} />
      )}
    </div>
  )
}

/* ================================ thẻ màn ================================ */

/** Nhãn loại thị trường. Bản của Python (`qc_boot().loai_thi_truong`) là nguồn thật; cái
 *  này chỉ để thẻ màn đọc được khi boot chưa về tới. */
const LOAI_TT: Record<string, string> = {
  forex: 'Ngoại hối', cfd: 'CFD', co_phieu: 'Cổ phiếu Mỹ', crypto: 'Crypto',
}

function TheMan({ m, ds, chon, khoa, doGon }: {
  m: ManQC; ds: ManQC[]; chon: (id: string) => void; khoa: boolean; doGon: BootQC['do_gon'] | null
}) {
  const v = m.ve_nop
  return (
    <div className="mc-the">
      {ds.length > 1 && (
        <select className="o" value={m.id} disabled={khoa} onChange={e => chon(e.target.value)}>
          {ds.map(x => <option key={x.id} value={x.id}>{x.ten}</option>)}
        </select>
      )}
      <div className="mc-the-dau">
        <div className="mc-ten-man">{m.ten}</div>
        <Sao n={m.tien_do.sao} />
      </div>
      <div className="mc-dan">{m.loi_dan}</div>
      <table className="mc-bang-nho"><tbody>
        {/* Màn của cỗ máy chạy cả RỔ: bày đủ rổ ra, vì chính nó là đầu vào của trạm
            ① — và vì «bản đồ · XAUUSD» cho một màn 4 mã là nói sai. */}
        <tr><td>Bản đồ</td><td>{m.ban_do}{
          /* Loại thị trường chỉ thêm vào khi nó NÓI THÊM được gì — «Ngoại hối · Ngoại
             hối» là một dòng rỗng nghĩa. */
          m.loai && (LOAI_TT[m.loai] ?? m.loai) !== m.ban_do
            ? ` · ${LOAI_TT[m.loai] ?? m.loai}` : ''}</td></tr>
        <tr><td>Rổ mã</td><td className="mono" title={m.ro.join(', ')}>
          {m.ro.join(' · ')} <span className="mc-mo">({m.ro.length} mã)</span></td></tr>
        <tr><td>Màn đã thấy</td><td className="mono">{m.thay[0]} → {m.thay[1]}</td></tr>
        <tr><td>▶ nhanh</td><td className="mono">{m.nhanh[0]} → {m.nhanh[1]}</td></tr>
        <tr><td>Màn ẩn</td><td>{m.an_mo_ta} — chỉ chạy khi <b>Nộp</b></td></tr>
        <tr><td>Boss</td><td><b>{m.boss.ten}</b> — {m.boss.mo_ta}</td></tr>
        <tr><td>Vốn</td><td className="mono">{m.von.toLocaleString('en-US')} $</td></tr>
      </tbody></table>

      <div className="mc-muc">Cỗ máy đang mở</div>
      <table className="mc-bang-nho"><tbody>
        <tr><td>Độ gọn</td><td>{doGon ? <><b>{doGon.tong}</b> = {doGon.so_khoi} khối + {doGon.so_tham_so} tham số</> : '—'}</td></tr>
        <tr><td>▶ đầy đủ</td><td>{v
          ? <>{pt(v.lai_pt)} vs boss {pt(v.mua_giu_pt)} · <Sao n={v.sach ? (v.thang_boss ? 2 : 1) : 0} /></>
          : <span className="mc-mo">chưa chạy — cần để được Nộp</span>}</td></tr>
        <tr><td>Đã nộp</td><td>{m.tien_do.so_lan_nop} lần</td></tr>
      </tbody></table>
      <BacSao sao={m.tien_do.sao} />
    </div>
  )
}

/* ================================ sáng tạo ================================ */

/** Sáng tạo cho CỖ MÁY 5 TRẠM: đầu vào là một RỔ mã, không phải một symbol — cỗ máy tự
 *  chọn mã ở trạm ①, nên đưa nó một mã duy nhất là bỏ phí cả trạm đó.  (D-10, lát 5f)
 *
 *  Ô mã là chữ tự do trong lúc gõ; tách, viết hoa, bỏ trùng và soát ký hiệu là việc của
 *  Python (`qc_chay.soat_tu_do_may`) — hai nơi cùng soát là hai luật sẽ lệch nhau. */
function TheTuDoMay({ v, dat, khoa, loaiTT, tran }: {
  v: TuDoMayQC; dat: (x: TuDoMayQC) => void; khoa: boolean
  loaiTT: Record<string, string>; tran: number
}) {
  const [chu, setChu] = useState<string | null>(null)
  return (
    <div className="mc-the">
      <div className="mc-ten-man">Sáng tạo · cỗ máy 5 trạm</div>
      <div className="mc-dan">
        Không màn, không boss, không sao — rổ mã nào, khoảng ngày nào cũng được (D-07).
        Tối đa {tran} mã một lượt.
      </div>
      <label className="mc-o">Rổ mã
        <input className="o" disabled={khoa} spellCheck={false}
               placeholder="EURUSD, XAUUSD, GBPJPY"
               title="Cách nhau bằng dấu phẩy hoặc khoảng trắng"
               value={chu ?? v.ma.join(', ')}
               onChange={e => {
                 setChu(e.target.value)
                 dat({ ...v, ma: e.target.value.split(/[,\s]+/).filter(Boolean) })
               }}
               onBlur={() => setChu(null)} /></label>
      <label className="mc-o">Loại thị trường
        <select className="o" value={v.loai} disabled={khoa}
                title="Lớp vỏ đăng ký mã theo loại này trên QuantConnect"
                onChange={e => dat({ ...v, loai: e.target.value })}>
          {Object.entries(loaiTT).map(([k, ten]) => (
            <option key={k} value={k}>{ten}</option>
          ))}
        </select></label>
      <label className="mc-o">Từ ngày
        <input className="o" type="date" value={v.tu} disabled={khoa}
               onChange={e => dat({ ...v, tu: e.target.value })} /></label>
      <label className="mc-o">Đến ngày
        <input className="o" type="date" value={v.den} disabled={khoa}
               onChange={e => dat({ ...v, den: e.target.value })} /></label>
      <label className="mc-o">Vốn ($)
        <input className="o" type="number" min={1} value={v.von} disabled={khoa}
               onChange={e => dat({ ...v, von: Number(e.target.value) })} /></label>
      <div className="mc-dan mc-mo">
        {v.ma.length} mã trong rổ{v.ma.length > tran ? ` — quá ${tran}, Python sẽ từ chối` : ''}
      </div>
    </div>
  )
}

/* ================================ tiến độ ================================ */
function TienDo({ tt }: { tt: TrangThaiQC }) {
  const chung = Math.round((tt.ti_le_chung ?? 0) * 100)
  return (
    <div className="mc-tien-do">
      <div className="mc-td-dau">
        <b>{TEN_LOAI[tt.loai ?? 'nhanh']}</b> đang chạy trên QuantConnect
        <span className="mc-mo">{tt.giay != null ? ` · ${tt.giay.toFixed(0)} giây` : ''}</span>
      </div>
      <div className="mc-thanh"><div style={{ width: `${Math.max(4, chung)}%` }} /></div>
      <div className="mc-td-chu">
        {tt.chu}{tt.ti_le != null ? ` · ${Math.round(tt.ti_le * 100)} %` : ''}
      </div>
      <div className="mc-mo mc-td-giai">
        Đóng gói cỗ máy → đẩy lên project trên QC → biên dịch → backtest trên dữ liệu của QC
        → tải nhật ký về máy. Đóng cửa sổ này cũng không dừng lượt chạy.
      </div>
    </div>
  )
}

const TEN_LOAI: Record<LoaiChay, string> = {
  nhanh: '▶ nhanh', day_du: '▶ đầy đủ', nop: 'Nộp', tu_do: '▶ tự do',
}

/* ================================ kết quả ================================ */
function PhanDinh({ lai, boss }: { lai: number; boss: number | null }) {
  if (boss == null) return <span className="mc-mo">boss: không có giá trong khoảng này</span>
  const thang = lai > boss
  return (
    <span className={'mc-dinh ' + (thang ? 'thang' : 'thua')}>
      {thang ? 'THẮNG boss' : 'chưa thắng boss'}
    </span>
  )
}

function TheKetQua({ x }: { x: KetQuaQC }) {
  const t = x.thong_ke
  const lai = x.cham?.lai_pt ?? t.lai_pt
  const boss = x.cham ? x.cham.mua_giu_pt : x.mua_giu_pt
  return (
    <div className="mc-kq">
      <div className="mc-kq-dau">
        <b>{x.loai ? TEN_LOAI[x.loai] : 'Lượt đã chạy'}</b>
        <span className="mono"> · {x.symbol} {x.tu} → {x.den}</span>
        {x.giay_tong != null && <span className="mc-mo"> · {x.giay_tong.toFixed(0)} giây</span>}
      </div>
      <div className="mc-doi">
        <div className="mc-ben"><div className="mc-ben-ten">Cỗ máy</div>
          <div className={'mc-so ' + (lai >= 0 ? 'lai' : 'lo')}>{pt(lai)}</div></div>
        <div className="mc-vs">vs</div>
        <div className="mc-ben"><div className="mc-ben-ten">Mua rồi giữ</div>
          <div className="mc-so">{pt(boss)}</div></div>
        <div className="mc-ben mc-ben-dinh"><PhanDinh lai={lai} boss={boss} />
          {x.loai === 'day_du' && x.sao != null && <div><Sao n={x.sao} /> <span className="mc-mo">(★★★ chỉ có khi Nộp)</span></div>}
        </div>
      </div>
      <div className="mc-chip">
        <span>{t.so_lenh} lệnh · {t.so_dong} đóng · {t.so_huy} huỷ</span>
        <span>thắng {t.thang}/{t.thua} = {t.ty_le_thang.toFixed(1)} %</span>
        <span>tổng {t.tong_R.toFixed(2)} R</span>
        <span>sụt giảm {t.drawdown_pt.toFixed(2)} %</span>
        <span>độ gọn {x.do_gon.tong}</span>
      </div>
      {x.so_luot != null && (
        <div className="mc-mo mc-kq-cuoi">
          {x.so_luot.toLocaleString('en-US')} lượt cỗ máy đã nghĩ — mở tab <b>Vì sao</b> để đọc
          từng lượt, chuột phải một dòng → «Xem trên sơ đồ» để thấy đường nó đã đi.
        </div>
      )}
    </div>
  )
}

function TheNop({ x, man }: { x: KetQuaQC; man: ManQC | null }) {
  const thay = x.thay
  const an = x.cham
  return (
    <div className="mc-kq mc-nop-kq">
      <div className="mc-kq-dau">
        <b>Nộp</b> · lần thứ <b>{x.lan_nop}</b> · {man?.ten}
        {x.giay_tong != null && <span className="mc-mo"> · {x.giay_tong.toFixed(0)} giây</span>}
      </div>
      <div className="mc-sao-to"><Sao n={x.sao} /></div>
      <table className="mc-bang-nho mc-hai-man"><thead>
        <tr><th></th><th>Cỗ máy</th><th>Mua rồi giữ</th><th></th></tr>
      </thead><tbody>
        <tr><td>Màn đã thấy</td><td className="mono">{pt(thay?.lai_pt)}</td>
            <td className="mono">{pt(thay?.mua_giu_pt)}</td>
            <td>{thay ? <PhanDinh lai={thay.lai_pt} boss={thay.mua_giu_pt} /> : '—'}</td></tr>
        <tr><td>Màn ẩn</td><td className="mono">{pt(an?.lai_pt)}</td>
            <td className="mono">{pt(an?.mua_giu_pt)}</td>
            <td>{an ? <PhanDinh lai={an.lai_pt} boss={an.mua_giu_pt} /> : '—'}</td></tr>
      </tbody></table>
      <BacSao sao={x.sao ?? 0} />
      <div className="mc-mo mc-kq-cuoi">
        Màn ẩn chỉ cho xem điểm — không có nhật ký, không có lệnh: xem từng nến của màn ẩn là
        học thuộc đề thi. Độ gọn lần này: <b>{x.do_gon.tong}</b>.
      </div>
    </div>
  )
}

function GioiThieu({ cheDo, laMay }: { cheDo: string; laMay?: boolean }) {
  return (
    <div className="mc-gioi-thieu">
      {cheDo !== 'chien_dich' && laMay ? (
        <>
          <p><b>Thả cỗ máy 5 trạm vào thị trường thật trong quá khứ.</b></p>
          <p>Chọn <b>rổ mã</b>, loại thị trường, khoảng ngày và vốn ở bên trái rồi bấm
             <b> ▶ chạy</b>. Cỗ máy tự lọc rổ ở trạm ①, phát tín hiệu ở ②, chia vốn ở ③,
             cắt rủi ro ở ④ và đặt lệnh ở ⑤.</p>
          <p>Mở tab <b>Vì sao</b> để xem từng quyết định của từng trạm; chuột phải một
             dòng → <b>Xem trên sơ đồ</b> để tô đúng khối đã chạy ở cửa sổ vẽ.</p>
        </>
      ) : cheDo === 'chien_dich' && laMay ? (
        <>
          <p><b>Chọn một màn, thả cỗ máy 5 trạm vào cả RỔ mã của màn đó.</b></p>
          <p>▶ nhanh và ▶ đầy đủ chạy trên <b>màn đã thấy</b> — chạy bao nhiêu lần cũng
             được. Boss của màn là <b>«Mua rồi giữ cả rổ»</b>: chia đều vốn cho mọi mã rồi
             để yên. Muốn hơn nó, cỗ máy phải chọn đúng mã (trạm ①), đúng lúc (trạm ②) và
             dám đứng ngoài.</p>
          <p><b>Nộp</b> chạy cỗ máy trên <b>màn ẩn</b> — đoạn thị trường nó chưa từng thấy
             — rồi chấm sao. Phải ▶ đầy đủ đúng cỗ máy đó trước đã.</p>
        </>
      ) : cheDo === 'chien_dich' ? (
        <>
          <p><b>Lắp cỗ máy, thả nó vào thị trường thật trong quá khứ.</b></p>
          <p>▶ nhanh và ▶ đầy đủ chạy trên <b>màn đã thấy</b> — chạy bao nhiêu lần cũng được,
             mở tab <b>Vì sao</b> để xem cỗ máy nghĩ gì ở từng nến, rồi sửa ở cửa sổ vẽ.</p>
          <p><b>Nộp</b> chạy cỗ máy trên <b>màn ẩn</b> — đoạn thị trường nó chưa từng thấy —
             và chấm sao. Mỗi lần nộp đều được đếm.</p>
        </>
      ) : (
        <p>Chọn symbol, khoảng ngày, vốn ở bên trái rồi bấm <b>▶ chạy</b>.</p>
      )}
    </div>
  )
}

/* ================================ bảng dưới ================================ */
function BangLenh({ ds }: { ds: LenhQC[] }) {
  if (!ds.length) return <div className="cd-rong">Chưa có lệnh nào.</div>
  return (
    <div className="nk-cuon">
      <table className="mc-bang"><thead><tr>
        <th>Lệnh</th><th>Hướng</th><th>Đặt lúc</th><th>Giá đặt</th><th>Khớp lúc</th>
        <th>Giá khớp</th><th>Đóng lúc</th><th>Giá đóng</th><th>Vì sao đóng</th><th>R</th>
      </tr></thead><tbody>
        {ds.map(l => {
          const chieu = l.huong === 'mua' ? 1 : -1
          const r = l.gia_dong != null && l.gia_khop != null && l.R
            ? (l.gia_dong - l.gia_khop) * chieu / l.R : null
          return (
            <tr key={l.id}>
              <td className="mono">{l.id}</td>
              <td>{l.huong === 'mua' ? 'Mua' : 'Bán'} · {l.loai}</td>
              <td className="mono">{gio(l.t_dat)}</td><td className="mono">{l.gia_dat}</td>
              <td className="mono">{gio(l.t_khop)}</td><td className="mono">{l.gia_khop ?? '—'}</td>
              <td className="mono">{gio(l.t_dong)}</td><td className="mono">{l.gia_dong ?? '—'}</td>
              <td>{l.ly_do_dong ?? '—'}</td>
              <td className={'mono ' + (r == null ? '' : r > 0 ? 'lai' : 'lo')}>
                {r == null ? '—' : `${r > 0 ? '+' : ''}${r.toFixed(2)}`}</td>
            </tr>
          )
        })}
      </tbody></table>
    </div>
  )
}

function BangDiem({ m }: { m: ManQC | null }) {
  if (!m) return <div className="cd-rong">Chưa có màn nào.</div>
  const lan = m.tien_do.lan_cuoi ? [m.tien_do.lan_cuoi] : []
  const tot = m.tien_do.tot_nhat
  return (
    <div className="nk-cuon mc-diem">
      <div><b>{m.ten}</b> · đã nộp <b>{m.tien_do.so_lan_nop}</b> lần · cao nhất <Sao n={m.tien_do.sao} /></div>
      {tot && <div>Lần tốt nhất: <b>{tot.ten}</b> · <Sao n={tot.sao} /> · độ gọn {tot.do_gon.tong}
                · màn đã thấy {pt(tot.thay.lai_pt)} · màn ẩn {pt(tot.an.lai_pt)} · {tot.t}</div>}
      {lan.map((x, k) => <div key={k} className="mc-mo">Lần cuối: {x.ten} · ★{x.sao} · {x.t}</div>)}
      {!m.tien_do.so_lan_nop && <div className="mc-mo">Chưa nộp lần nào.</div>}
    </div>
  )
}

function BangLichSu({ ds, mo, web }: {
  ds: MucLichSuQC[]; mo: (duong: string) => void; web: (url: string) => void
}) {
  if (!ds.length) return <div className="cd-rong">Chưa chạy lượt nào trên QuantConnect.</div>
  return (
    <div className="nk-cuon">
      <table className="mc-bang"><thead><tr>
        <th>Lúc (UTC)</th><th>Kiểu</th><th>Cỗ máy</th><th>Khoảng</th><th>Lãi</th>
        <th>Boss</th><th>Sao</th><th></th>
      </tr></thead><tbody>
        {ds.map((x, k) => (
          <tr key={k}>
            <td className="mono">{x.t}</td>
            <td>{TEN_LOAI[x.loai] ?? x.loai}{x.an ? ' · màn ẩn' : ''}</td>
            <td>{x.ten}</td>
            <td className="mono">{x.an ? `${x.symbol} · màn ẩn` : `${x.symbol} ${x.tu} → ${x.den}`}</td>
            <td className={'mono ' + (x.lai_pt >= 0 ? 'lai' : 'lo')}>{pt(x.lai_pt)}</td>
            <td className="mono">{pt(x.mua_giu_pt)}</td>
            <td>{x.sao != null ? <Sao n={x.sao} /> : ''}</td>
            <td className="mc-hang-nut">
              {!x.an && <button className="nut-nho" onClick={() => mo(x.duong)}
                                title="Mở lại để xem — đọc nhật ký trên máy, không chạy lại">xem</button>}
              {x.url && <button className="nut-nho" onClick={() => web(x.url!)}
                                title="Mở trang backtest trên quantconnect.com">QC ↗</button>}
            </td>
          </tr>
        ))}
      </tbody></table>
    </div>
  )
}
