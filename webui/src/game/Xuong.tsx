import type { ReactNode } from 'react'
import type { Tab } from '../types'
import type { Game } from './useGame'
import { IconLinhKien, MeoTho } from './HinhVe'
import { DuongVonNho, SaoGame } from './BieuDo'
import { gio, nam, ngay } from './dinh_dang'

/** XƯỞNG — trình vẽ sơ đồ khối CHÍNH LÀ bàn thợ của game ("vẽ sơ đồ kiểu này vẫn rất
 *  hay, đừng bỏ"). Ở chế độ game, dải ribbon nhường chỗ cho thanh xưởng này: khay linh
 *  kiện bên trái (như khay cánh tay / glyph của Opus Magnum), nút chạy bên phải. Mọi nút
 *  trỏ về ĐÚNG những hàm ribbon đang gọi — hai lối vào không thể lệch nhau. */

function LinhKien({ loai, ten, phu, onClick, title }: {
  loai: string; ten: string; phu: string; onClick: () => void; title: string
}) {
  return (
    <button className="g-lk" onClick={onClick} title={title}>
      <span className="g-lk-hinh"><IconLinhKien loai={loai} size={26} /></span>
      <span className="g-lk-ten">{ten}</span>
      <span className="g-lk-phu">{phu}</span>
    </button>
  )
}

function Nhom({ ten, children, lop = '' }: { ten: ReactNode; children: ReactNode; lop?: string }) {
  return (
    <div className={'g-hud-nhom ' + lop}>
      <div className="g-hud-cac">{children}</div>
      <div className="g-hud-nhan">{ten}</div>
    </div>
  )
}

export function GameHud({ g, tab, themMat, themTayVao, themTaySua, moThamSo, hoanTac, lamLai,
                          coLui, coToi, vuaKhung, soLoi, moKhoa }: {
  g: Game
  tab: Tab
  themMat: () => void
  themTayVao: () => void
  themTaySua: () => void
  moThamSo: () => void
  hoanTac: () => void
  lamLai: () => void
  coLui: boolean
  coToi: boolean
  vuaKhung: () => void
  soLoi: number
  moKhoa: () => void
}) {
  const m = g.phieu ?? g.man
  const ve = g.phieu?.ve_nop ?? null
  const gon = g.phieu?.do_gon ?? null
  const chay = g.dangChay
  const khoaCo = g.boot?.khoa.co ?? true
  const n = nam(m?.thay)
  const loiTruoc = soLoi > 0 ? `Sơ đồ còn ${soLoi} lỗi — xem bảng Vấn đề bên dưới. ` : ''
  return (
    <div className="g-hud">
      <button className="g-hud-ve" onClick={() => void g.veBanDo()} title="Về bản đồ chương">
        <span>◂</span> Bản đồ
      </button>

      <button className="g-hud-man" onClick={() => m && void g.moPhieu(m.id)}
              title="Mở lại phiếu việc của màn này">
        <span className="g-hud-so">{m?.id ?? '—'}</span>
        <span className="g-hud-chu">
          <span className="g-hud-ten">{m?.ten ?? 'Chưa chọn màn'}</span>
          <span className="g-hud-phu">Vàng · năm {n} · đối thủ: {m?.boss.ten ?? '—'}</span>
        </span>
        <SaoGame n={m?.tien_do.sao ?? 0} />
      </button>

      <Nhom ten="Linh kiện">
        <LinhKien loai="mat" ten="Mắt" phu="hỏi một câu" onClick={themMat}
                  title="Thêm khối Kiểm tra điều kiện — cỗ máy NHÌN thị trường và hỏi một câu. Nhiều mắt nối từ một khối = rẽ nhánh." />
        {tab === 'entry'
          ? <LinhKien loai="tay_vao" ten="Tay vào lệnh" phu="Mua · Bán" onClick={themTayVao}
                      title="Thêm khối Vào lệnh — tay đặt lệnh Mua/Bán, kèm SL và TP." />
          : <LinhKien loai="tay_sua" ten="Tay chỉnh lệnh" phu="dời SL · đóng" onClick={themTaySua}
                      title="Thêm khối Sửa lệnh — tay chỉnh lệnh đang chạy: dời SL, hoà vốn, đóng." />}
        <LinhKien loai="tham_so" ten="Núm vặn" phu="tham số" onClick={moThamSo}
                  title="Bảng tham số — những con số có tên của cỗ máy (chu kỳ MA, SL…)." />
      </Nhom>

      <Nhom ten="Bàn thợ">
        <button className="g-nut-tron" onClick={hoanTac} disabled={!coLui} title="Hoàn tác (Ctrl+Z)">↶</button>
        <button className="g-nut-tron" onClick={lamLai} disabled={!coToi} title="Làm lại (Ctrl+Y)">↷</button>
        <button className="g-nut-tron" onClick={vuaKhung} title="Thu cả cỗ máy vào khung">⤢</button>
      </Nhom>

      <Nhom lop="g-hud-gon"
            ten={gon ? `${gon.so_khoi} khối + ${gon.so_tham_so} núm` : 'độ gọn'}>
        <div className="g-dong-ho" title="Độ gọn = số khối + số tham số. Ít hơn là gọn hơn — một cột histogram, không cộng vào sao.">
          <span className="g-dong-ho-so">{gon?.tong ?? '—'}</span>
          <span className="g-dong-ho-nhan">ĐỘ GỌN</span>
        </div>
      </Nhom>

      <span className="g-hud-day" />

      {!khoaCo && (
        <button className="g-canh-khoa" onClick={moKhoa}
                title="App cần khoá API QuantConnect để chạy cỗ máy trên QC">
          Chưa có khoá QC — đặt khoá
        </button>
      )}

      <div className="g-hud-chay">
        <button className="g-nut g-nut-thu" disabled={chay} onClick={() => void g.chay('nhanh')}
                title={loiTruoc + `Chạy thử nhanh trên quý 4 năm ${n} (${ngay(m?.nhanh[0])} → ${ngay(m?.nhanh[1])}).`}>
          ▶ nhanh<small>quý 4 · {n}</small>
        </button>
        <button className="g-nut g-nut-thu" disabled={chay} onClick={() => void g.chay('day_du')}
                title={loiTruoc + `Chạy trọn năm ${n} — có histogram và có VÉ NỘP cho đúng cỗ máy này.`}>
          ▶ đầy đủ<small>cả năm {n}</small>
        </button>
        <button className={'g-nut g-nut-nop' + (ve ? ' san' : '')} disabled={chay || !ve}
                onClick={g.moNop}
                title={ve ? 'Nộp cỗ máy này — app chấm trên MÀN ẨN (12 tháng ngay sau năm này).'
                          : 'Chưa có vé nộp: chạy ▶ đầy đủ ĐÚNG cỗ máy này trước (sửa một khối là cỗ máy khác).'}>
          Nộp ↑<small>{ve ? 'đấu màn ẩn' : 'cần ▶ đầy đủ'}</small>
        </button>
      </div>
    </div>
  )
}

