/** NGÔN NGỮ GIAO DIỆN — tiếng Anh (mặc định) hay tiếng Việt.
 *
 *  Chép cơ chế của Jenifer_Studio (`webui/src/ngon_ngu.ts` bên ấy) — cùng tên hàm, cùng
 *  cách đặt khoá, cùng lời giải thích. Khác đúng MỘT chỗ: Cat_Studio mặc định hiện
 *  TIẾNG ANH, Jenifer mặc định tiếng Việt.
 *
 *  CÂU TIẾNG VIỆT LÀ KHOÁ. Mã vẫn viết nguyên câu tiếng Việt ngay chỗ nó hiện ra, chỉ
 *  bọc trong `tr(…)`; bảng `tieng_anh.ts` tra câu ấy ra câu tiếng Anh. Không đặt mã
 *  khoá kiểu "nut.luu" như các bộ dịch thường làm: đọc mã mà phải tra bảng mới biết nút
 *  ghi gì thì mất hẳn cái lợi lớn nhất của mã tiếng Việt. Ở chế độ tiếng Việt `tr` trả
 *  lại đúng câu đưa vào, nên giao diện tiếng Việt y hệt như trước khi có bộ dịch.
 *
 *  THIẾU BẢN DỊCH THÌ HIỆN CÂU TIẾNG VIỆT — không bao giờ trống. Thêm chữ mới vào giao
 *  diện mà quên dịch thì nhìn bản tiếng Anh là thấy ngay câu nào còn sót. Mà vì Cat
 *  MẶC ĐỊNH tiếng Anh, chỗ sót đập vào mắt ngay lần mở app đầu tiên.
 *
 *  Tên `tr` (translate — như `tr()` của Qt) chứ không phải `t`: cả trăm chỗ trong mã đã
 *  dùng `t` làm tên biến, lấy trùng là đè nhau.
 *
 *  Ô ĐIỀN: `{0}`, `{1}`… là chỗ điền giá trị theo thứ tự đưa vào:
 *      tr('Đã chạy {0} lượt', n)
 *  Bản tiếng Anh được thêm `{0|one|other}` — chọn số ít / số nhiều theo giá trị ô {0}:
 *      'Ran {0} {0|backtest|backtests}'
 *  Tiếng Việt không có số nhiều, nên câu gốc không bao giờ cần cách viết này.
 *
 *  `trx` là bản cho CON của JSX: ô điền được là phần tử React (`<b>…</b>`), nên cả câu
 *  — kể cả chữ in đậm giữa câu — dịch thành một khối, trật tự từ theo đúng tiếng Anh.
 *
 *  QUY TRÌNH khi sửa hay thêm giao diện — mỗi lần, trong cùng lượt sửa:
 *    1. Viết chữ tiếng Việt như thường (bọc tr() sẵn càng tốt).
 *    2. `npm run dich` — tự bọc chữ Việt còn trần, dàn dòng, rồi in những câu chưa có
 *       bản tiếng Anh, dạng dán thẳng.
 *    3. Dán vào `tieng_anh.ts` đúng nhóm, điền bản tiếng Anh theo bảng thuật ngữ đầu
 *       tệp ấy. Chạy lại tới khi báo "song ngữ đủ".
 *  `npm run build` và `tests/test_ngon_ngu.py` soát lại y như thế: thiếu một câu là dừng.
 *  `tools\dich.bat` (ở gốc kho) làm bước 2 cho CẢ web lẫn chữ Python sinh ra — một lệnh.
 *
 *  Bảng hằng đặt ngoài hàm thì công cụ không tự bọc (bọc lúc nạp tệp là chốt cứng tiếng
 *  Việt) — dịch chỗ HIỆN RA: `tr(TEN_NHOM[n])`. Component bọc `memo` thì gọi `useNgonNgu()`.
 */
import { createElement, Fragment, type ReactNode, useSyncExternalStore } from 'react'
import TIENG_ANH from './tieng_anh'

export type NgonNgu = 'vi' | 'en'

/** Các nấc cho ô chọn ở Cài đặt. Mỗi nấc ghi bằng CHÍNH tiếng của nó: người không đọc
 *  được tiếng đang hiện vẫn tìm ra chữ của mình. */
