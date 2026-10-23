import { BaseEdge, EdgeLabelRenderer, useReactFlow, type EdgeProps } from '@xyflow/react'
import { tr } from '../ngon_ngu'

/* ĐƯỜNG ↻ QUAY LẠI — mũi tên ngược về một khối phía trước, tức một vòng lặp trên sơ đồ.
 *
 * VẼ VỒNG LÊN PHÍA TRÊN các khối chứ không luồn giữa chúng: đường quay lại luôn đi
 * ngược chiều dòng chảy, mà vẽ bezier thẳng thì nó ép sát vào hàng khối và trông y hệt
 * một dây thường mắc nhầm. Vồng lên là nhìn một cái biết ngay.
 *
 * Ô SỐ nằm ngay giữa đường: số vòng là thứ duy nhất đường này mang, nên nó phải đọc và
 * sửa được ngay tại chỗ, không phải mở hộp thoại nào.
 *
 * HAI THỨ KHÁC NHAU đi qua cùng thành phần này:
 *   · đường ↻ THẬT — người dùng kéo tay, số vòng nằm trên chính nó, sửa tại chỗ;
 *   · đường ẢO của khối "Quay về" (`ao`) — KHÔNG nằm trong sơ đồ, chỉ hiện ra lúc bấm
 *     vào khối ấy. Số vòng thuộc về KHỐI, nên ở đây chỉ ĐỌC: sửa tại chỗ thì con số
 *     trên đường và con số trong khối bắt đầu trôi khỏi nhau.
 *
 * Chép từ Jenifer_Studio.
 */

/** Vồng cao tối đa bao nhiêu px. Đủ để vượt hẳn hàng khối, chưa đủ để lạc khỏi màn. */
const VONG_TOI_DA = 170

export default function DuongVong({
  id, sourceX, sourceY, targetX, targetY, data, markerEnd, selected,
}: EdgeProps) {
  const { setEdges } = useReactFlow()
  const d_ = data as { vong?: number | null; ao?: boolean } | undefined
  const ao = !!d_?.ao
  const so = Number(d_?.vong ?? 3)

  // Vồng theo KHOẢNG CÁCH hai đầu: hai khối cạnh nhau thì không cần vồng cao, mà vòng
  // ôm cả sơ đồ thì phải vồng cao mới thoát khỏi hàng khối ở giữa.
  const cao = Math.min(VONG_TOI_DA, 70 + Math.abs(sourceX - targetX) * 0.16)
  const c1x = sourceX + 70
  const c2x = targetX - 70
  const c1y = sourceY - cao
  const c2y = targetY - cao
  const d = `M ${sourceX},${sourceY} C ${c1x},${c1y} ${c2x},${c2y} ${targetX},${targetY}`
  // Điểm giữa của đường bậc ba tại t = 0,5 — công thức đúng, không ước lượng bằng mắt.
  const gx = (sourceX + 3 * c1x + 3 * c2x + targetX) / 8
  const gy = (sourceY + 3 * c1y + 3 * c2y + targetY) / 8

  const datSo = (v: string) => {
    const n = Math.max(1, Math.min(99999, parseInt(v.replace(/\D/g, ''), 10) || 1))
    setEdges(es => es.map(e => (e.id === id ? { ...e, data: { ...e.data, vong: n } } : e)))
  }

  return (
    <>
      <BaseEdge id={id} path={d} markerEnd={markerEnd}
                className={'duong-vong' + (selected ? ' chon' : '') + (ao ? ' ao' : '')} />
      <EdgeLabelRenderer>
        <div className={'o-vong nodrag nopan' + (ao ? ' chi-doc' : '')}
             style={{ transform: `translate(-50%, -50%) translate(${gx}px, ${gy}px)` }}>
          <span className="dau">↻</span>
          {ao
            ? <span className="don-vi">{d_?.vong ? tr('{0} vòng', so) : tr('lặp mãi')}</span>
            : <>
                <input value={String(so)} inputMode="numeric"
                       onChange={e => datSo(e.target.value)}
                       title={tr('Số lượt thân vòng chạy')} />
                <span className="don-vi">{tr('vòng')}</span>
              </>}
        </div>
      </EdgeLabelRenderer>
    </>
  )
}
