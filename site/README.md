# The Cat Studio website

**You draw it. LEAN runs it. The market decides.**

One page. `index.html`, `assets/site.css`, `assets/mach.js`, `assets/luot.js`, two
screenshots and two logos. No build step, no framework, no dependency. `.nojekyll` is
there so GitHub Pages serves the folder as it stands.

```bash
python -m http.server 8992 --directory site
```

## The page is one argument, not a feature list

1. **The claim**, in three beats — *you draw it, LEAN runs it, the market decides.*
   The third beat is not the product: it is the thing outside everyone's hands, and
   it is where the page's honesty comes from.
2. **The scene** — the scroll *is* the build. Five beats: a block lands, the code
   writes the lines that block produced, and the next beat adds the next one. The
   fifth beat presses Run and the real equity curve draws itself.
3. **The proof** — the scene is drawn in HTML so the blocks can land one by one, so
   the page says that in plain words and then shows two real screenshots.
4. **What it cannot do yet**, in full, at the end.

## Everything on the page is real

- **The code** is the file `sinh_ma.sinh` generated from that exact diagram. Wrapped
  to fit the column, otherwise untouched.
- **The curves** are one real LEAN backtest on this machine — XAUUSD, 2012-01-01 to
  2014-12-31, $100,000, fees on. The engine lost **9.87%**; buying and holding lost
  **24.42%**. Nine orders. That is the whole lesson of the product in two numbers,
  and it is why the page does not need a graph that goes up.
- **The screenshots** are the app at 800×500, nothing staged, nothing retouched.

To refresh the run, play the diagram on level 01 and re-extract:

```bash
python -c "import sys; sys.path.insert(0,'.'); from cat_studio import luu_tru, sinh_ma, chay_lean, hanh_trinh, luat_choi; d=luat_choi.ap_man(luu_tru.doc_ban_nhap(), hanh_trinh.man('m01'), 'thay'); g=sinh_ma.sinh(d); print(chay_lean.chay(g['ma'], g['ten_lop'])['thong_ke'])"
```

Then rebuild `assets/luot.js` from the result: two series, both converted to **percent
from the start**. The equity curve is money and the benchmark is the gold price —
leaving them in their own units on one axis compares two different things.

## Two things not to undo

- **`pathLength="1"` lives on the `<path>` elements, not in the CSS.** It is an SVG
  attribute; written as a CSS property the browser drops it silently, and
  `stroke-dasharray: 1` then means a one-pixel dash on a hundred-pixel wire — the
  wires turn into a nearly invisible dotted line and nothing reports an error.
- **The flat fallback must be flat.** One rule serves both narrow screens and
  `prefers-reduced-motion`: no sticky stage, no 600vh, everything already shown, the
  chart drawn on load. An earlier version revealed the content but kept the stage, so
  a reduced-motion reader scrolled six screens of a frozen scene. `mach.js` tests the
  same condition as the CSS — if those two ever disagree, the page goes flat while the
  script still thinks it is playing.

## Colours

The app's own palette (`webui/src/theme.css`), including the three colours it uses for
code — quantity names blue, numbers gold, operators dim. The screenshots and the page
must read as one product; do not invent a second palette here.

## The QuantConnect mark

`assets/qc/quantconnect.png` appears as **attribution** — the words "Runs on" come
first, the mark is small and dimmed, and it never sits beside the Cat Studio logo as
an equal. Cat Studio is not a QuantConnect partner; it runs their open-source engine.
Saying exactly that is both the accurate claim and the stronger one.
