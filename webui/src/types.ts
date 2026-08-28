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
  // ⚠ `nhip` đã đi cùng khung thời gian (đợt 3).
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
  // ⚠ `dat_ten` đã đi cùng bảng tham số (đợt 3).
}

/** Hai sơ đồ trong một chiến lược.
 *  `entry` đi săn (một lượt mỗi nến) · `manage` chạy một lượt cho MỖI lệnh đang sống. */
export type Tab = 'entry' | 'manage'

export interface SoDo {
  steps: Step[]
  edges: ProcEdge[]
  cards: Card[]
}

/** ⚠ `ThamSo` đã đi ở đợt 3 cùng bảng tham số. Khoá `tham_so` GIỮ LẠI trong
 *  `ProcessDoc` và luôn rỗng: `schema` không đổi, nên file lưu ra vẫn cùng hình dạng
 *  với file đọc vào và sơ đồ cũ mở lên không bị coi là hỏng. */
export interface ProcessDoc {
  name: string
  symbol: string
  tham_so: never[]
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
  // ⚠ `don_vi` · `sua_che_do` · `phep_so` · `trang_thai_lenh` · `ly_do_dong` đã đi
  // cùng từ vựng và `so_lenh.py` (đợt 3). Ba danh sách trên hiện luôn RỖNG.
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
  huong: Record<string, string>

  /* ⚠ HAI MƯƠI TƯ KHOÁ TỪ VỰNG ĐÃ ĐI ở đợt 3, khớp với `api.bootstrap`:
   *   nhom_lenh_nay · toan_hang_dung_sai · timeframes · nhip_mac_dinh · ma_methods
   *   toan_hang · phep_so · don_vi · don_vi_ngan · don_vi_cho · loai_lenh
   *   moc_entry · moc_can_zone · nhan_don_vi · don_vi_dem · toan_hang_don_vi
   *   toan_hang_loai · loai_co_don_vi · don_vi_chinh_no · toan_hang_can_zone
   *   don_vi_can_zone · sua_che_do · sua_can_gia · don_vi_o
   *
   * `Bootstrap` là hợp đồng "JS không viết cứng danh sách nào" — thêm một toán hạng ở
   * `kho/` là giao diện có ngay. Hợp đồng GIỮ NGUYÊN, chỉ là bên trái chưa có gì để
   * gửi. Bản cũ: `git show f1c90fb:webui/src/types.ts`. */

  // ⚠ `nguon` và `co_mt5` đã bỏ cùng nguồn nến MT5 (đợt 2).

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
  // ⚠ `sau_cong_zone` đã đi cùng cơ chế cổng zone (đợt 3).
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
