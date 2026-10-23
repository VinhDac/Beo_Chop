import type { ReactNode } from 'react'
import IconNet from './Icon'
import NutMenu from './NutMenu'
import { tr } from '../ngon_ngu'

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
 *      sàn = Thêm khối 373 + Cỗ máy 331 + lề 8 = 712
 *      + Hạt nhân 137 -> 849   + Strategy 136 -> 985
 *      + Sửa 147      -> 1132  + Hoàn tác 143 -> 1275
 *  Làm tròn lên một chút cho có chỗ thở. Cả dải là 1275px, vừa cửa sổ mặc định
 *  1360px — nên ở cỡ mặc định KHÔNG nhóm nào phải ẩn. Sàn cửa sổ là 1020px
 *  (`app_web.py min_size`), nên Hạt nhân thực tế chẳng bao giờ ẩn.
 *
 *  ⚠ ĐO LẠI NGÀY 18/10/2026, sau khi Strategy bỏ hai nút «Mới» và «Cài đặt»: nhóm ấy
 *  hẹp đi 62px (198 -> 136), nên BA ngưỡng sau nó đều tụt theo. Không đo lại thì ba
 *  nhóm ấy ẩn sớm hơn cần thiết — cửa sổ còn thừa cả trăm pixel mà nút đã biến mất,
 *  và không ai biết vì sao.
 *
 *  THỨ TỰ ẨN theo "còn đường nào khác không", đúng luật *ẩn một nhóm KHÔNG được lấy
 *  mất việc gì*: Hoàn tác đi trước (Ctrl+Z), rồi Sửa (Ctrl+D/Delete + menu chuột
 *  phải), rồi Strategy (Ctrl+N/O/S). Hạt nhân đi SAU CÙNG vì từ khi Ctrl+G thành của
 *  Nhóm thì nó chỉ còn hai đường: ribbon và menu chuột phải.
 *
 *  Nhóm nào đổi bề ngang thì đo lại cả bảng — và nhớ `@media` tương ứng ở `app.css`.
 *
 *  ⚠ ĐO LẠI NGÀY 19/10/2026, lúc app thành SONG NGỮ — và phải đo CẢ HAI TIẾNG, vì
 *  bảng này chỉ đúng nếu nó đủ cho tiếng RỘNG HƠN:
 *                 Thêm khối  Sửa  Hạt nhân  Hoàn tác  Strategy  Cỗ máy   tổng
 *      tiếng Việt      373   147       137       142       136     331   1266
 *      tiếng Anh       354   145       137       137       136     331   1240
 *  Tiếng Việt rộng hơn ở mọi nhóm, nên BẢNG GIỮ NGUYÊN theo số tiếng Việt: ở tiếng
 *  Anh nhóm ẩn sớm hơn cần một chút (ngưỡng thật chỉ cần 830 · 966 · 1111 · 1248),
 *  mà ẩn sớm thì chỉ mất một nhóm còn đường khác, còn ẩn muộn là ribbon tràn ngang.
 *  Đừng hạ bảng này theo số tiếng Anh: hạ xuống là bản tiếng Việt tràn.
 *
 *  MỘT BẢNG DUY NHẤT, vì mỗi số ở đây phải có một `@media (max-width: <số-1>px)
 *  .hien-tu-<số>` trong `app.css`. Thiếu dòng CSS thì lớp sinh ra CHẲNG ẨN GÌ CẢ:
 *  không lỗi, không cảnh báo, `tsc` sạch, build sạch — chỉ có ribbon tràn ngang và
 *  nhãn các nút đè lên nhau ở cửa sổ hẹp. (Đã hỏng thật với 1090 và 1250, suốt từ đầu.)
 *  `test_giao_dien` đọc đúng bảng này rồi đối chiếu với `app.css`. */
const HIEN_TU = { hatNhan: 860, strategy: 1000, sua: 1145, hoanTac: 1290 }

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

