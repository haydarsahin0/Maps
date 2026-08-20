"""Çevrimdışı çizim yolunu uçtan uca doğrular (ağ gerektirmez).

Sentetik bir .osm dosyası üretir, osm_extract ile katmanlara ayırır ve
render ile PNG'ye çizer. Gerçek Güzelyalı verisi değildir; amaç boru hattının
çalıştığını göstermektir.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from guzelyali_izmir import LAYERS, PALETTES  # noqa: E402
from osm_extract import load_gdfs  # noqa: E402
from render import draw  # noqa: E402
from make_sample_osm import build  # noqa: E402

CENTER = (38.4025, 27.0705)
EXPECTED = {"streets", "building", "green", "parking", "sea"}


def main():
    sample = "/tmp/sample_guzelyali.osm"
    with open(sample, "w", encoding="utf-8") as fh:
        fh.write(build())

    gdfs = load_gdfs(sample, CENTER, 600, LAYERS)
    filled = {name for name, gdf in gdfs.items() if name != "perimeter" and len(gdf)}

    missing = EXPECTED - filled
    if missing:
        print(f"HATA: şu katmanlar boş kaldı: {sorted(missing)}")
        return 1
    print("Katmanlar: " + ", ".join(f"{k}={len(gdfs[k])}" for k in sorted(filled)))

    out = draw(
        gdfs, LAYERS, PALETTES["ege"], "/tmp/offline_render_test.png",
        title="GÜZELYALI", subtitle="sentetik test verisi", dpi=80,
    )
    if not os.path.getsize(out):
        print("HATA: boş PNG")
        return 1
    print(f"Çizildi: {out} ({os.path.getsize(out)} bayt)")
    print("\nÇevrimdışı çizim yolu çalışıyor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
