/* MẠCH CUỘN — cuộn là dựng cỗ máy.
 *
 * Cả khúc `#mach` là MỘT cảnh, không phải mấy mục xếp chồng: sân dính lại
 * (`position: sticky`), còn chiều cao của khúc chính là thời lượng. Cuộn tới đâu thì
 * khối rơi xuống tới đó, mã tự gõ thêm tới đó; nhịp cuối thì sơ đồ nhường chỗ cho
 * ĐƯỜNG VỐN THẬT của một lượt LEAN đã chạy.
 *
 * ⚠ SỐ LIỆU LÀ THẬT, và đó là điều kiện sống của cả trang. `assets/luot.js` là một
 * lượt backtest có thật trên XAUUSD 2012-2014: −9,87% so với mua-rồi-giữ −24,42%.
 * Vẽ đại một đường cong cho đẹp là phá đúng lời hứa mà cả app dựng lên quanh nó
 * («app không tự nghĩ ra con số nào»), và nó sẽ là thứ duy nhất trên trang không thật.
 *
 * ⚠ DỮ LIỆU ĐỂ TRONG `.js`, KHÔNG PHẢI `.json`. Mở tệp bằng cách bấm đúp
 * (`file://`) thì `fetch` bị chặn vì khác nguồn gốc — trang vẫn chạy nhưng đồ thị
 * trống trơn, mà đó đúng là cách người ta xem thử một trang tĩnh lần đầu.
 *
 * Không thư viện, không bộ dựng. Một tệp.
 */
