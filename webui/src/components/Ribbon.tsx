import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'
import type { Tab } from '../types'
import Icon from './Icon'

/** Thanh công cụ kiểu ribbon của Paint: nút nhóm lại, nhãn nhóm nằm DƯỚI, có vạch
 *  ngăn giữa các nhóm. Mọi thứ "thêm vào" nằm ở trên; canvas phía dưới chỉ để di
 *  chuyển và nối. */

function Nhom({ ten, children }: { ten: string; children: ReactNode }) {
  return (
    <div className="nhom-ribbon">
      <div className="cac-nut">{children}</div>
      <div className="ten-nhom">{ten}</div>
    </div>
  )
}

function Nut({ ten, icon, onClick, tat, title }: {
  ten: string; icon: ReactNode; onClick?: () => void; tat?: boolean; title?: string
}) {
  return (
    <button className="nut-lon" onClick={onClick} disabled={tat} title={title || ten}>
      <span className="hinh">{icon}</span>
      <span>{ten}</span>
    </button>
  )
}

export interface MucMenu { nhan: string; chay: () => void; tat?: boolean; lyDo?: string }

/** Nút có menu xổ xuống.
 *  Mục bị tắt vẫn HIỆN kèm lý do: giấu đi thì người dùng tưởng tính năng không tồn tại. */
