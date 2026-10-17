import React from 'react'
import ReactDOM from 'react-dom/client'
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import SoDo from './SoDo'
import TrangKetQua from './TrangKetQua'

/* THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css, không thì
   nó đè lên luật của ta mà không báo gì. */

/* MỘT BUNDLE, HAI VAI. `?kq=<mã lượt>` thì cửa sổ này là một CỬA SỔ KẾT QUẢ riêng —
   mở được nhiều cái cùng lúc để xếp cạnh nhau mà so hai phiên bản của một chiến
   thuật. Không có tham số thì nó là cửa sổ chính, vẽ sơ đồ.

   Cố ý KHÔNG dựng một trang HTML thứ hai: hai trang thì sớm muộn một bên có thứ bên
   kia không, và cái lệch ấy chỉ lộ ra ở màn ít người mở nhất. */
const kq = new URLSearchParams(window.location.search).get('kq')

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    {kq ? <TrangKetQua ma={kq} /> : <SoDo />}
  </React.StrictMode>,
)
