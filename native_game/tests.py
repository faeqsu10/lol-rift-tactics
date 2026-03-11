from __future__ import annotations

import unittest

from .combat import BattleController
from .data import SELECTABLE_BLUE_IDS, SELECTABLE_RED_IDS


class BattleControllerTests(unittest.TestCase):
    def test_fastest_champion_starts_first(self) -> None:
        controller = BattleController()
        self.assertEqual(controller.get_active_unit().name, "징크스")

    def test_custom_lineup_is_used(self) -> None:
        controller = BattleController(
            ("blue-lux", "blue-vi", "blue-ahri"),
            ("red-yasuo", "red-morgana", "red-caitlyn"),
        )
        self.assertEqual(
            [unit.id for unit in controller.units],
            [
                "blue-lux",
                "blue-vi",
                "blue-ahri",
                "red-yasuo",
                "red-morgana",
                "red-caitlyn",
            ],
        )

    def test_expanded_roster_is_available(self) -> None:
        self.assertIn("blue-ezreal", SELECTABLE_BLUE_IDS)
        self.assertIn("blue-leona", SELECTABLE_BLUE_IDS)
        self.assertIn("blue-ashe", SELECTABLE_BLUE_IDS)
        self.assertIn("blue-braum", SELECTABLE_BLUE_IDS)
        self.assertIn("blue-riven", SELECTABLE_BLUE_IDS)
        self.assertIn("blue-orianna", SELECTABLE_BLUE_IDS)
        self.assertIn("red-zed", SELECTABLE_RED_IDS)
        self.assertIn("red-lissandra", SELECTABLE_RED_IDS)
        self.assertIn("red-katarina", SELECTABLE_RED_IDS)
        self.assertIn("red-brand", SELECTABLE_RED_IDS)
        self.assertIn("red-akali", SELECTABLE_RED_IDS)
        self.assertIn("red-sett", SELECTABLE_RED_IDS)
        self.assertEqual(len(SELECTABLE_BLUE_IDS), 11)
        self.assertEqual(len(SELECTABLE_RED_IDS), 11)

    def test_enemy_targeting_returns_all_living_enemies(self) -> None:
        controller = BattleController()
        self.assertEqual(
            controller.get_valid_target_ids("zap"),
            ["red-darius", "red-annie", "red-caitlyn"],
        )
        controller.resolve_active_turn("flame-chompers", "red-caitlyn")
        self.assertEqual(
            controller.get_valid_target_ids("orb-of-deception"),
            ["red-darius", "red-annie", "red-caitlyn"],
        )

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
