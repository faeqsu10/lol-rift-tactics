from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import count
from typing import Iterable
from typing import Literal

from native_game.data import AbilityEffect
from native_game.data import TeamId

from .data import BLOCKED_TILES
from .data import GRID_HEIGHT
from .data import GRID_WIDTH
from .data import GridPos
from .data import TacticalAbility
from .data import TacticalBlueprint
from .data import build_tactical_blueprints

ActionKind = Literal["move", "basic", "special", "end"]


@dataclass
class TacticalUnit:
    id: str
    name: str
    title: str
    team: TeamId
    role: str
    max_hp: int
    speed: int
    accent: str
    move_range: int
    basic_ability: TacticalAbility
    special_ability: TacticalAbility
    position: GridPos
    hp: int
    shield: int
    stun_turns: int
    cooldowns: dict[str, int]
    has_moved: bool
    has_acted: bool


@dataclass
class TacticalImpact:
    target_id: str
    damage: int = 0
    blocked: int = 0
    shield_gained: int = 0
    stun_applied: int = 0
    defeated: bool = False


@dataclass
class TacticalActionResult:
    actor_id: str
    kind: ActionKind
    ability_name: str | None = None
    start: GridPos | None = None
    end: GridPos | None = None
    impacts: list[TacticalImpact] = field(default_factory=list)
    target_ids: list[str] = field(default_factory=list)


@dataclass
class TacticalState:
    round: int = 1
    turn_queue: list[str] = field(default_factory=list)
    active_unit_id: str | None = None
    winner: TeamId | None = None
    log: list[str] = field(default_factory=list)


def unit_from_blueprint(blueprint: TacticalBlueprint, position: GridPos) -> TacticalUnit:
    return TacticalUnit(
        id=blueprint.id,
        name=blueprint.name,
        title=blueprint.title,
        team=blueprint.team,
        role=blueprint.role,
        max_hp=blueprint.max_hp,
        speed=blueprint.speed,
        accent=blueprint.accent,
        move_range=blueprint.move_range,
        basic_ability=blueprint.basic_ability,
        special_ability=blueprint.special_ability,
        position=position,
        hp=blueprint.max_hp,
        shield=0,
        stun_turns=0,
        cooldowns={blueprint.special_ability.id: 0},
        has_moved=False,
        has_acted=False,
    )


