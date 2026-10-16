/** Vỏ bọc có kiểu quanh `window.pywebview.api`.
 *
 * Mọi lời gọi Python đi qua đây, không rải `window.pywebview` khắp components — để sau
 * này đổi cách vận chuyển (hoặc giả lập khi test) chỉ phải sửa một file.
 *
 * ⚠ MỘT BỀ MẶT DUY NHẤT. `api.py` chỉ còn một lớp `Api`, nên ở đây cũng chỉ một `py`.
 * Bản trước tách `pyQC` riêng và bản xem thử tự định tuyến mọi tên `qc_*` sang lớp kia
 * — nên hộp Khoá bấm ngon trong trình duyệt mà app thật thì báo "không có hàm" (D-12).
 */
import type {
  Edge, KetQuaSinh, KetQuaSoat, KhoDanhMuc, KhoaQC, Reply, Step, StepKind, Strategy,
  TuDienBatDau, TuDienHoi, TuDienLam,
} from './types'

type PyApi = Record<string, (...a: unknown[]) => Promise<unknown>>

declare global {
  interface Window {
    pywebview?: { api: PyApi }
    __su_kien?: (ten: string, d: unknown) => void
  }
}

/** Chờ cầu nối sẵn sàng.
 *
 * Cố ý KHÔNG dùng sự kiện 'pywebviewready': nếu nó bắn trước khi bundle chạy xong thì
 * listener gắn sau sẽ không bao giờ nhận được, và app treo ở màn hình trắng.
 *
 * ⚠ Và cố ý KHÔNG kiểm `window.pywebview?.api` cho xong: pywebview tạo sẵn `api: {}` —
 * một object RỖNG nhưng TRUTHY — ngay từ khung hình đầu tiên, rồi mới đổ hàm vào sau.
 * Phải chờ một HÀM CÓ THẬT xuất hiện.
 */
export function cho_cau_noi(ham = 'ping', timeout = 10000): Promise<void> {
  const t0 = Date.now()
  return new Promise((ok, hong) => {
    const thu = () => {
      if (typeof window.pywebview?.api?.[ham] === 'function') return ok()
      if (Date.now() - t0 > timeout) return hong(new Error('Không kết nối được tới Python'))
      setTimeout(thu, 40)
    }
    thu()
  })
}

async function goi<T>(ten: string, ...args: unknown[]): Promise<Reply<T>> {
  const api = window.pywebview?.api
  if (!api || typeof api[ten] !== 'function') {
    return { ok: false, error: `api.py không có hàm "${ten}"` }
  }
  try {
    return (await api[ten](...args)) as Reply<T>
  } catch (e) {
    return { ok: false, error: String(e) }
  }
}

export const py = {
  ping: () => goi<string>('ping'),
  set_title: (ten: string) => goi<null>('set_title', ten),
  kho_danh_muc: () => goi<KhoDanhMuc>('kho_danh_muc'),
  /** Từ điển XÁC NHẬN. Giao diện KHÔNG tự khai danh sách này — nó hỏi Python, vì hai
   *  nơi cùng giữ một bảng thì sớm muộn lệch nhau. */
  tu_dien_hoi: () => goi<TuDienHoi>('tu_dien_hoi'),
  /** Từ điển HÀNH ĐỘNG — tám loại việc và các ô của từng loại. Cùng lý do như trên. */
  tu_dien_lam: () => goi<TuDienLam>('tu_dien_lam'),
  /** Từ điển KHỐI BẮT ĐẦU — sáu ô thiết lập. Cùng lý do như hai cửa trên. */
  tu_dien_bat_dau: () => goi<TuDienBatDau>('tu_dien_bat_dau'),
  /** Sơ đồ -> thuật toán LEAN Python. `ghi` true thì ghi luôn ra file. */
  sinh_ma: (ten: string, steps: Step[], edges: Edge[], ghi = false) =>
    goi<KetQuaSinh>('sinh_ma', ten, steps, edges, ghi),

  // --- sơ đồ ---
  khoi_moi: (kind: StepKind, loai?: string) =>
    goi<{ step: Step; card: KetQuaSoat['the'][string] }>('khoi_moi', kind, loai),
  /** MỘT cửa soát duy nhất — gọi sau MỖI thay đổi, rồi vẽ lại cái nhận về. */
  soat: (steps: Step[], edges: Edge[]) => goi<KetQuaSoat>('soat', steps, edges),
  nhan_ban: (steps: Step[], edges: Edge[], giuHatNhan = false) =>
    goi<{ steps: Step[]; edges: Edge[]; map: Record<string, string>;
          the: KetQuaSoat['the'] }>('nhan_ban', steps, edges, giuHatNhan),

  // --- lưu / mở ---
  ds_strategy: () => goi<{ ten: string; tuLuu: boolean }[]>('ds_strategy'),
  doi_ten_strategy: (cu: string, moi: string) =>
    goi<{ ten: string }>('doi_ten_strategy', cu, moi),
  nhan_ban_strategy: (ten: string, tenMoi: string) =>
    goi<{ ten: string }>('nhan_ban_strategy', ten, tenMoi),
  luu_strategy: (ten: string, steps: Step[], edges: Edge[]) =>
    goi<{ ten: string; duong: string }>('luu_strategy', ten, steps, edges),
  mo_strategy: (ten: string) => goi<Strategy>('mo_strategy', ten),
  xoa_strategy: (ten: string) => goi<boolean>('xoa_strategy', ten),
  tu_luu_strategy: (ten: string, steps: Step[], edges: Edge[]) =>
    goi<{ ten: string; duong: string } | null>('tu_luu_strategy', ten, steps, edges),
  luu_ban_nhap: (ten: string, steps: Step[], edges: Edge[]) =>
    goi<string>('luu_ban_nhap', ten, steps, edges),
  doc_ban_nhap: () => goi<Strategy | null>('doc_ban_nhap'),
  xoa_ban_nhap: () => goi<boolean>('xoa_ban_nhap'),

  // --- khoá QuantConnect. Mọi lỗi từ đây đã là một câu tiếng Việt. ---
  qc_khoa: () => goi<KhoaQC>('qc_khoa'),
  qc_luu_khoa: (userId: string, token: string) => goi<KhoaQC>('qc_luu_khoa', userId, token),
  qc_xoa_khoa: () => goi<KhoaQC>('qc_xoa_khoa'),
  qc_kiem_khoa: () => goi<boolean>('qc_kiem_khoa'),
  qc_mo_web: (url: string) => goi<boolean>('qc_mo_web', url),

  // --- cửa sổ (thanh tiêu đề tự vẽ) ---
  vung_khong_keo: (vung: number[][], cao: number) => goi<null>('vung_khong_keo', vung, cao),
  keo_cua_so: (ht: number) => goi<boolean>('keo_cua_so', ht),
  cua_so_thu_nho: () => goi<null>('cua_so_thu_nho'),
  cua_so_phong_to: () => goi<boolean>('cua_so_phong_to'),
  cua_so_dang_phong_to: () => goi<boolean>('cua_so_dang_phong_to'),
  cua_so_dong: () => goi<null>('cua_so_dong'),
}

/** ⚠ Giữ tên cũ cho `HopKhoa` khỏi phải sửa — nhưng nó TRỎ VÀO CÙNG một bề mặt. */
export const pyQC = py
