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
 *  Khối "Số hạng": dòng 1 là phát biểu, dòng 2 là ô `khi`, dòng 3 là HẬU QUẢ nếu có
 *  ("→ rút hết báo giá"). */
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
  /** Khoá màu NGỮ NGHĨA do Python suy ra: `start · hoi · gia · lot`. Không phải mã màu
   *  — giao diện tự ánh xạ sang biến CSS, nên đổi bảng màu không phải sửa Python. */
  mau?: string
}

export interface Problem {
  severity: 'error' | 'warning' | string
  message: string
  step?: string | null
  index?: number | null
  /** Sơ đồ nào — bảng Vấn đề gom lỗi của MỌI sơ đồ, kèm nhãn khi có nhiều hơn một. */
  tab: Tab
  // ⚠ `dat_ten` đã đi cùng bảng tham số (đợt 3).
}

/** Sơ đồ trong một chiến lược. Hiện chỉ MỘT.
 *
 *  ⚠ Bản cũ có hai: `entry` đi săn (một lượt mỗi nến) và `manage` chạy một lượt cho MỖI
 *  lệnh đang sống. Market maker không tách được như thế — mỗi sự kiện sổ lệnh, cả sơ đồ
 *  chạy lại và phát biểu TOÀN BỘ báo giá, nên "vào lệnh" và "quản lệnh" là cùng một
 *  lượt. Cơ chế nhiều sơ đồ thì giữ nguyên ở cả hai đầu (`core.TABS`, `PillTab`), sẵn
 *  cho §3 — lớp khớp lệnh. */
export type Tab = 'bao_gia'

export interface SoDo {
  steps: Step[]
  edges: ProcEdge[]
  cards: Card[]
}

/** ⚠ `ThamSo` đã đi ở đợt 3 cùng bảng tham số. Khoá `tham_so` GIỮ LẠI trong
 *  `ProcessDoc` và luôn rỗng: `schema` không đổi, nên file lưu ra vẫn cùng hình dạng
 *  với file đọc vào và sơ đồ cũ mở lên không bị coi là hỏng. */
export type ProcessDoc = {
  name: string
  symbol: string
  tham_so: never[]
} & Record<Tab, SoDo>

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
  // ⚠ `sua_che_do` · `trang_thai_lenh` · `ly_do_dong` đã đi cùng `so_lenh.py` (đợt 3):
  // market maker không có LỆNH RỜI mang trạng thái riêng để mà liệt kê.
  luu_tru: {
    goc: string
    muc: { ten: string; duong_dan: string; so_luong: number; danh_sach: string[] }[]
  }
}

export interface ToanHang {
  key: string
  /** Tên ĐẦY ĐỦ kèm lời giải — cho dropdown, nơi người dùng đang CHỌN. */
  nhan: string
  /** Tên TRẦN — cho chữ trên hộp. Thiếu thì rơi về `nhan` (xem `core.TOAN_HANG_NGAN`). */
  ngan?: string
  nhom: string
  /** `muc_gia` một MỨC · `khoang_cach` một BỀ RỘNG · `dem` số đếm · `dung_sai`. Quyết
   *  ô đơn vị sáng hay mờ, và quyết luôn phép so nào hợp lệ. */
  loai?: string
  /** Chỉ đại lượng `dem` mới có: `bid_kl` và `ton_kho` cùng đếm lot nhưng khác nghĩa. */
  don_vi?: string
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
  /** Hành động nào dùng được ở sơ đồ nào. Hiện mọi hành động dùng được ở sơ đồ duy
   *  nhất; cơ chế giữ nguyên cho ngày có sơ đồ thứ hai. */
  action_tabs: Record<string, Tab[]>
  /** Loại hành động đóng vai CỔNG rẽ nhánh. */
  branch_type: string
  huong: Record<string, string>

  /* ---- TỪ VỰNG. Hợp đồng: JS KHÔNG viết cứng danh sách nào. ----
   *
   * Khoá của thế giới nến đã đi ở đợt 3 (`timeframes` · `ma_methods` · `moc_entry` ·
   * `sua_che_do` · `don_vi_can_zone`…). Cái thay chúng ít hơn hẳn, vì từ vựng market
   * maker vốn nhỏ hơn — nhưng cùng một hợp đồng: thả một module vào `kho.MODULE` là
   * dropdown có ngay, không sờ vào TypeScript.
   * Bản cũ: `git show f1c90fb:webui/src/types.ts`. */
  toan_hang: ToanHang[]
  toan_hang_loai: Record<string, string>
  toan_hang_don_vi: Record<string, string>
  toan_hang_dung_sai: string[]
  phep_so: Record<string, string>
  /** Phép KHÔNG có vế phải, và cũng là phép duy nhất cho đại lượng đúng/sai. */
  phep_dung_sai: string[]
  don_vi: Record<string, string>
  don_vi_ngan: Record<string, string>
  don_vi_dem: Record<string, string>
  nhan_don_vi: Record<string, string>
  /** Loại đại lượng DUY NHẤT được chọn đơn vị (`khoang_cach`). */
  loai_co_don_vi: string
  /** Loại đại lượng → đơn vị CỐ ĐỊNH của ô so với nó. `null` = không có vế phải. */
  loai_don_vi: Record<string, string | null>

