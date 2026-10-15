import { useEffect, useState } from 'react'
import { pyMay } from '../api'
import Modal from '../components/Modal'
import { oCoNghia } from './doThi'
import OSo from './OSo'
import type { BootMay, MayDoc, TramKey, VanDeMay } from './mayTypes'

/** BẢNG GOM — bước cuối của một trạm, chạy MỘT LẦN cho cả trạm.  (D-10, phần 5, lát 5d)
 *
 *  Sơ đồ trả lời từng mã một; có những câu chỉ trả lời được khi nhìn CẢ RỔ — "giữ 10 mã
 *  điểm cao nhất", "tổng tỷ trọng không quá ngân sách". Những câu đó không nằm ở khối
 *  nào được, nên chúng ở đây. Chỉ ① và ③ có Gom.
 *
 *  Đổi một ô là soát lại NGAY cả cỗ máy (bản nháp, chưa ghi) — Gom sai khoảng hay "giữ N
 *  mã mà không khối nào cho điểm" phải hiện ra lúc đang vặn, không phải sau khi đóng.
 */
export default function GomDialog({ doc, tram, boot, onLuu, onDong }: {
  doc: MayDoc
  tram: TramKey
  boot: BootMay
  onLuu: (gom: Record<string, unknown>) => void
  onDong: () => void
}) {
  const khai = boot.gom[tram] ?? []
  const [gom, setGom] = useState<Record<string, unknown>>(
    () => JSON.parse(JSON.stringify(doc.tram[tram].gom ?? {})))
  const [vanDe, setVanDe] = useState<VanDeMay[]>([])

  const t = boot.tram.find(x => x.key === tram)

  useEffect(() => {
    let song = true
    const thu: MayDoc = {
      ...doc,
      tram: { ...doc.tram, [tram]: { ...doc.tram[tram], gom } },
    }
    pyMay.may_soat(thu).then(r => {
      if (!song) return
      /* Lấy MỌI vấn đề của trạm này, không chỉ vấn đề mang nhãn Gom: đổi một ô Gom hay
         làm nổi lên một câu gắn với KHỐI — "«Cho vào rổ» không có điểm, mà Gom giữ N mã
         điểm cao nhất". Lọc theo `step` rỗng là lọc mất đúng câu quan trọng nhất. */
      setVanDe((r.value ?? []).filter(v => v.tram === tram))
    })
    return () => { song = false }
  }, [gom, doc, tram])

  if (!khai.length) return null

  return (
    <Modal title={`Gom — ${t?.so ?? ''} ${t?.ten ?? ''}`} width={620} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh" onClick={() => { onLuu(gom); onDong() }}>
               Lưu
             </button>
           </>}>
      <div className="chu-dan">
        Chạy một lần sau khi MỌI đối tượng đã đi qua sơ đồ của trạm {t?.so} {t?.ten} —
        {tram === 'chon_ma'
          ? ' đây là chỗ cắt rổ xuống còn N mã.'
          : ' đây là chỗ chia ngân sách và chặn trần mỗi mã.'}
      </div>

      <div className="khoi-form">
        {khai.filter(f => oCoNghia(f, gom)).map(f => (
          <div className="hang" key={f.key}>
            <label className="nhan-o">{f.nhan}</label>
            {f.loai === 'chon' && f.chon ? (
              <select className="o" value={String(gom[f.key] ?? f.mac_dinh ?? '')}
                      onChange={e => setGom(g => ({ ...g, [f.key]: e.target.value }))}>
                {Object.entries(f.chon).map(([k, nhan]) => (
                  <option key={k} value={k}>{nhan}</option>
                ))}
              </select>
            ) : f.loai === 'bat_tat' ? (
              <label className="tick">
                <input type="checkbox"
                       checked={gom[f.key] === undefined ? !!f.mac_dinh : !!gom[f.key]}
                       onChange={e => setGom(g => ({ ...g, [f.key]: e.target.checked }))} />
                <span>{f.nhan}</span>
              </label>
            ) : (
              <>
                <OSo v={gom[f.key] as number | string | undefined}
                     thamSo={doc.tham_so} nguyen={f.nguyen}
                     title={[f.min !== undefined ? `từ ${f.min}` : '',
                             f.max !== undefined ? `tới ${f.max}` : '']
                       .filter(Boolean).join(' ')}
                     dat={x => setGom(g => ({ ...g, [f.key]: x }))} />
                {f.tuy_chon && (
                  <button className="nut nho"
                          title="Bỏ trống — không giới hạn"
                          onClick={() => setGom(g => {
                            const m = { ...g }
                            delete m[f.key]
                            return m
                          })}>bỏ trống</button>
                )}
              </>
            )}
            {f.don_vi === 'ma' && <span className="goi-y">mã</span>}
          </div>
        ))}
      </div>

      {vanDe.length > 0 && (
        <div className="loi-form">
          <div className="tieu-de-phu">Trạm {t?.so} {t?.ten} đang có</div>
          {vanDe.map((v, i) => (
            <div key={i} className={v.severity === 'error' ? 'loi-ghi' : 'goi-y'}>
              {v.severity === 'error' ? '● ' : '▲ '}{v.message}
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
