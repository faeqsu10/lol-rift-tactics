from __future__ import annotations

import os
import unittest

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from .app import GameApp
from .app import RUN_STAGE_COUNT
from .engine import TacticsController


class TacticsControllerTests(unittest.TestCase):
    def test_reachable_tiles_respect_move_range(self) -> None:
        controller = TacticsController()
        controller.blocked_tiles.clear()
        self.assertIn((3, 5), controller.get_reachable_tiles())
        self.assertNotIn((0, 3), controller.get_reachable_tiles())

    def test_custom_start_positions_are_used_and_preserved_on_reset(self) -> None:
        controller = TacticsController(
            ("blue-garen", "blue-ahri", "blue-jinx"),
            ("red-darius", "red-brand", "red-caitlyn"),
            ((0, 0), (0, 2), (1, 1)),
            ((7, 5), (7, 3), (6, 4)),
        )
        self.assertEqual(controller.get_unit("blue-garen").position, (0, 0))
        self.assertEqual(controller.get_unit("red-brand").position, (7, 3))

        controller.move_active((1, 0))
        controller.reset()

        self.assertEqual(controller.get_unit("blue-garen").position, (0, 0))
        self.assertEqual(controller.get_unit("red-brand").position, (7, 3))

    def test_move_then_basic_attack_applies_damage(self) -> None:
        controller = TacticsController(("blue-jinx",), ("red-darius",))
        controller.blocked_tiles.clear()
        blue = controller.get_unit("blue-jinx")
        red = controller.get_unit("red-darius")
        self.assertIsNotNone(blue)
        self.assertIsNotNone(red)
        blue.position = (0, 1)
        red.position = (5, 1)
        controller.move_active((1, 1))
        result = controller.use_basic("red-darius")
        self.assertIsNotNone(result)
        self.assertEqual(controller.get_unit("red-darius").hp, 87)

    def test_stun_special_skips_enemy_turn(self) -> None:
        controller = TacticsController(("blue-ahri",), ("red-brand",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-ahri").position = (0, 2)
        controller.get_unit("red-brand").position = (3, 2)
        result = controller.use_special("red-brand")
        self.assertIsNotNone(result)
        controller.end_turn()
        self.assertEqual(controller.get_active_unit().id, "blue-ahri")
        self.assertTrue(any("기절 상태로 턴을 넘긴다" in line for line in controller.state.log))

    def test_garen_passive_adds_damage_when_stationary(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-darius",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 1)
        controller.get_unit("red-darius").position = (1, 1)

        result = controller.use_basic("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(result.impacts[0].damage, 22)
        self.assertEqual(controller.get_unit("red-darius").hp, 80)
        self.assertTrue(any("선봉 결의 발동." in note for note in result.notes))

    def test_braum_passive_grants_shield_on_turn_start(self) -> None:
        controller = TacticsController(("blue-braum",), ("red-darius",))
        braum = controller.get_unit("blue-braum")

        self.assertEqual(controller.get_active_unit().id, "blue-braum")
        self.assertEqual(braum.shield, 12)
        self.assertTrue(any("보호막 12 획득" in line for line in controller.state.log))

    def test_preview_ai_intent_reports_target(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 2)
        controller.get_unit("red-brand").position = (4, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand"]

        intent = controller.preview_ai_intent()

        self.assertIsNotNone(intent)
        self.assertEqual(intent.target_id, "blue-garen")
        self.assertIn(intent.action_kind, {"basic", "special"})
        self.assertIn("예정", intent.summary)


class GameAppFlowTests(unittest.TestCase):
    def tearDown(self) -> None:
        pygame.quit()

    def test_reward_selection_advances_run_to_next_deploy(self) -> None:
        app = GameApp(headless=True)
        app._start_deploy()
        app._start_battle()
        app._prepare_reward_phase()

        self.assertEqual(app.screen_mode, "reward")
        self.assertEqual(len(app.reward_option_ids), 3)

        app._select_reward(app.reward_option_ids[0])
        app._advance_after_reward()

        self.assertEqual(app.screen_mode, "deploy")
        self.assertEqual(app.run_stage, 2)
        self.assertEqual(len(app.deploy_assignments), 3)

    def test_final_victory_restart_resets_run_stage(self) -> None:
        app = GameApp(headless=True)
        app._start_deploy()
        app.run_stage = RUN_STAGE_COUNT

        app._start_run_with_current_lineup()

        self.assertEqual(app.run_stage, 1)
        self.assertEqual(app.screen_mode, "deploy")


if __name__ == "__main__":
    unittest.main()
