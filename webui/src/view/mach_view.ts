/* BỘ CHUYỂN: một lượt LEAN đã chạy -> thứ cửa sổ View bày ra.
 *
 * Cửa sổ Strategy Tester cũ chạy engine riêng của app, nên nó có sẵn mọi thứ tại
 * từng nến: giá, chỉ báo, sổ lệnh. Bản nay app KHÔNG tính gì (D-11) — mọi con số đều
 * do LEAN in ra lúc chạy (`sinh_ma._dong_bay`). File này chỉ việc XẾP LẠI những gì
 * LEAN trả về thành một trục thời gian để tua.
 *
 * ⚠ KHÔNG TÍNH THÊM MỘT CON SỐ NÀO Ở ĐÂY. Cái cám dỗ là nội suy: nến thì 941 điểm mà
 * một đại lượng nào đó chỉ 900 (LEAN bỏ nến chỉ báo chưa chín), nên dễ nghĩ tới việc
 * «điền cho đủ». Điền là bịa: bảng số liệu sẽ bày một con số LEAN chưa từng tính, ở
 * đúng những nến người ta mở cửa sổ ra để soi. Thiếu thì để thiếu, và bày dấu «—».
 */
import type { DongLenh, KetQuaChay } from '../types'

/** Tên hai HỌ bảng `sinh_ma` bảo LEAN vẽ, mỗi mã một cặp: `Price SPY`,
 *  `Quantities SPY`. Đổi một bên là bảng trống — xem `sinh_ma.BANG_GIA`.
 *
 *  ⚠ MỖI MÃ MỘT CẶP, vì LEAN hay chạy cả rổ. Tám mã là tám cái chart, và đó đúng là
 *  thứ người xem cần: một phiên đang diễn ra trên tám mã, y như live.
 *
 *  Chỗ duy nhất ở đây phải TÁCH CHỮ là lấy tên mã ra khỏi tên bảng — việc bày biện,
 *  không phải việc đoán nghĩa. Còn ĐẠI LƯỢNG NÀO VẼ Ở ĐÂU thì `sinh_ma` đã quyết rồi
 *  (nó đọc `hoi.DON_VI_GIA`): cùng thang giá thì nó in thẳng vào bảng `Price`, nên ở
 *  đây không có phép suy nào cả — bảng nào thì vẽ bảng ấy. */
export const BANG_GIA = 'Price'
export const BANG_SO = 'Quantities'

/** MỘT NHỊP — một nến của lượt chạy. */
export interface NhipView {
  /** Giây UNIX, đúng như LEAN ghi. */
  t: number
  /** Mở, cao, thấp, đóng. */
  nen: [number, number, number, number]
  /** Lệnh LEAN ghi nhận ở đúng nhịp này. Phần lớn nhịp là rỗng. */
  lenh: DongLenh[]
  /** Lệnh CÒN TREO ở nhịp này — đặt rồi mà chưa khớp.
   *
   *  Đây là thứ cửa sổ Tester cũ gọi là «giá lệnh chờ», và nó dành riêng màu cam cho
   *  đúng một việc ấy: mức duy nhất chưa có tốt hay xấu. Mức đã khớp thì thành một
   *  chuyện đã rồi; mức còn treo mới là chỗ sắp xảy ra điều gì. */
  cho: DongLenh[]
}

export interface MachView {
  nhip: NhipView[]
  /** Tên mã của cuộn phim này. */
  ma: string
  /** Đại lượng CÙNG THANG GIÁ — vẽ chồng lên nến. */
  chong: { ten: string; gt: (number | null)[] }[]
  /** Đại lượng thang khác — mỗi cái một khung riêng. (null = LEAN không in nhịp ấy.) */
  so: { ten: string; gt: (number | null)[] }[]
  /** Mọi lệnh cả lượt, theo thứ tự thời gian. */
  lenh: DongLenh[]
  /** Nhịp thấp nhất / cao nhất của giá — để vẽ trục. */
  thap: number
  cao: number
}

/** `2020-03-12 09:31:00` (giờ UTC) -> giây UNIX. */
export function giayCuaLuc(luc: string): number {
  const t = Date.parse(String(luc || '').replace(' ', 'T') + 'Z')
  return Number.isFinite(t) ? Math.floor(t / 1000) : 0
}

/** Nhãn `[4A.2] RSI(14) < 30` -> `4A.2`. Rỗng nếu nhãn không theo khuôn ấy.
 *
 *  ⚠ MỘT CÔNG THỨC, DÙNG CHUNG VỚI MÀN CHẠY MÁY. Hai nơi đọc số khối theo hai kiểu
 *  thì khối sáng lên ở màn này và khối sáng lên ở cửa sổ kia là hai khối khác nhau,
 *  cho cùng một lệnh. */
