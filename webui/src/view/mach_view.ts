/* BỘ CHUYỂN: một lượt LEAN đã chạy -> thứ cửa sổ View bày ra.
 *
 * Cửa sổ Strategy Tester cũ chạy engine riêng của app nên có sẵn mọi thứ tại từng
 * nến. Bản nay app KHÔNG tính gì (D-11) — mọi con số do LEAN in ra lúc chạy
 * (`sinh_ma._dong_bay`). File này chỉ việc XẾP LẠI những gì LEAN trả về.
 *
 * ⚠ MỘT LƯỢT CHẠY LÀ MỘT, dù nó chạy trên năm chục mã. Nên:
 *
 *   · TRỤC THỜI GIAN là của CẢ LƯỢT — hợp của mọi mã. Lấy trục của một mã làm trục
 *     chung thì con trỏ đứng ở «nến thứ 42 của AAPL», mà lệnh của NVDA hôm ấy rơi
 *     vào đâu thì không ai biết. Rổ động còn tệ hơn: mã vào rổ tháng thứ hai thì
 *     trục của nó bắt đầu từ giữa lượt.
 *   · NHẬT KÝ là của CẢ LƯỢT — mọi lệnh, mọi mã. Lọc theo mã đang xem thì một lượt
 *     31 lệnh trên năm chục mã bày ra gần như trống, và đó đúng là thứ đã xảy ra.
 *   · Chỉ CHART mới theo từng mã, vì một cây nến thì phải của một mã.
 *
 * ⚠ KHÔNG TÍNH THÊM MỘT CON SỐ NÀO Ở ĐÂY. Cám dỗ là nội suy: nến thì 941 điểm mà một
 * đại lượng chỉ 900 (LEAN bỏ nến chỉ báo chưa chín), nên dễ nghĩ tới việc «điền cho
 * đủ». Điền là bịa — bảng sẽ bày một con số LEAN chưa từng tính, ở đúng những nến
 * người ta mở cửa sổ ra để soi. Thiếu thì để thiếu, và bày dấu «—».
 */
import { tr } from '../ngon_ngu'
import type { DongLenh, DongVet, KetQuaChay } from '../types'

/** Tên hai HỌ bảng `sinh_ma` bảo LEAN vẽ, mỗi mã một cặp: `Price SPY`,
 *  `Quantities SPY`. Đổi một bên là bảng trống — xem `sinh_ma.BANG_GIA`.
 *
 *  Chỗ duy nhất phải TÁCH CHỮ là lấy tên mã ra khỏi tên bảng: việc bày biện, không
 *  phải việc đoán nghĩa. Còn ĐẠI LƯỢNG NÀO VẼ Ở ĐÂU thì `sinh_ma` đã quyết (nó đọc
 *  `hoi.DON_VI_GIA`) — cùng thang giá thì in thẳng vào bảng `Price`. */
export const BANG_GIA = 'Price'
export const BANG_SO = 'Quantities'

export { soKhoiCuaNhan } from '../man/mach_chay'

/** `2020-03-12 09:31:00` (giờ UTC) -> giây UNIX. */
export function giayCuaLuc(luc: string): number {
  const t = Date.parse(String(luc || '').replace(' ', 'T') + 'Z')
  return Number.isFinite(t) ? Math.floor(t / 1000) : 0
}

/** MỘT DÒNG NHẬT KÝ — một việc đã xảy ra, trên một mã, tại một mốc. */
export interface DongNhatKy {
  /** Giây UNIX. Con trỏ nhảy tới đây; chart của mã nào thì mã ấy tự tìm nến. */
  t: number
  ngay: string
  ma: string
  chu: string
  /** Nhãn khối (`[1A.1] RSI(14) < 30`). Có nhãn thì bấm còn SOI được đường trên sơ đồ. */
  tag: string
  /** Lệnh bị sàn từ chối. */
  hong: boolean
  /** MỘT VIỆC ĐÃ LÀM (một cái lệnh), không phải một dòng tường thuật.
   *
   *  ⚠ DÒNG CÓ VIỆC KHÔNG BAO GIỜ BỊ GỘP — xem `NhatKy`. Hai lệnh mua cùng mã cùng
   *  giá vẫn là HAI cái lệnh, gộp thành «×2» là giấu mất một cái. Dòng tường thuật
   *  («dòng dừng ở [3]») thì lặp lại hàng chục nến liền, và gộp mới đọc nổi. */
  viec: boolean
  /** Dòng này nói hộ BAO NHIÊU MÃ. 1 với một cái lệnh; nhiều hơn khi cả một nhóm mã
   *  cùng nhịp cùng dừng ở một chỗ — xem `dungLuot`. */
  soMa: number
}

