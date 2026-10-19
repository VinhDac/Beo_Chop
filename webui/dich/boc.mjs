/** BỌC CHỮ: mọi câu tiếng Việt HIỂN THỊ chưa bọc thì bọc vào tr() / trx().
 *
 *  Chạy lại bao nhiêu lần cũng được: câu đã nằm trong tr() thì để yên, chỉ câu MỚI bị
 *  bọc. Không đổi chữ nào hiện ra ở chế độ tiếng Việt — chữ JSX gộp khoảng trắng đúng
 *  luật của JSX (Babel `cleanJSXElementLiteralChild`).
 *
 *  Cách bọc:
 *    chữ JSX đứng riêng          -> {tr('…')}
 *    câu có phần tử nội dòng     -> {trx('… {0} …', <b>…</b>)}   — dịch được cả câu
 *    thuộc tính title=, placeholder=… -> {tr('…')}
 *    chuỗi, chuỗi mẫu `…${x}…`, chuỗi cộng -> tr('… {0} …', x)
 *
 *  Cố ý KHÔNG bọc (để người viết tự lo): chuỗi ngoài mọi hàm (bảng hằng — dịch lúc hiện
 *  bằng `tr(biến)`), chuỗi đem so sánh / làm khoá / làm kiểu, đối số console.* và các
 *  phép chuỗi (.endsWith…). Bọc mấy thứ ấy là đổi LOGIC chứ không chỉ đổi chữ.
 */
import fs from 'node:fs'
import path from 'node:path'
import { BO_CAU, SRC, chuoi, docTep, laCong, laGoiDich, laViet, tenTep, ts } from './chung.mjs'

// `Icon`, `IconNet` (cùng component, `Ribbon.tsx` nhập dưới tên khác) và `ChuTim` (tô
// phần chữ khớp ô tìm) là phần tử NỘI DÒNG của Cat — nằm giữa câu, nên câu phải dịch
// thành MỘT khối chứ không chặt làm ba mảnh quanh chúng.
const INLINE = new Set(['b', 'i', 'em', 'strong', 'code', 'kbd', 'span', 'a', 'small', 'u',
  'sub', 'sup', 'br', 'mark', 's', 'q', 'abbr', 'Icon', 'IconNet', 'ChuTim'])
const THUOC_TINH_DU_LIEU = new Set(['key', 'className', 'id', 'value', 'name', 'type',
  'htmlFor', 'style', 'src', 'href'])
const SO_SANH = new Set([ts.SyntaxKind.EqualsEqualsEqualsToken, ts.SyntaxKind.ExclamationEqualsEqualsToken,
  ts.SyntaxKind.EqualsEqualsToken, ts.SyntaxKind.ExclamationEqualsToken])

function giaiThucThe(s) {
  const bang = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' }
  return s.replace(/&(#x[0-9a-f]+|#\d+|[a-z]+);/gi, (m, e) => {
    if (e[0] === '#') return String.fromCodePoint(e[1].toLowerCase() === 'x'
      ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10))
    return bang[e.toLowerCase()] ?? m
  })
}

/** Chữ JSX -> các mảnh theo dòng, đúng luật gộp khoảng trắng của JSX. */
function lamSachJsx(raw) {
  const dong = raw.split(/\r\n|\n|\r/)
  let cuoi = 0
  dong.forEach((l, i) => { if (/[^ \t]/.test(l)) cuoi = i })
  const ra = []
  dong.forEach((l, i) => {
    let s = l.replace(/\t/g, ' ')
    if (i !== 0) s = s.replace(/^[ ]+/, '')
    if (i !== dong.length - 1) s = s.replace(/[ ]+$/, '')
    if (s) { if (i !== cuoi) s += ' '; ra.push(giaiThucThe(s)) }
  })
  return ra
}

/** Khoá dài thì xuống dòng đúng chỗ mã gốc xuống dòng. */
function phatKhoa(manh, thut, eol) {
  manh = manh.filter(m => m !== '')
  const ca = manh.join('')
  if (manh.length <= 1 || ca.length <= 72) return chuoi(ca)
  return manh.map(chuoi).join(eol + thut + '+ ')
}

