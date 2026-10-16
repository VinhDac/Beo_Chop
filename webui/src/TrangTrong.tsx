import { useState } from 'react'
import { py, pyQC } from './api'
import KhoDialog from './components/KhoDialog'
import TitleBar, { type NhomMenu } from './components/TitleBar'
import HopKhoa from './qc/HopKhoa'
import type { KhoaQC } from './types'
import { useKhungCuaSo } from './useKhungCuaSo'

/** TRANG TẠM — khối và cách tương tác đang được thiết kế lại.  (D-12)
 *
 *  Cố ý KHÔNG để lại một trình vẽ nửa vời: khối cũ đã xoá hết, nên thứ trung thực nhất
 *  app có thể làm lúc này là nói ra điều đó. Hai việc vẫn làm được vì chúng không dính
 *  gì tới khối — đặt khoá QuantConnect, và xem app lưu file ở đâu — nên giữ lại.
 */
export default function TrangTrong() {
  useKhungCuaSo(32)
  const [moKho, setMoKho] = useState(false)
  /** Khoá QC: `null` = hộp đang đóng. Hộp chỉ mở SAU khi Python trả trạng thái thật —
   *  nó hiện cả đường dẫn file khoá, nên mở trước là hiện một dấu ngoặc rỗng. */
  const [khoa, setKhoa] = useState<KhoaQC | null>(null)

  const moKhoa = async () => {
    const r = await pyQC.qc_khoa()
    setKhoa(r.ok && r.value ? r.value
                            : { co: false, nguon: null, user_id: null, duong: '',
                                loi: r.error })
  }

  const menus: NhomMenu[] = [
    { ten: 'Cat Studio', muc: [
      { ten: 'Khoá QuantConnect…', icon: 'gear', onClick: () => { void moKhoa() } },
      { ten: 'Kho — app lưu file ở đâu…', icon: 'folder', onClick: () => setMoKho(true) },
      { ngan: true },
      { ten: 'Thoát', onClick: () => { void py.cua_so_dong() } },
    ] },
  ]

  return (
    <div className="khung">
      <TitleBar tieuDe="Cat Studio" menus={menus} />
      <div className="vung-canvas">
        <div className="trong-rong">
          <div className="to">Đang dựng lại từ đầu</div>
          <div>
            Bộ khối cũ và cách tương tác cũ đã được gỡ bỏ. Từ nay mọi phép tính giao dịch
            là của <b>QuantConnect</b>; app chỉ vẽ, soát và dịch sơ đồ thành thuật toán.
            <br />Bộ khối mới và cách tương tác mới đang được thiết kế.
          </div>
        </div>
      </div>
      <div className="thanh-trang-thai">
        <span>chưa có bộ khối nào</span>
        <span className="day" />
        <span>D-11 · D-12</span>
      </div>

      {moKho && <KhoDialog onDong={() => setMoKho(false)} />}
      {khoa && <HopKhoa khoa={khoa} dong={() => setKhoa(null)} doi={setKhoa} />}
    </div>
  )
}
