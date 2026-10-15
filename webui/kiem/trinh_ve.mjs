/* TRÌNH VẼ 5 TRẠM — phần logic thuần của canvas: `src/may/doThi.ts`.
 *
 * Thứ hỏng ở đây KHÔNG lộ ra bằng mắt: vẽ trạm ② bằng dữ liệu trạm ③, lấy số thứ tự của
 * trạm khác, đếm chấm đỏ theo cả cỗ máy thay vì theo từng trạm, hay làm mất vị trí khối
 * khi đổi trạm — màn hình nào cũng "trông có vẻ đúng". Nên nó phải kiểm được bằng máy.
 *
 * Chạy:  node webui/kiem/trinh_ve.mjs
 */
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// Dịch ĐÚNG `src/may/doThi.ts` (nó chỉ import KIỂU, nên bản .js không còn import nào)
// rồi nạp. Không tự bóc chú thích kiểu bằng regex: đó là một bộ biên dịch thứ hai.
const goc = fileURLToPath(new URL('..', import.meta.url))
const ra = mkdtempSync(join(tmpdir(), 'catve-'))
try {
  execFileSync('npx', ['tsc', 'src/may/doThi.ts', '--target', 'es2020', '--module',
                       'es2020', '--skipLibCheck', '--types', 'node', '--outDir', ra],
               { cwd: goc, stdio: 'pipe', shell: true })
} catch (e) {
  // tsc có thể thoát khác 0 vì lỗi kiểu ở nơi khác mà VẪN xuất ra file — chỉ hỏng thật
  // khi không có file nào để nạp.
  if (!existsSync(join(ra, 'may', 'doThi.js')) && !existsSync(join(ra, 'doThi.js'))) {
    console.error(String(e.stdout ?? e))
    throw new Error('không dịch nổi src/may/doThi.ts')
  }
}
const duong = existsSync(join(ra, 'may', 'doThi.js'))
  ? join(ra, 'may', 'doThi.js') : join(ra, 'doThi.js')
const { tramSangRf, rfSangTram, viTriMoi, demTheoTram, vanDeCuaTram, nhanTram } =
  await import(pathToFileURL(duong).href)

let dung = 0, sai = 0
const kiem = (ten, dk, chi = '') => {
  if (dk) { dung++; console.log(`  ✔ ${ten} ${chi}`) }
  else { sai++; console.log(`  ✘ ${ten} ${chi}`) }
}

const TRAM = ['chon_ma', 'tin_hieu', 'chia_von', 'rui_ro', 'khop_lenh']

/* Một trạm dựng tay, đúng hình dạng Python trả về: khối + dây + THẺ kèm số thứ tự. */
const the = (id, kind, so, title, lines = [], them = {}) => ({
  id, kind, type: kind === 'start' ? null : 'check_cond', tram: 'tin_hieu',
  title, so, lines: lines.map(text => ({ text })), mo_ta: '',
  mau: kind === 'start' ? 'start' : 'hoi', ghim: false, la_cong: kind !== 'start',
  ...them,
})
const tram2 = {
  steps: [
    { id: 'a', kind: 'start', name: 'Bắt đầu', pos: [80, 60], lich: 'moi_nen', khung: 'H1' },
    { id: 'b', kind: 'action', type: 'check_cond', name: 'Hỏi', pos: [80, 200] },
    { id: 'c', kind: 'action', type: 'bao', name: 'Báo tín hiệu', pos: [80, 340] },
    { id: 'd', kind: 'action', type: 'bao', name: 'Lạc', pos: [700, 340] },
  ],
  edges: [
    { from: 'a', to: 'b', port: 'out' },
    { from: 'b', to: 'c', port: 'out', from_side: 'bottom', to_side: 'top' },
  ],
  cards: [
    the('a', 'start', '1', 'Bắt đầu', ['Mỗi nến H1 · cho mỗi mã trong rổ']),
    the('b', 'action', '1A', 'Hỏi', ['EMA(H1, 20) > EMA(H1, 50)']),
    the('c', 'action', '1A.1', 'Báo tín hiệu', ['LÊN · hạn 24 nến'],
        { mau: 'lam', la_cong: false, vai: 'quyet_dinh' }),
    // Khối 'd' KHÔNG có đường nối tới -> Python trả `so = null`.
    the('d', 'action', null, 'Lạc', ['LÊN'], { mau: 'lam', la_cong: false }),
  ],
}
const luong2 = {
  order: { a: '1', b: '1A', c: '1A.1' },
  unreachable: ['d'],
  quay_lai: [['c', 'b']],
  vong_ho: [],
  lech_nhanh: [],
  so_loi: 0,
  so_canh_bao: 0,
}

console.log('\n▸ Tài liệu -> canvas')
const { nodes, edges } = tramSangRf(tram2, luong2)
kiem('đủ khối, đủ dây, không thêm không bớt',
     nodes.length === 4 && edges.length === 2, `(${nodes.length} khối · ${edges.length} dây)`)
kiem('vị trí lấy đúng từ tài liệu',
     nodes[0].position.x === 80 && nodes[0].position.y === 60
     && nodes[3].position.x === 700)
kiem('số thứ tự lấy từ THẺ của chính trạm này',
     nodes.map(n => n.data.so).join(',') === '1,1A,1A.1,',
     `(${nodes.map(n => n.data.so ?? '–').join(' · ')})`)
kiem('khối không có đường tới thì KHÔNG có số (vẽ mờ, không chạy)',
     nodes[3].data.so === null)
