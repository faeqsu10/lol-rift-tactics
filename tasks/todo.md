# TODO

## 현재 작업

- [x] 웹 중심 방향에서 네이티브 `Pygame` 방향으로 전환
- [x] 한글 폰트 번들 추가로 폰트 깨짐 해결
- [x] 전장 배경, 패널, 캐릭터 실루엣, 스킬 연출 1차 비주얼 개편
- [x] 적 대상 스킬 타겟 선택 버그 수정
- [x] 실제 챔피언 아이콘을 전장 유닛과 패널에 적용
- [x] 기본 효과음과 앰비언트 오디오 추가
- [x] WSL 리눅스 런타임용 PulseAudio 라이브러리 번들 및 부트스트랩 추가
- [x] 전투 시작 전 챔피언 선택 화면 추가
- [x] 블루/레드 로스터 풀 확장 및 커스텀 라인업 전투 반영
- [x] 블루/레드 로스터를 7인 풀로 2차 확장하고 선택 카드 레이아웃 보정
- [x] 블루/레드 로스터를 9인 풀로 3차 확장
- [x] `PyInstaller` 기반 실행 파일 패키징 경로 추가 및 산출물 검증
- [x] GitHub Actions 기반 Windows `.exe` 빌드 경로 추가
- [x] 챔피언별 선택/시전 테마 사운드 추가
- [x] 기존 아레나 버전을 유지한 채 `native_tactics` 전술 실험 패키지 추가
- [x] 헤드리스 스크린샷으로 비주얼 결과 확인
- [x] `native_tactics` 재미 요소 우선순위 로드맵 정리
- [x] `native_tactics` 챔피언 선택 화면 추가
- [x] `native_tactics` 시작 배치 단계 추가
- [x] `native_tactics` 3전 원정 구조와 전투 후 보상 선택 루프 추가
- [x] `native_tactics` 다음 적 조합 미리보기 추가
- [x] `native_tactics` 챔피언별 고유 패시브 1차 추가
- [x] `native_tactics` 적 의도 표시 1차 추가
- [ ] `native_tactics` 지형 효과와 더 나은 AI 추가
- [ ] `native_tactics` 적 의도에 예상 피해와 위협 구역 예고 추가
- [ ] `native_tactics` 전투 후 요약과 분기 선택 추가
- [ ] 실제 스프라이트 기반 캐릭터 아트 도입 여부 결정
- [ ] 공격, 피격, 사망, 승리 전용 애니메이션 세분화
- [ ] 배경 맵 아트 추가

## 검증

- [x] `python3 -m py_compile native_game/app.py`
- [x] `npm run native:test`
- [x] `npm run native:smoke`
- [x] `--screenshot` 출력 확인
- [x] `npm run native:package`
- [x] `./release/rift-tactics --headless --frames 2 --screenshot ...`
- [x] `npm run tactics:test`
- [x] `npm run tactics:smoke`
- [x] `npm run tactics:capture`
- [x] `GameApp` 선택 -> 배치 -> 전투 상태 전환 검증
- [x] 보상 선택 -> 다음 전투 배치 상태 전환 검증
- [x] 챔피언 패시브 피해/보호막 회귀 테스트
- [x] 적 의도 미리보기 회귀 테스트

## 리뷰 메모

- 현재 목표는 "게임처럼 보이는가"를 우선 해결하는 것
- 도형 프로토타입 느낌을 줄이기 위해 캐릭터 실루엣과 전장 레이어를 먼저 강화함
- 스크린샷 캡처 커맨드는 `npm run native:capture`
- 전술 실험은 기존 아레나 버전 위에 덮어쓰지 말고 별도 패키지로 병행 유지
- `native_tactics`의 다음 재미 포인트는 챔피언 수 확장보다 선택, 배치, 지형, 의도 표시, 보상 루프 순으로 붙이는 것이 효율적
- `native_tactics`처럼 상태가 여러 단계로 나뉘는 화면은 단순 프레임-0 스모크만으로 끝내지 말고 상태 전환까지 직접 검증할 것
- 전술 게임의 중독성은 전투 자체뿐 아니라 전투 뒤 다음 목표 제시에서 크게 갈리므로, 승리 후 보상과 다음 적 프리뷰를 먼저 붙이는 것이 효과적
- 적 의도 표시는 단순 문구만이 아니라 전장 위 하이라이트까지 같이 보여 줘야 플레이어가 바로 이해한다