/** Thẻ "đang chạy trên QuantConnect" — nổi góc phải canvas, không che sơ đồ. */
export function TheDangChay({ g }: { g: Game }) {
  const tt = g.tt
  if (!tt?.dang_chay || tt.loai === 'nop') return null
  const tl = Math.round((tt.ti_le_chung ?? 0) * 100)
  return (
    <div className="g-the-chay">
      <div className="g-banh-rang" aria-hidden>
        <svg viewBox="0 0 40 40" width="34" height="34">
          <g className="g-quay">
            {Array.from({ length: 8 }, (_, k) => (
              <rect key={k} x="17" y="1" width="6" height="8" rx="1.5"
                    transform={`rotate(${k * 45} 20 20)`} />
            ))}
            <circle cx="20" cy="20" r="12" />
          </g>
          <circle cx="20" cy="20" r="4.5" className="g-truc" />
        </svg>
      </div>
      <div className="g-the-chay-than">
        <div className="g-the-chay-dau">
          {tt.loai === 'nhanh' ? '▶ nhanh' : '▶ đầy đủ'} đang chạy trên QuantConnect
        </div>
        <div className="g-the-chay-buoc">{tt.chu ?? '…'}{tt.giay != null ? ` · ${Math.round(tt.giay)} giây` : ''}</div>
        <div className="g-thanh"><div className="g-thanh-day" style={{ width: `${tl}%` }} /></div>
      </div>
    </div>
  )
}

/** Lỗi của lượt bấm vừa rồi (sơ đồ còn lỗi, chưa có khoá, giác quan chưa mở…). */
export function ToastLoi({ g, moKhoa }: { g: Game; moKhoa: () => void }) {
  if (!g.loi || g.manHinh !== 'xuong') return null
  const veKhoa = /khoá|khoa|token|User ID/i.test(g.loi)
  return (
    <div className="g-toast">
      <div className="g-toast-dau">
        <MeoTho size={34} />
        <b>Mèo Thợ Cả: chưa chạy được</b>
        <button className="g-toast-tat" onClick={() => g.setLoi('')} title="Đóng">✕</button>
      </div>
      <div className="g-toast-chu">{g.loi}</div>
      {veKhoa && <button className="g-nut g-nut-nho" onClick={moKhoa}>Đặt khoá QC…</button>}
    </div>
  )
}

/** XEM MÁY NGHĨ — phát lại từng lượt cỗ máy đã nghĩ, tô đường đi ngay trên sơ đồ.
 *  Thanh này là "dòng thời gian" của game: kéo được, phát được, nhanh chậm được. */
