# native_tactics/app.py 렌더링 시스템 기술 지도

**분석 대상**: `/home/faeqsu10/projects/lol-rift-tactics/native_tactics/app.py` (5953줄)
**마지막 업데이트**: 2026-03-12

---

## 1. 모든 _draw_* 메서드 지도

### 1.1 주요 진입점 (_draw 메인 루프)

| 메서드명 | 라인 | 설명 | 호출 조건 |
|---------|------|------|----------|
| `_draw()` | 2966-2988 | 메인 렌더링 루프 - 모든 화면 모드 분기 | 매 프레임 실행 |
| `_draw_flow_breadcrumb()` | 2990-3020 | 현재 진행도 표시 (선택→배치→전투→보상→경로→결산) | `screen_mode` != "battle", "summary" |
| `_draw_finale_banner()` | 5514-5532 | 최종전 도입 텍스트 배너 | 최종전 대사 타이머 활성 |
| `_draw_battle_intro()` | 5533-5564 | 전투 시작 컷인 모션 오버레이 | `battle_intro_card` is not None |
| `_draw_help_overlay()` | 5628-5670 | 우측 하단 도움말 카드 | `help_overlay_visible` = True |
| `_draw_settings_overlay()` | 5671-5746 | 설정 오버레이 (음량, 난이도, 속도) | `settings_overlay_visible` = True |
| `_draw_winner_overlay()` | 5747-5830 | 전투 결과 승리/패배 화면 | 전투 종료 시 |

### 1.2 화면 모드별 주요 메서드

#### 선택 화면 (screen_mode = "select")

| 메서드명 | 라인 | 설명 | 부모 | 자식 |
|---------|------|------|------|------|
| `_draw_selection_screen()` | 3236-3249 | 선택 화면 전체 구성 | _draw | _draw_header, _draw_panel, _draw_selection_summary_strip, _draw_selection_focus_panel, _draw_selection_slots, _draw_selection_doctrine_panel, _draw_selection_pool, _draw_selection_enemy_preview |
| `_draw_selection_focus_panel()` | 3118-3198 | 선택된 챔피언 상세 정보 패널 | _draw_selection_screen | _draw_champion_card, _draw_portrait_art, _draw_info_chip, _draw_message_strip |
| `_draw_selection_summary_strip()` | 3199-3235 | 선택 라인업 요약 스트립 | _draw_selection_screen | (직접 렌더링) |
| `_draw_selection_slots()` | 3251-3269 | 출전 라인업 3개 슬롯 | _draw_selection_screen | _draw_champion_card, _draw_text |
| `_draw_selection_pool()` | 3271-3299 | 후보 로스터 그리드 (3-4개 열) | _draw_selection_screen | _draw_champion_card, _draw_message_strip |
| `_draw_selection_doctrine_panel()` | 3301-3326 | 원정 교리 선택 패널 | _draw_selection_screen | (직접 렌더링) |
| `_draw_selection_enemy_preview()` | 3349-3389 | 적군 조합 미리보기 | _draw_selection_screen | _draw_enemy_preview_pill |
| `_draw_enemy_preview_pill()` | 3328-3348 | 적 개별 챔피언 카드 | _draw_selection_enemy_preview | _draw_portrait_art, _draw_text |

#### 배치 화면 (screen_mode = "deploy")

| 메서드명 | 라인 | 설명 | 부모 | 자식 |
|---------|------|------|------|------|
| `_draw_deploy_screen()` | 3815-3823 | 배치 화면 전체 구성 | _draw | _draw_header, _draw_deploy_grid, _draw_deploy_left_panel, _draw_deploy_right_panel, _draw_deploy_bottom_panel |
| `_draw_deploy_grid()` | 3937-3969 | 8x6 그리드 배치 영역 | _draw_deploy_screen | _draw_grid_backdrop, _draw_grid_tile_base, _draw_blocked_tile_art, _draw_static_unit, _draw_terrain_tile |
| `_draw_deploy_left_panel()` | 3970-4000 | 배치 좌측 패널 (아군 선택 영역) | _draw_deploy_screen | _draw_panel, _draw_champion_card |
| `_draw_deploy_right_panel()` | 4001-4028 | 배치 우측 패널 (보스/엘리트 정보) | _draw_deploy_screen | _draw_panel, _draw_text |
| `_draw_deploy_bottom_panel()` | 4029-4065 | 배치 하단 패널 (경로 목표 표시) | _draw_deploy_screen | _draw_panel, _draw_text |

#### 전투 화면 (screen_mode = "battle")

