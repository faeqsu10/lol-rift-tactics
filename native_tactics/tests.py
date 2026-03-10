from __future__ import annotations

import os
import unittest

import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from .app import GameApp
from .app import BattleObjective
from .app import RouteEvent
from .app import NodeFollowUp
from .app import RunNode
from .app import RUN_STAGE_COUNT
from .app import StageModifier
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

    def test_elite_bulwark_trait_grants_shield_on_turn_start(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-darius",))
        controller.get_unit("blue-garen").speed = 1
        darius = controller.get_unit("red-darius")
        darius.is_elite = True
        darius.elite_trait_id = "bulwark"
        controller.state.turn_queue = ["red-darius"]
        controller.state.active_unit_id = None

        controller._prime_next_turn()

        self.assertEqual(controller.get_active_unit().id, "red-darius")
        self.assertEqual(darius.shield, 6)
        self.assertTrue(any("철벽" in line for line in controller.state.log))

    def test_vi_special_after_long_move_increases_damage_and_stun(self) -> None:
        controller = TacticsController(("blue-vi",), ("red-darius",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-vi").position = (0, 2)
        controller.get_unit("red-darius").position = (4, 2)

        controller.move_active((2, 2))
        result = controller.use_special("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(result.impacts[0].damage, 28)
        self.assertEqual(result.impacts[0].stun_applied, 2)

    def test_ezreal_basic_reduces_special_cooldown(self) -> None:
        controller = TacticsController(("blue-ezreal",), ("red-darius",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-ezreal").position = (0, 1)
        controller.get_unit("red-darius").position = (4, 1)
        controller.get_unit("blue-ezreal").cooldowns["trueshot-barrage"] = 2

        result = controller.use_basic("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(controller.get_unit("blue-ezreal").cooldowns["trueshot-barrage"], 1)
        self.assertTrue(any("마력 재장전 발동." in note for note in result.notes))

    def test_lux_special_creates_rune_tile(self) -> None:
        controller = TacticsController(("blue-lux",), ("red-darius",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-lux").position = (0, 2)
        controller.get_unit("red-darius").position = (4, 2)

        result = controller.use_special("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(controller.terrain_tiles[(0, 2)], "rune")
        self.assertEqual(controller.get_unit("blue-lux").shield, 8)

    def test_leona_special_stuns_multiple_targets(self) -> None:
        controller = TacticsController(("blue-leona",), ("red-darius", "red-brand"))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-leona").position = (0, 2)
        controller.get_unit("red-darius").position = (3, 2)
        controller.get_unit("red-brand").position = (4, 2)
        controller.state.active_unit_id = "blue-leona"
        controller.state.turn_queue = ["blue-leona"]

        result = controller.use_special("red-darius")

        self.assertIsNotNone(result)
        self.assertEqual(len(result.impacts), 2)
        self.assertTrue(all(impact.stun_applied == 1 for impact in result.impacts))
        self.assertEqual(controller.get_unit("red-darius").stun_turns, 1)
        self.assertEqual(controller.get_unit("red-brand").stun_turns, 1)

    def test_brand_special_creates_hazard_on_target_tile(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (3, 2)
        controller.get_unit("red-brand").position = (0, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand"]

        result = controller.use_special("blue-garen")

        self.assertIsNotNone(result)
        self.assertEqual(controller.terrain_tiles[(3, 2)], "hazard")

    def test_darius_special_kill_grants_shield(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-darius",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (3, 2)
        controller.get_unit("blue-garen").hp = 10
        controller.get_unit("red-darius").position = (1, 2)
        controller.state.active_unit_id = "red-darius"
        controller.state.turn_queue = ["red-darius"]

        result = controller.use_special("blue-garen")

        self.assertIsNotNone(result)
        self.assertEqual(controller.get_unit("red-darius").shield, 12)

    def test_zed_special_on_isolated_target_refunds_cooldown(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-zed",))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (3, 2)
        controller.get_unit("red-zed").position = (0, 2)
        controller.state.active_unit_id = "red-zed"
        controller.state.turn_queue = ["red-zed"]

        result = controller.use_special("blue-garen")

        self.assertIsNotNone(result)
        self.assertEqual(controller.get_unit("red-zed").shield, 6)
        self.assertEqual(controller.get_unit("red-zed").cooldowns["death-mark"], controller.get_unit("red-zed").special_ability.cooldown - 1)

    def test_boss_phase_triggers_once_below_half_hp(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-darius",))
        controller.blocked_tiles.clear()
        boss = controller.get_unit("red-darius")
        boss.position = (1, 1)
        boss.hp = 35
        boss.is_boss = True
        controller.get_unit("blue-garen").position = (0, 1)

        result = controller.use_basic("red-darius")

        self.assertIsNotNone(result)
        self.assertTrue(boss.boss_phase_triggered)
        self.assertEqual(boss.shield, 18)
        self.assertEqual(boss.speed, TACTICAL_BLUEPRINTS_BY_ID["red-darius"].speed + 2)
        self.assertEqual(boss.move_range, TACTICAL_BLUEPRINTS_BY_ID["red-darius"].move_range + 1)
        self.assertTrue(any("결전 각성 발동." in note for note in result.notes))
        self.assertTrue(any("결전 파동 확산" in note for note in result.notes))
        self.assertEqual(controller.terrain_tiles[(2, 1)], "hazard")
        self.assertEqual(controller.terrain_tiles[(0, 1)], "hazard")

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

    def test_preview_ai_intent_reports_phase_totals(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand", "red-caitlyn"))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 2)
        controller.get_unit("red-brand").position = (4, 2)
        controller.get_unit("red-caitlyn").position = (6, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand", "red-caitlyn", "blue-garen"]

        intent = controller.preview_ai_intent()

        self.assertIsNotNone(intent)
        self.assertEqual(intent.phase_actor_count, 2)
        self.assertEqual(intent.phase_total_damage, intent.predicted_damage + intent.follow_up_predicted_damage)
        self.assertGreaterEqual(intent.phase_target_count, 1)
        self.assertIsNotNone(intent.phase_summary)
        self.assertIn("적 연속 턴", intent.phase_summary)

    def test_preview_ai_intent_reports_danger_and_focus_target(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand", "red-caitlyn"))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 2)
        controller.get_unit("red-brand").position = (4, 2)
        controller.get_unit("red-caitlyn").position = (6, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand", "red-caitlyn", "blue-garen"]

        intent = controller.preview_ai_intent()

        self.assertIsNotNone(intent)
        self.assertIn(intent.danger_label, {"보통", "높음", "치명"})
        self.assertEqual(intent.phase_focus_target_name, "가렌")
        self.assertGreater(intent.phase_focus_damage, 0)
        self.assertIsNotNone(intent.chain_summary)

    def test_preview_ai_intent_counts_lethal_targets_in_enemy_phase(self) -> None:
        controller = TacticsController(("blue-garen",), ("red-brand", "red-caitlyn"))
        controller.blocked_tiles.clear()
        controller.get_unit("blue-garen").position = (0, 2)
        controller.get_unit("blue-garen").hp = 12
        controller.get_unit("red-brand").position = (4, 2)
        controller.get_unit("red-caitlyn").position = (6, 2)
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand", "red-caitlyn", "blue-garen"]

        intent = controller.preview_ai_intent()

        self.assertIsNotNone(intent)
        self.assertEqual(intent.phase_lethal_target_count, 1)
        self.assertIn("연쇄 집중", intent.chain_summary or "")

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

    def test_ai_contests_objective_tile_when_no_attack_available(self) -> None:
        controller = TacticsController(
            ("blue-garen",),
            ("red-brand",),
            ((0, 0),),
            ((7, 4),),
            objective_tiles=((7, 2),),
        )
        controller.blocked_tiles.clear()
        controller.state.active_unit_id = "red-brand"
        controller.state.turn_queue = ["red-brand", "blue-garen"]

        destination = controller._choose_ai_move(controller.get_unit("red-brand"))
        intent = controller.preview_ai_intent()

        self.assertEqual(destination, (7, 2))
        self.assertIsNotNone(intent)
        self.assertEqual(intent.move_to, (7, 2))
        self.assertIn((7, 2), intent.phase_objective_tiles)
        self.assertEqual(intent.objective_pressure_label, "목표 타일 점유 시도")


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

    def test_intermediate_victory_records_history_and_enters_reward_phase(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = 1
        app.deploy_assignments = {(0, 1): "blue-garen"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}
        app.current_objective = BattleObjective(
            route_id="assault-line",
            name="선제 제압",
            description="목표: 2라운드 이내 적 1명 처치",
            kind="kill_before_round",
            target=1,
            reward_id="bonus-damage",
            reward_label="날 선 무기 +1",
        )

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.controller.get_unit("red-darius").hp = 1

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertEqual(app.screen_mode, "reward")
        self.assertIsNone(app.run_summary)
        self.assertEqual(len(app.run_history), 1)
        self.assertEqual(app.run_history[0].result_label, "승리")

    def test_final_victory_enters_run_summary_screen(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = RUN_STAGE_COUNT
        app.deploy_assignments = {(0, 1): "blue-garen", (0, 3): "blue-ahri", (1, 5): "blue-jinx"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}
        app.current_objective = app._build_battle_objective()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.controller.get_unit("red-darius").hp = 1

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertEqual(app.screen_mode, "summary")
        self.assertIsNotNone(app.run_summary)
        self.assertEqual(app.run_summary.result_label, "원정 성공")
        self.assertEqual(app.run_summary.stage_label, "결전 완주")
        self.assertEqual(len(app.run_history), 1)

    def test_defeat_enters_run_summary_screen(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = 2
        app.deploy_assignments = {(0, 1): "blue-garen"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}
        app.current_objective = BattleObjective(
            route_id="supply-line",
            name="보급 확보",
            description="목표: 중앙 보급 칸 진입 1회",
            kind="occupy_tile",
            target=1,
            reward_id="bonus-shield",
            reward_label="수호 문장 +1",
        )

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.controller.state.active_unit_id = "red-darius"
        app.controller.state.turn_queue = ["red-darius"]
        app.controller.get_unit("blue-garen").hp = 1

        result = app.controller.use_basic("blue-garen")
        app._apply_action_result(result)

        self.assertEqual(app.screen_mode, "summary")
        self.assertIsNotNone(app.run_summary)
        self.assertEqual(app.run_summary.result_label, "원정 실패")
        self.assertIn("엘리트전", app.run_summary.stage_label)
        self.assertEqual(len(app.run_history), 1)

    def test_summary_enter_starts_new_run_and_clears_history(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = RUN_STAGE_COUNT
        app.deploy_assignments = {(0, 1): "blue-garen", (0, 3): "blue-ahri", (1, 5): "blue-jinx"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}
        app.current_objective = app._build_battle_objective()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.controller.get_unit("red-darius").hp = 1

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)
        app._handle_keydown(pygame.K_RETURN)

        self.assertEqual(app.screen_mode, "deploy")
        self.assertEqual(app.run_stage, 1)
        self.assertEqual(len(app.run_history), 0)
        self.assertIsNone(app.run_summary)
        self.assertEqual(len(app.deploy_assignments), 3)

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
        self.assertIsNotNone(elite_units[0].elite_trait_id)

    def test_stage_three_marks_boss_and_lieutenant_elite(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-zed", "red-brand"]
        app.run_stage = 3
        app._seed_deployment()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        boss_units = [unit for unit in app.controller.units if unit.team == "red" and unit.is_boss]
        lieutenant_elites = [unit for unit in app.controller.units if unit.team == "red" and unit.is_elite and not unit.is_boss]
        self.assertEqual(len(boss_units), 1)
        self.assertTrue(boss_units[0].is_elite)
        self.assertGreater(boss_units[0].max_hp, TACTICAL_BLUEPRINTS_BY_ID[boss_units[0].id].max_hp + 20)
        self.assertEqual(len(lieutenant_elites), 1)
        self.assertIsNotNone(lieutenant_elites[0].elite_trait_id)

    def test_stage_three_builds_boss_specific_finale_objective(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-zed", "red-brand"]
        app.run_stage = 3

        objective = app._build_battle_objective()

        self.assertIsNotNone(objective)
        self.assertTrue(objective.is_finale)
        self.assertEqual(objective.boss_id, "red-darius")
        self.assertEqual(objective.name, "결전 봉쇄")
        self.assertEqual(objective.target, 2)
        self.assertEqual(objective.objective_tiles, ((3, 2), (4, 2)))

    def test_finale_objective_success_weakens_boss_phase(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-zed", "red-brand"]
        app.run_stage = 3
        app._seed_deployment()
        app.current_objective = app._build_battle_objective()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        boss = app.controller.get_unit("red-darius")
        blue = app.controller.get_unit("blue-garen")
        app.controller.blocked_tiles.clear()
        blue.position = (0, 1)
        boss.position = (1, 1)
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.current_objective.completed = True
        pre_speed = boss.speed
        boss.hp = 35

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertTrue(boss.boss_phase_triggered)
        self.assertEqual(boss.shield, 8)
        self.assertEqual(boss.speed, pre_speed + 1)
        self.assertEqual(app.finale_banner_title, "결전 봉쇄 성공")

    def test_finale_objective_failure_empowers_boss_phase(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-zed", "red-brand"]
        app.run_stage = 3
        app._seed_deployment()
        app.current_objective = app._build_battle_objective()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        boss = app.controller.get_unit("red-darius")
        blue = app.controller.get_unit("blue-garen")
        app.controller.blocked_tiles.clear()
        blue.position = (0, 1)
        boss.position = (1, 1)
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.current_objective.failed = True
        pre_speed = boss.speed
        boss.hp = 35

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertTrue(boss.boss_phase_triggered)
        self.assertEqual(boss.shield, 26)
        self.assertEqual(boss.speed, pre_speed + 3)
        self.assertEqual(app.finale_banner_title, "결전 각성 증폭")

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

    def test_prepare_route_phase_rolls_events_for_each_option(self) -> None:
        app = GameApp(headless=True)

        app._prepare_route_phase()

        self.assertEqual(len(app.route_option_ids), 3)
        self.assertEqual(set(app.route_option_ids), set(app.route_event_by_route_id))
        self.assertEqual(set(app.route_option_ids), set(app.route_node_by_route_id))
        self.assertEqual(set(app.route_option_ids), set(app.node_follow_up_by_route_id))
        self.assertEqual(len({node.id for node in app.route_node_by_route_id.values()}), 3)

    def test_node_follow_up_modifies_next_battle_stats(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.route_option_ids = ["supply-line"]
        app.route_event_by_route_id = {}
        app.route_node_by_route_id = {
            "supply-line": RunNode(
                id="rest-camp",
                name="휴식 거점",
                category="정비 노드",
                description="테스트용",
                effect_label="아군 체력 +12 · 보호막 +6 · 예약 페널티 해제",
                stage_modifiers={"blue_hp": 12, "blue_shield": 6},
                clears_pending_penalty=True,
            )
        }
        app.node_follow_up_by_route_id = {
            "supply-line": NodeFollowUp(
                id="rest-regroup",
                node_id="rest-camp",
                name="신속 재집결",
                description="테스트용",
                effect_label="이번 전투 아군 속도 +4 · 이동력 +1",
                stage_modifiers={"blue_speed": 4, "blue_move": 1},
            )
        }
        app.selected_route_id = "supply-line"

        app._advance_after_route()
        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        garen = app.controller.get_unit("blue-garen")
        self.assertIsNotNone(app.current_node_follow_up)
        self.assertEqual(app.current_node_follow_up.name, "신속 재집결")
        self.assertEqual(garen.speed, TACTICAL_BLUEPRINTS_BY_ID["blue-garen"].speed + 4)
        self.assertEqual(garen.move_range, TACTICAL_BLUEPRINTS_BY_ID["blue-garen"].move_range + 1)
        node_summary = app._current_route_node_summary() or ""
        self.assertIn("휴식 거점", node_summary)
        self.assertIn("아군 체력 +12", node_summary)
        self.assertIn("신속 재집결", node_summary)
        self.assertIn("이동력 +1", node_summary)

    def test_deploy_escape_returns_to_clean_select_state(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.current_route_id = "supply-line"
        app.current_route_node = RunNode(
            id="rest-camp",
            name="휴식 거점",
            category="정비 노드",
            description="테스트용",
            effect_label="아군 체력 +12 · 보호막 +6 · 예약 페널티 해제",
            stage_modifiers={"blue_hp": 12, "blue_shield": 6},
            clears_pending_penalty=True,
        )
        app.current_node_follow_up = NodeFollowUp(
            id="rest-regroup",
            node_id="rest-camp",
            name="신속 재집결",
            description="테스트용",
            effect_label="이번 전투 아군 속도 +4 · 이동력 +1",
            stage_modifiers={"blue_speed": 4, "blue_move": 1},
        )
        app._seed_deployment()
        app.screen_mode = "deploy"

        app._handle_keydown(pygame.K_ESCAPE)

        self.assertEqual(app.screen_mode, "select")
        self.assertEqual(app.run_stage, 1)
        self.assertIsNone(app.current_route_id)
        self.assertIsNone(app.current_route_node)
        self.assertIsNone(app.current_node_follow_up)

    def test_deploy_header_action_returns_to_clean_select_state(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.current_route_id = "supply-line"
        app.current_route_node = RunNode(
            id="rest-camp",
            name="휴식 거점",
            category="정비 노드",
            description="테스트용",
            effect_label="아군 체력 +12 · 보호막 +6 · 예약 페널티 해제",
            stage_modifiers={"blue_hp": 12, "blue_shield": 6},
            clears_pending_penalty=True,
        )
        app.current_node_follow_up = NodeFollowUp(
            id="rest-regroup",
            node_id="rest-camp",
            name="신속 재집결",
            description="테스트용",
            effect_label="이번 전투 아군 속도 +4 · 이동력 +1",
            stage_modifiers={"blue_speed": 4, "blue_move": 1},
        )
        app._seed_deployment()
        app.screen_mode = "deploy"
        app._draw()

        app._handle_click(app.button_rects["header-action"].center)

        self.assertEqual(app.screen_mode, "select")
        self.assertEqual(app.run_stage, 1)
        self.assertIsNone(app.current_route_id)
        self.assertIsNone(app.current_route_node)
        self.assertIsNone(app.current_node_follow_up)

    def test_route_event_modifies_next_battle_stats(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.route_option_ids = ["supply-line"]
        app.route_event_by_route_id = {
            "supply-line": RouteEvent(
                id="test-supply-event",
                route_id="supply-line",
                name="테스트 보급",
                description="테스트용",
                effect_label="아군 시작 보호막 +6",
                stage_modifiers={"blue_shield": 6},
                failure_penalty_name="테스트 페널티",
                failure_penalty_label="적 시작 보호막 +10",
                penalty_modifiers={"enemy_shield": 10},
            )
        }
        app.selected_route_id = "supply-line"

        app._advance_after_route()
        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        self.assertEqual(app.screen_mode, "deploy")
        self.assertIsNotNone(app.current_route_event)
        self.assertEqual(app.controller.get_unit("blue-garen").shield, 14)

    def test_rest_node_clears_pending_penalty_and_grants_recovery_stats(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.route_option_ids = ["supply-line"]
        app.route_event_by_route_id = {}
        app.route_node_by_route_id = {
            "supply-line": RunNode(
                id="rest-camp",
                name="휴식 거점",
                category="정비 노드",
                description="테스트용",
                effect_label="아군 체력 +12 · 보호막 +6 · 예약 페널티 해제",
                stage_modifiers={"blue_hp": 12, "blue_shield": 6},
                clears_pending_penalty=True,
            )
        }
        app.pending_stage_penalty = StageModifier(
            name="역습 준비",
            description="다음 전투 적 전원 피해 +2",
            modifiers={"enemy_damage": 2},
        )
        app.selected_route_id = "supply-line"

        app._advance_after_route()
        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        garen = app.controller.get_unit("blue-garen")
        self.assertIsNone(app.active_stage_penalty)
        self.assertEqual(garen.max_hp, TACTICAL_BLUEPRINTS_BY_ID["blue-garen"].max_hp + 12)
        self.assertEqual(garen.shield, 14)

    def test_event_node_amplifies_route_event_and_failure_penalty(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.route_option_ids = ["assault-line"]
        route_event = RouteEvent(
            id="test-assault-event",
            route_id="assault-line",
            name="테스트 돌격",
            description="테스트용",
            effect_label="아군 피해 +2",
            stage_modifiers={"blue_damage": 2},
            failure_penalty_name="역습 준비",
            failure_penalty_label="적 전원 피해 +2",
            penalty_modifiers={"enemy_damage": 2},
        )
        app.route_event_by_route_id = {"assault-line": route_event}
        app.route_node_by_route_id = {
            "assault-line": RunNode(
                id="event-surge",
                name="변수 균열",
                category="증폭 노드",
                description="테스트용",
                effect_label="경로 이벤트 수치 +100% · 실패 페널티도 강화",
                stage_modifiers={},
                event_modifier_scale=2,
                penalty_modifier_scale=2,
            )
        }
        app.selected_route_id = "assault-line"

        app._advance_after_route()
        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        garen = app.controller.get_unit("blue-garen")
        base_damage = next(
            effect.amount
            for effect in TACTICAL_BLUEPRINTS_BY_ID["blue-garen"].basic_ability.effects
            if effect.kind == "damage"
        )
        boosted_damage = next(effect.amount for effect in garen.basic_ability.effects if effect.kind == "damage")
        self.assertEqual(boosted_damage, base_damage + 6)

        app.current_objective = BattleObjective(
            route_id="assault-line",
            name="선제 제압",
            description="목표: 2라운드 이내 적 1명 처치",
            kind="kill_before_round",
            target=1,
            reward_id="bonus-damage",
            reward_label="날 선 무기 +1",
            failed=True,
        )
        app.run_stage = 1

        summary = app._queue_objective_failure_penalty()

        self.assertIsNotNone(summary)
        self.assertEqual(app.pending_stage_penalty.modifiers["enemy_damage"], 4)
        self.assertIn("+4", app.pending_stage_penalty.description)

    def test_elite_node_adds_extra_elite_and_bonus_reward(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-zed", "red-brand"]
        app.run_stage = 2
        app.current_route_id = "assault-line"
        app.current_route_node = RunNode(
            id="elite-contract",
            name="정예 수배",
            category="고위험 노드",
            description="테스트용",
            effect_label="적 정예 +1 · 승리 시 기동 훈련 +1",
            stage_modifiers={},
            extra_elites=1,
            victory_reward_id="bonus-move",
            victory_reward_label="기동 훈련 +1",
        )
        app._seed_deployment()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        elite_units = [unit for unit in app.controller.units if unit.team == "red" and unit.is_elite]
        self.assertEqual(len(elite_units), 2)
        node_summary = app._apply_route_node_victory_bonus()
        self.assertEqual(app.run_bonuses["bonus-move"], 1)
        self.assertIn("기동 훈련 +1", node_summary or "")

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

    def test_failed_objective_queues_penalty_for_next_stage(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen"]
        app.selected_red_ids = ["red-darius"]
        app.run_stage = 1
        app.current_route_id = "assault-line"
        app.current_route_event = RouteEvent(
            id="test-assault-event",
            route_id="assault-line",
            name="테스트 돌격",
            description="테스트용",
            effect_label="아군 피해 +2",
            stage_modifiers={"blue_damage": 2},
            failure_penalty_name="역습 준비",
            failure_penalty_label="다음 전투 적 전원 피해 +2",
            penalty_modifiers={"enemy_damage": 2},
        )
        app.deploy_assignments = {(0, 1): "blue-garen"}
        app.red_deploy_assignments = {(1, 1): "red-darius"}

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)
        app.current_objective = app._build_battle_objective()
        app.controller.state.active_unit_id = "blue-garen"
        app.controller.state.turn_queue = ["blue-garen"]
        app.controller.state.round = 3
        app._refresh_objective_failure()
        app.controller.get_unit("red-darius").hp = 1

        result = app.controller.use_basic("red-darius")
        app._apply_action_result(result)

        self.assertEqual(app.screen_mode, "reward")
        self.assertIsNotNone(app.pending_stage_penalty)
        self.assertEqual(app.pending_stage_penalty.description, "다음 전투 적 전원 피해 +2")

        app.pending_red_ids = ["red-darius"]
        app._select_reward(app.reward_option_ids[0])
        app._advance_after_reward()
        app.route_option_ids = ["supply-line"]
        app.route_event_by_route_id = {
            "supply-line": RouteEvent(
                id="test-next-event",
                route_id="supply-line",
                name="다음 이벤트",
                description="테스트용",
                effect_label="아군 보호막 +6",
                stage_modifiers={"blue_shield": 6},
                failure_penalty_name="다음 페널티",
                failure_penalty_label="적 보호막 +10",
                penalty_modifiers={"enemy_shield": 10},
            )
        }
        app.route_node_by_route_id = {}
        app.node_follow_up_by_route_id = {}
        app.selected_route_id = "supply-line"
        app._advance_after_route()

        controller = app._build_controller_from_current_setup()
        app._attach_controller(controller)

        darius = app.controller.get_unit("red-darius")
        base_damage = next(effect.amount for effect in TACTICAL_BLUEPRINTS_BY_ID["red-darius"].basic_ability.effects if effect.kind == "damage")
        boosted_damage = next(effect.amount for effect in darius.basic_ability.effects if effect.kind == "damage")
        self.assertEqual(boosted_damage, base_damage + 7)

    def test_start_battle_syncs_objective_tiles_to_controller(self) -> None:
        app = GameApp(headless=True)
        app.selected_blue_ids = ["blue-garen", "blue-ahri", "blue-jinx"]
        app.selected_red_ids = ["red-darius", "red-annie", "red-caitlyn"]
        app.run_stage = 2
        app.current_route_id = "supply-line"
        app._seed_deployment()

        app._start_battle()

        self.assertEqual(app.screen_mode, "battle")
        self.assertIsNotNone(app.controller)
        self.assertIn((3, 2), app.controller.objective_tiles)


if __name__ == "__main__":
    unittest.main()