/** CẢ LƯỢT — thứ không thuộc riêng mã nào. */
export interface LuotXem {
  /** Trục thời gian của cả lượt: mọi mốc, đã sắp, không trùng. */
  truc: number[]
  /** Mã nào có chart, theo thứ tự `sinh_ma` khai. */
  dsMa: string[]
  nhatKy: DongNhatKy[]
  /** BƯỚC NHỊP GỐC — bao nhiêu giây giữa hai nến LEAN in ra, lấy khoảng cách HAY GẶP
   *  NHẤT chứ không phải trung bình: nến ngày có cuối tuần, nghỉ lễ, và mã vào rổ
   *  giữa chừng, nên trung bình của một lượt nến ngày ra khoảng 1,4 ngày — một con số
   *  không phải khung nào cả. Ô «Khung hiển thị» chỉ bày khung LỚN HƠN bước này: gộp
   *  nến thì được, chẻ một cây nến ra làm năm thì không ai làm được. */
  buoc: number
}

function bangGia(kq: KetQuaChay) {
  return (kq.bieu_do ?? []).filter(b => b.ten.startsWith(BANG_GIA + ' '))
}

/** VẾT TỪNG NHỊP -> dòng nhật ký.
 *
 *  ⚠ ĐỌC LỜI CỖ MÁY, KHÔNG SUY. `mach_chay` phải suy van đóng từ chỗ LEAN im lặng, và
 *  lời dặn đầu tệp ấy kể rõ chỗ suy có thể OAN (`set_holdings` không sinh lệnh khi tỷ
 *  trọng đang đúng: cổng mở, hành động chạy, LEAN im — nhìn y hệt cổng đóng). Vết thì
 *  không phải suy: chính cỗ máy ghi ra cổng nào nó chạy tới và cổng cho ra gì.
 *
 *  ⚠ CHỖ DỪNG LÀ CỔNG ĐÓNG CUỐI CÙNG, không phải cổng đầu. Một điểm rẽ sinh ra
 *  `if/elif/elif`: nhánh đầu trượt thì cỗ máy THỬ TIẾP nhánh sau, nên nói «dừng ở
 *  cổng đầu» là nói sai — dòng chảy còn đi nữa. Cổng đóng sau cùng mới là chỗ nó thật
 *  sự hết đường.
 *
 *  ⚠ GỘP MẤY MÃ CÙNG NHỊP CÙNG CHỖ DỪNG LÀM MỘT DÒNG. Một rổ năm chục mã mà mỗi mã
 *  một dòng thì một nhịp ra năm chục dòng giống nhau, và cuộn cả ngày không hết một
 *  tuần. Gộp trong CÙNG MỘT NHỊP nên không xáo trộn thứ tự thật của lượt chạy: nó chỉ
 *  đếm lại mấy dòng vốn đã đứng sát nhau và nói đúng một chuyện. */
