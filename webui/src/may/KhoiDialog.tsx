import { useCallback, useEffect, useRef, useState } from 'react'
import { pyMay } from '../api'
import Icon from '../components/Icon'
import Modal from '../components/Modal'
import { chotSo, locSo } from '../so'
import type { ThamSo } from '../types'
import { daiLuongCuaTram, nhomDaiLuong, oCoNghia } from './doThi'
import type {
  BootMay, KhoiMay, OKhai, TheKhoi, ToanHangKhai, TramKey, VanDeMay,
} from './mayTypes'

/** HỘP THOẠI KHỐI của cỗ máy 5 trạm.  (D-10, phần 5, lát 5c)
 *
 *  Hai luật, cả hai đều là lý do file này tồn tại:
 *
 *  1. **Hộp thoại KHÔNG tự soát gì.** Mỗi lần người chơi đổi một ô, bản nháp thô bay
 *     sang `may_luu_khoi`; Python trả về khối đã chuẩn hoá, CHỮ trên khối và vấn đề của
 *     chính khối đó. Nên không có luật hợp lệ nào sống ở đây để mà lệch với luật thật.
 *  2. **Chỉ bày ra thứ dùng được Ở TRẠM NÀY.** Khối Làm chỉ của trạm đang mở; đại lượng
 *     chỉ những cái trạm này đọc được («tín hiệu» chỉ ở ③, «khớp lệnh» chỉ ở ⑤). Bày hết
 *     rồi báo lỗi sau là bắt người chơi học bằng cách làm sai.
 */

/* ---------------------------- ô số (có thể là TÊN THAM SỐ) ---------------------- */

function OSo({ v, dat, thamSo, nguyen, title, lop }: {
  v: number | string | undefined
  dat: (x: number | string) => void
  thamSo: ThamSo[]
  nguyen?: boolean
  title?: string
  lop?: string
}) {
  /** Bản nháp đang gõ — `null` = ô đang hiện giá trị thật. */
  const [nhap, datNhap] = useState<string | null>(null)
  const laTen = typeof v === 'string' && v !== ''
  const ts = laTen ? thamSo.find(t => t.ten === v) : undefined
  const hop = thamSo.filter(t => t.ten !== v)

  if (laTen) {
    return (
      <span className={'chip-ts' + (ts ? '' : ' mat') + (lop ? ' ' + lop : '')}
            title={ts
              ? `Tham số "${v}" = ${ts.gia_tri}${ts.don_vi ? ` (${ts.don_vi})` : ''}`
              : `Không còn tham số nào tên "${v}" trong bảng — bấm ✕ để gõ lại một số.`}>
        <span className="chip-ten">{v}</span>
        <button className="chip-x" title="Bỏ tên, quay lại gõ số"
                onClick={() => dat(ts ? Number(ts.gia_tri) : 0)}>✕</button>
      </span>
    )
  }
  return (
    <span className={'cum-so' + (lop ? ' ' + lop : '')}>
      {/* ⚠ BẢN NHÁP khi đang gõ — ép về số ngay từng phím là NUỐT dấu chấm: `"1."` ra
          `1`, state không đổi, React ghi đè ô về `"1"`, phím kế cho `"15"`. Xem
          `src/so.ts` và bài kiểm `webui/kiem/o_so.mjs`. */}
      <input className="o so nho" inputMode="decimal" spellCheck={false}
             value={nhap ?? (v ?? '')} title={title}
             onChange={e => {
               const { chu, so } = locSo(e.target.value, nguyen)
               datNhap(chu)
               if (so !== null) dat(so)
             }}
             onBlur={() => {
               if (nhap !== null && locSo(nhap, nguyen).so === null) dat(chotSo(nhap))
               datNhap(null)
             }} />
      {/* Chỉ hiện khi cỗ máy CÓ tham số — không có thì ô sạch như cũ. */}
      {hop.length > 0 && (
        <select className="chon-ts" value=""
                title="Dùng một tham số đã có thay cho con số này"
                onChange={e => e.target.value && dat(e.target.value)}>
          <option value="">▾</option>
          {hop.map(t => (
            <option key={t.ten} value={t.ten}>
              {t.ten} = {t.gia_tri}{t.don_vi ? ` ${t.don_vi}` : ''}
            </option>
          ))}
        </select>
      )}
    </span>
  )
}