function Nut({ ten, icon, onClick, tat, title, lop }: {
  ten: string; icon: string; onClick?: () => void; tat?: boolean; title?: string
  lop?: string
}) {
  return (
    <button className={'nut-lon' + (lop ? ` ${lop}` : '')} onClick={onClick}
            disabled={tat} title={title ?? ten}>
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
  /** Mở hộp Optimize — quét mấy núm đã ghim trên sơ đồ. */
  toiUu: () => void
  /** Dừng lượt đang chạy — giết thẳng tiến trình LEAN (F6). */
  dung: () => void
  /** Mở lại kết quả lượt vừa chạy. */
  moKetQua: () => void
  moView: () => void
  /** Đã có kết quả để mở chưa. */
  coKetQua: boolean
  coView: boolean
  /** Đang chạy backtest — khoá nút lại. */
  dangChay: boolean
  luu: () => void
  luuThanh: () => void
  mo: () => void
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
      <Nhom ten={tr('Thêm khối')}>
        <Nut ten={tr('Bắt đầu')} icon="start" onClick={v.themBatDau}
             title={tr('Khối thiết lập: mã, khoảng ngày, vốn, nhịp chạy, sàn')} />
        <NutMenu ten={tr('Xác nhận')} icon="branch"
                 title={tr('Thêm một cổng rẽ nhánh — hỏi một câu về thế giới rồi rẽ')}
                 muc={v.loaiHoi.map(l => ({
                   nhan: tr(l.nhan), phu: tr(l.mo_ta), icon: l.icon,
                   tat: l.tat && tr(l.tat),
                   chay: () => v.themHoi(l.ma),
                 }))} />
        <NutMenu ten={tr('Hành động')} icon="action"
                 title={tr('Thêm một việc sẽ làm với thị trường, hoặc một dòng ghi ra ngoài')}
                 dauMuc={(m, i) => {
                   const n = v.loaiLam[i]?.nhom
                   return i === 0 || n !== v.loaiLam[i - 1]?.nhom ? tr(n) : undefined
                 }}
                 muc={v.loaiLam.map(l => ({
                   // Dòng phụ là HÀM LEAN nó sẽ gọi — cùng lời hứa như `.lean-khai`
                   // của hộp thoại: mỗi khối là một thứ có thật, kiểm được ngay ở đây.
                   nhan: tr(l.nhan), phu: l.lean, icon: l.icon,
                   tat: l.tat && tr(l.tat),
                   chay: () => v.themLam(l.ma),
                 }))} />
        <Nut ten={tr('Nhóm')} icon="group" onClick={v.themNhom}
             title={tr('Một chuỗi hành động gói vào một hộp — chạy thẳng một lượt (Ctrl+G gom khối '
               + 'đang chọn)')} />
        <Nut ten={tr('Quay về')} icon="quay-ve" onClick={v.themQuayVe}
             title={tr('Nhảy ngược về một khối phía trước — khối trụ để vẽ vòng lặp')} />
      </Nhom>

      <Nhom ten={tr('Sửa')} hienTu={HIEN_TU.sua}>
        <Nut ten={tr('Nhân bản')} icon="copy" onClick={v.nhanBan} tat={!soChon} title="Ctrl+D" />
        <Nut ten={tr('Xoá')} icon="trash" onClick={v.xoa} tat={!soChon} title="Delete" />
      </Nhom>

      {/* HẠT NHÂN KHÔNG CÒN CỤM PHÍM NÀO (Ctrl+G nay là của Nhóm, như Jenifer), nên
          ribbon và menu chuột phải là hai đường duy nhất — ẩn nhóm này sau cùng. */}
      <Nhom ten={tr('Hạt nhân')} hienTu={HIEN_TU.hatNhan}>
        <Nut ten={tr('Gom')} icon="frame" onClick={v.gomHatNhan} tat={soChon < 2 || trongHatNhan}
             title={tr('Gói các khối đang chọn thành một khung — CHỈ là cách nhìn, sơ đồ không đổi')} />
        <Nut ten={tr('Tách')} icon="unlink" onClick={v.taHatNhan} tat={!soChon}
             title={tr('Đưa các khối đang chọn ra khỏi hạt nhân của chúng')} />
      </Nhom>

      <Nhom ten={tr('Hoàn tác')} hienTu={HIEN_TU.hoanTac}>
        <Nut ten={tr('Hoàn tác')} icon="undo" onClick={v.hoanTac} tat={!coHoanTac} title="Ctrl+Z" />
        <Nut ten={tr('Làm lại')} icon="redo" onClick={v.lamLai} tat={!coLamLai} title="Ctrl+Y" />
      </Nhom>

      <Nhom ten="Strategy" hienTu={HIEN_TU.strategy}>
        {/* ⚠ CHỈ CÒN KHO VÀ LƯU. «Mới» và «Cài đặt» đã bỏ khỏi ribbon: cả hai còn
            cửa khác, và ribbon là chỗ của việc làm HÀNG NGÀY.
              · Mới   -> menu File > «Strategy mới», và Ctrl+N
              · Cài đặt -> nút bánh răng ở thanh trạng thái, và Ctrl+,
            Bỏ một nút mà việc của nó mất luôn thì không được — xem luật thứ tự ẩn
            nhóm ở đầu file. Hai cái này không mất gì. */}
        <Nut ten={tr('Kho')} icon="folder" onClick={v.mo}
             title={tr('Kho Strategy — mở, đổi tên, nhân bản, xoá (Ctrl+O)')} />
        <NutMenu ten={tr('Lưu')} icon="save" title="Ctrl+S"
                 muc={[{ nhan: tr('Lưu'), phu: tr('Ctrl+S — ghi đè bản đang mở'),
                         icon: 'save', chay: v.luu },
                       { nhan: tr('Lưu thành…'), phu: tr('một Strategy mới, giữ nguyên bản đang mở'),
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
      <Nhom ten={tr('Cỗ máy')} chinh>
        <Nut ten="Build" icon="gear" onClick={v.sinhMa}
             title={tr('Build — sơ đồ này thành thuật toán LEAN Python, xem trước rồi lưu ra file')} />
        {/* MỘT Ô, HAI VIỆC. Đang chạy thì chỗ này là nút DỪNG — mắt người dùng
            đang ở đúng đây vì họ vừa bấm Backtest, nên đừng bắt đi tìm chỗ khác.
            Không chạy thì chẳng có gì để dừng, bày thêm một nút mờ là thừa. */}
        {v.dangChay
          ? <Nut ten={tr('Dừng')} icon="dung" lop="nut-dung" onClick={v.dung}
                 title={tr('Dừng lượt backtest đang chạy (F6)')} />
          : <Nut ten="Backtest" icon="chay" onClick={v.chay}
                 title={tr('Backtest — chạy thử trên dữ liệu quá khứ bằng LEAN trên máy này')} />}
        <Nut ten="Optimize" icon="branch" onClick={v.toiUu}
             title={tr('Optimize — quét mấy núm đã ghim trên sơ đồ, tìm bộ số tốt nhất')} />
        {/* CHỖ NÀY TRƯỚC LÀ «Live» — một nút chết, `tat` vĩnh viễn, với chú
            giải «CHƯA CÓ». Giao dịch thật vẫn chưa có, nhưng một cái nút không bấm
            được nằm giữa bốn cái sống thì mỗi lần nhìn là một lần vấp. Nay chỗ ấy
            làm việc thật. */}
        <Nut ten="View" icon="kieu-nen" onClick={v.moView} tat={!v.coView}
             title={tr('View — tua lại lượt vừa chạy, nến từng nến: lệnh nằm ở đâu, '
                       + 'và mấy đại lượng cỗ máy đọc lúc ấy bằng bao nhiêu')} />
        <Nut ten="Results" icon="kieu-line" onClick={v.moKetQua} tat={!v.coKetQua}
             title={tr('Results — mở lại kết quả lượt backtest vừa rồi')} />
      </Nhom>
    </div>
  )
}
