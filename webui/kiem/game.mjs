/* GAME ĐẦU-CUỐI — chơi trọn màn 1-1 trong cửa sổ vẽ THẬT, như người chơi.  (D-09)
 *
 * Khác `man_choi.mjs` (bề mặt Python GIẢ): ở đây giao diện nói với `api.Api` THẬT qua
 * `cau_noi_game.py`, và "QuantConnect" là máy chủ giả chạy thật bộ file app đóng gói.
 * Nên một lượt đi qua đủ: giao diện → Api → luật game → đóng gói → "QC" → nhật ký → sao.
 *
 * Vòng chơi được bấm qua (khuôn Opus Magnum):
 *   màn hình chính → khoá QC → truyện mở chương → bản đồ → phiếu đặt máy → xưởng (lắp máy
 *   gợi ý) → ▶ đầy đủ nhiều lần, đổi núm → kết quả + ba histogram → xem máy nghĩ →
 *   đấu màn ẩn → hoàn thành, mở khoá 1-2 → phiếu 1-2 có giác quan MỚI.
 *
 * Cần: `npm run build` trước; Playwright (không có thì BỎ QUA — máy người dùng không bắt
 * buộc cài). Truyền thư mục thì chụp từng màn hình vào đó, đánh số theo thứ tự gặp.
 *
 * Chạy:  node webui/kiem/game.mjs  [thư_mục_ảnh]
 */
import { spawn, execSync } from 'node:child_process'
import { existsSync, mkdirSync } from 'node:fs'
import { createRequire } from 'node:module'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const goc = fileURLToPath(new URL('..', import.meta.url))
const ANH = process.argv[2] || ''

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
if (!existsSync(join(goc, 'dist', 'index.html'))) {
  console.log('  ✘ chưa build giao diện — chạy `npm run build` trong webui/ trước')
  process.exit(1)
}
if (ANH) mkdirSync(ANH, { recursive: true })

/* ---------- cầu nối Python ---------- */
const py = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3')
const cau = spawn(py, [join(goc, 'kiem', 'cau_noi_game.py'), '0'], { stdio: ['ignore', 'pipe', 'pipe'] })
let loiCau = ''
cau.stderr.on('data', d => { loiCau += d })
const cong = await new Promise((xong, hong) => {
  let ra = ''
  const h = setTimeout(() => hong(new Error('cầu nối không lên sau 60 giây\n' + loiCau)), 60000)
  cau.stdout.on('data', d => {
    ra += d
    const m = ra.match(/san_sang (\d+)/)
    if (m) { clearTimeout(h); xong(m[1]) }
  })
  cau.on('exit', c => { clearTimeout(h); hong(new Error(`cầu nối thoát (${c})\n` + loiCau)) })
})
const GOC = `http://127.0.0.1:${cong}`
const goiPy = async (ten, ...args) =>
  (await fetch(GOC + '/goi/chinh', { method: 'POST', body: JSON.stringify({ ten, args }) })).json()

/* ---------- trình duyệt ---------- */
let dung = 0, sai = 0, so = 0
const kiem = (t, dk, c = '') => { if (dk) { dung++; console.log(`  ✔ ${t} ${c}`) } else { sai++; console.log(`  ✘ ${t} ${c}`) } }
const trinh = await chromium.launch()
const loi = []
const t = await trinh.newPage({ viewport: { width: 1400, height: 880 } })
t.on('console', m => { if (m.type() === 'error') loi.push(m.text()) })
t.on('pageerror', e => loi.push(String(e)))
t.on('dialog', d => { loi.push('alert: ' + d.message()); d.dismiss() })
await t.addInitScript(`window.pywebview = { api: new Proxy({}, { get: (_, ten) => async (...args) =>
  (await fetch('/goi/chinh', { method: 'POST', body: JSON.stringify({ ten, args }) })).json() }) }`)

const co = async (chu, han = 8000) => { try { await t.getByText(chu, { exact: false }).first().waitFor({ timeout: han }); return true } catch { return false } }
const thay = async (sel, han = 8000) => { try { await t.locator(sel).first().waitFor({ timeout: han }); return true } catch { return false } }
const chup = async ten => {
  so++
  if (!ANH) return
  const f = join(ANH, `${String(so).padStart(2, '0')}-${ten}.png`)
  await t.screenshot({ path: f })
  console.log('    ảnh: ' + f)
}
const bam = (chu, sel = 'button') => t.locator(sel, { hasText: chu }).first().click()
const choChuXong = () => t.waitForFunction(() => (document.querySelector('.g-hoi-con')?.textContent ?? '') === '', null, { timeout: 8000 })

