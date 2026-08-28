import type { KetQuaTest } from '../types'

/** KẾT QUẢ ▶ Test — thay chỗ cửa sổ Strategy Tester cũ.
 *
 *  ⚠ Cửa sổ cũ (2.033 dòng + 720 dòng API) vẽ NẾN và hộp zone. Không một dòng nào dùng
 *  lại được: màn hình của market maker hỏi những câu khác hẳn. Đây là bản tối thiểu trả
 *  lời được bốn câu, theo đúng thứ tự người ta hỏi:
 *
 *    1. **Có lãi không?**          → dòng RÒNG
 *    2. **Nếu không thì vì sao?**  → tách GỘP ⟷ PHÍ. Hai nguyên nhân này cần hai cách
 *                                     chữa khác hẳn nhau, mà một con số lãi lỗ thì trộn
 *                                     chúng lại và không nói gì.
 *    3. **Gộp âm là do đâu?**      → MARKOUT. Đây là con số quan trọng nhất trên màn
 *                                     hình, xem chú thích ở `bo_chay.MARKOUT_MS`.
 *    4. **Chỗ nào không tin được?** → dòng ⚠, dải MÙ trên biểu đồ, số lần bị từ chối.
 *
 *  Và bốn GIẢ ĐỊNH luôn hiện ngay cạnh kết quả, không giấu trong Cài đặt: một bảng lãi
 *  lỗ không nói nó giả định gì thì không đọc được, mà tệ hơn là nó trông như sự thật.
 *
 *  KHÔNG có ở đây, và cố ý: thang báo giá hai bên, tua từng lượt, soi một sự kiện. Cả
 *  ba đều cần một CON TRỎ THỜI GIAN và phát lại được từng bước — đó là ổ cắm "soi một
 *  lượt", việc khác. Xem `tai_lieu/o_cam_trong.md`.
 */

const CAO_BD = 78          // chiều cao logic của mỗi biểu đồ trong viewBox
const RONG_BD = 1000

/** Gộp mẫu về ~2 điểm mỗi pixel, GIỮ CẢ ĐỈNH LẪN ĐÁY của từng nhóm.
 *
 *  ⚠ Lấy mẫu thưa kiểu "mỗi N điểm lấy một" sẽ NUỐT MẤT cú sụt sâu nhất — mà đó đúng là
 *  thứ người ta cần thấy. Giữ min và max của mỗi nhóm thì đường vẫn chạm đủ hai biên,
 *  chỉ mất hình dạng bên trong một pixel (thứ mắt không thấy được).
 */
function nen(ds: number[], soNhom: number): number[] {
  if (ds.length <= soNhom * 2) return ds
  const b = ds.length / soNhom
  const ra: number[] = []
  for (let i = 0; i < soNhom; i++) {
    const a = Math.floor(i * b)
    const z = Math.min(ds.length, Math.floor((i + 1) * b))
    if (z <= a) continue
    let lo = ds[a]
    let hi = ds[a]
    let iLo = a
    let iHi = a
    for (let k = a + 1; k < z; k++) {
      if (ds[k] < lo) { lo = ds[k]; iLo = k }
      if (ds[k] > hi) { hi = ds[k]; iHi = k }
    }
    // Giữ đúng thứ tự thời gian trong nhóm, nếu không đường sẽ răng cưa giả.
    if (iLo <= iHi) ra.push(lo, hi)
    else ra.push(hi, lo)
  }
  return ra
}

function duong(ds: number[], lo: number, hi: number): string {
  if (!ds.length) return ''
  const bien = hi - lo || 1
  const buoc = ds.length > 1 ? RONG_BD / (ds.length - 1) : 0
  let d = ''
  for (let i = 0; i < ds.length; i++) {
    const y = CAO_BD - ((ds[i] - lo) / bien) * CAO_BD
    d += (i ? 'L' : 'M') + (i * buoc).toFixed(1) + ' ' + y.toFixed(2)
  }
  return d
}

