import { useEffect, useState } from 'react'
import { RuotKetQua } from './components/HopKetQua'
import TitleBar from './components/TitleBar'
import Icon from './components/Icon'
import { cho_cau_noi, py } from './api'
import type { KetQuaChay } from './types'

/** TRANG KẾT QUẢ ĐỨNG MỘT MÌNH — ruột của một CỬA SỔ RIÊNG.
 *
 *  VÌ SAO CÓ TRANG NÀY. Người ta mở app lên để so HAI PHIÊN BẢN của cùng một chiến
 *  thuật: đổi chu kỳ từ 60 sang 90 rồi xem lãi đi lên hay xuống. So thì phải nhìn
 *  CÙNG LÚC, mà một hộp thoại thì mỗi lần một cái và nó còn che mất sơ đồ. Cửa sổ
 *  thật thì kéo sang màn hình khác được, Aero Snap được, xếp bốn cái cạnh nhau được.
 *
 *  CÙNG MỘT BUNDLE với cửa sổ chính, chỉ khác vai: `main.tsx` thấy `?kq=` thì dựng
 *  trang này thay cho sơ đồ. Dựng một trang HTML thứ hai thì sớm muộn nó lệch khỏi
 *  trang thứ nhất — và cái lệch ấy chỉ lộ ra ở màn ít người mở nhất.
 *
 *  Cửa sổ `frameless` như cửa sổ chính (Windows 10 không cho đổi màu thanh tiêu đề
 *  gốc), nên trang này phải tự vẽ thanh tiêu đề — dùng lại đúng `TitleBar`.
 */
export default function TrangKetQua({ ma }: { ma: string }) {
  const [kq, setKq] = useState<KetQuaChay | null>(null)
  const [loi, setLoi] = useState('')

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        setLoi('Không kết nối được tới Python.')
        return
      }
      const r = await py.doc_luot_chay(ma)
      if (r.ok && r.value) {
        // ⚠ KHÔNG gọi `set_title` ở đây. Python đã đặt tiêu đề lúc dựng cửa sổ, và
        // `_va_khung` TÌM CỬA SỔ THEO TIÊU ĐỀ trong bốn giây — đổi tiêu đề ngay lúc
        // nó đang tìm là nó tìm hụt, và cửa sổ mở ra không khung mà cũng không kéo
        // được. Trông y như lỗi của `khung_cua_so`.
        setKq(r.value)
      } else {
        setLoi(r.error ?? 'không đọc được lượt chạy này')
      }
    })()
  }, [ma])

  return (
    <div className="app cua-so-kq">
      <TitleBar tieuDe={kq ? `Kết quả — ${kq.ten_lop ?? ''}` : 'Kết quả'} menus={[]} />
      {loi && <div className="mc-bao loi kq-loi">⚠ {loi}</div>}
      {!kq && !loi && (
        <div className="kq-cho"><Icon name="chay" /> đang mở lượt chạy…</div>
      )}
      {kq && <RuotKetQua kq={kq} />}
    </div>
  )
}
