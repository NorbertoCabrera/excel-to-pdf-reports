"""Chart rendering.

Matplotlib renders to a temporary PNG which is then embedded in the PDF.
Colours come from the branding config so the chart matches the letterhead.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend: no display needed on a server
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .config import ChartSpec  # noqa: E402


def _rgb_to_mpl(color: tuple[int, int, int]) -> tuple[float, float, float]:
    return tuple(c / 255 for c in color)  # type: ignore[return-value]


def render_chart(
    series: pd.Series,
    spec: ChartSpec,
    color: tuple[int, int, int],
    width_in: float = 7.0,
    height_in: float = 3.2,
) -> Path:
    """Render the chart to a PNG file and return its path."""
    mpl_color = _rgb_to_mpl(color)
    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=200)

    if spec.kind == "line":
        ax.plot(series.index.astype(str), series.values, color=mpl_color, linewidth=2, marker="o")
    elif spec.kind == "barh":
        ax.barh(series.index.astype(str)[::-1], series.values[::-1], color=mpl_color)
    else:
        ax.bar(series.index.astype(str), series.values, color=mpl_color)

    # The section title is printed by the PDF itself, so the figure stays clean.
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")
    ax.tick_params(labelsize=8, colors="#555555")
    ax.grid(axis="x" if spec.kind == "barh" else "y", color="#e8e8e8", linewidth=0.8)
    ax.set_axisbelow(True)

    if spec.kind != "barh" and len(series) > 4:
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    fig.tight_layout()
    tmp = Path(tempfile.mkstemp(suffix=".png", prefix="chart_")[1])
    fig.savefig(tmp, transparent=False, facecolor="white")
    plt.close(fig)
    return tmp
