# edu-notify

교육 안내 메일·문자 발송 자동화.

지금 들어 있는 것은 **안내서(별첨2) PDF 생성**뿐입니다. 메일·문자 발송은 뒤이어 붙입니다.

## 무엇을 하는가

회차마다 사람이 PPT 를 열어 고치고 PDF 로 저장하던 일을, 값 네 개만 넣으면 끝나게 합니다.

```
교육명 · 일시 · 장소(Zoom ID/PW) · 체크리스트 링크
                    ↓
              안내서 PDF 완성
```

배경 그림, 로고, 표 테두리, 사전준비사항, 안내사항 — 나머지는 원본 그대로입니다.

## 왜 PPT 를 안 거치는가

PPT → PDF 변환에는 PowerPoint 가 필요한데 서버(리눅스)에서는 못 돌립니다.
그래서 **기존 안내서 PDF 자체를 틀로 씁니다.** 바뀌는 세 줄만 지우고 다시 찍고,
체크리스트 링크 주소를 갈아끼웁니다.

레이아웃이 틀어질 여지가 없다는 것이 이 방식의 장점입니다.

## 쓰기

```python
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

전체 템플릿을 한 번에 확인하려면:

```bash
uv sync
uv run python scripts/verify.py
```

## 저장소에 없는 것 — 따로 준비해야 합니다

이 저장소는 **공개**입니다. 아래 둘은 그래서 넣지 않았습니다.

**`templates/`** — 안내서 PDF 원본. 담당자 휴대전화 번호와 지난 회차 Zoom 비밀번호가
들어 있어 공개 저장소에 올릴 수 없습니다. 운영 자료에서 복사해 넣으세요.

**`fonts/`** — `SCDream4.otf`, `SCDream5.otf` (에스코어 드림).
[산돌](https://www.sandoll.co.kr) 에서 내려받아 넣으세요.
> 배포 조건을 확인해야 합니다. 무료 사용·재배포는 허용되지만 (1) 이 코드가 OTF 를
> TTF 로 변환해 쓰고 (2) 만들어진 PDF 에 글꼴이 부분 임베드됩니다.
> 실제 운영 배포 전에 배포처에 확인이 필요합니다.

## 글꼴

원본 안내서와 잉크량을 맞춰 굵기를 정했습니다 (2026-08-07 실측).

| 줄 | 글꼴 | 원본과 차이 |
|---|---|---|
| 교육명 · 일시 | 에스코어 드림 5 Medium + 테두리 0.2 | 0.0087 |
| 장소 | 에스코어 드림 4 Regular | 0.0008 |

`장소` 가 굵지 않은 것은 PPT 원본을 따른 것입니다.

## 확인된 범위

회차 템플릿 10종 × (평범한 값 / 가장 긴 값) = **20건 통과**.
과정명 형태가 제각각인 파일(`①②⑤⑦` 붙은 것, 하루짜리, 사흘짜리, `Zoom`/`ZOOM` 혼용)에서도
동작합니다. 가장 긴 값으로도 칸을 넘치지 않습니다 (최대 340pt / 칸 383pt).

## 만들면서 걸렸던 것들

`src/edu_notify/pdf.py` 맨 위 주석에 여섯 가지를 적어 두었습니다.
고치기 전에 반드시 읽으세요. 특히 첫 번째는 눈으로 확인되지 않는 종류의 문제입니다 —
**옛 글자를 가리기만 하면 복사할 때 지난 회차 Zoom 비밀번호가 그대로 나옵니다.**