const laHam = (c) => ts.isFunctionDeclaration(c) || ts.isFunctionExpression(c) ||
  ts.isArrowFunction(c) || ts.isMethodDeclaration(c) || ts.isConstructorDeclaration(c) ||
  ts.isGetAccessor(c) || ts.isSetAccessor(c)

/** Bọc một tệp. Trả { noi: ['tệp:dòng', …] } — mỗi chỗ vừa bọc. `ghi` = ghi ra đĩa. */
export function boc(p, ghi) {
  const { nguon, eol, sf } = docTep(p)
  const noi = []
  const laChuJsx = (n) => n.kind === ts.SyntaxKind.JsxText
  const raw = (n) => sf.text.slice(n.pos, n.end)
  const dau = (n) => (laChuJsx(n) ? n.pos : n.getStart(sf))
  const dongCua = (n) => sf.getLineAndCharacterOfPosition(dau(n)).line
  const thutCua = (n) => /^[ \t]*/.exec(
    sf.text.slice(sf.getPositionOfLineAndCharacter(dongCua(n), 0)))[0]
  const ghiNoi = (n) => noi.push(tenTep(p) + ':' + (dongCua(n) + 1))
  let dungTr = false, dungTrx = false

  const trongHam = (n) => { for (let c = n.parent; c; c = c.parent) if (laHam(c)) return true; return false }
  const phang = (n, ra) => { if (laCong(n)) { phang(n.left, ra); phang(n.right, ra) } else ra.push(n); return ra }
  const laChuoiTinh = (n) => !!n && (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n))
  const laChuoi = (n) => laChuoiTinh(n) || ts.isTemplateExpression(n)
  const chuMau = (n) => n.head.text + n.templateSpans.map(s => s.literal.text).join('')
  const coViet = (n) => laChuoiTinh(n) ? laViet(n.text) && !BO_CAU.has(n.text.trim())
    : ts.isTemplateExpression(n) ? laViet(chuMau(n)) : false
  const vietJsx = (c) => {
    if (!laChuJsx(c) || !raw(c).trim()) return false
    const s = lamSachJsx(raw(c)).join('').trim()
    return laViet(s, true) && !BO_CAU.has(s)
  }

  function khongBoc(u) {
    const p = u.parent
    if (!trongHam(u)) return true                                            // bảng hằng
    // Bên trong thuộc tính dữ liệu (className={…}, key={…}…): mã, không phải chữ hiện ra.
    for (let c = p; c; c = c.parent) {
      if (ts.isJsxAttribute(c)) { if (THUOC_TINH_DU_LIEU.has(c.name.getText(sf))) return true; break }
      if (ts.isJsxElement(c) || ts.isJsxSelfClosingElement(c)) break
    }
    if (ts.isBinaryExpression(p) && SO_SANH.has(p.operatorToken.kind)) return true
    if (ts.isCaseClause(p) || ts.isLiteralTypeNode(p)) return true
    if ((ts.isPropertyAssignment(p) || ts.isPropertyDeclaration(p)) && p.name === u) return true
    if (ts.isElementAccessExpression(p) && p.argumentExpression === u) return true
    if (ts.isImportDeclaration(p) || ts.isExportDeclaration(p) || ts.isTaggedTemplateExpression(p)) return true
    if (ts.isCallExpression(p) && p.arguments.includes(u)) {
      const f = p.expression.getText(sf)
      if (/^console\./.test(f)) return true
      if (/\.(endsWith|startsWith|includes|indexOf|lastIndexOf|split|replace|replaceAll|match|search|localeCompare)$/.test(f))
        return true
    }
    if (ts.isNewExpression(p) && /RegExp/.test(p.expression.getText(sf))) return true
    return false
  }

  function khoaMau(n, args) {
    let k = n.head.text
    for (const sp of n.templateSpans) {
      k += '{' + args.length + '}'
      args.push(bienDoi(sp.expression).trim())
      k += sp.literal.text
    }
    return k
  }

  function goiTr(manh, args, thut) {
    dungTr = true
    return 'tr(' + phatKhoa(manh, thut, eol) + (args.length ? ', ' + args.join(', ') : '') + ')'
  }

  /** Một cụm chữ (chuỗi, chuỗi mẫu, chuỗi cộng) -> văn bản thay, hay null = để yên. */
  function bocCum(u) {
    if (ts.isJsxAttribute(u.parent) && u.parent.initializer === u) {
      if (THUOC_TINH_DU_LIEU.has(u.parent.name.getText(sf))) return null
      ghiNoi(u)
      dungTr = true
      return '{tr(' + chuoi(giaiThucThe(u.text)) + ')}'
    }
    if (khongBoc(u)) return null
    if (laChuoiTinh(u)) { ghiNoi(u); dungTr = true; return 'tr(' + u.getText(sf) + ')' }
    if (ts.isTemplateExpression(u)) {
      ghiNoi(u)
      const args = []
      return goiTr([khoaMau(u, args)], args, thutCua(u))
    }
    const ops = phang(u, [])
    // a + b + 'chữ' với a, b là số: JS cộng số TRƯỚC — gộp thành một câu là đổi kết quả.
    if (ops.length > 1 && !laChuoi(ops[0]) && !laChuoi(ops[1])) return null
    ghiNoi(u)
    if (ops.every(laChuoiTinh)) { dungTr = true; return 'tr(' + u.getText(sf) + ')' }
    const args = [], manh = []
    let cur = ''
    ops.forEach((o, i) => {
      let phan
      if (laChuoiTinh(o)) phan = o.text
      else if (ts.isTemplateExpression(o)) phan = khoaMau(o, args)
      else { phan = '{' + args.length + '}'; args.push(bienDoi(o).trim()) }
      if (i > 0 && laChuoi(o) && dongCua(o) !== dongCua(ops[i - 1])) { manh.push(cur); cur = phan } else cur += phan
    })
    manh.push(cur)
    return goiTr(manh, args, thutCua(ops[ops.length - 1]))
  }

  const laKhoangTrangBo = (c) => laChuJsx(c) && /^\s*$/.test(raw(c)) && /[\r\n]/.test(raw(c))
  const laChuThich = (c) => ts.isJsxExpression(c) && !c.expression
  const tenThe = (c) => ts.isJsxElement(c) ? c.openingElement.tagName.getText(sf)
    : ts.isJsxSelfClosingElement(c) ? c.tagName.getText(sf) : ts.isJsxFragment(c) ? '<>' : null
  const laInline = (c) => laChuJsx(c) || ts.isJsxExpression(c) || INLINE.has(tenThe(c))

  /** Một mẩu chữ JSX đứng riêng -> {tr('…')}, giữ khoảng trắng dàn dòng ở hai đầu. */
  function bocJsxLe(c) {
    const r = raw(c)
    const manh = lamSachJsx(r)
    const m = /^(\s*)([\s\S]*?)(\s*)$/.exec(r)
    const truoc = /[\r\n]/.test(m[1]) ? m[1] : ''
    const sau = /[\r\n]/.test(m[3]) ? m[3] : ''
    const thut = (/\n([ \t]*)\S/.exec(r) || [, thutCua(c)])[1]
    ghiNoi(c)
    dungTr = true
    return truoc + '{tr(' + phatKhoa(manh, thut, eol) + ')}' + sau
  }

  /** Vùng con của một phần tử JSX có chữ Việt chưa bọc -> văn bản thay, hay null. */
  function bocConJsx(node) {
    const con = node.children
    if (!con.some(vietJsx)) return null
    let a = 0, b = con.length - 1
    while (a <= b && laKhoangTrangBo(con[a])) a++
    while (b >= a && laKhoangTrangBo(con[b])) b--
    const noiDung = con.slice(a, b + 1)
    const coO = noiDung.some(c => !laChuJsx(c) && !laChuThich(c) &&
      !(ts.isJsxExpression(c) && laChuoiTinh(c.expression)))
    if (!(coO && noiDung.every(laInline))) {
      // Từng mẩu chữ một: có khối cấu trúc (div, nút, ô nhập…) xen giữa.
      return con.map(c => (vietJsx(c) ? bocJsxLe(c) : bienDoi(c))).join('')
    }
    // GỘP cả câu: chữ + phần tử nội dòng + biểu thức -> MỘT trx, trật tự từ dịch được.
    const args = [], manh = [], chuThich = []
    let cur = ''
    for (const c of noiDung) {
      if (laChuJsx(c)) {
        lamSachJsx(raw(c)).forEach((x, i) => { if (i === 0) cur += x; else { manh.push(cur); cur = x } })
      } else if (laChuThich(c)) chuThich.push(c.getText(sf))
      else if (ts.isJsxExpression(c) && laChuoiTinh(c.expression)) cur += c.expression.text
      else {
        cur += '{' + args.length + '}'
        args.push((ts.isJsxExpression(c) ? bienDoi(c.expression) : bienDoi(c)).trim())
      }
    }
    manh.push(cur)
    ghiNoi(noiDung[0])
    dungTrx = true
    const thut = thutCua(noiDung[0])
    return con.slice(0, a).map(raw).join('') + chuThich.map(x => x + eol + thut).join('') +
      '{trx(' + phatKhoa(manh, thut, eol) + (args.length ? ', ' + args.join(', ') : '') + ')}' +
      con.slice(b + 1).map(raw).join('')
  }

  /** Văn bản MỚI của nút `n`, phủ đúng [n.pos, n.end) — kể cả khoảng trắng đứng trước. */
  function bienDoi(n) {
    // Câu của một lời gọi tr()/trx() đã có: đã bọc rồi, để nguyên.
    if (n.parent && laGoiDich(n.parent, sf) && n.parent.arguments[0] === n) return raw(n)
    const truoc = laChuJsx(n) ? '' : sf.text.slice(n.pos, n.getStart(sf))
    if ((laChuoi(n) && coViet(n) && !laCong(n.parent)) ||
        (laCong(n) && !laCong(n.parent) && phang(n, []).some(coViet))) {
      const r = bocCum(n)
      if (r !== null) return truoc + r
      return raw(n)                          // cụm cố ý không bọc: đừng bọc lẻ từng mảnh
    }
    if (ts.isJsxElement(n) || ts.isJsxFragment(n)) {
      const vung = bocConJsx(n)
      if (vung !== null) {
        const mo = ts.isJsxElement(n) ? n.openingElement : n.openingFragment
        const dong = ts.isJsxElement(n) ? n.closingElement : n.closingFragment
        return bienDoi(mo) + vung + bienDoi(dong)
      }
    }
    if (laChuJsx(n)) return raw(n)
    const con = n.getChildren(sf).filter(c => !(c.kind >= ts.SyntaxKind.FirstJSDocNode
                                                && c.kind <= ts.SyntaxKind.LastJSDocNode))
    if (!con.length) return raw(n)
    return con.map(bienDoi).join('')
  }

  let moi = bienDoi(sf)
  if (moi !== nguon && (dungTr || dungTrx)) moi = themImport(moi, sf, p, eol,
    [dungTr && 'tr', dungTrx && 'trx'].filter(Boolean))
  if (ghi && moi !== nguon) fs.writeFileSync(p, moi, 'utf8')
  return { noi }
}

