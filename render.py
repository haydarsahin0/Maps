"""Hazır GeoDataFrame'leri prettymaps stilleriyle çizer (ağ gerektirmez)."""

from __future__ import annotations

from copy import deepcopy

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from prettymaps.draw import create_background, draw_background, draw_layers


def draw(
    gdfs: dict,
    layers: dict,
    style: dict,
    out: str,
    title: str | None = None,
    subtitle: str | None = None,
    title_color: str = "#2F3737",
    figsize: tuple[float, float] = (12, 12),
    dpi: int = 300,
) -> str:
    """Katmanları çizip PNG olarak kaydeder, dosya yolunu döndürür."""
    # draw_background/create_background stil sözlüğünden anahtar 'pop'ladığı için
    # çağıranın sözlüğünü bozmayalım.
    style = deepcopy(style)

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    ax.set_aspect("equal")

    background, *_ = create_background(gdfs, style)
    draw_layers(layers, gdfs, style, fig, ax, None, "matplotlib")
    draw_background(background, ax, style, "matplotlib")

    ax.set_axis_off()
    ax.autoscale()

    if title:
        ax.set_title(title, fontsize=44, fontweight="bold", color=title_color, pad=18)
    if subtitle:
        ax.text(
            0.5, -0.02, subtitle, transform=ax.transAxes, ha="center", va="top",
            color=title_color, fontsize=13,
        )

    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor=style["background"]["fc"])
    plt.close(fig)
    return out