try {
  await t.goto(GOC + '/index.html')
  // Linux không có Consolas (font mono của app trên Windows), DejaVu Sans Mono thiếu chữ
  // Việt dựng sẵn → dấu bị tách. Liberation Mono đủ chữ — chỉ để ẢNH CHỤP giống Windows.
  await t.addStyleTag({ content: ':root{--mono:"Liberation Mono",Consolas,monospace !important}' })
  kiem('cửa sổ vẽ mở (bootstrap thật), có nút ◆ Màn chơi', await co('◆ Màn chơi', 15000))

  /* 1 · màn hình chính */
  await t.getByRole('button', { name: '◆ Màn chơi' }).click()
  kiem('◆ Màn chơi → màn hình chính của game', await thay('.g-chinh') && await co('CAT STUDIO'))
  kiem('chưa có khoá → màn hình chính nói rõ', await co('chưa có — cần để cỗ máy chạy được'))
  await t.waitForTimeout(400)
  await chup('man-hinh-chinh')

  const { uid, tok } = await (await fetch(GOC + '/_khoa_gia')).json()
  await bam('Khoá QuantConnect', '.g-menu-muc')
  await t.getByPlaceholder('vd. 123456').fill(uid)
  await t.getByPlaceholder('dán token vào đây').fill(tok)
  await t.locator('.ht-chan .nut', { hasText: 'Lưu' }).click()
  kiem('hộp khoá trong cửa sổ vẽ lưu qua cầu nối game', await co('Đã lưu khoá'))
  kiem('ô token xoá trắng sau khi lưu', (await t.getByPlaceholder('(đã lưu — nhập để thay)').inputValue()) === '')
  await t.locator('.ht-chan .nut', { hasText: 'Kiểm với QC' }).click()
  kiem('kiểm khoá → QC nhận', await co('QuantConnect nhận khoá'))
  await t.locator('.ht-chan .nut', { hasText: 'Đóng' }).click()
  kiem('màn hình chính báo đã có khoá', await co('đã có khoá'))

  /* 2 · truyện mở chương (lần đầu) */
  await bam('Chiến dịch', '.g-menu-muc')
  kiem('lần đầu vào chiến dịch → kể truyện mở chương', await thay('.g-truyen'))
  await choChuXong()
  await t.waitForTimeout(300)
  kiem('câu 1: Bà Tư', await co('Tiệm vàng nhà tôi'))
  await chup('truyen-ba-tu')
  await t.keyboard.press('Enter')
  await choChuXong()
  await t.waitForTimeout(300)
  kiem('Enter → câu 2: Mèo Thợ Cả', await co('Bà cần một cỗ máy'))
  await chup('truyen-meo-tho-ca')
  await t.keyboard.press('Escape')

  /* 3 · bản đồ */
  kiem('Esc bỏ qua truyện → bản đồ chương 1', await thay('.g-ban-do') && await co('Tiệm vàng nhà Tư'))
  const lop = async i => (await t.locator('.g-moc').nth(i).getAttribute('class')) ?? ''
  kiem('lúc đầu: 1-1 mở và nhấp nháy "chơi tiếp", 1-2…1-4 khoá',
       (await lop(0)).includes('tiep') && (await lop(1)).includes('khoa') && (await lop(3)).includes('khoa'))
  kiem('chương 2, 3 khoá — sắp ra mắt', (await t.locator('.g-chuong.khoa').count()) === 2)
  await t.waitForTimeout(400)
  await chup('ban-do-chuong-1')

  /* 4 · phiếu đặt máy */
  await bam('Nhận việc')
  kiem('phiếu đặt máy 1-1: boss, khoảng ngày, giác quan, sao', await thay('.g-phieu')
       && await co('Lãi hơn boss') && await co('01/01/2021') && await co('Giá đóng cửa'))
  kiem('phiếu KHÔNG lộ năm của màn ẩn (2022)', !(await t.locator('.g-phieu').innerText()).includes('2022'))
  await chup('phieu-dat-may-1-1')

  /* 5 · xưởng */
  await bam('Lắp máy gợi ý')
  kiem('xưởng: thanh game thay ribbon', await thay('.g-hud') && !(await t.locator('.ribbon').count()))
  kiem('máy gợi ý «Theo MA» lắp vào, KHÔNG lỗi', await co('Tay đang trống?') && await co('Giá trên MA?')
       && await co('Không có vấn đề nào'))
  kiem('chưa ▶ đầy đủ → Nộp tắt', await t.locator('.g-hud-chay .g-nut-nop').isDisabled())
  await t.waitForTimeout(900)
  await chup('xuong-may-theo-ma')

  /* 6 · ▶ đầy đủ nhiều lần — đổi núm như người chơi thật */
  const datThamSo = async ds => {
    await t.locator('.g-lk', { hasText: 'Núm vặn' }).click()
    await thay('.bang-tham-so')
    for (const [ten, gt] of Object.entries(ds)) {
      const i = await t.locator('.bang-tham-so tbody tr').evaluateAll((rows, ten) =>
        rows.findIndex(r => r.querySelector('input')?.value === ten), ten)
      await t.locator('.bang-tham-so tbody tr').nth(i).locator('input.so').fill(String(gt))
    }
    await t.locator('.ht-chan .nut.chinh', { hasText: 'Lưu' }).click()
    await t.waitForTimeout(900)            // phiếu nạp lại: vân tay mới → vé nộp đổi theo
  }
  const chayDayDu = async anh => {
    await t.locator('.g-hud-chay .g-nut-thu', { hasText: '▶ đầy đủ' }).click()
    const len = await thay('.g-the-chay', 8000)
    if (anh) { await t.waitForTimeout(700); await chup(anh) }
    await t.waitForFunction(() => !document.querySelector('.g-the-chay'), null, { timeout: 240000 })
    return len && await thay('.g-lop-kq', 20000)
  }
  kiem('▶ đầy đủ: thẻ "đang chạy trên QuantConnect" → kết quả', await chayDayDu('dang-chay-tren-qc'))
  const thu = [{ chu_ky_ma: 50, sl_atr: 3 }]
  for (const b of [{ chu_ky_ma: 20 }, { chu_ky_ma: 100 }, { chu_ky_ma: 30, sl_atr: 2 }]) {
    await bam('Sửa tiếp')
    await datThamSo(b)
    kiem(`đổi núm ${JSON.stringify(b)} → Nộp tắt (cỗ máy khác, chưa có vé)`,
         await t.locator('.g-hud-chay .g-nut-nop').isDisabled())
    thu.push({ ...thu[0], ...b })
    kiem('… ▶ đầy đủ lại', await chayDayDu(null))
  }
  // chọn lần lãi cao nhất (lịch sử: mới nhất đầu) rồi chạy lại đúng cỗ máy đó
  const p = (await goiPy('game_man', '1-1', null)).value
  const lai = p.lich_su.slice(0, thu.length).reverse().map(x => x.lai_pt)
  const tot = lai.indexOf(Math.max(...lai))
  console.log(`    lãi các lần thử: ${lai.join(' · ')} → chọn ${JSON.stringify(thu[tot])}`)
  await bam('Sửa tiếp')
  await datThamSo(thu[tot])
  kiem('chạy lại cỗ máy tốt nhất', await chayDayDu(null))
  await t.waitForTimeout(600)
  kiem('kết quả: ba histogram (Lãi · Sụt giảm · Độ gọn)', (await t.locator('.g-kq-histo .g-histo').count()) === 3)
  kiem('histogram đếm đủ mọi lần ▶ đầy đủ của màn', await co(`${thu.length + 1} lần thử`))
  kiem('có vạch Boss và vạch Bạn', (await t.locator('.g-vach-boss').count()) === 1
       && (await t.locator('.g-vach-ban').count()) === 3)
  await chup('ket-qua-ba-histogram')

  /* 7 · xem máy nghĩ */
  await bam('Xem máy nghĩ')
  kiem('thanh xem máy nghĩ + đường đi bằng TÊN khối', await thay('.g-xem') && await thay('.g-xem-buoc'))
  for (let i = 0; i < 40; i++) {
    if (/Mua/.test(await t.locator('.g-xem-duong').innerText().catch(() => '')) && i > 0) break
    await t.locator('.g-xem button[title="Lượt sau"]').click()
    await t.waitForTimeout(120)
  }
  await t.waitForTimeout(500)
  kiem('lượt có lệnh: Tay đang trống? ✓ → Giá trên MA? ✓ → Mua',
       (await t.locator('.g-xem-buoc.qua').count()) >= 2 && /Mua/.test(await t.locator('.g-xem-duong').innerText()))
  kiem('sơ đồ được tô theo lượt đó: 4 khối Entry sáng, dòng điều kiện đạt tô xanh',
       (await t.locator('.react-flow__node .soi-chay').count()) === 4
       && (await t.locator('.react-flow__node .dk-dat').count()) >= 2)
  await chup('xem-may-nghi')
  await t.keyboard.press('Escape')
  await t.waitForTimeout(200)
  kiem('Esc thôi xem máy nghĩ', !(await t.locator('.g-xem').count()))

  /* 8 · đấu màn ẩn */
  kiem('có vé → Nộp sáng', !(await t.locator('.g-hud-chay .g-nut-nop').isDisabled()))
  await t.locator('.g-hud-chay .g-nut-nop').click()
  kiem('màn hình đấu mở, CHƯA nộp (phải bấm «Bắt đầu đấu»)', await thay('.g-dau') && await co('Bắt đầu đấu')
       && (await goiPy('game_man', '1-1', null)).value.tien_do.so_lan_nop === 0)
  kiem('màn đấu nói năm đã thấy, KHÔNG nói ngày của màn ẩn', !(await t.locator('.g-dau').innerText()).includes('2022-'))
  await t.waitForTimeout(400)
  await chup('dau-man-an-truoc-tran')
  await bam('Bắt đầu đấu')
  await thay('.g-dau-san.dang', 8000)
  await t.waitForTimeout(600)
  await chup('dau-man-an-dang-chay')
  kiem('đấu xong: lật điểm → phán định + sao', await thay('.g-dau-ket', 240000))
  await t.waitForTimeout(2600)
  await chup('dau-man-an-ket-qua')
  const sao = await t.locator('.g-dau-ket .g-sao .co').count()
  kiem('sao trên màn đấu = sao Python chấm', sao === (await goiPy('game_man', '1-1', null)).value.tien_do.sao,
       `(${sao} ★)`)

  /* 9 · hoàn thành → mở khoá */
  await bam('Tiếp tục')
  if (sao >= 1) {
    kiem('màn hình hoàn thành: mở khoá 1-2 kèm giác quan mới', await thay('.g-xong') && await co('ĐÃ MỞ KHOÁ')
         && await co('ATR'))
    await t.waitForTimeout(2200)
    await chup('hoan-thanh-mo-khoa')
    await bam('Về bản đồ')
    await thay('.g-ban-do')
    await t.waitForTimeout(400)
    kiem('bản đồ: 1-1 có sao, 1-2 đã mở, 1-3 vẫn khoá', (await lop(0)).includes('xong')
         && !(await lop(1)).includes('khoa') && (await lop(2)).includes('khoa'))
    await t.locator('.g-moc').nth(1).click()
    await t.waitForTimeout(500)
    await chup('ban-do-sau-mo-khoa')
    await bam('Nhận việc')
    kiem('phiếu 1-2: giác quan MỚI, máy gợi ý «Hai chiều», giữ được cỗ máy đang vẽ',
         await thay('.g-phieu') && await co('MỚI') && await co('Hai chiều') && await co('Giữ cỗ máy đang vẽ'))
    await chup('phieu-1-2-giac-quan-moi')
  } else {
    kiem('chưa có sao → về xưởng sửa tiếp', await thay('.g-hud'))
  }
  kiem('không lỗi console / alert', loi.length === 0, loi.slice(0, 5).join(' | '))
} catch (e) {
  sai++
  console.log('  ✘ dừng giữa chừng: ' + String(e).split('\n')[0])
} finally {
  await trinh.close()
  cau.kill()
}
console.log(`\n  ${dung} đúng · ${sai} sai`)
process.exit(sai ? 1 : 0)
