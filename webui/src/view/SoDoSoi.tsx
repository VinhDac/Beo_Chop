/* POPUP SOI SƠ ĐỒ — ngay trong cửa sổ View.
 *
 * ⚠ VÌ SAO KHÔNG NHẢY SANG CỬA SỔ CHÍNH. `soi_luot` làm đúng thế, và nó vẫn còn: ghim
 * một lệnh lên CÁI SƠ ĐỒ ĐANG VẼ là việc của người sắp sửa sơ đồ. Nhưng lúc đang tua
 * một lượt chạy thì câu hỏi khác: «dòng này đi qua đâu» — hỏi xong là tua tiếp. Nhảy
 * cửa sổ thì mất chỗ đang xem, phải tìm lại cửa sổ View, tìm lại nhịp. Popup trả lời
 * ngay trong tầm mắt rồi tắt bằng Esc.
 *
 * ⚠ VÀ NÓ VẼ SƠ ĐỒ CỦA LƯỢT CHẠY, KHÔNG PHẢI SƠ ĐỒ ĐANG VẼ. Người ta mở lại một lượt
 * tuần trước, mà tuần này sơ đồ đã sửa ba lần — soi vào bản đang vẽ thì vệt sáng chạy
 * trên một cỗ máy khác hẳn cái đã sinh ra mấy cái lệnh ấy. `chay_lean` chụp sơ đồ
 * ngay lúc khởi động mỗi lượt (`TEN_SO_DO`), nên bản này là bản đúng. Lượt chạy từ
 * trước khi có bản chụp thì phải dò ngược từ tên lớp, và cửa sổ NÓI RA chuyện đó.
 *
 * ⚠ MẶT KHỐI LẤY NGUYÊN `Card` CỦA PYTHON, y như `StepNode` của Xưởng và `KhoiChay`
 * của màn Chạy máy: cùng `card.title`, `card.lines`, `card.badges`, cùng `DongChu` để
 * tô, cùng mấy lớp `.hop .dau .than`. Không một dòng chữ nào ghép lại ở đây — ghép là
 * bản sự thật thứ hai, và hôm nào mặt khối ở Xưởng nói khác mặt khối trong popup thì
 * không ai biết bên nào đúng.
 */
import { memo, useEffect, useMemo, useState } from 'react'
import {
  BaseEdge, Background, BackgroundVariant, Handle, Position, ReactFlow,
  ReactFlowProvider, getBezierPath,
  type EdgeProps, type NodeProps,
} from '@xyflow/react'
import Icon from '../components/Icon'
import { DongChu } from '../components/StepNode'
import { py } from '../api'
import { tr } from '../ngon_ngu'
import type { Card, SoDoSoiDL } from '../types'
import { doDuong, idDay, soKhoiCuaNhan } from '../man/mach_chay'

/* ------------------------------- một KHỐI ---------------------------------- */

