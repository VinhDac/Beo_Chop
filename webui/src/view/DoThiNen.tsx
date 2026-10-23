/* BIỂU ĐỒ NẾN của cửa sổ View — nến thật LEAN in ra, và lệnh thật nằm đúng chỗ.
 *
 * ⚠ TRỤC X ĐI THEO SỐ THỨ TỰ NẾN, không theo giờ. Vàng không giao dịch cuối tuần,
 * nên chia trục theo giờ là mỗi thứ Hai hở một khoảng trắng bằng hai ngày — biểu đồ
 * giá nào cũng xếp đều nến cạnh nhau vì lý do ấy.
 *
 * ⚠ CHỈ VẼ MỘT CỬA SỔ NẾN, không vẽ cả lượt. Ba năm vàng là 941 nến; nhét hết vào
 * 900 pixel thì mỗi nến chưa đầy một pixel, và cái «biểu đồ nến» ấy chỉ còn là một
 * vệt. Tua tới đâu thì bày cửa sổ nến quanh đó — đúng cách một màn chạy thật nhìn.
 */
import { memo, useMemo } from 'react'
import type { MachView } from './mach_view'
import { tr } from '../ngon_ngu'

const MAU_LEN = '#22ab94'
const MAU_XUONG = '#f23645'
/** Màu cho đại lượng vẽ chồng lên nến. Cố ý KHÔNG dùng xanh/đỏ: hai màu ấy đã mang
 *  nghĩa lên/xuống trên chính cây nến, mượn lại là một đường trung bình trượt trông
 *  như đang nói điều gì đó về lãi lỗ. */
const MAU_CHONG = ['#6aa5f5', '#ffa657', '#c792ea', '#80cbc4']

/** Mép biểu đồ: chừa chỗ cho trục giá bên phải và trục ngày bên dưới. */
const L = 8, R = 72, T = 10, B = 22

/** Ba kiểu vẽ của cửa sổ Tester cũ. Giữ cả ba: nến đọc được thân với bóng, thanh
 *  gọn hơn khi nến chen nhau, còn đường thì nhìn ra hình dáng cả đoạn nhanh nhất. */
export type KieuVe = 'nen' | 'bar' | 'line'

export interface DoThiNenProps {
  mach: MachView
  /** Nến đang đứng. */
  chiSo: number
  /** Bao nhiêu nến bày một lúc. */
  cua: number
  kieu: KieuVe
  rong: number
  cao: number
}