| 메서드명 | 라인 | 설명 | 부모 | 자식 |
|---------|------|------|------|------|
| `_draw_battle_screen()` | 4066-4078 | 전투 화면 전체 구성 | _draw | _draw_header, _draw_panel, _draw_battle_grid, _draw_battle_left_panel, _draw_battle_right_panel, _draw_battle_bottom_panel, _draw_battle_action_banner, _draw_floaters, _draw_winner_overlay |
| `_draw_battle_grid()` | 4080-4209 | 8x6 전술 전투 그리드 + UI 오버레이 | _draw_battle_screen | _draw_grid_backdrop, _draw_grid_tile_base, _draw_terrain_tile, _draw_blocked_tile_art, _draw_battle_unit, _draw_battle_atmosphere, _draw_battle_rings, _draw_battle_trails |
| `_draw_grid_backdrop()` | 3825-3884 | 그리드 배경 (테마별 무늬) | _draw_battle_grid, _draw_deploy_grid | (직접 Pygame 드로우) |
| `_draw_grid_tile_base()` | 3885-3899 | 개별 타일 기본 렌더링 (어둡기 바리에이션) | _draw_battle_grid, _draw_deploy_grid | (직접 Pygame 드로우) |
| `_draw_terrain_tile()` | 4841-4916 | 지형 타일 (풀, 룬, 화염) 표현 | _draw_battle_grid, _draw_deploy_grid | (직접 Pygame 드로우) |
| `_draw_blocked_tile_art()` | 3900-3936 | 막힌 타일 일러스트 (테마별) | _draw_battle_grid, _draw_deploy_grid | (직접 Pygame 드로우) |
| `_draw_battle_atmosphere()` | 4210-4225 | 전장 배경 입자/먼지 효과 | _draw_battle_grid | (직접 Pygame 드로우) |
| `_draw_battle_rings()` | 4226-4234 | 해킹 링 효과 (라운드 표시) | _draw_battle_grid | (직접 Pygame 드로우) |
| `_draw_battle_trails()` | 4235-4280 | 유닛 이동 궤적 파티클 | _draw_battle_grid | _draw_hit_spark (간접) |
| `_draw_battle_unit()` | 4340-4495 | 개별 유닛 렌더링 (스탠드/HP/상태) | _draw_battle_grid | _draw_tactical_standee, _draw_tactical_body_layer, _draw_tactical_accessory |
| `_draw_battle_left_panel()` | 4496-4613 | 전투 좌측 패널 (아군 정보) | _draw_battle_screen | _draw_panel, _draw_roster_row |
| `_draw_roster_row()` | 4667-4702 | 좌측 패널 개별 유닛 행 | _draw_battle_left_panel | _draw_text |
| `_draw_battle_right_panel()` | 4614-4666 | 전투 우측 패널 (적군 정보) | _draw_battle_screen | _draw_panel, _draw_roster_row |
| `_draw_battle_bottom_panel()` | 4703-4778 | 전투 하단 패널 (행동 선택 버튼) | _draw_battle_screen | _draw_panel, _draw_text |
| `_draw_battle_action_banner()` | 4322-4339 | 현재 활성 유닛 행동 배너 | _draw_battle_screen | _draw_text |
| `_draw_floaters()` | 5503-5513 | 떠다니는 텍스트 (데미지, 힐 수치) | _draw_battle_screen | (직접 Pygame 드로우) |

#### 유닛 렌더링 (스탠드 도표 시스템)

| 메서드명 | 라인 | 설명 | 부모 | 자식 |
|---------|------|------|------|------|
| `_draw_static_unit()` | 4917-4944 | 배치 화면 정적 유닛 표현 | _draw_deploy_grid | _draw_tactical_standee |
| `_draw_tactical_standee()` | 4945-5169 | 동적 스탠드 렌더링 (몸통, 팔, 다리) | _draw_battle_unit, _draw_static_unit | _draw_tactical_body_layer, _draw_tactical_accessory |
| `_draw_tactical_body_layer()` | 5170-5299 | 스탠드 신체 레이어 (색상, 자세, 애니메이션) | _draw_tactical_standee | (직접 Pygame 드로우) |
| `_draw_tactical_accessory()` | 5300-5490 | 스탠드 액세서리 (무기, 盾, 오브) | _draw_tactical_standee | (직접 Pygame 드로우) |

#### 보상/경로/결산 화면

| 메서드명 | 라인 | 설명 | 부모 | 자식 |
|---------|------|------|------|------|
| `_draw_reward_screen()` | 3391-3467 | 보상 선택 화면 | _draw | _draw_header, _draw_panel, _draw_battle_card, _draw_text |
| `_draw_route_screen()` | 3468-3688 | 경로 선택 3개 옵션 + 노드 미리보기 | _draw | _draw_header, _draw_panel, _draw_battle_card, _draw_text, _draw_champion_card |
| `_draw_summary_screen()` | 3689-3814 | 전투 결산 화면 (전투 통계 + 다음 단계) | _draw | _draw_header, _draw_panel, _draw_text |

