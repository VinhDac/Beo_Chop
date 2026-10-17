import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background, BackgroundVariant, ConnectionMode, MarkerType, ReactFlow,
  ReactFlowProvider, SelectionMode, addEdge, useEdgesState, useNodesState, useReactFlow,
  useStore,
  type Connection, type Edge as RfEdge, type Node as RfNode, type Viewport,
} from '@xyflow/react'
import { cho_cau_noi, py } from './api'
import StepNode from './components/StepNode'
import KhoiHatNhan, { type VeThuNho } from './components/HatNhan'
import DuongVong from './components/DuongVong'
import Ribbon, { type ViecRibbon } from './components/Ribbon'
import OTimKhoi, { type LocTim } from './components/OTimKhoi'
import ContextMenu, { type MucPhai } from './components/ContextMenu'
import BangPhimTat from './components/BangPhimTat'
import HopDoiTen from './components/HopDoiTen'
import BangDuoi, { type TabDuoi } from './components/BangDuoi'
import KhoStrategy from './components/KhoStrategy'
import HopDieuKien from './components/HopDieuKien'
import HopHanhDong, { laHanhDong } from './components/HopHanhDong'
import HopBatDau from './components/HopBatDau'
import HopSinhMa from './components/HopSinhMa'
import HopKetQua from './components/HopKetQua'
import HopNhom from './components/HopNhom'
import HopTienDo from './components/HopTienDo'
import Icon from './components/Icon'
import HopCaiDat from './components/HopCaiDat'
import HopKhoLuot from './components/HopKhoLuot'
import HopHoi, { bao, nhapChu } from './components/Hoi'
import TitleBar, { type NhomMenu } from './components/TitleBar'
import KhoDialog from './components/KhoDialog'
import HopKhoa from './qc/HopKhoa'
import type {
  Card, Edge, HatNhanTag, KetQuaSoat, KhoaQC, Step, StepKind, Strategy, TuDienHoi,
  KetQuaChay, KetQuaSinh, TienDoChay, TuDienBatDau, TuDienLam, VanDe,
} from './types'
import { khoiKhop } from './tim'
import { bangTra, chuPhim, cumPhim, LENH } from './phim_tat'

const nodeTypes = { buoc: StepNode, hatNhan: KhoiHatNhan }

/** ĐƯỜNG ↻ QUAY LẠI là một LOẠI DÂY RIÊNG, không phải dây thường tô màu khác: bên
 *  Python nó cũng là một loại cạnh riêng (`core.canh_vong`) mà mọi phép đánh số, tìm
 *  điểm bắt đầu và soát nhánh đều bỏ qua. Một khái niệm, hai phía gọi cùng một tên. */
const edgeTypes = { vong: DuongVong }

const MUI_TEN = { type: MarkerType.ArrowClosed, width: 10, height: 10, color: '#6a6a6a' }

/** Giữ Ctrl HOẶC Shift rồi bấm để chọn thêm khối. Shift cũng là phím quét-khung mặc
 *  định của React Flow, nên Shift+kéo trên nền vẫn quét chọn nhiều khối. */
const PHIM_CHON_NHIEU = ['Control', 'Meta', 'Shift']

/** Màu khối người dùng tự đặt. Tên tiếng Việt, màu lấy từ `theme.css` — đổi tông app
 *  là màu khối đổi theo, không đóng đinh mã màu vào đây. Bộ chạy KHÔNG đọc màu. */
const MAU_KHOI: [string, string][] = [
  ['Đỏ', '--khoi-do'], ['Cam', '--khoi-cam'], ['Vàng', '--khoi-vang'],
  ['Lục', '--khoi-luc'], ['Lam', '--khoi-lam'], ['Tím', '--khoi-tim'],
]

