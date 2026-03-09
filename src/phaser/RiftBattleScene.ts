import Phaser from 'phaser';
import type { BattleAction, CombatUnit, TeamId } from '../game/types';

interface UnitVisual {
  unitId: string;
  team: TeamId;
  accentColor: number;
  homeX: number;
  homeY: number;
  container: Phaser.GameObjects.Container;
  figure: Phaser.GameObjects.Container;
  hoverGlow: Phaser.GameObjects.Ellipse;
  activeRing: Phaser.GameObjects.Ellipse;
  targetRing: Phaser.GameObjects.Ellipse;
  shieldRing: Phaser.GameObjects.Ellipse;
  flash: Phaser.GameObjects.Ellipse;
  nameText: Phaser.GameObjects.Text;
  hpValueText: Phaser.GameObjects.Text;
  hpBarFill: Phaser.GameObjects.Rectangle;
  statusText: Phaser.GameObjects.Text;
  hitArea: Phaser.GameObjects.Zone;
  idleTween: Phaser.Tweens.Tween;
  activeTween: Phaser.Tweens.Tween;
}

function toColorNumber(hex: string): number {
  return parseInt(hex.replace('#', ''), 16);
}

function roleLabel(role: CombatUnit['role']): string {
  if (role === 'Vanguard') {
    return '전위';
  }

  if (role === 'Mage') {
    return '마법사';
  }

  return '사수';
}

export default class RiftBattleScene extends Phaser.Scene {
  private unitVisuals = new Map<string, UnitVisual>();
  private targetableIds = new Set<string>();
  private unitLayer?: Phaser.GameObjects.Layer;
  private fxLayer?: Phaser.GameObjects.Layer;
  private overlayLayer?: Phaser.GameObjects.Layer;
  private winnerBanner?: Phaser.GameObjects.Text;
  private onTarget: (unitId: string) => void = () => {};

  constructor() {
    super('RiftBattleScene');
  }

  create() {
    const { width, height } = this.scale;
    const background = this.add.graphics();

    background.fillGradientStyle(0x0a1722, 0x11283b, 0x1f1623, 0x0a1722, 1);
    background.fillRect(0, 0, width, height);

    background.fillStyle(0x143549, 0.22);
    background.fillEllipse(width * 0.16, height * 0.78, 260, 180);
    background.fillStyle(0x532b24, 0.24);
    background.fillEllipse(width * 0.84, height * 0.22, 260, 180);

    background.lineStyle(2, 0xd3b36c, 0.18);
    background.strokeCircle(width * 0.5, height * 0.5, 78);
    background.lineStyle(1, 0xffffff, 0.06);

    for (let index = 0; index < 9; index += 1) {
      background.strokeCircle(width * 0.5, height * 0.5, 110 + index * 34);
    }

    background.lineStyle(2, 0xffffff, 0.05);
    background.strokeRoundedRect(28, 28, width - 56, height - 56, 28);
    background.lineStyle(3, 0xd3b36c, 0.12);
    background.strokeRoundedRect(48, 48, width - 96, height - 96, 28);

    background.lineStyle(2, 0xffffff, 0.08);
    background.beginPath();
    background.moveTo(width * 0.2, height * 0.85);
    background.lineTo(width * 0.42, height * 0.65);
    background.lineTo(width * 0.58, height * 0.35);
    background.lineTo(width * 0.8, height * 0.15);
    background.strokePath();

    this.add
      .ellipse(width * 0.5, height * 0.5, 460, 180, 0xd3b36c, 0.06)
      .setBlendMode(Phaser.BlendModes.SCREEN);

    this.unitLayer = this.add.layer();
    this.fxLayer = this.add.layer();
    this.overlayLayer = this.add.layer();

    this.winnerBanner = this.add
      .text(width * 0.5, 52, '', {
        fontFamily: 'Trebuchet MS, sans-serif',
        fontSize: '28px',
        color: '#f4efe1',
        fontStyle: 'bold',
        stroke: '#08111c',
        strokeThickness: 5,
      })
      .setOrigin(0.5)
      .setAlpha(0);

    this.overlayLayer.add(this.winnerBanner);
  }

  setOnTarget(handler: (unitId: string) => void) {
    this.onTarget = handler;
  }

