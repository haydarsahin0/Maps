#!/usr/bin/env python3
"""GitHub Pages için basit bir sayfa üretir: üretilen haritaları yan yana gösterir."""

import datetime
import os
import sys

PAGE = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Güzelyalı · İzmir</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    margin: 0; padding: 2.5rem 1.25rem 4rem;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    background: #F2F4CB; color: #2F3737;
  }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #12181F; color: #E8D5B7; }}
    a {{ color: #F2A65A; }}
  }}
  header {{ max-width: 60rem; margin: 0 auto 2.5rem; }}
  h1 {{ font-size: clamp(2rem, 6vw, 3.25rem); margin: 0 0 .35rem; letter-spacing: .02em; }}
  p.sub {{ margin: 0; opacity: .75; font-size: 1.05rem; }}
  main {{ max-width: 60rem; margin: 0 auto; display: grid; gap: 3rem; }}
  figure {{ margin: 0; }}
  figure img {{ width: 100%; height: auto; border-radius: .5rem; display: block; }}
  figcaption {{ margin-top: .6rem; font-size: .95rem; opacity: .75; }}
  footer {{ max-width: 60rem; margin: 3.5rem auto 0; font-size: .9rem; opacity: .7; }}
</style>
</head>
<body>
<header>
  <h1>Güzelyalı, İzmir</h1>
  <p class="sub">OpenStreetMap verisinden <a href="https://github.com/marceloprates/prettymaps">prettymaps</a> ile çizildi · 1100 m yarıçap · 38.4022° K, 27.0705° D</p>
</header>
<main>
{figures}
</main>
<footer>
  Son güncelleme: {stamp} · Harita verisi © OpenStreetMap katılımcıları (ODbL) ·
  Çizim: prettymaps (AGPL-3.0)
</footer>
</body>
</html>
"""

FIGURES = [
    ("guzelyali-ege.png", "Ege paleti — gündüz teması"),
    ("guzelyali-gece.png", "Gece paleti — koyu tema"),
]


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "site"
    figures = []
    for filename, caption in FIGURES:
        if not os.path.exists(os.path.join(outdir, filename)):
            print(f"uyarı: {filename} yok, atlanıyor", file=sys.stderr)
            continue
        figures.append(
            f'  <figure>\n    <img src="{filename}" alt="{caption}">\n'
            f"    <figcaption>{caption}</figcaption>\n  </figure>"
        )

    if not figures:
        print("hata: gösterilecek harita yok", file=sys.stderr)
        return 1

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    path = os.path.join(outdir, "index.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(PAGE.format(figures="\n".join(figures), stamp=stamp))
    print(f"yazıldı: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
