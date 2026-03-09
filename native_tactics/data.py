from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from typing import Literal

from native_game.data import BLUEPRINTS_BY_ID
from native_game.data import DEFAULT_BLUE_IDS
from native_game.data import DEFAULT_RED_IDS
from native_game.data import SELECTABLE_BLUE_IDS
from native_game.data import SELECTABLE_RED_IDS
from native_game.data import AbilityEffect
from native_game.data import ChampionBlueprint

GridPos = tuple[int, int]
TacticalTargetMode = Literal["enemy", "self"]
TerrainId = Literal["brush", "rune", "hazard"]

GRID_WIDTH = 8
GRID_HEIGHT = 6
BLOCKED_TILES: tuple[GridPos, ...] = ((3, 0), (3, 5), (4, 1), (4, 4))
DEFAULT_BLUE_DEPLOY_TILES: tuple[GridPos, ...] = ((0, 1), (0, 3), (0, 5))
DEFAULT_RED_DEPLOY_TILES: tuple[GridPos, ...] = ((7, 1), (7, 3), (7, 5))

ART_FILE_BY_UNIT_ID: dict[str, str] = {
    "blue-garen": "Garen.png",
    "blue-ahri": "Ahri.png",
    "blue-jinx": "Jinx.png",
    "blue-lux": "Lux.png",
    "blue-vi": "Vi.png",
    "blue-ezreal": "Ezreal.png",
    "blue-leona": "Leona.png",
    "blue-ashe": "Ashe.png",
    "blue-braum": "Braum.png",
    "red-darius": "Darius.png",
    "red-annie": "Annie.png",
    "red-caitlyn": "Caitlyn.png",
    "red-morgana": "Morgana.png",
    "red-yasuo": "Yasuo.png",
    "red-zed": "Zed.png",
    "red-lissandra": "Lissandra.png",
    "red-katarina": "Katarina.png",
    "red-brand": "Brand.png",
}

ROLE_MOVE_RANGE: dict[str, int] = {
    "Vanguard": 3,
    "Mage": 3,
    "Marksman": 3,
    "Assassin": 4,
}

ROLE_BASIC_RANGE: dict[str, int] = {
    "Vanguard": 1,
    "Mage": 3,
    "Marksman": 4,
    "Assassin": 1,
}


@dataclass(frozen=True)
class TacticalTerrain:
    id: TerrainId
    name: str
    description: str
    color: str


TERRAIN_BY_ID: dict[TerrainId, TacticalTerrain] = {
    "brush": TacticalTerrain("brush", "수풀", "턴 시작 시 보호막 4를 얻습니다.", "#5f9f78"),
    "rune": TacticalTerrain("rune", "룬 지대", "턴 시작 시 이번 턴 피해가 3 증가합니다.", "#6fa9d8"),
    "hazard": TacticalTerrain("hazard", "화염 지대", "이동해 들어오면 즉시 피해 6을 받습니다.", "#d46d4f"),
}

STAGE_TERRAIN_TILES: dict[int, dict[GridPos, TerrainId]] = {
    1: {
        (1, 1): "brush",
        (1, 4): "brush",
        (6, 1): "brush",
        (6, 4): "brush",
        (3, 2): "rune",
        (4, 3): "rune",
    },
    2: {
        (1, 2): "brush",
        (1, 3): "brush",
        (6, 2): "brush",
        (6, 3): "brush",
        (2, 1): "rune",
        (5, 4): "rune",
        (2, 4): "hazard",
        (5, 1): "hazard",
    },
    3: {
        (1, 2): "brush",
        (6, 3): "brush",
        (2, 1): "rune",
        (5, 4): "rune",
        (3, 2): "hazard",
        (4, 2): "hazard",
        (3, 3): "hazard",
        (4, 3): "hazard",
    },
}


@dataclass(frozen=True)
class TacticalAbility:
    id: str
    name: str
    description: str
    cooldown: int
    target_mode: TacticalTargetMode
    cast_range: int
    area_radius: int
    effects: tuple[AbilityEffect, ...]


@dataclass(frozen=True)
class TacticalBlueprint:
    id: str
    name: str
    title: str
    team: str
    role: str
    max_hp: int
    speed: int
    accent: str
    move_range: int
    passive_name: str
    passive_description: str
    basic_ability: TacticalAbility
    special_ability: TacticalAbility


