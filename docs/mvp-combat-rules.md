# MVP Combat Rules

## Prototype Goal

- Deliver a fast, replayable 3v3 turn-based skirmish in the browser.
- Keep the rules readable enough to balance quickly without a backend.
- Prioritize clarity over full League of Legends feature parity.

## First Playable Roster

### Blue Team

- Garen: durable frontliner with shield and cleave damage
- Ahri: burst mage with single-target stun
- Jinx: fast finisher with ranged crowd control

### Red Team

- Darius: bruiser with heavy single-target execute pressure
- Annie: mage with shield and area damage
- Caitlyn: ranged carry with pick potential

## Battle Loop

1. Both teams enter a 3v3 fight with fixed stats and three abilities each.
2. Turn order is determined by speed, from highest to lowest, then repeats each round.
3. At the start of a champion's turn, their cooldowns tick down by 1.
4. A stunned champion loses that turn after cooldown reduction.
5. The acting champion uses one available ability.
6. Combat continues until one full team is defeated.

## Current Rules

- Health: champions are defeated at 0 HP
- Shield: absorbs incoming damage before HP is lost
- Stun: skips the target's next turn
- Cooldowns: set after use, reduce only on that champion's future turns
- Targeting:
  - `enemy`: choose one living enemy
  - `self`: immediately affects the caster
  - `all-enemies`: immediately affects all living enemies

## AI Heuristics

- Prefer high-damage abilities when a kill is possible
- Use self-shielding more aggressively at low HP
- Target the lowest-HP living enemy for single-target damage and stun

## Scope Kept Out Of MVP

- Gold, items, leveling, mana, and positioning grids
- Trait synergies, summons, crit, dodge, and elemental terrain
- Drafting, PvP, progression, and account systems
