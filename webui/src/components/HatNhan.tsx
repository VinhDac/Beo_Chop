import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'

/** HẠT NHÂN — một mảng sơ đồ gói lại thành một khung nhỏ cho dễ nhìn.
 *
 *  CHỈ LÀ CÁCH NHÌN. Các khối bên trong vẫn là khối thật, dây vẫn là dây thật; bộ chạy,
 *  số thứ tự, bảng Vấn đề không biết gì về hạt nhân. Khung này do `SoDo.nodesHatNhan`
 *  dựng ra để vẽ, không nằm trong `nodes`, không lưu ra file. Bấm đúp là bước VÀO bên
 *  trong — canvas chỉ còn các khối của nó, như một sơ đồ riêng.
 *
 *  Vì sao nó phải có: một sơ đồ thật đã đo được 1.170 khối trên canvas 19.000×16.000.
 *  Không có cách gói lại thì không ai vẽ nổi tới đó.
 *
 *  Chép từ Jenifer_Studio.
 */

/** Hình thu nhỏ của sơ đồ bên trong: mỗi khối một ô, mỗi dây một nét. Toạ độ đã quy về
 *  khung `w` × `h` ở phía SoDo. */
export interface VeThuNho {
  w: number
  h: number
  o: { x: number; y: number; w: number; h: number; mau?: string }[]
  day: { x1: number; y1: number; x2: number; y2: number }[]
}

export interface DuLieuHatNhan {
  ten: string
  /** Số khối bên trong. */
  so: number
  /** Số của khối đầu → số của khối cuối — hạt nhân chiếm khúc nào trên dòng chạy. */
  thuTu?: string
  ve: VeThuNho
  /** Ô tìm: bên trong có khối khớp. */
  timThay?: boolean
}

/* Hai cạnh trái/phải, mỗi cạnh có CẢ source LẪN target — cùng lẽ với `StepNode`: thiếu
   target trùng id thì React Flow không phân giải nổi đầu đích của một dây đã có. */
const CANH: [string, Position][] = [['left', Position.Left], ['right', Position.Right]]

function KhoiHatNhan({ data, selected }: NodeProps) {
  const d = data as unknown as DuLieuHatNhan
  return (
    <>
      {CANH.map(([id, pos]) => <Handle key={id} type="source" id={id} position={pos} />)}
      {CANH.map(([id, pos]) => (
        <Handle key={'t-' + id} type="target" id={id} position={pos}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}
      <div className={'hop hat-nhan' + (selected ? ' dang-chon' : '')
                      + (d.timThay ? ' tim-thay' : '')}
           title="Bấm đúp để vào bên trong sửa">
        <div className={'so-thu-tu' + (d.thuTu ? '' : ' trong')}>{d.thuTu ?? '–'}</div>
        <div className="dau">
          <span className="dai-mau" />
          <span className="ten" title={d.ten}>{d.ten}</span>
          <span className="loai">Hạt nhân</span>
        </div>
        <svg className="hn-ve" viewBox={`0 0 ${d.ve.w} ${d.ve.h}`} aria-hidden>
          {d.ve.day.map((l, i) => (
            <line key={i} x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} />
          ))}
          {d.ve.o.map((o, i) => (
            <rect key={i} x={o.x} y={o.y} width={o.w} height={o.h} rx={2}
                  style={o.mau ? { fill: o.mau } : undefined} />
          ))}
        </svg>
        <div className="chan">
          <span className="the">{d.so} khối</span>
          <span className="hn-goi-y">bấm đúp để vào sửa</span>
        </div>
      </div>
    </>
  )
}

export default memo(KhoiHatNhan)
