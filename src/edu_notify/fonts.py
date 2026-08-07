"""에스코어 드림을 PDF 생성기가 읽을 수 있는 형태로 바꾼다.

에스코어 드림은 `.otf` 로 배포된다. 안쪽 곡선이 3차 베지어(PostScript 방식)인데
reportlab 은 2차 베지어(TrueType 방식)만 읽는다. 그래서 한 번 변환해서 쓴다.

변환은 한 번만 하면 되므로 결과를 파일로 남겨 두고 다음부터 재사용한다.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

# 줄마다 굵기가 다르다. 원본 안내서와 잉크량을 맞춰 고른 값이다 (2026-08-07 실측).
#   교육명·일시 → 드림 5 Medium + 테두리 0.2   (원본과 차이 0.0087, 후보 7종 중 최소)
#   장소        → 드림 4 Regular, 테두리 없음   (원본과 차이 0.0008, 사실상 일치)
WEIGHT_FILES = {
    "굵게": "SCDream5.otf",
    "보통": "SCDream4.otf",
}
FONT_NAMES = {"굵게": "드림5", "보통": "드림4"}


def otf_to_ttf(src: Path, dst: Path, max_err: float = 1.0) -> Path:
    """OTF 의 3차 곡선을 2차로 근사해 TTF 로 저장한다. 이미 있으면 그대로 쓴다."""
    if dst.exists():
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)

    font = TTFont(str(src))
    glyph_set = font.getGlyphSet()
    glyphs = {}
    for name in font.getGlyphOrder():
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err, reverse_direction=True))
        glyphs[name] = pen.glyph()

    font["loca"] = newTable("loca")
    glyf = font["glyf"] = newTable("glyf")
    glyf.glyphOrder = font.getGlyphOrder()
    glyf.glyphs = glyphs
    del font["CFF "]

    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = maxp.maxTwilightPoints = maxp.maxStorage = 0
    maxp.maxFunctionDefs = maxp.maxInstructionDefs = maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = maxp.maxComponentElements = 0
    maxp.numGlyphs = len(glyphs)
    font["maxp"] = maxp
    glyf.compile(font)
    maxp.recalc(font)

    post = font["post"]
    post.formatType = 2.0
    post.extraNames, post.mapping = [], {}
    post.glyphOrder = font.getGlyphOrder()
    for tag in ("VORG", "CFF2"):
        if tag in font:
            del font[tag]

    font.sfntVersion = "\000\001\000\000"
    font.save(str(dst))
    return dst


def register(font_dir: Path, cache_dir: Path) -> dict[str, str]:
    """굵기별 글꼴을 reportlab 에 등록하고 {굵기: 등록이름} 을 돌려준다."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont as RLFont

    registered = pdfmetrics.getRegisteredFontNames()
    for weight, filename in WEIGHT_FILES.items():
        name = FONT_NAMES[weight]
        if name in registered:
            continue
        otf = font_dir / filename
        if not otf.exists():
            raise FileNotFoundError(
                f"글꼴이 없습니다: {otf}\n"
                "에스코어 드림을 내려받아 fonts/ 에 넣으세요 (README 참고)."
            )
        ttf = otf_to_ttf(otf, cache_dir / f"{otf.stem}.ttf")
        pdfmetrics.registerFont(RLFont(name, str(ttf)))
    return dict(FONT_NAMES)