kiem('chữ trên khối lấy nguyên từ Python, không ghép lại',
     nodes[0].data.card.lines[0].text === 'Mỗi nến H1 · cho mỗi mã trong rổ'
     && nodes[2].data.card.lines[0].text === 'LÊN · hạn 24 nến')
kiem('cổng nối mặc định phải -> trái; cổng đã khai thì giữ nguyên',
     edges[0].sourceHandle === 'right' && edges[0].targetHandle === 'left'
     && edges[1].sourceHandle === 'bottom' && edges[1].targetHandle === 'top')
// Dây NGƯỢC c -> b: cùng một dây, hai nghĩa khác nhau tuỳ khối đích đã ghim số chưa.
const coVong = { ...tram2, edges: [...tram2.edges, { from: 'c', to: 'b', port: 'out' }] }
kiem('dây quay lại (đích đã ghim) được đánh dấu để vẽ nét đứt màu ⟲',
     tramSangRf(coVong, luong2).edges.find(e => e.source === 'c')?.className
     === 'day-quay-lai')
kiem('vòng CHƯA ghim thì đánh dấu KHÁC (đỏ), không lẫn với vòng đã ghim',
     tramSangRf(coVong, { ...luong2, quay_lai: [], vong_ho: [['c', 'b']] })
       .edges.find(e => e.source === 'c')?.className === 'day-vong-ho')
kiem('dây thường thì không mang dấu nào',
     edges.every(e => e.className === undefined))
const khongThe = tramSangRf({ steps: tram2.steps, edges: [] })
kiem('tài liệu chưa qua Python (không có thẻ): vẫn vẽ được, KHÔNG tự bịa chữ',
     khongThe.nodes.length === 4 && khongThe.nodes[0].data.card.lines.length === 0
     && khongThe.nodes[0].data.card.title === 'Bắt đầu')

console.log('\n▸ Canvas -> tài liệu')
const keo = nodes.map(n => n.id === 'b'
  ? { ...n, position: { x: 123.4, y: 456.7 } } : n)
const quay = rfSangTram(keo, edges)
kiem('vị trí mới của khối vừa kéo đi vào tài liệu, làm tròn',
     quay.steps[1].pos[0] === 123 && quay.steps[1].pos[1] === 457,
     `(${quay.steps[1].pos.join(', ')})`)
kiem('nội dung khối KHÔNG bị canvas sửa (lịch, khung, tên còn nguyên)',
     quay.steps[0].lich === 'moi_nen' && quay.steps[0].khung === 'H1'
     && quay.steps[2].type === 'bao' && quay.steps[2].name === 'Báo tín hiệu')
kiem('dây giữ đúng hai đầu và hai cổng',
     JSON.stringify(quay.edges[1])
     === JSON.stringify({ from: 'b', to: 'c', port: 'out',
                          from_side: 'bottom', to_side: 'top' }))
kiem('đi một vòng tài liệu -> canvas -> tài liệu là BẤT BIẾN',
     JSON.stringify(rfSangTram(nodes, edges).steps)
     === JSON.stringify(tram2.steps.map(s => ({ ...s, pos: s.pos }))))

console.log('\n▸ Khối mới đặt ở đâu')
kiem('dưới khối thấp nhất, cùng cột với khối Bắt đầu — không đè hộp nào',
     JSON.stringify(viTriMoi(tram2.steps)) === JSON.stringify([80, 480]),
     `(${viTriMoi(tram2.steps).join(', ')})`)
kiem('trạm trắng hẳn thì về chỗ neo', JSON.stringify(viTriMoi([])) === '[80,120]')

console.log('\n▸ Chấm đỏ của dải 5 trạm')
const vd = [
  { severity: 'error', message: 'x', tram: 'chon_ma', step: 'a', index: null },
  { severity: 'error', message: 'y', tram: 'chon_ma', step: 'b', index: null },
  { severity: 'warning', message: 'z', tram: 'khop_lenh', step: null, index: null },
  { severity: 'error', message: 'cả cỗ máy', tram: null, step: null, index: null },
]
const dem = demTheoTram(vd, TRAM)
kiem('đếm RIÊNG từng trạm, không cộng dồn cả cỗ máy',
     dem.chon_ma.loi === 2 && dem.chon_ma.canhBao === 0
     && dem.khop_lenh.loi === 0 && dem.khop_lenh.canhBao === 1
     && dem.tin_hieu.loi === 0,
     `(① ${dem.chon_ma.loi} lỗi · ⑤ ${dem.khop_lenh.canhBao} cảnh báo)`)
kiem('mọi trạm đều có mục, kể cả trạm sạch', TRAM.every(k => k in dem))
kiem('vấn đề không thuộc trạm nào thì không chấm trạm nào',
     TRAM.reduce((s, k) => s + dem[k].loi, 0) === 2)
kiem('lọc theo trạm: lỗi lên trước cảnh báo',
     vanDeCuaTram(vd, 'chon_ma').length === 2
     && vanDeCuaTram([vd[2], { ...vd[2], severity: 'error' }], 'khop_lenh')[0]
        .severity === 'error')
kiem('nhãn trạm gọi y như Python: ký hiệu + tên',
     nhanTram({ key: 'tin_hieu', so: '②', ten: 'Tín hiệu' }) === '② Tín hiệu'
     && nhanTram(undefined, 'chia_von') === 'chia_von')

console.log(`\n${'─'.repeat(56)}\n  ${dung} đúng · ${sai} sai\n${'─'.repeat(56)}`)
process.exit(sai ? 1 : 0)
