/** Vỏ bọc có kiểu quanh `window.pywebview.api`.
 *
 * Mọi lời gọi Python đi qua đây, không rải `window.pywebview` khắp components — để
 * sau này đổi cách vận chuyển (hoặc giả lập khi test) chỉ phải sửa một file.
 */
import type {
  KhoDanhMuc, Reply, ThamSo,
  BootQC, KetQuaQC, KhoaQC, LenhQC, LoaiChay, LoNhatKyQC, ManQC, MucLichSuQC,
  TrangThaiQC, TuDoMayQC,
} from './types'
import type {
  BootMay, KetQuaSoatMay, KhoiVaThe, MayDoc, TramKey,
} from './may/mayTypes'

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
 * ⚠ Và cố ý KHÔNG kiểm `window.pywebview?.api` cho xong: pywebview tạo sẵn
 * `api: {}` — một object RỖNG nhưng TRUTHY — ngay từ khung hình đầu tiên, rồi mới đổ
 * hàm vào sau bằng `_createApi(funcList)`. Kiểm trống rỗng như vậy là qua ngay lập
 * tức, và lời gọi đầu tiên chết với "api.py không có hàm bootstrap" — trông y như lỗi
 * phía Python trong khi Python hoàn toàn ổn.
 * Phải chờ một HÀM CÓ THẬT xuất hiện.
 */
