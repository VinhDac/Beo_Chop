import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background, BackgroundVariant, ConnectionMode, Controls, MarkerType, ReactFlow,
  ReactFlowProvider, SelectionMode, addEdge, useEdgesState, useNodesState, useReactFlow,
  type Connection, type Edge as RfEdge, type Node as RfNode, type Viewport,
} from '@xyflow/react'
import { py } from './api'
import StepNode from './components/StepNode'
import KhoiHatNhan, { type VeThuNho } from './components/HatNhan'
import DuongVong from './components/DuongVong'
import Ribbon, { type ViecRibbon } from './components/Ribbon'
import TitleBar, { type NhomMenu } from './components/TitleBar'
import KhoDialog from './components/KhoDialog'
import HopKhoa from './qc/HopKhoa'
import type {
  Card, CoMay, Edge, HatNhanTag, KetQuaSoat, KhoaQC, Step, StepKind, VanDe,
} from './types'
import { useKhungCuaSo } from './useKhungCuaSo'

const nodeTypes = { buoc: StepNode, hatNhan: KhoiHatNhan }

/** ĐƯỜNG ↻ QUAY LẠI là một LOẠI DÂY RIÊNG, không phải dây thường tô màu khác: bên
 *  Python nó cũng là một loại cạnh riêng (`core.canh_vong`) mà mọi phép đánh số, tìm
 *  điểm bắt đầu và soát nhánh đều bỏ qua. Một khái niệm, hai phía gọi cùng một tên. */
const edgeTypes = { vong: DuongVong }

const MUI_TEN = { type: MarkerType.ArrowClosed, width: 10, height: 10, color: '#6a6a6a' }

/** Giữ Ctrl HOẶC Shift rồi bấm để chọn thêm khối. Shift cũng là phím quét-khung mặc
 *  định của React Flow, nên Shift+kéo trên nền vẫn quét chọn nhiều khối. */
const PHIM_CHON_NHIEU = ['Control', 'Meta', 'Shift']

const BUOC_X = 330
/** Khổ một khối, dùng khi React Flow chưa đo xong. */
const RONG_KHOI = 296
const CAO_KHOI = 150

/** Khổ hình thu nhỏ trong khung hạt nhân = phần trong của `.hn-ve` (app.css):
 *  1184 − 2×12 ngang, 472 − 8 − 4 cao. */
const HN_VE = { w: 1160, h: 460 }

/** Mức zoom ĐỌC RÕ chữ trên thẻ khối: 100%, đúng cỡ thẻ được vẽ ra. */
const ZOOM_DOC_RO = 1
/** Sàn thu nhỏ. Sơ đồ thật đã tới 19.000×16.000px — thấy trọn cần zoom ≈ 4%. Sàn cao
 *  thì "Vừa khung" dừng giữa chừng và không bao giờ thấy hết sơ đồ. */
const ZOOM_SAN = 0.02

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

/* -------------------------------- Hạt nhân -------------------------------- */

interface HatNhan {
  id: string
  ten: string
  khoi: string[]
  /** Khung bao các khối bên trong, toạ độ canvas — bố cục BÊN TRONG. */
  x: number; y: number; w: number; h: number
  /** Chỗ đứng của cái KHUNG ở sơ đồ chính, riêng, không đi theo bố cục bên trong.
   *  `ghim` = đã có chỗ riêng; chưa thì tạm đứng ở góc trên-trái bố cục bên trong. */
  kx: number; ky: number; ghim: boolean
  /** Khối ĐẦU (không có dây thường nào từ bên trong đi vào) và khối CUỐI (không có dây
   *  thường nào đi tiếp vào bên trong). Nối vào hạt nhân = nối vào khối đầu; nối ra từ
   *  nó = nối từ MỌI khối cuối. CẢ HAI ĐỀU SUY RA, không ai khai. */
  vao: string[]
  ra: string[]
}

