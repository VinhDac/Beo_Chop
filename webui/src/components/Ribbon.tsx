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
/** NGƯỠNG ẨN NHÓM — cửa sổ phải rộng từ ngần này px thì nhóm mới còn hiện.
 *
 *  MỘT BẢNG DUY NHẤT, vì mỗi số ở đây phải có một `@media (max-width: <số-1>px)
 *  .hien-tu-<số>` trong `app.css`. Thiếu dòng CSS thì lớp sinh ra CHẲNG ẨN GÌ CẢ:
 *  không lỗi, không cảnh báo, `tsc` sạch, build sạch — chỉ có ribbon tràn ngang và
 *  nhãn các nút đè lên nhau ở cửa sổ hẹp. (Đã hỏng thật với 1090 và 1250, suốt từ đầu.)
 *  `test_giao_dien` đọc đúng bảng này rồi đối chiếu với `app.css`. */
const HIEN_TU = { ghiBao: 1460, hoanTac: 1090, strategy: 1250 }

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
  /** Thêm một khối XÁC NHẬN của loại `loai`. */
  themHoi: (loai: string) => void
  /** Năm loại câu hỏi, lấy từ từ điển Python — ribbon KHÔNG tự khai danh sách. */
  loaiHoi: { ma: string; nhan: string; icon: string; mo_ta: string;
             tat: string | false }[]
  /** Thêm một khối HÀNH ĐỘNG của loại `loai`. */
  themLam: (loai: string) => void
  /** Tám loại việc, cũng lấy từ từ điển Python — kể cả việc chia nhóm. */
  loaiLam: { ma: string; nhan: string; icon: string; mo_ta: string; nhom: string;
             lean: string; tat: string | false }[]
  xoa: () => void
  nhanBan: () => void
  hoanTac: () => void
  lamLai: () => void
  gomHatNhan: () => void
  taHatNhan: () => void
  luu: () => void
  luuThanh: () => void
  mo: () => void
  moi: () => void
}

export default function Ribbon({ v, soChon, trongHatNhan, coHoanTac, coLamLai }: {
  v: ViecRibbon; soChon: number; trongHatNhan: boolean
  coHoanTac: boolean; coLamLai: boolean
}) {
  return (
    <div className="ribbon">
      <Nhom ten="Thêm khối">
        <Nut ten="Bắt đầu" icon="start" onClick={v.themBatDau} />
        <Nut ten="Nhóm" icon="group" onClick={v.themNhom}
             title="Một chuỗi hành động gói vào một hộp — chạy thẳng một lượt" />
        <Nut ten="Quay về" icon="quay-ve" onClick={v.themQuayVe}
             title="Nhảy ngược về một khối phía trước — khối trụ để vẽ vòng lặp" />
      </Nhom>

      {/* NĂM LOẠI CÂU HỎI, mỗi loại một nút riêng. Không gộp thành một nút "Hỏi" rồi
          bắt chọn loại trong hộp thoại: chọn loại là quyết định ĐẦU TIÊN, mà nó cũng
          quyết luôn hộp thoại bày ra cái gì. */}
      <Nhom ten="Xác nhận">
        {v.loaiHoi.map(l => (
          <Nut key={l.ma} ten={l.nhan.replace('Hỏi ', '')} icon={l.icon}
               onClick={() => v.themHoi(l.ma)}
               title={l.tat ? `${l.mo_ta} — ${l.tat}` : l.mo_ta} />
        ))}
      </Nhom>

      {/* HAI NHÓM HÀNH ĐỘNG, tên nhóm do Python quyết (`lam.NHOM_*`). Tám nút một
          hàng thì ribbon dài quá khổ cửa sổ, mà chúng cũng khác hẳn nhau: năm cái
          ĐỤNG VÀO thị trưồng, ba cái chỉ ghi ra ngoài. Nhóm sau ẩn đi khi cửa sổ hẽp. */}
      {[...new Set(v.loaiLam.map(l => l.nhom))].map((ten, i) => (
        <Nhom key={ten} ten={ten} hienTu={i === 0 ? undefined : HIEN_TU.ghiBao}>
          {v.loaiLam.filter(l => l.nhom === ten).map(l => (
            <Nut key={l.ma} ten={l.nhan} icon={l.icon}
                 onClick={() => v.themLam(l.ma)}
                 title={l.tat ? `${l.mo_ta} — ${l.tat}` : `${l.mo_ta}  ·  ${l.lean}`} />
          ))}
        </Nhom>
      ))}

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

      <Nhom ten="Hoàn tác" hienTu={HIEN_TU.hoanTac}>
        <Nut ten="Hoàn tác" icon="undo" onClick={v.hoanTac} tat={!coHoanTac} />
        <Nut ten="Làm lại" icon="redo" onClick={v.lamLai} tat={!coLamLai} />
      </Nhom>

      <Nhom ten="Strategy" hienTu={HIEN_TU.strategy}>
        <Nut ten="Mới" icon="file" onClick={v.moi} />
        <Nut ten="Kho" icon="folder" onClick={v.mo}
             title="Kho Strategy — mở, đổi tên, nhân bản, xoá" />
        <Nut ten="Lưu" icon="save" onClick={v.luu} />
        <Nut ten="Lưu thành…" icon="copy" onClick={v.luuThanh}
             title="Lưu thành một Strategy mới, giữ nguyên bản đang mở" />
      </Nhom>
    </div>
  )
}