  /* ---- SỐ HẠNG: đích · phép · lượng · khi ---- */
  dich: Record<string, string>
  /** Đích → kiểu (`muc_gia` · `khoang_cach` · `lot`). Quyết `lượng` nhận cái gì. */
  dich_kieu: Record<string, string>
  /** Đích nào sửa CẢ HAI phía cùng lúc: `bien` → `[bien_mua, bien_ban]`. */
  dich_ca_hai: Record<string, string[]>
  phep_gan: Record<string, string>
  /** Kiểu đích → những phép nó nhận. Hộp thoại xổ đúng chừng ấy, không bày ra rồi
   *  mới báo lỗi. */
  phep_cho_dich: Record<string, string[]>

  // ⚠ `nguon` và `co_mt5` đã bỏ cùng nguồn nến MT5 (đợt 2).

  template_kinds: Record<string, string>
  accent_presets: Record<string, string>
  max_process_steps: number
}

/** Một symbol đã có dữ liệu tick trên đĩa. Mọi con số do Python đo, JS không tự tính. */
export interface BoNguon {
  symbol: string
  so_ngay: number
  tu_ngay: string
  den_ngay: string
  mb: number
  so_ban_ghi: { so: number; khop: number }
  so_lo_hong: number
  ms_lo_hong: number
  /** Trung vị độ trễ, đo trên MẪU của ngày mới nhất. `null` = chưa đo được. */
  tre_ms: number | null
}

/** Bộ ghi còn sống không. `song` suy từ TUỔI NHỊP TIM, không từ việc pid có tồn tại —
 *  pid bị cấp lại cho tiến trình khác là chuyện thường. */
export interface TrangThaiGhi {
  song: boolean
  symbols: string[]
  pid: number | null
  tuoi_nhip: number | null
  bat_dau: number | null
}

/** BỐN con số duy nhất của nguồn mà chỉnh vào là đổi thật. Mọi thứ khác đều ĐO ĐƯỢC
 *  nên app tự đo — hỏi một thứ đo được là mời người ta gõ số sai rồi tin nó. */
export interface CaiDatNguon {
  /** Symbol đang ghi. Lưu lại vì bộ ghi khởi động lại thì phải nhớ ghi gì. */
  symbols: string[]
  /** Rỗng = `du_lieu/tick`. Tuyệt đối thì dùng nguyên; tương đối tính từ `du_lieu/`. */
  thu_muc: string
  /** 0 = giữ tất. Mặc định 0 vì xoá là việc không lùi được. */
  giu_ngay: number
  /** Thấp quá → lỗ hổng GIẢ. Cao quá → ngồi mù mà tưởng đang chạy. */
  im_lang_giay: number
  /** "Mất điện thì mất bao nhiêu". */
  giay_xa: number
}

/** Kết quả một lượt ▶ Test. Mọi con số do Python tính, JS không tính lại con nào. */
export interface KetQuaTest {
  /** ⚠ KHAI ĐỦ, KHÔNG dùng `[k: string]: unknown`. Một chữ ký chỉ mục biến mọi
   *  trường chưa khai thành `unknown` — tức TypeScript im lặng cho qua rồi bắt chỗ
   *  DÙNG phải ép kiểu, và lúc đó không ai còn biết Python thật sự trả về gì.
   *  Khớp với `bo_chay.KetQua.bang()` + `khop_lenh.SoKhop.tom_tat()`. */
  bang: {
    so_su_kien: number; so_luot: number; so_lan_khop: number; giay_chay: number
    tu_ms: number; den_ms: number
    ton_kho: number; tien: number; gia_tri: number; phi_da_tra: number
    so_khop: number; kl_da_khop: number
    so_dat: number; so_huy: number; so_tu_choi: number; giay_mu_co_lenh: number
    /** MARKOUT — sau khi khớp `markout_ms` thì giá đi đâu. ÂM = bị chọn ngược.
     *  Con số quan trọng nhất của market making; xem `bo_chay.MARKOUT_MS`. */
    markout_ms: number; markout_tong: number; markout_kl: number
    /** Trung bình mỗi lot, quy ra tick — dạng đọc được bằng mắt. */
    markout_tick: number
    /** Chỗ kết quả KHÔNG chắc — rỗng nghĩa là không có gì phải dè dặt. */
    loi: string
    /** Bốn giả định của mô hình khớp. Kết quả không được rời khỏi giả định của nó. */
    gia_dinh: CaiDatKhop & { buoc_gia: number }
  }
  /** MỘT ĐIỂM MẪU = MỘT ẢNH CHỤP ĐỦ DÙNG, mười số:
   *
   *      t · giá_trị · tồn_kho · phí · số_lần_từ_chối     ← để VẼ
   *      bid · ask · bid_kl · ask_kl · có_sổ              ← để SOI
   *
   *  Năm số đầu cùng một trục thời gian nên biểu đồ chồng lên nhau được. Năm số sau là
   *  thứ làm `soi_luot` thành hàm THUẦN — bấm vào biểu đồ là ra ngay, không phát lại
   *  hai phút. Xem `bo_chay.KetQua.mau`. */
  mau: [number, number, number, number, number,
        number, number, number, number, boolean][]
  /** `[tu, den]` — quãng MÙ. Trong đó sàn vẫn khớp mà backtest không thấy. */
  lo_hong: [number, number][]
  khop: { t: number; ben: number; gia: number; kl: number; phi: number
          ton_kho: number }[]
  symbol: string
  tu_ngay: string
  den_ngay: string
}

