import { useCallback, useEffect, useRef, type ReactNode } from 'react'

/** BẢNG DƯỚI — Vấn đề và Nhật ký.
 *
 *  MỞ APP RA LÀ GẬP. Hai thứ trong đây là để TRA khi có chuyện, không phải thứ nhìn
 *  suốt lúc dựng sơ đồ; mở sẵn là ăn mất một phần tư chiều cao canvas ngay từ giây
 *  đầu. Bấm hàng tab là mở lại.
 *
 *  Chiều cao KÉO ĐƯỢC: bảng Vấn đề có lúc một dòng, có lúc ba chục dòng, mà chiều cao
 *  cố định thì lúc nào cũng sai một trong hai.
 *
 *  Chép từ Jenifer_Studio.
 */
export const CAO_TOI_THIEU = 120
export const CAO_GAP = 31

export interface TabDuoi {
  ma: string
  ten: string
  /** Con số trong ngoặc sau tên tab — 0 thì không hiện. */
  so?: number
  /** Có lỗi (đỏ) hay chỉ cảnh báo. */
  nang?: boolean
  noiDung: ReactNode
}

export default function BangDuoi({ tabs, tab, onTab, cao, onCao, gap, onGap }: {
  tabs: TabDuoi[]
  tab: string
  onTab: (ma: string) => void
  cao: number
  onCao: (c: number) => void
  gap: boolean
  onGap: (g: boolean) => void
}) {
  const keo = useRef<{ y0: number; c0: number } | null>(null)

  const dangKeo = useCallback((e: MouseEvent) => {
    if (!keo.current) return
    onCao(Math.max(CAO_TOI_THIEU, keo.current.c0 + (keo.current.y0 - e.clientY)))
  }, [onCao])

  const thoiKeo = useCallback(() => { keo.current = null }, [])

  useEffect(() => {
    window.addEventListener('mousemove', dangKeo)
    window.addEventListener('mouseup', thoiKeo)
    return () => {
      window.removeEventListener('mousemove', dangKeo)
      window.removeEventListener('mouseup', thoiKeo)
    }
  }, [dangKeo, thoiKeo])

  const hien = tabs.find(t => t.ma === tab) ?? tabs[0]

  return (
    <div className="bang-duoi" style={{ height: gap ? CAO_GAP : cao }}>
      {!gap && (
        <div className="thanh-keo"
             onMouseDown={e => { keo.current = { y0: e.clientY, c0: cao } }} />
      )}
      {/* Bấm vào CẢ HÀNG TAB là mở/gập — không phải đi tìm một nút mũi tên tí xíu. */}
      <div className="hang-tab" onDoubleClick={() => onGap(!gap)}>
        {tabs.map(t => (
          <button key={t.ma}
                  className={'tab' + (t.ma === hien?.ma && !gap ? ' dang' : '')
                             + (t.nang ? ' nang' : '')}
                  onClick={() => { onTab(t.ma); onGap(false) }}>
            {t.ten}{t.so ? ` (${t.so})` : ''}
          </button>
        ))}
        <span className="day" />
        <button className="nut-nho" onClick={() => onGap(!gap)}
                title={gap ? 'Mở bảng dưới' : 'Gập bảng dưới'}>
          {gap ? '▲' : '▼'}
        </button>
      </div>
      {!gap && <div className="noi-dung-tab">{hien?.noiDung}</div>}
    </div>
  )
}
