/* MẠCH CHẠY — kết quả LEAN thật thành cuộn phim, và cái VAN phải đóng ĐÚNG CHỖ.
 *
 * VÌ SAO BÀI NÀY PHẢI CÓ
 * ----------------------
 * Màn «Chạy máy» nói với người xem một câu rất mạnh: *"nó không vào lệnh vì dòng dừng
 * ở cái cổng này"*. Mà LEAN ngắt ở điều kiện sai đầu tiên nên nó KHÔNG nói ra điều ấy —
 * `mach_chay.ts` SUY RA (chủ dự án chốt 19/10/2026, thiết kế §8.2). Một phép suy sai ở
 * đây không hỏng ồn ào: màn hình vẫn chạy mượt, van vẫn đóng mở, chỉ là nó CHỈ SAI CỔNG.
 * Và nó sai một cách rất thuyết phục — đúng loại lỗi không ai bắt được bằng mắt.
 *
 * Nên chỗ này phải có một bài kiểm bằng máy, và bài kiểm phải chạy trên HÌNH DẠNG THẬT
 * của dữ liệu LEAN. Mẫu dưới đây chép từ một lượt chạy thật (`MauRSI`, 15 lệnh, nhãn
 * `[1A.1] RSI(14) < 30`) và một sơ đồ thật (`du_lieu/strategy/RSI sample.json`, 5 khối):
 * số khối, chuỗi nhãn, đường vốn dạng NẾN `[giây, mở, cao, thấp, đóng]` — y nguyên.
 *
 * Chạy:  node webui/kiem/mach_chay.mjs
 */
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// Biên dịch `src/man/mach_chay.ts` rồi nạp bản .js. Tệp ấy cố ý chỉ `import type`, nên
// bản dịch ra KHÔNG còn một lời gọi nào sang React hay cầu nối Python — nạp được trần.
// Không tự bóc chú thích kiểu bằng regex: bóc bằng tay là một bộ biên dịch thứ hai.
const goc = fileURLToPath(new URL('..', import.meta.url))
const ra = mkdtempSync(join(tmpdir(), 'catmach-'))
try {
  execFileSync('npx', ['tsc', 'src/man/mach_chay.ts', '--target', 'es2020',
                       '--module', 'es2020', '--skipLibCheck', '--types', 'node',
                       '--outDir', ra],
               { cwd: goc, stdio: 'pipe', shell: true })
} catch (e) {
  // tsc có thể thoát khác 0 vì lỗi kiểu ở nơi khác mà VẪN xuất ra file.
  if (!existsSync(join(ra, 'man', 'mach_chay.js'))) {
    console.error(String(e.stdout ?? e))
    throw new Error('không dịch nổi src/man/mach_chay.ts')
  }
}
const { dungMach, soKhoiCuaNhan, idDay } =
  await import(pathToFileURL(join(ra, 'man', 'mach_chay.js')).href)

let dung = 0
let sai = 0
const kiem = (ten, dk, chi = '') => {
  if (dk) { dung++; console.log(`  ✔ ${ten} ${chi}`) }
  else { sai++; console.log(`  ✘ ${ten} ${chi}`) }
}

/* ---------------------------------------------------------------- mẫu THẬT */

/** Sơ đồ «RSI sample»: Bắt đầu -> HAI nhánh song song, mỗi nhánh một cổng rồi một
 *  hành động. Số khối lấy từ `api.soat` thật, không gõ bịa. */
const BAT_DAU = 'seb6f2bd1'
const CONG_A = 'sb7431523'      // «Oversold?»
const LAM_A = 's47d91220'       // «Go all in»
const CONG_B = 'sff6bcaf1'      // «Overbought?»
const LAM_B = 's3525c027'       // «Exit everything»

const the = (id, laCong, title) => [id, {
  id, kind: 'action', title, badges: [], lines: [], so_hanh_dong: 1, la_cong: laCong,
}]

