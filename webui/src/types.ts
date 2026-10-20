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
  /** Tên icon, do `core.icon_cua` lấy từ TỪ ĐIỂN. Giao diện không tự tra: bảng tra
   *  thứ hai ở đây đã từng lệch khoá và làm mọi dòng mất icon, lặng thinh. */
  icon?: string
  /** Tên mấy NÚM đã ghim xuất hiện trong dòng này, để thẻ tô sáng chúng lên. Python
   *  nói ra; giao diện không tự đoán chữ nào là tên núm. Xếp dài-trước. */
  num?: string[]
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
/** HỒ SƠ CỖ MÁY LEAN — bốn trạm, phí sàn, dữ liệu, ô nhớ, mốc so sánh.
 *
 *  Nằm trong TÀI LIỆU chiến thuật, ngang hàng `steps` và `edges` — KHÔNG nằm trong
 *  khối Bắt đầu nữa (luật "một khối một việc", 18/10/2026). Hình dạng do Python
 *  quyết (`core.co_may_mac_dinh`), nên ở đây là một túi khoá-giá trị chứ không phải
 *  một interface gõ cứng: gõ cứng là giữ bản thứ hai của từ điển. */
export type CoMay = Record<string, unknown>

/** MỘT KHỐI MỜ của nối thông minh (`core.goi_y_ke`) — bước còn thêm được sau khối
 *  đang chọn. Ngữ pháp do Python nói; giao diện chỉ bày và bấm. */
export interface GoiYKe {
  /** Loại khối sẽ dựng. Rỗng với khối Bắt đầu (kind đã đủ nói). */
  loai: string
  kind: StepKind
  nhan: string
  pos: [number, number]
}

export interface KetQuaSoat {
  /** {id khối: "4A.2"}. Không có khoá = khối không chạy tới. */
  thu_tu: Record<string, string>
  entry: string | null
  the: Record<string, Card>
  /** Hồ sơ cỗ máy ĐÃ CHUẨN HOÁ — giao diện giữ lại để lưu và để mở hộp Cỗ máy.
   *  File cũ (ô cỗ máy còn trong khối Bắt đầu) được Python lôi lên ở đây. */
  co_may: CoMay
  /** Mấy chữ cho viên thuốc góc phải — chỉ kể thứ đã đổi khác mặc định. */
  tom_tat_co_may: string[]
  van_de: VanDe[]
  /** {id khối cuối vòng: [id khối đầu vòng, số vòng | null]} */
  vong: Record<string, [string, number | null]>
  edges: Edge[]
}

