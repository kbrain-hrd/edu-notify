"""안내서(별첨2) PDF 의 값 네 개를 갈아끼운다.

    옛 글자 지우기  →  새 글자 찍기  →  체크리스트 링크 교체

**PPT 를 거치지 않는다.** 기존 안내서 PDF 자체를 틀로 쓴다. PPT → PDF 변환에는
PowerPoint 가 필요한데 서버(리눅스)에서는 못 돌리기 때문이다. 배경 그림·로고·표 테두리·
나머지 글자는 원본 그대로 남고, 손대는 것은 표 안 세 줄과 링크뿐이다.

만들면서 실제로 걸렸던 것들 — 고치기 전에 읽어 둘 것:

1. **옛 글자를 가리기만 하면 안 된다.** 흰 사각형으로 덮어도 글자는 PDF 안에 남아서
   복사하거나 검색하면 지난 회차 Zoom 비밀번호가 그대로 나온다. 내용 스트림에서 지운다.
2. **값만 지워야 한다.** '교육명'·'일시'·'장소' 라벨이 값과 같은 줄에 있어, 줄 단위로
   지우면 라벨까지 사라진다. 가로 위치가 X_MIN 이상인 것만 지운다.
3. **라벨 기준으로 값을 찾으면 안 된다.** '일시' 칸만 두 줄이라 라벨이 가운데 정렬되어
   어느 값 줄과도 기준선이 맞지 않는다. 표 가로선으로 칸을 나눈 뒤 그 칸의 맨 윗 줄을 잡는다.
4. **기준선이 1.6pt 어긋난다.** pdfplumber 가 보고하는 y 와 내용 스트림의 y 가 다르다.
   지우고 찍을 때는 스트림에서 직접 찾은 값을 쓴다.
5. **장소 줄은 기준선이 갈려 있다.** Zoom ID 숫자가 2.85pt 아래에 찍혀 있어 다른 줄로
   분류된다. 맨 윗 기준선에서 5pt 안쪽은 같은 줄로 합친다.
6. **굵게를 줄마다 명시적으로 켜고 꺼야 한다.** 끄는 쪽을 생략하면 앞 줄 설정이 남아,
   굵게가 아닌 줄이 앞 줄 테두리색(빨강)으로 물든다.
"""

from __future__ import annotations

import io
from collections import Counter
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, TextStringObject
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

NAVY = Color(0, 0.125, 0.376)
WHITE = Color(1, 1, 1)
RED = Color(1, 0, 0)
GREY = Color(0.2, 0.2, 0.2)

# 표에서 값이 들어가는 칸의 좌우 경계. X_MIN 왼쪽은 라벨이라 건드리지 않는다.
CELL_L, CELL_R, X_MIN = 114.0, 497.0, 114.0
LINE_TOL = 1.2      # 같은 줄로 볼 기준선 차이
MERGE_TOL = 5.0     # 한 줄 안에서 기준선이 갈린 구간을 합칠 범위
STRIP_TOL = 1.5     # 지울 글자를 고를 때의 기준선 허용 오차
BOLD_STROKE = 0.2   # 가짜 굵게 — 글자에 덧그리는 테두리 두께


@dataclass(frozen=True)
class Row:
    align: str      # "center" | "left"
    color: Color
    background: Color
    weight: str     # "굵게" | "보통"


# 굵게 여부는 PPT 원본을 따른다 — 교육명·일시는 굵게, 장소는 굵게가 아니다.
ROWS: dict[str, Row] = {
    "교육명": Row("center", WHITE, NAVY, "굵게"),
    "일시": Row("left", RED, WHITE, "굵게"),
    "장소": Row("left", GREY, WHITE, "보통"),
}


@dataclass
class Notice:
    """안내서에 들어갈 값. EMS 발송 화면에서 받는 것들이다."""

    course: str          # 교육명
    schedule: str        # 일시
    place: str           # 장소 (Zoom 회의 ID / PW)
    checklist_url: str   # 체크리스트 설문 주소 (회차마다 다름)

    def as_rows(self) -> dict[str, str]:
        return {"교육명": self.course, "일시": self.schedule, "장소": self.place}


# ── 원본에서 자리 읽기 ────────────────────────────────────────────────
def _group_lines(chars) -> list[list]:
    lines: list[list] = []
    for ch in sorted(chars, key=lambda c: (-c["y0"], c["x0"])):
        for line in lines:
            if abs(line[0]["y0"] - ch["y0"]) <= LINE_TOL:
                line.append(ch)
                break
        else:
            lines.append([ch])
    for line in lines:
        line.sort(key=lambda c: c["x0"])
    return lines