/** Phím tắt -> mã lệnh. Tra BẢNG theo đúng cụm đang bấm, không phải chuỗi `else if`. */
const TRA_PHIM = bangTra()
/** Nhãn phím của một lệnh, để hiện mờ bên phải menu chuột phải. */
const phimCua = (ma: string) => {
  const l = LENH.find(x => x.ma === ma)
  return l?.phim[0] ? chuPhim(l.phim[0]) : undefined
}

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
  // (bộ bắt kéo cửa sổ nay nằm trong chính `TitleBar` — xem chú thích ở đó)
  const { fitView, getViewport, setViewport, setCenter, zoomIn, zoomOut } = useReactFlow()
  /** Mức phóng hiện tại — đọc thẳng từ kho của React Flow nên con số không bao giờ
   *  trôi khỏi thứ đang hiện trên màn. */
  const mucZoom = useStore(st => st.transform[2])
  const [nodes, setNodes, onNodesChange] = useNodesState<RfNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<RfEdge>([])
  const [ten, setTen] = useState('')
  const [thuTu, setThuTu] = useState<Record<string, string>>({})
  const [vanDe, setVanDe] = useState<VanDe[]>([])
  const [moKho, setMoKho] = useState(false)
  /** Kho Strategy — hộp chọn file đã lưu. */
  const [moKhoStrategy, setMoKhoStrategy] = useState(false)
  /** Từ điển XÁC NHẬN, hỏi Python một lần lúc mở app. */
  const [tuDien, setTuDien] = useState<TuDienHoi | null>(null)
  /** Từ điển HÀNH ĐỘNG, hỏi Python một lần lúc mở app. */
  const [tuDienLam, setTuDienLam] = useState<TuDienLam | null>(null)
  /** Từ điển KHỐI BẮT ĐẦU — sáu ô thiết lập. */
  const [tuDienBD, setTuDienBD] = useState<TuDienBatDau | null>(null)
  /** Mã LEAN vừa sinh — null = chưa mở hộp. */
  const [maSinh, setMaSinh] = useState<KetQuaSinh | null>(null)

  /** Khối này có hộp sửa không.
   *
   *  MỘT bản dùng cho CẢ bấm đúp lẫn menu chuột phải — hai lối vào phải nhất trí,
   *  không thì một lối mở được còn lối kia im lặng mà chẳng ai hiểu vì sao.
   *
   *  Và nó kiểm luôn TỪ ĐIỂN ĐÃ NẠP CHƯA: thiếu từ điển thì menu hiện mục ấy mờ đi
   *  kèm lý do, thay vì bấm vào mà không ra gì. */
  const coHopSua = useCallback((st?: Step) => !!st && (
    (st.kind === 'start' && !!tuDienBD)
    || (st.kind === 'group' && !!tuDienLam && !!tuDien)
    || !!tuDien?.loai.some(l => l.ma === st.type)
    || (!!tuDien && laHanhDong(tuDienLam, st.type))
  ), [tuDien, tuDienLam, tuDienBD])

  /** VÌ SAO khối này chưa sửa được — nói rõ THIẾU GÌ, không nói chung chung.
   *
   *  ⚠ Bản trước ghi mỗi câu "Khối này chưa có hộp sửa" cho mọi trường hợp. Lúc một
   *  từ điển không nạp được thì mục menu vẫn mờ đúng câu ấy, và nhìn y như "khối này
   *  vốn không sửa được" — hai chuyện khác hẳn nhau, mà người dùng không có cách nào
   *  phân biệt. Đã mất một lượt hỏi đi hỏi lại vì câu chữ ấy. */
  const viSaoKhongSua = useCallback((st?: Step) => {
    if (!st) return 'Không đọc được khối này'
    const thieu = (ten: string) =>
      `Chưa nạp được từ điển ${ten} — mở lại app một lần. Còn lỗi thì xem Nhật ký.`
    if (st.kind === 'start') return tuDienBD ? '' : thieu('BẮT ĐẦU')
    if (st.kind === 'group') {
      return tuDienLam && tuDien ? '' : thieu(tuDienLam ? 'XÁC NHẬN' : 'HÀNH ĐỘNG')
    }
    if (st.type === 'quay_ve') return 'Khối Quay về chưa có hộp sửa — dùng Nối tới…'
    if (!tuDien) return thieu('XÁC NHẬN')
    if (!tuDienLam) return thieu('HÀNH ĐỘNG')
    return `Khối loại "${st.type ?? '?'}" chưa có hộp sửa`
  }, [tuDien, tuDienLam, tuDienBD])
  /** Kết quả lượt backtest vừa chạy — giữ lại để mở lại được sau khi đóng. */
  const [ketQua, setKetQua] = useState<KetQuaChay | null>(null)
  const [moKetQua, setMoKetQua] = useState(false)
  const [dangChay, setDangChay] = useState(false)
  /** Tiến độ lượt backtest đang chạy — null = không hiện hộp. */
  const [tienDo, setTienDo] = useState<TienDoChay | null>(null)
  const [moCaiDat, setMoCaiDat] = useState(false)
  /** Kho LƯỢT BACKTEST — khác `moKho` phía trên, cái ấy là kho Strategy. */
  const [moKhoLuot, setMoKhoLuot] = useState(false)
  /** Id khối đang mở hộp thoại điều kiện. */
  const [dangSua, setDangSua] = useState<string | null>(null)
  const [khoa, setKhoa] = useState<KhoaQC | null>(null)
  const [sanSang, setSanSang] = useState(false)
  /** Đang đứng TRONG hạt nhân nào; null = sơ đồ chính. */
  const [trongHN, setTrongHN] = useState<string | null>(null)
  /** Ô tìm khối: chữ đang gõ, lọc nhanh đang bật, và đang đứng ở khối khớp thứ mấy. */
  const [tim, setTim] = useState('')
  const [locTim, setLocTim] = useState<string | null>(null)
  const [dangO, setDangO] = useState(-1)
  /** Menu chuột phải: bấm ở đâu, và bấm trúng cái gì. */
  const [menuPhai, setMenuPhai] = useState<
    { x: number; y: number; loai: 'nen' | 'khoi' | 'hatNhan'; id?: string } | null>(null)
  const [moBangPhim, setMoBangPhim] = useState(false)
  const [doiTen, setDoiTen] = useState<{ loai: 'khoi' | 'hatNhan'; id: string;
                                         ten: string } | null>(null)
  /** Bảng dưới: tab nào, cao bao nhiêu, đang gập không. Mở app ra là GẬP. */
  const [tab, setTab] = useState('van-de')
  const [panelCao, setPanelCao] = useState(176)
  const [panelGap, setPanelGap] = useState(true)
  /** NHẬT KÝ của app — việc vừa làm, không phải việc chạy trên QuantConnect.
   *  Chưa có đường chạy (D-11), nên đây là nơi duy nhất nói "vừa xảy ra gì". */
  const [nhatKy, setNhatKy] = useState<{ gio: string; chu: string }[]>([])
  const ghi = useCallback((chu: string) => {
    const gio = new Date().toLocaleTimeString('vi-VN', { hour12: false })
    // Giữ 300 dòng gần nhất: dài hơn thì cuộn không ra gì mà ăn bộ nhớ.
    setNhatKy(ds => [...ds, { gio, chu }].slice(-300))
  }, [])
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
  /** Hẹn giờ và SỐ LƯỢT của phép soát — xem chú thích trong hiệu ứng soát. */
  const henSoat = useRef<number | undefined>(undefined)
  const luotSoat = useRef(0)
  useEffect(() => {
    if (!sanSang) return
    const s = rfSangSteps(nodes)
    const e = rfSangEdges(edges)
    // Kéo khối chỉ đổi `pos`, mà `pos` KHÔNG đổi số thứ tự lẫn bảng Vấn đề -> không
    // phải soát lại. Vân tay bỏ `pos` và `hat_nhan` ra (hạt nhân cũng chỉ là cách nhìn).
    const dau = JSON.stringify([s.map(({ pos: _p, hat_nhan: _h, ...x }) => x), e])
    if (dau === van.current) return
    van.current = dau
    /* ⚠ KHÔNG dọn bằng hàm trả về của effect, và đây là một cuộc đua ĐÃ CẮN THẬT.
     *
     * Bản trước `return () => { huy = true; clearTimeout(t) }`. React chạy hàm dọn ấy
     * TRƯỚC MỖI LẦN effect chạy lại — kể cả lần chạy lại không đổi gì. Nên chỉ cần
     * một lượt vẽ lại bất kỳ rơi vào 60ms đang chờ (lượt tự lưu vừa trả lời, một dòng
     * nhật ký mới…) là: dọn huỷ mất lượt soát đang hẹn, rồi effect thấy vân tay y
     * nguyên nên thoát sớm — KHÔNG hẹn lại. Lượt soát biến mất không dấu vết.
     *
     * Hậu quả im lặng: khối vừa dựng mang số "–" mãi, bảng Vấn đề đứng ở lượt cũ.
     * Bắt được lúc thử Ctrl+G: Nhóm mới gom xong không có số, mà thêm đại một khối
     * rồi Ctrl+Z là số hiện ra đủ — tức mô hình vẫn đúng, chỉ lượt soát bị nuốt.
     *
     * Nay giữ hẹn trong `ref` và chỉ huỷ khi thật sự có lượt mới; kết quả cũ bị bỏ
     * bằng số lượt, không bằng cờ của một closure đã chết. */
    const toi = ++luotSoat.current
    clearTimeout(henSoat.current)
    henSoat.current = window.setTimeout(async () => {
      const r = await py.soat(s, e)
      if (toi !== luotSoat.current || !r.ok || !r.value) return
      const kq: KetQuaSoat = r.value
      setThuTu(kq.thu_tu)
      setVanDe(kq.van_de)
      setNodes(ns => ns.map(n => {
        const c = kq.the[n.id]
        return c && c !== (n.data as { card?: Card }).card
          ? { ...n, data: { ...n.data, card: c } } : n
      }))
    }, 60)
  }, [nodes, edges, sanSang, setNodes])

  // Đóng cửa sổ giữa lúc đang hẹn thì bỏ hẹn — chỉ ở đây mới đúng là "dọn".
  useEffect(() => () => clearTimeout(henSoat.current), [])

  const nap = useCallback(async (doc: Strategy) => {
    const r = await py.soat(doc.steps, doc.edges)
    const the = r.ok && r.value ? r.value.the : {}
    // ⚠ Lượt soát này đã có SẴN số thứ tự và bảng Vấn đề — lấy luôn. Bản trước chỉ
    // nhặt mỗi `the` rồi để hiệu ứng soát lại một lượt nữa: thừa một vòng gọi, mà
    // giữa hai lượt thì mọi khối hiện số "–" như sơ đồ chưa đánh số được.
    if (r.ok && r.value) {
      setThuTu(r.value.thu_tu)
      setVanDe(r.value.van_de)
    }
    const { nodes: ns, edges: es } = docSangRf(doc.steps, doc.edges, the)
    setNodes(ns)
    setEdges(es)
    setTen(doc.name)
    setTrongHN(null)
    void py.set_title(doc.name || 'Strategy mới')
  }, [setNodes, setEdges])

  useEffect(() => {
    (async () => {
      /* ⚠ CHỜ CẦU NỐI XONG RỒI MỚI HỎI PYTHON.
       *
       * pywebview dựng sẵn `window.pywebview.api = {}` — RỖNG nhưng TRUTHY — ngay
       * khung hình đầu tiên, rồi mới đổ hàm vào sau. Hỏi sớm một nhịp là cả ba từ
       * điển cùng trượt, «api.py không có hàm tu_dien_hoi», và suốt lượt chạy ấy
       * mọi khối mất hộp sửa. Bản nháp cũng không mở lên được.
       *
       * `cho_cau_noi` viết ra chính vì chuyện này — nhưng KHÔNG CHỖ NÀO GỌI nó, nên
       * cái bẫy nó canh vẫn sập. Một hàng rào không ai đứng gác thì không phải hàng
       * rào. `test_giao_dien` nay bắt cửa chết trong `api.ts` để khỏi lặp lại.
       *
       * Chờ rộng tay 30 giây: máy chậm, lần chạy đầu sau khi build, LEAN đang bận —
       * thà đợi thêm còn hơn báo hỏng oan rồi tự què cả app. */
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        await bao({ loi: 'Không kết nối được tới Python sau 30 giây. Đóng hẳn app '
                         + 'rồi mở lại; còn lỗi thì xem Nhật ký.' })
        setSanSang(true)
        return
      }
      // ⚠ TỪ ĐIỂN HỎNG THÌ BÁO, không im lặng. Thiếu một từ điển thì cả một họ
      // khối mất hộp sửa — bấm đúp không ra gì, menu mờ đi — mà chẳng có dòng nào
      // nói vì sao. Đúng kiểu hỏng LẶNG dự án này săn từ đầu.
      const hong: string[] = []
      const td = await py.tu_dien_hoi()
      if (td.ok && td.value) setTuDien(td.value)
      else hong.push(`XÁC NHẬN (${td.error ?? '?'})`)
      const tl = await py.tu_dien_lam()
      if (tl.ok && tl.value) setTuDienLam(tl.value)
      else hong.push(`HÀNH ĐỘNG (${tl.error ?? '?'})`)
      const tb = await py.tu_dien_bat_dau()
      if (tb.ok && tb.value) setTuDienBD(tb.value)
      else hong.push(`BẮT ĐẦU (${tb.error ?? '?'})`)
      if (hong.length) {
        await bao({ loi: `Không nạp được từ điển: ${hong.join(' · ')}. Mấy họ khối `
                         + `tương ứng sẽ không mở hộp sửa được.` })
      }
      const r = await py.doc_ban_nhap()
      if (r.ok && r.value) await nap(r.value)
      setSanSang(true)
    })()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* -------------------------------------------------------------- mã của sơ đồ
     KHỐI BẮT ĐẦU LÀ NGUỒN DUY NHẤT. Mọi ô chọn mã trong mọi hộp thoại đọc từ đây,
     nên khai thêm một mã ở Bắt đầu là cả sơ đồ có ngay — và không hộp nào bày ra
     được một mã mà `sinh_ma` sẽ chối. Trước đây mấy ô ấy cho gõ chữ tự do, nên sai
     chính tả một cái là tới lúc bấm Build mới biết.

     `ca_danh_muc` = chạy MỘT LƯỢT cho cả rổ, lúc ấy không có «mã đang xét» nào —
     nên ô chọn cũng đừng bày lựa chọn ấy ra (`soat_ca_ro` bên Python bắt cùng luật). */
  const khoiBatDau = useMemo(
    () => nodes.map(n => (n.data as { step: Step }).step).find(s => s.kind === 'start'),
    [nodes])
  /* ⚠ Ô `ma` CÓ HAI KIỂU: mảng mã gõ sẵn, hay một object RỔ. Rổ thì object không có
     `.map` — dòng này từng đổ cả canvas. Và rổ thì ĐÚNG là không có mã nào để bày:
     rổ gồm những gì là chuyện LEAN quyết lại mỗi ngày, nên mọi ô chọn mã chỉ còn
     «mã đang xét» (`sinh_ma._sym_py` chối mọi tên mã gõ vào, cùng một luật). */
  const dsMa = useMemo(() => {
    const ds = Array.isArray(khoiBatDau?.ma)
      ? (khoiBatDau.ma as { ma?: string }[]) : []
    return ds.map(x => String(x?.ma ?? '').trim()).filter(Boolean)
  }, [khoiBatDau])
  const coMaDangXet = (khoiBatDau?.chay_cho as string | undefined) !== 'ca_danh_muc'

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

  // Hạt nhân đang đứng trong không còn (xoá hết khối của nó, mở Strategy khác…) thì tự ra.
  useEffect(() => {
    if (trongHN && !hatNhan.has(trongHN)) raHatNhan()
  }, [trongHN, hatNhan, raHatNhan])

  /** GOM khối đang chọn thành một hạt nhân. */
  const gomHatNhan = useCallback(() => {
    if (dangChon.length < 2) return
    chup()
    const tag: HatNhanTag = { id: idHatNhanMoi(), ten: `Hạt nhân ${hatNhan.size + 1}` }
    const bo = new Set(dangChon.map(n => n.id))
    ghi(`gom ${bo.size} khối thành ${trongHN ? tagDangO?.ten : tag.ten}`)
    setNodes(ns => ns.map(n => (bo.has(n.id)
      ? { ...ganTag(n, trongHN ? tagDangO : tag), selected: false } : n)))
  }, [dangChon, chup, hatNhan.size, setNodes, trongHN, tagDangO, ghi])

  /** TÁCH: khối đang chọn ra khỏi hạt nhân của chúng. */
  const taHatNhan = useCallback(() => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    setNodes(ns => ns.map(n => (bo.has(n.id) ? ganTag(n, undefined) : n)))
  }, [dangChon, chup, setNodes])

  /** Ctrl+G — GOM mấy khối Hành động đang chọn thành MỘT Nhóm.
   *
   *  Thứ tự hành động trong Nhóm lấy theo SỐ THỨ TỰ đang hiện trên canvas, không
   *  theo thứ tự bấm chuột: nhìn thấy "4, 5, 6" trên màn thì Nhóm phải xếp đúng thế.
   *  Khối chưa nối vào đâu (chưa có số) xuống cuối, giữ nguyên thứ tự tương đối.
   *
   *  Lõi ở Python (`core.gom_nhom`): "một khối khác một hành động ở chỗ nào" là
   *  kiến thức của lõi, và hai nơi cùng quyết một thứ là hai nơi để trôi khỏi nhau. */
  const gomNhom = useCallback(() => void (async () => {
    if (!dangChon.length) { await bao({ loi: 'Chọn vài khối Hành động rồi bấm Ctrl+G.' }); return }
    const xep = [...dangChon].sort((a, b) =>
      (thuTu[a.id] ?? 'zzz').localeCompare(thuTu[b.id] ?? 'zzz', undefined, { numeric: true }))
    const r = await py.gom_nhom(xep.map(n => (n.data as { step: Step }).step))
    if (!r.ok || !r.value) { await bao({ loi: r.error ?? 'Không gom được.' }); return }
    const { step, card } = r.value
    chup()
    const bo = new Set(xep.map(n => n.id))
    // Nhóm nằm ĐÚNG CHỖ khối đầu tiên: mắt đang nhìn ở đó, đừng bắt đi tìm.
    const p = { x: Math.round(xep[0].position.x), y: Math.round(xep[0].position.y) }
    step.pos = [p.x, p.y]
    // Gom NGAY TRONG một hạt nhân thì Nhóm mới vẫn thuộc hạt nhân ấy.
    const t0 = (xep[0].data as { step: Step }).step.hat_nhan
    if (t0 && xep.every(n => (n.data as { step: Step }).step.hat_nhan?.id === t0.id)) {
      step.hat_nhan = t0
    }
    setNodes(ds => [...ds.filter(k => !bo.has(k.id)).map(k => ({ ...k, selected: false })),
                    { id: step.id, type: 'buoc', position: p,
                      data: { step, card }, selected: true }])
    // DÂY NỐI: cái đi VÀO mấy khối ấy nay vào Nhóm, cái đi RA nay ra từ Nhóm, còn dây
    // NẰM GIỮA chúng thì biến mất — chúng đã thành hành động nối tiếp bên trong Nhóm,
    // mà trong Nhóm thì không có đường nối nào cả.
    setEdges(es => {
      const ra: typeof es = []
      const da = new Set<string>()
      for (const k of es) {
        const vao = bo.has(k.target)
        const roi = bo.has(k.source)
        if (vao && roi) continue
        if (!vao && !roi) { ra.push(k); continue }
        const khoa = `${roi ? step.id : k.source}->${vao ? step.id : k.target}`
        if (da.has(khoa)) continue        // nhiều dây dồn về một thì chỉ giữ một
        da.add(khoa)
        ra.push({ ...k, id: `${khoa}:${ra.length}`,
                  source: roi ? step.id : k.source, target: vao ? step.id : k.target })
      }
      return ra
    })
    ghi(`gom ${xep.length} khối thành "${step.name}"`)
  })(), [dangChon, thuTu, chup, setNodes, setEdges, ghi, bao])

  /** Ctrl+Shift+G — TÁCH Nhóm đang chọn trở lại từng khối Hành động. Ngược `gomNhom`. */
  const raNhom = useCallback(() => void (async () => {
    const nhom = dangChon.filter(n => (n.data as { step: Step }).step.kind === 'group')
    if (!nhom.length) { await bao({ loi: 'Chọn một khối Nhóm rồi bấm Ctrl+Shift+G.' }); return }
    const them: RfNode[] = []
    const noi: { dau: string; cuoi: string; cu: string }[] = []
    for (const n of nhom) {
      const st = (n.data as { step: Step }).step
      const r = await py.ra_nhom(st)
      if (!r.ok || !r.value) { await bao({ loi: r.error ?? 'Không tách được.' }); return }
      const { steps, the } = r.value
      steps.forEach((s, i) => {
        // Xếp XUỐNG DƯỚI chứ không xếp ngang: chúng nối tiếp nhau, mà cột dọc thì
        // không đè lên khối nào đang nằm bên phải.
        const p = { x: Math.round(n.position.x), y: Math.round(n.position.y) + i * 150 }
        s.pos = [p.x, p.y]
        if (st.hat_nhan) s.hat_nhan = st.hat_nhan   // tách trong hạt nhân thì ở lại đó
        them.push({ id: s.id, type: 'buoc', position: p,
                    data: { step: s, card: the[i] }, selected: true })
      })
      if (steps.length) {
        noi.push({ cu: n.id, dau: steps[0].id, cuoi: steps[steps.length - 1].id })
      }
    }
    if (!them.length) return
    chup()
    const bo = new Set(nhom.map(n => n.id))
    setNodes(ds => [...ds.filter(k => !bo.has(k.id)).map(k => ({ ...k, selected: false })),
                    ...them])
    setEdges(es => {
      const ra: typeof es = []
      // Mấy khối vừa tách phải NỐI TIẾP NHAU, không thì sơ đồ đổi nghĩa: trong Nhóm
      // chúng chạy lần lượt, ra ngoài mà không có dây thì chỉ cái đầu tiên chạy.
      const idThem = them.map(k => k.id)
      for (let i = 0; i + 1 < idThem.length; i++) {
        if (noi.some(x => x.cuoi === idThem[i])) continue   // hết một Nhóm thì ngắt
        ra.push({ id: `${idThem[i]}->${idThem[i + 1]}`, source: idThem[i],
                  target: idThem[i + 1], sourceHandle: 'right', targetHandle: 'left',
                  markerEnd: MUI_TEN })
      }
      // Dây CŨ của Nhóm: vào thì vào khối ĐẦU, ra thì ra từ khối CUỐI.
      for (const k of es) {
        const v = noi.find(x => x.cu === k.target)
        const r2 = noi.find(x => x.cu === k.source)
        if (!v && !r2) { ra.push(k); continue }
        ra.push({ ...k, id: `${k.id}:ra`, source: r2 ? r2.cuoi : k.source,
                  target: v ? v.dau : k.target })
      }
      return ra
    })
    ghi(`tách ${nhom.length > 1 ? nhom.length + ' Nhóm' : 'Nhóm'} thành ${them.length} khối`)
  })(), [dangChon, chup, setNodes, setEdges, ghi, bao])

  /** DỪNG lượt backtest đang chạy — F6, nút trong hộp tiến độ, nút trên ribbon.
   *
   *  ⚠ Đứng RIÊNG chứ không nằm trong `viec` của ribbon: `viec` khai mãi tận cuối
   *  component, sau cả bảng phím, và nó dựng LẠI ở mỗi lượt vẽ. Bảng phím trỏ vào
   *  một object dựng lại liên tục thì hoặc phải đăng ký lại listener mỗi lượt vẽ,
   *  hoặc giữ một bản cũ — cả hai đều là bẫy.
   *
   *  Chỉ bảo Python giết tiến trình rồi THÔI, không tự dọn trạng thái: vòng hỏi
   *  tiến độ sẽ thấy `xong` ở lượt kế tiếp và dọn đúng một lần. Dọn cả hai nơi thì
   *  nửa giây sau cái còn lại vẫn bắn. */
  const dungChay = useCallback(() => void (async () => {
    const r = await py.dung_backtest()
    if (!r.ok) await bao({ loi: r.error ?? 'không dừng được' })
  })(), [bao])

  /** "Màu khác…" — mở bảng màu của trình duyệt.
   *
   *  ⚠ Ô CHỌN MÀU NẰM SẴN TRONG TRANG, không nằm trong menu. Menu đóng ngay khi bấm,
   *  còn bảng màu thì vẫn mở — ô nằm trong menu là bị gỡ theo menu, chọn xong không
   *  còn ai nhận màu. Chỉ DỜI ô tới chỗ vừa bấm phải để bảng bung ra ngay đó.
   *  (Bẫy này Jenifer_Studio đã dính và đã ghi lại.)
   *
   *  Tô khi bảng ĐÓNG (`change`), không tô theo từng nhích kéo (`input`): một lần
   *  chọn là MỘT bước hoàn tác, không phải ba chục bước. */
  const oMau = useRef<HTMLInputElement>(null)
  const moBangMau = useCallback((x: number, y: number) => {
    const o = oMau.current
    if (!o) return
    o.style.left = `${x}px`
    o.style.top = `${y}px`
    o.onchange = () => doiKhoa(s => ({ ...s, mau: o.value }))
    o.click()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /** Đổi một khoá trên khối đang chọn (màu, ghim số…). */
  const doiKhoa = useCallback((f: (s: Step) => Step) => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    setNodes(ns => ns.map(n => {
      if (!bo.has(n.id)) return n
      const d = n.data as { step: Step }
      return { ...n, data: { ...d, step: f({ ...d.step }) } }
    }))
  }, [dangChon, chup, setNodes])

  /** Ngắt hết dây dính tới khối đang chọn. */
  const ngatNoi = useCallback(() => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    setEdges(es => es.filter(e => !bo.has(e.source) && !bo.has(e.target)))
  }, [dangChon, chup, setEdges])

  /** Nối khối đang chọn tới một khối khác — lối nối KHÔNG cần kéo chuột, dùng khi hai
   *  khối ở xa nhau trên một sơ đồ lớn. */
  const noiToi = useCallback((tu: string, toi: string) => {
    chup()
    setEdges(es => addEdge({ source: tu, target: toi, sourceHandle: 'right',
                             targetHandle: 'left', markerEnd: MUI_TEN }, es))
  }, [chup, setEdges])

  /* --------------------------------------------------------- ô tìm khối
     LỌC NHANH — hỏi theo DÂY thay vì theo chữ. Đây mới là cách soát một sơ đồ nghìn
     khối: không đọc từng cái, mà hỏi "chỗ nào rẽ", "chỗ nào không ai tới". */
  const dsLoc = useMemo(() => {
    const ra = new Map<string, number>()
    const vao = new Map<string, number>()
    for (const e of edges) {
      if (e.type === 'vong') continue
      ra.set(e.source, (ra.get(e.source) ?? 0) + 1)
      vao.set(e.target, (vao.get(e.target) ?? 0) + 1)
    }
    const quayVe = (n: RfNode) => (n.data as { step?: Step }).step?.type === 'quay_ve'
    const ds: { ma: string; ten: string; goiY: string; khop: (n: RfNode) => boolean }[] = [
      { ma: 'chia', ten: 'Chia nhánh', goiY: 'khối rẽ ra từ hai nhánh trở lên',
        khop: n => (ra.get(n.id) ?? 0) >= 2 },
      { ma: 'gop', ten: 'Gộp nhánh', goiY: 'khối có nhiều dây đổ vào',
        khop: n => (vao.get(n.id) ?? 0) >= 2 },
      { ma: 'cuoi', ten: 'Khối cuối', goiY: 'dòng chạy dừng ở đây',
        khop: n => !ra.get(n.id) && !quayVe(n) },
      { ma: 'khong-toi', ten: 'Không chạy tới', goiY: 'khối chưa có số',
        khop: n => !thuTu[n.id] },
    ]
    return ds.map(({ khop, ...l }) =>
      ({ ...l, ids: new Set(nodes.filter(khop).map(n => n.id)) }))
  }, [nodes, edges, thuTu])

  /** Id các khối khớp — khớp CHỮ, hay khớp lọc nhanh đang bật — xếp theo chỗ đứng trên
   *  canvas: trên xuống dưới, trái sang phải, ĐÚNG THỨ TỰ MẮT ĐỌC sơ đồ. Enter đi lần
   *  lượt theo thứ tự này, không theo thứ tự trong file. */
  const khopTim = useMemo(() => {
    const l = locTim ? dsLoc.find(x => x.ma === locTim) : undefined
    if (!l && !tim.trim()) return []
    return nodes
      .filter(n => (l ? l.ids.has(n.id)
                      : khoiKhop((n.data as { card: Card }).card, thuTu[n.id], tim)))
      .sort((a, b) => (a.position.y - b.position.y) || (a.position.x - b.position.x))
      .map(n => n.id)
  }, [nodes, tim, locTim, dsLoc, thuTu])
  const khopTimSet = useMemo(() => new Set(khopTim), [khopTim])

  /** Chọn khối rồi KÉO MÀN TỚI NÓ, phóng lên mức đọc rõ (đang to hơn thì giữ). Sơ đồ
   *  lớn thì đọc nhãn "[2A.1]" rồi tự đi tìm là không nổi. Khối nằm trong hạt nhân thì
   *  tự bước vào hạt nhân ấy trước. */
  const toiKhoi = useCallback((id: string) => {
    const hn = thuocHN.get(id)
    if (hn && hn !== trongHN) vaoHatNhan(hn)
    else if (!hn && trongHN) raHatNhan()
    setNodes(ns => ns.map(n => (n.selected === (n.id === id) ? n
                                : { ...n, selected: n.id === id })))
    setTimeout(() => {
      const n = nodes.find(x => x.id === id)
      if (!n) return
      setCenter(n.position.x + rongCua(n) / 2, n.position.y + caoCua(n) / 2,
                { zoom: Math.max(getViewport().zoom, ZOOM_DOC_RO), duration: 420 })
    }, hn && hn !== trongHN ? 520 : 0)
  }, [nodes, thuocHN, trongHN, vaoHatNhan, raHatNhan, setNodes, setCenter, getViewport])

  /** Enter trong ô tìm: khối khớp KẾ TIẾP, vòng lại từ đầu khi hết. */
  const toiKe = useCallback(() => {
    if (!khopTim.length) return
    const i = (dangO + 1) % khopTim.length
    setDangO(i)
    toiKhoi(khopTim[i])
  }, [khopTim, dangO, toiKhoi])

  // Đổi chữ tìm hay đổi lọc thì đếm lại từ đầu.
  useEffect(() => { setDangO(-1) }, [tim, locTim])

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
                thuTu: dau && cuoi && dau !== cuoi ? `${dau} → ${cuoi}` : dau,
                // Bên trong có khối khớp ô tìm thì CẢ KHUNG sáng lên — không thì tìm
                // thấy một khối đang nằm trong hạt nhân mà ngoài này không thấy gì.
                timThay: k.khoi.some(id => khopTimSet.has(id)) },
      })
    }
    return ra
  }, [trongHN, hatNhan, nodes, edges, thuTu, khopTimSet])

  const nodesVe = useMemo(() => {
    const ds = nodes.filter(n => !biGiau(n.id)).map(n => {
      const st = (n.data as { step?: Step }).step
      const veNhan = st?.type === 'quay_ve' && st.ve ? (thuTu[st.ve] ?? '?') : undefined
      const trongVong = !!vongDangXem?.trong.has(n.id) && n.id !== vongDangXem.tu
      const timThay = khopTimSet.has(n.id)
      // Chỉ khối KHỚP mới nhận chữ để tô — khối khác khỏi phải dựng lại thẻ.
      const chuTim = timThay ? tim : ''
      const d = n.data as Record<string, unknown>
      if (d.thuTu === thuTu[n.id] && d.veNhan === veNhan && d.trongVong === trongVong
          && d.timThay === timThay && d.tim === chuTim) {
        return n       // `memo` của StepNode so bằng THAM CHIẾU — không đổi thì giữ nguyên
      }
      return { ...n, data: { ...d, thuTu: thuTu[n.id], veNhan, trongVong,
                             timThay, tim: chuTim } }
    })
    return [...ds, ...nodesHatNhan]
  }, [nodes, thuTu, vongDangXem, biGiau, nodesHatNhan, khopTimSet, tim])

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
    ghi(`thêm ${card.title}`)
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
    // KHỐI HỎI mới là một cái vỏ rỗng — mở luôn hộp điều kiện, đừng bắt người dùng
    // đi tìm rồi bấm đúp. Chỉ muốn cái khối thôi thì Esc là xong.
    if (tuDien?.loai.some(l => l.ma === step.type)
        || laHanhDong(tuDienLam, step.type)) setDangSua(step.id)
  }, [chup, nodes, setNodes, biGiau, tagDangO, ghi, tuDien, tuDienLam])

  const xoa = useCallback(() => {
    if (!dangChon.length) return
    chup()
    const bo = new Set(dangChon.map(n => n.id))
    ghi(`xoá ${bo.size} khối`)
    setNodes(ns => ns.filter(n => !bo.has(n.id)))
    setEdges(es => es.filter(e => !bo.has(e.source) && !bo.has(e.target)))
  }, [chup, dangChon, setNodes, setEdges, ghi])

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
    await nap({ schema: 1, type: 'strategy', name: ten, steps: t.s, edges: t.e })
  }, [nodes, edges, ten, nap])

  const lamLai = useCallback(async () => {
    const t = chongLai.current.pop()
    if (!t) return
    chong.current.push({ s: rfSangSteps(nodes), e: rfSangEdges(edges) })
    setCoHoanTac(true)
    setCoLamLai(chongLai.current.length > 0)
    await nap({ schema: 1, type: 'strategy', name: ten, steps: t.s, edges: t.e })
  }, [nodes, edges, ten, nap])

  const strategyMoi = useCallback(() => {
    chup(); setNodes([]); setEdges([]); setTen(''); setTrongHN(null)
  }, [chup, setNodes, setEdges])

  /* --------------------------------------------------------------- bàn phím
     Tra BẢNG theo đúng cụm phím đang bấm. Bỏ qua khi con trỏ đang ở trong một ô nhập:
     gõ Ctrl+A trong ô tìm phải là "chọn hết chữ", không phải "chọn hết khối". */
  useEffect(() => {
    const nghe = (ev: KeyboardEvent) => {
      const t = ev.target as HTMLElement | null
      const trongO = !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA'
                             || t.isContentEditable)
      const cum = cumPhim(ev)
      if (!cum) return
      const ma = TRA_PHIM.get(cum)
      if (!ma) return
      // Esc trong ô nhập là việc của ô ấy (xoá chữ tìm), không phải "ra khỏi hạt nhân".
      if (trongO && !(cum === 'f2' || cum === 'ctrl+s')) return
      const viec: Record<string, () => void> = {
        'hoan-tac': () => void hoanTac(),
        'lam-lai': () => void lamLai(),
        'nhan-ban': () => void nhanBan(),
        xoa,
        'chon-het': () => setNodes(ns => ns.map(n => (biGiau(n.id) ? n
                                                      : { ...n, selected: true }))),
        'gom-nhom': gomNhom,
        'ra-nhom': raNhom,
        'gom-hat-nhan': gomHatNhan,
        'ta-hat-nhan': taHatNhan,
        'ra-hat-nhan': () => { if (trongHN) raHatNhan() },
        'doi-ten': () => {
          const n = dangChon[0]
          if (n) setDoiTen({ loai: 'khoi', id: n.id,
                             ten: (n.data as { card: Card }).card.title })
        },
        'dung-backtest': dungChay,
        'cai-dat': () => setMoCaiDat(true),
        'strategy-moi': strategyMoi,
        'mo-strategy': () => void mo(),
        luu: () => void luu(),
        'o-tim': () => (document.querySelector('.o-tim-khoi input') as HTMLInputElement
                        | null)?.focus(),
        'bang-phim-tat': () => setMoBangPhim(m => !m),
        'them-bat-dau': () => void themKhoi('start'),
        'them-nhom': () => void themKhoi('group'),
        'them-khoi-le': () => void themKhoi('action'),
        'them-quay-ve': () => void themKhoi('action', 'quay_ve'),
      }
      const f = viec[ma]
      if (!f) return
      ev.preventDefault()
      f()
    }
    window.addEventListener('keydown', nghe)
    return () => window.removeEventListener('keydown', nghe)
    // `luu` / `mo` là khai báo hàm nên được nâng lên đầu — gọi được từ đây.
  }, [hoanTac, lamLai, nhanBan, xoa, gomNhom, raNhom, gomHatNhan, taHatNhan,
      trongHN, raHatNhan, dungChay,
      dangChon, setNodes, biGiau, themKhoi, strategyMoi])

  /* ------------------------------------------------------------- bản nháp */
  useEffect(() => {
    if (!sanSang) return
    const t = setTimeout(() => {
      void py.luu_ban_nhap(ten, rfSangSteps(nodes), rfSangEdges(edges))
    }, 1200)
    return () => clearTimeout(t)
  }, [nodes, edges, ten, sanSang])

  async function luu() {
    // CHƯA CÓ TÊN thì hỏi, đừng tự đặt "Strategy mới": người dùng bấm Lưu xong đi tìm
    // trong kho sẽ thấy một đống bản tên y hệt nhau.
    let t = ten
    if (!t) {
      const v = await nhapChu({ tieu_de: 'Lưu Strategy', loi: 'Đặt tên:',
                                nhap: 'Strategy mới', nut_ok: 'Lưu' })
      if (!v?.trim()) return
      t = v.trim()
    }
    const r = await py.luu_strategy(t, rfSangSteps(nodes), rfSangEdges(edges))
    if (!r.ok || !r.value) { await bao({ loi: r.error ?? 'không lưu được' }); return }
    setTen(r.value.ten)
    void py.set_title(r.value.ten)
    ghi(`lưu ${r.value.ten}`)
  }

  /** Mở kho. Trước đây nút này lặng lẽ mở BẢN ĐẦU TIÊN trong danh sách — đúng kiểu
   *  "bấm một nút rồi nhận về một thứ mình không chọn". */
  function mo() { setMoKhoStrategy(true) }

  async function moTen(t: string) {
    const d = await py.mo_strategy(t)
    if (d.ok && d.value) { await nap(d.value); ghi(`mở ${t}`) }
    else ghi(`không mở được ${t}: ${d.error}`)
    setMoKhoStrategy(false)
  }

  /** Lưu thành một Strategy MỚI, giữ nguyên bản đang mở. */
  async function luuThanh() {
    const v = await nhapChu({ tieu_de: 'Lưu thành Strategy mới', loi: 'Tên:',
                              nhap: ten ? `${ten} (bản sao)` : 'Strategy mới',
                              nut_ok: 'Lưu' })
    if (!v?.trim()) return
    const r = await py.luu_strategy(v.trim(), rfSangSteps(nodes), rfSangEdges(edges))
    if (!r.ok || !r.value) { await bao({ loi: r.error ?? 'không lưu được' }); return }
    setTen(r.value.ten)
    void py.set_title(r.value.ten)
    ghi(`lưu thành ${r.value.ten}`)
  }

  /* ------------------------------------------------------- menu chuột phải */
  const mucMenu = useMemo<MucPhai[]>(() => {
    if (!menuPhai) return []
    const them = (kind: StepKind, loai?: string) => () => void themKhoi(kind, loai)

    if (menuPhai.loai === 'nen') {
      return [
        { ten: 'Thêm khối Bắt đầu', icon: 'start', onClick: them('start') },
        { ten: 'Thêm Nhóm', icon: 'group', onClick: them('group') },
        { ten: 'Thêm Khối lẻ', icon: 'action', onClick: them('action') },
        { ten: 'Thêm khối Quay về', icon: 'quay-ve',
          onClick: them('action', 'quay_ve') },
        { ngan: true },
        { ten: 'Chọn hết', phim: phimCua('chon-het'),
          onClick: () => setNodes(ns => ns.map(n => (biGiau(n.id) ? n
                                                     : { ...n, selected: true }))) },
      ]
    }

    if (menuPhai.loai === 'hatNhan') {
      const k = hatNhan.get(menuPhai.id!.slice(3))
      if (!k) return []
      return [
        { ten: 'Vào trong sửa', icon: 'frame', onClick: () => vaoHatNhan(k.id) },
        { ten: 'Đổi tên hạt nhân…', icon: 'edit',
          onClick: () => setDoiTen({ loai: 'hatNhan', id: k.id, ten: k.ten }) },
        { ngan: true },
        { ten: `Tách cả ${k.khoi.length} khối ra`, icon: 'unlink',
          onClick: () => {
            chup()
            const bo = new Set(k.khoi)
            setNodes(ns => ns.map(n => (bo.has(n.id) ? ganTag(n, undefined) : n)))
          } },
      ]
    }

    // --- menu của một KHỐI ---
    const n = nodes.find(x => x.id === menuPhai.id)
    if (!n) return []
    const st = (n.data as { step: Step }).step
    const so = dangChon.length || 1
    const khac = nodes.filter(x => x.id !== n.id && !biGiau(x.id))
    /* Sáu màu sẵn + mấy màu TỰ CHỌN đang có trên sơ đồ. Màu tự chọn tính thẳng từ
       các khối, không cất riêng ở đâu — không còn khối nào mang nó thì chấm tự mất,
       khỏi phải dọn một cái bảng nào. */
    const mauTuChon = [...new Set(nodes
      .map(x => (x.data as { step?: Step }).step?.mau)
      .filter((m): m is string => !!m && !m.startsWith('var(')))]
    const bangMau: [string, string][] = [
      ...MAU_KHOI.map(([ten, bien]) => [ten, `var(${bien})`] as [string, string]),
      ...mauTuChon.map(m => [m, m] as [string, string]),
    ]
    const mauDangDat = st.mau
    const coMau = (dangChon.length ? dangChon : [n])
      .some(x => !!(x.data as { step?: Step }).step?.mau)
    return [
      // Mở hộp sửa — đường thứ HAI vào ruột khối. Bấm đúp là nhanh hơn, nhưng trượt
      // ra nền một cái là không ra gì, nên phải có một lối KHÔNG cần trúng đích.
      { ten: 'Sửa khối…', icon: 'gear', tat: !coHopSua(st),
        viSao: viSaoKhongSua(st),
        onClick: () => setDangSua(n.id) },
      { ngan: true },
      { ten: 'Đổi tên…', icon: 'edit', phim: phimCua('doi-ten'),
        onClick: () => setDoiTen({ loai: 'khoi', id: n.id,
                                   ten: (n.data as { card: Card }).card.title }) },
      /* MÀU KHỐI — chép lối Jenifer_Studio.
       *
       *  Mỗi mục có CHẤM MÀU: tên «Lục», «Lam» thì phải bấm thử mới biết nó ra màu
       *  gì, mà bấm thử là một bước hoàn tác. Màu đang dùng mang dấu ✓.
       *
       *  Sáu màu sẵn, rồi tới mấy MÀU TỰ CHỌN đang có trên sơ đồ — lần sau bấm một
       *  nhát, khỏi pha lại. Danh sách ấy tính thẳng từ các khối, không cất riêng ở
       *  đâu: không còn khối nào mang màu ấy thì chấm tự mất. */
      { ten: 'Màu khối', icon: 've-mau', con: [
        ...bangMau.map(([ten, mau]) => ({
          ten, mau, dang: dangChon.length === 1 && mauDangDat === mau,
          onClick: () => doiKhoa(s => ({ ...s, mau })),
        })),
        { ten: 'Màu khác…', icon: 've-mau',
          onClick: () => moBangMau(menuPhai?.x ?? 0, menuPhai?.y ?? 0) },
        { ngan: true },
        { ten: 'Bỏ màu', icon: 'trash', tat: !coMau,
          viSao: 'mấy khối này chưa đặt màu nào',
          onClick: () => doiKhoa(s => { delete s.mau; return s }) },
      ] },
      { ten: st.ghim ? 'Bỏ ghim số' : 'Ghim số',
        icon: st.ghim ? 'bo-ghim' : 'ghim',
        viSao: 'Ghim số = xác nhận đây là điểm quay lại cố ý; số của khối được giữ nguyên',
        onClick: () => doiKhoa(s => (s.ghim ? (() => { delete s.ghim; return s })()
                                            : { ...s, ghim: true })) },
      ...(st.type === 'quay_ve' ? [{
        ten: 'Quay về khối…', icon: 'quay-ve', con: khac.length ? khac.map(x => ({
          ten: `${thuTu[x.id] ?? '–'} · ${(x.data as { card: Card }).card.title}`,
          onClick: () => doiKhoa(s => ({ ...s, ve: x.id })),
        })) : [{ ten: 'chưa có khối nào khác', tat: true }],
      } as MucPhai] : []),
      { ngan: true },
      { ten: 'Nối tới…', icon: 'branch', con: khac.length ? khac.map(x => ({
        ten: `${thuTu[x.id] ?? '–'} · ${(x.data as { card: Card }).card.title}`,
        onClick: () => noiToi(n.id, x.id),
      })) : [{ ten: 'chưa có khối nào khác', tat: true }] },
      { ten: 'Ngắt hết kết nối', icon: 'unlink', onClick: ngatNoi },
      { ngan: true },
      { ten: `Gom ${so} khối thành Nhóm`, icon: 'group',
        phim: phimCua('gom-nhom'), tat: !dangChon.length,
        viSao: 'phải chọn ít nhất một khối Hành động',
        onClick: gomNhom },
      ...(st.kind === 'group' ? [{ ten: 'Tách Nhóm', icon: 'group',
                                   phim: phimCua('ra-nhom'), onClick: raNhom } as MucPhai]
                              : []),
      { ten: `Gom ${so} khối thành Hạt nhân`, icon: 'frame',
        phim: phimCua('gom-hat-nhan'), tat: dangChon.length < 2 || !!trongHN,
        viSao: trongHN ? 'đang ở trong một hạt nhân rồi' : 'phải chọn từ hai khối trở lên',
        onClick: gomHatNhan },
      ...(st.hat_nhan ? [{ ten: 'Tách khỏi Hạt nhân', icon: 'unlink',
                           phim: phimCua('ta-hat-nhan'), onClick: taHatNhan } as MucPhai]
                      : []),
      { ngan: true },
      { ten: 'Nhân bản', icon: 'copy', phim: phimCua('nhan-ban'), onClick: nhanBan },
      { ten: `Xoá ${so > 1 ? so + ' khối' : 'khối'}`, icon: 'trash',
        phim: phimCua('xoa'), onClick: xoa },
    ]
  }, [coHopSua, viSaoKhongSua, menuPhai, nodes, dangChon, thuTu, hatNhan, trongHN,
      biGiau, themKhoi, setNodes, chup, doiKhoa, ngatNoi, noiToi, vaoHatNhan,
      gomNhom, raNhom, gomHatNhan, taHatNhan, nhanBan, xoa])

  /** Lọc nhanh kèm SỐ LƯỢNG — con số là thứ nói "sơ đồ này có 12 chỗ rẽ". */
  const locHien: LocTim[] = useMemo(
    () => dsLoc.map(({ ids, ...l }) => ({ ...l, so: ids.size })), [dsLoc])
  /** Danh sách khối khớp bày trong ô tìm. Cắt ở 40: dài hơn thì cuộn mỏi tay, mà đã
   *  tới mức ấy thì gõ thêm một chữ nhanh hơn. */
  const goiYTim = useMemo(() => khopTim.slice(0, 40).map(id => {
    const n = nodes.find(x => x.id === id)!
    const hn = thuocHN.get(id)
    return { id, nhan: thuTu[id] ?? '–', ten: (n.data as { card: Card }).card.title,
             hn: hn ? hatNhan.get(hn)?.ten : undefined }
  }), [khopTim, nodes, thuTu, thuocHN, hatNhan])

  const viec: ViecRibbon = {
    themBatDau: () => void themKhoi('start'),
    themNhom: () => void themKhoi('group'),
    themKhoiLe: () => void themKhoi('action'),
    themQuayVe: () => void themKhoi('action', 'quay_ve'),
    chay: () => void (async () => {
      // Hỏi trước xem LEAN đã trỏ đúng chỗ chưa: báo ngay tại đây dễ hiểu hơn hẳn
      // để người dùng chờ một phút rồi nhận một dòng lỗi của tiến trình con.
      const sb = await py.lean_san_sang()
      if (!sb.ok || !sb.value?.ok) {
        const d = await nhapChu({
          tieu_de: 'Chưa chạy được LEAN',
          loi: (sb.value?.loi ?? sb.error ?? '') + ' Dán đường dẫn thư mục LEAN:',
          nhap: sb.value?.goc ?? '', nut_ok: 'Lưu',
        })
        if (!d?.trim()) return
        const r2 = await py.lean_dat_goc(d.trim())
        if (!r2.ok || !r2.value?.ok) {
          await bao({ loi: r2.value?.loi ?? r2.error ?? 'vẫn chưa đúng' })
          return
        }
      }
      const r = await py.chay_backtest(ten || 'Co May', rfSangSteps(nodes),
                                       rfSangEdges(edges))
      if (!r.ok || !r.value) { await bao({ loi: r.error ?? 'không chạy được' }); return }
      if (!r.value.ok) { await bao({ loi: r.value.loi }); return }

      // Backtest chạy ở LUỒNG RIÊNG bên Python, nên ở đây chỉ HỎI mỗi nửa giây.
      // Chặn thật thì cửa sổ đứng im không vẽ gì, và người dùng tưởng app treo.
      setDangChay(true)
      setTienDo({ dang_chay: true, xong: false, giay: 0, giai_doan: '',
                  dong_cuoi: '', so_dong: 0, da_dung: false })
      const nhip = window.setInterval(() => void (async () => {
        const t = await py.tien_do_backtest()
        if (!t.ok || !t.value) return
        setTienDo(t.value)
        if (!t.value.xong) return
        window.clearInterval(nhip)
        setDangChay(false)
        setTienDo(null)
        // ⚠ DỪNG KHÔNG PHẢI LỖI. Bấm Dừng thì Python trả về `ok: false` kèm câu
        // «Bạn đã dừng lượt chạy này» — đúng với lõi, nhưng ném nó vào hộp báo lỗi
        // thì người dùng vừa cố ý dừng xong lại bị mắng. Ghi một dòng nhật ký là đủ.
        if (t.value.da_dung) { ghi('đã dừng backtest'); return }
        const kq = t.value.ket_qua
        if (!kq) { await bao({ loi: 'chạy xong mà không có kết quả' }); return }
        if (!kq.ok) { await bao({ loi: kq.loi }); return }
        setKetQua(kq)
        ghi(`backtest ${kq.ten_lop ?? ''}`)
        // MỘT CỬA SỔ RIÊNG cho lượt vừa chạy, không phải một hộp thoại đè lên sơ đồ:
        // chạy lần nữa là có cái thứ hai, xếp cạnh nhau mà so. Tắt được ở Cài đặt.
        const cd = await py.cai_dat_doc()
        if (cd.ok && cd.value?.mo_ket_qua === false) return
        if (kq.id) await py.mo_cua_so_ket_qua(kq.id)
        else setMoKetQua(true)
      })(), 500)
    })(),
    dung: dungChay,
    caiDat: () => setMoCaiDat(true),
    moKetQua: () => setMoKhoLuot(true),
    coKetQua: true,   // kho lượt chạy luôn mở được, kể cả lượt của hôm trước
    dangChay,
    sinhMa: () => void (async () => {
      const r = await py.sinh_ma(ten || 'Co May', rfSangSteps(nodes),
                                 rfSangEdges(edges), false)
      if (r.ok && r.value) setMaSinh(r.value)
      else await bao({ loi: r.error ?? 'không sinh được mã' })
    })(),
    themHoi: (loai: string) => void themKhoi('action', loai),
    themLam: (loai: string) => void themKhoi('action', loai),
    loaiLam: (tuDienLam?.loai ?? []).map(l => ({ ma: l.ma, nhan: l.nhan, icon: l.icon,
                                                 mo_ta: l.mo_ta, nhom: l.nhom,
                                                 lean: l.lean, tat: l.tat })),
    loaiHoi: (tuDien?.loai ?? []).map(l => ({ ma: l.ma, nhan: l.nhan, icon: l.icon,
                                              mo_ta: l.mo_ta, tat: l.tat })),
    xoa, nhanBan, hoanTac, lamLai,
    gomHatNhan, taHatNhan,
    luu: () => void luu(),
    luuThanh: () => void luuThanh(),
    mo,
    moi: strategyMoi,
  }

  const soLoi = vanDe.filter(v => v.severity === 'error').length

  /** BẢNG VẤN ĐỀ — bấm một dòng là KÉO MÀN TỚI đúng khối ấy. Không có cú nhảy đó thì
   *  một sơ đồ nghìn khối chỉ báo "[2A.1] sai" rồi để người ta tự đi tìm. */
  const tabs: TabDuoi[] = [
    { ma: 'van-de', ten: 'Vấn đề', so: vanDe.length, nang: soLoi > 0,
      noiDung: vanDe.length === 0
        ? <div className="trong">không có vấn đề nào</div>
        : <>{vanDe.map((v, i) => (
            <div key={i} className={'dong-van-de' + (v.severity === 'warning'
                                                     ? ' canh-bao' : '')}
                 onClick={() => { if (v.step) toiKhoi(v.step) }}
                 title={v.step ? 'Bấm để tới khối này' : undefined}>
              <span className="muc">{v.severity === 'error' ? '✘' : '⚠'}</span>
              <span>{v.message}</span>
            </div>
          ))}</> },
    { ma: 'nhat-ky', ten: 'Nhật ký', so: nhatKy.length,
      noiDung: nhatKy.length === 0
        ? <div className="trong">chưa có gì</div>
        : <div className="nhat-ky">{[...nhatKy].reverse().map((d, i) => (
            <div key={i} className="dong-log">
              <span className="gio">{d.gio}</span><span>{d.chu}</span>
            </div>
          ))}</div> },
  ]
  const hnDangO = trongHN ? hatNhan.get(trongHN) : undefined

  /* MENU TRÊN THANH TIÊU ĐỀ — bốn nhóm, theo lối Jenifer_Studio.
   *
   *  ⚠ Trước đây chỉ có MỘT nhóm «Cat Studio» với bốn mục, không mục nào hiện phím
   *  tắt và không mục nào mờ đi được. Hậu quả: mọi việc chỉ có một đường duy nhất là
   *  ribbon — mà ribbon ẩn bớt nhóm khi cửa sổ hẹp, nên ở cửa sổ 1020px thì Hoàn tác,
   *  Nhân bản, Xoá, Lưu không còn chỗ nào bấm được nữa. Menu là đường LUÔN CÓ.
   *
   *  Mỗi mục kèm `phim` (nhãn thôi — phím thật do chỗ nghe bàn phím lo) vì đó là cách
   *  duy nhất người dùng HỌC được phím tắt, và kèm `viSao` khi mờ: mờ mà không nói vì
   *  sao là thứ bực nhất trong một cái menu. */
  const menus: NhomMenu[] = [
    { ten: 'File', muc: [
      { ten: 'Strategy mới', icon: 'file', phim: phimCua('strategy-moi'),
        onClick: strategyMoi },
      { ten: 'Kho Strategy…', icon: 'folder', phim: phimCua('mo-strategy'),
        onClick: () => setMoKho(true) },
      { ngan: true },
      { ten: 'Lưu', icon: 'save', phim: phimCua('luu'), onClick: () => void luu() },
      { ten: 'Lưu thành…', icon: 'copy', onClick: () => void luuThanh() },
      { ngan: true },
      // Thả một Strategy ai gửi vào, hay chép một file kết quả cho người khác xem —
      // hai việc rất thường, mà trước đây phải tự đi tìm app nằm ở ổ nào.
      { ten: 'Mở thư mục', icon: 'folder', con: ([
        ['Strategy', 'strategy'], ['Mã sinh ra', 'ma'],
        ['Kết quả backtest', 'ket_qua'], ['Tất cả dữ liệu', 'goc'],
      ] as [string, string][]).map(([ten, loai]) => ({
        ten, onClick: () => void py.mo_thu_muc(loai).then(r => {
          if (!r.ok) void bao({ loi: r.error ?? 'không mở được thư mục' })
        }),
      })) },
      { ngan: true },
      { ten: 'Cài đặt…', icon: 'gear', phim: phimCua('cai-dat'),
        onClick: () => setMoCaiDat(true) },
      { ten: 'Thoát', onClick: () => { void py.cua_so_dong() } },
    ] },
    { ten: 'Sửa', muc: [
      { ten: 'Hoàn tác', icon: 'undo', phim: phimCua('hoan-tac'), tat: !coHoanTac,
        viSao: 'chưa có gì để hoàn tác', onClick: () => void hoanTac() },
      { ten: 'Làm lại', icon: 'redo', phim: phimCua('lam-lai'), tat: !coLamLai,
        viSao: 'chưa hoàn tác gì', onClick: () => void lamLai() },
      { ngan: true },
      { ten: 'Nhân bản', icon: 'copy', phim: phimCua('nhan-ban'), tat: !dangChon.length,
        viSao: 'chưa chọn khối nào', onClick: () => void nhanBan() },
      { ten: 'Xoá', icon: 'trash', phim: phimCua('xoa'), tat: !dangChon.length,
        viSao: 'chưa chọn khối nào', onClick: xoa },
      { ngan: true },
      { ten: 'Gom thành Nhóm', icon: 'group', phim: phimCua('gom-nhom'),
        tat: !dangChon.length, viSao: 'chưa chọn khối Hành động nào',
        onClick: gomNhom },
      { ten: 'Tách Nhóm', icon: 'group', phim: phimCua('ra-nhom'),
        tat: !dangChon.some(n => (n.data as { step: Step }).step.kind === 'group'),
        viSao: 'chưa chọn khối Nhóm nào', onClick: raNhom },
      { ngan: true },
      { ten: 'Chọn hết', phim: phimCua('chon-het'), tat: !nodes.length,
        viSao: 'canvas đang trống',
        onClick: () => setNodes(ns => ns.map(n => (biGiau(n.id) ? n
                                                   : { ...n, selected: true }))) },
    ] },
    { ten: 'Xem', muc: [
      { ten: 'Kho lượt backtest…', icon: 'chay', onClick: () => setMoKhoLuot(true) },
      { ten: 'Tìm khối', icon: 'tim', phim: phimCua('o-tim'),
        onClick: () => document.querySelector<HTMLInputElement>('.o-tim-khoi input')
          ?.focus() },
      { ngan: true },
      { ten: 'Bảng phím tắt…', icon: 'motSo', phim: phimCua('bang-phim-tat'),
        onClick: () => setMoBangPhim(true) },
    ] },
    { ten: 'Giúp', muc: [
      { ten: 'Khoá QuantConnect…', icon: 'gear',
        onClick: () => { void py.qc_khoa().then(r => setKhoa(r.ok && r.value ? r.value
          : { co: false, nguon: null, user_id: null, duong: '' })) } },
      { ngan: true },
      { ten: 'Cat Studio — vẽ chiến thuật, chạy bằng LEAN', tat: true,
        viSao: 'chỉ để xem, không bấm được' },
    ] },
  ]

  return (
    <div className="khung">
      <TitleBar tieuDe={ten || 'Strategy mới'} menus={menus} />
      <Ribbon v={viec} soChon={dangChon.length} trongHatNhan={!!trongHN}
              coHoanTac={coHoanTac} coLamLai={coLamLai} />
      <div className="vung-canvas">
        {/* Ô TÌM nổi ở GÓC TRÁI TRÊN canvas, không nằm trên ribbon: nó không "thêm" gì
            vào sơ đồ, nó chỉ giúp nhìn — mà thứ nó giúp nhìn là cái canvas ngay dưới
            nó. Để trên ribbon thì mắt phải nhảy lên một dải khác để tìm. */}
        <div className="o-tim-noi">
          <OTimKhoi giaTri={tim} onDoi={setTim} soKhop={khopTim.length}
                    dangO={dangO} onToi={toiKe}
                    loc={locTim} dsLoc={locHien} onLoc={m => setLocTim(m)}
                    goiY={goiYTim} onChon={id => { setDangO(khopTim.indexOf(id));
                                                   toiKhoi(id) }} />
        </div>
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
          // ⚠ TẮT PHÓNG TO KHI BẤM ĐÚP. Mặc định của React Flow là bấm đúp vào nền
          // thì phóng to — mà ở đây bấm đúp đã có nghĩa "mở khối ra sửa". Trượt ra
          // ngoài khối vài pixel là canvas nhảy một cái, và người dùng tưởng hộp hỏng.
          // Phóng to đã có cụm zoom dưới thanh trạng thái, không mất gì.
          zoomOnDoubleClick={false}
          onNodeDoubleClick={(_, n) => {
            if (n.id.startsWith('hn:')) { vaoHatNhan(n.id.slice(3)); return }
            if (coHopSua((n.data as { step?: Step }).step)) setDangSua(n.id)
          }}
          onPaneContextMenu={ev => {
            ev.preventDefault()
            const e = ev as unknown as MouseEvent
            setMenuPhai({ x: e.clientX, y: e.clientY, loai: 'nen' })
          }}
          onNodeContextMenu={(ev, n) => {
            ev.preventDefault()
            // Bấm phải vào khối CHƯA chọn thì chọn nó trước — không thì menu nói về
            // một khối, mà Xoá lại ăn vào khối khác đang chọn từ trước.
            if (!n.selected && !n.id.startsWith('hn:')) {
              setNodes(ns => ns.map(x => ({ ...x, selected: x.id === n.id })))
            }
            setMenuPhai({ x: ev.clientX, y: ev.clientY, id: n.id,
                          loai: n.id.startsWith('hn:') ? 'hatNhan' : 'khoi' })
          }}
          /* Quét khung xong, React Flow phủ một tấm lên các khối đã chọn (để kéo cả
             cụm) — chuột phải trúng tấm ấy chứ không trúng khối. Mở đúng menu khối. */
          onSelectionContextMenu={(ev, ds) => {
            ev.preventDefault()
            setMenuPhai({ x: ev.clientX, y: ev.clientY, id: ds[0]?.id, loai: 'khoi' })
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
        </ReactFlow>
        {nodesVe.length === 0 && (
          <div className="trong-rong">
            <div className="to">Chưa có khối nào</div>
            <div>Bấm một nút ở thanh trên để thêm khối đầu tiên.</div>
          </div>
        )}
      </div>
      <BangDuoi tabs={tabs} tab={tab} onTab={setTab}
                cao={panelCao} onCao={setPanelCao}
                gap={panelGap} onGap={setPanelGap} />
      <div className="thanh-trang-thai">
        {/* ⚙ GÓC TRÁI DƯỚI CÙNG — chỗ quen thuộc cho cài đặt (VSCode cũng vậy), và
            nó là thứ của CẢ APP nên không thuộc về ribbon, nơi mọi nút đều nói về
            sơ đồ đang vẽ. Chép chỗ đặt của Jenifer_Studio.
            (Chú thích cỡ chữ ngay trong `app.css` đã tính chỗ cho nút này từ lâu —
            «nút ⚙ 24→26» — mà nút thì chưa bao giờ có.) */}
        <button className="nut-tt" title="Cài đặt app (Ctrl+,)"
                onClick={() => setMoCaiDat(true)}><Icon name="gear" size={15} /></button>
        <span>{nodes.length} khối · {edges.length} dây</span>
        {hatNhan.size > 0 && <span>{hatNhan.size} hạt nhân</span>}
        <span className="day" />
        {soLoi > 0 && (
          <span className="loi nhay" onClick={() => { setTab('van-de'); setPanelGap(false) }}
                title="Bấm để mở bảng Vấn đề">{soLoi} lỗi</span>
        )}
        {vanDe.length > soLoi && (
          <span className="nhay" onClick={() => { setTab('van-de'); setPanelGap(false) }}
                title="Bấm để mở bảng Vấn đề">{vanDe.length - soLoi} cảnh báo</span>
        )}
        {/* BA NÚT THU PHÓNG. Trước đây là cụm DỌC của React Flow nổi trên canvas — nó
            che mất góc dưới-trái và trùng chức năng với thanh này. Gom về đây, xếp
            ngang, ngay cạnh con số phần trăm mà chúng điều khiển. */}
        <div className="cum-zoom">
          <button className="nut-zoom" onClick={() => zoomOut({ duration: 160 })}
                  title="Thu nhỏ">−</button>
          <button className="nut-zoom" onClick={() => zoomIn({ duration: 160 })}
                  title="Phóng to">+</button>
          <button className="nut-zoom" title="Vừa khung — thu phóng cho vừa cả sơ đồ"
                  onClick={() => fitView({ padding: 0.2, duration: 300 })}>
            <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor"
                 strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2.5 5.5v-3h3M13.5 5.5v-3h-3M2.5 10.5v3h3M13.5 10.5v3h-3" />
            </svg>
          </button>
        </div>
        <span className="so">{Math.round(mucZoom * 100)}%</span>
      </div>

      {/* Ô chọn màu của trình duyệt — xem `moBangMau`. Nằm ngoài menu CỐ Ý. */}
      <input ref={oMau} type="color" className="o-mau-an" tabIndex={-1} />
      {menuPhai && (
        <ContextMenu x={menuPhai.x} y={menuPhai.y} muc={mucMenu}
                     onDong={() => setMenuPhai(null)} />
      )}
      {moBangPhim && <BangPhimTat onDong={() => setMoBangPhim(false)} />}
      {doiTen && (
        <HopDoiTen tieuDe={doiTen.loai === 'khoi' ? 'Đổi tên khối' : 'Đổi tên hạt nhân'}
                   giaTri={doiTen.ten} onHuy={() => setDoiTen(null)}
                   onXong={v => {
                     chup()
                     if (doiTen.loai === 'khoi') {
                       setNodes(ns => ns.map(n => {
                         if (n.id !== doiTen.id) return n
                         const d = n.data as { step: Step }
                         return { ...n, data: { ...d, step: { ...d.step, name: v } } }
                       }))
                     } else {
                       // Tên hạt nhân nằm trên TỪNG khối của nó — đổi hết một lượt.
                       setNodes(ns => ns.map(n => {
                         const t = tagCua(n)
                         return t?.id === doiTen.id ? ganTag(n, { ...t, ten: v }) : n
                       }))
                     }
                     setDoiTen(null)
                   }} />
      )}
      {/* MỘT id đang sửa, HAI hộp thoại — loại của khối quyết mở cái nào. Không gom
          thành một hộp "sửa khối" chung: một bên là N dòng điều kiện giống nhau, bên kia
          là một bộ ô cố định — gỏi hai thứ đó vào một hộp thì cả hai đều dở. */}
      {dangSua && (() => {
        const n = nodes.find(x => x.id === dangSua)
        if (!n) return null
        const st = (n.data as { step: Step }).step
        const luu = (s: Step) => {
          chup()
          setNodes(ns => ns.map(x => (x.id === dangSua
            ? { ...x, data: { ...x.data, step: s } } : x)))
          ghi(`sửa ${s.name}`)
          setDangSua(null)
        }
        if (tuDien && tuDien.loai.some(l => l.ma === st.type)) {
          return <HopDieuKien step={st} tuDien={tuDien} dsMa={dsMa}
                              coMaDangXet={coMaDangXet} onLuu={luu}
                              onDong={() => setDangSua(null)} />
        }
        if (st.kind === 'group' && tuDienLam && tuDien) {
          return <HopNhom step={st} tuDienLam={tuDienLam} tuDienHoi={tuDien}
                          dsMa={dsMa} coMaDangXet={coMaDangXet}
                          onLuu={luu} onDong={() => setDangSua(null)} />
        }
        if (st.kind === 'start' && tuDienBD) {
          return <HopBatDau step={st} tuDien={tuDienBD} onLuu={luu}
                            onDong={() => setDangSua(null)} />
        }
        if (tuDienLam && tuDien && laHanhDong(tuDienLam, st.type)) {
          return <HopHanhDong step={st} tuDien={tuDienLam} tuDienHoi={tuDien}
                              dsMa={dsMa} coMaDangXet={coMaDangXet}
                              onLuu={luu} onDong={() => setDangSua(null)} />
        }
        return null
      })()}
      {moCaiDat && <HopCaiDat onDong={() => setMoCaiDat(false)} />}
      {moKhoLuot && <HopKhoLuot onDong={() => setMoKhoLuot(false)} />}
      {tienDo && (
        <HopTienDo td={tienDo} onHuy={() => setTienDo(null)} onDung={dungChay} />
      )}
      {moKetQua && ketQua && (
        <HopKetQua kq={ketQua} onDong={() => setMoKetQua(false)}
                   onChayLai={() => { setMoKetQua(false); viec.chay() }} />
      )}
      {maSinh && (
        <HopSinhMa kq={maSinh} onDong={() => setMaSinh(null)}
                   onGhi={() => void (async () => {
                     const r = await py.sinh_ma(ten || 'Co May', rfSangSteps(nodes),
                                                rfSangEdges(edges), true)
                     if (r.ok && r.value) setMaSinh(r.value)
                   })()} />
      )}
      {moKho && <KhoDialog onDong={() => setMoKho(false)} />}
      {moKhoStrategy && (
        <KhoStrategy
          dangMo={ten}
          lay={async () => {
            const r = await py.ds_strategy()
            return r.ok && r.value ? r.value : []
          }}
          onMo={t => void moTen(t)}
          onDong={() => setMoKhoStrategy(false)}
          onDoiTen={async (cu, moi) => {
            const r = await py.doi_ten_strategy(cu, moi)
            if (!r.ok) { await bao({ loi: r.error ?? 'không đổi tên được' }); return }
            // Đang mở chính bản vừa đổi tên thì thanh tiêu đề phải theo.
            if (ten === cu) { setTen(moi); void py.set_title(moi) }
            ghi(`đổi tên ${cu} → ${moi}`)
          }}
          onNhanBan={async (t, tMoi) => {
            const r = await py.nhan_ban_strategy(t, tMoi)
            if (!r.ok) { await bao({ loi: r.error ?? 'không nhân bản được' }); return }
            ghi(`nhân bản ${t} → ${tMoi}`)
          }}
          onXoa={async t => {
            const r = await py.xoa_strategy(t)
            if (!r.ok) { await bao({ loi: r.error ?? 'không xoá được' }); return }
            if (ten === t) { setTen(''); void py.set_title('Strategy mới') }
            ghi(`xoá ${t}`)
          }} />
      )}
      {khoa && <HopKhoa khoa={khoa} dong={() => setKhoa(null)} doi={setKhoa} />}
      {/* CUỐI CÙNG trong cây: mọi `.lop-phu` đều z-index 50, nên thứ tự DOM quyết định
          cái nào nằm trên. Đặt sớm hơn là hộp hỏi chui xuống dưới chính hộp vừa gọi nó. */}
      <HopHoi />
    </div>
  )
}

/** `useReactFlow` chỉ chạy được bên trong Provider — nên App thật nằm ở trong. */
export default function SoDo() {
  return <ReactFlowProvider><SoDoTrong /></ReactFlowProvider>
}
