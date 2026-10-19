/** MẠCH CHẠY — một lượt backtest của LEAN thành từng NHỊP xem được bằng mắt.
 *
 *  Tệp này KHÔNG vẽ gì và KHÔNG gọi Python. Nó chỉ nhận hai thứ LEAN đã trả về rồi
 *  xếp lại thành một cuộn phim: lượt ấy đi đường nào, van nào mở, van nào đóng, tiền
 *  tới đâu. Tách ra khỏi màn hình để soi được bằng mắt thường và để sau này kiểm được
 *  bằng máy — chỗ dễ sai nhất của cả màn «Chạy máy» nằm hết trong đây.
 *
 *  ⚠ KHÔNG DỰNG LẠI BỘ MÁY NÀO (D-11). Mọi con số ở đây là của LEAN:
 *    · `kq.lenh[].tag` — nhãn `bộ sinh mã` gắn sẵn lúc sinh: `[4A.2] RSI(14) < 30`,
 *      tức SỐ KHỐI cộng chuỗi điều kiện đã khớp để tới được khối ấy;
 *    · `kq.bieu_do` — đường vốn, chính là trục thời gian thật của lượt chạy.
 *  Không một chỗ nào trong đây tính lại giá, chỉ báo hay vị thế.
 *
 *  ======================= VAN ĐÓNG: SUY RA ĐƯỢC TỚI ĐÂU =======================
 *
 *  LEAN ngắt ở điều kiện sai đầu tiên, nên nó KHÔNG nói «RSI 62,30, cần < 30». Thiết
 *  kế (§8.2) để ngỏ hai đường: chèn dòng chẩn đoán vào thuật toán, hay suy ra. Chủ dự
 *  án chốt SUY RA — không đụng bộ sinh mã, không dòng nào app tự viết.
 *
 *  Suy được ngần này, và chỉ ngần này:
 *    · MỞ — chắc chắn. Nhịp ấy có một lệnh ra từ dưới cổng, nên dòng đã qua nó. Mọi
 *      cổng trên đường từ Bắt đầu tới khối nổ đều mở.
 *    · ĐÓNG — chắc trong phạm vi nói ở dưới. Dưới cổng không còn cổng nào nữa mà
 *      cũng không có lệnh nào ra.
 *    · LẶNG — chưa biết. Dưới cổng còn cổng khác: dòng dừng ở KHÚC ấy, mà dừng ở
 *      đúng cái nào thì không suy ra được. Vẽ mờ, KHÔNG đánh *cạch* — nói "chưa rõ"
 *      bằng hình, chứ không chỉ đích danh một cổng rồi có khi chỉ sai.
 *
 *  ⚠ VÀ MỘT CHỖ «ĐÓNG» VẪN CÓ THỂ OAN, nói thẳng ra đây: `set_holdings` không sinh
 *  lệnh khi tỷ trọng đang đúng rồi. Cổng mở, hành động chạy, mà LEAN im — nhìn y hệt
 *  cổng đóng. Nên chữ trên màn hình nói về DÒNG («dòng dừng ở đây»), không bao giờ
 *  nói về điều kiện («RSI chưa đủ thấp»): câu thứ hai là câu app không chứng minh
 *  được. Muốn chắc hẳn thì phải chèn dòng chẩn đoán — đường còn để ngỏ ở §8.2.
 *
 *  ⚠ CHỈ SUY TỪ KHỐI ĐÃ TỪNG NỔ trong cả lượt, và đây là chỗ bản đầu sai. Năm loại
 *  khối hành động KHÔNG BAO GIỜ sinh lệnh (Ghi chú, Vẽ bảng, Ghi nhớ, Báo tin, Phát
 *  tín hiệu). Lấy sự im lặng của chúng làm bằng chứng thì mọi cổng nằm trên chúng
 *  đóng vĩnh viễn suốt cả lượt — một màn hình đầy van đóng, sai hết, mà trông rất
 *  thuyết phục. Khối nào đã nổ ít nhất MỘT lần thì mới chắc nó sinh lệnh được; im
 *  lặng của nó từ đó mới nói lên điều gì. Tự hiệu chuẩn, không cần từ điển thứ hai.
 */