function KhoiSoiTrong({ data }: NodeProps) {
  const card = (data as { card: Card }).card
  const thuTu = (data as { thuTu?: string }).thuTu
  const tren = !!(data as { tren?: boolean }).tren

  return (
    <div className={'hop vs-khoi' + (tren ? ' vs-khoi-tren' : ' soi-mo')}>
      {/* Bốn cổng ở giữa bốn cạnh, cùng khuôn với `StepNode`: dây bám đúng cạnh nó
          đã bám ở Xưởng. Không bắt chuột — popup này không nối dây. */}
      {([['top', Position.Top], ['right', Position.Right],
         ['bottom', Position.Bottom], ['left', Position.Left]] as const).map(([k, p]) => (
        <Handle key={k} type="source" id={k} position={p}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}
      {([['top', Position.Top], ['right', Position.Right],
         ['bottom', Position.Bottom], ['left', Position.Left]] as const).map(([k, p]) => (
        <Handle key={'t-' + k} type="target" id={k} position={p}
                style={{ opacity: 0, pointerEvents: 'none' }} />
      ))}

      <div className={'so-thu-tu' + (thuTu ? '' : ' trong')}>{thuTu || '–'}</div>
      <div className="dau"><span className="ten" title={card.title}>{card.title}</span></div>
      {card.lines.length > 0 && (
        <div className="than">
          {card.lines.map((d, i) => (
            <div key={i} className="dong" title={d.text}>
              <span className="danh">{card.kind === 'group' ? '·' : ''}</span>
              <Icon name={d.icon ?? ''} size={12} />
              <span><DongChu text={d.text} num={d.num} net={d.net} tim="" /></span>
            </div>
          ))}
        </div>
      )}
      {card.badges.length > 0 && (
        <div className="chan">
          {card.badges.map((b, i) => <span key={i} className="the">{b}</span>)}
        </div>
      )}
    </div>
  )
}

const KhoiSoi = memo(KhoiSoiTrong)

/* -------------------------------- một DÂY ---------------------------------- */

/** ⚠ HAI ĐƯỜNG CHỒNG NHAU, không phải một — cùng lý do với `DayDien` của màn Chạy
 *  máy. Một đường không thể vừa là sợi dây vừa là vệt sáng chạy trên nó: muốn vệt
 *  sáng thì phải `stroke-dasharray`, mà đặt lên chính sợi dây thì gần hết sợi dây
 *  thành KHOẢNG TRỐNG — mấy cái khối rời nhau với mẩu dây cụt 8 pixel. */
function DaySoi({ id, data, sourceX, sourceY, targetX, targetY, sourcePosition,
                  targetPosition, markerEnd }: EdgeProps) {
  const [d] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY,
                              targetPosition })
  const tren = !!(data as { tren?: boolean } | undefined)?.tren
  return (
    <>
      <BaseEdge id={id} path={d} markerEnd={markerEnd}
                className={'day-nen' + (tren ? '' : ' soi-mo')} />
      {tren && <path className="day-dong" d={d} />}
    </>
  )
}

const nodeTypes = { soi: KhoiSoi }
const edgeTypes = { soi: DaySoi }
const VUA_KHUNG = { padding: 0.18, maxZoom: 1 }

/* --------------------------------- popup ----------------------------------- */

export interface SoDoSoiProps {
  /** Nhãn khối của dòng đang soi — `[1A] RSI(14) < 30`, hay `[1A]` với dòng tường
   *  thuật. Số khối trong ngoặc là tất cả những gì cần để dò đường. */
  nhan: string
  /** Chữ của dòng nhật ký, bày trên dải tiêu đề: popup phải tự nói nó đang soi cái gì
   *  — nhãn khối một mình thì đọc ra số với điều kiện, không ra «▲ Market 121,78». */
  chu: string
  onDong: () => void
}

export default function SoDoSoi(p: SoDoSoiProps) {
  return <ReactFlowProvider><Trong {...p} /></ReactFlowProvider>
}

