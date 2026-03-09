export type TeamId = 'blue' | 'red';
export type TargetType = 'enemy' | 'self' | 'all-enemies';
export type Role = 'Vanguard' | 'Mage' | 'Marksman';

export interface DamageEffect {
  kind: 'damage';
  amount: number;
}

export interface ShieldEffect {
  kind: 'shield';
  amount: number;
}

export interface StunEffect {
  kind: 'stun';
  turns: number;
}

export type AbilityEffect = DamageEffect | ShieldEffect | StunEffect;

export interface Ability {
  id: string;
  name: string;
  description: string;
  cooldown: number;
  targetType: TargetType;
  effects: AbilityEffect[];
}

export interface ChampionBlueprint {
  id: string;
  name: string;
  title: string;
  role: Role;
  team: TeamId;
  maxHp: number;
  speed: number;
  accent: string;
  abilities: Ability[];
}

export interface CombatUnit extends ChampionBlueprint {
  hp: number;
  shield: number;
  stunTurns: number;
  cooldowns: Record<string, number>;
}

export interface CombatLogEntry {
  id: string;
  round: number;
  text: string;
}

export interface BattleActionImpact {
  targetId: string;
  effectKinds: AbilityEffect['kind'][];
  damageDealt: number;
  shieldGained: number;
  stunTurnsApplied: number;
  blockedDamage: number;
  defeated: boolean;
}

export interface BattleAction {
  id: string;
  actorId: string;
  actorTeam: TeamId;
  abilityId: string;
  abilityName: string;
  targetType: TargetType;
  targetIds: string[];
  impacts: BattleActionImpact[];
}

export interface BattleState {
  round: number;
  units: CombatUnit[];
  turnQueue: string[];
  activeUnitId: string | null;
  winner: TeamId | null;
  log: CombatLogEntry[];
  lastAction: BattleAction | null;
}
