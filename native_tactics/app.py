from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Literal

import pygame

from native_game.audio import SoundBank
from native_game.data import BLUEPRINTS_BY_ID
from native_game.data import DEFAULT_BLUE_IDS
from native_game.data import SELECTABLE_BLUE_IDS
from native_game.data import SELECTABLE_RED_IDS
from native_game.runtime import project_root

from .data import ART_FILE_BY_UNIT_ID
from .data import BLOCKED_TILES
from .data import BOSS_PROFILES_BY_ID
from .data import DEFAULT_BLUE_DEPLOY_TILES
from .data import DEFAULT_RED_DEPLOY_TILES
from .data import ELITE_TRAITS_BY_ID
from .data import FINALE_VARIANTS_BY_ID
from .data import GRID_HEIGHT
from .data import GRID_WIDTH
from .data import GridPos
from .data import ROLE_ELITE_TRAIT_ID
from .data import STAGE_TERRAIN_TILES
from .data import TACTICAL_BLUEPRINTS_BY_ID
from .data import TERRAIN_BY_ID
from .data import boss_profile_id_for_champion
from .engine import TacticalActionResult
from .engine import TacticsController
from .history import DoctrineStatus
from .history import RunHistoryStore

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 960
GRID_CELL = 100
GRID_ORIGIN = pygame.Vector2(360, 130)
GRID_RECT = pygame.Rect(int(GRID_ORIGIN.x), int(GRID_ORIGIN.y), GRID_WIDTH * GRID_CELL, GRID_HEIGHT * GRID_CELL)
LEFT_PANEL = pygame.Rect(36, 120, 284, 694)
RIGHT_PANEL = pygame.Rect(1180, 120, 384, 694)
BOTTOM_PANEL = pygame.Rect(36, 832, WINDOW_WIDTH - 72, 92)
HEADER_RECT = pygame.Rect(36, 28, WINDOW_WIDTH - 72, 72)
SELECT_LEFT_PANEL = pygame.Rect(36, 120, 920, 784)
SELECT_RIGHT_PANEL = pygame.Rect(982, 120, 582, 784)

PROJECT_ROOT = project_root()
FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "NotoSansKR-Variable.ttf"
CHAMPION_ART_DIR = PROJECT_ROOT / "assets" / "champions"
RUN_STAGE_COUNT = 3
RUN_STAGE_LABELS = {
    1: "정찰전",
    2: "엘리트전",
    3: "결전",
}
RUN_REWARDS = (
    ("bonus-hp", "전장 보급", "아군 전원 체력 +10"),
    ("bonus-damage", "날 선 무기", "아군 전원 피해 +3"),
    ("bonus-speed", "속공 지휘", "아군 전원 속도 +5"),
    ("bonus-move", "기동 훈련", "아군 전원 이동력 +1"),
    ("bonus-shield", "수호 문장", "아군 전원 시작 보호막 +12"),
)
STAGE_RED_POOLS = {
    1: ("red-annie", "red-caitlyn", "red-darius", "red-morgana", "red-brand"),
    2: ("red-darius", "red-caitlyn", "red-morgana", "red-yasuo", "red-brand", "red-lissandra"),
    3: ("red-darius", "red-yasuo", "red-zed", "red-brand", "red-katarina", "red-lissandra"),
}
ROUTE_OPTIONS = (
    ("supply-line", "보급로", "목표: 중앙 보급 칸 진입 1회"),
    ("assault-line", "돌격로", "목표: 2라운드 이내 적 1명 처치"),
    ("hidden-trail", "은폐로", "목표: 수풀 칸 진입 2회"),
    ("rune-path", "룬 회랑", "목표: 룬 지대 진입 2회"),
    ("rapid-flank", "측면 질주로", "목표: 적 후방 표식 칸 진입 1회"),
    ("scorched-march", "초토화 행군", "목표: 화염 지대 진입 1회"),
)
ROUTE_STYLE_BY_ID = {
    "supply-line": "안정 운영형",
    "assault-line": "교전 압박형",
    "hidden-trail": "포지션 교란형",
    "rune-path": "폭딜 준비형",
    "rapid-flank": "선턴 압박형",
    "scorched-march": "하이리스크 화력형",
}
ROUTE_REWARD_BY_ID = {
    "supply-line": "아군 전원 시작 보호막 +8",
    "assault-line": "아군 전원 피해 +2",
    "hidden-trail": "추가 수풀 2개 생성",
    "rune-path": "추가 룬 지대 2개 생성",
    "rapid-flank": "아군 전원 속도 +5",
    "scorched-march": "아군 전원 피해 +4",
}
ROUTE_RISK_BY_ID = {
    "supply-line": "추가 위험 없음",
    "assault-line": "적 전원 피해 +1",
    "hidden-trail": "적 전원 속도 +2",
    "rune-path": "추가 화염 지대 1개 생성",
    "rapid-flank": "적 전원 속도 +2",
    "scorched-march": "추가 화염 지대 2개 + 적 피해 +1",
}
MODIFIER_LABEL_BY_ID = {
    "blue_hp": "아군 체력",
    "blue_damage": "아군 피해",
    "blue_speed": "아군 속도",
    "blue_move": "아군 이동력",
    "blue_shield": "아군 시작 보호막",
    "enemy_hp": "적 전원 체력",
    "enemy_damage": "적 전원 피해",
    "enemy_speed": "적 전원 속도",
    "enemy_shield": "적 전원 시작 보호막",
}
ROUTE_BONUSES = {
    "supply-line": {"blue_shield": 8},
    "assault-line": {"blue_damage": 2, "enemy_damage": 1},
    "hidden-trail": {"enemy_speed": 2},
    "rune-path": {},
    "rapid-flank": {"blue_speed": 5, "enemy_speed": 2},
    "scorched-march": {"blue_damage": 4, "enemy_damage": 1},
}
ROUTE_OBJECTIVES = {
    "supply-line": {"kind": "occupy_tile", "name": "보급 확보", "reward_id": "bonus-shield"},
    "assault-line": {"kind": "kill_before_round", "name": "선제 제압", "reward_id": "bonus-damage", "round_limit": 2},
    "hidden-trail": {"kind": "move_on_terrain", "name": "은폐 정찰", "reward_id": "bonus-move", "terrain_id": "brush", "target": 2},
    "rune-path": {"kind": "move_on_terrain", "name": "룬 장악", "reward_id": "bonus-damage", "terrain_id": "rune", "target": 2},
    "rapid-flank": {"kind": "occupy_tile", "name": "측면 돌파", "reward_id": "bonus-speed"},
    "scorched-march": {"kind": "move_on_terrain", "name": "화염 관통", "reward_id": "bonus-hp", "terrain_id": "hazard"},
}
ROUTE_OBJECTIVE_TILES = {
    "supply-line": {
        2: ((3, 2),),
        3: ((3, 1),),
    },
    "rapid-flank": {
        2: ((6, 2),),
        3: ((6, 3),),
    },
}
ROUTE_EXTRA_TERRAIN = {
    "hidden-trail": {
        2: {(2, 2): "brush", (5, 3): "brush"},
        3: {(2, 4): "brush", (5, 1): "brush"},
    },
    "rune-path": {
        2: {(2, 3): "rune", (5, 2): "rune", (4, 2): "hazard"},
        3: {(2, 1): "rune", (5, 4): "rune", (4, 1): "hazard"},
    },
    "scorched-march": {
        2: {(3, 1): "hazard", (4, 4): "hazard"},
        3: {(2, 2): "hazard", (5, 3): "hazard"},
    },
}
ROUTE_EVENT_TEMPLATES = {
    "supply-line": (
        {
            "id": "supply-medic",
            "name": "응급 보급품",
            "description": "보급대가 먼저 도착해 전열을 단단히 잡아 줍니다.",
            "effect_label": "이번 전투 아군 시작 보호막 +6",
            "stage_modifiers": {"blue_shield": 6},
            "failure_penalty_name": "보급 탈취",
            "failure_penalty_label": "다음 전투 적 전원 시작 보호막 +10",
            "penalty_modifiers": {"enemy_shield": 10},
        },
        {
            "id": "supply-rations",
            "name": "전장 식량",
            "description": "짧은 재정비로 다음 전투 체력을 더 끌어올립니다.",
            "effect_label": "이번 전투 아군 체력 +8",
            "stage_modifiers": {"blue_hp": 8},
            "failure_penalty_name": "보급 지연",
            "failure_penalty_label": "다음 전투 적 전원 피해 +1",
            "penalty_modifiers": {"enemy_damage": 1},
        },
    ),
    "assault-line": (
        {
            "id": "assault-drums",
            "name": "전장의 북소리",
            "description": "공세 리듬이 살아나며 공격 타이밍이 날카로워집니다.",
            "effect_label": "이번 전투 아군 피해 +2",
            "stage_modifiers": {"blue_damage": 2},
            "failure_penalty_name": "전선 역습",
            "failure_penalty_label": "다음 전투 적 전원 피해 +2",
            "penalty_modifiers": {"enemy_damage": 2},
        },
        {
            "id": "assault-vanguard",
            "name": "선봉 신호",
            "description": "돌격대가 먼저 움직이며 교전 템포를 앞당깁니다.",
            "effect_label": "이번 전투 아군 속도 +3",
            "stage_modifiers": {"blue_speed": 3},
            "failure_penalty_name": "무너진 돌파",
            "failure_penalty_label": "다음 전투 적 전원 속도 +2",
            "penalty_modifiers": {"enemy_speed": 2},
        },
    ),
    "hidden-trail": (
        {
            "id": "hidden-smoke",
            "name": "연막 정찰",
            "description": "은폐 경로가 열려 진입 속도가 더 빨라집니다.",
            "effect_label": "이번 전투 아군 이동력 +1",
            "stage_modifiers": {"blue_move": 1},
            "failure_penalty_name": "위치 노출",
            "failure_penalty_label": "다음 전투 적 전원 속도 +3",
            "penalty_modifiers": {"enemy_speed": 3},
        },
        {
            "id": "hidden-shadow",
            "name": "그림자 유도",
            "description": "숨은 척후가 타이밍을 맞춰 기동을 보조합니다.",
            "effect_label": "이번 전투 아군 속도 +2 · 보호막 +4",
            "stage_modifiers": {"blue_speed": 2, "blue_shield": 4},
            "failure_penalty_name": "역추적",
            "failure_penalty_label": "다음 전투 적 전원 피해 +1 · 속도 +2",
            "penalty_modifiers": {"enemy_damage": 1, "enemy_speed": 2},
        },
    ),
    "rune-path": (
        {
            "id": "rune-harmonic",
            "name": "공명 코어",
            "description": "룬 잔향이 전장을 감싸 공격과 보호를 함께 끌어올립니다.",
            "effect_label": "이번 전투 아군 피해 +2 · 보호막 +4",
            "stage_modifiers": {"blue_damage": 2, "blue_shield": 4},
            "failure_penalty_name": "룬 역류",
            "failure_penalty_label": "다음 전투 적 전원 피해 +1 · 보호막 +8",
            "penalty_modifiers": {"enemy_damage": 1, "enemy_shield": 8},
        },
        {
            "id": "rune-overclock",
            "name": "과충전 룬맥",
            "description": "룬이 과열되어 속도와 화력이 동시에 오릅니다.",
            "effect_label": "이번 전투 아군 피해 +1 · 속도 +3",
            "stage_modifiers": {"blue_damage": 1, "blue_speed": 3},
            "failure_penalty_name": "불안정 공명",
            "failure_penalty_label": "다음 전투 적 전원 보호막 +6 · 속도 +2",
            "penalty_modifiers": {"enemy_shield": 6, "enemy_speed": 2},
        },
    ),
    "rapid-flank": (
        {
            "id": "rapid-flags",
            "name": "측면 신호기",
            "description": "신호기가 측면 돌입 타이밍을 밀어 올립니다.",
            "effect_label": "이번 전투 아군 속도 +4",
            "stage_modifiers": {"blue_speed": 4},
            "failure_penalty_name": "측면 차단",
            "failure_penalty_label": "다음 전투 적 전원 속도 +2 · 피해 +1",
            "penalty_modifiers": {"enemy_speed": 2, "enemy_damage": 1},
        },
        {
            "id": "rapid-spearhead",
            "name": "선봉 투입",
            "description": "선봉대가 길을 열며 첫 교전을 유리하게 만듭니다.",
            "effect_label": "이번 전투 아군 이동력 +1 · 피해 +1",
            "stage_modifiers": {"blue_move": 1, "blue_damage": 1},
            "failure_penalty_name": "퇴로 붕괴",
            "failure_penalty_label": "다음 전투 아군 속도 -3",
            "penalty_modifiers": {"blue_speed": -3},
        },
    ),
    "scorched-march": (
        {
            "id": "scorched-embers",
            "name": "과열 검날",
            "description": "무기를 달군 채 강행군을 이어가며 화력을 끌어올립니다.",
            "effect_label": "이번 전투 아군 피해 +3",
            "stage_modifiers": {"blue_damage": 3},
            "failure_penalty_name": "소진 누적",
            "failure_penalty_label": "다음 전투 아군 체력 -12",
            "penalty_modifiers": {"blue_hp": -12},
        },
        {
            "id": "scorched-ashguard",
            "name": "재의 장막",
            "description": "불길 속을 뚫고 나가며 짧은 방호막을 얻습니다.",
            "effect_label": "이번 전투 아군 보호막 +6 · 피해 +1",
            "stage_modifiers": {"blue_shield": 6, "blue_damage": 1},
            "failure_penalty_name": "화상 후유증",
            "failure_penalty_label": "다음 전투 아군 체력 -8 · 적 피해 +1",
            "penalty_modifiers": {"blue_hp": -8, "enemy_damage": 1},
        },
    ),
}
RUN_NODE_TEMPLATES = {
    "rest-camp": {
        "name": "휴식 거점",
        "category": "정비 노드",
        "description": "짧은 재정비로 전열을 복구하고 예약 페널티를 지워 냅니다.",
        "effect_label": "아군 체력 +12 · 보호막 +6 · 예약 페널티 해제",
        "stage_modifiers": {"blue_hp": 12, "blue_shield": 6},
        "clears_pending_penalty": True,
    },
    "event-surge": {
        "name": "변수 균열",
        "category": "증폭 노드",
        "description": "경로 이벤트가 과충전되어 보너스와 실패 페널티가 모두 커집니다.",
        "effect_label": "경로 이벤트 수치 +100% · 실패 페널티도 강화",
        "stage_modifiers": {},
        "event_modifier_scale": 2,
        "penalty_modifier_scale": 2,
    },
    "elite-contract": {
        "name": "정예 수배",
        "category": "고위험 노드",
        "description": "추가 정예가 난입하지만 승리 시 런 강화를 하나 더 챙깁니다.",
        "effect_label": "적 정예 +1 · 승리 시 추가 강화 1개",
        "stage_modifiers": {},
        "extra_elites": 1,
    },
}
NODE_FOLLOW_UP_TEMPLATES = {
    "rest-camp": (
        {
            "id": "rest-medic",
            "name": "의무관 순회",
            "description": "현장 의무관이 전열을 다시 세우며 체력과 보호막을 보강합니다.",
            "effect_label": "이번 전투 아군 체력 +6 · 시작 보호막 +4",
            "stage_modifiers": {"blue_hp": 6, "blue_shield": 4},
        },
        {
            "id": "rest-regroup",
            "name": "신속 재집결",
            "description": "짧은 정비 후 재빠르게 재집결해 선턴 대응을 준비합니다.",
            "effect_label": "이번 전투 아군 속도 +4 · 이동력 +1",
            "stage_modifiers": {"blue_speed": 4, "blue_move": 1},
        },
    ),
    "event-surge": (
        {
            "id": "surge-overdrive",
            "name": "공명 폭주",
            "description": "균열 잔광이 무기를 과충전해 공격력을 끌어올립니다.",
            "effect_label": "이번 전투 아군 피해 +2 · 적 피해 +1",
            "stage_modifiers": {"blue_damage": 2, "enemy_damage": 1},
        },
        {
            "id": "surge-siphon",
            "name": "잔광 흡수",
            "description": "불안정한 파편을 보호막으로 전환해 진입 안정성을 높입니다.",
            "effect_label": "이번 전투 아군 시작 보호막 +8 · 피해 +1",
            "stage_modifiers": {"blue_shield": 8, "blue_damage": 1},
        },
    ),
    "elite-contract": (
        {
            "id": "elite-bounty",
            "name": "현상금 표식",
            "description": "정예 위치가 미리 드러나 블루 팀의 집중 화력이 강해집니다.",
            "effect_label": "이번 전투 아군 피해 +2 · 속도 +2",
            "stage_modifiers": {"blue_damage": 2, "blue_speed": 2},
        },
        {
            "id": "elite-breach",
            "name": "선봉 추적",
            "description": "추적조가 진입 경로를 열어 이동력과 초반 보호막을 지원합니다.",
            "effect_label": "이번 전투 아군 이동력 +1 · 시작 보호막 +6",
            "stage_modifiers": {"blue_move": 1, "blue_shield": 6},
        },
    ),
}


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    lifetime: float = 0.8


@dataclass
class BattleIntroCard:
    title: str
    subtitle: str
    detail_lines: list[str]
    color: tuple[int, int, int]
    timer: float = 1.65


@dataclass(frozen=True)
class RunReward:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class RouteOption:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class StageModifier:
    name: str
    description: str
    modifiers: dict[str, int]


@dataclass(frozen=True)
class RouteEvent:
    id: str
    route_id: str
    name: str
    description: str
    effect_label: str
    stage_modifiers: dict[str, int]
    failure_penalty_name: str
    failure_penalty_label: str
    penalty_modifiers: dict[str, int]


@dataclass(frozen=True)
class RunNode:
    id: str
    name: str
    category: str
    description: str
    effect_label: str
    stage_modifiers: dict[str, int]
    event_modifier_scale: int = 1
    penalty_modifier_scale: int = 1
    clears_pending_penalty: bool = False
    extra_elites: int = 0
    victory_reward_id: str | None = None
    victory_reward_label: str | None = None


@dataclass(frozen=True)
class NodeFollowUp:
    id: str
    node_id: str
    name: str
    description: str
    effect_label: str
    stage_modifiers: dict[str, int]


@dataclass
class BattleRecap:
    stage_label: str
    result_label: str
    rounds: int
    blue_damage: int
    red_damage: int
    blue_kills: int
    red_kills: int
    highlight: str
    objective_summary: str | None = None
    route_node_summary: str | None = None
    route_event_summary: str | None = None
    penalty_summary: str | None = None


@dataclass
class RunSummary:
    result_label: str
    stage_label: str
    lineup_label: str
    total_rounds: int
    total_blue_damage: int
    total_red_damage: int
    total_blue_kills: int
    total_red_kills: int
    build_lines: list[str]
    best_reward_line: str
    recommendation: str
    recap_entries: list[BattleRecap]
    history_overview_lines: list[str]
    history_comparison_lines: list[str]
    unlock_lines: list[str]


@dataclass
class BattleObjective:
    route_id: str
    name: str
    description: str
    kind: str
    target: int
    reward_id: str
    reward_label: str
    objective_tiles: tuple[GridPos, ...] = ()
    terrain_id: str | None = None
    round_limit: int | None = None
    progress: int = 0
    completed: bool = False
    failed: bool = False
    is_finale: bool = False
    boss_id: str | None = None
    success_label: str | None = None
    failure_label: str | None = None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[index : index + 2], 16) for index in (0, 2, 4))


