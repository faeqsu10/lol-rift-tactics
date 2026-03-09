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
- The native build opens a real game window and supports:
  - champion select screen before entering combat
  - 3v3 combat
  - player-controlled blue team and AI-controlled red team
  - bundled Korean font rendering
  - champion icon art applied to battlefield units and side panels
  - upgraded battlefield presentation, UI panels, and champion standees
  - procedural sound effects and ambient audio
  - vendored PulseAudio runtime fallback for WSL/Linux environments missing `libpulse0`
  - animated unit idle/cast/hit states
  - projectile and ring effects
  - floating combat text
  - speed-based turn order
  - cooldowns, shields, stun, and simple enemy AI
  - direct enemy target selection for single-target skills
- Initial roster:
  - Blue team: Garen, Ahri, Jinx
  - Red team: Darius, Annie, Caitlyn
- Expanded selectable roster:
  - Blue pool: Garen, Ahri, Jinx, Lux, Vi
  - Red pool: Darius, Annie, Caitlyn, Morgana, Yasuo
- Native dependency file: `requirements-native.txt`
- Native run command: `.venv/bin/python -m native_game`
- Native tests: `.venv/bin/python -m native_game.tests`
- Screenshot capture command: `npm run native:capture`
- Audio implementation: `native_game/audio.py`
- Runtime bootstrap: `native_game/__main__.py`
- Vendored WSL audio libs: `.vendor/pulse/extracted/usr/lib/x86_64-linux-gnu`
- Task tracker: `tasks/todo.md`
- Lessons log: `tasks/lessons.md`
- Dev log: `docs/DEVLOG.md`
- Verified locally on March 9, 2026:
  - `python -m native_game.tests` passes
  - headless smoke run with SDL dummy drivers passes
  - headless screenshot capture passes

## Recommended Next Steps

1. Replace shape-based placeholder characters with real sprite art or sprite sheets.
2. Add distinct animation sets for attack, impact, defeat, and victory.
3. Add sound effects, music stubs, and stronger camera feedback.
4. Improve battlefield presentation with tile art, lane markers, and scene dressing.
5. Re-evaluate long-term engine choice only after the native combat feel is validated.

## Resume Prompt

When opening Codex again in this folder, a good prompt is:

`Read AGENTS.md and PROJECT_CONTEXT.md, then continue improving the native Pygame combat prototype for League of Legends: Rift Tactics so it feels closer to a real game.`
