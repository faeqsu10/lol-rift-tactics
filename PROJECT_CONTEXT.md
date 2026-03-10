# Project Context

## Project

- Game name: `League of Legends: Rift Tactics`
- Repo name: `lol-rift-tactics`
- Local path: `/home/faeqsu10/projects/lol-rift-tactics`
- GitHub remote: `https://github.com/faeqsu10/lol-rift-tactics.git`

## Current Direction

- This is a fan-made turn-based combat game based on League of Legends champions.
- The primary goal is no longer a browser-first prototype.
- The current priority is a native `Pygame` prototype that feels like an actual game window with motion, targeting, and combat feedback.
- There are now two native tracks in the same repo:
  - `native_game`: arena-style 3v3 combat prototype
  - `native_tactics`: grid-based movement tactics prototype

## Decisions Already Made

- Use the direct title `League of Legends: Rift Tactics`.
- Keep all ongoing work in this repository.
- Use `AGENTS.md` for durable repository rules and this file for current handoff status.
- Treat the native `Pygame` client as the main playable build until a better engine decision is made.

## Current Status

- Local Git repo is initialized.
- `origin` is connected to GitHub.
- The initial `README.md` commit exists on GitHub.
- A web prototype still exists locally under `src/*`, but it is no longer the preferred gameplay path.
- A native `Pygame` prototype now exists under `native_game/*`.
- A second native tactics prototype now exists under `native_tactics/*`.
- The native build opens a real game window and supports:
  - champion select screen before entering combat
  - 3v3 combat
  - player-controlled blue team and AI-controlled red team
  - bundled Korean font rendering
  - champion icon art applied to battlefield units and side panels
  - upgraded battlefield presentation, UI panels, and champion standees
  - procedural sound effects and ambient audio
  - champion-themed original selection and cast sounds
  - vendored PulseAudio runtime fallback for WSL/Linux environments missing `libpulse0`
  - animated unit idle/cast/hit states
  - projectile and ring effects
  - floating combat text
  - speed-based turn order
  - cooldowns, shields, stun, and simple enemy AI
  - direct enemy target selection for single-target skills
- The tactics build opens a separate real game window and supports:
  - champion select before battle
  - manual blue-team starting deployment
  - 8x6 grid battlefield
  - three-battle expedition structure: scout -> elite -> finale
  - movement plus action on each turn
  - obstacle tiles and movement range highlighting
  - role-based tactical ranges with champion-specific ability names
  - champion-specific passive traits with second-pass differentiation
  - champion-specific tactical special picks so marquee skills stay consistent
  - enemy intent preview during red turns with predicted damage, threat tiles, multi-target counts, next-enemy warning, enemy-phase summaries, danger labels, and chain-focus warnings
  - stage-based terrain tiles: brush, rune, hazard
  - elite enemies in later expedition stages with trait rules
  - stage 3 boss battle with a marked boss unit and one-time phase shift
  - stage 3 boss battle now swaps route goals for boss-specific finale objectives with weaken-or-empower phase outcomes
  - stage 3 boss battle now branches into multiple boss patterns with dedicated finale terrain and obstacle layouts
  - route selection between battles with three risk/reward options and temporary next-battle modifiers
  - route cards now include a second-pass battle event for the next fight
  - route cards now also include a run node branch with rest/event/elite variants
  - each run node now rolls a node-specific follow-up event that is previewed on route cards and applied in deploy/battle HUD plus battle modifiers
  - route-specific map objectives during battles with progress HUD and marked objective tiles
  - completed objectives grant an automatic run bonus before the normal reward pick
  - failed objectives can queue a next-battle penalty that persists through the next route/deploy step
  - rest nodes can clear queued penalties, event nodes can amplify route-event bonuses/penalties, and elite nodes can add extra elite enemies plus a victory bonus
  - boss awakening now creates a hazard pulse on adjacent tiles and drives a dedicated finale banner/panel presentation
  - battle recap summary before choosing the next route
  - run-end summary screen with cumulative stats, build highlights, battle timeline, and direct replay/select actions
  - persisted run history with best-run comparison on the summary screen
  - node-specific and finale-specific battle-start cut-in presentation with a short intro lock
  - terrain-aware red-team AI movement and targeting
  - objective-aware red-team AI that contests marked tiles and pressure zones
  - post-victory reward pick with next-enemy preview
  - headless screenshot capture and tests
- Initial roster:
  - Blue team: Garen, Ahri, Jinx
  - Red team: Darius, Annie, Caitlyn
- Expanded selectable roster:
  - Blue pool: Garen, Ahri, Jinx, Lux, Vi, Ezreal, Leona, Ashe, Braum
  - Red pool: Darius, Annie, Caitlyn, Morgana, Yasuo, Zed, Lissandra, Katarina, Brand
- Native dependency file: `requirements-native.txt`
- Native run command: `.venv/bin/python -m native_game`
- Tactics run command: `.venv/bin/python -m native_tactics`
- Native package command: `npm run native:package`
- Native packaged executable: `release/rift-tactics`
- Windows package workflow: `.github/workflows/build-windows-exe.yml`
- Windows build script: `scripts/build-windows.ps1`
- Native tests: `.venv/bin/python -m native_game.tests`
- Tactics tests: `.venv/bin/python -m native_tactics.tests`
- Tactics history save path: `.local/native_tactics_history.json`
- Screenshot capture command: `npm run native:capture`
- Tactics screenshot capture command: `npm run tactics:capture`
- Audio implementation: `native_game/audio.py`
- Runtime bootstrap: `native_game/__main__.py`
- Runtime path helper: `native_game/runtime.py`
- Vendored WSL audio libs: `.vendor/pulse/extracted/usr/lib/x86_64-linux-gnu`
- Task tracker: `tasks/todo.md`
- Lessons log: `tasks/lessons.md`
- Dev log: `docs/DEVLOG.md`
- Tactics fun roadmap: `docs/TACTICS_FUN_ROADMAP.md`
- Tactics UX research: `docs/TACTICS_UX_RESEARCH.md`
- Tactics release target: `docs/TACTICS_RELEASE_TARGET.md`
- Tactics milestones: `docs/TACTICS_MILESTONES.md`
- Verified locally on March 11, 2026:
  - `python -m native_game.tests` passes
  - headless smoke run with SDL dummy drivers passes
  - headless screenshot capture passes
  - `python -m native_tactics.tests` passes
  - `npm run tactics:smoke` passes
  - `npm run tactics:capture` passes

## Recommended Next Steps

1. Replace shape-based placeholder characters with real sprite art or sprite sheets.
2. Expand map and objective variety on top of the boss loop.
3. Add more authored boss variants or finale-only special rules on top of the new boss pattern system.
4. Add richer meta progression or unlock structure on top of the saved run-history layer.
5. Add more authored node/event presentation on top of the new cut-in system.

## Resume Prompt

When opening Codex again in this folder, a good prompt is:

`Read AGENTS.md and PROJECT_CONTEXT.md, then continue improving the native Pygame combat prototype for League of Legends: Rift Tactics so it feels closer to a real game.`
