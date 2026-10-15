/** Hình dạng dữ liệu đi qua cầu nối. Phải khớp với `api.py` / `core.py`.
 *
 * Lưu ý: phía JS KHÔNG tự dựng mấy shape này từ con số 0 — nó nhận từ Python và gửi
 * lại nguyên vẹn. Mọi hiểu biết về định dạng file nằm ở `core.py`.
 */

/** Hai loại khối, không hơn. `start` là điểm neo — cả sơ đồ chạy lại từ đó mỗi nến. */
export type StepKind = 'start' | 'action'

/** Một khối — coi như hộp đen. JS chỉ đụng tới `id`, `kind`, `name`, `pos`, `ghim`. */
export interface Step {
  id: string
  kind: StepKind
  name?: string
  pos?: [number, number]
  /** Ghim số: khối này là điểm quay lại hợp lệ, nhãn của nó không đổi khi có
   *  đường nối ngược về. Bật/tắt bằng chuột phải. */
  ghim?: boolean
  /** CHỈ khối Bắt đầu: nhịp chạy của sơ đồ ("M5" / "M1" …). Trước đây là
   *  `doc.timeframe` + một dropdown trên ribbon; giờ thuộc về chính điểm neo. */
  nhip?: string
  [k: string]: unknown
}

export interface ProcEdge {
  from: string
  to: string
  port: string
  from_side?: string
  to_side?: string
}

/** Một dòng chữ trên hộp — do `api.describe()` sinh, không phải JS tự ghép.
 *  Khối "Kiểm tra điều kiện": mỗi dòng là MỘT điều kiện (nối nhau bằng VÀ).
 *  Khối "Vào lệnh" / "Sửa lệnh": mỗi dòng là MỘT TRƯỜNG (lot · đệm · SL · TP). */
export interface CardLine {
  text: string
  /** Loại hành động — giao diện dùng để CHỌN ICON. Python không gắn emoji vào text. */
  type?: string | null
}

export interface Card {
  id: string
  kind: StepKind
  title: string
  badges: string[]
  lines: CardLine[]
  /** Câu đầy đủ, dùng làm tooltip. `lines` là bản ngắn để vẽ lên hộp. */
  mo_ta: string
  /** CHỈ khối Bắt đầu — nhịp chạy, để menu chuột phải tick đúng mục. */
  nhip?: string
  ghim: boolean
  la_cong: boolean
  /** Khoá màu NGỮ NGHĨA do Python suy ra: `start · hoi · mua · ban · sua`. Không phải mã
   *  màu — giao diện tự ánh xạ sang biến CSS, nên đổi bảng màu không phải sửa Python. */
  mau?: string
}

export interface Problem {
  severity: 'error' | 'warning' | string
  message: string
  step?: string | null
  index?: number | null
  /** Sơ đồ nào — bảng Vấn đề hiện lỗi của CẢ HAI tab, kèm nhãn. */
  tab: Tab
  /** Chỉ có ở cảnh báo "số gõ tay hai chỗ" — đủ dữ liệu để đặt tên bằng MỘT nút.
   *  `cho` là đường đi vào từng ô số, để giao diện khỏi phải quét lại sơ đồ (quét hai
   *  lần bằng hai đoạn mã là hai luật, và chúng sẽ lệch nhau). */
  dat_ten?: {
    goi_y: string; gia_tri: number; don_vi: string; nhan: string
    cho: { tab: Tab; step: string; duong: (string | number)[] }[]
  }
}

/** Hai sơ đồ trong một chiến lược.
 *  `entry` đi săn (một lượt mỗi nến) · `manage` chạy một lượt cho MỖI lệnh đang sống. */
export type Tab = 'entry' | 'manage'

export interface SoDo {
  steps: Step[]
  edges: ProcEdge[]
  cards: Card[]
}

/** Một núm vặn của chiến lược. Hằng số CÓ TÊN, đơn vị bất biến (bps · nến · ×ATR ·
 *  ×R) — không pip, không đô. Đây là hợp đồng chuẩn hoá của D_02. */
export interface ThamSo {
  ten: string
  nhan: string
  gia_tri: number
  don_vi: string
  ghi_chu: string
}

export interface ProcessDoc {
  name: string
  symbol: string
  tham_so: ThamSo[]
  entry: SoDo
  manage: SoDo
}

