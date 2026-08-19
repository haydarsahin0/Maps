#!/usr/bin/env python3
"""
İzmir / Güzelyalı haritası — prettymaps ile.

Kullanım:
    python guzelyali_izmir.py                        # Ege paleti, 1100 m yarıçap
    python guzelyali_izmir.py --palette gece         # koyu tema
    python guzelyali_izmir.py --radius 1600          # daha geniş alan
    python guzelyali_izmir.py --query "Güzelyalı, Konak, İzmir, Türkiye"

Veri kaynağı OpenStreetMap'tir (osmnx -> Overpass API); çalıştırırken
overpass-api.de adresine (ve --query ile geocode için
nominatim.openstreetmap.org adresine) erişim gerekir.
"""

import argparse
import sys

import requests

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import prettymaps

# Güzelyalı İskelesi civarı — Mustafa Kemal Sahil Bulvarı, Konak/İzmir.
GUZELYALI = (38.4022, 27.0705)

# Çizilecek OSM katmanları (prettymaps'in "default" preset'i temel alındı,
# kıyı semti için sea/beach/pier katmanları öne çıkarıldı).
LAYERS = {
    "perimeter": {},
    "streets": {
        "width": {
            "motorway": 6,
            "trunk": 6,
            "primary": 5,
            "secondary": 4,
            "tertiary": 3.5,
            "cycleway": 3,
            "residential": 3,
            "unclassified": 2.5,
            "service": 1.8,
            "pedestrian": 2,
            "footway": 1,
        }
    },
    "building": {"tags": {"building": True, "landuse": "construction"}},
    # İzmir Körfezi: kıyı çizgisinden (natural=coastline) deniz poligonu üretir.
    "sea": {},
    # Kapalı su poligonları (liman havuzları, göletler, koylar).
    "water": {"tags": {"natural": ["water", "bay"]}},
    "green": {
        "tags": {
            "landuse": ["grass", "village_green", "recreation_ground"],
            "leisure": ["park", "garden", "pitch", "playground"],
            "natural": ["island", "wood", "scrub"],
        }
    },
    "beach": {"tags": {"natural": "beach"}},
    # Sahil bandındaki iskeleler ve yaya alanları.
    "parking": {
        "tags": {"amenity": "parking", "highway": "pedestrian", "man_made": "pier"}
    },
}

# Renk paletleri.
PALETTES = {
    # Ege esintili gündüz teması: kremit binalar, turkuaz körfez.
    "ege": {
        "perimeter": {"fill": False, "lw": 0, "zorder": 0},
        "background": {"fc": "#F2F4CB", "zorder": -1},
        "green": {
            "fc": "#8BB174", "ec": "#2F3737", "hatch_c": "#A7C497",
            "hatch": "ooo...", "lw": 1, "zorder": 1,
        },
        "beach": {
            "fc": "#FCE19C", "ec": "#2F3737", "hatch_c": "#D4D196",
            "hatch": "ooo...", "lw": 1, "zorder": 3,
        },
        "parking": {"fc": "#F2F4CB", "ec": "#2F3737", "lw": 1, "zorder": 3},
        "streets": {"fc": "#2F3737", "ec": "#475657", "alpha": 1, "lw": 0, "zorder": 4},
        "building": {
            "palette": ["#FFC857", "#E9724C", "#C5283D"],
            "ec": "#2F3737", "lw": 0.5, "zorder": 5,
        },
        "water": {
            "fc": "#5DA9A6", "ec": "#2F3737", "hatch_c": "#8FC7C4",
            "hatch": "ooo...", "lw": 1, "zorder": 99,
        },
        "sea": {
            "fc": "#5DA9A6", "ec": "#2F3737", "hatch_c": "#8FC7C4",
            "hatch": "ooo...", "lw": 1, "zorder": 99,
        },
    },
    # Koyu tema: körfez lacivert, binalar sıcak tonlarda parlıyor.
    "gece": {
        "perimeter": {"fill": False, "lw": 0, "zorder": 0},
        "background": {"fc": "#12181F", "zorder": -1},
        "green": {"fc": "#1F3B2C", "ec": "#2C5240", "lw": 1, "zorder": 1},
        "beach": {"fc": "#3A3524", "ec": "#4A452F", "lw": 1, "zorder": 3},
        "parking": {"fc": "#1A222B", "ec": "#2B3742", "lw": 1, "zorder": 3},
        "streets": {"fc": "#E8D5B7", "ec": "#E8D5B7", "alpha": 1, "lw": 0, "zorder": 4},
        "building": {
            "palette": ["#F2A65A", "#EC7357", "#B84A62"],
            "ec": "#12181F", "lw": 0.4, "zorder": 5,
        },
        "water": {"fc": "#16324F", "ec": "#1F4A73", "lw": 1, "zorder": 99},
        "sea": {"fc": "#16324F", "ec": "#1F4A73", "lw": 1, "zorder": 99},
    },
}

