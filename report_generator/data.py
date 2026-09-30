"""Data loading and aggregation.

Accepts .xlsx/.xls/.csv so the same pipeline works no matter what the
client exports from their system.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import ChartSpec, Config, KPI

_AGGREGATIONS = {"sum", "mean", "count", "min", "max", "nunique", "median"}


def load_dataframe(path: str | Path, sheet: str | int = 0) -> pd.DataFrame:
    """Read a spreadsheet or CSV into a DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        df = pd.read_excel(path, sheet_name=sheet)
    elif suffix in {".csv", ".txt"}:
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Normalise column names: strip whitespace, keep original casing.
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _aggregate(series: pd.Series, how: str) -> float:
    if how not in _AGGREGATIONS:
        raise ValueError(f"Unsupported aggregation: {how!r}")
    return float(getattr(series, how)())


def compute_kpis(df: pd.DataFrame, kpis: list[KPI]) -> list[tuple[str, str]]:
    """Return a list of (label, formatted_value) pairs."""
    results: list[tuple[str, str]] = []
    for kpi in kpis:
        if kpi.column not in df.columns:
            raise KeyError(f"KPI column {kpi.column!r} is not in the data")
        value = _aggregate(df[kpi.column], kpi.aggregation)
        results.append((kpi.label, kpi.number_format.format(value)))
    return results


def chart_series(df: pd.DataFrame, spec: ChartSpec) -> pd.Series:
    """Group and aggregate the data for the chart."""
    for column in (spec.group_by, spec.value_column):
        if column not in df.columns:
            raise KeyError(f"Chart column {column!r} is not in the data")

    grouped = getattr(df.groupby(spec.group_by)[spec.value_column], spec.aggregation)()
    grouped = grouped.sort_values(ascending=False)
    if spec.top_n:
        grouped = grouped.head(spec.top_n)
    return grouped


def table_frame(df: pd.DataFrame, config: Config) -> pd.DataFrame:
    """Select, sort and trim the rows that go into the PDF table."""
    spec = config.table
    columns = spec.columns or list(df.columns)
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Table columns not found in the data: {missing}")

    out = df[columns].copy()
    if spec.sort_by:
        out = out.sort_values(spec.sort_by, ascending=not spec.sort_desc)
    if spec.max_rows:
        out = out.head(spec.max_rows)
    return out.reset_index(drop=True)
