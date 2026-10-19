import { useEffect, useState } from 'react'
import TitleBar from '../components/TitleBar'
import Icon from '../components/Icon'
import { py } from '../api'
import { tr, trx, useNgonNgu } from '../ngon_ngu'
import type { ChamMan, ManHT } from '../types'
import type { ViecChayMay } from './ManChayMay'

/** MÀN CHẤM — lượt vừa chạy được mấy sao, và vì sao.
 *
 *  ⚠ KHÔNG TÍNH MỘT CON SỐ NÀO Ở ĐÂY. "Mấy sao" là LUẬT CHƠI, mà luật chơi chỉ được
 *  có một bản — `cat_studio/luat_choi.py`. Trang này hỏi rồi bày lại. Tính sao bằng
 *  TypeScript là đẻ bản thứ hai, và hôm hai bản lệch nhau thì bản đồ khoe ba sao mà
 *  sổ điểm ghi hai, chẳng ai biết bên nào đúng.
 *
 *  ⚠ VÀ TUYỆT ĐỐI KHÔNG BÀY NGÀY CỦA MÀN ẨN. Cửa `nop_man` cố ý chỉ trả về ĐIỂM —
 *  không mã lượt, không khoảng ngày. Biết ngày màn ẩn là vặn được cỗ máy cho vừa khít
 *  chính khoảng ấy, và ngôi sao thứ ba mất sạch nghĩa mà vẫn sáng lên y như thật.
 */
