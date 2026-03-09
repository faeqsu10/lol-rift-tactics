from __future__ import annotations

import unittest

from .combat import BattleController


class BattleControllerTests(unittest.TestCase):
    def test_fastest_champion_starts_first(self) -> None:
        controller = BattleController()
        self.assertEqual(controller.get_active_unit().name, "징크스")

    def test_stun_skips_enemy_turn(self) -> None:
        controller = BattleController()
        action = controller.resolve_active_turn("flame-chompers", "red-caitlyn")
        self.assertIsNotNone(action)
        caitlyn = controller.get_unit("red-caitlyn")
        self.assertEqual(caitlyn.stun_turns, 0)
        self.assertEqual(controller.get_active_unit().name, "아리")
        self.assertIn("기절 상태로 턴을 넘긴다", controller.state.log[0])

    def test_direct_damage_applies(self) -> None:
        controller = BattleController()
        action = controller.resolve_active_turn("zap", "red-caitlyn")
        self.assertIsNotNone(action)
        caitlyn = controller.get_unit("red-caitlyn")
        self.assertEqual(caitlyn.hp, 57)
        self.assertEqual(controller.get_active_unit().name, "케이틀린")


if __name__ == "__main__":
    unittest.main()
