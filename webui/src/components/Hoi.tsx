import { useEffect, useRef, useState } from 'react'
import Modal from './Modal'

/** HỘP HỎI CỦA APP — thay cho `window.confirm` / `alert` / `prompt`.
 *
 *  VÌ SAO PHẢI THAY. Hộp thoại gốc của trình duyệt hiện ra với tiêu đề
 *  "127.0.0.1:8777 says", nền trắng, nút xanh hệ thống — giữa một app nền tối tự vẽ cả
 *  thanh tiêu đề. Nó nói ra đúng thứ app cố giấu: đây là một trang web trong khung. Và
 *  nó không nhận được một nét nào của `theme.css`, nên không có cách nào chỉnh.
 *
 *  CÁI GIÁ: hộp gốc CHẶN ĐỒNG BỘ (`if (!confirm(...)) return`), còn hộp React thì
 *  không — nên mọi chỗ gọi phải thành `await`. Đổi lại viết vẫn gọn y như cũ:
 *
 *      if (!(await xacNhan({ loi: 'Xoá thật?' }))) return
 *
 *  VÌ SAO KHÔNG DÙNG CONTEXT: hộp hỏi chỉ có MỘT cái tại một thời điểm, nên một ô nhớ
 *  ở mức module cộng đúng một `<HopHoi />` cắm ở gốc là đủ; dựng cả Provider + hook để
 *  chuyển một hàm xuống là nhiều lớp hơn thứ nó gánh.
 *
 *  XẾP CHỒNG: `.lop-phu` của mọi Modal đều z-index 50, nên THỨ TỰ TRONG DOM quyết định
 *  cái nào nằm trên. `<HopHoi />` phải là thứ CUỐI CÙNG trong cây của App — không thì
 *  nó chui xuống dưới chính hộp thoại vừa gọi nó.
 *
 *  Chép từ Jenifer_Studio.
 */

type Yeu = {
  /** Câu hỏi chính. Một câu, nói thẳng hậu quả. */
  loi: string
  tieu_de?: string
  /** Phần dài đi kèm. Cuộn được, không phình hộp. */
  chi_tiet?: string
  /** Có mặt (kể cả chuỗi rỗng) = hộp NHẬP, và đây là giá trị mở sẵn. */
  nhap?: string
  nut_ok?: string
  /** Nút OK màu cảnh báo — cho thao tác không hoàn tác được. */
  nguy?: boolean
  /** Chỉ MỘT nút, không có Huỷ. Thay `window.alert`. */
  chi_bao?: boolean
}

type Cho = { y: Yeu; xong: (v: string | boolean | null) => void }

let _dat: ((c: Cho | null) => void) | null = null

function goi(y: Yeu): Promise<string | boolean | null> {
  // CHƯA CẮM `<HopHoi />` thì rơi về hộp gốc, ĐỪNG nuốt câu hỏi. Nuốt nghĩa là một
  // thao tác không hoàn tác được chạy thẳng mà không ai hỏi ai.
  if (!_dat) {
    if (y.nhap !== undefined) return Promise.resolve(window.prompt(y.loi, y.nhap))
    if (y.chi_bao) { window.alert(y.loi); return Promise.resolve(true) }
    return Promise.resolve(window.confirm(y.loi))
  }
  return new Promise(xong => _dat!({ y, xong }))
}

/** Hỏi có/không. Trả `true` nếu người dùng đồng ý. */
export async function xacNhan(y: Yeu): Promise<boolean> {
  return (await goi(y)) === true
}

/** Báo một tin, chỉ có nút Đóng. */
export async function bao(y: Yeu): Promise<void> {
  await goi({ ...y, chi_bao: true })
}

/** Hỏi một dòng chữ. Trả `null` nếu huỷ — GIỮ ĐÚNG giao kèo của `window.prompt`, vì
 *  chỗ gọi phân biệt "huỷ" với "gõ chuỗi rỗng". */
export async function nhapChu(y: Yeu & { nhap: string }): Promise<string | null> {
  const v = await goi(y)
  return typeof v === 'string' ? v : null
}

export default function HopHoi() {
  const [cho, setCho] = useState<Cho | null>(null)
  const [gia, setGia] = useState('')
  const o = useRef<HTMLInputElement>(null)
  const nut = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    _dat = c => { setCho(c); setGia(c?.y.nhap ?? '') }
    return () => { _dat = null }
  }, [])

  /* Con trỏ nhảy sẵn vào chỗ người dùng sắp dùng: ô nhập nếu có, không thì nút OK —
     để Enter ăn ngay mà không phải với chuột. */
  useEffect(() => {
    if (!cho) return
    const t = setTimeout(() => {
      if (cho.y.nhap !== undefined) { o.current?.focus(); o.current?.select() }
      else nut.current?.focus()
    }, 0)
    return () => clearTimeout(t)
  }, [cho])

  if (!cho) return null
  const { y } = cho
  const xong = (v: string | boolean | null) => { setCho(null); cho.xong(v) }
  const dong = () => xong(y.chi_bao ? true : y.nhap !== undefined ? null : false)
  const ok = () => xong(y.nhap !== undefined ? gia : true)

  return (
    <Modal title={y.tieu_de ?? 'Xác nhận'} width={y.chi_tiet ? 560 : 440} onClose={dong}
           footer={<>
             {!y.chi_bao && <button className="nut" onClick={dong}>Huỷ</button>}
             <button ref={nut} className={'nut ' + (y.nguy ? 'do' : 'chinh')} onClick={ok}>
               {y.nut_ok ?? (y.chi_bao ? 'Đóng' : 'Đồng ý')}
             </button>
           </>}>
      <div className="hoi-loi">{y.loi}</div>
      {y.chi_tiet && <div className="hoi-chi-tiet">{y.chi_tiet}</div>}
      {y.nhap !== undefined && (
        <input ref={o} className="o day" style={{ marginTop: 10 }}
               value={gia} onChange={e => setGia(e.target.value)}
               onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); ok() } }} />
      )}
    </Modal>
  )
}
