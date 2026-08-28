import { useEffect, useMemo, useState } from 'react'
import { py } from '../api'
import type { KhoDanhMuc } from '../types'
import Modal from './Modal'

/** Hộp thoại KHO — "app đang có những gì".
 *
 *  Dữ liệu do `kho/` bên Python tự gom từ các module con, nên thêm một engine mới là
 *  hộp thoại có ngay — KHÔNG có danh sách nào viết cứng ở đây. Đó là điểm mấu chốt:
 *  một cái kho mà phải cập nhật bằng tay thì sớm muộn nó nói khác thực tế.
 */

/** Nhãn sơ đồ. Bảng NHỎ và nằm ở đây thay vì lấy từ `bootstrap` vì hộp thoại Kho
 *  không nhận `boot` — nó là bảng tra cứu tĩnh, mở ra đọc rồi đóng. Sai lệch với
 *  `core.TAB_LABELS` thì chỉ lệch một cái nhãn trong bảng tra, không lệch hành vi. */
const TEN_TAB: Record<string, string> = { bao_gia: 'Quote' }

function Muc({ ten, phu, children }: {
  ten: string; phu?: string; children: React.ReactNode
}) {
  return (
    <div className="kho-muc">
      <div className="kho-dau">
        <span className="kho-ten">{ten}</span>
        {phu && <span className="kho-phu">{phu}</span>}
      </div>
      {children}
    </div>
  )
}

export default function KhoDialog({ onDong }: { onDong: () => void }) {
  const [d, setD] = useState<KhoDanhMuc | null>(null)
  const [loi, setLoi] = useState('')

  useEffect(() => {
    py.kho_danh_muc().then(r => (r.ok ? setD(r.value!) : setLoi(r.error ?? 'error')))
  }, [])

  /** Gom toán hạng theo NGUỒN rồi tới NHÓM — nhìn ra ngay thứ gì luôn có, thứ gì
   *  đến từ một chiến lược cụ thể. */
  const theoNguon = useMemo(() => {
    if (!d) return []
    return d.module.map(m => ({
      m,
      nhom: [...new Map(
        d.toan_hang.filter(t => t.nguon === m.ma_so)
          .map(t => [t.nhom, d.toan_hang.filter(
            x => x.nguon === m.ma_so && x.nhom === t.nhom)]),
      ).entries()],
      chi_bao: d.chi_bao.filter(c => c.nguon === m.ma_so),
      bang: d.bang_trang_thai.filter(b => b.nguon === m.ma_so),
    }))
  }, [d])

  return (
    <Modal title="Library — what the app has" width={900} onClose={onDong}
           footer={<button className="nut chinh" onClick={onDong}>Close</button>}>
      {loi && <div className="loi-form">✖ {loi}</div>}
      {!d && !loi && <div className="dong rong">loading…</div>}

      {d && (
        <div className="kho">
          <div className="chu-dan">
            Python <b>gathers</b> this list from the <code>kho/</code> folder itself.
            A new strategy = one more file in there, and it shows up below at once —
            no list is copied by hand, so it cannot disagree with reality.
          </div>

          {theoNguon.map(({ m, nhom, chi_bao, bang }) => (
            <Muc key={m.ma_so}
                 ten={m.ten}
                 phu={m.la_engine ? 'ENGINE' : 'shared'}>
              <div className="kho-mota">{m.mo_ta}</div>
              {m.nguon && <div className="kho-nguon">source: <code>{m.nguon}</code></div>}

              {chi_bao.length > 0 && (
                <table className="kho-bang">
                  <thead><tr><th>Indicator</th><th>Params</th><th>Formula</th></tr></thead>
                  <tbody>
                    {chi_bao.map(c => (
                      <tr key={c.key}>
                        <td>{c.nhan}</td>
                        <td className="mono">{c.tham_so.join(' · ') || '—'}</td>
                        <td className="kho-mota">{c.cong_thuc ?? ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {nhom.map(([g, ds]) => (
                <table className="kho-bang" key={g}>
                  <thead><tr>
                    <th>Operand · {g}</th><th>Params</th><th>Used in</th>
                  </tr></thead>
                  <tbody>
                    {ds.map(t => (
                      <tr key={t.key}>
                        <td title={t.mo_ta}>{t.nhan}
                          {t.dung_sai && <span className="kho-cheo">true/false</span>}</td>
                        <td className="mono">{t.tham_so.join(' · ') || '—'}</td>
                        <td>{t.tabs ? t.tabs.map(x => TEN_TAB[x]).join(', ') : 'all'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ))}

              {bang.map(b => (
                <div key={b.key}>
                  <div className="kho-dau2">State table · {b.nhan}</div>
                  <div className="kho-mota">{b.mo_ta}</div>
                  <table className="kho-bang">
                    <thead><tr><th>Field</th><th>Type</th><th>Note</th></tr></thead>
                    <tbody>
                      {b.truong.map(t => (
                        <tr key={t.ten}>
                          <td className="mono">{t.ten}</td><td>{t.kieu}</td>
                          <td className="kho-mota">{t.vd}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <ul className="kho-luat">
                    {b.luat.map((l, i) => <li key={i}>{l}</li>)}
                  </ul>
                </div>
              ))}
            </Muc>
          ))}

          <Muc ten="Actions" phu="which diagram each one belongs to">
            <table className="kho-bang">
              <thead><tr><th>Action</th><th>Diagram</th></tr></thead>
              <tbody>
                {d.hanh_dong.map(h => (
                  <tr key={h.key}>
                    <td>{h.nhan}</td>
                    <td>{h.tabs.map(x => TEN_TAB[x]).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Muc>

          {/* ⚠ HAI MỤC ĐÃ ĐI ở đợt 3 của lần dọn sang HFT market maker:
              · "Từ vựng"  — phép so · đơn vị khoảng cách · chế độ Sửa lệnh;
              · "Sổ lệnh"  — trạng thái lệnh và lý do đóng, cùng lời giải thích vì sao
                             lệnh mang id CỦA TA (`L-0001`) chứ không mượn ticket MT5:
                             nhờ vậy "vùng này đã sinh lệnh" là một phép TRA BẢNG chứ
                             không phải đoán như `HasOpenPosition()` của D_02.
              Cả hai vẽ từ những bảng `api.kho_danh_muc` không còn gửi nữa.
              Xem `tai_lieu/o_cam_trong.md`. */}

          <Muc ten="Storage" phu={d.luu_tru.goc}>
            <table className="kho-bang">
              <thead><tr><th>Folder</th><th>Count</th><th>Path</th></tr></thead>
              <tbody>
                {d.luu_tru.muc.map(m => (
                  <tr key={m.ten}>
                    <td>{m.ten}
                      {m.danh_sach.length > 0 &&
                        <div className="kho-mota">{m.danh_sach.join(' · ')}</div>}
                    </td>
                    <td>{m.so_luong}</td>
                    <td className="mono kho-mota">{m.duong_dan}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Muc>
        </div>
      )}
    </Modal>
  )
}