function dungVet(ds: DongVet[]): DongNhatKy[] {
  /** `<mốc>|<số khối dừng>` -> dòng đã dựng. Một nhịp một bảng là đủ, nhưng vết của
   *  một nhịp về liền nhau nên dùng một bảng chung cho cả lượt cũng không lẫn: khoá
   *  đã mang mốc. */
  const bang = new Map<string, DongNhatKy>()
  const ra: DongNhatKy[] = []
  for (const v of ds) {
    const cong = v.cong ?? []
    if (!cong.length) continue
    const cuoi = cong[cong.length - 1]
    // Cổng CUỐI mở = dòng chảy qua hết mấy cổng nó đã thử; chuyện xảy ra sau đó (ra
    // lệnh, hay không ra vì tỷ trọng đang đúng) thì dòng lệnh kể, không phải dòng này.
    const qua = cuoi[1]
    const so = qua ? cuoi[0]
      : [...cong].reverse().find(c => !c[1])?.[0] ?? cuoi[0]
    const t = giayCuaLuc(v.luc)
    const khoa = `${t}|${qua ? '+' : '-'}${so}`
    const co = bang.get(khoa)
    if (co) {
      co.soMa++
      // Nhiều mã thì không in tên mã nào: in tên mã đầu rồi đếm «×5» là nói dối về
      // bốn mã kia. Số mã thì đúng, và bấm vào vẫn nhảy tới đúng nhịp.
      co.ma = ''
      continue
    }
    const d: DongNhatKy = {
      t, ngay: String(v.luc).slice(0, 10), ma: v.ma, soMa: 1, viec: false, hong: false,
      tag: `[${so}]`,
      chu: qua ? tr('dòng qua cổng {0}', so) : tr('dòng dừng ở {0}', so),
    }
    bang.set(khoa, d)
    ra.push(d)
  }
  return ra
}

export function dungLuot(kq: KetQuaChay): LuotXem {
  const dsMa = bangGia(kq).map(b => b.ten.slice(BANG_GIA.length + 1))

  // TRỤC CHUNG: hợp mọi mốc của mọi mã. Mã vào rổ giữa chừng thì trục của nó ngắn,
  // nhưng trục CHUNG vẫn phủ cả lượt — con trỏ đi hết lượt chứ không hết một mã.
  const moc = new Set<number>()
  for (const b of bangGia(kq)) {
    const d = (b.duong ?? []).find(x => x.kieu === 'nen') ?? b.duong?.[0]
    for (const p of d?.diem ?? []) moc.add(p[0])
  }
  const truc = [...moc].sort((a, b) => a - b)

  const nhatKy: DongNhatKy[] = (kq.lenh ?? []).map(l => {
    const t = giayCuaLuc(l.luc)
    const sl = Number(l.so_luong)
    return {
      t, ngay: String(l.luc).slice(0, 10), ma: l.ma, tag: l.tag, hong: !l.hop_le,
      viec: true, soMa: 1,
      // ⚠ `tr()` QUANH CHỮ CỦA PYTHON. `chay_lean.LOAI_LENH` là một bảng tiếng Việt
      // KHÔNG bọc `tr` ở phía Python (nó là bảng tra, không phải câu), nên giao diện
      // phải dịch — đúng lối bảng Lệnh của cửa sổ Kết quả làm. Thiếu nó thì nhật ký
      // bày «Khớp lúc mở» giữa một cửa sổ tiếng Anh.
      // ⚠ LỆNH THỊ TRƯỜNG KHÔNG CÓ GIÁ ĐẶT — LEAN ghi `price` của nó bằng **0**, nên
      // bày thẳng ra là một dòng nhật ký «Market on open 0», trông y như một con bug.
      // Số lượng thì lệnh nào cũng có, và với lệnh thị trường nó là con số DUY NHẤT
      // có nghĩa ở đó.
      chu: `${sl > 0 ? '▲' : '▼'} ${tr(l.loai)} `
         + (Number(l.gia) ? l.gia : `${Math.abs(sl)}`)
         + (l.hop_le ? '' : ` · ${tr(l.trang_thai)}`),
    }
  })

  nhatKy.push(...dungVet(kq.vet ?? []))
  // SẮP THEO MỐC, GIỮ THỨ TỰ CŨ KHI TRÙNG MỐC. `Array.sort` của JS ổn định từ ES2019,
  // nên lệnh của một nhịp (đẩy vào trước) đứng trên dòng tường thuật của nhịp ấy —
  // đọc xuôi là «cổng mở, rồi lệnh ra», đúng thứ tự cỗ máy đã làm.
  nhatKy.sort((a, b) => a.t - b.t)

  /* BƯỚC HAY GẶP NHẤT, không phải trung bình — xem `LuotXem.buoc`. */
  const dem = new Map<number, number>()
  for (let k = 1; k < truc.length; k++) {
    const d = truc[k] - truc[k - 1]
    if (d > 0) dem.set(d, (dem.get(d) ?? 0) + 1)
  }
  let buoc = 0
  let nhieu = 0
  for (const [d, n] of dem) if (n > nhieu) { nhieu = n; buoc = d }

  return { truc, dsMa, nhatKy, buoc }
}

