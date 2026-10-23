/* NHẬT KÝ SỐNG — dòng nảy lên đúng lúc nó xảy ra.
 *
 * Khác một danh sách tĩnh cuộn được: lúc PHÁT, nó tự chạy theo con trỏ. Đó là cả
 * điểm của việc đọc nhật ký sống — thấy dòng «đặt lệnh» hiện ra đúng nhịp mà mũi tên
 * xuất hiện trên chart.
 *
 * ⚠ NHẬT KÝ LÀ CỦA CẢ LƯỢT, không lọc theo mã đang xem. Một lượt 31 lệnh trên năm
 * chục mã mà lọc theo mã thì bày ra gần như trống — và đó đúng là thứ đã xảy ra, chỉ
 * là người xem không thấy. Bấm một dòng thì mới mở to mã của dòng ấy.
 *
 * ⚠ BẤM TRÁI ĐỂ ĐI, BẤM PHẢI ĐỂ LÀM. Bấm trái nhảy con trỏ tới đó — việc làm cả
 * ngày, nên nó phải rẻ. Soi sơ đồ thì nằm trong menu chuột phải: nó mở một cửa sổ
 * con, mà một cú bấm nhầm làm bật cửa sổ con lên giữa lúc đang tua là phiền.
 */
import { memo, useEffect, useMemo, useRef, useState } from 'react'
import ContextMenu from '../components/ContextMenu'
import { tr } from '../ngon_ngu'
import type { DongNhatKy } from './mach_view'

/** Một DÃY dòng giống hệt nhau nằm liền nhau, gộp thành một. */
interface Nhom {
  /** Dòng ĐẦU của dãy — chỗ con trỏ sẽ nhảy tới, và dòng mang `tag` để soi. */
  d: DongNhatKy
  /** Mốc của dòng CUỐI trong dãy — để biết dãy ấy kéo dài tới đâu. */
  tCuoi: number
  dem: number
}

export interface NhatKyProps {
  ds: DongNhatKy[]
  /** Mốc con trỏ đang đứng — dòng sau mốc này thì CHƯA xảy ra. */
  tToi: number
  nhay: (t: number, ma: string) => void
  /** Mở sơ đồ ra soi đường của dòng này. */
  soi: (d: DongNhatKy) => void
}