import type { DongLenh, Edge, KetQuaChay, KetQuaSoat, Step } from '../types'

/** Id một sợi dây. Dùng CHUNG với chỗ dựng node/edge của màn Chạy máy — hai chỗ ghép
 *  id theo hai công thức thì dây sáng lên sẽ không phải sợi dây đang có dòng. */
export const idDay = (e: Edge) => `${e.from}->${e.to}:${e.port ?? 'out'}`

export type TrangThaiVan = 'mo' | 'dong' | 'lang'

/** MỘT NHỊP — một điểm trên trục thời gian của lượt chạy. */
export interface NhipChay {
  /** Giây UNIX, đúng như LEAN ghi trên biểu đồ. */
  t: number
  /** Vốn tại nhịp này. */
  von: number
  /** Lệnh ra ở nhịp này (có thể rỗng — phần lớn nhịp là rỗng). */
  lenh: DongLenh[]
  /** Khối hành động đã nổ, không lặp. */
  no: string[]
  /** Khối có lệnh BỊ SÀN TỪ CHỐI ở nhịp này. Vẫn nằm trong `no` — hành động ĐÃ chạy,
   *  nên mấy cổng phía trên nó vẫn mở; chỉ cái lệnh là không thành. Đỏ để dành đúng
   *  hai chỗ: lỗ, và lệnh bị từ chối (thiết kế §1). */
  tuChoi: string[]
  /** Trạng thái van của MỌI cổng Hỏi trong sơ đồ. */
  van: Record<string, TrangThaiVan>
  /** Dây đang có dòng chạy (id dây). */
  day: string[]
}

export interface MachChay {
  nhip: NhipChay[]
  /** Mọi cổng Hỏi chạy tới được — để màn hình biết phải vẽ bao nhiêu cái van. */
  cong: string[]
  vonDau: number
  vonMin: number
  vonMax: number
  /** Khối đã nổ ít nhất một lần cả lượt — cũng chính là tập dùng để suy van đóng. */
  khoiNo: string[]
  /** Lệnh mang nhãn không khớp khối nào trên sơ đồ. ĐẾM ĐỂ NÓI RA, không nuốt: nó
   *  nghĩa là sơ đồ đã sửa sau lượt chạy, và cuộn phim này kể chuyện sơ đồ khác. */
  soLenhLac: number
  /** Có đường vốn thật của LEAN không. Không có thì trục thời gian dựng tạm từ giờ
   *  của mấy cái lệnh — vẫn xem được, nhưng mép dưới không vẽ đường nào. */
  coVon: boolean
}

/** Nhãn `[4A.2] RSI(14) < 30` -> `4A.2`. Rỗng nếu nhãn không theo khuôn ấy. */
export function soKhoiCuaNhan(nhan: string): string {
  const m = /^\s*\[([^\]]+)\]/.exec(nhan || '')
  return m ? m[1].trim() : ''
}

/** Giây UNIX của một lệnh. LEAN ghi `2020-03-12 09:31:00`, giờ UTC. */
function giayCuaLenh(luc: string): number {
  const t = Date.parse(String(luc || '').replace(' ', 'T') + 'Z')
  return Number.isFinite(t) ? Math.floor(t / 1000) : 0
}

/** Đường vốn LEAN dựng -> [[giây, vốn]].
 *
 *  Một điểm của LEAN là `[giây, y]` với đường thường và `[giây, mở, cao, thấp, đóng]`
 *  với nến (xem `chay_lean._diem`), nên giá trị LUÔN là phần tử cuối — một phép lấy
 *  đúng cho cả hai, chứ không phải hai nhánh `if`. */
function diemVon(kq: KetQuaChay): number[][] {
  const bang = (kq.bieu_do ?? []).find(b => b.ten === 'Strategy Equity')
             ?? (kq.bieu_do ?? []).find(b => b.duong.some(d => d.diem.length > 1))
  if (!bang) return []
  const d = bang.duong.find(x => x.ten === 'Equity')
          ?? [...bang.duong].sort((a, b) => b.diem.length - a.diem.length)[0]
  return (d?.diem ?? []).filter(p => p.length >= 2)
}