const SOAT = {
  entry: BAT_DAU,
  thu_tu: { [BAT_DAU]: '1', [CONG_A]: '1A', [LAM_A]: '1A.1',
            [CONG_B]: '1B', [LAM_B]: '1B.1' },
  the: Object.fromEntries([
    the(BAT_DAU, false, 'Start'),
    the(CONG_A, true, 'Oversold?'),
    the(LAM_A, false, 'Go all in'),
    the(CONG_B, true, 'Overbought?'),
    the(LAM_B, false, 'Exit everything'),
  ]),
  edges: [
    { from: BAT_DAU, to: CONG_A, port: 'out' },
    { from: CONG_A, to: LAM_A, port: 'out' },
    { from: BAT_DAU, to: CONG_B, port: 'out' },
    { from: CONG_B, to: LAM_B, port: 'out' },
  ],
  co_may: {}, tom_tat_co_may: [], van_de: [], vong: {},
}

const BUOC = [
  { id: BAT_DAU, kind: 'start' },
  { id: CONG_A, kind: 'action', type: 'hoi_thi_truong' },
  { id: LAM_A, kind: 'action', type: 'lam_dat_ty_trong' },
  { id: CONG_B, kind: 'action', type: 'hoi_thi_truong' },
  { id: LAM_B, kind: 'action', type: 'lam_dong' },
]

const lenh = (id, luc, tag, soLuong, hopLe = true) => ({
  id, ma: 'SPY', luc, loai: 'Khớp lúc đóng', so_luong: soLuong, gia: 200,
  trang_thai: 'Đã khớp', hop_le: hopLe, tag,
})

/** Đường vốn dạng NẾN, đúng hình LEAN trả về: `[giây, mở, cao, thấp, đóng]`.
 *  Bốn ngày; ngày 2 có lệnh MUA, ngày 4 có lệnh BÁN. */
const T = [1420088400, 1420174800, 1420261200, 1420347600]
const KQ = {
  ok: true, loi: '', id: 'MauRSI/20261018-202443',
  bieu_do: [{
    ten: 'Strategy Equity', hien: true,
    duong: [
      // ⚠ HAI đường trong CÙNG một bảng, và `Return` DÀI chuyện riêng của nó. Lấy
      // nhầm đường là đồng hồ tiền chạy theo phần trăm lợi nhuận ngày.
      { ten: 'Return', kieu: 'cot', don_vi: '%', diem: T.map(t => [t, 0]) },
      { ten: 'Equity', kieu: 'nen', don_vi: '$',
        diem: [[T[0], 100000, 100000, 100000, 100000],
               [T[1], 100000, 101000, 99000, 101000],
               [T[2], 101000, 102000, 100500, 102000],
               [T[3], 102000, 102500, 101000, 101500]] },
    ],
  }],
  lenh: [lenh(1, '2015-01-02 00:00:00', '[1A.1] RSI(14) < 30', 85),
         lenh(2, '2015-01-04 00:00:00', '[1B.1] RSI(14) > 70', -85)],
}

/* ------------------------------------------------------- nhãn -> số khối */
console.log('\n▸ Nhãn trên lệnh -> số khối')
kiem('`[1A.1] RSI(14) < 30` ra `1A.1`',
     soKhoiCuaNhan('[1A.1] RSI(14) < 30') === '1A.1')
kiem('`[1] không điều kiện` ra `1`', soKhoiCuaNhan('[1] không điều kiện') === '1')
kiem('nhãn rỗng ra chuỗi rỗng', soKhoiCuaNhan('') === '')
// Một nhãn người dùng tự gõ ở ô «Ghi chú» KHÔNG theo khuôn — không được nhận bừa.
kiem('nhãn tự gõ không theo khuôn thì KHÔNG nhận', soKhoiCuaNhan('mua manh tay') === '')
kiem('id dây khớp đúng công thức `from->to:port`',
     idDay({ from: 'a', to: 'b', port: 'out' }) === 'a->b:out')

/* ------------------------------------------------------- cuộn phim thật */
console.log('\n▸ Lượt chạy thật -> bốn nhịp, van đóng mở đúng chỗ')
const m = dungMach(SOAT, KQ, BUOC)
kiem('bốn nhịp, lấy theo đường vốn', m.nhip.length === 4, `— ${m.nhip.length}`)
kiem('đọc đường `Equity` chứ không phải `Return`',
     m.vonDau === 100000 && m.nhip[1].von === 101000,
     `— vốn đầu ${m.vonDau}, nhịp 2 ${m.nhip[1].von}`)
