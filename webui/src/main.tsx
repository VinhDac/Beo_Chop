import React from 'react'
import ReactDOM from 'react-dom/client'
// THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css.
// Trước đây nó được import trong App.tsx, mà App lại import SAU css của mình, nên
// nó nằm cuối bundle và đè mất — vùng bấm cổng nối vẫn là 6px dù đã khai 24px.
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import MayApp from './may/MayApp'
import ManChoi from './qc/ManChoi'

/** Rẽ trang bằng `?qc=1` — KHÔNG thêm entry thứ hai cho Vite.
 *
 * Một dòng `if` ở đây rẻ hơn hẳn `build.rollupOptions.input`: một bundle, một `app.css`
 * toàn cục, dùng chung được `TitleBar` / `Modal` / `Icon` mà không phải tách gì. */
const laQC = new URLSearchParams(location.search).get('qc') === '1'

/* Cửa sổ vẽ là TRÌNH VẼ CỖ MÁY 5 TRẠM (D-10, phần 5). Sơ đồ cũ Entry/Manage (`App.tsx`)
   không còn lối vào nào: lối chạy duy nhất của app là cỗ máy 5 trạm trên QuantConnect,
   và phần 7 xoá hẳn phần mã của nó. */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {laQC ? <ManChoi /> : <MayApp />}
  </React.StrictMode>,
)
