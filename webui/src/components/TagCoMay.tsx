/** VIÊN THUỐC «CỖ MÁY LEAN» ở góc PHẢI trên canvas — cửa vào hộp Cỗ máy.
 *
 *  ⚠ NÓ LUÔN CÓ MẶT, kể cả khi chưa ai đặt gì. Cả bốn trạm dây chuyền mặc định là
 *  «— không dùng —», nên nếu giữ luật "mặc định thì im" cho cả viên thuốc thì góc
 *  phải trống trơn — mà nó lại là CỬA DUY NHẤT vào mấy ô ấy. Cửa vô hình thì không
 *  ai mở. Chưa đặt gì thì nó ghi đúng câu ấy: «chưa đặt gì».
 *
 *  CÒN CHỮ BÊN TRONG thì chỉ kể thứ ĐÃ ĐỔI (`core.tom_tat_co_may`). Kể cả mặc định
 *  thì viên thuốc dài bằng cả hộp thoại, và ta chỉ dời đống lộn xộn từ khối Bắt đầu
 *  sang góc màn hình — đúng cái vừa chữa.
 *
 *  CÙNG DÁNG VIÊN THUỐC với ô «Tìm khối…» ở góc trái (`.o-tim-khoi`): hai thứ nổi
 *  trên canvas mà khác dáng nhau thì trông như hai app.
 */
export default function TagCoMay({ tomTat, onMo }: {
  /** Mấy chữ Python dựng sẵn — chỗ này không biết ô nào là mặc định. */
  tomTat: string[]
  onMo: () => void
}) {
  const co = tomTat.length > 0
  return (
    <button type="button" className={'tag-co-may' + (co ? ' co' : '')}
            title={co ? `Cỗ máy LEAN: ${tomTat.join(' · ')} — bấm để sửa`
                      : 'Cỗ máy LEAN — dây chuyền, phí sàn, ô nhớ, mốc so sánh'}
            onClick={onMo}>
      <span className="ten">CỖ MÁY LEAN</span>
      <span className="gt">{co ? tomTat.join(' · ') : 'chưa đặt gì'}</span>
    </button>
  )
}
