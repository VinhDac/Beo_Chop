/** Hình dạng dữ liệu của CỖ MÁY 5 TRẠM đi qua cầu nối. Phải khớp `cat_studio/tram.py`
 *  (từ điển) và `cat_studio/may.py` (tài liệu, thẻ, soát lỗi).  (D-10, phần 5)
 *
 *  Luật y như sơ đồ cũ: phía JS KHÔNG tự dựng mấy shape này, cũng không tự ghép một mẩu
 *  chữ nào trên khối. Nó nhận từ Python, vẽ ra, rồi gửi lại nguyên vẹn.
 */
import type { ProcEdge, ThamSo } from '../types'

/** Năm trạm, đúng năm phần trong khung thuật toán của QuantConnect. */
export type TramKey = 'chon_ma' | 'tin_hieu' | 'chia_von' | 'rui_ro' | 'khop_lenh'

/** Một trạm tự giới thiệu: hỏi câu gì, chạy cho ai, ra cái gì, lịch nào chọn được. */
export interface TramMoTa {
  key: TramKey
  /** ① … ⑤ — ký hiệu, không phải số thứ tự để JS đếm. */
  so: string
  ten: string
  /** Tên mô hình tương ứng bên QuantConnect — để người chơi tra tài liệu của họ. */
  qc: string
  hoi: string
  cho_ai: string
  ra: string
  lich: string[]
  lich_mac_dinh: string
  khung_mac_dinh: string
}

/** Một Ô của khối Làm / của bảng Gom. `khi` = ô chỉ có nghĩa khi một ô khác mang giá
 *  trị đó (vd ô «%» chỉ hiện khi cách chia là «cố định X%»). */
export interface OKhai {
  key: string
  loai: 'so' | 'chon' | 'bat_tat' | 'toan_hang'
  nhan: string
  nguyen?: boolean
  min?: number
  max?: number
  mac_dinh?: unknown
  chon?: Record<string, string>
  khi?: Record<string, unknown>
  tuy_chon?: boolean
  don_vi?: string
}

/** Một đại lượng khối Hỏi đọc được. `tram === null` = đọc được ở MỌI trạm. */
export interface ToanHangKhai {
  key: string
  nhan: string
  nhom: string
  don_vi: string
  tham_so: string[]
  mac_dinh: Record<string, unknown>
  tram: TramKey[] | null
  mo_ta: string
  /** Chỉ báo nhiều đường (MACD · Stochastic): chọn đọc đường nào. */
  dong: Record<string, string> | null
}

export interface KhoiLamKhai {
  tram: TramKey
  nhan: string
  /** `quyet_dinh` chốt kết quả cho đối tượng đang xét — một đường chỉ được MỘT cái.
   *  `phu` đi kèm một quyết định. */
  vai: 'quyet_dinh' | 'phu'
  mo_ta: string
  truong: OKhai[]
}

/** Tham số của một đại lượng (chu kỳ, lùi, khung…). */
export interface ThamSoThKhai {
  loai: 'so' | 'chon'
  nhan: string
  chon?: Record<string, string>
  mac_dinh?: unknown
  nguyen?: boolean
  min?: number
  max?: number
}

/** Một mẫu dựng sẵn — CHỈ phần nhãn; sơ đồ do Python dựng khi lắp. */
export interface MauKhai {
  key: string
  ten: string
  qc: string
  mo_ta: string
}

/** `may_boot()` — cả từ điển, lấy một lần lúc mở trình vẽ. */
export interface BootMay {
  dang: string
  phien_ban: number
  tram: TramMoTa[]
  tram_keys: TramKey[]
  lich: Record<string, string>
  khung: string[]
  khung_phut: Record<string, number>
  /** `type` của khối Hỏi — giữ đúng khoá cổng cũ nên bộ đánh số dùng lại được. */
  hoi: string
  nhan_hoi: string
  phep_so: Record<string, string>
  don_vi: Record<string, string>
  tham_so_th: Record<string, ThamSoThKhai>
  toan_hang: ToanHangKhai[]
  toan_hang_cua_tram: Record<TramKey, string[]>
  khoi_lam: Record<string, KhoiLamKhai>
  khoi_lam_cua_tram: Record<TramKey, string[]>
  can_co: Record<string, string[]>
  gom: Record<string, OKhai[]>
  huong_tin_hieu: Record<string, string>
  cach_chia: Record<string, string>
  cach_tuong_doi: string[]
  mau: Record<TramKey, MauKhai[]>
  may_mau: Record<TramKey, string>
}

/** Một khối — hộp đen với JS, y như `Step` của sơ đồ cũ. */
export interface KhoiMay {
  id: string
  kind: 'start' | 'action'
  type?: string
  name?: string
  pos?: [number, number]
  ghim?: boolean
  [k: string]: unknown
}

/** Thẻ vẽ lên hộp — chữ do `may.the_khoi` sinh. */
export interface TheKhoi {
  id: string
  kind: 'start' | 'action'
  type?: string | null
  tram: TramKey
  title: string
  /** Nhãn đánh số của CHÍNH trạm này (`1 · 1A · 1A.1`), `null` = không có đường tới. */
  so: string | null
  lines: { text: string }[]
  mo_ta: string
  /** Khoá màu ngữ nghĩa: `start · hoi · lam`. Không phải mã màu. */
  mau: string
  ghim: boolean
  la_cong: boolean
  vai?: 'quyet_dinh' | 'phu' | null
}

export interface TramDoc {
  steps: KhoiMay[]
  edges: ProcEdge[]
  /** Bước cuối của trạm, chạy một lần cho cả trạm (chỉ ① và ③ có). */
  gom?: Record<string, unknown>
  /** Do `may_kem_the` gắn vào — không nằm trong file lưu. */
  cards?: TheKhoi[]
}

export interface MayDoc {
  dang: string
  phien_ban: number
  name: string
  tham_so: ThamSo[]
  tram: Record<TramKey, TramDoc>
}

export interface VanDeMay {
  severity: 'error' | 'warning' | string
  message: string
  /** Trạm nào — dải 5 trạm dùng để chấm đỏ, bảng Vấn đề dùng để gắn nhãn. */
  tram: TramKey | null
  step: string | null
  index: number | null
}

export interface LuongTram {
  order: Record<string, string>
  unreachable: string[]
  quay_lai: [string, string][]
  vong_ho: [string, string][]
  lech_nhanh: string[]
  so_loi: number
  so_canh_bao: number
}

/** Kết quả `may_soat` — soát CẢ NĂM trạm trong một lời gọi. */
export interface KetQuaSoatMay {
  ok: boolean
  value?: VanDeMay[]
  error?: string
  so_loi?: number
  so_canh_bao?: number
  tram?: Record<TramKey, LuongTram>
  van_tay?: string
}

/** Kết quả một cửa trả về khối: khối đã chuẩn hoá + thẻ + vấn đề của chính nó. */
export interface KhoiVaThe {
  step: KhoiMay
  card: TheKhoi
}
