import { useEffect, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { Ve } from './HopDieuKien'
import { Hang, KhaiLean } from './ORuot'
import type { LoaiLam, OLam, Step, TuDienHoi, TuDienLam, VeDieuKien } from '../types'

/** HỘP THOẠI KHỐI HÀNH ĐỘNG — nơi người chơi khai một việc sẽ làm với thị trường.
 *
 *  KHÁC HỘP XÁC NHẬN Ở HÌNH DẠNG: khối Hỏi là N dòng điều kiện giống nhau, còn khối
 *  Làm là một bộ Ô CỐ ĐỊNH do loại của nó quyết định — vì mỗi hàm LEAN nhận tham số
 *  khác nhau. Nên hộp này không dựng dòng, nó dựng ô theo đúng danh sách Python gửi
 *  sang (`LoaiLam.o` + `LoaiLam.theo_loai`).
 *
 *  HỘP NÓI THẲNG RA HÀM LEAN NÓ SẼ GỌI. Đó không phải để trang trí: cả bộ khối này
 *  dựng trên một lời hứa — mỗi khối chỉ ra được MỘT thứ có thật của LEAN, app không
 *  tự đẻ thêm backend nào (D-11). Bày cái hàm ra là cách người chơi kiểm được lời hứa
 *  ấy, chứ không phải tin suông.
 */

export default function HopHanhDong({ step, tuDien, tuDienHoi, onLuu, onDong }: {
  step: Step
  tuDien: TuDienLam
  /** Cần cả từ điển Hỏi: ô «giá trị vẽ» dùng lại ĐÚNG kho đại lượng của khối Hỏi. */
  tuDienHoi: TuDienHoi
  onLuu: (s: Step) => void
  onDong: () => void
}) {
  const loai = tuDien.loai.find(l => l.ma === step.type)
  const [ten, setTen] = useState(step.name ?? '')
  // Giữ CẢ khối, không chỉ mấy ô: như vậy `pos`, `mau`, `hat_nhan`… đi theo nguyên vẹn
  // mà hộp thoại không cần biết chúng tồn tại.
  const [gt, setGt] = useState<Record<string, unknown>>(() => ({ ...step }))
  const doi = (k: string, v: unknown) => setGt(x => ({ ...x, [k]: v }))

  const loaiDL = loai?.dai_luong_tu
    ? tuDienHoi.loai.find(l => l.ma === loai.dai_luong_tu)
    : undefined

  useEffect(() => {
    setGt(x => {
      const ra = { ...x }
      // Ô nào khối chưa có thì điền mặc định của từ điển — đúng thứ `core.o_lam` làm
      // bên Python. File cũ (lưu trước khi thêm một ô) mở ra sẽ bày số 0 trong khi
      // Python đọc ra 0.05, mà hai bên đều "đúng" theo luật của mình.
      const l = tuDien.loai.find(y => y.ma === step.type)
      const oChon = l?.o.find(o => o.kieu === 'chon')
      const them = oChon ? l?.theo_loai[String(ra[oChon.ten] ?? oChon.mac_dinh)]?.o : []
      for (const o of [...(l?.o ?? []), ...(them ?? [])]) {
        if (!(o.ten in ra)) ra[o.ten] = o.mac_dinh
      }
      // Khối cần một đại lượng mà chưa có thì cho sẵn cái đầu bảng: hộp mở ra với một
      // ô trống trơn thì lưu xuống là lỗi ngay, mà người chơi chẳng biết mình bỏ sót gì.
      if (loaiDL && !(ra.gia_tri as VeDieuKien | undefined)?.ma_dl) {
        const d = loaiDL.nhom[0].dai_luong[0]
        const ts: Record<string, number> = {}
        for (const t of d.tham_so) ts[t.ten] = t.mac_dinh
        ra.gia_tri = {
          ma_dl: d.ma,
          ...(d.tham_so.length ? { tham_so: ts } : {}),
          ...(d.duong ? { duong: d.duong[0][0] } : {}),
        }
      }
      return ra
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!loai) return null

  /** Ô CHỌN đầu tiên là cái cầm lái: nó quyết những ô còn lại hiện ra cái gì, và quyết
   *  luôn hàm LEAN. (Bản thân danh sách ô vẫn của Python — đây chỉ chọn nhánh nào.) */
  const oLai = loai.o.find(o => o.kieu === 'chon')
  const nhanh = oLai ? loai.theo_loai[String(gt[oLai.ten] ?? '')] : undefined
  const dsO: OLam[] = [...loai.o, ...(nhanh?.o ?? [])]
  const hamLean = nhanh?.lean ?? loai.lean

  /** Đổi ô cầm lái thì ĐIỀN LUÔN mặc định cho nhánh mới.
   *
   *  Không điền thì ô mới bày số 0, trong khi Python rơi về mặc định của từ điển
   *  (`core.o_lam`) — hộp thoại nói "trượt 0", thẻ khối nói "trượt 5%". Hỏng LẶNG, và
   *  đúng kiểu hỏng khó chịu nhất: hai nơi cùng đúng theo luật của riêng mình. */
  function doiLai(v: string) {
    setGt(x => {
      const ra = { ...x, [oLai!.ten]: v }
      for (const o of loai!.theo_loai[v]?.o ?? []) {
        if (!(o.ten in ra)) ra[o.ten] = o.mac_dinh
      }
      return ra
    })
  }

  /** Lưu, có BỎ ô của những nhánh không chọn.
   *
   *  Để chúng lại thì file mang theo "giá kích hoạt" của một lệnh Giới hạn — hôm nay
   *  vô hại (Python chỉ đọc ô của nhánh đang chọn), nhưng là đúng thứ làm người đọc
   *  file sau này tưởng khối đang làm chuyện khác. */
  function luu() {
    const dangHien = new Set(dsO.map(o => o.ten))
    const cuaNhanh = new Set(
      Object.values(loai!.theo_loai).flatMap(n => n.o.map(o => o.ten)))
    const ra: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(gt)) {
      if (!cuaNhanh.has(k) || dangHien.has(k)) ra[k] = v
    }
    onLuu({ ...(ra as unknown as Step), id: step.id, kind: step.kind,
            type: step.type, name: ten.trim() || loai!.nhan })
  }

  return (
    <Modal title={loai.nhan} width={620} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" onClick={luu}>Lưu</button>
           </>}>
      <div className="hop-lam">
        <div className="mo-ta-loai">
          <Icon name={loai.icon} /> {loai.mo_ta}
        </div>
        {loai.tat && <div className="mc-bao loi">⚠ {loai.tat}</div>}

        <label className="o-hang">
          <span className="nhan-o">Tên khối</span>
          <input className="o day" value={ten} spellCheck={false}
                 placeholder={loai.nhan} onChange={e => setTen(e.target.value)} />
        </label>

        {dsO.map(o => (
          <Hang key={o.ten} o={o} gt={gt[o.ten]}
                onDoi={v => (o === oLai ? doiLai(String(v)) : doi(o.ten, v))} />
        ))}

        {loaiDL && (
          <label className="o-hang">
            <span className="nhan-o">Giá trị vẽ</span>
            <Ve ve={(gt.gia_tri as VeDieuKien) ?? {}} loai={loaiDL} td={tuDienHoi}
                choSo={false} choMa={loai.can_ma}
                onDoi={v => doi('gia_tri', v)} />
          </label>
        )}

        <KhaiLean ham={hamLean} />
      </div>
    </Modal>
  )
}

/** Có phải một loại hành động không — để chỗ khác biết nên mở hộp nào. */
export function laHanhDong(td: TuDienLam | null, t?: string) {
  return !!t && !!td?.loai.some((l: LoaiLam) => l.ma === t)
}
