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
  /** Đơn vị — bảng chọn xếp «cùng đơn vị» lên trước nhờ ô này. Luôn có với `kieu` số. */
  don_vi: string
  tham_so: ThamSo[]
  /** Chỉ báo trả NHIỀU đường (MACD, Bollinger…): [mã, nhãn]. */
  duong?: [string, string][]
  /** Cần CHỌN MÃ không — Python suy thẳng từ ô `lean`, không phải cờ viết tay. */
  can_ma: boolean
  /** Họ nó thuộc về (`hoi_thi_truong`…) — để lấy icon và câu cảnh báo dữ liệu. */
  ho: string
  /** Tên mục trong bảng chọn: «Giá», «Chỉ báo», «Vị thế»… */
  nhom: string
}

/** Một VẾ của dòng điều kiện: một đại lượng, hoặc một con số. */
export interface VeDieuKien {
  ma_dl?: string
  /** Rỗng = mã đang xét. Chọn mã khác là ra so sánh chéo mã — CHỌN, không gõ:
   *  danh sách lấy từ khối Bắt đầu (xem `ChonMa.tsx`). */
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

/** Một HỌ câu hỏi. KHÔNG còn là tường ngăn: hai vế của một dòng rút từ cùng MỘT
 *  kho (`TuDienHoi.kho`), nên `Giá hiện tại > Giá vốn trung bình` vẽ được. Họ chỉ
 *  còn làm đầu mục trong bảng chọn, và cho khối cái icon + cảnh báo dữ liệu. */
export interface LoaiHoi {
  ma: string
  nhan: string
  mo_ta: string
  icon: string
  /** Chuỗi = họ này chưa chạy được, và đây là lý do. `false` = dùng được. */
  tat: string | false
}

export interface TuDienHoi {
  phep_so: { ma: string; nhan: string }[]
  phep_co_khong: { ma: string; nhan: string }[]
  loai: LoaiHoi[]
  /** CẢ 68 đại lượng, một mảng phẳng. Bảng chọn bày đúng mảng này — nên không có
   *  cách nào một đại lượng khai trong `hoi.py` mà người dùng với không tới. */
  kho: DaiLuong[]
}

/* ----------------------------- Khối HÀNH ĐỘNG ------------------------------ */

/** Một Ô của khối hành động. Khác khối Hỏi: ở đây không có "kho đại lượng dùng
 *  chung" — mỗi loại việc khai bộ ô của riêng nó, vì mỗi hàm LEAN nhận tham số khác. */
export interface OLam {
  ten: string
  nhan: string
  /** `ds_ma` và `khoang_ngay` chỉ khối Bắt đầu có — widget của chúng nằm ngay trong
   *  `HopBatDau.tsx`, không ở `ORuot.tsx`, vì ô chung phải ở lại chung. */
  kieu: 'so' | 'chu' | 'chon' | 'co_khong' | 'ds_ma' | 'khoang_ngay'
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
  /** Khối này có ô chọn ĐẠI LƯỢNG không (chọn trong CẢ kho, không riêng một họ). */
  co_dai_luong?: boolean
}

export interface TuDienLam {
  loai: LoaiLam[]
}

/** Kết quả sinh mã. `ok` False thì `ma` vẫn có (phần sinh được) — nhưng ĐừNG chạy:
 *  `van_de` nói chỗ nào sơ đồ chưa diễn đạt hết. */
export interface KetQuaSinh {
  ok: boolean
  ma: string
  ten_lop: string
  van_de: VanDe[]
  /** Có khi đã ghi ra file. */
  duong?: string
}

/** Một ĐƯỜNG trong một bảng biểu đồ của LEAN.
 *
 *  `kieu` do Python dịch từ `seriesType` — web KHÔNG tự khai bảng mã số ấy.
 *  `diem`: `[giây, giá trị]`, hoặc `[giây, mở, cao, thấp, đóng]` với nến. */
export interface DuongBieuDo {
  ten: string
  kieu: 'duong' | 'cham' | 'nen' | 'cot' | 'co' | 'vung_chong' | 'tron'
        | 'o_vuong' | 'nhiet'
  don_vi: string
  diem: number[][]
}

/** Một BẢNG biểu đồ — LEAN tự dựng tám cái, ta bày hết rồi cho bật tắt. */
export interface BangBieuDoDL {
  ten: string
  duong: DuongBieuDo[]
  /** Bày sẵn lúc mở màn Kết quả không. */
  hien: boolean
}

/** Bảng Thống kê trượt: mỗi tháng một dòng, bốn cột cửa sổ 1/3/6/12 tháng. */
export interface ThongKeCuon {
  chi_tieu: string[]
  dong: { ngay: string; cua: Record<string, Record<string, number>> }[]
}

/** Một dòng trong bảng Lệnh — chữ đã dịch sẵn ở Python, web không tự khai bảng mã số.
 *  (`OrderStatus` của LEAN không có số 4 — đoán một bảng như thế là sai lặng.) */
export interface DongLenh {
  id: number | string
  ma: string
  luc: string
  loai: string
  so_luong: number
  gia: number
  trang_thai: string
  /** false = sàn từ chối. */
  hop_le: boolean
  tag: string
}

export interface DongGiaoDich {
  ma: string
  vao_luc: string
  gia_vao: number
  ra_luc: string
  gia_ra: number
  so_luong: number
  phi: number
  lai_lo: number
  thang: boolean
}

/** Kết quả một lượt backtest. Mọi con số do LEAN tính, app chỉ bày. */
export interface KetQuaChay {
  ok: boolean
  loi: string
  ten_lop?: string
  thu_muc?: string
  /** TÁM ô số trên đầu — LEAN dựng sẵn đúng tám mục, không phải ta chọn. */
  o_so?: Record<string, string>
  bieu_do?: BangBieuDoDL[]
  thong_ke?: Record<string, string>
  cuon?: ThongKeCuon
  may_chu?: Record<string, string>
  /** Mã LEAN đã sinh và vừa chạy — cho tab Mã. */
  ma?: string
  lenh?: DongLenh[]
  giao_dich?: DongGiaoDich[]
  nhat_ky?: string
  /** Tên mốc so sánh thật — để trống thì LEAN tự lấy SPY. */
  moc_ten?: string
  van_de?: VanDe[]
}

/** Lượt backtest đang tới đâu.
 *
 *  ⚠ KHÔNG CÓ PHẦN TRĂM, và đó là cố ý: LEAN không in tiến độ ra màn hình. Bịa một
 *  con số còn tệ hơn không có — nó hứa một cái mốc mà không ai giữ được. */
export interface TienDoChay {
  dang_chay: boolean
  xong: boolean
  giay: number
  giai_doan: string
  dong_cuoi: string
  so_dong: number
  /** Chỉ có khi `xong`. */
  ket_qua?: KetQuaChay
}

/** LEAN đã trỏ đúng chỗ chưa. */
export interface LeanSanSang {
  ok: boolean
  goc: string
  launcher: string
  dll: string
  loi: string
}

/* ------------------------------ Khối BẮT ĐẦU -------------------------------- */

/** Một dòng trong danh sách mã. Mỗi loại tài sản là một hàm `add_*` khác của LEAN. */
export interface MaChay {
  ma: string
  loai: string
}

/** Khoảng backtest. Lưu kiểu ISO (`2010-01-31`) chứ không phải kiểu Việt: file phải
 *  xếp được theo thứ tự chữ và không mập mờ ngày/tháng. Thẻ khối mới hiện kiểu Việt. */
export interface KhoangNgay {
  tu: string
  den: string
}

/** Một nhịp chạy. `res` = độ phân giải dữ liệu phải đăng ký; `chay` = `on_data` hay
 *  một câu `schedule.on`. Hai thứ trong LEAN, một câu hỏi với người chơi. */
export interface NhipChay {
  ma: string
  nhan: string
  res: string
  chay: string
  /** Ô chỉ hiện khi chọn nhịp này (giờ, phút, số phút sau khi mở cửa…). */
  o_them: { ten: string; nhan: string; mac_dinh: number
            nho_nhat: number; lon_nhat: number }[]
}

export interface TuDienBatDau {
  /** Sáu ô, cùng hình dạng với ô của khối Làm nên dùng chung được widget. */
  o: OLam[]
  loai_tai_san: { ma: string; nhan: string; lean: string }[]
  /** Mã có sẵn trong bộ dữ liệu MIỄN PHÍ, để gợi ý — không phải để chặn. */
  co_san: Record<string, string[]>
  nhip: NhipChay[]
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
