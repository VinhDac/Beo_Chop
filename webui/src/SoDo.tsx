import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background, BackgroundVariant, ConnectionMode, Controls, MarkerType, ReactFlow,
  ReactFlowProvider, SelectionMode, addEdge, useEdgesState, useNodesState,
  type Connection, type Edge as RfEdge, type Node as RfNode,
} from '@xyflow/react'
import { py } from './api'
import StepNode from './components/StepNode'
import DuongVong from './components/DuongVong'
import Ribbon, { type ViecRibbon } from './components/Ribbon'
import TitleBar, { type NhomMenu } from './components/TitleBar'
import KhoDialog from './components/KhoDialog'
import HopKhoa from './qc/HopKhoa'
import type { Card, CoMay, Edge, KetQuaSoat, KhoaQC, Step, StepKind, VanDe } from './types'
import { useKhungCuaSo } from './useKhungCuaSo'

const nodeTypes = { buoc: StepNode }

/** ĐƯỜNG ↻ QUAY LẠI là một LOẠI DÂY RIÊNG, không phải dây thường tô màu khác: bên
 *  Python nó cũng là một loại cạnh riêng (`core.canh_vong`) mà mọi phép đánh số, tìm
 *  điểm bắt đầu và soát nhánh đều bỏ qua. Một khái niệm, hai phía gọi cùng một tên. */
const edgeTypes = { vong: DuongVong }

/** Mũi tên chỉ cần đủ để biết dây chạy về hướng nào. To quá thì nó nặng hơn cả cái
 *  cổng nó cắm vào và hút mắt khỏi nội dung khối. */
const MUI_TEN = { type: MarkerType.ArrowClosed, width: 10, height: 10, color: '#6a6a6a' }

/** Giữ Ctrl HOẶC Shift rồi bấm để chọn thêm khối. Shift cũng là phím quét-khung mặc
 *  định của React Flow, nên Shift+kéo trên nền vẫn quét chọn nhiều khối. */
const PHIM_CHON_NHIEU = ['Control', 'Meta', 'Shift']

/** Khoảng cách đặt khối mới so với khối cuối, khi chưa biết con trỏ ở đâu. */
const BUOC_X = 330

/* ---------- đổi qua lại giữa tài liệu của Python và node/edge của React Flow ---------- */

function docSangRf(steps: Step[], edges: Edge[], the: Record<string, Card>) {
  const nodes: RfNode[] = steps.map((s, i) => ({
    id: s.id,
    type: 'buoc',
    position: { x: s.pos?.[0] ?? 80 + i * BUOC_X, y: s.pos?.[1] ?? 120 },
    data: { step: s, card: the[s.id] },
  }))
  const rf: RfEdge[] = edges.map(e => ({
    id: `${e.from}->${e.to}:${e.port ?? 'out'}`,
    source: e.from,
    target: e.to,
    // Mặc định phải→trái: luồng chạy trái sang phải, nên dây đi ra cạnh phải của hộp
    // trước và vào cạnh trái của hộp sau.
    sourceHandle: e.from_side ?? 'right',
    targetHandle: e.to_side ?? 'left',
    markerEnd: MUI_TEN,
    ...(e.so_vong !== undefined ? { type: 'vong', data: { vong: e.so_vong } } : {}),
  }))
  return { nodes, edges: rf }
}

function rfSangSteps(nodes: RfNode[]): Step[] {
  return nodes.map(n => ({
    ...(n.data as { step: Step }).step,
    pos: [Math.round(n.position.x), Math.round(n.position.y)] as [number, number],
  }))
}

function rfSangEdges(edges: RfEdge[]): Edge[] {
  return edges.map(e => ({
    from: e.source,
    to: e.target,
    port: 'out',
    from_side: e.sourceHandle ?? 'right',
    to_side: e.targetHandle ?? 'left',
    ...(e.type === 'vong'
      ? { so_vong: Number((e.data as { vong?: number } | undefined)?.vong) || 0 }
      : {}),
  }))
}

/* ------------------------------------- App ------------------------------------- */

