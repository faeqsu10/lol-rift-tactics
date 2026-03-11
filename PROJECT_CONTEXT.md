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
  - saved-history-driven doctrine unlocks that now grant permanent start bonuses or a route reroll choice
  - node-specific and finale-specific battle-start cut-in presentation with a short intro lock
  - node-specific intro motifs, badges, and themed start sounds for rest/event/elite/finale battles
  - boss-specific awakening surge rules that now deal immediate pressure damage and expose predicted danger tiles on the finale map
  - select, route, and summary screens polished to reduce UI clutter and eliminate major text overlap
  - champion select now uses a featured-champion focus panel, horizontal enemy counter preview, and a separated action footer so right-panel overlap stays resolved
  - shared text-fitting helpers now keep route cards, reward buttons, summary buttons, battle side panels, and intro overlays from colliding when Korean labels run long
  - battle presentation first pass with animated battlefield atmosphere, stronger unit emphasis, pulse rings, and attack trails
  - portrait-based tactical standees on deploy and battle screens to reduce the placeholder-token look
  - portrait-driven sprite standees now use scale-aware full-body silhouettes and accessory rendering so select, deploy, and battle units read more like character pieces than tokens
  - standees now also switch between hero, ready, attack, hit, and victory poses so combat states are reflected in the body silhouette and weapon posture
  - pose-linked battle FX now add attack afterimages, hit sparks, and victory shards on top of the standee states to reduce the static-board feel
  - battle-only attack, hit, death, and victory animation states with a short end-of-battle hold so finishing blows are visible
  - stage/finale-specific battlefield themes, richer terrain glyphs, and prop-style obstacle rendering
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
- Local specialist agent pack: `.claude/agents/rift-tactics/*`
- Verified locally on March 11, 2026:
  - `python -m native_game.tests` passes
  - headless smoke run with SDL dummy drivers passes
  - headless screenshot capture passes
  - `python -m native_tactics.tests` passes
  - `npm run tactics:smoke` passes
  - `npm run tactics:capture` passes

## Recommended Next Steps

1. Keep `AGENTS.md`, `README.md`, and `PROJECT_CONTEXT.md` aligned around the native-first direction whenever priorities shift.
2. Use the local specialist agents under `.claude/agents/rift-tactics/` when work is clearly about art, audio, UX, content, AI, QA, balance, or docs.
3. Add more authored node/event presentation on top of the new cut-in system.
4. Introduce real sprite art plus first-pass attack/hit/death/victory animation work on top of the new standee fallback.
5. Expand map and objective variety on top of the new doctrine and boss loop.
6. Add more authored boss variants or finale-only special rules after the doctrine layer settles.

## Resume Prompt

When opening Codex again in this folder, a good prompt is:

`Read AGENTS.md and PROJECT_CONTEXT.md, then continue improving the native Pygame combat prototype for League of Legends: Rift Tactics so it feels closer to a real game.`