/** Thêm `tr` / `trx` vào import từ ngon_ngu — sửa dòng import sẵn có, chưa có thì chèn
 *  một dòng ngay sau import cuối. Phần trước import cuối không đổi chữ nào khi bọc (import
 *  không chứa câu tiếng Việt), nên vị trí trong văn bản cũ vẫn đúng ở văn bản mới. */
function themImport(moi, sf, p, eol, can) {
  const cacImport = sf.statements.filter(ts.isImportDeclaration)
  const co = cacImport.find(i => /\/ngon_ngu['"]$/.test(i.moduleSpecifier.getText(sf)))
  if (co) {
    const ds = co.importClause?.namedBindings
    const ten = ts.isNamedImports(ds) ? ds.elements.map(e => e.getText(sf)) : []
    if (can.every(t => ten.includes(t))) return moi
    const tat = [...new Set([...ten, ...can])].sort((a, b) => a.localeCompare(b))
    return moi.slice(0, ds.getStart(sf)) + '{ ' + tat.join(', ') + ' }' + moi.slice(ds.end)
  }
  const duong = path.relative(path.dirname(p), path.join(SRC, 'ngon_ngu')).replace(/\\/g, '/')
  const dong = `import { ${can.join(', ')} } from '${duong.startsWith('.') ? duong : './' + duong}'` + eol
  if (cacImport.length) {
    const nl = moi.indexOf('\n', cacImport[cacImport.length - 1].end)
    return moi.slice(0, nl + 1) + dong + moi.slice(nl + 1)
  }
  return dong + eol + moi
}
