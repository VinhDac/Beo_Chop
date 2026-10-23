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

/** Tên hai bảng `sinh_ma` bảo LEAN vẽ. Đổi một bên là bảng trống — xem `sinh_ma`. */
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
}

export interface MachView {
  nhip: NhipView[]
  /** Tên mã — lấy từ tên đường nến, chính là cái `sinh_ma` đặt. */
  ma: string
  /** Mỗi đại lượng một hàng: tên, và giá trị theo từng nhịp (null = LEAN không in). */
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

function bang(kq: KetQuaChay, ten: string) {
  return (kq.bieu_do ?? []).find(b => b.ten === ten)
}

export function dungMachView(kq: KetQuaChay): MachView {
  const bGia = bang(kq, BANG_GIA)
  const dGia = bGia?.duong?.[0]
  // LEAN ghi một nến là `[giây, mở, cao, thấp, đóng]` — xem `chay_lean._diem`.
  const diem = (dGia?.diem ?? []).filter(p => p.length >= 5)

  const lenh = [...(kq.lenh ?? [])].sort(
    (a, b) => giayCuaLuc(a.luc) - giayCuaLuc(b.luc))

  // Lệnh rơi vào nhịp NÀO. Ghép theo nhịp gần nhất KHÔNG VƯỢT QUÁ giờ của lệnh:
  // lệnh khớp trong lòng một nến, nên nó thuộc về nến đang mở lúc ấy.
  const nhip: NhipView[] = diem.map(p => ({
    t: p[0], nen: [p[1], p[2], p[3], p[4]] as [number, number, number, number],
    lenh: [],
  }))
  let i = 0
  for (const l of lenh) {
    const g = giayCuaLuc(l.luc)
    while (i + 1 < nhip.length && nhip[i + 1].t <= g) i++
    if (nhip.length) nhip[Math.min(i, nhip.length - 1)].lenh.push(l)
  }

  // ĐẠI LƯỢNG. Mỗi đường một hàng, giá trị xếp theo đúng trục nhịp của giá — LEAN
  // có thể bỏ vài nhịp đầu (chỉ báo chưa chín), nên chỗ nào không có thì để null.
  const bSo = bang(kq, BANG_SO)
  const chiSo = new Map(nhip.map((n, k) => [n.t, k]))
  const so = (bSo?.duong ?? []).map(d => {
    const gt: (number | null)[] = new Array(nhip.length).fill(null)
    for (const p of d.diem ?? []) {
      const k = chiSo.get(p[0])
      if (k !== undefined) gt[k] = p[p.length - 1]
    }
    return { ten: d.ten, gt }
  })

  let thap = Infinity, cao = -Infinity
  for (const n of nhip) {
    if (n.nen[2] < thap) thap = n.nen[2]
    if (n.nen[1] > cao) cao = n.nen[1]
  }
  if (!Number.isFinite(thap)) { thap = 0; cao = 1 }

  return { nhip, ma: dGia?.ten ?? '', so, lenh, thap, cao }
}
