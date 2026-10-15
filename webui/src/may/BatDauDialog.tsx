import { useEffect, useRef, useState } from 'react'
import { pyMay } from '../api'
import Modal from '../components/Modal'
import type { BootMay, KhoiMay, TheKhoi, TramKey, VanDeMay } from './mayTypes'

/** KHỐI BẮT ĐẦU của một trạm: lịch chạy, khung nến, và (chỉ ①) phạm vi.
 *  (D-10, phần 5, lát 5d)
 *
 *  Khối Bắt đầu là ĐIỂM NEO: cả sơ đồ của trạm chạy lại từ nó cho TỪNG đối tượng trong
 *  phạm vi, theo lịch của nó. Nên ba thứ ấy không phải "cài đặt" nằm đâu đó — chúng là
 *  nội dung của chính khối, và hiện ngay trên hộp.
 *
 *  Mỗi trạm chỉ mời những lịch có nghĩa với nó (`tram.py`): ① chọn mã thì một lần lúc
 *  đầu / mỗi ngày / đầu tuần / đầu tháng; ② và ④ thì mỗi nến; ③ còn có «khi tín hiệu
 *  đổi». Bày hết rồi báo lỗi sau là dạy bằng cách bắt làm sai.
 */
export default function BatDauDialog({ khoi, tram, boot, onLuu, onDong }: {
  khoi: KhoiMay
  tram: TramKey
  boot: BootMay
  onLuu: (st: KhoiMay) => void
  onDong: () => void
}) {
  const [nhap, setNhap] = useState<KhoiMay>(() => JSON.parse(JSON.stringify(khoi)))
  const [the, setThe] = useState<TheKhoi | null>(null)
  const [loi, setLoi] = useState<VanDeMay[]>([])
  const sach = useRef<KhoiMay | null>(null)

  const t = boot.tram.find(x => x.key === tram)
  const laChonMa = tram === 'chon_ma'
  const pv = (nhap.pham_vi ?? { loai: 'tat_ca' }) as { loai: string; ma?: string[] }
  /** Ô mã là chữ TỰ DO trong lúc gõ — Python mới là chỗ tách, viết hoa và bỏ trùng. */
  const [chuMa, setChuMa] = useState<string | null>(null)

  useEffect(() => {
    let song = true
    pyMay.may_luu_khoi(tram, nhap as unknown as Record<string, unknown>)
      .then(r => {
        if (!song) return
        if (r.ok && r.value) {
          sach.current = r.value.step
          setThe(r.value.card)
          setLoi((r.loi as VanDeMay[]) ?? [])
        } else {
          setLoi([{ severity: 'error', message: r.error ?? 'không đọc được khối',
                    tram, step: null, index: null }])
        }
      })
    return () => { song = false }
  }, [nhap, tram])

  return (
    <Modal title={`Bắt đầu — ${t?.so ?? ''} ${t?.ten ?? ''}`} width={680} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Huỷ</button>
             <button className="nut chinh"
                     onClick={() => { onLuu(sach.current ?? nhap); onDong() }}>
               Lưu khối
             </button>
           </>}>
      <div className="chu-dan">
        {t?.hoi} Cả sơ đồ của trạm chạy lại từ khối này cho {t?.cho_ai}.
      </div>

      <div className="hang">
        <label className="nhan-o">Chạy lúc nào</label>
        <select className="o" value={String(nhap.lich ?? t?.lich_mac_dinh ?? '')}
                onChange={e => setNhap(n => ({ ...n, lich: e.target.value }))}>
          {(t?.lich ?? []).map(k => (
            <option key={k} value={k}>{boot.lich[k] ?? k}</option>
          ))}
        </select>

        {nhap.lich === 'moi_nen' && (
          <>
            <label className="nhan-o phu">khung nến</label>
            <select className="o nho"
                    value={String(nhap.khung ?? t?.khung_mac_dinh ?? '')}
                    title={'Khung của trạm — cũng là khung mặc định cho đại lượng nào '
                      + 'trong trạm bỏ trống ô khung'}
                    onChange={e => setNhap(n => ({ ...n, khung: e.target.value }))}>
              {boot.khung.map(k => <option key={k} value={k}>{k}</option>)}
            </select>
          </>
        )}
      </div>

      {laChonMa && (
        <>
          <div className="hang">
            <label className="nhan-o">Xét những mã nào</label>
            <select className="o" value={pv.loai}
                    onChange={e => setNhap(n => ({
                      ...n,
                      pham_vi: e.target.value === 'danh_sach'
                        ? { loai: 'danh_sach', ma: pv.ma ?? [] }
                        : { loai: 'tat_ca' },
                    }))}>
              <option value="tat_ca">mọi mã của màn chơi</option>
              <option value="danh_sach">một danh sách riêng</option>
            </select>
          </div>
          {pv.loai === 'danh_sach' && (
            <div className="hang">
              <label className="nhan-o">Danh sách mã</label>
              <input className="o co-gian" spellCheck={false}
                     placeholder="EURUSD, XAUUSD, GBPJPY"
                     title="Cách nhau bằng dấu phẩy hoặc khoảng trắng"
                     value={chuMa ?? (pv.ma ?? []).join(', ')}
                     onChange={e => {
                       setChuMa(e.target.value)
                       setNhap(n => ({
                         ...n,
                         pham_vi: {
                           loai: 'danh_sach',
                           ma: e.target.value.split(/[,\s]+/).filter(Boolean),
                         },
                       }))
                     }}
                     onBlur={() => setChuMa(null)} />
            </div>
          )}
        </>
      )}

      <div className="hang">
        <label className="nhan-o">Tên khối</label>
        <input className="o co-gian" spellCheck={false} placeholder="Bắt đầu"
               value={String(nhap.name ?? '')}
               onChange={e => setNhap(n => ({ ...n, name: e.target.value }))} />
      </div>

      <div className="xem-truoc">
        <div className="tieu-de-phu">Trên hộp sẽ hiện</div>
        {(the?.lines ?? []).map((d, i) => <div key={i} className="dong">{d.text}</div>)}
        {!the?.lines.length && <div className="dong mo">—</div>}
      </div>

      {loi.length > 0 && (
        <div className="loi-form">
          {loi.map((v, i) => (
            <div key={i} className={v.severity === 'error' ? 'loi-ghi' : 'goi-y'}>
              {v.severity === 'error' ? '● ' : '▲ '}{v.message}
            </div>
          ))}
        </div>
      )}
    </Modal>
  )
}