/** MỘT NHỊP — một nến của MỘT mã. */
export interface NhipView {
  t: number
  /** Mở, cao, thấp, đóng. */
  nen: [number, number, number, number]
  /** Lệnh của mã này tại nhịp này. */
  lenh: DongLenh[]
  /** Lệnh của mã này CÒN TREO ở nhịp này — đặt rồi mà chưa khớp.
   *
   *  Cửa sổ Tester cũ gọi là «giá lệnh chờ», và dành riêng màu cam cho đúng một việc
   *  ấy: mức duy nhất chưa có tốt hay xấu. */
  cho: DongLenh[]
}

export interface MachView {
  nhip: NhipView[]
  ma: string
  /** Đại lượng CÙNG THANG GIÁ — vẽ chồng lên nến. */
  chong: { ten: string; gt: (number | null)[] }[]
  /** Đại lượng thang khác — mỗi cái một khung riêng. (null = LEAN không in nhịp ấy.) */
  so: { ten: string; gt: (number | null)[] }[]
}

function bang(kq: KetQuaChay, ho: string, ma: string) {
  return (kq.bieu_do ?? []).find(b => b.ten === `${ho} ${ma}`)
}

export function dungMachView(kq: KetQuaChay, ma: string): MachView {
  const bGia = bang(kq, BANG_GIA, ma)
  const dGia = (bGia?.duong ?? []).find(d => d.kieu === 'nen') ?? bGia?.duong?.[0]
  // LEAN ghi một nến là `[giây, mở, cao, thấp, đóng]` — xem `chay_lean._diem`.
  const diem = (dGia?.diem ?? []).filter(p => p.length >= 5)

  // CHỈ LỆNH CỦA MÃ NÀY lên chart của mã này. Bày hết lên chart của SPY là vẽ lệnh
  // của QQQ ở đúng mức giá của SPY — một cái chart trông bình thường mà sai hẳn.
  // (Nhật ký thì ngược lại: nó là của cả lượt — xem `dungLuot`.)
  const lenh = (kq.lenh ?? []).filter(l => l.ma === ma)
    .sort((a, b) => giayCuaLuc(a.luc) - giayCuaLuc(b.luc))

  const nhip: NhipView[] = diem.map(p => ({
    t: p[0], nen: [p[1], p[2], p[3], p[4]] as [number, number, number, number],
    lenh: [], cho: [],
  }))
  let i = 0
  for (const l of lenh) {
    const g = giayCuaLuc(l.luc)
    while (i + 1 < nhip.length && nhip[i + 1].t <= g) i++
    if (nhip.length) nhip[Math.min(i, nhip.length - 1)].lenh.push(l)
  }

  // LỆNH CÒN TREO tại từng nhịp.
  // ⚠ ĐỌC HAI MỐC CỦA LEAN, ĐỪNG SUY TỪ `trang_thai`. `trang_thai` là tình trạng
  // CUỐI lượt — một lệnh «Đã khớp» thì suốt mấy chục nến trước lúc khớp nó vẫn đang
  // treo, mà nhìn vào `trang_thai` không thấy quãng ấy ở đâu.
  for (const l of lenh) {
    if (!l.tao) continue
    const t0 = giayCuaLuc(l.tao)
    const t1 = l.khop ? giayCuaLuc(l.khop) : Infinity
    if (!(t1 > t0)) continue
    for (const n of nhip) if (n.t >= t0 && n.t < t1) n.cho.push(l)
  }

  const chiSo = new Map(nhip.map((n, k) => [n.t, k]))
  const xep = (d: { ten: string; diem: number[][] }) => {
    const gt: (number | null)[] = new Array(nhip.length).fill(null)
    for (const p of d.diem ?? []) {
      const k = chiSo.get(p[0])
      if (k !== undefined) gt[k] = p[p.length - 1]
    }
    return { ten: d.ten, gt }
  }
  const chong = (bGia?.duong ?? []).filter(d => d !== dGia).map(xep)
  const so = (bang(kq, BANG_SO, ma)?.duong ?? []).map(xep)

  return { nhip, ma, chong, so }
}

