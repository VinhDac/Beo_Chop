import { Fragment, useState } from 'react'
import Icon from './Icon'
import { DocThem, Hang, OTheoKieu } from './ORuot'
import type {
  BangCoOThem, KhoangNgay, MaChay, OLam, RoChay, TuDienBatDau,
} from '../types'

/** RUỘT dùng chung của HAI hộp thoại: «Bắt đầu» và «Cỗ máy LEAN».
 *
 *  ⚠ VÌ SAO MỘT FILE CHỨ KHÔNG HAI. Hai hộp bày ô theo CÙNG một luật: xếp theo nhóm
 *  Python khai, ô con đi ngay sau ô cha, đổi ô cha thì điền mặc định cho ô con, lưu
 *  thì bỏ ô của lựa chọn không còn hiện. Chép bộ ấy ra hai bản là hai bản sẽ lệch —
 *  và lệch ở đây nghĩa là một hộp mất ô con, model chạy ở mặc định của LEAN mà nhãn
 *  hứa một đằng. Đúng cái bệnh cả dự án này viết hàng rào để chặn.
 *
 *  Hộp nào bày ô nào thì PYTHON chia (`bat_dau.NHOM_CO_MAY`, gửi sang thành `o` và
 *  `o_co_may`); chỗ này chỉ nhận một danh sách ô rồi vẽ.
 */

/** MỘT Ô NHỚ đã khai: mã của từ điển + tên người dùng đặt + giá trị ban đầu. */
type ONhoKhai = { ma: string; nhan: string; ban_dau?: unknown }

/** Ô «Cỗ máy nhớ những gì» — khai mấy ô nhớ, mỗi ô một TÊN.
 *
 *  ⚠ MÃ Ô NHỚ LÀ CỦA TỪ ĐIỂN, TÊN LÀ CỦA NGƯỜI DÙNG. Mười hai mã cố định khai bên
 *  Python (`hoi.TRI_NHO`); chỗ này chỉ cho chọn một mã còn trống rồi đặt tên. Cho
 *  người dùng tự khai tên biến thì từ điển hết là từ điển, và mọi hàng rào lặp qua
 *  nó mất chỗ đứng. */
function ODsNho({ ds, td, onDoi }: {
  ds: ONhoKhai[]
  td: TuDienBatDau
  onDoi: (v: ONhoKhai[]) => void
}) {
  const daDung = new Set(ds.map(x => x.ma))
  const conTrong = td.o_nho.filter(o => !daDung.has(o.ma))
  const kieuCua = (ma: string) => td.o_nho.find(o => o.ma === ma)?.kieu
  return (
    <div className="ds-nho">
      {ds.map((x, i) => {
        const o = td.o_nho.find(y => y.ma === x.ma)
        const doi = (v: Partial<ONhoKhai> | null) => onDoi(v === null
          ? ds.filter((_, k) => k !== i)
          : ds.map((y, k) => (k === i ? { ...y, ...v } : y)))
        return (
          <div className="dong-nho" key={x.ma || i}>
            <input className="o day" value={x.nhan ?? ''} spellCheck={false}
                   placeholder="tên ô nhớ — «đang chờ mua lại»"
                   onChange={e => doi({ nhan: e.target.value })} />
            <select className="o" value={x.ma}
                    onChange={e => doi({ ma: e.target.value,
                      ban_dau: kieuCua(e.target.value) === 'co_khong'
                        ? false : 0 })}>
              {/* Ô đang chọn luôn có mặt, không thì đổi tên là mất chỗ. */}
              {[...(o ? [o] : []), ...conTrong].map(y => (
                <option key={y.ma} value={y.ma}>{y.nhan}</option>
              ))}
            </select>
            {/* GIÁ TRỊ BAN ĐẦU — bắt buộc có, vì nhịp đầu tiên đã đọc ô này rồi. */}
            {o?.kieu === 'co_khong'
              ? <select className="o" value={x.ban_dau ? '1' : ''}
                        onChange={e => doi({ ban_dau: !!e.target.value })}>
                  <option value="">ban đầu: SAI</option>
                  <option value="1">ban đầu: ĐÚNG</option>
                </select>
              : <input className="o so" inputMode="decimal"
                       defaultValue={String(x.ban_dau ?? 0)}
                       onChange={e => doi({
                         ban_dau: e.target.value as unknown as number })} />}
            <button className="nut-nho" title="Bỏ ô nhớ này"
                    onClick={() => doi(null)}>✕</button>
          </div>
        )
      })}
      {conTrong.length > 0 && (
        <button className="nut-nho" onClick={() => onDoi([...ds, {
          ma: conTrong[0].ma, nhan: '',
          ban_dau: conTrong[0].kieu === 'co_khong' ? false : 0 }])}>
          + Thêm một ô nhớ
        </button>
      )}
      <div className="ro-nhac">
        Ô nhớ giữ một quyết định cỗ máy đã ra, để nhịp sau đọc lại. Thứ LEAN đã lo —
        đỉnh giá từ lúc vào, cửa sổ N giá đóng, đang giữ mã nào — thì đừng nhớ lại
        ở đây.
      </div>
    </div>
  )
}

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


