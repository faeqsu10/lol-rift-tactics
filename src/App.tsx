import type { CSSProperties } from 'react';
import { Suspense, lazy, startTransition, useEffect, useRef, useState } from 'react';
import ChampionAvatar from './components/ChampionAvatar';
import {
  createInitialBattleState,
  getActiveUnit,
  getUnitById,
  getValidTargetIds,
  planEnemyTurn,
  resolveActiveTurn,
  resolvePlayerTurn,
} from './game/engine';
import type { Ability, BattleAction, BattleState, CombatUnit } from './game/types';

const PhaserBattlefield = lazy(() => import('./components/PhaserBattlefield'));

const roleLabels = {
  Vanguard: '전위',
  Mage: '마법사',
  Marksman: '사수',
} as const;

function resolvePreviewTargetIds(
  units: CombatUnit[],
  actor: CombatUnit,
  ability: Ability,
  targetId?: string,
): string[] {
  if (ability.targetType === 'self') {
    return [actor.id];
  }

  if (ability.targetType === 'all-enemies') {
    return units
      .filter((unit) => unit.team !== actor.team && unit.hp > 0)
      .map((unit) => unit.id);
  }

  return targetId ? [targetId] : [];
}

function createPreviewAction(
  previewId: string,
  actor: CombatUnit,
  ability: Ability,
  targetIds: string[],
): BattleAction {
  const effectKinds = Array.from(new Set(ability.effects.map((effect) => effect.kind)));

  return {
    id: previewId,
    actorId: actor.id,
    actorTeam: actor.team,
    abilityId: ability.id,
    abilityName: ability.name,
    targetType: ability.targetType,
    targetIds,
    impacts: targetIds.map((targetId) => ({
      targetId,
      effectKinds,
      damageDealt: 0,
      shieldGained: 0,
      stunTurnsApplied: 0,
      blockedDamage: 0,
      defeated: false,
    })),
  };
}

const teamCopy = {
  blue: {
    label: '블루 팀',
    blurb: '플레이어가 조작하는 시범 로스터',
  },
  red: {
    label: '레드 팀',
    blurb: 'AI가 조작하는 적 로스터',
  },
} as const;

function formatTeamState(units: CombatUnit[]): string {
  const aliveCount = units.filter((unit) => unit.hp > 0).length;
  return `${aliveCount}/${units.length} 생존`;
}

