import { useEffect, useState } from 'react'
import { py } from '../api'
import { chotSo, locSo } from '../so'
import type { Bootstrap, Tab } from '../types'
import Icon from './Icon'
import Modal from './Modal'

/** Hộp thoại sửa MỘT hành động.
 *
 *  Hộp thoại này KHÔNG tự soát lỗi: nó gửi bản nháp thô sang `api.save_action`, Python
 *  chuẩn hoá rồi trả về câu mô tả + danh sách lỗi. Nhờ vậy luật hợp lệ chỉ nằm ở đúng
 *  một chỗ (`core.validate_actions`), và dòng chữ xem trước ở đây chắc chắn là đúng
 *  cái lõi thực sự hiểu — chứ không phải bản dịch thứ hai do JS ghép.
 *
 *  ⚠ ~590 dòng của bản D_02 đã đi ở đợt 3, cùng từ vựng bên Python: ô Hướng · Loại
 *  lệnh · Lot · Đặt tại · Đệm · SL · TP · Chế độ sửa, và cơ chế ẩn-ô-theo-ngữ-cảnh
 *  (thứ thuộc về zone bị GIẤU khi khối chưa nằm sau cổng zone).
 *
 *  HAI BÀI HỌC CỦA BẢN CŨ THÌ SỐNG NGUYÊN VẸN trong file này:
 *
 *  · **`OSo`** — ô số dùng chung cho MỌI chỗ chờ một con số, và nó cố tình "ngu": gõ
 *    thì chỉ ra SỐ. Trước đó bốn trong năm ô chạy `parseFloat` nên chúng **hiện ra
 *    một cái tên mà gõ vào là nuốt mất** (`chu_ky_atr` → `0`), trong khi ô thứ năm lại
 *    mời gõ tên. Lọc từng phím nằm ở `so.ts` vì phải kiểm được bằng máy — lỗi kiểu này
 *    chỉ lộ khi gõ TỪNG PHÍM (`"1."` → `1` → React ghi đè → `1,5` thành `15`).
 *  · **Không có nguồn sự thật thứ hai.** Bản cũ giữ cờ `so_dai_luong` cho CẢ KHỐI,
 *    tách rời khỏi dữ liệu điều kiện — nên có ca sơ đồ mẫu thiếu cờ: hộp thoại tưởng
 *    là "so với giá trị" và bày ô số trắng trơn, trong khi CHỮ TRÊN THẺ vẫn đúng vì nó
 *    tự suy từ `phai.ten`. Ở đây cờ ấy KHÔNG tồn tại: chế độ so được suy thẳng từ dữ
 *    liệu (`!!phai.ten`), nên không có gì để lệch.
 *
 *  Xem `tai_lieu/o_cam_trong.md`; bản cũ ở
 *  `git show f1c90fb:webui/src/components/ActionDialog.tsx`.
 */

type HD = Record<string, any>
type DK = Record<string, any>

/* ------------------------------- ô số dùng chung ------------------------------ */

/** Giữ bản nháp CHUỖI trong state riêng, chỉ đẩy số lên tài liệu khi chuỗi đã đọc
 *  được. Xem `so.ts` để biết vì sao phải có trạng thái dở dang. */
function OSo({ gt, dat, rong }: {
  gt: number; dat: (v: number) => void; rong?: number
}) {
  const [chu, setChu] = useState(String(gt ?? 0))
  const [dangGo, setDangGo] = useState(false)
  // Ngoài lúc đang gõ thì ô luôn bám theo tài liệu — đổi đích làm số reset thì ô phải
  // thấy ngay, không giữ con số cũ của trường trước.
  useEffect(() => { if (!dangGo) setChu(String(gt ?? 0)) }, [gt, dangGo])
  return (
    <input className="o o-so" style={{ width: rong ?? 74 }} value={chu}
           onFocus={() => setDangGo(true)}
           onChange={e => {
             const { chu: c, so } = locSo(e.target.value)
             setChu(c)
             if (so !== null) dat(so)
           }}
           onBlur={() => { setDangGo(false); dat(chotSo(chu)) }} />
  )
}

/* ------------------------------ một điều kiện --------------------------------- */

/** Hàng `[đại lượng] [phép] [vế phải]`.
 *
 *  DÙNG CHUNG cho cổng và cho ô `khi` của số hạng — cùng một hình dạng dữ liệu bên
 *  Python (`core._soat_dieu_kien` soát cả hai bằng một hàm), nên phải cùng một ô nhập.
 *  Hai bản sao sẽ lệch nhau, và cái lệch thì im lặng. */
