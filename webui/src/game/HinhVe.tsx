/** HÌNH VẼ CỦA GAME — chân dung nhân vật, logo, icon linh kiện. SVG tay, NÉT + MÀU THEME.
 *
 * Không emoji, không ảnh tải ngoài: app chạy offline trong WebView2, và emoji mang màu
 * riêng của font hệ thống nên lệch tông với mọi thứ còn lại (xem `components/Icon.tsx`).
 * Màu lấy từ biến `--g-*` trong `theme.css`.
 */

/** Mèo Thợ Cả — thợ cả của xưởng, người dẫn đường. Kính bảo hộ bằng đồng trên trán. */
export function MeoTho({ size = 120 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" aria-label="Mèo Thợ Cả">
      <circle cx="60" cy="60" r="58" style={{ fill: 'var(--g-dem-3)', stroke: 'var(--g-dong-toi)' }} strokeWidth="2" />
      {/* tai */}
      <path d="M28 46 L34 14 L54 34 Z" style={{ fill: 'var(--g-dong)' }} />
      <path d="M92 46 L86 14 L66 34 Z" style={{ fill: 'var(--g-dong)' }} />
      <path d="M33 38 L36 22 L46 33 Z" style={{ fill: 'var(--g-dong-toi)' }} />
      <path d="M87 38 L84 22 L74 33 Z" style={{ fill: 'var(--g-dong-toi)' }} />
      {/* mặt */}
      <ellipse cx="60" cy="66" rx="36" ry="32" style={{ fill: 'var(--g-dong)' }} />
      {/* kính bảo hộ trên trán */}
      <rect x="30" y="34" width="60" height="9" rx="4" style={{ fill: 'var(--g-dong-toi)' }} />
      <circle cx="46" cy="38" r="9" style={{ fill: 'var(--g-dem-2)', stroke: 'var(--g-dong-sang)' }} strokeWidth="3" />
      <circle cx="74" cy="38" r="9" style={{ fill: 'var(--g-dem-2)', stroke: 'var(--g-dong-sang)' }} strokeWidth="3" />
      <circle cx="43" cy="35" r="2.5" style={{ fill: 'var(--g-giay)' }} />
      <circle cx="71" cy="35" r="2.5" style={{ fill: 'var(--g-giay)' }} />
      {/* mắt */}
      <ellipse cx="47" cy="62" rx="5" ry="6" style={{ fill: 'var(--g-dem)' }} />
      <ellipse cx="73" cy="62" rx="5" ry="6" style={{ fill: 'var(--g-dem)' }} />
      <circle cx="48.5" cy="60" r="1.6" style={{ fill: 'var(--g-giay)' }} />
      <circle cx="74.5" cy="60" r="1.6" style={{ fill: 'var(--g-giay)' }} />
      {/* mũi, miệng, râu */}
      <path d="M56 72 L64 72 L60 77 Z" style={{ fill: 'var(--g-dem-2)' }} />
      <path d="M60 77 Q55 83 50 80 M60 77 Q65 83 70 80" fill="none" style={{ stroke: 'var(--g-dem-2)' }} strokeWidth="2" strokeLinecap="round" />
      <path d="M34 72 L18 68 M34 77 L17 79 M86 72 L102 68 M86 77 L103 79" style={{ stroke: 'var(--g-giay-toi)' }} strokeWidth="1.6" strokeLinecap="round" />
      {/* tạp dề thợ */}
      <path d="M36 96 Q60 106 84 96 L80 118 L40 118 Z" style={{ fill: 'var(--g-dong-toi)' }} />
      <circle cx="60" cy="106" r="3" style={{ fill: 'var(--g-dong-sang)' }} />
    </svg>
  )
}

