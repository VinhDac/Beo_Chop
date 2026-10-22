# Cat Studio

**You draw it. LEAN runs it. The market decides.**

QuantConnect's engine has always been free. The price of admission was Python. Cat
Studio pays it for you: draw a trading engine as a block diagram, and the algorithm
writes itself — then **LEAN** runs it, on real data, with real fills and real fees.

- **Website:** https://vinhdac.github.io/Cat-Studio/
- **Download:** [latest release](https://github.com/VinhDac/Cat-Studio/releases/latest) — Windows 10/11, 64-bit

## What it is

You draw. Cat Studio writes an ordinary QuantConnect algorithm — `main.py`, readable,
yours to keep — and hands it to LEAN. It computes **nothing** about the market itself:
fills, position sizing, margin, brokerage fees and slippage are all LEAN's. Every
number you see came back from the engine.

It also will not let you flatter yourself. Your result is always set beside **buying
and holding** the same symbol over the same dates, and the third of three stars only
comes if the engine still works over a period it was never shown.

Inside: 164 quantities (each naming the LEAN line it compiles to), 90 indicators,
11 ready-made universes, 10 things an engine can do, 26 levels in 10 acts, and an
Optimize that can search on 27 metrics.

## Getting it

1. Run the installer. It goes into `%LOCALAPPDATA%\Programs\Cat Studio` — **no admin
   rights** — adds a Start menu entry and registers an uninstaller. A portable `.zip`
   is in the same release if you would rather not install anything.
2. **Bring your own LEAN.** Open Settings and point it at the folder holding
   `Launcher\` and `Data\`, or drop a folder named `Lean\` beside the app and it finds
   it by itself.
3. Draw, then press Backtest.

Your diagrams, drafts and scores live in `du_lieu\` beside the app. Uninstalling does
not touch that folder, and if you set a QuantConnect key it stays in there, on your
machine, and goes nowhere.

### Why the installer does not include LEAN

Three reasons, and none is size. The LEAN build is framework-dependent, so it needs
.NET 10 already present — shipping it means rebuilding LEAN self-contained, about
70 MB more. LEAN runs Python algorithms through pythonnet, so a Python runtime has to
travel with it too. And LEAN's `Data/` folder carries no licence file: the engine is
Apache-2.0, which does not automatically cover market data, so QuantConnect has to be
asked before anything ships with it.

Until that is settled, the honest arrangement is this one: you bring LEAN, and Cat
Studio never pretends to be the thing doing the computing.

## Known limits

- **Windows 10 and 11** only. The app is Python with a web UI in a native window.
- **No live trading.** Backtests on historical data. The *Live* button exists because
  LEAN has one, and it is switched off.
- **23 of the 26 levels run.** Levels 17, 18 and 19 ask about the company behind a
  symbol — P/E, market cap, self-filtering universes — which needs QuantConnect's
  `fine` data, a paid feed. Those three say so on their own card rather than failing
  quietly.

## About this repository

This repository holds the **website and the releases**, not the source code.

The site is one page: `index.html`, `assets/site.css`, `assets/mach.js`,
`assets/luot.js`, two screenshots and two logos. No build step, no framework.
`.nojekyll` makes GitHub Pages serve the folder as it stands. To work on it:

```bash
python -m http.server 8992
```

Everything on the page is real and must stay that way:

- **The code** on the page is the file Cat Studio generated from that exact diagram.
- **The curves** are one real LEAN backtest: XAUUSD, 2012-01-01 to 2014-12-31,
  $100,000, fees on. The engine lost **9.87%**; buying and holding lost **24.42%**.
  Nine orders. A graph that went up would have been easy to draw and worth nothing.
- **The screenshots** are the app at 800×500, nothing staged.

The scene in the middle of the page is drawn in HTML so the blocks can land one at a
time — the page says so in plain words, right under it, and then shows the real app.

The QuantConnect mark appears as **attribution**: "Runs on" comes first, the mark is
small and dimmed, and it never sits beside the Cat Studio logo as an equal. Cat Studio
is not a QuantConnect partner; it runs their open-source engine.
