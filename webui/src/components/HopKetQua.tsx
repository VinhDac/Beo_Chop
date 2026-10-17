import { useMemo, useState } from 'react'
import Modal from './Modal'
import Icon from './Icon'
import BangBieuDo from './BangBieuDo'
import { useKeoCao } from './BangDuoi'
import type { KetQuaChay } from '../types'

/** MÀN KẾT QUẢ — tám ô số, tám bảng biểu đồ bật tắt được, rồi các bảng chi tiết.
 *
 *  KHÔNG TÍNH GÌ CẢ. LEAN chạy xong ghi ra file đã có sẵn tám biểu đồ nó tự dựng,
 *  tám con số tổng, 27 thống kê, bảng thống kê trượt theo tháng, danh sách lệnh và
 *  giao dịch. Màn này chỉ bày ra — đúng lời hứa D-11 "app chỉ là VỎ".
 *
 *  Bố cục dựng theo ảnh chụp trang backtest của QuantConnect mà chủ dự án đưa (lưu ở
 *  `tai_lieu/backtest/`): hàng ô số trên cùng, vùng biểu đồ bên trái, cột chọn bảng
 *  bên phải, các bảng chi tiết xếp tab phía dưới. Mã thì của ta, nền tối của ta.
 *
 *  BA THỨ CỐ Ý KHÔNG DỰNG, và nói rõ chứ không giả vờ quên:
 *    · **Research Guide** (đếm backtest còn lại, cảnh báo quá khớp) — dịch vụ đám mây
 *      của QuantConnect, đếm trên tài khoản của họ.
 *    · **Share Results** — chia sẻ lên web của họ.
 *    · **Report** — bản báo cáo có logo và bố cục riêng của họ.
 */

/** Tám ô số, theo đúng tên LEAN ghi trong `runtimeStatistics`, kèm chữ Việt. */
const O_SO: [string, string][] = [
  ['Equity', 'Vốn'],
  ['Fees', 'Phí'],
  ['Holdings', 'Đang giữ'],
  ['Net Profit', 'Lãi ròng'],
  ['Probabilistic Sharpe Ratio', 'PSR'],
  ['Return', 'Lợi suất'],
  ['Unrealized', 'Chưa chốt'],
  ['Volume', 'Khối lượng'],
]

/** Dấu của con số quyết màu — không phải cái tên. */
function huong(gt: string) {
  const n = parseFloat(String(gt).replace(/[^0-9.-]/g, ''))
  if (!Number.isFinite(n) || n === 0) return ''
  return n > 0 ? ' tot' : ' xau'
}

function so(n: unknown, le = 2) {
  const v = typeof n === 'number' ? n : parseFloat(String(n))
  return Number.isFinite(v)
    ? v.toLocaleString('vi-VN', { maximumFractionDigits: le })
    : String(n ?? '')
}

/** RUỘT màn Kết quả — mọi thứ TRỪ cái vỏ.
 *
 *  Tách ra vì nay có HAI vỏ: hộp thoại trong cửa sổ chính, và một CỬA SỔ RIÊNG cho
 *  mỗi lượt chạy (`TrangKetQua`) — để xếp hai phiên bản cạnh nhau mà so. Hai bản
 *  chép tay thì sớm muộn một bên có tab mà bên kia không. */
