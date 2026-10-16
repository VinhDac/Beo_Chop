/** Vỏ bọc có kiểu quanh `window.pywebview.api`.
 *
 * Mọi lời gọi Python đi qua đây, không rải `window.pywebview` khắp components — để sau
 * này đổi cách vận chuyển (hoặc giả lập khi test) chỉ phải sửa một file.
 *
 * D-12: khối cũ đã xoá, nên ở đây chỉ còn những cửa KHÔNG dính gì tới khối — cửa sổ,
 * chỗ lưu file, và khoá QuantConnect.
 */
import type { KhoDanhMuc, KhoaQC, Reply } from './types'

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
  /** App lưu file ở đâu. */
  kho_danh_muc: () => goi<KhoDanhMuc>('kho_danh_muc'),

  // --- cửa sổ (thanh tiêu đề tự vẽ) ---
  vung_khong_keo: (vung: number[][], cao: number) => goi<null>('vung_khong_keo', vung, cao),
  keo_cua_so: (ht: number) => goi<boolean>('keo_cua_so', ht),
  cua_so_thu_nho: () => goi<null>('cua_so_thu_nho'),
  cua_so_phong_to: () => goi<boolean>('cua_so_phong_to'),
  cua_so_dang_phong_to: () => goi<boolean>('cua_so_dang_phong_to'),
  cua_so_dong: () => goi<null>('cua_so_dong'),
}

/** Khoá QuantConnect — của `api.ApiQC`. Mọi lỗi từ đây đã là một câu tiếng Việt. */
export const pyQC = {
  qc_khoa: () => goi<KhoaQC>('qc_khoa'),
  qc_luu_khoa: (userId: string, token: string) => goi<KhoaQC>('qc_luu_khoa', userId, token),
  qc_xoa_khoa: () => goi<KhoaQC>('qc_xoa_khoa'),
  qc_kiem_khoa: () => goi<boolean>('qc_kiem_khoa'),
}