export const CAC_NGON_NGU: { ma: NgonNgu; nhan: string }[] = [
  { ma: 'en', nhan: 'English' },
  { ma: 'vi', nhan: 'Tiếng Việt' },
]

/** MẶC ĐỊNH TIẾNG ANH — và đặt sẵn ở đây, chứ không chờ Python trả lời. `cho_cau_noi`
 *  mới hỏi được cài đặt, mà khung hình đầu đã vẽ trước đó rồi; để sẵn 'vi' thì người
 *  dùng tiếng Anh thấy một nháy tiếng Việt mỗi lần mở app. */
let hien: NgonNgu = 'en'
const nghe = new Set<() => void>()

/** Đổi ngôn ngữ. Nhận cả giá trị lạ (cài đặt cũ, gõ tay vào file): lạ thì về tiếng Anh —
 *  cùng luật với `cat_studio/core.ngon_ngu`, một chỗ lạ không được làm hai bên lệch nhau. */
export function datNgonNgu(n: unknown) {
  const moi: NgonNgu = n === 'vi' ? 'vi' : 'en'
  if (moi === hien) return
  hien = moi
  document.documentElement.lang = moi
  nghe.forEach(f => f())
}

export const ngonNgu = (): NgonNgu => hien

/** Gọi ở đầu component để nó VẼ LẠI khi đổi ngôn ngữ.
 *
 *  Gốc của mỗi cửa sổ gọi nó là đủ cho gần hết cây: gốc vẽ lại thì con vẽ lại theo.
 *  Chỉ component bọc `memo` — khối trên sơ đồ, hạt nhân — phải tự gọi, vì `memo` chặn
 *  đúng cái lượt vẽ lại ấy. Kết quả trả về cũng dùng làm phụ thuộc cho `useMemo` nào
 *  sinh ra chữ. */
export function useNgonNgu(): NgonNgu {
  return useSyncExternalStore(dangKy, ngonNgu)
}

function dangKy(f: () => void) {
  nghe.add(f)
  return () => { nghe.delete(f) }
}

/** Câu mẫu theo ngôn ngữ đang hiện. Khoảng trắng hai đầu giữ nguyên, chỉ tra phần
 *  giữa: chữ JSX nằm sát một thẻ in đậm mang theo dấu cách, mà bảng dịch chỉ ghi câu. */
function mau(chu: string): string {
  if (hien === 'vi') return chu
  const m = /^(\s*)([\s\S]*?)(\s*)$/.exec(chu)!
  const en = TIENG_ANH[m[2]]
  return en === undefined ? chu : m[1] + en + m[3]
}

const O_DIEN = /\{(\d+)(?:\|([^|}]*)\|([^}]*))?\}/g

/** Dịch một câu, điền giá trị vào `{0}`, `{1}`… Trả CHUỖI — dùng ở mọi chỗ cần chữ:
 *  thuộc tính, thông báo, nhật ký. Giá trị điền vào theo luật chuỗi mẫu của JS
 *  (`${x}`), để thay một chuỗi mẫu bằng `tr` không đổi chữ nào hiện ra. */
export function tr(chu: string, ...bien: unknown[]): string {
  return mau(chu).replace(O_DIEN, (_m, i: string, mot?: string, nhieu?: string) =>
    mot !== undefined ? (Number(bien[+i]) === 1 ? mot : nhieu!) : String(bien[+i]))
}

/** Như `tr` nhưng ô điền là CON của JSX — phần tử React, số, chữ — và trả về một
 *  Fragment. Giá trị rỗng (`null`, `false`, `undefined`) không hiện gì, đúng luật JSX. */
export function trx(chu: string, ...bien: ReactNode[]): ReactNode {
  const s = mau(chu)
  const ra: ReactNode[] = []
  let tu = 0
  for (const m of s.matchAll(O_DIEN)) {
    if (m.index! > tu) ra.push(s.slice(tu, m.index))
    const v = bien[+m[1]]
    ra.push(m[2] !== undefined ? (Number(v) === 1 ? m[2] : m[3]) : v)
    tu = m.index! + m[0].length
  }
  if (tu < s.length) ra.push(s.slice(tu))
  return createElement(Fragment, null, ...ra)
}
