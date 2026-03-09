import { useEffect, useRef, useState } from 'react';
import Phaser from 'phaser';
import RiftBattleScene from '../phaser/RiftBattleScene';
import type { BattleAction, CombatUnit, TeamId } from '../game/types';

export default function PhaserBattlefield({
  units,
  activeUnit,
  winner,
  lastAction,
  previewAction,
  latestLogText,
  selectedAbilityName,
  validTargetSet,
  onTarget,
}: {
  units: CombatUnit[];
  activeUnit: CombatUnit | null;
  winner: TeamId | null;
  lastAction: BattleAction | null;
  previewAction: BattleAction | null;
  latestLogText: string;
  selectedAbilityName: string | null;
  validTargetSet: Set<string>;
  onTarget: (unitId: string) => void;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const sceneRef = useRef<RiftBattleScene | null>(null);
  const gameRef = useRef<Phaser.Game | null>(null);
  const onTargetRef = useRef(onTarget);
  const [resolvedActionCue, setResolvedActionCue] = useState<BattleAction | null>(null);

  const blueAlive = units.filter((unit) => unit.team === 'blue' && unit.hp > 0).length;
  const redAlive = units.filter((unit) => unit.team === 'red' && unit.hp > 0).length;
  const visibleAction = previewAction ?? resolvedActionCue;
  const stageTitle = winner
    ? winner === 'blue'
      ? '블루 팀이 전장을 장악했습니다'
      : '레드 팀이 전장을 장악했습니다'
    : previewAction
      ? `${previewAction.abilityName} 시전 중`
      : activeUnit
        ? `${activeUnit.name}의 턴`
        : '전투 종료';
  const stageDescription = winner
    ? '전투 초기화를 누르면 다시 바로 플레이할 수 있습니다.'
    : previewAction
      ? '캔버스 전장에서 실제 시전 애니메이션이 진행됩니다.'
      : selectedAbilityName
        ? `${selectedAbilityName}의 대상을 전장 위에서 클릭하세요.`
        : latestLogText;

  useEffect(() => {
    onTargetRef.current = onTarget;
  }, [onTarget]);

  useEffect(() => {
    if (!hostRef.current || gameRef.current) {
      return undefined;
    }

    const scene = new RiftBattleScene();
    sceneRef.current = scene;

    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: hostRef.current,
      width: 960,
      height: 560,
      transparent: true,
      render: {
        antialias: true,
      },
      scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH,
      },
      scene: [scene],
    });

    gameRef.current = game;
    scene.setOnTarget((unitId) => onTargetRef.current(unitId));

    return () => {
      sceneRef.current = null;
      gameRef.current?.destroy(true);
      gameRef.current = null;
    };
  }, []);

  useEffect(() => {
    sceneRef.current?.setOnTarget((unitId) => onTargetRef.current(unitId));
  }, [onTarget]);

  useEffect(() => {
    sceneRef.current?.syncState({
      units,
      activeUnitId: activeUnit?.id ?? null,
      targetableIds: Array.from(validTargetSet),
      winner,
    });
  }, [units, activeUnit?.id, validTargetSet, winner]);

  useEffect(() => {
    if (!previewAction) {
      return;
    }

    sceneRef.current?.playPreviewAction(previewAction);
  }, [previewAction?.id]);

  useEffect(() => {
    if (!lastAction) {
      return undefined;
    }

    setResolvedActionCue(lastAction);
    sceneRef.current?.playResolvedAction(lastAction);

    const timer = window.setTimeout(() => {
      setResolvedActionCue((currentAction) =>
        currentAction?.id === lastAction.id ? null : currentAction,
      );
    }, 1100);

    return () => window.clearTimeout(timer);
  }, [lastAction?.id]);

  return (
    <section className="battlefield-panel battlefield-panel--phaser">
      <div className="panel-header battlefield-panel__header">
        <div>
          <p className="eyebrow">Phaser 전장</p>
          <h2>실시간 2D 전투 캔버스</h2>
        </div>
        <p>중앙 전장을 Phaser로 교체해 캐릭터가 실제로 움직이고 스킬 연출이 지나가도록 구성했습니다.</p>
      </div>

      <div className="phaser-battlefield-shell">
        <div ref={hostRef} className="phaser-stage-host" />

        <div className="phaser-overlay phaser-overlay--top">
          <div className="phaser-hud-card">
            <p className="eyebrow">전투 연출</p>
            <strong>{stageTitle}</strong>
            <p>{stageDescription}</p>
          </div>

          <div className="phaser-team-strip">
            <span className="phaser-team-chip team-blue">블루 {blueAlive} 생존</span>
            <span className="phaser-team-chip team-red">레드 {redAlive} 생존</span>
          </div>
        </div>

        <div className="phaser-overlay phaser-overlay--bottom">
          <div className="phaser-tip-row">
            <span>파란 링: 현재 턴</span>
            <span>청록 링: 클릭 가능한 대상</span>
            <span>시전 후 실제 피격 연출 재생</span>
          </div>

          {visibleAction ? (
            <div className="phaser-ability-ribbon">
              <span className="eyebrow">현재 액션</span>
              <strong>{visibleAction.abilityName}</strong>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
