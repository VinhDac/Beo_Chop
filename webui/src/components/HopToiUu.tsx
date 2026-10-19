import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import type { Step, TuDienToiUu, NumSoDo, CaiToiUu, RangBuoc } from '../types'
import { tr, trx } from '../ngon_ngu'

/** HỘP OPTIMIZE — năm dòng, mỗi dòng một khoá có thật trong config của LEAN.
 *
 *  THỨ TỰ LÀ CỐ Ý, và nó NGƯỢC với màn Optimize của QuantConnect. Bên họ, «Select
 *  Target» nằm ở khối gập cuối cùng — trong khi "tìm cái gì" mới là câu hỏi đầu
 *  tiên. Ở đây: mục tiêu -> núm -> ràng buộc -> chạy thế nào, một mạch, không gập.
 *
 *  BA THỨ CỦA HỌ TA CỐ Ý BỎ, cả ba đều là chuyện thuê máy trên cloud: chọn loại
 *  node, giá mỗi giờ, tổng tiền USD + số dư QCC. Chạy tại máy thì không thuê gì, bày
 *  ra là ba ô vĩnh viễn rỗng và một số tiền vĩnh viễn bằng 0.
 *
 *  MỘT THỨ CỦA HỌ ĐÁNG CHÉP NHẤT và ta giữ: ước lượng SỐ LƯỢT · BAO LÂU, ngay trên
 *  nút Chạy. Ba núm × hai mươi bước là 8000 lượt backtest, hơn ba tiếng; không nói
 *  trước thì người ta bấm Chạy rồi ngồi đoán.
 *
 *  VÀ KHÔNG CÓ NÚT «+ Add Parameter». Bên QC có, vì người dùng của họ tự viết
 *  `self.get_parameter("lookback_year", 4)` trong code nên phải gõ lại tên. Ở đây
 *  không ai viết code: gõ sai một chữ là optimizer quét một tham số chẳng ai đọc,
 *  rồi N lượt backtest ra y hệt nhau mà không một dòng lỗi. Bảng này chỉ LIỆT KÊ
 *  mấy ô đã ghim trên sơ đồ; thêm bớt là việc của cái ghim ở bánh răng.
 */
