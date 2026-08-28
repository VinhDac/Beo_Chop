import { useCallback, useEffect, useRef, useState } from 'react'
import { py } from '../api'
import type { BoNguon, CaiDatNguon, DongThiTruong, TrangThaiGhi } from '../types'

/** NGUỒN DỮ LIỆU — một TAB trong Cài đặt.
 *
 * ⚠ Bản đầu làm nó thành hộp thoại RIÊNG ở File → Nguồn dữ liệu. Người dùng đi thẳng
 * vào **Cài đặt** tìm nó — và họ đúng: nguồn dữ liệu là một thiết lập, mắt tìm nó ở
 * chỗ mọi thiết lập khác nằm. Đã dời vào và bỏ hẳn cửa cũ.
 *
 * ⚠ Bản thứ hai chỉ có đèn báo + nút bật/tắt + một cái bảng — tức một **bảng điều
 * khiển**, không phải cài đặt: không có gì để chỉnh. Người dùng nói thẳng: *"cài đặt
 * như này thì làm gì có tác dụng"*. Đúng.
 *
 * BỐN Ô Ở ĐÂY LÀ BỐN CON SỐ DUY NHẤT CỦA NGUỒN MÀ CHỈNH VÀO LÀ ĐỔI THẬT:
 *
 *     thư mục        ~800 MB/ngày/symbol → 24 GB/tháng. Ổ C: không phải lúc nào cũng
 *                    chịu nổi, mà ổ đầy thì bộ ghi chết lúc 3 giờ sáng
 *     giữ N ngày     không đặt thì sớm muộn đĩa đầy
 *     ngưỡng im lặng thấp quá → lỗ hổng GIẢ; cao quá → ngồi mù mà tưởng đang chạy
 *     nhịp xả        "mất điện thì mất bao nhiêu"
 *
 * Mọi thứ CÒN LẠI về nguồn đều **đo được** — độ trễ, lệch đồng hồ, spread, khối lượng
 * — nên app tự đo và chỉ HIỆN RA. Hỏi một thứ đo được là mời người ta gõ một con số
 * sai rồi tin nó; đúng cái bẫy ô `spread = 20 points` của bản MT5 cũ.
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

export default function NguonPanel() {
  const [ds, setDs] = useState<BoNguon[]>([])
  const [ghi, setGhi] = useState<TrangThaiGhi | null>(null)
  const [thuMuc, setThuMuc] = useState('')
  const [cd, setCd] = useState<CaiDatNguon | null>(null)
  /** Bản nháp của bốn ô. Tách khỏi `cd` để gõ dở dang không bị vòng làm mới 3 giây
   *  ghi đè — đúng loại bực mình mà một bảng tự cập nhật rất dễ gây ra. */
  const [nhap, setNhap] = useState<Partial<CaiDatNguon>>({})
  const [symMoi, setSymMoi] = useState('')
  const [loi, setLoi] = useState('')
  const [tin, setTin] = useState('')
  const [dangCho, setDangCho] = useState(false)
  const daNap = useRef(false)
  const [sanSang, setSanSang] = useState(false)

  const [tt, setTt] = useState<DongThiTruong[] | null>(null)
  const [dangDo, setDangDo] = useState(false)
  const [ttPhi0, setTtPhi0] = useState(false)

  const lamMoi = useCallback(async () => {
    const r = await py.nguon_liet_ke()
    if (!r.ok || !r.value) { setLoi(r.error ?? 'không đọc được nguồn'); return }
    setDs(r.value.ds)
    setGhi(r.value.ghi)
    setThuMuc(r.value.thu_muc)
    setCd(r.value.cai_dat)
    if (!daNap.current) { daNap.current = true; setSanSang(true) }
  }, [])

  useEffect(() => {
    void lamMoi()
    const h = setInterval(() => void lamMoi(), NHIP_LAM_MOI)
    return () => clearInterval(h)
  }, [lamMoi])

  const o = <K extends keyof CaiDatNguon>(k: K): CaiDatNguon[K] | undefined =>
    (nhap[k] !== undefined ? nhap[k] : cd?.[k]) as CaiDatNguon[K] | undefined
  const banNhap = Object.keys(nhap).length > 0

  async function luuCaiDat() {
    setLoi(''); setTin(''); setDangCho(true)
    const r = await py.nguon_luu_cai_dat(nhap)
    setDangCho(false)
    if (!r.ok) { setLoi(r.error ?? 'không lưu được'); return }
    setNhap({})
    setCd(r.value?.cai_dat ?? null)
    setTin(r.value?.can_khoi_dong_lai
      // Bộ ghi đọc cài đặt LÚC KHỞI ĐỘNG. Không nói ra thì người dùng đổi ngưỡng rồi
      // tưởng ăn ngay, và mấy tiếng sau vẫn thấy hành vi cũ.
      ? 'Đã lưu. Ngưỡng và nhịp xả chỉ ăn ở lần chạy sau của bộ ghi — dừng rồi bật lại.'
      : 'Đã lưu.')
  }

  function themSym(s: string) {
    const ten = s.trim().toUpperCase()
    if (!ten) return
    const cu = o('symbols') ?? []
    if (cu.includes(ten)) return
    setNhap(x => ({ ...x, symbols: [...cu, ten] }))
    setSymMoi('')
  }

  function boSym(s: string) {
    setNhap(x => ({ ...x, symbols: (o('symbols') ?? []).filter(t => t !== s) }))
  }

  async function batDau() {
    const syms = o('symbols') ?? []
    if (!syms.length) { setLoi('Chưa có symbol nào trong danh sách.'); return }
    setLoi(''); setTin(''); setDangCho(true)
    const r = await py.nguon_bat_dau(syms)
    setDangCho(false)
    if (!r.ok) { setLoi(r.error ?? 'không mở được bộ ghi'); return }
    setNhap(x => { const { symbols: _bo, ...con } = x; return con })
    // Bộ ghi cần một nhịp mới đập lần đầu — đợi rồi hãy hỏi, không thì bảng báo "chưa
    // chạy" ngay sau khi vừa bấm và trông như nút hỏng.
    setTimeout(() => void lamMoi(), 1200)
  }

  async function dung() {
    setLoi(''); setDangCho(true)
    const r = await py.nguon_dung()
    setDangCho(false)
    if (!r.ok) { setLoi(r.error ?? 'không dừng được'); return }
    setTin('Đã xin dừng — bộ ghi xả nốt đệm rồi thoát, mất vài giây.')
  }

  async function xoa(sym: string, mb: number) {
    if (!confirm(`Xoá HẲN ${mb} MB dữ liệu của ${sym}?\n\n`
                 + 'Ghi lại thì phải chờ từ đầu — dữ liệu quá khứ không mua lại được.')) return
    const r = await py.nguon_xoa(sym)
    if (!r.ok) { setLoi(r.error ?? 'không xoá được'); return }
    setDs(r.value?.ds ?? [])
  }

  async function doThiTruong(phi0: boolean) {
    setDangDo(true); setLoi(''); setTtPhi0(phi0)
    const r = await py.nguon_do_thi_truong(200, phi0 ? 0 : null)
    setDangDo(false)
    if (!r.ok) { setLoi(r.error ?? 'không đo được'); return }
    setTt(r.value?.ds ?? [])
  }

  const tongMb = ds.reduce((s, d) => s + d.mb, 0)
  const dangGhi = !!ghi?.song

  return (
    <>
      {/* ---- BỘ GHI ---- */}
      <div className={'ng-ghi' + (dangGhi ? ' song' : '')}>
        <span className="ng-den" />
        {dangGhi ? (
          <>
            <b>Đang ghi</b>
            <span className="mono">{ghi!.symbols.join(' · ')}</span>
            <span className="phu">từ {gio(ghi!.bat_dau)} · nhịp {ghi!.tuoi_nhip}s trước</span>
            <button className="nut nho" onClick={dung} disabled={dangCho}>Dừng</button>
          </>
        ) : (
          <>
            <b>Bộ ghi không chạy</b>
            <span className="phu">
              {sanSang ? 'Mỗi giờ không ghi là một giờ lịch sử không lấy lại được.' : '…'}
            </span>
            <button className="nut nho chinh" onClick={batDau}
                    disabled={dangCho || !(o('symbols') ?? []).length}>Bắt đầu ghi</button>
          </>
        )}
      </div>

      {/* ---- SYMBOL ---- */}
      <div className="hang">
        <span className="nhan-o">Symbol</span>
        <div className="ng-chip">
          {(o('symbols') ?? []).map(s => (
            <span key={s} className="the">
              {s}
              <button className="ng-x" title="bỏ khỏi danh sách"
                      onClick={() => boSym(s)} disabled={dangGhi}>✕</button>
            </span>
          ))}
          {!(o('symbols') ?? []).length && <span className="cd-rong">chưa chọn cái nào</span>}
        </div>
      </div>
      <div className="hang">
        <span className="nhan-o" />
        <input className="o" value={symMoi} spellCheck={false} placeholder="TRUMPUSDT"
               disabled={dangGhi}
               onChange={e => setSymMoi(e.target.value.toUpperCase())}
               onKeyDown={e => { if (e.key === 'Enter') themSym(symMoi) }} />
        <button className="nut" onClick={() => themSym(symMoi)} disabled={dangGhi}>Thêm</button>
        <button className="nut" onClick={() => void doThiTruong(false)} disabled={dangDo}
                title="spread ÷ (2 × phí maker) — điều kiện CẦN của cả hệ">
          {dangDo ? 'đang hỏi 4 sàn…' : 'Đo thị trường'}
        </button>
      </div>

      {/* ---- BẢNG ĐO THỊ TRƯỜNG ---- */}
      {tt && (
        <div className="ng-bang">
          <div className="ng-dau">
            spread ÷ (2 × phí maker) · khối lượng ≥ 200 triệu $/ngày
            {ttPhi0 && <b className="ng-canh"> · ÉP phí = 0, đây là giả định</b>}
            <button className="nut nho" style={{ marginLeft: 8 }}
                    onClick={() => void doThiTruong(!ttPhi0)} disabled={dangDo}>
              {ttPhi0 ? 'về phí thật' : 'thử phí = 0'}
            </button>
          </div>
          {tt.length === 0 ? <div className="cd-rong">không symbol nào qua ngưỡng</div> : (
            <table className="kho-bang">
              <thead><tr>
                <th>Sàn</th><th>Symbol</th><th>spread</th><th>phí</th>
                <th>TỈ LỆ</th><th>tick</th><th>KL 24h</th><th />
              </tr></thead>
              <tbody>
                {tt.slice(0, 12).map(d => (
                  <tr key={d.san + d.ma}>
                    <td className="mono">{d.san}</td>
                    <td><b>{d.ma}</b></td>
                    <td className="mono">{d.spread_bps.toFixed(2)}</td>
                    <td className="mono">{d.phi_bps.toFixed(1)}</td>
                    {/* Tỉ lệ ≤ 1 là SAI DẤU — bắt spread không có lãi gộp. Phải đỏ. */}
                    <td className={'mono' + (d.ti_le > 1 ? '' : ' ng-canh')}>
                      {d.ti_le.toFixed(2)}
                    </td>
                    <td className="mono">{d.tick ? d.tick.toFixed(0) : '—'}</td>
                    <td className="mono">{d.kl_trieu.toLocaleString('vi', {
                      maximumFractionDigits: 0 })}</td>
                    <td>
                      {d.san.startsWith('binance') && (
                        <button className="nut nho" disabled={dangGhi}
                                onClick={() => themSym(d.ma)}>Thêm</button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="chu-dan">
            Tỉ lệ &gt; 1 là điều kiện <b>CẦN</b>, không phải đủ — nó giả định bạn ăn
            trọn spread. Chỉ thêm được symbol Binance: bộ ghi hiện chỉ nói chuyện với
            sàn đó.
          </div>
        </div>
      )}

      {/* ---- BỐN Ô CÀI ĐẶT ---- */}
      <div className="ng-dau" style={{ marginTop: 14 }}>Cài đặt</div>
      <div className="hang">
        <span className="nhan-o">Thư mục</span>
        <input className="o" value={o('thu_muc') ?? ''} spellCheck={false}
               placeholder="(để trống = du_lieu/tick)"
               onChange={e => setNhap(x => ({ ...x, thu_muc: e.target.value }))} />
      </div>
      <div className="hang">
        <span className="nhan-o">Giữ</span>
        <input className="o nho" type="number" min={0} value={o('giu_ngay') ?? 0}
               onChange={e => setNhap(x => ({ ...x, giu_ngay: +e.target.value }))} />
        <span className="phu">ngày · 0 = giữ tất</span>
        <span className="nhan-o phu">Ngưỡng im lặng</span>
        <input className="o nho" type="number" min={5} value={o('im_lang_giay') ?? 45}
               onChange={e => setNhap(x => ({ ...x, im_lang_giay: +e.target.value }))} />
        <span className="phu">giây</span>
        <span className="nhan-o phu">Nhịp xả</span>
        <input className="o nho" type="number" min={0.2} step={0.5}
               value={o('giay_xa') ?? 2}
               onChange={e => setNhap(x => ({ ...x, giay_xa: +e.target.value }))} />
        <span className="phu">giây</span>
      </div>
      <div className="hang">
        <span className="nhan-o" />
        <button className="nut chinh" onClick={luuCaiDat} disabled={!banNhap || dangCho}>
          Lưu cài đặt
        </button>
        {banNhap && <button className="nut" onClick={() => setNhap({})}>Bỏ sửa</button>}
        <span className="phu">
          Đổi thư mục <b>không dời</b> dữ liệu cũ — dời vài chục GB ngầm sau lưng là
          việc không được phép làm im lặng.
        </span>
      </div>

      {/* ---- DỮ LIỆU ĐÃ CÓ ---- */}
      <div className="ng-bang">
        <div className="ng-dau">Đã có trên đĩa</div>
        {!sanSang ? <div className="cd-rong">đang đọc…</div>
          : ds.length === 0 ? (
            <div className="cd-rong">chưa có dữ liệu nào — chưa backtest được gì</div>
          ) : (
            <table className="kho-bang">
              <thead><tr>
                <th>Symbol</th><th>Ngày</th><th>Dải</th><th>Sổ lệnh</th><th>Khớp</th>
                <th>Dung lượng</th><th>Lỗ hổng</th><th>Trễ</th><th />
              </tr></thead>
              <tbody>
                {ds.map(d => (
                  <tr key={d.symbol}>
                    <td><b>{d.symbol}</b></td>
                    <td className="mono">{d.so_ngay}</td>
                    <td className="mono">{ngay(d.tu_ngay)} → {ngay(d.den_ngay)}</td>
                    <td className="mono">{d.so_ban_ghi.so.toLocaleString('vi')}</td>
                    <td className="mono">{d.so_ban_ghi.khop.toLocaleString('vi')}</td>
                    <td className="mono">{d.mb.toLocaleString('vi')} MB</td>
                    {/* Lỗ hổng quyết định backtest có tin được không. 0 thì mờ, khác 0 đỏ. */}
                    <td className={'mono' + (d.so_lo_hong ? ' ng-canh' : '')}>
                      {d.so_lo_hong === 0 ? '—'
                        : `${d.so_lo_hong} · ${(d.ms_lo_hong / 1000).toFixed(0)}s`}
                    </td>
                    <td className="mono">{d.tre_ms == null ? '—' : `${d.tre_ms} ms`}</td>
                    <td>
                      <button className="nut nho" onClick={() => xoa(d.symbol, d.mb)}
                              disabled={dangGhi && ghi!.symbols.includes(d.symbol)}
                              title={dangGhi && ghi!.symbols.includes(d.symbol)
                                ? 'đang ghi symbol này — dừng bộ ghi trước' : 'xoá hẳn'}>
                        Xoá
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
      </div>

      {loi && <div className="chu-dan canh">{loi}</div>}
      {tin && !loi && <div className="chu-dan">{tin}</div>}

      <div className="chu-dan">
        <code>{thuMuc}</code> · {tongMb.toLocaleString('vi')} MB · ước tính
        <b> ~800 MB/ngày</b> cho mỗi symbol tầm trung. Bộ ghi chạy trong một tiến trình
        <b> riêng</b>: đóng app nó vẫn ghi tiếp.
      </div>
    </>
  )
}