/* ------------------------------- ô ĐẠI LƯỢNG ----------------------------------- */

function ODaiLuong({ o, boot, tram, thamSo, dat, veFai }: {
  o: Record<string, unknown>
  boot: BootMay
  tram: TramKey
  thamSo: ThamSo[]
  dat: (x: Record<string, unknown>) => void
  /** Vế phải còn có hệ số nhân: `Giá đóng(D1) > SMA(D1, 200) × 1.02`. */
  veFai?: boolean
}) {
  const ds = daiLuongCuaTram(boot, tram)
  const d: ToanHangKhai | undefined = boot.toan_hang.find(t => t.key === o.ten)
  const nhom = nhomDaiLuong(ds)

  return (
    <span className="cum-toan-hang">
      <select className="o" value={String(o.ten ?? '')}
              title={d?.mo_ta || 'Đại lượng khối Hỏi đọc được ở trạm này'}
              onChange={e => dat({ ten: e.target.value })}>
        {!d && <option value={String(o.ten ?? '')}>
          {o.ten ? `«${String(o.ten)}» — không đọc được ở trạm này` : '— chọn đại lượng —'}
        </option>}
        {nhom.map(n => (
          <optgroup key={n} label={n}>
            {ds.filter(t => t.nhom === n).map(t => (
              <option key={t.key} value={t.key}>{t.nhan}</option>
            ))}
          </optgroup>
        ))}
      </select>

      {/* Tham số của chính đại lượng đó — khai ở `tram.THAM_SO_TH`, nên thêm một tham
          số bên Python là hộp thoại có ngay. */}
      {(d?.tham_so ?? []).map(k => {
        const khai = boot.tham_so_th[k]
        if (!khai) return null
        const chon = k === 'dong' ? (d?.dong ?? {})
          : k === 'khung' ? Object.fromEntries(boot.khung.map(x => [x, x]))
            : khai.chon
        if (khai.loai === 'chon' && chon) {
          return (
            <select key={k} className="o nho" value={String(o[k] ?? '')}
                    title={khai.nhan}
                    onChange={e => dat({ ...o, [k]: e.target.value })}>
              {Object.entries(chon).map(([v, nhan]) => (
                <option key={v} value={v}>{nhan}</option>
              ))}
            </select>
          )
        }
        return (
          <span key={k} className="nhan-o" title={khai.nhan}>
            <span className="nhan-cho">{khai.nhan}</span>
            <OSo v={o[k] as number | string | undefined} thamSo={thamSo}
                 nguyen={khai.nguyen} title={khai.nhan}
                 dat={x => dat({ ...o, [k]: x })} />
          </span>
        )
      })}

      {veFai && d && (
        <span className="nhan-o" title="Nhân đại lượng này với một hệ số">
          <span className="nhan-cho">×</span>
          <OSo v={(o.he_so as number | string | undefined) ?? 1} thamSo={thamSo}
               title="Hệ số nhân — bỏ trống hoặc 1 là không nhân"
               dat={x => dat({ ...o, he_so: x })} />
        </span>
      )}
    </span>
  )
}

/* ------------------------------ một dòng điều kiện ------------------------------ */

function DongDieuKien({ c, boot, tram, thamSo, dat, xoa, so }: {
  c: Record<string, unknown>
  boot: BootMay
  tram: TramKey
  thamSo: ThamSo[]
  dat: (x: Record<string, unknown>) => void
  xoa: () => void
  so: number
}) {
  const phai = (c.phai ?? {}) as Record<string, unknown>
  const phaiLaDaiLuong = 'ten' in phai

  return (
    <div className="dong-dk may">
      {/* Nối tiếp = VÀ. Ghi ra, vì nhìn hai dòng cạnh nhau thì đoán là HOẶC cũng hợp lý
          như đoán là VÀ — mà hai cái cho hai cỗ máy khác hẳn nhau. */}
      <span className="so-dk">{so === 0 ? '' : 'và'}</span>
      <ODaiLuong o={(c.trai ?? {}) as Record<string, unknown>} boot={boot} tram={tram}
                 thamSo={thamSo} dat={x => dat({ ...c, trai: x })} />
      <select className="o nho phep" value={String(c.phep ?? '>')}
              onChange={e => dat({ ...c, phep: e.target.value })}>
        {Object.entries(boot.phep_so).map(([v, nhan]) => (
          <option key={v} value={v}>{nhan}</option>
        ))}
      </select>
      <select className="o nho"
              title="Vế phải: một con số (hoặc tham số), hay một đại lượng khác"
              value={phaiLaDaiLuong ? 'dl' : 'so'}
              onChange={e => dat({
                ...c,
                phai: e.target.value === 'dl'
                  ? { ten: boot.toan_hang_cua_tram[tram]?.[0] ?? '' }
                  : { value: 0 },
              })}>
        <option value="so">số</option>
        <option value="dl">đại lượng</option>
      </select>
      {phaiLaDaiLuong
        ? <ODaiLuong o={phai} boot={boot} tram={tram} thamSo={thamSo} veFai
                     dat={x => dat({ ...c, phai: x })} />
        : <OSo v={phai.value as number | string | undefined} thamSo={thamSo}
               dat={x => dat({ ...c, phai: { value: x } })} />}
      <button className="xoa-dk" title="Bỏ điều kiện này" onClick={xoa}>✕</button>
    </div>
  )
}

