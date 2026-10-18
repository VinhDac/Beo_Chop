import { Handle, Position, type NodeProps } from '@xyflow/react'

/** KHỐI MỜ của NỐI THÔNG MINH — chép từ `KhoiGoiY` của Jenifer_Studio.
 *
 *  Bước còn thêm được sau khối đang chọn. CHỈ LÀ GỢI Ý: không nằm trong sơ đồ, không
 *  có số, không có cổng kéo dây, không bao giờ được lưu. Bấm vào thì `SoDo` dựng khối
 *  thật ngay chỗ này, tự nối dây từ khối đang chọn, và mở luôn hộp thoại.
 *
 *  Tên `KhoiMo` chứ không `KhoiGoiY`: `KhoiGoiY` trong `types.ts` đã là một thứ khác
 *  (một dòng gợi ý trong ô Tìm khối). Hai thứ cùng tên là hai thứ sẽ bị nhầm.
 *
 *  ⚠ CÚ BẤM NẰM Ở ĐÂY, KHÔNG Ở `onNodeClick`. Bên Jenifer nó nằm ở `onNodeClick` của
 *  React Flow, và chép y thế sang đây thì BẤM KHÔNG RA GÌ — đã dựng lại được bằng tay:
 *  chuột NHẤN XUỐNG làm React Flow bỏ chọn khối đang chọn, khối mờ tính theo khối ấy
 *  nên biến mất ngay trong nhịp vẽ kế, và cú `click` (chỉ bắn sau khi nhả chuột) rơi
 *  vào một nút đã bị gỡ khỏi cây. Lặng hoàn toàn: con trỏ vẫn là bàn tay, bấm vẫn
 *  không ra gì.
 *      Chữa bằng cách chặn ngay từ `mousedown`: `stopPropagation` để React Flow không
 *  coi đây là một cú bấm xuống NỀN (thứ làm bỏ chọn), và dựng khối ngay ở đó luôn —
 *  không chờ `click`. Bấm xuống là có khối, không có nhịp nào để lỡ.
 */
export default function KhoiMo({ data }: NodeProps) {
  const { nhan, onBam } = data as { nhan: string; onBam?: () => void }
  return (
    <>
      {/* Chỉ để dây mờ có chỗ bám — không kéo nối được. */}
      <Handle type="target" id="left" position={Position.Left}
              style={{ opacity: 0, pointerEvents: 'none' }} />
      <div className="khoi-goi-y" title="Bấm để thêm — tự nối dây"
           onMouseDown={e => { e.stopPropagation(); e.preventDefault(); onBam?.() }}
           // Khối mờ không phải một bước: không có menu chuột phải của khối.
           onContextMenu={e => { e.preventDefault(); e.stopPropagation() }}>
        <b>+</b> {nhan}
      </div>
    </>
  )
}
