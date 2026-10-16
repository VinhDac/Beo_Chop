import type { MayDoc } from './may/mayTypes'

/** Hình dạng dữ liệu đi qua cầu nối cho CỬA SỔ MÀN CHƠI và mấy thứ dùng chung.
 *
 * Kiểu của chính cỗ máy 5 trạm nằm ở `may/mayTypes.ts` — đó mới là tài liệu app vẽ.
 *
 * Lưu ý: phía JS KHÔNG tự dựng mấy shape này từ con số 0 — nó nhận từ Python và gửi lại
 * nguyên vẹn. Mọi hiểu biết về định dạng file nằm ở Python.
 */

export interface ProcEdge {
  from: string
  to: string
  port: string
  from_side?: string
  to_side?: string
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

/** Danh mục "app đang có những gì" — do `api.kho_danh_muc` gom từ TỪ ĐIỂN 5 TRẠM. */
export interface KhoDanhMuc {
  tram: { so: string; ten: string; qc: string; hoi: string; cho_ai: string; ra: string
          so_khoi_lam: number; so_dai_luong: number; so_mau: number }[]
  khoi_lam: { key: string; nhan: string; tram: string; vai: string; mo_ta: string }[]
  toan_hang: { key: string; nhan: string; nhom: string; don_vi: string; tram: string
               mo_ta: string }[]
  may_san: { ten: string; mo_ta: string }[]
  luu_tru: { goc: string
             muc: { ten: string; duong_dan: string; so_luong: number
                    danh_sach: string[] }[] }
}

export interface Reply<T> {
  ok: boolean
  value?: T
  error?: string
  trace?: string
  [k: string]: unknown
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
  id: string; ten: string; ban_do: string; von: number
  /** Dạng tài liệu màn này dành cho: `"may5"` (cỗ máy 5 trạm) hay `"so_do"` (sơ đồ cũ). */
  dang: string
  /** Màn của cỗ máy chạy trên cả một RỔ mã; màn của sơ đồ cũ chỉ có một symbol — ở đó
   *  `ro` là chính symbol ấy, để giao diện chỉ phải biết MỘT khái niệm. */
  ro: string[]
  /** Loại thị trường của rổ (`forex` · `cfd` · `co_phieu` · `crypto`), màn cỗ máy mới có. */
  loai: string | null
  symbol: string | null
  thay: [string, string]; nhanh: [string, string]; an_mo_ta: string
  boss: BossQC; loi_dan: string; tien_do: TienDoMan; ve_nop: VeNop | null
}

/** Khoá đặt ở đâu. KHÔNG BAO GIỜ có token. */
export interface KhoaQC {
  co: boolean; nguon: 'bien_moi_truong' | 'file' | null; user_id: string | null
  duong: string; loi?: string
}

/** Chế độ Sáng tạo của CỖ MÁY 5 TRẠM: một RỔ mã, không phải một symbol — cỗ máy chọn mã
 *  ở trạm ①, nên đầu vào của nó là cả rổ. `loai` quyết lớp vỏ đăng ký mã kiểu gì trên
 *  QuantConnect (ngoại hối/CFD qua OANDA, cổ phiếu Mỹ, crypto Coinbase).  (D-10) */
export interface TuDoMayQC {
  ma: string[]; loai: string; tu: string; den: string; von: number
}

export interface KetQuaQC {
  ten: string; van_tay: string; symbol: string; tu: string; den: string; tf: string
  /** CỖ MÁY 5 TRẠM: cả rổ mã của lượt chạy, và loại thị trường. `symbol` rỗng ở đây. */
  dang?: string; ma?: string[]; loai_thi_truong?: string
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
  phien_ban: string; accent: string | null; doc: MayDoc | null
  man: ManQC[]; loai: Record<LoaiChay, string>; khoa: KhoaQC; do_gon: DoGon
  trang_thai: TrangThaiQC; co_ket_qua: boolean
  /** `"may5"` = đang chạy cỗ máy 5 trạm, `"so_do"` = sơ đồ Entry/Manage cũ. Do Python
   *  nói, không đoán từ hình dạng `doc`. */
  dang: string
  tu_do_may: TuDoMayQC
  /** D-11: đường chạy đang được dựng lại — câu Python đưa sang để cửa sổ nói thẳng ra.
   *  Rỗng nghĩa là chạy được bình thường. */
  chua_noi?: string
  /** Loại thị trường chọn được, và trần số mã một rổ — `qc_chay` khai. */
  loai_thi_truong: Record<string, string>
  tran_so_ma: number
}

export interface DongNkQC {
  i: number; lenh_id: string | null; co_viec: boolean; chu: string
  /** Trạm nào của cỗ máy đã chạy ra dòng này (`chon_ma` … `khop_lenh`). */
  tram?: string
}
export interface LoNhatKyQC { tong: number; tu: number; dong: DongNkQC[] }

export interface LenhQC {
  id: string; huong: string; loai: string; lot: number
  gia_dat: number; gia_khop: number | null; gia_dong: number | null
  sl: number | null; tp: number | null; R: number
  trang_thai: string; ly_do_dong: string | null
  t_dat: number | null; t_khop: number | null; t_dong: number | null
}