kiem('vốn lấy GIÁ ĐÓNG của nến (phần tử cuối), không lấy giá mở',
     m.nhip[3].von === 101500, `— ${m.nhip[3].von}`)
kiem('hai cổng, không nhận khối nào khác làm cổng',
     m.cong.length === 2 && m.cong.includes(CONG_A) && m.cong.includes(CONG_B))
kiem('không lệnh nào lạc', m.soLenhLac === 0, `— ${m.soLenhLac}`)
kiem('cả hai khối hành động đều đã nổ ít nhất một lần',
     m.khoiNo.length === 2 && m.khoiNo.includes(LAM_A) && m.khoiNo.includes(LAM_B))

const n0 = m.nhip[0]
kiem('nhịp 1 không lệnh: CẢ HAI van đóng',
     n0.van[CONG_A] === 'dong' && n0.van[CONG_B] === 'dong',
     `— A=${n0.van[CONG_A]} B=${n0.van[CONG_B]}`)
kiem('và không sợi dây nào có dòng… ', n0.day.length === 2,
     `— ${n0.day.length} sợi (hai đoạn tới hai cổng: dòng CHẮC CHẮN tới được cổng)`)
kiem('…nhưng đúng là hai đoạn TỚI cổng, không phải đoạn SAU cổng',
     n0.day.includes(idDay(SOAT.edges[0])) && n0.day.includes(idDay(SOAT.edges[2]))
     && !n0.day.includes(idDay(SOAT.edges[1])))

const n1 = m.nhip[1]
kiem('nhịp 2 có lệnh MUA: van A MỞ', n1.van[CONG_A] === 'mo', `— ${n1.van[CONG_A]}`)
// ⭐ ĐÂY LÀ PHÉP SUY ĐẮT NHẤT CỦA CẢ MÀN HÌNH: nhánh B không nổ, mà dưới cổng B không
// còn cổng nào nữa — nên dòng dừng ĐÚNG ở B, không phải "dừng đâu đó".
kiem('cùng nhịp ấy van B ĐÓNG — suy ra được, không cần log',
     n1.van[CONG_B] === 'dong', `— ${n1.van[CONG_B]}`)
kiem('khối A nổ, khối B không', n1.no.length === 1 && n1.no[0] === LAM_A)
kiem('dây nhánh A có dòng chạy tới hết',
     n1.day.includes(idDay(SOAT.edges[0])) && n1.day.includes(idDay(SOAT.edges[1])))
kiem('dây SAU cổng B thì không', !n1.day.includes(idDay(SOAT.edges[3])))
kiem('không lệnh nào bị từ chối', n1.tuChoi.length === 0)

const n3 = m.nhip[3]
kiem('nhịp 4 có lệnh BÁN: van B mở, van A đóng',
     n3.van[CONG_B] === 'mo' && n3.van[CONG_A] === 'dong',
     `— A=${n3.van[CONG_A]} B=${n3.van[CONG_B]}`)

/* --------------------------------------------- lệnh bị sàn TỪ CHỐI */
console.log('\n▸ Lệnh bị sàn TỪ CHỐI — hành động VẪN chạy, nên cổng vẫn mở')
const mTuChoi = dungMach(SOAT, {
  ...KQ,
  lenh: [lenh(1, '2015-01-02 00:00:00', '[1A.1] RSI(14) < 30', 85, false)],
}, BUOC)
kiem('cổng trên nó vẫn MỞ', mTuChoi.nhip[1].van[CONG_A] === 'mo')
kiem('và khối được đánh dấu bị từ chối', mTuChoi.nhip[1].tuChoi.includes(LAM_A))

