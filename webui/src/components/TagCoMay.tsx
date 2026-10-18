import { useState } from 'react'
import Icon from './Icon'

/** Ô CỖ MÁY LEAN ở góc PHẢI canvas — cài đặt chung của cả sơ đồ.
 *
 *  DÁNG CHÉP TỪ Ô TRỢ THỦ CỦA JENIFER_STUDIO (`.o-tro-thu`), và chép vì cùng một lẽ:
 *  **nó không phải một bước**. Không số thứ tự, không cổng nối, không kéo đi được,
 *  không nằm trong `steps`. Vẽ nó giống một khối thì người dùng sẽ đi tìm cổng để
 *  nối, tìm số thứ tự để biết nó chạy lúc nào — hai thứ không tồn tại. Nên:
 *    · viền ĐỨT — quy ước quen thuộc cho "không nằm trong luồng"
 *    · KHÔNG bóng đổ — bóng làm nó nổi lên như một khối thật
 *    · hẹp hơn khối (296px) một quãng rõ rệt, để không ai nhầm là cùng một họ
 *    · màu riêng `--co-may`, không lẫn với màu khối nào trên sơ đồ
 *
 *  ⚠ NÓ LUÔN CÓ MẶT, kể cả khi chưa đặt gì. Cả bốn trạm dây chuyền mặc định là
 *  «— không dùng —», nên nếu giữ luật "mặc định thì im" cho cả cái ô thì góc phải
 *  trống trơn — mà nó lại là CỬA DUY NHẤT vào mấy ô ấy. Cửa vô hình thì không ai mở.
 *
 *  THU GỌN CÒN ĐÚNG HÀNG ĐẦU. Phần chữ giải thích là để đọc MỘT LẦN — đọc xong rồi
 *  thì nó chỉ còn là một mảng chắn mất góc canvas. Gọn lại vẫn giữ hàng đầu, vì đó
 *  mới là thứ cần thấy mỗi ngày: sơ đồ này CÓ cài đặt ấy, và đang đặt mấy thứ.
 */
export default function TagCoMay({ tomTat, onMo }: {
  /** Mấy thẻ Python dựng sẵn, đã rút ngắn (`core.tom_tat_co_may`) — chỗ này không
   *  biết ô nào là mặc định, cũng không tự cắt chữ. */
  tomTat: string[]
  onMo: () => void
}) {
  const [gon, setGon] = useState(false)
  const co = tomTat.length > 0
  return (
    <div className={'o-co-may' + (gon ? ' gon' : '')}>
      {/* Double-click ở HÀNG ĐẦU, không phải cả ô: gọn lại rồi thì cả ô chính là
          hàng đầu, nên lối mở cài đặt không mất đi khi thu gọn. */}
      <div className="cm-dau" onDoubleClick={onMo}>
        <span className="dai-mau" />
        <Icon name="gear" size={13} />
        <span className="cm-ten">Cỗ máy LEAN</span>
        <span className="cm-nhan">{co ? `${tomTat.length} thứ` : 'chưa đặt gì'}</span>
        <button className="cm-gon" onClick={() => setGon(!gon)}
                onDoubleClick={e => e.stopPropagation()}
                title={gon ? 'Mở ra' : 'Thu gọn'}>{gon ? '▼' : '▲'}</button>
      </div>
      {!gon && (
        <>
          <div className="cm-than">
            Không phải một bước — đây là <b>những thứ LEAN lo hộ</b>, dùng chung cho
            cả sơ đồ: bốn trạm dây chuyền, phí sàn, ô nhớ, mốc so sánh.
            <div className="cm-nhac">
              {co
                ? tomTat.map(x => <span className="the" key={x}>{x}</span>)
                : 'Chưa đặt gì — LEAN chạy ở mặc định của nó.'}
            </div>
          </div>
          <button className="nut nut-nho cm-sua" onClick={onMo}>
            <Icon name="gear" size={12} /> Cài đặt cỗ máy
          </button>
        </>
      )}
    </div>
  )
}