PASSIVE_BY_CHAMPION_ID: dict[str, tuple[str, str]] = {
    "blue-garen": ("선봉 결의", "이번 턴 이동하지 않았다면 공격 피해가 4 증가합니다."),
    "blue-ahri": ("매혹의 사냥", "체력이 가득 찬 적에게 주는 피해가 5 증가합니다."),
    "blue-jinx": ("들뜬 광기", "적을 처치하면 즉시 보호막 10을 얻습니다."),
    "blue-lux": ("광채 잔향", "특수기를 쓰면 자신에게 보호막 8을 부여합니다."),
    "blue-vi": ("추격 압박", "이번 턴 이동했다면 공격 피해가 4 증가합니다."),
    "blue-ezreal": ("원거리 조준", "거리 3칸 이상에서 가한 피해가 4 증가합니다."),
    "blue-leona": ("여명의 수호", "턴 시작 시 보호막 8을 얻습니다."),
    "blue-ashe": ("서리 노출", "거리 3칸 이상에서 가한 피해가 3 증가합니다."),
    "blue-braum": ("불굴", "턴 시작 시 보호막 12를 얻습니다."),
    "red-darius": ("학살 본능", "체력이 절반 이하인 적에게 주는 피해가 5 증가합니다."),
    "red-annie": ("화염 점화", "보호막이 없는 적에게 특수기 피해가 4 증가합니다."),
    "red-caitlyn": ("헤드샷", "거리 4칸 이상 기본기 피해가 4 증가합니다."),
    "red-morgana": ("칠흑 보호", "특수기를 쓰면 자신에게 보호막 10을 부여합니다."),
    "red-yasuo": ("질풍", "이번 턴 이동했다면 공격 피해가 4 증가합니다."),
    "red-zed": ("그림자 암살", "인접한 아군이 없는 적에게 주는 피해가 6 증가합니다."),
    "red-lissandra": ("냉기 균열", "기절한 적에게 주는 피해가 5 증가합니다."),
    "red-katarina": ("연쇄 참수", "적을 처치하면 즉시 보호막 10을 얻습니다."),
    "red-brand": ("확산 화염", "특수기 피해가 3 증가합니다."),
}


def _damage_total(effects: tuple[AbilityEffect, ...]) -> int:
    return sum(effect.amount for effect in effects if effect.kind == "damage")


def _pick_special_ability(blueprint: ChampionBlueprint):
    candidates = blueprint.abilities[1:] or blueprint.abilities[:1]
    return max(
        candidates,
        key=lambda ability: (
            any(effect.kind == "stun" for effect in ability.effects),
            ability.target_type == "all-enemies",
            any(effect.kind == "shield" for effect in ability.effects),
            _damage_total(ability.effects),
            ability.cooldown,
        ),
    )


def _build_basic_ability(blueprint: ChampionBlueprint) -> TacticalAbility:
    ability = blueprint.abilities[0]
    return TacticalAbility(
        id=ability.id,
        name=ability.name,
        description=ability.description,
        cooldown=0,
        target_mode="enemy",
        cast_range=ROLE_BASIC_RANGE[blueprint.role],
        area_radius=0,
        effects=ability.effects,
    )


def _build_special_ability(blueprint: ChampionBlueprint) -> TacticalAbility:
    ability = _pick_special_ability(blueprint)
    if ability.target_type == "self":
        target_mode: TacticalTargetMode = "self"
        cast_range = 0
        area_radius = 0
    elif ability.target_type == "all-enemies":
        target_mode = "enemy"
        cast_range = 4 if blueprint.role in {"Mage", "Marksman"} else 3
        area_radius = 1
    else:
        target_mode = "enemy"
        cast_range = ROLE_BASIC_RANGE[blueprint.role] + (1 if blueprint.role in {"Mage", "Marksman"} else 0)
        area_radius = 0

    return TacticalAbility(
        id=ability.id,
        name=ability.name,
        description=ability.description,
        cooldown=ability.cooldown,
        target_mode=target_mode,
        cast_range=cast_range,
        area_radius=area_radius,
        effects=ability.effects,
    )


def build_tactical_blueprint(champion_id: str) -> TacticalBlueprint:
    blueprint = BLUEPRINTS_BY_ID[champion_id]
    passive_name, passive_description = PASSIVE_BY_CHAMPION_ID[champion_id]
    return TacticalBlueprint(
        id=blueprint.id,
        name=blueprint.name,
        title=blueprint.title,
        team=blueprint.team,
        role=blueprint.role,
        max_hp=blueprint.max_hp,
        speed=blueprint.speed,
        accent=blueprint.accent,
        move_range=ROLE_MOVE_RANGE[blueprint.role],
        passive_name=passive_name,
        passive_description=passive_description,
        basic_ability=_build_basic_ability(blueprint),
        special_ability=_build_special_ability(blueprint),
    )


def build_tactical_blueprints(
    blue_ids: Iterable[str] | None = None,
    red_ids: Iterable[str] | None = None,
) -> tuple[TacticalBlueprint, ...]:
    selected_blue_ids = tuple(blue_ids or DEFAULT_BLUE_IDS)
    selected_red_ids = tuple(red_ids or DEFAULT_RED_IDS)
    return tuple(build_tactical_blueprint(champion_id) for champion_id in (*selected_blue_ids, *selected_red_ids))


TACTICAL_BLUEPRINTS_BY_ID: dict[str, TacticalBlueprint] = {
    champion_id: build_tactical_blueprint(champion_id) for champion_id in BLUEPRINTS_BY_ID
}
