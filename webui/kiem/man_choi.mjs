/* CỬA SỔ MÀN CHƠI — chạy thật trong Chromium, với bề mặt Python GIẢ.
 *
 * Bài kiểm khói cho giao diện: nạp `webui/dist/index.html?qc=1`, thay `window.pywebview.api`
 * bằng một bản giả nói đúng hình dạng của `api.ApiQC`, rồi bấm qua đủ vòng chơi:
 * mở → ▶ đầy đủ (tiến độ → kết quả → Vì sao / Thống kê / Lệnh) → Nộp (màn ẩn: chỉ điểm)
 * → khoá → Sáng tạo. Bắt mọi lỗi console. Phần Python thật đã có bài riêng
 * (`tests/test_game_qc.py`); bài này canh chỗ hai bên gặp nhau: tên hàm, hình dạng dữ liệu.
 *
 * Cần: `npm run build` trước, và Playwright (không có thì BỎ QUA, không báo hỏng —
 * máy người dùng không bắt buộc cài nó).
 *
 * Chạy:  node webui/kiem/man_choi.mjs  [thư_mục_ảnh]
 */
import { createServer } from 'node:http'
import { existsSync, mkdirSync, readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { execSync } from 'node:child_process'
import { extname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const goc = fileURLToPath(new URL('..', import.meta.url))
const dist = join(goc, 'dist')
const anh = process.argv[2] || ''

let chromium
try {
  const req = createRequire(import.meta.url)
  let duong
  try { duong = req.resolve('playwright') } catch {
    duong = req.resolve(join(execSync('npm root -g').toString().trim(), 'playwright'))
  }
  chromium = req(duong).chromium
} catch {
  console.log('  — bỏ qua: máy này chưa cài Playwright')
  process.exit(0)
}
if (!existsSync(join(dist, 'index.html'))) {
  console.log('  ✘ chưa build giao diện — chạy `npm run build` trong webui/ trước')
  process.exit(1)
}

/* ---------------- máy chủ tĩnh cho dist/ ---------------- */
const KIEU = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
               '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.png': 'image/png' }
const srv = createServer((q, r) => {
  const p = join(dist, decodeURIComponent(new URL(q.url, 'http://x').pathname))
  if (!p.startsWith(dist) || !existsSync(p)) { r.writeHead(404); r.end(); return }
  r.writeHead(200, { 'Content-Type': KIEU[extname(p)] || 'application/octet-stream' })
  r.end(readFileSync(p))
})
await new Promise(ok => srv.listen(0, '127.0.0.1', ok))
const cong = srv.address().port

/* ---------------- bề mặt Python GIẢ (chạy trong trang) ---------------- */
function giaApi() {
  const ok = v => ({ ok: true, value: v })
  const s = { chay: false, hoi: 0, loai: null, dayDu: false, nop: 0, kq: null,
              khoa: { co: true, nguon: 'file', user_id: '424242', duong: 'C:/cat/du_lieu/qc_khoa.json' },
              lichSu: [] }
  window.__goi = []
  const tk = { so_lenh: 52, so_dong: 40, so_huy: 12, thang: 18, thua: 22, ty_le_thang: 45,
               lai_tien: 310, tong_R: 6.5, von_dau: 10000, von_cuoi: 10310, lai_pt: 3.1,
               drawdown_pt: 4.2, drawdown_tien: 430, drawdown_luc: 1717000000, R_moi_lenh: 0.163,
               R_khi_thang: 1.9, R_khi_thua: -1, he_so_lai: 1.3, chuoi_thua: 5, so_zone: 30,
               nen_mo_ho: 0, so_luot: 180000 }
  const cham = { lai_pt: 3.1, mua_giu_pt: 27.2, thang_boss: false, so_dong: 40, sach: true }
  const man = () => [{
    id: 'vang-2024', ten: 'Vàng · 2024', ban_do: 'Vàng', symbol: 'XAUUSD', von: 10000,
    thay: ['2024-01-01', '2024-12-31'], nhanh: ['2024-10-01', '2024-12-31'],
    an_mo_ta: '12 tháng ngay sau màn này',
    boss: { id: 'mua_giu', ten: 'Mua rồi giữ', mo_ta: 'Mua ở nến đầu tiên, giữ tới nến cuối cùng.' },
    loi_dan: 'Năm vàng tăng rất mạnh.',
    tien_do: { so_lan_nop: s.nop, sao: s.nop ? 1 : 0, tot_nhat: null, lan_cuoi: null },
    ve_nop: s.dayDu ? { t: '2026-10-14 10:00', ten: 'Compress (mẫu)', duong: 'x', ...cham } : null,
  }]
  const ketQua = loai => ({
    ten: 'Compress (mẫu)', van_tay: 'abc', symbol: 'XAUUSD',
    tu: loai === 'nhanh' ? '2024-10-01' : '2024-01-01', den: '2024-12-31', tf: 'M5',
    thong_ke: tk, duong_von: [[1704100000, 10000, 0], [1710000000, 9800, -2], [1720000000, 10310, 0]],
    gia_dau: 2063, gia_cuoi: 2624, mua_giu_pt: 27.2,
    dem: { m1: 350000, truc: 70000, entry: 70000, manage: 100000, entry_tre: 12 },
    giay_chay: 31.2, so_luot: 180000, duong_nhat_ky: 'C:/cat/du_lieu/nhat_ky/a.jsonl',
    do_gon: { so_khoi: 11, so_tham_so: 11, tong: 22 }, t_dau: 1704100000, t_cuoi: 1735600000,
    nhip: { entry: 'M5', manage: 'M1' }, loai, man: 'vang-2024', an: false, cham,
    url: 'https://www.quantconnect.com/project/1/b', giay_tong: 48,
    sao: loai === 'day_du' ? 1 : null, lan_nop: null,
  })
  const ketQuaNop = () => ({ ...ketQua('nop'), tu: null, den: null, url: null, duong_von: [], so_luot: null,
    an: true, sao: 1, lan_nop: s.nop, thay: man()[0].ve_nop,
    cham: { lai_pt: 5.4, mua_giu_pt: 41.0, thang_boss: false, so_dong: 31, sach: true } })
  const dong = [
    { i: 0, nen: 0, tab: 'entry', lenh_id: null, co_viec: true,
      chu: '01-02 22:45  ENTRY   [1]→[2]→[3]→[4B]  đặt Bán L-0001 @2063.10  SL 2070.00  TP 2050.00' },
    { i: 5, nen: 3, tab: 'manage', lenh_id: 'L-0001', co_viec: true,
      chu: '01-03 01:10  MANAGE L-0001  [1]→[2]  sửa L-0001 · hoà vốn → SL 2063.10' },
  ]
  const api = {
    vung_khong_keo: async () => ok(true), cua_so_dang_phong_to: async () => ok(false),
    keo_cua_so: async () => ok(true), set_title: async () => ok(true),
    qc_boot: async () => ok({
      phien_ban: 'x', accent: null,
      doc: { name: 'Compress (mẫu)', symbol: 'XAUUSD', tham_so: [], entry: { steps: [], edges: [] },
             manage: { steps: [], edges: [] } },
      man: man(), loai: { nhanh: '▶ nhanh', day_du: '▶ đầy đủ', nop: 'Nộp', tu_do: '▶ tự do' },
      khoa: s.khoa, do_gon: { so_khoi: 11, so_tham_so: 11, tong: 22 },
      tu_do: { symbol: 'XAUUSD', tu: '2025-10-01', den: '2025-12-31', von: 10000 },
      trang_thai: { dang_chay: false, xong: null, loi: null }, co_ket_qua: false }),
    qc_man: async () => ok(man()),
    qc_lich_su: async () => ok(s.lichSu),
    qc_khoa: async () => ok(s.khoa),
    qc_chay: async (loai, manId, tuDo) => {
      window.__goi.push(['chay', loai, manId, tuDo])
      if (loai === 'nop' && !s.dayDu) return { ok: false, error: 'Chạy ▶ đầy đủ cỗ máy này trước khi nộp' }
      s.chay = true; s.hoi = 0; s.loai = loai
      return ok(true)
    },
    qc_trang_thai: async () => {
      if (!s.chay) return ok({ dang_chay: false, xong: null, loi: null })
      s.hoi += 1
      if (s.hoi < 5) return ok({ dang_chay: true, loai: s.loai,
        chu: s.hoi < 3 ? 'Biên dịch' : 'Chạy backtest', ti_le: s.hoi < 3 ? null : 0.5,
        ti_le_chung: s.hoi * 0.18, giay: s.hoi, xong: null, loi: null })
      s.chay = false
      let x
      if (s.loai === 'nop') { s.nop += 1; x = ketQuaNop() }
      else { x = ketQua(s.loai); s.kq = x; if (s.loai === 'day_du') s.dayDu = true }
      s.lichSu = [{ t: '2026-10-14 10:00', loai: s.loai, man: 'vang-2024', ten: 'Compress (mẫu)',
                    van_tay: 'abc', symbol: 'XAUUSD', tu: x.tu, den: x.den, an: !!x.an, sao: x.sao,
                    lai_pt: x.cham.lai_pt, mua_giu_pt: x.cham.mua_giu_pt, so_lenh: 52,
                    url: x.url, duong: 'C:/cat/du_lieu/nhat_ky/a.jsonl' }, ...s.lichSu]
      return ok({ dang_chay: false, loai: s.loai, xong: x, loi: null, ti_le_chung: 1 })
    },
    qc_ket_qua: async () => ok(s.kq),
    qc_nhat_ky: async (tu, so, chi) => ok({ tong: dong.length, tu, dong }),
    qc_lenh: async () => ok([{ id: 'L-0001', huong: 'ban', loai: 'stop', lot: 0.1, gia_dat: 2063.1,
      gia_khop: 2063.1, gia_dong: 2050, sl: 2070, tp: 2050, R: 6.9, trang_thai: 'dong',
      ly_do_dong: 'tp', t_dat: 1704235500, t_khop: 1704236000, t_dong: 1704250000 }]),
    qc_soi_luot: async i => { window.__goi.push(['soi', i]); return ok({ da_ban: true }) },
    qc_mo_lai: async d => { window.__goi.push(['mo_lai', d]); s.kq = ketQua('nhanh'); return ok(s.kq) },
    qc_mo_web: async u => { window.__goi.push(['web', u]); return ok(true) },
    qc_luu_khoa: async (u, t) => {
      window.__goi.push(['luu_khoa', u, t.length])
      s.khoa = { co: true, nguon: 'file', user_id: u, duong: 'C:/cat/du_lieu/qc_khoa.json' }
      return ok(s.khoa)
    },
    qc_kiem_khoa: async () => ok(true),
    qc_xoa_khoa: async () => { s.khoa = { co: false, nguon: null, user_id: null, duong: 'x' }; return ok(s.khoa) },
  }
  window.pywebview = { api }
}

/* ---------------- chạy ---------------- */
let dung = 0, sai = 0
const kiem = (ten, dk, chi = '') => {
  if (dk) { dung += 1; console.log(`  ✔ ${ten} ${chi}`) } else { sai += 1; console.log(`  ✘ ${ten} ${chi}`) }
}
const trinh = await chromium.launch()
const trang = await trinh.newPage({ viewport: { width: 1360, height: 860 } })
const loiConsole = []
trang.on('console', m => { if (m.type() === 'error') loiConsole.push(m.text()) })
trang.on('pageerror', e => loiConsole.push(String(e)))
await trang.addInitScript(giaApi)
const chup = async ten => { if (anh) { mkdirSync(anh, { recursive: true }); await trang.screenshot({ path: join(anh, ten) }) } }
/** Bấm tab bảng dưới theo KHOÁ nhãn — nhãn có thể kèm số đếm (`Lịch sử2`). */
const tab = async nhan => trang.locator('.hang-tab .tab', { hasText: nhan }).first().click()
const co = async (chu, han = 5000) => {
  try { await trang.getByText(chu, { exact: false }).first().waitFor({ timeout: han }); return true }
  catch { return false }
}

try {
  await trang.goto(`http://127.0.0.1:${cong}/index.html?qc=1`)
  kiem('mở cửa sổ: thẻ màn, boss, độ gọn', await co('Vàng · 2024') && await co('Mua rồi giữ')
       && await co('11 khối + 11 tham số'))
  const nutNop = trang.getByRole('button', { name: 'Nộp ↑' })
  kiem('chưa ▶ đầy đủ → nút Nộp tắt', await nutNop.isDisabled())
  await chup('1-mo.png')

  await trang.getByRole('button', { name: '▶ đầy đủ' }).click()
  kiem('bấm ▶ đầy đủ → hiện tiến độ', await co('đang chạy trên QuantConnect', 3000))
  await chup('2-tien-do.png')
  kiem('xong → thẻ kết quả: cỗ máy vs boss, phán định',
       await co('chưa thắng boss', 8000) && await co('+27.20 %'))
  kiem('tab «Vì sao» hiện dòng nhật ký', await co('đặt Bán L-0001'))
  await chup('3-ket-qua.png')

  await trang.getByText('đặt Bán L-0001').first().click({ button: 'right' })
  await trang.locator('.menu-phai .muc-phai', { hasText: 'Xem trên sơ đồ' }).click()
  const goi = await trang.evaluate(() => window.__goi)
  kiem('chuột phải → «Xem trên sơ đồ» gọi qc_soi_luot', goi.some(g => g[0] === 'soi' && g[1] === 0))

  await tab('Thống kê')
  kiem('tab Thống kê vẽ bằng ThongKe dùng chung', await co('Đường vốn') && await co('10,310.00'))
  await chup('4-thong-ke.png')
  await tab('Lệnh')
  // Bán khớp 2063.1, chốt lời 2050, R = 6.9 → (2063.1 − 2050) / 6.9 = +1.90 R
  kiem('tab Lệnh: giờ, giá, R', await co('2024-01-02 22:45') && await co('+1.90'))

  kiem('đã ▶ đầy đủ → nút Nộp bật', !(await nutNop.isDisabled()))
  await nutNop.click()
  kiem('Nộp → thẻ điểm màn ẩn: lần thứ 1, hai màn, chỉ điểm',
       await co('lần thứ', 8000) && await co('Màn ẩn chỉ cho xem điểm') && await co('+41.00 %'))
  await chup('5-nop.png')

  await tab('Lịch sử')
  kiem('tab Lịch sử: lượt màn ẩn không ngày, không «xem», không link QC',
       await co('XAUUSD · màn ẩn') && (await trang.getByRole('button', { name: 'xem' }).count()) === 1
       && (await trang.locator('.mc-hang-nut .nut-nho', { hasText: 'QC' }).count()) === 1
       && !(await co('null', 500)))

  await trang.getByRole('button', { name: /QC · 424242/ }).click()
  kiem('bấm huy hiệu khoá → hộp khoá', await co('Khoá QuantConnect') && await co('toàn quyền tài khoản'))
  await trang.getByPlaceholder('(đã lưu — nhập để thay)').fill('tok-moi-0123456789abcdef')
  await trang.getByRole('button', { name: 'Lưu' }).click()
  kiem('lưu khoá → báo đã lưu, ô token xoá trắng', await co('Đã lưu khoá')
       && (await trang.getByPlaceholder('(đã lưu — nhập để thay)').inputValue()) === '')
  await chup('6-khoa.png')
  await trang.locator('.ht-chan .nut', { hasText: 'Đóng' }).click()   // nút của HỘP, không phải ✕ cửa sổ

  await trang.getByRole('button', { name: 'Sáng tạo' }).click()
  await trang.getByRole('button', { name: '▶ chạy' }).click()
  const goi2 = await trang.evaluate(() => window.__goi)
  const cuoi = goi2.filter(g => g[0] === 'chay').pop()
  kiem('Sáng tạo: ▶ chạy gửi symbol/ngày/vốn, không gửi màn',
       cuoi && cuoi[1] === 'tu_do' && cuoi[2] === null && cuoi[3]?.symbol === 'XAUUSD')
  await co('chưa thắng boss', 8000)
  await chup('7-sang-tao.png')

  kiem('không có lỗi console', loiConsole.length === 0, loiConsole.slice(0, 3).join(' | '))
} catch (e) {
  kiem('chạy trọn kịch bản', false, String(e))
} finally {
  await trinh.close()
  srv.close()
}
console.log(`\n  ${dung} đúng · ${sai} sai`)
process.exit(sai ? 1 : 0)
