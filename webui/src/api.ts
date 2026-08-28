/** Vỏ bọc có kiểu quanh `window.pywebview.api`.
 *
 * Mọi lời gọi Python đi qua đây, không rải `window.pywebview` khắp components — để
 * sau này đổi cách vận chuyển (hoặc giả lập khi test) chỉ phải sửa một file.
 */
import type {
  BoNguon, Bootstrap, CaiDatNguon, Card, DongThiTruong, KetQuaSoat, KetQuaTest,
  KhoDanhMuc,
  ProcEdge, ProcessDoc, Reply, Step, Tab, TrangThaiGhi,
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
      // Chờ ĐÚNG hàm mà trang này sắp gọi: cửa sổ tester có `ApiTester` riêng, KHÔNG
      // có `bootstrap`. Chờ cứng `bootstrap` ở đó là treo 10 giây rồi báo mất kết nối.
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

// ⚠ `GoiNen` — gói nến cho chart của cửa sổ tester — đã đi ở đợt 2.

export const py = {
  bootstrap: () => goi<Bootstrap>('bootstrap'),
  set_title: (ten: string) => goi<null>('set_title', ten),

  // --- tài liệu ---
  new_process: () => goi<ProcessDoc>('new_process'),
  demo_process: () => goi<ProcessDoc>('demo_process'),
  load_process: (ten: string) => goi<ProcessDoc>('load_process', ten),
  /** Khối + nối của MỘT tab trong một chiến lược đã lưu, để THÊM CHỒNG lên sơ đồ đang
   *  mở. Kèm những tham số đám khối đó thật sự đọc. */
  import_steps: (ten: string, tab: Tab) =>
    goi<{ steps: Step[]; edges: ProcEdge[]; tham_so: never[]
          bo_start: boolean; ten: string }>('import_steps', ten, tab),
  save_process: (doc: ProcessDoc) =>
    goi<{ path: string; name: string }>('save_process', doc),
  open_process_file: () => goi<ProcessDoc>('open_process_file'),
  save_process_file: (doc: ProcessDoc) => goi<{ path: string }>('save_process_file', doc),

  // --- template ---
  list_templates: () => goi<string[]>('list_templates', 'strategy'),
  delete_template: (ten: string) => goi<boolean>('delete_template', 'strategy', ten),

  // --- khối ---
  new_step: (kind: string, actionType?: string) =>
    goi<{ step: Step; card: Card }>('new_step', kind, actionType ?? null),
  clone_steps: (steps: Step[]) =>
    goi<{ steps: Step[]; map: Record<string, string>; cards: Card[] }>(
      'clone_steps', steps, []),
  describe: (steps: Step[]) =>
    goi<Card[]>('describe', steps, []),

  /** Danh mục kho — engine nào đang nạp, tính được những gì, lưu ở đâu. */
  kho_danh_muc: () => goi<KhoDanhMuc>('kho_danh_muc'),

  /** Nguồn của HUY HIỆU SỐ và của bảng Vấn đề — CẢ HAI sơ đồ, một lời gọi. */
  validate: (doc: ProcessDoc) => goi<never>('validate', doc) as Promise<KetQuaSoat>,

  // --- hộp thoại hành động ---
  save_action: (draft: Record<string, unknown>, tab: Tab) =>
    goi<{ action: Record<string, unknown>; display: string }>(
      'save_action', draft, tab, []),
  action_defaults: (t: string) => goi<Record<string, unknown>>('action_defaults', t),

  // --- cài đặt ---
  save_settings: (s: Record<string, unknown>) =>
    goi<Record<string, unknown>>('save_settings', s),
  /** Trả bốn núm vặn của mô hình khớp về mặc định BI QUAN. */
  khop_mac_dinh: () => goi<Record<string, unknown>>('khop_mac_dinh'),
  save_ui: (state: Record<string, unknown>) =>
    goi<Record<string, unknown>>('save_ui', state),
  // ⚠ `save_test_settings` ĐÃ BỎ cùng mục "Strategy Test" trong Cài đặt — nó lưu
  // spread/vốn/phí/đòn bẩy của một bộ chạy theo nến không còn tồn tại.

  // --- NGUỒN DỮ LIỆU (ổ cắm §1) ---
  //
  // ⚠ App KHÔNG sở hữu bộ ghi — nó là tiến trình riêng phải sống 24/7 kể cả khi app
  // đóng. `nguon_bat_dau` mở một tiến trình RỜI, `nguon_dung` chỉ ĐẶT CỜ chứ không
  // giết (giết là mất phần đệm chưa xả). Xem `cat_studio/api.py`.
  nguon_liet_ke: () => goi<{ ds: BoNguon[]; ghi: TrangThaiGhi; thu_muc: string
                             cai_dat: CaiDatNguon }>('nguon_liet_ke'),
  nguon_luu_cai_dat: (cd: Partial<CaiDatNguon>) => goi<{
    cai_dat: CaiDatNguon; can_khoi_dong_lai: boolean }>('nguon_luu_cai_dat', cd),
  /** Quét bốn sàn. CHẬM (vài chục giây) — giao diện phải hiện trạng thái chờ. */
  nguon_do_thi_truong: (klToiThieu: number, phi: number | null) => goi<{
    ds: DongThiTruong[]; so: number; hong: string[]
    phi_dang_dung: Record<string, number> }>('nguon_do_thi_truong', klToiThieu, phi),
  nguon_bat_dau: (symbols: string[]) => goi<{ symbols: string[] }>(
    'nguon_bat_dau', symbols),
  nguon_dung: () => goi<{ da_xin: boolean; pid: number | null }>('nguon_dung'),
  nguon_xoa: (symbol: string) => goi<{ mb: number; ds: BoNguon[] }>('nguon_xoa', symbol),

  // --- ▶ Chạy · ● Live — HAI Ổ CẮM TRỐNG ---
  //
  // Python trả `{ok:false, error:…}` cho cả hai: bộ chạy và tầng đặt lệnh đã gỡ cùng
  // MT5 (đợt 2). Giữ nguyên chữ ký ở đây chứ không xoá — `App.tsx` đã sẵn nhánh
  // `if (!r.ok) alert(r.error)`, nên nút vẫn nói được thành lời thay vì trông như hỏng.
  // Xem `tai_lieu/o_cam_trong.md`.
  /** ▶ Test — chạy backtest trên dữ liệu tick đã ghi. Trả BẢNG SỐ; cửa sổ Tester
   *  (biểu đồ, tua, soi từng lượt) là ổ cắm còn trống. */
  mo_tester: (doc: ProcessDoc, symbol?: string) =>
    goi<KetQuaTest>('mo_tester', doc, symbol),
  mo_live: (doc: ProcessDoc) => goi<{ da_mo: boolean }>('mo_live', doc),

  // --- cửa sổ (thanh tiêu đề tự vẽ) ---
  vung_khong_keo: (vung: number[][], cao: number) => goi<null>('vung_khong_keo', vung, cao),
  keo_cua_so: (ht: number) => goi<boolean>('keo_cua_so', ht),
  cua_so_thu_nho: () => goi<null>('cua_so_thu_nho'),
  cua_so_phong_to: () => goi<boolean>('cua_so_phong_to'),
  cua_so_dang_phong_to: () => goi<boolean>('cua_so_dang_phong_to'),
  cua_so_dong: () => goi<null>('cua_so_dong'),
}
