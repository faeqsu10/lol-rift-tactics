# CLAUDE.md

This file provides guidance for working in this repository.

## Project Overview

`League of Legends: Rift Tactics`

- League of Legends fan-made turn-based combat prototype
- Current primary build: native `Pygame` client
- Current active native tracks:
  - `native_game`: 9인 풀에서 3인 선택 -> 3v3 battle
  - `native_tactics`: 3인 선택 -> 시작 배치 -> 3전 원정 -> 보상 -> 전투 요약 -> 3안 경로+런 노드 선택 + 전투 이벤트 + 노드 후속 이벤트 -> 패시브 2차/챔피언별 특수기/적 의도 4차/연속 턴 예고/지형/엘리트 특성/보스 결전/보스 전용 목표/보스 패턴 2종/결전 전용 지형 변주/보스 각성 추가 규칙/결전 위험 타일 예고/저장 기록 기반 원정 교리/경로 재추첨/맵 목표/목표 경쟁 AI/실패 페널티/휴식·변수·정예 노드 분기/전투 시작 컷인 -> 런 종료 결산/저장 기록 비교/즉시 새 원정
- Current secondary build: legacy web prototype under `src/*`

## Commands

- 의존성 설치: `npm install`
- 네이티브 환경 준비: `npm run native:setup`
- 네이티브 실행: `npm run native:play`
- 네이티브 패키징: `npm run native:package`
- 윈도우 빌드 스크립트: `scripts/build-windows.ps1`
- 네이티브 테스트: `npm run native:test`
- 네이티브 스모크: `npm run native:smoke`
- 전술 실험 실행: `npm run tactics:play`
- 전술 실험 테스트: `npm run tactics:test`
- 전술 실험 스모크: `npm run tactics:smoke`
- 전술 실험 캡처: `npm run tactics:capture`
- 웹 개발 서버: `npm run dev`
- 웹 테스트: `npm test`

## Architecture

```text
native_game/
├── app.py          # Pygame 렌더링, 입력, 연출
├── audio.py        # 절차형 효과음과 앰비언트 오디오
├── combat.py       # 턴제 전투 상태와 해석
├── data.py         # 챔피언/스킬 정의
├── runtime.py      # 번들/일반 실행 공통 리소스 경로
├── tests.py        # 전투 규칙 테스트
└── __main__.py     # 런타임 부트스트랩과 실행 진입점

native_tactics/
├── app.py          # 그리드 전술 UI와 입력
├── data.py         # 전술용 이동력, 사거리, 맵 설정
├── engine.py       # 이동/행동 턴제 전술 상태 해석
├── history.py      # 런 기록 저장과 최고 기록 비교
├── tests.py        # 전술 규칙 테스트
└── __main__.py     # 전술 빌드 실행 진입점

src/
├── App.tsx
├── components/
└── phaser/
```

## Working Rules

### Simplicity First

- 먼저 실제 플레이 감각을 개선하는 최소 변경부터 적용
- 전투 로직보다 사용자 체감이 나쁜 영역을 우선 수정

### Documentation Sync

- 기능 방향이 바뀌면 함께 업데이트:
  - `README.md`
  - `PROJECT_CONTEXT.md`
  - `CLAUDE.md`
  - `docs/DEVLOG.md`
  - `tasks/todo.md`
  - `tasks/lessons.md`

### Task Management

- 새 작업은 `tasks/todo.md`에 체크박스로 추가
- 사용자 교정이나 반복 실수 방지 규칙은 `tasks/lessons.md`에 추가
- 완료 후 검증 결과를 `tasks/todo.md`에 반영

### Verification Before Done

- 렌더링 변경 후:
  - `python3 -m py_compile native_game/app.py`
  - `npm run native:test`
  - `npm run native:smoke`
- 필요하면 `--screenshot`으로 결과 캡처
- 상태가 여러 단계인 흐름은 화면 진입뿐 아니라 실제 상태 전환까지 별도 검증
- 앱 상태와 엔진 상태를 둘 다 쓰는 규칙은 동기화 헬퍼와 회귀 테스트를 함께 둘 것
- 전술 리텐션 관련 근거는 `docs/TACTICS_UX_RESEARCH.md`에 함께 업데이트
- 출시 목표 변화가 생기면 `docs/TACTICS_RELEASE_TARGET.md`와 `docs/TACTICS_MILESTONES.md`를 먼저 갱신
- 챔피언별 스킬 선택 규칙을 건드리면 `tactics:test`, `tactics:smoke`, `tactics:capture`를 항상 같이 다시 돌릴 것
- 보스/엘리트 스테이지 규칙을 바꾸면 배치 화면과 전투 화면 둘 다 캡처해서 표식과 텍스트 밀도를 같이 확인할 것
- 적 의도 패널 줄 수를 늘릴 때는 전장 포커스 표식과 함께 캡처해, 텍스트만 늘어난 게 아니라 실제 대응 포인트가 보이는지 확인할 것
- 경로/노드/이벤트처럼 프리뷰와 실전이 함께 있는 시스템은 선택 화면 문구와 실제 전투 적용 수치가 같은 계산을 쓰는지 테스트로 고정할 것
- 경로 카드에 노드 후속 이벤트처럼 추가 정보를 붙이면 카드와 좌측 상세 프리뷰를 함께 캡처해 텍스트 밀도와 버튼 겹침을 같이 확인할 것
- 최종전 규칙을 따로 추가하면 경로 화면, 배치 화면, 전투 HUD가 모두 같은 결전 목표를 보여 주는지 확인할 것
- 런 종료 UX를 건드리면 `최종 승리`, `패배`, `결산 -> 새 원정`, `결산 -> 선택 화면` 네 상태 전환을 같이 검증할 것
- 보스 패턴이나 결전 지형을 바꾸면 `tactics:test`, `tactics:smoke`, `tactics:capture`를 돌리고, 보스 패턴/지형/목표가 프리뷰와 전투 패널 양쪽에 같이 노출되는지 확인할 것
- 보스 각성에 즉시 추가 피해를 붙이면 스킬 본타 `impacts`와 분리해, 챔피언 패시브의 처치/다중 타겟 판정이 오염되지 않는지 테스트로 고정할 것
- 메타 진행을 붙이면 `선택 화면 해금 표시`, `런 시작 적용`, `경로/배치 프리뷰`, `결산 화면 해금 문구`가 같은 이름과 같은 효과를 보여 주는지 함께 검증할 것
- 파일 저장이 들어가는 기능은 `headless` 테스트에서 기본 저장을 끄고, 필요할 때만 임시 경로를 주입해 검증할 것
- 전투 시작 컷인을 추가하면 레드 선턴 조합에서 AI가 먼저 움직이지 않도록, 컷인 타이머 동안 입력과 AI를 함께 멈추는지 확인할 것

### Frequent Commits

- 의미 있는 작업 단위마다 바로 커밋
- 사용자가 요청했으므로 수시로 푸시까지 진행

## Commit Convention

```text
<type>(<scope>): <한국어 설명>
```

Examples:

- `feat(frontend): 네이티브 전장 비주얼 개편`
- `docs(config): 작업 루틴 문서 추가`
