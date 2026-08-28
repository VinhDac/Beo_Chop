import { useState } from 'react'
import { py } from '../api'
import type { CaiDatKhop } from '../types'

/** MÔ HÌNH KHỚP — bốn con số quyết định backtest thật hay ảo tưởng.
 *
 *  ⚠ TAB NÀY LÀ MẶT KIA CỦA TAB "NGUỒN DỮ LIỆU". Ở đó luật là *"đo được thì đừng
 *  hỏi"* — độ trễ, spread, lệch đồng hồ đều app tự đo, hỏi là mời gõ sai rồi tin nó.
 *  Ở đây luật ngược lại và cũng bắt buộc y như vậy: **không đo được thì đừng giấu.**
 *
 *  Ba trong bốn ô dưới đây là thứ dữ liệu L1 KHÔNG BAO GIỜ trả lời được. Chôn chúng
 *  thành hằng số trong `khop_lenh.py` thì chúng vẫn quyết định toàn bộ bảng lãi lỗ —
 *  chỉ khác là không ai biết chúng tồn tại để mà nghi ngờ.
 *
 *  Vì thế mỗi ô đi kèm một câu nói rõ **vặn sai về phía nào thì mất tiền**, chứ không
 *  chỉ là một cái nhãn. Một con số không có ngữ cảnh thì không chỉnh được.
 */

/** Một ô số + câu giải thích. `ĐO ĐƯỢC` / `PHẢI ĐOÁN` là nhãn quan trọng nhất trên
 *  màn hình này — nó nói cho người dùng biết con số nào đáng tin. */
function O({ nhan, don_vi, gt, dat, doan, mo_ta, buoc, min, max }: {
  nhan: string; don_vi: string; gt: number; dat: (v: number) => void
  doan?: boolean; mo_ta: React.ReactNode
  buoc?: number; min?: number; max?: number
}) {
  return (
    <div className="k-o">
      <div className="hang">
        <span className="nhan-o k-nhan">{nhan}</span>
        <input className="o o-so" type="number" value={gt}
               step={buoc ?? 0.1} min={min} max={max}
               onChange={e => {
                 const v = Number(e.target.value)
                 if (Number.isFinite(v)) dat(v)
               }} />
        <span className="chu-mo">{don_vi}</span>
        <span className={'k-the' + (doan ? ' doan' : '')}>
          {doan ? 'PHẢI ĐOÁN' : 'TRA ĐƯỢC'}
        </span>
      </div>
      <div className="k-mo-ta">{mo_ta}</div>
    </div>
  )
}

export default function KhopPanel({ khop, dat }: {
  khop: CaiDatKhop
  dat: (k: keyof CaiDatKhop, v: number) => void
}) {
  const [dangTra, setDangTra] = useState(false)

  async function veMacDinh() {
    setDangTra(true)
    const r = await py.khop_mac_dinh()
    setDangTra(false)
    if (r.ok && r.value) {
      const k = (r.value as Record<string, any>).khop as CaiDatKhop
      for (const t of Object.keys(k) as (keyof CaiDatKhop)[]) dat(t, k[t])
    }
  }

  return (
    <div className="khop-panel">
      <div className="chu-dan">
        Câu hỏi mà mô hình khớp phải trả lời là <b>“lệnh của ta xếp thứ mấy trong hàng
        đợi?”</b> — và dữ liệu đỉnh sổ lệnh <b>không chứa câu trả lời</b>. Bốn ô dưới
        đây là toàn bộ phần app phải đoán. Chúng in kèm mọi kết quả backtest.
      </div>

      <O nhan="Phí maker" don_vi="bps" gt={khop.phi_maker_bps} buoc={0.1}
         dat={v => dat('phi_maker_bps', v)}
         mo_ta={<>
           2,0 bps = 0,02%, biểu phí chuẩn của Binance · Bybit · OKX. <b>Số ÂM là
           rebate</b> — sàn trả cho ta, và đó thường là thứ duy nhất làm market making
           có lãi được; phải vào chương trình Market Maker mới có, không phải hạng VIP
           thường. Đối chiếu với spread thật bằng <code>tools/do_spread.py</code>:
           spread phải hơn <b>hai lần</b> con số này.
         </>} />

      <O nhan="Độ trễ ra" don_vi="ms" gt={khop.tre_ra_ms} buoc={0.5} min={0} doan
         dat={v => dat('tre_ra_ms', v)}
         mo_ta={<>
           Từ lúc chiến lược quyết tới lúc lệnh <b>nằm ở sàn</b>. Không đo được nếu chưa
           từng gửi lệnh thật. Mọi thứ xảy ra trong quãng này là cơ hội ta không với
           tới — đặt quá thấp là tự cho mình phản xạ nhanh hơn thực tế.
         </>} />

      <O nhan="Huỷ ở TRƯỚC ta" don_vi="tỉ lệ 0–1" gt={khop.phan_huy_truoc}
         buoc={0.1} min={0} max={1} doan
         dat={v => dat('phan_huy_truoc', v)}
         mo_ta={<>
           <b>Núm quan trọng nhất.</b> Khi khối lượng ở mức của ta biến mất mà không có
           lệnh khớp nào giải thích, tức người ta huỷ — họ đứng trước hay sau ta?
           <br />
           <b>0</b> bi quan: huỷ đều ở sau, vị trí của ta không bao giờ tự tốt lên ·
           <b> 0,5</b> rải đều · <b>1</b> lạc quan: ta tiến lên đầu hàng rất nhanh.
           <br />
           Chạy lại cả ba mức rồi nhìn khoảng cách — <b>đó chính là phần backtest không
           biết</b>. Vặn về phía lạc quan là đem tiền thật ra trả học phí.
         </>} />

      <O nhan="Mức sâu đứng trước ta" don_vi="tỉ lệ 0–1" gt={khop.phan_muc_sau}
         buoc={0.1} min={0} max={1} doan
         dat={v => dat('phan_muc_sau', v)}
         mo_ta={<>
           Treo <b>sâu hơn đỉnh</b> thì bao nhiêu phần của mức đó nằm trước ta? Đỉnh sổ
           lệnh không thấy tầng dưới, nên đây là con số mượn tạm của tầng trên. 1 = cả
           mức đứng trước ta. Chiến lược treo cách công bằng nửa spread rơi vào ca này
           thường xuyên.
         </>} />

      <div className="hang">
        <button className="nut" onClick={veMacDinh} disabled={dangTra}>
          Về mặc định (bi quan)
        </button>
        <span className="chu-mo">
          Vặn thử rồi quên vặn về thì mọi kết quả sau đó lạc quan hơn sự thật.
        </span>
      </div>
    </div>
  )
}