export default function ManCham({ man, maLuot, viec, onSuaTiep, onRa }: {
  man: ManHT
  maLuot: string
  /** Cỗ máy vừa chạy — cần để NỘP chạy lại đúng nó trên màn ẩn. */
  viec: ViecChayMay
  onSuaTiep: () => void
  onRa: () => void
}) {
  const nn = useNgonNgu()
  const [d, setD] = useState<ChamMan | null>(null)
  const [loi, setLoi] = useState('')
  const [dangNop, setDangNop] = useState(false)

  useEffect(() => {
    void (async () => {
      const r = await py.cham_man(man.ma, maLuot, viec.steps)
      if (r.ok && r.value) setD(r.value)
      else setLoi(r.error ?? tr('Không chấm được lượt này.'))
    })()
  }, [man.ma, maLuot, viec.steps, nn])

  async function nop() {
    setDangNop(true)
    setLoi('')
    const r = await py.nop_man(man.ma, viec.ten, viec.steps, viec.edges, viec.coMay)
    setDangNop(false)
    if (!r.ok || !r.value) { setLoi(r.error ?? tr('Không nộp được.')); return }
    if (!r.value.ok) { setLoi(r.value.loi ?? tr('Không nộp được.')); return }
    setD(r.value)
  }

  const coTheNop = !!d && !d.khong_cham && !!man.co_man_an
    && !!d.thay?.thang_boss && !d.an

  return (
    <div className="ch">
      <TitleBar tieuDe={tr('Chấm điểm')} menus={[]} them={
        <button className="tb-ve" data-khong-keo onClick={onRa}
                title={tr('Về Hành trình')}>←</button>
      } />

      <div className="ch-than">
        <div className="ch-ten">
          <span className="mono ch-so">{String(man.so).padStart(2, '0')}</span>
          {man.ten}
        </div>

        {loi && <div className="mc-bao loi ch-loi">⚠ {loi}</div>}
        {!d && !loi && (
          <div className="ch-cho"><Icon name="chay" /> {tr('đang chấm…')}</div>
        )}

        {/* MÀN KHÔNG CHẤM — màn 0. Nói thẳng vì sao, đừng bày ba ô sao rỗng rồi để
            người chơi tưởng mình vừa làm sai cái gì. */}
        {d?.khong_cham && (
          <div className="ch-khong-cham">
            {trx('Màn này {0} — nó dạy bạn dựng chính con boss. Mà «Mua rồi giữ» thì '
                 + 'không đóng lệnh nào, nên không có gì để chấm.',
                 <b key="b">{tr('không chấm sao')}</b>)}
          </div>
        )}

        {d && !d.khong_cham && (
          <>
            <Sao n={d.sao} />

            <div className="ch-bang">
              <Dong nhan={tr('Cỗ máy của bạn')} gt={pt(d.thay?.lai_pt)}
                    manh={(d.thay?.lai_pt ?? 0) >= (d.thay?.boss_pt ?? 0)} />
              <Dong nhan={d.boss?.ten ?? tr('Boss')} gt={pt(d.thay?.boss_pt)} />
              <Dong nhan={tr('Lệnh đã đóng')} gt={String(d.thay?.so_dong ?? 0)} />
              {!!d.gon && (
                <Dong nhan={tr('Độ gọn')}
                      gt={`${d.gon.tong} = ${d.gon.so_khoi} ${tr('khối')} + `
                          + `${d.gon.so_num} ${tr('núm')}`}
                      manh={!!man.gon && d.gon.tong <= man.gon} />
              )}
            </div>

            {/* HUY CHƯƠNG GỌN — máy càng ít khối, càng ít núm thì càng khó bị quá
                khớp, nên nó và màn ẩn dạy CÙNG một bài học từ hai phía. */}
            {!!man.gon && !!d.gon && d.sao >= 3 && d.gon.tong <= man.gon && (
              <div className="ch-huy">{tr('Huy chương GỌN — ba sao mà vẫn dưới {0} '
                                          + 'khối cộng núm.', man.gon)}</div>
            )}

            {d.an ? (
              <div className="ch-an">
                <div className="ch-an-dau">{tr('Trên màn ẩn')}</div>
                <Dong nhan={tr('Cỗ máy của bạn')} gt={pt(d.an.lai_pt)}
                      manh={!!d.an.thang_boss} />
                <Dong nhan={d.boss?.ten ?? tr('Boss')} gt={pt(d.an.boss_pt)} />
                <div className="ch-an-cau">
                  {d.an.thang_boss
                    ? tr('Nó còn chạy được trên khoảng ngày nó chưa từng thấy. Đó mới '
                         + 'là chiến thuật.')
                    : tr('Khớp đẹp trên khoảng đã thấy, hụt trên khoảng chưa thấy. Đó '
                         + 'là dấu hiệu cỗ máy đang vẽ lại quá khứ.')}
                </div>
              </div>
            ) : man.co_man_an && (
              <div className="ch-nhac">
                {d.thay?.thang_boss
                  ? tr('Thắng boss rồi. Nộp đi — app sẽ chạy đúng cỗ máy này trên một '
                       + 'khoảng ngày bạn chưa từng thấy.')
                  : tr('Thắng boss trên màn đã thấy rồi mới nộp được.')}
              </div>
            )}
          </>
        )}

        <div className="ch-nut">
          <button className="nut" onClick={onSuaTiep}>{tr('Sửa tiếp')}</button>
          {coTheNop && (
            <button className="nut chinh" disabled={dangNop} onClick={() => void nop()}>
              {dangNop ? tr('đang chạy màn ẩn…') : tr('Nộp')}
            </button>
          )}
          <button className="nut" onClick={onRa}>{tr('Hành trình')}</button>
        </div>
      </div>
    </div>
  )
}

const pt = (x: number | null | undefined) =>
  x == null ? '—' : `${x > 0 ? '+' : ''}${x.toFixed(2)} %`

/** Sao bằng ký hiệu ĐƠN SẮC (★ ☆), không emoji — để ăn theo màu của theme. Cùng lý do
 *  thẻ «khoá» ở bản đồ hành trình dùng chữ chứ không dùng 🔒. */
function Sao({ n }: { n: number }) {
  const k = Math.max(0, Math.min(3, n || 0))
  const nac = [
    tr('chạy sạch'), tr('thắng boss trên màn đã thấy'), tr('và trên màn ẩn cũng thắng'),
  ]
  return (
    <div className="ch-sao">
      <div className="ch-sao-to" title={`${k}/3`}>
        <b>{'★'.repeat(k)}</b>{'☆'.repeat(3 - k)}
      </div>
      <ol className="ch-nac">
        {nac.map((c, i) => (
          <li key={i} className={k > i ? 'dat' : ''}>{c}</li>
        ))}
      </ol>
    </div>
  )
}

function Dong({ nhan, gt, manh }: { nhan: string; gt: string; manh?: boolean }) {
  return (
    <div className="ch-hang">
      <span className="ch-nhan">{nhan}</span>
      <span className={manh ? 'ch-gt manh' : 'ch-gt'}>{gt}</span>
    </div>
  )
}
