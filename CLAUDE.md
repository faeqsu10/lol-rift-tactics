# CLAUDE.md

This file provides guidance for working in this repository.

## Project Overview

`League of Legends: Rift Tactics`

- League of Legends fan-made turn-based combat prototype
- Current primary build: native `Pygame` client
- Current active native tracks:
  - `native_game`: 9인 풀에서 3인 선택 -> 3v3 battle
  - `native_tactics`: 3인 선택 -> 시작 배치 -> 3전 원정 -> 보상 -> 전투 요약 -> 3안 경로 선택 + 전투 이벤트 -> 패시브/적 의도/연속 턴 예고/지형/엘리트전/맵 목표/목표 경쟁 AI/실패 페널티
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
