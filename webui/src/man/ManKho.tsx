import { useEffect, useMemo, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { cho_cau_noi, py } from '../api'
import { tr, useNgonNgu } from '../ngon_ngu'
import type { KhoDaiLuong, NhomKho } from '../types'

/** MÀN HÌNH KHO — 164 đại lượng và 10 loại hành động, tra được.
 *
 *  ⭐ ĐÂY LÀ CHỖ "DẠY HẾT" SỐNG LÂU DÀI. 26 màn dạy 9 NHÓM và ngữ pháp; từng món thì
 *  tra ở đây. Dạy 164 món bằng 164 màn là 90 màn chỉ báo giống hệt nhau, và người chơi
 *  bỏ ở màn thứ sáu — xem `tai_lieu/thiet_ke_tro_choi.md` §0.
 *
 *  ⚠ MÓN CHƯA MỞ VẪN KÊ TÊN RA. Giấu hẳn thì người chơi không biết trước mặt còn bao
 *  nhiêu thứ, mà biết mình đang đi tới đâu chính là thứ giữ người ta chơi tiếp. Cùng
 *  lý do bản đồ hành trình bày cả màn đang khoá.
 *
 *  ⚠ VÀ MỖI MÓN BÀY CÂU LEAN THẬT CỦA NÓ. Đó là cả lời hứa D-11: mỗi đại lượng khai
 *  ĐÚNG MỘT thứ có thật của LEAN, không phải một cái tên app tự nghĩ ra. Người chơi
 *  đọc được câu ấy thì sang QuantConnect là dùng được ngay, không phải học lại.
 */
export default function ManKho({ onRa }: { onRa: () => void }) {
  const nn = useNgonNgu()
  const [d, setD] = useState<KhoDaiLuong | null>(null)
  const [loi, setLoi] = useState('')
  const [chon, setChon] = useState('')
  const [tim, setTim] = useState('')

  useEffect(() => {
    void (async () => {
      try {
        await cho_cau_noi('ping', 30000)
      } catch {
        setLoi(tr('Không kết nối được tới Python.'))
        return
      }
      const r = await py.kho_dai_luong()
      if (r.ok && r.value) {
        setD(r.value)
        setChon(c => c || r.value!.nhom.find(n => n.mo)?.ten || r.value!.nhom[0]?.ten || '')
      } else setLoi(r.error ?? tr('Không mở được kho.'))
    })()
  }, [nn])

  /** Lọc theo chữ gõ — tìm cả trong tên lẫn trong câu LEAN, vì người đã biết LEAN sẽ
   *  gõ thẳng `rsi` hay `securities` chứ không gõ tên tiếng Việt. */
  const nhomHien = useMemo(() => {
    if (!d) return []
    const q = tim.trim().toLowerCase()
    if (!q) return d.nhom
    return d.nhom
      .map(n => ({ ...n, muc: n.muc.filter(m =>
        m.nhan.toLowerCase().includes(q) || m.lean.toLowerCase().includes(q)
        || m.ma.toLowerCase().includes(q)) }))
      .filter(n => n.muc.length)
  }, [d, tim])

  const nhom = nhomHien.find(n => n.ten === chon) ?? nhomHien[0]

  return (
    <div className="kh">
      <TitleBar tieuDe={tr('Kho')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={tr('Về Hành trình')}>←</button>
      } />

      {loi && <div className="mc-bao loi kh-loi">⚠ {loi}</div>}
      {!d && !loi && (
        <div className="kh-cho"><Icon name="chay" /> {tr('đang mở kho…')}</div>
      )}

      {d && (
        <div className="kh-than">
          <div className="kh-trai">
            <input className="o kh-tim" value={tim} spellCheck={false}
                   placeholder={tr('Tìm trong kho…')}
                   onChange={e => setTim(e.target.value)} />
            <div className="kh-dem">
              {tr('{0}/{1} nhóm đã mở', d.so_mo, d.so_nhom)}
            </div>
            {nhomHien.map(n => (
              <button key={n.ten}
                      className={'kh-nhom' + (n.ten === nhom?.ten ? ' dang-chon' : '')
                                 + (n.mo ? '' : ' khoa')}
                      onClick={() => setChon(n.ten)}>
                <span className="kh-nhom-ten">{n.ten}</span>
                <span className="kh-nhom-so">{n.muc.length}</span>
              </button>
            ))}

            <div className="kh-muc-ten">{tr('Hành động')}</div>
            {d.lam.map(x => (
              <div key={x.ma} className={'kh-lam' + (x.mo ? '' : ' khoa')}
                   title={tr(x.mo_ta)}>
                <span className="kh-nhom-ten">{tr(x.nhan)}</span>
                {!x.mo && <span className="kh-khoa">{tr('khoá')}</span>}
              </div>
            ))}
          </div>

          <div className="kh-phai">
            {!nhom && <div className="kh-rong">{tr('Không có món nào khớp.')}</div>}
            {nhom && (
              <>
                <div className="kh-dau">
                  <h2>{nhom.ten}</h2>
                  <span className="day" />
                  {!nhom.mo && (
                    <span className="kh-khoa">{tr('chưa mở — chơi tới màn mở nó')}</span>
                  )}
                </div>
                <div className="kh-luoi">
                  {nhom.muc.map(m => (
                    <div className={'kh-the' + (nhom.mo ? '' : ' khoa')} key={m.ma}>
                      {/* ⚠ NHÃN TỪ ĐIỂN DO PHÍA WEB DỊCH, lúc hiện ra. Chúng là
                          hằng đặt ngoài hàm bên Python nên không bọc `tr()` ở đấy
                          được — bọc lúc nạp tệp là chốt cứng một thứ tiếng. Quên
                          `tr()` ở đây thì vỏ tiếng Anh mà tên món vẫn tiếng Việt,
                          và chỉ ảnh chụp mới thấy. Xem `ngon_ngu.py` cuối docstring. */}
                      <div className="kh-the-ten">{tr(m.nhan)}</div>
                      {/* CÂU LEAN THẬT — xem chú thích đầu tệp. */}
                      <code className="kh-lean">{m.lean}</code>
                      <div className="kh-the-chan">
                        {m.ho && <span className="kh-the-ho">{tr(m.ho)}</span>}
                        {!!m.tham_so.length && (
                          <span className="kh-the-ts">
                            {tr('tham số: {0}', m.tham_so.join(', '))}
                          </span>
                        )}
                        {m.don_vi && <span className="kh-the-dv">{tr(m.don_vi)}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export type { NhomKho }