### 1.3 기본 UI 컴포넌트 (재사용 가능)

| 메서드명 | 라인 | 설명 | 호출 빈도 |
|---------|------|------|----------|
| `_draw_header()` | 3022-3059 | 헤더 (제목, 부제, 중앙 상태, 액션) | 매 화면 모드 1회 |
| `_draw_panel()` | 3061-3067 | 패널 (그래디언트 배경 + 테두리) | 매 화면 모드 여러 회 |
| `_draw_battle_card()` | 3099-3117 | 카드 (보상/경로 옵션 표현) | 보상/경로 화면 |
| `_draw_message_strip()` | 3068-3075 | 메시지 스트립 (상태 텍스트) | 선택 화면 |
| `_draw_info_chip()` | 3076-3098 | 정보 칩 (값, 레이블 조합) | 선택 포커스 패널 |
| `_draw_champion_card()` | 4779-4840 | 챔피언 카드 (초상화, 역할, 이름) | 선택, 배치, 경로 화면 |
| `_draw_portrait_art()` | 5491-5502 | 초상화 일러스트 + 액센트 테두리 | _draw_champion_card |

### 1.4 특수 효과 렌더링

| 메서드명 | 라인 | 설명 | 트리거 |
|---------|------|------|---------|
| `_draw_hit_spark()` | 4281-4302 | 타격 스파크 파티클 | 유닛 피해 시 |
| `_draw_victory_shards()` | 4303-4321 | 승리 샤드 파티클 | 유닛 처치 시 |
| `_draw_battle_intro_motif()` | 5565-5627 | 전투 시작 컷인 모션 (3단계) | battle_intro_card 진행 |

### 1.5 텍스트 렌더링 유틸

| 메서드명 | 라인 | 설명 |
|---------|------|------|
| `_draw_text()` | 5847-5865 | 단일 라인 텍스트 + 정렬(중앙, 우측) |
| `_draw_text_fit()` | 5832-5846 | 폰트 크기 자동 조정 텍스트 (fallback 지원) |
| `_draw_wrapped_text()` | 5866-5878 | 여러 라인 텍스트 (max_lines) |
| `_draw_wrapped_text_fit()` | 5879-5900 | 폰트 조정 + 줄바꿈 (폰트 fallback 3단계) |
| `_ellipsize_text()` | 5901-5910 | 텍스트 말줄임표 추가 |

---

## 2. 레이아웃 상수

### 2.1 윈도우 및 그리드 레이아웃

```python
# 윈도우
WINDOW_WIDTH = 1600     # 라인 40
WINDOW_HEIGHT = 960     # 라인 41

# 그리드
GRID_CELL = 100         # 라인 42 - 타일 크기
GRID_ORIGIN = pygame.Vector2(360, 130)  # 라인 43 - 좌상단 시작점
GRID_RECT = pygame.Rect(360, 130, GRID_WIDTH*100, GRID_HEIGHT*100)  # 라인 44
# 계산: 8x6 그리드 = 800x600 픽셀 영역

# 패널 영역
LEFT_PANEL = pygame.Rect(36, 120, 284, 694)      # 라인 45 - 좌측 스크린 영역
RIGHT_PANEL = pygame.Rect(1180, 120, 384, 694)   # 라인 46 - 우측 스크린 영역
BOTTOM_PANEL = pygame.Rect(36, 832, 1528, 92)    # 라인 47 - 하단 패널
HEADER_RECT = pygame.Rect(36, 28, 1528, 72)      # 라인 48 - 헤더 영역

# 선택 화면 전용
SELECT_LEFT_PANEL = pygame.Rect(36, 120, 920, 784)    # 라인 49 - 좌측 챔피언 선택
SELECT_RIGHT_PANEL = pygame.Rect(982, 120, 582, 784)  # 라인 50 - 우측 적군/교리
```

### 2.2 계산된 여백값 (주요 사용처)

| 값 | 사용 위치 | 목적 |
|----|---------|------|
| 16-24 | 패널 내부 마진 | 텍스트, 카드 여백 |
| 10-14 | 칩/작은 요소 여백 | 버튼, 배지 간격 |
| 12-18 | 카드 그리드 간격 | 챔피언 카드, 선택지 배열 |
| 22-34 | 타일 인플레이트 | 타일 하이라이트 안쪽 여백 |

---

## 3. 폰트 시스템

### 3.1 폰트 정의