function UnitCard({
  unit,
  isActive,
  isTargetable,
  onTarget,
}: {
  unit: CombatUnit;
  isActive: boolean;
  isTargetable: boolean;
  onTarget?: (unitId: string) => void;
}) {
  const hpPercent = Math.max(0, (unit.hp / unit.maxHp) * 100);
  const accentStyle = {
    '--unit-accent': unit.accent,
  } as CSSProperties;
  const cardClassName = [
    'unit-card',
    `team-${unit.team}`,
    isActive ? 'is-active' : '',
    isTargetable ? 'is-targetable' : '',
    unit.hp <= 0 ? 'is-defeated' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const cardContent = (
    <>
      <div className="unit-card__hero">
        <ChampionAvatar unit={unit} size="card" />
        <div className="unit-card__identity">
          <div className="unit-card__header">
            <div>
              <p className="eyebrow">{roleLabels[unit.role]}</p>
              <h3>{unit.name}</h3>
              <p className="unit-title">{unit.title}</p>
            </div>
            <span className="speed-pill">속도 {unit.speed}</span>
          </div>
        </div>
      </div>

      <div className="unit-card__stats">
        <div>
          <div className="stat-row">
            <span>체력</span>
            <strong>
              {unit.hp}/{unit.maxHp}
            </strong>
          </div>
          <div className="bar-track">
            <div className="bar-fill hp-bar" style={{ width: `${hpPercent}%` }} />
          </div>
        </div>

        <div className="stat-row subtle-row">
          <span>보호막</span>
          <strong>{unit.shield}</strong>
        </div>
        <div className="stat-row subtle-row">
          <span>상태</span>
          <strong>{unit.stunTurns > 0 ? `기절 ${unit.stunTurns}턴` : '정상'}</strong>
        </div>
      </div>

      <div className="cooldown-list">
        {unit.abilities.map((ability) => {
          const remaining = unit.cooldowns[ability.id];
          return (
            <div key={ability.id} className="cooldown-chip">
              <span>{ability.name}</span>
              <strong>{remaining > 0 ? `대기 ${remaining}` : '준비'}</strong>
            </div>
          );
        })}
      </div>
    </>
  );

  if (isTargetable && onTarget && unit.hp > 0) {
    return (
      <button
        type="button"
        className={cardClassName}
        style={accentStyle}
        onClick={() => onTarget(unit.id)}
      >
        {cardContent}
      </button>
    );
  }

  return (
    <article className={cardClassName} style={accentStyle}>
      {cardContent}
    </article>
  );
}

function AbilityButton({
  ability,
  remainingCooldown,
  isSelected,
  disabled,
  onSelect,
}: {
  ability: Ability;
  remainingCooldown: number;
  isSelected: boolean;
  disabled?: boolean;
  onSelect: (ability: Ability) => void;
}) {
  const isDisabled = remainingCooldown > 0 || disabled;
  return (
    <button
      type="button"
      className={[
        'ability-button',
        isSelected ? 'is-selected' : '',
        isDisabled ? 'is-disabled' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      onClick={() => onSelect(ability)}
      disabled={isDisabled}
    >
      <div className="ability-button__top">
        <strong>{ability.name}</strong>
        <span>
          {remainingCooldown > 0 ? `대기 ${remainingCooldown}` : disabled ? '시전 중' : '준비'}
        </span>
      </div>
      <p>{ability.description}</p>
    </button>
  );
}

export default function App() {
  const [battleState, setBattleState] = useState(createInitialBattleState);
  const [selectedAbilityId, setSelectedAbilityId] = useState<string | null>(null);
  const [previewAction, setPreviewAction] = useState<BattleAction | null>(null);
  const previewSequenceRef = useRef(0);
  const planningTimerRef = useRef<number | null>(null);
  const resolutionTimerRef = useRef<number | null>(null);

  const activeUnit = getActiveUnit(battleState);
  const blueUnits = battleState.units.filter((unit) => unit.team === 'blue');
  const redUnits = battleState.units.filter((unit) => unit.team === 'red');
  const interactionLocked = Boolean(previewAction);
  const playerTurn =
    Boolean(activeUnit) &&
    activeUnit?.team === 'blue' &&
    !battleState.winner &&
    !interactionLocked;

  const selectedAbility =
    activeUnit && selectedAbilityId
      ? activeUnit.abilities.find((ability) => ability.id === selectedAbilityId) ?? null
      : null;

  const validTargetIds = selectedAbility
    ? getValidTargetIds(battleState, selectedAbility.id)
    : [];

  const validTargetSet = new Set(interactionLocked ? [] : validTargetIds);
  const latestLogText = battleState.log[0]?.text ?? '';
  const queuePreview = battleState.turnQueue
    .slice(0, 6)
    .reduce<CombatUnit[]>((previewUnits, unitId) => {
      const unit = getUnitById(battleState.units, unitId);
      if (unit) {
        previewUnits.push(unit);
      }
      return previewUnits;
    }, []);

  useEffect(() => {
    setSelectedAbilityId(null);
  }, [activeUnit?.id, battleState.winner]);

  function clearPendingTimers() {
    if (planningTimerRef.current) {
      window.clearTimeout(planningTimerRef.current);
      planningTimerRef.current = null;
    }

    if (resolutionTimerRef.current) {
      window.clearTimeout(resolutionTimerRef.current);
      resolutionTimerRef.current = null;
    }
  }

  function queueAction(
    nextPreviewAction: BattleAction,
    resolver: (currentState: BattleState) => BattleState,
    resolveDelay = 620,
  ) {
    clearPendingTimers();
    setPreviewAction(nextPreviewAction);

    resolutionTimerRef.current = window.setTimeout(() => {
      resolutionTimerRef.current = null;
      setPreviewAction(null);
      startTransition(() => {
        setBattleState(resolver);
      });
    }, resolveDelay);
  }

  function buildPreviewActionFromSelection(
    actor: CombatUnit,
    ability: Ability,
    targetId?: string,
  ): BattleAction {
    previewSequenceRef.current += 1;
    return createPreviewAction(
      `preview-${previewSequenceRef.current}`,
      actor,
      ability,
      resolvePreviewTargetIds(battleState.units, actor, ability, targetId),
    );
  }

  useEffect(() => {
    if (
      !activeUnit ||
      activeUnit.team !== 'red' ||
      battleState.winner ||
      interactionLocked
    ) {
      return undefined;
    }

    planningTimerRef.current = window.setTimeout(() => {
      planningTimerRef.current = null;

      const plannedTurn = planEnemyTurn(battleState);

      if (!plannedTurn) {
        return;
      }

      const ability =
        activeUnit.abilities.find((candidate) => candidate.id === plannedTurn.abilityId) ??
        null;

      if (!ability) {
        return;
      }

      queueAction(
        buildPreviewActionFromSelection(activeUnit, ability, plannedTurn.targetId),
        (currentState) =>
          resolveActiveTurn(currentState, plannedTurn.abilityId, plannedTurn.targetId),
      );
    }, 480);

    return () => clearPendingTimers();
  }, [activeUnit, battleState, battleState.winner, interactionLocked]);

  useEffect(() => clearPendingTimers, []);

  function handleAbilitySelect(ability: Ability) {
    if (
      !activeUnit ||
      !playerTurn ||
      activeUnit.cooldowns[ability.id] > 0 ||
      interactionLocked
    ) {
      return;
    }

    if (ability.targetType !== 'enemy') {
      setSelectedAbilityId(null);
      queueAction(
        buildPreviewActionFromSelection(activeUnit, ability),
        (currentState) => resolvePlayerTurn(currentState, ability.id),
      );
      return;
    }

    setSelectedAbilityId((currentId) =>
      currentId === ability.id ? null : ability.id,
    );
  }

  function handleTargetSelect(targetId: string) {
    if (!selectedAbilityId || interactionLocked) {
      return;
    }

    const ability =
      activeUnit?.abilities.find((candidate) => candidate.id === selectedAbilityId) ?? null;

    if (!activeUnit || !ability) {
      return;
    }

    setSelectedAbilityId(null);
    queueAction(
      buildPreviewActionFromSelection(activeUnit, ability, targetId),
      (currentState) => resolvePlayerTurn(currentState, selectedAbilityId, targetId),
    );
  }

  function handleReset() {
    clearPendingTimers();
    setSelectedAbilityId(null);
    setPreviewAction(null);
    startTransition(() => {
      setBattleState(createInitialBattleState());
    });
  }

  return (
    <div className="app-shell">
      <header className="hero-panel">
        <div className="hero-panel__copy">
          <p className="eyebrow">리그 오브 레전드: 리프트 택틱스</p>
          <h1>웹 MVP 교전 프로토타입</h1>
          <p className="hero-summary">
            고정 로스터, 재사용 대기시간 기반 스킬, 속도 순 턴 진행, 단순 적 AI를
            갖춘 브라우저용 3대3 전투 프로토타입입니다.
          </p>
        </div>

        <div className="hero-panel__status">
          <div className="status-card">
            <span>라운드</span>
            <strong>{battleState.round}</strong>
          </div>
          <div className="status-card">
            <span>현재 턴</span>
            <strong>{activeUnit ? activeUnit.name : '종료'}</strong>
          </div>
          <div className="status-card">
            <span>전황</span>
            <strong>
              {battleState.winner
                ? `${teamCopy[battleState.winner].label} 승리`
                : interactionLocked
                  ? '스킬 시전 중'
                : playerTurn
                  ? '플레이어 행동'
                  : '적 행동 계산 중'}
            </strong>
          </div>
          <button type="button" className="reset-button" onClick={handleReset}>
            전투 초기화
          </button>
        </div>
      </header>

      <main className="battle-layout">
        <section className="team-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">{teamCopy.blue.label}</p>
              <h2>{formatTeamState(blueUnits)}</h2>
            </div>
            <p>{teamCopy.blue.blurb}</p>
          </div>

          <div className="unit-grid">
            {blueUnits.map((unit) => (
              <UnitCard
                key={unit.id}
                unit={unit}
                isActive={battleState.activeUnitId === unit.id}
                isTargetable={validTargetSet.has(unit.id)}
                onTarget={handleTargetSelect}
              />
            ))}
          </div>
        </section>

        <div className="battlefield-column">
          <Suspense
            fallback={
              <section className="battlefield-panel battlefield-panel--phaser">
                <div className="phaser-loading">Phaser 전장을 불러오는 중...</div>
              </section>
            }
          >
            <PhaserBattlefield
              units={battleState.units}
              activeUnit={activeUnit}
              winner={battleState.winner}
              lastAction={battleState.lastAction}
              previewAction={previewAction}
              latestLogText={latestLogText}
              selectedAbilityName={selectedAbility?.name ?? null}
              validTargetSet={validTargetSet}
              onTarget={handleTargetSelect}
            />
          </Suspense>

          <section className="control-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">턴 순서</p>
                <h2>행동 흐름</h2>
              </div>
              <div className="queue-strip" aria-label="현재 턴 순서">
                {queuePreview.length > 0 ? (
                  queuePreview.map((unit) => (
                    <span
                      key={unit.id}
                      className={['queue-pill', `team-${unit.team}`]
                        .filter(Boolean)
                        .join(' ')}
                    >
                      {unit.name}
                    </span>
                  ))
                ) : (
                  <span className="queue-empty">남은 턴 없음</span>
                )}
              </div>
            </div>

            <div className="rules-strip">
              <span>재사용 대기시간은 자신의 턴에 감소</span>
              <span>보호막이 피해를 먼저 흡수</span>
              <span>기절은 다음 턴을 건너뜀</span>
            </div>

            <div className="action-panel">
              {battleState.winner ? (
                <div className="action-summary">
                  <p className="eyebrow">결과</p>
                  <h3>{teamCopy[battleState.winner].label} 승리</h3>
                  <p>전투를 초기화하면 현재 로스터 매치를 다시 플레이할 수 있습니다.</p>
                </div>
              ) : activeUnit ? (
                <>
                  <div className="action-summary">
                    <p className="eyebrow">현재 챔피언</p>
                    <h3>{activeUnit.name}</h3>
                    <p>
                      {activeUnit.team === 'blue'
                        ? selectedAbility
                          ? '시전을 완료할 적 대상을 선택하세요.'
                          : '이번 턴에 사용할 스킬을 선택하세요.'
                        : '적 AI가 가장 좋은 행동을 계산하고 있습니다.'}
                    </p>
                  </div>

                  <div className="ability-list">
                    {activeUnit.abilities.map((ability) => (
                      <AbilityButton
                      key={ability.id}
                      ability={ability}
                      remainingCooldown={activeUnit.cooldowns[ability.id]}
                      isSelected={selectedAbilityId === ability.id}
                      disabled={interactionLocked}
                      onSelect={handleAbilitySelect}
                    />
                  ))}
                </div>
              </>
            ) : null}
          </div>

          <div className="log-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">전투 로그</p>
                <h2>최근 행동</h2>
              </div>
            </div>

            <div className="log-list">
              {battleState.log.map((entry) => (
                <article key={entry.id} className="log-entry">
                  <span>라운드 {entry.round}</span>
                  <p>{entry.text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </div>

      <section className="team-panel enemy-panel">
        <div className="panel-header">
          <div>
            <p className="eyebrow">{teamCopy.red.label}</p>
            <h2>{formatTeamState(redUnits)}</h2>
          </div>
          <p>{teamCopy.red.blurb}</p>
        </div>

        <div className="unit-grid">
          {redUnits.map((unit) => (
            <UnitCard
              key={unit.id}
              unit={unit}
              isActive={battleState.activeUnitId === unit.id}
              isTargetable={validTargetSet.has(unit.id)}
              onTarget={handleTargetSelect}
            />
          ))}
        </div>
      </section>
    </main>
    </div>
  );
}
