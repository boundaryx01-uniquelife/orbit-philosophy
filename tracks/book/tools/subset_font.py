#!/usr/bin/env python3
"""Create static, text-specific Noto Sans KR fonts for the current prototypes."""

from __future__ import annotations

from pathlib import Path
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


EXTRA_TEXT = "첫 답은 끝이 아니다 인간과 LLM이 서로의 뜻을 맞춰 가는 대화의 기술 ORBIT PHILOSOPHY EPUB WEB PDF PROTOTYPE v0.1 0123456789"


def make_font(source: Path, output: Path, weight: int, text: str) -> None:
    font = TTFont(source)
    font = instantiateVariableFont(font, {"wght": weight}, inplace=True)

    options = subset.Options()
    options.layout_features = ["*"]
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6]
    options.name_legacy = True
    options.name_languages = [0x409, 0x412]
    options.notdef_glyph = True
    options.notdef_outline = True
    options.recommended_glyphs = True

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)

    family = "Noto Sans KR Book Subset"
    subfamily = "Bold" if weight >= 700 else "Regular"
    full_name = f"{family} {subfamily}"
    postscript_name = f"NotoSansKRBookSubset-{subfamily}"
    for platform_id, encoding_id, language_id in ((3, 1, 0x409), (3, 1, 0x412)):
        font["name"].setName(family, 1, platform_id, encoding_id, language_id)
        font["name"].setName(subfamily, 2, platform_id, encoding_id, language_id)
        font["name"].setName(full_name, 4, platform_id, encoding_id, language_id)
        font["name"].setName(postscript_name, 6, platform_id, encoding_id, language_id)
        font["name"].setName(family, 16, platform_id, encoding_id, language_id)
        font["name"].setName(subfamily, 17, platform_id, encoding_id, language_id)
    font["OS/2"].usWeightClass = weight
    if weight >= 700:
        font["head"].macStyle |= 1
    else:
        font["head"].macStyle &= ~1
    output.parent.mkdir(parents=True, exist_ok=True)
    font.save(output)


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit(
            "usage: subset_font.py SOURCE REGULAR_OUTPUT BOLD_OUTPUT TEXT_FILE..."
        )

    source = Path(sys.argv[1])
    regular = Path(sys.argv[2])
    bold = Path(sys.argv[3])
    text_paths = [Path(value) for value in sys.argv[4:]]
    text = EXTRA_TEXT + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in text_paths
    )

    make_font(source, regular, 400, text)
    make_font(source, bold, 700, text)


if __name__ == "__main__":
    main()
