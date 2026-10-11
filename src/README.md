# CTABot source

`index.html` at the top of the repo is **generated**. Don't edit it by hand: the next build overwrites it. Edit the files here instead.

| File | What it is |
| --- | --- |
| `engine.html` | A pinned copy of MetraBot's `index.html` (the shared map engine). |
| `assemble.py` | Builds `../index.html`: takes the engine, swaps in the CTA blocks below, and applies CTA-only patches. |
| `a_network.js` … `h_car.js` | CTA-specific code: network data, base map, live feed, arrivals, ticker, check-ins, train card, little trains. |
| `i_ats.js` | O'Hare's Airport Transit System: drawn when zoomed in at the airport, with simulated trains (it has no live feed). |
| `bgvoice.py` | Check-in timing edits shared word for word with MetraBot (shorter rides, keep going in a background tab). |
| `icon.svg`, `icon180.png` | The favicon and home-screen icon. |

## Build

From the repo root:

```
python3 src/assemble.py && python3 tools/build_layout.py
```

`assemble.py` writes `index.html` with an empty map, and `build_layout.py` bakes the map in. GitHub Actions run this automatically when anything in `src/` changes.

## Updating the engine from MetraBot

1. Copy MetraBot's latest `index.html` over `src/engine.html`.
2. Run the build. `assemble.py` patches the engine by exact text. If MetraBot changed a line it patches, the build stops and names the line, and nothing is overwritten.
3. Fix the patch in `assemble.py`, rebuild, and test.
