import type { ReactNode } from 'react'
import IconNet from './Icon'
import NutMenu from './NutMenu'

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
 *  SỐ ĐO THẬT, không chọn cho tròn (luật của Jenifer_Studio). Đo bề ngang từng nhóm
 *  trong trình duyệt rồi CỘNG DỒN từ cái luôn hiện:
 *      sàn = Thêm khối 374 + Cỗ máy 332 + lề 8 = 714
 *      + Hạt nhân 137 -> 851   + Strategy 198 -> 1049
 *      + Sửa 147      -> 1196  + Hoàn tác 143 -> 1339
 *  Làm tròn lên một chút cho có chỗ thở. Cả dải là 1339px, vừa cửa sổ mặc định
 *  1360px — nên ở cỡ mặc định KHÔNG nhóm nào phải ẩn. Sàn cửa sổ là 1020px
 *  (`app_web.py min_size`), nên Hạt nhân thực tế chẳng bao giờ ẩn.
 *
 *  THỨ TỰ ẨN theo "còn đường nào khác không", đúng luật *ẩn một nhóm KHÔNG được lấy
 *  mất việc gì*: Hoàn tác đi trước (Ctrl+Z), rồi Sửa (Ctrl+D/Delete + menu chuột
 *  phải), rồi Strategy (Ctrl+N/O/S). Hạt nhân đi SAU CÙNG vì từ khi Ctrl+G thành của
 *  Nhóm thì nó chỉ còn hai đường: ribbon và menu chuột phải.
 *
 *  Nhóm nào đổi bề ngang thì đo lại cả bảng — và nhớ `@media` tương ứng ở `app.css`.
 *
 *  MỘT BẢNG DUY NHẤT, vì mỗi số ở đây phải có một `@media (max-width: <số-1>px)
 *  .hien-tu-<số>` trong `app.css`. Thiếu dòng CSS thì lớp sinh ra CHẲNG ẨN GÌ CẢ:
 *  không lỗi, không cảnh báo, `tsc` sạch, build sạch — chỉ có ribbon tràn ngang và
 *  nhãn các nút đè lên nhau ở cửa sổ hẹp. (Đã hỏng thật với 1090 và 1250, suốt từ đầu.)
 *  `test_giao_dien` đọc đúng bảng này rồi đối chiếu với `app.css`. */
const HIEN_TU = { hatNhan: 860, strategy: 1060, sua: 1200, hoanTac: 1345 }

