import type { TramKey, TramMoTa } from './mayTypes'

/** DẢI 5 TRẠM — ①→⑤ nổi trên đầu canvas.  (D-10, phần 5, lát 5b)
 *
 *  Trả lời câu "đang vẽ phần nào của cỗ máy", nên nó nằm ngay trên chính cái đang vẽ —
 *  y chỗ `PillTab` của sơ đồ cũ. Mũi `→` giữa các trạm là cố ý: thứ tự năm trạm KHÔNG
 *  phải để chọn cho đẹp, nó là đúng thứ tự QuantConnect chạy một thuật toán.
 *
 *  Chấm đỏ = trạm đó có LỖI, chấm vàng = chỉ cảnh báo. Phải thấy được từ trạm đang mở:
 *  giấu lỗi của trạm khác thì bấm ▶ mới lòi ra, lúc đó không ai hiểu vì sao.
 */
export default function DaiTram({ tram, dsTram, dang, dat, dem }: {
  /** Trạm đang mở. */
  tram: TramKey
  dsTram: TramMoTa[]
  /** Có cỗ máy chưa — chưa có thì dải vẫn hiện nhưng không bấm được. */
  dang: boolean
  dat: (k: TramKey) => void
  dem: Record<TramKey, { loi: number; canhBao: number }>
}) {
  const t = dsTram.find(x => x.key === tram)
  return (
    <div className="dai-tram">
      <div className="dt-hang">
        {dsTram.map((x, i) => {
          const d = dem[x.key] ?? { loi: 0, canhBao: 0 }
          const cham = d.loi ? 'do' : d.canhBao ? 'vang' : ''
          return (
            <span key={x.key} className="dt-o">
              {i > 0 && <span className="dt-mui" aria-hidden>→</span>}
              <button
                className={'dt-tram' + (x.key === tram ? ' dang' : '')}
                disabled={!dang}
                onClick={() => dat(x.key)}
                title={`${x.so} ${x.ten} — ${x.hoi}\nQuantConnect gọi là ${x.qc}`
                  + (d.loi ? `\n${d.loi} lỗi` : '')
                  + (d.canhBao ? `\n${d.canhBao} cảnh báo` : '')}>
                <span className="dt-so">{x.so}</span>
                <span className="dt-ten">{x.ten}</span>
                {cham && <span className={'dt-cham ' + cham} aria-hidden />}
              </button>
            </span>
          )
        })}
      </div>
      {t && (
        /* Câu hỏi của trạm, do Python khai trong `tram.py` — giao diện không tự viết
           lời giải thích nào, nên sửa từ điển là màn hình đổi theo. */
        <div className="dt-giai">
          <b>{t.hoi}</b>
          <span className="dt-phu">chạy cho {t.cho_ai} · ra {t.ra}</span>
        </div>
      )}
    </div>
  )
}
