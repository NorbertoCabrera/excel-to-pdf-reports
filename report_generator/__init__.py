"""Excel/CSV -> branded PDF report generator."""

from .config import Config
from .data import compute_kpis, chart_series, load_dataframe, table_frame
from .chart import render_chart
from .pdf_builder import build_pdf

__version__ = "1.0.0"
__all__ = [
    "Config",
    "load_dataframe",
    "compute_kpis",
    "chart_series",
    "table_frame",
    "render_chart",
    "build_pdf",
]