function HangDK({ dk, boot, dat }: {
  dk: DK; boot: Bootstrap; dat: (d: DK) => void
}) {
  const ten = dk.trai?.ten ?? ''
  const loai = boot.toan_hang_loai[ten]
  const laDS = boot.toan_hang_dung_sai.includes(ten)
  const phai = dk.phai ?? {}
  /* Chế độ so SUY TỪ DỮ LIỆU, không phải một cờ riêng. Xem docstring đầu file. */
  const soVoiDaiLuong = !!phai.ten

  /* Phép so bày ra ĐÚNG những phép hợp lệ với kiểu đại lượng: đúng/sai chỉ nhận
     `là ĐÚNG`/`là SAI`, số thì chỉ nhận phép so sánh. Lọc ở đây thay vì bày cả bảng
     rồi để `validate_actions` mắng sau — mắng sau thì người dùng đã tin vào thứ mình
     vừa chọn rồi. */
  const phepChoPhep = Object.keys(boot.phep_so).filter(
    p => boot.phep_dung_sai.includes(p) === laDS)

  function doiToanHang(t: string) {
    const ds = boot.toan_hang_dung_sai.includes(t)
    const l = boot.toan_hang_loai[t]
    // Đổi loại đại lượng thì phép cũ có thể hết hợp lệ. Rơi về phép ĐẦU TIÊN hợp lệ
    // chứ không giữ nguyên: giữ nguyên là để lại một câu sai ngay sau một cú bấm.
    const p = boot.phep_dung_sai.includes(dk.phep) === ds
      ? dk.phep : (ds ? boot.phep_dung_sai[0] : '>=')
    if (ds) { dat({ trai: { ten: t }, phep: p }); return }
    const tinh = l === boot.loai_co_don_vi
      ? (boot.don_vi[phai.tinh] ? phai.tinh : 'tick')
      : (boot.loai_don_vi[l] ?? boot.toan_hang_don_vi[t] ?? '')
    dat({ trai: { ten: t }, phep: p, phai: { value: phai.value ?? 0, tinh } })
  }

  /* Ô đơn vị chỉ SÁNG với đại lượng `khoang_cach` — chỉ bề rộng mới quy đổi được.
     Mức giá thì cố định `giá tuyệt đối`, số đếm thì cố định đơn vị đếm của chính nó
     (`bid_kl` và `ton_kho` cùng đếm lot, nhưng một cái là của người khác). */
  const chonDuocDonVi = loai === boot.loai_co_don_vi

  return (
    <div className="hang">
      <select className="o o-dai" value={ten}
              onChange={e => doiToanHang(e.target.value)}>
        <option value="">— pick an operand —</option>
        {[...new Set(boot.toan_hang.map(t => t.nhom))].map(nhom => (
          <optgroup key={nhom} label={nhom}>
            {boot.toan_hang.filter(t => t.nhom === nhom).map(t => (
              <option key={t.key} value={t.key} title={t.mo_ta}>{t.nhan}</option>
            ))}
          </optgroup>
        ))}
      </select>

      <select className="o o-phep" value={dk.phep ?? ''}
              onChange={e => dat({ ...dk, phep: e.target.value })}>
        {phepChoPhep.map(p => <option key={p} value={p}>{boot.phep_so[p]}</option>)}
      </select>

      {/* Đại lượng đúng/sai KHÔNG có vế phải — không làm mờ, mà không vẽ ra. Một ô mờ
          vẫn là một lời mời; chỗ trống thì nói rõ "câu này đã đủ". */}
      {!laDS && (
        <>
          {soVoiDaiLuong ? (
            <select className="o o-dai" value={phai.ten ?? ''}
                    onChange={e => dat({ ...dk, phai: { ten: e.target.value } })}>
              {boot.toan_hang.filter(t => boot.toan_hang_loai[t.key] === loai)
                .map(t => <option key={t.key} value={t.key}>{t.nhan}</option>)}
            </select>
          ) : (
            <>
              <OSo gt={phai.value ?? 0}
                   dat={v => dat({ ...dk, phai: { ...phai, value: v } })} />
              <select className="o o-dv" disabled={!chonDuocDonVi}
                      value={phai.tinh ?? ''}
                      onChange={e => dat({ ...dk, phai: { ...phai, tinh: e.target.value } })}>
                {chonDuocDonVi
                  ? Object.entries(boot.don_vi).map(([k, v]) =>
                      <option key={k} value={k}>{v}</option>)
                  : <option value={phai.tinh ?? ''}>
                      {boot.nhan_don_vi[phai.tinh] ?? '—'}
                    </option>}
              </select>
            </>
          )}
          {/* Đổi qua lại số ⇄ đại lượng. Nút chứ không phải hai radio: nó chỉ có hai
              trạng thái và trạng thái hiện tại đã nhìn thấy ngay bên trái. */}
          <button className="nut nho" title="Compare against a NUMBER, or against another OPERAND"
                  onClick={() => dat(soVoiDaiLuong
                    ? { ...dk, phai: { value: 0, tinh: loai === boot.loai_co_don_vi
                        ? 'tick' : (boot.loai_don_vi[loai] ?? '') } }
                    : { ...dk, phai: { ten: boot.toan_hang
                        .find(t => boot.toan_hang_loai[t.key] === loai)?.key ?? '' } })}>
            {soVoiDaiLuong ? '↔ number' : '↔ operand'}
          </button>
        </>
      )}
    </div>
  )
}

