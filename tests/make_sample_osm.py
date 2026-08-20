"""Testler için küçük, sentetik bir .osm XML dosyası üretir.

Gerçek Güzelyalı verisi değildir; yalnızca çevrimdışı çizim yolunu
(osm_extract + render) doğrulamak içindir: kıyı çizgisi, yol ızgarası,
binalar, park ve iskele içerir.
"""

import sys

LAT0, LON0 = 38.3980, 27.0640   # güneybatı köşe
LAT1, LON1 = 38.4070, 27.0770   # kuzeydoğu köşe
COAST_LAT = 38.4045             # kıyı çizgisi; kuzeyi deniz


def build():
    nodes, ways = [], []
    nid = it = 1

    def node(lat, lon):
        nonlocal nid
        nodes.append(f'  <node id="{nid}" lat="{lat:.6f}" lon="{lon:.6f}" version="1"/>')
        nid += 1
        return nid - 1

    def way(refs, tags):
        nonlocal it
        body = "".join(f'\n    <nd ref="{r}"/>' for r in refs)
        body += "".join(f'\n    <tag k="{k}" v="{v}"/>' for k, v in tags.items())
        ways.append(f'  <way id="{100000 + it}" version="1">{body}\n  </way>')
        it += 1

    # Kıyı çizgisi (batıdan doğuya, hafif eğimli). OSM kuralı: sol taraf kara.
    coast = [node(COAST_LAT + 0.0006 * i / 8, LON0 + (LON1 - LON0) * i / 8) for i in range(9)]
    way(coast, {"natural": "coastline"})

    # Sahil bulvarı — kıyıya paralel ana yol.
    blvd = [node(COAST_LAT - 0.0010, LON0 + (LON1 - LON0) * i / 8) for i in range(9)]
    way(blvd, {"highway": "primary", "name": "Mustafa Kemal Sahil Bulvari"})

    # Yol ızgarası (kara tarafında).
    rows = [LAT0 + 0.0012 * i for i in range(1, 5)]
    cols = [LON0 + 0.0016 * j for j in range(1, 8)]
    for lat in rows:
        way([node(lat, LON0 + 0.0005), node(lat, LON1 - 0.0005)], {"highway": "residential"})
    for lon in cols:
        way([node(LAT0 + 0.0005, lon), node(COAST_LAT - 0.0012, lon)], {"highway": "residential"})

    # Binalar: ızgara aralarına küçük kareler.
    for lat in rows:
        for lon in cols:
            a = node(lat + 0.00025, lon + 0.00025)
            b = node(lat + 0.00025, lon + 0.00105)
            c = node(lat + 0.00080, lon + 0.00105)
            d = node(lat + 0.00080, lon + 0.00025)
            way([a, b, c, d, a], {"building": "yes"})

    # Park.
    p = [node(LAT0 + 0.0020, LON0 + 0.0100), node(LAT0 + 0.0020, LON0 + 0.0125),
         node(LAT0 + 0.0038, LON0 + 0.0125), node(LAT0 + 0.0038, LON0 + 0.0100)]
    way(p + [p[0]], {"leisure": "park"})

    # İskele (denize uzanan).
    pier_lon = LON0 + 0.0060
    way([node(COAST_LAT - 0.0009, pier_lon), node(COAST_LAT + 0.0010, pier_lon)],
        {"man_made": "pier"})

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="sample">\n'
        + "\n".join(nodes) + "\n" + "\n".join(ways) + "\n</osm>\n"
    )


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sample_guzelyali.osm"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print(f"yazıldı: {out}")
