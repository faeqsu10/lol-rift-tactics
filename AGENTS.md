# AGENTS.md

This file provides project-specific guidance to Codex and other coding agents working in this repository.

## Project Summary

- Project: `League of Legends: Rift Tactics`
- Type: fan-made turn-based tactics prototype based on League of Legends champions
- Primary target: native `Pygame` playable prototype
- Main release candidate: `native_tactics`
- Near-term goal: turn the current tactics run into a polished, replayable vertical slice before expanding scope further

## Stack and Commands

- Native client: Python 3 + `Pygame`
- Legacy web prototype: React 19 + TypeScript + Vite
- Native setup: `npm run native:setup`
- Arena prototype run: `npm run native:play`
- Tactics prototype run: `npm run tactics:play`
- Native arena tests: `npm run native:test`
- Native tactics tests: `npm run tactics:test`
- Headless smoke checks: `npm run native:smoke`, `npm run tactics:smoke`
- Screenshot capture: `npm run native:capture`, `npm run tactics:capture`
- Native package build: `npm run native:package`
- Legacy web build: `npm run build`

## Current Architecture

- Main gameplay path lives in `native_tactics/`.
- `native_game/` remains as the older arena-style native prototype.
- `src/` contains the legacy web prototype and should not drive core roadmap decisions unless explicitly revived.
- Prefer keeping combat rules, turn resolution, AI, and progression in explicit Python logic rather than UI event code.
- Favor this separation as native code evolves:
  - `native_tactics/engine.py` for tactical rules and deterministic state transitions
  - `native_tactics/data.py` for champion kits, terrain, boss, and encounter data
  - `native_tactics/app.py` for rendering, screen flow, and input handling
  - `native_tactics/history.py` for persisted run-history and doctrine state

This target structure is guidance, not a requirement to refactor immediately.

## Engineering Priorities

### 1. MVP First

- Prefer the smallest change that improves the playable native prototype.
- Do not build backend services, accounts, matchmaking, or online features.

### 2. Keep Game Rules Deterministic

- Turn order, targeting, damage, cooldowns, terrain effects, AI decisions, and win conditions should live in explicit engine logic, not inside rendering code.

### 3. Separate Data From Behavior

- Champion kits and balance values should be data-driven where practical.
- Avoid scattering combat constants across rendering code or screen-state branches.

### 4. Preserve Strictness

- Keep Python and TypeScript changes type-safe where practical.
- Avoid weakening compiler or test expectations without a concrete reason.

### 5. Keep Documentation In Sync

- When commands, architecture, or project direction change materially, update `README.md`, `PROJECT_CONTEXT.md`, and this file together.

## Working Style For Agents

- Read `PROJECT_CONTEXT.md` at the start of a new session for current status and handoff notes.
- Prefer simple state models and pure functions for combat logic.
- Avoid premature abstractions; extract shared systems only after repeated use is real.
- Verify code changes with the narrowest useful command. For the main path, prefer `npm run tactics:test` and `npm run tactics:smoke`.
- If you touch the legacy web prototype, verify with `npm test` or `npm run build`.
- Do not commit or push unless the user explicitly asks.
- Repo-local specialist agents live under `.claude/agents/rift-tactics/`; use the matching role when the task is clearly about art, combat presentation, audio, UX, content, balance, AI, QA/release, or docs sync.

## Domain Notes

- Treat this as a prototype inspired by League of Legends, not a content-complete game.
- `native_tactics` is the product direction; `native_game` and `src/` are supporting tracks unless the user redirects.
- Current near-term priority is presentation and feel: node-specific cut-in art/sound, first-pass sprites/animation, and map/objective variety.