/* ------------------------- CHUỖI HAI CỔNG: phải nói «chưa rõ», không chỉ bừa */
console.log('\n▸ Chuỗi HAI cổng nối tiếp — không suy ra được thì phải nói «chưa rõ»')
const G1 = 'g1'
const G2 = 'g2'
const A1 = 'a1'
const SOAT2 = {
  entry: BAT_DAU,
  thu_tu: { [BAT_DAU]: '1', [G1]: '1A', [G2]: '1A.1', [A1]: '1A.1.1' },
  the: Object.fromEntries([
    the(BAT_DAU, false, 'Start'), the(G1, true, 'RSI thấp?'),
    the(G2, true, 'Còn tiền?'), the(A1, false, 'Mua'),
  ]),
  edges: [{ from: BAT_DAU, to: G1, port: 'out' },
          { from: G1, to: G2, port: 'out' },
          { from: G2, to: A1, port: 'out' }],
  co_may: {}, tom_tat_co_may: [], van_de: [], vong: {},
}
const BUOC2 = [{ id: BAT_DAU, kind: 'start' }, { id: G1, kind: 'action' },
               { id: G2, kind: 'action' }, { id: A1, kind: 'action' }]
const m2 = dungMach(SOAT2, {
  ...KQ, lenh: [lenh(1, '2015-01-02 00:00:00', '[1A.1.1] RSI thấp và còn tiền', 85)],
}, BUOC2)
kiem('nhịp CÓ lệnh: cả hai cổng đều MỞ (chắc chắn)',
     m2.nhip[1].van[G1] === 'mo' && m2.nhip[1].van[G2] === 'mo')
kiem('nhịp KHÔNG lệnh: cổng ĐẦU chuỗi báo «chưa rõ», KHÔNG báo đóng',
     m2.nhip[0].van[G1] === 'lang', `— ${m2.nhip[0].van[G1]}`)
kiem('và cổng SAU nó cũng «chưa rõ» — chưa biết dòng có tới đó không',
     m2.nhip[0].van[G2] === 'lang', `— ${m2.nhip[0].van[G2]}`)

/* ---------- KHỐI CHƯA BAO GIỜ NỔ: im lặng của nó KHÔNG phải bằng chứng ---------- */
console.log('\n▸ Khối không bao giờ sinh lệnh (Ghi chú, Vẽ bảng…) — im lặng của nó '
            + 'KHÔNG được làm cổng đóng')
// Năm loại khối hành động không bao giờ sinh lệnh. Lấy sự im lặng của chúng làm bằng
// chứng thì mọi cổng nằm trên chúng ĐÓNG VĨNH VIỄN suốt cả lượt — một màn hình đầy van
// đóng, sai hết, mà trông rất thuyết phục.
const GHI = 'ghi1'
const SOAT3 = {
  entry: BAT_DAU,
  thu_tu: { [BAT_DAU]: '1', [CONG_A]: '1A', [GHI]: '1A.1' },
  the: Object.fromEntries([
    the(BAT_DAU, false, 'Start'), the(CONG_A, true, 'Oversold?'),
    the(GHI, false, 'Ghi chú'),
  ]),
  edges: [{ from: BAT_DAU, to: CONG_A, port: 'out' },
          { from: CONG_A, to: GHI, port: 'out' }],
  co_may: {}, tom_tat_co_may: [], van_de: [], vong: {},
}
const m3 = dungMach(SOAT3, { ...KQ, lenh: [] },
                    [{ id: BAT_DAU, kind: 'start' }, { id: CONG_A, kind: 'action' },
                     { id: GHI, kind: 'action', type: 'lam_ghi_chu' }])
kiem('cả lượt KHÔNG một lệnh nào: van chỉ dám nói «chưa rõ»',
     m3.nhip.every(n => n.van[CONG_A] === 'lang'),
     `— ${[...new Set(m3.nhip.map(n => n.van[CONG_A]))].join(', ')}`)
kiem('và không khối nào vào tập suy luận', m3.khoiNo.length === 0)