export { soKhoiCuaNhan } from '../man/mach_chay'

/** Mã nào có bảng nến trong lượt này, theo thứ tự `sinh_ma` khai. */
export function dsMaCuaLuot(kq: KetQuaChay): string[] {
  return (kq.bieu_do ?? [])
    .filter(b => b.ten.startsWith(BANG_GIA + ' '))
    .map(b => b.ten.slice(BANG_GIA.length + 1))
}

function bang(kq: KetQuaChay, ho: string, ma: string) {
  return (kq.bieu_do ?? []).find(b => b.ten === `${ho} ${ma}`)
}

export function dungMachView(kq: KetQuaChay, ma: string): MachView {
  const bGia = bang(kq, BANG_GIA, ma)
  // Đường NẾN của bảng giá; mấy đường còn lại là đại lượng CÙNG THANG, vẽ chồng lên.
  const dGia = (bGia?.duong ?? []).find(d => d.kieu === 'nen') ?? bGia?.duong?.[0]
  // LEAN ghi một nến là `[giây, mở, cao, thấp, đóng]` — xem `chay_lean._diem`.
  const diem = (dGia?.diem ?? []).filter(p => p.length >= 5)

  // CHỈ LỆNH CỦA MÃ NÀY. Cả rổ thì mọi mã nằm chung một danh sách; bày hết lên chart
  // của SPY là vẽ lệnh của QQQ ở đúng mức giá của SPY — một cái chart trông bình
  // thường mà sai hẳn.
  const lenh = (kq.lenh ?? []).filter(l => l.ma === ma)
    .sort((a, b) => giayCuaLuc(a.luc) - giayCuaLuc(b.luc))

  // Lệnh rơi vào nhịp NÀO. Ghép theo nhịp gần nhất KHÔNG VƯỢT QUÁ giờ của lệnh:
  // lệnh khớp trong lòng một nến, nên nó thuộc về nến đang mở lúc ấy.
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

  // LỆNH CÒN TREO tại từng nhịp: đặt rồi mà chưa khớp.
  //
  // ⚠ ĐỌC HAI MỐC CỦA LEAN, ĐỪNG SUY TỪ `trang_thai`. `trang_thai` là tình trạng
  // CUỐI lượt chạy — một lệnh «Đã khớp» thì suốt mấy chục nến trước lúc khớp nó vẫn
  // đang treo, mà nhìn vào `trang_thai` thì không thấy quãng ấy ở đâu cả.
  // `tao` thiếu (lượt chạy bằng bản cũ) thì bỏ qua: thà không vẽ còn hơn vẽ sai.
  for (const l of lenh) {
    if (!l.tao) continue
    const t0 = giayCuaLuc(l.tao)
    const t1 = l.khop ? giayCuaLuc(l.khop) : Infinity
    if (!(t1 > t0)) continue           // khớp ngay — không có quãng nào để treo
    for (const n of nhip) {
      if (n.t >= t0 && n.t < t1) n.cho.push(l)
    }
  }

  // ĐẠI LƯỢNG. Mỗi đường một hàng, giá trị xếp theo đúng trục nhịp của giá — LEAN
  // có thể bỏ vài nhịp đầu (chỉ báo chưa chín), nên chỗ nào không có thì để null.
  const chiSo = new Map(nhip.map((n, k) => [n.t, k]))
  const xep = (d: { ten: string; diem: number[][] }) => {
    const gt: (number | null)[] = new Array(nhip.length).fill(null)
    for (const p of d.diem ?? []) {
      const k = chiSo.get(p[0])
      if (k !== undefined) gt[k] = p[p.length - 1]
    }
    return { ten: d.ten, gt }
  }
  // Cùng thang giá -> `sinh_ma` đã in thẳng vào bảng `Price`, nên chúng vẽ CHỒNG lên
  // nến. Thang khác -> bảng `Quantities`, mỗi cái một khung riêng bên dưới.
  const chong = (bGia?.duong ?? []).filter(d => d !== dGia).map(xep)
  const so = (bang(kq, BANG_SO, ma)?.duong ?? []).map(xep)

  let thap = Infinity, cao = -Infinity
  for (const n of nhip) {
    if (n.nen[2] < thap) thap = n.nen[2]
    if (n.nen[1] > cao) cao = n.nen[1]
  }
  if (!Number.isFinite(thap)) { thap = 0; cao = 1 }

  return { nhip, ma, chong, so, lenh, thap, cao }
}
