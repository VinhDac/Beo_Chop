import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import type { DaiLuong, LoaiHoi, Step, TuDienHoi, VeDieuKien, DongDieuKien } from '../types'

/** HỘP THOẠI KHỐI XÁC NHẬN — nơi người chơi gõ điều kiện.
 *
 *  MỘT DÒNG = MỘT ĐIỀU KIỆN, các dòng nối bằng VÀ. Muốn HOẶC thì KHÔNG nhét vào đây —
 *  vẽ thành hai nhánh trên sơ đồ. Đó là ngữ pháp đã chốt: *"cái nào trong N cái" là
 *  hình học, không phải cú pháp*; nhét HOẶC vào hộp thoại là giấu mất một quyết định
 *  mà lẽ ra phải nhìn thấy trên canvas.
 *
 *  HỘP CHỈ BÀY THỨ LOẠI NÀY CẦN: Hỏi tài khoản không có ô mã, Hỏi vị thế không có ô
 *  chu kỳ. Đó là cả lý do chia năm loại thay vì một khối "so sánh bất cứ gì".
 */

/** Một VẾ: chọn đại lượng (+ mã, tham số, đường), hoặc gõ một con số.
 *
 *  XUẤT RA ngoài vì khối «Vẽ lên bảng» cũng cần đúng bộ chọn này — `Plot` của LEAN
 *  nhận một con số, và con số ấy lấy từ cùng kho đại lượng. Hai bộ chọn thì sớm muộn
 *  một bên bày ra thứ bên kia không có. */
export function Ve({ ve, loai, td, choSo, choMa, onDoi }: {
  ve: VeDieuKien
  loai: LoaiHoi
  td: TuDienHoi
  /** Vế phải được phép là một con số; vế trái thì không. */
  choSo: boolean
  choMa: boolean
  onDoi: (v: VeDieuKien) => void
}) {
  const laSo = choSo && ve.ma_dl === undefined
  const dl = ve.ma_dl
    ? loai.nhom.flatMap(n => n.dai_luong).find(d => d.ma === ve.ma_dl)
    : undefined

  return (
    <div className="ve-dk">
      {choSo && (
        <select className="o nho" value={laSo ? 'so' : 'dl'}
                onChange={e => onDoi(e.target.value === 'so'
                  ? { so: 0 }
                  : { ma_dl: loai.nhom[0].dai_luong[0].ma })}>
          <option value="so">một số</option>
          <option value="dl">một đại lượng</option>
        </select>
      )}

      {laSo ? (
        <input className="o so" inputMode="decimal" value={String(ve.so ?? 0)}
               onChange={e => onDoi({ so: e.target.value as unknown as number })} />
      ) : (
        <>
          {choMa && (
            <input className="o ma" placeholder="mã" spellCheck={false}
                   title="Để trống = mã đang xét. Gõ mã khác là ra so sánh chéo mã."
                   value={ve.ma ?? ''}
                   onChange={e => onDoi({ ...ve, ma: e.target.value.toUpperCase() })} />
          )}
          <select className="o dl" value={ve.ma_dl}
                  onChange={e => {
                    const m = e.target.value
                    const d = loai.nhom.flatMap(n => n.dai_luong).find(x => x.ma === m)!
                    // Đổi đại lượng thì điền LẠI tham số mặc định của nó — giữ tham
                    // số cũ là "chu kỳ 14" của RSI dính sang Bollinger.
                    const ts: Record<string, number> = {}
                    for (const t of d.tham_so) ts[t.ten] = t.mac_dinh
                    onDoi({ ...ve, ma_dl: m, duong: d.duong?.[0]?.[0],
                            ...(d.tham_so.length ? { tham_so: ts } : { tham_so: undefined }) })
                  }}>
            {loai.nhom.map(n => (
              <optgroup key={n.ten} label={n.ten}>
                {n.dai_luong.map(d => <option key={d.ma} value={d.ma}>{d.nhan}</option>)}
              </optgroup>
            ))}
          </select>

          {dl?.tham_so.map(t => (
            <label key={t.ten} className="o-ts" title={t.nhan}>
              <span>{t.nhan}</span>
              <input className="o so" inputMode="numeric"
                     value={String(ve.tham_so?.[t.ten] ?? t.mac_dinh)}
                     onChange={e => onDoi({ ...ve, tham_so: {
                       ...(ve.tham_so ?? {}),
                       [t.ten]: e.target.value as unknown as number } })} />
            </label>
          ))}

          {dl?.duong && (
            <select className="o dl" value={ve.duong ?? dl.duong[0][0]}
                    onChange={e => onDoi({ ...ve, duong: e.target.value })}>
              {dl.duong.map(([m, n]) => <option key={m} value={m}>{n}</option>)}
            </select>
          )}
        </>
      )}
    </div>
  )
}

