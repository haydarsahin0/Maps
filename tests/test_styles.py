"""Palet/katman stillerinin matplotlib tarafından kabul edildiğini doğrular.

OSM erişimi gerektirmez: gerçek veri yerine sentetik geometriler çizilir.
Çalıştırma:  python tests/test_styles.py
"""

import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gp
from shapely.geometry import LineString, Polygon

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prettymaps.draw import plot_gdf  # noqa: E402
from guzelyali_izmir import LAYERS, PALETTES  # noqa: E402


def fake_polygons(n=3):
    return gp.GeoDataFrame(
        geometry=[
            Polygon([(i, 0), (i + 0.8, 0), (i + 0.8, 0.8), (i, 0.8)]) for i in range(n)
        ],
        crs=3857,
    )


def fake_streets():
    gdf = gp.GeoDataFrame(
        {"highway": ["primary", "residential", "footway"]},
        geometry=[
            LineString([(0, 1), (3, 1)]),
            LineString([(1, 0), (1, 2)]),
            LineString([(0, 2), (3, 2.5)]),
        ],
        crs=3857,
    )
    return gdf


def main():
    failures = []
    for palette_name, style in PALETTES.items():
        fig, ax = plt.subplots(figsize=(4, 4))
        for layer, kwargs in style.items():
            if layer in ("background", "perimeter"):
                continue  # arka plan/çerçeve prettymaps tarafından ayrıca çizilir
            gdf = fake_streets() if layer == "streets" else fake_polygons()
            width = LAYERS.get(layer, {}).get("width")
            try:
                plot_gdf(layer, gdf, ax, width=width, **kwargs)
            except Exception as exc:
                failures.append(f"{palette_name}/{layer}: {type(exc).__name__}: {exc}")
        ax.set_axis_off()
        ax.autoscale()
        out = f"/tmp/style_smoke_{palette_name}.png"
        fig.savefig(out, dpi=60, facecolor=style["background"]["fc"])
        plt.close(fig)
        print(f"{palette_name}: çizildi -> {out}")

    # Her katmanın bir stil karşılığı var mı?
    for palette_name, style in PALETTES.items():
        missing = [l for l in LAYERS if l not in style and l != "perimeter"]
        if missing:
            failures.append(f"{palette_name}: stil tanımı eksik katmanlar: {missing}")

    if failures:
        print("\nHATALAR:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nTüm paletler ve katman stilleri sorunsuz çizildi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