/* --------------------------------- hộp thoại ---------------------------------- */

export default function ActionDialog({ action, boot, tab, onLuu, onDong }: {
  action: HD
  boot: Bootstrap
  tab: Tab
  onLuu: (a: HD) => void
  onDong: () => void
}) {
  const loaiChoPhep = boot.action_types.filter(t => boot.action_tabs[t]?.includes(tab))
  const [a, setA] = useState<HD>(() => JSON.parse(JSON.stringify(action)))
  const [xem, setXem] = useState('')
  const [loi, setLoi] = useState<string[]>([])

  const dat = (k: string, v: unknown) => setA(x => ({ ...x, [k]: v }))

  /* Xem trước + soát lỗi do PYTHON trả về, hoãn 200ms để gõ không bắn liên tục qua
     cầu nối. */
  useEffect(() => {
    const h = setTimeout(async () => {
      const r = await py.save_action(a, tab)
      if (r.ok) {
        setXem(r.value?.display ?? '')
        setLoi(((r as any).loi as string[]) ?? [])
      } else {
        setXem(''); setLoi([r.error ?? 'could not read the action'])
      }
    }, 200)
    return () => clearTimeout(h)
  }, [a, tab])

  async function doiLoai(t: string) {
    // Lấy mặc định từ Python chứ không tự nặn ở JS: giá trị khởi điểm của một hành
    // động là kiến thức của lõi, không phải của hộp thoại.
    const r = await py.action_defaults(t)
    setA(r.ok && r.value ? { ...r.value, name: a.name } : { type: t, name: a.name })
  }

  /* ---- số hạng: đích quyết KIỂU, kiểu quyết phép và quyết `lượng` nhận gì ---- */
  const kieu = boot.dich_kieu[a.dich]
  const luong = a.luong ?? {}
  const loaiTH = luong.toan_hang ? boot.toan_hang_loai[luong.toan_hang] : null
  /* Đại lượng giá TỰ MANG đơn vị (`spread` là spread, hết) — cho chọn thêm một thước
     nữa là mời viết `spread × 2 tick`, một câu không quy được về đâu. */
  const tuMangDonVi = loaiTH === 'muc_gia' || loaiTH === 'khoang_cach'
  const chonDuocDonVi = kieu !== 'lot' && !tuMangDonVi

  function datLuong(v: Record<string, unknown>) {
    dat('luong', { ...luong, ...v })
  }

  function doiDich(d: string) {
    const k = boot.dich_kieu[d]
    const cho = boot.phep_cho_dich[k] ?? []
    // Phép cũ có thể hết hợp lệ (`lot ×= 2` đúng, `biên ×= 2` thì không) — rơi về phép
    // đầu tiên hợp lệ thay vì để lại một câu sai ngay sau cú bấm.
    setA(x => ({ ...x, dich: d,
                 phep: cho.includes(x.phep) ? x.phep : cho[0],
                 luong: k === 'lot' ? { ...luong, don_vi: 'lot' } : luong }))
  }

  function doiToanHangLuong(t: string) {
    if (!t) { datLuong({ toan_hang: undefined }); return }
    const l = boot.toan_hang_loai[t]
    // Đại lượng giá không cần thước; đại lượng đếm thì cần. Dọn ô đơn vị theo, đừng
    // để lại một thước cũ vô nghĩa nằm im.
    datLuong({ toan_hang: t,
               don_vi: l === 'muc_gia' || l === 'khoang_cach' ? undefined
                 : (kieu === 'lot' ? 'lot' : (luong.don_vi ?? 'tick')) })
  }

  return (
    <Modal title={`Action — ${boot.action_labels[a.type] ?? a.type}`} width={700}
           onClose={onDong}
           footer={
             <>
               <div className="xem-truoc" title="Exactly how the core reads this action">
                 {xem || '…'}
               </div>
               <button className="nut" onClick={onDong}>Cancel</button>
               <button className="nut chinh" onClick={() => onLuu(a)}>Save</button>
             </>
           }>

      <div className="hang">
        <span className="nhan-o">Type</span>
        <select className="o" value={a.type} onChange={e => doiLoai(e.target.value)}>
          {loaiChoPhep.map(t =>
            <option key={t} value={t}>{boot.action_labels[t]}</option>)}
        </select>
        <span className="nhan-o phu">Name</span>
        <input className="o" value={a.name ?? ''} placeholder="(blank = name it automatically)"
               onChange={e => dat('name', e.target.value)} />
      </div>

      {/* ---------------------------- CỔNG ---------------------------- */}
      {a.type === 'check_cond' && (
        <>
          {((a.conditions ?? []) as DK[]).map((c, i) => (
            <div key={i} className="hang-boc">
              <span className="nhan-o">{i === 0 ? 'When' : 'AND'}</span>
              <HangDK dk={c} boot={boot} dat={d => {
                const ds = [...(a.conditions ?? [])]; ds[i] = d; dat('conditions', ds)
              }} />
              <button className="nut nho" title="Remove this condition"
                      onClick={() => dat('conditions',
                        (a.conditions as DK[]).filter((_, k) => k !== i))}>
                <Icon name="trash" />
              </button>
            </div>
          ))}
          <div className="hang">
            <button className="nut" onClick={() => dat('conditions',
              [...(a.conditions ?? []), { trai: { ten: '' }, phep: '>=',
                                          phai: { value: 0, tinh: 'tick' } }])}>
              <Icon name="plus" /> Add condition
            </button>
            <span className="chu-mo">
              Conditions join with AND — the gate opens only if ALL of them match.
            </span>
          </div>
        </>
      )}

      {/* --------------------------- SỐ HẠNG --------------------------- */}
      {a.type === 'so_hang' && (
        <>
          <div className="hang">
            <span className="nhan-o">Set</span>
            <select className="o o-dai" value={a.dich ?? ''}
                    onChange={e => doiDich(e.target.value)}>
              {Object.entries(boot.dich).map(([k, v]) =>
                <option key={k} value={k}>{v}</option>)}
            </select>

            <select className="o o-phep" value={a.phep ?? ''}
                    onChange={e => dat('phep', e.target.value)}>
              {(boot.phep_cho_dich[kieu] ?? []).map(p =>
                <option key={p} value={p}>{boot.phep_gan[p]}</option>)}
            </select>

            <OSo gt={luong.he_so ?? 0} dat={v => datLuong({ he_so: v })} />

            <span className="chu-mo">×</span>
            <select className="o o-dai" value={luong.toan_hang ?? ''}
                    onChange={e => doiToanHangLuong(e.target.value)}>
              <option value="">(no operand)</option>
              {[...new Set(boot.toan_hang.map(t => t.nhom))].map(nhom => (
                <optgroup key={nhom} label={nhom}>
                  {boot.toan_hang
                    .filter(t => t.nhom === nhom
                      && !boot.toan_hang_dung_sai.includes(t.key))
                    .map(t => <option key={t.key} value={t.key} title={t.mo_ta}>
                      {t.nhan}
                    </option>)}
                </optgroup>
              ))}
            </select>

            <select className="o o-dv" disabled={!chonDuocDonVi}
                    value={luong.don_vi ?? ''}
                    onChange={e => datLuong({ don_vi: e.target.value })}>
              {chonDuocDonVi
                ? Object.entries(boot.don_vi).map(([k, v]) =>
                    <option key={k} value={k}>{v}</option>)
                : <option value={luong.don_vi ?? ''}>
                    {tuMangDonVi ? '(from the operand)'
                      : (boot.nhan_don_vi[luong.don_vi] ?? '—')}
                  </option>}
            </select>
          </div>

          {/* Ô `khi` — điều kiện gắn lên CHÍNH khối số hạng, không phải một cổng riêng.
              Hai hạn mức tồn kho làm bằng cổng là bốn nhánh; làm bằng `khi` là hai
              dòng, và chuỗi vẫn thẳng. */}
          <div className="hang-boc">
            <label className="tick">
              <input type="checkbox" checked={!!a.khi}
                     onChange={e => setA(x => {
                       if (!e.target.checked) { const { khi, ...con } = x; return con }
                       return { ...x, khi: { trai: { ten: '' }, phep: '>=',
                                             phai: { value: 0, tinh: 'tick' } } }
                     })} />
              Only apply when…
            </label>
            {a.khi && <HangDK dk={a.khi} boot={boot} dat={d => dat('khi', d)} />}
          </div>

          <div className="chu-dan">
            Order along the chain IS meaning: terms accumulate in numbering order, so
            an <b>=</b> placed after a <b>+=</b> on the same target wipes out whatever
            was just added.
          </div>
        </>
      )}

      {loi.length > 0 && (
        <div className="chu-dan canh">
          {loi.map((m, i) => <div key={i}>✖ {m}</div>)}
        </div>
      )}
    </Modal>
  )
}