class TacticsController:
    def __init__(
        self,
        blue_ids: Iterable[str] | None = None,
        red_ids: Iterable[str] | None = None,
    ) -> None:
        self.initial_blue_ids = tuple(blue_ids or ())
        self.initial_red_ids = tuple(red_ids or ())
        blue_lineup = tuple(self.initial_blue_ids or ("blue-garen", "blue-ahri", "blue-jinx"))
        red_lineup = tuple(self.initial_red_ids or ("red-darius", "red-annie", "red-caitlyn"))
        blueprints = build_tactical_blueprints(blue_lineup, red_lineup)
        blue_positions: tuple[GridPos, ...] = ((0, 1), (0, 3), (0, 5))
        red_positions: tuple[GridPos, ...] = ((7, 1), (7, 3), (7, 5))
        positions = (*blue_positions[: len(blue_lineup)], *red_positions[: len(red_lineup)])
        self.units = [unit_from_blueprint(blueprint, position) for blueprint, position in zip(blueprints, positions)]
        self.blocked_tiles = set(BLOCKED_TILES)
        self.state = TacticalState(
            round=1,
            turn_queue=self._build_turn_queue(),
            active_unit_id=None,
            winner=None,
            log=["전술 전투 개시. 이동과 행동을 조합하세요."],
        )
        self._log_counter = count(1)
        self._prime_next_turn()

    def reset(self) -> None:
        self.__init__(self.initial_blue_ids or None, self.initial_red_ids or None)

    def get_unit(self, unit_id: str | None) -> TacticalUnit | None:
        if not unit_id:
            return None
        for unit in self.units:
            if unit.id == unit_id:
                return unit
        return None

    def get_active_unit(self) -> TacticalUnit | None:
        return self.get_unit(self.state.active_unit_id)

    def living_units(self) -> list[TacticalUnit]:
        return [unit for unit in self.units if unit.hp > 0]

    def living_team_units(self, team: TeamId) -> list[TacticalUnit]:
        return [unit for unit in self.living_units() if unit.team == team]

    def get_reachable_tiles(self, unit_id: str | None = None) -> set[GridPos]:
        unit = self.get_unit(unit_id) if unit_id else self.get_active_unit()
        if unit is None or unit.hp <= 0 or unit.has_moved:
            return set()

        frontier: deque[tuple[GridPos, int]] = deque([(unit.position, 0)])
        visited = {unit.position}
        reachable: set[GridPos] = set()

        while frontier:
            position, distance = frontier.popleft()
            if distance >= unit.move_range:
                continue

            for neighbor in self._neighbors(position):
                if neighbor in visited or neighbor in self.blocked_tiles:
                    continue
                if self._occupied(neighbor) and neighbor != unit.position:
                    continue
                visited.add(neighbor)
                reachable.add(neighbor)
                frontier.append((neighbor, distance + 1))

        return reachable

    def get_valid_targets(self, ability_kind: Literal["basic", "special"]) -> list[str]:
        actor = self.get_active_unit()
        if actor is None:
            return []

        ability = actor.basic_ability if ability_kind == "basic" else actor.special_ability
        if ability_kind == "special" and actor.cooldowns[ability.id] > 0:
            return []

        if ability.target_mode == "self":
            return [actor.id]

        return [
            unit.id
            for unit in self.living_units()
            if unit.team != actor.team and self.distance(actor.position, unit.position) <= ability.cast_range
        ]

    def move_active(self, destination: GridPos) -> TacticalActionResult | None:
        actor = self.get_active_unit()
        if actor is None or destination not in self.get_reachable_tiles(actor.id):
            return None

        start = actor.position
        actor.position = destination
        actor.has_moved = True
        result = TacticalActionResult(actor_id=actor.id, kind="move", start=start, end=destination)
        self._push_log(f"{actor.name}, {start} -> {destination} 이동.")
        self._auto_finish_turn_if_needed()
        return result

    def use_basic(self, target_id: str) -> TacticalActionResult | None:
        return self._use_ability("basic", target_id)

    def use_special(self, target_id: str | None = None) -> TacticalActionResult | None:
        actor = self.get_active_unit()
        if actor is None:
            return None
        resolved_target = actor.id if actor.special_ability.target_mode == "self" else target_id
        return self._use_ability("special", resolved_target)

    def end_turn(self) -> TacticalActionResult | None:
        actor = self.get_active_unit()
        if actor is None:
            return None
        self.state.turn_queue = self.state.turn_queue[1:]
        result = TacticalActionResult(actor_id=actor.id, kind="end")
        self._prime_next_turn()
        return result

    def run_ai_turn(self) -> list[TacticalActionResult]:
        actor = self.get_active_unit()
        if actor is None or actor.team != "red" or self.state.winner:
            return []

        results: list[TacticalActionResult] = []
        special_targets = self.get_valid_targets("special")
        should_open_with_special = special_targets and (
            actor.special_ability.target_mode != "self" or actor.hp / actor.max_hp <= 0.65
        )
        if should_open_with_special:
            target_id = self._pick_ai_target(actor, special_targets, special=True)
            result = self.use_special(target_id)
            if result:
                results.append(result)

        if actor is self.get_active_unit() and not actor.has_acted:
            basic_targets = self.get_valid_targets("basic")
            if basic_targets:
                result = self.use_basic(self._pick_ai_target(actor, basic_targets))
                if result:
                    results.append(result)

        if actor is self.get_active_unit() and not actor.has_moved:
            destination = self._choose_ai_move(actor)
            if destination is not None and destination != actor.position:
                result = self.move_active(destination)
                if result:
                    results.append(result)

        actor = self.get_active_unit()
        if actor is not None and actor.team == "red" and not actor.has_acted:
            special_targets = self.get_valid_targets("special")
            basic_targets = self.get_valid_targets("basic")
            if special_targets and (actor.special_ability.target_mode != "self" or actor.hp / actor.max_hp <= 0.65):
                result = self.use_special(self._pick_ai_target(actor, special_targets, special=True))
                if result:
                    results.append(result)
            elif basic_targets:
                result = self.use_basic(self._pick_ai_target(actor, basic_targets))
                if result:
                    results.append(result)

        actor = self.get_active_unit()
        if actor is not None and actor.team == "red" and not self.state.winner:
            results.append(self.end_turn())
        return [result for result in results if result is not None]

    def distance(self, a: GridPos, b: GridPos) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _use_ability(self, ability_kind: Literal["basic", "special"], target_id: str | None) -> TacticalActionResult | None:
        actor = self.get_active_unit()
        if actor is None:
            return None

        ability = actor.basic_ability if ability_kind == "basic" else actor.special_ability
        if actor.has_acted:
            return None
        if ability_kind == "special" and actor.cooldowns[ability.id] > 0:
            return None
        if target_id not in self.get_valid_targets(ability_kind):
            return None

        target_ids = self._resolve_targets(actor, ability, target_id)
        impacts = [self._apply_effects(target_unit_id, ability.effects) for target_unit_id in target_ids]
        actor.has_acted = True
        if ability_kind == "special":
            actor.cooldowns[ability.id] = ability.cooldown

        summary = " ".join(self._format_impact_text(self.get_unit(target_unit_id), impact) for target_unit_id, impact in zip(target_ids, impacts))
        self._push_log(f"{actor.name}, {ability.name} 사용. {summary}".strip())
        self._check_winner()
        result = TacticalActionResult(
            actor_id=actor.id,
            kind=ability_kind,
            ability_name=ability.name,
            impacts=impacts,
            target_ids=target_ids,
        )
        self._auto_finish_turn_if_needed()
        return result

    def _resolve_targets(self, actor: TacticalUnit, ability: TacticalAbility, target_id: str | None) -> list[str]:
        if ability.target_mode == "self":
            return [actor.id]

        primary = self.get_unit(target_id)
        if primary is None or primary.hp <= 0:
            return []

        if ability.area_radius <= 0:
            return [primary.id]

        return [
            unit.id
            for unit in self.living_units()
            if unit.team != actor.team and self.distance(primary.position, unit.position) <= ability.area_radius
        ]

    def _apply_effects(self, target_id: str, effects: tuple[AbilityEffect, ...]) -> TacticalImpact:
        target = self.get_unit(target_id)
        if target is None:
            return TacticalImpact(target_id=target_id)

        impact = TacticalImpact(target_id=target_id)
        for effect in effects:
            if effect.kind == "damage":
                blocked = min(target.shield, effect.amount)
                dealt = max(0, effect.amount - blocked)
                target.shield -= blocked
                target.hp = max(0, target.hp - dealt)
                impact.damage += dealt
                impact.blocked += blocked
            elif effect.kind == "shield":
                target.shield += effect.amount
                impact.shield_gained += effect.amount
            elif effect.kind == "stun":
                target.stun_turns = max(target.stun_turns, effect.turns)
                impact.stun_applied = max(impact.stun_applied, effect.turns)

        impact.defeated = target.hp <= 0
        return impact

    def _format_impact_text(self, target: TacticalUnit | None, impact: TacticalImpact) -> str:
        if target is None:
            return ""

        parts: list[str] = []
        if impact.damage:
            parts.append(f"{target.name} {impact.damage} 피해")
        if impact.blocked:
            parts.append(f"보호막 {impact.blocked} 흡수")
        if impact.shield_gained:
            parts.append(f"{target.name} 보호막 {impact.shield_gained}")
        if impact.stun_applied:
            parts.append(f"{target.name} {impact.stun_applied}턴 기절")
        if impact.defeated:
            parts.append(f"{target.name} 쓰러짐")
        return ". ".join(parts) + ("." if parts else "")

    def _check_winner(self) -> None:
        living_teams = {unit.team for unit in self.living_units()}
        if len(living_teams) == 1:
            self.state.winner = next(iter(living_teams))
            self.state.active_unit_id = None
            self.state.turn_queue = []
            self._push_log("블루 팀 승리." if self.state.winner == "blue" else "레드 팀 승리.")

    def _auto_finish_turn_if_needed(self) -> None:
        actor = self.get_active_unit()
        if actor is None or self.state.winner:
            return
        if actor.has_moved and actor.has_acted:
            self.end_turn()

    def _push_log(self, text: str) -> None:
        self.state.log = [f"[{next(self._log_counter):02d}] {text}", *self.state.log[:9]]

    def _build_turn_queue(self) -> list[str]:
        return [
            unit.id
            for unit in sorted(
                self.living_units(),
                key=lambda unit: (-unit.speed, unit.team, unit.id),
            )
        ]

    def _prime_next_turn(self) -> None:
        while True:
            if self.state.winner:
                return

            self.state.turn_queue = [unit_id for unit_id in self.state.turn_queue if (unit := self.get_unit(unit_id)) and unit.hp > 0]
            if not self.state.turn_queue:
                self.state.round += 1
                self.state.turn_queue = self._build_turn_queue()
                self._push_log(f"라운드 {self.state.round} 시작.")

            actor = self.get_unit(self.state.turn_queue[0] if self.state.turn_queue else None)
            if actor is None:
                continue

            actor.has_moved = False
            actor.has_acted = False
            actor.cooldowns[actor.special_ability.id] = max(0, actor.cooldowns[actor.special_ability.id] - 1)

            if actor.stun_turns > 0:
                actor.stun_turns -= 1
                self.state.turn_queue = self.state.turn_queue[1:]
                self._push_log(f"{actor.name}, 기절 상태로 턴을 넘긴다.")
                continue

            self.state.active_unit_id = actor.id
            return

    def _neighbors(self, position: GridPos) -> list[GridPos]:
        x, y = position
        neighbors = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        return [neighbor for neighbor in neighbors if 0 <= neighbor[0] < GRID_WIDTH and 0 <= neighbor[1] < GRID_HEIGHT]

    def _occupied(self, position: GridPos) -> bool:
        return any(unit.position == position and unit.hp > 0 for unit in self.units)

    def _pick_ai_target(self, actor: TacticalUnit, target_ids: list[str], *, special: bool = False) -> str:
        def score(target_id: str) -> tuple[int, int, int]:
            target = self.get_unit(target_id)
            if target is None:
                return (-999, 0, 0)
            stun_bonus = 18 if special and any(effect.kind == "stun" for effect in actor.special_ability.effects) else 0
            low_hp_bonus = max(0, target.max_hp - target.hp)
            speed_bonus = target.speed
            return (stun_bonus + low_hp_bonus, speed_bonus, -self.distance(actor.position, target.position))

        return max(target_ids, key=score)

    def _choose_ai_move(self, actor: TacticalUnit) -> GridPos | None:
        reachable = self.get_reachable_tiles(actor.id)
        if not reachable:
            return None

        enemies = [unit for unit in self.living_units() if unit.team != actor.team]
        if not enemies:
            return None

        def score(tile: GridPos) -> tuple[int, int, int]:
            nearest_distance = min(self.distance(tile, enemy.position) for enemy in enemies)
            special_in_range = any(self.distance(tile, enemy.position) <= actor.special_ability.cast_range for enemy in enemies)
            basic_in_range = any(self.distance(tile, enemy.position) <= actor.basic_ability.cast_range for enemy in enemies)
            return (
                2 if special_in_range else 0,
                1 if basic_in_range else 0,
                -nearest_distance,
            )

        return max(reachable, key=score)
