/** Hình dạng dữ liệu đi qua cầu nối.
 *
 * Luật: giao diện KHÔNG tự ghép chữ trên khối, KHÔNG tự tính số thứ tự, KHÔNG tự soát
 * luật nào — nó gửi sơ đồ sang Python rồi vẽ lại đúng cái nhận về (`Card`, `thu_tu`,
 * `van_de`). Nhờ vậy huy hiệu trên hộp không thể nói khác thứ lõi thật sự hiểu.
 */

export interface Reply<T> {
  ok: boolean
  value?: T
  error?: string
  trace?: string
  [k: string]: unknown
}

/* ----------------------------------- Sơ đồ ----------------------------------- */

export type StepKind = 'start' | 'action' | 'group'

/** Khối nằm trong HẠT NHÂN nào — một mảng sơ đồ gói lại cho dễ nhìn.
 *  CHỈ là cách nhìn: bộ chạy, số thứ tự, bảng Vấn đề đều không đọc nó. */
export interface HatNhanTag {
  id: string
  ten: string
  /** Chỗ đứng của cái KHUNG trên sơ đồ chính (có thể chưa có). */
  x?: number
  y?: number
}

/** Một khối. Khoá riêng của từng loại hành động đi kèm tự do — lõi giữ nguyên chúng
 *  cho tới khi có từ điển khối (D-12). */
export interface Step {
  id: string
  kind: StepKind
  name?: string
  /** Loại hành động; Nhóm và Bắt đầu không có. */
  type?: string
  /** Chỉ Nhóm: chuỗi hành động bên trong. */
  actions?: Record<string, unknown>[]
  /** Chỉ khối Quay về: id khối đích, và số vòng (trống = lặp mãi). */
  ve?: string
  so_vong?: number | null

  // --- khoá tả CÁI NÚT, không tả việc khối làm (core.KHOA_CANVAS) ---
  pos?: [number, number]
  mau?: string
  ghim?: boolean
  hat_nhan?: HatNhanTag

  [k: string]: unknown
}

export interface Edge {
  from: string
  to: string
  port?: string
  from_side?: string
  to_side?: string
  /** Có khoá này tức đây là ĐƯỜNG ↻ quay lại, không phải dây thường. */
  so_vong?: number | null
}

/** Một dòng chữ trên thẻ khối. `type` để giao diện chọn icon — Python nói ĐÓ LÀ GÌ,
 *  web quyết VẼ GÌ. */
export interface DongThe {
  text: string
  type?: string | null
}

/** Thẻ vẽ một khối. Mọi chuỗi trong đây do Python sinh. */
export interface Card {
  id: string
  kind: StepKind
  title: string
  badges: string[]
  lines: DongThe[]
  so_hanh_dong: number
  la_cong: boolean
}

export interface VanDe {
  severity: 'error' | 'warning'
  step: string | null
  index: number | null
  message: string
}

/** Những gì `api.soat` trả về — tất cả trong MỘT lượt. */
export interface KetQuaSoat {
  /** {id khối: "4A.2"}. Không có khoá = khối không chạy tới. */
  thu_tu: Record<string, string>
  entry: string | null
  the: Record<string, Card>
  van_de: VanDe[]
  /** {id khối cuối vòng: [id khối đầu vòng, số vòng | null]} */
  vong: Record<string, [string, number | null]>
  edges: Edge[]
}

export interface Strategy {
  schema: number
  type: string
  name: string
  steps: Step[]
  edges: Edge[]
}

/* ----------------------------- Khối XÁC NHẬN ------------------------------- */

/** Một ô tham số của đại lượng (chu kỳ, hệ số…). */
export interface ThamSo {
  ten: string
  nhan: string
  mac_dinh: number
  nho_nhat: number
  lon_nhat: number
}

/** Một đại lượng đọc được từ LEAN. `lean` là lời khai: thứ của LEAN đứng sau nó —
 *  không khai được thì nó không được có mặt trong từ điển. */
export interface DaiLuong {
  ma: string
  nhan: string
  lean: string
  kieu: 'so' | 'co_khong'
  don_vi: string
  tham_so: ThamSo[]
  /** Chỉ báo trả NHIỀU đường (MACD, Bollinger…): [mã, nhãn]. */
  duong?: [string, string][]
}

/** Một VẾ của dòng điều kiện: một đại lượng, hoặc một con số. */
export interface VeDieuKien {
  ma_dl?: string
  /** Để trống = mã đang xét. Gõ mã khác là ra so sánh chéo mã. */
  ma?: string
  tham_so?: Record<string, number>
  duong?: string
  so?: number
}

export interface DongDieuKien {
  trai: VeDieuKien
  phep: string
  phai: VeDieuKien
}

export interface LoaiHoi {
  ma: string
  nhan: string
  mo_ta: string
  icon: string
  can_ma: boolean
  /** Vế phải có ô chọn mã riêng không — chỉ loại nào cho so chéo mã. */
  hai_ve_ma: boolean
  /** Chuỗi = loại này chưa chạy được, và đây là lý do. `false` = dùng được. */
  tat: string | false
  nhom: { ten: string; dai_luong: DaiLuong[] }[]
}

export interface TuDienHoi {
  phep_so: { ma: string; nhan: string }[]
  phep_co_khong: { ma: string; nhan: string }[]
  loai: LoaiHoi[]
}

/* ----------------------------- Khối HÀNH ĐỘNG ------------------------------ */

/** Một Ô của khối hành động. Khác khối Hỏi: ở đây không có "kho đại lượng dùng
 *  chung" — mỗi loại việc khai bộ ô của riêng nó, vì mỗi hàm LEAN nhận tham số khác. */
export interface OLam {
  ten: string
  nhan: string
  kieu: 'so' | 'chu' | 'chon' | 'co_khong'
  mac_dinh: unknown
  don_vi: string
  goi_y: string
  /** Chỉ ô CHỌN: [mã, nhãn]. */
  chon: [string, string][]
  bat_buoc: boolean
}

/** Một loại việc. `lean` là lời khai: hàm có thật của LEAN đứng sau nó. */
export interface LoaiLam {
  ma: string
  nhan: string
  mo_ta: string
  icon: string
  /** Nhóm trên ribbon — Python quyết, web không tự chia. */
  nhom: string
  can_ma: boolean
  lean: string
  /** Chuỗi = loại này có cái bẫy, và đây là lời cảnh báo. `false` = dùng thẳng. */
  tat: string | false
  o: OLam[]
  /** Ô THÊM theo lựa chọn của ô chọn đầu tiên (lệnh Giới hạn cần giá giới hạn, lệnh
   *  Dừng cần giá kích hoạt). Khoá = mã lựa chọn. */
  theo_loai: Record<string, { lean: string; o: OLam[] }>
  /** Có khoá này tức khối cần một ĐẠI LƯỢNG, lấy từ nhóm Hỏi tên ở đây. */
  dai_luong_tu?: string | null
}

export interface TuDienLam {
  loai: LoaiLam[]
}

/* ------------------------------- Kho và khoá -------------------------------- */

/** App lưu file ở đâu — `api.kho_danh_muc`. */
export interface KhoDanhMuc {
  luu_tru: {
    goc: string
    muc: { ten: string; duong_dan: string; so_luong: number; danh_sach: string[] }[]
  }
}

/** Khoá đặt ở đâu. KHÔNG BAO GIỜ có token. */
export interface KhoaQC {
  co: boolean
  nguon: 'bien_moi_truong' | 'file' | null
  user_id: string | null
  duong: string
  loi?: string
}
