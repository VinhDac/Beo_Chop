/** VIÊN THUỐC «CỖ MÁY LEAN» ở góc PHẢI trên canvas — cửa vào hộp Cỗ máy.
 *
 *  ⚠ NÓ LUÔN CÓ MẶT, kể cả khi chưa ai đặt gì. Cả bốn trạm dây chuyền mặc định là
 *  «— không dùng —», nên nếu giữ luật "mặc định thì im" cho cả viên thuốc thì góc
 *  phải trống trơn — mà nó lại là CỬA DUY NHẤT vào mấy ô ấy. Cửa vô hình thì không
 *  ai mở. Chưa đặt gì thì nó ghi đúng câu ấy: «chưa đặt gì».
 *
 *  MỖI VIỆC MỘT THẺ `.the`, KHÔNG NỐI THÀNH MỘT CÂU — lối của Jenifer_Studio, và
 *  `.the` là đúng cái class thẻ huy hiệu trên khối đang dùng. Bản trước nối mấy mẩu
 *  bằng dấu chấm giữa, nên viên thuốc thành một dòng chữ chạy ngang nửa canvas và
 *  không đọc ra được món nào với món nào. Thẻ rời thì mắt ĐẾM được: liếc một cái là
 *  biết LEAN đang lo mấy việc, chứ không phải đọc hết câu mới biết.
 *
 *  PHÌNH THÌ PHÌNH XUỐNG DƯỚI. Bề ngang chặn cứng bên CSS, nên thêm một món là thẻ
 *  xuống dòng chứ cái hộp không kéo dài ra giữa canvas — chỗ ấy là chỗ nhìn sơ đồ.
 *  Và không cắt bớt thẻ: cắt là mất hẳn mấy việc cuối mà không có dấu hiệu nào. Chữ
 *  trong MỘT thẻ mới cắt ba chấm.
 */
export default function TagCoMay({ tomTat, onMo }: {
  /** Mấy thẻ Python dựng sẵn, đã rút ngắn (`core.tom_tat_co_may`) — chỗ này không
   *  biết ô nào là mặc định, cũng không tự cắt chữ. */
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
      {co ? tomTat.map(x => <span className="the" key={x}>{x}</span>)
          : <span className="trong">chưa đặt gì</span>}
    </button>
  )
}
