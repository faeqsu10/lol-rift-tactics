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


@dataclass(frozen=True)
class EliteTrait:
    id: str
    name: str
    description: str
    color: str


TERRAIN_BY_ID: dict[TerrainId, TacticalTerrain] = {
    "brush": TacticalTerrain("brush", "수풀", "턴 시작 시 보호막 4를 얻습니다.", "#5f9f78"),
    "rune": TacticalTerrain("rune", "룬 지대", "턴 시작 시 이번 턴 피해가 3 증가합니다.", "#6fa9d8"),
    "hazard": TacticalTerrain("hazard", "화염 지대", "이동해 들어오면 즉시 피해 6을 받습니다.", "#d46d4f"),
}

ELITE_TRAITS_BY_ID: dict[str, EliteTrait] = {
    "bulwark": EliteTrait("bulwark", "철벽", "턴 시작 시 보호막 6을 얻습니다.", "#d7bc73"),
    "relentless": EliteTrait("relentless", "맹추격", "이번 턴 2칸 이상 이동 후 공격하면 피해가 4 증가합니다.", "#d76f6f"),
    "spellburst": EliteTrait("spellburst", "비전 폭주", "특수기 피해가 4 증가하고 턴 시작 시 이번 턴 피해 +2를 얻습니다.", "#7aa9e7"),
}

ROLE_ELITE_TRAIT_ID: dict[str, str] = {
    "Vanguard": "bulwark",
    "Mage": "spellburst",
    "Marksman": "relentless",
    "Assassin": "relentless",
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
    "blue-garen": ("선봉 결의", "이번 턴 이동하지 않았다면 공격 피해가 4 증가합니다. 심판으로 둘 이상 적중하면 보호막 6을 얻습니다."),
    "blue-ahri": ("매혹의 사냥", "체력이 가득 찬 적에게 주는 피해가 5 증가합니다. 고립 대상에게 혼령 질주를 쓰면 재사용 대기시간이 1 줄어듭니다."),
    "blue-jinx": ("들뜬 광기", "적을 처치하면 즉시 보호막 10을 얻습니다. 초강력 초토화 로켓이 둘 이상 맞으면 보호막 6을 추가로 얻습니다."),
    "blue-lux": ("광채 잔향", "최후의 섬광을 쓰면 자신에게 보호막 8을 부여하고 현재 칸을 룬 지대로 바꿉니다."),
    "blue-vi": ("추격 압박", "이번 턴 2칸 이상 이동했다면 공격 피해가 6 증가합니다. 정지 명령의 기절이 1턴 늘어납니다."),
    "blue-ezreal": ("원거리 조준", "거리 3칸 이상에서 가한 피해가 4 증가합니다. 기본기 적중 시 정조준 일격 재사용 대기시간이 1 줄어듭니다."),
    "blue-leona": ("여명의 수호", "보호막이 있는 상태로 인접 공격하면 피해가 3 증가합니다. 태양 폭발이 둘 이상 맞으면 모두 1턴 기절합니다."),
    "blue-ashe": ("서리 노출", "거리 3칸 이상에서 가한 피해가 3 증가합니다. 먼 거리에서 수정화살을 맞히면 기절이 1턴 늘어납니다."),
    "blue-braum": ("불굴", "턴 시작 시 보호막 12를 얻습니다. 공격 후 상대가 기절 상태면 보호막 6을 추가로 얻습니다."),
    "red-darius": ("학살 본능", "체력이 절반 이하인 적에게 주는 피해가 5 증가합니다. 녹서스의 단두대로 처치하면 보호막 12를 얻습니다."),
    "red-annie": ("화염 점화", "보호막이 없는 적에게 티버 피해가 4 증가합니다. 티버가 둘 이상 맞으면 보호막 8을 얻습니다."),
    "red-caitlyn": ("헤드샷", "거리 4칸 이상 기본기 피해가 4 증가합니다. 기절한 적을 노리면 피해가 2 더 증가합니다."),
    "red-morgana": ("칠흑 보호", "영혼의 족쇄를 쓰면 자신에게 보호막 10을 얻습니다. 둘 이상 맞히면 보호막 6을 추가로 얻습니다."),
    "red-yasuo": ("질풍", "이번 턴 2칸 이상 이동했다면 공격 피해가 6 증가합니다. 기절한 적에게는 피해가 4 더 증가합니다."),
    "red-zed": ("그림자 암살", "인접한 아군이 없는 적에게 주는 피해가 6 증가합니다. 죽음의 표식으로 고립 대상을 맞히면 보호막 6과 재사용 대기시간 1 감소를 얻습니다."),
    "red-lissandra": ("냉기 균열", "기절한 적에게 주는 피해가 5 증가합니다. 얼음 무덤이 기절한 적에게 닿으면 기절을 1턴 연장합니다."),
    "red-katarina": ("연쇄 참수", "적을 처치하면 즉시 보호막 10을 얻습니다. 죽음의 연꽃이 둘 이상 맞으면 보호막 6을 추가로 얻습니다."),
    "red-brand": ("확산 화염", "파멸의 불덩이 피해가 3 증가합니다. 맞은 타일을 화염 지대로 바꿉니다."),
}

