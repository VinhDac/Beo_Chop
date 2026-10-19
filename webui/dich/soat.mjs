/** SOÁT: câu nào cần bản tiếng Anh, bảng dịch đã có chưa.
 *
 *  Câu cần dịch là:
 *    · câu của mọi lời gọi tr() / trx() khi nó là chữ cố định (chuỗi, chuỗi cộng);
 *    · chuỗi tiếng Việt nằm NGOÀI mọi hàm — bảng hằng, dịch bằng tr(biến) lúc hiện ra;
 *    · nhãn Python gửi sang mà giao diện dịch bằng tr(nhãn) — lấy từ
 *      `tools/nhan_python_dich.py`, chạy bằng Python trong .venv.
 */
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { BANG, BO_CAU, WEBUI, coChu, docTep, dsTep, laCong, laGoiDich, laViet, oDien, tenTep, tinh, ts }
  from './chung.mjs'

const laHam = (c) => ts.isFunctionDeclaration(c) || ts.isFunctionExpression(c) ||
  ts.isArrowFunction(c) || ts.isMethodDeclaration(c) || ts.isConstructorDeclaration(c) ||
  ts.isGetAccessor(c) || ts.isSetAccessor(c)

/** Câu trong mã: Map câu -> nơi dùng đầu tiên ("tệp:dòng"). */
export function cauTrongMa() {
  const can = new Map()
  for (const p of dsTep()) {
    const { sf } = docTep(p)
    const noi = (n) => tenTep(p) + ':' + (sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1)
    const them = (k, n) => { k = k.trim(); if (k && !BO_CAU.has(k) && !can.has(k)) can.set(k, noi(n)) }
    const trongHamHayTr = (n) => {
      for (let c = n.parent; c; c = c.parent) if (laHam(c) || laGoiDich(c, sf)) return true
      return false
    }
    ;(function di(n) {
      if (laGoiDich(n, sf) && n.arguments.length) {
        const v = tinh(n.arguments[0])
        if (v !== null) them(v, n)
      } else if (!trongHamHayTr(n)) {
        // Bảng hằng đầu tệp.
        if ((ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n)) && laViet(n.text)
            && !laCong(n.parent) && !(ts.isPropertyAssignment(n.parent) && n.parent.name === n)) {
          them(n.text, n)
        } else if (laCong(n) && !laCong(n.parent)) {
          const v = tinh(n)
          if (v !== null && laViet(v)) { them(v, n); return }
        }
      }
      ts.forEachChild(n, di)
    })(sf)
  }
  return can
}

/** Nhãn Python mà giao diện dịch bằng tr(nhãn): { nhan } — hoặc { loi } là vì sao không
 *  chạy được, kèm đuôi stderr để thấy ngay khoá / module nào hỏng.
 *  Lọc như bảng hằng (laViet không cờ jsx): bootstrap gửi cả MÃ lẫn nhãn, mà mã như
 *  'cam', 'trang', 'cho' trùng chữ Việt không dấu. */
export function nhanPython() {
  const goc = path.dirname(WEBUI)
  const py = path.join(goc, '.venv', 'Scripts', 'python.exe')
  if (!fs.existsSync(py)) return { loi: 'không có ' + py }
  const r = spawnSync(py, [path.join(goc, 'tools', 'nhan_python_dich.py')], {
    encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } })
  // loi phải luôn khác rỗng — stderr trắng mà coi là "không lỗi" thì cổng lại xanh oan.
  if (r.status !== 0)
    return { loi: (r.stderr || r.error?.message || '').trim().split(/\r?\n/).slice(-8).join('\n')
      || 'mã thoát ' + (r.status ?? r.signal) }
  let nhan
  // `BO_CAU` lọc ở đây NỮA, không chỉ trong `cauTrongMa`: nhãn hai tiếng của nhóm Ngôn
  // ngữ do Python khai, nên nó tới qua đường này (xem chú thích ở `chung.mjs`).
  try { nhan = JSON.parse(r.stdout).filter(s => laViet(s) && !BO_CAU.has(s.trim())) }
  catch (e) { return { loi: 'đầu ra không phải JSON: ' + e.message } }
  // Rỗng cũng là hỏng: hôm nay ~100 nhãn. Cho qua thì --don coi mọi bản dịch nhãn Python
  // là thừa — y như lúc script chết.
  return nhan.length ? { nhan } : { loi: 'script chạy được mà không trả nhãn nào' }
}

/** Bảng dịch: Map câu -> { en, nut } (nút cú pháp, để còn xoá được). */
export function docBang() {
  const { sf, nguon, eol } = docTep(BANG)
  const bang = new Map()
  ts.forEachChild(sf, function di(n) {
    if (ts.isPropertyAssignment(n) && ts.isStringLiteral(n.name) && ts.isStringLiteral(n.initializer))
      bang.set(n.name.text, { en: n.initializer.text, nut: n })
    ts.forEachChild(n, di)
  })
  return { bang, sf, nguon, eol }
}

/** So mã với bảng. Trả { thieu: [[câu, nơi]], lech: [[câu, nơi]], thua: [câu], loiPython }.
 *  Có loiPython thì thieu / thua thiếu hẳn nhãn Python — đừng tin, càng đừng dọn theo. */
export function soat() {
  const can = cauTrongMa()
  const py = nhanPython()
  for (const k of py.nhan ?? []) if (!can.has(k)) can.set(k, 'python')
  const { bang } = docBang()
  const thieu = [...can].filter(([k]) => coChu(k) && !(bang.get(k)?.en))
  const lech = [...can].filter(([k]) => bang.get(k)?.en && oDien(k) !== oDien(bang.get(k).en))
  const thua = [...bang.keys()].filter(k => !can.has(k))
  return { thieu, lech, thua, loiPython: py.loi }
}

/** Bỏ khoá thừa khỏi bảng dịch — cả dòng của nó, và dòng nhóm "// ── tệp" nào bỏ xong
 *  thì trống trơn. Trả số khoá đã bỏ. */
export function donBang(thua) {
  if (!thua.length) return 0
  const { bang, sf, nguon } = docBang()
  const bo = new Set(thua)
  const khoang = []
  for (const [k, { nut }] of bang) {
    if (!bo.has(k)) continue
    const dau = nguon.lastIndexOf('\n', nut.getStart(sf)) + 1
    let cuoi = nguon.indexOf('\n', nut.end)
    cuoi = cuoi < 0 ? nguon.length : cuoi + 1
    khoang.push([dau, cuoi])
  }
  let moi = nguon
  for (const [a, b] of khoang.sort((x, y) => y[0] - x[0])) moi = moi.slice(0, a) + moi.slice(b)
  // Nhóm rỗng: dòng "// ── …" mà ngay sau là một nhóm khác hay dấu đóng bảng.
  moi = moi.replace(/^[ \t]*\/\/ ── [^\r\n]*\r?\n(?=[ \t]*(\/\/ ── |\}))/gm, '')
  fs.writeFileSync(BANG, moi, 'utf8')
  return khoang.length
}
