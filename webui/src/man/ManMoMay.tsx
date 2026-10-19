import { useEffect, useState } from 'react'
import TitleBar from '../components/TitleBar'
import { CAC_NGON_NGU, datNgonNgu, tr, useNgonNgu } from '../ngon_ngu'
import { cho_cau_noi, py } from '../api'

/** MÀN MỞ MÁY — thứ đầu tiên người ta thấy khi bật app.
 *
 *  Trước mốc này, mở app lên là một canvas trống với 164 đại lượng chờ sẵn. Không một
 *  dòng nào nói đây là cái gì, bắt đầu từ đâu. Màn này làm đúng một việc: nói app này
 *  là cái gì, rồi đưa người ta đi đúng một trong hai hướng.
 *
 *  ⚠ CÓ Ô ĐỔI TIẾNG NGAY ĐÂY, và nó không thừa. App mặc định tiếng Anh, mà hộp Cài đặt
 *  lại nằm trong Xưởng — tức người Việt mở app lần đầu phải đi xuyên qua một màn hình
 *  tiếng Anh mới tới được chỗ đổi sang tiếng Việt. Ô này ghi bằng CHÍNH tiếng của nó
 *  ("English" / "Tiếng Việt") nên ai cũng tìm ra chữ của mình.
 */
export default function ManMoMay({ onHanhTrinh, onSangTao }: {
  onHanhTrinh: () => void
  onSangTao: () => void
}) {
  const nn = useNgonNgu()
  /** Có bản nháp dở dang không — để nút đầu tiên nói đúng việc nó làm. */
  const [coNhap, setCoNhap] = useState(false)

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        return                      // không nối được thì vẫn vào được Xưởng, nó tự báo
      }
      const r = await py.doc_ban_nhap()
      setCoNhap(!!(r.ok && r.value && (r.value.steps?.length ?? 0) > 0))
    })()
  }, [])

  /** Đổi tiếng — đi qua ĐÚNG cửa mà hộp Cài đặt đi, không gọi thẳng `datNgonNgu`.
   *
   *  ⚠ ĐÃ HỎNG THẬT, và hỏng hai kiểu cùng lúc. Gọi thẳng `datNgonNgu` chỉ đổi ngôn ngữ
   *  TRONG BỘ NHỚ CỦA WEB:
   *    · Python không nghe thấy — mà tên hồi, tên màn, câu dạy đều do Python dựng. Đổi
   *      sang tiếng Việt xong, bản đồ hành trình vẫn nguyên tiếng Anh.
   *    · Không ghi vào Cài đặt, nên `cho_cau_noi` ở lần nối sau đọc lại cài đặt CŨ rồi
   *      `datNgonNgu` ĐẶT NGƯỢC về tiếng Anh (xem `api.ts`). Người dùng đổi tiếng, đi
   *      sang màn khác, và nó tự nhảy về — trông y như app không nhận.
   *  Một cửa duy nhất thì không có chỗ nào để lệch. */
  async function doiTieng(n: string) {
    const r = await py.cai_dat_ghi({ ngon_ngu: n })
    if (r.ok && r.value) datNgonNgu(r.value.gia_tri.ngon_ngu)
  }

  return (
    <div className="mm" key={nn}>
      <TitleBar tieuDe="Cat Studio" menus={[]} />

      <div className="mm-than">
        <MayChay />

        <h1 className="mm-ten">Cat Studio</h1>
        <p className="mm-cau">{tr('Vẽ một cỗ máy. Thả nó vào thị trường. Xem nó sống được không.')}</p>

        <div className="mm-nut">
          <button className="nut-to chinh" onClick={onHanhTrinh}>
            {tr('Hành trình')}
            <small>{tr('26 màn — học từ cái máy hai khối tới boss cuối')}</small>
          </button>
          <button className="nut-to" onClick={onSangTao}>
            {coNhap ? tr('Vẽ tiếp') : tr('Sáng tạo')}
            <small>{coNhap
              ? tr('Mở lại cỗ máy đang vẽ dở')
              : tr('Mở hết đồ nghề, không chấm điểm')}</small>
          </button>
        </div>
      </div>

      <div className="mm-chan">
        <select className="o mm-tieng" value={nn}
                onChange={e => void doiTieng(e.target.value)}>
          {CAC_NGON_NGU.map(n => (
            <option key={n.ma} value={n.ma}>{n.nhan}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

/** CỖ MÁY ĐANG CHẠY — hình nền sống của màn mở.
 *
 *  Vẽ bằng SVG ngay tại đây chứ không nhét một file ảnh: đây CHÍNH LÀ thứ app làm ra —
 *  mấy khối nối nhau và dòng điện chạy trong dây — nên nó phải sống, không phải một bức
 *  hình chết. Và nó là bản xem trước của màn «Chạy máy» ở mốc sau.
 *
 *  ⚠ MỖI SỢI DÂY LÀ HAI ĐƯỜNG CHỒNG NHAU, và đây là chỗ bản đầu làm sai. Một đường
 *  không thể vừa là sợi dây vừa là vệt sáng chạy trên nó: muốn vệt sáng thì phải đặt
 *  `stroke-dasharray`, mà đặt lên chính sợi dây thì gần hết sợi dây thành KHOẢNG TRỐNG.
 *  Nhìn ảnh chụp mới thấy — bốn cái khối rời nhau với mấy mẩu dây cụt 8 pixel, không ra
 *  cái máy nào cả. Nay: một đường NỀN liền nét lúc nào cũng có, một đường SÁNG đứt nét
 *  chạy đè lên.
 *
 *  Dòng chảy làm bằng `stroke-dashoffset` chạy vòng: một thuộc tính, chạy trên GPU,
 *  không tốn một khung hình JS nào và không bao giờ giật khi máy đang bận. */
function MayChay() {
  /** Ba chặng dây, viết một lần dùng hai lần (nền + vệt sáng) — chép tay hai bản là
   *  sớm muộn sửa toạ độ một bên mà quên bên kia. */
  const day = ['M96 64 H176', 'M232 64 H312', 'M368 64 H440']
  return (
    <svg className="mm-may" viewBox="0 0 520 128" aria-hidden>
      <g className="mm-nen">
        {day.map(d => <path key={d} d={d} />)}
      </g>
      <g className="mm-dong">
        {day.map((d, i) => (
          <path key={d} d={d} style={{ animationDelay: `${i * 0.34}s` }} />
        ))}
      </g>
      <g className="mm-khoi">
        <rect x="30" y="40" width="66" height="48" rx="9" style={{ animationDelay: '0s' }} />
        <rect x="176" y="40" width="56" height="48" rx="9" style={{ animationDelay: '.34s' }} />
        <rect x="312" y="40" width="56" height="48" rx="9" style={{ animationDelay: '.68s' }} />
        <circle cx="462" cy="64" r="22" style={{ animationDelay: '1.02s' }} />
      </g>
    </svg>
  )
}