/* ----------------------------------- hộp thoại --------------------------------- */

export default function KhoiDialog({ khoi, tram, boot, thamSo, onLuu, onDong }: {
  khoi: KhoiMay
  tram: TramKey
  boot: BootMay
  thamSo: ThamSo[]
  onLuu: (st: KhoiMay) => void
  onDong: () => void
}) {
  const [nhap, setNhap] = useState<KhoiMay>(() => JSON.parse(JSON.stringify(khoi)))
  const [the, setThe] = useState<TheKhoi | null>(null)
  const [loi, setLoi] = useState<VanDeMay[]>([])
  /** Khối ĐÃ CHUẨN HOÁ do Python trả về — đó mới là cái được lưu, không phải bản nháp. */
  const sach = useRef<KhoiMay | null>(null)

  const laHoi = nhap.type === boot.hoi
  const khai = laHoi ? null : boot.khoi_lam[String(nhap.type)]

  /* Mỗi lần đổi một ô: gửi bản nháp sang Python, nhận lại chữ trên khối và vấn đề.
     Không debounce — cầu nối nằm ngay trong tiến trình, và thấy chữ đổi NGAY khi vặn
     núm là nửa giá trị của hộp thoại này. */
  useEffect(() => {
    let song = true
    pyMay.may_luu_khoi(tram, nhap as unknown as Record<string, unknown>, thamSo)
      .then(r => {
        if (!song) return
        if (r.ok && r.value) {
          sach.current = r.value.step
          setThe(r.value.card)
          setLoi((r.loi as VanDeMay[]) ?? [])
        } else {
          setLoi([{ severity: 'error', message: r.error ?? 'không đọc được khối',
                    tram, step: null, index: null }])
        }
      })
    return () => { song = false }
  }, [nhap, tram, thamSo])

  const dieuKien = (nhap.conditions ?? []) as Record<string, unknown>[]
  const datDK = useCallback((ds: Record<string, unknown>[]) => {
    setNhap(n => ({ ...n, conditions: ds }))
  }, [])

  /** Một ô của khối Làm — `khi` quyết định ô có nghĩa hay không ở trạng thái hiện tại. */
  function veO(f: OKhai) {
    if (!oCoNghia(f, nhap as Record<string, unknown>)) return null
    const v = nhap[f.key]
    const dat = (x: unknown) => setNhap(n => ({ ...n, [f.key]: x }))
    return (
      <div className="hang" key={f.key}>
        <label className="nhan-o">{f.nhan}</label>
        {f.loai === 'chon' && f.chon ? (
          <select className="o" value={String(v ?? f.mac_dinh ?? '')}
                  onChange={e => dat(e.target.value)}>
            {Object.entries(f.chon).map(([k, nhan]) => (
              <option key={k} value={k}>{nhan}</option>
            ))}
          </select>
        ) : f.loai === 'bat_tat' ? (
          <label className="tick">
            <input type="checkbox" checked={v === undefined ? !!f.mac_dinh : !!v}
                   onChange={e => dat(e.target.checked)} />
            <span>{f.nhan}</span>
          </label>
        ) : f.loai === 'toan_hang' ? (
          <span className="cum-toan-hang">
            {v
              ? <ODaiLuong o={v as Record<string, unknown>} boot={boot} tram={tram}
                           thamSo={thamSo} dat={x => dat(x)} />
              : <button className="nut nho" onClick={() => dat({ ten: '' })}>
                  + thêm {f.nhan}
                </button>}
            {!!v && f.tuy_chon && (
              <button className="xoa-dk" title={`Bỏ ${f.nhan}`}
                      onClick={() => dat(null)}>✕</button>
            )}
          </span>
        ) : (
          <OSo v={v as number | string | undefined} thamSo={thamSo} nguyen={f.nguyen}
               title={[f.min !== undefined ? `từ ${f.min}` : '',
                       f.max !== undefined ? `tới ${f.max}` : ''].filter(Boolean).join(' ')}
               dat={x => dat(x)} />
        )}
        {f.tuy_chon && f.loai !== 'toan_hang' && (
          <span className="goi-y">có thể bỏ trống</span>
        )}
      </div>
    )
  }

  const tenTram = boot.tram.find(t => t.key === tram)
  return (
    <Modal
      title={`${laHoi ? boot.nhan_hoi : khai?.nhan ?? 'Khối'} — ${tenTram?.so ?? ''} ${tenTram?.ten ?? ''}`}
      width={760} onClose={onDong}
      footer={<>
        <span className="day" />
        <button className="nut" onClick={onDong}>Huỷ</button>
        <button className="nut chinh"
                onClick={() => { onLuu(sach.current ?? nhap); onDong() }}>Lưu khối</button>
      </>}>

      {/* Mô tả của khối do `tram.py` khai — một câu nói khối này làm gì, không phải chú
          thích viết lại trong JS. */}
      {(khai?.mo_ta || (laHoi && 'Qua thì đi tiếp; trượt thì thử nhánh kế bên dưới.')) && (
        <div className="chu-dan">
          {khai?.mo_ta ?? 'Qua thì đi tiếp; trượt thì thử nhánh kế bên dưới.'}
          {khai?.vai === 'phu' && (
            <b> Khối phụ: phải đi kèm một khối quyết định, tự nó không chốt gì.</b>
          )}
        </div>
      )}

      <div className="hang">
        <label className="nhan-o">Tên khối</label>
        <input className="o co-gian" spellCheck={false}
               value={String(nhap.name ?? '')}
               placeholder={laHoi ? boot.nhan_hoi : khai?.nhan ?? ''}
               title="Tên hiện trên hộp — đặt theo câu hỏi thì sơ đồ đọc như một mạch văn"
               onChange={e => setNhap(n => ({ ...n, name: e.target.value }))} />
      </div>

      {laHoi ? (
        <div className="khoi-form">
          {dieuKien.map((c, i) => (
            <DongDieuKien key={i} c={c} boot={boot} tram={tram} thamSo={thamSo} so={i}
                          dat={x => datDK(dieuKien.map((y, j) => (j === i ? x : y)))}
                          xoa={() => datDK(dieuKien.filter((_, j) => j !== i))} />
          ))}
          <div>
            <button className="nut nho" onClick={() => datDK([...dieuKien, {
              trai: { ten: boot.toan_hang_cua_tram[tram]?.[0] ?? '' },
              phep: '>', phai: { value: 0 },
            }])}>
              <Icon name="plus" /> Thêm điều kiện (VÀ)
            </button>
          </div>
        </div>
      ) : (
        <div className="khoi-form">{(khai?.truong ?? []).map(veO)}</div>
      )}

      {/* XEM TRƯỚC: đúng chữ sẽ hiện trên hộp, do Python dựng. Vặn một núm là thấy đổi
          ngay — không phải đóng hộp thoại rồi mới biết mình vừa làm gì. */}
      <div className="xem-truoc">
        <div className="tieu-de-phu">Trên hộp sẽ hiện</div>
        {(the?.lines ?? []).map((d, i) => <div key={i} className="dong">{d.text}</div>)}
        {!the?.lines.length && <div className="dong mo">—</div>}
      </div>

      {loi.length > 0 && (
        <div className="loi-form">
          {loi.map((v, i) => (
            <div key={i} className={v.severity === 'error' ? 'loi-ghi' : 'goi-y'}>
              {v.severity === 'error' ? '● ' : '▲ '}{v.message}
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
