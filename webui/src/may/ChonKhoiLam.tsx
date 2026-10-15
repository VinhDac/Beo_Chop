import Modal from '../components/Modal'
import { khoiLamCuaTram } from './doThi'
import type { BootMay, TramKey } from './mayTypes'

/** CHỌN KHỐI LÀM để thêm vào trạm đang mở.  (D-10, phần 5, lát 5c)
 *
 *  Mỗi trạm có bộ khối Làm RIÊNG — đó là chỗ duy nhất năm trạm khác nhau về hành động.
 *  Nên danh sách ở đây chỉ gồm khối của trạm đang mở: bày cả 14 khối rồi báo "«Báo tín
 *  hiệu» là khối của trạm ②" sau khi người chơi đã đặt nó xuống là dạy bằng cách bắt
 *  làm sai.
 */
export default function ChonKhoiLam({ tram, boot, onChon, onDong }: {
  tram: TramKey
  boot: BootMay
  onChon: (loai: string) => void
  onDong: () => void
}) {
  const t = boot.tram.find(x => x.key === tram)
  const ds = khoiLamCuaTram(boot, tram)

  return (
    <Modal title={`Khối Làm của ${t?.so ?? ''} ${t?.ten ?? ''}`} width={560}
           onClose={onDong}
           footer={<><span className="day" />
                     <button className="nut" onClick={onDong}>Huỷ</button></>}>
      <div className="chu-dan">
        {t?.hoi} Trạm này chạy cho {t?.cho_ai}, và {t?.ra}.
      </div>
      <div className="ds-hanh-dong">
        {ds.map(({ key, d, canCo }) => (
          <button key={key} className="danh-hd" onClick={() => { onChon(key); onDong() }}>
            <div className="dong-hd">
              <b>{d.nhan}</b>
              {/* Khối nào mà THIẾU thì trạm không ra được kết quả — nói ngay ở đây, chỗ
                  người chơi đang chọn, chứ không đợi bảng Vấn đề. */}
              {canCo && <span className="the">trạm cần ít nhất một</span>}
              {d.vai === 'phu' && <span className="the">khối phụ</span>}
            </div>
            <div className="kho-mota">{d.mo_ta}</div>
          </button>
        ))}
      </div>
    </Modal>
  )
}