function DoThiNen({ mach, chiSo, cua, kieu, rong, cao }: DoThiNenProps) {
  const { nhip } = mach
  const d = useMemo(() => {
    const het = Math.min(nhip.length, chiSo + 1)
    const dau = Math.max(0, het - cua)
    const lat = nhip.slice(dau, het)
    let thap = Infinity, caoNhat = -Infinity
    for (const n of lat) {
      if (n.nen[2] < thap) thap = n.nen[2]
      if (n.nen[1] > caoNhat) caoNhat = n.nen[1]
    }
    if (!Number.isFinite(thap)) { thap = 0; caoNhat = 1 }
    // Chừa 4% trên dưới: nến chạm sát mép trông như bị cắt.
    const dem = (caoNhat - thap) * 0.04 || 1
    thap -= dem; caoNhat += dem
    return { dau, het, lat, thap, cao: caoNhat }
  }, [nhip, chiSo, cua])

  if (!d.lat.length) return <div className="view-trong">{tr('chưa có nến nào')}</div>

  const W = Math.max(240, rong), H = Math.max(140, cao)
  const buoc = (W - L - R) / Math.max(1, d.lat.length)
  const rNen = Math.max(0.5, buoc * 0.33)
  const px = (i: number) => L + (i + 0.5) * buoc
  const py = (gia: number) =>
    T + (d.cao - gia) / (d.cao - d.thap) * (H - T - B)

  // Năm mốc giá bên phải — đủ đọc, không rối.
  const moc = Array.from({ length: 5 }, (_, k) => d.thap + (d.cao - d.thap) * k / 4)

  return (
    <svg className="view-do-thi" viewBox={`0 0 ${W} ${H}`} width={W} height={H}>
      {moc.map((g, k) => (
        <g key={k}>
          <line x1={L} y1={py(g)} x2={W - R} y2={py(g)} className="view-luoi" />
          <text x={W - R + 6} y={py(g) + 4} className="view-nhan-truc">
            {g.toFixed(2)}
          </text>
        </g>
      ))}

      {kieu === 'line' ? (
        <path className="view-duong"
              d={d.lat.map((n, i) =>
                `${i ? 'L' : 'M'}${px(i).toFixed(1)} ${py(n.nen[3]).toFixed(1)}`
              ).join(' ')} />
      ) : d.lat.map((n, i) => {
        const len = n.nen[3] >= n.nen[0]
        const mau = len ? MAU_LEN : MAU_XUONG
        const x = px(i)
        const tren = py(Math.max(n.nen[0], n.nen[3]))
        const duoi = py(Math.min(n.nen[0], n.nen[3]))
        return (
          <g key={d.dau + i}>
            <line x1={x} y1={py(n.nen[1])} x2={x} y2={py(n.nen[2])}
                  stroke={mau} strokeWidth={1} />
            {kieu === 'nen' ? (
              <rect x={x - rNen} y={tren} width={rNen * 2}
                    height={Math.max(1, duoi - tren)} fill={mau} />
            ) : (
              /* THANH: hai gạch con — mở bên trái, đóng bên phải. Cùng một cây nến,
                 ít mực hơn, nên đọc được khi nến chen sát nhau. */
              <>
                <line x1={x - rNen} y1={py(n.nen[0])} x2={x} y2={py(n.nen[0])}
                      stroke={mau} strokeWidth={1} />
                <line x1={x} y1={py(n.nen[3])} x2={x + rNen} y2={py(n.nen[3])}
                      stroke={mau} strokeWidth={1} />
              </>
            )}
          </g>
        )
      })}

      {/* ĐẠI LƯỢNG CÙNG THANG GIÁ — trung bình trượt, dải, đỉnh/đáy N nến — vẽ
          CHỒNG lên nến, vì chúng đo cùng một thứ. `sinh_ma` đã quyết cái nào thuộc
          nhóm này (nó đọc `hoi.DON_VI_GIA`), nên ở đây không suy gì cả.
          ⚠ Chỗ trống thì CẮT ĐƯỜNG: chỉ báo chưa chín thì LEAN không in nhịp ấy, nối
          thẳng qua là vẽ một đoạn chưa từng có. */}
      {mach.chong.map((h, k) => {
        const khuc: string[] = []
        let cur = ''
        for (let i = 0; i < d.lat.length; i++) {
          const v = h.gt[d.dau + i]
          if (v === null || v === undefined) { if (cur) { khuc.push(cur); cur = '' } continue }
          cur += `${cur ? 'L' : 'M'}${px(i).toFixed(1)} ${py(v).toFixed(1)} `
        }
        if (cur) khuc.push(cur)
        return khuc.map((q, j) => (
          <path key={`${h.ten}-${j}`} d={q.trim()} className="view-chong"
                stroke={MAU_CHONG[k % MAU_CHONG.length]} />
        ))
      })}

      {/* MỨC GIÁ LỆNH CÒN TREO — kẻ ngang suốt khung, ở ĐÚNG MỨC GIÁ.
          CAM, và cam chỉ làm đúng việc này: mức duy nhất chưa có tốt hay xấu. Màu
          xanh/đỏ để dành cho cây nến và cho lãi/lỗ, mượn sang đây là một mức giá
          trông như đang nói nó tốt hay xấu — mà nó chưa là gì cả, nó đang chờ. */}
      {d.lat[d.lat.length - 1]?.cho.map(l => (
        <g key={'cho' + String(l.id)}>
          <line x1={L} y1={py(Number(l.gia))} x2={W - R} y2={py(Number(l.gia))}
                className="view-muc-cho" />
          <text x={L + 4} y={py(Number(l.gia)) - 4} className="view-nhan-cho">
            {l.loai} {l.gia}
          </text>
        </g>
      ))}

      {/* LỆNH THẬT. Mỗi lệnh một mũi tên ở đúng nến và đúng giá LEAN ghi — đây là
          thứ cả cửa sổ này sinh ra để xem. */}
      {d.lat.map((n, i) => n.lenh.map(l => {
        const mua = Number(l.so_luong) > 0
        const x = px(i), y = py(Number(l.gia))
        const h = 7
        return (
          <polygon
            key={String(l.id)}
            points={mua ? `${x},${y - h} ${x - h},${y + h} ${x + h},${y + h}`
                        : `${x},${y + h} ${x - h},${y - h} ${x + h},${y - h}`}
            className={'view-lenh' + (l.hop_le ? '' : ' tu-choi')}
            fill={mua ? MAU_LEN : MAU_XUONG}
          >
            <title>{`${l.luc} · ${l.loai} · ${l.gia}\n${l.tag}`}</title>
          </polygon>
        )
      }))}

      {/* ĐẦU PHÁT — nến đang đứng. */}
      <line x1={px(d.lat.length - 1)} y1={T} x2={px(d.lat.length - 1)} y2={H - B}
            className="view-dau-phat" />
    </svg>
  )
}

export default memo(DoThiNen)