TITLE_COLORS = {"ege": "#2F3737", "gece": "#E8D5B7"}

OSM_HOSTS = {
    "Overpass (harita verisi)": "https://overpass-api.de/api/status",
    "Nominatim (geocode)": "https://nominatim.openstreetmap.org/status",
}


def check_osm_access():
    """OSM sunucularına erişimi önden dener.

    osmnx, veri çekemediği katmanları sessizce boş geçtiği için ağ kapalıysa
    script boş bir harita üretebilir. Bunu baştan yakalıyoruz.
    """
    unreachable = []
    for label, url in OSM_HOSTS.items():
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "prettymaps-guzelyali"})
            if resp.status_code >= 400:
                unreachable.append(f"{label}: HTTP {resp.status_code}")
        except requests.RequestException as exc:
            unreachable.append(f"{label}: {type(exc).__name__}")
    return unreachable


def build_args():
    p = argparse.ArgumentParser(description="İzmir Güzelyalı haritası üretir.")
    p.add_argument(
        "--query",
        default=None,
        help="Yer adı (Nominatim ile geocode edilir). Verilmezse Güzelyalı "
             "koordinatları kullanılır — 'Güzelyalı' adı Türkiye'de birden çok "
             "yerde geçtiği için varsayılan koordinattır.",
    )
    p.add_argument("--lat", type=float, default=GUZELYALI[0])
    p.add_argument("--lon", type=float, default=GUZELYALI[1])
    p.add_argument("--radius", type=int, default=1100, help="Metre cinsinden yarıçap.")
    p.add_argument("--palette", choices=sorted(PALETTES), default="ege")
    p.add_argument("--out", default=None, help="Çıktı dosyası (.png).")
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--no-title", action="store_true", help="Başlık yazısını gizle.")
    p.add_argument(
        "--skip-check", action="store_true",
        help="OSM erişim ön kontrolünü atla (ör. kendi Overpass sunucunuzu kullanıyorsanız).",
    )
    return p.parse_args()


def main():
    args = build_args()
    query = args.query if args.query else (args.lat, args.lon)
    style = PALETTES[args.palette]
    out = args.out or f"guzelyali_izmir_{args.palette}_{args.radius}m.png"

    if not args.skip_check:
        unreachable = check_osm_access()
        if unreachable:
            print(
                "OpenStreetMap sunucularına ulaşılamıyor:\n  - "
                + "\n  - ".join(unreachable)
                + "\n\nHarita verisi çalışma anında OSM'den indiriliyor; bu adresler "
                  "açık olmadan harita üretilemez (script boş bir görsel üretmesin diye "
                  "burada duruyor). Ağ/proxy izinlerini kontrol edip tekrar deneyin.",
                file=sys.stderr,
            )
            return 2

    fig, ax = plt.subplots(figsize=(12, 12), constrained_layout=True)
    ax.set_aspect("equal")

    print(f"OSM verisi indiriliyor: {query} (r={args.radius} m) ...", flush=True)
    try:
        plot = prettymaps.plot(
            query,
            radius=args.radius,
            ax=ax,
            layers=LAYERS,
            style=style,
            use_preset=False,   # hazır preset yerine yukarıdaki tanımlar
            credit=False,       # prettymaps'in kendi imzasını kapat
            show=False,
        )
    except Exception as exc:  # ağ / Overpass hataları burada görünür
        print(f"\nHarita çizilemedi: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(
            "OpenStreetMap sunucularına (overpass-api.de, nominatim.openstreetmap.org) "
            "erişilebildiğinden emin olun.",
            file=sys.stderr,
        )
        return 1

    drawn = {
        name: len(gdf)
        for name, gdf in plot.geodataframes.items()
        if name != "perimeter" and len(gdf) > 0
    }
    if not drawn:
        print(
            "Hiçbir katman için veri gelmedi — harita boş çıkacaktı, kaydetmiyorum. "
            "OSM erişimini kontrol edin.",
            file=sys.stderr,
        )
        return 3
    print("Çizilen katmanlar: " + ", ".join(f"{k}={v}" for k, v in sorted(drawn.items())))

    ax.set_axis_off()

    if not args.no_title:
        fg = TITLE_COLORS[args.palette]
        ax.set_title("GÜZELYALI", fontsize=44, fontweight="bold", color=fg, pad=18)
        ax.text(
            0.5,
            -0.02,
            f"İZMİR  ·  {args.lat:.4f}° K, {args.lon:.4f}° D"
            "  ·  © OpenStreetMap katılımcıları",
            transform=ax.transAxes,
            ha="center",
            va="top",
            color=fg,
            fontsize=13,
        )

    fig.savefig(
        out, dpi=args.dpi, bbox_inches="tight",
        facecolor=style["background"]["fc"],
    )
    print(f"Kaydedildi: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
