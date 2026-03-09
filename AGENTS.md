# AGENTS.md

This file provides project-specific guidance to Codex and other coding agents working in this repository.

## Project Summary

- Project: `League of Legends: Rift Tactics`
- Type: fan-made turn-based tactics prototype based on League of Legends champions
- Primary target: web-based playable MVP
- Near-term goal: prove the core combat loop before expanding roster, maps, or progression systems

## Stack and Commands

- Frontend: React 19 + TypeScript + Vite
- Install dependencies: `npm install`
- Start dev server: `npm run dev`
- Build for production: `npm run build`
- Preview build: `npm run preview`

## Current Architecture

- Entry HTML: `index.html`
- React bootstrap: `src/main.tsx`
- Keep the project frontend-only unless the game design clearly requires backend state or services.
- As gameplay code appears, prefer this separation:
  - `src/game/` for combat rules, turn resolution, state transitions, and AI
  - `src/data/` for champion stats, abilities, traits, and encounter definitions
  - `src/components/` for UI and presentation
  - `src/app/` or `src/screens/` for page-level composition

This target structure is guidance, not a requirement to refactor immediately.

## Engineering Priorities

### 1. MVP First

- Prefer the smallest change that moves the playable prototype forward.
- Do not build account systems, persistence, matchmaking, or backend APIs before the combat loop justifies them.

### 2. Keep Game Rules Deterministic

- Turn order, targeting, damage, cooldowns, mana, and win conditions should live in explicit TypeScript logic, not inside JSX event handlers.

### 3. Separate Data From Behavior

- Champion kits and balance values should be data-driven where practical.
- Avoid scattering combat constants across components.

### 4. Preserve Strictness

- Keep TypeScript strict mode enabled.
- Avoid weakening compiler options or bypassing type errors without a concrete reason.

### 5. Keep Documentation In Sync

- When commands, architecture, or project direction change materially, update `README.md`, `PROJECT_CONTEXT.md`, and this file together.

## Working Style For Agents

- Read `PROJECT_CONTEXT.md` at the start of a new session for current status and handoff notes.
- Prefer simple state models and pure functions for combat logic.
- Avoid premature abstractions; extract shared systems only after repeated use is real.
- Verify code changes with the narrowest useful command. For app-wide validation, prefer `npm run build` once dependencies are installed.
- Do not commit or push unless the user explicitly asks.

## Domain Notes

- Treat this as a prototype inspired by League of Legends, not a content-complete game.
- Favor placeholder UI and placeholder assets over polish during early development.
