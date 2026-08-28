/** Bộ icon NÉT dùng chung.
 *
 * Không dùng emoji tô màu: nó mang màu riêng nên không theo `currentColor` và không
 * hoà với theme, hình dáng thì phụ thuộc font hệ thống nên mỗi máy một kiểu, nét dày
 * mỏng cũng không khớp với các icon còn lại.
 *
 * Toàn bộ vẽ bằng `stroke="currentColor"` nên tự ăn màu chỗ đặt: mờ khi nút bị tắt,
 * sáng khi hover, đổi theo màu nhấn nếu cần.
 *
 * KHÔNG đụng tới ký hiệu đơn sắc (→ ↻ ◆ ⟲ ■ ▶ ① ✕): chúng vốn đã là nét một màu.
 */

const S = {
  fill: 'none' as const,
  stroke: 'currentColor',
  strokeWidth: 1.5,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

const HINH: Record<string, React.ReactNode> = {
  /* --- loại hành động --- */
  /* Kiểm tra điều kiện: một đường vào, hai đường ra — đúng hình rẽ nhánh vẽ trên giấy. */
  'check-cond': <><path {...S} d="M1.8 8h3.9M5.7 8l3.1-3.1M5.7 8l3.1 3.1" /><circle {...S} cx="11.3" cy="4.9" r="1.8" /><circle {...S} cx="11.3" cy="11.1" r="1.8" /></>,
  /* Số hạng: hai bậc thang cộng dồn + dấu cộng — "góp thêm một tầng vào báo giá".
     Không vẽ dấu `=` hay `+=` thành hình: phép nằm ngay trên dòng chữ của hộp rồi,
     icon mà lặp lại nó thì tốn chỗ mà không thêm gì. */
  'so-hang': <><path {...S} d="M1.9 12.4h3.4V9.2h3.4V6" /><path {...S} d="M1.9 12.4v-2" strokeDasharray="1.4 1.3" /><path {...S} d="M11.4 3.1v4.6M9.1 5.4h4.6" /></>,

  /* ⚠ `vao-lenh` (nến + mũi tên phá vùng) và `sua-lenh` (đường giá + tay kéo chốt
       SL/TP) đã đi cùng hai động từ ấy. Cả hai vẽ về một thế giới có LỆNH RỜI mang
       SL/TP riêng — market maker không có thứ đó.

     ⚠ MƯỜI BỐN ICON ĐÃ ĐI ở đợt 4, cùng thứ chúng đứng trên:
       kieu-nen · kieu-bar · kieu-line · ve-mau · zone · an-lenh · ve-nay   thanh công
         cụ chart của cửa sổ Tester (ba kiểu vẽ giá, ba nút xem, hộp zone);
       up · down · motSo · minus · dau · cuoi   nút xếp thứ tự bảng tham số, submenu
         nhịp, và điều khiển tua của tester;
       dat-co   hành động "Đặt cờ" đã bỏ từ trước cả lần dọn này — `ICON_HANH_DONG`
         vẫn còn ánh xạ tới nó, tức một dòng chết nằm im suốt nhiều bản.
     Bản cũ: `git show f1c90fb:webui/src/components/Icon.tsx`. */

  /* --- loại khối --- */
  start: <><circle {...S} cx="8" cy="8" r="5.9" /><path {...S} d="M8 3.6l2.6 4.4L8 12.4 5.4 8z" /></>,
  action: <><path {...S} d="M9.4 1.8 4 9h3.3l-.8 5.2L11.9 7H8.6z" /></>,

  /* --- ghim số: đinh ghim + mũi tên quay lại --- */
  ghim: <><path {...S} d="M9.6 1.9l4.5 4.5-1.8 1L9 5.1z" /><path {...S} d="M9 5.1L4.6 8.3l3.1 3.1 3.2-4.4" /><path {...S} d="M6.2 9.8L2.4 13.6" /></>,
  'bo-ghim': <><path {...S} d="M9.6 1.9l4.5 4.5-1.8 1L9 5.1z" /><path {...S} d="M9 5.1L4.6 8.3l3.1 3.1 3.2-4.4" /><path {...S} d="M1.6 1.6l12.8 12.8" strokeWidth={1.7} /></>,

  /* --- nút --- */
  trash: <><path {...S} d="M2.6 4.4h10.8M6 4.4V2.8h4v1.6M4 4.4l.8 9h6.4l.8-9" /><path {...S} d="M6.6 6.8v4.2M9.4 6.8v4.2" /></>,
  plus: <><path {...S} d="M8 3v10M3 8h10" /></>,
  gear: <><circle {...S} cx="8" cy="8" r="4.9" /><circle {...S} cx="8" cy="8" r="1.9" /><g strokeWidth={2} stroke="currentColor" strokeLinecap="round"><path d="M8 1.3v1.4M8 13.3v1.4M14.7 8h-1.4M2.7 8H1.3" /><path d="M12.7 3.3l-1 1M4.3 11.7l-1 1M12.7 12.7l-1-1M4.3 4.3l-1-1" /></g></>,
  edit: <><path {...S} d="M9.8 3.2l3 3L6 13H3v-3z" /><path {...S} d="M8.4 4.6l3 3" /></>,
  copy: <><rect {...S} x="5.6" y="2.4" width="8" height="9.6" rx="1.3" /><path {...S} d="M10.6 14.2H3.7a1.3 1.3 0 0 1-1.3-1.3V5.2" /></>,
  paste: <><path {...S} d="M6 3.2H4.3a1.3 1.3 0 0 0-1.3 1.3v8.2a1.3 1.3 0 0 0 1.3 1.3h7.4a1.3 1.3 0 0 0 1.3-1.3V4.5a1.3 1.3 0 0 0-1.3-1.3H10" /><rect {...S} x="6" y="1.8" width="4" height="2.8" rx=".9" /></>,
  branch: <><path {...S} d="M1.8 8h3.9M5.7 8l3.1-3.1M5.7 8l3.1 3.1" /><circle {...S} cx="11.3" cy="4.9" r="1.8" /><circle {...S} cx="11.3" cy="11.1" r="1.8" /></>,
  folder: <><path {...S} d="M2 12.6V4.4a1 1 0 0 1 1-1h3.2l1.4 1.8H13a1 1 0 0 1 1 1v6.4a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z" /></>,
  save: <><path {...S} d="M3.4 2.6h7.4L13.4 5.2v8.2a1 1 0 0 1-1 1H3.6a1 1 0 0 1-1-1V3.6a1 1 0 0 1 .8-1z" /><path {...S} d="M5.4 2.6v3.6h5V2.6M5.4 14.4V9.8h5.2v4.6" /></>,
  undo: <><path {...S} d="M6 5.2 2.8 8.4 6 11.6" /><path {...S} d="M2.8 8.4h6.4a3.6 3.6 0 0 1 0 7.2H7" /></>,
  redo: <><path {...S} d="m10 5.2 3.2 3.2L10 11.6" /><path {...S} d="M13.2 8.4H6.8a3.6 3.6 0 0 0 0 7.2H9" /></>,
  unlink: <><path {...S} d="M6.6 9.4 4.9 11a2.6 2.6 0 0 1-3.7-3.7l1.7-1.7M9.4 6.6 11 4.9a2.6 2.6 0 0 1 3.7 3.7L13 10.3" /><path {...S} d="M2 2l12 12" /></>,
  fit: <><path {...S} d="M3 6V3h3M13 6V3h-3M3 10v3h3M13 10v3h-3" /><rect {...S} x="6" y="6" width="4" height="4" rx=".8" /></>,
  chay: <><circle {...S} cx="8" cy="8" r="6" /><path {...S} d="M6.5 5.3l4.4 2.7-4.4 2.7z" /></>,
}

export default function Icon({ name, size = 14 }: { name: string; size?: number }) {
  const h = HINH[name]
  if (!h) return null
  return (
    <svg viewBox="0 0 16 16" width={size} height={size} className="icon" aria-hidden>{h}</svg>
  )
}

/** Loại hành động -> tên icon. Web tự quyết VẼ GÌ; Python chỉ nói ĐÓ LÀ GÌ (`type`). */
export const ICON_HANH_DONG: Record<string, string> = {
  check_cond: 'check-cond',
  so_hang: 'so-hang',
}