```python
# __init__ (라인 756-774)
self.font_micro = load_font(12)           # 라인 769 - 매우 작은 텍스트 (1px 차이)
self.font_tiny = load_font(13)            # 라인 768 - 매우 작은 텍스트 (1px 차이)
self.font_small = load_font(16)           # 라인 770 - 작은 텍스트 (설명, 부제)
self.font_ui = load_font(20)              # 라인 771 - 기본 UI 텍스트
self.font_heading = load_font(26, bold=True)  # 라인 772 - 섹션 제목
self.font_large = load_font(34, bold=True)    # 라인 773 - 페이지 제목
self.font_title = load_font(42, bold=True)    # 라인 774 - 메인 제목
```

### 3.2 폰트 크기 사용 통계

| 크기 | 용도 | 사용 빈도 | 주요 메서드 |
|------|------|---------|-----------|
| 12-13 (micro/tiny) | 통계, 수치, 작은 레이블 | 78회+ | _draw_wrapped_text_fit, _draw_text_fit (fallback) |
| 16 (small) | 설명, 부제, 일반 라벨 | 40회+ | _draw_selection_screen, _draw_route_screen |
| 20 (ui) | 기본 UI 텍스트, 버튼 | 30회+ | _draw_selection_slots |
| 26 (heading) | 섹션 제목 | 15회+ | _draw_selection_screen, _draw_battle_screen |
| 34-42 (large/title) | 페이지 제목 | 10회+ | _draw_header |

### 3.3 font_micro vs font_tiny 1px 차이 이슈

**현황**:
- `font_micro` = 12px
- `font_tiny` = 13px
- 차이: 1픽셀만

**영향**:
- 텍스트 피팅 시 선택 순서 중요 (작은 것부터 시도)
- `_draw_text_fit()` 및 `_draw_wrapped_text_fit()`에서 fallback 튜플 순서:
  ```python
  (self.font_tiny, self.font_micro)  # 또는
  (self.font_small, self.font_tiny, self.font_micro)
  ```

**개선 기회**:
- 12px와 13px 차이가 가시적이지 않을 수 있음
- `font_micro` 사용을 14px로 올리거나
- `font_tiny`와 `font_micro`를 통합 검토 권장

---

## 4. 색상 사용 통계

### 4.1 팔레트 상수 (라인 56-97)

#### 배경색 (BG_* 계열)

| 상수 | RGB | 용도 | 사용 빈도 |
|-----|-----|------|---------|
| `BG_DEEP` | (10, 18, 29) | 배지 내부, 최어두운 배경 | 11회 |
| `BG_BASE` | (11, 18, 29) | 메인 배경 그래디언트 상단 | 배경 캐시 |
| `BG_BASE_BOT` | (20, 31, 48) | 메인 배경 그래디언트 하단 | 배경 캐시 |
| `BG_PANEL` | (11, 20, 31) | 기본 패널 채우기 | 50회+ |
| `BG_PANEL_MID` | (12, 21, 31) | 스트립/칩 그래디언트 상단 | 30회+ |
| `BG_PANEL_ALT` | (13, 24, 37) | 슬롯/카드 바리에이션 | 20회+ |
| `BG_PANEL_LT` | (15, 24, 37) | 헤더 패널, 밝은 패널 | 15회+ |
| `BG_PANEL_UP` | (15, 26, 39) | 카드 그래디언트 상단 (경로/타임라인) | 25회+ |
| `BG_HEADER` | (19, 31, 47) | 헤더 그래디언트 하단 | 10회+ |
| `BG_ELEM` | (16, 28, 40) | 설정 버튼, 작은 요소 | 15회+ |
| `BG_ELEM_MID` | (18, 30, 43) | 이동/기본 칩 | 8회+ |
| `BG_ELEM_LT` | (18, 32, 46) | 난이도 칩, 스타일 직사각형 | 12회+ |
| `BG_ACCENT_BG` | (27, 41, 54) | 보상/위험 행 배경 | 8회+ |
| `BG_CARD_TOP` | (10, 19, 29) | _draw_panel 그래디언트 상단 | 6회+ |
| `BG_CARD_ALT` | (10, 20, 32) | _draw_battle_card 그래디언트 상단 | 8회+ |

#### 액센트색 (ACCENT_* 계열)