/** Bà Tư — chủ tiệm vàng phố cổ, khách đặt máy. Búi tóc, dây chuyền vàng. */
export function BaTu({ size = 120 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" aria-label="Bà Tư">
      <circle cx="60" cy="60" r="58" style={{ fill: 'var(--g-dem-3)', stroke: 'var(--g-dong-toi)' }} strokeWidth="2" />
      {/* búi tóc + tóc */}
      <circle cx="60" cy="20" r="12" style={{ fill: 'var(--g-dem)' }} />
      <path d="M28 60 Q28 26 60 26 Q92 26 92 60 L88 70 Q84 40 60 40 Q36 40 32 70 Z" style={{ fill: 'var(--g-dem)' }} />
      {/* mặt */}
      <ellipse cx="60" cy="62" rx="27" ry="30" style={{ fill: 'var(--g-giay-toi)' }} />
      <path d="M33 56 Q36 38 60 36 Q84 38 87 56 Q78 44 60 44 Q42 44 33 56 Z" style={{ fill: 'var(--g-dem)' }} />
      {/* mắt, lông mày */}
      <path d="M44 58 Q49 55 54 58" fill="none" style={{ stroke: 'var(--g-dem)' }} strokeWidth="2.2" strokeLinecap="round" />
      <path d="M66 58 Q71 55 76 58" fill="none" style={{ stroke: 'var(--g-dem)' }} strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="49" cy="64" r="2.6" style={{ fill: 'var(--g-dem)' }} />
      <circle cx="71" cy="64" r="2.6" style={{ fill: 'var(--g-dem)' }} />
      {/* miệng mỉm */}
      <path d="M52 78 Q60 84 68 78" fill="none" style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="2.4" strokeLinecap="round" />
      {/* bông tai vàng */}
      <circle cx="32" cy="70" r="3.4" style={{ fill: 'var(--g-dong-sang)' }} />
      <circle cx="88" cy="70" r="3.4" style={{ fill: 'var(--g-dong-sang)' }} />
      {/* áo + dây chuyền */}
      <path d="M26 118 Q30 94 60 92 Q90 94 94 118 Z" style={{ fill: 'var(--g-dong-toi)' }} />
      <path d="M44 94 Q60 108 76 94" fill="none" style={{ stroke: 'var(--g-dong-sang)' }} strokeWidth="2.4" />
      <circle cx="60" cy="104" r="4.5" style={{ fill: 'var(--g-dong-sang)' }} />
    </svg>
  )
}

/** Boss "Mua rồi giữ" — cái két sắt: mua một lần, khoá lại, ngồi im tới cuối năm.
 *  Không làm gì mà vẫn là đối thủ khó nhất của năm vàng lên. */
export function BossMuaGiu({ size = 140 }: { size?: number }) {
  const net = { fill: 'none', strokeLinecap: 'round' as const }
  return (
    <svg width={size} height={size} viewBox="0 0 140 140" aria-label="Boss Mua rồi giữ">
      <circle cx="70" cy="70" r="68" style={{ fill: 'var(--g-dem-3)', stroke: 'var(--g-dong-toi)' }} strokeWidth="2" />
      {/* chân két */}
      <rect x="36" y="110" width="14" height="10" rx="2" style={{ fill: 'var(--g-dem)' }} />
      <rect x="90" y="110" width="14" height="10" rx="2" style={{ fill: 'var(--g-dem)' }} />
      {/* thân két */}
      <rect x="26" y="30" width="88" height="84" rx="9" style={{ fill: 'var(--g-khoa)', stroke: 'var(--g-dem)' }} strokeWidth="3" />
      <rect x="35" y="39" width="70" height="66" rx="6" style={{ fill: 'var(--g-dem-3)', stroke: 'var(--g-dong-toi)' }} strokeWidth="1.5" />
      {/* bản lề */}
      <rect x="22" y="46" width="7" height="14" rx="2" style={{ fill: 'var(--g-dong-toi)' }} />
      <rect x="22" y="84" width="7" height="14" rx="2" style={{ fill: 'var(--g-dong-toi)' }} />
      {/* lông mày gắt + mắt */}
      <path d="M45 54 L61 59 M95 54 L79 59" {...net} style={{ stroke: 'var(--g-dong-sang)' }} strokeWidth="4" />
      <circle cx="55" cy="65" r="4.5" style={{ fill: 'var(--g-dong-sang)' }} />
      <circle cx="85" cy="65" r="4.5" style={{ fill: 'var(--g-dong-sang)' }} />
      {/* núm xoay mã khoá */}
      <circle cx="70" cy="88" r="12" style={{ fill: 'var(--g-dong)', stroke: 'var(--g-dong-toi)' }} strokeWidth="3" />
      <path d="M70 76 L70 81 M82 88 L77 88 M70 100 L70 95 M58 88 L63 88" {...net}
            style={{ stroke: 'var(--g-dem)' }} strokeWidth="2" />
      <circle cx="70" cy="88" r="3" style={{ fill: 'var(--g-dem)' }} />
      {/* tay nắm */}
      <path d="M96 80 L96 96" {...net} style={{ stroke: 'var(--g-dong-sang)' }} strokeWidth="4" />
      {/* thỏi vàng trên nóc */}
      <path d="M52 30 L58 20 L82 20 L88 30 Z" style={{ fill: 'var(--g-dong-sang)', stroke: 'var(--g-dong-toi)' }} strokeWidth="1.5" />
    </svg>
  )
}

