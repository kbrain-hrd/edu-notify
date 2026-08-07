"""템플릿 전부에 값을 넣어 보고 이상이 없는지 확인한다.

    uv run python scripts/verify.py

보는 것은 넷이다 — 옛 값이 남았는가, 라벨이 살아 있는가, 새 값이 들어갔는가,
글자가 칸을 넘치는가. 특히 **옛 값 잔존**은 눈으로는 안 보이므로 반드시 기계가 봐야 한다.
길이가 가장 긴 값으로도 한 번 더 돌려 넘침을 확인한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber
from reportlab.pdfbase import pdfmetrics

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from edu_notify.fonts import register  # noqa: E402
from edu_notify.pdf import CELL_L, CELL_R, ROWS, Notice, build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
FONTS = ROOT / "fonts"
CACHE = ROOT / ".fontcache"
OUT = ROOT / "out" / "verify"

보통 = Notice(
    course="AI 챔피언 그린(초급) 종합과정 5회차",
    schedule="2026년 9월 7일 (월) ~ 9월 9일 (수) 09:00 ~ 18:00",
    place="Zoom 회의 ID : 123 4567 8901 / PW : green5",
    checklist_url="https://kbrain-ems.vercel.app/pretraining/TESTTOKEN",
)
긴값 = Notice(
    course="생성형 AI 활용 데이터분석 심화(중급) 종합과정 12회차",
    schedule="2026년 12월 22일 (월) ~ 12월 24일 (수) 09:00 ~ 18:00",
    place="Zoom 회의 ID : 888 8888 8888 / PW : greenblue2026",
    checklist_url="https://kbrain-ems.vercel.app/pretraining/TESTTOKEN",
)

# 템플릿에 남아 있으면 안 되는 지난 회차 값들
옛값_흔적 = ("5527", "4423", "8535", "0250", "3095", "2177", "1113", "4108",
             "vis7QrdI", "dteyPSlt", "JHHbogoB")


def check(template: Path, notice: Notice, tag: str, fonts: dict[str, str]) -> bool:
    dst = OUT / f"{tag}_{template.name}"
    try:
        build(template, dst, notice, fonts)
    except Exception as e:  # noqa: BLE001
        print(f"  ✗ {template.name[:40]:<40} 실패 {type(e).__name__}: {e}")
        return False

    with pdfplumber.open(dst) as pdf:
        text = pdf.pages[0].extract_text() or ""

    problems = []
    남은옛값 = [k for k in 옛값_흔적 if k in text]
    if 남은옛값:
        problems.append(f"옛 값 잔존 {남은옛값}")
    if not all(k in text for k in ("교육명", "일시", "장소", "수료기준")):
        problems.append("라벨 누락")
    for label, value in notice.as_rows().items():
        if value.split()[0] not in text:
            problems.append(f"{label} 누락")
        width = pdfmetrics.stringWidth(value, fonts[ROWS[label].weight], 11.04)
        if width > CELL_R - CELL_L:
            problems.append(f"{label} 넘침 {width:.0f}pt")

    mark = "✓" if not problems else "✗"
    print(f"  {mark} {template.name[:40]:<40}{'  ' + ' / '.join(problems) if problems else ''}")
    return not problems


def main() -> int:
    if not TEMPLATES.exists() or not any(TEMPLATES.glob("*.pdf")):
        print(f"템플릿이 없습니다: {TEMPLATES}\n안내서 PDF 를 넣고 다시 실행하세요.")
        return 1

    fonts = register(FONTS, CACHE)
    print(f"값 칸 폭 {CELL_R - CELL_L:.0f}pt")

    failed = 0
    for tag, notice in (("보통", 보통), ("긴값", 긴값)):
        print(f"\n━━━ {tag} ━━━")
        for template in sorted(TEMPLATES.glob("*.pdf")):
            failed += not check(template, notice, tag, fonts)

    print(f"\n{'모두 통과' if failed == 0 else f'{failed}건 실패'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