| 상수 | RGB | 용도 | 사용 빈도 |
|-----|-----|------|---------|
| `ACCENT_GOLD` | (214, 182, 112) | 버튼, 라벨, 핵심 강조 | 28회 |
| `ACCENT_GOLD_SOFT` | (236, 218, 176) | 패널/카드 테두리, 부드러운 아웃라인 | 25회 |
| `ACCENT_GOLD_PALE` | (255, 244, 217) | 버튼 테두리 강조, 밝은 크림색 | 46회 (가장 높음) |
| `ACCENT_GOLD_WARM` | (226, 204, 156) | 헤더 부제, 따뜻한 라벨 텍스트 | 21회 |
| `ACCENT_BLUE` | (108, 192, 235) | 설정 테두리, 이동 칩, 청록색 | 6회 |
| `ACCENT_BLUE_DEEP` | (74, 157, 214) | 패널 글로우, 단계 배지, 통계색 | 11회 |
| `ACCENT_TEAL` | (95, 222, 201) | 진행률 바 채우기, 선택 배지 | 4회 |
| `ACCENT_TEAL_SOFT` | (108, 224, 203) | 선택 카드 테두리, 완료 칩 | 8회 |
| `ACCENT_RED` | (236, 126, 90) | 위험 테두리, 보스색, 위험 | 22회 |

#### 텍스트색 (TEXT_* 계열)

| 상수 | RGB | 용도 | 사용 빈도 |
|-----|-----|------|---------|
| `TEXT_PRIMARY` | (244, 239, 225) | 메인 읽을 수 있는 텍스트 | 30회 |
| `TEXT_DIM` | (208, 219, 226) | 보조/캡션 텍스트 | 16회 |
| `TEXT_GOLD` | (226, 204, 156) | 헤더 부제, 따뜻한 라벨 텍스트 | 사용 안 함 (주로 hardcoded) |

#### UI 음소거 (UI_* 계열)

| 상수 | RGB | 용도 | 사용 빈도 |
|-----|-----|------|---------|
| `UI_MUTED` | (91, 134, 166) | 비활성 테두리, 상태 아웃라인 | 25회+ |
| `UI_DISABLED` | (76, 84, 96) | 비활성 버튼 채우기 | 5회 |
| `UI_DISABLED_ALT` | (70, 80, 92) | 대체 비활성 채우기 | 5회 |

### 4.2 Hardcoded RGB 색상 (상위 40개)

| 순위 | RGB | 사용 횟수 | 권장 상수명 | 주요 메서드 |
|-----|-----|---------|-----------|-----------|
| 1 | (255, 244, 217) | 46 | `ACCENT_GOLD_PALE` (이미 정의됨) | 텍스트, 테두리 |
| 2 | (244, 239, 225) | 30 | `TEXT_PRIMARY` (이미 정의됨) | 제목, 본문 |
| 3 | (214, 182, 112) | 28 | `ACCENT_GOLD` (이미 정의됨) | 버튼, 강조 |
| 4 | (236, 218, 176) | 25 | `ACCENT_GOLD_SOFT` (이미 정의됨) | 테두리 |
| 5 | (236, 126, 90) | 22 | `ACCENT_RED` (이미 정의됨) | 위험, 보스 |
| 6 | (229, 210, 164) | 21 | **새 상수 필요** | 라벨 (선택, 후보) |
| 7 | (208, 219, 226) | 16 | `TEXT_DIM` (이미 정의됨) | 보조 텍스트 |
| 8 | (170, 222, 210) | 13 | **새 상수 필요** | 목표 완료, 조합 |
| 9 | (10, 18, 29) | 11 | `BG_DEEP` (이미 정의됨) | 배지 |
| 10 | (74, 157, 214) | 11 | `ACCENT_BLUE_DEEP` (이미 정의됨) | 글로우, 배지 |
| 11 | (223, 206, 164) | 11 | **새 상수 필요** | 특수기 라벨 |
| 12 | (12, 20, 31) | 10 | **새 상수 필요** | 폰트 어두운색 |
| 13 | (11, 20, 31) | 9 | `BG_PANEL` 근처 | 배경 |
| 14 | (255, 213, 150) | 9 | **새 상수 필요** | 경로 목표 |
| ... | ... | ... | ... | ... |

### 4.3 색상 최적화 권장사항

**즉시 추가할 상수 (hardcoded 6-13회)**:
```python
ACCENT_GOLD_WARM_ALT = (229, 210, 164)    # 라벨 (선택, 후보 로스터)
ACCENT_TEAL_ACTIVE = (170, 222, 210)      # 목표 완료, 조합
ACCENT_SPECIAL = (223, 206, 164)          # 특수기 라벨 텍스트
BG_TEXT_DARK = (12, 20, 31)               # 다크 텍스트 컨테이너
ACCENT_GOAL = (255, 213, 150)             # 경로 목표 강조
```

**고려할 정리 (3-5회 사용)**:
- (255, 255, 255) - 순백색, 사용 7회
- (235, 156, 140) - 붉은계 경고, 사용 7회
- (174, 208, 235) - 밝은 파랑, 사용 6회
- (108, 192, 235) - 파랑 칩, 사용 6회 (이미 `ACCENT_BLUE`)
- (198, 176, 168) - 중성 따뜻한색, 사용 6회
- (83, 170, 236) - 대체 파랑, 사용 4회
- (104, 191, 234) - 밝은 파랑 변형, 사용 4회

