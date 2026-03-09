from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from typing import Iterable

from .data import ALL_BLUEPRINTS, Ability, AbilityEffect, ChampionBlueprint, TargetType, TeamId


@dataclass
class CombatUnit:
    id: str
    name: str
    title: str
    role: str
    team: TeamId
    max_hp: int
    speed: int
    accent: str
    abilities: tuple[Ability, ...]
    hp: int
    shield: int
    stun_turns: int
    cooldowns: dict[str, int]


@dataclass
class ActionImpact:
    target_id: str
    effect_kinds: list[str] = field(default_factory=list)
    damage_dealt: int = 0
    shield_gained: int = 0
    stun_turns_applied: int = 0
    blocked_damage: int = 0
    defeated: bool = False


@dataclass
class BattleAction:
    id: str
    actor_id: str
    actor_team: TeamId
    ability_id: str
    ability_name: str
    target_type: TargetType
    target_ids: list[str]
    impacts: list[ActionImpact]


@dataclass
class BattleState:
    round: int = 1
    turn_queue: list[str] = field(default_factory=list)
    active_unit_id: str | None = None
    winner: TeamId | None = None
    log: list[str] = field(default_factory=list)
    last_action: BattleAction | None = None


def unit_from_blueprint(blueprint: ChampionBlueprint) -> CombatUnit:
    return CombatUnit(
        id=blueprint.id,
        name=blueprint.name,
        title=blueprint.title,
        role=blueprint.role,
        team=blueprint.team,
        max_hp=blueprint.max_hp,
        speed=blueprint.speed,
        accent=blueprint.accent,
        abilities=blueprint.abilities,
        hp=blueprint.max_hp,
        shield=0,
        stun_turns=0,
        cooldowns={ability.id: 0 for ability in blueprint.abilities},
    )


