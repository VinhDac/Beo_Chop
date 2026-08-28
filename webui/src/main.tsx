import React from 'react'
import ReactDOM from 'react-dom/client'
// THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css.
// Trước đây nó được import trong App.tsx, mà App lại import SAU css của mình, nên
// nó nằm cuối bundle và đè mất — vùng bấm cổng nối vẫn là 6px dù đã khai 24px.
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import App from './App'

/** Rẽ trang bằng `?tester=1` — KHÔNG thêm entry thứ hai cho Vite.
 *
 * `api.py` gắn sẵn `?tester=1` vào url cửa sổ Strategy Tester từ lâu, nhưng trước đây
 * KHÔNG chỗ nào đọc nó, nên cửa sổ thứ hai dựng lại y hệt trình soạn thảo — hai thanh
 * tiêu đề, hai ribbon, và mọi lời gọi `py.*` đều nhắm vào cửa sổ chính.
 *
 * Một dòng `if` ở đây rẻ hơn hẳn `build.rollupOptions.input`: một bundle, một `app.css`
 * toàn cục, dùng chung được `TitleBar` / `Modal` / `Icon` mà không phải tách gì. */
const laTester = new URLSearchParams(location.search).get('tester') === '1'
const laLive = new URLSearchParams(location.search).get('live') === '1'

/** Ổ CẮM TRỐNG — cửa sổ Tester và Live đã bị gỡ (đợt 1 của lần dọn sang HFT market
 *  maker). Hai cửa sổ cũ dựng quanh chart nến và thống kê bội R; màn hình của một
 *  market maker — thang báo giá, tồn kho theo thời gian, chất lượng khớp — không dùng
 *  chung một dòng nào với chúng.
 *
 *  ⚠ GIỮ nhánh rẽ này chứ không xoá. Bỏ nó đi thì `?tester=1` rơi về `<App/>`, và cửa
 *  sổ thứ hai lại dựng nguyên trình soạn thảo lần nữa — đúng con bug mà chú thích phía
 *  trên kể. Một tấm bia đọc được thì thà hơn một cửa sổ nói dối.
 *
 *  Xem `tai_lieu/o_cam_trong.md`. */
function ChuaCo({ ten }: { ten: string }) {
  return (
    <div style={{
      height: '100vh', display: 'grid', placeContent: 'center', gap: 8,
      background: 'var(--bg)', color: 'var(--muted)',
      font: '13px/1.6 system-ui, sans-serif', textAlign: 'center',
    }}>
      <div style={{ color: 'var(--text)', fontSize: 15 }}>Chưa có cửa sổ {ten}</div>
      <div>Cửa sổ cũ đã gỡ cùng MT5 và mô hình nến.</div>
      <div>Cái thay thế chờ chọn xong sàn.</div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {laLive ? <ChuaCo ten="Live" />
      : laTester ? <ChuaCo ten="Strategy Tester" />
        : <App />}
  </React.StrictMode>,
)
