import React from 'react'
import ReactDOM from 'react-dom/client'
// THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css.
// Trước đây nó được import trong App.tsx, mà App lại import SAU css của mình, nên
// nó nằm cuối bundle và đè mất — vùng bấm cổng nối vẫn là 6px dù đã khai 24px.
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import App from './App'

/* ⚠ NHÁNH RẼ `?tester=1` / `?live=1` ĐÃ ĐI (đợt 2). Tấm bia dựng ở đợt 1 chỉ đúng
 * chừng nào `api.py` còn MỞ cửa sổ thứ hai — giờ `mo_tester` và `mo_live` trả thẳng
 * một câu lỗi và không tạo cửa sổ nào, nên không url nào mang được hai tham số đó nữa.
 * Giữ lại là để một nhánh không bao giờ chạy tới, tức đúng loại mã làm người đọc sau
 * tưởng còn có cửa sổ thứ hai ở đâu đó.
 *
 * Ngày dựng lại cửa sổ chạy: chỗ rẽ nằm ở ĐÂY, và chú thích cũ giải thích vì sao rẽ
 * bằng một dòng `if` chứ không bằng `build.rollupOptions.input` — một bundle, một
 * `app.css` toàn cục, dùng chung `TitleBar`/`Modal`/`Icon` mà không phải tách gì.
 * Đọc `git show f1c90fb:webui/src/main.tsx`. Xem `tai_lieu/o_cam_trong.md`. */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