/** Mấy bảng ô-cha-mang-ô-con. Dùng chung cho cả hai hộp.
 *
 *  ⚠ THÊM MỘT Ô CÓ Ô CON MÀ QUÊN KHAI Ở ĐÂY thì ô ấy chọn xong KHÔNG núm nào hiện
 *  ra, và model chạy ở mặc định của LEAN — nhãn hứa một đằng, mã sinh ra một nẻo.
 *  `tests/test_moi_noi.py` canh: bảng nào Python gửi có `o_them` thì phải có một
 *  dòng tra ở đây. */
export function bangOThemCua(td: TuDienBatDau): Record<string, BangCoOThem[]> {
  return {
    nhip: td.nhip,
    quy_tac_gio: td.quy_tac_gio,
    phong_rui_ro: td.phong_rui_ro,
    phat_tin_hieu: td.phat_tin_hieu,
    phi: td.phi,
    truot_gia: td.truot_gia,
  }
}

/** Lưu, có BỎ ô của lựa chọn không còn hiện — để file không mang theo "giờ 14:30"
 *  của một cỗ máy chạy mỗi nến ngày, hay một ngưỡng cắt lỗ của trạm đã tắt. */
export function locOAnHien(gt: Record<string, unknown>, td: TuDienBatDau) {
  const bang = bangOThemCua(td)
  const dangHien = new Set(Object.entries(bang).flatMap(([ten, b]) =>
    (b.find(x => x.ma === String(gt[ten] ?? ''))?.o_them ?? []).map(o => o.ten)))
  const moi = Object.values(bang).flat().flatMap(n => n.o_them.map(o => o.ten))
  const ra: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(gt)) {
    if (!moi.includes(k) || dangHien.has(k)) ra[k] = v
  }
  return ra
}