export interface Strategy {
  /** Cỗ máy LEAN của chiến thuật này — xem `CoMay`. */
  co_may?: CoMay
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
  /** HỆ SỐ nhân vào vế này: «0,25 × ROC(63)». Thiếu hay bằng 1 thì không nhân gì.
   *
   *  Nó nằm TRONG thành phần chứ không thành một phép `×` riêng, và đó là cả mẹo:
   *  chuỗi ghép nối TRÁI→PHẢI, không có thứ tự ưu tiên. Không có hệ số riêng thì
   *  `0,25 × a + 0,35 × b` viết thành bốn thành phần ra `((0,25×a)+0,35)×b` — sai,
   *  mà sai LẶNG vì vẫn ra một con số. */
  he_so?: number
  /** GHÉP — một CHUỖI thành phần, nối trái→phải: «0,25×ROC(63) + 0,35×ROC(126) +
   *  0,40×ROC(252) − 0,20×độ lệch chuẩn».
   *
   *  ⚠ Vẫn KHÔNG phải cây biểu thức, và chỗ ấy cố ý: một tổng có trọng số là một
   *  DANH SÁCH, nên hàng điều kiện vẫn là mấy dòng đọc được chứ không thành ô gõ
   *  công thức. Xem `hoi.ds_ghep` và `sinh_ma._ve_py`.
   *
   *  ⚠ FILE CŨ ghi `ghep` là MỘT object. Đọc phải nhận cả hai hình — mất nhánh ấy
   *  là mọi sơ đồ đã lưu thiếu mất nửa điều kiện mà vẫn vẽ ra bình thường. */
  ghep?: (VeDieuKien & { phep: string }) | (VeDieuKien & { phep: string })[]
  /** Ô nào của vế này đã GHIM làm tham số Optimize: tên ô -> tên núm. Nằm CẠNH con
   *  số chứ không thay nó, nên mọi chỗ đang đọc số vẫn thấy một con số thật.
   *  ⚠ `ghim_num`, KHÔNG phải `ghim`: `ghim` đã là khoá CŨ của canvas («ghim khối
   *  tại chỗ», một boolean) và nó nằm trong `KHOA_CANVAS`, nên dict của ta bị gỡ
   *  sạch lúc chuẩn hoá khối — ghim trên ô số của khối Làm không sống qua lưu/mở.
   *  Đã dính thật. */
  ghim_num?: Record<string, string>
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
  /** Bốn phép GHÉP hai đại lượng — đúng bộ `IndicatorExtensions` của LEAN. */
  phep_ghep: { ma: string; nhan: string }[]
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
    | 'ds_nho'
  /** Chỉ nhận số NGUYÊN (giờ, phút). Python khai, giao diện KHÔNG tự đoán. */
  nguyen?: boolean
  mac_dinh: unknown
  don_vi: string
  goi_y: string
  /** Chỉ ô CHỌN: [mã, nhãn]. */
  chon: [string, string][]
  bat_buoc: boolean
  /** Nhóm của ô, chỉ khối Bắt đầu dùng (xem `TuDienBatDau.nhom`). Để trống hay
   *  vắng thì ô rơi vào nhóm «Khác» và vẫn hiện ra — rơi về êm mà KHÔNG mất ô. */
  nhom?: string
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
  /** TÊN ô CẦM LÁI — ô CHỌN quyết nhánh `theo_loai` nào được dùng. Python nói ra,
   *  giao diện KHÔNG đoán: khối «Ghi nhớ» có hai ô chọn và ô cầm lái là ô THỨ HAI,
   *  nên lối đoán "ô chọn đầu tiên" bày nhánh sai và điền mặc định của nhánh sai —
   *  trong khi bộ sinh mã dùng nhánh đúng. Hai bên cùng "đúng" theo luật riêng. */
  o_lai: string
  /** Khối này có ô chọn ĐẠI LƯỢNG không (chọn trong CẢ kho, không riêng một họ). */
  co_dai_luong?: boolean
  /** Tên ô đại lượng ấy: «Giá trị vẽ», «Trọng số»… — từ điển nói, giao diện bày. */
  nhan_dai_luong?: string
  /** Ô ấy nhận được một CON SỐ thay cho đại lượng không. «Trọng số» thì có (mặc định
   *  là 1); «Giá trị vẽ» thì không — vẽ hằng số là một đường thẳng tắp. */
  dai_luong_so?: boolean
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
  /** `<tên lớp>/<mã lượt>` — khoá mở lại lượt này trong một cửa sổ riêng. */
  id?: string
  ma_luot?: string
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
  /** Người dùng đã bấm Dừng — lượt này KHÔNG phải hỏng, nên đừng báo như lỗi. */
  da_dung: boolean
  /** Chỉ có khi `xong`. */
  ket_qua?: KetQuaChay
}

/** Một lượt backtest đã lưu — thẻ tóm tắt trong Kho lượt chạy.
 *
 *  `so` là mấy con số lấy THẲNG từ `statistics` của LEAN, giữ nguyên tên tiếng Anh
 *  của nó: đổi tên ở đây là tự đẻ một bảng tra thứ hai phải trông coi. */