(() => {
  'use strict';

  const san = document.querySelector('#mach');
  if (!san) return;

  const NHIP = 5;
  const demSo = san.querySelector('[data-dem-so]');
  const cau = Array.from(san.querySelectorAll('[data-cau]'));
  const ray = san.querySelector('[data-ray]');
  /* Thứ MỌC DẦN theo nhịp: khối, dây, dòng mã. Mỗi món khai nhịp của nó ngay trong
     HTML, nên thêm một khối là thêm một thuộc tính — không phải sửa ở đây.
     ⚠ Bật bằng CLASS chứ không bằng luật CSS theo `data-nhip`: viết bằng CSS thì phải
     gõ tay mọi cặp (nhịp × món) — mười lăm luật cho năm nhịp, và quên một cặp là một
     khối không bao giờ hiện ra. */
  const moc = Array.from(san.querySelectorAll('[data-khoi],[data-day],[data-d]'));
  const nhipCua = (el) => Number(el.dataset.khoi || el.dataset.day || el.dataset.d);
  const oMa = san.querySelector('.ma pre');
  /* DUỖI THẲNG: màn quá hẹp, hay người đã bật «giảm chuyển động». Cùng một điều kiện
     với bộ luật CSS cuối tệp `site.css` — hai nơi mà lệch nhau thì CSS duỗi còn JS vẫn
     tưởng đang diễn, và đồ thị nằm im với mấy dấu gạch cho tới khi cuộn hết khúc. */
  const phang = matchMedia('(max-width: 900px), (prefers-reduced-motion: reduce)');
  const im = matchMedia('(prefers-reduced-motion: reduce)').matches;

  let nhipHien = 0;

  function datNhip(n) {
    if (n === nhipHien) return;
    nhipHien = n;
    san.dataset.nhip = String(n);
    if (demSo) demSo.textContent = String(n);
    cau.forEach((p) => p.classList.toggle('hien', Number(p.dataset.cau) === n));
    moc.forEach((el) => el.classList.toggle('hien', nhipCua(el) <= n));
    theoMa(n);
    if (ray) ray.style.width = `${((n - 1) / (NHIP - 1)) * 100}%`;
    if (n === NHIP) veDoThi();
  }

  /* Bảng mã TỰ CUỘN THEO dòng vừa mọc.
   *
   * ⚠ KHÔNG CÓ NÓ THÌ CẢ HIỆU ỨNG MẤT SẠCH, và mất lặng lẽ. Mấy dòng mới vẫn hiện ra
   * đúng nhịp — nhưng ở dưới mép khung, nên người xem thấy một khối mã đứng im suốt
   * năm nhịp và kết luận là nó có sẵn từ đầu. Đúng thứ chỉ ảnh chụp mới bắt được.
   *
   * Đưa dòng cuối lên khoảng hai phần ba khung chứ không sát đáy: còn thấy chỗ trống
   * phía dưới thì mới ra cảm giác «đang viết tiếp», sát đáy thì trông như đã hết. */
  function theoMa(n) {
    // Duỗi thẳng thì bảng mã là một đoạn VĂN BẢN để đọc từ đầu, không phải một cảnh
    // đang viết: kéo nó xuống giữa là người đọc mở ra đã thấy mất đoạn đầu.
    if (!oMa || phang.matches) return;
    const cuoi = [...oMa.querySelectorAll('[data-d]')].filter((e) => nhipCua(e) <= n).pop();
    if (!cuoi) return;
    const toi = Math.max(0, cuoi.offsetTop - oMa.clientHeight * 0.66);
    oMa.scrollTo({ top: toi, behavior: im ? 'auto' : 'smooth' });
  }

  /* Nhịp hiện tại = cuộn được bao nhiêu phần của khúc. `- innerHeight` vì sân dính
     lại suốt khúc: phần cuộn THẬT SỰ dùng được là chiều cao khúc trừ một màn hình. */
  function doNhip() {
    const r = san.getBoundingClientRect();
    const dai = san.offsetHeight - innerHeight;
    const p = dai > 0 ? Math.min(Math.max(-r.top / dai, 0), 1) : 0;
    datNhip(Math.min(NHIP, 1 + Math.floor(p * NHIP)));
  }

  /* ------------------------------------------------------------ ĐỒ THỊ THẬT */
  let daVe = false;

  function veDoThi() {
    if (daVe) return;
    const d = window.LUOT;
    if (!d || !d.may || !d.boss) return;      // thiếu số liệu thì để nguyên dấu —
    daVe = true;

    const W = 560, H = 210, LE = 10;
    const moi = [...d.may, ...d.boss].map((p) => p[1]);
    const lo = Math.min(...moi, 0), hi = Math.max(...moi, 0);
    const khoang = hi - lo || 1;
    const y = (v) => LE + (hi - v) / khoang * (H - LE * 2);

    const duong = (ds) => ds
      .map((p, i) => `${i ? 'L' : 'M'}${(i / (ds.length - 1) * W).toFixed(1)} ${y(p[1]).toFixed(1)}`)
      .join('');

    const dat = (sel, ds) => {
      const el = san.querySelector(sel);
      if (!el) return;
      el.setAttribute('d', duong(ds));
      // Vẽ dần bằng `stroke-dashoffset`: một thuộc tính, chạy trên GPU.
      const dai = el.getTotalLength();
      el.style.strokeDasharray = String(dai);
      el.style.strokeDashoffset = im ? '0' : String(dai);
      if (!im) requestAnimationFrame(() => { el.style.strokeDashoffset = '0'; });
    };

    const khong = san.querySelector('[data-khong]');
    if (khong) { khong.setAttribute('y1', y(0)); khong.setAttribute('y2', y(0)); }
    dat('[data-duong-boss]', d.boss);
    dat('[data-duong-may]', d.may);

    const pt = (v) => `${v > 0 ? '+' : ''}${Number(v).toFixed(2)}%`;
    const chu = (sel, v) => { const el = san.querySelector(sel); if (el) el.textContent = v; };
    chu('[data-may-pt]', pt(d.may_pt));
    chu('[data-boss-pt]', pt(d.boss_pt));
    chu('[data-lenh]', String(d.lenh));
  }

  /* --------------------------------------------------------------- nghe cuộn */
  let cho = false;
  function nghe() {
    if (phang.matches || cho) return;
    cho = true;
    requestAnimationFrame(() => { cho = false; doNhip(); });
  }

  function batDau() {
    if (phang.matches) {
      // Không có cảnh để diễn: mọi thứ ở trạng thái CUỐI ngay, đồ thị vẽ luôn.
      datNhip(NHIP);
      veDoThi();
      return;
    }
    doNhip();
  }

  addEventListener('scroll', nghe, { passive: true });
  addEventListener('resize', nghe);
  phang.addEventListener('change', batDau);
  batDau();
})();