const tagCua = (n: RfNode) => (n.data as { step?: Step }).step?.hat_nhan
const rongCua = (n: RfNode) => n.measured?.width ?? RONG_KHOI
const caoCua = (n: RfNode) => n.measured?.height ?? CAO_KHOI

/** Tỉ lệ hình thu nhỏ: cả mảng khối quy về khổ `HN_VE`, giữ nguyên tỉ lệ. Vẽ hình và
 *  phóng ra lúc bước vào dùng CHUNG một số — lệch nhau là hình nhảy. */
const tiLeVe = (k: HatNhan) =>
  Math.min(HN_VE.w / Math.max(k.w, 1), HN_VE.h / Math.max(k.h, 1))

/** Lối vào / lối ra của một mảng khối. Dây ↻ không tính: nó là đường quay lại chứ
 *  không phải đường đi tới. Khối Quay về không phải khối cuối — chạy tới nó là nhảy
 *  về, không đi tiếp. */
function loiHatNhan(khoi: Set<string>, nodes: RfNode[], edges: RfEdge[]) {
  const coVao = new Set<string>()
  const coRa = new Set<string>()
  for (const e of edges) {
    if (e.type === 'vong' || !khoi.has(e.source) || !khoi.has(e.target)) continue
    coRa.add(e.source)
    coVao.add(e.target)
  }
  const quayVe = new Set(nodes
    .filter(n => (n.data as { step?: Step }).step?.type === 'quay_ve').map(n => n.id))
  return {
    vao: [...khoi].filter(id => !coVao.has(id)),
    ra: [...khoi].filter(id => !coRa.has(id) && !quayVe.has(id)),
  }
}

/** Gắn (`tag`) hay gỡ (`undefined`) khoá hạt nhân trên một khối. */
function ganTag(n: RfNode, tag: HatNhanTag | undefined): RfNode {
  const d = n.data as { step: Step }
  const st = { ...d.step }
  if (tag) st.hat_nhan = tag
  else delete st.hat_nhan
  return { ...n, data: { ...d, step: st } }
}

const idHatNhanMoi = () =>
  'hn' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)

/* ------------------------------------- App ------------------------------------- */

