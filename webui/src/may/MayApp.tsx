import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Background, BackgroundVariant, ConnectionMode, MarkerType, ReactFlow, ReactFlowProvider,
  addEdge, useEdgesState, useNodesState, useReactFlow,
  type Connection, type Edge, type EdgeChange, type Node, type NodeChange,
} from '@xyflow/react'
import { cho_cau_noi, py, pyMay } from '../api'
import KhoDialog from '../components/KhoDialog'
import TitleBar, { type NhomMenu } from '../components/TitleBar'
import BatDauDialog from './BatDauDialog'
import ChonKhoiLam from './ChonKhoiLam'
import DaiTram from './DaiTram'
import GomDialog from './GomDialog'
import KhoiDialog from './KhoiDialog'
import KhoiNode from './KhoiNode'
import ThamSoMayDialog from './ThamSoMayDialog'
import MayPicker from './MayPicker'
import MayRibbon from './MayRibbon'
import {
  demTheoTram, rfSangTram, tramSangRf, viTriMoi, type EdgeMay, type NodeMay,
} from './doThi'
import type { BootMay, KhoiMay, LuongTram, MayDoc, TramKey, VanDeMay } from './mayTypes'

/** TRÌNH VẼ CỖ MÁY 5 TRẠM — cửa sổ vẽ của app.  (D-10, phần 5)
 *
 *  Luật của màn này, y luật sơ đồ cũ nhưng nhân cho năm:
 *
 *  1. **Tài liệu là của Python.** Mọi thay đổi cấu trúc gửi CẢ cỗ máy sang Python, nhận
 *     về bản đã chuẩn hoá + thẻ + đánh số + vấn đề, rồi canvas vẽ lại từ đó. JS không
 *     ghép một mẩu chữ nào trên khối, cũng không tự tính số thứ tự.
 *  2. **Năm trạm, một canvas.** Một sơ đồ = một phạm vi chạy, nên canvas chỉ vẽ MỘT
 *     trạm; dải ①→⑤ ở trên để đổi trạm, và nó mang chấm đỏ của cả bốn trạm kia.
 *  3. **Soát cả cỗ máy sau mỗi thay đổi.** Bảng Vấn đề hiện lỗi của MỌI trạm, có nhãn
 *     trạm và bấm được để nhảy tới khối.
 */

const nodeTypes = { khoi: KhoiNode }

/** Mũi tên chỉ cần đủ để biết dây chạy về hướng nào. */
const MUI_TEN = { type: MarkerType.ArrowClosed, width: 10, height: 10, color: '#6a6a6a' }

/** 'default' = bezier. Không dùng 'smoothstep': hộp cao thấp khác nhau nên đường bậc
 *  thang gãy khúc trông như lỗi vẽ. */
const KIEU_DUONG_NOI = { type: 'default', animated: false, markerEnd: MUI_TEN }

const PHIM_CHON_NHIEU = ['Control', 'Meta', 'Shift']

const TOI_DA_UNDO = 60
const CAO_GAP = 33

const TRAM_DAU: TramKey = 'chon_ma'