  syncState({
    units,
    activeUnitId,
    targetableIds,
    winner,
  }: {
    units: CombatUnit[];
    activeUnitId: string | null;
    targetableIds: string[];
    winner: TeamId | null;
  }) {
    if (!this.unitLayer || !this.fxLayer || !this.overlayLayer) {
      return;
    }

    const currentIds = units.map((unit) => unit.id).sort().join('|');
    const existingIds = Array.from(this.unitVisuals.keys()).sort().join('|');

    if (currentIds !== existingIds) {
      this.rebuildUnits(units);
    }

    this.targetableIds = new Set(targetableIds);

    for (const unit of units) {
      const visual = this.unitVisuals.get(unit.id);

      if (!visual) {
        continue;
      }

      const hpRatio = Math.max(0, unit.hp / unit.maxHp);
      visual.hpBarFill.width = 94 * hpRatio;
      visual.hpBarFill.x = -47 + visual.hpBarFill.width / 2;
      visual.hpValueText.setText(`${unit.hp}/${unit.maxHp}`);
      visual.statusText.setText(
        unit.hp <= 0
          ? '전투 불능'
          : unit.stunTurns > 0
            ? `기절 ${unit.stunTurns}턴`
            : unit.shield > 0
              ? `보호막 ${unit.shield}`
              : roleLabel(unit.role),
      );

      visual.container.alpha = unit.hp <= 0 ? 0.38 : 1;
      visual.container.scale = unit.hp <= 0 ? 0.92 : 1;
      visual.hoverGlow.setVisible(this.targetableIds.has(unit.id) && unit.hp > 0);
      visual.targetRing.setVisible(this.targetableIds.has(unit.id) && unit.hp > 0);
      visual.shieldRing.setVisible(unit.shield > 0 && unit.hp > 0);

      if (activeUnitId === unit.id && unit.hp > 0) {
        visual.activeRing.setVisible(true);
        visual.activeTween.resume();
      } else {
        visual.activeRing.setVisible(false);
        visual.activeTween.pause();
      }
    }

    if (winner && this.winnerBanner) {
      this.winnerBanner.setText(
        winner === 'blue' ? '블루 팀 승리' : '레드 팀 승리',
      );
      this.tweens.killTweensOf(this.winnerBanner);
      this.winnerBanner.setAlpha(0);
      this.winnerBanner.setScale(0.92);
      this.tweens.add({
        targets: this.winnerBanner,
        alpha: 1,
        scale: 1,
        duration: 420,
        ease: 'Back.Out',
      });
    } else if (this.winnerBanner) {
      this.winnerBanner.setAlpha(0);
    }
  }

  playPreviewAction(action: BattleAction) {
    const actor = this.unitVisuals.get(action.actorId);

    if (!actor) {
      return;
    }

    if (action.targetType === 'enemy') {
      const primaryTarget = this.unitVisuals.get(action.targetIds[0] ?? '');

      this.tweens.killTweensOf(actor.container);
      this.tweens.add({
        targets: actor.container,
        x:
          actor.team === 'blue'
            ? actor.homeX + 42
            : actor.homeX - 42,
        y: actor.homeY - 16,
        duration: 210,
        yoyo: true,
        ease: 'Cubic.Out',
      });

      if (primaryTarget) {
        this.time.delayedCall(90, () => {
          this.spawnProjectile(actor, primaryTarget, actor.team === 'blue' ? 0x66ddd6 : 0xef8a71);
        });
      }
    }

    if (action.targetType === 'all-enemies') {
      this.spawnShockwave(actor.homeX, actor.homeY - 22, actor.accentColor);
      this.tweens.killTweensOf(actor.figure);
      this.tweens.add({
        targets: actor.figure,
        scale: 1.06,
        duration: 220,
        yoyo: true,
        ease: 'Sine.InOut',
      });
    }

    if (action.targetType === 'self') {
      this.spawnShieldBurst(actor.homeX, actor.homeY - 18, 0x89d79d);
      this.tweens.killTweensOf(actor.figure);
      this.tweens.add({
        targets: actor.figure,
        scale: 1.04,
        duration: 240,
        yoyo: true,
        ease: 'Sine.InOut',
      });
    }
  }