function SoDoTrong() {
  useKhungCuaSo(32)
  const [nodes, setNodes, onNodesChange] = useNodesState<RfNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<RfEdge>([])
  const [ten, setTen] = useState('')
  const [thuTu, setThuTu] = useState<Record<string, string>>({})
  const [vanDe, setVanDe] = useState<VanDe[]>([])
  const [moKho, setMoKho] = useState(false)
  const [khoa, setKhoa] = useState<KhoaQC | null>(null)
  const [sanSang, setSanSang] = useState(false)
  /** Chồng hoàn tác: ảnh chụp (steps, edges) TRƯỚC mỗi thay đổi có chủ ý. Kéo khối
   *  KHÔNG chụp — kéo chỉ đổi `pos`, mà `pos` không đổi số thứ tự lẫn bảng Vấn đề. */
  const chong = useRef<{ s: Step[]; e: Edge[] }[]>([])
  const chongLai = useRef<{ s: Step[]; e: Edge[] }[]>([])
  const [coHoanTac, setCoHoanTac] = useState(false)
  const [coLamLai, setCoLamLai] = useState(false)

  const dangChon = useMemo(() => nodes.filter(n => n.selected), [nodes])

  const chup = useCallback(() => {
    chong.current.push({ s: rfSangSteps(nodes), e: rfSangEdges(edges) })
    if (chong.current.length > 60) chong.current.shift()
    chongLai.current = []
    setCoHoanTac(true)
    setCoLamLai(false)
  }, [nodes, edges])

  /* ------------------------------------------------------------- soát
     MỘT CỬA DUY NHẤT, gọi sau MỖI thay đổi. Giao diện không tự tính số thứ tự, không
     tự ghép chữ trên thẻ, không tự soát luật nào — nó vẽ lại đúng cái Python trả về.
     Nhờ vậy huy hiệu trên hộp không thể nói khác thứ lõi thật sự hiểu. */
  const van = useRef('')
  useEffect(() => {
    if (!sanSang) return
    const s = rfSangSteps(nodes)
    const e = rfSangEdges(edges)
    // Kéo khối chỉ đổi `pos` -> không phải soát lại. So vân tay BỎ `pos` ra.
    const dau = JSON.stringify([s.map(({ pos: _b, ...x }) => x), e])
    if (dau === van.current) return
    van.current = dau
    let huy = false
    const t = setTimeout(async () => {
      const r = await py.soat(s, e)
      if (huy || !r.ok || !r.value) return
      const kq: KetQuaSoat = r.value
      setThuTu(kq.thu_tu)
      setVanDe(kq.van_de)
      // Thẻ do Python dựng — đổ ngược vào `data` của từng node.
      setNodes(ns => ns.map(n => {
        const c = kq.the[n.id]
        return c && c !== (n.data as { card?: Card }).card
          ? { ...n, data: { ...n.data, card: c } } : n
      }))
    }, 60)
    return () => { huy = true; clearTimeout(t) }
  }, [nodes, edges, sanSang, setNodes])

  /* ------------------------------------------------------------- mở app */
  useEffect(() => {
    (async () => {
      const r = await py.doc_ban_nhap()
      if (r.ok && r.value) nap(r.value)
      setSanSang(true)
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const nap = useCallback(async (doc: CoMay) => {
    const r = await py.soat(doc.steps, doc.edges)
    const the = r.ok && r.value ? r.value.the : {}
    const { nodes: ns, edges: es } = docSangRf(doc.steps, doc.edges, the)
    setNodes(ns)
    setEdges(es)
    setTen(doc.name)
    void py.set_title(doc.name || 'Cỗ máy mới')
  }, [setNodes, setEdges])

  /* ------------------------------------------------- khối đang chọn là Quay về?
     Bấm vào một khối Quay về thì:
       · vẽ ĐƯỜNG ẢO ↻ từ nó về đích — không nằm trong sơ đồ, chỉ hiện lúc bấm;
       · tô sáng MỌI khối nằm trong vòng ấy — nhìn thấy cái vòng, khỏi tự dò theo dây.
     Cả hai chỉ là cách nhìn: không đổi một chữ nào của sơ đồ. */
  const vongDangXem = useMemo(() => {
    const n = dangChon.length === 1 ? dangChon[0] : null
    const st = n && (n.data as { step?: Step }).step
    if (!st || st.type !== 'quay_ve' || !st.ve) return null
    const ke = new Map<string, string[]>()
    for (const e of edges) {
      if (e.type === 'vong') continue
      ke.set(e.source, [...(ke.get(e.source) ?? []), e.target])
    }
    // Đi từ ĐÍCH theo dây thường; mọi khối chạm tới trước khi về lại chính khối Quay
    // về đều nằm trong thân vòng.
    const trong = new Set<string>([st.ve, st.id])
    const hang = [st.ve]
    while (hang.length) {
      const x = hang.shift() as string
      for (const k of ke.get(x) ?? []) {
        if (!trong.has(k)) { trong.add(k); hang.push(k) }
      }
    }
    return { tu: st.id, den: st.ve, so: st.so_vong ?? null, trong }
  }, [dangChon, edges])

  /* --------------------------------------------------- node/edge đem đi vẽ */
  const nodesVe = useMemo(() => nodes.map(n => {
    const st = (n.data as { step?: Step }).step
    const veNhan = st?.type === 'quay_ve' && st.ve ? (thuTu[st.ve] ?? '?') : undefined
    const trongVong = !!vongDangXem?.trong.has(n.id) && n.id !== vongDangXem.tu
    const d = n.data as Record<string, unknown>
    if (d.thuTu === thuTu[n.id] && d.veNhan === veNhan && d.trongVong === trongVong) {
      return n     // `memo` của StepNode so bằng THAM CHIẾU — không đổi thì giữ nguyên
    }
    return { ...n, data: { ...d, thuTu: thuTu[n.id], veNhan, trongVong } }
  }), [nodes, thuTu, vongDangXem])

  const edgesVe = useMemo(() => {
    if (!vongDangXem) return edges
    return [...edges, {
      id: 'ao-vong',
      source: vongDangXem.tu,
      target: vongDangXem.den,
      sourceHandle: 'top',
      targetHandle: 'top',
      type: 'vong',
      data: { vong: vongDangXem.so, ao: true },
      markerEnd: MUI_TEN,
      selectable: false,
    } as RfEdge]
  }, [edges, vongDangXem])

  /* --------------------------------------------------------------- thao tác */
  const onConnect = useCallback((c: Connection) => {
    if (c.source === c.target) return      // tự nối vào chính mình thì vô nghĩa
    chup()
    setEdges(es => addEdge({ ...c, markerEnd: MUI_TEN }, es))
  }, [chup, setEdges])

  const themKhoi = useCallback(async (kind: StepKind, loai?: string) => {
    const r = await py.khoi_moi(kind, loai)
    if (!r.ok || !r.value) return
    chup()
    const { step, card } = r.value
    // KHỐI MỚI rơi cạnh khối cuối, KHÔNG rơi ra ngoài khung nhìn. Bản của Jenifer ghi
    // lại bài học: xếp sang phải khối xa nhất thì tới khối thứ tư, thứ năm là nó rơi
    // hẳn ra ngoài màn — người dùng bấm thêm mà màn hình không đổi gì, tưởng nút hỏng.
    const cuoi = nodes[nodes.length - 1]
    const x = cuoi ? cuoi.position.x + BUOC_X : 80
    const y = cuoi ? cuoi.position.y : 120
    step.pos = [x, y]
    setNodes(ns => [...ns.map(n => ({ ...n, selected: false })),
                    { id: step.id, type: 'buoc', position: { x, y },
                      data: { step, card }, selected: true }])
  }, [chup, nodes, setNodes])

  const xoa = useCallback(() => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    setNodes(ns => ns.filter(n => !bo.has(n.id)))
    setEdges(es => es.filter(e => !bo.has(e.source) && !bo.has(e.target)))
  }, [chup, dangChon, setNodes, setEdges])

  const nhanBan = useCallback(async () => {
    if (!dangChon.length) return
    const bo = new Set(dangChon.map(n => n.id))
    const s = rfSangSteps(dangChon)
    const e = rfSangEdges(edges.filter(x => bo.has(x.source) && bo.has(x.target)))
    const r = await py.nhan_ban(s, e)
    if (!r.ok || !r.value) return
    chup()
    const { steps: ms, edges: me, the } = r.value
    // Bản chép lệch xuống 40px để nhìn thấy ngay là có hai cái, không chồng khít lên
    // bản gốc rồi tưởng bấm hụt.
    const them = ms.map(st => {
      const x = (st.pos?.[0] ?? 80) + 40
      const y = (st.pos?.[1] ?? 120) + 40
      return {
        id: st.id, type: 'buoc', position: { x, y },
        data: { step: { ...st, pos: [x, y] as [number, number] }, card: the[st.id] },
        selected: true,
      } as RfNode
    })
    setNodes(ns => [...ns.map(n => ({ ...n, selected: false })), ...them])
    setEdges(es => [...es, ...docSangRf([], me, {}).edges])
  }, [chup, dangChon, edges, setNodes, setEdges])

  const hoanTac = useCallback(async () => {
    const t = chong.current.pop()
    if (!t) return
    chongLai.current.push({ s: rfSangSteps(nodes), e: rfSangEdges(edges) })
    setCoLamLai(true)
    setCoHoanTac(chong.current.length > 0)
    await nap({ schema: 1, type: 'co_may', name: ten, steps: t.s, edges: t.e })
  }, [nodes, edges, ten, nap])

  const lamLai = useCallback(async () => {
    const t = chongLai.current.pop()
    if (!t) return
    chong.current.push({ s: rfSangSteps(nodes), e: rfSangEdges(edges) })
    setCoHoanTac(true)
    setCoLamLai(chongLai.current.length > 0)
    await nap({ schema: 1, type: 'co_may', name: ten, steps: t.s, edges: t.e })
  }, [nodes, edges, ten, nap])

  /* ------------------------------------------------------------- bản nháp
     Việc đang dở của cửa sổ, kể cả cỗ máy CHƯA TỪNG lưu. Không đụng file cỗ máy nào. */
  useEffect(() => {
    if (!sanSang) return
    const t = setTimeout(() => {
      void py.luu_ban_nhap(ten, rfSangSteps(nodes), rfSangEdges(edges))
    }, 1200)
    return () => clearTimeout(t)
  }, [nodes, edges, ten, sanSang])

  const viec: ViecRibbon = {
    themBatDau: () => void themKhoi('start'),
    themNhom: () => void themKhoi('group'),
    themKhoiLe: () => void themKhoi('action'),
    themQuayVe: () => void themKhoi('action', 'quay_ve'),
    xoa, nhanBan, hoanTac, lamLai,
    luu: () => void luu(),
    mo: () => void mo(),
    moi: () => { chup(); setNodes([]); setEdges([]); setTen('') },
  }

  async function luu() {
    const t = ten || 'Cỗ máy mới'
    const r = await py.luu_co_may(t, rfSangSteps(nodes), rfSangEdges(edges))
    if (r.ok && r.value) { setTen(r.value.ten); void py.set_title(r.value.ten) }
  }

  async function mo() {
    const r = await py.ds_co_may()
    if (!r.ok || !r.value?.length) return
    const d = await py.mo_co_may(r.value[0])
    if (d.ok && d.value) await nap(d.value)
  }

  const soLoi = vanDe.filter(v => v.severity === 'error').length

  const menus: NhomMenu[] = [
    { ten: 'Cat Studio', muc: [
      { ten: 'Khoá QuantConnect…', icon: 'gear',
        onClick: () => { void py.qc_khoa().then(r => setKhoa(r.ok && r.value ? r.value
          : { co: false, nguon: null, user_id: null, duong: '' })) } },
      { ten: 'Kho — app lưu file ở đâu…', icon: 'folder', onClick: () => setMoKho(true) },
      { ngan: true },
      { ten: 'Thoát', onClick: () => { void py.cua_so_dong() } },
    ] },
  ]

  return (
    <div className="khung">
      <TitleBar tieuDe={ten || 'Cỗ máy mới'} menus={menus} />
      <Ribbon v={viec} soChon={dangChon.length}
              coHoanTac={coHoanTac} coLamLai={coLamLai} />
      <div className="vung-canvas">
        <ReactFlow
          nodes={nodesVe} edges={edgesVe}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes} edgeTypes={edgeTypes}
          /* Loose: mỗi cạnh hộp có cả source lẫn target, nối hướng nào cũng được. */
          connectionMode={ConnectionMode.Loose}
          multiSelectionKeyCode={PHIM_CHON_NHIEU}
          selectionMode={SelectionMode.Partial}
          deleteKeyCode={null}
          minZoom={0.05} maxZoom={2}
          proOptions={{ hideAttribution: true }}
          fitView
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
        {nodes.length === 0 && (
          <div className="trong-rong">
            <div className="to">Chưa có khối nào</div>
            <div>Bấm một nút ở thanh trên để thêm khối đầu tiên.</div>
          </div>
        )}
      </div>
      <div className="thanh-trang-thai">
        <span>{nodes.length} khối · {edges.length} dây</span>
        <span className="day" />
        {soLoi > 0 && <span className="loi">{soLoi} lỗi</span>}
        {vanDe.length > soLoi && <span>{vanDe.length - soLoi} cảnh báo</span>}
      </div>

      {moKho && <KhoDialog onDong={() => setMoKho(false)} />}
      {khoa && <HopKhoa khoa={khoa} dong={() => setKhoa(null)} doi={setKhoa} />}
    </div>
  )
}

/** `useReactFlow` chỉ chạy được bên trong Provider — nên App thật nằm ở trong. */
export default function SoDo() {
  return <ReactFlowProvider><SoDoTrong /></ReactFlowProvider>
}