/* ------------------------------------------------ ĐƯỜNG ↻ không được tính */
console.log('\n▸ Đường ↻ QUAY LẠI đi ngược dòng chảy — không được tính vào đường đi')
/* ⚠ MẪU PHẢI LÀ MỘT ĐƯỜNG TẮT, không phải một đường ↻ bất kỳ, và chỗ này đã bị bắt
 * một lần: bản đầu thêm ↻ vào một khối mà phép duyệt rộng đã tới được bằng đường
 * ngắn hơn rồi — nên bỏ hẳn phép lọc `so_vong` mà bài kiểm vẫn xanh.
 *
 * Đây là ↻ từ cổng ĐẦU chuỗi tới thẳng khối hành động, tức một đường TẮT nhảy qua cổng
 * thứ hai. Tính nó vào thì:
 *   · nhịp CÓ lệnh — cổng G2 không được tính là đã mở, dù nó chắc chắn đã mở;
 *   · nhịp KHÔNG lệnh — chuỗi tụt từ hai cổng xuống một, nên van G1 bị CHỈ ĐÍCH DANH
 *     là chỗ dòng dừng, đúng cái câu app không chứng minh được.
 * Hỏng ở đây là hỏng chính lời hứa của màn hình. */
const SOAT4 = {
  ...SOAT2,
  edges: [...SOAT2.edges, { from: G1, to: A1, port: 'out', so_vong: 3 }],
}
const m4 = dungMach(SOAT4, {
  ...KQ, lenh: [lenh(1, '2015-01-02 00:00:00', '[1A.1.1] RSI thấp và còn tiền', 85)],
}, BUOC2)
kiem('nhịp có lệnh: CẢ HAI cổng vẫn mở, đường ↻ không nhảy qua cổng nào',
     m4.nhip[1].van[G1] === 'mo' && m4.nhip[1].van[G2] === 'mo',
     `— G1=${m4.nhip[1].van[G1]} G2=${m4.nhip[1].van[G2]}`)
kiem('nhịp không lệnh: vẫn là «chưa rõ», đường ↻ không làm chuỗi ngắn đi',
     m4.nhip[0].van[G1] === 'lang', `— ${m4.nhip[0].van[G1]}`)
kiem('và không sợi ↻ nào được coi là có dòng',
     !m4.nhip[1].day.includes(idDay(SOAT4.edges[3])))
kiem('dòng vẫn chạy theo DÂY THƯỜNG, qua đủ cả ba đoạn',
     SOAT2.edges.every(e => m4.nhip[1].day.includes(idDay(e))))

/* ------------------------------------- lệnh LẠC: sơ đồ đã sửa sau lượt chạy */
console.log('\n▸ Nhãn không khớp khối nào — ĐẾM ĐỂ NÓI RA, không nuốt')
const m5 = dungMach(SOAT, {
  ...KQ, lenh: [lenh(1, '2015-01-02 00:00:00', '[7Z.9] khối đã xoá', 85)],
}, BUOC)
kiem('đếm được một lệnh lạc', m5.soLenhLac === 1, `— ${m5.soLenhLac}`)
kiem('và không khối nào bị nhận nhầm là đã nổ', m5.khoiNo.length === 0)

/* ----------------------------------- KHÔNG có đường vốn: không được sập */
console.log('\n▸ LEAN không trả đường vốn — vẫn xem được, chỉ là không vẽ đường')
const m6 = dungMach(SOAT, { ...KQ, bieu_do: [] }, BUOC)
kiem('nói thẳng là không có đường vốn', m6.coVon === false)
kiem('vẫn dựng nhịp từ giờ của mấy cái lệnh', m6.nhip.length === 2,
     `— ${m6.nhip.length}`)
kiem('và van vẫn đóng mở đúng', m6.nhip[0].van[CONG_A] === 'mo'
     && m6.nhip[0].van[CONG_B] === 'dong')
const m7 = dungMach(SOAT, { ...KQ, bieu_do: [], lenh: [] }, BUOC)
kiem('không đường vốn mà cũng không lệnh: một nhịp rỗng, không sập',
     m7.nhip.length === 1 && m7.coVon === false)

console.log(`\n  ${sai ? '✘' : '✔'} ${dung}/${dung + sai} phép kiểm qua`)
process.exit(sai ? 1 : 0)