def read_rows(template: Path) -> dict[str, dict]:
    """표의 각 칸에서 바꿀 줄의 자리·크기·기준선을 읽는다."""
    with pdfplumber.open(template) as pdf:
        page = pdf.pages[0]
        height = page.height
        edges = sorted(
            {round(height - ln["top"], 1) for ln in page.lines if ln["width"] > 200},
            reverse=True,
        )
        lines = _group_lines(page.chars)

    bands = [(edges[i], edges[i + 1]) for i in range(len(edges) - 1)]
    found: dict[str, dict] = {}

    for label in ROWS:
        band = None
        for line in lines:
            left = "".join(c["text"] for c in line if c["x0"] < X_MIN).replace(" ", "")
            if label in left:
                band = next((b for b in bands if b[1] <= line[0]["y0"] < b[0]), None)
                break
        if band is None:
            continue

        in_band = [
            ln for ln in lines
            if any(c["x0"] >= X_MIN for c in ln) and band[1] <= ln[0]["y0"] < band[0]
        ]
        if not in_band:
            continue

        top_baseline = max(ln[0]["y0"] for ln in in_band)
        values = sorted(
            (c for ln in in_band for c in ln
             if c["x0"] >= X_MIN and abs(c["y0"] - top_baseline) <= MERGE_TOL),
            key=lambda c: c["x0"],
        )
        segments = [
            {"size": size, "baseline": base}
            for (size, base), _ in groupby(
                values, key=lambda c: (round(c["size"], 2), round(c["y0"], 2))
            )
        ]
        size, baseline = Counter(
            (s["size"], s["baseline"]) for s in segments
        ).most_common(1)[0][0]

        found[label] = {
            "x0": min(c["x0"] for c in values),
            "top": min(c["top"] for c in values),
            "bottom": max(c["bottom"] for c in values),
            "size": size,
            "baseline": baseline,
            "segments": segments,
            "page_height": height,
        }
    return found


def _stream_baselines(content: ContentStream, expected: list[float]) -> list[float]:
    """내용 스트림에서 실제로 쓰인 기준선을 찾는다 (pdfplumber 값과 1.6pt 어긋난다)."""
    seen: set[float] = set()
    x = y = None
    for operands, op in content.operations:
        if op == b"Tm":
            x, y = float(operands[4]), float(operands[5])
        elif op in (b"Td", b"TD"):
            x, y = (x or 0) + float(operands[0]), (y or 0) + float(operands[1])
        if op in (b"Tj", b"TJ") and y is not None and (x or 0) >= X_MIN:
            if any(abs(y - e) <= 3.0 for e in expected):
                seen.add(round(y, 2))
    return sorted(seen)


def _strip(content: ContentStream, baselines: list[float]) -> int:
    """값 칸의 옛 글자를 그리는 명령만 뺀다. 라벨과 배경은 남긴다."""
    kept, dropped = [], 0
    x = y = None
    for operands, op in content.operations:
        if op == b"Tm":
            x, y = float(operands[4]), float(operands[5])
        elif op in (b"Td", b"TD"):
            x, y = (x or 0) + float(operands[0]), (y or 0) + float(operands[1])
        if op in (b"Tj", b"TJ", b"'", b'"') and y is not None:
            on_target = any(abs(y - b) <= STRIP_TOL for b in baselines)
            if on_target and (x or 0) >= X_MIN:
                dropped += 1
                continue
        kept.append((operands, op))
    content.operations = kept
    return dropped


def build(template: Path, dst: Path, notice: Notice, font_names: dict[str, str]) -> None:
    """template 을 틀로 삼아 notice 의 값을 넣은 PDF 를 dst 에 쓴다."""
    rows = read_rows(template)
    missing = [k for k in ROWS if k not in rows]
    if missing:
        raise LookupError(f"표에서 찾지 못한 줄: {missing}")

    reader = PdfReader(str(template))
    page = reader.pages[0]
    content = ContentStream(page.get_contents(), reader)

    expected = [s["baseline"] for r in rows.values() for s in r["segments"]]
    baselines = _stream_baselines(content, expected)
    _strip(content, baselines)
    page[NameObject("/Contents")] = content

    height = rows["교육명"]["page_height"]
    values = notice.as_rows()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page.mediabox.width, height))

    for label, row in ROWS.items():
        spot = rows[label]
        font = font_names[row.weight]
        text = values[label]

        # 옛 글자가 있던 자리를 그 칸의 배경색으로 덮는다. '일시' 칸은 아래에
        # '환경 점검' 줄이 붙어 있어 아래쪽 여백을 좁게 잡는다.
        bottom_pad = 0.6 if label == "일시" else 2.2
        top = height - spot["top"] + 2.2
        bottom = height - spot["bottom"] - bottom_pad
        c.setFillColor(row.background)
        c.rect(CELL_L, bottom, CELL_R - CELL_L, top - bottom, stroke=0, fill=1)

        width = pdfmetrics.stringWidth(text, font, spot["size"])
        left = (CELL_L + CELL_R - width) / 2 if row.align == "center" else spot["x0"]
        baseline = min(baselines, key=lambda b: abs(b - spot["baseline"]))

        c.setLineWidth(BOLD_STROKE)
        text_obj = c.beginText(left, baseline)
        text_obj.setFont(font, spot["size"])
        text_obj.setFillColor(row.color)
        text_obj.setStrokeColor(row.color)
        text_obj.setTextRenderMode(2 if row.weight == "굵게" else 0)
        text_obj.textOut(text)
        c.drawText(text_obj)

    c.save()
    buf.seek(0)
    page.merge_page(PdfReader(buf).pages[0])

    for ref in page.get("/Annots") or []:
        action = ref.get_object().get("/A")
        if action and "kbrain-ems" in str(action.get("/URI", "")):
            action[NameObject("/URI")] = TextStringObject(notice.checklist_url)

    dst.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_page(page)
    with dst.open("wb") as f:
        writer.write(f)
