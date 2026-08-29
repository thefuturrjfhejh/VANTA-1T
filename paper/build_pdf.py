#!/usr/bin/env python3
"""Render the VANTA-1T preprint as a designed, source-linked PDF."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "preprint.md"
RESULTS = ROOT / "model" / "output" / "results.json"
OUTPUT = ROOT / "output" / "pdf" / "VANTA-1T_preprint.pdf"

INK = HexColor("#172235")
MUTED = HexColor("#526077")
TEAL = HexColor("#00A7A0")
TEAL_DARK = HexColor("#08746F")
LIME = HexColor("#A4D65E")
BLUE = HexColor("#2E67D1")
ORANGE = HexColor("#F29D49")
RED = HexColor("#D95C5C")
PAPER = HexColor("#F7F8F4")
PANEL = HexColor("#EAF1EE")
GRID = HexColor("#CBD6D2")


class SectionRule(Flowable):
    def __init__(self, width: float, color=TEAL):
        super().__init__()
        self.width = width
        self.height = 3
        self.color = color

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(2.2)
        self.canv.line(0, 1.4, self.width, 1.4)


def inline_markup(text: str) -> str:
    escaped = html.escape(text.strip())
    escaped = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"(?<![\"'=])(https?://[^\s<]+)",
        lambda m: f'<link href="{m.group(1)}" color="#08746F">{m.group(1)}</link>',
        escaped,
    )
    return escaped


def make_styles():
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.4,
            leading=11.2,
            textColor=INK,
            spaceAfter=4.5,
            alignment=TA_LEFT,
            allowWidows=0,
            allowOrphans=0,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=INK,
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=13.5,
            textColor=TEAL_DARK,
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True,
        ),
        "abstract": ParagraphStyle(
            "Abstract",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12.4,
            textColor=INK,
            leftIndent=7 * mm,
            rightIndent=7 * mm,
            borderColor=TEAL,
            borderWidth=1.2,
            borderPadding=8,
            backColor=PANEL,
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.2,
            leading=10.8,
            textColor=INK,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2.5,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            textColor=TEAL_DARK,
            leftIndent=9 * mm,
            rightIndent=9 * mm,
            borderColor=LIME,
            borderWidth=0,
            borderLeft=3,
            borderPadding=7,
            backColor=HexColor("#F1F6E8"),
            spaceBefore=5,
            spaceAfter=7,
        ),
        "equation": ParagraphStyle(
            "Equation",
            parent=base["BodyText"],
            fontName="Courier-Bold",
            fontSize=8.5,
            leading=12,
            alignment=TA_CENTER,
            textColor=INK,
            backColor=HexColor("#EEF1F5"),
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.2,
            leading=9,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "table": ParagraphStyle(
            "TableCell",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=6.8,
            leading=8.3,
            textColor=INK,
        ),
        "table_head": ParagraphStyle(
            "TableHead",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8.3,
            textColor=colors.white,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=9.3,
            textColor=MUTED,
        ),
    }


def architecture_figure() -> Drawing:
    d = Drawing(470, 178)
    d.add(Rect(0, 0, 470, 178, rx=8, ry=8, fillColor=HexColor("#F4F7F5"), strokeColor=GRID))
    d.add(String(16, 158, "VANTA-1T package dataflow", fontName="Helvetica-Bold", fontSize=11, fillColor=INK))

    # HBM sectors
    for i, label in enumerate(("HBM4 A", "HBM4 B", "HBM4 C", "HBM4 D")):
        x = 18 + i * 112
        d.add(Rect(x, 106, 94, 36, rx=4, ry=4, fillColor=HexColor("#DDF2EE"), strokeColor=TEAL_DARK))
        d.add(String(x + 47, 129, label, fontName="Helvetica-Bold", fontSize=8, textAnchor="middle", fillColor=INK))
        d.add(String(x + 47, 116, "binary MAC", fontName="Helvetica", fontSize=7, textAnchor="middle", fillColor=TEAL_DARK))

    # Fabric and chiplets
    d.add(Rect(18, 79, 430, 12, rx=3, ry=3, fillColor=TEAL, strokeColor=TEAL))
    d.add(String(233, 82, "route + memory fabric", fontName="Helvetica-Bold", fontSize=6.8, textAnchor="middle", fillColor=colors.white))
    for i in range(4):
        x = 18 + i * 112
        d.add(Rect(x, 27, 94, 38, rx=4, ry=4, fillColor=HexColor("#E6ECFA"), strokeColor=BLUE))
        d.add(String(x + 47, 50, f"compute chiplet {i + 1}", fontName="Helvetica-Bold", fontSize=7.3, textAnchor="middle", fillColor=INK))
        d.add(String(x + 47, 37, "residual + attention", fontName="Helvetica", fontSize=6.4, textAnchor="middle", fillColor=BLUE))
        d.add(Line(x + 47, 65, x + 47, 79, strokeColor=BLUE, strokeWidth=1.2))
        d.add(Polygon([x + 44, 75, x + 50, 75, x + 47, 79], fillColor=BLUE, strokeColor=BLUE))

    d.add(String(18, 10, "Top-k is resolved before expert movement; higher precision work stays on compute chiplets.", fontName="Helvetica-Oblique", fontSize=7, fillColor=MUTED))
    return d


def memory_chart(results: dict) -> Drawing:
    fp8 = 1026.686
    mxfp4 = results["headline"]["mxfp4_resident_weight_gb"]
    balanced = 306.924
    stretch = results["headline"]["vanta_stretch_resident_weight_gb"]
    d = Drawing(470, 206)
    d.add(Rect(0, 0, 470, 206, rx=8, ry=8, fillColor=HexColor("#F4F7F5"), strokeColor=GRID))
    d.add(String(18, 184, "Resident weight image (decimal GB)", fontName="Helvetica-Bold", fontSize=11, fillColor=INK))
    chart = VerticalBarChart()
    chart.x = 50
    chart.y = 37
    chart.height = 125
    chart.width = 385
    chart.data = [[fp8, mxfp4, balanced, stretch]]
    chart.categoryAxis.categoryNames = ["FP8", "MXFP4", "Balanced", "Stretch"]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 1100
    chart.valueAxis.valueStep = 200
    chart.valueAxis.labels.fontName = "Helvetica"
    chart.valueAxis.labels.fontSize = 6.5
    chart.valueAxis.gridStrokeColor = GRID
    chart.valueAxis.gridStrokeWidth = 0.5
    chart.bars[0].fillColor = TEAL
    chart.bars[0].strokeColor = TEAL_DARK
    chart.barWidth = 38
    chart.barSpacing = 18
    d.add(chart)
    for x, value in zip((95, 192, 289, 386), (fp8, mxfp4, balanced, stretch)):
        y = 42 + (value / 1100) * 125
        d.add(String(x, min(y + 4, 171), f"{value:.1f}", fontName="Helvetica-Bold", fontSize=7, textAnchor="middle", fillColor=INK))
    d.add(String(450, 11, "Calculated, not measured", fontName="Helvetica-Oblique", fontSize=6.5, textAnchor="end", fillColor=MUTED))
    return d


def validation_figure() -> Drawing:
    d = Drawing(470, 103)
    d.add(Rect(0, 0, 470, 103, rx=8, ry=8, fillColor=HexColor("#F4F7F5"), strokeColor=GRID))
    d.add(String(18, 82, "Evidence ladder", fontName="Helvetica-Bold", fontSize=11, fillColor=INK))
    labels = (("1", "quality"), ("2", "traffic"), ("3", "RTL"), ("4", "physical"), ("5", "system"))
    for i, (number, label) in enumerate(labels):
        x = 18 + i * 89
        color = ORANGE if i == 0 else BLUE
        d.add(Rect(x, 31, 68, 32, rx=5, ry=5, fillColor=colors.white, strokeColor=color, strokeWidth=1.3))
        d.add(String(x + 12, 47, number, fontName="Helvetica-Bold", fontSize=10, fillColor=color))
        d.add(String(x + 25, 47, label, fontName="Helvetica-Bold", fontSize=7.3, fillColor=INK))
        if i < len(labels) - 1:
            d.add(Line(x + 68, 47, x + 86, 47, strokeColor=MUTED, strokeWidth=1))
            d.add(Polygon([x + 82, 44, x + 87, 47, x + 82, 50], fillColor=MUTED, strokeColor=MUTED))
    d.add(String(18, 14, "The 68.1% capacity point is publishable as analysis; quality remains the first falsification gate.", fontName="Helvetica-Oblique", fontSize=7, fillColor=MUTED))
    return d


def table_from_rows(rows: list[list[str]], styles, page_width: float) -> Table:
    ncols = len(rows[0])
    if ncols == 2:
        widths = [page_width * 0.72, page_width * 0.28]
    elif ncols == 3:
        widths = [page_width * 0.47, page_width * 0.18, page_width * 0.35]
    elif ncols == 4:
        widths = [page_width * 0.38, page_width * 0.18, page_width * 0.22, page_width * 0.22]
    elif ncols == 6:
        widths = [page_width * 0.25] + [page_width * 0.15] * 5
    elif ncols == 7:
        widths = [page_width * 0.22] + [page_width * 0.13] * 6
    else:
        widths = [page_width / ncols] * ncols
    # Normalize rounding and make text paragraph-aware.
    scale = page_width / sum(widths)
    widths = [w * scale for w in widths]
    cooked = []
    for r_idx, row in enumerate(rows):
        style = styles["table_head"] if r_idx == 0 else styles["table"]
        cooked.append([Paragraph(inline_markup(cell), style) for cell in row])
    table = Table(cooked, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL_DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#F0F4F2")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    return table


def cover_story(results: dict, styles, page_width: float):
    reduction = results["headline"]["weight_reduction_vs_mxfp4_pct"]
    weight = results["headline"]["vanta_stretch_resident_weight_gb"]
    story = [Spacer(1, 15 * mm)]
    story.append(Paragraph("OPEN ARCHITECTURE STUDY / VERSION 0.1", ParagraphStyle(
        "Kicker", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=TEAL_DARK, tracking=1.5
    )))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("VANTA-1T", ParagraphStyle(
        "CoverTitle", fontName="Helvetica-Bold", fontSize=39, leading=42, textColor=INK
    )))
    story.append(Paragraph("An Analytical Single-Package Inference Architecture for Trillion-Parameter Mixture-of-Experts Models", ParagraphStyle(
        "CoverSub", fontName="Helvetica", fontSize=17, leading=21, textColor=MUTED, spaceAfter=8 * mm
    )))
    story.append(SectionRule(page_width, TEAL))
    story.append(Spacer(1, 8 * mm))
    cards = Table(
        [
            [
                Paragraph(f"<b><font size=22>{reduction:.1f}%</font></b><br/><font size=8>less resident weight memory<br/>vs modeled MXFP4</font>", styles["body"]),
                Paragraph(f"<b><font size=22>{weight:.1f} GB</font></b><br/><font size=8>stretch weight image<br/>inside 192 GB target</font>", styles["body"]),
                Paragraph("<b><font size=22>1T / 32B</font></b><br/><font size=8>total / active parameters<br/>reference workload</font>", styles["body"]),
            ]
        ],
        colWidths=[page_width / 3] * 3,
    )
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("BOX", (0, 0), (-1, -1), 0.7, GRID),
        ("INNERGRID", (0, 0), (-1, -1), 0.7, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
    ]))
    story.append(cards)
    story.append(Spacer(1, 9 * mm))
    story.append(architecture_figure())
    story.append(Spacer(1, 7 * mm))
    status = Table([[Paragraph(
        "<b>STATUS:</b> capacity-plausible, quality-unproven. No fabricated silicon and no measured performance.",
        styles["body"],
    )]], colWidths=[page_width])
    status.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FFF0DE")),
        ("BOX", (0, 0), (-1, -1), 0.8, ORANGE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(status)
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("Mahee Monjur / Independent Researcher", ParagraphStyle(
        "Author", fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=INK
    )))
    story.append(Paragraph("26 August 2026", styles["small"]))
    story.append(PageBreak())
    return story


def parse_markdown(text: str, results: dict, styles, page_width: float):
    lines = text.splitlines()
    story = []
    i = 0
    # Skip title, author and version block already represented on the cover.
    while i < len(lines) and not lines[i].startswith("## Abstract"):
        i += 1

    paragraph_lines: list[str] = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if not paragraph_lines:
            return
        text_value = " ".join(line.strip() for line in paragraph_lines)
        style = styles["body"]
        if story and isinstance(story[-1], Paragraph) and getattr(story[-1], "style", None) == styles["h1"] and "Abstract" in story[-1].getPlainText():
            style = styles["abstract"]
        elif re.match(r"^(P_routed|M_weights|M_KV|tokens/s)", text_value):
            style = styles["equation"]
        story.append(Paragraph(inline_markup(text_value), style))
        paragraph_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            heading = stripped[3:]
            heading_group = [Spacer(1, 2), Paragraph(inline_markup(heading), styles["h1"]), SectionRule(page_width)]
            if heading.startswith("3. Architecture"):
                heading_group.extend([Spacer(1, 5), architecture_figure(), Paragraph("Figure 1. Package-level split between near-memory binary expert work and higher-precision chiplet work.", styles["caption"])])
            elif heading.startswith("6. Results"):
                heading_group.extend([Spacer(1, 5), memory_chart(results), Paragraph("Figure 2. Analytical resident weight image. VANTA profiles are quality hypotheses; the values are not silicon measurements.", styles["caption"])])
            elif heading.startswith("7. Validation"):
                heading_group.extend([Spacer(1, 5), validation_figure(), Paragraph("Figure 3. Validation sequence from the first quality falsification gate to end-to-end system evidence.", styles["caption"])])
            story.append(KeepTogether(heading_group))
            i += 1
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[4:]), styles["h2"]))
            i += 1
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            quote_parts = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_parts.append(lines[i].strip().lstrip(">").strip())
                i += 1
            story.append(Paragraph(inline_markup(" ".join(quote_parts)), styles["quote"]))
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = []
            for idx, table_line in enumerate(table_lines):
                cells = [c.strip() for c in table_line.strip("|").split("|")]
                if idx == 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    continue
                rows.append(cells)
            story.append(KeepTogether([table_from_rows(rows, styles, page_width), Spacer(1, 5)]))
            continue

        if re.match(r"^(\d+\.|-) ", stripped):
            flush_paragraph()
            match = re.match(r"^(\d+\.|-) (.*)", stripped)
            marker, item = match.groups()
            i += 1
            continuation = []
            while i < len(lines):
                next_line = lines[i]
                if not next_line.strip() or re.match(r"^(\d+\.|-) ", next_line.strip()) or next_line.startswith("##"):
                    break
                continuation.append(next_line.strip())
                i += 1
            text_value = " ".join([item] + continuation)
            symbol = "-" if marker == "-" else marker
            story.append(Paragraph(f"<b>{symbol}</b>&nbsp;&nbsp;{inline_markup(text_value)}", styles["bullet"]))
            continue

        paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    return story


def draw_page(canvas, doc):
    width, height = A4
    page = canvas.getPageNumber()
    if page == 1:
        return
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(20 * mm, height - 15 * mm, width - 20 * mm, height - 15 * mm)
    canvas.setFont("Helvetica-Bold", 7)
    canvas.setFillColor(TEAL_DARK)
    canvas.drawString(20 * mm, height - 11 * mm, "VANTA-1T / OPEN ANALYTICAL DESIGN STUDY")
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(width - 20 * mm, height - 11 * mm, "Mahee Monjur / v0.1 / 26 Aug 2026")
    canvas.line(20 * mm, 13 * mm, width - 20 * mm, 13 * mm)
    canvas.drawString(20 * mm, 8.5 * mm, "Calculated capacities and ceilings - no fabricated silicon")
    canvas.drawRightString(width - 20 * mm, 8.5 * mm, str(page))
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text(encoding="utf-8"))
    source = SOURCE.read_text(encoding="utf-8")
    styles = make_styles()
    page_width = A4[0] - 40 * mm
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=21 * mm,
        bottomMargin=18 * mm,
        title="VANTA-1T: An Analytical Single-Package Inference Architecture",
        author="Mahee Monjur",
        subject="Open analytical architecture study for 1T MoE inference",
        creator="VANTA-1T artifact",
    )
    story = cover_story(results, styles, page_width)
    story.extend(parse_markdown(source, results, styles, page_width))
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(OUTPUT)


if __name__ == "__main__":
    build()
