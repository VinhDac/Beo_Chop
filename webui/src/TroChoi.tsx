import { useCallback, useEffect, useRef, useState } from 'react'
import SoDo from './SoDo'
import ManMoMay from './man/ManMoMay'
import ManHanhTrinh from './man/ManHanhTrinh'

/** VỎ TRÒ CHƠI — giữ màn hình nào đang hiện, và chuyển cảnh giữa chúng.
 *
 *  ⭐ CANVAS THÔI LÀM HOME. Trước mốc này app chỉ có MỘT màn hình: mở lên là canvas, và
 *  mọi thứ về sau treo lên nó — ribbon, bảng dưới, thanh trạng thái, thẻ Cỗ máy, tám hộp
 *  thoại, 1.987 dòng. Đúng cái bệnh "nhồi ô vào khối Bắt đầu" mà ta đã chữa ở cấp khối,
 *  lặp lại ở cấp màn hình. Nay canvas là MỘT màn hình — cái Xưởng — và mỗi màn hình một
 *  việc. Xem `tai_lieu/thiet_ke_tro_choi.md` §2.
 *
 *  ⚠ ĐÚNG MỘT MÀN HÌNH SỐNG TẠI MỘT LÚC, và đây là luật cứng chứ không phải chuyện gọn
 *  mã. `TitleBar` mang theo `useKhungCuaSo` — bộ bắt kéo cửa sổ, nghe chuột ở mức
 *  `document`. Hai `TitleBar` cùng sống là hai bộ cùng bắt một cú bấm rồi cùng bảo
 *  Windows "bắt đầu kéo", mà mỗi màn hình lại tự vẽ thanh tiêu đề của mình. Nên không
 *  có chuyện giấu màn này đi rồi chồng màn kia lên: rời màn nào là gỡ hẳn màn ấy.
 *
 *  ⚠ VÀ VÌ GỠ HẲN nên rời Xưởng là `SoDo` bị tháo: ngăn Hoàn tác mất theo. Sơ đồ thì
 *  KHÔNG mất — `SoDo` tự ghi bản nháp và tự đọc lại lúc dựng. Nhưng nó ghi TRỄ 1,2 giây,
 *  nên rời Xưởng ngay sau một nét sửa là nét ấy chưa kịp ghi mà bộ đếm giờ đã bị huỷ
 *  theo component. `SoDo` phải ghi nốt TRƯỚC khi gọi `onRa` — xem chỗ ấy trong `SoDo`.
 */
export type Man = 'mo-may' | 'hanh-trinh' | 'xuong'

/** Màn che lúc chuyển cảnh tối trong bao lâu (ms). Phải khớp `--chuyen-canh` trong CSS.
 *
 *  180ms là con số đo bằng mắt: đủ để che hẳn cú tháo-lắp màn hình (lắp `SoDo` với cả
 *  trăm khối mất một nhịp vẽ thấy được), mà chưa đủ lâu để thành ra chờ. */
const CHE_MS = 180

export default function TroChoi() {
  const [man, setMan] = useState<Man>('mo-may')
  /** Màn chơi đang vào. Rỗng = chế độ SÁNG TẠO (vẽ tự do, không chấm). */
  const [manChoi, setManChoi] = useState('')
  /** Đang kéo màn che — trong lúc này màn hình cũ đã gỡ, màn mới chưa lắp. */
  const [dangChe, setDangChe] = useState(false)
  const hen = useRef(0)

  useEffect(() => () => window.clearTimeout(hen.current), [])

  /** Đổi màn hình: kéo màn che xuống, đổi, rồi kéo lên.
   *
   *  Cố ý KHÔNG hoà tan hai màn hình vào nhau (cross-fade): hoà tan thì cả hai phải
   *  cùng sống một lúc, mà luật trên đầu tệp cấm đúng chuyện đó. Màn che vừa né được
   *  luật ấy, vừa đúng chất một trò chơi hơn hẳn. */
  const doi = useCallback((m: Man, mc = '') => {
    setDangChe(true)
    window.clearTimeout(hen.current)
    hen.current = window.setTimeout(() => {
      setManChoi(mc)
      setMan(m)
      // Nhả màn che ở nhịp vẽ SAU, không nhả ngay: nhả cùng nhịp thì màn mới chưa kịp
      // dựng xong đã lộ ra, và người ta thấy một cái giật.
      requestAnimationFrame(() => requestAnimationFrame(() => setDangChe(false)))
    }, CHE_MS)
  }, [])

  return (
    <>
      {man === 'mo-may' && (
        <ManMoMay onHanhTrinh={() => doi('hanh-trinh')}
                  onSangTao={() => doi('xuong')} />
      )}
      {man === 'hanh-trinh' && (
        <ManHanhTrinh onVaoMan={ma => doi('xuong', ma)}
                      onRa={() => doi('mo-may')} />
      )}
      {man === 'xuong' && (
        <SoDo manChoi={manChoi}
              onRa={() => doi(manChoi ? 'hanh-trinh' : 'mo-may')} />
      )}
      <div className={'man-che' + (dangChe ? ' hien' : '')} aria-hidden />
    </>
  )
}