  playResolvedAction(action: BattleAction) {
    for (const impact of action.impacts) {
      const visual = this.unitVisuals.get(impact.targetId);

      if (!visual) {
        continue;
      }

      if (impact.damageDealt > 0) {
        this.flashUnit(visual, 0xff7f6f);
        this.tweens.killTweensOf(visual.container);
        this.tweens.add({
          targets: visual.container,
          x:
            visual.team === 'blue'
              ? visual.homeX - 14
              : visual.homeX + 14,
          y: visual.homeY - 6,
          duration: 90,
          yoyo: true,
          repeat: 1,
          ease: 'Sine.Out',
          onComplete: () => {
            visual.container.setPosition(visual.homeX, visual.homeY);
          },
        });
        this.spawnFloatingText(
          visual.homeX,
          visual.homeY - 110,
          `-${impact.damageDealt}`,
          '#ff9f8b',
        );
      }

      if (impact.blockedDamage > 0) {
        this.spawnFloatingText(
          visual.homeX,
          visual.homeY - 138,
          `막음 ${impact.blockedDamage}`,
          '#8dddea',
        );
      }

      if (impact.shieldGained > 0) {
        this.spawnShieldBurst(visual.homeX, visual.homeY - 10, 0x89d79d);
        this.spawnFloatingText(
          visual.homeX,
          visual.homeY - 110,
          `+보호막 ${impact.shieldGained}`,
          '#a4efb4',
        );
      }

      if (impact.stunTurnsApplied > 0) {
        this.spawnStunStars(visual.homeX, visual.homeY - 98);
        this.spawnFloatingText(visual.homeX, visual.homeY - 138, '기절', '#ffe08f');
      }

      if (impact.defeated) {
        this.tweens.add({
          targets: visual.figure,
          angle: visual.team === 'blue' ? -12 : 12,
          y: visual.figure.y + 8,
          alpha: 0.6,
          duration: 420,
          ease: 'Cubic.Out',
        });
      }
    }
  }

  private rebuildUnits(units: CombatUnit[]) {
    for (const visual of this.unitVisuals.values()) {
      visual.idleTween.stop();
      visual.activeTween.stop();
      visual.container.destroy(true);
    }

    this.unitVisuals.clear();

    const blueUnits = units.filter((unit) => unit.team === 'blue');
    const redUnits = units.filter((unit) => unit.team === 'red');
    const { width, height } = this.scale;
    const bluePositions = [
      { x: width * 0.18, y: height * 0.73 },
      { x: width * 0.16, y: height * 0.52 },
      { x: width * 0.18, y: height * 0.31 },
    ];
    const redPositions = [
      { x: width * 0.82, y: height * 0.27 },
      { x: width * 0.84, y: height * 0.48 },
      { x: width * 0.82, y: height * 0.69 },
    ];

    blueUnits.forEach((unit, index) => {
      const visual = this.createUnitVisual(unit, bluePositions[index] ?? bluePositions[0]);
      this.unitVisuals.set(unit.id, visual);
    });

    redUnits.forEach((unit, index) => {
      const visual = this.createUnitVisual(unit, redPositions[index] ?? redPositions[0]);
      this.unitVisuals.set(unit.id, visual);
    });
  }

  private createUnitVisual(
    unit: CombatUnit,
    position: { x: number; y: number },
  ): UnitVisual {
    const accentColor = toColorNumber(unit.accent);
    const container = this.add.container(position.x, position.y);
    const shadow = this.add.ellipse(0, 56, 108, 24, 0x000000, 0.3);
    const hoverGlow = this.add
      .ellipse(0, 20, 152, 180, accentColor, 0.08)
      .setVisible(false)
      .setBlendMode(Phaser.BlendModes.SCREEN);
    const targetRing = this.add
      .ellipse(0, 58, 126, 36, 0, 0)
      .setStrokeStyle(3, 0x5fc7c0, 1)
      .setVisible(false);
    const activeRing = this.add
      .ellipse(0, 58, 140, 42, 0, 0)
      .setStrokeStyle(3, 0xd3b36c, 1)
      .setVisible(false);
    const shieldRing = this.add
      .ellipse(0, 8, 120, 148, 0, 0)
      .setStrokeStyle(3, 0x89d79d, 1)
      .setVisible(false);
    const flash = this.add
      .ellipse(0, 8, 124, 154, 0xffffff, 0)
      .setBlendMode(Phaser.BlendModes.SCREEN);
    const figure = this.createChampionFigure(unit);
    const nameText = this.add.text(0, -112, unit.name, {
      fontFamily: 'Trebuchet MS, sans-serif',
      fontSize: '18px',
      color: '#f4efe1',
      fontStyle: 'bold',
      stroke: '#07111c',
      strokeThickness: 5,
    });
    nameText.setOrigin(0.5);
    const hpTrack = this.add.rectangle(0, -86, 94, 10, 0xffffff, 0.12);
    const hpBarFill = this.add.rectangle(-47 + 47, -86, 94, 10, 0x73d48b, 1);
    const hpValueText = this.add.text(0, -68, `${unit.hp}/${unit.maxHp}`, {
      fontFamily: 'Trebuchet MS, sans-serif',
      fontSize: '12px',
      color: '#bfe8cb',
      stroke: '#07111c',
      strokeThickness: 4,
    });
    hpValueText.setOrigin(0.5);
    const statusText = this.add.text(0, -126, roleLabel(unit.role), {
      fontFamily: 'Trebuchet MS, sans-serif',
      fontSize: '12px',
      color: '#d3b36c',
      stroke: '#07111c',
      strokeThickness: 4,
    });
    statusText.setOrigin(0.5);

    const hitArea = this.add.zone(0, 0, 130, 180).setOrigin(0.5);
    hitArea.setInteractive({ useHandCursor: true });

    container.add([
      shadow,
      hoverGlow,
      targetRing,
      activeRing,
      shieldRing,
      flash,
      figure,
      statusText,
      nameText,
      hpTrack,
      hpBarFill,
      hpValueText,
      hitArea,
    ]);

    this.unitLayer?.add(container);

    hitArea.on('pointerdown', () => {
      if (this.targetableIds.has(unit.id)) {
        this.onTarget(unit.id);
      }
    });

    hitArea.on('pointerover', () => {
      if (this.targetableIds.has(unit.id) && unit.hp > 0) {
        hoverGlow.setVisible(true);
      }
    });

    hitArea.on('pointerout', () => {
      if (!this.targetableIds.has(unit.id)) {
        hoverGlow.setVisible(false);
      }
    });

    const idleTween = this.tweens.add({
      targets: figure,
      y: '+=6',
      duration: 1450 + Math.round(position.y),
      yoyo: true,
      repeat: -1,
      ease: 'Sine.InOut',
    });
    const activeTween = this.tweens.add({
      targets: activeRing,
      alpha: { from: 0.35, to: 1 },
      scaleX: { from: 0.96, to: 1.06 },
      scaleY: { from: 0.96, to: 1.06 },
      duration: 620,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.InOut',
      paused: true,
    });

    return {
      unitId: unit.id,
      team: unit.team,
      accentColor,
      homeX: position.x,
      homeY: position.y,
      container,
      figure,
      hoverGlow,
      activeRing,
      targetRing,
      shieldRing,
      flash,
      nameText,
      hpValueText,
      hpBarFill,
      statusText,
      hitArea,
      idleTween,
      activeTween,
    };
  }

