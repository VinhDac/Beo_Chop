/** PHÍM TẮT: bảng lệnh, cách đọc cụm phím, và cách trộn phím người dùng đặt.
 *
 *  MỘT BẢNG, KHÔNG PHẢI MỘT CHUỖI `else if`. Bản của Jenifer trước đây là 15 nhánh
 *  `else if` xếp theo thứ tự, và ba trong số đó phải kèm chú thích cảnh báo cùng một
 *  lỗi: `ctrl && key === 'g'` nuốt luôn Ctrl+Shift+G nếu đặt sai chỗ. Tra bảng theo
 *  ĐÚNG cụm phím đang bấm thì không còn thứ tự nào để sai — "ctrl+g" và "ctrl+shift+g"
 *  là hai khoá khác nhau, hết chuyện.
 *
 *  Tên phím ở đây là tên CỦA TRÌNH DUYỆT. Phím tắt của app do trình duyệt bắt và so,
 *  không bao giờ đi xuống Python.
 *
 *  Chép từ Jenifer_Studio.
 */

export type Nhom = 'khoi' | 'sua' | 'file'

export const TEN_NHOM: Record<Nhom, string> = {
  khoi: 'Thêm khối',
  sua: 'Sửa sơ đồ',
  file: 'Strategy · Cửa sổ',
}

export interface Lenh {
  /** Mã bền, dùng làm khoá lưu xuống settings. Đổi mã là mất phím người dùng đã đặt. */
  ma: string
  nhan: string
  nhom: Nhom
  /** Phím MẶC ĐỊNH. Nhiều cụm = nhiều lối vào cùng một lệnh (Làm lại có hai). */
  phim: string[]
}

export const LENH: Lenh[] = [
  // --- thêm khối ---
  { ma: 'them-bat-dau', nhan: 'Thêm khối Bắt đầu', nhom: 'khoi', phim: [] },
  { ma: 'them-nhom', nhan: 'Thêm Nhóm', nhom: 'khoi', phim: [] },
  { ma: 'them-khoi-le', nhan: 'Thêm Khối lẻ', nhom: 'khoi', phim: [] },
  { ma: 'them-quay-ve', nhan: 'Thêm khối Quay về', nhom: 'khoi', phim: [] },

  // --- sửa sơ đồ ---
  { ma: 'hoan-tac', nhan: 'Hoàn tác', nhom: 'sua', phim: ['ctrl+z'] },
  // Hai cụm cho một lệnh: Ctrl+Y (nết Windows) và Ctrl+Shift+Z (nết app vẽ).
  { ma: 'lam-lai', nhan: 'Làm lại', nhom: 'sua', phim: ['ctrl+y', 'ctrl+shift+z'] },
  { ma: 'nhan-ban', nhan: 'Nhân bản khối', nhom: 'sua', phim: ['ctrl+d'] },
  { ma: 'xoa', nhan: 'Xoá khối', nhom: 'sua', phim: ['delete'] },
  { ma: 'doi-ten', nhan: 'Đổi tên khối', nhom: 'sua', phim: ['f3'] },
  { ma: 'chon-het', nhan: 'Chọn hết', nhom: 'sua', phim: ['ctrl+a'] },
  { ma: 'gom-hat-nhan', nhan: 'Gom thành Hạt nhân', nhom: 'sua', phim: ['ctrl+g'] },
  { ma: 'ta-hat-nhan', nhan: 'Tách khỏi Hạt nhân', nhom: 'sua', phim: ['ctrl+shift+g'] },
  { ma: 'ghim-so', nhan: 'Ghim số của khối', nhom: 'sua', phim: [] },
  { ma: 'ngat-noi', nhan: 'Ngắt hết kết nối', nhom: 'sua', phim: [] },
  { ma: 'ra-hat-nhan', nhan: 'Ra khỏi hạt nhân', nhom: 'sua', phim: ['escape'] },

  // --- Strategy, cửa sổ ---
  { ma: 'strategy-moi', nhan: 'Strategy mới', nhom: 'file', phim: ['ctrl+n'] },
  { ma: 'mo-strategy', nhan: 'Mở Strategy…', nhom: 'file', phim: ['ctrl+o'] },
  { ma: 'luu', nhan: 'Lưu Strategy', nhom: 'file', phim: ['ctrl+s'] },
  { ma: 'o-tim', nhan: 'Nhảy vào ô tìm khối', nhom: 'file', phim: ['ctrl+f'] },
  { ma: 'bang-phim-tat', nhan: 'Bảng phím tắt (bảng này)', nhom: 'file', phim: ['f2'] },
]

/** Cụm phím của một sự kiện bàn phím, dạng chuẩn: "ctrl+shift+s", "f3", "delete".
 *
 *  Lấy tên từ `ev.code` cho phím chữ và phím số, KHÔNG lấy từ `ev.key`: giữ Shift thì
 *  `ev.key` của phím 1 là "!" — gán Ctrl+Shift+1 xong nhìn vào bảng thấy "ctrl+shift+!"
 *  thì không ai đoán ra đó là phím nào.
 *
 *  Phím bổ trợ bấm MỘT MÌNH trả về '' — giữ Ctrl rồi mới bấm phím thật là thói quen
 *  bình thường, coi cú giữ ấy là một cụm thì nó nuốt mất cú bấm ngay sau.
 */
export function cumPhim(ev: KeyboardEvent): string {
  if (['Shift', 'Control', 'Alt', 'Meta'].includes(ev.key)) return ''
  const p: string[] = []
  if (ev.ctrlKey || ev.metaKey) p.push('ctrl')
  if (ev.altKey) p.push('alt')
  if (ev.shiftKey) p.push('shift')
  const c = ev.code
  let ten: string
  if (c.startsWith('Key')) ten = c.slice(3).toLowerCase()
  else if (c.startsWith('Digit')) ten = c.slice(5)
  else if (c.startsWith('Numpad')) ten = 'num' + c.slice(6).toLowerCase()
  else ten = (ev.key.length === 1 ? ev.key : ev.key).toLowerCase()
  p.push(ten)
  return p.join('+')
}

/** Cụm phím -> chữ hiện cho người đọc: "ctrl+shift+g" -> "Ctrl+Shift+G". */
export function chuPhim(cum: string): string {
  return cum.split('+').map(p => {
    if (p === 'ctrl') return 'Ctrl'
    if (p === 'shift') return 'Shift'
    if (p === 'alt') return 'Alt'
    if (p === 'delete') return 'Delete'
    if (p === 'escape') return 'Esc'
    if (/^f\d+$/.test(p)) return p.toUpperCase()
    return p.toUpperCase()
  }).join('+')
}

/** Bảng tra: cụm phím -> mã lệnh. Người dùng đặt lại thì truyền `doi` vào. */
export function bangTra(doi?: Record<string, string[]>): Map<string, string> {
  const m = new Map<string, string>()
  for (const l of LENH) {
    for (const c of (doi?.[l.ma] ?? l.phim)) m.set(c, l.ma)
  }
  return m
}
