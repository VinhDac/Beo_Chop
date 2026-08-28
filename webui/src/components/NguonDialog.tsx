import { useCallback, useEffect, useRef, useState } from 'react'
import { py } from '../api'
import type { BoNguon, TrangThaiGhi } from '../types'
import Modal from './Modal'

/** NGUỒN DỮ LIỆU — hộp thoại RIÊNG, không nhét vào Cài đặt.
 *
 * Tách ra vì hai thứ khác hẳn nhau: Cài đặt là thứ đặt một lần rồi quên (mã mặc định,
 * màu nhấn), còn đây là một **bảng điều khiển sống** — bộ ghi đang chạy hay chết, dữ
 * liệu dày lên tới đâu, có lỗ hổng nào không. Nhét chung thì mỗi lần muốn liếc xem bộ
 * ghi còn sống lại phải đi qua một hộp thoại nói về màu sắc.
 *
 * ⚠ APP KHÔNG SỞ HỮU BỘ GHI. Nó là tiến trình riêng, phải sống 24/7 kể cả khi app
 * đóng — đúng bài học cửa sổ Live cũ đã trả giá: *"đóng cửa sổ không được dừng phiên"*.
 * Nên hộp thoại này chỉ **nhìn** (qua nhịp tim) và **xin** (qua cờ dừng); đóng nó,
 * đóng cả app, bộ ghi vẫn chạy tiếp.
 *
 * TỰ LÀM MỚI mỗi 3 giây khi đang mở. Một bảng điều khiển đứng hình là bảng nói dối:
 * bộ ghi chết lúc 3 giờ sáng mà đèn vẫn xanh thì thà đừng có đèn.
 */

const NHIP_LAM_MOI = 3000

function gio(ms: number | null) {
  if (!ms) return '—'
  return new Date(ms).toLocaleString('vi', { hour12: false })
}

/** `2026-08-28` → `28/08`. Bảng hẹp, mà năm thì gần như luôn giống nhau. */
function ngay(s: string) {
  const p = s.split('-')
  return p.length === 3 ? `${p[2]}/${p[1]}` : s
}

