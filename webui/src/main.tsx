import React from 'react'
import ReactDOM from 'react-dom/client'
// THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css.
// Trước đây nó được import trong App.tsx, mà App lại import SAU css của mình, nên
// nó nằm cuối bundle và đè mất — vùng bấm cổng nối vẫn là 6px dù đã khai 24px.
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import App from './App'
import ManChoi from './qc/ManChoi'

/** Rẽ trang bằng `?qc=1` — KHÔNG thêm entry thứ hai cho Vite.
 *
 * Một dòng `if` ở đây rẻ hơn hẳn `build.rollupOptions.input`: một bundle, một `app.css`
 * toàn cục, dùng chung được `TitleBar` / `Modal` / `Icon` mà không phải tách gì. */
const laQC = new URLSearchParams(location.search).get('qc') === '1'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {laQC ? <ManChoi /> : <App />}
  </React.StrictMode>,
)
