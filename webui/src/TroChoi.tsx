import { useCallback, useEffect, useRef, useState } from 'react'
import SoDo from './SoDo'
import ManMoMay from './man/ManMoMay'
import ManHanhTrinh from './man/ManHanhTrinh'
import ManNhanViec from './man/ManNhanViec'
import ManChayMay, { type ViecChayMay } from './man/ManChayMay'
import ManCham from './man/ManCham'
import ManKho from './man/ManKho'
import { py } from './api'
import type { ManHT } from './types'

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
export type Man = 'mo-may' | 'hanh-trinh' | 'nhan-viec' | 'xuong' | 'chay-may'
                | 'cham' | 'kho'

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
  /** Việc của màn CHẠY MÁY: sơ đồ Xưởng vừa giao, kèm lượt soát của đúng sơ đồ ấy.
   *
   *  Giữ Ở ĐÂY chứ không trong `ManChayMay`, vì `SoDo` bị THÁO lúc chuyển cảnh (luật
   *  một màn hình sống) — sơ đồ phải đi qua tay vỏ trò chơi mới sang được màn kia. */
  const [viecChay, setViecChay] = useState<ViecChayMay | null>(null)
  /** Lượt vừa chạy xong của một màn, chờ chấm. */
  const [luotCham, setLuotCham] = useState('')
  /** Màn đang chơi, bản đầy đủ — màn Chấm cần `co_man_an`, `gon`, `ten`.
   *
   *  Hỏi lại Python mỗi lần vào màn chứ không giữ bản chép: danh sách màn chỉ có một
   *  chỗ (`hanh_trinh.py`), và giữ bản chép ở đây là chỗ thứ hai. */
  const [manDay, setManDay] = useState<ManHT | null>(null)
  const hen = useRef(0)

  useEffect(() => {
    if (!manChoi) { setManDay(null); return }
    let song = true
    void (async () => {
      const r = await py.hanh_trinh()
      if (song && r.ok && r.value) {
        setManDay(r.value.man.find(m => m.ma === manChoi) ?? null)
      }
    })()
    return () => { song = false }
  }, [manChoi])

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
        <ManHanhTrinh onVaoMan={ma => doi('nhan-viec', ma)}
                      onKho={() => doi('kho')}
                      onRa={() => doi('mo-may')} />
      )}
      {/* NHẬN VIỆC — màn hình số 3 của bản thiết kế, và nó THIẾU suốt từ mốc M1.
          Bấm một màn trên bản đồ là nhảy thẳng vào Xưởng, mà Xưởng dùng CHUNG với chế
          độ Sáng tạo — nên vào màn và vẽ tự do trông y hệt nhau, đúng như người dùng
          báo. Nay có một cánh cửa nói rõ: màn này là gì, sân ở đâu, boss là ai, ăn sao
          thế nào. Xem `ManNhanViec`. */}
      {man === 'nhan-viec' && (
        <ManNhanViec man={manDay} onVao={() => doi('xuong', manChoi)}
                     onRa={() => doi('hanh-trinh')} />
      )}
      {/* KHO — vai thứ sáu. Mở được từ bản đồ bất cứ lúc nào: nó là chỗ TRA, không
          phải một chặng phải đi qua. */}
      {man === 'kho' && <ManKho onRa={() => doi('hanh-trinh')} />}
      {/* ⚠ HAI THỨ, HAI VIỆC, KHÔNG PHẢI HAI BẢN CỦA MỘT THỨ. `manChoi` là MÃ màn —
          đặt ĐỒNG THỜI với lúc đổi màn hình, nên Xưởng có nó ngay khung hình đầu và
          kịp dán sân lên khối Bắt đầu. `manDay` là bản ĐẦY ĐỦ, hỏi Python về sau, chỉ
          để BÀY tên màn. Truyền mỗi `manDay` rồi tự suy ra mã là sân không bao giờ
          được dán, vì lúc Xưởng dựng thì nó còn `null`. */}
      {man === 'xuong' && (
        <SoDo manChoi={manChoi} man={manDay}
              onRa={() => doi(manChoi ? 'nhan-viec' : 'mo-may')}
              onChayMay={v => { setViecChay(v); doi('chay-may', manChoi) }} />
      )}
      {/* CHẠY MÁY — vai thứ tư. Vào màn này là MỘT lượt chạy mới: rời màn là component
          bị tháo hẳn (luật một màn hình sống), nên không có cuộn phim cũ nào còn đứng
          ở nhịp 300 để phải dọn. */}
      {man === 'chay-may' && viecChay && (
        <ManChayMay viec={viecChay} onRa={() => doi('xuong', manChoi)}
                    onCham={ml => { setLuotCham(ml); doi('cham', manChoi) }} />
      )}
      {/* CHẤM — vai thứ năm. Chỉ có khi đang chơi một màn: Sáng tạo không chấm. */}
      {man === 'cham' && manDay && viecChay && (
        <ManCham man={manDay} maLuot={luotCham} viec={viecChay}
                 onSuaTiep={() => doi('xuong', manChoi)}
                 onRa={() => doi('hanh-trinh')} />
      )}
      <div className={'man-che' + (dangChe ? ' hien' : '')} aria-hidden />
    </>
  )
}