/** Chân dung theo mã nhân vật (`meo`, `ba_tu`). */
export function ChanDung({ ai, size = 120 }: { ai: string; size?: number }) {
  return ai === 'ba_tu' ? <BaTu size={size} /> : <MeoTho size={size} />
}

/** Logo màn hình chính: bánh răng đồng + đường giá + đồng xu. */
export function LogoGame({ size = 168 }: { size?: number }) {
  const rang = Array.from({ length: 12 }, (_, k) => {
    const g = (k * 30 * Math.PI) / 180
    const x = 84 + Math.cos(g) * 66, y = 84 + Math.sin(g) * 66
    return <rect key={k} x={x - 7} y={y - 7} width="14" height="14" rx="3"
                 transform={`rotate(${k * 30} ${x} ${y})`} style={{ fill: 'var(--g-dong-toi)' }} />
  })
  return (
    <svg width={size} height={size} viewBox="0 0 168 168" aria-label="Cat Studio">
      {rang}
      <circle cx="84" cy="84" r="62" style={{ fill: 'var(--g-dem-2)', stroke: 'var(--g-dong)' }} strokeWidth="4" />
      <circle cx="84" cy="84" r="50" fill="none" style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="1.5" strokeDasharray="3 5" />
      <polyline points="40,110 58,96 70,102 86,74 100,84 116,56 128,62" fill="none"
                style={{ stroke: 'var(--g-dong-sang)' }} strokeWidth="5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx="116" cy="56" r="6" style={{ fill: 'var(--g-dong-sang)' }} />
      {/* tai mèo trên vành */}
      <path d="M50 30 L60 6 L74 26 Z" style={{ fill: 'var(--g-dong)' }} />
      <path d="M118 30 L108 6 L94 26 Z" style={{ fill: 'var(--g-dong)' }} />
    </svg>
  )
}

/** Ổ khoá nhỏ — màn / chương chưa mở. */
export function IconKhoa({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-label="đang khoá">
      <path d="M6 9 V6.5 a4 4 0 0 1 8 0 V9" fill="none" stroke="currentColor" strokeWidth="2" />
      <rect x="4" y="9" width="12" height="9" rx="2" fill="currentColor" />
    </svg>
  )
}

/** Cảnh nền của truyện: gian trong tiệm vàng — cửa sổ tròn nhìn ra "thị trường" (một
 *  đường giá mờ), kệ thỏi vàng hai bên, đèn lồng, quầy gỗ. Phủ kín khung (`slice`). */