/** Danh mục kho — mọi thứ app tính được, do `kho/` tự gom từ các module con. */
export interface KhoDanhMuc {
  module: {
    ma_so: string; ten: string; mo_ta: string; la_engine: boolean; nguon: string
    so_chi_bao: number; so_toan_hang: number; so_bang: number
  }[]
  chi_bao: { key: string; nhan: string; tham_so: string[]; cong_thuc?: string
             mo_ta?: string; nguon: string }[]
  toan_hang: ToanHang[]
  bang_trang_thai: {
    key: string; nhan: string; mo_ta: string; nguon: string
    truong: { ten: string; kieu: string; vd: string }[]
    luat: string[]
  }[]
  hanh_dong: { key: string; nhan: string; tabs: Tab[] }[]
  don_vi: Record<string, string>
  sua_che_do: Record<string, string>
  phep_so: Record<string, string>
  trang_thai_lenh: Record<string, string>
  ly_do_dong: Record<string, string>
  luu_tru: {
    goc: string
    muc: { ten: string; duong_dan: string; so_luong: number; danh_sach: string[] }[]
  }
}

export interface ToanHang {
  key: string
  nhan: string
  nhom: string
  tham_so: string[]
  /** Module nào cung cấp: `nen_tang` · `chi_bao` · `d02` … */
  nguon?: string
  mo_ta?: string
  dung_sai?: boolean
  /** null/thiếu = dùng được ở cả hai sơ đồ. */
  tabs?: Tab[] | null
}

export interface Bootstrap {
  phien_ban: string
  settings: Record<string, unknown>
  app_dir: string

  kinds: StepKind[]
  kind_labels: Record<string, string>

  tabs: Tab[]
  tab_labels: Record<string, string>
  action_types: string[]
  action_labels: Record<string, string>
  /** Hành động nào dùng được ở tab nào. Entry chỉ TẠO, Manage chỉ SỬA. */
  action_tabs: Record<string, Tab[]>
  /** Loại hành động đóng vai CỔNG rẽ nhánh. */
  branch_type: string
  /** Tên nhóm toán hạng chỉ có nghĩa ở Manage. */
  nhom_lenh_nay: string
  /** Toán hạng vốn đã đúng/sai — hộp thoại ẩn ô vế phải. */
  toan_hang_dung_sai: string[]

  timeframes: string[]
  /** Nhịp mặc định mỗi sơ đồ: Entry M5 (quyết định) · Manage M1 (phản ứng). */
  nhip_mac_dinh: Record<Tab, string>
  ma_methods: Record<string, string>
  toan_hang: ToanHang[]
  /** Tám phép: `< ≤ > ≥ = ≠` + `là ĐÚNG` / `là SAI`. Hai phép cuối dùng CHO VÀ CHỈ CHO
   *  toán hạng đúng/sai, và chúng KHÔNG có vế phải. */
  phep_so: Record<string, string>
  /** ĐƠN VỊ — MỘT bảng cho cả app: điều kiện, SL/TP/đệm, sửa lệnh.
   *  Trước đây là hai bảng (`CACH_TINH` + `DON_VI_SS`) trùng nhau ba cặp. */
  don_vi: Record<string, string>
  don_vi_ngan: Record<string, string>
  /** Đơn vị nào dùng được ở đâu: `dieu_kien` · `dem` · `sl` · `tp` · `sua`. */
  don_vi_cho: Record<string, string[]>
  huong: Record<string, string>
  loai_lenh: Record<string, string>
  /** Mốc neo của khối Vào lệnh — `zone_HH` · `zone_LL` · `gia_hien_tai`. */
  moc_entry: Record<string, string>
  /** Mốc nào chỉ có nghĩa khi phía trên có cổng zone. */
  moc_can_zone: string[]
  /** MỌI đơn vị → nhãn, kể cả đơn vị ĐẾM. Bảng tham số khai `don_vi` bằng khoá ở đây. */
  nhan_don_vi: Record<string, string>
  /** Đơn vị ĐẾM (`nen` · `lenh` · `lot`) — không quy đổi gì, chỉ nói con số đo cái gì. */
  don_vi_dem: Record<string, string>
  /** Toán hạng → đơn vị CỐ ĐỊNH của ô so với nó. `null` = đúng/sai, không có vế phải. */
  toan_hang_don_vi: Record<string, string | null>
  /** Toán hạng → loại đại lượng. Quyết định ô đơn vị sống hay mờ. */
  toan_hang_loai: Record<string, string>
  /** Loại DUY NHẤT được chọn đơn vị: `khoang_cach`. */
  loai_co_don_vi: string
  /** Toán hạng → đơn vị chính là NÓ. Chọn cái đó thì kết quả luôn = 1, nên không bày. */
  don_vi_chinh_no: Record<string, string>
  /** Toán hạng chỉ có nghĩa khi đã có zone. */
  toan_hang_can_zone: string[]
  /** Đơn vị chỉ có nghĩa khi đã có zone (`× ATR zone` · `mép zone đối diện`). */
  don_vi_can_zone: string[]
  /** Bốn chế độ: dời SL · dời TP · SL về hoà vốn · KẾT THÚC LỆNH NÀY (gộp đóng+huỷ). */
  sua_che_do: Record<string, string>
  sua_can_gia: string[]

