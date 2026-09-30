"""Command line entry point.

Usage:
    python -m report_generator --data examples/sample_sales.xlsx \
        --config examples/config_sales.yaml --output output/report.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .chart import render_chart
from .config import Config
from .data import chart_series, compute_kpis, load_dataframe, table_frame
from .pdf_builder import build_pdf


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="report_generator",
        description="Turn an Excel/CSV file into a branded PDF report.",
    )
    parser.add_argument("--data", required=True, help="Path to .xlsx, .xls or .csv input file")
    parser.add_argument("--config", required=True, help="Path to the YAML config file")
    parser.add_argument("--output", default="output/report.pdf", help="Path of the PDF to write")
    parser.add_argument("--sheet", default=0, help="Sheet name or index (Excel only)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = Config.from_yaml(args.config)
        sheet = int(args.sheet) if str(args.sheet).isdigit() else args.sheet
        df = load_dataframe(args.data, sheet=sheet)

        kpis = compute_kpis(df, config.kpis)

        chart_png = None
        if config.chart.enabled and config.chart.group_by and config.chart.value_column:
            series = chart_series(df, config.chart)
            chart_png = render_chart(series, config.chart, config.branding.accent_color)

        table = table_frame(df, config) if config.table.columns else None

        out = build_pdf(config, kpis, chart_png, table, args.output)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"PDF written to {Path(out).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