/** SOI MỘT LƯỢT — sơ đồ đã làm gì tại một thời điểm, và vì sao. */
export interface KetQuaSoi {
  /** Trạng thái sơ đồ NHÌN THẤY lúc đó. `mid`/`spread` là `null` khi đang mất sổ. */
  nhin: {
    bid: number | null; ask: number | null; bid_kl: number; ask_kl: number
    co_so: boolean; ton_kho: number; mid: number | null; spread: number | null
  }
  /** Sáu ô của bản nháp báo giá. `null` = CHƯA ĐẶT, khác hẳn với đặt bằng 0. */
  nhap: {
    cong_bang: number | null; bien_mua: number; bien_ban: number
    lech: number; lot_mua: number; lot_ban: number
  }
  /** Giá ĐÃ LÀM TRÒN về tick — con số sẽ gửi đi, không phải con số trong đầu sơ đồ. */
  bao_gia: {
    mua_gia: number | null; mua_lot: number
    ban_gia: number | null; ban_lot: number
  }
  /** Theo ĐÚNG thứ tự đã đi, kể cả khối thử rồi bỏ. */
  khoi: {
    id: string; nhan: string; loai: 'cong' | 'so_hang'
    /** Cổng: mọi điều kiện có khớp không. Số hạng: luôn `true`. */
    qua: boolean
    /** Nhánh này bị BỎ khi lùi — số hạng của nó đã hoàn nguyên. */
    bo?: boolean
    /** Cổng: con số hai vế + PHÉP của TỪNG điều kiện, tính ĐỦ không ngắt sớm.
     *  Có `phep` để dựng lại đúng câu với số thật thay vào (`3 ≥ 5`). */
    dieu_kien?: { trai: number; phai: number | null; phep: string; dat: boolean }[]
    /** Số hạng: ô `khi` (nếu có), có áp dụng không, lượng, và trước/sau. */
    khi?: { trai: number; phai: number | null; phep: string; dat: boolean }
    ap_dung?: boolean
    luong?: number
    truoc?: (number | null)[]
    sau?: (number | null)[]
  }[]
  tick: number
}

/** BỐN núm vặn của mô hình khớp, và BA TRONG BỐN là thứ dữ liệu L1 không bao giờ trả
 *  lời được. Mặt kia của `CaiDatNguon`: ở đó luật là *đo được thì đừng hỏi*, ở đây là
 *  *không đo được thì đừng giấu*. Xem `cat_studio/khop_lenh.MoHinh`. */
export interface CaiDatKhop {
  /** bps. ÂM = rebate — sàn trả cho ta (chương trình Market Maker, không phải VIP). */
  phi_maker_bps: number
  /** Từ lúc quyết tới lúc lệnh NẰM ở sàn. Không đo được nếu chưa gửi lệnh thật. */
  tre_ra_ms: number
  /** 0 bi quan · 1 lạc quan. Núm quan trọng nhất của cả backtest. */
  phan_huy_truoc: number
  /** Treo sâu hơn đỉnh thì bao nhiêu phần của mức đó nằm trước ta. */
  phan_muc_sau: number
}

/** Một dòng của bảng `spread ÷ (2 × phí maker)`. Do Python đo, JS không tính lại. */
export interface DongThiTruong {
  san: string
  ma: string
  spread_bps: number
  phi_bps: number
  ti_le: number
  /** Spread rộng mấy tick. 1 = không chen vào giữa được, chỉ xếp hàng. */
  tick: number
  kl_trieu: number
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