/* ═══════════════════ KHUNG HIỂN THỊ: gộp nến lại, KHÔNG tính thêm ══════════════

   ⚠ GỘP LÀ CÁCH VẼ, KHÔNG PHẢI CÁCH TÍNH — y câu `title` của cửa sổ Tester cũ:
   *«Khung hiển thị — chỉ đổi CÁCH VẼ»*. Cỗ máy đọc nến GỐC; đổi ô này không đổi lấy
   một con số nào của lượt chạy, chỉ đổi mấy cây nến bày ra màn hình.

   ⚠ VÀ KHÔNG NỘI SUY MỘT ĐIỂM NÀO. Bốn giá của một nến gộp đều LẤY SẴN: mở = mở của
   nến đầu, cao = cao nhất, thấp = thấp nhất, đóng = đóng của nến cuối. Không phép
   nào ở đây sinh ra một con số LEAN chưa từng in. Đại lượng thì lấy giá trị CUỐI
   trong khoảng — đúng con số tại lúc khoảng ấy đóng, chứ không phải bình quân (bình
   quân của RSI là một con số không tồn tại ở nhịp nào cả).

   ⚠ GỘP SAU KHI CẮT THEO CON TRỎ, không trước. Cắt trước thì khoảng đang dở chỉ gồm
   mấy nến đã xảy ra — đúng hình một cây nến đang hình thành ở mép phải, y như chart
   thật lúc chạy. Gộp trước rồi mới cắt thì cây nến cuối mang luôn giá của những nến
   CHƯA TỚI: một cái chart nhìn bình thường mà kể trước tương lai. */

/** Một LÁT đã cắt tới con trỏ và đã gộp theo khung hiển thị. */
export interface LatView {
  nhip: NhipView[]
  /** Song song với `nhip`, cùng thứ tự `MachView.chong`. */
  chong: (number | null)[][]
  so: (number | null)[][]
}

export function gopLat(mach: MachView, tToi: number, giay: number): LatView {
  const ds: NhipView[] = []
  const gi: number[] = []            // nhịp gốc nào vào ô nào
  for (let k = 0; k < mach.nhip.length; k++) {
    const n = mach.nhip[k]
    // Mã chưa có nến nào tới mốc này (rổ động: nó vào rổ sau) — để trống, đừng vẽ
    // bừa nến đầu tiên của nó ra như thể nó đã ở đó từ đầu.
    if (n.t > tToi) break
    // `giay <= 0` = khung GỐC: mỗi nến một ô, không gộp gì. Nhánh riêng chứ không
    // dựa vào `floor(t/1)*1` — khỏi tốn một vòng chia cho cả hai chục chart.
    const o = giay > 0 ? Math.floor(n.t / giay) * giay : n.t
    const cuoi = ds[ds.length - 1]
    if (cuoi && cuoi.t === o) {
      cuoi.nen[1] = Math.max(cuoi.nen[1], n.nen[1])
      cuoi.nen[2] = Math.min(cuoi.nen[2], n.nen[2])
      cuoi.nen[3] = n.nen[3]
      cuoi.lenh = cuoi.lenh.concat(n.lenh)
      // Lệnh CÒN TREO của ô = treo tại lúc ô ấy đóng. Gộp cả khoảng thì một lệnh đã
      // khớp từ nến đầu vẫn hiện ra như đang treo.
      cuoi.cho = n.cho
      gi[ds.length - 1] = k
    } else {
      ds.push({ t: o, nen: [...n.nen] as NhipView['nen'], lenh: [...n.lenh], cho: n.cho })
      gi.push(k)
    }
  }

  /** Giá trị CUỐI CÓ THẬT trong mỗi ô. Dò lùi từ nhịp cuối của ô về nhịp đầu: LEAN bỏ
   *  trống mấy nến chỉ báo chưa chín, nên nhịp cuối có thể rỗng mà ô vẫn có số. */
  const xep = (gt: (number | null)[]) => {
    const ra: (number | null)[] = []
    for (let o = 0; o < ds.length; o++) {
      const dau = o > 0 ? gi[o - 1] + 1 : 0
      let v: number | null = null
      for (let k = gi[o]; k >= dau; k--) {
        const x = gt[k]
        if (x !== null && x !== undefined) { v = x; break }
      }
      ra.push(v)
    }
    return ra
  }

  return { nhip: ds, chong: mach.chong.map(h => xep(h.gt)), so: mach.so.map(h => xep(h.gt)) }
}


