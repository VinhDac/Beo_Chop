import { useEffect, useRef, useState } from 'react'
import { pyGame } from '../api'
import type { ChuongGame, GiacQuan, KetQuaQC, ManGame } from '../types'
import type { Game } from './useGame'
import {
  BossMuaGiu, CanhTiemVang, ChanDung, IconKhoa, LogoGame, MeoTho,
} from './HinhVe'
import { DuongVonNho, Histogram, SaoGame } from './BieuDo'
import { nam, ngay, pt, tien } from './dinh_dang'

/** CÁC MÀN HÌNH GAME — phủ lên cửa sổ vẽ (dưới thanh tiêu đề), trừ XƯỞNG: xưởng chính là
 *  trình vẽ sơ đồ (`App`), không phủ gì.
 *
 *  Khuôn Opus Magnum (DECISIONS.md D-09): màn hình chính → bản đồ chương → truyện →
 *  phiếu việc → xưởng ⇄ kết quả (ba histogram) → đấu màn ẩn → hoàn thành.
 *  Luật (sao, boss, màn mở) đều do Python trả — ở đây chỉ VẼ. */

/* ======================================================================= *
 *  Mẩu dùng chung
 * ======================================================================= */

function ChipGiacQuan({ gq }: { gq: GiacQuan }) {
  return (
    <span className={'g-chip' + (gq.moi ? ' moi' : '')} title={gq.key}>
      {gq.nhan}{gq.moi && <b>MỚI</b>}
    </span>
  )
}

/** Số đếm lên từ 0 — màn đấu boss lật điểm như một bảng tỉ số. */
function DemSo({ v, ms = 1400 }: { v: number | null | undefined; ms?: number }) {
  const [x, setX] = useState(0)
  useEffect(() => {
    if (v == null) return
    let id = 0
    const t0 = performance.now()
    const buoc = (t: number) => {
      const k = Math.min(1, (t - t0) / ms)
      setX(v * (1 - Math.pow(1 - k, 3)))
      if (k < 1) id = requestAnimationFrame(buoc)
    }
    id = requestAnimationFrame(buoc)
    return () => cancelAnimationFrame(id)
  }, [v, ms])
  return <>{v == null ? '—' : pt(x)}</>
}

/** "12 tháng ngay sau năm này" → "… năm 2021": nói thẳng năm nào, khỏi bắt người đọc dò. */
const anMoTa = (s: string, n: string) => s.replace('năm này', `năm ${n}`)

const LUAT_SAO = (n: string) => [
  ['★', 'Chạy sạch', `chạy trọn năm ${n}, có ít nhất một lệnh đóng`],
  ['★★', 'Thắng boss', `lãi hơn «Mua rồi giữ» trên năm ${n}`],
  ['★★★', 'Vẫn thắng', 'thắng boss cả trên MÀN ẨN — năm cỗ máy chưa từng thấy'],
]

/* ======================================================================= *
 *  1 · Màn hình chính
 * ======================================================================= */

