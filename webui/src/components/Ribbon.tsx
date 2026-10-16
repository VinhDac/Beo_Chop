import type { ReactNode } from 'react'
import IconNet from './Icon'

/** Thanh công cụ kiểu ribbon của Paint: nút nhóm lại, nhãn nhóm nằm DƯỚI, có vạch ngăn
 *  giữa các nhóm.
 *
 *  LUẬT BỐ CỤC (chép từ Jenifer_Studio): mọi thứ "thêm vào" nằm ở TRÊN; canvas phía
 *  dưới chỉ để DI CHUYỂN và NỐI. Nhờ vậy không bao giờ phải hỏi "thêm khối ở đâu nhỉ".
 *
 *  `hienTu` = nhóm chỉ hiện khi cửa sổ rộng từ ngần ấy px — cửa sổ hẹp thì bỏ nhóm ít
 *  dùng trước, không bóp nhỏ mọi nút cho vừa.
 */
function Nhom({ ten, children, hienTu }: {
  ten: string; children: ReactNode; hienTu?: number
}) {
  return (
    <div className={'nhom-ribbon' + (hienTu ? ` hien-tu-${hienTu}` : '')}>
      <div className="cac-nut">{children}</div>
      <div className="ten-nhom">{ten}</div>
    </div>
  )
}

function Nut({ ten, icon, onClick, tat, title }: {
  ten: string; icon: string; onClick?: () => void; tat?: boolean; title?: string
}) {
  return (
    <button className="nut-lon" onClick={onClick} disabled={tat} title={title ?? ten}>
      <span className="hinh"><IconNet name={icon} size={18} /></span>
      {ten}
    </button>
  )
}

export interface ViecRibbon {
  themBatDau: () => void
  themNhom: () => void
  themKhoiLe: () => void
  themQuayVe: () => void
  xoa: () => void
  nhanBan: () => void
  hoanTac: () => void
  lamLai: () => void
  gomHatNhan: () => void
  taHatNhan: () => void
  luu: () => void
  mo: () => void
  moi: () => void
}

export default function Ribbon({ v, soChon, trongHatNhan, coHoanTac, coLamLai, oTim }: {
  v: ViecRibbon; soChon: number; trongHatNhan: boolean
  coHoanTac: boolean; coLamLai: boolean
  /** Ô tìm khối — dạt sang PHẢI, tách hẳn khỏi các nhóm nút: nó không "thêm" gì vào
   *  sơ đồ, nó chỉ giúp nhìn. Trộn vào giữa các nhóm là người ta bấm nhầm. */
  oTim?: ReactNode
}) {
  return (
    <div className="ribbon">
      <Nhom ten="Thêm khối">
        <Nut ten="Bắt đầu" icon="start" onClick={v.themBatDau} />
        <Nut ten="Nhóm" icon="group" onClick={v.themNhom}
             title="Một chuỗi hành động gói vào một hộp — chạy thẳng một lượt" />
        <Nut ten="Khối lẻ" icon="action" onClick={v.themKhoiLe} />
        <Nut ten="Quay về" icon="quay-ve" onClick={v.themQuayVe}
             title="Nhảy ngược về một khối phía trước — khối trụ để vẽ vòng lặp" />
      </Nhom>

      <Nhom ten="Sửa">
        <Nut ten="Nhân bản" icon="copy" onClick={v.nhanBan} tat={!soChon} />
        <Nut ten="Xoá" icon="trash" onClick={v.xoa} tat={!soChon} />
      </Nhom>

      <Nhom ten="Hạt nhân">
        <Nut ten="Gom" icon="frame" onClick={v.gomHatNhan} tat={soChon < 2 || trongHatNhan}
             title="Gói các khối đang chọn thành một khung — CHỈ là cách nhìn, sơ đồ không đổi" />
        <Nut ten="Tách" icon="unlink" onClick={v.taHatNhan} tat={!soChon}
             title="Đưa các khối đang chọn ra khỏi hạt nhân của chúng" />
      </Nhom>

      <Nhom ten="Hoàn tác" hienTu={1090}>
        <Nut ten="Hoàn tác" icon="undo" onClick={v.hoanTac} tat={!coHoanTac} />
        <Nut ten="Làm lại" icon="redo" onClick={v.lamLai} tat={!coLamLai} />
      </Nhom>

      <Nhom ten="Cỗ máy" hienTu={1250}>
        <Nut ten="Mới" icon="file" onClick={v.moi} />
        <Nut ten="Mở" icon="folder" onClick={v.mo} />
        <Nut ten="Lưu" icon="save" onClick={v.luu} />
      </Nhom>

      <div className="ribbon-day" />
      {oTim}
    </div>
  )
}