  /** Đơn vị của những ô CỐ ĐỊNH ngoài điều kiện: `chu_ky` → nến, `lot` → lot. */
  don_vi_o: Record<string, string>
  template_kinds: Record<string, string>
  accent_presets: Record<string, string>
  max_process_steps: number
}

export interface Reply<T> {
  ok: boolean
  value?: T
  error?: string
  trace?: string
  [k: string]: unknown
}

export interface LuongSoDo {
  order: Record<string, string>
  unreachable: string[]
  /** Cạnh quay lại HỢP LỆ (tới khối đã ghim) — vẽ nét đứt. */
  quay_lai: [string, string][]
  /** Vòng lặp CHƯA ghim. */
  vong_ho: [string, string][]
  lech_nhanh: string[]
  /** Khối nào dòng chảy đã đi QUA cổng zone trước khi tới — chỉ ở đó zone mới tồn tại,
   *  nên chỉ ở đó mới bày ra toán hạng zone và đơn vị `× ATR zone`. */
  sau_cong_zone: string[]
}

/** Kết quả `api.validate` — soát CẢ HAI sơ đồ trong một lời gọi. */
export interface KetQuaSoat extends Reply<Problem[]> {
  so_loi?: number
  so_canh_bao?: number
  luong?: Record<Tab, LuongSoDo>
}

/* ======================= KẾT QUẢ MỘT LƯỢT CHẠY =======================
 * Do Python dựng (`qc_chay.KetQuaQC` · `nhat_ky`). Giao diện KHÔNG tự tính con số nào —
 * kể cả một phép cộng. Chữ trong nhật ký cũng do Python dựng (core.md §12.8).
 */

export interface ThongKe {
  so_lenh: number; so_dong: number; so_huy: number
  thang: number; thua: number; ty_le_thang: number
  lai_tien: number; tong_R: number; von_cuoi: number; drawdown_pt: number
  von_dau: number; lai_pt: number
  drawdown_tien: number
  /** Thời điểm chạm đáy sụt giảm. `null` = chưa có lệnh nào đóng. */
  drawdown_luc: number | null
  R_moi_lenh: number; R_khi_thang: number; R_khi_thua: number
  /** `null` = CHƯA CÓ lệnh lỗ nào, không phải 0. Hai chuyện khác hẳn nhau. */
  he_so_lai: number | null
  chuoi_thua: number
  so_zone: number
  /** Số nến M1 có CẢ SL lẫn TP trong biên độ. 0 = kết quả không phụ thuộc giả định
   *  đường đi 4 điểm (core.md §12.13d). */
  nen_mo_ho: number
  so_luot: number
}

/** Tab Thống kê — tổng kết CẢ LƯỢT CHẠY, cố định, không theo con trỏ. */
export interface ThongKeChay {
  tk: ThongKe
  /** `[thời_điểm, vốn, sụt_giảm_%]` — mỗi nến trục có lệnh đóng một điểm. Sụt giảm là
   *  số ÂM để vẽ úp xuống. */
  duong_von: [number, number, number][]
  /** Khoảng THẬT SỰ có nến. */
  t_dau: number; t_cuoi: number
  /** Khoảng ĐÃ YÊU CẦU cho lượt chạy — lệch với trên là chuyện thường. */
  yc_tu: string; yc_den: string
  symbol: string
  nhip: { entry: string; manage: string }
}

/** SOI MỘT LƯỢT trên sơ đồ — do `api.ApiQC.qc_soi_luot` bắn sang cửa sổ vẽ.
 *
 *  `cong` mang MỌI cổng lượt đó đã thử, kèm vết TỪNG điều kiện theo đúng thứ tự các
 *  dòng trong hộp — nhờ vậy tô được tới đúng dòng điều kiện hỏng, không chỉ tô cả hộp. */
export interface SoiLuot {
  tab: Tab
  duong: string[]
  cong: { khoi: string; khop: boolean; ve: { trai: number | null; phai: number | null; dat: boolean }[] }[]
  ket: string
  lenh_id: string | null
  nhan: Record<string, string>
  chu: string
}

/** Thứ bơm vào từng node lúc vẽ. `null` = không soi gì. */
export interface SoiKhoi {
  daChay: boolean
  truot: boolean
  /** `dat` của từng điều kiện, cùng thứ tự với `card.lines`. Rỗng = không tô dòng nào
   *  (khối không phải cổng, hoặc số điều kiện đã đổi từ lúc chạy). */
  dieuKien: boolean[]
}