function Nhom({ ten, children, hienTu, chinh }: {
  ten: string; children: ReactNode; hienTu?: number
  /** Nhóm CHÍNH: đẩy sát mép phải và tô sáng. Đúng một nhóm được mang cờ này. */
  chinh?: boolean
}) {
  return (
    <div className={'nhom-ribbon' + (hienTu ? ` hien-tu-${hienTu}` : '')
                    + (chinh ? ' chinh' : '')}>
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
  /** Sinh thuật toán LEAN từ sơ đồ đang vẽ. */
  sinhMa: () => void
  /** Sinh rồi chạy backtest luôn. */
  chay: () => void
  /** Mở lại kết quả lượt vừa chạy. */
  moKetQua: () => void
  /** Đã có kết quả để mở chưa. */
  coKetQua: boolean
  /** Đang chạy backtest — khoá nút lại. */
  dangChay: boolean
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
      {/* ⚠ HAI VÙNG, không phải một hàng. Nhóm phải được GHIM, không phải đẩy bằng
          `margin-left: auto` — đẩy thì chỉ ăn khi CÒN CHỖ TRỐNG, mà ribbon này có bảy
          nhóm nên nó luôn dài hơn cửa sổ: cụm chính bị trôi hẳn ra ngoài màn hình.
          Nay phần trái tự cuộn, phần phải đứng im. */}
      <div className="ribbon-cuon">
      {/* MỘT NHÓM DUY NHẤT CHO VIỆC «THẢ MỘT KHỐI XUỐNG» — năm slot, như Jenifer.
          Trước đây mười ba nút rải thành ba nhóm, mà cả mười ba cùng làm đúng một
          việc ấy; ribbon dài hơn cửa sổ và nhãn thì cụt thành "thị trường", "vị thế"
          — danh từ không có động từ, phải đọc tên nhóm mới hiểu.

          ⚠ Chỗ này từng có một lời biện hộ, nay đã HẾT HIỆU LỰC: *"chọn loại là
          quyết định ĐẦU TIÊN, mà nó cũng quyết luôn hộp thoại bày ra cái gì"*. Đúng
          hồi năm họ câu hỏi còn là tường ngăn. Nay cả 68 đại lượng nằm chung một kho
          và họ nào cũng với tới được từ bất kỳ khối nào, nên chọn họ không còn quyết
          cái gì nữa — nó chỉ là «mở sẵn ở mục này». Một lời biện hộ sống lâu hơn cái
          lý của nó thì nguy hơn là không có lời nào. */}
      <Nhom ten="Thêm khối">
        <Nut ten="Bắt đầu" icon="start" onClick={v.themBatDau}
             title="Khối thiết lập: mã, khoảng ngày, vốn, nhịp chạy, sàn" />
        <NutMenu ten="Xác nhận" icon="branch"
                 title="Thêm một cổng rẽ nhánh — hỏi một câu về thế giới rồi rẽ"
                 muc={v.loaiHoi.map(l => ({
                   nhan: l.nhan, phu: l.mo_ta, icon: l.icon, tat: l.tat,
                   chay: () => v.themHoi(l.ma),
                 }))} />
        <NutMenu ten="Hành động" icon="action"
                 title="Thêm một việc sẽ làm với thị trường, hoặc một dòng ghi ra ngoài"
                 dauMuc={(m, i) => {
                   const n = v.loaiLam[i]?.nhom
                   return i === 0 || n !== v.loaiLam[i - 1]?.nhom ? n : undefined
                 }}
                 muc={v.loaiLam.map(l => ({
                   // Dòng phụ là HÀM LEAN nó sẽ gọi — cùng lời hứa như `.lean-khai`
                   // của hộp thoại: mỗi khối là một thứ có thật, kiểm được ngay ở đây.
                   nhan: l.nhan, phu: l.lean, icon: l.icon, tat: l.tat,
                   chay: () => v.themLam(l.ma),
                 }))} />
        <Nut ten="Nhóm" icon="group" onClick={v.themNhom}
             title="Một chuỗi hành động gói vào một hộp — chạy thẳng một lượt (Ctrl+G gom khối đang chọn)" />
        <Nut ten="Quay về" icon="quay-ve" onClick={v.themQuayVe}
             title="Nhảy ngược về một khối phía trước — khối trụ để vẽ vòng lặp" />
      </Nhom>

      <Nhom ten="Sửa" hienTu={HIEN_TU.sua}>
        <Nut ten="Nhân bản" icon="copy" onClick={v.nhanBan} tat={!soChon} title="Ctrl+D" />
        <Nut ten="Xoá" icon="trash" onClick={v.xoa} tat={!soChon} title="Delete" />
      </Nhom>

      {/* HẠT NHÂN KHÔNG CÒN CỤM PHÍM NÀO (Ctrl+G nay là của Nhóm, như Jenifer), nên
          ribbon và menu chuột phải là hai đường duy nhất — ẩn nhóm này sau cùng. */}
      <Nhom ten="Hạt nhân" hienTu={HIEN_TU.hatNhan}>
        <Nut ten="Gom" icon="frame" onClick={v.gomHatNhan} tat={soChon < 2 || trongHatNhan}
             title="Gói các khối đang chọn thành một khung — CHỈ là cách nhìn, sơ đồ không đổi" />
        <Nut ten="Tách" icon="unlink" onClick={v.taHatNhan} tat={!soChon}
             title="Đưa các khối đang chọn ra khỏi hạt nhân của chúng" />
      </Nhom>

      <Nhom ten="Hoàn tác" hienTu={HIEN_TU.hoanTac}>
        <Nut ten="Hoàn tác" icon="undo" onClick={v.hoanTac} tat={!coHoanTac} title="Ctrl+Z" />
        <Nut ten="Làm lại" icon="redo" onClick={v.lamLai} tat={!coLamLai} title="Ctrl+Y" />
      </Nhom>

      <Nhom ten="Strategy" hienTu={HIEN_TU.strategy}>
        <Nut ten="Mới" icon="file" onClick={v.moi} title="Ctrl+N" />
        <Nut ten="Kho" icon="folder" onClick={v.mo}
             title="Kho Strategy — mở, đổi tên, nhân bản, xoá (Ctrl+O)" />
        <NutMenu ten="Lưu" icon="save" title="Ctrl+S"
                 muc={[{ nhan: 'Lưu', phu: 'Ctrl+S — ghi đè bản đang mở',
                         icon: 'save', chay: v.luu },
                       { nhan: 'Lưu thành…', phu: 'một Strategy mới, giữ nguyên bản đang mở',
                         icon: 'copy', chay: v.luuThanh }]} />
      </Nhom>

      {/* CỤM CHÍNH — đẩy SÁT MÉP PHẢI và tô sáng. Đây là ĐẦU RA của cả việc vẽ, không
          phải một thao tác sửa, nên nó không được lẫn vào hàng nút sửa. Xếp theo đúng thứ
          tự việc: sinh -> chạy -> tối ưu -> thật -> đọc, giống thanh của QuantConnect. */}
      </div>

      {/* TÊN TIẾNG ANH, cố ý: đây là thuật ngữ chuẩn của nghề — Build, Backtest,
          Optimize, Live — và là đúng chữ người trong nghề đọc trên bất cứ nền nào
          khác. Dịch ra tiếng Việt thì phải học lại khi sang QuantConnect. Nghĩa tiếng
          Việt nằm ở chú giải khi rê chuột. */}
      <Nhom ten="Cỗ máy" chinh>
        <Nut ten="Build" icon="gear" onClick={v.sinhMa}
             title="Build — sơ đồ này thành thuật toán LEAN Python, xem trước rồi lưu ra file" />
        <Nut ten="Backtest" icon="chay" onClick={v.chay} tat={v.dangChay}
             title="Backtest — chạy thử trên dữ liệu quá khứ bằng LEAN trên máy này" />
        <Nut ten="Optimize" icon="branch" tat
             title="Optimize — quét tham số tìm bộ tốt nhất. CHƯA CÓ: cần mở ô số cho gõ tên tham số trước." />
        <Nut ten="Live" icon="an-lenh" tat
             title="Live — giao dịch bằng tiền thật. CHƯA CÓ: cần tài khoản sàn." />
        <Nut ten="Results" icon="kieu-line" onClick={v.moKetQua} tat={!v.coKetQua}
             title="Results — mở lại kết quả lượt backtest vừa rồi" />
      </Nhom>
    </div>
  )
}
