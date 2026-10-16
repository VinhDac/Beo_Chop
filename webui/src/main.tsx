import React from 'react'
import ReactDOM from 'react-dom/client'
import '@xyflow/react/dist/style.css'
import './theme.css'
import './app.css'
import SoDo from './SoDo'

/* THỨ TỰ QUAN TRỌNG: stylesheet gốc của React Flow phải nạp TRƯỚC app.css, không thì
   nó đè lên luật của ta mà không báo gì. */
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SoDo />
  </React.StrictMode>,
)