export default function RuotBatDau({ dsO, nhom, gt, setGt, tuDien,
                                    maSoDo }: {
  /** Danh sách ô hộp này bày — Python chia, chỗ này không lọc lại.
   *  Tên `dsO` chứ không `o`: trong thân có hai vòng lặp đặt biến `o`, và một
   *  cái tên bị che là một chỗ đọc ra nghĩa khác với nghĩa nó chạy. */
  dsO: OLam[]
  nhom: { ma: string; nhan: string; mo_ta: string }[]
  gt: Record<string, unknown>
  setGt: (f: (x: Record<string, unknown>) => Record<string, unknown>) => void
  tuDien: TuDienBatDau
  /** Mã sơ đồ này khai ở khối Bắt đầu — để ô «Mốc so sánh» gợi ý chúng.
   *
   *  ⚠ PHẢI TRUYỀN VÀO, không đọc ra từ `gt`. «Mã» ở hộp Bắt đầu còn «Mốc so sánh»
   *  ở hộp Cỗ máy — hai hồ sơ khác nhau, nên trong hộp Cỗ máy thì `gt.ma` không tồn
   *  tại. Đọc bừa thì ô mốc chỉ còn mấy mã có dữ liệu miễn phí, và người dùng mất
   *  cách chọn chính mã cỗ máy mình đang chạy. Hỏng LẶNG: ô vẫn bày, vẫn chọn được,
   *  chỉ thiếu đúng mấy dòng đáng chọn nhất. */
  maSoDo?: string[]
}) {
  const doi = (k: string, v: unknown) => setGt(x => ({ ...x, [k]: v }))

  const bangOThem = bangOThemCua(tuDien)

  /** Ô con ĐANG HIỆN của một ô cha — rỗng nếu ô ấy không mang ô con nào. */
  function oConCua(ten: string): OLam[] {
    const bang = bangOThem[ten]
    if (!bang) return []
    const muc = bang.find(x => x.ma === String(gt[ten] ?? ''))
    return muc?.o_them ?? []
  }

  /** Đổi một ô mang ô thêm thì điền luôn mặc định cho mấy ô mới hiện ra.
   *
   *  Không điền thì ô mới bày số 0 trong khi Python rơi về mặc định của từ điển —
   *  thẻ khối và hộp thoại nói hai đằng. Đúng cái bẫy đã gặp ở hộp Hành động. */
  function doiCoOThem(ten: string, v: string) {
    setGt(x => {
      const ra: Record<string, unknown> = { ...x, [ten]: v }
      for (const o of bangOThem[ten].find(n => n.ma === v)?.o_them ?? []) {
        if (!(o.ten in ra)) ra[o.ten] = o.mac_dinh
      }
      return ra
    })
  }

  /** Vẽ MỘT ô của khối Bắt đầu. Tách khỏi vòng lặp vì nay vòng lặp đi theo NHÓM, và
   *  mỗi ô còn phải kéo theo ô con của nó. */
  function veMotO(o: OLam) {
    if (o.kieu === 'ds_ma') {
      return (
        <Hang o={o}>
          <OChayTrenMa gt={gt.ma} td={tuDien} onDoi={v => doi('ma', v)} />
        </Hang>
      )
    }
    if (o.kieu === 'ds_nho') {
      return (
        <Hang o={o}>
          <ODsNho ds={(gt.tri_nho as ONhoKhai[]) ?? []} td={tuDien}
                  onDoi={v => doi('tri_nho', v)} />
        </Hang>
      )
    }
    /* MỐC SO SÁNH — Ô CHỌN, không phải ô gõ. Danh sách là mấy mã khối này vừa khai,
     * cộng mấy mã CÓ DỮ LIỆU MIỄN PHÍ. Gõ tay thì gõ sai, mà mốc sai không làm
     * backtest hỏng — nó chỉ vẽ một đường so sánh vô nghĩa, tức là hỏng LẶNG. */
    if (o.ten === 'moc_so_sanh') {
      /* ⚠ `gt.ma` CÓ THỂ LÀ MỘT RỔ, và object không có `.map` — dòng này từng đổ cả
         hộp thoại ngay lúc mở. Rổ thì không có mã nào gõ trước được. */
      const cua = maSoDo ?? (Array.isArray(gt.ma)
        ? (gt.ma as MaChay[]).map(m => m.ma).filter(Boolean) : [])
      const ds = [...new Set([...cua, ...Object.values(tuDien.co_san).flat()])]
      return (
        <Hang o={o}>
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
        <Hang o={o}>
          <OKhoangNgay k={(gt.khoang as KhoangNgay) ?? { tu: '', den: '' }}
                       onDoi={v => doi('khoang', v)} />
        </Hang>
      )
    }
    return (
      <Hang o={o} gt={gt[o.ten]}
            onDoi={v => (o.ten in bangOThem
              ? doiCoOThem(o.ten, String(v)) : doi(o.ten, v))} />
    )
  }


  /** Một ô cùng TOÀN BỘ ô con của nó, lồng bao nhiêu tầng cũng được.
   *
   *  ⚠ PHẢI ĐỆ QUY. Chuỗi thật sâu hai tầng rồi: « Nhịp » mở ra « Lúc nào trong ngày »,
   *  và ô ấy lại mở ra « Số phút sau khi mở » hay « Giờ » + « Phút ». Bản vẽ một tầng
   *  thì tầng thứ hai biến mất, và lịch chạy ở mặc định — không lỗi, không một lời nào. */
  function veOVaCon(o: OLam, sau = 0) {
    const con = oConCua(o.ten)
    return (
      <>
        {sau === 0 ? veMotO(o)
          : <Hang o={o} gt={gt[o.ten] ?? o.mac_dinh}
                  onDoi={v => (o.ten in bangOThem
                    ? doiCoOThem(o.ten, String(v)) : doi(o.ten, v))} />}
        {con.length > 0 && (
          <div className="o-con">
            {con.map(c => (
              <Fragment key={c.ten}>{veOVaCon(c, sau + 1)}</Fragment>
            ))}
          </div>
        )}
      </>
    )
  }


  return (
    <>
        {/* BÀY THEO NHÓM — thứ tự nhóm và nhóm của từng ô đều do PYTHON khai
          *  (`bat_dau.NHOM_O`, và `nhom=` trên từng `_o`). Chỗ này không biết có
          *  mấy nhóm, cũng không biết nhóm nào gồm ô nào.
          *
          *  ⚠ Ô CON ĐI NGAY SAU Ô CHA. Bản trước dồn hết ô con xuống ĐÁY hộp, nên
          *  «Giờ» và «Phút» của nhịp nằm cách ô «Nhịp» mười ô, và ô «Ngưỡng» của
          *  model cắt lỗ thì nằm sau cả «Mốc so sánh». Hồi có sáu ô thì còn thấy
          *  được; nay hơn hai mươi ô thì người dùng chọn một model rồi không biết
          *  núm của nó mọc ra ở đâu. */}
      {[...nhom, { ma: tuDien.nhom_khac, nhan: 'Khác', mo_ta: '' }]
        .map(nh => {
            const cua = dsO.filter(x => (x.nhom || tuDien.nhom_khac) === nh.ma)
            if (!cua.length) return null
            return (
              <section className="nhom-o" key={nh.ma} data-nhom={nh.ma}>
                <h4 className="nhom-ten">
                  {nh.nhan}
                  {nh.mo_ta && <span className="nhom-mo-ta">{nh.mo_ta}</span>}
                </h4>
                {cua.map(o => (
                  <Fragment key={o.ten}>{veOVaCon(o)}</Fragment>
                ))}
              </section>
            )
          })}

    </>
  )
}
