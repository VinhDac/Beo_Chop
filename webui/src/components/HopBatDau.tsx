import { useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import { KhaiLean } from './ORuot'
import { py } from '../api'
import RuotBatDau, { locOAnHien } from './RuotBatDau'
import { useEffect } from 'react'
import type { Step, TuDienBatDau } from '../types'

/** HỘP KHỐI BẮT ĐẦU — sơ đồ này chạy trên cái gì, bao giờ, bằng bao nhiêu tiền.
 *
 *  ⚠ CHỈ CÓ NGẦN ẤY, và đó là một quyết định chứ không phải tình cờ. Hộp này từng
 *  mang hơn hai mươi ô chia bảy nhóm — dây chuyền LEAN, phí sàn, ô nhớ, mốc so
 *  sánh — vì mỗi lần cần thêm một khả năng thì gắn thêm một ô vào đây là tiện nhất.
 *  Chủ dự án chốt ngày 18/10/2026: *"ta đang lạm dụng khối Bắt đầu để gài logic vào
 *  chứ không thực sự tạo ra khối mới để vẽ… nên hạn chế nhất khả năng trong 1 khối,
 *  giữ sự đơn giản sạch, từ đó mới build những thứ to lớn được."*
 *      Mười một ô kia nay ở hộp «Cỗ máy LEAN» (`HopCoMay`), và chúng không còn nằm
 *  trong khối Bắt đầu nữa — cả trên giao diện lẫn trong file lưu.
 *
 *  Ruột vẽ ô dùng chung với hộp Cỗ máy: xem `RuotBatDau`.
 */
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

  /* MẤY CÂU LEAN KHỐI NÀY KHAI RA — HỎI PYTHON, KHÔNG TỰ GHÉP.
   *
   * Dòng khai tồn tại ĐÚNG ĐỂ người dùng đối chiếu với mã sinh ra, nên nó nói sai
   * thì tệ hơn là không có. `tests/test_moi_noi.py` canh cả họ: không file .tsx nào
   * được gõ cứng một mẩu LEAN. */
  const [khai, setKhai] = useState<string[]>([])
  useEffect(() => {
    let con = true
    void py.khai_bat_dau(gt).then(r => { if (con && r.ok) setKhai(r.value ?? []) })
    return () => { con = false }
  }, [gt])

  function luu() {
    const ra = locOAnHien(gt, tuDien)
    onLuu({ ...(ra as unknown as Step), id: step.id, kind: step.kind,
            name: ten.trim() || 'Bắt đầu' })
  }

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

        <RuotBatDau dsO={tuDien.o} nhom={tuDien.nhom} gt={gt} setGt={setGt}
                    tuDien={tuDien} />

        <KhaiLean ham={khai} />
      </div>
    </Modal>
  )
}
