# Session Handoff

## Date

- 2026-03-12

## Current State

- Primary playable build is `native_tactics`
- Recent work focused on making the game feel like a real packaged tactics game rather than a prototype
- Working tree was clean before this handoff file was added

## Major Work Completed This Session

1. Visual/UX polish
- selection, route, reward, summary, and battle HUD text overlap reduced
- selection roster layout adapted to 11-champion pool
- right-side selection panel simplified with doctrine summary and enemy portrait pills
- battle left control panel height constrained so it no longer collides with the bottom bar

2. Tactics presentation upgrade
- standees upgraded with pose differences: `hero`, `ready`, `attack`, `hit`, `victory`
- pose-linked FX added: attack afterimages, hit sparks, victory shards
- cutout asset pipeline added
- generated transparent cutout art pack added under `assets/tactics-cutouts/`

3. Content expansion
- roster expanded to `Blue 11 / Red 11`
- added: `Riven`, `Orianna`, `Akali`, `Sett`
- passives, tactical special mapping, enemy stage pools, art maps, and tests were updated together

4. UX/onboarding/settings
- first-run help overlay added
- help is persisted via `help_overlay_seen`
- `H` / `F1` reopens help
- flow breadcrumb added for non-battle screens
- `F10` settings overlay added
- settings now persist:
  - master volume
  - ambient volume
  - combat pace
  - difficulty

5. Difficulty
- added `Standard` and `Veteran`
- `Standard` preserves current balance
- `Veteran` currently applies enemy-only scaling:
  - enemy HP `+8`
  - enemy damage `+1`
  - enemy speed `+2`
  - boss bonus HP `+12`
  - boss bonus shield `+6`

6. Windows packaging
- Windows build path was switched from `native_game` to `native_tactics`
- new entrypoint: [run_tactics.py](/home/faeqsu10/projects/lol-rift-tactics/run_tactics.py)
- workflow and build script were updated accordingly

## Important Commits

- `dbcfdc6` `build(windows): native_tactics exe로 전환`
- `b4896ca` `feat(tactics): 설정과 난이도 2단계 추가`
- `2d567d2` `feat(tactics): 난이도 라벨 가시성 보강`
- `a7c2358` `feat(tactics): 온보딩 오버레이와 흐름 브레드크럼 추가`
- `06ed0a0` `feat(tactics): 설정 오버레이와 저장된 설정 추가`
- `362328e` `feat(tactics): 챔피언 로스터 4차 확장`

## Latest Verified Windows Artifact

- exe:
  - [rift-tactics-win.exe](/home/faeqsu10/projects/lol-rift-tactics/release/windows-artifact-22985639583/rift-tactics-win.exe)
- zip:
  - [rift-tactics-win.zip](/home/faeqsu10/projects/lol-rift-tactics/release/windows-artifact-22985639583/rift-tactics-win.zip)
- source workflow run:
  - `22985639583`

## Current Validation Status

- `./.venv/bin/python -m native_game.tests` passed earlier in session
- `./.venv/bin/python -m native_tactics.tests` passed
  - latest observed count: `98 tests`
- `npm run tactics:smoke` passed
- `npm run tactics:capture` passed
- Windows GitHub Actions build for `native_tactics` succeeded

## Known Gaps

- Linux packaging path still points at `native_game` via `native:package`; Windows `.exe` path is already `native_tactics`
- generated cutout pack is serviceable, but still not hand-tuned or based on true transparent source art
- difficulty is functional but still needs balance tuning and stronger in-game surfacing
- settings overlay does not yet include resolution/fullscreen/window-scale controls

## Recommended Next Tasks

1. Tune `Veteran` difficulty
- verify the current enemy-only scaling feels fair over a full run
- consider showing difficulty more explicitly in route/reward/battle summary text

2. Improve real art quality
- replace generated cutouts with hand-tuned or true transparent cutouts champion by champion
- if needed, add per-champion crop tuning metadata

3. Expand authored content
- more boss variants
- more route/node/event combinations
- more finale-specific presentation and rules

4. Finish release readiness
- decide whether Linux packaging should also target `native_tactics`
- tighten README packaging instructions around the new Windows tactics build

## Useful Commands

- run tactics locally:
```bash
npm run tactics:play
```

- run tactics tests:
```bash
./.venv/bin/python -m native_tactics.tests
```

- tactics smoke:
```bash
npm run tactics:smoke
```

- tactics capture:
```bash
npm run tactics:capture
```

- regenerate cutouts:
```bash
npm run tactics:generate-cutouts
```

- latest downloaded Windows artifact directory:
```bash
/home/faeqsu10/projects/lol-rift-tactics/release/windows-artifact-22985639583/
```

## Suggested Resume Prompt

`Read AGENTS.md, PROJECT_CONTEXT.md, and docs/SESSION_HANDOFF_2026-03-12.md, then continue improving native_tactics from the current release-candidate state.`
