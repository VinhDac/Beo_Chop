/** Đổi qua lại giữa TÀI LIỆU cỗ máy (Python) và node/edge của React Flow — và vài phép
 *  đếm nhỏ cho dải 5 trạm.  (D-10, phần 5)
 *
 *  Ở riêng một file, KHÔNG import React cũng không import @xyflow: để `webui/kiem/
 *  trinh_ve.mjs` dịch và chạy được bằng node trần. Thứ hỏng ở đây — vẽ trạm ② bằng dữ
 *  liệu của trạm ③, hay đánh số của trạm khác — là thứ nhìn màn hình không chắc thấy,
 *  nên nó phải kiểm được bằng máy.
 */
import type { ProcEdge } from '../types'
import type { KhoiMay, LuongTram, TheKhoi, TramDoc, TramKey, TramMoTa, VanDeMay } from './mayTypes'

/** Node của React Flow, khai lại bằng hình dạng tối thiểu ta thật sự dùng. */
export interface NodeMay {
  id: string
  type: string
  position: { x: number; y: number }
  data: {
    step: KhoiMay
    card: TheKhoi
    /** Nhãn đánh số của trạm này (`1 · 1A · 1A.1`); `null` = không có đường tới. */
    so: string | null
  }
}

export interface EdgeMay {
  id: string
  source: string
  target: string
  sourceHandle: string
  targetHandle: string
  /** Dây quay lại (tới khối đã ghim) hay vòng hở — vẽ khác, xem app.css. */
  className?: string
}

/** Khoảng cách xếp khối khi tài liệu chưa có `pos` (file cũ, hoặc khối vừa sinh). */
const COT = 340
const HANG = 140

export function tramSangRf(g: TramDoc, luong?: LuongTram): {
  nodes: NodeMay[]; edges: EdgeMay[]
} {
  const the = new Map((g.cards ?? []).map(c => [c.id, c]))
  const so = luong?.order ?? {}
  const nodes: NodeMay[] = (g.steps ?? []).map((s, i) => ({
    id: s.id,
    type: 'khoi',
    position: { x: s.pos?.[0] ?? 80 + i * COT, y: s.pos?.[1] ?? 120 },
    data: {
      step: s,
      // Thẻ do Python dựng. Thiếu thẻ (tài liệu chưa qua `may_kem_the`) thì dựng một
      // thẻ trần mang đúng cái biết chắc, chứ KHÔNG tự ghép chữ mô tả khối.
      card: the.get(s.id) ?? {
        id: s.id, kind: s.kind, type: s.type ?? null, tram: 'chon_ma' as TramKey,
        title: s.name ?? '', so: null, lines: [], mo_ta: '',
        mau: s.kind === 'start' ? 'start' : 'hoi', ghim: !!s.ghim, la_cong: false,
      },
      so: so[s.id] ?? null,
    },
  }))
  const quay = new Set((luong?.quay_lai ?? []).map(([a, b]) => `${a}->${b}`))
  const ho = new Set((luong?.vong_ho ?? []).map(([a, b]) => `${a}->${b}`))
  const edges: EdgeMay[] = (g.edges ?? []).map(e => ({
    id: `${e.from}->${e.to}:${e.port}`,
    source: e.from,
    target: e.to,
    // Mặc định phải→trái: luồng chạy trái sang phải, nên dây ra cạnh phải của hộp
    // trước và vào cạnh trái của hộp sau.
    sourceHandle: e.from_side ?? 'right',
    targetHandle: e.to_side ?? 'left',
    className: ho.has(`${e.from}->${e.to}`) ? 'day-vong-ho'
      : quay.has(`${e.from}->${e.to}`) ? 'day-quay-lai' : undefined,
  }))
  return { nodes, edges }
}

/** Node/edge trên canvas → `steps`/`edges` để gửi về Python. Vị trí lấy từ canvas (người
 *  chơi vừa kéo), mọi thứ khác lấy từ chính khối — JS không sửa nội dung khối ở đây. */
export function rfSangTram(nodes: NodeMay[], edges: EdgeMay[]): {
  steps: KhoiMay[]; edges: ProcEdge[]
} {
  return {
    steps: nodes.map(n => ({
      ...n.data.step,
      pos: [Math.round(n.position.x), Math.round(n.position.y)] as [number, number],
    })),
    edges: edges.map(e => ({
      from: e.source,
      to: e.target,
      port: 'out',
      from_side: e.sourceHandle ?? 'right',
      to_side: e.targetHandle ?? 'left',
    })),
  }
}

/** Vị trí cho một khối MỚI: dưới khối thấp nhất của trạm, cùng cột với khối Bắt đầu.
 *  Thả đúng chỗ khối khác là hai hộp đè nhau và người chơi tưởng chưa thêm được gì. */
export function viTriMoi(steps: KhoiMay[]): [number, number] {
  if (!steps.length) return [80, 120]
  const x = steps.find(s => s.kind === 'start')?.pos?.[0] ?? steps[0].pos?.[0] ?? 80
  const y = Math.max(...steps.map(s => s.pos?.[1] ?? 120))
  return [x, y + HANG]
}

/** Đếm lỗi/cảnh báo cho TỪNG trạm — nguồn của chấm đỏ trên dải 5 trạm.
 *
 *  Đếm từ chính danh sách vấn đề chứ không tin vào một con số gửi kèm: hai đường ra số
 *  là hai luật, và chúng sẽ lệch nhau. */
export function demTheoTram(vanDe: VanDeMay[], keys: TramKey[]): Record<TramKey, {
  loi: number; canhBao: number
}> {
  const ra = {} as Record<TramKey, { loi: number; canhBao: number }>
  for (const k of keys) ra[k] = { loi: 0, canhBao: 0 }
  for (const v of vanDe) {
    if (!v.tram || !(v.tram in ra)) continue
    if (v.severity === 'error') ra[v.tram].loi += 1
    else ra[v.tram].canhBao += 1
  }
  return ra
}

/** Vấn đề của một trạm, lỗi trước cảnh báo — bảng Vấn đề đọc từ trên xuống. */
export function vanDeCuaTram(vanDe: VanDeMay[], tram: TramKey): VanDeMay[] {
  return vanDe.filter(v => v.tram === tram)
    .sort((a, b) => (a.severity === 'error' ? 0 : 1) - (b.severity === 'error' ? 0 : 1))
}

/** `② Tín hiệu` — ký hiệu trạm kèm tên, dùng ở mọi nhãn. Y câu `tram.nhan_tram` của
 *  Python, để hai bên không bao giờ gọi một trạm bằng hai cái tên. */
export function nhanTram(t: TramMoTa | undefined, key?: TramKey): string {
  return t ? `${t.so} ${t.ten}` : String(key ?? '')
}