export interface TheLuotChay {
  /** `<tên lớp>/<mã lượt>` — cũng là khoá mở cửa sổ. */
  id: string
  ten_lop: string
  /** `20261017-131737`. */
  ma_luot: string
  luc: number
  so: Record<string, string>
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

/** Ô «Chạy trên mã nào» khi nó nói kiểu RỔ — một câu `set_universe_selection`.
 *
 *  HAI KIỂU CHO MỘT Ô, phân biệt bằng HÌNH DẠNG: `MaChay[]` là mấy mã gõ sẵn,
 *  `RoChay` là một rổ. Đúng lối vế phải của điều kiện (`{so}` hay `{ma_dl}`), và nhờ
 *  vậy file cũ (ô `ma` là một mảng) mở ra vẫn chạy, không phải di cư schema.
 *
 *  `ma_etf`/`lay` là ô CON của rổ ETF — Python khai chúng trong `RoDong.o_them`, chứ
 *  TypeScript không khai lại. Ô con nào rổ khác không có thì không có mặt. */
export interface RoChay {
  ro: string
  [o: string]: unknown
}

/** Một RỔ có thể chọn. `lop` là lớp `UniverseSelectionModel` có thật của LEAN. */
export interface RoDong {
  ma: string
  nhan: string
  lop: string
  o_them: OLam[]
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
  /** Ô chỉ hiện khi chọn nhịp này (giờ, phút, số phút sau khi mở cửa…).
   *
   *  ⚠ ĐÚNG `OLam[]`, y `RoDong.o_them`. Bản trước khai một hình dạng RIÊNG ở đây
   *  với hai khoá `nho_nhat`/`lon_nhat` mà từ điển Python KHÔNG HỀ CÓ — nên hộp
   *  thoại phải `as unknown as OLam` mỗi lần dùng, và `tsc` thì sạch vì chính dòng
   *  khai này nói thế. Khai sai mà build vẫn sạch là đúng họ lỗi dự án này săn. */
  o_them: OLam[]
  /** CÙNG nhịp ấy nhưng ô `ma` là một RỔ: lịch không neo vào mã nào được, vì rổ lúc
   *  `initialize` còn rỗng. Python khai câu thứ hai này ở `bat_dau.NHIP`. */
  chay_ro: string
}

/** Một bảng «chọn cái này thì hiện thêm mấy ô kia» — `nhip`, `phong_rui_ro`,
 *  `quy_tac_gio`, `phat_tin_hieu`, `phi`, `truot_gia` đều đúng hình này. Nhờ vậy
 *  hộp thoại chỉ cần biết «ô TÊN NÀY tra BẢNG NÀO», không cần biết trong `o_them`
 *  có mấy ô hay chúng là ô gõ hay ô chọn. */
export interface BangCoOThem { ma: string; nhan: string; o_them: OLam[] }

export interface TuDienBatDau {
  /** Ô của HỘP CỖ MÁY. Python chia (`bat_dau.NHOM_CO_MAY`) — giao diện không lọc
   *  lại, kẻo nó giữ một bản thứ hai của đường ranh. */
  o_co_may: OLam[]
  nhom_co_may: { ma: string; nhan: string; mo_ta: string }[]
  /** Mười lăm ô, cùng hình dạng với ô của khối Làm nên dùng chung được widget. */
  o: OLam[]
  /** NHÓM — hộp thoại xếp ô theo đây, thứ tự trong mảng là thứ tự bày ra.
   *
   *  Hộp Bắt đầu từng là MỘT danh sách phẳng, và hồi nó có sáu ô thì thế là đủ. Nay
   *  mười lăm ô chính cộng ô con của nhịp, quy tắc giờ, rổ, bốn trạm dây chuyền,
   *  model phí và trượt giá — hơn hai mươi ô một cột. Nhóm khai bên PYTHON chứ không
   *  gõ cứng ở đây: gõ danh sách nhóm trong .tsx là dựng bảng tra thứ hai, và nó sẽ
   *  tụt lại sau từ điển. */
  nhom: { ma: string; nhan: string; mo_ta: string }[]
  /** Nhóm cho ô nào CHƯA khai nhóm — bày cuối cùng, để một ô mới quên khai nhóm thì
   *  vẫn hiện ra chứ không biến mất lặng lẽ. */
  nhom_khac: string
  loai_tai_san: { ma: string; nhan: string; lean: string }[]
  /** Mã có sẵn trong bộ dữ liệu MIỄN PHÍ, để gợi ý — không phải để chặn. */
  co_san: Record<string, string[]>
  nhip: NhipChay[]
  /** Kiểu thứ hai của ô «Chạy trên mã nào» — xem `RoChay`. */
  ro: RoDong[]
  /** Model PHÒNG RỦI RO, mỗi cái mang ô NGƯỠNG của riêng nó — cùng hình dạng
   *  `nhip`/`ro`, nên hộp thoại bày chúng bằng đúng một đường. Nhãn ô khác nhau ở
   *  từng model (cắt khi lỗ / chốt khi lãi / tụt khỏi đỉnh), nên TypeScript KHÔNG
   *  dựng lại ô ấy: ngưỡng là cả cái phanh, nó phải nói đúng phanh nào. */
  phong_rui_ro: BangCoOThem[]
  /** MƯỜI HAI ô nhớ CỐ ĐỊNH của `hoi.TRI_NHO` — giao diện bày danh sách này cho
   *  người dùng chọn, rồi họ đặt TÊN cho ô nào muốn dùng. Không sinh mã mới: mã ô
   *  nhớ là của từ điển, chỉ cái tên là của người dùng. */
  o_nho: { ma: string; nhan: string; kieu: string; can_ma: boolean }[]
  /** Quy tắc GIỜ — bảng riêng, vì `schedule.on(date_rules.X, time_rules.Y)` nhận
   *  mọi X với mọi Y. Gộp hai thứ ấy vào một danh sách cặp là chỉ phủ được những
   *  cặp ai đó nghĩ ra để thêm. */
  quy_tac_gio: BangCoOThem[]
  /** Model Alpha — trạm TỰ phát tín hiệu, không cần khối vẽ nào. */
  phat_tin_hieu: BangCoOThem[]
  /** Phí và trượt giá GHI ĐÈ ô «Sàn». */
  phi: BangCoOThem[]
  truot_gia: BangCoOThem[]
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

/* ------------------------------- OPTIMIZE ---------------------------------- */

/** Một ràng buộc: chỉ tiêu + phép so + giá trị. Đúng khuôn `constraints` của LEAN. */
export interface RangBuoc {
  chi_tieu: string
  phep: string
  gia_tri: number
}

/** Cài đặt một mẻ Optimize. Mỗi khoá ánh xạ thẳng sang config optimizer. */
export interface CaiToiUu {
  cach_tim: string
  muc_tieu: string
  huong: string
  chia_doan: number
  cung_luc: number
  rang_buoc: RangBuoc[]
  /** tên núm -> khoảng quét. */
  tham_so: Record<string, { tu: number; den: number; buoc: number }>
}

/** Một núm sơ đồ đang ghim — `core.ds_tham_so` trả về. KHÔNG phải bảng riêng: nó
 *  đọc thẳng từ sơ đồ mỗi lần, nên sửa sơ đồ là nó đúng theo ngay. */
export interface NumSoDo {
  ten: string
  mac_dinh: number | string
  /** Núm này nằm ở những ô nào — thứ màn Optimize của QC không có. */
  o_tai: string[]
}

export interface TuDienToiUu {
  cach_tim: { ma: string; nhan: string }[]
  phep_so: { ma: string; nhan: string }[]
  huong: { ma: string; nhan: string }[]
  /** 27 chỉ tiêu LEAN ghi vào file kết quả — đếm từ file thật. */
  chi_tieu: string[]
  /** Sáu cột bảng xếp hạng bày sẵn. Bày cả 27 thì bảng rộng gấp ba màn hình. */
  chi_tieu_chinh: string[]
  /** Mặc định cho một mẻ mới — PYTHON khai, giao diện không tự nghĩ ra con số nào. */
  mac_dinh: CaiToiUu
  giay_moi_luot: number
}

/** Thẻ tóm tắt một mẻ — Kho đọc thẻ, không mở từng file kết quả: một mẻ có thể
 *  chứa hàng trăm lượt, mỗi lượt một file của LEAN nặng vài MB. */
export interface TheMeToiUu {
  id: string
  ten_lop?: string
  ma_luot?: string
  luc?: number
  so_luot?: number
  so_xong?: number
  cai?: CaiToiUu
}

/** Một mẻ đã chạy, cho cửa sổ Optimize. */
export interface LuotToiUu {
  ten_lop?: string
  ma_luot?: string
  so_luot?: number
  cai?: CaiToiUu
  ket_qua: {
    id: string
    tham_so: Record<string, string>
    chi_tieu: Record<string, string>
  }[]
}

/** Một HỒI của hành trình. */
export interface HoiHT {
  ma: string
  ten: string
  /** Câu một dòng của hồi — "Máy phải biết nhìn". */
  cau: string
}

/** Phần chấm của MỘT lượt. Do `cat_studio/luat_choi.cham` tính — giao diện không
 *  tính lại con số nào. */
export interface PhanCham {
  lai_pt: number | null
  boss_pt: number | null
  thang_boss: boolean
  so_dong: number
  /** Chạy trọn VÀ có ít nhất một lệnh đóng. */
  sach: boolean
}

/** Độ gọn: khối + núm. Ít hơn là khó quá khớp hơn. */
export interface DoGon {
  so_khoi: number
  so_num: number
  tong: number
}

/** Kết quả chấm một màn. `an` chỉ có sau khi NỘP — và nó KHÔNG bao giờ kèm ngày
 *  tháng của màn ẩn (xem `api.nop_man`). */
export interface ChamMan {
  khong_cham: boolean
  ok?: boolean
  loi?: string
  thay?: PhanCham
  an?: PhanCham | null
  gon?: DoGon
  sao: number
  sao_lan_nay?: number
  boss?: { ma: string; ten: string; mo_ta: string }
}

/** Một MÀN. Chữ đã do Python dịch sẵn, trang bản đồ không ghép câu nào. */
export interface ManHT {
  ma: string
  hoi: string
  /** Số thứ tự trong cả hành trình, 0-25. */
  so: number
  ten: string
  /** MỘT ý mới duy nhất của màn này. */
  day: string
  /** Màn này mở khoá những gì. */
  mo: string[]
  /** Màn gánh cả trò chơi — bản đồ vẽ khác đi. */
  dau: boolean
  khoa: boolean
  xong: boolean
  sao: number
  /** Màn đã có sân chơi thật (mã + khoảng ngày) chưa. False thì vẽ được mà chưa
   *  chạy chấm được — bản đồ phải NÓI RA. */
  co_san?: boolean
  symbol?: string
  von?: number
  /** Khoảng ngày ĐÃ THẤY. Khoảng ẩn KHÔNG bao giờ ra tới đây. */
  thay?: [string, string] | string[]
  /** Màn ẩn tả bằng lời, không bằng ngày — "12 tháng ngay sau màn đã thấy". */
  an_mo_ta?: string
  co_man_an?: boolean
  /** Màn 0: dựng chính con boss, nên không có gì để chấm. */
  khong_cham?: boolean
  /** Ngưỡng độ gọn để ăn huy chương. */
  gon?: number
  loi_dan?: string
  boss?: { ma: string; ten: string; mo_ta: string } | null
}

/** Cả hành trình. Giao diện KHÔNG khai lại một màn nào — xem `hanh_trinh.py`. */
export interface HanhTrinh {
  hoi: HoiHT[]
  man: ManHT[]
  /** Màn người chơi đang đứng. */
  dang_o: string
  /** Luật chấm sao đã có chưa. False thì bản đồ phải NÓI RA, đừng vẽ sao như thật. */
  co_luat_cham: boolean
}

/** Một món trong KHO. `lean` là CÂU LEAN THẬT của nó — lời hứa D-11: mỗi đại lượng
 *  khai đúng một thứ có thật của LEAN, không phải cái tên app tự nghĩ. */
export interface MucKho {
  ma: string
  nhan: string
  lean: string
  don_vi: string
  kieu: string
  /** Họ câu hỏi hỏi được món này — "Hỏi thị trường", "Hỏi vị thế"… */
  ho: string
  tham_so: string[]
}

export interface NhomKho {
  ten: string
  /** Nhóm này đã mở khoá chưa. Chưa mở thì vẫn kê tên, chỉ không dùng được. */
  mo: boolean
  muc: MucKho[]
}

/** Cả KHO: 164 đại lượng theo nhóm + 10 loại hành động. */
export interface KhoDaiLuong {
  nhom: NhomKho[]
  lam: { ma: string; nhan: string; mo_ta: string; mo: boolean }[]
  so_mo: number
  so_nhom: number
}
