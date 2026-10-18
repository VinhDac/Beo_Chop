import type { ChipKhung } from '../types'

/** KHUNG LƯỢT CHẠY — mấy chip nổi ở góc PHẢI trên canvas.
 *
 *  VÌ SAO NÓ RỜI KHỎI KHỐI BẮT ĐẦU. Thẻ khối trước đây in cả khoảng ngày, vốn, mốc so
 *  sánh — nên một khối phình ra năm sáu dòng vì mấy thứ chẳng dính gì tới dòng chảy
 *  ngay dưới nó. Chúng là KHUNG của lượt chạy, đúng với cả sơ đồ, không phải một
 *  bước. Và trên sơ đồ lớn thì khối Bắt đầu trôi ra ngoài màn hình từ lâu, trong khi
 *  câu «đang chạy bằng bao nhiêu tiền» thì lúc nào cũng cần trả lời được.
 *
 *  CÙNG DÁNG VIÊN THUỐC với ô «Tìm khối…» ở góc trái (`.o-tim-khoi`): hai thứ nổi
 *  trên canvas mà khác dáng nhau thì trông như hai app.
 *
 *  BẢNG CHIP DO PYTHON DỰNG (`core.khung_chay`), kể cả luật "mặc định thì im". Chỗ
 *  này không biết có mấy ô, cũng không biết ô nào là mặc định — biết thì nó thành
 *  bản thứ hai của từ điển, và bản thứ hai thì trôi khỏi bản gốc.
 */
export default function TagKhungChay({ chip, onMo }: {
  chip: ChipKhung[]
  /** Bấm một chip -> mở hộp Bắt đầu, cuộn tới đúng NHÓM của chip ấy. */
  onMo: (nhom: string) => void
}) {
  // Chưa soát xong thì không vẽ gì: một viên thuốc rỗng khó hiểu hơn là chưa vẽ, mà
  // nó chỉ rỗng trong đúng vài nhịp đầu.
  if (!chip.length) return null
  return (
    <div className="tag-khung">
      {chip.map(c => (
        <button key={c.nhan} type="button" className="chip"
                title={`${c.nhan}: ${c.gia_tri} — bấm để sửa`}
                onClick={() => onMo(c.nhom)}>
          <span className="nhan">{c.nhan}</span>
          <span className="gt">{c.gia_tri}</span>
        </button>
      ))}
    </div>
  )
}