export function ThanhXem({ g, tenKhoi }: {
  g: Game
  /** Tên khối theo id — lấy từ sơ đồ đang vẽ (cả hai tab). */
  tenKhoi: (id: string) => string | null
}) {
  const p = g.phat
  if (!p) return null
  const d = p.ds[p.k]
  const kq = g.kq
  /* Đường cỗ máy đi trong lượt này, bằng TÊN khối người chơi đặt: cổng qua ✓, cổng trượt
     ✗ (cổng trượt không nằm trong đường đi nên nối thêm vào cuối). Dòng chữ máy ghi
     (`chu`) vẫn ở dưới cho ai cần con số. */
  const l = p.luot
  const cong = new Map((l?.cong ?? []).map(c => [c.khoi, c.khop]))
  const buoc = l ? [...l.duong, ...(l.cong ?? []).filter(c => !c.khop && !l.duong.includes(c.khoi))
                                               .map(c => c.khoi)] : []
  return (
    <div className="g-xem">
      <div className="g-xem-nghi">
        <div className="g-xem-meo"><MeoTho size={40} /></div>
        <div className="g-xem-bong">
          <div className="g-xem-gio">
            {gio(d?.t)} · {d?.tab === 'manage' ? 'trông lệnh' : 'đi săn'}
            {d?.lenh_id ? ` · lệnh ${d.lenh_id}` : ''}
          </div>
          {buoc.length > 0 && (
            <div className="g-xem-duong">
              {buoc.map((id, i) => {
                const k = cong.get(id)
                return (
                  <span key={id + i} className="g-xem-buoc-boc">
                    {i > 0 && <span className="g-xem-mui">→</span>}
                    <span className={'g-xem-buoc' + (k === true ? ' qua' : k === false ? ' truot' : '')}>
                      {tenKhoi(id) ?? l?.nhan[id] ?? id}{k === true ? ' ✓' : k === false ? ' ✗' : ''}
                    </span>
                  </span>
                )
              })}
              {cong.size > 0 && [...cong.values()].some(v => !v) && <span className="g-xem-dung">— dừng ở đây</span>}
            </div>
          )}
          <div className="g-xem-chu">{p.chu || '…'}</div>
        </div>
      </div>
      <div className="g-xem-dieu-khien">
        <button className="g-nut-tron" onClick={() => void g.nhayPhat(0)} title="Về lượt đầu">⏮</button>
        <button className="g-nut-tron" onClick={() => void g.buocPhat(-1)} title="Lượt trước">◀</button>
        <button className="g-nut-tron to" onClick={() => g.datPhat({ phat: !p.phat })}
                title={p.phat ? 'Dừng' : 'Phát'}>{p.phat ? '❚❚' : '▶'}</button>
        <button className="g-nut-tron" onClick={() => void g.buocPhat(1)} title="Lượt sau">▶</button>
        <button className="g-nut-tron" onClick={() => void g.nhayPhat(p.ds.length - 1)} title="Về lượt cuối">⏭</button>
        <select className="g-chon" value={p.toc} onChange={e => g.datPhat({ toc: Number(e.target.value) })}
                title="Tốc độ phát">
          {[1, 2, 4, 8].map(v => <option key={v} value={v}>×{v}</option>)}
        </select>
        <div className="g-xem-truc">
          <input type="range" min={0} max={Math.max(0, p.ds.length - 1)} value={p.k}
                 onChange={e => void g.nhayPhat(Number(e.target.value))} />
          <div className="g-xem-dem">
            lượt {p.k + 1} / {p.ds.length}
            {p.tong > p.ds.length ? ` (đã tải ${p.ds.length} trong ${p.tong})` : ''}
            {p.chiViec ? ' · chỉ lượt có việc' : ' · mọi lượt'}
          </div>
        </div>
        {kq && kq.duong_von.length > 0 && (
          <div className="g-xem-von" title="Đường vốn — vạch dọc là giờ đang xem">
            <DuongVonNho diem={kq.duong_von} vonDau={kq.thong_ke.von_dau} rong={180} cao={40}
                         tDau={kq.t_dau} tCuoi={kq.t_cuoi} viTri={d?.t ?? null} />
          </div>
        )}
        <label className="g-xem-loc" title="Bỏ chọn để xem cả những lượt cỗ máy chỉ nhìn rồi thôi">
          <input type="checkbox" checked={p.chiViec}
                 onChange={e => void g.xemMayNghi(e.target.checked)} /> chỉ lượt có việc
        </label>
        <button className="g-nut g-nut-nho" onClick={() => g.setManHinh('ket_qua')}
                title="Về bảng kết quả">Kết quả</button>
        <button className="g-nut-tron" onClick={g.tatPhat} title="Thôi xem (Esc)">✕</button>
      </div>
    </div>
  )
}