function NhatKy({ ds, tToi, nhay, soi }: NhatKyProps) {
  const hop = useRef<HTMLDivElement>(null)
  const [menu, setMenu] = useState<{ x: number; y: number; n: Nhom } | null>(null)

  /* ⭐ GỘP DÃY LẶP — thứ đáng giá nhất của nhật ký cửa sổ Tester cũ.
   *
   * Cỗ máy chạy mỗi nến, nên một cổng chặn suốt ba tháng đẻ ra sáu chục dòng y hệt
   * nhau: người đọc phải cuộn qua một bức tường chữ giống nhau để tìm dòng có nghĩa.
   * Gộp lại kèm `×6` vừa gọn sáu lần, vừa TRẢ LỜI THÊM được câu «cổng đó chặn mấy
   * nến liền» — thứ mà đếm tay không ra.
   *
   * ⚠ CHỈ GỘP DÃY LIỀN KỀ, không gộp cách quãng: gộp cách quãng là xáo trộn thứ tự
   * thật của lượt chạy.
   *
   * ⚠ DÒNG CÓ VIỆC KHÔNG BAO GIỜ BỊ GỘP. Hai lệnh mua cùng mã cùng giá vẫn là HAI
   * cái lệnh; gộp lại thành «×2» là giấu mất một cái, mà đếm lệnh thì phải đúng. */
  const nhom = useMemo(() => {
    const ra: Nhom[] = []
    for (const d of ds) {
      if (d.t > tToi) break
      const cuoi = ra[ra.length - 1]
      if (cuoi && !d.viec && !cuoi.d.viec
          && cuoi.d.chu === d.chu && cuoi.d.ma === d.ma && cuoi.d.tag === d.tag) {
        cuoi.dem++
        cuoi.tCuoi = d.t
      } else {
        ra.push({ d, tCuoi: d.t, dem: 1 })
      }
    }
    return ra
  }, [ds, tToi])

  /** Nhóm được tô sáng: nhóm GẦN NHẤT tính tới con trỏ, không phải nhóm trùng khít
   *  nhịp hiện tại. Lệnh chỉ ra ở ít nến, nên lấy mốc trùng khít thì phần lớn thời
   *  gian màn hình chẳng có gì sáng — mà câu người xem cần trả lời («gần đây nhất cỗ
   *  máy làm gì») thì lúc nào cũng có đáp án. */
  const sang = nhom.length - 1

  /* TỰ CUỘN THEO DÒNG MỚI NHẤT. Không có nó thì lúc phát, dòng mới rơi xuống dưới
     mép và người xem nhìn một danh sách đứng im — đúng cái bản cũ phải sửa. */
  useEffect(() => {
    const el = hop.current
    if (el) el.scrollTop = el.scrollHeight
  }, [nhom.length])

  return (
    <div className="view-nk">
      <div className="view-nk-cuon" ref={hop}>
        {ds.length === 0 && (
          <div className="view-nk-trong">{tr('Lượt này chưa ghi dòng nhật ký nào.')}</div>
        )}
        {nhom.map((n, k) => (
          <button
            key={k} type="button"
            className={'view-nk-dong' + (n.d.hong ? ' hong' : '')
                       + (n.d.viec ? '' : ' view-nk-lang')
                       + (k === sang ? ' dang' : '')
                       + (menu?.n === n ? ' dang-menu' : '')}
            title={tr('Bấm để nhảy tới đây · chuột phải để soi trên sơ đồ')}
            onClick={() => nhay(n.d.t, n.d.ma)}
            onContextMenu={e => {
              e.preventDefault()
              setMenu({ x: e.clientX, y: e.clientY, n })
            }}>
            <span className="view-nk-ngay">{n.d.ngay}</span>
            <span className="view-nk-ma">
              {n.d.soMa > 1 ? tr('{0} mã', n.d.soMa) : n.d.ma}
            </span>
            <span className="view-nk-chu">{n.d.chu}</span>
            {n.dem > 1 && (
              <span className="view-nk-lap"
                    title={tr('{0} nến liền nhau ghi đúng dòng này', n.dem)}>
                ×{n.dem}
              </span>
            )}
            <span className="view-nk-tag">{n.d.tag}</span>
          </button>
        ))}
      </div>

      {menu && (
        <ContextMenu x={menu.x} y={menu.y} onDong={() => setMenu(null)}
          muc={[
            { ten: tr('Nhảy tới đây'),
              onClick: () => nhay(menu.n.d.t, menu.n.d.ma) },
            // Dòng không mang nhãn khối thì không soi được — bày một mục bấm vào
            // chẳng ra gì thì thà đừng bày.
            ...(menu.n.d.tag
              // KHÔNG dùng icon `dau`: trên thanh điều khiển nó đang mang nghĩa
              // «về lệnh trước». Một hình hai nghĩa là hỏng cả hai.
              ? [{ ten: tr('Soi trên sơ đồ'), icon: 'branch',
                   onClick: () => soi(menu.n.d) }]
              : []),
            { ngan: true },
            // Nhật ký là thứ hay phải mang đi hỏi hay đối chiếu. Không chép được thì
            // chỉ còn cách gõ tay lại một dòng mono dài.
            { ten: tr('Chép dòng'), icon: 'copy',
              onClick: () => void navigator.clipboard?.writeText(
                `${menu.n.d.ngay} ${menu.n.d.ma} ${menu.n.d.chu} ${menu.n.d.tag}`.trim()) },
          ]} />
      )}
    </div>
  )
}

export default memo(NhatKy)