class BattleController:
    def __init__(self) -> None:
        self.units = [unit_from_blueprint(blueprint) for blueprint in ALL_BLUEPRINTS]
        self.state = BattleState(
            round=1,
            turn_queue=self._build_turn_queue(),
            active_unit_id=None,
            winner=None,
            log=["전투 개시. 전장으로 돌입합니다."],
            last_action=None,
        )
        self._log_counter = count(1)
        self._action_counter = count(1)
        self._prime_next_turn()

    def reset(self) -> None:
        self.__init__()

    def get_unit(self, unit_id: str | None) -> CombatUnit | None:
        if not unit_id:
            return None

        for unit in self.units:
            if unit.id == unit_id:
                return unit
        return None

    def get_active_unit(self) -> CombatUnit | None:
        return self.get_unit(self.state.active_unit_id)

    def get_valid_target_ids(self, ability_id: str) -> list[str]:
        actor = self.get_active_unit()
        if actor is None:
            return []

        ability = self._find_ability(actor, ability_id)
        if ability is None or actor.cooldowns[ability.id] > 0:
            return []

        return self._resolve_targets(actor, ability, None)

    def create_preview_action(self, ability_id: str, target_id: str | None = None) -> BattleAction | None:
        actor = self.get_active_unit()
        if actor is None:
            return None

        ability = self._find_ability(actor, ability_id)
        if ability is None:
            return None

        target_ids = self._resolve_targets(actor, ability, target_id)
        effect_kinds = list(dict.fromkeys(effect.kind for effect in ability.effects))
        return BattleAction(
            id=f"preview-{next(self._action_counter)}",
            actor_id=actor.id,
            actor_team=actor.team,
            ability_id=ability.id,
            ability_name=ability.name,
            target_type=ability.target_type,
            target_ids=target_ids,
            impacts=[
                ActionImpact(target_id=resolved_target_id, effect_kinds=effect_kinds[:])
                for resolved_target_id in target_ids
            ],
        )

    def plan_enemy_turn(self) -> tuple[str, str | None] | None:
        actor = self.get_active_unit()
        if actor is None or actor.team != "red" or self.state.winner:
            return None

        available = [ability for ability in actor.abilities if actor.cooldowns[ability.id] == 0]
        if not available:
            available = list(actor.abilities)

        chosen = sorted(available, key=lambda ability: self._score_ability(actor, ability), reverse=True)[0]
        target_id = self._choose_enemy_target(actor) if chosen.target_type == "enemy" else None
        return chosen.id, target_id

    def resolve_active_turn(self, ability_id: str, target_id: str | None = None) -> BattleAction | None:
        actor = self.get_active_unit()
        if actor is None or self.state.winner:
            return None

        ability = self._find_ability(actor, ability_id)
        if ability is None or actor.cooldowns[ability.id] > 0:
            return None

        target_ids = self._resolve_targets(actor, ability, target_id)
        if not target_ids:
            return None

        impact_map: dict[str, ActionImpact] = {}
        summaries: list[str] = []

        for resolved_target_id in target_ids:
            for effect in ability.effects:
                summary, impact = self._apply_effect(resolved_target_id, effect)
                if summary:
                    summaries.append(summary)
                existing = impact_map.setdefault(
                    resolved_target_id,
                    ActionImpact(target_id=resolved_target_id),
                )
                if impact.kind not in existing.effect_kinds:
                    existing.effect_kinds.append(impact.kind)
                existing.damage_dealt += impact.damage_dealt
                existing.shield_gained += impact.shield_gained
                existing.stun_turns_applied += impact.stun_turns_applied
                existing.blocked_damage += impact.blocked_damage
                existing.defeated = existing.defeated or impact.defeated

        actor.cooldowns[ability.id] = ability.cooldown
        self.state.turn_queue = self.state.turn_queue[1:]
        action = BattleAction(
            id=f"action-{next(self._action_counter)}",
            actor_id=actor.id,
            actor_team=actor.team,
            ability_id=ability.id,
            ability_name=ability.name,
            target_type=ability.target_type,
            target_ids=target_ids,
            impacts=[impact_map[target_id] for target_id in target_ids if target_id in impact_map],
        )
        self.state.last_action = action
        self._push_log(f"{actor.name}, {ability.name} 사용. {' '.join(summaries)}")

        winner = self._get_winner()
        if winner:
            self.state.winner = winner
            self.state.active_unit_id = None
            self.state.turn_queue = []
            self._push_log("블루 팀 승리." if winner == "blue" else "레드 팀 승리.")
            return action

        self._prime_next_turn()
        return action

    def _push_log(self, text: str) -> None:
        prefixed = f"[{next(self._log_counter):02d}] {text}"
        self.state.log = [prefixed, *self.state.log[:10]]

    def _find_ability(self, actor: CombatUnit, ability_id: str) -> Ability | None:
        for ability in actor.abilities:
            if ability.id == ability_id:
                return ability
        return None

    def _alive_units(self) -> Iterable[CombatUnit]:
        return (unit for unit in self.units if unit.hp > 0)

    def _build_turn_queue(self) -> list[str]:
        return [
            unit.id
            for unit in sorted(
                self._alive_units(),
                key=lambda unit: (-unit.speed, unit.team, unit.id),
            )
        ]

    def _get_winner(self) -> TeamId | None:
        living_teams = {unit.team for unit in self._alive_units()}
        if len(living_teams) == 1:
            return next(iter(living_teams))
        return None

    def _tick_cooldowns(self, actor: CombatUnit) -> None:
        for ability_id, remaining in list(actor.cooldowns.items()):
            actor.cooldowns[ability_id] = max(0, remaining - 1)

    def _prime_next_turn(self) -> None:
        while True:
            winner = self._get_winner()
            if winner:
                self.state.winner = winner
                self.state.active_unit_id = None
                self.state.turn_queue = []
                return

            self.state.turn_queue = [
                unit_id
                for unit_id in self.state.turn_queue
                if (unit := self.get_unit(unit_id)) is not None and unit.hp > 0
            ]

            if not self.state.turn_queue:
                self.state.round += 1
                self.state.turn_queue = self._build_turn_queue()
                self._push_log(f"라운드 {self.state.round} 시작.")

            actor = self.get_unit(self.state.turn_queue[0] if self.state.turn_queue else None)
            if actor is None or actor.hp <= 0:
                if self.state.turn_queue:
                    self.state.turn_queue = self.state.turn_queue[1:]
                continue

            self._tick_cooldowns(actor)

            if actor.stun_turns > 0:
                actor.stun_turns = max(0, actor.stun_turns - 1)
                self.state.turn_queue = self.state.turn_queue[1:]
                self._push_log(f"{actor.name}, 기절 상태로 턴을 넘긴다.")
                continue

            self.state.active_unit_id = actor.id
            return

    def _resolve_targets(
        self,
        actor: CombatUnit,
        ability: Ability,
        target_id: str | None,
    ) -> list[str]:
        if ability.target_type == "self":
            return [actor.id]

        if ability.target_type == "all-enemies":
            return [unit.id for unit in self.units if unit.team != actor.team and unit.hp > 0]

        if ability.target_type == "enemy" and target_id is None:
            return [unit.id for unit in self.units if unit.team != actor.team and unit.hp > 0]

        if target_id:
            target = self.get_unit(target_id)
            if target and target.team != actor.team and target.hp > 0:
                return [target.id]
        return []

    @dataclass
    class _EffectImpact:
        kind: str
        damage_dealt: int = 0
        shield_gained: int = 0
        stun_turns_applied: int = 0
        blocked_damage: int = 0
        defeated: bool = False

    def _apply_effect(self, target_id: str, effect: AbilityEffect) -> tuple[str, _EffectImpact]:
        target = self.get_unit(target_id)
        if target is None or target.hp <= 0:
            return "", BattleController._EffectImpact(kind=effect.kind)

        if effect.kind == "damage":
            blocked = min(target.shield, effect.amount)
            hp_damage = max(0, effect.amount - blocked)
            target.shield -= blocked
            target.hp = max(0, target.hp - hp_damage)
            defeated = target.hp == 0
            if hp_damage > 0:
                summary = f"{target.name} 체력 {hp_damage} 감소."
            else:
                summary = f"{target.name} 모든 피해를 막아냈다."
            if blocked > 0:
                summary += f" 보호막이 {blocked} 피해를 흡수했다."
            if defeated:
                summary += " 쓰러졌다."
            return summary, BattleController._EffectImpact(
                kind="damage",
                damage_dealt=hp_damage,
                blocked_damage=blocked,
                defeated=defeated,
            )

        if effect.kind == "shield":
            target.shield += effect.amount
            return (
                f"{target.name} 보호막 {effect.amount} 획득.",
                BattleController._EffectImpact(kind="shield", shield_gained=effect.amount),
            )

        target.stun_turns = max(target.stun_turns, effect.turns)
        return (
            f"{target.name} {effect.turns}턴 기절.",
            BattleController._EffectImpact(kind="stun", stun_turns_applied=effect.turns),
        )

    def _score_ability(self, actor: CombatUnit, ability: Ability) -> float:
        actor_hp_ratio = actor.hp / actor.max_hp
        enemy_count = len([unit for unit in self.units if unit.team != actor.team and unit.hp > 0])
        score = ability.cooldown * 0.75

        for effect in ability.effects:
            if effect.kind == "damage":
                score += effect.amount * (max(1.25, enemy_count * 0.85) if ability.target_type == "all-enemies" else 1.15)
            elif effect.kind == "shield":
                score += effect.amount * (1.5 if actor_hp_ratio <= 0.45 else 0.18)
            elif effect.kind == "stun":
                score += 13

        if ability.target_type == "self" and actor_hp_ratio >= 0.75:
            score -= 14

        return score

    def _choose_enemy_target(self, actor: CombatUnit) -> str | None:
        enemies = sorted(
            (unit for unit in self.units if unit.team != actor.team and unit.hp > 0),
            key=lambda unit: (unit.hp, unit.speed),
        )
        return enemies[0].id if enemies else None
