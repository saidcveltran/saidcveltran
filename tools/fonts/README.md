# Fonts

Both files are embedded into the SVG cards as data URIs (GitHub loads nothing external into README images).
They are subsets (see `glyph_ranges.py`), generated from the full fonts in `source/` by `../build_fonts.py`.

| File | Source | Licence |
| --- | --- | --- |
| `inter-600-subset.woff2` | Inter, body text of the cards | SIL Open Font License 1.1 |
| `jetbrains-mono-800-subset.woff2` | `@fontsource/jetbrains-mono@5.3.0`, `files/jetbrains-mono-latin-800-normal.woff2`, titles and figures | SIL Open Font License 1.1, see `OFL-jetbrains-mono.txt` |

Text outside the ranges falls back to the system font; tests keep the cards inside the ranges.