function ManHinhChinh({ g, moKhoa }: { g: Game; moKhoa: () => void }) {
  const b = g.boot
  const c = b?.chuong.find(x => x.mo) ?? b?.chuong[0]
  const tong = b?.chuong.reduce((s, x) => s + x.sao, 0) ?? 0
  const toiDa = b?.chuong.filter(x => !x.sap_ra_mat).reduce((s, x) => s + x.sao_toi_da, 0) ?? 0
  const tiep = b?.chuong.flatMap(x => x.man).find(m => m.id === b?.man_tiep)
  return (
    <div className="g-man-hinh g-chinh">
      <div className="g-chinh-nen" aria-hidden>
        <svg viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice">
          <polyline points="0,560 120,520 200,540 300,470 380,500 470,420 560,450 650,360 740,390 830,300 930,330 1030,240 1200,210"
                    fill="none" strokeWidth="3" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="g-chinh-giua">
        <LogoGame size={150} />
        <h1 className="g-chinh-ten">CAT STUDIO</h1>
        <div className="g-chinh-phu">Xưởng chế tạo cỗ máy giao dịch</div>
        <div className="g-menu">
          <button className="g-menu-muc chinh" onClick={() => void g.vaoChienDich()}>
            <span className="g-menu-ten">Chiến dịch</span>
            <span className="g-menu-mo">
              {c ? `Chương ${c.so} · ${c.ten}` : 'đang nạp…'} · {tong}/{toiDa} ★
            </span>
            {tiep && <span className="g-menu-tiep">Tiếp theo: màn {tiep.id} · {tiep.ten}</span>}
          </button>
          <button className="g-menu-muc" onClick={g.thoatGame}>
            <span className="g-menu-ten">Sáng tạo</span>
            <span className="g-menu-mo">Vẽ tự do — mọi giác quan, mọi khoảng ngày, không chấm điểm</span>
          </button>
          <button className="g-menu-muc" onClick={moKhoa}>
            <span className="g-menu-ten">Khoá QuantConnect</span>
            <span className="g-menu-mo">
              {b?.khoa.co ? `đã có khoá · User ${b.khoa.user_id}` : 'chưa có — cần để cỗ máy chạy được'}
            </span>
          </button>
        </div>
        <div className="g-chinh-chan">
          Mỗi cỗ máy chạy thật trên QuantConnect · điểm thật chấm trên năm nó chưa từng thấy
        </div>
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  2 · Bản đồ chương — chọn màn
 * ======================================================================= */

/** Toạ độ (%) của mốc thứ i trên bản đồ: đi từ trái sang phải, lên xuống như đường giá. */
function viTriMoc(i: number, n: number): [number, number] {
  const x = n <= 1 ? 50 : 11 + (i * 78) / (n - 1)
  return [x, i % 2 === 0 ? 66 : 34]
}

function duongBanDo(n: number) {
  const p = Array.from({ length: n }, (_, i) => viTriMoc(i, n))
  if (!p.length) return ''
  let d = `M ${p[0][0]} ${p[0][1]}`
  for (let i = 1; i < p.length; i++) {
    const [x0, y0] = p[i - 1]
    const [x1, y1] = p[i]
    const gx = (x0 + x1) / 2
    d += ` C ${gx} ${y0}, ${gx} ${y1}, ${x1} ${y1}`
  }
  return d
}

function MocMan({ m, i, n, chon, tiep, onChon }: {
  m: ManGame; i: number; n: number; chon: boolean; tiep: boolean; onChon: () => void
}) {
  const [x, y] = viTriMoc(i, n)
  const lop = ['g-moc', m.mo ? '' : 'khoa', chon ? 'chon' : '', m.tien_do.sao > 0 ? 'xong' : '',
               tiep && m.mo ? 'tiep' : ''].join(' ')
  return (
    <button className={lop} style={{ left: `${x}%`, top: `${y}%` }} onClick={onChon}
            title={m.mo ? `Màn ${m.id} — ${m.ten}` : `Màn ${m.id} còn khoá — xong màn trước (có ★) để mở`}>
      <span className="g-moc-dia">{m.mo ? m.id : <IconKhoa size={22} />}</span>
      <SaoGame n={m.tien_do.sao} />
      <span className="g-moc-ten">{m.ten}</span>
      <span className="g-moc-nam">năm {nam(m.thay)}</span>
    </button>
  )
}

function ChonMan({ g }: { g: Game }) {
  const b = g.boot
  const c: ChuongGame | undefined = b?.chuong.find(x => x.id === g.chuongId) ?? b?.chuong[0]
  const chon = c?.man.find(m => m.id === g.manId) ?? c?.man[0]
  useEffect(() => {
    if (chon && g.phieu?.id !== chon.id) void g.chonMan(chon.id)
    // chỉ khi đổi màn đang chọn
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chon?.id])
  if (!b || !c) {
    return <div className="g-man-hinh g-ban-do"><div className="g-dang-nap">Đang mở bản đồ…</div></div>
  }
  const p = chon && g.phieu?.id === chon.id ? g.phieu : null
  const tong = b.chuong.reduce((s, x) => s + x.sao, 0)
  return (
    <div className="g-man-hinh g-ban-do">
      <div className="g-thanh-tren">
        <button className="g-nut g-nut-nho" onClick={() => g.setManHinh('chinh')}>◂ Màn hình chính</button>
        <div className="g-thanh-tieu-de">Bản đồ chiến dịch</div>
        <div className="g-thanh-sao">{tong} ★</div>
      </div>

      <div className="g-ban-do-than">
        <div className="g-ds-chuong">
          {b.chuong.map(cc => (
            <button key={cc.id} disabled={!cc.mo}
                    className={'g-chuong' + (cc.id === c.id ? ' chon' : '') + (cc.mo ? '' : ' khoa')}
                    onClick={() => g.setChuongId(cc.id)}>
              <span className="g-chuong-so">Chương {cc.so}{!cc.mo && <IconKhoa size={13} />}</span>
              <span className="g-chuong-ten">{cc.ten}</span>
              <span className="g-chuong-phu">
                {cc.mo ? `${cc.ban_do} · ${cc.sao}/${cc.sao_toi_da} ★`
                       : cc.sap_ra_mat ? 'sắp ra mắt' : 'xong chương trước để mở'}
              </span>
              {!cc.mo && cc.mo_ta && <span className="g-chuong-mo-ta">{cc.mo_ta}</span>}
            </button>
          ))}
        </div>

        <div className="g-ban-do-giua">
          <div className="g-chuong-dau">
            {c.khach_id && <ChanDung ai={c.khach_id} size={64} />}
            <div>
              <div className="g-chuong-dau-so">CHƯƠNG {c.so} · BẢN ĐỒ {c.ban_do.toUpperCase()} ({c.symbol})</div>
              <div className="g-chuong-dau-ten">{c.ten}</div>
              {c.khach && <div className="g-chuong-dau-khach">Khách đặt máy: <b>{c.khach.ten}</b> — {c.khach.vai}</div>}
            </div>
            <span className="g-hud-day" />
            <button className="g-nut g-nut-nho" onClick={() => void g.xemTruyen(c.id, 'mo', 'chon_man')}>
              Xem lại truyện
            </button>
          </div>

          <div className="g-ban-do-khung">
            <svg className="g-ban-do-gia" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
              <polyline vectorEffect="non-scaling-stroke"
                        points="0,82 8,78 14,80 22,70 28,73 36,62 44,66 52,52 60,57 68,44 76,48 84,36 92,40 100,28" />
            </svg>
            <svg className="g-ban-do-duong" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
              <path d={duongBanDo(c.man.length)} vectorEffect="non-scaling-stroke" />
            </svg>
            {c.man.map((m, i) => (
              <MocMan key={m.id} m={m} i={i} n={c.man.length} chon={m.id === chon?.id}
                      tiep={m.id === b.man_tiep} onChon={() => void g.chonMan(m.id)} />
            ))}
          </div>
        </div>

        {chon && (
          <div className="g-xem-truoc">
            <div className="g-xt-dau">
              <span className="g-xt-so">MÀN {chon.id}</span>
              <SaoGame n={chon.tien_do.sao} />
            </div>
            <h2 className="g-xt-ten">{chon.ten}</h2>
            <div className="g-xt-nam">Vàng · năm {nam(chon.thay)} · vốn {tien(chon.von)}</div>
            <blockquote className="g-xt-loi">
              “{chon.loi_khach}”
              {c.khach && <cite>— {c.khach.ten}</cite>}
            </blockquote>
            <div className="g-xt-boss">
              <BossMuaGiu size={42} />
              <div><span>Đối thủ</span><b>{chon.boss.ten}</b></div>
            </div>
            {p && p.lich_su.length > 0 ? (
              <Histogram ten="Lãi % các lần ▶ đầy đủ" donVi="%" giaTri={p.lich_su.map(l => l.lai_pt)}
                         cuaBan={p.lich_su[0].lai_pt} boss={p.lich_su[0].mua_giu_pt} tot="cao" />
            ) : (
              <div className="g-xt-trong">Chưa chạy lần nào trên màn này.</div>
            )}
            <div className="g-xt-ky-luc">
              {chon.tien_do.so_lan_nop
                ? `Đã nộp ${chon.tien_do.so_lan_nop} lần · tốt nhất ${'★'.repeat(chon.tien_do.sao) || '0 ★'}`
                : 'Chưa nộp lần nào'}
            </div>
            <button className="g-nut g-nut-lon" disabled={!chon.mo} onClick={() => void g.moPhieu(chon.id)}>
              {chon.mo ? 'Nhận việc ▸' : 'Còn khoá'}
            </button>
            {!chon.mo && <div className="g-xt-khoa">Xong màn trước (nộp được ít nhất ★) để mở.</div>}
          </div>
        )}
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  3 · Truyện — mở / đóng chương
 * ======================================================================= */

function Truyen({ g }: { g: Game }) {
  const t = g.truyen
  const [hien, setHien] = useState(0)
  const l = t?.loi[t.k]
  const du = l ? hien >= l.loi.length : true

  /* Chữ hiện dần như máy đánh chữ. Bấm khi đang hiện = hiện hết; bấm lần nữa = sang câu. */
  useEffect(() => {
    setHien(0)
    if (!l) return
    const id = window.setInterval(() => {
      setHien(h => {
        if (h >= l.loi.length) { window.clearInterval(id); return h }
        return h + 2
      })
    }, 16)
    return () => window.clearInterval(id)
  }, [l])

  const tiep = () => {
    if (!l) return
    if (!du) setHien(l.loi.length)
    else void g.truyenTiep()
  }
  /* Phím đi qua ref: chữ hiện dần làm màn này vẽ lại 60 lần/giây — gắn lại listener mỗi
     lần như thế là thừa. */
  const phim = useRef({ tiep, boQua: g.boQuaTruyen })
  phim.current = { tiep, boQua: g.boQuaTruyen }

  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); phim.current.tiep() }
      else if (e.key === 'Escape') { e.preventDefault(); void phim.current.boQua() }
    }
    window.addEventListener('keydown', f)
    return () => window.removeEventListener('keydown', f)
  }, [])

  if (!t || !l) return null
  const c = g.boot?.chuong.find(x => x.id === t.chuong)
  const vai = ['meo', ...new Set(t.loi.map(x => x.ai).filter(a => a !== 'meo'))]
  return (
    <div className="g-man-hinh g-truyen" onClick={tiep}>
      <CanhTiemVang />
      <div className="g-truyen-tieu-de">
        {c ? `Chương ${c.so} · ${c.ten}` : ''}{t.phan === 'dong' ? ' — khép chương' : ''}
      </div>
      <div className="g-truyen-vai">
        {vai.map((ai, i) => (
          <div key={ai} className={'g-vai ' + (i === 0 ? 'trai' : 'phai') + (ai === l.ai ? ' noi' : ' im')}>
            <ChanDung ai={ai} size={230} />
          </div>
        ))}
      </div>
      <div className="g-hoi-thoai" onClick={e => { e.stopPropagation(); tiep() }}>
        <div className="g-hoi-ten">{l.ten}<span>{l.vai}</span></div>
        <div className="g-hoi-chu">{l.loi.slice(0, hien)}<span className="g-hoi-con">{l.loi.slice(hien)}</span></div>
        <div className="g-hoi-chan">
          <span className="g-hoi-cham">
            {t.loi.map((_, i) => <i key={i} className={i <= t.k ? 'co' : ''} />)}
          </span>
          <span className="g-hoi-meo">Space / Enter để tiếp · Esc bỏ qua</span>
          <button className="g-nut g-nut-nho" onClick={e => { e.stopPropagation(); void g.boQuaTruyen() }}>
            Bỏ qua
          </button>
          <button className="g-nut" onClick={e => { e.stopPropagation(); tiep() }}>
            {t.k + 1 < t.loi.length || !du ? 'Tiếp ▸' : 'Vào việc ▸'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  4 · Phiếu việc — đề bài của một màn
 * ======================================================================= */

function PhieuViec({ g, coSoDo, tenMay }: { g: Game; coSoDo: boolean; tenMay: string }) {
  const m = g.phieu
  if (!m) return <div className="g-man-hinh g-phieu-nen"><div className="g-dang-nap">Đang mở phiếu…</div></div>
  const c = g.boot?.chuong.find(x => x.id === m.chuong)
  const n = nam(m.thay)
  const td = m.tien_do
  return (
    <div className="g-man-hinh g-phieu-nen">
      <div className="g-phieu">
        <div className="g-phieu-dau">
          <div>
            <div className="g-phieu-loai">PHIẾU ĐẶT MÁY · {c ? `Chương ${c.so}` : ''} · Màn {m.id}</div>
            <h1 className="g-phieu-ten">{m.ten}</h1>
          </div>
          <SaoGame n={td.sao} to />
        </div>

        <div className="g-phieu-khach">
          <ChanDung ai={c?.khach_id ?? 'meo'} size={76} />
          <blockquote>
            “{m.loi_khach}”
            <cite>— {c?.khach?.ten ?? 'Khách'}, {c?.khach?.vai ?? ''}</cite>
          </blockquote>
        </div>

        <div className="g-phieu-luoi">
          <section>
            <h3>Yêu cầu</h3>
            <div className="g-phieu-boss">
              <BossMuaGiu size={58} />
              <div>
                Lãi hơn boss <b>«{m.boss.ten}»</b>
                <div className="g-phieu-mo">{m.boss.mo_ta}</div>
              </div>
            </div>
            <table className="g-phieu-bang">
              <tbody>
                <tr><td>Thị trường</td><td>Vàng · {m.symbol} · vốn {tien(m.von)}</td></tr>
                <tr><td>▶ nhanh</td><td>{ngay(m.nhanh[0])} → {ngay(m.nhanh[1])}</td></tr>
                <tr><td>▶ đầy đủ</td><td>{ngay(m.thay[0])} → {ngay(m.thay[1])} · có vé nộp</td></tr>
                <tr><td>Nộp</td><td><b>Màn ẩn</b> — {anMoTa(m.an_mo_ta, n)}. App giữ ngày, không cho xem nến.</td></tr>
              </tbody>
            </table>
          </section>

          <section>
            <h3>Giác quan được dùng</h3>
            <div className="g-phieu-chip">{m.giac_quan.map(gq => <ChipGiacQuan key={gq.key} gq={gq} />)}</div>
            <div className="g-phieu-mo">Cỗ máy chỉ được hỏi những thứ này. Giác quan mở dần theo màn.</div>
            <h3>Sao</h3>
            <ul className="g-phieu-sao">
              {LUAT_SAO(n).map(([s, ten, mo], i) => (
                <li key={i} className={td.sao > i ? 'dat' : ''}>
                  <span className="g-phieu-sao-k">{s}</span><b>{ten}</b> — {mo}
                </li>
              ))}
            </ul>
          </section>
        </div>

        <div className="g-phieu-goi-y">
          <MeoTho size={50} />
          <div><b>Mèo Thợ Cả:</b> {m.goi_y}</div>
        </div>

        {td.so_lan_nop > 0 && (
          <div className="g-phieu-ky-luc">
            Đã nộp {td.so_lan_nop} lần · tốt nhất {'★'.repeat(td.sao) || '0 ★'}
            {td.tot_nhat ? ` · độ gọn ${td.tot_nhat.do_gon.tong}` : ''}
          </div>
        )}

        <div className="g-phieu-chan">
          <button className="g-nut g-nut-nho" onClick={() => void g.veBanDo()}>◂ Bản đồ</button>
          <span className="g-hud-day" />
          <button className="g-nut" onClick={() => void g.vaoXuong('trang')}>Sơ đồ trắng</button>
          {coSoDo && (
            <button className={'g-nut' + (m.may_goi_y ? '' : ' g-nut-lon')}
                    onClick={() => void g.vaoXuong('giu')}>
              Giữ cỗ máy đang vẽ «{tenMay}» ▸
            </button>
          )}
          {m.may_goi_y && (
            <button className="g-nut g-nut-lon" onClick={() => void g.vaoXuong('goi_y')}>
              Lắp máy gợi ý «{m.may_goi_y_ten ?? m.may_goi_y}» ▸
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  5 · Kết quả — ba histogram
 * ======================================================================= */

function SoLieu({ x }: { x: KetQuaQC }) {
  const t = x.thong_ke
  return (
    <div className="g-kq-so-lieu">
      <div><span>Lệnh</span><b>{t.so_lenh}</b></div>
      <div><span>Thắng / thua</span><b>{t.thang} / {t.thua}</b></div>
      <div><span>Tỉ lệ thắng</span><b>{t.ty_le_thang.toFixed(1)} %</b></div>
      <div><span>Sụt giảm tối đa</span><b>{t.drawdown_pt.toFixed(2)} %</b></div>
      <div><span>Vốn cuối</span><b>{tien(t.von_cuoi)}</b></div>
      <div><span>Độ gọn</span><b>{x.do_gon.tong}</b></div>
    </div>
  )
}

function KetQua({ g }: { g: Game }) {
  const x = g.kq
  const veXuong = g.setManHinh
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape') veXuong('xuong') }
    window.addEventListener('keydown', f)
    return () => window.removeEventListener('keydown', f)
  }, [veXuong])
  if (!x) return null
  const c = x.cham ?? { lai_pt: x.thong_ke.lai_pt, mua_giu_pt: x.mua_giu_pt, thang_boss: false,
                        so_dong: x.thong_ke.so_dong, sach: x.thong_ke.so_dong > 0,
                        sut_giam: x.thong_ke.drawdown_pt }
  const day = x.loai === 'day_du'
  const ls = (g.phieu?.id === x.man ? g.phieu?.lich_su : null) ?? []
  const ve = g.phieu?.ve_nop
  const phanDinh = c.mua_giu_pt == null ? ['hoa', 'KHÔNG CÓ GIÁ BOSS'] : c.thang_boss
    ? ['thang', 'THẮNG BOSS'] : ['thua', 'THUA BOSS']
  return (
    <div className="g-man-hinh g-lop-kq">
      <div className="g-kq">
        <div className="g-kq-dau">
          <div>
            <div className="g-kq-loai">
              {day ? '▶ ĐẦY ĐỦ' : '▶ NHANH'} · màn {x.man} · {ngay(x.tu)} → {ngay(x.den)}
            </div>
            <h2 className="g-kq-ten">{x.ten}</h2>
          </div>
          {day && (
            <div className="g-kq-sao">
              <SaoGame n={x.sao ?? 0} to />
              <small>trên năm đã thấy · ★★★ chỉ có khi nộp</small>
            </div>
          )}
        </div>

        <div className="g-kq-doi">
          <div className="g-kq-ben">
            <span className="g-kq-nhan">Cỗ máy</span>
            <span className={'g-kq-so ' + (c.lai_pt >= 0 ? 'lai' : 'lo')}>{pt(c.lai_pt)}</span>
          </div>
          <div className={'g-kq-phan-dinh ' + phanDinh[0]}>{phanDinh[1]}</div>
          <div className="g-kq-ben boss">
            <BossMuaGiu size={46} />
            <div>
              <span className="g-kq-nhan">Mua rồi giữ</span>
              <span className={'g-kq-so ' + ((c.mua_giu_pt ?? 0) >= 0 ? 'lai' : 'lo')}>{pt(c.mua_giu_pt)}</span>
            </div>
          </div>
        </div>

        {day ? (
          <div className="g-kq-histo">
            <Histogram ten="Lãi %" donVi="%" giaTri={ls.map(l => l.lai_pt)} cuaBan={c.lai_pt}
                       boss={c.mua_giu_pt} tot="cao" />
            <Histogram ten="Sụt giảm %" donVi="%" giaTri={ls.map(l => l.sut_giam)}
                       cuaBan={c.sut_giam ?? x.thong_ke.drawdown_pt} tot="thap" />
            <Histogram ten="Độ gọn" donVi="" giaTri={ls.map(l => l.do_gon)} cuaBan={x.do_gon.tong}
                       tot="thap" so={0} />
          </div>
        ) : (
          <div className="g-kq-nhanh">
            ▶ nhanh chỉ chạy quý 4 cho nhanh. Histogram và <b>vé nộp</b> cần ▶ đầy đủ cả năm.
          </div>
        )}

        <div className="g-kq-duoi">
          <div className="g-kq-von">
            <div className="g-kq-von-nhan">Đường vốn</div>
            <DuongVonNho diem={x.duong_von} vonDau={x.thong_ke.von_dau} rong={330} cao={70}
                         tDau={x.t_dau} tCuoi={x.t_cuoi} />
          </div>
          <SoLieu x={x} />
        </div>

        <div className="g-kq-chan">
          {x.url && (
            <button className="g-nut g-nut-nho" onClick={() => void pyGame.moWeb(x.url!)}
                    title="Mở backtest này trên trang QuantConnect">Mở trên QC ↗</button>
          )}
          <span className="g-hud-day" />
          <button className="g-nut" onClick={() => g.setManHinh('xuong')}>Sửa tiếp</button>
          <button className="g-nut" onClick={() => void g.xemMayNghi(true)}>Xem máy nghĩ ▸</button>
          {day && (
            <button className="g-nut g-nut-lon g-nut-nop" disabled={!ve} onClick={g.moNop}
                    title={ve ? 'Đấu màn ẩn với cỗ máy này'
                              : 'Cỗ máy đã đổi từ lúc chạy — chạy ▶ đầy đủ lại để có vé'}>
              Nộp ↑
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  6 · Đấu màn ẩn (nộp)
 * ======================================================================= */

function GiaiThichSao({ sao, n }: { sao: number; n: string }) {
  const chu = [
    `Lượt ▶ đầy đủ năm ${n} chưa có lệnh nào đóng — chưa chạy sạch.`,
    `★ chạy sạch. Trên năm ${n} cỗ máy chưa hơn boss — ★★ cần thắng boss năm đó.`,
    '★★ thắng boss trên năm đã thấy. Trên màn ẩn boss hơn — ★★★ cần thắng cả ở đây.',
    '★★★ — cỗ máy thắng boss cả trên năm nó chưa từng thấy.',
  ][Math.max(0, Math.min(3, sao))]
  return <div className="g-dau-giai">{chu}</div>
}

function DauManAn({ g, tenMay }: { g: Game; tenMay: string }) {
  const m = g.phieu ?? g.man
  const x = g.nop
  const tt = g.tt
  const dangChay = !!tt?.dang_chay && tt.loai === 'nop'
  const ve = g.phieu?.ve_nop ?? x?.thay ?? null
  const gon = g.phieu?.do_gon?.tong
  const n = nam(m?.thay)
  const [lo, setLo] = useState(false)
  /* Lật điểm xong (~1,5 giây) mới hiện phán định + sao — cho kịp hồi hộp. */
  useEffect(() => {
    setLo(false)
    if (!x) return
    const id = window.setTimeout(() => setLo(true), 1600)
    return () => window.clearTimeout(id)
  }, [x])
  const thang = !!x?.cham?.thang_boss
  return (
    <div className="g-man-hinh g-dau">
      <div className="g-dau-tieu-de">
        <span>ĐẤU MÀN ẨN</span>
        Màn {m?.id} · {m?.ten} — {m ? anMoTa(m.an_mo_ta, n) : ''}
      </div>

      <div className={'g-dau-san' + (dangChay ? ' dang' : '') + (lo ? (thang ? ' ban-thang' : ' boss-thang') : '')}>
        <div className="g-dau-ben ban">
          <div className="g-dau-hinh"><LogoGame size={150} /></div>
          <div className="g-dau-ten">{tenMay}</div>
          <div className="g-dau-phu">cỗ máy của bạn{gon != null ? ` · độ gọn ${gon}` : ''}</div>
          <div className="g-dau-so">{x ? <DemSo v={x.cham?.lai_pt} /> : <span className="g-dau-cho">?</span>}</div>
        </div>
        <div className="g-dau-vs">VS</div>
        <div className="g-dau-ben boss">
          <div className="g-dau-hinh"><BossMuaGiu size={150} /></div>
          <div className="g-dau-ten">{m?.boss.ten}</div>
          <div className="g-dau-phu">{m?.boss.mo_ta}</div>
          <div className="g-dau-so">{x ? <DemSo v={x.cham?.mua_giu_pt} /> : <span className="g-dau-cho">?</span>}</div>
        </div>
      </div>

      {ve && (
        <div className="g-dau-thay">
          Năm đã thấy ({n}): cỗ máy {pt(ve.lai_pt)} · boss {pt(ve.mua_giu_pt)}
          {ve.thang_boss ? ' — đã thắng' : ' — chưa thắng'}
        </div>
      )}

      {!x && !dangChay && !g.loi && (
        <div className="g-dau-chan">
          <div className="g-dau-luat">
            App chạy cỗ máy trên 12 tháng nó chưa từng thấy. Chỉ có điểm — không ngày, không nến,
            không link. Đây sẽ là lần nộp thứ {(m?.tien_do.so_lan_nop ?? 0) + 1} của màn này.
          </div>
          <div className="g-dau-nut">
            <button className="g-nut" onClick={() => g.setManHinh('xuong')}>◂ Về xưởng</button>
            <button className="g-nut g-nut-lon g-nut-nop" disabled={!ve} onClick={() => void g.chay('nop')}>
              Bắt đầu đấu ▸
            </button>
          </div>
        </div>
      )}

      {dangChay && (
        <div className="g-dau-chan">
          <div className="g-dau-buoc">{tt?.chu ?? '…'}{tt?.giay != null ? ` · ${Math.round(tt.giay)} giây` : ''}</div>
          <div className="g-thanh to"><div className="g-thanh-day" style={{ width: `${Math.round((tt?.ti_le_chung ?? 0) * 100)}%` }} /></div>
        </div>
      )}

      {g.loi && !dangChay && (
        <div className="g-dau-chan">
          <div className="g-dau-loi">{g.loi}</div>
          <div className="g-dau-nut">
            <button className="g-nut" onClick={() => { g.setLoi(''); g.setManHinh('xuong') }}>◂ Về xưởng</button>
          </div>
        </div>
      )}

      {x && lo && (
        <div className="g-dau-chan g-dau-ket">
          <div className={'g-dau-phan-dinh ' + (thang ? 'thang' : 'thua')}>
            {thang ? 'CỖ MÁY THẮNG' : 'BOSS THẮNG'}
          </div>
          <SaoGame n={x.sao ?? 0} to hieuUng />
          <GiaiThichSao sao={x.sao ?? 0} n={n} />
          <div className="g-dau-lan">Lần nộp thứ {x.lan_nop}</div>
          <div className="g-dau-nut">
            <button className="g-nut g-nut-lon" onClick={() => void g.sauNop()}>Tiếp tục ▸</button>
          </div>
        </div>
      )}
    </div>
  )
}

/* ======================================================================= *
 *  7 · Hoàn thành màn
 * ======================================================================= */

function HoanThanh({ g }: { g: Game }) {
  const h = g.hoanThanh
  if (!h) return null
  const c = g.boot?.chuong.find(x => x.id === h.man.chuong)
  const xong = c?.man.filter(m => m.tien_do.sao >= 1).length ?? 0
  const tong = c?.man.length ?? 0
  const moi = h.manTiep?.giac_quan.filter(x => x.moi) ?? []
  const loiMeo = h.sao >= 3
    ? 'Ba sao. Cỗ máy này không học thuộc đề — nó thắng cả năm nó chưa từng thấy.'
    : 'Màn đã qua. Muốn ★★★ thì cỗ máy phải thắng cả năm nó chưa thấy — quay lại lúc nào cũng được.'
  return (
    <div className="g-man-hinh g-xong">
      <div className="g-xong-the">
        <div className="g-xong-nhan">MÀN {h.man.id} HOÀN THÀNH</div>
        <h1 className="g-xong-ten">{h.man.ten}</h1>
        <SaoGame n={h.sao} to hieuUng />
        <div className="g-xong-phu">sau {h.lanNop} lần nộp</div>

        {h.manTiep && (
          <div className="g-mo-khoa">
            <div className="g-mo-khoa-nhan">ĐÃ MỞ KHOÁ</div>
            <div className="g-mo-khoa-man">
              Màn {h.manTiep.id} · <b>{h.manTiep.ten}</b> · năm {nam(h.manTiep.thay)}
            </div>
            {moi.length > 0 && (
              <div className="g-mo-khoa-gq">
                <span>Giác quan mới</span>
                {moi.map(gq => <ChipGiacQuan key={gq.key} gq={gq} />)}
              </div>
            )}
          </div>
        )}
        {h.xongChuong && (
          <div className="g-mo-khoa">
            <div className="g-mo-khoa-nhan">XONG CHƯƠNG {c?.so}</div>
            <div className="g-mo-khoa-man">{c?.ten} — mọi màn đã có sao.</div>
          </div>
        )}

        <div className="g-xong-chuong">
          <div>Chương {c?.so} · {c?.ten}: {xong}/{tong} màn · {c?.sao}/{c?.sao_toi_da} ★</div>
          <div className="g-thanh"><div className="g-thanh-day" style={{ width: `${tong ? (xong / tong) * 100 : 0}%` }} /></div>
        </div>

        <div className="g-xong-meo">
          <MeoTho size={54} />
          <p>{loiMeo}</p>
        </div>

        <div className="g-xong-chan">
          <button className="g-nut" onClick={() => void g.sauHoanThanh(false)}>Về bản đồ</button>
          {h.manTiep && (
            <button className="g-nut g-nut-lon" onClick={() => void g.sauHoanThanh(true)}>
              Màn tiếp ▸
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

/* ======================================================================= *
 *  Vỏ: màn hình nào đang mở
 * ======================================================================= */

export default function ManHinhGame({ g, moKhoa, coSoDo, tenMay }: {
  g: Game
  moKhoa: () => void
  /** Cỗ máy đang vẽ có khối nào ngoài khối Bắt đầu không — để mời "giữ cỗ máy đang vẽ". */
  coSoDo: boolean
  tenMay: string
}) {
  if (!g.bat || g.manHinh === 'xuong') return null
  switch (g.manHinh) {
    case 'chinh': return <ManHinhChinh g={g} moKhoa={moKhoa} />
    case 'chon_man': return <ChonMan g={g} />
    case 'truyen': return <Truyen g={g} />
    case 'phieu': return <PhieuViec g={g} coSoDo={coSoDo} tenMay={tenMay} />
    case 'ket_qua': return <KetQua g={g} />
    case 'nop': return <DauManAn g={g} tenMay={tenMay} />
    case 'hoan_thanh': return <HoanThanh g={g} />
    default: return null
  }
}
