#!/usr/bin/env python3
"""Build the A5 print-oriented ORBIT book prototype PDF."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
import sys

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A5
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
)


PAPER = colors.HexColor("#F6F2E9")
INK = colors.HexColor("#171715")
MUTED = colors.HexColor("#6F6A62")
ACCENT = colors.HexColor("#DF501F")
CREAM = colors.HexColor("#F7F2E9")


def inline_markup(text: str) -> str:
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='OrbitRegular'>\1</font>", text)
    return text


class CoverPage(Flowable):
    def __init__(self, artwork: Path, title: str, subtitle: str) -> None:
        super().__init__()
        self.artwork = artwork
        self.title = title
        self.subtitle = subtitle
        self.width, self.height = A5

    def wrap(self, avail_width, avail_height):
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        with PILImage.open(self.artwork) as image:
            ratio = image.width / image.height
        draw_width = self.width
        draw_height = draw_width / ratio
        y = (self.height - draw_height) / 2
        canvas.drawImage(
            str(self.artwork), 0, y, width=draw_width, height=draw_height, mask="auto"
        )
        canvas.setFillColor(colors.Color(0, 0, 0, alpha=0.22))
        canvas.rect(0, self.height - 67 * mm, self.width, 67 * mm, fill=1, stroke=0)
        canvas.setFillColor(CREAM)
        canvas.setFont("OrbitBold", 8.5)
        canvas.drawString(15 * mm, self.height - 17 * mm, "ORBIT PHILOSOPHY")
        canvas.setFont("OrbitBold", 22)
        canvas.drawString(15 * mm, self.height - 33 * mm, "첫 결과물이 곧")
        canvas.drawString(15 * mm, self.height - 46 * mm, "완성은 아니다")
        canvas.setFont("OrbitRegular", 7.7)
        canvas.setFillColor(colors.HexColor("#D9D2C7"))
        canvas.drawString(15 * mm, self.height - 57 * mm, self.subtitle)
        canvas.setFillColor(ACCENT)
        canvas.circle(15 * mm, 16 * mm, 1.3 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#AAA49B"))
        canvas.setFont("OrbitRegular", 7.2)
        canvas.drawString(20 * mm, 14.8 * mm, "PDF PROTOTYPE · v0.2")


class OrbitDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs) -> None:
        super().__init__(filename, **kwargs)
        self._outline_index = 0

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        level = getattr(flowable, "outline_level", None)
        if level is None:
            return
        self._outline_index += 1
        key = f"section-{self._outline_index}"
        text = flowable.getPlainText()
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)


def heading(text: str, style: ParagraphStyle, level: int) -> Paragraph:
    paragraph = Paragraph(inline_markup(text), style)
    paragraph.outline_level = level
    return paragraph


def parse_markdown(path: Path, styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    lines = path.read_text(encoding="utf-8").splitlines()
    story: list[Flowable] = []
    paragraph_lines: list[str] = []
    quote_lines: list[str] = []
    skip_draft_quote = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            story.append(Paragraph(inline_markup(" ".join(paragraph_lines)), styles["body"]))
            story.append(Spacer(1, 2.5 * mm))
            paragraph_lines = []

    def flush_quote() -> None:
        nonlocal quote_lines, skip_draft_quote
        if not quote_lines:
            return
        text = " ".join(quote_lines)
        if "Version: SAMPLE MVP" not in text:
            story.append(Paragraph(inline_markup(text), styles["quote"]))
            story.append(Spacer(1, 2.5 * mm))
        quote_lines = []
        skip_draft_quote = False

    for line in lines + [""]:
        stripped = line.strip()
        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines.append(stripped.lstrip("> "))
            continue
        flush_quote()

        if not stripped:
            flush_paragraph()
            continue
        if stripped == "---":
            flush_paragraph()
            story.append(Spacer(1, 2 * mm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDB5A9")))
            story.append(Spacer(1, 4 * mm))
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            story.append(PageBreak())
            story.append(heading(stripped[2:], styles["h1"], 0))
            story.append(Spacer(1, 5 * mm))
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            if stripped[3:] == "독자 기록":
                story.append(PageBreak())
            story.append(heading(stripped[3:], styles["h2"], 1))
            story.append(Spacer(1, 2 * mm))
            continue
        if re.match(r"^\d+\.\s", stripped):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped), styles["list"]))
            story.append(Spacer(1, 1.2 * mm))
            continue
        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(inline_markup(stripped[2:]), styles["bullet"], bulletText="•"))
            story.append(Spacer(1, 1.2 * mm))
            continue
        paragraph_lines.append(stripped)

    return story


def draw_body_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, A5[0], A5[1], fill=1, stroke=0)
    if doc.page > 2:
        canvas.setStrokeColor(colors.HexColor("#D7CFC2"))
        canvas.setLineWidth(0.35)
        canvas.line(18 * mm, 13 * mm, A5[0] - 18 * mm, 13 * mm)
        canvas.setFillColor(MUTED)
        canvas.setFont("OrbitRegular", 6.8)
        canvas.drawString(18 * mm, 8.2 * mm, "첫 결과물이 곧 완성은 아니다")
        canvas.drawRightString(A5[0] - 18 * mm, 8.2 * mm, str(doc.page))
    canvas.restoreState()


def build(repo_root: Path, output: Path) -> None:
    assets = repo_root / "tracks/book/assets"
    regular_font = assets / "fonts/NotoSansKR-Book-Regular.ttf"
    bold_font = assets / "fonts/NotoSansKR-Book-Bold.ttf"
    pdfmetrics.registerFont(TTFont("OrbitRegular", regular_font))
    pdfmetrics.registerFont(TTFont("OrbitBold", bold_font))

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="OrbitRegular",
        fontSize=9.5,
        leading=16.2,
        textColor=INK,
        wordWrap="CJK",
        spaceAfter=0,
    )
    style_map = {
        "body": body,
        "h1": ParagraphStyle(
            "H1", parent=body, fontName="OrbitBold", fontSize=21, leading=28,
            textColor=INK, spaceBefore=8 * mm, borderWidth=0, wordWrap="CJK"
        ),
        "h2": ParagraphStyle(
            "H2", parent=body, fontName="OrbitBold", fontSize=13, leading=19,
            textColor=INK, spaceBefore=7 * mm, keepWithNext=True, wordWrap="CJK"
        ),
        "quote": ParagraphStyle(
            "Quote", parent=body, fontSize=9.2, leading=15.5, leftIndent=7 * mm,
            rightIndent=3 * mm, borderColor=ACCENT, borderWidth=0,
            borderPadding=(0, 0, 0, 4 * mm), textColor=colors.HexColor("#504C46"),
            wordWrap="CJK"
        ),
        "list": ParagraphStyle(
            "List", parent=body, leftIndent=5 * mm, firstLineIndent=-5 * mm,
            fontSize=9.1, leading=14.5, wordWrap="CJK"
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=body, leftIndent=6 * mm, firstLineIndent=-3 * mm,
            bulletIndent=1 * mm, fontSize=9.1, leading=14.5, wordWrap="CJK"
        ),
    }

    margin_x = 18 * mm
    frame = Frame(
        margin_x,
        17 * mm,
        A5[0] - 2 * margin_x,
        A5[1] - 32 * mm,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="body",
    )
    cover_frame = Frame(
        0,
        0,
        A5[0],
        A5[1],
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="cover",
    )
    cover_template = PageTemplate(id="cover", frames=[cover_frame])
    body_template = PageTemplate(id="body", frames=[frame], onPage=draw_body_page)
    doc = OrbitDocTemplate(
        str(output),
        pagesize=A5,
        pageTemplates=[cover_template, body_template],
        title="첫 결과물이 곧 완성은 아니다",
        author="ORBIT Philosophy",
        subject="첫 프롬프트와 MVP 이후, 인간과 LLM이 함께 완성해 가는 법",
        creator="ORBIT Philosophy PDF pipeline",
    )

    story: list[Flowable] = [
        CoverPage(
            assets / "cover-art-v0.1.png",
            "첫 결과물이 곧 완성은 아니다",
            "첫 프롬프트와 MVP 이후, 인간과 LLM이 함께 완성해 가는 법",
        ),
        NextPageTemplate("body"),
        PageBreak(),
        Spacer(1, 30 * mm),
        Paragraph("첫 결과물이 곧<br/>완성은 아니다", ParagraphStyle(
            "Title", parent=body, fontName="OrbitBold", fontSize=25, leading=33,
            alignment=TA_LEFT, textColor=INK, wordWrap="CJK"
        )),
        Spacer(1, 5 * mm),
        Paragraph("첫 프롬프트와 MVP 이후,<br/>인간과 LLM이 함께 완성해 가는 법", ParagraphStyle(
            "Subtitle", parent=body, fontSize=10.5, leading=17, textColor=MUTED,
            wordWrap="CJK"
        )),
        Spacer(1, 38 * mm),
        Paragraph("ORBIT Philosophy", ParagraphStyle(
            "Credit", parent=body, fontName="OrbitBold", fontSize=9, textColor=ACCENT
        )),
        Spacer(1, 4 * mm),
        Paragraph("PDF PROTOTYPE · v0.2 · 2026-09-30", ParagraphStyle(
            "Edition", parent=body, fontSize=7.5, textColor=MUTED
        )),
        PageBreak(),
        heading("전체 구성", style_map["h1"], 0),
        Spacer(1, 5 * mm),
    ]

    parts = [
        ("1부. 완성처럼 보이는 첫 결과물", [
            "1. 완성처럼 보이는 첫 결과물",
            "2. 친절한 답이 목표를 잃게 할 때",
            "3. 같은 말을 해도 같은 뜻이 아니다",
        ]),
        ("2부. 대화를 판단의 과정으로 바꾸기", [
            "4. 대화 깔때기와 통역",
            "5. 다름을 지우지 않는 관계",
            "6. 판단권과 파트너의 책임",
            "7. 선택에는 이유가 따라야 한다",
        ]),
        ("3부. 다음 판단을 처음부터 시작하지 않기", [
            "8. 대화가 사라지면 관계도 처음으로 돌아간다",
            "9. 오해와 교정의 궤적을 남기는 법",
            "10. 완성하지 않고도 완결할 수 있는가",
        ]),
    ]
    for part, chapters in parts:
        block = [Paragraph(part, ParagraphStyle(
            "Part", parent=body, fontName="OrbitBold", fontSize=10.5, leading=16,
            textColor=ACCENT, keepWithNext=True, wordWrap="CJK"
        ))]
        block.extend(Paragraph(chapter, style_map["list"]) for chapter in chapters)
        block.append(Spacer(1, 5 * mm))
        story.append(KeepTogether(block))

    story.extend([
        PageBreak(),
        Image(str(assets / "chapter-01-first-output-v0.1.png"), width=112 * mm, height=74.67 * mm),
        Spacer(1, 4 * mm),
        Paragraph("완성되어 보이는 결과도 목표와 맞는지 다시 확인해야 한다.", ParagraphStyle(
            "Caption", parent=body, fontSize=7.8, leading=12, alignment=TA_CENTER,
            textColor=MUTED, wordWrap="CJK"
        )),
        Spacer(1, 8 * mm),
        Paragraph("이 판본에 대하여", ParagraphStyle(
            "PrefaceTitle", parent=body, fontName="OrbitBold", fontSize=15, leading=22,
            textColor=INK, wordWrap="CJK"
        )),
        Spacer(1, 3 * mm),
        Paragraph(
            "이 파일은 《첫 결과물이 곧 완성은 아니다》의 출간본이 아니다. 제목과 구성, 읽기 경험을 함께 검토하기 위한 PDF 시제품이다. 현재 3부 10장의 설계와 제1장 샘플을 담았다.",
            body,
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "이 책은 한 번에 좋은 프롬프트를 만드는 기술보다 첫 결과물 이후의 판단을 다룬다. 첫 응답이나 첫 MVP가 완성처럼 보여도, 인간과 LLM은 목표·경계·완료 조건을 서로 다르게 이해할 수 있다. 그 차이를 어떻게 확인하고 교정하며 다음 판단을 위해 무엇을 기록할지 묻는다.",
            body,
        ),
    ])
    story.extend(parse_markdown(
        repo_root / "tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md",
        style_map,
    ))

    output.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_pdf.py REPO_ROOT OUTPUT_PDF")
    build(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())


if __name__ == "__main__":
    main()