---

## 5. 상태 머신 (State Machine)

### 5.1 게임 페이즈/화면 모드

```python
# 라인 783 - screen_mode
self.screen_mode: Literal["select", "deploy", "battle", "reward", "route", "summary"] = "select"

# FLOW_STEPS 표현 (라인 694)
FLOW_STEPS = ("선택", "배치", "전투", "보상", "경로", "결산")
```

### 5.2 화면 전환 흐름

```
시작 → select (챔피언 선택)
       ↓
     deploy (아군 배치)
       ↓
     battle (3전 원정, 반복)
       ↓
     reward (승리 선택)
       ↓
     route (경로 선택)
       ↓
     battle (다음 전투)
     ...
     summary (최종 결산)
       ↓
     종료
```

### 5.3 주요 상태 변수

| 변수 | 타입 | 초기값 | 역할 |
|-----|------|------|------|
| `screen_mode` | Literal[6개] | "select" | 현재 화면 모드 |
| `mode` | str | "move" | 전투 중 선택 모드 ("move", "basic", "special", "end") |
| `run_stage` | int | 1 | 현재 원정 단계 (1-3) |
| `controller` | TacticsController | None | 전술 게임 로직 엔진 |
| `battle_intro_card` | BattleIntroCard | None | 전투 시작 컷인 카드 |
| `help_overlay_visible` | bool | False | 도움말 표시 여부 |
| `settings_overlay_visible` | bool | False | 설정 표시 여부 |
| `pending_battle_resolution` | str | None | 전투 결과 대기 (None/"victory"/"defeat") |

### 5.4 메인 게임 루프

```python
# 라인 871-885
def run(self, max_frames: int | None = None, screenshot_path: str | None = None) -> None:
    frames = 0
    while self.running:
        dt = self.clock.tick(60) / 1000.0      # 60 FPS 타이밍
        self._handle_events()                   # 라인 875 - 입력 처리
        self._update(dt)                        # 라인 876 - 로직 업데이트
        self._draw()                            # 라인 877 - 렌더링
        pygame.display.flip()                   # 화면 갱신
        frames += 1
        if max_frames is not None and frames >= max_frames:
            break
```

### 5.5 렌더링 조건부 분기 (_draw 메서드)

```python
# 라인 2966-2988
def _draw(self) -> None:
    self.screen.blit(self.background_cache, (0, 0))  # 배경 먼저 그리기
    self.button_rects.clear()
    self.tile_rects.clear()
    self.reward_card_rects.clear()
    self.route_card_rects.clear()

    # 화면 모드별 메인 콘텐츠 렌더링
    if self.screen_mode == "select":
        self._draw_selection_screen()
    elif self.screen_mode == "reward":
        self._draw_reward_screen()
    elif self.screen_mode == "route":
        self._draw_route_screen()
    elif self.screen_mode == "summary":
        self._draw_summary_screen()
    elif self.screen_mode == "deploy":
        self._draw_deploy_screen()
    else:  # "battle"
        self._draw_battle_screen()

    # 오버레이/UI (모든 화면 모드에서)
    self._draw_flow_breadcrumb()      # 진행도 표시
    self._draw_finale_banner()        # 최종전 배너
    self._draw_battle_intro()         # 전투 시작 컷인
    self._draw_help_overlay()         # 도움말
    self._draw_settings_overlay()     # 설정
```

### 5.6 화면별 조건부 렌더링

| 메서드 | 렌더링 조건 | 스킵 조건 |
|--------|-----------|----------|
| `_draw_flow_breadcrumb()` | 라인 2992 | `screen_mode` in {"battle", "summary"} 또는 `help_overlay_visible` |
| `_draw_selection_screen()` | `screen_mode == "select"` | - |
| `_draw_battle_grid()` | `controller is not None` | - |
| `_draw_battle_intro()` | 라인 5534 | `screen_mode != "battle"` 또는 `battle_intro_card is None` |
| `_draw_winner_overlay()` | 라인 4078 | `pending_battle_resolution is not None` |
| `_draw_help_overlay()` | `help_overlay_visible == True` | - |
| `_draw_settings_overlay()` | `settings_overlay_visible == True` | - |

---

## 6. 리팩토링 기회 분석

### 6.1 중복 렌더링 패턴

#### 패턴 1: 패널 + 텍스트 조합
**발생 빈도**: 50회+
**위치**:
- `_draw_selection_screen()` (라인 3238-3243)
- `_draw_deploy_screen()` (라인 4068-4070)
- `_draw_battle_screen()` (라인 4068-4070)

