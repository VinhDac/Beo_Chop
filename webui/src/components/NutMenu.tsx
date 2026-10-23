import { useRef, useState } from 'react'
import BangNoi from './BangNoi'
import Icon from './Icon'

/** NÚT CÓ MENU XỔ trên ribbon — chép lối `NutMenu` của Jenifer_Studio.
 *
 *  VÌ SAO CẦN. Mười ba nút «thêm khối» rải thành ba nhóm trên một hàng thì ribbon
 *  dài hơn cửa sổ, mà mười ba cái cũng CÙNG MỘT VIỆC: thả một khối xuống canvas.
 *  Jenifer giải đúng chuyện này bằng một nút THỂ LOẠI: *"chọn loại nào là việc của
 *  hộp thoại"*. Một slot thay cho năm, và cái tên trên nút nói đúng việc nó làm.
 *
 *  MỤC BỊ TẮT VẪN HIỆN, KÈM LÝ DO — luật của Jenifer, và nó đúng gấp đôi ở đây vì
 *  «Hỏi doanh nghiệp» tắt là do THIẾU DỮ LIỆU chứ không phải do chưa làm xong. Giấu
 *  đi thì người chơi tưởng tính năng không tồn tại và không bao giờ đi tìm.
 *
 *  Vỏ nổi dùng lại `BangNoi`: nó đã lo định vị theo khung nhìn, tự lật khi dưới hết
 *  chỗ, Esc, và bấm ra ngoài. Dải ribbon có `overflow-x: auto`, mà hễ một trục thôi
 *  `visible` thì trục kia cũng thôi — nên một menu `absolute` sẽ bị dải ribbon xén
 *  cụt theo chiều dọc. (Lỗi ấy Jenifer đã dính và đã ghi lại.)
 */
export interface MucMenu {
  nhan: string
  /** Dòng phụ nhỏ bên dưới — mô tả, hoặc hàm LEAN nó sẽ gọi. */
  phu?: string
  icon?: string
  /** Chuỗi = mục này chưa dùng được, và đây là lý do. */
  tat?: string | false
  chay: () => void
}

export default function NutMenu({ ten, icon, muc, title, dauMuc }: {
  ten: string
  icon: string
  muc: MucMenu[]
  title?: string
  /** Tên mục đầu đoạn, theo thứ tự — mục nào không khai thì nối vào đoạn trước. */
  dauMuc?: (m: MucMenu, i: number) => string | undefined
}) {
  const [neo, setNeo] = useState<DOMRect | null>(null)
  const rf = useRef<HTMLButtonElement>(null)

  return (
    <>
      <button ref={rf} className={'nut-lon' + (neo ? ' dang-mo' : '')}
              title={title ?? ten}
              onClick={() => setNeo(neo ? null : (rf.current?.getBoundingClientRect() ?? null))}>
        <span className="hinh"><Icon name={icon} size={18} /></span>
        {ten} ▾
      </button>
      {neo && (
        <BangNoi neo={neo} rong={286} cao={420} onDong={() => setNeo(null)}>
          <div className="menu-xo">
            {muc.map((m, i) => {
              const dau = dauMuc?.(m, i)
              return (
                <div key={m.nhan + i}>
                  {dau && <div className="mx-dau">{dau}</div>}
                  <button className="mx-muc" disabled={!!m.tat}
                          onClick={() => { setNeo(null); m.chay() }}>
                    {m.icon && <Icon name={m.icon} size={15} />}
                    <span className="mx-chu">
                      <b>{m.nhan}</b>
                      {(m.tat || m.phu) && <i>{m.tat || m.phu}</i>}
                    </span>
                  </button>
                </div>
              )
            })}
          </div>
        </BangNoi>
      )}
    </>
  )
}