export function dungMach(soat: KetQuaSoat, kq: KetQuaChay, steps: Step[]): MachChay {
  const the = soat.the ?? {}
  const thuTu = soat.thu_tu ?? {}

  /* ---- số khối -> id. Nhãn trên lệnh mang SỐ, không mang id. ---- */
  const theoSo = new Map<string, string>()
  for (const [id, so] of Object.entries(thuTu)) theoSo.set(so, id)

  /* ---- CHA của mỗi khối: duyệt rộng từ khối Bắt đầu, bỏ đường ↻ ----
     Đường ↻ đi NGƯỢC dòng chảy; tính nó vào là đường từ Bắt đầu tới một khối có thể
     chạy lùi, và cả phép suy van ở dưới sai theo. Cùng luật với `core.so_vong_canh`:
     CÓ KHOÁ `so_vong` là đường quay lại, kể cả khi giá trị là 0 hay null. */
  const ra = new Map<string, Edge[]>()
  for (const e of soat.edges ?? []) {
    if ('so_vong' in e) continue
    const d = ra.get(e.from) ?? []
    d.push(e)
    ra.set(e.from, d)
  }
  const cha = new Map<string, { cha: string; day: string }>()
  const goc = soat.entry ?? ''
  if (goc) {
    const hang = [goc]
    const da = new Set([goc])
    for (let i = 0; i < hang.length; i++) {
      for (const e of ra.get(hang[i]) ?? []) {
        if (da.has(e.to)) continue
        da.add(e.to)
        cha.set(e.to, { cha: hang[i], day: idDay(e) })
        hang.push(e.to)
      }
    }
  }

  /** Đường từ khối Bắt đầu tới `id`: các khối đi qua, và các dây đi qua.
   *
   *  Sơ đồ có thể có chỗ NHẬP (hai nhánh vào cùng một khối); duyệt rộng ở trên giữ
   *  đường NGẮN NHẤT, và ở đây cũng vậy. Nói ra chứ không lặng lẽ: với sơ đồ nhập
   *  nhánh, vệt sáng là một trong mấy đường tới, không phải chắc chắn đường ấy. */
  const nho = new Map<string, { nut: string[]; day: string[] }>()
  function duong(id: string): { nut: string[]; day: string[] } {
    const sanCo = nho.get(id)
    if (sanCo) return sanCo
    const nut: string[] = []
    const day: string[] = []
    let cur = id
    // Chặn bằng SỐ KHỐI, không bằng `while (true)`: bảng `cha` dựng từ duyệt rộng
    // nên không thể có vòng, mà một vòng lọt vào đây là treo cả cửa sổ.
    for (let i = 0; i <= cha.size + 1 && cur; i++) {
      nut.unshift(cur)
      const c = cha.get(cur)
      if (!c) break
      day.unshift(c.day)
      cur = c.cha
    }
    const kq2 = { nut, day }
    nho.set(id, kq2)
    return kq2
  }

  const laCong = (id: string) => !!the[id]?.la_cong
  /** Cổng Hỏi CHẠY TỚI ĐƯỢC (có số thứ tự). Cổng không ai nối vào thì không chạy,
   *  nên vẽ van cho nó là vẽ một bộ phận không gắn vào máy. */
  const cong = Object.keys(thuTu).filter(laCong)

  /* ---- gom lệnh theo KHỐI, rồi theo NHỊP ---- */
  const dsLenh = kq.lenh ?? []
  let soLenhLac = 0
  const lenhCuaKhoi = dsLenh.map(l => {
    const id = theoSo.get(soKhoiCuaNhan(l.tag)) ?? ''
    if (!id) soLenhLac++
    return { l, id, t: giayCuaLenh(l.luc) }
  })

  /* ---- trục thời gian: đường vốn của LEAN ---- */
  const dv = diemVon(kq)
  const coVon = dv.length > 1
  const khung: { t: number; von: number }[] = coVon
    ? dv.map(p => ({ t: p[0], von: p[p.length - 1] }))
    : [...new Set(lenhCuaKhoi.map(x => x.t))].sort((a, b) => a - b)
        .map(t => ({ t, von: 0 }))
  if (!khung.length) khung.push({ t: 0, von: 0 })

  /* ---- mỗi lệnh về NHỊP GẦN NHẤT ----
     Lệnh xảy ra trong phiên còn đường vốn lấy mẫu theo ngày, nên giờ không bao giờ
     trùng khít. Gần nhất thì lệch nhiều nhất nửa nhịp về một phía — dồn hết sang một
     phía (nhịp sau) thì cú mua đầu tiên hiện ra muộn một ngày so với đường vốn đã
     nhảy, và nhìn ảnh thấy ngay là lệch. */
  const theoNhip: { l: DongLenh; id: string }[][] = khung.map(() => [])
  for (const x of lenhCuaKhoi) {
    let lo = 0
    let hi = khung.length - 1
    while (lo < hi) {
      const giua = (lo + hi) >> 1
      if (khung[giua].t < x.t) lo = giua + 1
      else hi = giua
    }
    const j = lo > 0 && Math.abs(khung[lo - 1].t - x.t) <= Math.abs(khung[lo].t - x.t)
      ? lo - 1 : lo
    theoNhip[j].push({ l: x.l, id: x.id })
  }

  /** Khối đã nổ ít nhất một lần cả lượt — xem lời dặn đầu tệp: CHỈ tập này mới được
   *  dùng để suy van đóng. */
  const khoiNo = [...new Set(lenhCuaKhoi.map(x => x.id).filter(Boolean))]
  /** Khối Quay về không phải khối sinh lệnh; nó cũng không bao giờ nằm trong `khoiNo`,
   *  nên lọc ở đây chỉ là lưới an toàn cho sơ đồ lạ. */
  const quayVe = new Set(steps.filter(s => s.type === 'quay_ve').map(s => s.id))
  const suyTu = khoiNo.filter(id => !quayVe.has(id) && !laCong(id))

  /* ---- dựng từng nhịp ---- */
  const nhip: NhipChay[] = khung.map((k, i) => {
    const ds = theoNhip[i]
    const no = [...new Set(ds.map(x => x.id).filter(Boolean))]

    // MỞ: mọi cổng trên đường tới một khối đã nổ. Chắc chắn, không suy đoán.
    const moChac = new Set<string>()
    const day = new Set<string>()
    for (const a of no) {
      const d = duong(a)
      for (const n of d.nut) if (laCong(n)) moChac.add(n)
      for (const e of d.day) day.add(e)
    }

    const van: Record<string, TrangThaiVan> = {}
    for (const g of cong) van[g] = moChac.has(g) ? 'mo' : 'lang'

    // ĐÓNG: khối sinh-lệnh-được mà nhịp này im. Chỉ chỉ đích danh khi dưới cổng
    // không còn cổng nào nữa — còn thì để 'lang'.
    for (const a of suyTu) {
      if (no.includes(a)) continue
      const gs = duong(a).nut.filter(laCong)
      const i2 = gs.findIndex(g => !moChac.has(g))
      if (i2 < 0) continue        // mọi cổng đã mở mà vẫn im: hành động không đổi gì
      const g = gs[i2]
      // Dòng CHẮC CHẮN tới được cổng ấy, nên đoạn dây tới nó phải sáng.
      for (const e of duong(g).day) day.add(e)
      if (gs.length - i2 === 1) van[g] = 'dong'
    }

    const tuChoi = [...new Set(ds.filter(x => x.id && !x.l.hop_le).map(x => x.id))]
    return { t: k.t, von: k.von, lenh: ds.map(x => x.l), no, tuChoi, van, day: [...day] }
  })

  const von = khung.map(k => k.von)
  return {
    nhip,
    cong,
    khoiNo,
    soLenhLac,
    coVon,
    vonDau: von[0] ?? 0,
    vonMin: Math.min(...von),
    vonMax: Math.max(...von),
  }
}