**현재 코드**:
```python
self._draw_panel(LEFT_PANEL, (74, 157, 214))
self._draw_text("플레이어 팀 선택", self.font_heading, (244, 239, 225), ...)
self._draw_text("핵심 챔피언을...", self.font_small, (150, 182, 201), ...)
```

**개선 제안**:
```python
def _draw_panel_with_header(self, rect, glow_color, title, subtitle, ...):
    self._draw_panel(rect, glow_color)
    self._draw_text(title, self.font_heading, TEXT_PRIMARY, ...)
    self._draw_text(subtitle, self.font_small, (150, 182, 201), ...)
```

#### 패턴 2: 카드 그리드 반복
**발생 빈도**: 3회 (선택 슬롯, 선택 풀, 선택 교리)
**위치**:
- `_draw_selection_slots()` (라인 3260-3269)
- `_draw_selection_pool()` (라인 3285-3299)
- `_draw_selection_doctrine_panel()` (라인 3315-3326)

**개선 제안**:
```python
def _draw_card_grid(self, rect, items, columns, card_render_fn):
    # 공통 그리드 레이아웃 계산
    # 각 카드 렌더링은 콜백으로
```

#### 패턴 3: 타일 렌더링 반복
**발생 빈도**: 2회
**위치**:
- `_draw_battle_grid()` (라인 4098-4103)
- `_draw_deploy_grid()` (라인 3937-3969)

**현재 코드**:
```python
for y in range(GRID_HEIGHT):
    for x in range(GRID_WIDTH):
        rect = pygame.Rect(...)
        self.tile_rects[(x, y)] = rect
        self._draw_grid_tile_base(rect, x, y, theme)
        self._draw_terrain_tile(...)
```

**개선 제안**:
```python
def _draw_grid_tiles(self, terrain_tiles, blocked_tiles,
                     draw_units=True, draw_blocked=True):
    # 공통 타일 그리기 로직
```

### 6.2 메서드 결합 기회

#### 기회 1: 유닛 렌더링 레이어 통합
**현재 구조**:
```python
_draw_battle_unit()           # 라인 4340
  → _draw_tactical_standee()  # 라인 4945
    → _draw_tactical_body_layer()     # 라인 5170
    → _draw_tactical_accessory()      # 라인 5300
```

**문제**: 스탠드 렌더링이 4개 메서드로 분산
**개선**: 스탠드 렌더링을 단일 구조 클래스로 캡슐화

#### 기회 2: 배경 그래디언트 통합
**현재 사용처** (라인 3024, 2996, 3332 등):
```python
draw_vertical_gradient(surface, rect, top_color, bottom_color)
```

**문제**: 색상 상수가 메서드 내부에 하드코딩됨
**개선**: 그래디언트 프리셋 정의
```python
GRADIENT_HEADER = (BG_PANEL_LT, BG_HEADER)
GRADIENT_PANEL = (BG_PANEL_MID, BG_PANEL)
```

### 6.3 하드코딩된 값 → 상수화 기회

#### 고정 좌표 (화면 레이아웃)
**현재 예**:
- 라인 2994: `strip_rect = pygame.Rect(WINDOW_WIDTH // 2 - 360, ...)`
- 라인 3260: `slot_rect = pygame.Rect(rect.x + index * (slot_width + gap), ...)`

**문제**: 레이아웃 변경 시 모든 메서드 수정 필요
**개선**: 레이아웃 프리셋 클래스
```python
@dataclass
class LayoutPreset:
    breadcrumb_rect: pygame.Rect
    selection_grid: dict  # columns, gap_x, gap_y
```

#### 색상 동적 선택
**현재 예** (라인 3041-3043):
```python
diff_bg = (32, 22, 8) if is_veteran else (18, 22, 28)
diff_border = (214, 148, 48) if is_veteran else (88, 100, 112)
diff_text_color = (255, 196, 96) if is_veteran else (148, 160, 172)
```

**개선**:
```python
DIFFICULTY_THEME = {
    "standard": {
        "bg": (18, 22, 28),
        "border": (88, 100, 112),
        "text": (148, 160, 172)
    },
    "veteran": {
        "bg": (32, 22, 8),
        "border": (214, 148, 48),
        "text": (255, 196, 96)
    }
}
```

### 6.4 폰트 선택 자동화

**현재 패턴** (25회+):
```python
self._draw_text_fit(label, (self.font_tiny, self.font_micro), color, rect, ...)
self._draw_wrapped_text_fit(text, (self.font_small, self.font_tiny, self.font_micro), ...)
```

**문제**: fallback 튜플이 반복되고, `font_micro`와 `font_tiny` 1px 차이 활용 불명확
**개선**:
```python
FONT_FALLBACK_LABEL = (self.font_tiny, self.font_micro)
FONT_FALLBACK_BODY = (self.font_small, self.font_tiny, self.font_micro)

# 사용
self._draw_text_fit(label, FONT_FALLBACK_LABEL, color, rect, ...)
```