/* ======================= MÀN CHƠI — chạy trên QuantConnect ========================
 * Hình dạng dữ liệu của `api.ApiQC` (cat_studio/api.py) · luật ở `cat_studio/game.py`.
 * Không có nến: kết quả QC không mang chuỗi giá về máy — mỗi lượt tự mang giờ `t`. */

export type LoaiChay = 'nhanh' | 'day_du' | 'nop' | 'tu_do'

export interface BossQC { id: string; ten: string; mo_ta: string }

/** Phần chấm của một lần chạy — `game.cham`. */
export interface ChamQC {
  lai_pt: number
  /** `null` = khoảng ngày không có giá → không ai thắng ai. */
  mua_giu_pt: number | null
  thang_boss: boolean
  so_dong: number
  /** Chạy trọn và có ít nhất một lệnh đóng. */
  sach: boolean
}

export interface DoGon { so_khoi: number; so_tham_so: number; tong: number }

export interface LanNop {
  t: string; ten: string; van_tay: string; sao: number; do_gon: DoGon
  thay: ChamQC; an: ChamQC
}

export interface TienDoMan {
  so_lan_nop: number; sao: number; tot_nhat: LanNop | null; lan_cuoi: LanNop | null
}

/** Lượt ▶ đầy đủ của ĐÚNG cỗ máy đang mở — có nó mới được Nộp. */
export interface VeNop extends ChamQC { t: string; ten: string; duong: string }

/** Một màn (KHÔNG có ngày của màn ẩn — app giữ, D-06). */
export interface ManQC {
  id: string; ten: string; ban_do: string; symbol: string; von: number
  thay: [string, string]; nhanh: [string, string]; an_mo_ta: string
  boss: BossQC; loi_dan: string; tien_do: TienDoMan; ve_nop: VeNop | null
}

/** Khoá đặt ở đâu. KHÔNG BAO GIỜ có token. */
export interface KhoaQC {
  co: boolean; nguon: 'bien_moi_truong' | 'file' | null; user_id: string | null
  duong: string; loi?: string
}

export interface TuDoQC { symbol: string; tu: string; den: string; von: number }

export interface KetQuaQC {
  ten: string; van_tay: string; symbol: string; tu: string; den: string; tf: string
  thong_ke: ThongKe
  duong_von: [number, number, number][]
  gia_dau: number | null; gia_cuoi: number | null; mua_giu_pt: number | null
  dem: Record<string, number>; giay_chay: number | null; so_luot: number | null
  duong_nhat_ky: string; do_gon: DoGon
  t_dau: number | null; t_cuoi: number | null
  nhip: { entry: string; manage: string }
  // ---- chỉ có khi vừa chạy xong (mở lại từ lịch sử thì một phần) ----
  loai?: LoaiChay; man?: string | null; an?: boolean; cham?: ChamQC; url?: string
  giay_tong?: number; sao?: number | null; lan_nop?: number | null; thay?: VeNop | null
}

export interface TrangThaiQC {
  dang_chay: boolean; loai?: LoaiChay; man?: string | null
  /** Bước đang làm, nói bằng lời. */
  chu?: string
  /** Tiến độ TRONG bước (chỉ backtest đo được). */
  ti_le?: number | null
  /** Tiến độ cả lượt, 0…1. */
  ti_le_chung?: number
  giay?: number
  xong: KetQuaQC | null
  loi: string | null
}

export interface MucLichSuQC {
  t: string; loai: LoaiChay; man: string | null; ten: string; van_tay: string
  /** Lượt nộp (`an`): KHÔNG có ngày, KHÔNG có link — app giữ màn ẩn (D-06). */
  symbol: string; tu: string | null; den: string | null; an: boolean; sao: number | null
  lai_pt: number; mua_giu_pt: number | null; so_lenh: number; url: string | null; duong: string
}

export interface BootQC {
  phien_ban: string; accent: string | null; doc: ProcessDoc | null
  man: ManQC[]; loai: Record<LoaiChay, string>; khoa: KhoaQC; do_gon: DoGon
  tu_do: TuDoQC; trang_thai: TrangThaiQC; co_ket_qua: boolean
}

export interface DongNkQC {
  i: number; nen: number; tab: Tab; lenh_id: string | null; co_viec: boolean; chu: string
}
export interface LoNhatKyQC { tong: number; tu: number; dong: DongNkQC[] }

export interface LenhQC {
  id: string; huong: string; loai: string; lot: number
  gia_dat: number; gia_khop: number | null; gia_dong: number | null
  sl: number | null; tp: number | null; R: number
  trang_thai: string; ly_do_dong: string | null
  t_dat: number | null; t_khop: number | null; t_dong: number | null
}
