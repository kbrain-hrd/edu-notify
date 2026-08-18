# edu-notify

교육 안내서(별첨2) PDF 에서 **회차마다 바뀌는 값 네 개만** 갈아끼우는 생성기. 교육명,
일시, 장소(Zoom 회의 ID·PW), 사전 체크리스트 링크를 넣으면 안내서가 나온다. 상단 배너와
로고, 로봇 일러스트, 표 테두리, 사전 준비 사항, 안내 사항, 문의처는 원본 그대로 남는다.
지금까지 회차마다 담당자가 PPT 를 열어 이 네 곳을 고치고 PDF 로 저장해 메일에 첨부하던
일을 대체하기 위해 만들었다. 교육 안내 메일 발송과 교육 당일 아침 문자 예약 발송은
뒤이어 붙인다.

## 설치

- Python 3.12 이상

```powershell
uv sync
```

## 준비 — 저장소에 없는 것

이 저장소는 **공개**다. 아래 두 폴더는 그래서 넣지 않았다(`.gitignore`). 직접 채워야 한다.

**`templates/`** — 안내서 PDF 원본. 운영 자료에서 복사해 넣는다.
안내서 하단 문의처에 **담당자 휴대전화 번호 두 개**가 있고, 표에는 지난 회차 **Zoom
비밀번호**가 있어 공개 저장소에 올릴 수 없다.

**`fonts/`** — `SCDream4.otf`, `SCDream5.otf`(에스코어 드림). [산돌](https://www.sandoll.co.kr)
에서 내려받아 넣는다. 배포 조건은 확인이 필요하다 — [docs/01](docs/01-안내서-pdf.md#글꼴) 참고.

## 사용법

```python
from pathlib import Path

from edu_notify import Notice, build
from edu_notify.fonts import register

fonts = register(Path("fonts"), Path(".fontcache"))

build(
    template=Path("templates/별첨2. AI 챔피언 그린 비대면 교육 사전 안내서.pdf"),
    dst=Path("out/안내서.pdf"),
    notice=Notice(
        course="AI 챔피언 그린(초급) 종합과정 5회차",
        schedule="2026년 9월 7일 (월) ~ 9월 9일 (수) 09:00 ~ 18:00",
        place="Zoom 회의 ID : 123 4567 8901 / PW : green5",
        checklist_url="https://kbrain-ems.vercel.app/pretraining/vis7QrdI",
    ),
    font_names=fonts,
)
```

`checklist_url` 은 회차마다 다르다. 그 설문을 발급하는 것이 EMS 자신이므로, EMS 안에서
호출할 때는 해당 회차 주소를 그대로 넘기면 된다.

`templates/` 의 모든 안내서에 값을 넣어 보고 이상이 없는지 확인하려면:

```powershell
uv run python scripts/verify.py
```

## 문서

| 문서 | 언제 읽나 |
|---|---|
| [docs/01-안내서-pdf.md](docs/01-안내서-pdf.md) | **PDF 생성 코드를 고치기 전.** 왜 PPT 를 안 거치는지, 값을 어떻게 찾는지, 눈에 안 보이는 함정 여섯 가지 |
| [docs/02-발송-계획.md](docs/02-발송-계획.md) | 메일·문자 발송을 붙이기 전. 타스온 API 규격, Cron 을 믿을 수 없는 지점, 발송 이력이 왜 필수인지 |
| [docs/03-확인-필요.md](docs/03-확인-필요.md) | 외부 답변에 달린 항목. **어디서 어떻게 확인하는지까지** 적혀 있다 |
| [docs/04-발송이력.md](docs/04-발송이력.md) | 발송 코드를 쓰기 전. 무엇을 기록하고 언제 건너뛰는지 — **중복 발송을 막는 유일한 장치** |

`docs/01` 의 [고치기 전에 읽을 것](docs/01-안내서-pdf.md#고치기-전에-읽을-것)은 장식이 아니다.
가장 위험한 항목은 눈으로 확인되지 않는다 — 옛 글자를 가리기만 하면 복사할 때 지난 회차
Zoom 비밀번호가 그대로 나온다.
