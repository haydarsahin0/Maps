"""Yerel bir OSM dosyasından prettymaps katmanları üretir.

İnternet erişimi olmayan (Overpass'a çıkamayan) ortamlarda kullanılır:
openstreetmap.org > Export ile indirilen `.osm` XML dosyası, Geofabrik'ten
alınan `.osm.pbf` uzantılı bir bölge dosyası ya da hazır bir
GeoJSON/GeoPackage okunur; `guzelyali_izmir.LAYERS` içindeki etiket
filtrelerine göre katmanlara ayrılır ve merkez+yarıçapa kırpılır.

Okuma GDAL'ın OSM sürücüsü (pyogrio) üzerinden yapılır.
"""

from __future__ import annotations

import re
from typing import Any

import geopandas as gp
import pandas as pd
from shapely.geometry import LineString, MultiPolygon, Point, box
from shapely.ops import linemerge, unary_union

# GDAL OSM sürücüsünün ürettiği katmanlar.
OSM_SUBLAYERS = ("points", "lines", "multilinestrings", "multipolygons")

_OTHER_TAGS_RE = re.compile(r'"(?P<key>[^"]+)"=>"(?P<value>[^"]*)"')


def _parse_other_tags(value: Any) -> dict:
    """GDAL'ın `other_tags` hstore alanını sözlüğe çevirir."""
    if not isinstance(value, str):
        return {}
    return {m.group("key"): m.group("value") for m in _OTHER_TAGS_RE.finditer(value)}


def _tag_series(gdf: gp.GeoDataFrame, key: str) -> pd.Series:
    """Bir etiketin değerlerini döndürür: önce sütun, yoksa other_tags."""
    if key in gdf.columns:
        base = gdf[key]
    else:
        base = pd.Series([None] * len(gdf), index=gdf.index, dtype=object)

    if "other_tags" in gdf.columns:
        extra = gdf["other_tags"].map(lambda v: _parse_other_tags(v).get(key))
        base = base.where(base.notna(), extra)
    return base


def _matches(gdf: gp.GeoDataFrame, tags: dict) -> pd.Series:
    """osmnx etiket sözlüğü semantiği: etiketlerden herhangi biri tutarsa satır alınır."""
    mask = pd.Series(False, index=gdf.index)
    for key, wanted in tags.items():
        values = _tag_series(gdf, key)
        if wanted is True:
            mask |= values.notna()
        elif isinstance(wanted, str):
            mask |= values == wanted
        else:  # liste
            mask |= values.isin(list(wanted))
    return mask


def read_source(path: str) -> dict[str, gp.GeoDataFrame]:
    """Kaynak dosyayı okur; OSM dosyalarında alt katmanları tek tek alır."""
    lowered = path.lower()
    if lowered.endswith((".osm", ".xml", ".pbf", ".osm.pbf", ".osm.bz2")):
        frames = {}
        for sublayer in OSM_SUBLAYERS:
            try:
                gdf = gp.read_file(path, layer=sublayer)
            except Exception:
                continue
            if len(gdf):
                frames[sublayer] = gdf.set_crs(4326, allow_override=True)
        if not frames:
            raise ValueError(f"{path} içinde okunabilir OSM katmanı bulunamadı.")
        return frames

    gdf = gp.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    return {"all": gdf.to_crs(4326)}


def make_perimeter(center: tuple[float, float], radius: float) -> gp.GeoDataFrame:
    """Merkez (lat, lon) ve metre yarıçaptan dairesel sınır üretir."""
    lat, lon = center
    point = gp.GeoDataFrame(geometry=[Point(lon, lat)], crs=4326)
    utm = point.estimate_utm_crs()
    circle = point.to_crs(utm).buffer(radius)
    return gp.GeoDataFrame(geometry=circle, crs=utm).to_crs(4326)


def _street_lines(frames: dict[str, gp.GeoDataFrame], widths: dict) -> gp.GeoDataFrame:
    """Yol çizgilerini `highway` sütunuyla birlikte toplar."""
    parts = []
    for gdf in frames.values():
        if not gdf.geom_type.isin(["LineString", "MultiLineString"]).any():
            continue
        highway = _tag_series(gdf, "highway")
        keep = highway.isin(list(widths))
        if keep.any():
            part = gdf.loc[keep, ["geometry"]].copy()
            part["highway"] = highway[keep].values
            parts.append(part)
    if not parts:
        return gp.GeoDataFrame({"highway": []}, geometry=[], crs=4326)
    return gp.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=4326)