function NutMenu({ ten, icon, muc }: { ten: string; icon: ReactNode; muc: MucMenu[] }) {
  const [mo, setMo] = useState(false)
  const [viTri, setViTri] = useState({ x: 0, y: 0 })
  const boc = useRef<HTMLDivElement>(null)
  const nut = useRef<HTMLButtonElement>(null)
  const bang = useRef<HTMLDivElement>(null)

  /* Menu này ĐỊNH VỊ THEO KHUNG NHÌN, không theo khối cha.
     `.ribbon` có `overflow-x: auto`, mà theo chuẩn CSS hễ một trục thôi `visible` thì
     trục kia cũng thôi luôn — nên dải ribbon cắt cụt menu theo CHIỀU DỌC: bấm "Mở ▾"
     ra một mẩu menu bị xén, không bấm được mục nào.
     `position: fixed` thoát khỏi mọi vùng cắt của khối cha. */
  useLayoutEffect(() => {
    if (!mo || !nut.current) return
    const r = nut.current.getBoundingClientRect()
    const m = bang.current?.getBoundingClientRect()
    const le = 6
    setViTri({
      x: Math.max(le, Math.min(r.left, window.innerWidth - (m?.width ?? 268) - le)),
      y: Math.max(le, Math.min(r.bottom + 2, window.innerHeight - (m?.height ?? 0) - le)),
    })
  }, [mo])

  useEffect(() => {
    if (!mo) return
    const f = (e: MouseEvent) => {
      if (!boc.current?.contains(e.target as globalThis.Node)) setMo(false)
    }
    const dong = () => setMo(false)
    window.addEventListener('mousedown', f)
    window.addEventListener('resize', dong)
    return () => {
      window.removeEventListener('mousedown', f)
      window.removeEventListener('resize', dong)
    }
  }, [mo])

  return (
    <div className="boc-menu" ref={boc}>
      <button className="nut-lon" ref={nut} onClick={() => setMo(v => !v)}>
        <span className="hinh">{icon}</span>
        <span>{ten} ▾</span>
      </button>
      {mo && (
        <div className="menu-xo" ref={bang} style={{ left: viTri.x, top: viTri.y }}>
          {muc.map((m, i) => (
            <button key={i} className="muc-menu" disabled={m.tat}
                    title={m.tat ? m.lyDo : undefined}
                    onClick={() => { setMo(false); m.chay() }}>
              {m.nhan}{m.tat && m.lyDo ? <span className="ly-do">— {m.lyDo}</span> : null}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

const S = {
  fill: 'none', stroke: 'currentColor', strokeWidth: 1.5,
  strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
}

/** Icon 22px của ribbon — to hơn bộ 16px trong `Icon.tsx` nên vẽ riêng, cùng ngôn ngữ nét. */
const I = {
  /* Một đường vào, hai đường ra — đúng hình rẽ nhánh người dùng vẽ trên giấy. */
  branch: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M2.5 11h5M7.5 11l5-5M7.5 11l5 5" /><circle {...S} cx="15.5" cy="6" r="2.6" /><circle {...S} cx="15.5" cy="16" r="2.6" /></svg>,
  /* Số hạng: bậc thang cộng dồn + dấu cộng. Cùng hình với `Icon.tsx`, chỉ khác cỡ. */
  soHang: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M2.8 17.2h4.8V12.8h4.8V8.4" /><path {...S} d="M2.8 17.2v-2.8" strokeDasharray="2 1.8" /><path {...S} d="M16.2 4.4v6.4M13 7.6h6.4" /></svg>,
  start: <svg viewBox="0 0 22 22" width="22" height="22"><circle {...S} cx="11" cy="11" r="8" /><path {...S} d="M11 5.4l3.6 5.6-3.6 5.6-3.6-5.6z" /></svg>,
  edit: <svg viewBox="0 0 22 22" width="22" height="22"><rect {...S} x="3.5" y="3.5" width="15" height="15" rx="2" /><path {...S} d="M7.5 13.5l6-6M11 6.5l4 4" /></svg>,
  copy: <svg viewBox="0 0 22 22" width="22" height="22"><rect {...S} x="7" y="7" width="11" height="11" rx="1.8" /><path {...S} d="M14.5 4.5H5.8A1.3 1.3 0 0 0 4.5 5.8v8.7" /></svg>,
  del: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M4.5 6.5h13M9 6.5V4.5h4v2M6.5 6.5l1 12h7l1-12" /><path {...S} d="M9.5 9.5v6M12.5 9.5v6" /></svg>,
  undo: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M6 9.5H14a4.5 4.5 0 0 1 0 9h-3" /><path {...S} d="M9 6l-3.5 3.5L9 13" /></svg>,
  redo: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M16 9.5H8a4.5 4.5 0 0 0 0 9h3" /><path {...S} d="M13 6l3.5 3.5L13 13" /></svg>,
  save: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M4.5 5.8A1.3 1.3 0 0 1 5.8 4.5h8.4l3.3 3.3v8.4a1.3 1.3 0 0 1-1.3 1.3H5.8a1.3 1.3 0 0 1-1.3-1.3z" /><path {...S} d="M7.5 4.5v4h6v-4M7.5 17.5v-4h7v4" /></svg>,
  open: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M3.5 17V6.5A1 1 0 0 1 4.5 5.5h4l2 2.2h6a1 1 0 0 1 1 1V17z" /><path {...S} d="M3.5 17l2.6-6h13l-2.6 6z" /></svg>,
  // Số ① — CỐ Ý không dùng hình tam giác play: nút ▶ Chạy ở ngay cạnh, hai biểu tượng
  // play trong một ribbon thì không ai đoán được cái nào làm gì.
  motSo: <svg viewBox="0 0 22 22" width="22" height="22"><circle {...S} cx="11" cy="11" r="7.8" /><path {...S} d="M9.6 8.6L11.4 7.4v7.4M9.8 14.8h3.4" /></svg>,
  ghim: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M13.2 2.6l6.2 6.2-2.5 1.4-4-4z" /><path {...S} d="M12.9 6.2L6.4 11.4l4.2 4.2 4.5-6.2" /><path {...S} d="M8.6 13.4L3.2 18.8" /></svg>,
  fit: <svg viewBox="0 0 22 22" width="22" height="22"><path {...S} d="M4 8V4.5h3.5M18 8V4.5h-3.5M4 14v3.5h3.5M18 14v3.5h-3.5" /><rect {...S} x="8" y="8" width="6" height="6" rx="1" /></svg>,
}

export interface RibbonProps {
  tab: Tab
  themKiemTra: () => void
  themSoHang: () => void
  sua: () => void
  datBatDau: () => void
  doiGhim: () => void
  nhanBan: () => void
  xoa: () => void
  hoanTac: () => void
  lamLai: () => void
  vuaKhung: () => void
  mucLuu: MucMenu[]
  mucMo: MucMenu[]
  // cụm chạy ghim mép phải ribbon
  ten: string
  datTen: (v: string) => void
  symbol: string
  datSymbol: (v: string) => void
  chay: () => void
  live: () => void
  coChon: boolean
  chonDaGhim: boolean
  coTheHoanTac: boolean
  coTheLamLai: boolean
}

/** Pill chuyển sơ đồ — nằm NGAY DƯỚI dải ribbon, sát mép trái.
 *
 *  Đặt ở đó vì nó không phải một nút trong ribbon mà là câu trả lời cho "mọi thứ phía
 *  trên đang tác động lên sơ đồ NÀO". Chấm đỏ trên tab kia để lỗi không trốn được sau
 *  lưng: bấm ▶ Chạy mới biết tab kia hỏng là quá muộn.
 *
 *  ⚠ Danh sách tab và nhãn của chúng giờ lấy từ `bootstrap`, không viết cứng ở đây.
 *  Bản cũ khai `TEN_TAB` + `CHU_THICH_TAB` cho đúng hai tab Entry/Manage — mà tên tab
 *  vốn là kiến thức của lõi (`core.TABS` / `TAB_LABELS`), nên chép sang JS là dựng hai
 *  nguồn sự thật cho một thứ.
 *
 *  MỘT TAB THÌ KHÔNG VẼ GÌ: một cái pill đứng một mình không trả lời được câu hỏi nào
 *  — không có lựa chọn nào để thấy — mà vẫn chiếm chỗ trên canvas. */
export function PillTab({ tab, tabs, nhan, datTab, tabCoLoi }: {
  tab: Tab; tabs: Tab[]; nhan: Record<string, string>
  datTab: (t: Tab) => void; tabCoLoi: Record<string, boolean>
}) {
  if (tabs.length < 2) return null
  return (
    <div className="pill-tab">
      {tabs.map(t => (
        <button key={t} className={'pill' + (tab === t ? ' dang' : '')}
                onClick={() => datTab(t)}>
          {nhan[t] ?? t}
          {tabCoLoi[t] && <span className="cham-loi" title="This diagram has errors" />}
        </button>
      ))}
    </div>
  )
}

export default function Ribbon(p: RibbonProps) {
  return (
    <div className="ribbon">
      {/* ⚠ Bản cũ ẨN/HIỆN nút theo tab: Entry chỉ TẠO lệnh, Manage chỉ SỬA lệnh. Cả
          hai nút và cả cái luật ấy đã đi cùng hai động từ — market maker chỉ có MỘT
          sơ đồ, nên không còn gì để ẩn theo. Cơ chế `action_tabs` thì vẫn còn bên
          Python, sẵn cho ngày có sơ đồ thứ hai. */}
      <Nhom ten="Add block">
        <Nut ten="Check" icon={I.branch} onClick={p.themKiemTra}
             title={'Add a "Check condition" gate — wire several gates out of one block '
                    + 'to fork. If it matches you take that branch, otherwise the next '
                    + 'one down is tried.'} />
        <Nut ten="Term" icon={I.soHang} onClick={p.themSoHang}
             title={'Contribute one term to the quote: set or add to fair value, '
                    + 'half-spread, skew or size. It can carry a "when …" condition.'} />
      </Nhom>

      <Nhom ten="Sửa">
        <Nut ten="Edit" icon={I.edit} onClick={p.sua} tat={!p.coChon}
             title="Open the editor for the selected block (or double-click it)" />
        <Nut ten="Duplicate" icon={I.copy} onClick={p.nhanBan} tat={!p.coChon}
             title="Duplicate the selected block (Ctrl+D)" />
        <Nut ten="Delete" icon={I.del} onClick={p.xoa} tat={!p.coChon}
             title="Delete the selected block (Delete)" />
      </Nhom>

      <Nhom ten="Flow">
        <Nut ten="Make ①" icon={I.motSo} onClick={p.datBatDau} tat={!p.coChon}
             title="Make the selected block ① — the one that runs first" />
        <Nut ten={p.chonDaGhim ? 'Unpin' : 'Pin number'} icon={I.ghim}
             onClick={p.doiGhim} tat={!p.coChon}
             title={'Pin the selected block\'s number: any edge looping back to it keeps '
                    + 'that same number, and the loop warning goes away'} />
        <Nut ten="Fit view" icon={I.fit} onClick={p.vuaKhung}
             title="Fit the whole diagram on screen" />
      </Nhom>

      <Nhom ten="Undo">
        <Nut ten="Undo" icon={I.undo} onClick={p.hoanTac} tat={!p.coTheHoanTac} title="Ctrl+Z" />
        <Nut ten="Redo" icon={I.redo} onClick={p.lamLai} tat={!p.coTheLamLai} title="Ctrl+Y" />
      </Nhom>

      <Nhom ten="Template">
        <NutMenu ten="Save" icon={I.save} muc={p.mucLuu} />
        <NutMenu ten="Open" icon={I.open} muc={p.mucMo} />
      </Nhom>

      {/* Cụm chạy — ghim mép phải. Hai tầng: tên chiến lược ở trên, hàng nút hạ xuống
          dưới cho ngang hàng với nhãn nhóm. Xếp chồng nên KHÔNG tốn thêm bề ngang. */}
      <div className="cum-chay">
        <input className="o o-ten-process" value={p.ten} spellCheck={false}
               placeholder="Strategy name"
               title="Strategy name — also shown in the title bar"
               onChange={e => p.datTen(e.target.value)} />
        <div className="hang-chay">
          <input className="o nho o-symbol" value={p.symbol} spellCheck={false}
                 title="Trading symbol" placeholder="BTCUSDT"
                 onChange={e => p.datSymbol(e.target.value.toUpperCase())} />
          {/* LIVE đứng TRÁI và màu đỏ. Đỏ không phải để đẹp: hai nút cạnh nhau, một
              cái tiêu vài giây CPU, một cái tiêu tiền thật — chúng không được trông
              giống nhau. Trái/phải cũng cố ý: tay quen bấm cái bên phải. */}
          <button className="nut do" onClick={p.live}
                  title="Open the Live window — NO EXCHANGE CONNECTION YET (Ctrl+L)">● Live</button>
          <button className="nut chinh" onClick={p.chay}
                  title="Backtest this diagram on recorded tick data (Ctrl+R)">▶ Test</button>
        </div>
      </div>
    </div>
  )
}
