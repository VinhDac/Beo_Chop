// BỘ CÔNG CỤ SONG NGỮ — một lệnh làm hết phần máy móc của việc dịch giao diện.
//
//   npm run dich               bọc chữ Việt mới vào tr()/trx(), dàn dòng, rồi soát
//   npm run dich -- --don      như trên, rồi bỏ khoá thừa khỏi bảng dịch
//   node dich/chay.mjs --chi-soat
//                              chỉ soát, KHÔNG ghi gì — `npm run build` và
//                              tests/test_ngon_ngu.py chạy lối này
//
// QUY TRÌNH khi sửa / thêm giao diện (xem đầu `src/ngon_ngu.ts`):
//   1. Viết chữ tiếng Việt như thường — bọc tr() sẵn càng tốt, quên thì bước 2 bọc hộ.
//   2. `npm run dich` — nó in ra đúng những câu chưa có bản tiếng Anh, dạng dán thẳng.
//   3. Dán vào `src/tieng_anh.ts` đúng nhóm tệp, điền bản tiếng Anh (theo bảng thuật
//      ngữ đầu tệp). Chạy lại tới khi sạch.
// Thiếu bản dịch thì build dừng và bài kiểm đỏ: không có đường lọt ra bản phát hành.
import { boc } from './boc.mjs'
import { dan } from './dan.mjs'
import { donBang, soat } from './soat.mjs'
import { chuoi, dsTep } from './chung.mjs'

const chiSoat = process.argv.includes('--chi-soat')
const don = process.argv.includes('--don')
const ds = dsTep()
let loi = false

// 1. Bọc chữ Việt chưa bọc. Lối chỉ soát: bọc NHÁP, chỗ nào còn bọc được là chỗ bị sót.
const bocDuoc = ds.flatMap(p => boc(p, !chiSoat).noi)
if (bocDuoc.length) {
  if (chiSoat) {
    loi = true
    console.log(`✘ ${bocDuoc.length} chỗ chữ Việt CHƯA bọc tr() — chạy \`npm run dich\` để bọc:`)
  } else console.log(`✔ đã bọc ${bocDuoc.length} chỗ chữ Việt mới:`)
  for (const n of bocDuoc) console.log('    ' + n)
}

// 2. Dàn dòng — chỉ ở lối có ghi.
if (!chiSoat) {
  const danDuoc = ds.flatMap(p => dan(p, true).noi)
  if (danDuoc.length) console.log(`✔ đã dàn lại ${danDuoc.length} dòng dài`)
}

// 3. Soát bảng dịch.
const kq = soat()
// Không thấy nhãn Python thì DỪNG ở mọi lối, trước cả --don: bỏ qua là cổng xanh mà nhãn
// Python không ai soát, còn --don sẽ coi mọi bản dịch của chúng là thừa mà xoá sạch.
if (kq.loiPython) {
  console.log('✘ không chạy được tools/nhan_python_dich.py — không soát được nhãn Python:')
  for (const d of kq.loiPython.split('\n')) console.log('    ' + d)
  process.exit(1)
}
if (kq.thieu.length) {
  loi = true
  console.log(`✘ ${kq.thieu.length} câu chưa có bản tiếng Anh. Dán vào src/tieng_anh.ts, đúng nhóm, `
    + 'rồi điền phần sau dấu hai chấm:')
  const theoTep = new Map()
  for (const [k, noi] of kq.thieu) {
    const t = noi.split(':')[0]
    if (!theoTep.has(t)) theoTep.set(t, [])
    theoTep.get(t).push(k)
  }
  for (const [t, cau] of theoTep) {
    console.log(`  // ── ${t}`)
    for (const k of cau) console.log(`  ${chuoi(k)}: '',`)
  }
}
if (kq.lech.length) {
  loi = true
  console.log(`✘ ${kq.lech.length} câu có ô điền {n} hai bên lệch nhau:`)
  for (const [k, noi] of kq.lech) console.log(`    ${noi}  ${k}`)
}
if (kq.thua.length) {
  if (don) console.log(`✔ đã bỏ ${donBang(kq.thua)} khoá thừa khỏi bảng dịch`)
  else {
    console.log(`⚠ ${kq.thua.length} khoá trong bảng dịch không còn dùng — \`npm run dich -- --don\` để bỏ:`)
    for (const k of kq.thua.slice(0, 20)) console.log('    ' + k.slice(0, 90))
    if (kq.thua.length > 20) console.log('    …')
  }
}
if (!loi) console.log('✔ song ngữ đủ: mọi câu tiếng Việt của giao diện đã có bản tiếng Anh')
process.exit(loi ? 1 : 0)