def mix(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = clamp(amount, 0.0, 1.0)
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def draw_vertical_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    for offset in range(rect.height):
        progress = offset / max(1, rect.height - 1)
        pygame.draw.line(surface, mix(top, bottom, progress), (rect.x, rect.y + offset), (rect.right, rect.y + offset))


def load_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    if FONT_PATH.exists():
        font = pygame.font.Font(FONT_PATH, size)
        font.set_bold(bold)
        return font

    matched = pygame.font.match_font(["Noto Sans CJK KR", "NanumGothic", "malgungothic", "arial"], bold=bold)
    if matched:
        font = pygame.font.Font(matched, size)
        font.set_bold(bold)
        return font

    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class GameApp:
    def __init__(self, headless: bool = False, history_path: Path | None = None) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("리프트 택틱스: 전술 실험")
        flags = pygame.HIDDEN if headless else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True
        self.headless = headless
        resolved_history_path = history_path if history_path is not None else (None if headless else RunHistoryStore.default_path())
        self.history_store = RunHistoryStore.load(resolved_history_path)

        self.font_tiny = load_font(13)
        self.font_small = load_font(16)
        self.font_ui = load_font(20)
        self.font_heading = load_font(26, bold=True)
        self.font_large = load_font(34, bold=True)
        self.font_title = load_font(42, bold=True)

        self.audio = SoundBank()
        self.audio.start_ambient()
        self.champion_art = self._load_champion_art()
        self.background_cache = self._build_background()

        self.screen_mode: Literal["select", "deploy", "battle", "reward", "route", "summary"] = "select"
        self.mode = "move"
        self.status_text = ""
        self.selection_message = ""
        self.selected_blue_ids = list(DEFAULT_BLUE_IDS)
        self.run_stage = 1
        self.run_rewards = {reward_id: RunReward(reward_id, name, description) for reward_id, name, description in RUN_REWARDS}
        self.route_options = {route_id: RouteOption(route_id, name, description) for route_id, name, description in ROUTE_OPTIONS}
        self.run_bonuses = {reward_id: 0 for reward_id in self.run_rewards}
        self.reward_option_ids: list[str] = []
        self.selected_reward_id: str | None = None
        self.route_option_ids: list[str] = []
        self.route_event_by_route_id: dict[str, RouteEvent] = {}
        self.route_node_by_route_id: dict[str, RunNode] = {}
        self.node_follow_up_by_route_id: dict[str, NodeFollowUp] = {}
        self.selected_route_id: str | None = None
        self.current_route_id: str | None = None
        self.current_route_event: RouteEvent | None = None
        self.current_route_node: RunNode | None = None
        self.current_node_follow_up: NodeFollowUp | None = None
        self.pending_red_ids: list[str] = []
        self.pending_stage_penalty: StageModifier | None = None
        self.active_stage_penalty: StageModifier | None = None
        self.last_penalty_summary: str | None = None
        self.last_node_summary: str | None = None
        self.objective_failure_penalty_applied = False
        self.last_battle_recap: BattleRecap | None = None
        self.run_history: list[BattleRecap] = []
        self.run_summary: RunSummary | None = None
        self.current_objective: BattleObjective | None = None
        self.last_objective_summary: str | None = None
        self.objective_bonus_applied = False
        self.doctrine_statuses: list[DoctrineStatus] = []
        self.selected_doctrine_id: str | None = None
        self.active_doctrine_id: str | None = None
        self.route_reroll_charges = 0
        self.battle_stats = {
            "blue_damage": 0,
            "red_damage": 0,
            "blue_kills": 0,
            "red_kills": 0,
        }
        self.selected_red_ids = self._random_enemy_lineup(self.run_stage)
        self.deploy_assignments: dict[tuple[int, int], str] = {}
        self.red_deploy_assignments: dict[tuple[int, int], str] = {}
        self.selected_deploy_champion_id: str | None = None

        self.controller: TacticsController | None = None
        self.ai_timer = 0.55
        self.last_active_id: str | None = None
        self.floaters: list[FloatingText] = []
        self.hit_flash: dict[str, float] = {}
        self.unit_visual_positions: dict[str, pygame.Vector2] = {}
        self.finale_banner_title: str | None = None
        self.finale_banner_subtitle: str | None = None
        self.finale_banner_color: tuple[int, int, int] = (236, 126, 90)
        self.finale_banner_timer = 0.0
        self.battle_intro_card: BattleIntroCard | None = None

        self.tile_rects: dict[tuple[int, int], pygame.Rect] = {}
        self.button_rects: dict[str, pygame.Rect] = {}
        self.selection_card_rects: dict[str, pygame.Rect] = {}
        self.selection_slot_rects: list[pygame.Rect] = []
        self.doctrine_card_rects: dict[str, pygame.Rect] = {}
        self.deploy_roster_rects: dict[str, pygame.Rect] = {}
        self.reward_card_rects: dict[str, pygame.Rect] = {}
        self.route_card_rects: dict[str, pygame.Rect] = {}
        self._refresh_doctrine_statuses()
        self.selection_message = "플레이어 팀 3명을 고른 뒤 배치 단계로 넘어가세요."

    def run(self, max_frames: int | None = None, screenshot_path: str | None = None) -> None:
        frames = 0
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break

        if screenshot_path:
            pygame.image.save(self.screen, screenshot_path)
        pygame.quit()

    def _load_champion_art(self) -> dict[str, pygame.Surface]:
        art: dict[str, pygame.Surface] = {}
        for unit_id, filename in ART_FILE_BY_UNIT_ID.items():
            path = CHAMPION_ART_DIR / filename
            if path.exists():
                art[unit_id] = pygame.image.load(path).convert_alpha()
        return art

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        draw_vertical_gradient(surface, surface.get_rect(), (11, 18, 29), (20, 31, 48))
        for index in range(14):
            color = (214, 184, 114) if index % 2 == 0 else (78, 119, 155)
            alpha = 20 if index % 2 == 0 else 14
            circle = pygame.Surface((340, 340), pygame.SRCALPHA)
            pygame.draw.circle(circle, (*color, alpha), (170, 170), 170)
            surface.blit(circle, (index * 110 - 120, (index % 3) * 210 - 90))
        return surface

    def _current_stage_label(self) -> str:
        return RUN_STAGE_LABELS.get(self.run_stage, f"{self.run_stage}전")

    def _refresh_doctrine_statuses(self) -> None:
        self.doctrine_statuses = self.history_store.doctrine_statuses()
        unlocked_ids = [status.id for status in self.doctrine_statuses if status.unlocked]
        if self.selected_doctrine_id not in unlocked_ids:
            self.selected_doctrine_id = unlocked_ids[0] if unlocked_ids else None

    def _selected_doctrine(self) -> DoctrineStatus | None:
        return next(
            (
                status
                for status in self.doctrine_statuses
                if status.id == self.selected_doctrine_id and status.unlocked
            ),
            None,
        )

    def _active_doctrine(self) -> DoctrineStatus | None:
        return next(
            (
                status
                for status in self.doctrine_statuses
                if status.id == self.active_doctrine_id and status.unlocked
            ),
            None,
        )

    def _activate_selected_doctrine(self) -> None:
        doctrine = self._selected_doctrine()
        self.active_doctrine_id = doctrine.id if doctrine is not None else None
        self.route_reroll_charges = doctrine.route_reroll_charges if doctrine is not None else 0
        if doctrine is not None and doctrine.bonus_reward_id is not None:
            self.run_bonuses[doctrine.bonus_reward_id] += 1

    def _enemy_pool_for_stage(self, stage: int) -> tuple[str, ...]:
        return STAGE_RED_POOLS.get(stage, tuple(SELECTABLE_RED_IDS))

    def _terrain_tiles_for_stage(
        self,
        stage: int | None = None,
        route_id: str | None = None,
        enemy_ids: list[str] | None = None,
    ) -> dict[tuple[int, int], str]:
        resolved_stage = stage or self.run_stage
        finale_variant = self._finale_variant_for_stage(stage=resolved_stage, lineup=enemy_ids)
        tiles = dict(finale_variant.terrain_tiles if finale_variant is not None else STAGE_TERRAIN_TILES.get(resolved_stage, {}))
        resolved_route_id = route_id if route_id is not None else self.current_route_id
        if resolved_route_id in ROUTE_EXTRA_TERRAIN:
            for tile, terrain_id in ROUTE_EXTRA_TERRAIN[resolved_route_id].get(resolved_stage, {}).items():
                tiles[tile] = terrain_id
        return tiles

    def _blocked_tiles_for_stage(self, stage: int | None = None, enemy_ids: list[str] | None = None) -> tuple[GridPos, ...]:
        resolved_stage = stage or self.run_stage
        finale_variant = self._finale_variant_for_stage(stage=resolved_stage, lineup=enemy_ids)
        if finale_variant is not None:
            return finale_variant.blocked_tiles
        return BLOCKED_TILES

    def _boss_enemy_id_for_stage(self, stage: int | None = None, lineup: list[str] | None = None) -> str | None:
        current_stage = stage or self.run_stage
        enemy_ids = tuple(lineup or self.selected_red_ids)
        if current_stage < RUN_STAGE_COUNT or not enemy_ids:
            return None
        return max(enemy_ids, key=lambda champion_id: (TACTICAL_BLUEPRINTS_BY_ID[champion_id].max_hp, TACTICAL_BLUEPRINTS_BY_ID[champion_id].speed))

    def _boss_profile_for_stage(self, stage: int | None = None, lineup: list[str] | None = None):
        boss_id = self._boss_enemy_id_for_stage(stage=stage, lineup=lineup)
        if boss_id is None:
            return None
        return BOSS_PROFILES_BY_ID[boss_profile_id_for_champion(boss_id)]

    def _finale_variant_for_stage(self, stage: int | None = None, lineup: list[str] | None = None):
        resolved_stage = stage or self.run_stage
        if resolved_stage < RUN_STAGE_COUNT:
            return None
        boss_profile = self._boss_profile_for_stage(stage=resolved_stage, lineup=lineup)
        if boss_profile is None:
            return None
        return FINALE_VARIANTS_BY_ID[boss_profile.finale_variant_id]

    def _elite_enemy_ids_for_stage(
        self,
        stage: int | None = None,
        lineup: list[str] | None = None,
        route_node: RunNode | None = None,
    ) -> tuple[str, ...]:
        current_stage = stage or self.run_stage
        enemy_ids = tuple(lineup or self.selected_red_ids)
        if current_stage <= 1 or not enemy_ids:
            return ()
        resolved_route_node = route_node if route_node is not None else self.current_route_node
        extra_elites = resolved_route_node.extra_elites if resolved_route_node is not None else 0
        leader = self._boss_enemy_id_for_stage(current_stage, list(enemy_ids)) or max(
            enemy_ids,
            key=lambda champion_id: (TACTICAL_BLUEPRINTS_BY_ID[champion_id].max_hp, TACTICAL_BLUEPRINTS_BY_ID[champion_id].speed),
        )
        if current_stage == 2 or len(enemy_ids) == 1:
            ranked_ids = sorted(
                enemy_ids,
                key=lambda champion_id: (TACTICAL_BLUEPRINTS_BY_ID[champion_id].max_hp, TACTICAL_BLUEPRINTS_BY_ID[champion_id].speed),
                reverse=True,
            )
            elite_count = min(len(enemy_ids), 1 + extra_elites)
            return tuple(ranked_ids[:elite_count])
        lieutenant_candidates = sorted(
            (champion_id for champion_id in enemy_ids if champion_id != leader),
            key=lambda champion_id: (TACTICAL_BLUEPRINTS_BY_ID[champion_id].speed, TACTICAL_BLUEPRINTS_BY_ID[champion_id].max_hp),
            reverse=True,
        )
        elite_count = min(len(lieutenant_candidates), 1 + extra_elites)
        return tuple(lieutenant_candidates[:elite_count])

    def _elite_trait_id_for_enemy(self, champion_id: str) -> str | None:
        blueprint = TACTICAL_BLUEPRINTS_BY_ID.get(champion_id)
        if blueprint is None:
            return None
        return ROLE_ELITE_TRAIT_ID.get(blueprint.role)

    def _random_enemy_lineup(self, stage: int | None = None) -> list[str]:
        current_stage = stage or self.run_stage
        return random.sample(list(self._enemy_pool_for_stage(current_stage)), 3)

    def _reset_run_progress(self) -> None:
        self.run_stage = 1
        self.run_bonuses = {reward_id: 0 for reward_id in self.run_rewards}
        self.active_doctrine_id = None
        self.route_reroll_charges = 0
        self.reward_option_ids = []
        self.selected_reward_id = None
        self.route_option_ids = []
        self.route_event_by_route_id = {}
        self.route_node_by_route_id = {}
        self.node_follow_up_by_route_id = {}
        self.selected_route_id = None
        self.current_route_id = None
        self.current_route_event = None
        self.current_route_node = None
        self.current_node_follow_up = None
        self.pending_red_ids = []
        self.pending_stage_penalty = None
        self.active_stage_penalty = None
        self.last_penalty_summary = None
        self.last_node_summary = None
        self.objective_failure_penalty_applied = False
        self.last_battle_recap = None
        self.run_history = []
        self.run_summary = None
        self.current_objective = None
        self.last_objective_summary = None
        self.objective_bonus_applied = False
        self.finale_banner_title = None
        self.finale_banner_subtitle = None
        self.finale_banner_timer = 0.0
        self.battle_intro_card = None
        self.selected_red_ids = self._random_enemy_lineup(self.run_stage)

    def _reset_battle_stats(self) -> None:
        self.battle_stats = {
            "blue_damage": 0,
            "red_damage": 0,
            "blue_kills": 0,
            "red_kills": 0,
        }

    def _run_bonus_lines(self) -> list[str]:
        lines: list[str] = []
        for reward_id, stacks in self.run_bonuses.items():
            if stacks <= 0:
                continue
            reward = self.run_rewards[reward_id]
            suffix = f" x{stacks}" if stacks > 1 else ""
            lines.append(f"{reward.name}{suffix}")
        return lines or ["아직 강화 없음"]

    def _prepare_reward_phase(self) -> None:
        available_ids = list(self.run_rewards)
        self.reward_option_ids = random.sample(available_ids, 3)
        self.selected_reward_id = None
        self.battle_intro_card = None
        self.pending_red_ids = self._random_enemy_lineup(self.run_stage + 1)
        self.current_route_id = None
        self.current_route_event = None
        self.current_route_node = None
        self.current_node_follow_up = None
        self.active_stage_penalty = None
        self.current_objective = None
        self.screen_mode = "reward"
        objective_line = self.last_objective_summary
        penalty_line = self.last_penalty_summary
        node_line = self.last_node_summary
        if objective_line and penalty_line and node_line:
            self.selection_message = f"{objective_line} · {node_line} · {penalty_line} · 보상 하나를 고르세요."
        elif objective_line and penalty_line:
            self.selection_message = f"{objective_line} · {penalty_line} · 보상 하나를 고르세요."
        elif objective_line and node_line:
            self.selection_message = f"{objective_line} · {node_line} · 보상 하나를 고르세요."
        elif penalty_line and node_line:
            self.selection_message = f"{node_line} · {penalty_line} · 보상 하나를 고르세요."
        elif objective_line is not None:
            self.selection_message = f"{objective_line} · 보상 하나를 고르세요."
        elif node_line is not None:
            self.selection_message = f"{node_line} · 보상 하나를 고르세요."
        elif penalty_line is not None:
            self.selection_message = f"{penalty_line} · 보상 하나를 고르세요."
        else:
            self.selection_message = "보상 하나를 고른 뒤 다음 전투로 넘어가세요."

    def _roll_route_choices(self) -> None:
        self.route_option_ids = random.sample(list(self.route_options), 3)
        node_ids = random.sample(list(RUN_NODE_TEMPLATES), len(self.route_option_ids))
        self.route_event_by_route_id = {
            route_id: self._roll_route_event(route_id)
            for route_id in self.route_option_ids
        }
        self.route_node_by_route_id = {
            route_id: self._roll_route_node(node_id)
            for route_id, node_id in zip(self.route_option_ids, node_ids)
        }
        self.node_follow_up_by_route_id = {
            route_id: self._roll_node_follow_up(self.route_node_by_route_id[route_id].id)
            for route_id in self.route_option_ids
        }
        self.selected_route_id = None

    def _prepare_route_phase(self) -> None:
        self._roll_route_choices()
        self.current_objective = None
        self.screen_mode = "route"
        if self.pending_stage_penalty is not None:
            self.selection_message = f"전투 요약을 보고 경로를 고르세요. 예약 페널티: {self.pending_stage_penalty.description}"
        else:
            self.selection_message = "전투 요약을 확인하고 다음 경로 하나를 선택하세요."

    def _reroll_route_choices(self) -> None:
        if self.route_reroll_charges <= 0:
            self.selection_message = "남은 경로 재추첨이 없습니다."
            self.audio.play("reset")
            return
        self.route_reroll_charges -= 1
        self._roll_route_choices()
        self.selection_message = f"경로를 다시 정찰했습니다. 남은 재추첨 {self.route_reroll_charges}회."
        self.audio.play("ui-confirm")

    def _select_route(self, route_id: str) -> None:
        if route_id not in self.route_option_ids:
            return
        self.selected_route_id = route_id
        route_event = self.route_event_by_route_id.get(route_id)
        route_node = self.route_node_by_route_id.get(route_id)
        node_follow_up = self.node_follow_up_by_route_id.get(route_id)
        node_line = "" if route_node is None else f" · 노드 {route_node.name}"
        follow_up_line = "" if node_follow_up is None else f" · 후속 {node_follow_up.name}"
        event_line = "" if route_event is None else f" · 이벤트 {route_event.name}"
        penalty_line = ""
        if route_node is not None and route_node.clears_pending_penalty and self.pending_stage_penalty is not None:
            penalty_line = " · 예약 페널티 해제"
        self.selection_message = f"{self.route_options[route_id].name} 선택{node_line}{follow_up_line}{event_line}{penalty_line}. 다음 전투 배치를 시작할 수 있습니다."
        self.audio.play("ui-confirm")

    def _advance_after_route(self) -> None:
        if self.selected_route_id is None:
            self.selection_message = "먼저 다음 경로 하나를 선택해야 합니다."
            self.audio.play("reset")
            return
        self.current_route_id = self.selected_route_id
        self.current_route_event = self.route_event_by_route_id.get(self.current_route_id)
        self.current_route_node = self.route_node_by_route_id.get(self.current_route_id)
        self.current_node_follow_up = self.node_follow_up_by_route_id.get(self.current_route_id)
        cleared_penalty = self.current_route_node is not None and self.current_route_node.clears_pending_penalty
        self.active_stage_penalty = None if cleared_penalty else self.pending_stage_penalty
        self.pending_stage_penalty = None
        self.route_option_ids = []
        self.route_event_by_route_id = {}
        self.route_node_by_route_id = {}
        self.node_follow_up_by_route_id = {}
        self.selected_route_id = None
        self._seed_deployment()
        self.screen_mode = "deploy"
        route_name = self.route_options[self.current_route_id].name
        node_line = "" if self.current_route_node is None else f" · 노드 {self.current_route_node.name}"
        follow_up_line = "" if self.current_node_follow_up is None else f" · 후속 {self.current_node_follow_up.name}"
        event_line = "" if self.current_route_event is None else f" · 이벤트 {self.current_route_event.name}"
        penalty_line = "" if self.active_stage_penalty is None else f" · 주의 {self.active_stage_penalty.name}"
        rest_line = " · 예약 페널티 정리" if cleared_penalty else ""
        self.selection_message = f"{self._current_stage_label()} · {route_name}{node_line}{follow_up_line}{event_line}{penalty_line}{rest_line}. 시작 위치를 다시 배치하세요."
        self.audio.play("ui-confirm")

    def _select_reward(self, reward_id: str) -> None:
        if reward_id not in self.reward_option_ids:
            return
        self.selected_reward_id = reward_id
        self.selection_message = f"{self.run_rewards[reward_id].name} 선택. 다음 전투 준비가 완료되었습니다."
        self.audio.play("ui-confirm")

    def _apply_selected_reward(self) -> None:
        if self.selected_reward_id is None:
            return
        self.run_bonuses[self.selected_reward_id] += 1

    def _start_run_with_current_lineup(self) -> None:
        if len(self.selected_blue_ids) != 3:
            self.selected_blue_ids = list(DEFAULT_BLUE_IDS)
        self._reset_run_progress()
        self._activate_selected_doctrine()
        self.controller = None
        self.last_active_id = None
        self.selected_deploy_champion_id = None
        self._seed_deployment()
        self.screen_mode = "deploy"
        doctrine = self._active_doctrine()
        doctrine_line = f" · 교리 {doctrine.name}" if doctrine is not None else ""
        self.selection_message = f"{self._current_stage_label()} 시작 위치를 조정하세요{doctrine_line}."
        self.audio.play("ui-confirm")

    def _advance_after_reward(self) -> None:
        if self.selected_reward_id is None:
            self.selection_message = "먼저 전투 보상 하나를 선택해야 합니다."
            self.audio.play("reset")
            return
        self._apply_selected_reward()
        self.run_stage = min(RUN_STAGE_COUNT, self.run_stage + 1)
        self.selected_red_ids = list(self.pending_red_ids or self._random_enemy_lineup(self.run_stage))
        self.pending_red_ids = []
        self.reward_option_ids = []
        self.selected_reward_id = None
        self.last_penalty_summary = None
        self.last_node_summary = None
        self._prepare_route_phase()

    def _build_battle_recap(self, result_label: str) -> BattleRecap | None:
        if self.controller is None:
            return None
        highlight = self.controller.state.log[0] if self.controller.state.log else "전투 종료"
        return BattleRecap(
            stage_label=self._current_stage_label(),
            result_label=result_label,
            rounds=self.controller.state.round,
            blue_damage=self.battle_stats["blue_damage"],
            red_damage=self.battle_stats["red_damage"],
            blue_kills=self.battle_stats["blue_kills"],
            red_kills=self.battle_stats["red_kills"],
            highlight=highlight,
            objective_summary=self.last_objective_summary or self._summarize_current_objective(),
            route_node_summary=self._current_route_node_summary(),
            route_event_summary=self._current_route_event_summary(),
            penalty_summary=self.last_penalty_summary or self._active_stage_penalty_summary(),
        )

    def _current_lineup_label(self) -> str:
        return " · ".join(BLUEPRINTS_BY_ID[champion_id].name for champion_id in self.selected_blue_ids)

    def _best_reward_line(self) -> str:
        active_rewards = [(reward_id, stacks) for reward_id, stacks in self.run_bonuses.items() if stacks > 0]
        if not active_rewards:
            return "주요 강화 없음"
        reward_id, stacks = max(active_rewards, key=lambda item: (item[1], self.run_rewards[item[0]].name))
        reward_name = self.run_rewards[reward_id].name
        suffix = f" x{stacks}" if stacks > 1 else ""
        return f"{reward_name}{suffix}"

    def _build_run_recommendation(
        self,
        result_label: str,
        recaps: list[BattleRecap],
        total_blue_damage: int,
        total_red_damage: int,
    ) -> str:
        objective_failures = sum(1 for recap in recaps if recap.objective_summary and "실패" in recap.objective_summary)
        if result_label == "원정 성공":
            if objective_failures == 0 and total_red_damage <= max(45, total_blue_damage // 2):
                return "깔끔한 완주였습니다. 같은 조합으로 더 공격적인 경로와 정예 수배 노드를 노려볼 만합니다."
            if self._best_reward_line() != "주요 강화 없음":
                return f"{self._best_reward_line()} 빌드가 잘 맞았습니다. 같은 조합으로 다른 경로를 타며 확장해보세요."
            return "완주는 했지만 빌드 여지는 남아 있습니다. 같은 조합 재도전이나 새 조합 실험 둘 다 좋습니다."
        if self.run_stage == 1:
            return "정찰전에서 끊겼습니다. 브라움·레오나 같은 전열과 기절 연계를 늘리면 안정감이 확 올라갑니다."
        if total_red_damage > total_blue_damage + 25:
            return "받는 피해가 컸습니다. 보급로, 전장 보급, 수호 문장처럼 생존 보강부터 챙기는 편이 좋습니다."
        if total_blue_damage < 70:
            return "화력이 부족했습니다. 날 선 무기, 룬 회랑, 원거리 압박 조합을 더 적극적으로 노려보세요."
        if objective_failures:
            return "경로 목표를 여러 번 놓쳤습니다. 다음 런에서는 조합과 목표가 맞는 경로만 골라 효율을 높이세요."
        return "조합은 나쁘지 않았습니다. 같은 조합으로 바로 한 판 더 돌리면서 경로 선택만 더 공격적으로 조정해보세요."

    def _build_run_summary(self, result_label: str) -> RunSummary:
        recaps = list(self.run_history)
        total_rounds = sum(recap.rounds for recap in recaps)
        total_blue_damage = sum(recap.blue_damage for recap in recaps)
        total_red_damage = sum(recap.red_damage for recap in recaps)
        total_blue_kills = sum(recap.blue_kills for recap in recaps)
        total_red_kills = sum(recap.red_kills for recap in recaps)
        stage_label = "결전 완주" if result_label == "원정 성공" else f"{self._current_stage_label()}에서 원정 종료"
        build_lines: list[str] = []
        active_doctrine = self._active_doctrine()
        if active_doctrine is not None:
            build_lines.append(f"교리 · {active_doctrine.name}")
        for line in self._run_bonus_lines()[:3]:
            build_lines.append(f"강화 · {line}")
        if recaps:
            last_recap = recaps[-1]
            if last_recap.route_node_summary:
                build_lines.append(f"노드 · {last_recap.route_node_summary}")
            if last_recap.route_event_summary:
                build_lines.append(f"이벤트 · {last_recap.route_event_summary}")
            if last_recap.objective_summary:
                build_lines.append(f"목표 · {last_recap.objective_summary}")
        build_lines = build_lines[:5]
        return RunSummary(
            result_label=result_label,
            stage_label=stage_label,
            lineup_label=self._current_lineup_label(),
            total_rounds=total_rounds,
            total_blue_damage=total_blue_damage,
            total_red_damage=total_red_damage,
            total_blue_kills=total_blue_kills,
            total_red_kills=total_red_kills,
            build_lines=build_lines,
            best_reward_line=self._best_reward_line(),
            recommendation=self._build_run_recommendation(result_label, recaps, total_blue_damage, total_red_damage),
            recap_entries=recaps,
            history_overview_lines=[],
            history_comparison_lines=[],
            unlock_lines=[],
        )

    def _record_battle_recap(self, result_label: str) -> BattleRecap | None:
        recap = self._build_battle_recap(result_label)
        self.last_battle_recap = recap
        if recap is not None:
            self.run_history.append(recap)
        return recap

    def _enter_run_summary(self, result_label: str) -> None:
        self.run_summary = self._build_run_summary(result_label)
        history_summary = self.history_store.record_summary(self.run_summary, stage_number=self.run_stage)
        self.run_summary.history_overview_lines = history_summary.overview_lines
        self.run_summary.history_comparison_lines = history_summary.comparison_lines
        self.run_summary.unlock_lines = history_summary.unlock_lines
        self.battle_intro_card = None
        self.screen_mode = "summary"
        self.mode = "move"
        self.finale_banner_title = None
        self.finale_banner_subtitle = None
        self.finale_banner_timer = 0.0
        self.selection_message = self.run_summary.recommendation

    def _roll_route_event(self, route_id: str) -> RouteEvent:
        template = random.choice(ROUTE_EVENT_TEMPLATES[route_id])
        return RouteEvent(
            id=template["id"],
            route_id=route_id,
            name=template["name"],
            description=template["description"],
            effect_label=template["effect_label"],
            stage_modifiers=dict(template["stage_modifiers"]),
            failure_penalty_name=template["failure_penalty_name"],
            failure_penalty_label=template["failure_penalty_label"],
            penalty_modifiers=dict(template["penalty_modifiers"]),
        )

    def _roll_route_node(self, node_id: str) -> RunNode:
        template = RUN_NODE_TEMPLATES[node_id]
        victory_reward_id = None
        victory_reward_label = None
        effect_label = template["effect_label"]
        if node_id == "elite-contract":
            victory_reward_id = random.choice(list(self.run_rewards))
            victory_reward_label = f"{self.run_rewards[victory_reward_id].name} +1"
            effect_label = f"적 정예 +1 · 승리 시 {victory_reward_label}"
        return RunNode(
            id=node_id,
            name=template["name"],
            category=template["category"],
            description=template["description"],
            effect_label=effect_label,
            stage_modifiers=dict(template["stage_modifiers"]),
            event_modifier_scale=template.get("event_modifier_scale", 1),
            penalty_modifier_scale=template.get("penalty_modifier_scale", 1),
            clears_pending_penalty=template.get("clears_pending_penalty", False),
            extra_elites=template.get("extra_elites", 0),
            victory_reward_id=victory_reward_id,
            victory_reward_label=victory_reward_label,
        )

    def _roll_node_follow_up(self, node_id: str) -> NodeFollowUp:
        template = random.choice(NODE_FOLLOW_UP_TEMPLATES[node_id])
        return NodeFollowUp(
            id=template["id"],
            node_id=node_id,
            name=template["name"],
            description=template["description"],
            effect_label=template["effect_label"],
            stage_modifiers=dict(template["stage_modifiers"]),
        )

    def _scale_modifiers(self, modifiers: dict[str, int], scale: int) -> dict[str, int]:
        if scale == 1:
            return dict(modifiers)
        return {key: value * scale for key, value in modifiers.items()}

    def _modifier_summary(self, modifiers: dict[str, int]) -> str:
        lines = []
        for modifier_id in MODIFIER_LABEL_BY_ID:
            value = modifiers.get(modifier_id)
            if not value:
                continue
            lines.append(f"{MODIFIER_LABEL_BY_ID[modifier_id]} {value:+d}")
        return " · ".join(lines) if lines else "변화 없음"

    def _route_event_stage_modifiers(self, route_event: RouteEvent | None, route_node: RunNode | None) -> dict[str, int]:
        if route_event is None:
            return {}
        scale = route_node.event_modifier_scale if route_node is not None else 1
        return self._scale_modifiers(route_event.stage_modifiers, scale)

    def _route_event_penalty_modifiers(self, route_event: RouteEvent | None, route_node: RunNode | None) -> dict[str, int]:
        if route_event is None:
            return {}
        scale = route_node.penalty_modifier_scale if route_node is not None else 1
        return self._scale_modifiers(route_event.penalty_modifiers, scale)

    def _route_event_effect_label(self, route_event: RouteEvent | None, route_node: RunNode | None) -> str | None:
        if route_event is None:
            return None
        if route_node is None or route_node.event_modifier_scale == 1:
            return route_event.effect_label
        return self._modifier_summary(self._route_event_stage_modifiers(route_event, route_node))

    def _route_event_penalty_label(self, route_event: RouteEvent | None, route_node: RunNode | None) -> str | None:
        if route_event is None:
            return None
        if route_node is None or route_node.penalty_modifier_scale == 1:
            return route_event.failure_penalty_label
        return self._modifier_summary(self._route_event_penalty_modifiers(route_event, route_node))

    def _current_route_node_summary(self) -> str | None:
        if self.current_route_node is None:
            return None
        effect_label = self._node_effect_preview_label(self.current_route_node, self.current_node_follow_up)
        return f"{self.current_route_node.name} · {effect_label}"

    def _node_effect_preview_label(self, node: RunNode | None, follow_up: NodeFollowUp | None) -> str:
        if node is None:
            return ""
        if follow_up is None:
            return node.effect_label
        return f"{node.effect_label} / 후속 {follow_up.name}: {follow_up.effect_label}"

    def _current_route_event_summary(self) -> str | None:
        if self.current_route_event is None:
            return None
        effect_label = self._route_event_effect_label(self.current_route_event, self.current_route_node)
        return f"{self.current_route_event.name} · {effect_label}"

    def _active_stage_penalty_summary(self) -> str | None:
        if self.active_stage_penalty is None:
            return None
        return f"{self.active_stage_penalty.name} · {self.active_stage_penalty.description}"

    def _stage_modifier_total(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        sources = [
            ROUTE_BONUSES.get(self.current_route_id or "", {}),
            self._route_event_stage_modifiers(self.current_route_event, self.current_route_node),
            self.current_route_node.stage_modifiers if self.current_route_node is not None else {},
            self.current_node_follow_up.stage_modifiers if self.current_node_follow_up is not None else {},
            self.active_stage_penalty.modifiers if self.active_stage_penalty is not None else {},
        ]
        for source in sources:
            for key, value in source.items():
                totals[key] = totals.get(key, 0) + value
        return totals

    def _current_boss_id(self) -> str | None:
        return self._boss_enemy_id_for_stage(lineup=self.selected_red_ids)

    def _current_boss_unit(self):
        if self.controller is None:
            return None
        return next((unit for unit in self.controller.units if unit.team == "red" and unit.is_boss), None)

    def _trigger_finale_banner(self, title: str, subtitle: str, color: tuple[int, int, int]) -> None:
        self.finale_banner_title = title
        self.finale_banner_subtitle = subtitle
        self.finale_banner_color = color
        self.finale_banner_timer = 1.75

    def _current_boss_pressure_preview(
        self,
    ) -> tuple[list[GridPos], tuple[int, int, int], str | None, str | None, bool]:
        if self.controller is None or self.run_stage != RUN_STAGE_COUNT:
            return [], (236, 126, 90), None, None, False
        boss = self._current_boss_unit()
        if boss is None:
            return [], (236, 126, 90), None, None, False
        boss_profile = self._boss_profile_for_stage(lineup=[unit.id for unit in self.controller.units if unit.team == "red"])
        if boss_profile is None:
            return [], (236, 126, 90), None, None, boss.boss_phase_triggered
        color = (236, 126, 90) if boss_profile.id == "warlord" else (126, 154, 236)
        return (
            self.controller.boss_pressure_tiles(boss.id),
            color,
            boss_profile.surge_name,
            boss_profile.surge_description,
            boss.boss_phase_triggered,
        )

    def _trigger_battle_intro(self) -> None:
        detail_lines: list[str] = []
        color = (108, 224, 203)
        title = f"{self._current_stage_label()} 시작"
        subtitle = "전술 상황을 확인하고 첫 턴 계획을 세우세요."

        if self.current_route_node is not None:
            title = f"{self.current_route_node.name} 진입"
            subtitle = self.current_route_node.description
            detail_lines.append(f"노드 효과 · {self.current_route_node.effect_label}")
            if self.current_route_node.id == "rest-camp":
                color = (128, 214, 174)
            elif self.current_route_node.id == "event-surge":
                color = (123, 151, 236)
            elif self.current_route_node.id == "elite-contract":
                color = (236, 126, 90)
        if self.current_node_follow_up is not None:
            detail_lines.append(f"후속 · {self.current_node_follow_up.name} · {self.current_node_follow_up.effect_label}")
        if self.current_route_event is not None:
            detail_lines.append(f"이벤트 · {self.current_route_event.name} · {self._route_event_effect_label(self.current_route_event, self.current_route_node)}")
        if self.active_stage_penalty is not None:
            detail_lines.append(f"주의 · {self.active_stage_penalty.description}")
        if self.current_objective is not None:
            objective_text = self.current_objective.description.replace("목표: ", "")
            if self.current_objective.is_finale:
                boss_profile = self._boss_profile_for_stage()
                finale_variant = self._finale_variant_for_stage()
                color = (236, 126, 90)
                title = finale_variant.name if finale_variant is not None else "결전 개시"
                profile_text = boss_profile.name if boss_profile is not None else "보스 패턴 미확인"
                subtitle = f"{profile_text} · {objective_text}"
                finale_lines = [f"목표 · {objective_text}"]
                if boss_profile is not None:
                    finale_lines.insert(0, f"각성 규칙 · {boss_profile.surge_name}")
                if self.current_route_node is not None:
                    finale_lines.append(f"노드 효과 · {self.current_route_node.effect_label}")
                elif self.current_route_event is not None:
                    finale_lines.append(f"이벤트 · {self._route_event_effect_label(self.current_route_event, self.current_route_node)}")
                if self.active_stage_penalty is not None and len(finale_lines) < 3:
                    finale_lines.append(f"주의 · {self.active_stage_penalty.description}")
                detail_lines = finale_lines
            else:
                detail_lines.append(f"목표 · {objective_text}")
        self.battle_intro_card = BattleIntroCard(title=title, subtitle=subtitle, detail_lines=detail_lines[:3], color=color)

    def _preview_battle_objective(
        self,
        *,
        stage: int | None = None,
        route_id: str | None = None,
        enemy_ids: list[str] | None = None,
    ) -> BattleObjective | None:
        resolved_stage = stage or self.run_stage
        resolved_route_id = route_id if route_id is not None else self.current_route_id
        resolved_enemy_ids = enemy_ids if enemy_ids is not None else self.selected_red_ids
        if resolved_stage == RUN_STAGE_COUNT:
            boss_id = self._boss_enemy_id_for_stage(stage=resolved_stage, lineup=resolved_enemy_ids)
            finale_variant = self._finale_variant_for_stage(stage=resolved_stage, lineup=resolved_enemy_ids)
            if boss_id is not None and finale_variant is not None:
                return BattleObjective(
                    route_id="boss-finale",
                    name=finale_variant.objective_name,
                    description=finale_variant.objective_description,
                    kind="occupy_tile",
                    target=finale_variant.objective_target,
                    reward_id="bonus-shield",
                    reward_label=finale_variant.reward_label,
                    objective_tiles=finale_variant.objective_tiles,
                    round_limit=finale_variant.round_limit,
                    is_finale=True,
                    boss_id=boss_id,
                    success_label=finale_variant.success_label,
                    failure_label=finale_variant.failure_label,
                )
        if resolved_route_id is None:
            return None
        definition = ROUTE_OBJECTIVES.get(resolved_route_id)
        if definition is None:
            return None
        reward_id = definition["reward_id"]
        objective_tiles = tuple(ROUTE_OBJECTIVE_TILES.get(resolved_route_id, {}).get(resolved_stage, ()))
        return BattleObjective(
            route_id=resolved_route_id,
            name=definition["name"],
            description=self.route_options[resolved_route_id].description,
            kind=definition["kind"],
            target=definition.get("target", 1),
            reward_id=reward_id,
            reward_label=f"{self.run_rewards[reward_id].name} +1",
            objective_tiles=objective_tiles,
            terrain_id=definition.get("terrain_id"),
            round_limit=definition.get("round_limit"),
        )

    def _build_battle_objective(self) -> BattleObjective | None:
        return self._preview_battle_objective()

    def _objective_focus_tiles(self) -> tuple[GridPos, ...]:
        objective = self.current_objective
        if objective is None or objective.completed or objective.failed:
            return ()
        if objective.kind == "occupy_tile":
            return objective.objective_tiles
        if objective.kind == "move_on_terrain" and objective.terrain_id is not None:
            terrain_tiles = self.controller.terrain_tiles if self.controller is not None else self._terrain_tiles_for_stage()
            return tuple(tile for tile, terrain_id in terrain_tiles.items() if terrain_id == objective.terrain_id)
        return ()

    def _sync_controller_objective_focus(self) -> None:
        if self.controller is None:
            return
        self.controller.set_objective_tiles(self._objective_focus_tiles())

    def _summarize_current_objective(self) -> str | None:
        if self.current_objective is None:
            return None
        objective = self.current_objective
        if objective.completed:
            return f"{objective.name} 달성 · {objective.success_label or objective.reward_label}"
        if objective.failed:
            return f"{objective.name} 실패 · {objective.failure_label or '목표 미달성'}"
        return f"{objective.name} 미달성 {objective.progress}/{objective.target}"

    def _complete_objective(self) -> None:
        if self.current_objective is None or self.current_objective.completed:
            return
        self.current_objective.completed = True
        self.last_objective_summary = self._summarize_current_objective()
        summary_label = self.current_objective.success_label or self.current_objective.reward_label
        self.status_text = f"{self.current_objective.name} 달성. {summary_label} 확보 예정."
        if self.current_objective.is_finale:
            self._trigger_finale_banner("결전 목표 달성", f"{summary_label} 예약", (120, 224, 184))
        self.audio.play("shield")

    def _objective_failure_penalty_preview(self) -> str | None:
        if self.current_route_event is None or not self.current_route_event.penalty_modifiers:
            return None
        return self._route_event_penalty_label(self.current_route_event, self.current_route_node)

    def _refresh_objective_failure(self) -> None:
        if self.current_objective is None or self.current_objective.completed or self.current_objective.failed:
            return
        if self.current_objective.round_limit is not None and self.controller is not None and self.controller.state.round > self.current_objective.round_limit:
            self.current_objective.failed = True
            self.last_objective_summary = self._summarize_current_objective()
            penalty_preview = self._objective_failure_penalty_preview()
            if penalty_preview:
                self.status_text = f"{self.current_objective.name} 실패. 승리해도 다음 전투에 {penalty_preview}"
            elif self.current_objective.is_finale:
                self.status_text = f"{self.current_objective.name} 실패. 보스 각성이 강화됩니다."
                self._trigger_finale_banner("결전 목표 실패", self.current_objective.failure_label or "보스 각성 증폭", (236, 126, 90))
            self.audio.play("reset")

    def _queue_objective_failure_penalty(self) -> str | None:
        if (
            self.current_objective is None
            or not self.current_objective.failed
            or self.current_route_event is None
            or self.objective_failure_penalty_applied
            or self.run_stage >= RUN_STAGE_COUNT
        ):
            return None
        if not self.current_route_event.penalty_modifiers:
            return None
        penalty_modifiers = self._route_event_penalty_modifiers(self.current_route_event, self.current_route_node)
        penalty_label = self._route_event_penalty_label(self.current_route_event, self.current_route_node) or self.current_route_event.failure_penalty_label
        self.pending_stage_penalty = StageModifier(
            name=self.current_route_event.failure_penalty_name,
            description=penalty_label,
            modifiers=penalty_modifiers,
        )
        self.last_penalty_summary = f"목표 실패 페널티 예약 · {self.pending_stage_penalty.description}"
        self.objective_failure_penalty_applied = True
        return self.last_penalty_summary

    def _update_battle_objective_from_result(self, result: TacticalActionResult) -> None:
        if self.controller is None or self.current_objective is None:
            return

        objective = self.current_objective
        actor = self.controller.get_unit(result.actor_id)
        if actor is None:
            return

        if objective.kind == "kill_before_round" and actor.team == "blue" and result.kind in {"basic", "special"}:
            if objective.round_limit is None or self.controller.state.round <= objective.round_limit:
                defeated_count = sum(1 for impact in result.impacts if impact.defeated)
                if defeated_count:
                    objective.progress = min(objective.target, objective.progress + defeated_count)
                    if objective.progress >= objective.target:
                        self._complete_objective()

        if actor.team != "blue":
            self._refresh_objective_failure()
            return

        if result.kind == "move":
            destination = result.end
            if objective.kind == "occupy_tile" and destination in objective.objective_tiles:
                objective.progress = min(objective.target, objective.progress + 1)
            elif objective.kind == "move_on_terrain" and destination is not None and self.controller.terrain_tiles.get(destination) == objective.terrain_id:
                objective.progress = min(objective.target, objective.progress + 1)

        if objective.progress >= objective.target and not objective.completed:
            self._complete_objective()
        self._refresh_objective_failure()
        self._sync_controller_objective_focus()

    def _apply_completed_objective_bonus(self) -> str | None:
        if self.current_objective is None:
            self.last_objective_summary = None
            return None
        self.last_objective_summary = self._summarize_current_objective()
        if self.current_objective.is_finale:
            return self.last_objective_summary
        if not self.current_objective.completed or self.objective_bonus_applied:
            return self.last_objective_summary
        self.run_bonuses[self.current_objective.reward_id] += 1
        self.objective_bonus_applied = True
        self.last_objective_summary = self._summarize_current_objective()
        return self.last_objective_summary

    def _resolve_finale_phase_state(self) -> None:
        if self.controller is None or self.current_objective is None or not self.current_objective.is_finale:
            return
        boss = self._current_boss_unit()
        if boss is None or not boss.boss_phase_triggered:
            return
        if not self.current_objective.completed and not self.current_objective.failed:
            self.current_objective.failed = True
            self.last_objective_summary = self._summarize_current_objective()
        else:
            self.last_objective_summary = self._summarize_current_objective()
        anchor = self.unit_visual_positions.get(boss.id)
        if self.current_objective.completed:
            boss.shield = max(0, boss.shield - 10)
            boss.speed = max(1, boss.speed - 1)
            if boss.boss_profile_id == "warlord":
                boss.move_range = max(1, boss.move_range - 1)
            elif boss.boss_profile_id == "spellstorm":
                boss.special_ability = replace(boss.special_ability, cast_range=max(1, boss.special_ability.cast_range - 1))
            self.controller._push_log(f"{self.current_objective.name} 성공 · {boss.name}의 결전 각성이 약화됨.")
            self.status_text = f"{self.current_objective.name} 성공. {boss.name}의 결전 각성이 약화됩니다."
            self._trigger_finale_banner(f"{self.current_objective.name} 성공", f"{boss.name} 각성 약화", (120, 224, 184))
            if anchor is not None:
                self.floaters.append(FloatingText(anchor.x, anchor.y - 132, "각성 약화", (120, 224, 184), lifetime=1.0))
        else:
            boss.shield += 8
            boss.speed += 1
            if boss.boss_profile_id == "warlord":
                boss.move_range += 1
            elif boss.boss_profile_id == "spellstorm":
                boss.special_ability = replace(boss.special_ability, cast_range=boss.special_ability.cast_range + 1)
            self.controller._push_log(f"{self.current_objective.name} 실패 · {boss.name}의 결전 각성이 증폭됨.")
            self.status_text = f"{self.current_objective.name} 실패. {boss.name}의 결전 각성이 증폭됩니다."
            self._trigger_finale_banner("결전 각성 증폭", f"{boss.name} 각성 강화", (236, 126, 90))
            if anchor is not None:
                self.floaters.append(FloatingText(anchor.x, anchor.y - 132, "각성 강화", (236, 126, 90), lifetime=1.0))

    def _apply_route_node_victory_bonus(self) -> str | None:
        if self.current_route_node is None or self.current_route_node.victory_reward_id is None:
            self.last_node_summary = None
            return None
        self.run_bonuses[self.current_route_node.victory_reward_id] += 1
        reward_label = self.current_route_node.victory_reward_label or f"{self.run_rewards[self.current_route_node.victory_reward_id].name} +1"
        self.last_node_summary = f"{self.current_route_node.name} 보상 · {reward_label}"
        return self.last_node_summary

    def _seed_deployment(self) -> None:
        self.deploy_assignments = {
            tile: champion_id
            for tile, champion_id in zip(DEFAULT_BLUE_DEPLOY_TILES, self.selected_blue_ids)
        }
        enemy_ids = list(self.selected_red_ids)
        random.shuffle(enemy_ids)
        self.red_deploy_assignments = {
            tile: champion_id
            for tile, champion_id in zip(DEFAULT_RED_DEPLOY_TILES, enemy_ids)
        }
        self.selected_deploy_champion_id = self.selected_blue_ids[0] if self.selected_blue_ids else None

    def _build_controller_from_current_setup(self) -> TacticsController:
        blue_positions = [self._tile_for_deployed_champion(champion_id, self.deploy_assignments) for champion_id in self.selected_blue_ids]
        red_positions = [self._tile_for_deployed_champion(champion_id, self.red_deploy_assignments) for champion_id in self.selected_red_ids]
        return TacticsController(
            self.selected_blue_ids,
            self.selected_red_ids,
            blue_positions,
            red_positions,
            terrain_tiles=self._terrain_tiles_for_stage(enemy_ids=self.selected_red_ids),
            elite_unit_ids=self._elite_enemy_ids_for_stage(),
            objective_tiles=self._objective_focus_tiles(),
            blocked_tiles=self._blocked_tiles_for_stage(enemy_ids=self.selected_red_ids),
        )

    def _attach_controller(self, controller: TacticsController) -> None:
        self._apply_run_modifiers(controller)
        self.controller = controller
        self._sync_controller_objective_focus()
        boss_unit = next((unit for unit in controller.units if unit.team == "red" and unit.is_boss), None)
        if boss_unit is not None:
            boss_profile = self._boss_profile_for_stage(lineup=[unit.id for unit in controller.units if unit.team == "red"])
            finale_variant = self._finale_variant_for_stage(lineup=[unit.id for unit in controller.units if unit.team == "red"])
            controller._push_log(f"{boss_unit.name} 보스 개체 등장 · 체력 절반 이하 시 결전 각성.")
            if boss_profile is not None:
                controller._push_log(f"보스 패턴 · {boss_profile.name} · {boss_profile.phase_description}.")
            if finale_variant is not None:
                controller._push_log(f"결전 지형 · {finale_variant.name} · {finale_variant.description}.")
            if self.run_stage == RUN_STAGE_COUNT and self.current_objective is not None and self.current_objective.is_finale:
                subtitle = f"{boss_unit.name} · {self.current_objective.description.replace('목표: ', '')}"
                if boss_profile is not None:
                    subtitle = f"{boss_profile.name} · {subtitle}"
                self._trigger_finale_banner("결전 개시", subtitle, (236, 126, 90))
        for elite_unit in [unit for unit in controller.units if unit.team == "red" and unit.is_elite and not unit.is_boss]:
            trait = ELITE_TRAITS_BY_ID.get(elite_unit.elite_trait_id or "")
            if trait is not None:
                controller._push_log(f"{elite_unit.name} 엘리트 특성 · {trait.name}.")
        if self.current_route_node is not None:
            controller._push_log(f"{self.current_route_node.name} 적용 · {self.current_route_node.effect_label}.")
        if self.current_node_follow_up is not None:
            controller._push_log(f"{self.current_node_follow_up.name} 발동 · {self.current_node_follow_up.effect_label}.")
        if self.current_route_event is not None:
            controller._push_log(f"{self.current_route_event.name} 적용 · {self._route_event_effect_label(self.current_route_event, self.current_route_node)}.")
        self._reset_battle_stats()
        self.hit_flash = {unit.id: 0.0 for unit in controller.units}
        self.unit_visual_positions = {
            unit.id: pygame.Vector2(self._tile_center(unit.position)) for unit in controller.units
        }
        self.floaters.clear()
        self.ai_timer = 0.55
        self.last_active_id = None
        self.mode = "move"

    def _boost_damage_effects(self, ability, bonus_damage: int, *, range_bonus: int = 0):
        boosted_effects = tuple(
            replace(effect, amount=effect.amount + bonus_damage) if effect.kind == "damage" else effect
            for effect in ability.effects
        )
        return replace(ability, cast_range=ability.cast_range + range_bonus, effects=boosted_effects)

    def _apply_run_modifiers(self, controller: TacticsController) -> None:
        damage_bonus = self.run_bonuses["bonus-damage"] * 3
        hp_bonus = self.run_bonuses["bonus-hp"] * 10
        speed_bonus = self.run_bonuses["bonus-speed"] * 5
        move_bonus = self.run_bonuses["bonus-move"]
        shield_bonus = self.run_bonuses["bonus-shield"] * 12
        enemy_tier = max(0, self.run_stage - 1)
        enemy_lineup = [unit.id for unit in controller.units if unit.team == "red"]
        boss_id = self._boss_enemy_id_for_stage(lineup=enemy_lineup)
        boss_profile = self._boss_profile_for_stage(lineup=enemy_lineup)
        elite_ids = self._elite_enemy_ids_for_stage(lineup=enemy_lineup)
        stage_modifiers = self._stage_modifier_total()
        route_damage_bonus = stage_modifiers.get("blue_damage", 0)
        route_shield_bonus = stage_modifiers.get("blue_shield", 0)
        route_speed_bonus = stage_modifiers.get("blue_speed", 0)
        route_hp_bonus = stage_modifiers.get("blue_hp", 0)
        route_move_bonus = stage_modifiers.get("blue_move", 0)
        enemy_route_damage_bonus = stage_modifiers.get("enemy_damage", 0)
        enemy_route_speed_bonus = stage_modifiers.get("enemy_speed", 0)
        enemy_route_shield_bonus = stage_modifiers.get("enemy_shield", 0)
        enemy_route_hp_bonus = stage_modifiers.get("enemy_hp", 0)

        for unit in controller.units:
            if unit.team == "blue":
                unit.max_hp = max(1, unit.max_hp + hp_bonus + route_hp_bonus)
                unit.hp = unit.max_hp
                unit.speed += speed_bonus + route_speed_bonus
                unit.move_range = max(1, unit.move_range + move_bonus + route_move_bonus)
                unit.shield += shield_bonus + route_shield_bonus
                unit.basic_ability = self._boost_damage_effects(unit.basic_ability, damage_bonus + route_damage_bonus)
                unit.special_ability = self._boost_damage_effects(unit.special_ability, damage_bonus + route_damage_bonus)
            else:
                unit.max_hp = max(1, unit.max_hp + enemy_tier * 8 + enemy_route_hp_bonus)
                unit.hp = unit.max_hp
                unit.speed += enemy_tier * 2 + enemy_route_speed_bonus
                unit.shield += enemy_route_shield_bonus
                unit.basic_ability = self._boost_damage_effects(unit.basic_ability, enemy_tier * 2 + enemy_route_damage_bonus)
                unit.special_ability = self._boost_damage_effects(unit.special_ability, enemy_tier * 2 + enemy_route_damage_bonus)
                if boss_id is not None and unit.id == boss_id:
                    unit.is_boss = True
                    unit.boss_profile_id = boss_profile.id if boss_profile is not None else None
                    unit.is_elite = True
                    unit.max_hp += 36
                    unit.hp = unit.max_hp
                    unit.speed += 4
                    unit.move_range += 1
                    unit.shield += 14
                    unit.basic_ability = self._boost_damage_effects(unit.basic_ability, 6, range_bonus=1)
                    unit.special_ability = self._boost_damage_effects(unit.special_ability, 6, range_bonus=1)
                elif unit.id in elite_ids:
                    unit.is_elite = True
                    unit.elite_trait_id = self._elite_trait_id_for_enemy(unit.id)
                    unit.max_hp += 16 if self.run_stage == 2 else 24
                    unit.hp = unit.max_hp
                    unit.speed += 2
                    unit.move_range += 1 if self.run_stage == 3 else 0
                    unit.basic_ability = self._boost_damage_effects(unit.basic_ability, 3 if self.run_stage == 2 else 5)
                    unit.special_ability = self._boost_damage_effects(unit.special_ability, 3 if self.run_stage == 2 else 5)

        controller.state.turn_queue = controller._build_turn_queue()
        controller.state.active_unit_id = None
        controller._prime_next_turn()

    def _start_deploy(self) -> None:
        if len(self.selected_blue_ids) != 3:
            self.selection_message = "플레이어 팀은 정확히 3명을 선택해야 합니다."
            self.audio.play("reset")
            return
        self._reset_run_progress()
        self._activate_selected_doctrine()
        self._seed_deployment()
        self.screen_mode = "deploy"
        doctrine = self._active_doctrine()
        doctrine_line = f" · 교리 {doctrine.name}" if doctrine is not None else ""
        self.selection_message = f"{self._current_stage_label()} 시작 위치를 조정한 뒤 전투를 시작하세요{doctrine_line}."
        self.audio.play("ui-confirm")

    def _start_battle(self) -> None:
        if len(self.deploy_assignments) != 3:
            self.selection_message = "세 챔피언 모두 시작 칸에 배치해야 합니다."
            self.audio.play("reset")
            return
        self.current_objective = self._build_battle_objective()
        self.last_objective_summary = None
        self.last_node_summary = None
        self.objective_bonus_applied = False
        self.objective_failure_penalty_applied = False
        self.finale_banner_title = None
        self.finale_banner_subtitle = None
        self.finale_banner_timer = 0.0
        controller = self._build_controller_from_current_setup()
        self._attach_controller(controller)
        self._trigger_battle_intro()
        self.screen_mode = "battle"
        self.status_text = "이동할 칸을 고르거나 스킬을 선택하세요."
        self.audio.play("ui-confirm")

    def _return_to_select(self) -> None:
        self.screen_mode = "select"
        self.controller = None
        self.mode = "move"
        self.last_active_id = None
        self.selected_deploy_champion_id = None
        self.battle_intro_card = None
        self._reset_run_progress()
        self._refresh_doctrine_statuses()
        self.deploy_assignments.clear()
        self.red_deploy_assignments.clear()
        self.selection_message = "새 원정을 준비하세요. 현재 조합은 유지됩니다."
        self.audio.play("ui-select")

    def _reset_selection(self) -> None:
        self.screen_mode = "select"
        self.selected_blue_ids = list(DEFAULT_BLUE_IDS)
        self._reset_run_progress()
        self._refresh_doctrine_statuses()
        self.deploy_assignments.clear()
        self.red_deploy_assignments.clear()
        self.selected_deploy_champion_id = None
        self.selection_message = "기본 조합으로 되돌렸습니다."
        self.audio.play("reset")

    def _reset_battle(self) -> None:
        if self.controller is None:
            return
        self.current_objective = self._build_battle_objective()
        self.last_objective_summary = None
        self.objective_bonus_applied = False
        self.objective_failure_penalty_applied = False
        self.finale_banner_title = None
        self.finale_banner_subtitle = None
        self.finale_banner_timer = 0.0
        self.battle_intro_card = None
        self.controller.reset()
        self._attach_controller(self.controller)
        self.status_text = "전술 전투를 다시 시작했습니다."
        self.audio.play("reset")

    def _toggle_blue_selection(self, champion_id: str) -> None:
        blueprint = BLUEPRINTS_BY_ID[champion_id]
        if champion_id in self.selected_blue_ids:
            self.selected_blue_ids.remove(champion_id)
            self.selection_message = f"{blueprint.name} 선택을 해제했습니다."
            self.audio.play("ui-select", champion_id=champion_id)
            return

        if len(self.selected_blue_ids) >= 3:
            self.selection_message = "플레이어 팀은 3명까지만 선택할 수 있습니다."
            self.audio.play("reset")
            return

        self.selected_blue_ids.append(champion_id)
        self.selection_message = f"{blueprint.name}을(를) 플레이어 팀에 추가했습니다."
        self.audio.play("ui-confirm", champion_id=champion_id)

    def _select_doctrine(self, doctrine_id: str) -> None:
        doctrine = next((status for status in self.doctrine_statuses if status.id == doctrine_id), None)
        if doctrine is None:
            return
        if not doctrine.unlocked:
            self.selection_message = f"{doctrine.name} 잠금 · {doctrine.requirement_label} ({doctrine.progress_label})"
            self.audio.play("reset")
            return
        self.selected_doctrine_id = doctrine.id
        reroll_line = f" · 경로 재추첨 {doctrine.route_reroll_charges}회" if doctrine.route_reroll_charges else ""
        self.selection_message = f"{doctrine.name} 선택 · {doctrine.description}{reroll_line}"
        self.audio.play("ui-confirm")

    def _tile_for_deployed_champion(self, champion_id: str, assignments: dict[tuple[int, int], str]) -> tuple[int, int]:
        for tile, deployed_id in assignments.items():
            if deployed_id == champion_id:
                return tile
        raise KeyError(champion_id)

    def _move_deploy_assignment(self, tile: tuple[int, int]) -> None:
        occupant = self.deploy_assignments.get(tile)
        if self.selected_deploy_champion_id is None:
            if occupant:
                self.selected_deploy_champion_id = occupant
                self.selection_message = f"{BLUEPRINTS_BY_ID[occupant].name} 배치 칸을 바꿀 준비를 했습니다."
                self.audio.play("ui-select", champion_id=occupant)
            return

        selected_id = self.selected_deploy_champion_id
        previous_tile = self._tile_for_deployed_champion(selected_id, self.deploy_assignments)
        if previous_tile == tile:
            self.selected_deploy_champion_id = None
            self.selection_message = "배치 선택을 해제했습니다."
            self.audio.play("ui-select", champion_id=selected_id)
            return

        if occupant:
            self.deploy_assignments[previous_tile] = occupant
        else:
            self.deploy_assignments.pop(previous_tile, None)
        self.deploy_assignments[tile] = selected_id
        self.selected_deploy_champion_id = None
        self.selection_message = f"{BLUEPRINTS_BY_ID[selected_id].name}의 시작 위치를 변경했습니다."
        self.audio.play("ui-confirm", champion_id=selected_id)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_keydown(self, key: int) -> None:
        if self.screen_mode == "summary":
            if key in {pygame.K_RETURN, pygame.K_SPACE, pygame.K_r}:
                self._start_run_with_current_lineup()
                return
            if key == pygame.K_ESCAPE:
                self._return_to_select()
                return

        if self.screen_mode == "route":
            if key in {pygame.K_ESCAPE}:
                self._return_to_select()
                return
            if key == pygame.K_r:
                self._return_to_select()
                return
            if key in {pygame.K_RETURN, pygame.K_SPACE}:
                self._advance_after_route()
                return

        if self.screen_mode == "reward":
            if key in {pygame.K_ESCAPE}:
                self._return_to_select()
                return
            if key == pygame.K_r:
                self._return_to_select()
                return
            if key in {pygame.K_RETURN, pygame.K_SPACE}:
                self._advance_after_reward()
                return

        if self.screen_mode == "battle" and self.controller and self.controller.state.winner:
            if key in {pygame.K_RETURN, pygame.K_SPACE}:
                if self.controller.state.winner == "blue" and self.run_stage == RUN_STAGE_COUNT:
                    self._start_run_with_current_lineup()
                else:
                    self._return_to_select()
                return
            if key == pygame.K_r:
                if self.controller.state.winner == "blue" and self.run_stage == RUN_STAGE_COUNT:
                    self._start_run_with_current_lineup()
                else:
                    self._reset_battle()
                return
            if key == pygame.K_ESCAPE:
                self._return_to_select()
                return

        if key == pygame.K_ESCAPE:
            if self.screen_mode == "battle":
                self._return_to_select()
            elif self.screen_mode == "deploy":
                self._return_to_select()
            else:
                self.running = False
            return

        if key == pygame.K_r:
            if self.screen_mode == "battle":
                self._reset_battle()
            else:
                self._reset_selection()
            return

        if self.screen_mode == "select":
            if key in {pygame.K_RETURN, pygame.K_SPACE}:
                self._start_deploy()
            return

        if self.screen_mode == "deploy":
            if key == pygame.K_RETURN:
                self._start_battle()
            return

        if self.screen_mode == "battle" and self.battle_intro_card is not None:
            return

        if key == pygame.K_m:
            self.mode = "move"
        elif key == pygame.K_1:
            self.mode = "basic"
        elif key == pygame.K_2:
            self._choose_special_mode()
        elif key == pygame.K_e:
            self._end_turn()

    def _handle_click(self, position: tuple[int, int]) -> None:
        header_action = self.button_rects.get("header-action")
        if header_action and header_action.collidepoint(position):
            if self.screen_mode == "battle":
                self._reset_battle()
            elif self.screen_mode == "route":
                self._return_to_select()
            elif self.screen_mode == "reward":
                self._return_to_select()
            elif self.screen_mode == "summary":
                self._return_to_select()
            elif self.screen_mode == "deploy":
                self._return_to_select()
            else:
                self.running = False
            return

        if self.screen_mode == "select":
            self._handle_select_click(position)
            return

        if self.screen_mode == "reward":
            self._handle_reward_click(position)
            return

        if self.screen_mode == "route":
            self._handle_route_click(position)
            return

        if self.screen_mode == "deploy":
            self._handle_deploy_click(position)
            return

        if self.screen_mode == "summary":
            self._handle_summary_click(position)
            return

        self._handle_battle_click(position)

    def _handle_select_click(self, position: tuple[int, int]) -> None:
        if self.button_rects.get("selection-start") and self.button_rects["selection-start"].collidepoint(position):
            self._start_deploy()
            return
        if self.button_rects.get("selection-reroll") and self.button_rects["selection-reroll"].collidepoint(position):
            self.selected_red_ids = self._random_enemy_lineup()
            self.selection_message = "적 조합을 다시 섞었습니다."
            self.audio.play("ui-select")
            return
        for doctrine_id, rect in self.doctrine_card_rects.items():
            if rect.collidepoint(position):
                self._select_doctrine(doctrine_id)
                return

        for champion_id, rect in self.selection_card_rects.items():
            if rect.collidepoint(position):
                self._toggle_blue_selection(champion_id)
                return

        for index, rect in enumerate(self.selection_slot_rects):
            if rect.collidepoint(position) and index < len(self.selected_blue_ids):
                champion_id = self.selected_blue_ids.pop(index)
                self.selection_message = f"{BLUEPRINTS_BY_ID[champion_id].name} 선택을 해제했습니다."
                self.audio.play("ui-select", champion_id=champion_id)
                return

    def _handle_deploy_click(self, position: tuple[int, int]) -> None:
        if self.button_rects.get("deploy-start") and self.button_rects["deploy-start"].collidepoint(position):
            self._start_battle()
            return

        for champion_id, rect in self.deploy_roster_rects.items():
            if rect.collidepoint(position):
                self.selected_deploy_champion_id = champion_id
                self.selection_message = f"{BLUEPRINTS_BY_ID[champion_id].name}의 시작 위치를 고르세요."
                self.audio.play("ui-select", champion_id=champion_id)
                return

        tile = self._tile_from_screen(position)
        if tile and tile in DEFAULT_BLUE_DEPLOY_TILES:
            self._move_deploy_assignment(tile)

    def _handle_reward_click(self, position: tuple[int, int]) -> None:
        if self.button_rects.get("reward-next") and self.button_rects["reward-next"].collidepoint(position):
            self._advance_after_reward()
            return
        if self.button_rects.get("reward-select") and self.button_rects["reward-select"].collidepoint(position):
            self._return_to_select()
            return
        for reward_id, rect in self.reward_card_rects.items():
            if rect.collidepoint(position):
                self._select_reward(reward_id)
                return

    def _handle_route_click(self, position: tuple[int, int]) -> None:
        if self.button_rects.get("route-next") and self.button_rects["route-next"].collidepoint(position):
            self._advance_after_route()
            return
        if self.button_rects.get("route-select") and self.button_rects["route-select"].collidepoint(position):
            self._return_to_select()
            return
        if self.button_rects.get("route-reroll") and self.button_rects["route-reroll"].collidepoint(position):
            self._reroll_route_choices()
            return
        for route_id, rect in self.route_card_rects.items():
            if rect.collidepoint(position):
                self._select_route(route_id)
                return

    def _handle_summary_click(self, position: tuple[int, int]) -> None:
        rerun_rect = self.button_rects.get("summary-rerun")
        select_rect = self.button_rects.get("summary-select")
        if rerun_rect and rerun_rect.collidepoint(position):
            self._start_run_with_current_lineup()
            return
        if select_rect and select_rect.collidepoint(position):
            self._return_to_select()

    def _handle_battle_click(self, position: tuple[int, int]) -> None:
        controller = self.controller
        if controller is None:
            return

        if controller.state.winner:
            select_rect = self.button_rects.get("winner-select")
            rematch_rect = self.button_rects.get("winner-rematch")
            if select_rect and select_rect.collidepoint(position):
                self._return_to_select()
                return
            if rematch_rect and rematch_rect.collidepoint(position):
                if controller.state.winner == "blue" and self.run_stage == RUN_STAGE_COUNT:
                    self._start_run_with_current_lineup()
                else:
                    self._reset_battle()
                return
            return
        if self.battle_intro_card is not None:
            return

        active = controller.get_active_unit()
        if active is None or active.team != "blue":
            return

        for key in ("move", "basic", "special", "end"):
            rect = self.button_rects.get(key)
            if rect and rect.collidepoint(position):
                if key == "move":
                    self.mode = "move"
                    self.status_text = "도달 가능한 칸을 클릭해 이동하세요."
                elif key == "basic":
                    self.mode = "basic"
                    self.status_text = "사거리 안 적을 클릭해 기본 공격을 사용하세요."
                elif key == "special":
                    self._choose_special_mode()
                elif key == "end":
                    self._end_turn()
                return

        clicked_tile = self._tile_from_screen(position)
        if clicked_tile is None:
            return

        if self.mode == "move" and clicked_tile in controller.get_reachable_tiles():
            result = controller.move_active(clicked_tile)
            if result:
                self._apply_action_result(result)
            return

        target = self._unit_at_tile(clicked_tile)
        if target is None or target.team == active.team:
            return

        if self.mode == "basic" and target.id in controller.get_valid_targets("basic"):
            result = controller.use_basic(target.id)
            if result:
                self._apply_action_result(result)
            return

        if self.mode == "special" and target.id in controller.get_valid_targets("special"):
            result = controller.use_special(target.id)
            if result:
                self._apply_action_result(result)

    def _choose_special_mode(self) -> None:
        controller = self.controller
        if controller is None:
            return
        active = controller.get_active_unit()
        if active is None:
            return
        ability = active.special_ability
        if active.cooldowns[ability.id] > 0 or active.has_acted:
            self.status_text = "특수기는 아직 사용할 수 없습니다."
            self.audio.play("reset")
            return
        if ability.target_mode == "self":
            result = controller.use_special(active.id)
            if result:
                self._apply_action_result(result)
            return
        self.mode = "special"
        self.status_text = f"사거리 안 적을 클릭해 {ability.name}을(를) 사용하세요."

    def _end_turn(self) -> None:
        controller = self.controller
        if controller is None:
            return
        result = controller.end_turn()
        if result:
            self._apply_action_result(result)

    def _update(self, dt: float) -> None:
        if self.finale_banner_timer > 0:
            self.finale_banner_timer = max(0.0, self.finale_banner_timer - dt)
        if self.battle_intro_card is not None:
            self.battle_intro_card.timer = max(0.0, self.battle_intro_card.timer - dt)
            if self.battle_intro_card.timer <= 0:
                self.battle_intro_card = None

        if self.screen_mode != "battle" or self.controller is None:
            return
        if self.battle_intro_card is not None:
            return

        active = self.controller.get_active_unit()
        active_id = active.id if active else None
        if active_id != self.last_active_id:
            if active and active.team == "blue":
                self.mode = "move"
                self.status_text = f"{active.name} 차례입니다. 이동 후 행동하거나, 바로 행동할 수 있습니다."
            elif active and active.team == "red":
                self.mode = "observe"
                self.status_text = f"{active.name}가 행동을 고르는 중입니다."
                self.ai_timer = 0.55
            self.last_active_id = active_id

        for unit in self.controller.units:
            target = pygame.Vector2(self._tile_center(unit.position))
            current = self.unit_visual_positions.setdefault(unit.id, target)
            current.update(current.lerp(target, clamp(dt * 8.5, 0.0, 1.0)))

        for unit_id in list(self.hit_flash):
            self.hit_flash[unit_id] = max(0.0, self.hit_flash[unit_id] - dt)

        for floater in list(self.floaters):
            floater.lifetime -= dt
            floater.y -= dt * 34
            if floater.lifetime <= 0:
                self.floaters.remove(floater)

        active = self.controller.get_active_unit()
        if active and active.team == "red" and not self.controller.state.winner:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                results = self.controller.run_ai_turn()
                for result in results:
                    self._apply_action_result(result)
                self.ai_timer = 0.55

    def _apply_action_result(self, result: TacticalActionResult) -> None:
        actor = self.controller.get_unit(result.actor_id) if self.controller else None
        if result.kind == "move":
            self.audio.play("ui-confirm", champion_id=result.actor_id)
        elif result.kind == "end":
            self.audio.play("ui-confirm")
        else:
            self.audio.play("cast", champion_id=result.actor_id)

        any_damage = False
        any_shield = False
        any_stun = False
        for impact in result.impacts:
            if self.controller is None:
                continue
            unit = self.controller.get_unit(impact.target_id)
            if unit is None:
                continue
            anchor = self.unit_visual_positions[unit.id]
            if actor is not None:
                if actor.team == "blue":
                    self.battle_stats["blue_damage"] += impact.damage
                    if impact.defeated:
                        self.battle_stats["blue_kills"] += 1
                else:
                    self.battle_stats["red_damage"] += impact.damage
                    if impact.defeated:
                        self.battle_stats["red_kills"] += 1
            if impact.damage:
                any_damage = True
                self.hit_flash[unit.id] = 0.28
                self.floaters.append(FloatingText(anchor.x, anchor.y - 46, f"-{impact.damage}", (255, 172, 144)))
            if impact.shield_gained:
                any_shield = True
                self.floaters.append(FloatingText(anchor.x, anchor.y - 70, f"+보호막 {impact.shield_gained}", (166, 235, 191)))
            if impact.stun_applied:
                any_stun = True
                self.floaters.append(FloatingText(anchor.x, anchor.y - 94, "기절", (255, 229, 145)))
            if impact.defeated:
                self.floaters.append(FloatingText(anchor.x, anchor.y - 118, "처치", (255, 216, 168)))

        if any_damage:
            heavy = any(impact.damage >= 18 for impact in result.impacts)
            self.audio.play("hit-heavy" if heavy else "hit")
        if any_shield:
            self.audio.play("shield")
        if any_stun:
            self.audio.play("stun")

        if result.kind == "move":
            self.status_text = "이동 완료. 행동을 선택하거나 턴을 끝낼 수 있습니다."
            if result.notes:
                self.status_text = " ".join(result.notes)
        elif result.kind == "end":
            self.mode = "move"
            self.status_text = "턴을 넘겼습니다."
        else:
            self.status_text = "기본 공격 사용 완료." if result.kind == "basic" else f"{result.ability_name} 사용 완료."
            if result.notes:
                self.status_text = f"{self.status_text} {' '.join(result.notes)}"

        self._update_battle_objective_from_result(result)
        if any("결전 각성 발동." in note for note in result.notes):
            self._resolve_finale_phase_state()

        if self.controller and self.controller.state.winner == "blue":
            self.audio.play("victory")
            objective_summary = self._apply_completed_objective_bonus()
            node_summary = self._apply_route_node_victory_bonus()
            penalty_summary = self._queue_objective_failure_penalty()
            self._record_battle_recap("승리")
            if self.run_stage < RUN_STAGE_COUNT:
                self.status_text = f"{self._current_stage_label()} 승리. 전투 보상을 선택하세요."
                if objective_summary:
                    self.status_text = f"{self.status_text} {objective_summary}"
                if node_summary:
                    self.status_text = f"{self.status_text} {node_summary}"
                if penalty_summary:
                    self.status_text = f"{self.status_text} {penalty_summary}"
                self._prepare_reward_phase()
            else:
                self.status_text = "최종 결전을 승리했습니다."
                if objective_summary:
                    self.status_text = f"{self.status_text} {objective_summary}"
                if node_summary:
                    self.status_text = f"{self.status_text} {node_summary}"
                self._enter_run_summary("원정 성공")
        elif self.controller and self.controller.state.winner == "red":
            self.audio.play("defeat")
            self.last_objective_summary = self._summarize_current_objective()
            self.last_node_summary = None
            self._record_battle_recap("패배")
            self.status_text = f"{self._current_stage_label()}에서 패배했습니다."
            self._enter_run_summary("원정 실패")

    def _draw(self) -> None:
        self.screen.blit(self.background_cache, (0, 0))
        self.button_rects.clear()
        self.tile_rects.clear()
        self.reward_card_rects.clear()
        self.route_card_rects.clear()
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
        else:
            self._draw_battle_screen()
        self._draw_finale_banner()
        self._draw_battle_intro()

    def _draw_header(self, title: str, subtitle: str, center_text: str, action_label: str) -> None:
        panel = pygame.Surface(HEADER_RECT.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (15, 24, 37), (19, 31, 47))
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=24)
        self.screen.blit(panel, HEADER_RECT.topleft)
        title_pos = (HEADER_RECT.x + 22, HEADER_RECT.y + 6)
        subtitle_pos = (HEADER_RECT.x + 24, HEADER_RECT.y + 44)
        self._draw_text(title, self.font_large, (244, 239, 225), title_pos)
        self._draw_text(subtitle, self.font_small, (226, 204, 156), subtitle_pos)

        status_rect = pygame.Rect(HEADER_RECT.centerx - 148, HEADER_RECT.y + 12, 296, 46)
        pygame.draw.rect(self.screen, (12, 21, 31), status_rect, border_radius=16)
        pygame.draw.rect(self.screen, (91, 134, 166), status_rect, 1, border_radius=16)
        self._draw_text("현재 단계", self.font_tiny, (141, 173, 195), (status_rect.x + 16, status_rect.y + 7))
        self._draw_wrapped_text(center_text, self.font_small, (221, 231, 238), pygame.Rect(status_rect.x + 16, status_rect.y + 20, status_rect.width - 32, 18), max_lines=1)

        action_rect = pygame.Rect(HEADER_RECT.right - 174, HEADER_RECT.y + 10, 152, 50)
        self.button_rects["header-action"] = action_rect
        pygame.draw.rect(self.screen, (214, 182, 112), action_rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 244, 217), action_rect, 1, border_radius=14)
        self._draw_text(action_label, self.font_ui, (13, 21, 31), action_rect.center, center=True)

    def _draw_panel(self, rect: pygame.Rect, glow_color: tuple[int, int, int]) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (10, 19, 29), (17, 28, 42))
        pygame.draw.rect(panel, (*glow_color, 18), panel.get_rect(), border_radius=26)
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=26)
        self.screen.blit(panel, rect.topleft)

    def _draw_message_strip(self, rect: pygame.Rect, text: str, accent: tuple[int, int, int]) -> None:
        strip = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(strip, strip.get_rect(), (12, 21, 31), (16, 28, 42))
        pygame.draw.rect(strip, (*accent, 24), strip.get_rect(), border_radius=18)
        pygame.draw.rect(strip, (236, 218, 176), strip.get_rect(), 1, border_radius=18)
        self.screen.blit(strip, rect.topleft)
        self._draw_wrapped_text(text, self.font_small, (208, 219, 226), rect.inflate(-20, -14), max_lines=2)

    def _draw_info_chip(
        self,
        rect: pygame.Rect,
        label: str,
        value: str,
        accent: tuple[int, int, int],
        *,
        value_color: tuple[int, int, int] = (244, 239, 225),
    ) -> None:
        chip = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(chip, chip.get_rect(), (12, 21, 31), (17, 28, 42))
        pygame.draw.rect(chip, (*accent, 20), chip.get_rect(), border_radius=18)
        pygame.draw.rect(chip, (*accent, 110), chip.get_rect(), 1, border_radius=18)
        self.screen.blit(chip, rect.topleft)
        self._draw_text(label, self.font_tiny, accent, (rect.x + 14, rect.y + 10))
        self._draw_wrapped_text(value, self.font_small, value_color, pygame.Rect(rect.x + 14, rect.y + 26, rect.width - 28, rect.height - 34), max_lines=2)

    def _draw_selection_screen(self) -> None:
        self._draw_header("리그 오브 레전드: 리프트 택틱스", "3전 원정 준비", f"챔피언 선택 · 1/{RUN_STAGE_COUNT} 시작", "ESC 종료")
        self._draw_panel(SELECT_LEFT_PANEL, (74, 157, 214))
        self._draw_panel(SELECT_RIGHT_PANEL, (212, 105, 86))
        self._draw_text("플레이어 팀 선택", self.font_heading, (244, 239, 225), (SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 18))
        self._draw_text("3명을 골라 배치 단계로 넘어가세요", self.font_small, (150, 182, 201), (SELECT_LEFT_PANEL.x + 24, SELECT_LEFT_PANEL.y + 52))
        self._draw_text("적 조합 미리보기", self.font_heading, (244, 239, 225), (SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 18))
        self._draw_text("전술 상대를 재추첨할 수 있습니다", self.font_small, (198, 176, 168), (SELECT_RIGHT_PANEL.x + 24, SELECT_RIGHT_PANEL.y + 52))
        self._draw_selection_slots()
        self._draw_selection_doctrine_panel()
        self._draw_selection_pool()
        self._draw_selection_enemy_preview()

    def _draw_selection_slots(self) -> None:
        rect = pygame.Rect(SELECT_LEFT_PANEL.x + 18, SELECT_LEFT_PANEL.y + 86, SELECT_LEFT_PANEL.width - 36, 178)
        self.selection_slot_rects = []
        self._draw_text("출전 라인업", self.font_ui, (229, 210, 164), (rect.x, rect.y))
        self._draw_text(f"{len(self.selected_blue_ids)}/3 선택", self.font_small, (128, 164, 188), (rect.right, rect.y + 4), align_right=True)
        slot_width = (rect.width - 36) // 3
        gap = 18
        for index in range(3):
            slot_rect = pygame.Rect(rect.x + index * (slot_width + gap), rect.y + 42, slot_width, 118)
            self.selection_slot_rects.append(slot_rect)
            pygame.draw.rect(self.screen, (13, 24, 37), slot_rect, border_radius=22)
            pygame.draw.rect(self.screen, (236, 218, 176), slot_rect, 1, border_radius=22)
            if index < len(self.selected_blue_ids):
                champion_id = self.selected_blue_ids[index]
                self._draw_champion_card(slot_rect, champion_id, compact=True, badge=str(index + 1), footer="클릭해서 제거")
            else:
                self._draw_text("+", self.font_large, (119, 154, 178), slot_rect.center, center=True)
                self._draw_text("빈 슬롯", self.font_ui, (180, 192, 204), (slot_rect.centerx, slot_rect.y + 74), center=True)

    def _draw_selection_pool(self) -> None:
        rect = pygame.Rect(SELECT_LEFT_PANEL.x + 18, SELECT_LEFT_PANEL.y + 300, SELECT_LEFT_PANEL.width - 36, SELECT_LEFT_PANEL.height - 394)
        self.selection_card_rects.clear()
        self._draw_text("후보 로스터", self.font_ui, (229, 210, 164), (rect.x, rect.y))
        self._draw_text("각 챔피언의 역할과 패시브를 보고 출전 조합을 만드세요", self.font_tiny, (150, 182, 201), (rect.x + 2, rect.y + 28))
        grid_rect = pygame.Rect(rect.x, rect.y + 52, rect.width, rect.height - 52)
        columns = 3
        gap_x = 18
        gap_y = 18
        rows = max(1, (len(SELECTABLE_BLUE_IDS) + columns - 1) // columns)
        card_width = (grid_rect.width - gap_x * (columns - 1)) // columns
        card_height = (grid_rect.height - gap_y * (rows - 1)) // rows
        for index, champion_id in enumerate(SELECTABLE_BLUE_IDS):
            col = index % columns
            row = index // columns
            card_rect = pygame.Rect(
                grid_rect.x + col * (card_width + gap_x),
                grid_rect.y + row * (card_height + gap_y),
                card_width,
                card_height,
            )
            self.selection_card_rects[champion_id] = card_rect
            selected = champion_id in self.selected_blue_ids
            order = str(self.selected_blue_ids.index(champion_id) + 1) if selected else None
            passive_name = TACTICAL_BLUEPRINTS_BY_ID[champion_id].passive_name
            self._draw_champion_card(card_rect, champion_id, selected=selected, compact=True, badge=order, footer=f"패시브 · {passive_name}")

        footer = pygame.Rect(rect.x, SELECT_LEFT_PANEL.bottom - 82, rect.width, 58)
        self._draw_message_strip(footer, self.selection_message, (74, 157, 214))

    def _draw_selection_doctrine_panel(self) -> None:
        panel_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 92, SELECT_RIGHT_PANEL.width - 44, 154)
        pygame.draw.rect(self.screen, (11, 20, 31), panel_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), panel_rect, 1, border_radius=24)
        self._draw_text("원정 교리", self.font_ui, (229, 210, 164), (panel_rect.x + 16, panel_rect.y + 12))
        self._draw_text("기록으로 해금한 시작 보너스 중 하나를 선택합니다", self.font_tiny, (170, 191, 207), (panel_rect.x + 16, panel_rect.y + 40))
        history_chip = pygame.Rect(panel_rect.right - 176, panel_rect.y + 14, 160, 30)
        pygame.draw.rect(self.screen, (15, 28, 40), history_chip, border_radius=12)
        pygame.draw.rect(self.screen, (91, 134, 166), history_chip, 1, border_radius=12)
        self._draw_text(f"기록 {len(self.history_store.records)} · 완주 {self.history_store.clear_count()}", self.font_tiny, (205, 217, 225), (history_chip.centerx, history_chip.centery), center=True)
        self.doctrine_card_rects.clear()
        gap = 14
        card_width = (panel_rect.width - 32 - gap * 2) // 3
        for index, doctrine in enumerate(self.doctrine_statuses[:3]):
            card_rect = pygame.Rect(panel_rect.x + 16 + index * (card_width + gap), panel_rect.y + 74, card_width, 62)
            self.doctrine_card_rects[doctrine.id] = card_rect
            selected = doctrine.id == self.selected_doctrine_id and doctrine.unlocked
            fill = (22, 46, 58) if selected else (15, 26, 39)
            border = (108, 224, 203) if selected else (236, 218, 176) if doctrine.unlocked else (96, 104, 112)
            pygame.draw.rect(self.screen, fill, card_rect, border_radius=14)
            pygame.draw.rect(self.screen, border, card_rect, 1, border_radius=14)
            title_color = (244, 239, 225) if doctrine.unlocked else (166, 174, 182)
            sub_color = (170, 222, 210) if doctrine.unlocked else (140, 149, 158)
            self._draw_text(doctrine.name, self.font_small, title_color, (card_rect.x + 12, card_rect.y + 8))
            detail_line = doctrine.description if doctrine.unlocked else f"{doctrine.requirement_label} · {doctrine.progress_label}"
            self._draw_wrapped_text(detail_line, self.font_tiny, sub_color, pygame.Rect(card_rect.x + 12, card_rect.y + 28, card_rect.width - 24, 24), max_lines=2)

    def _draw_selection_enemy_preview(self) -> None:
        section_y = SELECT_RIGHT_PANEL.y + 270
        self._draw_text("예상 적 조합", self.font_ui, (229, 210, 164), (SELECT_RIGHT_PANEL.x + 22, section_y))
        self._draw_text("상대의 핵심 특징만 보고 출전 조합을 마무리하세요", self.font_tiny, (198, 176, 168), (SELECT_RIGHT_PANEL.x + 24, section_y + 28))

        for index, champion_id in enumerate(self.selected_red_ids):
            card_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, section_y + 52 + index * 128, SELECT_RIGHT_PANEL.width - 44, 112)
            passive_name = TACTICAL_BLUEPRINTS_BY_ID[champion_id].passive_name
            self._draw_champion_card(card_rect, champion_id, compact=True, enemy=True, footer=f"패시브 · {passive_name}")

        note_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.bottom - 124, SELECT_RIGHT_PANEL.width - 44, 52)
        selected_doctrine = self._selected_doctrine()
        note_text = (
            f"선택 교리 · {selected_doctrine.name} · {selected_doctrine.description}"
            if selected_doctrine is not None
            else "원정 교리를 고르거나 그대로 기본 교리 없이 시작할 수 있습니다."
        )
        self._draw_message_strip(note_rect, note_text, (212, 105, 86))

        reroll_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.bottom - 62, 248, 48)
        start_rect = pygame.Rect(SELECT_RIGHT_PANEL.right - 270, SELECT_RIGHT_PANEL.bottom - 62, 248, 48)
        self.button_rects["selection-reroll"] = reroll_rect
        self.button_rects["selection-start"] = start_rect
        pygame.draw.rect(self.screen, (214, 182, 112), reroll_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), reroll_rect, 1, border_radius=15)
        self._draw_text("적 재추첨", self.font_ui, (12, 20, 31), reroll_rect.center, center=True)
        enabled = len(self.selected_blue_ids) == 3
        fill = (214, 182, 112) if enabled else (76, 84, 96)
        text_color = (12, 20, 31) if enabled else (188, 196, 204)
        pygame.draw.rect(self.screen, fill, start_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), start_rect, 1, border_radius=15)
        self._draw_text("배치 시작", self.font_ui, text_color, start_rect.center, center=True)

    def _draw_reward_screen(self) -> None:
        self._draw_header(
            "리그 오브 레전드: 리프트 택틱스",
            "원정 보상 선택",
            f"{self.run_stage}/{RUN_STAGE_COUNT} 전투 승리",
            "선택으로",
        )
        self._draw_panel(SELECT_LEFT_PANEL, (74, 157, 214))
        self._draw_panel(SELECT_RIGHT_PANEL, (214, 182, 112))
        self._draw_text("다음 전투 브리핑", self.font_heading, (244, 239, 225), (SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 18))
        self._draw_text(self.selection_message, self.font_small, (167, 192, 212), (SELECT_LEFT_PANEL.x + 24, SELECT_LEFT_PANEL.y + 52))
        self._draw_text("전투 보상", self.font_heading, (244, 239, 225), (SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 18))
        self._draw_text("보상 하나를 고르면 다음 전투로 진입할 수 있습니다", self.font_small, (198, 176, 168), (SELECT_RIGHT_PANEL.x + 24, SELECT_RIGHT_PANEL.y + 52))

        progress_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 96, SELECT_LEFT_PANEL.width - 44, 96)
        pygame.draw.rect(self.screen, (13, 24, 37), progress_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), progress_rect, 1, border_radius=24)
        self._draw_text("원정 진행도", self.font_ui, (229, 210, 164), (progress_rect.x + 18, progress_rect.y + 14))
        self._draw_text(
            f"{self._current_stage_label()} 승리 · 다음은 {RUN_STAGE_LABELS.get(self.run_stage + 1, '결산')}",
            self.font_heading,
            (244, 239, 225),
            (progress_rect.x + 18, progress_rect.y + 44),
        )
        self._draw_text(
            f"{self.run_stage}승 달성 / 총 {RUN_STAGE_COUNT}전",
            self.font_small,
            (171, 193, 208),
            (progress_rect.x + 18, progress_rect.y + 72),
        )

        bonus_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 216, SELECT_LEFT_PANEL.width - 44, 188)
        pygame.draw.rect(self.screen, (11, 20, 31), bonus_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), bonus_rect, 1, border_radius=24)
        self._draw_text("현재 강화", self.font_ui, (229, 210, 164), (bonus_rect.x + 18, bonus_rect.y + 14))
        for index, line in enumerate(self._run_bonus_lines()):
            self._draw_text(line, self.font_small, (209, 220, 227), (bonus_rect.x + 18, bonus_rect.y + 50 + index * 28))

        preview_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 432, SELECT_LEFT_PANEL.width - 44, 420)
        pygame.draw.rect(self.screen, (11, 20, 31), preview_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), preview_rect, 1, border_radius=24)
        self._draw_text("다음 적 조합", self.font_ui, (229, 210, 164), (preview_rect.x + 18, preview_rect.y + 14))
        for index, champion_id in enumerate(self.pending_red_ids):
            card_rect = pygame.Rect(preview_rect.x + 18, preview_rect.y + 48 + index * 118, preview_rect.width - 36, 102)
            self._draw_champion_card(card_rect, champion_id, compact=True, enemy=True)

        for index, reward_id in enumerate(self.reward_option_ids):
            card_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 96 + index * 188, SELECT_RIGHT_PANEL.width - 44, 160)
            self.reward_card_rects[reward_id] = card_rect
            reward = self.run_rewards[reward_id]
            selected = reward_id == self.selected_reward_id
            top = (22, 46, 58) if selected else (15, 26, 39)
            bottom = (26, 68, 76) if selected else (20, 32, 46)
            card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
            draw_vertical_gradient(card, card.get_rect(), top, bottom)
            pygame.draw.rect(card, (95, 222, 201, 36) if selected else (214, 182, 112, 18), card.get_rect(), border_radius=24)
            pygame.draw.rect(card, (108, 224, 203) if selected else (236, 218, 176), card.get_rect(), 1, border_radius=24)
            self.screen.blit(card, card_rect.topleft)
            badge_rect = pygame.Rect(card_rect.x + 18, card_rect.y + 18, 70, 28)
            pygame.draw.rect(self.screen, (214, 182, 112), badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, (10, 18, 29), badge_rect, 1, border_radius=10)
            self._draw_text("보상", self.font_small, (10, 18, 29), badge_rect.center, center=True)
            self._draw_text(reward.name, self.font_heading, (244, 239, 225), (card_rect.x + 18, card_rect.y + 58))
            self._draw_wrapped_text(reward.description, self.font_ui, (208, 219, 226), pygame.Rect(card_rect.x + 18, card_rect.y + 96, card_rect.width - 36, 48), max_lines=2)

        select_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 32, SELECT_RIGHT_PANEL.bottom - 118, 190, 48)
        next_rect = pygame.Rect(SELECT_RIGHT_PANEL.right - 242, SELECT_RIGHT_PANEL.bottom - 118, 190, 48)
        self.button_rects["reward-select"] = select_rect
        self.button_rects["reward-next"] = next_rect
        pygame.draw.rect(self.screen, (70, 80, 92), select_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), select_rect, 1, border_radius=15)
        self._draw_text("선택 화면으로", self.font_ui, (231, 236, 240), select_rect.center, center=True)
        enabled = self.selected_reward_id is not None
        pygame.draw.rect(self.screen, (214, 182, 112) if enabled else (76, 84, 96), next_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), next_rect, 1, border_radius=15)
        self._draw_text("경로 선택", self.font_ui, (12, 20, 31) if enabled else (188, 196, 204), next_rect.center, center=True)

    def _draw_route_screen(self) -> None:
        self._draw_header(
            "리그 오브 레전드: 리프트 택틱스",
            "전투 요약과 경로 선택",
            f"{self._current_stage_label()} 진입 준비",
            "선택으로",
        )
        self._draw_panel(SELECT_LEFT_PANEL, (74, 157, 214))
        self._draw_panel(SELECT_RIGHT_PANEL, (214, 182, 112))
        self._draw_text("전투 요약", self.font_heading, (244, 239, 225), (SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 18))
        self._draw_text(self.selection_message, self.font_small, (167, 192, 212), (SELECT_LEFT_PANEL.x + 24, SELECT_LEFT_PANEL.y + 52))
        self._draw_text("다음 경로 선택", self.font_heading, (244, 239, 225), (SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 18))
        self._draw_text("경로와 노드 조합 3안 중 하나를 골라 다음 전투에 적용하세요", self.font_small, (198, 176, 168), (SELECT_RIGHT_PANEL.x + 24, SELECT_RIGHT_PANEL.y + 52))

        recap = self.last_battle_recap
        overview_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 96, SELECT_LEFT_PANEL.width - 44, 144)
        pygame.draw.rect(self.screen, (11, 20, 31), overview_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), overview_rect, 1, border_radius=24)
        if recap is not None:
            badge_rect = pygame.Rect(overview_rect.x + 18, overview_rect.y + 18, 110, 28)
            pygame.draw.rect(self.screen, (74, 157, 214), badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, (10, 18, 29), badge_rect, 1, border_radius=10)
            self._draw_text(recap.result_label, self.font_small, (10, 18, 29), badge_rect.center, center=True)
            self._draw_text(recap.stage_label, self.font_heading, (244, 239, 225), (overview_rect.x + 18, overview_rect.y + 56))
            self._draw_text(f"전투 라운드 {recap.rounds}", self.font_small, (223, 206, 164), (overview_rect.right - 18, overview_rect.y + 60), align_right=True)
            highlight_rect = pygame.Rect(overview_rect.x + 18, overview_rect.y + 92, overview_rect.width - 36, 18)
            self._draw_wrapped_text(recap.highlight, self.font_small, (208, 219, 226), highlight_rect, max_lines=1)
            if recap.objective_summary:
                self._draw_wrapped_text(recap.objective_summary, self.font_tiny, (255, 213, 150), pygame.Rect(overview_rect.x + 18, overview_rect.y + 108, overview_rect.width - 36, 16), max_lines=1)
            secondary_line = recap.route_node_summary or recap.route_event_summary or recap.penalty_summary
            secondary_color = (
                (170, 222, 210)
                if recap.route_node_summary
                else (174, 208, 235)
                if recap.route_event_summary
                else (235, 156, 140)
            )
            if secondary_line:
                self._draw_wrapped_text(secondary_line, self.font_tiny, secondary_color, pygame.Rect(overview_rect.x + 18, overview_rect.y + 124, overview_rect.width - 36, 16), max_lines=1)
        else:
            self._draw_text("직전 전투 기록 없음", self.font_heading, (244, 239, 225), (overview_rect.x + 18, overview_rect.y + 28))
            self._draw_text("전투 종료 후 핵심 수치와 마지막 로그를 여기서 보여 줍니다.", self.font_small, (208, 219, 226), (overview_rect.x + 18, overview_rect.y + 72))

        stat_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 258, SELECT_LEFT_PANEL.width - 44, 148)
        pygame.draw.rect(self.screen, (11, 20, 31), stat_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), stat_rect, 1, border_radius=24)
        self._draw_text("핵심 수치", self.font_ui, (229, 210, 164), (stat_rect.x + 18, stat_rect.y + 14))
        if recap is not None:
            chip_width = (stat_rect.width - 50) // 2
            chip_height = 42
            stat_specs = [
                ("아군 피해", str(recap.blue_damage), (74, 157, 214)),
                ("적군 피해", str(recap.red_damage), (236, 126, 90)),
                ("아군 처치", str(recap.blue_kills), (108, 224, 203)),
                ("적군 처치", str(recap.red_kills), (214, 182, 112)),
            ]
            for index, (label, value, accent) in enumerate(stat_specs):
                col = index % 2
                row = index // 2
                chip_rect = pygame.Rect(
                    stat_rect.x + 18 + col * (chip_width + 14),
                    stat_rect.y + 48 + row * (chip_height + 12),
                    chip_width,
                    chip_height,
                )
                self._draw_info_chip(chip_rect, label, value, accent)
        else:
            self._draw_text("전투 종료 후 자동 집계", self.font_small, (209, 220, 227), (stat_rect.x + 18, stat_rect.y + 52))

        stage_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 424, SELECT_LEFT_PANEL.width - 44, 334)
        pygame.draw.rect(self.screen, (11, 20, 31), stage_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), stage_rect, 1, border_radius=24)
        self._draw_text("다음 전투 프리뷰", self.font_ui, (229, 210, 164), (stage_rect.x + 18, stage_rect.y + 14))
        self._draw_text(f"{self._current_stage_label()} 준비", self.font_heading, (244, 239, 225), (stage_rect.x + 18, stage_rect.y + 48))
        selected_route = self.selected_route_id or self.current_route_id
        selected_node = self.route_node_by_route_id.get(selected_route) if self.selected_route_id else self.current_route_node
        selected_follow_up = self.node_follow_up_by_route_id.get(selected_route) if self.selected_route_id else self.current_node_follow_up
        preview_objective = self._preview_battle_objective(route_id=selected_route, enemy_ids=self.selected_red_ids)
        active_doctrine = self._active_doctrine()
        route_value = "경로 선택 전" if selected_route is None else self.route_options[selected_route].name
        doctrine_value = "없음"
        if active_doctrine is not None:
            doctrine_value = active_doctrine.name
            if active_doctrine.route_reroll_charges:
                doctrine_value += f" · 재추첨 {self.route_reroll_charges}"
        chip_width = (stage_rect.width - 50) // 2
        self._draw_info_chip(
            pygame.Rect(stage_rect.x + 18, stage_rect.y + 88, chip_width, 64),
            "선택 경로",
            route_value,
            (214, 182, 112),
        )
        self._draw_info_chip(
            pygame.Rect(stage_rect.x + 32 + chip_width, stage_rect.y + 88, chip_width, 64),
            "원정 교리",
            doctrine_value,
            (108, 224, 203),
        )
        objective_preview_text = "경로를 고르면 목표가 보입니다."
        if selected_route is not None:
            objective_preview_text = (
                preview_objective.description.replace("목표: ", "")
                if preview_objective is not None
                else self.route_options[selected_route].description.replace("목표: ", "")
            )
        terrain_lines = []
        terrain_counts: dict[str, int] = {}
        preview_route_id = self.selected_route_id or self.current_route_id
        preview_profile = self._boss_profile_for_stage(lineup=self.selected_red_ids)
        preview_variant = self._finale_variant_for_stage(lineup=self.selected_red_ids)
        for terrain_id in self._terrain_tiles_for_stage(route_id=preview_route_id, enemy_ids=self.selected_red_ids).values():
            terrain_counts[terrain_id] = terrain_counts.get(terrain_id, 0) + 1
        for terrain_id, count in terrain_counts.items():
            terrain_lines.append(f"{TERRAIN_BY_ID[terrain_id].name} {count}칸")
        terrain_value = ", ".join(terrain_lines[:2]) if terrain_lines else "특수 지형 없음"
        self._draw_info_chip(
            pygame.Rect(stage_rect.x + 18, stage_rect.y + 160, chip_width, 68),
            "맵 목표",
            objective_preview_text,
            (174, 208, 235),
        )
        self._draw_info_chip(
            pygame.Rect(stage_rect.x + 32 + chip_width, stage_rect.y + 160, chip_width, 68),
            "지형",
            terrain_value,
            (108, 192, 235),
        )

        notes: list[tuple[str, tuple[int, int, int]]] = []
        if selected_route is not None:
            notes.append((f"보상 · {ROUTE_REWARD_BY_ID[selected_route]}", (228, 214, 167)))
            notes.append((f"위험 · {ROUTE_RISK_BY_ID[selected_route]}", (233, 156, 140)))
            if selected_node is not None:
                notes.append((f"노드 · {selected_node.name} · {self._node_effect_preview_label(selected_node, selected_follow_up)}", (170, 222, 210)))
            selected_event = self.route_event_by_route_id.get(selected_route) if self.selected_route_id else self.current_route_event
            if selected_event is not None:
                notes.append((f"이벤트 · {selected_event.name} · {self._route_event_effect_label(selected_event, selected_node)}", (174, 208, 235)))
        if self.pending_stage_penalty is not None:
            penalty_color = (138, 234, 171) if selected_node is not None and selected_node.clears_pending_penalty else (235, 156, 140)
            penalty_prefix = "해제 예정" if selected_node is not None and selected_node.clears_pending_penalty else "예약 페널티"
            notes.append((f"{penalty_prefix} · {self.pending_stage_penalty.description}", penalty_color))

        notes_rect = pygame.Rect(stage_rect.x + 18, stage_rect.y + 242, stage_rect.width - 36, 46)
        pygame.draw.rect(self.screen, (14, 24, 36), notes_rect, border_radius=18)
        pygame.draw.rect(self.screen, (236, 218, 176), notes_rect, 1, border_radius=18)
        if notes:
            for index, (line, color) in enumerate(notes[:2]):
                self._draw_wrapped_text(line, self.font_tiny, color, pygame.Rect(notes_rect.x + 14, notes_rect.y + 12 + index * 20, notes_rect.width - 28, 18), max_lines=1)
        else:
            self._draw_wrapped_text("경로를 고르면 보상, 위험, 노드 효과가 여기에 요약됩니다.", self.font_tiny, (171, 193, 208), pygame.Rect(notes_rect.x + 14, notes_rect.y + 14, notes_rect.width - 28, 18), max_lines=1)

        enemy_line = " · ".join(BLUEPRINTS_BY_ID[champion_id].name for champion_id in self.selected_red_ids)
        enemy_notes: list[str] = [f"적 조합 · {enemy_line}"]
        elite_count = len(self._elite_enemy_ids_for_stage(lineup=self.selected_red_ids, route_node=selected_node))
        if elite_count:
            enemy_notes.append(f"정예 {elite_count}명")
        preview_boss_id = self._boss_enemy_id_for_stage(lineup=self.selected_red_ids)
        if preview_boss_id is not None:
            enemy_notes.append(
                (
                    f"보스 {BLUEPRINTS_BY_ID[preview_boss_id].name} · {preview_variant.name} · {preview_profile.name}"
                    if preview_profile is not None and preview_variant is not None
                    else f"보스 {BLUEPRINTS_BY_ID[preview_boss_id].name}"
                )
            )
        enemy_rect = pygame.Rect(stage_rect.x + 18, stage_rect.y + 298, stage_rect.width - 36, 24)
        self._draw_wrapped_text(" · ".join(enemy_notes), self.font_tiny, (209, 220, 227), enemy_rect, max_lines=2)

        for index, route_id in enumerate(self.route_option_ids):
            rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 96 + index * 176, SELECT_RIGHT_PANEL.width - 44, 160)
            self.route_card_rects[route_id] = rect
            option = self.route_options[route_id]
            route_event = self.route_event_by_route_id.get(route_id)
            route_node = self.route_node_by_route_id.get(route_id)
            node_follow_up = self.node_follow_up_by_route_id.get(route_id)
            selected = route_id == self.selected_route_id
            card = pygame.Surface(rect.size, pygame.SRCALPHA)
            draw_vertical_gradient(card, card.get_rect(), (22, 46, 58) if selected else (15, 26, 39), (26, 68, 76) if selected else (20, 32, 46))
            pygame.draw.rect(card, (95, 222, 201, 36) if selected else (214, 182, 112, 18), card.get_rect(), border_radius=24)
            pygame.draw.rect(card, (108, 224, 203) if selected else (236, 218, 176), card.get_rect(), 1, border_radius=24)
            self.screen.blit(card, rect.topleft)
            style_rect = pygame.Rect(rect.right - 142, rect.y + 18, 124, 28)
            pygame.draw.rect(self.screen, (18, 32, 46), style_rect, border_radius=10)
            pygame.draw.rect(self.screen, (236, 218, 176), style_rect, 1, border_radius=10)
            self._draw_text(ROUTE_STYLE_BY_ID[route_id], self.font_tiny, (223, 206, 164), style_rect.center, center=True)
            self._draw_text(option.name, self.font_heading, (244, 239, 225), (rect.x + 18, rect.y + 18))
            self._draw_wrapped_text(option.description.replace("목표: ", "목표 · "), self.font_small, (208, 219, 226), pygame.Rect(rect.x + 18, rect.y + 56, rect.width - 36, 20), max_lines=1)
            if route_node is not None:
                node_label = f"노드 · {route_node.name} · {route_node.category}"
                if node_follow_up is not None:
                    node_label += f" · 후속 {node_follow_up.name}"
                self._draw_wrapped_text(node_label, self.font_tiny, (170, 222, 210), pygame.Rect(rect.x + 18, rect.y + 86, rect.width - 36, 16), max_lines=1)
            if route_event is not None:
                self._draw_wrapped_text(f"이벤트 · {route_event.name}", self.font_tiny, (214, 203, 156), pygame.Rect(rect.x + 18, rect.y + 104, rect.width - 36, 16), max_lines=1)
            reward_rect = pygame.Rect(rect.x + 18, rect.y + 122, 222, 24)
            risk_rect = pygame.Rect(rect.x + 254, rect.y + 122, rect.width - 272, 24)
            pygame.draw.rect(self.screen, (27, 41, 54), reward_rect, border_radius=10)
            pygame.draw.rect(self.screen, (214, 182, 112), reward_rect, 1, border_radius=10)
            pygame.draw.rect(self.screen, (27, 41, 54), risk_rect, border_radius=10)
            pygame.draw.rect(self.screen, (236, 126, 90), risk_rect, 1, border_radius=10)
            self._draw_wrapped_text(f"보상 · {ROUTE_REWARD_BY_ID[route_id]}", self.font_tiny, (221, 215, 178), pygame.Rect(reward_rect.x + 10, reward_rect.y + 5, reward_rect.width - 20, 14), max_lines=1)
            self._draw_wrapped_text(f"위험 · {ROUTE_RISK_BY_ID[route_id]}", self.font_tiny, (231, 168, 152), pygame.Rect(risk_rect.x + 10, risk_rect.y + 5, risk_rect.width - 20, 14), max_lines=1)

        select_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 24, SELECT_RIGHT_PANEL.bottom - 70, 160, 48)
        reroll_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 201, SELECT_RIGHT_PANEL.bottom - 70, 168, 48)
        next_rect = pygame.Rect(SELECT_RIGHT_PANEL.right - 184, SELECT_RIGHT_PANEL.bottom - 70, 160, 48)
        self.button_rects["route-select"] = select_rect
        self.button_rects["route-reroll"] = reroll_rect
        self.button_rects["route-next"] = next_rect
        pygame.draw.rect(self.screen, (70, 80, 92), select_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), select_rect, 1, border_radius=15)
        self._draw_text("선택 화면으로", self.font_ui, (231, 236, 240), select_rect.center, center=True)
        reroll_enabled = self.route_reroll_charges > 0
        pygame.draw.rect(self.screen, (214, 182, 112) if reroll_enabled else (76, 84, 96), reroll_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), reroll_rect, 1, border_radius=15)
        self._draw_text(f"경로 재추첨 {self.route_reroll_charges}", self.font_ui, (12, 20, 31) if reroll_enabled else (188, 196, 204), reroll_rect.center, center=True)
        enabled = self.selected_route_id is not None
        pygame.draw.rect(self.screen, (214, 182, 112) if enabled else (76, 84, 96), next_rect, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), next_rect, 1, border_radius=15)
        self._draw_text("다음 전투 배치", self.font_ui, (12, 20, 31) if enabled else (188, 196, 204), next_rect.center, center=True)

    def _draw_summary_screen(self) -> None:
        summary = self.run_summary
        success = summary is not None and summary.result_label == "원정 성공"
        accent = (108, 224, 203) if success else (236, 126, 90)
        center_text = summary.stage_label if summary is not None else "원정 종료"
        self._draw_header("리그 오브 레전드: 리프트 택틱스", "원정 결산", center_text, "선택으로")
        self._draw_panel(SELECT_LEFT_PANEL, (74, 157, 214))
        self._draw_panel(SELECT_RIGHT_PANEL, accent)
        self._draw_text("원정 결과", self.font_heading, (244, 239, 225), (SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 18))
        self._draw_text(
            "같은 조합으로 바로 새 런을 시작하거나 챔피언을 다시 고를 수 있습니다.",
            self.font_small,
            (167, 192, 212),
            (SELECT_LEFT_PANEL.x + 24, SELECT_LEFT_PANEL.y + 52),
        )
        self._draw_text("전투 타임라인", self.font_heading, (244, 239, 225), (SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 18))
        self._draw_text("이번 런의 각 전투 기록과 핵심 선택을 한눈에 정리했습니다.", self.font_small, (198, 176, 168), (SELECT_RIGHT_PANEL.x + 24, SELECT_RIGHT_PANEL.y + 52))

        if summary is None:
            fallback_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 96, SELECT_LEFT_PANEL.width - 44, 200)
            pygame.draw.rect(self.screen, (11, 20, 31), fallback_rect, border_radius=24)
            pygame.draw.rect(self.screen, (236, 218, 176), fallback_rect, 1, border_radius=24)
            self._draw_text("결산 정보를 불러오는 중입니다.", self.font_heading, (244, 239, 225), (fallback_rect.x + 18, fallback_rect.y + 26))
            self._draw_text("Enter로 같은 조합 새 런 · ESC로 선택 화면", self.font_small, (209, 220, 227), (fallback_rect.x + 18, fallback_rect.y + 72))
            return

        result_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 96, SELECT_LEFT_PANEL.width - 44, 150)
        pygame.draw.rect(self.screen, (11, 20, 31), result_rect, border_radius=24)
        pygame.draw.rect(self.screen, (*accent, 42), result_rect, 1, border_radius=24)
        badge_rect = pygame.Rect(result_rect.x + 18, result_rect.y + 18, 118, 30)
        pygame.draw.rect(self.screen, accent, badge_rect, border_radius=12)
        pygame.draw.rect(self.screen, (10, 18, 29), badge_rect, 1, border_radius=12)
        self._draw_text(summary.result_label, self.font_small, (10, 18, 29), badge_rect.center, center=True)
        self._draw_text(summary.stage_label, self.font_heading, (244, 239, 225), (result_rect.x + 18, result_rect.y + 62))
        self._draw_wrapped_text(f"출전 조합: {summary.lineup_label}", self.font_small, (208, 219, 226), pygame.Rect(result_rect.x + 18, result_rect.y + 96, result_rect.width - 36, 24), max_lines=1)
        self._draw_text(f"주력 강화: {summary.best_reward_line}", self.font_small, (255, 213, 150), (result_rect.x + 18, result_rect.y + 122))

        stats_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 262, SELECT_LEFT_PANEL.width - 44, 124)
        pygame.draw.rect(self.screen, (11, 20, 31), stats_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), stats_rect, 1, border_radius=24)
        self._draw_text("원정 누적 수치", self.font_ui, (229, 210, 164), (stats_rect.x + 18, stats_rect.y + 14))
        stat_lines = [
            f"총 라운드 {summary.total_rounds}",
            f"아군 누적 피해 {summary.total_blue_damage}",
            f"적 누적 피해 {summary.total_red_damage}",
            f"아군 처치 {summary.total_blue_kills} · 적 처치 {summary.total_red_kills}",
        ]
        for index, line in enumerate(stat_lines):
            self._draw_text(line, self.font_small, (209, 220, 227), (stats_rect.x + 18, stats_rect.y + 42 + index * 20))

        build_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 402, SELECT_LEFT_PANEL.width - 44, 120)
        pygame.draw.rect(self.screen, (11, 20, 31), build_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), build_rect, 1, border_radius=24)
        self._draw_text("이번 런 빌드 포인트", self.font_ui, (229, 210, 164), (build_rect.x + 18, build_rect.y + 14))
        for index, line in enumerate((summary.build_lines or ["강화 · 아직 강화 없음"])[:4]):
            self._draw_wrapped_text(line, self.font_small, (209, 220, 227), pygame.Rect(build_rect.x + 18, build_rect.y + 44 + index * 20, build_rect.width - 36, 18), max_lines=1)

        record_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 22, SELECT_LEFT_PANEL.y + 538, SELECT_LEFT_PANEL.width - 44, 150)
        pygame.draw.rect(self.screen, (11, 20, 31), record_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), record_rect, 1, border_radius=24)
        self._draw_text("저장 기록 · 해금 · 다음 추천", self.font_ui, (229, 210, 164), (record_rect.x + 18, record_rect.y + 14))
        history_lines = (
            [*summary.history_overview_lines[:1], *summary.history_comparison_lines[:1], *summary.unlock_lines[:2]]
            or ["저장 기록 없음"]
        )
        for index, line in enumerate(history_lines[:4]):
            self._draw_wrapped_text(line, self.font_tiny, (208, 219, 226), pygame.Rect(record_rect.x + 18, record_rect.y + 46 + index * 16, record_rect.width - 36, 14), max_lines=1)
        recommendation_rect = pygame.Rect(record_rect.x + 18, record_rect.bottom - 54, record_rect.width - 36, 36)
        pygame.draw.rect(self.screen, (15, 28, 40), recommendation_rect, border_radius=14)
        pygame.draw.rect(self.screen, (*accent, 64), recommendation_rect, 1, border_radius=14)
        self._draw_wrapped_text(summary.recommendation, self.font_small, (208, 219, 226), recommendation_rect.inflate(-14, -8), max_lines=2)

        rerun_rect = pygame.Rect(SELECT_LEFT_PANEL.x + 32, SELECT_LEFT_PANEL.bottom - 70, 246, 48)
        select_rect = pygame.Rect(SELECT_LEFT_PANEL.right - 278, SELECT_LEFT_PANEL.bottom - 70, 246, 48)
        self.button_rects["summary-rerun"] = rerun_rect
        self.button_rects["summary-select"] = select_rect
        pygame.draw.rect(self.screen, accent, rerun_rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 244, 217), rerun_rect, 1, border_radius=16)
        self._draw_text("같은 조합 새 원정", self.font_ui, (13, 21, 31), rerun_rect.center, center=True)
        pygame.draw.rect(self.screen, (70, 80, 92), select_rect, border_radius=16)
        pygame.draw.rect(self.screen, (255, 244, 217), select_rect, 1, border_radius=16)
        self._draw_text("캐릭터 다시 선택", self.font_ui, (231, 236, 240), select_rect.center, center=True)
        self._draw_text("Enter 또는 R로 즉시 새 원정 · ESC로 캐릭터 선택", self.font_small, (208, 219, 226), (SELECT_LEFT_PANEL.centerx, SELECT_LEFT_PANEL.bottom - 16), center=True)

        if not summary.recap_entries:
            empty_rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 96, SELECT_RIGHT_PANEL.width - 44, 160)
            pygame.draw.rect(self.screen, (11, 20, 31), empty_rect, border_radius=24)
            pygame.draw.rect(self.screen, (236, 218, 176), empty_rect, 1, border_radius=24)
            self._draw_text("전투 기록 없음", self.font_heading, (244, 239, 225), (empty_rect.x + 18, empty_rect.y + 26))
            return

        for index, recap in enumerate(summary.recap_entries[:RUN_STAGE_COUNT]):
            rect = pygame.Rect(SELECT_RIGHT_PANEL.x + 22, SELECT_RIGHT_PANEL.y + 96 + index * 196, SELECT_RIGHT_PANEL.width - 44, 182)
            card = pygame.Surface(rect.size, pygame.SRCALPHA)
            draw_vertical_gradient(card, card.get_rect(), (15, 26, 39), (20, 32, 46))
            pygame.draw.rect(card, (*accent, 16), card.get_rect(), border_radius=24)
            pygame.draw.rect(card, (236, 218, 176), card.get_rect(), 1, border_radius=24)
            self.screen.blit(card, rect.topleft)
            stage_badge = pygame.Rect(rect.x + 18, rect.y + 18, 62, 28)
            pygame.draw.rect(self.screen, accent, stage_badge, border_radius=10)
            pygame.draw.rect(self.screen, (10, 18, 29), stage_badge, 1, border_radius=10)
            self._draw_text(f"{index + 1}전", self.font_small, (10, 18, 29), stage_badge.center, center=True)
            self._draw_text(f"{recap.stage_label} · {recap.result_label}", self.font_heading, (244, 239, 225), (rect.x + 94, rect.y + 20))
            self._draw_text(f"라운드 {recap.rounds} · 아군 피해 {recap.blue_damage} · 적 피해 {recap.red_damage}", self.font_small, (223, 206, 164), (rect.x + 18, rect.y + 60))
            self._draw_text(f"아군 처치 {recap.blue_kills} · 적 처치 {recap.red_kills}", self.font_small, (174, 208, 235), (rect.x + 18, rect.y + 84))
            self._draw_wrapped_text(recap.highlight, self.font_small, (208, 219, 226), pygame.Rect(rect.x + 18, rect.y + 112, rect.width - 36, 22), max_lines=1)
            detail_line = recap.objective_summary or recap.route_node_summary or recap.route_event_summary or recap.penalty_summary or "핵심 보조 정보 없음"
            detail_color = (
                (255, 213, 150)
                if recap.objective_summary
                else (170, 222, 210)
                if recap.route_node_summary
                else (174, 208, 235)
                if recap.route_event_summary
                else (235, 156, 140)
            )
            self._draw_wrapped_text(detail_line, self.font_tiny, detail_color, pygame.Rect(rect.x + 18, rect.y + 138, rect.width - 36, 16), max_lines=1)
            secondary_line = recap.route_event_summary if recap.objective_summary and recap.route_event_summary else recap.penalty_summary if recap.penalty_summary and detail_line != recap.penalty_summary else None
            if secondary_line:
                secondary_color = (174, 208, 235) if secondary_line == recap.route_event_summary else (235, 156, 140)
                self._draw_wrapped_text(secondary_line, self.font_tiny, secondary_color, pygame.Rect(rect.x + 18, rect.y + 154, rect.width - 36, 16), max_lines=1)

    def _draw_deploy_screen(self) -> None:
        self._draw_header("리그 오브 레전드: 리프트 택틱스", "원정 전술 배치", f"{self._current_stage_label()} · {self.run_stage}/{RUN_STAGE_COUNT}", "선택으로")
        self._draw_panel(LEFT_PANEL, (74, 157, 214))
        self._draw_panel(RIGHT_PANEL, (212, 105, 86))
        self._draw_panel(BOTTOM_PANEL, (214, 182, 112))
        self._draw_deploy_grid()
        self._draw_deploy_left_panel()
        self._draw_deploy_right_panel()
        self._draw_deploy_bottom_panel()

    def _draw_deploy_grid(self) -> None:
        grid_surface = pygame.Surface(GRID_RECT.size, pygame.SRCALPHA)
        draw_vertical_gradient(grid_surface, grid_surface.get_rect(), (7, 16, 26), (10, 22, 36))
        self.screen.blit(grid_surface, GRID_RECT.topleft)
        terrain_tiles = self._terrain_tiles_for_stage(enemy_ids=self.selected_red_ids)
        blocked_tiles = set(self._blocked_tiles_for_stage(enemy_ids=self.selected_red_ids))

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(GRID_RECT.x + x * GRID_CELL, GRID_RECT.y + y * GRID_CELL, GRID_CELL, GRID_CELL)
                self.tile_rects[(x, y)] = rect
                base = (18, 31, 49) if (x + y) % 2 == 0 else (15, 26, 41)
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (255, 255, 255, 18), rect, 1)
                self._draw_terrain_tile((x, y), rect, terrain_tiles)

                tile = (x, y)
                if tile in DEFAULT_BLUE_DEPLOY_TILES:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((78, 170, 225, 52))
                    self.screen.blit(overlay, rect.topleft)
                elif tile in DEFAULT_RED_DEPLOY_TILES:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((224, 108, 92, 42))
                    self.screen.blit(overlay, rect.topleft)
                if tile in blocked_tiles:
                    pygame.draw.rect(self.screen, (47, 57, 68), rect.inflate(-18, -18), border_radius=18)
                    pygame.draw.rect(self.screen, (173, 139, 104), rect.inflate(-18, -18), 1, border_radius=18)

        for tile, champion_id in self.red_deploy_assignments.items():
            self._draw_static_unit(champion_id, tile, selected=False)
        for tile, champion_id in self.deploy_assignments.items():
            selected = champion_id == self.selected_deploy_champion_id
            self._draw_static_unit(champion_id, tile, selected=selected)

        pygame.draw.rect(self.screen, (236, 218, 176), GRID_RECT, 1, border_radius=26)

    def _draw_deploy_left_panel(self) -> None:
        self._draw_text("배치 브리핑", self.font_heading, (244, 239, 225), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 18))
        self._draw_text(self.selection_message, self.font_small, (167, 192, 212), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 54))
        if self.current_route_node is not None:
            node_label = f"런 노드 · {self.current_route_node.name}"
            if self.current_node_follow_up is not None:
                node_label += f" / {self.current_node_follow_up.name}"
            self._draw_text(node_label, self.font_small, (170, 222, 210), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 82))
        if self.current_route_event is not None:
            self._draw_text(f"전술 이벤트 · {self.current_route_event.name}", self.font_small, (223, 206, 164), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 104))
        self._draw_text("선택한 챔피언", self.font_ui, (229, 210, 164), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 132))
        self.deploy_roster_rects.clear()
        for index, champion_id in enumerate(self.selected_blue_ids):
            rect = pygame.Rect(LEFT_PANEL.x + 18, LEFT_PANEL.y + 166 + index * 116, LEFT_PANEL.width - 36, 98)
            self.deploy_roster_rects[champion_id] = rect
            self._draw_champion_card(rect, champion_id, compact=True, selected=champion_id == self.selected_deploy_champion_id)

        guide_rect = pygame.Rect(LEFT_PANEL.x + 18, LEFT_PANEL.bottom - 194, LEFT_PANEL.width - 36, 166)
        pygame.draw.rect(self.screen, (11, 20, 31), guide_rect, border_radius=22)
        pygame.draw.rect(self.screen, (236, 218, 176), guide_rect, 1, border_radius=22)
        self._draw_text("배치 규칙", self.font_ui, (229, 210, 164), (guide_rect.x + 16, guide_rect.y + 14))
        guides = [
            "1. 왼쪽 챔피언 카드를 클릭",
            "2. 파란 시작 칸을 클릭해 위치 변경",
            "3. 같은 칸을 클릭하면 선택 해제",
            "4. 수풀/룬/화염 지대를 보고 배치",
            "5. 배치가 끝나면 전투 시작",
        ]
        for index, line in enumerate(guides):
            self._draw_text(line, self.font_small, (201, 213, 221), (guide_rect.x + 16, guide_rect.y + 48 + index * 28))

    def _draw_deploy_right_panel(self) -> None:
        self._draw_text("적 시작 위치", self.font_heading, (244, 239, 225), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 18))
        self._draw_text("적은 자동으로 배치되며 순서가 바뀔 수 있습니다", self.font_small, (198, 176, 168), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 52))
        boss_id = self._boss_enemy_id_for_stage()
        boss_profile = self._boss_profile_for_stage()
        finale_variant = self._finale_variant_for_stage()
        if boss_profile is not None and finale_variant is not None:
            self._draw_wrapped_text(
                f"결전 타입 · {finale_variant.name} / {boss_profile.name}",
                self.font_tiny,
                (170, 222, 210),
                pygame.Rect(RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 72, RIGHT_PANEL.width - 36, 18),
                max_lines=1,
            )
        elite_ids = set(self._elite_enemy_ids_for_stage())
        for index, champion_id in enumerate(self.selected_red_ids):
            rect = pygame.Rect(RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 98 + index * 172, RIGHT_PANEL.width - 36, 150)
            tile = self._tile_for_deployed_champion(champion_id, self.red_deploy_assignments)
            if champion_id == boss_id:
                footer = f"보스 · {boss_profile.name if boss_profile is not None else '결전 각성'} · 시작 칸 {tile}"
            elif champion_id in elite_ids:
                trait = ELITE_TRAITS_BY_ID.get(self._elite_trait_id_for_enemy(champion_id) or "")
                trait_label = trait.name if trait is not None else "엘리트"
                footer = f"엘리트 · {trait_label} · 시작 칸 {tile}"
            else:
                footer = f"시작 칸 {tile}"
            self._draw_champion_card(rect, champion_id, compact=True, enemy=True, footer=footer)

    def _draw_deploy_bottom_panel(self) -> None:
        start_rect = pygame.Rect(BOTTOM_PANEL.x + 26, BOTTOM_PANEL.y + 18, 220, 56)
        self.button_rects["deploy-start"] = start_rect
        pygame.draw.rect(self.screen, (214, 182, 112), start_rect, border_radius=18)
        pygame.draw.rect(self.screen, (255, 244, 217), start_rect, 1, border_radius=18)
        self._draw_text("전투 시작", self.font_ui, (13, 21, 31), start_rect.center, center=True)
        self._draw_text("현재 선택", self.font_small, (223, 206, 164), (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 18))
        champion_name = BLUEPRINTS_BY_ID[self.selected_deploy_champion_id].name if self.selected_deploy_champion_id else "없음"
        self._draw_text(champion_name, self.font_heading, (244, 239, 225), (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 38))
        deploy_preview_objective = self._preview_battle_objective()
        combined_node_effect = self._node_effect_preview_label(self.current_route_node, self.current_node_follow_up)
        if self.current_route_node is not None:
            self._draw_text(f"노드 · {self.current_route_node.name}", self.font_tiny, (170, 222, 210), (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 46))
        elif self.current_route_event is not None:
            self._draw_text(f"이벤트 · {self._route_event_effect_label(self.current_route_event, self.current_route_node)}", self.font_tiny, (170, 222, 210), (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 46))
        else:
            self._draw_text("파란 시작 칸을 눌러 위치를 바꾸세요", self.font_small, (184, 205, 221), (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 46))
        penalty_line = (
            f"적용 페널티 · {self.active_stage_penalty.description}"
            if self.active_stage_penalty is not None
            else (
                f"노드 효과 · {combined_node_effect}"
                if self.current_route_node is not None
                else (
                f"결전 목표 · {deploy_preview_objective.description.replace('목표: ', '')}"
                if deploy_preview_objective is not None and deploy_preview_objective.is_finale
                else (
                f"이벤트 · {self._route_event_effect_label(self.current_route_event, self.current_route_node)}"
                if self.current_route_event is not None and self.current_route_node is not None
                else "수풀=보호막 · 룬=피해 +3 · 화염=이동 피해"
                )
                )
            )
        )
        penalty_color = (235, 156, 140) if self.active_stage_penalty is not None else (174, 208, 235)
        self._draw_text(penalty_line, self.font_tiny if self.active_stage_penalty is not None else self.font_small, penalty_color, (BOTTOM_PANEL.x + 290, BOTTOM_PANEL.y + 68))

    def _draw_battle_screen(self) -> None:
        self._draw_header("리그 오브 레전드: 리프트 택틱스", "원정 진행 중", f"{self._current_stage_label()} · {self.run_stage}/{RUN_STAGE_COUNT} · 8x6 전술 전투", "R 리셋")
        self._draw_panel(LEFT_PANEL, (59, 129, 191))
        self._draw_panel(RIGHT_PANEL, (189, 92, 82))
        self._draw_panel(BOTTOM_PANEL, (214, 182, 112))
        self._draw_battle_grid()
        self._draw_battle_left_panel()
        self._draw_battle_right_panel()
        self._draw_battle_bottom_panel()
        self._draw_floaters()
        self._draw_winner_overlay()

    def _draw_battle_grid(self) -> None:
        if self.controller is None:
            return

        grid_surface = pygame.Surface(GRID_RECT.size, pygame.SRCALPHA)
        draw_vertical_gradient(grid_surface, grid_surface.get_rect(), (7, 16, 26), (10, 22, 36))
        self.screen.blit(grid_surface, GRID_RECT.topleft)

        reachable = self.controller.get_reachable_tiles()
        basic_targets = set(self.controller.get_valid_targets("basic")) if self.mode == "basic" else set()
        special_targets = set(self.controller.get_valid_targets("special")) if self.mode == "special" else set()
        active = self.controller.get_active_unit()
        intent = self.controller.preview_ai_intent() if active and active.team == "red" else None
        terrain_tiles = self.controller.terrain_tiles
        boss_pressure_tiles, boss_pressure_color, _, _, boss_pressure_active = self._current_boss_pressure_preview()

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(GRID_RECT.x + x * GRID_CELL, GRID_RECT.y + y * GRID_CELL, GRID_CELL, GRID_CELL)
                self.tile_rects[(x, y)] = rect
                base = (18, 31, 49) if (x + y) % 2 == 0 else (15, 26, 41)
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (255, 255, 255, 18), rect, 1)
                self._draw_terrain_tile((x, y), rect, terrain_tiles)

                if (x, y) in self.controller.blocked_tiles:
                    pygame.draw.rect(self.screen, (47, 57, 68), rect.inflate(-18, -18), border_radius=18)
                    pygame.draw.rect(self.screen, (173, 139, 104), rect.inflate(-18, -18), 1, border_radius=18)

                if (x, y) in reachable:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((89, 170, 219, 58))
                    self.screen.blit(overlay, rect.topleft)

        if self.current_objective is not None:
            for objective_tile in self.current_objective.objective_tiles:
                rect = self.tile_rects.get(objective_tile)
                if rect is None:
                    continue
                objective_color = (236, 126, 90) if self.current_objective.is_finale else (241, 214, 126)
                pygame.draw.rect(self.screen, objective_color, rect.inflate(-18, -18), 2, border_radius=18)
                pygame.draw.rect(self.screen, objective_color, rect.inflate(-34, -34), 1, border_radius=12)

        for pressure_tile in boss_pressure_tiles:
            rect = self.tile_rects.get(pressure_tile)
            if rect is None:
                continue
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((*boss_pressure_color, 28 if boss_pressure_active else 14))
            self.screen.blit(overlay, rect.topleft)
            pygame.draw.rect(
                self.screen,
                boss_pressure_color,
                rect.inflate(-22 if boss_pressure_active else -28, -22 if boss_pressure_active else -28),
                2 if boss_pressure_active else 1,
                border_radius=14,
            )

        for target_id in basic_targets | special_targets:
            unit = self.controller.get_unit(target_id)
            if unit is None:
                continue
            rect = self.tile_rects[unit.position]
            color = (255, 183, 88) if target_id in basic_targets else (255, 129, 129)
            pygame.draw.rect(self.screen, color, rect.inflate(-8, -8), 3, border_radius=18)

        if intent is not None:
            current_threats = set(intent.threat_tiles)
            follow_up_threats = set(intent.follow_up_threat_tiles)
            for threat_tile in intent.phase_threat_tiles:
                if threat_tile in current_threats or threat_tile in follow_up_threats:
                    continue
                rect = self.tile_rects[threat_tile]
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((198, 113, 255, 20))
                self.screen.blit(overlay, rect.topleft)
            for objective_tile in intent.phase_objective_tiles:
                rect = self.tile_rects.get(objective_tile)
                if rect is None:
                    continue
                pygame.draw.rect(self.screen, (255, 122, 122), rect.inflate(-26, -26), 2, border_radius=14)
            for threat_tile in intent.threat_tiles:
                rect = self.tile_rects[threat_tile]
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((255, 86, 86, 38))
                self.screen.blit(overlay, rect.topleft)
            for threat_tile in intent.follow_up_threat_tiles:
                rect = self.tile_rects[threat_tile]
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill((255, 196, 92, 26))
                self.screen.blit(overlay, rect.topleft)
            if intent.move_to is not None:
                move_rect = self.tile_rects[intent.move_to]
                pygame.draw.rect(self.screen, (140, 196, 255), move_rect.inflate(-14, -14), 3, border_radius=18)
            if intent.follow_up_move_to is not None:
                follow_rect = self.tile_rects[intent.follow_up_move_to]
                pygame.draw.rect(self.screen, (240, 205, 120), follow_rect.inflate(-20, -20), 2, border_radius=16)
            if intent.target_tile is not None:
                target_rect = self.tile_rects[intent.target_tile]
                pygame.draw.rect(self.screen, (255, 122, 122), target_rect.inflate(-8, -8), 3, border_radius=18)
                source_tile = intent.move_to or active.position
                pygame.draw.line(
                    self.screen,
                    (255, 208, 151),
                    self._tile_center(source_tile),
                    self._tile_center(intent.target_tile),
                    3,
                )
            if intent.follow_up_target_tile is not None:
                target_rect = self.tile_rects[intent.follow_up_target_tile]
                pygame.draw.rect(self.screen, (255, 204, 117), target_rect.inflate(-16, -16), 2, border_radius=16)
            if intent.phase_focus_target_id is not None:
                focus_unit = self.controller.get_unit(intent.phase_focus_target_id)
                if focus_unit is not None and focus_unit.hp > 0:
                    focus_rect = self.tile_rects[focus_unit.position]
                    pygame.draw.rect(self.screen, (255, 92, 92), focus_rect.inflate(-10, -10), 3, border_radius=18)

        for unit in self.controller.units:
            if unit.hp <= 0:
                continue
            self._draw_battle_unit(unit, active.id == unit.id if active else False)

        pygame.draw.rect(self.screen, (236, 218, 176), GRID_RECT, 1, border_radius=26)

    def _draw_battle_unit(self, unit, is_active: bool) -> None:
        center = self.unit_visual_positions[unit.id]
        tile_rect = self.tile_rects[unit.position]
        accent = hex_to_rgb(unit.accent)
        pulse = 0.2 + 0.2 * self.hit_flash.get(unit.id, 0.0)
        badge_text, badge_color = self._encounter_badge_for_unit(unit)

        shadow_rect = pygame.Rect(0, 0, 64, 18)
        shadow_rect.center = (int(center.x), int(center.y + 28))
        pygame.draw.ellipse(self.screen, (0, 0, 0, 90), shadow_rect)

        if is_active:
            pygame.draw.rect(self.screen, (255, 219, 122), tile_rect.inflate(-12, -12), 3, border_radius=18)

        frame_rect = pygame.Rect(0, 0, 74, 74)
        frame_rect.center = (int(center.x), int(center.y - 2))
        frame_fill = badge_color if badge_text is not None else mix(accent, (255, 255, 255), pulse)
        pygame.draw.rect(self.screen, frame_fill, frame_rect, border_radius=22)
        pygame.draw.rect(self.screen, (255, 244, 217), frame_rect, 2 if badge_text is not None else 1, border_radius=22)

        art = self.champion_art.get(unit.id)
        if art is not None:
            portrait = self._masked_art_surface(art, (66, 66), border_radius=18)
            self.screen.blit(portrait, portrait.get_rect(center=frame_rect.center))
        if badge_text is not None:
            self._draw_text(badge_text, self.font_tiny, (13, 21, 31), (frame_rect.centerx, frame_rect.y + 8), center=True)

        hp_ratio = unit.hp / unit.max_hp
        hp_rect = pygame.Rect(frame_rect.x, frame_rect.y - 14, frame_rect.width, 8)
        pygame.draw.rect(self.screen, (28, 40, 53), hp_rect, border_radius=4)
        pygame.draw.rect(self.screen, (101, 226, 148), (hp_rect.x, hp_rect.y, int(hp_rect.width * hp_ratio), hp_rect.height), border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), hp_rect, 1, border_radius=4)
        if unit.shield > 0:
            self._draw_text(f"보 {unit.shield}", self.font_tiny, (164, 225, 243), (frame_rect.x, frame_rect.bottom + 6))
        if unit.stun_turns > 0:
            self._draw_text("기절", self.font_tiny, (255, 228, 150), (frame_rect.right - 28, frame_rect.bottom + 6))
        self._draw_text(unit.name, self.font_small, (244, 239, 225), (frame_rect.centerx, frame_rect.bottom + 18), center=True)

    def _draw_battle_left_panel(self) -> None:
        active = self.controller.get_active_unit() if self.controller else None
        intent = self.controller.preview_ai_intent() if self.controller and active and active.team == "red" else None
        self._draw_text("전술 브리핑", self.font_heading, (244, 239, 225), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 18))
        self._draw_text(self.status_text, self.font_small, (167, 192, 212), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 54))
        if self.current_route_node is not None:
            node_label = f"런 노드 · {self.current_route_node.name}"
            if self.current_node_follow_up is not None:
                node_label += f" / {self.current_node_follow_up.name}"
            self._draw_text(node_label, self.font_small, (170, 222, 210), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 78))
        elif self.current_route_event is not None:
            self._draw_text(f"전술 이벤트 · {self.current_route_event.name}", self.font_small, (170, 222, 210), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 78))

        info_rect = pygame.Rect(LEFT_PANEL.x + 16, LEFT_PANEL.y + 104, LEFT_PANEL.width - 32, 206)
        pygame.draw.rect(self.screen, (13, 24, 37), info_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), info_rect, 1, border_radius=24)
        if active is not None:
            accent = hex_to_rgb(active.accent)
            portrait_rect = pygame.Rect(info_rect.x + 18, info_rect.y + 18, 92, 92)
            art = self.champion_art.get(active.id)
            pygame.draw.rect(self.screen, accent, portrait_rect, border_radius=24)
            pygame.draw.rect(self.screen, (255, 244, 217), portrait_rect, 1, border_radius=24)
            if art is not None:
                portrait = self._masked_art_surface(art, (84, 84), border_radius=20)
                self.screen.blit(portrait, portrait.get_rect(center=portrait_rect.center))
            self._draw_text(active.name, self.font_heading, (244, 239, 225), (info_rect.x + 128, info_rect.y + 20))
            self._draw_text(active.title, self.font_small, (170, 191, 207), (info_rect.x + 128, info_rect.y + 54))
            encounter_label = active.role
            if active.is_boss:
                encounter_label = f"{active.role} · 보스 결전 각성"
            elif active.is_elite and active.elite_trait_id is not None:
                trait = ELITE_TRAITS_BY_ID.get(active.elite_trait_id)
                if trait is not None:
                    encounter_label = f"{active.role} · 엘리트 {trait.name}"
            self._draw_text(f"{encounter_label} · 체력 {active.hp}/{active.max_hp}", self.font_small, accent, (info_rect.x + 128, info_rect.y + 82))
            self._draw_text(f"이동 {active.move_range}칸 · 속도 {active.speed}", self.font_small, (206, 215, 222), (info_rect.x + 18, info_rect.y + 126))
            self._draw_text(f"기본기: {active.basic_ability.name}", self.font_small, (223, 206, 164), (info_rect.x + 18, info_rect.y + 154))
            special_label = f"특수기: {active.special_ability.name}"
            cooldown = active.cooldowns[active.special_ability.id]
            if cooldown > 0:
                special_label += f" (CD {cooldown})"
            self._draw_text(special_label, self.font_small, (223, 206, 164), (info_rect.x + 18, info_rect.y + 182))
            passive_rect = pygame.Rect(info_rect.x + 16, info_rect.bottom + 16, info_rect.width - 32, 106)
            pygame.draw.rect(self.screen, (11, 20, 31), passive_rect, border_radius=22)
            pygame.draw.rect(self.screen, (236, 218, 176), passive_rect, 1, border_radius=22)
            self._draw_text("패시브", self.font_ui, (229, 210, 164), (passive_rect.x + 16, passive_rect.y + 12))
            self._draw_text(active.passive_name, self.font_ui, accent, (passive_rect.x + 16, passive_rect.y + 42))
            self._draw_wrapped_text(active.passive_description, self.font_small, (208, 219, 226), pygame.Rect(passive_rect.x + 16, passive_rect.y + 68, passive_rect.width - 32, 26), max_lines=2)

        intent_rect = pygame.Rect(LEFT_PANEL.x + 16, LEFT_PANEL.y + 436, LEFT_PANEL.width - 32, 188)
        pygame.draw.rect(self.screen, (11, 20, 31), intent_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), intent_rect, 1, border_radius=24)
        self._draw_text("적 의도", self.font_ui, (229, 210, 164), (intent_rect.x + 18, intent_rect.y + 18))
        if intent is not None:
            self._draw_wrapped_text(intent.summary, self.font_small, (214, 191, 184), pygame.Rect(intent_rect.x + 18, intent_rect.y + 52, intent_rect.width - 36, 42), max_lines=2)
            current_parts = []
            if intent.move_to is not None:
                current_parts.append(f"이동 {intent.move_to}")
            if intent.target_tile is not None:
                current_parts.append(f"대상 {intent.target_tile}")
            if intent.target_count > 1:
                current_parts.append(f"광역 {intent.target_count}명")
            current_parts.append(f"피해 {intent.predicted_damage}")
            if intent.danger_label:
                current_parts.append(f"위험 {intent.danger_label}")
            if intent.objective_pressure_label:
                current_parts.append("목표 압박")
            self._draw_wrapped_text("이번 적 차례 · " + " / ".join(current_parts), self.font_tiny, (255, 213, 150), pygame.Rect(intent_rect.x + 18, intent_rect.y + 102, intent_rect.width - 36, 18), max_lines=1)
            if intent.phase_summary:
                self._draw_wrapped_text(intent.phase_summary, self.font_tiny, (221, 188, 255), pygame.Rect(intent_rect.x + 18, intent_rect.y + 122, intent_rect.width - 36, 32), max_lines=2)
            if intent.follow_up_actor_name:
                next_parts = [f"다음 {intent.follow_up_actor_name}"]
                if intent.follow_up_target_tile is not None:
                    next_parts.append(f"대상 {intent.follow_up_target_tile}")
                if intent.follow_up_target_count > 1:
                    next_parts.append(f"광역 {intent.follow_up_target_count}명")
                next_parts.append(f"피해 {intent.follow_up_predicted_damage}")
                if intent.follow_up_objective_pressure_label:
                    next_parts.append("목표 압박")
                self._draw_wrapped_text(" / ".join(next_parts), self.font_tiny, (242, 201, 133), pygame.Rect(intent_rect.x + 18, intent_rect.y + 158, intent_rect.width - 36, 18), max_lines=1)
        else:
            self._draw_wrapped_text("현재는 플레이어 턴입니다. 적 차례가 오면 이동 칸, 예상 피해, 연속 턴 압박을 미리 보여 줍니다.", self.font_small, (208, 219, 226), pygame.Rect(intent_rect.x + 18, intent_rect.y + 52, intent_rect.width - 36, 72), max_lines=3)

        guide_rect = pygame.Rect(LEFT_PANEL.x + 16, LEFT_PANEL.y + 638, LEFT_PANEL.width - 32, 154)
        pygame.draw.rect(self.screen, (11, 20, 31), guide_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), guide_rect, 1, border_radius=24)
        self._draw_text("조작", self.font_ui, (229, 210, 164), (guide_rect.x + 18, guide_rect.y + 18))
        guides = [
            "1. 이동 버튼 후 파란 칸 클릭",
            "2. 기본기 또는 특수기 선택",
            "3. 사거리 안 적을 클릭해 공격",
            "4. 이동과 행동을 모두 쓰면 자동 종료",
            "5. 승리 시 보상 선택 후 다음 전투 진입",
            "6. E로 턴 종료, ESC로 선택 화면 복귀",
        ]
        for index, line in enumerate(guides):
            self._draw_text(line, self.font_small, (201, 213, 221), (guide_rect.x + 18, guide_rect.y + 44 + index * 18))

    def _draw_battle_right_panel(self) -> None:
        if self.controller is None:
            return
        self._draw_text("전장 현황", self.font_heading, (244, 239, 225), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 18))
        self._draw_text(f"라운드 {self.controller.state.round}", self.font_small, (189, 200, 208), (RIGHT_PANEL.right - 24, RIGHT_PANEL.y + 22), align_right=True)
        blue_header_y = RIGHT_PANEL.y + 62
        if self.run_stage == RUN_STAGE_COUNT:
            boss_unit = self._current_boss_unit()
            boss_profile = self._boss_profile_for_stage(lineup=[unit.id for unit in self.controller.units if unit.team == "red"])
            finale_variant = self._finale_variant_for_stage(lineup=[unit.id for unit in self.controller.units if unit.team == "red"])
            _, _, pressure_label, pressure_description, pressure_active = self._current_boss_pressure_preview()
            phase_label = "결전 각성 완료" if boss_unit is not None and boss_unit.boss_phase_triggered else "결전 각성 전"
            boss_name = boss_unit.name if boss_unit is not None else "보스 대기"
            profile_label = boss_profile.name if boss_profile is not None else "결전 패턴 미확인"
            self._draw_text(f"결전 상태 · {boss_name}", self.font_small, (236, 126, 90), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 58))
            self._draw_text(f"{phase_label} · {profile_label}", self.font_tiny, (255, 213, 150), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 82))
            if finale_variant is not None:
                self._draw_text(f"지형 · {finale_variant.name}", self.font_tiny, (170, 222, 210), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 96))
            if self.current_objective is not None and self.current_objective.is_finale:
                objective_status = "성공" if self.current_objective.completed else "실패" if self.current_objective.failed else f"{self.current_objective.progress}/{self.current_objective.target}"
                self._draw_text(f"결전 목표 · {self.current_objective.name} · {objective_status}", self.font_tiny, (170, 222, 210), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 112))
            if pressure_label is not None:
                pressure_state = "활성" if pressure_active else "예고"
                self._draw_text(f"특수 규칙 · {pressure_label} · {pressure_state}", self.font_tiny, (223, 206, 164), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 128))
                self._draw_wrapped_text(pressure_description or "", self.font_tiny, (192, 207, 220), pygame.Rect(RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 144, RIGHT_PANEL.width - 36, 28), max_lines=2)
            blue_header_y = RIGHT_PANEL.y + 176
        self._draw_text("블루 팀", self.font_ui, (108, 192, 235), (RIGHT_PANEL.x + 18, blue_header_y))
        for index, unit in enumerate([unit for unit in self.controller.units if unit.team == "blue"]):
            self._draw_roster_row(unit, RIGHT_PANEL.x + 18, blue_header_y + 34 + index * 64)

        red_header_y = blue_header_y + 224
        self._draw_text("레드 팀", self.font_ui, (237, 129, 111), (RIGHT_PANEL.x + 18, red_header_y))
        for index, unit in enumerate([unit for unit in self.controller.units if unit.team == "red"]):
            self._draw_roster_row(unit, RIGHT_PANEL.x + 18, red_header_y + 34 + index * 64)

        log_rect = pygame.Rect(RIGHT_PANEL.x + 16, RIGHT_PANEL.bottom - 180, RIGHT_PANEL.width - 32, 164)
        pygame.draw.rect(self.screen, (11, 20, 31), log_rect, border_radius=22)
        pygame.draw.rect(self.screen, (236, 218, 176), log_rect, 1, border_radius=22)
        self._draw_text("최근 로그", self.font_ui, (229, 210, 164), (log_rect.x + 16, log_rect.y + 14))
        for index, line in enumerate(self.controller.state.log[:4]):
            self._draw_wrapped_text(line, self.font_small, (210, 220, 227), pygame.Rect(log_rect.x + 16, log_rect.y + 48 + index * 26, log_rect.width - 28, 22), max_lines=1)

    def _draw_roster_row(self, unit, x: int, y: int) -> None:
        row_rect = pygame.Rect(x, y, RIGHT_PANEL.width - 36, 52)
        pygame.draw.rect(self.screen, (15, 26, 39), row_rect, border_radius=16)
        badge_text, badge_color = self._encounter_badge_for_unit(unit)
        border_color = badge_color if badge_text is not None else (236, 218, 176)
        pygame.draw.rect(self.screen, border_color, row_rect, 1, border_radius=16)
        accent = hex_to_rgb(unit.accent)
        pygame.draw.circle(self.screen, accent, (row_rect.x + 22, row_rect.y + 26), 10)
        self._draw_text(unit.name, self.font_small, (244, 239, 225), (row_rect.x + 44, row_rect.y + 8))
        self._draw_text(f"{unit.hp}/{unit.max_hp}", self.font_tiny, (176, 201, 219), (row_rect.x + 44, row_rect.y + 28))
        status = []
        if unit.shield > 0:
            status.append(f"보호막 {unit.shield}")
        if unit.stun_turns > 0:
            status.append("기절")
        if unit.hp <= 0:
            status.append("전투불능")
        if unit.is_boss:
            status.append("Boss")
        elif unit.is_elite:
            trait = ELITE_TRAITS_BY_ID.get(unit.elite_trait_id or "")
            status.append(f"Elite {trait.name}" if trait is not None else "Elite")
        self._draw_text(" · ".join(status) if status else unit.role, self.font_tiny, accent, (row_rect.right - 12, row_rect.y + 18), align_right=True)

    def _draw_battle_bottom_panel(self) -> None:
        if self.controller is None:
            return
        active = self.controller.get_active_unit()
        if active is None:
            return

        buttons = [
            ("move", "이동", not active.has_moved and active.team == "blue"),
            ("basic", active.basic_ability.name, not active.has_acted and active.team == "blue"),
            ("special", active.special_ability.name, not active.has_acted and active.cooldowns[active.special_ability.id] == 0 and active.team == "blue"),
            ("end", "턴 종료", active.team == "blue"),
        ]
        start_x = BOTTOM_PANEL.x + 18
        for index, (key, label, enabled) in enumerate(buttons):
            rect = pygame.Rect(start_x + index * 250, BOTTOM_PANEL.y + 18, 220, 56)
            self.button_rects[key] = rect
            fill = (214, 182, 112) if enabled else (70, 80, 92)
            text = (13, 21, 31) if enabled else (177, 187, 196)
            if key == "move" and self.mode == "move":
                fill = (104, 191, 234)
            elif key == "basic" and self.mode == "basic":
                fill = (104, 191, 234)
            elif key == "special" and self.mode == "special":
                fill = (104, 191, 234)
            pygame.draw.rect(self.screen, fill, rect, border_radius=18)
            pygame.draw.rect(self.screen, (255, 244, 217), rect, 1, border_radius=18)
            self._draw_text(label, self.font_ui, text, rect.center, center=True)

        info_x = BOTTOM_PANEL.right - 340
        objective = self.current_objective
        if self.current_route_node is not None:
            self._draw_text(f"노드 효과 · {self._node_effect_preview_label(self.current_route_node, self.current_node_follow_up)}", self.font_tiny, (170, 222, 210), (info_x, BOTTOM_PANEL.y + 18))
        else:
            self._draw_text("현재 턴", self.font_small, (223, 206, 164), (info_x, BOTTOM_PANEL.y + 18))
        self._draw_text(active.name, self.font_heading, (244, 239, 225), (info_x, BOTTOM_PANEL.y + 38))
        if active.team == "blue":
            move_state = "완료" if active.has_moved else "가능"
            action_state = "완료" if active.has_acted else "가능"
            self._draw_text(f"이동 {move_state} · 행동 {action_state}", self.font_small, (184, 205, 221), (info_x, BOTTOM_PANEL.y + 48))
            if objective is not None:
                objective_status = "달성" if objective.completed else "실패" if objective.failed else f"{objective.progress}/{objective.target}"
                objective_color = (138, 234, 171) if objective.completed else (235, 156, 140) if objective.failed else (255, 213, 150)
                self._draw_text(f"전술 목표 · {objective.description.replace('목표: ', '')} · {objective_status} · {objective.reward_label}", self.font_tiny, objective_color, (info_x, BOTTOM_PANEL.y + 68))
            else:
                self._draw_text("수풀=보호막 · 룬=피해 +3 · 화염=이동 피해", self.font_small, (174, 208, 235), (info_x, BOTTOM_PANEL.y + 70))
        else:
            self._draw_text("적 AI가 경로와 타겟을 계산 중", self.font_small, (214, 191, 184), (info_x, BOTTOM_PANEL.y + 48))
            if objective is not None:
                objective_status = "달성" if objective.completed else "실패" if objective.failed else f"{objective.progress}/{objective.target}"
                objective_color = (138, 234, 171) if objective.completed else (235, 156, 140) if objective.failed else (255, 213, 150)
                self._draw_text(f"전술 목표 · {objective.description.replace('목표: ', '')} · {objective_status} · {objective.reward_label}", self.font_tiny, objective_color, (info_x, BOTTOM_PANEL.y + 68))
            else:
                self._draw_text("위협 칸과 예상 피해를 보고 대응하세요", self.font_small, (255, 213, 150), (info_x, BOTTOM_PANEL.y + 70))

    def _draw_champion_card(
        self,
        rect: pygame.Rect,
        champion_id: str,
        *,
        selected: bool = False,
        enemy: bool = False,
        compact: bool = False,
        badge: str | None = None,
        footer: str | None = None,
    ) -> None:
        blueprint = BLUEPRINTS_BY_ID[champion_id]
        accent = hex_to_rgb(blueprint.accent)
        top = (14, 24, 37) if not enemy else (28, 18, 18)
        bottom = (20, 32, 46) if not enemy else (40, 23, 22)
        if selected:
            top = (20, 43, 56)
            bottom = (22, 60, 70)
        card = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(card, card.get_rect(), top, bottom)
        pygame.draw.rect(card, (*accent, 22 if not selected else 42), card.get_rect(), border_radius=24)
        pygame.draw.rect(card, (236, 218, 176) if not selected else (108, 224, 203), card.get_rect(), 1, border_radius=24)
        self.screen.blit(card, rect.topleft)

        portrait_size = 72 if compact else 88
        portrait_rect = pygame.Rect(rect.x + 14, rect.y + 14, portrait_size, portrait_size)
        self._draw_portrait_art(champion_id, portrait_rect, accent)
        text_x = portrait_rect.right + 14
        text_width = rect.right - text_x - 14
        if compact:
            self._draw_text(blueprint.name, self.font_ui, (244, 239, 225), (text_x, rect.y + 14))
            self._draw_wrapped_text(blueprint.title, self.font_small, (176, 195, 208), pygame.Rect(text_x, rect.y + 42, text_width, 18), max_lines=1)
            self._draw_text(blueprint.role, self.font_tiny, accent, (text_x, rect.y + 64))
            detail_text = footer or f"체력 {blueprint.max_hp} · 속도 {blueprint.speed}"
            detail_rect = pygame.Rect(text_x, rect.y + 82, text_width, rect.height - 92)
            self._draw_wrapped_text(detail_text, self.font_tiny, (214, 222, 229), detail_rect, max_lines=2 if rect.height >= 124 else 1)
        else:
            self._draw_text(blueprint.name, self.font_ui, (244, 239, 225), (text_x, rect.y + 14))
            self._draw_wrapped_text(blueprint.title, self.font_small, (176, 195, 208), pygame.Rect(text_x, rect.y + 42, text_width, 18), max_lines=1)
            self._draw_text(blueprint.role, self.font_small, accent, (text_x, rect.y + 66))
            self._draw_text(f"체력 {blueprint.max_hp} · 속도 {blueprint.speed}", self.font_tiny, (198, 209, 218), (text_x, rect.y + 88))
            description = footer or f"패시브: {TACTICAL_BLUEPRINTS_BY_ID[champion_id].passive_name}"
            self._draw_wrapped_text(description, self.font_tiny, (214, 222, 229), pygame.Rect(text_x, rect.y + 108, text_width, rect.height - 120), max_lines=2)

        if badge:
            badge_rect = pygame.Rect(rect.right - 44, rect.y + 14, 28, 28)
            pygame.draw.rect(self.screen, (95, 222, 201) if selected else accent, badge_rect, border_radius=10)
            pygame.draw.rect(self.screen, (10, 18, 29), badge_rect, 1, border_radius=10)
            self._draw_text(badge, self.font_small, (10, 18, 29), badge_rect.center, center=True)

    def _draw_terrain_tile(
        self,
        tile: tuple[int, int],
        rect: pygame.Rect,
        terrain_tiles: dict[tuple[int, int], str],
    ) -> None:
        terrain_id = terrain_tiles.get(tile)
        if terrain_id is None:
            return
        terrain = TERRAIN_BY_ID[terrain_id]
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((*hex_to_rgb(terrain.color), 34))
        self.screen.blit(overlay, rect.topleft)
        icon_rect = rect.inflate(-48, -48)
        pygame.draw.rect(self.screen, hex_to_rgb(terrain.color), icon_rect, 2, border_radius=14)
        initial = terrain.name[0]
        self._draw_text(initial, self.font_small, hex_to_rgb(terrain.color), rect.center, center=True)

    def _encounter_badge_for_unit(self, unit) -> tuple[str | None, tuple[int, int, int]]:
        if unit.is_boss:
            if unit.boss_phase_triggered:
                return "A", (255, 180, 92)
            return "B", (236, 126, 90)
        if unit.is_elite:
            trait = ELITE_TRAITS_BY_ID.get(unit.elite_trait_id or "")
            return "E", hex_to_rgb(trait.color) if trait is not None else (214, 182, 112)
        return None, (236, 218, 176)

    def _encounter_badge_for_champion(self, champion_id: str) -> tuple[str | None, tuple[int, int, int]]:
        if champion_id == self._boss_enemy_id_for_stage():
            return "B", (236, 126, 90)
        if champion_id in set(self._elite_enemy_ids_for_stage()):
            trait_id = self._elite_trait_id_for_enemy(champion_id)
            trait = ELITE_TRAITS_BY_ID.get(trait_id or "")
            return "E", hex_to_rgb(trait.color) if trait is not None else (214, 182, 112)
        return None, (236, 218, 176)

    def _draw_static_unit(self, champion_id: str, tile: tuple[int, int], *, selected: bool) -> None:
        center = self._tile_center(tile)
        rect = self.tile_rects[tile]
        blueprint = BLUEPRINTS_BY_ID[champion_id]
        accent = hex_to_rgb(blueprint.accent)
        badge_text, badge_color = self._encounter_badge_for_champion(champion_id)
        shadow_rect = pygame.Rect(0, 0, 64, 18)
        shadow_rect.center = (center[0], center[1] + 28)
        pygame.draw.ellipse(self.screen, (0, 0, 0, 90), shadow_rect)
        if selected:
            pygame.draw.rect(self.screen, (95, 222, 201), rect.inflate(-12, -12), 3, border_radius=18)

        frame_rect = pygame.Rect(0, 0, 74, 74)
        frame_rect.center = (center[0], center[1] - 2)
        frame_fill = badge_color if badge_text is not None else accent
        pygame.draw.rect(self.screen, frame_fill, frame_rect, border_radius=22)
        pygame.draw.rect(self.screen, (255, 244, 217), frame_rect, 2 if badge_text is not None else 1, border_radius=22)
        art = self.champion_art.get(champion_id)
        if art is not None:
            portrait = self._masked_art_surface(art, (66, 66), border_radius=18)
            self.screen.blit(portrait, portrait.get_rect(center=frame_rect.center))
        if badge_text is not None:
            self._draw_text(badge_text, self.font_tiny, (13, 21, 31), (frame_rect.centerx, frame_rect.y + 8), center=True)
        self._draw_text(blueprint.name, self.font_small, (244, 239, 225), (frame_rect.centerx, frame_rect.bottom + 18), center=True)

    def _draw_portrait_art(self, champion_id: str, rect: pygame.Rect, accent: tuple[int, int, int]) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (12, 21, 31), (16, 28, 42))
        pygame.draw.rect(panel, (*accent, 26), panel.get_rect(), border_radius=20)
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=20)
        self.screen.blit(panel, rect.topleft)
        art = self.champion_art.get(champion_id)
        if art is None:
            return
        portrait = self._masked_art_surface(art, (rect.width - 8, rect.height - 8), border_radius=18)
        self.screen.blit(portrait, portrait.get_rect(center=rect.center))

    def _draw_floaters(self) -> None:
        for floater in self.floaters:
            alpha = int(255 * clamp(floater.lifetime / 0.8, 0.0, 1.0))
            rendered = self.font_ui.render(floater.text, True, floater.color)
            rendered.set_alpha(alpha)
            self.screen.blit(rendered, rendered.get_rect(center=(int(floater.x), int(floater.y))))

    def _draw_finale_banner(self) -> None:
        if self.finale_banner_timer <= 0 or self.finale_banner_title is None or self.finale_banner_subtitle is None:
            return
        alpha = int(210 * clamp(self.finale_banner_timer / 1.75, 0.0, 1.0))
        banner_rect = pygame.Rect(WINDOW_WIDTH // 2 - 280, HEADER_RECT.bottom + 18, 560, 82)
        banner = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(
            banner,
            banner.get_rect(),
            mix((12, 21, 31), self.finale_banner_color, 0.24),
            mix((9, 18, 29), self.finale_banner_color, 0.1),
        )
        pygame.draw.rect(banner, (*self.finale_banner_color, 44), banner.get_rect(), border_radius=24)
        pygame.draw.rect(banner, (255, 244, 217), banner.get_rect(), 1, border_radius=24)
        banner.set_alpha(alpha)
        self.screen.blit(banner, banner_rect.topleft)
        self._draw_text(self.finale_banner_title, self.font_heading, (255, 244, 217), (banner_rect.centerx, banner_rect.y + 16), center=True)
        self._draw_text(self.finale_banner_subtitle, self.font_small, (223, 231, 238), (banner_rect.centerx, banner_rect.y + 48), center=True)

    def _draw_battle_intro(self) -> None:
        if self.screen_mode != "battle" or self.battle_intro_card is None:
            return
        intro = self.battle_intro_card
        progress = clamp(intro.timer / 1.65, 0.0, 1.0)
        alpha = int(214 * progress)
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((7, 13, 21, min(120, alpha // 2)))
        self.screen.blit(shade, (0, 0))

        card_rect = pygame.Rect(WINDOW_WIDTH // 2 - 310, WINDOW_HEIGHT // 2 - 128, 620, 212)
        card = pygame.Surface(card_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(
            card,
            card.get_rect(),
            mix((14, 24, 37), intro.color, 0.18),
            mix((9, 18, 29), intro.color, 0.06),
        )
        pygame.draw.rect(card, (*intro.color, 36), card.get_rect(), border_radius=28)
        pygame.draw.rect(card, (255, 244, 217), card.get_rect(), 1, border_radius=28)
        card.set_alpha(alpha)
        self.screen.blit(card, card_rect.topleft)

        slash_rect = pygame.Rect(card_rect.x + 24, card_rect.y + 24, 96, 8)
        pygame.draw.rect(self.screen, intro.color, slash_rect, border_radius=4)
        pygame.draw.rect(self.screen, intro.color, slash_rect.move(0, 14), border_radius=4)
        self._draw_text(intro.title, self.font_title, (255, 244, 217), (card_rect.x + 28, card_rect.y + 46))
        self._draw_wrapped_text(intro.subtitle, self.font_ui, (216, 226, 233), pygame.Rect(card_rect.x + 28, card_rect.y + 94, card_rect.width - 56, 32), max_lines=2)
        for index, line in enumerate(intro.detail_lines[:3]):
            self._draw_wrapped_text(line, self.font_small, (203, 214, 221), pygame.Rect(card_rect.x + 28, card_rect.y + 138 + index * 22, card_rect.width - 56, 18), max_lines=1)

    def _draw_winner_overlay(self) -> None:
        if self.controller is None or not self.controller.state.winner:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 8, 13, 180))
        self.screen.blit(overlay, (0, 0))
        if self.controller.state.winner == "blue":
            title = "원정 성공" if self.run_stage == RUN_STAGE_COUNT else "블루 팀 승리"
            subtitle = "같은 조합으로 새 런을 시작하거나 챔피언 선택으로 돌아갈 수 있습니다." if self.run_stage == RUN_STAGE_COUNT else "다음 행동을 선택하세요."
            rematch_label = "같은 조합 새 런" if self.run_stage == RUN_STAGE_COUNT else "같은 전투 재도전"
        else:
            title = "원정 실패"
            subtitle = "같은 전투에 다시 도전하거나 챔피언 선택으로 돌아갈 수 있습니다."
            rematch_label = "같은 전투 재도전"
        self._draw_text(title, self.font_title, (255, 244, 217), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 62), center=True)
        self._draw_text(subtitle, self.font_ui, (208, 219, 226), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 4), center=True)
        if self.run_stage == RUN_STAGE_COUNT and self.last_objective_summary:
            self._draw_text(self.last_objective_summary, self.font_small, (255, 213, 150), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 22), center=True)

        button_y = WINDOW_HEIGHT // 2 + 58 if self.run_stage == RUN_STAGE_COUNT and self.last_objective_summary else WINDOW_HEIGHT // 2 + 44
        rematch_rect = pygame.Rect(WINDOW_WIDTH // 2 - 238, button_y, 220, 56)
        select_rect = pygame.Rect(WINDOW_WIDTH // 2 + 18, button_y, 220, 56)
        self.button_rects["winner-rematch"] = rematch_rect
        self.button_rects["winner-select"] = select_rect

        pygame.draw.rect(self.screen, (70, 80, 92), rematch_rect, border_radius=18)
        pygame.draw.rect(self.screen, (255, 244, 217), rematch_rect, 1, border_radius=18)
        self._draw_text(rematch_label, self.font_ui, (231, 236, 240), rematch_rect.center, center=True)

        pygame.draw.rect(self.screen, (214, 182, 112), select_rect, border_radius=18)
        pygame.draw.rect(self.screen, (255, 244, 217), select_rect, 1, border_radius=18)
        self._draw_text("캐릭터 다시 선택", self.font_ui, (13, 21, 31), select_rect.center, center=True)

        shortcut_line = "Enter 또는 ESC로 선택 화면 복귀 · R로 즉시 새 런" if self.controller.state.winner == "blue" and self.run_stage == RUN_STAGE_COUNT else "Enter 또는 ESC로 선택 화면 복귀 · R로 즉시 재대결"
        self._draw_text(shortcut_line, self.font_small, (208, 219, 226), (WINDOW_WIDTH // 2, button_y + 72), center=True)

    def _tile_center(self, tile: tuple[int, int]) -> tuple[int, int]:
        return (
            GRID_RECT.x + tile[0] * GRID_CELL + GRID_CELL // 2,
            GRID_RECT.y + tile[1] * GRID_CELL + GRID_CELL // 2,
        )

    def _tile_from_screen(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not GRID_RECT.collidepoint(position):
            return None
        x = (position[0] - GRID_RECT.x) // GRID_CELL
        y = (position[1] - GRID_RECT.y) // GRID_CELL
        tile = (int(x), int(y))
        return tile if tile in self.tile_rects else None

    def _unit_at_tile(self, tile: tuple[int, int]):
        if self.controller is None:
            return None
        for unit in self.controller.units:
            if unit.hp > 0 and unit.position == tile:
                return unit
        return None

    def _masked_art_surface(self, art: pygame.Surface, size: tuple[int, int], *, border_radius: int = 18) -> pygame.Surface:
        scaled = pygame.transform.smoothscale(art, size)
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
        output = pygame.Surface(size, pygame.SRCALPHA)
        output.blit(scaled, (0, 0))
        output.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return output

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int] | pygame.Vector2,
        *,
        center: bool = False,
        align_right: bool = False,
    ) -> None:
        rendered = font.render(text, True, color)
        if center:
            rect = rendered.get_rect(center=position)
        elif align_right:
            rect = rendered.get_rect(topright=position)
        else:
            rect = rendered.get_rect(topleft=position)
        self.screen.blit(rendered, rect)

    def _draw_wrapped_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
        *,
        max_lines: int | None = None,
    ) -> None:
        lines = self._wrap_text(text, font, rect.width, max_lines=max_lines)
        for index, line in enumerate(lines):
            self.screen.blit(font.render(line, True, color), (rect.x, rect.y + index * font.get_linesize()))

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int, *, max_lines: int | None = None) -> list[str]:
        lines: list[str] = []
        current = ""
        for char in text:
            candidate = current + char
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = char.lstrip()
                if max_lines is not None and len(lines) >= max_lines:
                    return lines
                continue
            current = candidate
        if current:
            lines.append(current)
        return lines[:max_lines] if max_lines is not None else lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rift Tactics grid tactics prototype")
    parser.add_argument("--frames", type=int, default=None, help="Run only for a fixed number of frames")
    parser.add_argument("--headless", action="store_true", help="Use a hidden window for smoke tests")
    parser.add_argument("--screenshot", type=str, default=None, help="Save the last rendered frame to a PNG path")
    parser.add_argument("--history-path", type=str, default=None, help="Override the saved run-history JSON path")
    return parser
