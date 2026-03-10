from __future__ import annotations

import os
import unittest

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from .app import GameApp
from .app import RUN_STAGE_COUNT
from .data import TACTICAL_BLUEPRINTS_BY_ID
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
        self.assertGreater(intent.predicted_damage, 0)
        self.assertIn((0, 2), intent.threat_tiles)

    def test_preview_ai_intent_includes_follow_up_enemy_warning(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand", "red-caitlyn"))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 2)
        controller.get_unit("red-brand").position = (4, 2)
        controller.get_unit("red-caitlyn").position = (6, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand", "red-caitlyn"]

        intent = controller.preview_ai_intent()

        self.assertIsNotNone(intent)
        self.assertEqual(intent.follow_up_actor_id, "red-caitlyn")
        self.assertIsNotNone(intent.follow_up_summary)
        self.assertIn("다음 적 차례 예상", intent.follow_up_summary)

    def test_hazard_tile_deals_damage_on_move(self) -> None:
        controller = TacticsController(
            ("blue-garen",),
            ("red-darius",),
            ((0, 1),),
            ((7, 1),),
            terrain_tiles={(1, 1): "hazard"},
        )
        controller.blocked_tiles.clear()

        result = controller.move_active((1, 1))

        self.assertIsNotNone(result)
        self.assertEqual(result.impacts[0].damage, 6)
        self.assertEqual(controller.get_unit("blue-garen").hp, 92)

    def test_rune_tile_boosts_damage_for_turn(self) -> None:
        controller = TacticsController(
            ("blue-garen",),
            ("red-darius",),
            ((0, 1),),
            ((1, 1),),
            terrain_tiles={(0, 1): "rune"},
        )
        controller.blocked_tiles.clear()

        result = controller.use_basic("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(result.impacts[0].damage, 25)
        self.assertTrue(any("룬 지대 강화 발동." in note for note in result.notes))

    def test_ai_avoids_hazard_when_rune_tile_exists(self) -> None:
        controller = TacticsController(
            ("blue-garen",),
            ("red-brand",),
            ((0, 2),),
            ((4, 2),),
            terrain_tiles={(3, 2): "hazard", (5, 2): "rune"},
        )
        controller.blocked_tiles.clear()
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand"]

        destination = controller._choose_ai_move(controller.get_unit("red-brand"))

        self.assertNotEqual(destination, (3, 2))


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

        self.assertEqual(app.screen_mode, "route")
        self.assertEqual(app.run_stage, 2)
        self.assertEqual(len(app.route_option_ids), 3)

    def test_final_victory_restart_resets_run_stage(self) -> None:
        app = GameApp(headless=True)
        app._start_deploy()
        app.run_stage = RUN_STAGE_COUNT

        app._start_run_with_current_lineup()

        self.assertEqual(app.run_stage, 1)
        self.assertEqual(app.screen_mode, "deploy")

    def test_stage_two_marks_elite_enemy(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app._seed_deployment()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        elite_units = [unit for unit in app.controller.units if unit.team == "red" and unit.is_elite]
        self.assertEqual(len(elite_units), 1)
        self.assertGreater(elite_units[0].max_hp, 102)

    def test_reward_then_route_choice_advances_to_deploy(self) -> None:
        app = GameApp(headless=True)
        app._start_deploy()
        app._start_battle()
        app._prepare_reward_phase()
        app._select_reward(app.reward_option_ids[0])
        app._advance_after_reward()

        self.assertEqual(app.screen_mode, "route")
        self.assertEqual(len(app.route_option_ids), 3)

        app._select_route(app.route_option_ids[0])
        app._advance_after_route()

        self.assertEqual(app.screen_mode, "deploy")
        self.assertIsNotNone(app.current_route_id)

    def test_assault_route_boosts_next_battle_damage(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.current_route_id = "assault-line"
        app._seed_deployment()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        garen = app.controller.get_unit("blue-garen")
        base_damage = next(effect.amount for effect in garen.basic_ability.effects if effect.kind == "damage")
        self.assertGreaterEqual(base_damage, 20)

    def test_hidden_trail_preview_adds_brush_tiles_to_route_screen(self) -> None:
        app = GameApp(headless=True)
        app.run_stage = 2

        base_brush_count = sum(1 for terrain_id in app._terrain_tiles_for_stage().values() if terrain_id == "brush")
        preview_brush_count = sum(
            1
            for terrain_id in app._terrain_tiles_for_stage(route_id="hidden-trail").values()
            if terrain_id == "brush"
        )

        self.assertGreater(preview_brush_count, base_brush_count)

    def test_rapid_flank_increases_both_team_speed(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 1
        app.current_route_id = "rapid-flank"
        app._seed_deployment()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        blue_speed = app.controller.get_unit("blue-garen").speed
        red_speed = app.controller.get_unit("red-darius").speed
        self.assertEqual(blue_speed, TACTICAL_BLUEPRINTS_BY_ID["blue-garen"].speed + 5)
        self.assertEqual(red_speed, TACTICAL_BLUEPRINTS_BY_ID["red-darius"].speed + 2)

    def test_scorched_march_preview_adds_hazard_tiles(self) -> None:
        app = GameApp(headless=True)
        app.run_stage = 2

        base_hazard_count = sum(1 for terrain_id in app._terrain_tiles_for_stage().values() if terrain_id == "hazard")
        preview_hazard_count = sum(
            1
            for terrain_id in app._terrain_tiles_for_stage(route_id="scorched-march").values()
            if terrain_id == "hazard"
        )

        self.assertGreater(preview_hazard_count, base_hazard_count)

    def test_supply_line_objective_completes_on_marked_tile(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = 2
        app.current_route_id = "supply-line"
        app.deploy_assignments = {(2, 2): "blue-garen"}
        app.red_deploy_assignments = {(7, 2): "red-darius"}

        controller = app._build_controller_from_current_setup()
        controller.blocked_tiles.clear()
        app._attach_controller(controller)
        app.current_objective = app._build_battle_objective()
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]

        result = app.controller.move_active((3, 2))
        app._apply_action_result(result)

        self.assertTrue(app.current_objective.completed)
        self.assertEqual(app.current_objective.progress, 1)

    def test_assault_objective_grants_bonus_reward_on_victory(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = 2
        app.current_route_id = "assault-line"
        app.deploy_assignments = {(0, 1): "blue-garen"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.current_objective = app._build_battle_objective()
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.controller.get_unit("red-darius").hp = 1

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertEqual(app.screen_mode, "reward")
        self.assertEqual(app.run_bonuses["bonus-damage"], 1)
        self.assertIn("선제 제압", app.last_objective_summary)


if __name__ == "__main__":
    unittest.main()
