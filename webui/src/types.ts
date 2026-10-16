/** Hình dạng dữ liệu đi qua cầu nối.
 *
 * D-12: khối cũ đã xoá, nên ở đây chỉ còn ba thứ không dính gì tới khối. Kiểu của bộ
 * khối mới sẽ khai cùng lúc với bộ khối đó.
 */

export interface Reply<T> {
  ok: boolean
  value?: T
  error?: string
  trace?: string
  [k: string]: unknown
}

/** App lưu file ở đâu — `api.kho_danh_muc`. */
export interface KhoDanhMuc {
  luu_tru: {
    goc: string
    muc: { ten: string; duong_dan: string; so_luong: number; danh_sach: string[] }[]
  }
}

/** Khoá đặt ở đâu. KHÔNG BAO GIỜ có token. */
export interface KhoaQC {
  co: boolean; nguon: 'bien_moi_truong' | 'file' | null; user_id: string | null
  duong: string; loi?: string
}