function Trong({ nhan, chu, onDong }: SoDoSoiProps) {
  const [dl, setDl] = useState<SoDoSoiDL | null>(null)
  const [loi, setLoi] = useState('')

  /* HỎI MỘT LẦN, lúc popup mở. Không nạp sẵn lúc mở cửa sổ: phần lớn lượt xem không
     ai bấm soi, mà sơ đồ cộng bản soát là một cú gọi cầu nối không nhỏ. */
  useEffect(() => {
    void (async () => {
      const r = await py.so_do_soi()
      if (r.ok && r.value) setDl(r.value)
      else setLoi(r.error ?? tr('không mở được sơ đồ của lượt này'))
    })()
  }, [])

  /* Esc tắt popup — đường thoát thấy được là nút ✕, phím chỉ là lối tắt. */
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); onDong() } }
    window.addEventListener('keydown', f, true)
    return () => window.removeEventListener('keydown', f, true)
  }, [onDong])

  /** ĐƯỜNG TỪ KHỐI BẮT ĐẦU TỚI KHỐI CỦA NHÃN — dùng CHÍNH `doDuong` của màn Chạy máy.
   *
   *  ⚠ KHÔNG DÒ LẠI Ở ĐÂY. Luật này có hai chỗ tinh dễ sót (bỏ đường ↻, chặn vòng
   *  bằng số khối), và bản chép sót một trong hai thì vệt sáng chạy lùi, hoặc treo
   *  cửa sổ — xem lời dặn ở `mach_chay.doDuong`. */
  const soi = useMemo(() => {
    if (!dl) return null
    const { theoSo, duong } = doDuong(dl.soat)
    const id = theoSo.get(soKhoiCuaNhan(nhan))
    if (!id) return { nut: new Set<string>(), day: new Set<string>(), lech: true }
    const d = duong(id)
    return { nut: new Set(d.nut), day: new Set(d.day), lech: false }
  }, [dl, nhan])

  const nodes = useMemo(() => {
    if (!dl || !soi) return []
    const the = dl.soat.the ?? {}
    const thuTu = dl.soat.thu_tu ?? {}
    return dl.steps.filter(s => the[s.id]).map((s, k) => ({
      id: s.id, type: 'soi',
      position: { x: s.pos?.[0] ?? 80 + k * 330, y: s.pos?.[1] ?? 120 },
      data: { card: the[s.id], thuTu: thuTu[s.id], tren: soi.nut.has(s.id) },
      selectable: false, draggable: false, connectable: false, deletable: false,
    }))
  }, [dl, soi])

  const edges = useMemo(() => {
    if (!dl || !soi) return []
    // ĐƯỜNG ↻ KHÔNG VẼ, y màn Chạy máy: nó là đường quay lại, mà bộ sinh mã còn
    // chưa sinh nổi khối Quay về — `doDuong` cũng đã bỏ nó khỏi phép dò đường, nên
    // vẽ ra đây là vẽ một sợi dây không bao giờ sáng.
    return (dl.soat.edges ?? []).filter(e => !('so_vong' in e)).map(e => {
      const id = idDay(e)
      return { id, source: e.from, target: e.to, type: 'soi',
               sourceHandle: e.from_side ?? 'right', targetHandle: e.to_side ?? 'left',
               data: { tren: soi.day.has(id) } }
    })
  }, [dl, soi])

  return (
    <div className="vs-nen" onMouseDown={e => { if (e.target === e.currentTarget) onDong() }}>
      <div className="vs-khung">
        <div className="vs-dai">
          <span className="soi-nhan">{tr('SOI LƯỢT')}</span>
          {/* Dòng tường thuật đã mang sẵn số khối trong câu («dòng dừng ở 1C»), nên
              dán thêm `[1C]` vào sau là đọc hai lần một thứ. Dòng lệnh thì ngược lại:
              chữ của nó nói về tiền, nhãn khối mới nói nó ra từ đâu. */}
          <span className="soi-chu">
            {chu}{chu.includes(soKhoiCuaNhan(nhan)) ? '' : ` · ${nhan}`}
          </span>
          {soi?.lech && (
            <span className="soi-canh">
              {tr('nhãn này không khớp khối nào trên sơ đồ')}
            </span>
          )}
          {dl && !dl.chup && (
            <span className="soi-canh">
              {tr('lượt cũ không lưu sơ đồ — đây là bản dò từ kho, có thể đã sửa')}
            </span>
          )}
          <button className="soi-tat" title={tr('Tắt (Esc)')} onClick={onDong}>✕</button>
        </div>
        <div className="vs-san">
          {loi && <div className="mc-bao loi kq-loi">⚠ {loi}</div>}
          {!dl && !loi && <div className="view-trong">{tr('đang mở sơ đồ…')}</div>}
          {dl && (
            <ReactFlow nodes={nodes} edges={edges}
                       nodeTypes={nodeTypes} edgeTypes={edgeTypes}
                       fitView fitViewOptions={VUA_KHUNG}
                       nodesDraggable={false} nodesConnectable={false}
                       elementsSelectable={false} panOnDrag zoomOnScroll
                       proOptions={{ hideAttribution: true }}>
              <Background variant={BackgroundVariant.Dots} gap={22} size={1} />
            </ReactFlow>
          )}
        </div>
      </div>
    </div>
  )
}
