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

  // ⚠ `nguon` và `co_mt5` ĐÃ BỎ cùng nguồn nến MT5 (đợt 2).

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


/* ========================= Ổ CẮM TRỐNG =========================
 *
 * Từ đây trở xuống từng có ~330 dòng kiểu dữ liệu của CỬA SỔ Strategy Tester và cửa
 * sổ Live: `BoNen` · `TesterBoot` · `ThongKe` · `LenhVe` · `Khung` · `LoNhatKy` ·
 * `DoanPhat` · `TinKetNoi` · `DePhong` · `KetQuaHieuChuan`…
 *
 * Tất cả do `api.ApiTester` / `api.ApiLive` sinh ra, mà cả hai lớp đó đã bị gỡ trong
 * đợt 2 của lần dọn sang HFT market maker. Một `interface` không còn ai sinh ra dữ
 * liệu cho nó thì không phải hợp đồng — nó là chú thích giả trang thành hợp đồng, và
 * đó đúng là thứ khó bỏ nhất về sau vì trông vẫn như mã đang sống.
 *
 * Lấy lại: `git show f1c90fb:webui/src/types.ts`. Xem `tai_lieu/o_cam_trong.md`.
 */
