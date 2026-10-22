# The Cat Studio website

**Instead of code, you draw. Everything else is identical.**

One page: `index.html`, `assets/site.css`, five screenshots and the logo. No build
step, no framework, no dependency — open `index.html` in a browser and it is the site.
`.nojekyll` is there so GitHub Pages serves the folder as it stands.

```bash
python -m http.server 8991 --directory site
```

## What the page has to do

Sell one idea and then prove it, in that order:

1. **The claim**, in the hero — *instead of code, you draw; everything else is
   identical.*
2. **The proof**, immediately after — the five-block diagram beside the real
   `main.py` it generated. Not a description of the code: the file itself, wrapped to
   fit the column and otherwise untouched.
3. **Why "identical" is true** — every quantity names the LEAN line behind it, and
   the app computes nothing about the market itself.
4. **What it cannot do yet**, in full. Three things block a packaged build and they
   are all named.

## Keeping it honest

- **The screenshots are the real app**, taken at 800×500 with nothing staged and
  nothing retouched. Replace them by taking new ones at the same size.
- **The numbers are counted, not estimated.** 164 quantities · 90 indicators · 10
  actions · 11 universes · 26 levels · 27 Optimize metrics all come from the app's own
  dictionaries. If a dictionary grows, these go stale — recount before editing them:

  ```bash
  python -c "import sys; sys.path.insert(0,'.'); from cat_studio import hoi; print(len(hoi.tu_dien()['kho']))"
  ```

- **The code sample is generated, never typed.** To refresh it, open the diagram in
  the app, press Build, and copy what LEAN was handed.

## Colours

The page uses the app's own palette (`webui/src/theme.css`) and the app's own three
colours for code — quantity names blue, numbers gold, joining words grey — so the
screenshots and the page read as one product. Do not invent a second palette here.
