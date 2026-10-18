import { useEffect, useRef, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import BangNoi from './BangNoi'
import ChonDaiLuong from './ChonDaiLuong'
import ChonMa from './ChonMa'
import { OGhim } from './ORuot'
import type { DaiLuong, Step, TuDienHoi, VeDieuKien, DongDieuKien } from '../types'

/** MỘT THÀNH PHẦN của chuỗi ghép: một vế, cộng một phép nối vào vế trước. */
type TPGhep = VeDieuKien & { phep: string }

/** HỘP THOẠI KHỐI XÁC NHẬN — nơi người chơi gõ điều kiện.
 *
 *  MỘT DÒNG = MỘT ĐIỀU KIỆN, các dòng nối bằng VÀ. Muốn HOẶC thì KHÔNG nhét vào đây —
 *  vẽ thành hai nhánh trên sơ đồ. Đó là ngữ pháp đã chốt: *"cái nào trong N cái" là
 *  hình học, không phải cú pháp*; nhét HOẶC vào hộp thoại là giấu mất một quyết định
 *  mà lẽ ra phải nhìn thấy trên canvas.
 *
 *  BA Ô, KHÔNG HƠN:  [ vế trái ⚙ ]  [ > ]  [ vế phải ⚙ ]
 *
 *  ⚠ Bản trước rải MỌI thứ của một vế ra cùng một hàng: ô mã, ô đại lượng, một ô số
 *  cho mỗi tham số, ô chọn đường. MACD so với MACD là **15 ô** trên một dòng — hàng
 *  tràn ngang, chữ "một đại lượng" bị cắt còn "một đại lượ", và không bề rộng cửa sổ
 *  nào cứu được, vì số ô phụ thuộc vào đại lượng người dùng chọn.
 *
 *  Nay mỗi vế là MỘT cái nút: bấm vào CHỮ để đổi *cái gì*, bấm vào BÁNH RĂNG để chỉnh
 *  *thế nào*. Bánh răng chỉ mọc ra khi thật sự có gì để chỉnh — `Giờ` không có mã,
 *  không tham số, nên không có bánh răng. Dòng rộng bao nhiêu cũng vừa.
 */

/** Dấu thay cho chữ. Chữ "lớn hơn hoặc bằng" dài gấp sáu lần `≥` mà không nói thêm
 *  gì — và sáu phép cố định thì bắt mở dropdown là bắt bấm thừa một nhát.
 *
 *  ⚠ CHỈ ĐỔI CÁCH HIỆN. Trong file vẫn lưu `>=`, `!=` như cũ, nên mọi sơ đồ đã lưu
 *  mở ra vẫn đúng và bộ sinh mã không phải biết gì về bảng này. */
const DAU: Record<string, string> = {
  '>': '>', '<': '<', '>=': '≥', '<=': '≤', '==': '=', '!=': '≠',
}

/** Một VẾ: chọn đại lượng (+ mã, tham số, đường), hoặc gõ một con số.
 *
 *  XUẤT RA ngoài vì khối «Vẽ lên bảng» cũng cần đúng bộ chọn này — `Plot` của LEAN
 *  nhận một con số, và con số ấy lấy từ cùng kho đại lượng. Hai bộ chọn thì sớm muộn
 *  một bên bày ra thứ bên kia không có. */
/** Mấy núm của MỘT đại lượng: mã, tham số, đường. Dùng hai lần trong một bảng —
 *  cho đại lượng chính và cho đại lượng được GHÉP vào — nên tách ra, hai bản sao thì
 *  sớm muộn một bên thêm núm mà bên kia không có. */
function ChinhDL({ dl, ve, dsMa, coMaDangXet, onDoi }: {
  dl: DaiLuong
  ve: VeDieuKien
  dsMa: string[]
  coMaDangXet: boolean
  onDoi: (v: Partial<VeDieuKien>) => void
}) {
  return (<>
    {dl.can_ma && (
      <label className="bn-hang"><span>Mã</span>
        <ChonMa ds={dsMa} giaTri={ve.ma} coMaDangXet={coMaDangXet}
                onDoi={m => onDoi({ ma: m || undefined })} />
      </label>
    )}
    {dl.tham_so.map(t => (
      <label key={t.ten} className="bn-hang"><span>{t.nhan}</span>
        <OGhim chu={ve as unknown as Record<string, unknown>} tenO={t.ten}
               nhan={`${dl.nhan.split(' — ')[0]} ${t.nhan}`}
               so={ve.tham_so?.[t.ten] ?? t.mac_dinh}
               onDoi={m => onDoi(m as unknown as VeDieuKien)}>
          <input className="o so" inputMode="numeric"
                 value={String(ve.tham_so?.[t.ten] ?? t.mac_dinh)}
                 onChange={e => onDoi({ ...ve, tham_so: {
                   ...(ve.tham_so ?? {}),
                   [t.ten]: e.target.value as unknown as number } })} />
        </OGhim>
      </label>
    ))}
    {dl.duong && (
      <label className="bn-hang"><span>Đường</span>
        <select className="o" value={ve.duong ?? dl.duong[0][0]}
                onChange={e => onDoi({ duong: e.target.value })}>
          {dl.duong.map(([m, n]) => <option key={m} value={m}>{n}</option>)}
        </select>
      </label>
    )}
  </>)
}

/** Bảng chọn đại lượng cho VẾ GHÉP — `select` thường, không phải bảng nổi thứ hai.
 *
 *  ⚠ VÌ SAO KHÔNG LỒNG `Ve` VÀO ĐÂY. `BangNoi` nghe Esc trên `window`, và hai bảng
 *  lồng nhau thì bảng NGOÀI đăng ký trước nên nó đóng trước — một phím Esc đóng cả
 *  hai, mất cả phép ghép vừa đặt. `select` của trình duyệt không có chuyện đó. */
function ChonGhep({ td, giaTri, onDoi }: {
  td: TuDienHoi
  giaTri: string
  onDoi: (ma: string) => void
}) {
  const nhom = [...new Set(td.kho.filter(d => d.kieu === 'so').map(d => d.nhom))]
  return (
    <select className="o" value={giaTri} onChange={e => onDoi(e.target.value)}>
      <option value="">một con số</option>
      {nhom.map(n => (
        <optgroup key={n} label={n}>
          {td.kho.filter(d => d.kieu === 'so' && d.nhom === n).map(d => (
            <option key={d.ma} value={d.ma}>{d.nhan}</option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}

export function Ve({ ve, td, dsMa, coMaDangXet = true, choSo, donViKia, onDoi }: {
  ve: VeDieuKien
  td: TuDienHoi
  /** Mã khối Bắt đầu đang khai — nguồn DUY NHẤT của ô chọn mã. */
  dsMa: string[]
  coMaDangXet?: boolean
  /** Vế phải được phép là một con số; vế trái thì không. */
  choSo: boolean
  /** Đơn vị của vế bên kia — để xếp «cùng đơn vị» lên trước. */
  donViKia?: string
  onDoi: (v: VeDieuKien) => void
}) {
  const [mo, setMo] = useState<'' | 'chon' | 'chinh'>('')
  const nutRf = useRef<HTMLButtonElement>(null)
  const gearRf = useRef<HTMLButtonElement>(null)
  const [neo, setNeo] = useState<DOMRect | null>(null)

  const laSo = choSo && ve.ma_dl === undefined
  const dl = ve.ma_dl ? td.kho.find(d => d.ma === ve.ma_dl) : undefined
  // Đại lượng kiểu SỐ thì bánh răng luôn có, kể cả khi nó không mã không tham số:
  // phép GHÉP nằm trong bảng ấy, không có bánh răng thì không ai tới được.
  // Ô CON SỐ cũng có bánh răng — ngưỡng so sánh («RSI <= 45») là thứ đáng ghim
  // làm tham số nhất, mà trước đây nó là chỗ DUY NHẤT không có bánh răng nào.
  const coChinh = laSo || (!!dl && (dl.can_ma || dl.tham_so.length > 0
                                    || !!dl.duong || dl.kieu === 'so'))
  /* ⚠ ĐỌC PHẢI NHẬN CẢ HAI HÌNH. File cũ ghi `ghep` là MỘT object; bản này ghi một
     DANH SÁCH. Mất nhánh gói-thành-danh-sách là mọi sơ đồ đã lưu mất phần ghép —
     hộp thoại vẫn mở, vẫn sửa được, chỉ là nửa điều kiện biến mất không một lời.
     Đây là bản sao của `hoi.ds_ghep` bên Python; `test_giao_dien` canh hai bên. */
  const dsGhep: TPGhep[] = Array.isArray(ve.ghep) ? ve.ghep
    : (ve.ghep ? [ve.ghep] : [])

  const bat = (o: 'chon' | 'chinh', r: React.RefObject<HTMLButtonElement>) => {
    setNeo(r.current?.getBoundingClientRect() ?? null)
    setMo(o)
  }

  /** Đổi đại lượng thì điền LẠI tham số mặc định của nó — giữ tham số cũ là "chu kỳ
   *  14" của RSI dính sang Bollinger. */
  const chonDL = (d: DaiLuong) => {
    const ts: Record<string, number> = {}
    for (const t of d.tham_so) ts[t.ten] = t.mac_dinh
    onDoi({ ma: d.can_ma ? ve.ma : undefined, ma_dl: d.ma,
            duong: d.duong?.[0]?.[0],
            ...(d.tham_so.length ? { tham_so: ts } : { tham_so: undefined }) })
  }

  return (
    <div className="ve-dk">
      <button ref={nutRf} type="button" className="o nut-ve"
              title={dl ? dl.lean : 'Bấm để chọn đại lượng'}
              onClick={() => bat('chon', nutRf)}>
        {/* Mặt nút là mấy MẨU rời, không phải một câu ghép sẵn: câu tả chuẩn do
            Python dựng (`mo_ta_dieu_kien`) và nó hiện trên thẻ khối, không phải ở
            đây — hai chỗ cùng ghép câu thì sớm muộn nói khác nhau. */}
        {laSo ? <span className="ve-so">{String(ve.so ?? 0)}</span> : dl ? (<>
          {ve.ma && <span className="ve-ma">{ve.ma}</span>}
          <span className="ve-ten">{dl.nhan.split(' — ')[0]}</span>
          {ve.tham_so && Object.keys(ve.tham_so).length > 0 && (
            <span className="ve-ts">({Object.values(ve.tham_so).join(',')})</span>
          )}
          {ve.duong && <span className="ve-ts">
            {dl.duong?.find(([m]) => m === ve.duong)?.[1] ?? ve.duong}</span>}
        </>) : <span className="ve-trong">chọn đại lượng…</span>}
      </button>

      {coChinh && (
        <button ref={gearRf} type="button" className="nut-nho nut-rang"
                title="Chỉnh mã, chu kỳ, đường" onClick={() => bat('chinh', gearRf)}>
          <Icon name="gear" />
        </button>
      )}

      {mo === 'chon' && neo && (
        <ChonDaiLuong neo={neo} td={td} dangChon={ve.ma_dl} donViKia={donViKia}
                      choSo={choSo ? { gia_tri: Number(ve.so ?? 0) } : undefined}
                      onChonSo={n => onDoi({ so: n })}
                      onChon={chonDL} onDong={() => setMo('')} />
      )}

      {mo === 'chinh' && neo && (dl || laSo) && (
        <BangNoi neo={neo} rong={262} cao={440} onDong={() => setMo('')}>
          <div className="bn-chinh">
            {laSo ? (
              <label className="bn-hang"><span>Con số</span>
                <OGhim chu={ve as unknown as Record<string, unknown>} tenO="so"
                       nhan="nguong" so={ve.so ?? 0}
                       onDoi={m => onDoi(m as unknown as VeDieuKien)}>
                  <input className="o so" inputMode="decimal"
                         value={String(ve.so ?? 0)}
                         onChange={e => onDoi({ ...ve,
                           so: e.target.value as unknown as number })} />
                </OGhim>
              </label>
            ) : (
              <ChinhDL dl={dl!} ve={ve} dsMa={dsMa} coMaDangXet={coMaDangXet}
                       onDoi={v => onDoi({ ...ve, ...v })} />
            )}

            {/* GHÉP — một CHUỖI thành phần, nối TRÁI→PHẢI.
                «giá / đỉnh 60 nến ≤ 0,97» là rơi 3% từ đỉnh — hai thành phần.
                «0,25×ROC(63) + 0,35×ROC(126) + 0,40×ROC(252) − 0,20×độ lệch» là
                một điểm số — bốn thành phần. Cùng một hình, khác số dòng.

                Chỉ bày cho đại lượng kiểu SỐ: ĐÚNG/SAI thì cộng trừ vô nghĩa. */}
            {(!dl || dl.kieu === 'so') && (<>
              {dsGhep.length > 0 && (
                <label className="bn-hang"><span>Hệ số</span>
                  <input className="o so" inputMode="decimal"
                         defaultValue={String(ve.he_so ?? 1)}
                         onChange={e => onDoi({ ...ve,
                           he_so: e.target.value as unknown as number })} />
                  <span className="bn-nhac">× đại lượng trên</span>
                </label>
              )}
              {dsGhep.map((g, i) => {
                const dlG = g.ma_dl ? td.kho.find(d => d.ma === g.ma_dl) : undefined
                const doiTP = (v: Partial<TPGhep> | null) =>
                  onDoi({ ...ve, ghep: v === null
                    ? dsGhep.filter((_, k) => k !== i)
                    : dsGhep.map((x, k) => (k === i ? { ...x, ...v } : x)) })
                return (
                  <div className="bn-tp" key={i}>
                    <label className="bn-hang bn-ghep"><span>Rồi</span>
                      <select className="o bn-phep" value={g.phep}
                              onChange={e => doiTP({ phep: e.target.value })}>
                        {td.phep_ghep.map(p => (
                          <option key={p.ma} value={p.ma}>{p.nhan}</option>
                        ))}
                      </select>
                      <input className="o so" inputMode="decimal"
                             defaultValue={String(g.he_so ?? 1)}
                             onChange={e => doiTP({
                               he_so: e.target.value as unknown as number })} />
                      <span className="bn-nhac">×</span>
                      <button className="nut-nho" title="Bỏ thành phần này"
                              onClick={() => doiTP(null)}>✕</button>
                    </label>
                    <label className="bn-hang"><span>Đại lượng</span>
                      <ChonGhep td={td} giaTri={g.ma_dl ?? ''} onDoi={ma => {
                        if (!ma) { doiTP({ ma_dl: undefined, so: 1 }); return }
                        const d = td.kho.find(x => x.ma === ma)
                        if (!d) return
                        const ts: Record<string, number> = {}
                        for (const t of d.tham_so) ts[t.ten] = t.mac_dinh
                        doiTP({ ma_dl: ma, so: undefined,
                          duong: d.duong?.[0]?.[0],
                          ...(d.tham_so.length ? { tham_so: ts } : {}) })
                      }} />
                    </label>
                    {dlG
                      ? <ChinhDL dl={dlG} ve={g} dsMa={dsMa}
                                 coMaDangXet={coMaDangXet}
                                 onDoi={v => doiTP(v as Partial<TPGhep>)} />
                      : <label className="bn-hang"><span>Con số</span>
                          {/* `defaultValue` + chuyền NGUYÊN chuỗi, đúng lối ô số
                              của `ChonDaiLuong`: ép `Number()` từng phím là nuốt
                              dấu chấm, «0.97» lặng lẽ thành «97». */}
                          <input className="o so" inputMode="decimal"
                                 defaultValue={String(g.so ?? 1)}
                                 onChange={e => doiTP({ ma_dl: undefined,
                                   so: e.target.value as unknown as number })} />
                        </label>}
                  </div>
                )
              })}
              <label className="bn-hang bn-them-tp"><span />
                <button className="nut-nho" onClick={() => onDoi({ ...ve,
                  // Mở ra là SỐ 1, không đoán hộ một đại lượng. Và 1 chứ không
                  // phải 0: chia cho 0 thì cả vế thành 0 cứng.
                  ghep: [...dsGhep, { phep: '+', he_so: 1, so: 1 }] })}>
                  + Ghép thêm một thành phần
                </button>
              </label>
            </>)}
          </div>
          {/* NGOÀI `.bn-chinh` — tấm ấy cuộn được, nên dòng khai hàm LEAN để trong
              nó là nó cuộn mất. Ghim ở chân, đúng như bảng chọn đại lượng. */}
          <div className="bn-lean">
            {dl ? dl.lean : 'một con số'}
            {dsGhep.map((g, i) => {
              const dlG = g.ma_dl ? td.kho.find(d => d.ma === g.ma_dl) : undefined
              const he = Number(g.he_so ?? 1)
              return ` ${g.phep} ${he === 1 ? '' : `${he} * `}${
                dlG ? dlG.lean : String(g.so ?? 1)}`
            }).join('')}
          </div>
        </BangNoi>
      )}
    </div>
  )
}

export default function HopDieuKien({ step, tuDien, dsMa, coMaDangXet, onLuu, onDong }: {
  step: Step
  tuDien: TuDienHoi
  dsMa: string[]
  coMaDangXet: boolean
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

  const dlCua = (v?: VeDieuKien) =>
    (v?.ma_dl ? tuDien.kho.find(d => d.ma === v.ma_dl) : undefined)

  /** Dòng mới mở sẵn ở đại lượng ĐẦU của họ khối này — người chơi thả khối "Hỏi vị
   *  thế" thì muốn hỏi về vị thế, dù nay đổi sang họ khác được. */
  function moi(): DongDieuKien {
    const d = tuDien.kho.find(x => x.ho === loai!.ma) ?? tuDien.kho[0]
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
  const laCoKhong = (dk: DongDieuKien) => dlCua(dk.trai)?.kieu === 'co_khong'

  return (
    <Modal title={loai.nhan} width={720} onClose={onDong}
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

        {ds.map((dk, i) => {
          const ck = laCoKhong(dk)
          const phep = ck ? tuDien.phep_co_khong : tuDien.phep_so
          return (
            <div className="dong-dk" key={i}>
              <span className="va">{i === 0 ? '' : 'VÀ'}</span>
              <Ve ve={dk.trai} td={tuDien} dsMa={dsMa} coMaDangXet={coMaDangXet}
                  choSo={false} donViKia={dlCua(dk.phai)?.don_vi}
                  onDoi={v => {
                    const d = v.ma_dl ? tuDien.kho.find(x => x.ma === v.ma_dl) : undefined
                    // Đổi sang đại lượng đúng/sai thì phép so cũ thành vô nghĩa.
                    const sangCK = d?.kieu === 'co_khong'
                    doiDong(i, { trai: v,
                                 ...(sangCK !== ck ? { phep: sangCK ? 'la' : '>' } : {}) })
                  }} />

              {/* Sáu dấu liền nhau thay cho một dropdown. Chữ đầy đủ vẫn còn — nằm ở
                  `title`, rê chuột là đọc được. */}
              <div className={`cum-phep${ck ? ' ck' : ''}`} role="group">
                {phep.map(p => (
                  <button key={p.ma} type="button" title={p.nhan}
                          className={dk.phep === p.ma ? 'dang' : ''}
                          onClick={() => doiDong(i, { phep: p.ma })}>
                    {ck ? p.nhan.replace('là ', '') : (DAU[p.ma] ?? p.ma)}
                  </button>
                ))}
              </div>

              {ck
                ? <span className="ve-dk mo">— không có vế phải —</span>
                : <Ve ve={dk.phai} td={tuDien} dsMa={dsMa} coMaDangXet={coMaDangXet}
                      choSo donViKia={dlCua(dk.trai)?.don_vi}
                      onDoi={v => doiDong(i, { phai: v })} />}

              <button className="nut-nho" title="Bỏ dòng này"
                      onClick={() => setDs(x => x.filter((_c, j) => j !== i))}>✕</button>
            </div>
          )
        })}
      </div>
    </Modal>
  )
}