TACTICAL_ABILITY_OVERRIDES: dict[tuple[str, str], dict[str, int]] = {
    ("blue-braum", "winters-bite"): {"cast_range": 2},
    ("blue-ezreal", "mystic-shot"): {"cast_range": 5},
    ("blue-ezreal", "trueshot-barrage"): {"cast_range": 5},
    ("blue-lux", "final-spark"): {"cast_range": 5},
    ("blue-vi", "cease-and-desist"): {"cast_range": 3},
    ("red-caitlyn", "piltover-peacemaker"): {"cast_range": 5},
    ("red-caitlyn", "ace-in-the-hole"): {"cast_range": 5},
    ("red-darius", "noxian-guillotine"): {"cast_range": 2},
    ("red-zed", "death-mark"): {"cast_range": 3},
    ("red-brand", "pyroclasm"): {"cast_range": 5},
}

TACTICAL_SPECIAL_ABILITY_IDS: dict[str, str] = {
    "blue-garen": "judgment",
    "blue-ahri": "charm",
    "blue-jinx": "super-mega-death-rocket",
    "blue-lux": "final-spark",
    "blue-vi": "cease-and-desist",
    "blue-ezreal": "trueshot-barrage",
    "blue-leona": "solar-flare",
    "blue-ashe": "enchanted-crystal-arrow",
    "blue-braum": "glacial-fissure",
    "red-darius": "noxian-guillotine",
    "red-annie": "summon-tibbers",
    "red-caitlyn": "ace-in-the-hole",
    "red-morgana": "soul-shackles",
    "red-yasuo": "last-breath",
    "red-zed": "death-mark",
    "red-lissandra": "frozen-tomb",
    "red-katarina": "death-lotus",
    "red-brand": "pyroclasm",
}


def _damage_total(effects: tuple[AbilityEffect, ...]) -> int:
    return sum(effect.amount for effect in effects if effect.kind == "damage")


def _pick_special_ability(blueprint: ChampionBlueprint):
    preferred_id = TACTICAL_SPECIAL_ABILITY_IDS.get(blueprint.id)
    if preferred_id is not None:
        for ability in blueprint.abilities:
            if ability.id == preferred_id:
                return ability

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
    tactical_ability = TacticalAbility(
        id=ability.id,
        name=ability.name,
        description=ability.description,
        cooldown=0,
        target_mode="enemy",
        cast_range=ROLE_BASIC_RANGE[blueprint.role],
        area_radius=0,
        effects=ability.effects,
    )
    return _apply_tactical_override(blueprint.id, tactical_ability)


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

    tactical_ability = TacticalAbility(
        id=ability.id,
        name=ability.name,
        description=ability.description,
        cooldown=ability.cooldown,
        target_mode=target_mode,
        cast_range=cast_range,
        area_radius=area_radius,
        effects=ability.effects,
    )
    return _apply_tactical_override(blueprint.id, tactical_ability)


def _apply_tactical_override(champion_id: str, ability: TacticalAbility) -> TacticalAbility:
    override = TACTICAL_ABILITY_OVERRIDES.get((champion_id, ability.id))
    if override is None:
        return ability
    return TacticalAbility(
        id=ability.id,
        name=ability.name,
        description=ability.description,
        cooldown=override.get("cooldown", ability.cooldown),
        target_mode=ability.target_mode,
        cast_range=override.get("cast_range", ability.cast_range),
        area_radius=override.get("area_radius", ability.area_radius),
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