export function cho_cau_noi(ham = 'bootstrap', timeout = 10000): Promise<void> {
  const t0 = Date.now()
  return new Promise((ok, hong) => {
    const thu = () => {
      // Chờ ĐÚNG hàm mà trang này sắp gọi: cửa sổ Màn chơi có `ApiQC` riêng, KHÔNG có
      // `bootstrap`. Chờ cứng `bootstrap` ở đó là treo 10 giây rồi báo mất kết nối.
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
  /** ◆ Màn chơi — mở cửa sổ chạy cỗ máy trên QuantConnect. Cỗ máy còn lỗi thì từ chối
   *  kèm `loi` (danh sách lỗi y bảng Vấn đề). */
  mo_qc: (doc: MayDoc) => goi<{ da_mo: boolean }>('mo_qc', doc),
  set_title: (ten: string) => goi<null>('set_title', ten),

  /** Hộp thoại "Kho": app đang có những gì — từ điển 5 trạm, mẫu, chỗ lưu file. */
  kho_danh_muc: () => goi<KhoDanhMuc>('kho_danh_muc'),

  // --- cửa sổ (thanh tiêu đề tự vẽ) ---
  vung_khong_keo: (vung: number[][], cao: number) => goi<null>('vung_khong_keo', vung, cao),
  keo_cua_so: (ht: number) => goi<boolean>('keo_cua_so', ht),
  cua_so_thu_nho: () => goi<null>('cua_so_thu_nho'),
  cua_so_phong_to: () => goi<boolean>('cua_so_phong_to'),
  cua_so_dang_phong_to: () => goi<boolean>('cua_so_dang_phong_to'),
  cua_so_dong: () => goi<null>('cua_so_dong'),
}

/** Bề mặt của cửa sổ MÀN CHƠI (`api.ApiQC`). Mọi lỗi từ đây đã là một câu tiếng Việt.
 *
 * Tách hẳn khỏi `py`: cửa sổ đó chạy `ApiQC` bên Python, một lớp cố ý HẸP — không lưu
 * chiến lược, không mở hộp thoại file, không đổi cài đặt. Gọi nhầm `py.*` ở đó sẽ trả
 * "api.py không có hàm …" chứ không âm thầm đụng vào cửa sổ chính.
 *
 * Nhóm `cua_so_*` trùng TÊN với `py` nhưng là hàm KHÁC — mỗi cửa sổ một thể hiện, nên bấm
 * ✕ ở Màn chơi chỉ đóng Màn chơi. Nhờ vậy `TitleBar` dùng lại được nguyên vẹn. */
export const pyQC = {
  qc_boot: () => goi<BootQC>('qc_boot'),
  qc_khoa: () => goi<KhoaQC>('qc_khoa'),
  qc_luu_khoa: (userId: string, token: string) => goi<KhoaQC>('qc_luu_khoa', userId, token),
  qc_xoa_khoa: () => goi<KhoaQC>('qc_xoa_khoa'),
  qc_kiem_khoa: () => goi<boolean>('qc_kiem_khoa'),
  /** Chạy NỀN, trả ngay — rồi hỏi `qc_trang_thai` tới khi `dang_chay` tắt. */
  /** `tuDo` là RỔ mã của chế độ Sáng tạo; Chiến dịch thì lấy rổ của màn, nên `null`. */
  qc_chay: (loai: LoaiChay, man: string | null, tuDo: TuDoMayQC | null) =>
    goi<boolean>('qc_chay', loai, man, tuDo),
  qc_trang_thai: () => goi<TrangThaiQC>('qc_trang_thai'),
  qc_ket_qua: () => goi<KetQuaQC | null>('qc_ket_qua'),
  qc_nhat_ky: (tu: number, so: number, chiViec: boolean) =>
    goi<LoNhatKyQC>('qc_nhat_ky', tu, so, chiViec),
  qc_lenh: () => goi<LenhQC[]>('qc_lenh'),
  qc_soi_luot: (i: number) => goi<{ da_ban: boolean }>('qc_soi_luot', i),
  qc_man: () => goi<ManQC[]>('qc_man'),
  qc_lich_su: () => goi<MucLichSuQC[]>('qc_lich_su'),
  qc_mo_lai: (duong: string) => goi<KetQuaQC>('qc_mo_lai', duong),
  qc_mo_web: (url: string) => goi<boolean>('qc_mo_web', url),
}

/** Bề mặt của TRÌNH VẼ 5 TRẠM (các cửa `may_*` của `api.Api`).  (D-10, phần 5)
 *
 * Tách hẳn khỏi `py` dù cùng một lớp Python: hai dạng tài liệu khác hẳn nhau, và gộp
 * chúng vào một vỏ là đường ngắn nhất tới chỗ gọi `validate` (sơ đồ cũ) cho một cỗ máy
 * rồi nhận về "không có vấn đề nào" trong khi cỗ máy đầy lỗi.
 *
 * Mọi hàm ở đây trả về thứ Python đã chuẩn hoá — kể cả chữ trên khối. Giao diện không
 * tự ghép một mẩu nào.
 */
export const pyMay = {
  /** Từ điển 5 trạm — gọi MỘT lần lúc mở trình vẽ. */
  may_boot: () => goi<BootMay>('may_boot'),

  // --- tài liệu ---
  may_moi: (ten?: string) => goi<MayDoc>('may_moi', ten ?? null),
  /** Cỗ máy mẫu đủ năm trạm, sạch lỗi, chạy được ngay. */
  may_mo_mau: (chon?: Partial<Record<TramKey, string>>, ma?: string[]) =>
    goi<MayDoc>('may_mo_mau', chon ?? null, ma ?? null),
  /** Một cỗ máy DỰNG SẴN của chương 1 (`may_boot().may_san`). */
  may_mo_san: (key: string, ma?: string[]) =>
    goi<MayDoc>('may_mo_san', key, ma ?? null),
  /** Chuẩn hoá + đánh số + chữ trên khối. Gọi sau MỌI thay đổi cấu trúc. */
  may_kem_the: (doc: MayDoc) => goi<MayDoc>('may_kem_the', doc),
  /** Nguồn của chấm đỏ trên dải 5 trạm và của bảng Vấn đề. */
  may_soat: (doc: MayDoc) => goi<never>('may_soat', doc) as Promise<KetQuaSoatMay>,

  // --- khối ---
  may_khoi_moi: (tram: TramKey, kind: 'start' | 'action', loai?: string | null,
                 thamSo?: ThamSo[]) =>
    goi<KhoiVaThe>('may_khoi_moi', tram, kind, loai ?? null, thamSo ?? []),
  /** Chuẩn hoá + soát MỘT khối. Hộp thoại không tự soát gì. */
  may_luu_khoi: (tram: TramKey, draft: Record<string, unknown>, thamSo?: ThamSo[]) =>
    goi<KhoiVaThe>('may_luu_khoi', tram, draft, thamSo ?? []),

  // --- mẫu dựng sẵn ---
  may_ap_mau: (doc: MayDoc, tram: TramKey, mauKey: string, ma?: string[]) =>
    goi<MayDoc>('may_ap_mau', doc, tram, mauKey, ma ?? null),

  // --- kho cỗ máy trên đĩa ---
  may_ds: () => goi<string[]>('may_ds'),
  may_luu: (doc: MayDoc) =>
    goi<{ path: string; name: string; van_tay: string }>('may_luu', doc),
  may_mo: (ten: string) => goi<MayDoc>('may_mo', ten),
  may_xoa: (ten: string) => goi<boolean>('may_xoa', ten),
  may_mo_file: () => goi<MayDoc>('may_mo_file'),
  may_luu_file: (doc: MayDoc) => goi<{ path: string }>('may_luu_file', doc),
}
