import { memo, useEffect, useMemo, useRef, useState } from 'react'
import ContextMenu from '../components/ContextMenu'

export interface DongNk {
  i: number; co_viec: boolean; lenh_id: string | null; chu: string
}

/** Một DÃY dòng giống hệt nhau nằm liền nhau, gộp thành một. */
interface Nhom {
  i: number                 // lượt ĐẦU của dãy — chỗ «Xem trên sơ đồ» sẽ soi
  co_viec: boolean
  chu: string
  dem: number
}

/** NHẬT KÝ "VÌ SAO" — mỗi dòng là một lượt cỗ máy chạy. (Vỏ bảng nằm ở `BangDuoi`.)
 *
 * Chữ do PYTHON dựng (`nhat_ky.dung_lo`), JS không ghép mẩu nào. Tải dần từng lô — đổ cả
 * 135.000 dòng vào DOM là treo hẳn WebView2.
 *
 * ⭐ GỘP DÃY LẶP là thứ đáng giá nhất ở đây. Manage chạy nhịp M1 nên MỖI nến M5 đẻ ra 5
 * dòng y hệt nhau: 296 dòng trên màn hình thật ra chỉ là ~60 sự việc, và người dùng phải
 * cuộn qua một bức tường chữ giống nhau để tìm dòng có nghĩa. Gộp lại kèm `×3` vừa gọn
 * 5 lần, vừa TRẢ LỜI THÊM được câu "cổng đó chặn mấy lượt liền" — thứ mà đếm tay không
 * ra. Chỉ gộp dãy LIỀN KỀ, không gộp cách quãng: gộp cách quãng là xáo trộn thứ tự thật.
 */
/** ⚠ BỌC `memo` — xem cuối file. Cửa sổ vẽ lại mỗi nhịp hỏi tiến độ (300 ms), mà nhật ký
 *  thì hàng trăm dòng và hiếm khi đổi. Không chặn ở đây thì vẽ thừa liên tục. */
function Journey({ dong, soi, chiViec }: {
  dong: DongNk[]
  /** Kéo cửa sổ vẽ lên trước và tô đường lượt này đã đi. */
  soi: (i: number) => void
  chiViec: boolean
}) {
  const boc = useRef<HTMLDivElement>(null)

  /** Dòng đang mở menu chuột phải. Giữ cả `i` chứ không chỉ toạ độ: mọi dòng trông
   *  giống nhau, nên phải TÔ dòng đang bị tác động — mở menu mà không biết nó thuộc
   *  dòng nào thì cái bấm nhầm chỉ dời đi một bước chứ không mất. */
  const [menu, setMenu] = useState<{ x: number; y: number; i: number; chu: string } | null>(null)

  const nhom = useMemo(() => {
    const ra: Nhom[] = []
    for (const d of dong) {
      if (chiViec && !d.co_viec) continue
      const cuoi = ra[ra.length - 1]
      // Dòng CÓ VIỆC không bao giờ bị gộp: hai lần đặt lệnh giống chữ nhau vẫn là hai
      // việc khác nhau, gộp lại là giấu mất một cái.
      if (cuoi && !d.co_viec && !cuoi.co_viec && cuoi.chu === d.chu) cuoi.dem++
      else ra.push({ i: d.i, co_viec: d.co_viec, chu: d.chu, dem: 1 })
    }
    return ra
  }, [dong, chiViec])

  /* Cuộn xuống cuối mỗi khi danh sách đổi: tải thêm một lô là thấy ngay những dòng vừa
     tải, không phải tự kéo xuống tìm. */
  useEffect(() => {
    if (boc.current) boc.current.scrollTop = boc.current.scrollHeight
  }, [nhom])

  /* ⚠ Bấm TRÁI không làm gì — phải chuột phải rồi chọn.
   *
   * Nhật ký là thứ để ĐỌC: cuộn, dò, quét mắt. Mà cả danh sách là một bức tường dòng
   * cao 20px giống hệt nhau, nên chỉ cần trượt tay một chút là kéo cửa sổ vẽ lên che mất
   * chỗ đang đọc. Việc kéo cửa sổ khác lên thì phải cố ý mới gọi được.
   *
   * Chuột phải không bao giờ bị bấm nhầm, và menu còn cho biết mình sắp làm gì. */
  return (
    <div className="nk-cuon" ref={boc}>
      {nhom.map(n => (
        <div key={n.i}
             className={'nk-dong' + (n.co_viec ? ' co-viec' : '')
                        + (menu?.i === n.i ? ' dang-menu' : '')}
             onContextMenu={e => {
               e.preventDefault()
               setMenu({ x: e.clientX, y: e.clientY, i: n.i, chu: n.chu })
             }}>
          <span className="chu">{n.chu}</span>
          {n.dem > 1 && <span className="lap" title={`${n.dem} lượt liền nhau giống hệt`}>
            ×{n.dem}
          </span>}
        </div>
      ))}

      {menu && (
        <ContextMenu x={menu.x} y={menu.y} onDong={() => setMenu(null)}
                     muc={[
                       // Câu hỏi ngay sau "chuyện gì đã xảy ra" luôn là "chỗ nào trên
                       // sơ đồ". Dò tay 20 hộp mất cả phút; cái này nối thẳng hai đầu.
                       { ten: 'Xem trên sơ đồ', icon: 'branch',
                         onClick: () => soi(menu.i) },
                       { ngan: true },
                       // Nhật ký là thứ hay phải mang đi hỏi/đối chiếu. Không chép được
                       // thì chỉ còn cách gõ tay lại một dòng mono dài.
                       { ten: 'Chép dòng', icon: 'copy',
                         onClick: () => void navigator.clipboard?.writeText(menu.chu) },
                     ]} />
      )}
    </div>
  )
}

/** ⚠ `soi` PHẢI là hàm ổn định ở phía cha (`useCallback`), không thì `memo`
 *  vô hiệu — prop hàm mới mỗi lần vẽ là đủ để React vẽ lại. */
export default memo(Journey)
