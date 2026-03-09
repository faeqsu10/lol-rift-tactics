from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import count
from typing import Iterable
from typing import Literal

from native_game.data import AbilityEffect
from native_game.data import TeamId

from .data import BLOCKED_TILES
from .data import DEFAULT_BLUE_DEPLOY_TILES
from .data import DEFAULT_RED_DEPLOY_TILES
from .data import GRID_HEIGHT
from .data import GRID_WIDTH
from .data import GridPos
from .data import TERRAIN_BY_ID
from .data import TacticalAbility
from .data import TacticalBlueprint
from .data import TerrainId
from .data import build_tactical_blueprints

ActionKind = Literal["move", "basic", "special", "end"]


@dataclass
class TacticalUnit:
    id: str
    name: str
    title: str
    team: TeamId
    role: str
    passive_name: str
    passive_description: str
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
    temporary_damage_bonus: int
    is_elite: bool


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
    notes: list[str] = field(default_factory=list)


@dataclass
class TacticalIntent:
    actor_id: str
    actor_name: str
    move_to: GridPos | None
    action_kind: ActionKind | None
    action_name: str | None
    target_id: str | None
    target_tile: GridPos | None
    summary: str
    predicted_damage: int = 0
    threat_tiles: list[GridPos] = field(default_factory=list)


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
        passive_name=blueprint.passive_name,
        passive_description=blueprint.passive_description,
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
        temporary_damage_bonus=0,
        is_elite=False,
    )


