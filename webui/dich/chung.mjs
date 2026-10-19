/** Phần DÙNG CHUNG của bộ công cụ song ngữ — xem `chay.mjs`.
 *
 *  CHÉP TỪ Jenifer_Studio (`webui/dich/chung.mjs` bên ấy) — cùng tên hàm, cùng bảng
 *  `KHONG_DAU`, cùng lời chú thích. Hai app cùng một bài toán và cùng một tác giả;
 *  tự chế một lối khác là tự nuôi hai bộ công cụ phải sửa song song. */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import ts from 'typescript'

export { ts }
export const WEBUI = path.dirname(path.dirname(fileURLToPath(import.meta.url)))
export const SRC = path.join(WEBUI, 'src')
export const BANG = path.join(SRC, 'tieng_anh.ts')

/** Không phải chữ giao diện (`tim.ts` bỏ dấu để tìm), hoặc chính là bộ dịch. */
export const BO_TEP = new Set(['ngon_ngu.ts', 'tieng_anh.ts', 'tim.ts'])
/** Cố ý KHÔNG dịch: nhãn ghi sẵn cả hai tiếng, và tên một thứ tiếng ghi bằng chính nó. */
export const BO_CAU = new Set(['Ngôn ngữ · Language:', 'Ngôn ngữ · Language', 'Tiếng Việt'])

const DAU = /[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]/i
/** Tiếng Việt KHÔNG DẤU mà không trùng chữ tiếng Anh. Lọc theo dấu thì sót đúng những
 *  chữ này — đã sót thật: "Sang {0}", <b>cao</b>, "Mua xong", tab "Chung", màu "Cam". */
const KHONG_DAU = new Set(['sau', 'cao', 'xong', 'mua', 'trong', 'ngay', 'qua', 'khung',
  'chung', 'sang', 'cam', 'lam', 'khi', 'nhanh', 'thanh', 'xanh', 'trang', 'tay', 'chia',
  'giao', 'kho', 'cho', 'sao', 'theo', 'xem', 'bao', 'doanh'])

/** Câu này là tiếng Việt (cần dịch) không.
 *
 *  Có dấu là chắc. Không dấu thì tra `KHONG_DAU` từng TỪ, bỏ qua từ trông như mã — có
 *  `_ - . / : =` ('lam-lai', 'ket_qua', tên tệp, lớp CSS 'em-khung'). Với CHUỖI TRONG MÃ
 *  còn phải trông như câu chữ: có dấu cách, hay viết hoa chữ đầu như một nhãn ('Cam',
 *  'Chung') — 'chung', 'tay' trần là mã định danh. Chữ JSX (`jsx`) thì luôn là chữ hiện ra. */
export function laViet(s, jsx = false) {
  if (DAU.test(s)) return true
  const g = s.trim()
  if (!jsx && !(/ /.test(g) || /^[A-Z]/.test(g))) return false
  return g.split(/\s+/).some(tu => !/[_\-./:=]/.test(tu)
    && tu.toLowerCase().split(/[^a-z]+/).some(t => KHONG_DAU.has(t)))
}

/** Mọi tệp .ts/.tsx của giao diện, trừ `BO_TEP`. */
export function dsTep() {
  const ra = []
  ;(function duyet(d) {
    for (const f of fs.readdirSync(d)) {
      const p = path.join(d, f)
      if (fs.statSync(p).isDirectory()) duyet(p)
      else if (/\.(ts|tsx)$/.test(f) && !BO_TEP.has(f)) ra.push(p)
    }
  })(SRC)
  return ra
}

/** Đọc một tệp: nguồn, kiểu xuống dòng của CHÍNH tệp ấy, cây cú pháp. Trong kho có cả
 *  tệp CRLF lẫn LF — dòng chèn thêm phải theo đúng kiểu của tệp. */
export function docTep(p) {
  const nguon = fs.readFileSync(p, 'utf8')
  return {
    nguon,
    eol: nguon.includes('\r\n') ? '\r\n' : '\n',
    sf: ts.createSourceFile(p, nguon, ts.ScriptTarget.Latest, true,
      p.endsWith('.tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS),
  }
}

export const tenTep = (p) => path.relative(SRC, p).replace(/\\/g, '/')
export const laCong = (n) => !!n && ts.isBinaryExpression(n)
  && n.operatorToken.kind === ts.SyntaxKind.PlusToken
export const laGoiDich = (n, sf) => ts.isCallExpression(n)
  && /^(tr|trx)$/.test(n.expression.getText(sf))

/** Giá trị TĨNH của một biểu thức chuỗi (chuỗi, chuỗi mẫu không lỗ, chuỗi cộng), hay null. */
export function tinh(n) {
  if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) return n.text
  if (ts.isParenthesizedExpression(n)) return tinh(n.expression)
  if (laCong(n)) {
    const a = tinh(n.left), b = tinh(n.right)
    return a === null || b === null ? null : a + b
  }
  return null
}

/** Chuỗi JS nháy đơn. Hai ký tự xuống dòng của Unicode (U+2028/2029) cũng phải thoát:
 *  JS coi chúng là hết dòng, để trần trong chuỗi là vỡ cú pháp. */
const LS = String.fromCharCode(0x2028), PS = String.fromCharCode(0x2029)
export const chuoi = (s) => "'" + s.replace(/\\/g, '\\\\').replace(/'/g, "\\'")
  .replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t')
  .split(LS).join('\\u2028').split(PS).join('\\u2029') + "'"

/** Ô điền {n} của một câu — "{0} khối" và "{0} {0|block|blocks}" cùng là {0}. */
const O = /\{(\d+)(?:\|[^|}]*\|[^}]*)?\}/g
export const oDien = (s) => [...new Set([...s.matchAll(O)].map(m => m[1]))].sort().join()
/** Câu chỉ có ô điền và dấu (vd "{0}: {1}") thì không có chữ nào để dịch. */
export const coChu = (s) => /\p{L}/u.test(s.replace(O, ''))