export function CanhTiemVang() {
  const thoi = (x: number, y: number, k: number) => (
    <path key={k} d={`M${x} ${y} l6 -12 h26 l6 12 z`}
          style={{ fill: 'var(--g-dong)', stroke: 'var(--g-dong-toi)' }} strokeWidth="1.5" />
  )
  const ke = (x0: number) => [0, 1, 2].map(h => (
    <g key={`${x0}-${h}`}>
      <rect x={x0} y={150 + h * 92} width={210} height={8} rx={2} style={{ fill: 'var(--g-dong-toi)' }} />
      {[0, 1, 2, 3].map(i => (h + i) % 3 !== 2 && thoi(x0 + 10 + i * 50, 150 + h * 92, i))}
    </g>
  ))
  return (
    <svg className="g-canh" viewBox="0 0 1200 600" preserveAspectRatio="xMidYMid slice" aria-hidden>
      <defs>
        <clipPath id="g-cua-tron"><circle cx="600" cy="230" r="150" /></clipPath>
        <radialGradient id="g-den-sang">
          <stop offset="0" style={{ stopColor: 'var(--g-dong-sang)', stopOpacity: 0.55 }} />
          <stop offset="1" style={{ stopColor: 'var(--g-dong-sang)', stopOpacity: 0 }} />
        </radialGradient>
      </defs>
      <rect width="1200" height="600" style={{ fill: 'var(--g-dem-2)' }} />
      {/* cửa sổ tròn — ngoài kia là thị trường */}
      <circle cx="600" cy="230" r="150" style={{ fill: 'var(--g-dem)' }} />
      <g clipPath="url(#g-cua-tron)">
        <polyline points="440,300 480,270 510,285 545,230 580,250 615,190 650,215 690,160 720,175 770,120"
                  fill="none" style={{ stroke: 'var(--g-dong)' }} strokeWidth="5" opacity=".55"
                  strokeLinejoin="round" />
        {[-100, -50, 0, 50, 100].map(d => (
          <line key={'d' + d} x1={600 + d} x2={600 + d} y1="70" y2="390"
                style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="3" />
        ))}
        {[-80, 0, 80].map(d => (
          <line key={'n' + d} y1={230 + d} y2={230 + d} x1="440" x2="760"
                style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="3" />
        ))}
      </g>
      <circle cx="600" cy="230" r="150" fill="none" style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="10" />
      {/* kệ thỏi vàng */}
      {ke(90)}
      {ke(900)}
      {/* đèn lồng */}
      {[330, 870].map(x => (
        <g key={x}>
          <line x1={x} x2={x} y1="0" y2="62" style={{ stroke: 'var(--g-dong-toi)' }} strokeWidth="2" />
          <circle cx={x} cy="96" r="70" fill="url(#g-den-sang)" />
          <ellipse cx={x} cy="94" rx="20" ry="28" style={{ fill: 'var(--g-dong-sang)' }} opacity=".9" />
          <rect x={x - 12} y="62" width="24" height="6" rx="2" style={{ fill: 'var(--g-dong-toi)' }} />
        </g>
      ))}
      {/* quầy */}
      <rect x="0" y="470" width="1200" height="130" style={{ fill: 'var(--g-dem-3)' }} />
      <rect x="0" y="462" width="1200" height="12" style={{ fill: 'var(--g-dong-toi)' }} />
    </svg>
  )
}

/** Icon linh kiện cho khay trong xưởng. */
export function IconLinhKien({ loai, size = 30 }: { loai: string; size?: number }) {
  const net = { fill: 'none', stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round' as const,
                strokeLinejoin: 'round' as const }
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      {loai === 'mat' && <>
        <path d="M3 16 Q16 4 29 16 Q16 28 3 16 Z" {...net} />
        <circle cx="16" cy="16" r="5" {...net} />
        <circle cx="16" cy="16" r="1.6" fill="currentColor" />
      </>}
      {loai === 'tay_vao' && <>
        <path d="M6 26 L6 14 Q6 10 10 10 L18 10" {...net} />
        <path d="M14 6 L19 10 L14 14" {...net} />
        <path d="M22 18 L28 18 M25 15 L25 21" {...net} />
        <rect x="4" y="24" width="12" height="4" rx="1.5" {...net} />
      </>}
      {loai === 'tay_sua' && <>
        <path d="M20 4 a6 6 0 0 0 -5 9 L5 23 a2.5 2.5 0 0 0 4 4 L19 17 a6 6 0 0 0 9 -5 l-4 2 -3 -3 2 -4 Z" {...net} />
      </>}
      {loai === 'tham_so' && <>
        <circle cx="16" cy="16" r="10" {...net} />
        <path d="M16 16 L22 10" {...net} />
        <path d="M8 22 L10 20 M24 22 L22 20 M16 6 L16 8" {...net} />
      </>}
    </svg>
  )
}