function Trinh() {
  const [boot, setBoot] = useState<BootMay | null>(null)
  const [doc, setDoc] = useState<MayDoc | null>(null)
  const [tram, setTram] = useState<TramKey>(TRAM_DAU)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [vanDe, setVanDe] = useState<VanDeMay[]>([])
  const [luong, setLuong] = useState<Partial<Record<TramKey, LuongTram>>>({})
  const [vanTay, setVanTay] = useState('')
  const [ten, setTen] = useState('Cỗ máy mẫu')
  const [trangThai, setTrangThai] = useState('đang khởi động…')
  const [sanSang, setSanSang] = useState(false)
  const [dangNoi, setDangNoi] = useState(false)
  const [tabDuoi, setTabDuoi] = useState<'van-de' | 'nhat-ky'>('van-de')
  const [panelGap, setPanelGap] = useState(false)
  const [nhatKy, setNhatKy] = useState<{ gio: string; msg: string; loi?: boolean }[]>([])
  const [moMo, setMoMo] = useState(false)
  const [moKho, setMoKho] = useState(false)
  /** Khối đang sửa (id) và hộp chọn khối Làm — lát 5c. */
  const [dangSua, setDangSua] = useState<string | null>(null)
  const [moChonLam, setMoChonLam] = useState(false)
  /** Bảng Gom của trạm và bảng tham số của cỗ máy — lát 5d. */
  const [moGom, setMoGom] = useState(false)
  const [moThamSo, setMoThamSo] = useState(false)
  const [lui, setLui] = useState<string[]>([])
  const [toi, setToi] = useState<string[]>([])

  const { fitView, setCenter, zoomIn, zoomOut } = useReactFlow()

  /** Năm trạm tự giới thiệu — khai TRƯỚC mọi việc, vì mọi câu nhật ký đều gọi tên trạm
   *  bằng `nhan()` và phải gọi y như Python gọi (`tram.nhan_tram`). */
  const dsTram = boot?.tram ?? []
  const nhan = useCallback((k: TramKey | null) => {
    const t = (boot?.tram ?? []).find(x => x.key === k)
    return t ? `${t.so} ${t.ten}` : String(k ?? '')
  }, [boot])
  const cuoiLog = useRef<HTMLDivElement>(null)
  /** Cỗ máy MỚI NHẤT, đọc được từ trong callback mà không phải khai phụ thuộc — bàn
   *  phím và menu bắn vào đây, mà chúng đăng ký một lần. */
  const docRef = useRef<MayDoc | null>(null)
  const tramRef = useRef<TramKey>(TRAM_DAU)

  const ghi = useCallback((msg: string, loi = false) => {
    const gio = new Date().toLocaleTimeString('vi-VN', { hour12: false })
    setNhatKy(ds => [...ds.slice(-400), { gio, msg, loi }])
    if (loi) setTabDuoi('nhat-ky')
  }, [])

  /* ------------------------------------------------------------------ vẽ lại */

  const vuaKhung = useCallback(() => {
    fitView({ padding: 0.2, duration: 300, maxZoom: 1 })
  }, [fitView])

  const ve = useCallback((m: MayDoc, k: TramKey,
                          l: Partial<Record<TramKey, LuongTram>>) => {
    const g = m.tram[k]
    const { nodes: n, edges: e } = tramSangRf(g, l[k])
    setNodes(n as unknown as Node[])
    setEdges(e as unknown as Edge[])
  }, [setNodes, setEdges])

  /** Đổi trạm thì kéo khung về đúng sơ đồ mới. Trạm này 2 khối, trạm kia 9 khối ở toạ
   *  độ khác hẳn — giữ nguyên khung nhìn là bấm sang trạm khác thấy canvas TRỐNG, mà
   *  nhìn thì không có gì nói rằng sơ đồ nằm ngoài tầm. Chờ một nhịp cho React vẽ xong
   *  node mới rồi mới đo. */
  const veRoiVua = useCallback((m: MayDoc, k: TramKey,
                                l: Partial<Record<TramKey, LuongTram>>) => {
    ve(m, k, l)
    setTimeout(vuaKhung, 30)
  }, [ve, vuaKhung])

  /** Nạp một cỗ máy: Python chuẩn hoá + dựng thẻ + soát, rồi canvas vẽ lại từ cái trả
   *  về. ĐƯỜNG DUY NHẤT để cỗ máy đổi — không chỗ nào tự vẽ canvas từ dữ liệu chưa qua
   *  Python, nên chữ trên khối và số thứ tự không bao giờ lệch với luật. */
  const nap = useCallback(async (d: MayDoc, tramMo?: TramKey) => {
    const r = await pyMay.may_kem_the(d)
    if (!r.ok || !r.value) {
      ghi(r.error ?? 'không đọc được cỗ máy', true)
      return
    }
    const m = r.value
    const s = await pyMay.may_soat(m)
    const l = (s.tram ?? {}) as Partial<Record<TramKey, LuongTram>>
    const k = tramMo ?? tramRef.current
    docRef.current = m
    tramRef.current = k
    setDoc(m)
    setTen(m.name)
    setTram(k)
    setVanDe(s.ok ? (s.value ?? []) : [])
    setLuong(l)
    setVanTay(s.van_tay ?? '')
    if (!s.ok) ghi(s.error ?? 'không soát được cỗ máy', true)
    veRoiVua(m, k, l)
  }, [ghi, veRoiVua])

  /** Cỗ máy ĐANG trên canvas: lấy vị trí khối và dây từ canvas, mọi thứ khác từ tài
   *  liệu. Trạm khác không bị đụng tới. */
  const tuCanvas = useCallback((m: MayDoc, k: TramKey, n: Node[], e: Edge[]): MayDoc => {
    const { steps, edges: ed } = rfSangTram(n as unknown as NodeMay[],
                                            e as unknown as EdgeMay[])
    return { ...m, tram: { ...m.tram, [k]: { ...m.tram[k], steps, edges: ed } } }
  }, [])

  const ghiLui = useCallback((m: MayDoc | null) => {
    if (!m) return
    setLui(ds => [...ds.slice(-TOI_DA_UNDO), JSON.stringify(m)])
    setToi([])
  }, [])

  /** Một thay đổi CẤU TRÚC: chụp ảnh hoàn tác, rồi gửi cả cỗ máy sang Python. */
  const doi = useCallback(async (lam: (m: MayDoc, k: TramKey) => MayDoc) => {
    const m = docRef.current
    if (!m) return
    const k = tramRef.current
    const goc = tuCanvas(m, k, nodes, edges)
    ghiLui(goc)
    await nap(lam(goc, k))
  }, [nodes, edges, tuCanvas, ghiLui, nap])

  /* ------------------------------------------------------------------ khởi động */

  useEffect(() => {
    let song = true
    cho_cau_noi('may_boot').then(async () => {
      const b = await pyMay.may_boot()
      if (!song) return
      if (!b.ok || !b.value) {
        setTrangThai(b.error ?? 'không nạp được từ điển 5 trạm')
        return
      }
      setBoot(b.value)
      /* Mở app là thấy một cỗ máy CHẠY ĐƯỢC, không phải canvas trắng: người chơi mới
         có thứ để đọc và sửa: đủ năm trạm, sạch lỗi. Cỗ máy trắng vẫn ở menu. */
      const m = await pyMay.may_mo_mau()
      if (!song) return
      if (m.ok && m.value) await nap(m.value, TRAM_DAU)
      else ghi(m.error ?? 'không dựng được cỗ máy mẫu', true)
      setSanSang(true)
      setTrangThai('sẵn sàng')
    }).catch(e => setTrangThai(String(e)))
    return () => { song = false }
    // Chạy ĐÚNG MỘT LẦN lúc mở cửa sổ.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (tabDuoi === 'nhat-ky') cuoiLog.current?.scrollIntoView({ block: 'end' })
  }, [nhatKy, tabDuoi])

  /* ------------------------------------------------------------------ việc */

  const doiTram = useCallback((k: TramKey) => {
    const m = docRef.current
    if (!m) return
    /* Giữ vị trí khối người chơi vừa kéo ở trạm cũ TRƯỚC khi rời đi — không giữ thì
       đổi trạm rồi quay lại là mọi hộp nhảy về chỗ cũ. Không cần qua Python: vị trí
       không đổi chữ trên khối, cũng không đổi vân tay. */
    const m2 = tuCanvas(m, tramRef.current, nodes, edges)
    docRef.current = m2
    tramRef.current = k
    setDoc(m2)
    setTram(k)
    veRoiVua(m2, k, luong)
  }, [nodes, edges, luong, tuCanvas, veRoiVua])

  /** Thêm một khối vào trạm đang mở. `loai` rỗng = khối Hỏi; còn lại là khối Làm của
   *  chính trạm đó. Khối MỚI mở hộp thoại ngay: người chơi vừa chọn "Báo tín hiệu" thì
   *  thứ họ muốn tiếp theo là đặt hướng và hạn, không phải đi tìm nút Sửa. */
  const themKhoi = useCallback(async (loai: string | null) => {
    const m = docRef.current
    if (!m) return
    const k = tramRef.current
    const r = await pyMay.may_khoi_moi(k, 'action', loai, m.tham_so)
    if (!r.ok || !r.value) return ghi(r.error ?? 'không tạo được khối', true)
    const st: KhoiMay = { ...r.value.step, pos: viTriMoi(m.tram[k].steps) }
    await doi((d, kk) => ({
      ...d,
      tram: { ...d.tram, [kk]: { ...d.tram[kk], steps: [...d.tram[kk].steps, st] } },
    }))
    ghi(`thêm khối ${r.value.card.title} vào ${nhan(k)}`)
    setDangSua(st.id)
  }, [doi, ghi, nhan])

  /** Ghi bảng Gom của trạm đang mở. */
  const ghiGom = useCallback(async (gom: Record<string, unknown>) => {
    await doi((d, k) => ({
      ...d, tram: { ...d.tram, [k]: { ...d.tram[k], gom } },
    }))
    ghi(`đổi Gom của ${nhan(tramRef.current)}`)
  }, [doi, ghi, nhan])

  /** Ghi bảng tham số. Tham số là của CẢ cỗ máy, không của riêng trạm nào. */
  const ghiThamSo = useCallback(async (ds: MayDoc['tham_so']) => {
    await doi(d => ({ ...d, tham_so: ds }))
    ghi(`bảng tham số: ${ds.length} tham số`)
  }, [doi, ghi])

  /** Ghi một khối đã sửa trở lại trạm của nó. */
  const ghiKhoi = useCallback(async (st: KhoiMay) => {
    await doi((d, k) => ({
      ...d,
      tram: {
        ...d.tram,
        [k]: {
          ...d.tram[k],
          steps: d.tram[k].steps.map(s => (s.id === st.id
            ? { ...st, pos: s.pos, ghim: s.ghim } : s)),
        },
      },
    }))
  }, [doi])

  const xoaChon = useCallback(async () => {
    const bo = new Set(nodes.filter(n => n.selected).map(n => n.id))
    if (!bo.size) return
    // Khối Bắt đầu là ĐIỂM NEO của trạm: xoá nó thì trạm không biết chạy lúc nào, cho
    // ai — chặn ngay thay vì để bảng Vấn đề báo sau.
    const neo = nodes.filter(n => bo.has(n.id)
      && (n.data as { step: KhoiMay }).step.kind === 'start')
    if (neo.length) {
      ghi('không xoá được khối Bắt đầu — mỗi trạm phải có đúng một cái', true)
      return
    }
    await doi((d, k) => ({
      ...d,
      tram: {
        ...d.tram,
        [k]: {
          ...d.tram[k],
          steps: d.tram[k].steps.filter(s => !bo.has(s.id)),
          edges: (d.tram[k].edges ?? []).filter(e => !bo.has(e.from) && !bo.has(e.to)),
        },
      },
    }))
    ghi(`xoá ${bo.size} khối`)
  }, [nodes, doi, ghi])

  const doiGhim = useCallback(async () => {
    const bo = new Set(nodes.filter(n => n.selected).map(n => n.id))
    if (!bo.size) return
    const dang = nodes.filter(n => bo.has(n.id))
      .every(n => (n.data as { step: KhoiMay }).step.ghim)
    await doi((d, k) => ({
      ...d,
      tram: {
        ...d.tram,
        [k]: {
          ...d.tram[k],
          steps: d.tram[k].steps.map(s => bo.has(s.id)
            ? (dang ? { ...s, ghim: false } : { ...s, ghim: true })
            : s),
        },
      },
    }))
  }, [nodes, doi])

  const noi = useCallback((c: Connection) => {
    const e = addEdge({ ...c, ...KIEU_DUONG_NOI }, edges)
    setEdges(e)
    void doi((d, k) => {
      const { edges: ed } = rfSangTram(nodes as unknown as NodeMay[],
                                       e as unknown as EdgeMay[])
      return { ...d, tram: { ...d.tram, [k]: { ...d.tram[k], edges: ed } } }
    })
  }, [edges, nodes, setEdges, doi])

  const huyNoi = useCallback((_: unknown, e: Edge) => {
    const con = edges.filter(x => x.id !== e.id)
    setEdges(con)
    void doi((d, k) => {
      const { edges: ed } = rfSangTram(nodes as unknown as NodeMay[],
                                       con as unknown as EdgeMay[])
      return { ...d, tram: { ...d.tram, [k]: { ...d.tram[k], edges: ed } } }
    })
  }, [edges, nodes, setEdges, doi])

  /** Kéo xong thì chốt vị trí vào tài liệu — không qua Python (vị trí không đổi luật). */
  const ketThucKeo = useCallback(() => {
    const m = docRef.current
    if (!m) return
    const m2 = tuCanvas(m, tramRef.current, nodes, edges)
    docRef.current = m2
    setDoc(m2)
  }, [nodes, edges, tuCanvas])

  /* ⚠ Việc thật KHÔNG được nằm trong hàm cập nhật state: `StrictMode` gọi hàm đó HAI
     lần ở bản dev, nên `nap` sẽ chạy hai lượt và ngăn xếp hoàn tác tụt hai bậc cho một
     cú Ctrl+Z. Đọc state ngay tại đây, rồi mới đẩy. */
  const hoanTac = useCallback(() => {
    if (!lui.length) return
    const truoc = lui[lui.length - 1]
    const nay = docRef.current
    if (nay) {
      setToi(t => [...t, JSON.stringify(tuCanvas(nay, tramRef.current, nodes, edges))])
    }
    setLui(ds => ds.slice(0, -1))
    void nap(JSON.parse(truoc) as MayDoc)
  }, [lui, nodes, edges, tuCanvas, nap])

  const lamLai = useCallback(() => {
    if (!toi.length) return
    const sau = toi[toi.length - 1]
    const nay = docRef.current
    if (nay) {
      setLui(l => [...l, JSON.stringify(tuCanvas(nay, tramRef.current, nodes, edges))])
    }
    setToi(ds => ds.slice(0, -1))
    void nap(JSON.parse(sau) as MayDoc)
  }, [toi, nodes, edges, tuCanvas, nap])

  /* -- tài liệu -- */

  const coMayMoi = useCallback(async () => {
    const r = await pyMay.may_moi()
    if (r.ok && r.value) {
      ghiLui(docRef.current)
      await nap(r.value, TRAM_DAU)
      ghi('cỗ máy mới — năm trạm trắng, mỗi trạm một khối Bắt đầu')
    } else ghi(r.error ?? 'không tạo được cỗ máy mới', true)
  }, [nap, ghi, ghiLui])

  const coMayMau = useCallback(async () => {
    const r = await pyMay.may_mo_mau()
    if (r.ok && r.value) {
      ghiLui(docRef.current)
      await nap(r.value, TRAM_DAU)
      ghi('mở cỗ máy mẫu — đủ năm trạm, sạch lỗi')
    } else ghi(r.error ?? 'không dựng được cỗ máy mẫu', true)
  }, [nap, ghi, ghiLui])

  const moTen = useCallback(async (t: string) => {
    setMoMo(false)
    const r = await pyMay.may_mo(t)
    if (r.ok && r.value) {
      ghiLui(docRef.current)
      await nap(r.value, TRAM_DAU)
      ghi(`mở cỗ máy "${t}"`)
    } else ghi(r.error ?? `không mở được "${t}"`, true)
  }, [nap, ghi, ghiLui])

  const moFile = useCallback(async () => {
    setMoMo(false)
    const r = await pyMay.may_mo_file()
    if (r.ok && r.value) {
      ghiLui(docRef.current)
      await nap(r.value, TRAM_DAU)
      ghi('mở cỗ máy từ file')
    } else if (r.error) ghi(r.error, true)
  }, [nap, ghi, ghiLui])

  const luu = useCallback(async () => {
    const m = docRef.current
    if (!m) return
    const d = tuCanvas({ ...m, name: ten }, tramRef.current, nodes, edges)
    const r = await pyMay.may_luu(d)
    if (r.ok && r.value) {
      docRef.current = d
      setDoc(d)
      ghi(`đã lưu "${r.value.name}" (vân tay ${r.value.van_tay})`)
      setTrangThai(`đã lưu — ${r.value.path}`)
    } else ghi(r.error ?? 'không lưu được', true)
  }, [nodes, edges, ten, tuCanvas, ghi])

  const luuRaFile = useCallback(async () => {
    const m = docRef.current
    if (!m) return
    const r = await pyMay.may_luu_file(
      tuCanvas({ ...m, name: ten }, tramRef.current, nodes, edges))
    if (r.ok && r.value) ghi(`đã lưu ra ${r.value.path}`)
    else if (r.error) ghi(r.error, true)
  }, [nodes, edges, ten, tuCanvas, ghi])

  /* ------------------------------------------------------------------ bàn phím */

  useEffect(() => {
    const f = (e: KeyboardEvent) => {
      const o = e.target as HTMLElement | null
      if (o && (o.tagName === 'INPUT' || o.tagName === 'TEXTAREA'
                || o.isContentEditable)) return
      const ctrl = e.ctrlKey || e.metaKey
      if (ctrl && e.key.toLowerCase() === 'z' && !e.shiftKey) { e.preventDefault(); hoanTac() }
      else if (ctrl && (e.key.toLowerCase() === 'y'
                        || (e.shiftKey && e.key.toLowerCase() === 'z'))) {
        e.preventDefault(); lamLai()
      } else if (ctrl && e.key.toLowerCase() === 's') { e.preventDefault(); void luu() }
      else if (e.key === 'Delete' || e.key === 'Backspace') { void xoaChon() }
    }
    window.addEventListener('keydown', f)
    return () => window.removeEventListener('keydown', f)
  }, [hoanTac, lamLai, luu, xoaChon])

  /* ------------------------------------------------------------------ dẫn xuất */

  const tramMoTa = dsTram.find(t => t.key === tram)

  const dem = useMemo(
    () => demTheoTram(vanDe, boot?.tram_keys ?? []),
    [vanDe, boot])
  const soLoi = vanDe.filter(v => v.severity === 'error').length
  const soCanhBao = vanDe.length - soLoi
  const dangChon = nodes.filter(n => n.selected)

  const menuTieuDe: NhomMenu[] = useMemo(() => [
    { ten: 'Cỗ máy', muc: [
      { ten: 'Cỗ máy mới (năm trạm trắng)', icon: 'plus', onClick: () => void coMayMoi() },
      { ten: 'Cỗ máy mẫu — Theo EMA', icon: 'start', onClick: () => void coMayMau() },
      { ngan: true },
      { ten: 'Mở cỗ máy đã lưu…', icon: 'folder', onClick: () => setMoMo(true) },
      { ten: 'Mở từ file…', onClick: () => void moFile() },
      { ngan: true },
      { ten: 'Lưu cỗ máy', icon: 'save', phim: 'Ctrl+S', onClick: () => void luu() },
      { ten: 'Lưu ra file khác…', onClick: () => void luuRaFile() },
      { ngan: true },
      { ten: 'Tham số của cỗ máy…', icon: 'edit', tat: !doc, viSao: 'chưa có cỗ máy',
        onClick: () => setMoThamSo(true) },
      { ten: 'Gom của trạm đang mở…', tat: !(boot?.gom[tram]?.length),
        viSao: 'trạm này không có Gom (chỉ ① và ③ có)',
        onClick: () => setMoGom(true) },
      { ngan: true },
      { ten: 'Kho — app đang có những gì…', icon: 'folder', onClick: () => setMoKho(true) },
      { ten: 'Thoát', onClick: () => py.cua_so_dong() },
    ] },
    { ten: 'Sửa', muc: [
      { ten: 'Hoàn tác', icon: 'undo', tat: !lui.length, viSao: 'chưa có gì để hoàn tác',
        phim: 'Ctrl+Z', onClick: hoanTac },
      { ten: 'Làm lại', icon: 'redo', tat: !toi.length, viSao: 'chưa hoàn tác gì',
        phim: 'Ctrl+Y', onClick: lamLai },
      { ngan: true },
      { ten: 'Xoá khối đang chọn', icon: 'trash', tat: !dangChon.length,
        viSao: 'chưa chọn khối nào', phim: 'Delete', onClick: () => void xoaChon() },
    ] },
    { ten: 'Trạm', muc: dsTram.map(t => ({
      ten: `${t.so} ${t.ten} — ${t.hoi}`,
      onClick: () => doiTram(t.key),
      tat: !doc,
      viSao: 'chưa có cỗ máy',
    })) },
    { ten: 'Xem', muc: [
      { ten: 'Vừa khung', icon: 'fit', onClick: vuaKhung },
      { ten: 'Phóng to', onClick: () => zoomIn() },
      { ten: 'Thu nhỏ', onClick: () => zoomOut() },
      { ngan: true },
      { ten: panelGap ? 'Mở bảng dưới' : 'Gập bảng dưới',
        onClick: () => setPanelGap(v => !v) },
    ] },
  ], [coMayMoi, coMayMau, moFile, luu, luuRaFile, hoanTac, lamLai, xoaChon, dsTram,
      doiTram, doc, boot, tram, vuaKhung, zoomIn, zoomOut, panelGap, lui.length,
      toi.length, dangChon.length])

  /* ------------------------------------------------------------------ vẽ */

  return (
    <div className="khung">
      <TitleBar tieuDe={`${ten} — Cat Studio`} menus={menuTieuDe} />
      <MayRibbon
        tramMoTa={tramMoTa}
        ten={ten} datTen={setTen}
        themHoi={() => void themKhoi(null)}
        themLam={() => setMoChonLam(true)}
        sua={() => dangChon[0] && setDangSua(dangChon[0].id)}
        chinhGom={() => setMoGom(true)}
        thamSo={() => setMoThamSo(true)}
        coGom={!!(boot && (boot.gom[tram]?.length ?? 0) > 0)}
        xoa={() => void xoaChon()}
        doiGhim={() => void doiGhim()}
        hoanTac={hoanTac} lamLai={lamLai}
        vuaKhung={vuaKhung}
        coChon={dangChon.length > 0}
        chonDaGhim={dangChon.length > 0
          && dangChon.every(n => (n.data as { step: KhoiMay }).step.ghim)}
        coTheHoanTac={lui.length > 0} coTheLamLai={toi.length > 0}
        dang={!!doc}
      />

      {/* Dải 5 trạm là một DẢI RIÊNG, không nổi trên canvas như pill của sơ đồ cũ: ở
          đây nó luôn hiện (năm trạm là cấu trúc của cỗ máy, không phải một lựa chọn
          thỉnh thoảng), và nổi lên trên thì nó che đúng khối Bắt đầu — khối nằm ở góc
          trái trên của MỌI trạm. */}
      <DaiTram tram={tram} dsTram={dsTram} dang={!!doc} dat={doiTram} dem={dem} />

      <div className={'vung-canvas' + (dangNoi ? ' dang-noi' : '')}>
        <ReactFlow
          nodes={nodes} edges={edges}
          onNodesChange={onNodesChange as (c: NodeChange[]) => void}
          onEdgesChange={onEdgesChange as (c: EdgeChange[]) => void}
          onConnect={noi}
          onConnectStart={() => setDangNoi(true)}
          onConnectEnd={() => setDangNoi(false)}
          onNodeDragStop={ketThucKeo}
          onNodeDoubleClick={(_, n) => setDangSua(n.id)}
          onEdgeDoubleClick={huyNoi}
          nodeTypes={nodeTypes}
          connectionMode={ConnectionMode.Loose}
          proOptions={{ hideAttribution: true }}
          minZoom={0.2} maxZoom={2}
          defaultEdgeOptions={KIEU_DUONG_NOI}
          deleteKeyCode={null}
          multiSelectionKeyCode={PHIM_CHON_NHIEU}
          fitView
        >
          <Background variant={BackgroundVariant.Dots} gap={22} size={1.4}
                      color="var(--canvas-dot)" />
        </ReactFlow>

        {sanSang && nodes.length <= 1 && (
          <div className="trong-rong duoi">
            <div className="to">{tramMoTa ? `${tramMoTa.so} ${tramMoTa.ten}` : 'Trạm'} còn trắng</div>
            <div>
              Bấm <b>Hỏi</b> ở thanh trên để thêm một nhánh điều kiện, rồi kéo từ cổng
              bên cạnh hộp <b>Bắt đầu</b> để nối.
              <br />Nhiều cổng cùng nối từ một khối = <b>rẽ nhánh</b>, thử lần lượt từ
              trên xuống.
            </div>
          </div>
        )}
      </div>

      <div className={'bang-duoi' + (panelGap ? ' thu-gon' : '')}
           style={{ height: panelGap ? CAO_GAP : 176 }}>
        <div className="hang-tab" onDoubleClick={() => setPanelGap(v => !v)}>
          <button className={'tab' + (tabDuoi === 'van-de' ? ' dang' : '')}
                  onClick={() => { setTabDuoi('van-de'); setPanelGap(false) }}>
            Vấn đề{vanDe.length ? ` (${vanDe.length})` : ''}
          </button>
          <button className={'tab' + (tabDuoi === 'nhat-ky' ? ' dang' : '')}
                  onClick={() => { setTabDuoi('nhat-ky'); setPanelGap(false) }}>
            Nhật ký
          </button>
          <span className="day" />
          {tabDuoi === 'nhat-ky' && !panelGap && (
            <button className="nut-nho" onClick={() => setNhatKy([])}>Xoá nhật ký</button>
          )}
          <button className="nut-nho nut-gap" onClick={() => setPanelGap(v => !v)}
                  title={panelGap ? 'Mở bảng' : 'Gập bảng xuống'}>
            {panelGap ? '▲' : '▼'}
          </button>
        </div>
        {!panelGap && <div className="noi-dung-tab">
          {tabDuoi === 'van-de' ? (
            vanDe.length === 0
              ? <div className="trong">Không có vấn đề nào — cỗ máy chạy được.</div>
              : vanDe.map((v, i) => (
                <div key={i}
                     className={'dong-van-de ' + (v.severity === 'error' ? 'loi' : 'canh-bao')}
                     title="Bấm để nhảy tới khối bị lỗi"
                     onClick={() => {
                       /* Lỗi có thể ở trạm khác — đổi trạm trước rồi mới chọn khối. */
                       const k = v.tram
                       if (k && k !== tram) doiTram(k)
                       const id = v.step
                       if (!id) return
                       setTimeout(() => {
                         setNodes(ds => ds.map(n => ({ ...n, selected: n.id === id })))
                         const m = docRef.current
                         const st = m && k ? m.tram[k].steps.find(s => s.id === id) : null
                         if (st?.pos) {
                           setCenter(st.pos[0] + 150, st.pos[1] + 80,
                                     { zoom: 1, duration: 350 })
                         }
                       }, k && k !== tram ? 60 : 0)
                     }}>
                  <span className="muc">{v.severity === 'error' ? '●' : '▲'}</span>
                  <span className="nhan-tram">{nhan(v.tram)}</span>
                  <span>{v.message}</span>
                </div>
              ))
          ) : (
            nhatKy.length === 0
              ? <div className="trong">Chưa có gì.</div>
              : <div className="nhat-ky">
                  {nhatKy.map((l, i) => (
                    <div key={i} className={'dong-log' + (l.loi ? ' t-err' : '')}>
                      <span className="gio">{l.gio}</span>{l.msg}
                    </div>
                  ))}
                  <div ref={cuoiLog} />
                </div>
          )}
        </div>}
      </div>

      <div className="thanh-trang-thai">
        <span><span className="so">{nodes.length}</span> khối</span>
        <span><span className="so">{edges.length}</span> đường nối</span>
        {soLoi > 0 && <span style={{ color: 'var(--err)' }}>{soLoi} lỗi</span>}
        {soCanhBao > 0 && <span style={{ color: 'var(--warn)' }}>{soCanhBao} cảnh báo</span>}
        {soLoi === 0 && soCanhBao === 0 && doc && (
          <span style={{ color: 'var(--ok)' }}>cỗ máy sạch</span>
        )}
        <span className="day" />
        {vanTay && (
          <span className="so"
                title={'Vân tay LOGIC của cỗ máy: đổi một ngưỡng, một dây nối hay một ô '
                       + 'Gom là đổi — kéo khối đi chỗ khác thì không'}>
            ⟐ {vanTay}
          </span>
        )}
        <span>{trangThai}</span>
        <div className="cum-zoom">
          <button className="nut-zoom" onClick={() => zoomOut()} title="Thu nhỏ">−</button>
          <button className="nut-zoom" onClick={() => zoomIn()} title="Phóng to">+</button>
          <button className="nut-zoom" title="Vừa khung" onClick={vuaKhung}>⤢</button>
        </div>
      </div>

      {moMo && (
        <MayPicker tieuDe="Mở cỗ máy" onChon={t => void moTen(t)}
                   onDong={() => setMoMo(false)}
                   onDuyetFile={() => void moFile()} />
      )}
      {moKho && <KhoDialog onDong={() => setMoKho(false)} />}

      {moChonLam && boot && (
        <ChonKhoiLam tram={tram} boot={boot} onDong={() => setMoChonLam(false)}
                     onChon={loai => void themKhoi(loai)} />
      )}

      {dangSua && boot && doc && (() => {
        const st = doc.tram[tram].steps.find(s => s.id === dangSua)
        if (!st) return null
        /* Khối Bắt đầu KHÁC hẳn: nó không có điều kiện hay ô nào của từ điển khối Làm —
           thứ đổi được ở nó là LỊCH, KHUNG và (ở ①) phạm vi. */
        return st.kind === 'start' ? (
          <BatDauDialog khoi={st} tram={tram} boot={boot}
                        onLuu={s => void ghiKhoi(s)}
                        onDong={() => setDangSua(null)} />
        ) : (
          <KhoiDialog khoi={st} tram={tram} boot={boot} thamSo={doc.tham_so}
                      onLuu={s => void ghiKhoi(s)}
                      onDong={() => setDangSua(null)} />
        )
      })()}

      {moGom && boot && doc && (
        <GomDialog doc={doc} tram={tram} boot={boot}
                   onLuu={g => void ghiGom(g)} onDong={() => setMoGom(false)} />
      )}

      {moThamSo && boot && doc && (
        <ThamSoMayDialog dsGoc={doc.tham_so} boot={boot}
                         onLuu={ds => { setMoThamSo(false); void ghiThamSo(ds) }}
                         onDong={() => setMoThamSo(false)} />
      )}
    </div>
  )
}

export default function MayApp() {
  return <ReactFlowProvider><Trinh /></ReactFlowProvider>
}