export default function NguonDialog({ onDong }: { onDong: () => void }) {
  const [ds, setDs] = useState<BoNguon[]>([])
  const [ghi, setGhi] = useState<TrangThaiGhi | null>(null)
  const [thuMuc, setThuMuc] = useState('')
  const [nhap, setNhap] = useState('')
  const [loi, setLoi] = useState('')
  const [dangCho, setDangCho] = useState(false)
  /** Đã nạp lần đầu chưa — để phân biệt "chưa có dữ liệu" với "chưa hỏi xong". Hai
   *  thứ đó trông giống nhau trên màn hình mà nghĩa khác hẳn. */
  const daNap = useRef(false)
  const [sanSang, setSanSang] = useState(false)

  const lamMoi = useCallback(async () => {
    const r = await py.nguon_liet_ke()
    if (!r.ok || !r.value) { setLoi(r.error ?? 'không đọc được nguồn'); return }
    setDs(r.value.ds)
    setGhi(r.value.ghi)
    setThuMuc(r.value.thu_muc)
    if (!daNap.current) { daNap.current = true; setSanSang(true) }
  }, [])

  useEffect(() => {
    void lamMoi()
    const h = setInterval(() => void lamMoi(), NHIP_LAM_MOI)
    return () => clearInterval(h)
  }, [lamMoi])

  async function batDau() {
    // Tách bằng dấu phẩy HOẶC khoảng trắng: người ta dán từ đâu cũng được, và bắt họ
    // nhớ đúng một dấu phân cách là bắt nhớ một thứ máy đoán được.
    const syms = nhap.split(/[\s,]+/).map(s => s.trim().toUpperCase()).filter(Boolean)
    if (!syms.length) { setLoi('Gõ ít nhất một symbol.'); return }
    setLoi(''); setDangCho(true)
    const r = await py.nguon_bat_dau(syms)
    setDangCho(false)
    if (!r.ok) { setLoi(r.error ?? 'không mở được bộ ghi'); return }
    setNhap('')
    // Bộ ghi cần một nhịp mới đập lần đầu — đợi rồi hãy hỏi, không thì hộp thoại báo
    // "chưa chạy" ngay sau khi vừa bấm Bắt đầu và trông như nút hỏng.
    setTimeout(() => void lamMoi(), 1200)
  }

  async function dung() {
    setLoi(''); setDangCho(true)
    const r = await py.nguon_dung()
    setDangCho(false)
    if (!r.ok) { setLoi(r.error ?? 'không dừng được'); return }
    setLoi('Đã xin dừng — bộ ghi xả nốt đệm rồi thoát, mất vài giây.')
  }

  async function xoa(sym: string, mb: number) {
    if (!confirm(`Xoá HẲN ${mb} MB dữ liệu của ${sym}?\n\n`
                 + 'Ghi lại thì phải chờ từ đầu — dữ liệu quá khứ không mua lại được.')) return
    const r = await py.nguon_xoa(sym)
    if (!r.ok) { setLoi(r.error ?? 'không xoá được'); return }
    setDs(r.value?.ds ?? [])
  }

  const tongMb = ds.reduce((s, d) => s + d.mb, 0)

  return (
    <Modal title="Nguồn dữ liệu" width={720} onClose={onDong}
           footer={<button className="nut" onClick={onDong}>Đóng</button>}>

      {/* ---- BỘ GHI ---- */}
      <div className={'ng-ghi' + (ghi?.song ? ' song' : '')}>
        <span className="ng-den" />
        {ghi?.song ? (
          <>
            <b>Đang ghi</b>
            <span className="mono">{ghi.symbols.join(' · ')}</span>
            <span className="phu">từ {gio(ghi.bat_dau)} · nhịp {ghi.tuoi_nhip}s trước</span>
            <button className="nut nho" onClick={dung} disabled={dangCho}>Dừng</button>
          </>
        ) : (
          <>
            <b>Bộ ghi không chạy</b>
            <span className="phu">
              {sanSang ? 'Mỗi giờ không ghi là một giờ lịch sử không lấy lại được.' : '…'}
            </span>
          </>
        )}
      </div>

      <div className="hang">
        <span className="nhan-o">Ghi symbol</span>
        <input className="o" value={nhap} spellCheck={false}
               placeholder="TRUMPUSDT PUMPUSDT"
               onChange={e => setNhap(e.target.value)}
               onKeyDown={e => { if (e.key === 'Enter') void batDau() }} />
        <button className="nut" onClick={batDau} disabled={dangCho || !!ghi?.song}>
          Bắt đầu ghi
        </button>
      </div>

      <div className="chu-dan">
        Bộ ghi chạy trong một tiến trình <b>riêng</b>. Đóng hộp thoại này — đóng cả
        app — nó vẫn ghi tiếp. Dừng thì phải bấm Dừng.
      </div>

      {/* ---- DỮ LIỆU ĐÃ CÓ ---- */}
      <div className="ng-bang">
        <div className="ng-dau">Đã có trên đĩa</div>
        {!sanSang ? <div className="cd-rong">đang đọc…</div>
          : ds.length === 0 ? (
            <div className="cd-rong">
              chưa có dữ liệu nào — chưa backtest được gì
            </div>
          ) : (
            <table className="kho-bang">
              <thead>
                <tr>
                  <th>Symbol</th><th>Ngày</th><th>Dải</th>
                  <th>Sổ lệnh</th><th>Khớp</th>
                  <th>Dung lượng</th><th>Lỗ hổng</th><th>Trễ</th><th />
                </tr>
              </thead>
              <tbody>
                {ds.map(d => (
                  <tr key={d.symbol}>
                    <td><b>{d.symbol}</b></td>
                    <td className="mono">{d.so_ngay}</td>
                    <td className="mono">{ngay(d.tu_ngay)} → {ngay(d.den_ngay)}</td>
                    <td className="mono">{d.so_ban_ghi.so.toLocaleString('vi')}</td>
                    <td className="mono">{d.so_ban_ghi.khop.toLocaleString('vi')}</td>
                    <td className="mono">{d.mb.toLocaleString('vi')} MB</td>
                    {/* Lỗ hổng là thứ PHẢI nổi lên: nó quyết định backtest có tin được
                        không. 0 thì mờ đi, khác 0 thì đỏ. */}
                    <td className={'mono' + (d.so_lo_hong ? ' ng-canh' : '')}>
                      {d.so_lo_hong === 0 ? '—'
                        : `${d.so_lo_hong} · ${(d.ms_lo_hong / 1000).toFixed(0)}s`}
                    </td>
                    <td className="mono">{d.tre_ms == null ? '—' : `${d.tre_ms} ms`}</td>
                    <td>
                      <button className="nut nho" onClick={() => xoa(d.symbol, d.mb)}
                              disabled={!!ghi?.song && ghi.symbols.includes(d.symbol)}
                              title={ghi?.song && ghi.symbols.includes(d.symbol)
                                ? 'đang ghi symbol này — dừng bộ ghi trước'
                                : 'xoá hẳn'}>Xoá</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>

      {loi && <div className="chu-dan canh">{loi}</div>}

      <div className="chu-dan">
        {thuMuc && <><code>{thuMuc}</code> · </>}
        {tongMb.toLocaleString('vi')} MB · ước tính <b>~800 MB/ngày</b> cho mỗi symbol
        tầm trung.
      </div>
    </Modal>
  )
}
