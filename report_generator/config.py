"""Configuration loading and validation.

The whole look of the report (branding, colours, which columns are shown,
which KPIs are computed) is driven by a single YAML file, so a new client
only needs a new config -- not new code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid hex colour: {value!r}")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


@dataclass
class Branding:
    company_name: str = "Your Company"
    document_title: str = "Report"
    subtitle: str = ""
    logo_path: str | None = None
    footer_text: str = ""
    primary_color: tuple[int, int, int] = (17, 66, 108)
    accent_color: tuple[int, int, int] = (0, 150, 136)
    text_color: tuple[int, int, int] = (40, 40, 40)


@dataclass
class KPI:
    label: str
    column: str
    aggregation: str = "sum"  # sum | mean | count | min | max | nunique
    number_format: str = "{:,.0f}"


@dataclass
class ChartSpec:
    enabled: bool = True
    title: str = ""
    kind: str = "bar"  # bar | line | barh
    group_by: str = ""
    value_column: str = ""
    aggregation: str = "sum"
    top_n: int = 10


@dataclass
class TableSpec:
    columns: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    number_format: str = "{:,.2f}"
    max_rows: int | None = None
    sort_by: str | None = None
    sort_desc: bool = True


@dataclass
class Config:
    branding: Branding = field(default_factory=Branding)
    kpis: list[KPI] = field(default_factory=list)
    chart: ChartSpec = field(default_factory=ChartSpec)
    table: TableSpec = field(default_factory=TableSpec)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        raw: dict[str, Any] = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}

        b = raw.get("branding", {}) or {}
        branding = Branding(
            company_name=b.get("company_name", Branding.company_name),
            document_title=b.get("document_title", Branding.document_title),
            subtitle=b.get("subtitle", ""),
            logo_path=b.get("logo_path"),
            footer_text=b.get("footer_text", ""),
            primary_color=_hex_to_rgb(b.get("primary_color", "#11426C")),
            accent_color=_hex_to_rgb(b.get("accent_color", "#009688")),
            text_color=_hex_to_rgb(b.get("text_color", "#282828")),
        )

        kpis = [
            KPI(
                label=k["label"],
                column=k["column"],
                aggregation=k.get("aggregation", "sum"),
                number_format=k.get("number_format", "{:,.0f}"),
            )
            for k in raw.get("kpis", []) or []
        ]

        c = raw.get("chart", {}) or {}
        chart = ChartSpec(
            enabled=c.get("enabled", bool(c)),
            title=c.get("title", ""),
            kind=c.get("kind", "bar"),
            group_by=c.get("group_by", ""),
            value_column=c.get("value_column", ""),
            aggregation=c.get("aggregation", "sum"),
            top_n=int(c.get("top_n", 10)),
        )

        t = raw.get("table", {}) or {}
        table = TableSpec(
            columns=t.get("columns", []) or [],
            headers=t.get("headers", {}) or {},
            number_format=t.get("number_format", "{:,.2f}"),
            max_rows=t.get("max_rows"),
            sort_by=t.get("sort_by"),
            sort_desc=bool(t.get("sort_desc", True)),
        )

        return cls(branding=branding, kpis=kpis, chart=chart, table=table)