def _collect(frames: dict[str, gp.GeoDataFrame], tags: dict) -> gp.GeoDataFrame:
    parts = []
    for gdf in frames.values():
        mask = _matches(gdf, tags)
        if mask.any():
            parts.append(gdf.loc[mask, ["geometry"]])
    if not parts:
        return gp.GeoDataFrame(geometry=[], crs=4326)
    return gp.GeoDataFrame(pd.concat(parts, ignore_index=True), crs=4326)


def _extend_line(line: LineString, distance: float) -> LineString:
    """Bir çizgiyi iki ucundan, uç segmentlerin yönünde uzatır.

    Gerçek OSM kıyı çizgileri indirilen alanın dışına taşar; kullanıcının
    verdiği dosya tam da sınır kutusunda bitiyorsa çizgi kutuyu ikiye
    bölemez ve deniz tespit edilemez. Uçları uzatarak bunu garantiliyoruz.
    """
    coords = list(line.coords)
    if len(coords) < 2:
        return line

    def outward(p_inner, p_outer):
        dx, dy = p_outer[0] - p_inner[0], p_outer[1] - p_inner[1]
        length = (dx * dx + dy * dy) ** 0.5
        if length == 0:
            return p_outer
        return (p_outer[0] + dx / length * distance, p_outer[1] + dy / length * distance)

    return LineString(
        [outward(coords[1], coords[0])] + coords + [outward(coords[-2], coords[-1])]
    )


def _derive_sea(
    frames: dict[str, gp.GeoDataFrame],
    perimeter: gp.GeoDataFrame,
    streets: gp.GeoDataFrame,
) -> gp.GeoDataFrame:
    """`natural=coastline` çizgilerinden deniz poligonu üretir.

    prettymaps'in yaklaşımı: kıyı çizgisi sınır kutusunu ikiye böler; yol ağıyla
    kesişmeyen parça denizdir.
    """
    coast = _collect(frames, {"natural": "coastline"})
    if coast.empty:
        return gp.GeoDataFrame(geometry=[], crs=4326)

    bbox = box(*perimeter.total_bounds)
    joined = unary_union(coast.geometry.tolist())
    merged = linemerge(joined) if joined.geom_type == "MultiLineString" else joined
    lines = [g for g in getattr(merged, "geoms", [merged]) if g.geom_type == "LineString"]
    diagonal = ((bbox.bounds[2] - bbox.bounds[0]) ** 2 + (bbox.bounds[3] - bbox.bounds[1]) ** 2) ** 0.5
    coastline = unary_union([_extend_line(line, diagonal) for line in lines])
    candidates = bbox.difference(coastline.buffer(1e-9))
    candidates = list(getattr(candidates, "geoms", [candidates]))

    if streets.empty:
        # Yol ağı yoksa ayrım yapamayız; en küçük parçayı deniz saymak yanıltıcı
        # olurdu, boş dönüyoruz.
        return gp.GeoDataFrame(geometry=[], crs=4326)

    sea_parts = [c for c in candidates if not streets.geometry.intersects(c).any()]
    if not sea_parts:
        return gp.GeoDataFrame(geometry=[], crs=4326)

    sea = unary_union(MultiPolygon(sea_parts).geoms).buffer(1e-8)
    return gp.GeoDataFrame(geometry=[sea], crs=4326)


def load_gdfs(
    path: str,
    center: tuple[float, float],
    radius: float,
    layers: dict[str, dict],
) -> dict[str, gp.GeoDataFrame]:
    """Dosyadan prettymaps'in beklediği {katman: GeoDataFrame} sözlüğünü üretir."""
    frames = read_source(path)
    perimeter = make_perimeter(center, radius)
    perimeter_geom = perimeter.geometry.iloc[0]

    gdfs: dict[str, gp.GeoDataFrame] = {"perimeter": perimeter}

    streets_spec = layers.get("streets", {})
    streets = _street_lines(frames, streets_spec.get("width", {}))

    for name, spec in layers.items():
        if name == "perimeter":
            continue
        if name == "streets":
            gdf = streets
        elif name == "sea":
            gdf = _derive_sea(frames, perimeter, streets)
        else:
            gdf = _collect(frames, spec.get("tags", {}))

        if not gdf.empty:
            gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
        if not gdf.empty:
            gdf = gp.clip(gdf, perimeter_geom)
        gdfs[name] = gdf.reset_index(drop=True)

    return gdfs
