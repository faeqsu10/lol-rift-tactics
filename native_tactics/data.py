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
    basic_ability: TacticalAbility
    special_ability: TacticalAbility


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
