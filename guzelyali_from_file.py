#!/usr/bin/env python3
"""Yerel bir OSM dosyasından Güzelyalı haritası çizer (internet gerekmez).

Veri kaynağı olarak şunlar kullanılabilir:
  * openstreetmap.org > Export ile indirilen `.osm` XML dosyası,
  * Geofabrik vb. kaynaklardan alınan `.osm.pbf`,
  * hazır bir GeoJSON / GeoPackage.

Kullanım:
    python guzelyali_from_file.py izmir.osm.pbf
    python guzelyali_from_file.py map.osm --radius 1500 --palette gece
"""

import argparse
import sys

from guzelyali_izmir import GUZELYALI, LAYERS, PALETTES, TITLE_COLORS
from osm_extract import load_gdfs
from render import draw


def build_args():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("source", help="OSM/GeoJSON dosyası.")
    p.add_argument("--lat", type=float, default=GUZELYALI[0])
    p.add_argument("--lon", type=float, default=GUZELYALI[1])
    p.add_argument("--radius", type=int, default=1100, help="Metre cinsinden yarıçap.")
    p.add_argument("--palette", choices=sorted(PALETTES), default="ege")
    p.add_argument("--out", default=None)
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--no-title", action="store_true")
    return p.parse_args()


def main():
    args = build_args()
    style = PALETTES[args.palette]
    out = args.out or f"guzelyali_izmir_{args.palette}_{args.radius}m.png"

    print(f"{args.source} okunuyor (merkez {args.lat}, {args.lon}; r={args.radius} m) ...")
    gdfs = load_gdfs(args.source, (args.lat, args.lon), args.radius, LAYERS)

    drawn = {k: len(v) for k, v in gdfs.items() if k != "perimeter" and len(v)}
    if not drawn:
        print(
            "Dosyadan hiçbir katman çıkmadı — kapsadığı alan merkez/yarıçapla "
            "örtüşmüyor olabilir. Kaydetmiyorum.",
            file=sys.stderr,
        )
        return 3
    print("Katmanlar: " + ", ".join(f"{k}={v}" for k, v in sorted(drawn.items())))

    draw(
        gdfs,
        LAYERS,
        style,
        out,
        title=None if args.no_title else "GÜZELYALI",
        subtitle=None if args.no_title else (
            f"İZMİR  ·  {args.lat:.4f}° K, {args.lon:.4f}° D"
            "  ·  © OpenStreetMap katılımcıları"
        ),
        title_color=TITLE_COLORS[args.palette],
        dpi=args.dpi,
    )
    print(f"Kaydedildi: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
