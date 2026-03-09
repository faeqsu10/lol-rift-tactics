import { createInitialUnits } from './data';
import type {
  Ability,
  BattleActionImpact,
  AbilityEffect,
  BattleState,
  CombatLogEntry,
  CombatUnit,
  TeamId,
} from './types';

const MAX_LOG_ENTRIES = 12;

let logCounter = 0;
let actionCounter = 0;

function makeLogEntry(round: number, text: string): CombatLogEntry {
  logCounter += 1;
  return {
    id: `log-${logCounter}`,
    round,
    text,
  };
}

function addLog(state: BattleState, text: string): BattleState {
  return {
    ...state,
    log: [makeLogEntry(state.round, text), ...state.log].slice(0, MAX_LOG_ENTRIES),
  };
}

function makeActionId(): string {
  actionCounter += 1;
  return `action-${actionCounter}`;
}

function isAlive(unit: CombatUnit): boolean {
  return unit.hp > 0;
}

function updateUnit(
  units: CombatUnit[],
  unitId: string,
  recipe: (unit: CombatUnit) => CombatUnit,
): CombatUnit[] {
  return units.map((unit) => (unit.id === unitId ? recipe(unit) : unit));
}

function findAbility(unit: CombatUnit, abilityId: string): Ability | null {
  return unit.abilities.find((ability) => ability.id === abilityId) ?? null;
}

function tickCooldowns(units: CombatUnit[], actorId: string): CombatUnit[] {
  return updateUnit(units, actorId, (unit) => ({
    ...unit,
    cooldowns: Object.fromEntries(
      Object.entries(unit.cooldowns).map(([abilityId, remaining]) => [
        abilityId,
        Math.max(0, remaining - 1),
      ]),
    ),
  }));
}

function getWinner(units: CombatUnit[]): TeamId | null {
  const livingTeams = Array.from(
    new Set(units.filter(isAlive).map((unit) => unit.team)),
  );

  return livingTeams.length === 1 ? livingTeams[0] : null;
}

function applyEffect(
  units: CombatUnit[],
  targetId: string,
  effect: AbilityEffect,
): {
  units: CombatUnit[];
  summary: string;
  impact: Omit<BattleActionImpact, 'targetId' | 'effectKinds'> & {
    effectKind: AbilityEffect['kind'];
  };
} {
  const target = getUnitById(units, targetId);

  if (!target || !isAlive(target)) {
    return {
      units,
      summary: '',
      impact: {
        effectKind: effect.kind,
        damageDealt: 0,
        shieldGained: 0,
        stunTurnsApplied: 0,
        blockedDamage: 0,
        defeated: false,
      },
    };
  }

  if (effect.kind === 'damage') {
    const blocked = Math.min(target.shield, effect.amount);
    const hpDamage = Math.max(0, effect.amount - blocked);
    const nextTarget = {
      ...target,
      shield: target.shield - blocked,
      hp: Math.max(0, target.hp - hpDamage),
    };
    const defeatedText = nextTarget.hp === 0 ? ' 쓰러졌다.' : '';
    const blockedText = blocked > 0 ? ` 보호막이 ${blocked} 피해를 흡수했다.` : '';

    return {
      units: updateUnit(units, targetId, () => nextTarget),
      summary:
        hpDamage > 0
          ? `${target.name} 체력 ${hpDamage} 감소.${blockedText}${defeatedText}`
          : `${target.name} 모든 피해를 막아냈다.${defeatedText}`,
      impact: {
        effectKind: 'damage',
        damageDealt: hpDamage,
        shieldGained: 0,
        stunTurnsApplied: 0,
        blockedDamage: blocked,
        defeated: nextTarget.hp === 0,
      },
    };
  }

  if (effect.kind === 'shield') {
    return {
      units: updateUnit(units, targetId, (unit) => ({
        ...unit,
        shield: unit.shield + effect.amount,
      })),
      summary: `${target.name} 보호막 ${effect.amount} 획득.`,
      impact: {
        effectKind: 'shield',
        damageDealt: 0,
        shieldGained: effect.amount,
        stunTurnsApplied: 0,
        blockedDamage: 0,
        defeated: false,
      },
    };
  }

  return {
    units: updateUnit(units, targetId, (unit) => ({
      ...unit,
      stunTurns: Math.max(unit.stunTurns, effect.turns),
    })),
    summary: `${target.name} ${effect.turns}턴 기절.`,
    impact: {
      effectKind: 'stun',
      damageDealt: 0,
      shieldGained: 0,
      stunTurnsApplied: effect.turns,
      blockedDamage: 0,
      defeated: false,
    },
  };
}

