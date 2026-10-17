import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'

/** VỎ BẢNG NỔI — một tấm nhỏ bật ra cạnh cái nút vừa bấm.
 *
 *  ⚠ PHẢI `position: fixed`, không được `absolute`. Thân hộp thoại (`.ht-than`) có
 *  `overflow: auto`, nên một tấm `absolute` nằm trong đó sẽ bị CẮT ở mép hộp và cuộn
 *  theo nội dung — đúng chỗ bảng chọn dài nhất thì nó mất nửa dưới. `fixed` thì nó
 *  nổi trên mọi thứ, và ta tự tính chỗ từ hình chữ nhật của cái nút.
 *
 *  Tự lật lên trên khi dưới hết chỗ, và tự kéo vào trong khi tràn mép phải: một bảng
 *  bày ra ngoài màn hình thì không khác gì không bày.
 *
 *  Đóng bằng Esc hoặc bấm ra ngoài. `capture: true` cho Esc để nó chạy TRƯỚC listener
 *  của `Modal` — không thì một phím Esc đóng luôn cả hộp thoại phía dưới.
 */
/** ĐẾM số bảng nổi đang mở.
 *
 *  ⚠ VÌ SAO PHẢI ĐẾM, THAY VÌ `stopPropagation`. Cả `Modal` lẫn bảng này đều nghe
 *  `keydown` trên `window` với `capture: true`. `capture` KHÔNG đảo thứ tự chạy khi
 *  hai listener cùng một đích: chúng chạy theo THỨ TỰ ĐĂNG KÝ, mà `Modal` mở trước
 *  nên nó luôn chạy trước. `stopPropagation` của bảng gọi thì đã muộn — một phím Esc
 *  đóng luôn cả hộp thoại phía dưới, mất hết những gì đang sửa dở.
 *
 *  Nên `Modal` HỎI trước: còn bảng nào nổi thì Esc là của bảng ấy. */
let dangMo = 0
export const coBangNoi = () => dangMo > 0

export default function BangNoi({ neo, rong = 300, cao = 380, onDong, children }: {
  /** Hình chữ nhật của cái nút đã mở bảng này (`getBoundingClientRect()`). */
  neo: DOMRect
  rong?: number
  /** Chiều cao TỐI ĐA — bảng ngắn hơn thì co lại đúng nội dung. */
  cao?: number
  onDong: () => void
  children: ReactNode
}) {
  const rf = useRef<HTMLDivElement>(null)
  const [cho, setCho] = useState<{ left: number; top: number } | null>(null)

  useLayoutEffect(() => {
    const h = rf.current?.offsetHeight ?? cao
    const duoi = window.innerHeight - neo.bottom - 8
    // Lật lên chỉ khi TRÊN rộng hơn DƯỚI — lật bừa thì bảng nhảy lung tung.
    const top = (duoi < h && neo.top - 8 > duoi) ? Math.max(8, neo.top - 6 - h)
                                                : neo.bottom + 6
    const left = Math.max(8, Math.min(neo.left, window.innerWidth - rong - 8))
    setCho({ left, top })
  }, [neo, rong, cao])

  useEffect(() => {
    dangMo += 1
    const phim = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.stopPropagation(); onDong() }
    }
    const ngoai = (e: MouseEvent) => {
      if (!rf.current?.contains(e.target as Node)) onDong()
    }
    window.addEventListener('keydown', phim, true)
    // `setTimeout` 0: chính cú bấm MỞ bảng cũng là một mousedown — gắn ngay thì nó
    // bắt luôn cú ấy và bảng đóng lại trước khi kịp hiện.
    const t = setTimeout(() => window.addEventListener('mousedown', ngoai, true), 0)
    return () => {
      dangMo -= 1
      clearTimeout(t)
      window.removeEventListener('keydown', phim, true)
      window.removeEventListener('mousedown', ngoai, true)
    }
  }, [onDong])

  return (
    <div ref={rf} className="bang-noi"
         style={{ width: rong, maxHeight: cao, left: cho?.left ?? -9999,
                  top: cho?.top ?? -9999, visibility: cho ? 'visible' : 'hidden' }}>
      {children}
    </div>
  )
}
