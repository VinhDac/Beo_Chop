import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { DocThem, Hang, KhaiLean, OTheoKieu } from './ORuot'
import { py } from '../api'
import type {
  KhoangNgay, MaChay, OLam, RoChay, Step, TuDienBatDau,
} from '../types'

/** Ô «Chạy trên mã nào» đang nói kiểu nào — MỘT CHỖ DUY NHẤT quyết định.
 *
 *  Phân biệt bằng HÌNH DẠNG, y như Python (`bat_dau.ro_cua`): mảng là mấy mã gõ sẵn,
 *  object là một rổ. Hai nơi cùng đoán hình dạng là hai nơi để trôi khỏi nhau. */
export function laRo(v: unknown): v is RoChay {
  return !!v && typeof v === 'object' && !Array.isArray(v)
}

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

  /** Mã này có dữ liệu đi kèm LEAN không. Biết ngay lúc gõ, chứ đừng để tới lúc
   *  backtest chạy xong mà không có lệnh nào rồi mới ngồi đoán vì sao. */
  const coDuLieu = (m: MaChay) => (td.co_san[m.loai] ?? []).includes(m.ma)

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
          {/* Không CHẶN — ai có bộ dữ liệu riêng thì mã nào cũng chạy được. Chỉ nói
              ra, vì bộ miễn phí chỉ có 13 mã. */}
          {m.ma && !coDuLieu(m) && (
            <span className="ma-khong-co" title={
              `Bộ dữ liệu miễn phí đi kèm LEAN không có ${m.ma}. Vẽ vẫn vẽ được, `
              + 'nhưng backtest trên máy này sẽ không ra lệnh nào — trừ khi bạn tự '
              + 'tải dữ liệu về.'}>không có dữ liệu</span>
          )}
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

/** Ô «Chạy trên mã nào» — HAI KIỂU, một widget.
 *
 *  Đúng lối vế phải của điều kiện: ở đấy một vế là MỘT SỐ hay MỘT ĐẠI LƯỢNG, và chỉ
 *  có một nút để đổi qua lại. Ở đây là MẤY MÃ GÕ SẴN hay MỘT RỔ.
 *
 *  ⚠ ĐỔI KIỂU THÌ THAY CẢ GIÁ TRỊ, không trộn. Giữ lại danh sách mã cũ bên trong
 *  object rổ là lưu ra một ô mang cả hai câu trả lời, rồi `bat_dau.ro_cua` thấy
 *  object nên chọn nhánh rổ — và danh sách mã kia nằm im trong file, không ai xoá
 *  được vì giao diện không còn chỗ nào bày nó ra. */