function getResolvedTargets(
  state: BattleState,
  actor: CombatUnit,
  ability: Ability,
  targetId?: string,
): string[] {
  if (ability.targetType === 'self') {
    return [actor.id];
  }

  if (ability.targetType === 'all-enemies') {
    return state.units
      .filter((unit) => unit.team !== actor.team && isAlive(unit))
      .map((unit) => unit.id);
  }

  const validTargetIds = state.units
    .filter((unit) => unit.team !== actor.team && isAlive(unit))
    .map((unit) => unit.id);

  if (targetId && validTargetIds.includes(targetId)) {
    return [targetId];
  }

  return [];
}

function finalizeAction(
  state: BattleState,
  actor: CombatUnit,
  ability: Ability,
  targetId?: string,
): BattleState {
  if (actor.cooldowns[ability.id] > 0) {
    return state;
  }

  const targets = getResolvedTargets(state, actor, ability, targetId);

  if (targets.length === 0) {
    return state;
  }

  let units = state.units;
  const summaries: string[] = [];
  const impactMap = new Map<string, BattleActionImpact>();

  for (const resolvedTargetId of targets) {
    for (const effect of ability.effects) {
      const result = applyEffect(units, resolvedTargetId, effect);
      units = result.units;
      if (result.summary) {
        summaries.push(result.summary);
      }

      const existingImpact = impactMap.get(resolvedTargetId) ?? {
        targetId: resolvedTargetId,
        effectKinds: [],
        damageDealt: 0,
        shieldGained: 0,
        stunTurnsApplied: 0,
        blockedDamage: 0,
        defeated: false,
      };

      if (!existingImpact.effectKinds.includes(result.impact.effectKind)) {
        existingImpact.effectKinds.push(result.impact.effectKind);
      }

      existingImpact.damageDealt += result.impact.damageDealt;
      existingImpact.shieldGained += result.impact.shieldGained;
      existingImpact.stunTurnsApplied += result.impact.stunTurnsApplied;
      existingImpact.blockedDamage += result.impact.blockedDamage;
      existingImpact.defeated = existingImpact.defeated || result.impact.defeated;

      impactMap.set(resolvedTargetId, existingImpact);
    }
  }

  units = updateUnit(units, actor.id, (unit) => ({
    ...unit,
    cooldowns: {
      ...unit.cooldowns,
      [ability.id]: ability.cooldown,
    },
  }));

  let nextState = addLog(
    {
      ...state,
      units,
      activeUnitId: null,
      turnQueue: state.turnQueue.slice(1),
      lastAction: {
        id: makeActionId(),
        actorId: actor.id,
        actorTeam: actor.team,
        abilityId: ability.id,
        abilityName: ability.name,
        targetType: ability.targetType,
        targetIds: targets,
        impacts: targets
          .map((resolvedTargetId) => impactMap.get(resolvedTargetId))
          .filter((impact): impact is BattleActionImpact => Boolean(impact)),
      },
    },
    `${actor.name}, ${ability.name} 사용. ${summaries.join(' ')}`.trim(),
  );

  const winner = getWinner(nextState.units);

  if (winner) {
    nextState = addLog(
      {
        ...nextState,
        winner,
        activeUnitId: null,
        turnQueue: [],
      },
      winner === 'blue' ? '블루 팀 승리.' : '레드 팀 승리.',
    );
    return {
      ...nextState,
      winner,
      activeUnitId: null,
      turnQueue: [],
    };
  }

  return primeNextTurn(nextState);
}

function primeNextTurn(state: BattleState): BattleState {
  let nextState = state;

  while (true) {
    const winner = getWinner(nextState.units);

    if (winner) {
      return {
        ...nextState,
        winner,
        activeUnitId: null,
        turnQueue: [],
      };
    }

    let queue = nextState.turnQueue.filter((unitId) => {
      const unit = getUnitById(nextState.units, unitId);
      return Boolean(unit && isAlive(unit));
    });

    if (queue.length === 0) {
      nextState = addLog(
        {
          ...nextState,
          round: nextState.round + 1,
          turnQueue: buildTurnQueue(nextState.units),
          activeUnitId: null,
        },
        `라운드 ${nextState.round + 1} 시작.`,
      );
      queue = nextState.turnQueue;
    }

    const actorId = queue[0];
    const cooledUnits = tickCooldowns(nextState.units, actorId);
    const actor = getUnitById(cooledUnits, actorId);

    if (!actor || !isAlive(actor)) {
      nextState = {
        ...nextState,
        units: cooledUnits,
        turnQueue: queue.slice(1),
        activeUnitId: null,
      };
      continue;
    }

    if (actor.stunTurns > 0) {
      nextState = addLog(
        {
          ...nextState,
          units: updateUnit(cooledUnits, actorId, (unit) => ({
            ...unit,
            stunTurns: Math.max(0, unit.stunTurns - 1),
          })),
          turnQueue: queue.slice(1),
          activeUnitId: null,
        },
        `${actor.name}, 기절 상태로 턴을 넘긴다.`,
      );
      continue;
    }

    return {
      ...nextState,
      units: cooledUnits,
      turnQueue: queue,
      activeUnitId: actorId,
      winner: null,
    };
  }
}