export default function HopToiUu({ td, num, cai0, dangChay, onChay, onDong }: {
  td: TuDienToiUu
  num: NumSoDo[]
  cai0?: CaiToiUu
  dangChay: boolean
  onChay: (cai: CaiToiUu) => void
  onDong: () => void
}) {
  const [cai, setCai] = useState<CaiToiUu>(() => ({
    ...td.mac_dinh, ...(cai0 ?? {}),
  }))
  const doi = (k: keyof CaiToiUu, v: unknown) => setCai(x => ({ ...x, [k]: v }))

  /* Núm nào chưa có khoảng thì ĐIỀN SẴN quanh giá trị hiện tại của nó. Để min/max
     cùng bằng 0 như màn QC thì khoảng rỗng, quét đúng một điểm — mà màn ấy không
     kêu gì cả. */
  useEffect(() => {
    setCai(x => {
      const ts = { ...(x.tham_so ?? {}) }
      let doiGi = false
      for (const n of num) {
        if (ts[n.ten]) continue
        const g = Number(n.mac_dinh) || 0
        const buoc = Number.isInteger(g) ? Math.max(1, Math.round(Math.abs(g) / 10))
                                         : Math.abs(g) / 10 || 0.1
        ts[n.ten] = { tu: g - buoc * 2, den: g + buoc * 2, buoc }
        doiGi = true
      }
      for (const k of Object.keys(ts)) {
        if (!num.some(n => n.ten === k)) { delete ts[k]; doiGi = true }
      }
      return doiGi ? { ...x, tham_so: ts } : x
    })
  }, [num])

  const soBuoc = (k?: { tu: number; den: number; buoc: number }) => {
    const tu = Number(k?.tu), den = Number(k?.den), b = Number(k?.buoc)
    if (!Number.isFinite(tu) || !Number.isFinite(den) || !(b > 0) || den <= tu) return 0
    return Math.floor((den - tu) / b) + 1
  }
  const thieu = num.filter(n => soBuoc(cai.tham_so?.[n.ten]) <= 0).map(n => n.ten)
  const soLuot = thieu.length || !num.length ? 0
    : num.reduce((a, n) => a * soBuoc(cai.tham_so?.[n.ten]), 1)
  const songSong = Math.max(1, Number(cai.cung_luc) || 2)
  const giay = soLuot * td.giay_moi_luot / songSong
  const lauLa = giay < 90 ? tr('{0} giây', Math.round(giay))
    : giay < 5400 ? tr('{0} phút', Math.round(giay / 60))
      : tr('{0} tiếng', (giay / 3600).toFixed(1))

  const doiNum = (ten: string, o: string, v: string) =>
    setCai(x => ({ ...x, tham_so: { ...(x.tham_so ?? {}),
      [ten]: { ...(x.tham_so?.[ten] ?? { tu: 0, den: 0, buoc: 1 }),
               [o]: v as unknown as number } } }))
  const doiRb = (i: number, o: keyof RangBuoc, v: string) =>
    setCai(x => ({ ...x, rang_buoc: (x.rang_buoc ?? []).map(
      (r, j) => j === i ? { ...r, [o]: v } : r) }))

  return (
    <Modal title="Optimize" width={620} onClose={onDong}
           footer={<>
             <span className={'tu-uoc' + (soLuot ? '' : ' thieu')}>
               {soLuot
                 ? <>{trx('sẽ chạy {0} lượt · ước chừng {1}', <b>{soLuot.toLocaleString('vi')}</b>,
                   <b>{lauLa}</b>)}</>
                 : num.length
                   ? <>{trx('chưa khai khoảng quét: {0}', thieu.join(', '))}</>
                   : <>{tr('sơ đồ chưa ghim núm nào — bấm bánh răng cạnh một ô số')}</>}
             </span>
             <button className="nut" onClick={onDong}>{tr('Đóng')}</button>
             <button className="nut chinh" disabled={!soLuot || dangChay}
                     onClick={() => onChay(cai)}>
               {trx('{0} Chạy', <Icon name="chay" />)}</button>
           </>}>
      <div className="hop-lam hop-tu">
        <label className="o-hang"><span className="nhan-o">{tr('Mục tiêu')}</span>
          <select className="o day" value={cai.muc_tieu}
                  onChange={e => doi('muc_tieu', e.target.value)}>
            {td.chi_tieu.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select className="o" style={{ flex: '0 0 110px' }} value={cai.huong}
                  onChange={e => doi('huong', e.target.value)}>
            {td.huong.map(h => <option key={h.ma} value={h.ma}>{tr(h.nhan)}</option>)}
          </select>
        </label>

        <div className="tu-muc">{tr('Núm sơ đồ đang ghim')}</div>
        {!num.length && (
          <div className="tu-rong">{tr('Chưa có núm nào. Mở một khối ra, bấm bánh răng '
            + 'cạnh ô số rồi bấm nút ghim.')}</div>
        )}
        {num.map(n => {
          const k = cai.tham_so?.[n.ten]
          const sb = soBuoc(k)
          return (
            <div key={n.ten} className={'tu-num' + (sb ? '' : ' thieu')}>
              <div className="tu-ten">
                <span className="num-ghim">{n.ten}</span>
                <span className="tu-noi" title={n.o_tai.join(' · ')}>
                  {n.o_tai.length > 1 ? tr('dùng ở {0} chỗ', n.o_tai.length) : n.o_tai[0]}
                </span>
              </div>
              <div className="tu-khoang">
                <span>{tr('từ')}</span>
                <input className="o so" inputMode="decimal" value={String(k?.tu ?? '')}
                       onChange={e => doiNum(n.ten, 'tu', e.target.value)} />
                <span>{tr('đến')}</span>
                <input className="o so" inputMode="decimal" value={String(k?.den ?? '')}
                       onChange={e => doiNum(n.ten, 'den', e.target.value)} />
                <span>{tr('bước')}</span>
                <input className="o so" inputMode="decimal"
                       value={String(k?.buoc ?? '')}
                       onChange={e => doiNum(n.ten, 'buoc', e.target.value)} />
                <span className="tu-dem">{sb ? tr('{0} giá trị', sb) : tr('khoảng rỗng')}</span>
              </div>
            </div>
          )
        })}

        <div className="tu-muc">{tr('Ràng buộc')}
          <button className="nut-nho" onClick={() => setCai(x => ({ ...x,
            rang_buoc: [...(x.rang_buoc ?? []),
              { chi_tieu: 'Drawdown', phep: 'lessOrEqual', gia_tri: 0.2 }] }))}>
            {trx('{0} thêm', <Icon name="plus" />)}</button>
        </div>
        {!cai.rang_buoc?.length && (
          <div className="tu-rong">{tr('Không bắt buộc. Có ràng buộc thì optimizer BỎ '
            + 'những lượt không đạt, nên nó không trao giải cho một lượt Sharpe cao mà '
            + 'sụt 60%.')}</div>
        )}
        {(cai.rang_buoc ?? []).map((r, i) => (
          <div key={i} className="tu-rb">
            <select className="o" value={r.chi_tieu}
                    onChange={e => doiRb(i, 'chi_tieu', e.target.value)}>
              {td.chi_tieu.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select className="o" value={r.phep}
                    onChange={e => doiRb(i, 'phep', e.target.value)}>
              {td.phep_so.map(p => <option key={p.ma} value={p.ma}>{tr(p.nhan)}</option>)}
            </select>
            <input className="o so" inputMode="decimal" value={String(r.gia_tri)}
                   onChange={e => doiRb(i, 'gia_tri', e.target.value)} />
            <button className="nut-nho" title={tr('Bỏ dòng này')}
                    onClick={() => setCai(x => ({ ...x,
                      rang_buoc: (x.rang_buoc ?? []).filter((_, j) => j !== i) }))}>
              <Icon name="trash" />
            </button>
          </div>
        ))}

        <div className="tu-muc">{tr('Chạy thế nào')}</div>
        <label className="o-hang"><span className="nhan-o">{tr('Cách tìm')}</span>
          <select className="o day" value={cai.cach_tim}
                  onChange={e => doi('cach_tim', e.target.value)}>
            {td.cach_tim.map(c => <option key={c.ma} value={c.ma}>{tr(c.nhan)}</option>)}
          </select>
        </label>
        <label className="o-hang"><span className="nhan-o">{tr('Chạy cùng lúc')}</span>
          <input className="o so" inputMode="numeric" value={String(cai.cung_luc)}
                 onChange={e => doi('cung_luc', e.target.value)} />
          <span className="doc-them">{tr('lượt một lúc · 0 = để LEAN tự lấy nửa số nhân CPU')}</span>
        </label>
      </div>
    </Modal>
  )
}