export function RuotKetQua({ kq }: { kq: KetQuaChay }) {
  const [tab, setTab] = useState<'tong_quan' | 'lenh' | 'giao_dich' | 'nhat_ky' | 'ma'>(
    'tong_quan')
  const [hien, setHien] = useState<Record<string, boolean>>(() =>
    Object.fromEntries((kq.bieu_do ?? []).map(b => [b.ten, b.hien])))
  const [chiTieu, setChiTieu] = useState('sharpeRatio')
  /* CỤM TAB DƯỚI KÉO ĐƯỢC, đúng cảm giác bảng Vấn đề/Nhật ký của cửa sổ chính —
     dùng CHÍNH bộ kéo của nó (`useKeoCao`), không chép lại. Bảng Lệnh có lúc 5 dòng
     có lúc 600; chiều cao cố định thì lúc nào cũng sai một trong hai. */
  const [caoDuoi, setCaoDuoi] = useState(260)
  const batKeo = useKeoCao(caoDuoi, setCaoDuoi)

  const oSo = kq.o_so ?? {}
  const tk = kq.thong_ke ?? {}
  const lenh = kq.lenh ?? []
  const hong = lenh.filter(l => !l.hop_le).length

  /** Thống kê xếp hai cột, như bản web — 27 dòng một cột thì phải cuộn mãi. */
  const haiCot = useMemo(() => {
    const ds = Object.entries(tk)
    const nua = Math.ceil(ds.length / 2)
    return [ds.slice(0, nua), ds.slice(nua)]
  }, [tk])

  const cuon = kq.cuon
  const coCuon = !!cuon?.dong?.length

  return (
    <div className="man-kq">
        {/* ⚠ Mọi lệnh bị từ chối mà backtest vẫn báo đủ thống kê — bẫy đã gặp thật
            (sàn không nhận lệnh «khớp lúc đóng cửa»). Nói ngay trên đầu. */}
        {hong > 0 && (
          <div className="mc-bao loi">
            ⚠ {hong}/{lenh.length} lệnh <b>KHÔNG HỢP LỆ</b> — sàn từ chối. Mọi con số
            phía dưới vì thế gần như vô nghĩa. Mở tab <b>Lệnh</b> xem lý do.
          </div>
        )}

        <div className="o-lon">
          {O_SO.filter(([k]) => k in oSo).map(([k, nhan]) => (
            <div className={'o-so-lon' + huong(oSo[k])} key={k}>
              <b>{oSo[k]}</b>
              <span>{nhan}</span>
            </div>
          ))}
        </div>

        <div className="kq-giua">
          <div className="kq-bieu-do">
            {(kq.bieu_do ?? []).filter(b => hien[b.ten]).map(b => (
              <BangBieuDo key={b.ten} ten={b.ten} duong={b.duong}
                          onDong={() => setHien(h => ({ ...h, [b.ten]: false }))} />
            ))}
            {!(kq.bieu_do ?? []).some(b => hien[b.ten]) && (
              <div className="bang-bd mo">Chưa bật bảng nào — chọn ở cột bên phải.</div>
            )}
          </div>

          <div className="kq-ben">
            <div className="kq-hop">
              <div className="kq-hop-dau">Chọn biểu đồ</div>
              {(kq.bieu_do ?? []).map(b => (
                <label className="kq-chon" key={b.ten}>
                  <input type="checkbox" checked={!!hien[b.ten]}
                         onChange={e =>
                           setHien(h => ({ ...h, [b.ten]: e.target.checked }))} />
                  {b.ten}
                </label>
              ))}
            </div>

            {kq.may_chu && Object.keys(kq.may_chu).length > 0 && (
              <div className="kq-hop">
                <div className="kq-hop-dau">Máy chạy</div>
                {Object.entries(kq.may_chu).map(([k, v]) => (
                  <div className="kq-doi" key={k}><span>{k}</span><b>{v}</b></div>
                ))}
              </div>
            )}

            {kq.thu_muc && (
              <div className="kq-hop">
                <div className="kq-hop-dau">File kết quả</div>
                <div className="kq-duong">{kq.thu_muc}</div>
              </div>
            )}
          </div>
        </div>

        {/* Tay kéo nằm NGAY TRÊN hàng tab — chỗ mắt đã nhìn khi muốn xem bảng dưới. */}
        <div className="thanh-keo" onMouseDown={batKeo} />
        <div className="hang-tab">
          {([['tong_quan', 'Tổng quan'],
             ['lenh', `Lệnh (${lenh.length})`],
             ['giao_dich', `Giao dịch (${(kq.giao_dich ?? []).length})`],
             ['nhat_ky', 'Nhật ký'],
             ['ma', 'Mã']] as const).map(([m, n]) => (
            <button key={m} className={'nut-nho' + (tab === m ? ' chon' : '')}
                    onClick={() => setTab(m)}>{n}</button>
          ))}
        </div>

        <div className="than-tab" style={{ height: caoDuoi }}>
          {tab === 'tong_quan' && (
            <>
              <div className="tk-hai-cot">
                {haiCot.map((cot, i) => (
                  <table className="bang-kq" key={i}>
                    <tbody>
                      {cot.map(([k, v]) => (
                        <tr key={k}>
                          <td>{k}</td><td className="phai mono">{v}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ))}
              </div>

              {coCuon && (
                <>
                  <div className="hang-tab phu">
                    <b>Thống kê trượt</b>
                    <span className="day" />
                    <select className="o" value={chiTieu}
                            onChange={e => setChiTieu(e.target.value)}>
                      {cuon!.chi_tieu.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <table className="bang-kq">
                    <thead><tr>
                      <th>Chốt ngày</th>
                      <th className="phai">1 tháng</th><th className="phai">3 tháng</th>
                      <th className="phai">6 tháng</th><th className="phai">12 tháng</th>
                    </tr></thead>
                    <tbody>
                      {cuon!.dong.map(d => (
                        <tr key={d.ngay}>
                          <td className="mono">{d.ngay}</td>
                          {['1', '3', '6', '12'].map(c => (
                            <td className="phai mono" key={c}>
                              {so(d.cua[c]?.[chiTieu], 4)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </>
          )}

          {tab === 'lenh' && (
            <table className="bang-kq">
              <thead><tr>
                <th>#</th><th>Lúc</th><th>Mã</th><th>Loại</th>
                <th className="phai">Số lượng</th><th className="phai">Giá</th>
                <th>Trạng thái</th><th>Ghi chú đi kèm</th>
              </tr></thead>
              <tbody>
                {lenh.map(l => (
                  <tr key={String(l.id)} className={l.hop_le ? '' : 'hong'}>
                    <td>{String(l.id)}</td>
                    <td className="mono">{l.luc}</td>
                    <td>{l.ma}</td>
                    <td>{l.loai}</td>
                    <td className="phai mono">{so(l.so_luong)}</td>
                    <td className="phai mono">{so(l.gia)}</td>
                    <td>{l.trang_thai}</td>
                    <td className="mono nho">{l.tag}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {tab === 'giao_dich' && (
            <table className="bang-kq">
              <thead><tr>
                <th>Mã</th><th>Vào</th><th className="phai">Giá vào</th>
                <th>Ra</th><th className="phai">Giá ra</th>
                <th className="phai">Số lượng</th><th className="phai">Phí</th>
                <th className="phai">Lãi/lỗ</th>
              </tr></thead>
              <tbody>
                {(kq.giao_dich ?? []).map((g, i) => (
                  <tr key={i}>
                    <td>{g.ma}</td>
                    <td className="mono">{g.vao_luc}</td>
                    <td className="phai mono">{so(g.gia_vao)}</td>
                    <td className="mono">{g.ra_luc}</td>
                    <td className="phai mono">{so(g.gia_ra)}</td>
                    <td className="phai mono">{so(g.so_luong)}</td>
                    <td className="phai mono">{so(g.phi)}</td>
                    <td className={'phai mono ' + (g.thang ? 'tot' : 'xau')}>
                      {so(g.lai_lo)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {tab === 'nhat_ky' && <pre className="ma-lean">{kq.nhat_ky || '(trống)'}</pre>}

          {/* Tab Mã bày ĐÚNG file vừa chạy, không sinh lại một bản khác rồi bảo là nó. */}
          {tab === 'ma' && <pre className="ma-lean">{kq.ma || '(trống)'}</pre>}
      </div>
    </div>
  )
}

export default function HopKetQua({ kq, onDong, onChayLai }: {
  kq: KetQuaChay
  onDong: () => void
  onChayLai: () => void
}) {
  return (
    <Modal title={`Kết quả — ${kq.ten_lop ?? ''}`} width={1180} onClose={onDong}
           footer={<>
             <span className="day" />
             <button className="nut" onClick={onDong}>Đóng</button>
             <button className="nut chinh" onClick={onChayLai}>
               <Icon name="chay" /> Chạy lại
             </button>
           </>}>
      <RuotKetQua kq={kq} />
    </Modal>
  )
}
