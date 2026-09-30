"""PDF layout: letterhead, KPI cards, chart and data table.

Built with fpdf2. The header and footer are drawn automatically on every
page, so multi-page reports keep the letterhead and page numbering.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from fpdf import FPDF

from .config import Config

PAGE_MARGIN = 15.0


class ReportPDF(FPDF):
    def __init__(self, config: Config, generated_at: datetime):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.config = config
        self.generated_at = generated_at
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN)
        self.set_title(config.branding.document_title)
        self.set_author(config.branding.company_name)

    # --- letterhead -----------------------------------------------------
    def header(self) -> None:
        b = self.config.branding
        top = 10.0

        if b.logo_path and Path(b.logo_path).exists():
            self.image(b.logo_path, x=PAGE_MARGIN, y=top - 2, h=14)
            text_x = PAGE_MARGIN + 20
        else:
            text_x = PAGE_MARGIN

        self.set_xy(text_x, top)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*b.primary_color)
        self.cell(0, 6, b.company_name, new_x="LMARGIN", new_y="NEXT")

        self.set_x(text_x)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, b.document_title, new_x="LMARGIN", new_y="NEXT")

        # Date, right aligned on the first header line.
        self.set_xy(-70 - PAGE_MARGIN, top + 1)
        self.set_font("Helvetica", "", 9)
        self.cell(70, 5, self.generated_at.strftime("%d/%m/%Y %H:%M"), align="R")

        # Rule under the letterhead.
        y = top + 14
        self.set_draw_color(*b.primary_color)
        self.set_line_width(0.6)
        self.line(PAGE_MARGIN, y, self.w - PAGE_MARGIN, y)
        self.set_y(y + 8)

    def footer(self) -> None:
        b = self.config.branding
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.2)
        self.line(PAGE_MARGIN, self.get_y(), self.w - PAGE_MARGIN, self.get_y())
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, b.footer_text or b.company_name, align="L")
        self.set_y(-12)
        self.cell(0, 5, f"Page {self.page_no()} / {{nb}}", align="R")

    # --- content blocks -------------------------------------------------
    def title_block(self) -> None:
        b = self.config.branding
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*b.text_color)
        self.cell(0, 9, b.document_title, new_x="LMARGIN", new_y="NEXT")
        if b.subtitle:
            self.set_font("Helvetica", "", 10)
            self.set_text_color(110, 110, 110)
            self.multi_cell(0, 5, b.subtitle)
        self.ln(4)

    def kpi_cards(self, kpis: list[tuple[str, str]]) -> None:
        if not kpis:
            return
        b = self.config.branding
        usable = self.w - 2 * PAGE_MARGIN
        gap = 4.0
        n = len(kpis)
        card_w = (usable - gap * (n - 1)) / n
        card_h = 20.0
        y = self.get_y()

        for i, (label, value) in enumerate(kpis):
            x = PAGE_MARGIN + i * (card_w + gap)
            self.set_fill_color(245, 247, 250)
            self.set_draw_color(225, 230, 236)
            self.set_line_width(0.2)
            self.rect(x, y, card_w, card_h, style="DF")

            self.set_xy(x + 3, y + 3.5)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(120, 120, 120)
            self.cell(card_w - 6, 4, label.upper()[:28])

            self.set_xy(x + 3, y + 9)
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*b.primary_color)
            self.cell(card_w - 6, 8, value)

        self.set_y(y + card_h + 8)

    def section_title(self, text: str) -> None:
        b = self.config.branding
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*b.primary_color)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def chart_image(self, png_path: Path) -> None:
        usable = self.w - 2 * PAGE_MARGIN
        self.image(str(png_path), x=PAGE_MARGIN, w=usable)
        self.ln(6)

    def data_table(self, df: pd.DataFrame) -> None:
        b = self.config.branding
        spec = self.config.table
        headers = [spec.headers.get(c, c) for c in df.columns]
        usable = self.w - 2 * PAGE_MARGIN
        col_w = usable / len(df.columns)
        row_h = 6.5

        def draw_header() -> None:
            self.set_font("Helvetica", "B", 8)
            self.set_fill_color(*b.primary_color)
            self.set_text_color(255, 255, 255)
            for head in headers:
                self.cell(col_w, row_h, str(head)[:26], border=0, align="C", fill=True)
            self.ln(row_h)

        draw_header()
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*b.text_color)

        for i, (_, row) in enumerate(df.iterrows()):
            if self.get_y() + row_h > self.h - 22:  # keep the footer clear
                self.add_page()
                draw_header()
                self.set_font("Helvetica", "", 8)
                self.set_text_color(*b.text_color)

            fill = i % 2 == 1
            if fill:
                self.set_fill_color(246, 248, 250)
            for column in df.columns:
                value = row[column]
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    # Whole numbers (quantities, counts) read better without decimals.
                    fmt = "{:,.0f}" if float(value).is_integer() else spec.number_format
                    text = fmt.format(value)
                    align = "R"
                else:
                    text = str(value)
                    align = "L"
                self.cell(col_w, row_h, text[:30], border=0, align=align, fill=fill)
            self.ln(row_h)

        self.ln(4)


def build_pdf(
    config: Config,
    kpis: list[tuple[str, str]],
    chart_png: Path | None,
    table: pd.DataFrame | None,
    output_path: str | Path,
) -> Path:
    pdf = ReportPDF(config, datetime.now())
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.title_block()
    pdf.kpi_cards(kpis)

    if chart_png is not None:
        if config.chart.title:
            pdf.section_title(config.chart.title)
        pdf.chart_image(chart_png)

    if table is not None and not table.empty:
        pdf.section_title("Detail")
        pdf.data_table(table)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