/** Một biểu đồ. Chữ nằm NGOÀI svg — svg bị kéo giãn phi tỉ lệ nên chữ trong đó sẽ méo. */
function BieuDo({ ten, duongs, lo, hi, moc0, mu, dinhDang, conTro, bam }: {
  ten: string
  duongs: { d: string; mau: string; to?: boolean; nhan: string }[]
  lo: number; hi: number
  moc0?: boolean
  mu: { x: number; w: number }[]
  dinhDang: (v: number) => string
  /** Vị trí 0…1 của mốc đang soi, hoặc `null`. */
  conTro: number | null
  /** Bấm vào biểu đồ → tỉ lệ 0…1 theo bề ngang. */
  bam: (ti: number) => void
}) {
  const y0 = CAO_BD - ((0 - lo) / (hi - lo || 1)) * CAO_BD
  return (
    <div className="kq-bd">
      <div className="kq-bd-dau">
        <span className="kq-bd-ten">{ten}</span>
        {duongs.map(x => (
          <span key={x.nhan} className="kq-chu-giai">
            <i style={{ background: x.mau }} />{x.nhan}
          </span>
        ))}
      </div>
      {/* Nhãn trục ĐÈ LÊN biểu đồ, không chiếm dòng riêng: hai dòng chỉ để chở hai con
          số là 32px — bằng một phần ba chiều cao của chính biểu đồ. Đè lên thì vẫn giữ
          được liên hệ "số trên = đỉnh, số dưới = đáy", thứ mà gộp cả hai vào một hàng
          tiêu đề sẽ làm mất. */}
      <div className="kq-khung">
        <span className="kq-truc kq-truc-tren">{dinhDang(hi)}</span>
        <span className="kq-truc kq-truc-duoi">{dinhDang(lo)}</span>
      <svg className="kq-svg" viewBox={`0 0 ${RONG_BD} ${CAO_BD}`}
           preserveAspectRatio="none"
           onClick={e => {
             const r = e.currentTarget.getBoundingClientRect()
             bam(Math.min(1, Math.max(0, (e.clientX - r.left) / r.width)))
           }}>
        {/* Dải MÙ vẽ TRƯỚC để nằm dưới đường — nó là nền, không phải dữ liệu. */}
        {mu.map((m, i) => (
          <rect key={i} x={m.x} y={0} width={Math.max(m.w, 1.5)} height={CAO_BD}
                fill="var(--err)" opacity=".16" />
        ))}
        {moc0 && y0 >= 0 && y0 <= CAO_BD && (
          <line x1="0" y1={y0} x2={RONG_BD} y2={y0} stroke="var(--border)"
                strokeWidth="1" strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />
        )}
        {duongs.map(x => (
          <path key={x.nhan} d={x.d} fill="none" stroke={x.mau}
                strokeWidth={x.to ? 1.6 : 1.1} vectorEffect="non-scaling-stroke" />
        ))}
        {/* Con trỏ soi vẽ SAU CÙNG để nằm trên mọi đường — nó là thứ đang được hỏi. */}
        {conTro !== null && (
          <line x1={conTro * RONG_BD} y1={0} x2={conTro * RONG_BD} y2={CAO_BD}
                stroke="var(--accent)" strokeWidth="1.4"
                vectorEffect="non-scaling-stroke" />
        )}
      </svg>
      </div>
    </div>
  )
}

/** ⚠ `toLocaleString` cho ra gạch nối ASCII `-`, mà cả app dùng dấu TRỪ thật `−`
 *  (`core._so`, `bo_chay._so_vi`). Trộn hai ký tự trong cùng một bảng số thì cột không
 *  thẳng hàng và mắt vấp — gạch nối hẹp hơn dấu trừ. Đổi tại đây, một chỗ. */
const truVi = (chu: string) => chu.replace('-', '−')
const so = (v: number, le = 2) =>
  truVi(v.toLocaleString('vi-VN', { minimumFractionDigits: le, maximumFractionDigits: le }))
const nguyen = (v: number) => truVi(v.toLocaleString('vi-VN'))
/** Số "tự nhiên" — bao nhiêu chữ số thập phân cũng được, miễn đúng quy ước Việt.
 *  Dùng cho những con số mà ta KHÔNG biết trước độ lớn: bước giá (`0,001`), độ trễ,
 *  thời gian chạy. Ép cứng 2 chữ số ở đó là làm `0,001` thành `0,00`. */