또는 메서드 매개변수 기본값:
```python
def _draw_text_fit(self, text, fonts=None, color=TEXT_PRIMARY, ...):
    fonts = fonts or FONT_FALLBACK_LABEL
```

### 6.5 텍스트 색상 스키마

**현재 문제**:
- Hardcoded 색상 6-13회 사용하는 것들이 상수 없음
- 같은 목적(예: "라벨")이 여러 색상으로 표현

**개선 예**:
```python
# 라벨 색상 집합
LABEL_COLORS = {
    "pool": (229, 210, 164),      # 후보 로스터
    "selection": (229, 210, 164),
    "passive": (223, 206, 164),   # 패시브 라벨
    "special": (223, 206, 164),   # 특수기 라벨
    "move": (205, 220, 229),      # 이동 라벨
    "secondary": (150, 182, 201), # 보조 설명
}
```

### 6.6 조건부 렌더링 단순화

**현재 예** (라인 4108-4112):
```python
if (x, y) in reachable:
    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    overlay.fill((89, 170, 219, 58))
    self.screen.blit(overlay, rect.topleft)
    pygame.draw.rect(self.screen, (120, 202, 246), rect.inflate(-22, -22), 2, ...)
```

**문제**: Hardcoded 색상, 반복되는 Surface 생성
**개선**:
```python
def _draw_tile_overlay(self, rect, overlay_type):
    overlay_config = {
        "reachable": {"fill": (89, 170, 219, 58), "border": (120, 202, 246)},
        "objective": {"fill": (236, 126, 90, ...), "border": (236, 126, 90)},
    }
    config = overlay_config.get(overlay_type)
    # 공통 렌더링
```

---

## 7. 요약 및 액션 아이템

### 7.1 즉시 개선 (1-2시간)

1. **색상 상수 6개 추가** (라인 70 이후)
   - `ACCENT_GOLD_WARM_ALT = (229, 210, 164)`
   - `ACCENT_TEAL_ACTIVE = (170, 222, 210)`
   - 등 5개

2. **폰트 fallback 튜플 상수화**
   ```python
   FONT_FALLBACK_LABEL = (self.font_tiny, self.font_micro)
   FONT_FALLBACK_BODY = (self.font_small, self.font_tiny, self.font_micro)
   ```

3. **어려운 난이도 색상 테마 추출** (라인 3041-3043 형태)

### 7.2 중기 개선 (반나절)

1. **공통 패널 헤더 메서드** → 10회+ 반복 제거
2. **레이아웃 상수 모음** (breadcrumb, selection_grid, etc.)
3. **`_draw_panel()` 확장** (선택적 헤더/서브헤더 매개변수)

### 7.3 장기 개선 (1일 이상)

1. **유닛 렌더러 클래스 분리** (`TacticalStandeeRenderer`)
2. **화면 모드별 렌더 컨텍스트** 클래스화
3. **그리드 렌더 시스템** 통합 (배치/전투 공유)

### 7.4 기술 부채 추적

| 항목 | 파일 | 라인 | 우선도 |
|-----|------|------|--------|
| font_micro vs font_tiny 1px 차이 | app.py | 768-769 | 낮음 |
| 패널 + 헤더 반복 | app.py | 3238-3243 외 | 중간 |
| 그리드 렌더링 중복 | app.py | 4098 vs 3937 | 중간 |
| Hardcoded 색상 6가지 | 전체 | 다수 | 높음 |
| 유닛 렌더 메서드 4단계 | app.py | 4340-5300 | 중간 |

---

## 8. 참고 자료

### 파일 정보
- **경로**: `/home/faeqsu10/projects/lol-rift-tactics/native_tactics/app.py`
- **라인 수**: 5953줄
- **주요 클래스**: `GameApp` (755줄)
- **폰트 정의**: 756-774줄
- **색상 팔레트**: 56-97줄
- **메인 루프**: 871-885줄
- **렌더링 진입점**: 2966줄

### 관련 파일
- `native_tactics/data.py` - 전술 게임 데이터 정의
- `native_tactics/engine.py` - 전술 게임 로직
- `native_game/data.py` - 챔피언 블루프린트
- `native_game/audio.py` - 사운드 시스템

### 주요 상수 위치

| 항목 | 라인 범위 |
|-----|---------|
| 윈도우/그리드 레이아웃 | 40-50 |
| 색상 팔레트 | 56-97 |
| 게임 설정 | 99-415 |
| 헬퍼 함수 | 705-752 |
| GameApp 클래스 | 755-5910 |

