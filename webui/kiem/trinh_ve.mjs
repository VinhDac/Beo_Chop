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
const {
  tramSangRf, rfSangTram, viTriMoi, demTheoTram, vanDeCuaTram, nhanTram,
  oCoNghia, daiLuongCuaTram, nhomDaiLuong, khoiLamCuaTram,
} = await import(pathToFileURL(duong).href)

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

console.log('\n▸ Hộp thoại khối: chỉ bày thứ dùng được Ở TRẠM NÀY')
/* Từ điển rút gọn, đúng hình dạng `may_boot` trả về. */
const boot = {
  toan_hang: [
    { key: 'gia_dong', nhan: 'Giá đóng', nhom: 'Giá', tram: null },
    { key: 'ema', nhan: 'EMA', nhom: 'Chỉ báo', tram: null },
    { key: 'rsi', nhan: 'RSI', nhom: 'Chỉ báo', tram: null },
    { key: 'tin_cay', nhan: 'Độ tin cậy', nhom: 'Tín hiệu', tram: ['chia_von'] },
    { key: 'lech_muc_tieu_pt', nhan: 'Lệch mục tiêu %', nhom: 'Khớp lệnh',
      tram: ['khop_lenh'] },
  ],
  toan_hang_cua_tram: {
    tin_hieu: ['gia_dong', 'ema', 'rsi'],
    chia_von: ['gia_dong', 'ema', 'rsi', 'tin_cay'],
    khop_lenh: ['gia_dong', 'ema', 'rsi', 'lech_muc_tieu_pt'],
  },
  khoi_lam: {
    bao: { tram: 'tin_hieu', nhan: 'Báo tín hiệu', vai: 'quyet_dinh', mo_ta: '', truong: [] },
    dua_ve_0: { tram: 'rui_ro', nhan: 'Đưa về 0', vai: 'quyet_dinh', mo_ta: '', truong: [] },
    cam_vao_lai: { tram: 'rui_ro', nhan: 'Cấm vào lại', vai: 'phu', mo_ta: '', truong: [] },
  },
  khoi_lam_cua_tram: { tin_hieu: ['bao'], rui_ro: ['dua_ve_0', 'cam_vao_lai'] },
  can_co: { tin_hieu: ['bao'] },
}
kiem('trạm ② không thấy đại lượng «tín hiệu» (của ③) hay «khớp lệnh» (của ⑤)',
     daiLuongCuaTram(boot, 'tin_hieu').map(t => t.key).join(',') === 'gia_dong,ema,rsi')
kiem('trạm ③ thấy thêm «Độ tin cậy», trạm ⑤ thấy thêm «Lệch mục tiêu %»',
     daiLuongCuaTram(boot, 'chia_von').some(t => t.key === 'tin_cay')
     && daiLuongCuaTram(boot, 'khop_lenh').some(t => t.key === 'lech_muc_tieu_pt')
     && !daiLuongCuaTram(boot, 'khop_lenh').some(t => t.key === 'tin_cay'))
kiem('nhóm giữ đúng thứ tự từ điển, không lặp',
     nhomDaiLuong(daiLuongCuaTram(boot, 'chia_von')).join(' · ')
     === 'Giá · Chỉ báo · Tín hiệu')
kiem('mỗi trạm chỉ thấy khối Làm CỦA NÓ',
     khoiLamCuaTram(boot, 'tin_hieu').map(x => x.key).join(',') === 'bao'
     && khoiLamCuaTram(boot, 'rui_ro').map(x => x.key).join(',') === 'dua_ve_0,cam_vao_lai')
kiem('khối trạm BẮT BUỘC phải có được đánh dấu, khối phụ cũng vậy',
     khoiLamCuaTram(boot, 'tin_hieu')[0].canCo === true
     && khoiLamCuaTram(boot, 'rui_ro')[0].canCo === false
     && khoiLamCuaTram(boot, 'rui_ro')[1].d.vai === 'phu')

/* Ô `khi`: ô «%» chỉ có nghĩa khi cách chia là «cố định X%». */
const oPt = { key: 'pt', loai: 'so', nhan: '%', khi: { cach: 'co_dinh' } }
const oKhung = { key: 'khung', loai: 'chon', nhan: 'khung', khi: { cach: 'rui_ro_ngang' } }
const oCach = { key: 'cach', loai: 'chon', nhan: 'cách' }
kiem('ô phụ thuộc chỉ hiện khi ô kia mang đúng giá trị',
     oCoNghia(oPt, { cach: 'co_dinh' }) && !oCoNghia(oPt, { cach: 'chia_deu' })
     && !oCoNghia(oKhung, { cach: 'co_dinh' })
     && oCoNghia(oKhung, { cach: 'rui_ro_ngang' }))
kiem('ô không khai `khi` thì luôn có nghĩa',
     oCoNghia(oCach, {}) && oCoNghia(oCach, { cach: 'x' }))

console.log(`\n${'─'.repeat(56)}\n  ${dung} đúng · ${sai} sai\n${'─'.repeat(56)}`)
process.exit(sai ? 1 : 0)