const tuNhien = (v: number) => truVi(v.toLocaleString('vi-VN', { maximumFractionDigits: 8 }))

function gio(ms: number) {
  const d = new Date(ms)
  return d.toISOString().slice(0, 16).replace('T', ' ')
}

export default function KetQuaPanel({ kq, dangChay, soiIdx, onSoi }: {
  kq: KetQuaTest | null
  dangChay: boolean
  /** Chỉ số điểm mẫu đang soi, hoặc `null`. */
  soiIdx: number | null
  onSoi: (i: number | null) => void
}) {
  if (dangChay) return <div className="trong">Đang chạy backtest…</div>
  if (!kq) {
    return (
      <div className="trong">
        Chưa chạy lần nào. Bấm <b>▶ Test</b> để chạy sơ đồ trên dữ liệu tick đã ghi.
      </div>
    )
  }

  const b = kq.bang
  const mau = kq.mau
  const t0 = mau.length ? mau[0][0] : 0
  const t1 = mau.length ? mau[mau.length - 1][0] : 1
  const beRong = t1 - t0 || 1
  const soNhom = 500

  const von = mau.map(m => m[1])
  const gop = mau.map(m => m[1] + m[3])          // ròng + phí = trước phí
  const tonKho = mau.map(m => m[2])

  const vLo = Math.min(0, ...von, ...gop)
  const vHi = Math.max(0, ...von, ...gop)
  const kLo = Math.min(0, ...tonKho)
  const kHi = Math.max(0, ...tonKho)

  const mu = kq.lo_hong.map(([a, z]) => ({
    x: ((a - t0) / beRong) * RONG_BD,
    w: ((z - a) / beRong) * RONG_BD,
  }))

  const phi = b.phi_da_tra
  const rong = b.gia_tri
  const truocPhi = rong + phi

  /* Bấm vào biểu đồ → BÁM VÀO ĐIỂM MẪU GẦN NHẤT, không nội suy.
     Chỉ những mốc đã lấy mẫu mới có ảnh chụp đầy đủ để soi (xem `bo_chay.KetQua.mau`);
     nội suy giữa hai mốc là bịa ra một trạng thái chưa từng tồn tại. Con trỏ nhảy về
     đúng mốc nên người dùng THẤY được chuyện đó, không phải đoán. */
  const bamBieuDo = (ti: number) => {
    if (!mau.length) return
    const i = Math.min(mau.length - 1, Math.max(0, Math.round(ti * (mau.length - 1))))
    onSoi(i === soiIdx ? null : i)
  }
  const conTro = soiIdx === null || !mau.length
    ? null : (mau[soiIdx][0] - t0) / beRong

  return (
    <div className="kq">
      {/* ---- ba dòng số, theo đúng thứ tự người ta hỏi ---- */}
      <div className="kq-tren">
        <div className="kq-tach">
          <div className="kq-dong">
            <span>Gộp (trước phí)</span>
            <b className={truocPhi >= 0 ? 't-ok' : 't-err'}>{so(truocPhi)}</b>
          </div>
          <div className="kq-dong">
            <span>Phí maker</span>
            {/* Phí luôn hiện dấu TRỪ dù `phi_da_tra` là số dương: ở phép cộng này nó là
                khoản BỊ TRỪ ĐI. Trừ khi có rebate (phí âm) — lúc đó nó cộng vào, và
                phải hiện đúng như vậy chứ không được nuốt dấu. */}
            <b className={phi > 0 ? 't-dim' : 't-ok'}>
              {phi > 0 ? '−' + so(phi) : '+' + so(-phi)}
            </b>
          </div>
          <div className="kq-dong kq-cong">
            <span>Ròng</span>
            <b className={rong >= 0 ? 't-ok' : 't-err'}>{so(rong)}</b>
          </div>
        </div>

        <div className="kq-so">
          {/* MARKOUT đứng riêng và to hơn: nó là câu trả lời cho "gộp âm vì sao". */}
          <div className="kq-noi-bat" title={
            'Sau khi khớp ' + b.markout_ms + ' ms thì giá đi đâu, tính trung bình mỗi '
            + 'lot. ÂM = bị chọn ngược: người khớp vào ta biết thứ ta không biết. '
            + 'Nới spread không cứu được nếu nguyên nhân là báo giá đứng im khi chợ '
            + 'đã đi.'}>
            <span className="kq-nhan">Markout {b.markout_ms} ms</span>
            <b className={b.markout_tick >= 0 ? 't-ok' : 't-err'}>
              {b.markout_tick >= 0 ? '+' : ''}{so(b.markout_tick, 3)} tick/lot
            </b>
            <span className="kq-phu">
              {b.markout_tick < 0 ? 'bị chọn ngược' : 'bắt được phần thưởng thanh khoản'}
            </span>
          </div>
          <div><span className="kq-nhan">Khớp</span> {nguyen(b.so_lan_khop)} lần ·{' '}
            {so(b.kl_da_khop, 0)} lot</div>
          <div><span className="kq-nhan">Tồn kho cuối</span> {so(b.ton_kho, 2)}</div>
          <div><span className="kq-nhan">Đặt / huỷ / từ chối</span>{' '}
            {nguyen(b.so_dat)} · {nguyen(b.so_huy)} ·{' '}
            <span className={b.so_tu_choi ? 't-err' : ''}>{nguyen(b.so_tu_choi)}</span>
          </div>
        </div>

        <div className="kq-so">
          <div><span className="kq-nhan">Dữ liệu</span> {kq.symbol} ·{' '}
            {kq.tu_ngay}…{kq.den_ngay}</div>
          <div><span className="kq-nhan">Sự kiện</span> {nguyen(b.so_su_kien)} trong{' '}
            {tuNhien(b.giay_chay)}s</div>
          {/* GIẢ ĐỊNH nằm NGAY CẠNH kết quả, không giấu trong Cài đặt. */}
          <div className="kq-gia-dinh" title="Bốn con số app phải ĐOÁN. Sửa ở Cài đặt → Mô hình khớp.">
            <span className="kq-nhan">Giả định</span>{' '}
            phí {tuNhien(b.gia_dinh.phi_maker_bps)} bps ·
            trễ ra {tuNhien(b.gia_dinh.tre_ra_ms)} ms ·
            huỷ trước {tuNhien(b.gia_dinh.phan_huy_truoc)} ·
            mức sâu {tuNhien(b.gia_dinh.phan_muc_sau)} ·
            tick {tuNhien(b.gia_dinh.buoc_gia)}
          </div>
        </div>
      </div>

      {b.loi && <div className="chu-dan canh">⚠ {b.loi}</div>}

      <BieuDo ten="Vốn" moc0 mu={mu} lo={vLo} hi={vHi} dinhDang={v => so(v, 0)}
              conTro={conTro} bam={bamBieuDo}
              duongs={[
                { nhan: 'gộp (trước phí)', mau: 'var(--dim)',
                  d: duong(nen(gop, soNhom), vLo, vHi) },
                { nhan: 'ròng', mau: rong >= 0 ? 'var(--ok)' : 'var(--err)', to: true,
                  d: duong(nen(von, soNhom), vLo, vHi) },
              ]} />

      <BieuDo ten="Tồn kho" moc0 mu={mu} lo={kLo} hi={kHi} dinhDang={v => so(v, 0)}
              conTro={conTro} bam={bamBieuDo}
              duongs={[{ nhan: '±lot', mau: 'var(--khoi-lot)', to: true,
                         d: duong(nen(tonKho, soNhom), kLo, kHi) }]} />

      <div className="kq-chan">
        <span>{gio(t0)}</span>
        <span className="kq-chu-giai">
          {soiIdx === null
            ? 'Bấm vào biểu đồ để SOI sơ đồ tại thời điểm đó'
            : <b className="kq-dang-soi">đang soi {gio(mau[soiIdx][0])} — bấm lại để bỏ</b>}
        </span>
        {mu.length > 0 && (
          <span className="kq-chu-giai">
            <i style={{ background: 'var(--err)', opacity: .4 }} />
            {mu.length} quãng mù — sàn vẫn khớp trong đó, backtest không thấy
          </span>
        )}
        <span className="day" />
        <span>{gio(t1)}</span>
      </div>
    </div>
  )
}
