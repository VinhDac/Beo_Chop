import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { tr } from '../ngon_ngu'
import { soTien } from '../so'
import type { ManHT } from '../types'
import { Sao } from './ManCham'

/** MÀN NHẬN VIỆC — màn hình số 3 của bản thiết kế (§2), và nó THIẾU suốt từ mốc M1.
 *
 *  ⚠ ĐÂY LÀ CHỖ HỎNG NGƯỜI DÙNG BÁO: «bấm vào không link tới màn mà lại link sang
 *  creative mode». Bấm một màn trên bản đồ là nhảy THẲNG vào Xưởng — mà Xưởng thì dùng
 *  CHUNG với chế độ Sáng tạo, cùng ribbon, cùng bản nháp, cùng thanh tiêu đề mang tên
 *  bản vẽ. Sân của màn có được dán lên khối Bắt đầu thật, nhưng đó là thay đổi nằm
 *  TRONG một cái hộp giữa canvas: nhìn cả màn hình thì không một chữ nào nói mình đang
 *  chơi màn nào, thắng cái gì là thắng. Nên vào màn và vẽ tự do trông y hệt nhau.
 *
 *  Màn này là cánh cửa: đọc xong mới vào Xưởng, và lúc ra vào lại được. Nó KHÔNG tính
 *  gì cả — mọi thứ bày ở đây đều do `hanh_trinh.py` gửi sang.
 *
 *  ⚠ KHÔNG BAO GIỜ BÀY NGÀY CỦA MÀN ẨN. `cong_khai` bên Python đã cắt chúng từ gốc, và
 *  ở đây chỉ có `an_mo_ta` — một câu tả, không phải hai cái mốc. Biết ngày ẩn là vặn
 *  máy cho vừa khít đúng khoảng ấy, và ngôi sao thứ ba mất sạch nghĩa mà vẫn sáng lên
 *  y như thật. */
export default function ManNhanViec({ man, onVao, onRa }: {
  man: ManHT | null
  /** Vào Xưởng vẽ màn này. */
  onVao: () => void
  onRa: () => void
}) {
  return (
    <div className="nv">
      <TitleBar tieuDe={tr('Nhận việc')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={tr('Về bản đồ')}>←</button>
      } />

      {!man && (
        <div className="nv-cho"><Icon name="chay" /> {tr('đang mở màn…')}</div>
      )}

      {man && (
        <div className="nv-than">
          <div className="nv-giua">
            <div className="nv-dau">
              <span className="nv-so">{String(man.so).padStart(2, '0')}</span>
              <h1 className="nv-ten">{man.ten}</h1>
            </div>
            <p className="nv-day">{man.day}</p>

            {/* LỜI DẶN của con mèo — chuyện của cái thị trường này, vì sao màn này
                khó. Đây là phần KỂ, nên nó đứng tách khỏi mấy ô số liệu. */}
            {!!man.loi_dan && (
              <p className="nv-dan">
                {/* Logo app làm mặt con mèo đang nói — bộ icon không có con mèo nào,
                    mà vẽ thêm một con mèo thứ hai ở đây là lại hai bộ mặt. */}
                <img className="nv-meo" src="./logo.png" alt="" />
                {man.loi_dan}
              </p>
            )}

            {/* MÀN CHƯA CÓ SÂN thì nói thẳng vì sao, và không mời vào Xưởng nữa. */}
            {man.co_san === false && !!man.vi_sao_chua && (
              <div className="nv-chua">⚠ {man.vi_sao_chua}</div>
            )}

            <div className="nv-o">
              {!!man.symbol && (
                <section className="nv-hop">
                  <h2>{tr('Sân')}</h2>
                  <div className="nv-san">
                    <span className="nv-ma">{man.symbol.toUpperCase()}</span>
                    {!!man.thay && <span>{man.thay[0]} → {man.thay[1]}</span>}
                    {!!man.von && <span>${soTien(man.von)}</span>}
                  </div>
                  {man.co_man_an && !!man.an_mo_ta && (
                    <p className="nv-an">{tr('Và một màn ẩn: {0}', man.an_mo_ta)}</p>
                  )}
                </section>
              )}

              {!!man.boss && (
                <section className="nv-hop">
                  <h2>{tr('Boss')}</h2>
                  <div className="nv-boss">{man.boss.ten}</div>
                  <p className="nv-boss-ta">{man.boss.mo_ta}</p>
                </section>
              )}
            </div>

            {/* BA SAO — mục tiêu, nên vẽ bằng ĐÚNG thành phần của màn Chấm với 0 sao.
                Gõ lại ba câu ấy ở đây là bản thứ ba của luật chơi (bản đầu là
                `luat_choi.sao`, bản hai là màn Chấm), và hôm luật đổi thì màn Nhận
                việc hứa một đằng còn màn Chấm chấm một nẻo. */}
            <section className="nv-hop nv-sao">
              <h2>{tr('Ăn sao thế nào')}</h2>
              {man.cham_duoc
                ? <>
                    <Sao n={0} />
                    {/* ⚠ Y NGUYÊN CÂU CỦA MÀN CHẤM, tới từng chữ. Viết khác một chữ là
                        bảng dịch có HAI khoá gần giống nhau, rồi hôm sửa lời thì chỉ
                        một bên đổi — màn Nhận việc hứa một kiểu, màn Chấm chấm một
                        kiểu, mà không bài kiểm nào thấy. */}
                    {!!man.gon && (
                      <p className="nv-gon">{tr('Huy chương GỌN — ba sao mà vẫn dưới '
                        + '{0} khối cộng núm.', man.gon)}</p>
                    )}
                  </>
                : <p className="nv-khong">{tr('Màn này KHÔNG chấm sao — nó dựng ra thứ '
                    + 'mấy màn sau phải đánh bại.')}</p>}
            </section>

            {!!man.mo.length && (
              <section className="nv-hop">
                <h2>{tr('Màn này mở thêm')}</h2>
                <div className="nv-mo">
                  {man.mo.map(x => (
                    <span className={'ht-the ' + x.loai} key={x.nhan}>{x.nhan}</span>
                  ))}
                </div>
              </section>
            )}

            <div className="nv-nut">
              <button className="nut-to chinh" onClick={onVao}>
                {tr('Vào xưởng')}
                <small>{tr('Vẽ cỗ máy cho màn này')}</small>
              </button>
              <button className="nut-to" onClick={onRa}>
                {tr('Về bản đồ')}
                <small>{tr('Chọn màn khác')}</small>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