/* ════════════════ BẢNG SỐ LIỆU: đúng mấy con số cỗ máy ĐỌC tại nến ấy ══════════

   ⚠ BẢNG ĐỌC NẾN GỐC, KHÔNG ĐỌC NẾN ĐÃ GỘP. Đổi ô «Khung hiển thị» là đổi cách VẼ;
   con số cỗ máy thật sự đọc tại nến ấy thì vẫn là con số của nến GỐC. Lấy số của ô
   đã gộp vào bảng là bày một giá trị ở một thời điểm không có trong lượt chạy, đúng
   lúc người ta mở cửa sổ ra để soi. */

/** MỘT HÀNG bảng số liệu. */
export interface HangSo {
  /** Phần MÃ tách khỏi tên — `XAUUSD` của «XAUUSD·RSI(14)». Rỗng = không có.
   *
   *  ⚠ TÁCH, KHÔNG BỊA. `core.chu_dai_luong` đã ghép sẵn `MÃ·TÊN`; ở đây chỉ cắt lại
   *  chỗ nó ghép, để tên dài còn chỗ mà bày ra cho đủ — đúng việc cột `phu` của cửa
   *  sổ Tester cũ làm. Không có dấu `·` thì cột trống, chứ không đi tìm một nhãn phụ
   *  nào khác để điền vào cho kín. */
  phu: string
  ten: string
  gt: number | null
  /** Hàng ĐẦU của một nhóm — chỗ kẻ một đường mảnh.
   *
   *  ⚠ KHÔNG IN TÊN NHÓM. Cửa sổ Tester cũ từng in, và `VÙNG NÉN` đứng ngang hàng với
   *  GIÁ / CHỈ BÁO — ba cái kia phổ quát, cái đó là khái niệm của đúng một chiến
   *  lược. Không tiêu đề nào thì không tiêu đề nào sai được. Nhóm ở đây cũng không do
   *  ai gõ: nó là CHỖ VẼ mà `sinh_ma` đã quyết (chồng lên nến, hay khung riêng). */
  dauNhom?: boolean
}

export interface SoLieuView {
  hang: HangSo[]
  /** Nhịp GỐC con trỏ đang đứng, hay null khi mã này chưa có nến nào tới mốc ấy. */
  nhip: NhipView | null
}

/** Tên `XAUUSD·RSI(14)` -> `{phu: 'XAUUSD', ten: 'RSI(14)'}`. */
function cat(ten: string): { phu: string; ten: string } {
  const i = ten.indexOf('·')
  return i < 0 ? { phu: '', ten } : { phu: ten.slice(0, i), ten: ten.slice(i + 1) }
}

export function soLieuTai(mach: MachView, tToi: number): SoLieuView {
  let k = -1
  for (let x = 0; x < mach.nhip.length && mach.nhip[x].t <= tToi; x++) k = x
  if (k < 0) return { hang: [], nhip: null }
  const n = mach.nhip[k]

  const hang: HangSo[] = [
    { phu: '', ten: tr('Mở'), gt: n.nen[0], dauNhom: true },
    { phu: '', ten: tr('Cao'), gt: n.nen[1] },
    { phu: '', ten: tr('Thấp'), gt: n.nen[2] },
    { phu: '', ten: tr('Đóng'), gt: n.nen[3] },
  ]
  mach.chong.forEach((h, i) =>
    hang.push({ ...cat(h.ten), gt: h.gt[k] ?? null, dauNhom: i === 0 }))
  mach.so.forEach((h, i) =>
    hang.push({ ...cat(h.ten), gt: h.gt[k] ?? null, dauNhom: i === 0 }))
  return { hang, nhip: n }
}