  private createChampionFigure(unit: CombatUnit) {
    const figure = this.add.container(0, 0);
    const teamTint = unit.team === 'blue' ? 0x4fa7dd : 0xd66b57;
    const accent = toColorNumber(unit.accent);
    const outline = 0xf4efe1;
    const dark = unit.team === 'blue' ? 0x173245 : 0x442018;
    const skin = 0xf0c7aa;
    const legs = this.add.rectangle(0, 34, 34, 44, dark);
    const torso = this.add.rectangle(0, 0, 60, 78, accent);
    torso.setStrokeStyle(3, outline, 0.8);
    const chest = this.add.rectangle(0, -6, 28, 30, teamTint, 0.92);
    const head = this.add.circle(0, -56, 22, skin);
    head.setStrokeStyle(3, outline, 0.45);

    figure.add([legs, torso, chest, head]);

    switch (unit.id) {
      case 'blue-garen':
        figure.add(this.add.rectangle(40, -6, 10, 92, 0xd9dde5));
        figure.add(this.add.triangle(40, -58, 0, 18, 18, 18, 9, -6, 0xf4efe1));
        figure.add(this.add.rectangle(-18, -12, 18, 22, 0xe0b764));
        break;
      case 'blue-ahri':
        figure.add(this.add.triangle(-18, -78, -10, 18, 0, -10, 10, 18, 0xf6d7da));
        figure.add(this.add.triangle(18, -78, -10, 18, 0, -10, 10, 18, 0xf6d7da));
        figure.add(this.add.circle(36, -20, 12, 0x8ee5ff));
        figure.add(
          this.add
            .arc(-10, 42, 22, 200, 340, false, 0xffe7ef, 0)
            .setStrokeStyle(8, 0xffe7ef, 1),
        );
        figure.add(
          this.add
            .arc(10, 42, 22, 200, 340, false, 0xffe7ef, 0)
            .setStrokeStyle(8, 0xffe7ef, 1),
        );
        break;
      case 'blue-jinx':
        figure.add(this.add.line(-28, -12, 0, 0, -26, 66, 0x49c7e6).setLineWidth(8));
        figure.add(this.add.line(28, -12, 0, 0, 26, 66, 0x49c7e6).setLineWidth(8));
        figure.add(this.add.rectangle(42, 10, 52, 14, 0x303b5f).setRotation(-0.2));
        figure.add(this.add.circle(58, 12, 8, 0xf26f80));
        break;
      case 'red-darius':
        figure.add(this.add.rectangle(44, -2, 10, 88, 0xd8dadf));
        figure.add(this.add.triangle(44, -48, -16, 18, 16, 18, 0, -18, 0xc54638));
        figure.add(this.add.triangle(44, 40, -16, -18, 16, -18, 0, 18, 0xd8dadf));
        break;
      case 'red-annie':
        figure.add(this.add.circle(-18, -74, 12, 0x5b2d26));
        figure.add(this.add.circle(18, -74, 12, 0x5b2d26));
        figure.add(this.add.circle(36, -20, 14, 0xff9e47));
        break;
      case 'red-caitlyn':
        figure.add(this.add.rectangle(0, -84, 44, 14, 0x314769));
        figure.add(this.add.rectangle(0, -96, 26, 18, 0x314769));
        figure.add(this.add.rectangle(40, 6, 66, 10, 0x2e3343).setRotation(-0.12));
        figure.add(this.add.circle(56, 4, 7, 0xc9cbd0));
        break;
      default:
        figure.add(this.add.circle(0, -84, 16, accent));
        break;
    }

    return figure;
  }

