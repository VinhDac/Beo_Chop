import { useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { Hang, ONhapSo, KhaiLean } from './ORuot'
import type {
  KhoangNgay, MaChay, OLam, Step, TuDienBatDau,
} from '../types'

/** HỘP THOẠI KHỐI BẮT ĐẦU — nửa «thiết lập» của thuật toán.
 *
 *  Một script QuantConnect có hai nửa: `initialize` nói MỘT LẦN (ngày nào, bao nhiêu
 *  tiền, mã nào, nhịp nào), rồi `on_data` chạy LẠI mỗi nhịp. Sơ đồ nối dây là nửa
 *  dưới; hộp này là nửa trên — trước D-15 nó không có chỗ nào trên canvas.
 *
 *  SÁU Ô, và hai trong số đó cần widget riêng (danh sách mã, khoảng ngày) nên chúng
 *  nằm ở đây chứ không ở `ORuot.tsx`: ô chung phải ở lại chung.
 */

/** Danh sách mã — mỗi dòng một mã kèm loại tài sản.
 *
 *  KHÔNG gộp loại tài sản thành MỘT ô cho cả cỗ máy: LEAN có sáu hàm `add_*` khác
 *  nhau vì sáu loại có giờ giao dịch, đơn vị và đòn bẩy khác nhau, nên loại đi theo
 *  TỪNG mã mới đúng. */
function DanhSachMa({ ds, td, onDoi }: {
  ds: MaChay[]; td: TuDienBatDau; onDoi: (v: MaChay[]) => void
}) {
  const sua = (i: number, d: Partial<MaChay>) =>
    onDoi(ds.map((m, j) => (j === i ? { ...m, ...d } : m)))

  return (
    <div className="ds-ma">
      {ds.map((m, i) => (
        <div className="dong-ma" key={i}>
          <input className="o ma" spellCheck={false} placeholder="mã"
                 list={`co-san-${m.loai}`} value={m.ma}
                 onChange={e => sua(i, { ma: e.target.value.toUpperCase() })} />
          <select className="o day" value={m.loai}
                  onChange={e => sua(i, { loai: e.target.value })}>
            {td.loai_tai_san.map(l => (
              <option key={l.ma} value={l.ma}>{l.nhan}</option>
            ))}
          </select>
          <button className="nut-nho" title="Bỏ mã này"
                  onClick={() => onDoi(ds.filter((_x, j) => j !== i))}>✕</button>
        </div>
      ))}
      {/* Gợi ý mã CÓ SẴN trong bộ dữ liệu miễn phí. `datalist` nên nó chỉ gợi ý —
          ai có dữ liệu riêng thì cứ gõ mã khác, không bị chặn. */}
      {Object.entries(td.co_san).map(([loai, dsm]) => (
        <datalist key={loai} id={`co-san-${loai}`}>
          {dsm.map(x => <option key={x} value={x} />)}
        </datalist>
      ))}
      <button className="nut" onClick={() => onDoi([...ds, { ma: '', loai: 'equity' }])}>
        <Icon name="plus" /> Thêm mã
      </button>
    </div>
  )
}

/** Khoảng backtest. Hai ô ngày gốc của trình duyệt — chúng tự lo lịch và khuôn ngày. */
function OKhoangNgay({ k, onDoi }: {
  k: KhoangNgay; onDoi: (v: KhoangNgay) => void
}) {
  return (
    <div className="khoang-ngay">
      <input className="o" type="date" value={k.tu ?? ''}
             onChange={e => onDoi({ ...k, tu: e.target.value })} />
      <span className="mui">→</span>
      <input className="o" type="date" value={k.den ?? ''}
             onChange={e => onDoi({ ...k, den: e.target.value })} />
    </div>
  )
}

export default function HopBatDau({ step, tuDien, onLuu, onDong }: {
  step: Step
  tuDien: TuDienBatDau
  onLuu: (s: Step) => void
  onDong: () => void
}) {
  const [ten, setTen] = useState(step.name ?? '')
  // Giữ CẢ khối: `pos`, `mau`, `hat_nhan`… đi theo nguyên vẹn mà hộp thoại không cần
  // biết chúng tồn tại.
  const [gt, setGt] = useState<Record<string, unknown>>(() => ({ ...step }))
  const doi = (k: string, v: unknown) => setGt(x => ({ ...x, [k]: v }))

  const nhip = tuDien.nhip.find(n => n.ma === String(gt.nhip ?? ''))

  /** Đổi nhịp thì điền luôn mặc định cho mấy ô mới hiện ra.
   *
   *  Không điền thì ô mới bày số 0 trong khi Python rơi về mặc định của từ điển —
   *  thẻ khối và hộp thoại nói hai đằng. Đúng cái bẫy đã gặp ở hộp Hành động. */
  function doiNhip(v: string) {
    setGt(x => {
      const ra: Record<string, unknown> = { ...x, nhip: v }
      for (const o of tuDien.nhip.find(n => n.ma === v)?.o_them ?? []) {
        if (!(o.ten in ra)) ra[o.ten] = o.mac_dinh
      }
      return ra
    })
  }

  /** Lưu, có BỎ ô của nhịp không chọn — để file không mang theo "giờ 14:30" của một
   *  cỗ máy chạy mỗi nến ngày. */
  function luu() {
    const dangHien = new Set((nhip?.o_them ?? []).map(o => o.ten))
    const cuaNhip = new Set(tuDien.nhip.flatMap(n => n.o_them.map(o => o.ten)))
    const ra: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(gt)) {
      if (!cuaNhip.has(k) || dangHien.has(k)) ra[k] = v
    }
    onLuu({ ...(ra as unknown as Step), id: step.id, kind: step.kind,
            name: ten.trim() || 'Bắt đầu' })
  }

  const hamLean = nhip
    ? (nhip.chay === 'on_data'
        ? `add_*(ma, Resolution.${nhip.res})`
        : `add_*(ma, Resolution.${nhip.res}) · ${nhip.chay}`)
    : ''

  return (
    <Modal title="Bắt đầu" width={660} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" onClick={luu}>Lưu</button>
           </>}>
      <div className="hop-lam">
        <div className="mo-ta-loai">
          <Icon name="start" /> cỗ máy này chạy trên cái gì, từ bao giờ, bằng bao nhiêu tiền
        </div>

        <label className="o-hang">
          <span className="nhan-o">Tên khối</span>
          <input className="o day" value={ten} spellCheck={false}
                 placeholder="Bắt đầu" onChange={e => setTen(e.target.value)} />
        </label>

        {tuDien.o.map(o => {
          if (o.kieu === 'ds_ma') {
            return (
              <Hang key={o.ten} o={o}>
                <DanhSachMa ds={(gt.ma as MaChay[]) ?? []} td={tuDien}
                            onDoi={v => doi('ma', v)} />
              </Hang>
            )
          }
          if (o.kieu === 'khoang_ngay') {
            return (
              <Hang key={o.ten} o={o}>
                <OKhoangNgay k={(gt.khoang as KhoangNgay) ?? { tu: '', den: '' }}
                             onDoi={v => doi('khoang', v)} />
              </Hang>
            )
          }
          return (
            <Hang key={o.ten} o={o} gt={gt[o.ten]}
                  onDoi={v => (o.ten === 'nhip' ? doiNhip(String(v))
                                                : doi(o.ten, v))} />
          )
        })}

        {/* Ô thêm của nhịp — giờ, phút, số phút sau khi mở cửa. */}
        {(nhip?.o_them ?? []).map(o => (
          <Hang key={o.ten}
                o={{ ten: o.ten, nhan: o.nhan, kieu: 'so', mac_dinh: o.mac_dinh,
                     don_vi: '', goi_y: `Từ ${o.nho_nhat} đến ${o.lon_nhat}.`,
                     chon: [], bat_buoc: true } as OLam}>
            <ONhapSo gt={gt[o.ten] ?? o.mac_dinh} nguyen
                     onDoi={v => doi(o.ten, v)} />
          </Hang>
        ))}

        <KhaiLean ham={hamLean} />
      </div>
    </Modal>
  )
}
