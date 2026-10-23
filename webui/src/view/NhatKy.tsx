/* NHẬT KÝ SỐNG — dòng nảy lên đúng lúc nó xảy ra.
 *
 * Khác một danh sách tĩnh cuộn được: lúc PHÁT, nó tự chạy theo con trỏ. Đó là cả
 * điểm của việc đọc nhật ký sống — thấy dòng «đặt lệnh» hiện ra đúng nhịp mà mũi tên
 * xuất hiện trên chart.
 *
 * Bấm một dòng làm HAI việc cùng lúc: con trỏ nhảy tới nhịp ấy, và sơ đồ ở cửa sổ
 * chính sáng lên đúng đường lệnh ấy đã đi. Hai việc vì người ta bấm vào một dòng
 * nhật ký đúng lúc đang hỏi «cái này ở đâu ra» — mà câu trả lời nằm cả ở chart lẫn
 * ở sơ đồ.
 */
import { memo, useEffect, useRef } from 'react'
import { py } from '../api'
import { tr } from '../ngon_ngu'
import type { DongNhatKy } from './mach_view'

export interface NhatKyProps {
  ds: DongNhatKy[]
  /** Nhịp con trỏ đang đứng — dòng nào thuộc nhịp sau đó thì chưa xảy ra. */
  chiSo: number
  nhay: (i: number) => void
}

function NhatKy({ ds, chiSo, nhay }: NhatKyProps) {
  const hop = useRef<HTMLDivElement>(null)
  const daRa = ds.filter(d => d.i <= chiSo)

  /* TỰ CUỘN THEO DÒNG MỚI NHẤT. Không có nó thì lúc phát, dòng mới rơi xuống dưới
     mép và người xem nhìn một danh sách đứng im — đúng cái bản cũ phải sửa. */
  useEffect(() => {
    const el = hop.current
    if (el) el.scrollTop = el.scrollHeight
  }, [daRa.length])

  return (
    <div className="view-nk">
      <div className="view-nk-dau">
        {tr('Nhật ký')}
        <span className="view-nk-dem">{daRa.length}/{ds.length}</span>
      </div>
      <div className="view-nk-cuon" ref={hop}>
        {ds.length === 0 && (
          <div className="view-nk-trong">{tr('Lượt này không ra lệnh nào.')}</div>
        )}
        {daRa.map((d, k) => (
          <button
            key={k} type="button"
            className={'view-nk-dong' + (d.hong ? ' hong' : '')
                       + (d.i === chiSo ? ' dang' : '')}
            title={tr('Nhảy tới đây, và soi đường trên sơ đồ')}
            onClick={() => {
              nhay(d.i)
              if (d.tag) void py.soi_luot(d.tag)
            }}>
            <span className="view-nk-ngay">{d.ngay}</span>
            <span className="view-nk-chu">{d.chu}</span>
            <span className="view-nk-tag">{d.tag}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default memo(NhatKy)
