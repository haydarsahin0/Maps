"""Kıyı çizgisinden deniz poligonu üretimi (hızlı yol).

prettymaps'in yerleşik `sea` katmanı, sınır kutusundaki tüm sürüş ağını
indirip her aday poligon için kesişim testi yapar; yoğun kıyı semtlerinde bu
çok yavaş. Buradaki yaklaşım aynı fikri kullanır ama zaten elde olan
verilerle çalışır:

1. `natural=coastline` çizgileri sınır kutusunu parçalara böler,
2. içinde hiç bina/yol bulunmayan ve yeterince büyük parçalar deniz sayılır.
"""

from __future__ import annotations

import geopandas as gp
from shapely.geometry import LineString, MultiPolygon, box
from shapely.ops import linemerge, unary_union

EMPTY = gp.GeoDataFrame(geometry=[], crs=4326)


def extend_line(line: LineString, distance: float) -> LineString:
    """Çizgiyi iki ucundan, uç segmentlerin yönünde uzatır.

    İndirilen alanın kenarında biten kıyı çizgileri sınır kutusunu ikiye
    bölemez; uçları uzatmak bunu garantiler.
    """
    coords = list(line.coords)
    if len(coords) < 2:
        return line

    def outward(inner, outer):
        dx, dy = outer[0] - inner[0], outer[1] - inner[1]
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return outer
        return (outer[0] + dx / length * distance, outer[1] + dy / length * distance)

    return LineString(
        [outward(coords[1], coords[0])] + coords + [outward(coords[-2], coords[-1])]
    )


def split_bbox(bounds, coastlines) -> list:
    """Sınır kutusunu kıyı çizgileriyle böler, parçaları döndürür."""
    bbox = box(*bounds)
    joined = unary_union(list(coastlines))
    merged = linemerge(joined) if joined.geom_type == "MultiLineString" else joined
    lines = [g for g in getattr(merged, "geoms", [merged]) if g.geom_type == "LineString"]
    if not lines:
        return []

    xmin, ymin, xmax, ymax = bounds
    diagonal = ((xmax - xmin) ** 2 + (ymax - ymin) ** 2) ** 0.5
    extended = unary_union([extend_line(line, diagonal) for line in lines])

    pieces = bbox.difference(extended.buffer(1e-9))
    return [p for p in getattr(pieces, "geoms", [pieces]) if not p.is_empty]


def derive_sea(perimeter, coastline, obstacles=(), min_area_ratio=0.03):
    """Deniz poligonunu üretir.

    Args:
        perimeter: sınır GeoDataFrame'i (EPSG:4326).
        coastline: `natural=coastline` geometrilerini içeren GeoDataFrame.
        obstacles: kara göstergesi katmanlar (binalar, yollar) — bunları
            içeren parça kara sayılır.
        min_area_ratio: sınır kutusuna oranla bu kadardan küçük parçalar
            (kıyıdaki ince dilimler) deniz sayılmaz.
    """
    if coastline is None or len(coastline) == 0:
        return EMPTY

    bounds = tuple(perimeter.total_bounds)
    candidates = split_bbox(bounds, coastline.geometry.tolist())
    if len(candidates) < 2:
        return EMPTY  # kıyı çizgisi kutuyu bölmemiş; deniz tarafı belirsiz

    bbox_area = box(*bounds).area
    land_markers = []
    for layer in obstacles:
        if layer is not None and len(layer):
            land_markers.append(layer.geometry)

    def has_land(piece):
        for markers in land_markers:
            hits = markers.sindex.query(piece, predicate="intersects")
            if len(hits):
                return True
        return False

    sea_pieces = [
        piece
        for piece in candidates
        if piece.area / bbox_area >= min_area_ratio and not has_land(piece)
    ]
    if not sea_pieces:
        return EMPTY

    sea = unary_union(MultiPolygon(sea_pieces).geoms).buffer(1e-8)
    return gp.GeoDataFrame(geometry=[sea], crs=4326)


def fetch_coastline(perimeter):
    """Sınır kutusundaki kıyı çizgilerini OSM'den çeker (tek sorgu)."""
    import osmnx as ox

    try:
        return ox.features_from_polygon(
            box(*perimeter.total_bounds), tags={"natural": "coastline"}
        )
    except Exception:
        return EMPTY
