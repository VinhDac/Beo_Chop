import { useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import HopHanhDong from './HopHanhDong'
import type { Step, TuDienHoi, TuDienLam } from '../types'

/** HỘP SỬA KHỐI NHÓM — chuỗi hành động bên trong một hộp.
 *
 *  Trước nay bấm đúp một khối Nhóm KHÔNG ra gì: hộp thoại chỉ có cho khối Hỏi, khối
 *  Làm và khối Bắt đầu. Lòi ra lúc dựng lại một chiến thuật thật (vd2) — cả tám nhánh
 *  của nó đều kết thúc bằng một Nhóm ba hành động, mà không có cách nào mở ra sửa.
 *
 *  HỘP NÀY KHÔNG TỰ TẢ HÀNH ĐỘNG. Mỗi dòng chỉ hiện NHÃN LOẠI (lấy từ từ điển Python)
 *  và cái mã — còn câu mô tả đầy đủ thì để nguyên trên thẻ khối ngoài canvas, nơi
 *  Python dựng nó. Giao diện ghép chữ lấy là sớm muộn nó tả khác thứ lõi thật sự hiểu.
 */
export default function HopNhom({ step, tuDienLam, tuDienHoi, dsMa, coMaDangXet,
                                 onLuu, onDong }: {
  step: Step
  tuDienLam: TuDienLam
  tuDienHoi: TuDienHoi
  dsMa: string[]
  coMaDangXet: boolean
  onLuu: (s: Step) => void
  onDong: () => void
}) {
  const [ten, setTen] = useState(step.name ?? '')
  const [ds, setDs] = useState<Record<string, unknown>[]>(
    () => [...((step.actions as Record<string, unknown>[]) ?? [])])
  /** Hành động đang mở hộp con; null = không mở cái nào. */
  const [sua, setSua] = useState<number | null>(null)
  const [themLoai, setThemLoai] = useState(tuDienLam.loai[0]?.ma ?? '')

  const loaiCua = (a: Record<string, unknown>) =>
    tuDienLam.loai.find(l => l.ma === a.type)

  function doi(i: number, a: Record<string, unknown>) {
    setDs(x => x.map((c, j) => (j === i ? a : c)))
  }

  function doiCho(i: number, buoc: number) {
    const j = i + buoc
    if (j < 0 || j >= ds.length) return
    setDs(x => {
      const r = [...x]
      ;[r[i], r[j]] = [r[j], r[i]]
      return r
    })
  }

  /** Một hành động mới, dựng từ MẶC ĐỊNH của từ điển — y như khối Làm lẻ. */
  function them() {
    const l = tuDienLam.loai.find(x => x.ma === themLoai)
    if (!l) return
    const a: Record<string, unknown> = { kind: 'action', type: l.ma, name: l.nhan }
    for (const o of l.o) a[o.ten] = o.mac_dinh
    const oChon = l.o.find(o => o.kieu === 'chon')
    if (oChon) {
      for (const o of l.theo_loai[String(oChon.mac_dinh)]?.o ?? []) {
        a[o.ten] = o.mac_dinh
      }
    }
    if (l.co_dai_luong) a.gia_tri = {}
    setDs(x => [...x, a])
    setSua(ds.length)
  }

  return (
    <>
      <Modal title="Nhóm" width={620} onClose={onDong}
             footer={<>
               <span className="day" />
               <button className="nut" onClick={onDong}>Huỷ</button>
               <button className="nut chinh"
                       onClick={() => onLuu({ ...step, name: ten.trim() || 'Nhóm mới',
                                              actions: ds })}>Lưu</button>
             </>}>
        <div className="hop-lam">
          <div className="mo-ta-loai">
            <Icon name="group" /> một chuỗi hành động chạy thẳng một lượt, không rẽ nhánh
          </div>

          <label className="o-hang">
            <span className="nhan-o">Tên khối</span>
            <input className="o day" value={ten} spellCheck={false}
                   placeholder="Nhóm mới" onChange={e => setTen(e.target.value)} />
          </label>

          <div className="ds-hd">
            {ds.map((a, i) => {
              const l = loaiCua(a)
              const ma = String(a.ma ?? '').trim()
              return (
                <div className="dong-hd" key={i}>
                  <span className="stt">{i + 1}</span>
                  <Icon name={l?.icon ?? 'action'} />
                  <b>{l?.nhan ?? String(a.type ?? '?')}</b>
                  {ma && <span className="ma-hd">{ma}</span>}
                  <span className="day" />
                  <button className="nut-nho" title="Lên"
                          onClick={() => doiCho(i, -1)} disabled={i === 0}>↑</button>
                  <button className="nut-nho" title="Xuống"
                          onClick={() => doiCho(i, 1)}
                          disabled={i === ds.length - 1}>↓</button>
                  <button className="nut-nho" onClick={() => setSua(i)}>Sửa</button>
                  <button className="nut-nho bo" title="Bỏ hành động này"
                          onClick={() => setDs(x => x.filter((_c, j) => j !== i))}>
                    ✕
                  </button>
                </div>
              )
            })}
            {!ds.length && <div className="dong-hd mo">chưa có hành động nào</div>}
          </div>

          <div className="o-hang">
            <span className="nhan-o">Thêm hành động</span>
            <select className="o day" value={themLoai}
                    onChange={e => setThemLoai(e.target.value)}>
              {tuDienLam.loai.map(l => (
                <option key={l.ma} value={l.ma}>{l.nhan}</option>
              ))}
            </select>
            <button className="nut" onClick={them}><Icon name="plus" /> Thêm</button>
          </div>
        </div>
      </Modal>

      {/* Sửa một hành động thì mở ĐÚNG hộp của khối Làm lẻ — một hành động trong Nhóm
          với một khối Làm đứng riêng là cùng một thứ, nên không dựng hộp thứ hai. */}
      {sua !== null && ds[sua] && (
        <HopHanhDong step={ds[sua] as unknown as Step} tuDien={tuDienLam}
                     tuDienHoi={tuDienHoi} dsMa={dsMa} coMaDangXet={coMaDangXet}
                     onDong={() => setSua(null)}
                     onLuu={s => {
                       doi(sua, s as unknown as Record<string, unknown>)
                       setSua(null)
                     }} />
      )}
    </>
  )
}
