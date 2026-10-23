/** ÂM THANH — dựng bằng WebAudio, KHÔNG có một file nhạc nào.
 *
 *  ⚠ VÌ SAO KHÔNG DÙNG FILE. Cả dự án trước mốc này có đúng không file âm thanh nào, và
 *  thêm chúng vào là thêm vài trăm KB tài nguyên phải đóng gói, phải cấp phép, phải nhớ
 *  chép vào bản `dist`. Mấy tiếng app này cần — một cú tách, một tiếng van đóng, một
 *  chuỗi ba nốt khi ăn sao — đều là sóng đơn giản, dựng tại chỗ bằng mấy chục dòng thì
 *  gọn hơn hẳn, và đổi được bằng cách sửa một con số.
 *
 *  ⚠ KHÔNG BẬT ÂM THANH TRƯỚC CÚ BẤM ĐẦU TIÊN. Trình duyệt (và WebView2) CHẶN
 *  `AudioContext` cho tới khi người dùng chạm vào trang — gọi sớm thì context sinh ra ở
 *  trạng thái `suspended` và mọi tiếng sau đó im lặng, không lỗi, không cảnh báo. Nên
 *  context chỉ dựng ở lần `keu()` ĐẦU TIÊN, và lần ấy luôn nằm sau một cú bấm.
 *
 *  ⚠ VÀ IM LẶNG KHÔNG ĐƯỢC PHÉP LÀM HỎNG GÌ. Máy không có loa, trình duyệt chặn, người
 *  dùng tắt tiếng — cả ba đều bình thường. Mọi lỗi ở đây nuốt hết: một cái app vẽ sơ đồ
 *  không được chết vì không kêu được.
 */

/** Bật/tắt. Giao diện đọc từ Cài đặt rồi gọi `dat_tieng`. */
let bat = true
let ctx: AudioContext | null = null

export function dat_tieng(v: unknown) {
  bat = v !== false
}

export function co_tieng(): boolean {
  return bat
}

function lay(): AudioContext | null {
  if (!bat) return null
  try {
    if (!ctx) {
      const A = window.AudioContext
        ?? (window as unknown as { webkitAudioContext?: typeof AudioContext })
          .webkitAudioContext
      if (!A) return null
      ctx = new A()
    }
    // Context có thể bị treo lại sau khi cửa sổ mất tiêu điểm — đánh thức mỗi lần.
    if (ctx.state === 'suspended') void ctx.resume()
    return ctx
  } catch {
    return null
  }
}

/** Một nốt: sóng `dang`, từ tần số `f0` tới `f1`, dài `giay`, to `to`. */
function not(f0: number, f1: number, giay: number, to: number,
             dang: OscillatorType = 'sine', tre = 0) {
  const c = lay()
  if (!c) return
  try {
    const t = c.currentTime + tre
    const o = c.createOscillator()
    const g = c.createGain()
    o.type = dang
    o.frequency.setValueAtTime(f0, t)
    if (f1 !== f0) o.frequency.exponentialRampToValueAtTime(Math.max(1, f1), t + giay)
    // Lên nhanh rồi tắt dần: không có đoạn lên thì nghe thành tiếng "bụp" của loa.
    g.gain.setValueAtTime(0.0001, t)
    g.gain.exponentialRampToValueAtTime(to, t + 0.008)
    g.gain.exponentialRampToValueAtTime(0.0001, t + giay)
    o.connect(g).connect(c.destination)
    o.start(t)
    o.stop(t + giay + 0.02)
  } catch {
    /* không kêu được thì thôi — xem chú thích đầu tệp */
  }
}

/** Tiếng động KHÔNG cao độ (tách, cạch) — nhiễu trắng cắt ngắn. */
function cach(giay: number, to: number, loc: number) {
  const c = lay()
  if (!c) return
  try {
    const n = Math.max(1, Math.floor(c.sampleRate * giay))
    const buf = c.createBuffer(1, n, c.sampleRate)
    const d = buf.getChannelData(0)
    for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / n)
    const s = c.createBufferSource()
    s.buffer = buf
    const f = c.createBiquadFilter()
    f.type = 'lowpass'
    f.frequency.value = loc
    const g = c.createGain()
    g.gain.value = to
    s.connect(f).connect(g).connect(c.destination)
    s.start()
  } catch {
    /* im lặng */
  }
}

/** Mọi tiếng của app. Tên theo VIỆC, không theo âm — đổi âm thì chỗ gọi không phải sửa. */
export const keu = {
  /** Thả một khối xuống canvas. */
  tha: () => cach(0.05, 0.1, 2200),
  /** Nối xong một sợi dây. */
  noi: () => not(520, 780, 0.09, 0.07, 'triangle'),
  /** Ngắt một sợi dây. */
  ngat: () => not(420, 180, 0.1, 0.06, 'triangle'),
  /** Van MỞ — dòng đi tiếp. */
  van_mo: () => not(640, 960, 0.07, 0.045, 'sine'),
  /** Van ĐÓNG — dòng dừng ở đây. Tiếng *cạch*, không cao độ. */
  van_dong: () => cach(0.045, 0.085, 900),
  /** Một lệnh nổ. */
  lenh: () => not(300, 170, 0.13, 0.085, 'square'),
  /** Đồng hồ tiền giật một nhịp. */
  tien: () => not(900, 1300, 0.05, 0.03, 'sine'),
  /** Ăn sao — `n` từ 1 tới 3, ba nốt cao dần. */
  sao: (n: number) => {
    const nac = [523.25, 659.25, 783.99]       // đô – mi – son
    for (let i = 0; i < Math.max(0, Math.min(3, n)); i++) {
      not(nac[i], nac[i], 0.26, 0.1, 'triangle', i * 0.16)
    }
  },
  /** ⚠ MÀN ẨN VẢ — một tiếng trầm, phũ. Thiết kế §6 gọi đúng nó là "một âm thật phũ":
   *  đây là lúc trò chơi nói với người chơi rằng cỗ máy họ vừa tâm đắc chỉ là vẽ lại
   *  quá khứ, và một tiếng chuông vui ở đây thì phản lại chính bài học. */
  vap: () => {
    not(150, 70, 0.42, 0.12, 'sawtooth')
    cach(0.2, 0.07, 420)
  },
  /** Thắng boss. */
  thang: () => {
    not(659.25, 659.25, 0.14, 0.08, 'triangle')
    not(987.77, 987.77, 0.3, 0.09, 'triangle', 0.13)
  },
}
