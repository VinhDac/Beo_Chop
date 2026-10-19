import { tr, trx } from '../ngon_ngu'

/** Ô CHỌN MÃ — danh sách rút từ KHỐI BẮT ĐẦU, không cho gõ tay.
 *
 *  ⚠ VÌ SAO KHÔNG CHO GÕ. Gõ tay thì gõ sai, mà cái sai ấy chỉ lộ ra lúc bấm Build:
 *  `_sym_py` của bộ sinh mã báo «điều kiện trỏ tới mã "SPT" mà khối Bắt đầu chưa khai
 *  nó». Luật đã có sẵn trong lõi từ lâu — chỗ này chỉ thôi bày ra cái cửa cho người
 *  ta đi sai. Không gõ được mã lạ thì không có lỗi ấy nữa.
 *
 *  Một nguồn DUY NHẤT: khối Bắt đầu. Khai thêm mã ở đó là mọi ô chọn trong sơ đồ tự
 *  có ngay, không phải sửa chỗ nào khác.
 */
export default function ChonMa({ ds, giaTri, coMaDangXet = true, onDoi }: {
  /** Mã khối Bắt đầu đang khai. */
  ds: string[]
  giaTri?: string
  /** Chạy MỘT LƯỢT cho cả rổ thì không có «mã đang xét» — đừng bày lựa chọn ấy ra. */
  coMaDangXet?: boolean
  onDoi: (ma: string) => void
}) {
  const v = giaTri ?? ''
  // Mã đã lưu mà nay khối Bắt đầu không còn khai (xoá mã, mở sơ đồ cũ) vẫn phải hiện
  // ra — nếu không thì ô lặng lẽ nhảy sang mã khác và người dùng không hề hay biết.
  const lac = v && !ds.includes(v)

  if (!ds.length) {
    return (
      <span className="chon-ma rong">
        {tr('khối Bắt đầu chưa khai mã nào')}
      </span>
    )
  }
  return (
    <select className="o chon-ma" value={v}
            onChange={e => onDoi(e.target.value)}>
      {coMaDangXet && <option value="">{tr('(mã đang xét)')}</option>}
      {!coMaDangXet && !v && <option value="">{tr('— chọn mã —')}</option>}
      {ds.map(m => <option key={m} value={m}>{m}</option>)}
      {lac && <option value={v}>{trx('{0} — không còn trong khối Bắt đầu', v)}</option>}
    </select>
  )
}