function scoreAbility(
  state: BattleState,
  actor: CombatUnit,
  ability: Ability,
): number {
  const actorHpRatio = actor.hp / actor.maxHp;
  const enemyCount = state.units.filter(
    (unit) => unit.team !== actor.team && isAlive(unit),
  ).length;

  let score = ability.cooldown * 0.75;

  for (const effect of ability.effects) {
    if (effect.kind === 'damage') {
      score +=
        ability.targetType === 'all-enemies'
          ? effect.amount * Math.max(1.25, enemyCount * 0.85)
          : effect.amount * 1.15;
    }

    if (effect.kind === 'shield') {
      score += actorHpRatio <= 0.45 ? effect.amount * 1.5 : effect.amount * 0.18;
    }

    if (effect.kind === 'stun') {
      score += 13;
    }
  }

  if (ability.targetType === 'self' && actorHpRatio >= 0.75) {
    score -= 14;
  }

  return score;
}

function chooseEnemyTarget(state: BattleState, actor: CombatUnit): string | undefined {
  const enemies = state.units
    .filter((unit) => unit.team !== actor.team && isAlive(unit))
    .sort((left, right) => left.hp - right.hp || left.speed - right.speed);

  return enemies[0]?.id;
}

export function buildTurnQueue(units: CombatUnit[]): string[] {
  return [...units]
    .filter(isAlive)
    .sort(
      (left, right) =>
        right.speed - left.speed || left.team.localeCompare(right.team) || left.id.localeCompare(right.id),
    )
    .map((unit) => unit.id);
}

export function createInitialBattleState(): BattleState {
  const units = createInitialUnits();
  return primeNextTurn({
    round: 1,
    units,
    turnQueue: buildTurnQueue(units),
    activeUnitId: null,
    winner: null,
    log: [makeLogEntry(1, '전투 개시. 단순화된 리프트 교전 맵에서 시작합니다.')],
    lastAction: null,
  });
}

export function getUnitById(
  units: CombatUnit[],
  unitId: string | null,
): CombatUnit | null {
  if (!unitId) {
    return null;
  }

  return units.find((unit) => unit.id === unitId) ?? null;
}

export function getActiveUnit(state: BattleState): CombatUnit | null {
  return getUnitById(state.units, state.activeUnitId);
}

export function getValidTargetIds(
  state: BattleState,
  abilityId: string,
): string[] {
  const actor = getActiveUnit(state);

  if (!actor) {
    return [];
  }

  const ability = findAbility(actor, abilityId);

  if (!ability || actor.cooldowns[ability.id] > 0) {
    return [];
  }

  return getResolvedTargets(state, actor, ability);
}

export function resolveActiveTurn(
  state: BattleState,
  abilityId: string,
  targetId?: string,
): BattleState {
  const actor = getActiveUnit(state);

  if (!actor || state.winner) {
    return state;
  }

  const ability = findAbility(actor, abilityId);

  if (!ability) {
    return state;
  }

  return finalizeAction(state, actor, ability, targetId);
}

export function resolvePlayerTurn(
  state: BattleState,
  abilityId: string,
  targetId?: string,
): BattleState {
  const actor = getActiveUnit(state);

  if (!actor || actor.team !== 'blue' || state.winner) {
    return state;
  }

  return resolveActiveTurn(state, abilityId, targetId);
}

export function planEnemyTurn(
  state: BattleState,
): { abilityId: string; targetId?: string } | null {
  const actor = getActiveUnit(state);

  if (!actor || actor.team !== 'red' || state.winner) {
    return null;
  }

  const availableAbilities = actor.abilities.filter(
    (ability) => actor.cooldowns[ability.id] === 0,
  );

  const chosenAbility =
    [...availableAbilities].sort(
      (left, right) => scoreAbility(state, actor, right) - scoreAbility(state, actor, left),
    )[0] ?? actor.abilities[0];

  return {
    abilityId: chosenAbility.id,
    targetId:
      chosenAbility.targetType === 'enemy'
        ? chooseEnemyTarget(state, actor)
        : undefined,
  };
}

export function runEnemyTurn(state: BattleState): BattleState {
  const plannedTurn = planEnemyTurn(state);

  if (!plannedTurn) {
    return state;
  }

  return resolveActiveTurn(state, plannedTurn.abilityId, plannedTurn.targetId);
}