export default function HopDieuKien({ step, tuDien, onLuu, onDong }: {
  step: Step
  tuDien: TuDienHoi
  onLuu: (s: Step) => void
  onDong: () => void
}) {
  const loai = tuDien.loai.find(l => l.ma === step.type)
  const [ten, setTen] = useState(step.name ?? '')
  const [ds, setDs] = useState<DongDieuKien[]>(
    (step.dieu_kien as DongDieuKien[] | undefined) ?? [])

  // Khối vừa tạo thì cho sẵn MỘT dòng: hộp rỗng trơn không nói được phải làm gì.
  useEffect(() => {
    if (ds.length === 0 && loai) them()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!loai) return null

  function moi(): DongDieuKien {
    const d = loai!.nhom[0].dai_luong[0]
    const ts: Record<string, number> = {}
    for (const t of d.tham_so) ts[t.ten] = t.mac_dinh
    return {
      trai: { ma_dl: d.ma, ...(d.tham_so.length ? { tham_so: ts } : {}),
              ...(d.duong ? { duong: d.duong[0][0] } : {}) },
      phep: d.kieu === 'co_khong' ? 'la' : '>',
      phai: { so: 0 },
    }
  }
  const them = () => setDs(x => [...x, moi()])

  function doiDong(i: number, d: Partial<DongDieuKien>) {
    setDs(x => x.map((c, j) => (j === i ? { ...c, ...d } : c)))
  }

  /** Phép so đổi theo KIỂU của vế trái: đại lượng đúng/sai không so lớn-nhỏ được. */
  function phepCua(dk: DongDieuKien) {
    const d = loai!.nhom.flatMap(n => n.dai_luong).find(x => x.ma === dk.trai.ma_dl)
    return d?.kieu === 'co_khong' ? tuDien.phep_co_khong : tuDien.phep_so
  }
  const laCoKhong = (dk: DongDieuKien) => phepCua(dk) === tuDien.phep_co_khong

  return (
    <Modal title={loai.nhan} width={760} onClose={onDong}
           footer={<>
             <button className="nut" onClick={them}><Icon name="plus" /> Thêm điều kiện</button>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh"
                     onClick={() => onLuu({ ...step, name: ten.trim() || loai.nhan,
                                            dieu_kien: ds })}>Lưu</button>
           </>}>
      <div className="hop-dk">
        <div className="mo-ta-loai">
          <Icon name={loai.icon} /> {loai.mo_ta}
        </div>
        {loai.tat && <div className="mc-bao loi">⚠ {loai.tat}</div>}

        <label className="o-hang">
          <span>Tên khối</span>
          <input className="o day" value={ten} spellCheck={false}
                 placeholder={loai.nhan}
                 onChange={e => setTen(e.target.value)} />
        </label>

        <div className="dau-dk">
          Các dòng dưới nối với nhau bằng <b>VÀ</b> — phải đúng hết thì cổng mới khớp.
          Muốn <b>HOẶC</b> thì vẽ thành hai nhánh trên sơ đồ.
        </div>

        {ds.map((dk, i) => (
          <div className="dong-dk" key={i}>
            <span className="va">{i === 0 ? '' : 'VÀ'}</span>
            <Ve ve={dk.trai} loai={loai} td={tuDien} choSo={false}
                choMa={loai.can_ma}
                onDoi={v => {
                  const d = loai.nhom.flatMap(n => n.dai_luong)
                    .find(x => x.ma === v.ma_dl)
                  // Đổi sang đại lượng đúng/sai thì phép so cũ thành vô nghĩa.
                  const p = d?.kieu === 'co_khong' ? 'la' : '>'
                  const doiPhep = (d?.kieu === 'co_khong')
                    !== (phepCua(dk) === tuDien.phep_co_khong)
                  doiDong(i, { trai: v, ...(doiPhep ? { phep: p } : {}) })
                }} />
            <select className="o phep" value={dk.phep}
                    onChange={e => doiDong(i, { phep: e.target.value })}>
              {phepCua(dk).map(p => <option key={p.ma} value={p.ma}>{p.nhan}</option>)}
            </select>
            {laCoKhong(dk)
              ? <span className="ve-dk mo">—</span>
              : <Ve ve={dk.phai} loai={loai} td={tuDien} choSo
                    choMa={loai.hai_ve_ma}
                    onDoi={v => doiDong(i, { phai: v })} />}
            <button className="nut-nho" title="Bỏ dòng này"
                    onClick={() => setDs(x => x.filter((_c, j) => j !== i))}>✕</button>
          </div>
        ))}
      </div>
    </Modal>
  )
}
