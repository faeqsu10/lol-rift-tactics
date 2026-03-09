import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import {
  createInitialBattleState,
  getActiveUnit,
  getUnitById,
  resolvePlayerTurn,
} from './engine';

describe('battle engine', () => {
  it('starts with the fastest champion taking the first turn', () => {
    const state = createInitialBattleState();

    assert.equal(getActiveUnit(state)?.name, '징크스');
  });

  it('skips a stunned enemy turn and advances to the next champion', () => {
    const initialState = createInitialBattleState();
    const nextState = resolvePlayerTurn(
      initialState,
      'flame-chompers',
      'red-caitlyn',
    );

    assert.equal(getUnitById(nextState.units, 'red-caitlyn')?.stunTurns, 0);
    assert.equal(getActiveUnit(nextState)?.name, '아리');
    assert.match(
      nextState.log[0]?.text ?? '',
      /케이틀린, 기절 상태로 턴을 넘긴다\./,
    );
  });

  it('applies direct damage and passes initiative after a player action', () => {
    const initialState = createInitialBattleState();
    const nextState = resolvePlayerTurn(initialState, 'zap', 'red-caitlyn');

    assert.equal(getUnitById(nextState.units, 'red-caitlyn')?.hp, 57);
    assert.equal(getActiveUnit(nextState)?.name, '케이틀린');
  });
});
