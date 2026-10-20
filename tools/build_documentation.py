#!/usr/bin/env python3
"""Build enterprise documentation PDFs from markdown volumes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
VOLUMES_DIR = DOCS / "volumes"
PDF_DIR = DOCS / "pdf"
MANIFEST_PATH = DOCS / "document-manifest.json"

PRIMARY = colors.HexColor("#1a365d")
ACCENT = colors.HexColor("#2b6cb0")
LIGHT_BG = colors.HexColor("#f7fafc")
BORDER = colors.HexColor("#e2e8f0")
TEXT = colors.HexColor("#2d3748")
MUTED = colors.HexColor("#718096")

VOLUMES = [
    ("01", "Product Requirements Document", "01-product-requirements.md", "01-product-requirements.pdf"),
    ("02", "Software Requirements Specification", "02-software-requirements.md", "02-software-requirements.pdf"),
    ("03", "System Design Document", "03-system-design.md", "03-system-design.pdf"),
    ("04", "Database Design", "04-database-design.md", "04-database-design.pdf"),
    ("05", "REST API Documentation", "05-rest-api.md", "05-rest-api.pdf"),
    ("06", "AI Design Document", "06-ai-design.md", "06-ai-design.pdf"),
    ("07", "UI/UX Specification", "07-ui-ux.md", "07-ui-ux.pdf"),
    ("08", "DevOps and Deployment", "08-devops-deployment.md", "08-devops-deployment.pdf"),
    ("09", "Testing Documentation", "09-testing.md", "09-testing.pdf"),
    ("10", "Project Management", "10-project-management.md", "10-project-management.pdf"),
]


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base["Title"], fontSize=24, leading=30, textColor=PRIMARY, alignment=TA_CENTER),
        "subtitle": ParagraphStyle("Subtitle", parent=base["Normal"], fontSize=12, leading=16, textColor=MUTED, alignment=TA_CENTER),
        "h1": ParagraphStyle("H1", parent=base["Heading1"], fontSize=16, leading=20, textColor=PRIMARY, spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("H2", parent=base["Heading2"], fontSize=13, leading=17, textColor=ACCENT, spaceBefore=12, spaceAfter=6),
        "h3": ParagraphStyle("H3", parent=base["Heading3"], fontSize=11, leading=14, textColor=TEXT, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base["Normal"], fontSize=9, leading=12, textColor=TEXT, alignment=TA_JUSTIFY, spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", parent=base["Normal"], fontSize=9, leading=12, textColor=TEXT, leftIndent=14, spaceAfter=2),
        "code": ParagraphStyle("Code", parent=base["Code"], fontSize=7.5, leading=9.5, textColor=TEXT, backColor=LIGHT_BG, leftIndent=10, fontName="Courier"),
        "toc": ParagraphStyle("TOC", parent=base["Normal"], fontSize=9, leading=12, leftIndent=10, spaceAfter=1),
        "caption": ParagraphStyle("Caption", parent=base["Normal"], fontSize=8, leading=10, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8),
    }


def escape_xml(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline_format(text: str) -> str:
    text = escape_xml(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def parse_table(lines: list[str], cell_style: ParagraphStyle) -> Table | None:
    rows = []
    for line in lines:
        if re.match(r"^\|[-:\s|]+\|$", line.strip()):
            continue
        cells = [inline_format(c.strip()) for c in line.strip().strip("|").split("|")]
        if cells:
            rows.append(cells)
    if not rows:
        return None
    col_count = max(len(r) for r in rows)
    rows = [r + [""] * (col_count - len(r)) for r in rows]
    wrapped = [[Paragraph(c, cell_style) for c in row] for row in rows]
    table = Table(wrapped, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def diagram_block(title: str, lines: list[str], styles: dict[str, ParagraphStyle]) -> list:
    story = [Paragraph(title, styles["h3"]), Spacer(1, 4)]
    box_rows = [[Paragraph(escape_xml(line), ParagraphStyle("d", fontSize=8, fontName="Courier"))] for line in lines]
    table = Table(box_rows, colWidths=[16 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, ACCENT),
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend([table, Spacer(1, 8)])
    return story


def add_cover(story: list, styles: dict[str, ParagraphStyle], volume_no: str, title: str) -> None:
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph("SentinelVision AI", styles["title"]))
    story.append(Paragraph(f"Volume {volume_no}", styles["subtitle"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(title, ParagraphStyle("vol", fontSize=14, alignment=TA_CENTER, textColor=ACCENT)))
    story.append(Spacer(1, 1.5 * cm))
    meta = [
        ["Suite Version", "1.0.0"],
        ["Classification", "Internal / Confidential"],
        ["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
    ]
    table = Table(meta, colWidths=[4.5 * cm, 8 * cm])
    table.setStyle(TableStyle([("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9)]))
    story.append(table)
    story.append(PageBreak())


def parse_markdown(md_text: str, styles: dict[str, ParagraphStyle]) -> list:
    story: list = []
    lines = md_text.splitlines()
    i = 0
    in_code = False
    code_buffer: list[str] = []
    table_buffer: list[str] = []
    cell_style = ParagraphStyle("cell", fontSize=8, leading=10)

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                if code_buffer and code_buffer[0].strip().startswith("mermaid"):
                    title = "Diagram"
                    diagram_lines = code_buffer[1:] if len(code_buffer) > 1 else ["(see source markdown diagram)"]
                    story.extend(diagram_block(title, diagram_lines, styles))
                else:
                    for code_line in code_buffer:
                        story.append(Paragraph(escape_xml(code_line), styles["code"]))
                    story.append(Spacer(1, 6))
                code_buffer = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue

        if in_code:
            code_buffer.append(line)
            i += 1
            continue

        if stripped.startswith("|"):
            table_buffer.append(stripped)
            i += 1
            if i >= len(lines) or not lines[i].strip().startswith("|"):
                table = parse_table(table_buffer, cell_style)
                if table:
                    story.extend([Spacer(1, 4), table, Spacer(1, 8)])
                table_buffer = []
            continue

        if stripped.startswith("# "):
            i += 1
            continue
        if stripped.startswith("## "):
            story.append(Spacer(1, 4))
            story.append(Paragraph(inline_format(stripped[3:]), styles["h1"]))
            i += 1
            continue
        if stripped.startswith("### "):
            story.append(Paragraph(inline_format(stripped[4:]), styles["h2"]))
            i += 1
            continue
        if stripped.startswith("#### "):
            story.append(Paragraph(inline_format(stripped[5:]), styles["h3"]))
            i += 1
            continue
        if stripped.startswith("---"):
            story.append(Spacer(1, 4))
            i += 1
            continue
        if stripped.startswith("- "):
            story.append(Paragraph(f"• {inline_format(stripped[2:])}", styles["bullet"]))
            i += 1
            continue
        if re.match(r"^\d+\.\s", stripped):
            story.append(Paragraph(inline_format(stripped), styles["bullet"]))
            i += 1
            continue
        if stripped:
            story.append(Paragraph(inline_format(stripped), styles["body"]))
        i += 1
    return story


def page_footer(canvas, doc, footer_text: str):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    page_num = canvas.getPageNumber()
    if page_num > 1:
        canvas.drawString(2 * cm, 1.2 * cm, footer_text)
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {page_num}")
    canvas.restoreState()


def build_volume_pdf(volume_no: str, title: str, source_name: str, pdf_name: str) -> Path:
    source = VOLUMES_DIR / source_name
    if not source.exists():
        raise FileNotFoundError(source)
    styles = build_styles()
    output = PDF_DIR / pdf_name
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        title=f"SentinelVision AI - Volume {volume_no}",
    )
    story: list = []
    add_cover(story, styles, volume_no, title)
    story.extend(parse_markdown(source.read_text(encoding="utf-8"), styles))
    footer = f"SentinelVision AI — Volume {volume_no} — {title}"
    doc.build(story, onFirstPage=lambda c, d: page_footer(c, d, footer), onLaterPages=lambda c, d: page_footer(c, d, footer))
    return output


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_combined_pdf(manifest_entries: list[dict]) -> Path:
    from pypdf import PdfWriter

    combined = PDF_DIR / "enterprise-ai-smart-security-documentation-suite.pdf"
    writer = PdfWriter()
    for entry in manifest_entries:
        writer.append(str(PDF_DIR / entry["pdf"]))
    with open(combined, "wb") as f:
        writer.write(f)
    writer.close()
    return combined


def write_manifest(entries: list[dict]) -> None:
    manifest = {
        "suite": "SentinelVision AI Enterprise Documentation",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "volumes": entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build documentation PDFs")
    parser.add_argument("--volume", help="Build only one volume number, e.g. 01")
    args = parser.parse_args()

    entries = []
    selected = VOLUMES
    if args.volume:
        selected = [v for v in VOLUMES if v[0] == args.volume.zfill(2)]
        if not selected:
            print(f"Unknown volume: {args.volume}", file=sys.stderr)
            return 1

    for vol_no, title, md_name, pdf_name in selected:
        print(f"Building Volume {vol_no}: {title}")
        pdf_path = build_volume_pdf(vol_no, title, md_name, pdf_name)
        source_path = VOLUMES_DIR / md_name
        entries.append(
            {
                "volume": vol_no,
                "title": title,
                "source": str(source_path.relative_to(ROOT)).replace("\\", "/"),
                "pdf": pdf_name,
                "source_sha256": sha256_file(source_path),
                "pdf_sha256": sha256_file(pdf_path),
                "pdf_size_kb": round(pdf_path.stat().st_size / 1024, 1),
            }
        )
        print(f"  -> {pdf_path} ({entries[-1]['pdf_size_kb']} KB)")

    # Update manifest with all volumes if building full suite
    if not args.volume:
        full_entries = []
        for vol_no, title, md_name, pdf_name in VOLUMES:
            source_path = VOLUMES_DIR / md_name
            pdf_path = PDF_DIR / pdf_name
            if pdf_path.exists():
                full_entries.append(
                    {
                        "volume": vol_no,
                        "title": title,
                        "source": str(source_path.relative_to(ROOT)).replace("\\", "/"),
                        "pdf": pdf_name,
                        "source_sha256": sha256_file(source_path),
                        "pdf_sha256": sha256_file(pdf_path),
                        "pdf_size_kb": round(pdf_path.stat().st_size / 1024, 1),
                    }
                )
        write_manifest(full_entries)
        try:
            combined = build_combined_pdf(full_entries)
            print(f"Combined suite PDF: {combined}")
        except Exception as exc:
            print(f"Combined PDF skipped: {exc}")
    else:
        write_manifest(entries)

    print(f"Manifest written: {MANIFEST_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
