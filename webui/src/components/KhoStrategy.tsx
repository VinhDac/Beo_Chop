import { useEffect, useState, type ReactNode } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { xacNhan, nhapChu } from './Hoi'

/** MỘT DÒNG trong kho.
 *
 *  Mang `tuLuu` để hộp bày nó ở tab riêng: bản tự lưu lẫn vào bản gốc là **mở nhầm,
 *  lưu nhầm** — hai thứ cùng tên, khác ruột.
 */
export interface MucKho {
  ten: string
  tuLuu?: boolean
}

/** Khoá một dòng = tab GHÉP VỚI tên.
 *
 *  Bên Jenifer có một lỗi sống đáng chép lại: họ từng lấy riêng *chế độ* làm khoá, mà
 *  mọi Process cùng chế độ thì mang chung một giá trị — nên ba dòng dùng chung một
 *  khoá, bấm một dòng là cả ba cùng sáng, và nút Xoá ăn vào dòng ĐẦU nhóm chứ không
 *  phải dòng vừa bấm. Tức là **xoá nhầm file**. Ở đây tên đã là duy nhất trong mỗi
 *  tab, nhưng vẫn ghép tab vào cho khoá không bao giờ đụng nhau.
 */
const khoa = (m: MucKho) => (m.tuLuu ? 'tl/' : 'g/') + m.ten

/** KHO STRATEGY — chọn, đổi tên, nhân bản, xoá.
 *
 *  Thay cho việc gõ tay tên file: gõ tay là cách chắc chắn gõ sai. Mở bằng bấm đúp
 *  hoặc chọn rồi bấm Mở.
 */
export default function KhoStrategy({ dangMo, lay, onMo, onDong, onDoiTen, onNhanBan,
                                      onXoa }: {
  /** Tên Strategy đang mở — đánh dấu trong danh sách để khỏi mở lại chính nó. */
  dangMo?: string
  lay: () => Promise<MucKho[]>
  onMo: (ten: string) => void
  onDong: () => void
  onDoiTen: (cu: string, moi: string) => Promise<void>
  onNhanBan: (ten: string, tenMoi: string) => Promise<void>
  onXoa: (ten: string) => Promise<void>
}) {
  const [ds, setDs] = useState<MucKho[]>([])
  const [chon, setChon] = useState<string | null>(null)
  const [dangTai, setDangTai] = useState(true)
  const [xemTuLuu, setXemTuLuu] = useState(false)
  const [tim, setTim] = useState('')

  const nap = () => {
    setDangTai(true)
    lay().then(d => { setDs(d); setDangTai(false) })
  }
  useEffect(nap, [])

  const q = tim.trim().toLowerCase()
  const bay = ds.filter(m => !!m.tuLuu === xemTuLuu
                             && (!q || m.ten.toLowerCase().includes(q)))
  const muc = bay.find(m => khoa(m) === chon) ?? null

  async function xoa() {
    if (!muc) return
    if (!(await xacNhan({
      tieu_de: 'Xoá Strategy',
      loi: `Xoá "${muc.ten}"?`,
      chi_tiet: 'File bị xoá hẳn khỏi đĩa, không hoàn tác được.',
      nut_ok: 'Xoá', nguy: true,
    }))) return
    await onXoa(muc.ten)
    setChon(null)
    nap()
  }

  async function doiTen() {
    if (!muc) return
    const v = await nhapChu({ tieu_de: 'Đổi tên Strategy', loi: 'Tên mới:',
                              nhap: muc.ten, nut_ok: 'Đổi tên' })
    if (!v || v.trim() === muc.ten) return
    await onDoiTen(muc.ten, v.trim())
    setChon(null)
    nap()
  }

  async function nhanBan() {
    if (!muc) return
    const v = await nhapChu({ tieu_de: 'Nhân bản Strategy', loi: 'Tên bản sao:',
                              nhap: `${muc.ten} (bản sao)`, nut_ok: 'Nhân bản' })
    if (!v?.trim()) return
    await onNhanBan(muc.ten, v.trim())
    setChon(null)
    nap()
  }

  const trong: ReactNode = xemTuLuu
    ? <>Chưa có bản tự lưu nào. Bản tự lưu là phần đang làm dở của một Strategy đã lưu —
       mở nó ra là mở lại bản gốc kèm phần dở, Ctrl+S ghi về bản gốc.</>
    : <>Chưa có Strategy nào. Vẽ một sơ đồ rồi bấm <b>Lưu</b> là nó xuất hiện ở đây.</>

  return (
    <Modal title="Kho Strategy" width={520} onClose={onDong}
           footer={<>
             <button className="nut" disabled={!muc} onClick={doiTen}>
               <Icon name="edit" /> Đổi tên</button>
             <button className="nut" disabled={!muc} onClick={nhanBan}>
               <Icon name="copy" /> Nhân bản</button>
             <button className="nut do" disabled={!muc} onClick={xoa}>
               <Icon name="trash" /> Xoá</button>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" disabled={!muc}
                     onClick={() => muc && onMo(muc.ten)}>Mở</button>
           </>}>
      {/* HAI TAB. Bản gốc và bản tự lưu lẫn vào nhau là mở nhầm, lưu nhầm. */}
      <div className="hang-tab">
        <button className={'tab' + (!xemTuLuu ? ' dang' : '')}
                onClick={() => { setXemTuLuu(false); setChon(null) }}>Strategy</button>
        <button className={'tab' + (xemTuLuu ? ' dang' : '')}
                onClick={() => { setXemTuLuu(true); setChon(null) }}>Tự lưu</button>
        <span className="day" />
        <input className="o" style={{ width: 150 }} value={tim} spellCheck={false}
               placeholder="lọc theo tên…" onChange={e => setTim(e.target.value)} />
      </div>
      <div className="danh-sach">
        {dangTai && <div className="muc mo">đang đọc…</div>}
        {!dangTai && bay.length === 0 && <div className="muc mo">{trong}</div>}
        {bay.map(m => (
          <div key={khoa(m)} className={'muc' + (khoa(m) === chon ? ' chon' : '')}
               onClick={() => setChon(khoa(m))}
               onDoubleClick={() => onMo(m.ten)}>
            <span className="ten">{m.ten}</span>
            {m.ten === dangMo && <b className="the">đang mở</b>}
          </div>
        ))}
      </div>
    </Modal>
  )
}