function OChayTrenMa({ gt, td, onDoi }: {
  gt: unknown; td: TuDienBatDau; onDoi: (v: MaChay[] | RoChay) => void
}) {
  const ro = laRo(gt) ? gt : null
  const muc = ro ? td.ro.find(r => r.ma === String(ro.ro ?? '')) : undefined

  /** Đổi sang một rổ khác thì điền luôn mặc định cho mấy ô con của nó.
   *
   *  Không điền thì ô con bày số 0 trong khi Python rơi về mặc định của từ điển —
   *  thẻ khối và hộp thoại nói hai đằng. Đúng cái bẫy đã gặp ở ô nhịp. */
  function chonRo(maRo: string) {
    if (!maRo) { onDoi([{ ma: '', loai: 'equity' }]); return }
    const v: RoChay = { ro: maRo }
    for (const o of td.ro.find(r => r.ma === maRo)?.o_them ?? []) {
      v[o.ten] = o.mac_dinh
    }
    onDoi(v)
  }

  return (
    <div className="o-chay-ma">
      <select className="o day" value={ro ? String(ro.ro ?? '') : ''}
              onChange={e => chonRo(e.target.value)}>
        <option value="">Mấy mã gõ sẵn</option>
        {td.ro.map(r => (
          <option key={r.ma} value={r.ma}>Rổ — {r.nhan}</option>
        ))}
      </select>

      {!ro ? (
        <DanhSachMa ds={Array.isArray(gt) ? (gt as MaChay[]) : []} td={td}
                    onDoi={onDoi} />
      ) : (<>
        {/* Ô CON của rổ — ĐƯA THẲNG `o` CỦA PYTHON VÀO, không dựng lại. Bày lại một
            object `kieu: 'so'` đóng cứng là đúng cái bệnh dự án này săn: ô «Mã ETF»
            sẽ thành ô số, và câu gợi ý thật mà Python đã viết thì mất.

            Dùng `OTheoKieu` chứ KHÔNG dùng `Hang`: `Hang` dựng một `<label>`, mà cả
            khối này đã nằm trong `<label>` của hàng «Chạy trên mã nào» — label lồng
            label thì bấm vào nhãn con nhảy focus sang ô cha, lặng lẽ. */}
        {(muc?.o_them ?? []).map(o => (
          <div className="ro-o" key={o.ten}>
            <div className="ro-hang">
              <span className="ro-nhan">{o.nhan}</span>
              <OTheoKieu o={o} gt={ro[o.ten] ?? o.mac_dinh}
                         onDoi={v => onDoi({ ...ro, [o.ten]: v })} />
              <DocThem o={o} gt={ro[o.ten] ?? o.mac_dinh} />
            </div>
            {/* Gợi ý hiện THÀNH DÒNG, không chỉ nằm trong `title`. Câu của ô «Mã
                ETF» nói bộ dữ liệu miễn phí có rổ của ETF nào — giấu nó sau một cái
                hover là để người chơi gõ một mã không có dữ liệu rồi ngồi đoán vì
                sao backtest không ra lệnh nào. */}
            {o.goi_y && <div className="ro-goi-y">{o.goi_y}</div>}
          </div>
        ))}
        {/* Rổ gồm mã nào là chuyện LEAN quyết lại mỗi ngày, nên không khối nào gõ
            được tên mã. Nói ra Ở ĐÂY, lúc chọn — chứ đừng để tới lúc bấm Build mới
            hiện một bảng Vấn đề dài. */}
        <div className="ro-nhac">
          Rổ đổi theo ngày, nên không khối nào gõ được tên mã — mọi khối chạy cho
          «mã đang xét». Cần khối «Phát tín hiệu» để LEAN chia vốn.
        </div>
      </>)}
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

  /* MẤY CÂU LEAN KHỐI NÀY KHAI RA — HỎI PYTHON, KHÔNG TỰ GHÉP.
   *
   * Dòng khai tồn tại ĐÚNG ĐỂ người dùng đối chiếu với mã sinh ra, nên nó nói sai
   * thì tệ hơn là không có. Bản trước tự dựng lại câu ấy ở đây bằng TypeScript: tự
   * quyết lấy `add_*` hay `universe_settings`, tự ghép với tên hàm lịch, tự suy ra
   * độ phân giải thật. Cả bốn phép ấy `bat_dau.ham_lean` bên Python đã làm rồi —
   * hai bản ghép chữ nằm hai bên cầu nối, không ai đứng so. Và câu của RỔ ĐỘNG thì
   * bản ấy không nói được, nên chọn rổ xong hộp chỉ nói về nhịp mà im đúng câu
   * quan trọng nhất (`bat_dau.lean_ro`, hồi đó không ai gọi).
   *
   * Nay một cửa trả về CẢ DANH SÁCH, và chỗ này không biết trong đó có mấy câu —
   * thêm một câu khai bên Python là hộp thoại có ngay. `tests/test_moi_noi.py`
   * canh cả họ: không file .tsx nào được gõ cứng một mẩu LEAN.
   *
   * ⚠ Gọi theo `gt` nên gõ mỗi phím là một lượt hỏi, và lượt gửi trước có thể về
   * SAU lượt gửi sau — nên câu trả lời của một `gt` đã cũ phải bị vứt, không thì
   * dòng khai đứng lại ở một giá trị người dùng vừa xoá. */
  const [khai, setKhai] = useState<string[]>([])
  useEffect(() => {
    let con = true
    void py.khai_bat_dau(gt).then(r => { if (con && r.ok) setKhai(r.value ?? []) })
    return () => { con = false }
  }, [gt])

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
                <OChayTrenMa gt={gt.ma} td={tuDien} onDoi={v => doi('ma', v)} />
              </Hang>
            )
          }
          /* MỐC SO SÁNH — Ô CHỌN, không phải ô gõ. Danh sách là mấy mã khối này
           * vừa khai, cộng mấy mã CÓ DỮ LIỆU MIỄN PHÍ. Gõ tay thì gõ sai, mà mốc
           * sai không làm backtest hỏng — nó chỉ vẽ một đường so sánh vô nghĩa,
           * tức là hỏng LẶNG, loại khó thấy nhất. */
          if (o.ten === 'moc_so_sanh') {
            /* ⚠ `gt.ma` CÓ THỂ LÀ MỘT RỔ, và object không có `.map` — dòng này từng
               đổ cả hộp thoại ngay lúc mở. Rổ thì không có mã nào gõ trước được,
               nên danh sách chỉ còn mấy mã có dữ liệu miễn phí. */
            const cua = Array.isArray(gt.ma)
              ? (gt.ma as MaChay[]).map(m => m.ma).filter(Boolean) : []
            const ds = [...new Set([...cua, ...Object.values(tuDien.co_san).flat()])]
            return (
              <Hang key={o.ten} o={o}>
                <select className="o day" value={String(gt.moc_so_sanh ?? '')}
                        onChange={e => doi('moc_so_sanh', e.target.value)}>
                  <option value="">(để trống — LEAN tự lấy SPY)</option>
                  {ds.map(m => (
                    <option key={m} value={m}>
                      {m}{cua.includes(m) ? ' — mã của cỗ máy này' : ''}
                    </option>
                  ))}
                </select>
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

        {/* Ô THÊM của nhịp — giờ, phút, số phút sau khi mở cửa, độ phân giải.
         *
         *  ⚠ ĐƯA THẲNG `o` CỦA PYTHON VÀO, không dựng lại. Bản trước nặn một object
         *  mới với `kieu: 'so'` đóng cứng và `chon: []`, nên:
         *    · «Độ phân giải dữ liệu» là ô CHỌN năm mức mà hiện ra như ô gõ chữ,
         *      năm lựa chọn bị vứt sạch;
         *    · câu gợi ý tự chế từ `o.nho_nhat`/`o.lon_nhat` — hai khoá KHÔNG HỀ CÓ
         *      trong từ điển — nên in ra đúng chữ "Từ undefined đến undefined",
         *      đè mất câu gợi ý thật mà Python đã viết.
         *  Giao diện khai lại thứ Python đã khai là đúng cái bệnh dự án này săn. */}
        {(nhip?.o_them ?? []).map(o => (
          <Hang key={o.ten} o={o as unknown as OLam} gt={gt[o.ten] ?? o.mac_dinh}
                onDoi={v => doi(o.ten, v)} />
        ))}

        <KhaiLean ham={khai} />
      </div>
    </Modal>
  )
}