class TacticsController:
    def __init__(
        self,
        blue_ids: Iterable[str] | None = None,
        red_ids: Iterable[str] | None = None,
        blue_positions: Iterable[GridPos] | None = None,
        red_positions: Iterable[GridPos] | None = None,
        terrain_tiles: dict[GridPos, TerrainId] | None = None,
        elite_unit_ids: Iterable[str] | None = None,
    ) -> None:
        self.initial_blue_ids = tuple(blue_ids or ())
        self.initial_red_ids = tuple(red_ids or ())
        self.initial_blue_positions = tuple(blue_positions or ())
        self.initial_red_positions = tuple(red_positions or ())
        self.initial_terrain_tiles = dict(terrain_tiles or {})
        self.initial_elite_unit_ids = tuple(elite_unit_ids or ())
        blue_lineup = tuple(self.initial_blue_ids or ("blue-garen", "blue-ahri", "blue-jinx"))
        red_lineup = tuple(self.initial_red_ids or ("red-darius", "red-annie", "red-caitlyn"))
        blueprints = build_tactical_blueprints(blue_lineup, red_lineup)
        resolved_blue_positions = tuple(self.initial_blue_positions or DEFAULT_BLUE_DEPLOY_TILES)[: len(blue_lineup)]
        resolved_red_positions = tuple(self.initial_red_positions or DEFAULT_RED_DEPLOY_TILES)[: len(red_lineup)]
        positions = (*resolved_blue_positions, *resolved_red_positions)
        self.units = [unit_from_blueprint(blueprint, position) for blueprint, position in zip(blueprints, positions)]
        self.blocked_tiles = set(BLOCKED_TILES)
        self.terrain_tiles = dict(self.initial_terrain_tiles)
        self.elite_unit_ids = set(self.initial_elite_unit_ids)
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
        self.__init__(
            self.initial_blue_ids or None,
            self.initial_red_ids or None,
            self.initial_blue_positions or None,
            self.initial_red_positions or None,
            self.initial_terrain_tiles or None,
            self.initial_elite_unit_ids or None,
        )

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
        terrain_impact, terrain_note = self._apply_move_terrain(actor)
        if terrain_impact is not None:
            result.impacts.append(terrain_impact)
        if terrain_note:
            result.notes.append(terrain_note)
        self._push_log(f"{actor.name}, {start} -> {destination} 이동.")
        if terrain_note:
            self._push_log(terrain_note)
        self._check_winner()
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

    def preview_ai_intent(self) -> TacticalIntent | None:
        actor = self.get_active_unit()
        if actor is None or actor.team != "red" or self.state.winner:
            return None

        special_targets = self.get_valid_targets("special")
        should_open_with_special = special_targets and (
            actor.special_ability.target_mode != "self" or actor.hp / actor.max_hp <= 0.65
        )
        if should_open_with_special:
            target_id = self._pick_ai_target(actor, special_targets, special=True)
            target = self.get_unit(target_id)
            threat_tiles, predicted_damage = self._preview_action_outcome(actor, actor.position, actor.special_ability, "special", target_id)
            return TacticalIntent(
                actor_id=actor.id,
                actor_name=actor.name,
                move_to=None,
                action_kind="special",
                action_name=actor.special_ability.name,
                target_id=target_id,
                target_tile=target.position if target else None,
                summary=f"{actor.name}가 {target.name if target else '대상'}에게 {actor.special_ability.name} 사용 예정",
                predicted_damage=predicted_damage,
                threat_tiles=threat_tiles,
            )

        basic_targets = self.get_valid_targets("basic")
        if basic_targets:
            target_id = self._pick_ai_target(actor, basic_targets)
            target = self.get_unit(target_id)
            threat_tiles, predicted_damage = self._preview_action_outcome(actor, actor.position, actor.basic_ability, "basic", target_id)
            return TacticalIntent(
                actor_id=actor.id,
                actor_name=actor.name,
                move_to=None,
                action_kind="basic",
                action_name=actor.basic_ability.name,
                target_id=target_id,
                target_tile=target.position if target else None,
                summary=f"{actor.name}가 {target.name if target else '대상'}에게 {actor.basic_ability.name} 사용 예정",
                predicted_damage=predicted_damage,
                threat_tiles=threat_tiles,
            )

        destination = self._choose_ai_move(actor)
        if destination is None:
            return TacticalIntent(
                actor_id=actor.id,
                actor_name=actor.name,
                move_to=None,
                action_kind="end",
                action_name="대기",
                target_id=None,
                target_tile=None,
                summary=f"{actor.name}가 이동 없이 턴 종료 예정",
            )

        action_kind, action_name, target_id, target_tile = self._predict_follow_up_from_position(actor, destination)
        if action_name and target_id:
            target = self.get_unit(target_id)
            ability = actor.special_ability if action_kind == "special" else actor.basic_ability
            threat_tiles, predicted_damage = self._preview_action_outcome(actor, destination, ability, action_kind, target_id)
            return TacticalIntent(
                actor_id=actor.id,
                actor_name=actor.name,
                move_to=destination,
                action_kind=action_kind,
                action_name=action_name,
                target_id=target_id,
                target_tile=target_tile,
                summary=f"{actor.name}가 {destination}로 이동 후 {target.name if target else '대상'}에게 {action_name} 사용 예정",
                predicted_damage=predicted_damage,
                threat_tiles=threat_tiles,
            )

        return TacticalIntent(
            actor_id=actor.id,
            actor_name=actor.name,
            move_to=destination,
            action_kind="move",
            action_name="이동",
            target_id=None,
            target_tile=None,
            summary=f"{actor.name}가 {destination}로 이동 예정",
        )

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
        impacts: list[TacticalImpact] = []
        notes: list[str] = []
        for target_unit_id in target_ids:
            target = self.get_unit(target_unit_id)
            modified_effects, passive_notes = self._modified_effects(actor, target, ability_kind, ability.effects)
            impact = self._apply_effects(target_unit_id, modified_effects)
            impacts.append(impact)
            notes.extend(passive_notes)
        actor.has_acted = True
        if ability_kind == "special":
            actor.cooldowns[ability.id] = ability.cooldown
        notes.extend(self._apply_post_action_passives(actor, ability_kind, impacts))

        summary = " ".join(self._format_impact_text(self.get_unit(target_unit_id), impact) for target_unit_id, impact in zip(target_ids, impacts))
        log_line = f"{actor.name}, {ability.name} 사용. {summary}".strip()
        if notes:
            log_line = f"{log_line} {' '.join(notes)}".strip()
        self._push_log(log_line)
        self._check_winner()
        result = TacticalActionResult(
            actor_id=actor.id,
            kind=ability_kind,
            ability_name=ability.name,
            impacts=impacts,
            target_ids=target_ids,
            notes=notes,
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

    def _get_valid_targets_for_position(
        self,
        actor: TacticalUnit,
        ability: TacticalAbility,
        position: GridPos,
    ) -> list[str]:
        if ability.target_mode == "self":
            return [actor.id]
        return [
            unit.id
            for unit in self.living_units()
            if unit.team != actor.team and self.distance(position, unit.position) <= ability.cast_range
        ]

    def _predict_follow_up_from_position(
        self,
        actor: TacticalUnit,
        position: GridPos,
    ) -> tuple[ActionKind | None, str | None, str | None, GridPos | None]:
        special_targets = self._get_valid_targets_for_position(actor, actor.special_ability, position)
        should_use_special = special_targets and (
            actor.special_ability.target_mode != "self" or actor.hp / actor.max_hp <= 0.65
        )
        if should_use_special:
            target_id = self._pick_ai_target_from_position(actor, position, special_targets, special=True)
            target = self.get_unit(target_id)
            return ("special", actor.special_ability.name, target_id, target.position if target else None)

        basic_targets = self._get_valid_targets_for_position(actor, actor.basic_ability, position)
        if basic_targets:
            target_id = self._pick_ai_target_from_position(actor, position, basic_targets)
            target = self.get_unit(target_id)
            return ("basic", actor.basic_ability.name, target_id, target.position if target else None)

        return (None, None, None, None)

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

    def _modified_effects(
        self,
        actor: TacticalUnit,
        target: TacticalUnit | None,
        ability_kind: Literal["basic", "special"],
        effects: tuple[AbilityEffect, ...],
        source_position: GridPos | None = None,
    ) -> tuple[tuple[AbilityEffect, ...], list[str]]:
        if target is None:
            return effects, []

        bonus_damage = 0
        notes: list[str] = []
        origin = source_position or actor.position
        distance = self.distance(origin, target.position)

        if actor.temporary_damage_bonus > 0:
            bonus_damage += actor.temporary_damage_bonus
            notes.append("룬 지대 강화 발동.")

        if actor.id == "blue-garen" and not actor.has_moved:
            bonus_damage += 4
            notes.append("선봉 결의 발동.")
        elif actor.id == "blue-ahri" and target.hp == target.max_hp:
            bonus_damage += 5
            notes.append("매혹의 사냥 발동.")
        elif actor.id == "blue-vi" and actor.has_moved:
            bonus_damage += 4
            notes.append("추격 압박 발동.")
        elif actor.id == "blue-ezreal" and distance >= 3:
            bonus_damage += 4
            notes.append("원거리 조준 발동.")
        elif actor.id == "blue-ashe" and distance >= 3:
            bonus_damage += 3
            notes.append("서리 노출 발동.")
        elif actor.id == "red-darius" and target.hp <= target.max_hp // 2:
            bonus_damage += 5
            notes.append("학살 본능 발동.")
        elif actor.id == "red-annie" and ability_kind == "special" and target.shield <= 0:
            bonus_damage += 4
            notes.append("화염 점화 발동.")
        elif actor.id == "red-caitlyn" and ability_kind == "basic" and distance >= 4:
            bonus_damage += 4
            notes.append("헤드샷 발동.")
        elif actor.id == "red-yasuo" and actor.has_moved:
            bonus_damage += 4
            notes.append("질풍 발동.")
        elif actor.id == "red-zed" and self._is_isolated(target):
            bonus_damage += 6
            notes.append("그림자 암살 발동.")
        elif actor.id == "red-lissandra" and target.stun_turns > 0:
            bonus_damage += 5
            notes.append("냉기 균열 발동.")
        elif actor.id == "red-brand" and ability_kind == "special":
            bonus_damage += 3
            notes.append("확산 화염 발동.")

        if bonus_damage <= 0:
            return effects, notes

        boosted_effects = tuple(
            AbilityEffect(kind=effect.kind, amount=effect.amount + bonus_damage, turns=effect.turns)
            if effect.kind == "damage"
            else effect
            for effect in effects
        )
        return boosted_effects, notes

    def _apply_post_action_passives(
        self,
        actor: TacticalUnit,
        ability_kind: Literal["basic", "special"],
        impacts: list[TacticalImpact],
    ) -> list[str]:
        notes: list[str] = []
        defeated_any = any(impact.defeated for impact in impacts)

        if actor.id in {"blue-jinx", "red-katarina"} and defeated_any:
            actor.shield += 10
            notes.append(f"{actor.passive_name} 발동.")
        if actor.id == "blue-lux" and ability_kind == "special":
            actor.shield += 8
            notes.append("광채 잔향 발동.")
        if actor.id == "red-morgana" and ability_kind == "special":
            actor.shield += 10
            notes.append("칠흑 보호 발동.")
        return notes

    def _apply_turn_start_passives(self, actor: TacticalUnit) -> None:
        if actor.id == "blue-leona":
            actor.shield += 8
            self._push_log(f"{actor.name}, {actor.passive_name}으로 보호막 8 획득.")
        elif actor.id == "blue-braum":
            actor.shield += 12
            self._push_log(f"{actor.name}, {actor.passive_name}으로 보호막 12 획득.")

    def _terrain_at(self, position: GridPos) -> TerrainId | None:
        return self.terrain_tiles.get(position)

    def _apply_turn_start_terrain(self, actor: TacticalUnit) -> None:
        actor.temporary_damage_bonus = 0
        terrain_id = self._terrain_at(actor.position)
        if terrain_id == "brush":
            actor.shield += 4
            self._push_log(f"{actor.name}, 수풀에서 보호막 4 획득.")
        elif terrain_id == "rune":
            actor.temporary_damage_bonus = 3
            self._push_log(f"{actor.name}, 룬 지대의 힘으로 이번 턴 피해 +3.")

    def _apply_move_terrain(self, actor: TacticalUnit) -> tuple[TacticalImpact | None, str | None]:
        terrain_id = self._terrain_at(actor.position)
        if terrain_id != "hazard":
            return None, None
        damage = 6
        actor.hp = max(0, actor.hp - damage)
        impact = TacticalImpact(target_id=actor.id, damage=damage, defeated=actor.hp <= 0)
        return impact, f"{actor.name}, 화염 지대를 밟아 {damage} 피해."

    def _resolve_targets_from_position(
        self,
        actor: TacticalUnit,
        ability: TacticalAbility,
        target_id: str | None,
        source_position: GridPos,
    ) -> list[str]:
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

    def _preview_action_outcome(
        self,
        actor: TacticalUnit,
        source_position: GridPos,
        ability: TacticalAbility,
        ability_kind: Literal["basic", "special"],
        target_id: str | None,
    ) -> tuple[list[GridPos], int]:
        threat_tiles: list[GridPos] = []
        predicted_damage = 0
        for resolved_target_id in self._resolve_targets_from_position(actor, ability, target_id, source_position):
            target = self.get_unit(resolved_target_id)
            if target is None:
                continue
            modified_effects, _ = self._modified_effects(actor, target, ability_kind, ability.effects, source_position)
            threat_tiles.append(target.position)
            predicted_damage += self._estimate_damage(target, modified_effects)
        return threat_tiles, predicted_damage

    def _estimate_damage(self, target: TacticalUnit, effects: tuple[AbilityEffect, ...]) -> int:
        shield = target.shield
        total = 0
        for effect in effects:
            if effect.kind != "damage":
                continue
            blocked = min(shield, effect.amount)
            dealt = max(0, effect.amount - blocked)
            shield -= blocked
            total += dealt
        return total

    def _is_isolated(self, target: TacticalUnit) -> bool:
        for unit in self.living_units():
            if unit.id == target.id or unit.team != target.team:
                continue
            if self.distance(unit.position, target.position) == 1:
                return False
        return True

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
            actor.temporary_damage_bonus = 0
            actor.cooldowns[actor.special_ability.id] = max(0, actor.cooldowns[actor.special_ability.id] - 1)

            if actor.stun_turns > 0:
                actor.stun_turns -= 1
                self.state.turn_queue = self.state.turn_queue[1:]
                self._push_log(f"{actor.name}, 기절 상태로 턴을 넘긴다.")
                continue

            self._apply_turn_start_terrain(actor)
            self._apply_turn_start_passives(actor)
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

    def _pick_ai_target_from_position(
        self,
        actor: TacticalUnit,
        position: GridPos,
        target_ids: list[str],
        *,
        special: bool = False,
    ) -> str:
        def score(target_id: str) -> tuple[int, int, int]:
            target = self.get_unit(target_id)
            if target is None:
                return (-999, 0, 0)
            stun_bonus = 18 if special and any(effect.kind == "stun" for effect in actor.special_ability.effects) else 0
            low_hp_bonus = max(0, target.max_hp - target.hp)
            speed_bonus = target.speed
            return (stun_bonus + low_hp_bonus, speed_bonus, -self.distance(position, target.position))

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
