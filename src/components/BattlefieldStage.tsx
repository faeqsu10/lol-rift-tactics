import type { CSSProperties } from 'react';
import { useEffect, useState } from 'react';
import ChampionAvatar from './ChampionAvatar';
import type { BattleAction, BattleActionImpact, CombatUnit, TeamId } from '../game/types';

function getImpactByTargetId(
  actionCue: BattleAction | null,
  targetId: string,
): BattleActionImpact | null {
  if (!actionCue) {
    return null;
  }

  return actionCue.impacts.find((impact) => impact.targetId === targetId) ?? null;
}

function BattlefieldUnit({
  unit,
  positionIndex,
  isActive,
  isTargetable,
  actionCue,
  onTarget,
}: {
  unit: CombatUnit;
  positionIndex: number;
  isActive: boolean;
  isTargetable: boolean;
  actionCue: BattleAction | null;
  onTarget: (unitId: string) => void;
}) {
  const hpPercent = Math.max(0, (unit.hp / unit.maxHp) * 100);
  const impact = getImpactByTargetId(actionCue, unit.id);
  const isActionActor = actionCue?.actorId === unit.id;
  const isActionTarget = Boolean(impact);
  const slotShift =
    unit.team === 'blue'
      ? [-28, 0, 28][positionIndex] ?? 0
      : [28, 0, -28][positionIndex] ?? 0;
  const style = {
    '--unit-accent': unit.accent,
    '--slot-shift': `${slotShift}px`,
    '--hp-width': `${hpPercent}%`,
  } as CSSProperties;
  const statusText =
    unit.hp <= 0 ? '전투 불능' : unit.stunTurns > 0 ? `기절 ${unit.stunTurns}턴` : '교전 가능';
  const className = [
    'battlefield-unit',
    `battlefield-unit--${unit.team}`,
    isActive ? 'is-active' : '',
    isTargetable ? 'is-targetable' : '',
    isActionActor ? 'is-action-actor' : '',
    isActionTarget ? 'is-action-target' : '',
    isActionActor && actionCue ? `action-target-type-${actionCue.targetType}` : '',
    impact?.effectKinds.includes('damage') ? 'receives-damage' : '',
    impact?.effectKinds.includes('shield') ? 'receives-shield' : '',
    impact?.effectKinds.includes('stun') ? 'receives-stun' : '',
    unit.hp <= 0 ? 'is-defeated' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const content = (
    <>
      <div className="battlefield-unit__avatar-wrap">
        <ChampionAvatar unit={unit} size="battlefield" />
        {isActive ? <span className="battlefield-unit__tag">현재 턴</span> : null}
        {isTargetable ? <span className="battlefield-unit__tag is-target">공격</span> : null}
        {impact ? (
          <div className="battlefield-floaters" aria-hidden="true">
            {impact.damageDealt > 0 ? (
              <span className="battlefield-floater is-damage">-{impact.damageDealt}</span>
            ) : null}
            {impact.blockedDamage > 0 ? (
              <span className="battlefield-floater is-block">막음 {impact.blockedDamage}</span>
            ) : null}
            {impact.shieldGained > 0 ? (
              <span className="battlefield-floater is-shield">+보호막 {impact.shieldGained}</span>
            ) : null}
            {impact.stunTurnsApplied > 0 ? (
              <span className="battlefield-floater is-stun">기절</span>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="battlefield-unit__meta">
        <div className="battlefield-unit__header">
          <strong>{unit.name}</strong>
          <span>{unit.role === 'Vanguard' ? '전위' : unit.role === 'Mage' ? '마법사' : '사수'}</span>
        </div>
        <div className="battlefield-unit__bar">
          <span className="battlefield-unit__bar-fill" />
        </div>
        <div className="battlefield-unit__numbers">
          <span>
            체력 {unit.hp}/{unit.maxHp}
          </span>
          <span>{statusText}</span>
        </div>
        <div className="battlefield-unit__chips">
          <span>보호막 {unit.shield}</span>
          <span>속도 {unit.speed}</span>
        </div>
      </div>
    </>
  );

  if (isTargetable && unit.hp > 0) {
    return (
      <button
        type="button"
        className={className}
        style={style}
        onClick={() => onTarget(unit.id)}
      >
        {content}
      </button>
    );
  }

  return (
    <article className={className} style={style}>
      {content}
    </article>
  );
}

export default function BattlefieldStage({
  blueUnits,
  redUnits,
  activeUnit,
  winner,
  lastAction,
  previewAction,
  latestLogText,
  selectedAbilityName,
  validTargetSet,
  onTarget,
}: {
  blueUnits: CombatUnit[];
  redUnits: CombatUnit[];
  activeUnit: CombatUnit | null;
  winner: TeamId | null;
  lastAction: BattleAction | null;
  previewAction: BattleAction | null;
  latestLogText: string;
  selectedAbilityName: string | null;
  validTargetSet: Set<string>;
  onTarget: (unitId: string) => void;
}) {
  const [actionCue, setActionCue] = useState<BattleAction | null>(null);

  useEffect(() => {
    if (!lastAction) {
      return undefined;
    }

    setActionCue(lastAction);

    const timer = window.setTimeout(() => {
      setActionCue((currentAction) =>
        currentAction?.id === lastAction.id ? null : currentAction,
      );
    }, 1100);

    return () => window.clearTimeout(timer);
  }, [lastAction?.id]);

  const visibleActionCue = previewAction ?? actionCue;

  const stageTitle = winner
    ? winner === 'blue'
      ? '블루 팀이 전장을 장악했습니다'
      : '레드 팀이 전장을 장악했습니다'
    : activeUnit
      ? `${activeUnit.name}의 턴`
      : '전투 종료';
  const stageDescription = winner
    ? '전투 초기화를 누르면 같은 매치를 다시 시작할 수 있습니다.'
    : previewAction
      ? `${previewAction.abilityName} 시전 중...`
    : selectedAbilityName
      ? `${selectedAbilityName}의 대상을 전장 위에서 선택하세요.`
      : latestLogText;
  const stageEffectClassName = visibleActionCue
    ? [
        'battlefield-effect',
        previewAction ? 'is-preview' : '',
        `effect-from-${visibleActionCue.actorTeam}`,
        `effect-type-${visibleActionCue.targetType}`,
        visibleActionCue.impacts.some((impact) => impact.effectKinds.includes('damage'))
          ? 'has-damage'
          : '',
        visibleActionCue.impacts.some((impact) => impact.effectKinds.includes('shield'))
          ? 'has-shield'
          : '',
        visibleActionCue.impacts.some((impact) => impact.effectKinds.includes('stun'))
          ? 'has-stun'
          : '',
      ]
        .filter(Boolean)
        .join(' ')
    : '';

  return (
    <section className={['battlefield-panel', winner ? `winner-${winner}` : '']
      .filter(Boolean)
      .join(' ')}>
      <div className="panel-header battlefield-panel__header">
        <div>
          <p className="eyebrow">전장</p>
          <h2>리프트 교전</h2>
        </div>
        <p>캐릭터를 직접 보며 대상 지정과 전황 파악이 가능하도록 구성한 시각 전투판입니다.</p>
      </div>

      <div className="battlefield-stage">
        <div className="battlefield-stage__aura battlefield-stage__aura--blue" />
        <div className="battlefield-stage__aura battlefield-stage__aura--red" />
        {visibleActionCue ? (
          <div key={visibleActionCue.id} className={stageEffectClassName} aria-hidden="true">
            <span className="battlefield-effect__label">{visibleActionCue.abilityName}</span>
          </div>
        ) : null}

        <div className="battlefield-side battlefield-side--red">
          {redUnits.map((unit, index) => (
            <BattlefieldUnit
              key={unit.id}
              unit={unit}
              positionIndex={index}
              isActive={activeUnit?.id === unit.id}
              isTargetable={validTargetSet.has(unit.id)}
              actionCue={visibleActionCue}
              onTarget={onTarget}
            />
          ))}
        </div>

        <div className="battlefield-center">
          <div className="battlefield-center__sigil" />
          <div className="battlefield-announcer">
            <p className="eyebrow">전장 중계</p>
            <h3>{stageTitle}</h3>
            <p>{stageDescription}</p>
          </div>

          {activeUnit ? (
            <div
              className={[
                'battlefield-spotlight',
                visibleActionCue?.actorId === activeUnit.id ? 'is-casting' : '',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <ChampionAvatar unit={activeUnit} size="spotlight" />
              <div className="battlefield-spotlight__copy">
                <p className="eyebrow">
                  {activeUnit.team === 'blue' ? '플레이어 챔피언' : '적 챔피언'}
                </p>
                <strong>{activeUnit.name}</strong>
                <span>{activeUnit.title}</span>
              </div>
            </div>
          ) : null}
        </div>

        <div className="battlefield-side battlefield-side--blue">
          {blueUnits.map((unit, index) => (
            <BattlefieldUnit
              key={unit.id}
              unit={unit}
              positionIndex={index}
              isActive={activeUnit?.id === unit.id}
              isTargetable={validTargetSet.has(unit.id)}
              actionCue={visibleActionCue}
              onTarget={onTarget}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
