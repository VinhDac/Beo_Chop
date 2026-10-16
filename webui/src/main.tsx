import React from 'react'
import ReactDOM from 'react-dom/client'
import './theme.css'
import './app.css'
import TrangTrong from './TrangTrong'

/* D-12: bộ khối cũ và cách tương tác cũ đã gỡ bỏ. Cửa sổ mở lên nói đúng điều đó, thay
   vì bày ra một trình vẽ không còn khối nào để vẽ. */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <TrangTrong />
  </React.StrictMode>,
)