  private spawnProjectile(
    from: UnitVisual,
    to: UnitVisual,
    color: number,
  ) {
    const distance = Phaser.Math.Distance.Between(
      from.homeX,
      from.homeY - 14,
      to.homeX,
      to.homeY - 14,
    );
    const angle = Phaser.Math.Angle.Between(
      from.homeX,
      from.homeY - 14,
      to.homeX,
      to.homeY - 14,
    );
    const beam = this.add
      .rectangle(
        (from.homeX + to.homeX) / 2,
        (from.homeY + to.homeY - 28) / 2,
        distance,
        8,
        color,
        0.86,
      )
      .setRotation(angle)
      .setBlendMode(Phaser.BlendModes.SCREEN);

    this.fxLayer?.add(beam);

    this.tweens.add({
      targets: beam,
      alpha: 0,
      scaleX: 0.28,
      duration: 280,
      ease: 'Cubic.Out',
      onComplete: () => beam.destroy(),
    });
  }

  private spawnShockwave(x: number, y: number, color: number) {
    const ring = this.add.circle(x, y, 20, color, 0.1);
    ring.setStrokeStyle(4, color, 0.7);
    ring.setBlendMode(Phaser.BlendModes.SCREEN);
    this.fxLayer?.add(ring);

    this.tweens.add({
      targets: ring,
      scale: 6.2,
      alpha: 0,
      duration: 540,
      ease: 'Cubic.Out',
      onComplete: () => ring.destroy(),
    });
  }

  private spawnShieldBurst(x: number, y: number, color: number) {
    const ring = this.add.ellipse(x, y, 80, 110, color, 0.08);
    ring.setStrokeStyle(4, color, 0.82);
    ring.setBlendMode(Phaser.BlendModes.SCREEN);
    this.fxLayer?.add(ring);

    this.tweens.add({
      targets: ring,
      scaleX: 1.52,
      scaleY: 1.38,
      alpha: 0,
      duration: 520,
      ease: 'Cubic.Out',
      onComplete: () => ring.destroy(),
    });
  }

  private spawnFloatingText(
    x: number,
    y: number,
    text: string,
    color: string,
  ) {
    const floater = this.add.text(x, y, text, {
      fontFamily: 'Trebuchet MS, sans-serif',
      fontSize: '18px',
      color,
      fontStyle: 'bold',
      stroke: '#07111c',
      strokeThickness: 6,
    });
    floater.setOrigin(0.5);
    this.fxLayer?.add(floater);

    this.tweens.add({
      targets: floater,
      y: y - 42,
      alpha: 0,
      duration: 620,
      ease: 'Cubic.Out',
      onComplete: () => floater.destroy(),
    });
  }

  private spawnStunStars(x: number, y: number) {
    const starLeft = this.add.star(x - 16, y, 5, 5, 10, 0xffe08f);
    const starRight = this.add.star(x + 16, y - 6, 5, 5, 10, 0xffe08f);
    this.fxLayer?.add([starLeft, starRight]);

    this.tweens.add({
      targets: [starLeft, starRight],
      angle: 240,
      y: '-=14',
      alpha: 0,
      duration: 680,
      ease: 'Cubic.Out',
      onComplete: () => {
        starLeft.destroy();
        starRight.destroy();
      },
    });
  }

  private flashUnit(visual: UnitVisual, color: number) {
    visual.flash.fillColor = color;
    visual.flash.fillAlpha = 0.64;
    this.tweens.killTweensOf(visual.flash);
    this.tweens.add({
      targets: visual.flash,
      alpha: 0,
      duration: 320,
      ease: 'Cubic.Out',
    });
  }
}