function SoDoTrong() {
  useKhungCuaSo(32)
  const { fitView, getViewport, setViewport } = useReactFlow()
  const [nodes, setNodes, onNodesChange] = useNodesState<RfNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<RfEdge>([])
  const [ten, setTen] = useState('')
  const [thuTu, setThuTu] = useState<Record<string, string>>({})
  const [vanDe, setVanDe] = useState<VanDe[]>([])
  const [moKho, setMoKho] = useState(false)
  const [khoa, setKhoa] = useState<KhoaQC | null>(null)
  const [sanSang, setSanSang] = useState(false)
  /** Đang đứng TRONG hạt nhân nào; null = sơ đồ chính. */
  const [trongHN, setTrongHN] = useState<string | null>(null)
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
     tự ghép chữ trên thẻ, không tự soát luật nào. */
  const van = useRef('')
  useEffect(() => {
    if (!sanSang) return
    const s = rfSangSteps(nodes)
    const e = rfSangEdges(edges)
    // Kéo khối chỉ đổi `pos`, mà `pos` KHÔNG đổi số thứ tự lẫn bảng Vấn đề -> không
    // phải soát lại. Vân tay bỏ `pos` và `hat_nhan` ra (hạt nhân cũng chỉ là cách nhìn).
    const dau = JSON.stringify([s.map(({ pos: _p, hat_nhan: _h, ...x }) => x), e])
    if (dau === van.current) return
    van.current = dau
    let huy = false
    const t = setTimeout(async () => {
      const r = await py.soat(s, e)
      if (huy || !r.ok || !r.value) return
      const kq: KetQuaSoat = r.value
      setThuTu(kq.thu_tu)
      setVanDe(kq.van_de)
      setNodes(ns => ns.map(n => {
        const c = kq.the[n.id]
        return c && c !== (n.data as { card?: Card }).card
          ? { ...n, data: { ...n.data, card: c } } : n
      }))
    }, 60)
    return () => { huy = true; clearTimeout(t) }
  }, [nodes, edges, sanSang, setNodes])

  const nap = useCallback(async (doc: CoMay) => {
    const r = await py.soat(doc.steps, doc.edges)
    const the = r.ok && r.value ? r.value.the : {}
    const { nodes: ns, edges: es } = docSangRf(doc.steps, doc.edges, the)
    setNodes(ns)
    setEdges(es)
    setTen(doc.name)
    setTrongHN(null)
    void py.set_title(doc.name || 'Cỗ máy mới')
  }, [setNodes, setEdges])

  useEffect(() => {
    (async () => {
      const r = await py.doc_ban_nhap()
      if (r.ok && r.value) await nap(r.value)
      setSanSang(true)
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ------------------------------------------------------------ hạt nhân
     Dựng THẲNG từ khoá trên từng khối, không cất riêng ở đâu: xoá hết khối của nó là
     nó tự mất, không phải dọn bảng nào. */
  const hatNhan = useMemo(() => {
    const m = new Map<string, HatNhan & { x2: number; y2: number }>()
    for (const n of nodes) {
      const t = tagCua(n)
      if (!t?.id) continue
      let k = m.get(t.id)
      if (!k) {
        k = { id: t.id, ten: t.ten, khoi: [], vao: [], ra: [], kx: 0, ky: 0, ghim: false,
              x: Infinity, y: Infinity, w: 0, h: 0, x2: -Infinity, y2: -Infinity }
        m.set(t.id, k)
      }
      if (!k.ghim && typeof t.x === 'number' && typeof t.y === 'number') {
        k.kx = t.x; k.ky = t.y; k.ghim = true
      }
      k.khoi.push(n.id)
      k.x = Math.min(k.x, n.position.x)
      k.y = Math.min(k.y, n.position.y)
      k.x2 = Math.max(k.x2, n.position.x + rongCua(n))
      k.y2 = Math.max(k.y2, n.position.y + caoCua(n))
    }
    const ra = new Map<string, HatNhan>()
    for (const { x2, y2, ...k } of m.values()) {
      ra.set(k.id, { ...k, w: x2 - k.x, h: y2 - k.y,
                     kx: k.ghim ? k.kx : k.x, ky: k.ghim ? k.ky : k.y,
                     ...loiHatNhan(new Set(k.khoi), nodes, edges) })
    }
    return ra
  }, [nodes, edges])

  /** Khối nằm trong hạt nhân nào. Dựng từ một CHUỖI KHOÁ chứ không thẳng từ `hatNhan`:
   *  `hatNhan` đổi theo từng nhịp kéo khối (khung bao dịch đi), mà bảng này thì không —
   *  nó chỉ đổi khi có khối vào / ra hạt nhân. Bám thẳng `hatNhan` là cứ kéo một khối
   *  bất kỳ thì danh sách dây dựng lại 60 lần mỗi giây. */
  const khoaHN = useMemo(() => nodes.filter(n => tagCua(n))
    .map(n => `${n.id}>${tagCua(n)!.id}`).join('|'), [nodes])
  const thuocHN = useMemo(() => new Map(khoaHN ? khoaHN.split('|')
    .map(s => s.split('>') as [string, string]) : []), [khoaHN])

  /** Khối bị GIẤU ở chỗ đang đứng: ở sơ đồ chính là khối trong hạt nhân (cái khung đứng
   *  thay nó), ở trong một hạt nhân là mọi khối khác. */
  const biGiau = useCallback((id: string) =>
    (trongHN ? thuocHN.get(id) !== trongHN : thuocHN.has(id)), [trongHN, thuocHN])

  /** Tag của hạt nhân đang đứng trong — khối mới tạo ở đây thuộc về nó. */
  const tagDangO = useMemo<HatNhanTag | undefined>(() => {
    const k = trongHN ? hatNhan.get(trongHN) : undefined
    return k ? { id: k.id, ten: k.ten, ...(k.ghim ? { x: k.kx, y: k.ky } : {}) } : undefined
  }, [trongHN, hatNhan])

  /** Khung nhìn của sơ đồ chính lúc bước vào — Đóng là về đúng chỗ ấy. */
  const vpChinh = useRef<Viewport | null>(null)

  /** Đổi chỗ đứng. BỎ CHỌN HẾT: khối đang chọn mà bị giấu đi thì Xoá, Nhân bản… ăn vào
   *  thứ không ai nhìn thấy. */
  const doiChoDung = useCallback((hn: string | null) => {
    if (!trongHN && hn) vpChinh.current = getViewport()
    setTrongHN(hn)
    const k = hn ? hatNhan.get(hn) : undefined
    // Bước vào hạt nhân chưa có chỗ đứng riêng thì GHIM khung tại chỗ nó đang đứng
    // trước đã: từ đây sắp lại bên trong không kéo cái khung đi theo.
    const ghim = k && !k.ghim ? { x: Math.round(k.kx), y: Math.round(k.ky) } : null
    setNodes(ds => ds.map(n => {
      const t = ghim ? tagCua(n) : undefined
      const r = t?.id === hn ? ganTag(n, { ...t, ...ghim }) : n
      return r.selected ? { ...r, selected: false } : r
    }))
  }, [trongHN, getViewport, setNodes, hatNhan])

  /** Vào hạt nhân: canvas chỉ còn khối của nó, phóng vừa khít như mở một sơ đồ riêng.
   *
   *  BUNG RA TỪ CHÍNH CÁI KHUNG: trước khi phóng, đặt màn hình sao cho khối thật hiện
   *  ra TRÙNG KHỚP lên hình thu nhỏ trong khung, rồi mới phóng cho vừa — mắt thấy khung
   *  mở bung tại chỗ. Phóng thẳng thì màn hình trượt chéo đi mất. */
  const vaoHatNhan = useCallback((id: string) => {
    const k = hatNhan.get(id)
    if (!k) return
    const ve = document.querySelector(`.react-flow__node[data-id="hn:${id}"] .hn-ve`)
      ?.getBoundingClientRect()
    const nen = document.querySelector('.vung-canvas .react-flow')?.getBoundingClientRect()
    doiChoDung(id)
    if (ve && nen) {
      const z = Math.max(getViewport().zoom * tiLeVe(k), ZOOM_SAN)
      setViewport({ x: ve.left - nen.left + ve.width / 2 - (k.x + k.w / 2) * z,
                    y: ve.top - nen.top + ve.height / 2 - (k.y + k.h / 2) * z, zoom: z })
    }
    // Đợi một nhịp vẽ: khối còn đang giấu thì chưa có gì để căn.
    setTimeout(() => fitView({ nodes: k.khoi.map(x => ({ id: x })), padding: 0.15,
                               maxZoom: ZOOM_DOC_RO, duration: 450 }), 60)
  }, [hatNhan, doiChoDung, fitView, getViewport, setViewport])

  const raHatNhan = useCallback(() => {
    const vp = vpChinh.current
    vpChinh.current = null
    doiChoDung(null)
    if (vp) setViewport(vp, { duration: 300 })
  }, [doiChoDung, setViewport])

  // Hạt nhân đang đứng trong không còn (xoá hết khối của nó, mở cỗ máy khác…) thì tự ra.
  useEffect(() => {
    if (trongHN && !hatNhan.has(trongHN)) raHatNhan()
  }, [trongHN, hatNhan, raHatNhan])

  /** GOM khối đang chọn thành một hạt nhân. */
  const gomHatNhan = useCallback(() => {
    if (dangChon.length < 2) return
    chup()
    const tag: HatNhanTag = { id: idHatNhanMoi(), ten: `Hạt nhân ${hatNhan.size + 1}` }
    const bo = new Set(dangChon.map(n => n.id))
    setNodes(ns => ns.map(n => (bo.has(n.id)
      ? { ...ganTag(n, trongHN ? tagDangO : tag), selected: false } : n)))
  }, [dangChon, chup, hatNhan.size, setNodes, trongHN, tagDangO])

  /** TÁCH: khối đang chọn ra khỏi hạt nhân của chúng. */
  const taHatNhan = useCallback(() => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    setNodes(ns => ns.map(n => (bo.has(n.id) ? ganTag(n, undefined) : n)))
  }, [dangChon, chup, setNodes])

  /* ------------------------------------- khối Quay về đang chọn */
  const vongDangXem = useMemo(() => {
    const n = dangChon.length === 1 ? dangChon[0] : null
    const st = n && (n.data as { step?: Step }).step
    if (!st || st.type !== 'quay_ve' || !st.ve) return null
    const ke = new Map<string, string[]>()
    for (const e of edges) {
      if (e.type === 'vong') continue
      ke.set(e.source, [...(ke.get(e.source) ?? []), e.target])
    }
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

  /* --------------------------------------------------- node đem đi vẽ */
  const nodesHatNhan = useMemo(() => {
    if (trongHN) return []        // đứng trong một hạt nhân thì không vẽ khung nào
    const ra: RfNode[] = []
    const theoId = new Map(nodes.map(n => [n.id, n]))
    for (const k of hatNhan.values()) {
      // HÌNH THU NHỎ: quy cả mảng về khung HN_VE, giữ nguyên tỉ lệ, đặt giữa.
      const s = tiLeVe(k)
      const ox = (HN_VE.w - k.w * s) / 2
      const oy = (HN_VE.h - k.h * s) / 2
      const bo = new Set(k.khoi)
      const o = k.khoi.map(id => {
        const n = theoId.get(id)!
        return { x: ox + (n.position.x - k.x) * s, y: oy + (n.position.y - k.y) * s,
                 w: rongCua(n) * s, h: caoCua(n) * s,
                 mau: (n.data as { step?: Step }).step?.mau }
      })
      const day = edges
        .filter(e => e.type !== 'vong' && bo.has(e.source) && bo.has(e.target))
        .map(e => {
          const a = theoId.get(e.source)!
          const b = theoId.get(e.target)!
          return { x1: ox + (a.position.x + rongCua(a) - k.x) * s,
                   y1: oy + (a.position.y + caoCua(a) / 2 - k.y) * s,
                   x2: ox + (b.position.x - k.x) * s,
                   y2: oy + (b.position.y + caoCua(b) / 2 - k.y) * s }
        })
      // SỐ: khoảng từ khối đầu tới khối cuối — "2 → 2B.1", khối nối sau khung mang đúng
      // số kế tiếp, đọc liền mạch. Không đúng một khối đầu/cuối thì không có khoảng nào
      // để nói, chỉ ghi số đầu.
      const dau = k.vao.length === 1 ? thuTu[k.vao[0]] : undefined
      const cuoi = k.ra.length === 1 ? thuTu[k.ra[0]] : undefined
      const ve: VeThuNho = { ...HN_VE, o, day }
      ra.push({
        id: 'hn:' + k.id, type: 'hatNhan', position: { x: k.kx, y: k.ky }, deletable: false,
        selected: k.khoi.every(id => theoId.get(id)!.selected),
        data: { ten: k.ten, so: k.khoi.length, ve,
                thuTu: dau && cuoi && dau !== cuoi ? `${dau} → ${cuoi}` : dau },
      })
    }
    return ra
  }, [trongHN, hatNhan, nodes, edges, thuTu])

  const nodesVe = useMemo(() => {
    const ds = nodes.filter(n => !biGiau(n.id)).map(n => {
      const st = (n.data as { step?: Step }).step
      const veNhan = st?.type === 'quay_ve' && st.ve ? (thuTu[st.ve] ?? '?') : undefined
      const trongVong = !!vongDangXem?.trong.has(n.id) && n.id !== vongDangXem.tu
      const d = n.data as Record<string, unknown>
      if (d.thuTu === thuTu[n.id] && d.veNhan === veNhan && d.trongVong === trongVong) {
        return n       // `memo` của StepNode so bằng THAM CHIẾU — không đổi thì giữ nguyên
      }
      return { ...n, data: { ...d, thuTu: thuTu[n.id], veNhan, trongVong } }
    })
    return [...ds, ...nodesHatNhan]
  }, [nodes, thuTu, vongDangXem, biGiau, nodesHatNhan])

  /** Dây đem đi vẽ. Ở sơ đồ chính, dây nối tới một khối BỊ GIẤU được cắm vào cái KHUNG
   *  đứng thay nó — nhìn vẫn thấy luồng chạy đi qua hạt nhân. Dây nằm gọn bên trong một
   *  hạt nhân thì bỏ hẳn: nó đã được vẽ thành nét trong hình thu nhỏ. */
  const edgesVe = useMemo(() => {
    const doi = (id: string) => {
      const h = thuocHN.get(id)
      return !trongHN && h ? 'hn:' + h : id
    }
    const thay = new Set<string>()
    const ds: RfEdge[] = []
    for (const e of edges) {
      const a = doi(e.source)
      const b = doi(e.target)
      if (a === b) continue             // dây nằm gọn trong một hạt nhân -> đã vẽ ở hình
      if (trongHN && (thuocHN.get(e.source) !== trongHN
                      || thuocHN.get(e.target) !== trongHN)) {
        continue                        // dây của lớp ngoài: đứng trong thì không thấy
      }
      if (a === e.source && b === e.target) { ds.push(e); continue }
      const id = `${a}->${b}:khung`
      if (thay.has(id)) continue
      thay.add(id)
      ds.push({ ...e, id, source: a, target: b,
                sourceHandle: a.startsWith('hn:') ? 'right' : e.sourceHandle,
                targetHandle: b.startsWith('hn:') ? 'left' : e.targetHandle,
                selectable: false })
    }
    if (vongDangXem) {
      ds.push({ id: 'ao-vong', source: vongDangXem.tu, target: vongDangXem.den,
                sourceHandle: 'top', targetHandle: 'top', type: 'vong',
                data: { vong: vongDangXem.so, ao: true }, markerEnd: MUI_TEN,
                selectable: false } as RfEdge)
    }
    return ds
  }, [edges, thuocHN, trongHN, vongDangXem])

  /* --------------------------------------------------------------- thao tác */
  const onConnect = useCallback((c: Connection) => {
    if (c.source === c.target) return
    if (c.source?.startsWith('hn:') || c.target?.startsWith('hn:')) {
      // Nối vào KHUNG = nối vào khối đầu của nó; nối ra từ khung = nối từ MỌI khối cuối.
      const lay = (id: string, dau: boolean) => {
        const k = hatNhan.get(id.slice(3))
        return k ? (dau ? k.vao : k.ra) : []
      }
      chup()
      const nguon = c.source!.startsWith('hn:') ? lay(c.source!, false) : [c.source!]
      const dich = c.target!.startsWith('hn:') ? lay(c.target!, true) : [c.target!]
      setEdges(es => {
        let r = es
        for (const a of nguon) for (const b of dich) {
          r = addEdge({ source: a, target: b, sourceHandle: 'right', targetHandle: 'left',
                        markerEnd: MUI_TEN }, r)
        }
        return r
      })
      return
    }
    chup()
    setEdges(es => addEdge({ ...c, markerEnd: MUI_TEN }, es))
  }, [chup, setEdges, hatNhan])

  const themKhoi = useCallback(async (kind: StepKind, loai?: string) => {
    const r = await py.khoi_moi(kind, loai)
    if (!r.ok || !r.value) return
    chup()
    const { step, card } = r.value
    // KHỐI MỚI rơi cạnh khối cuối ĐANG NHÌN THẤY, không rơi ra ngoài khung nhìn.
    const thay = nodes.filter(n => !biGiau(n.id))
    const cuoi = thay[thay.length - 1]
    const x = cuoi ? cuoi.position.x + BUOC_X : 80
    const y = cuoi ? cuoi.position.y : 120
    step.pos = [x, y]
    // Thêm lúc đang ở trong một hạt nhân thì nó là một phần của hạt nhân ấy.
    if (tagDangO) step.hat_nhan = tagDangO
    setNodes(ns => [...ns.map(n => ({ ...n, selected: false })),
                    { id: step.id, type: 'buoc', position: { x, y },
                      data: { step, card }, selected: true }])
  }, [chup, nodes, setNodes, biGiau, tagDangO])

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
    const them = ms.map(st => {
      const x = (st.pos?.[0] ?? 80) + 40
      const y = (st.pos?.[1] ?? 120) + 40
      const b = { ...st, pos: [x, y] as [number, number] }
      if (tagDangO) b.hat_nhan = tagDangO
      return { id: st.id, type: 'buoc', position: { x, y },
               data: { step: b, card: the[st.id] }, selected: true } as RfNode
    })
    setNodes(ns => [...ns.map(n => ({ ...n, selected: false })), ...them])
    setEdges(es => [...es, ...docSangRf([], me, {}).edges])
  }, [chup, dangChon, edges, setNodes, setEdges, tagDangO])

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

  /* ------------------------------------------------------------- bản nháp */
  useEffect(() => {
    if (!sanSang) return
    const t = setTimeout(() => {
      void py.luu_ban_nhap(ten, rfSangSteps(nodes), rfSangEdges(edges))
    }, 1200)
    return () => clearTimeout(t)
  }, [nodes, edges, ten, sanSang])

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

  const viec: ViecRibbon = {
    themBatDau: () => void themKhoi('start'),
    themNhom: () => void themKhoi('group'),
    themKhoiLe: () => void themKhoi('action'),
    themQuayVe: () => void themKhoi('action', 'quay_ve'),
    xoa, nhanBan, hoanTac, lamLai,
    gomHatNhan, taHatNhan,
    luu: () => void luu(),
    mo: () => void mo(),
    moi: () => { chup(); setNodes([]); setEdges([]); setTen(''); setTrongHN(null) },
  }

  const soLoi = vanDe.filter(v => v.severity === 'error').length
  const hnDangO = trongHN ? hatNhan.get(trongHN) : undefined

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
      <Ribbon v={viec} soChon={dangChon.length} trongHatNhan={!!trongHN}
              coHoanTac={coHoanTac} coLamLai={coLamLai} />
      <div className="vung-canvas">
        {hnDangO && (
          <div className="thanh-hn">
            <span className="nhan">đang ở trong</span>
            <b>{hnDangO.ten}</b>
            <span className="the">{hnDangO.khoi.length} khối</span>
            <span className="day" />
            <button className="nut nho" onClick={raHatNhan}>Đóng — về sơ đồ chính</button>
          </div>
        )}
        <ReactFlow
          nodes={nodesVe} edges={edgesVe}
          onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeDoubleClick={(_, n) => {
            if (n.id.startsWith('hn:')) vaoHatNhan(n.id.slice(3))
          }}
          nodeTypes={nodeTypes} edgeTypes={edgeTypes}
          /* Loose: mỗi cạnh hộp có cả source lẫn target, nối hướng nào cũng được. */
          connectionMode={ConnectionMode.Loose}
          multiSelectionKeyCode={PHIM_CHON_NHIEU}
          selectionMode={SelectionMode.Partial}
          deleteKeyCode={null}
          minZoom={ZOOM_SAN} maxZoom={2}
          proOptions={{ hideAttribution: true }}
          fitView
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1} />
          <Controls showInteractive={false} />
        </ReactFlow>
        {nodesVe.length === 0 && (
          <div className="trong-rong">
            <div className="to">Chưa có khối nào</div>
            <div>Bấm một nút ở thanh trên để thêm khối đầu tiên.</div>
          </div>
        )}
      </div>
      <div className="thanh-trang-thai">
        <span>{nodes.length} khối · {edges.length} dây</span>
        {hatNhan.size > 0 && <span>{hatNhan.size} hạt nhân</span>}
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
