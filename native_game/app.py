from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame

from .combat import BattleAction, BattleController, CombatUnit

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 960
ARENA_RECT = pygame.Rect(298, 116, 1004, 596)
LEFT_PANEL = pygame.Rect(36, 116, 232, 596)
RIGHT_PANEL = pygame.Rect(1332, 116, 232, 596)
ACTION_PANEL = pygame.Rect(298, 738, 1004, 188)
LOG_PANEL = pygame.Rect(1332, 738, 232, 188)
HEADER_RECT = pygame.Rect(36, 28, WINDOW_WIDTH - 72, 70)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "NotoSansKR-Variable.ttf"


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    lifetime: float = 0.85
    drift: float = 54.0


@dataclass
class ProjectileEffect:
    start: tuple[float, float]
    end: tuple[float, float]
    color: tuple[int, int, int]
    progress: float = 0.0
    speed: float = 2.8
    width: int = 10
    style: str = "bolt"


@dataclass
class RingEffect:
    center: tuple[float, float]
    color: tuple[int, int, int]
    radius: float = 18.0
    alpha: float = 180.0
    growth: float = 260.0
    width: int = 4


@dataclass
class UnitFxState:
    hit_timer: float = 0.0
    shield_timer: float = 0.0
    stun_timer: float = 0.0
    cast_timer: float = 0.0
    flare_timer: float = 0.0


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    sub_label: str
    ability_id: str
    disabled: bool = False
    selected: bool = False


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[index : index + 2], 16) for index in (0, 2, 4))


def mix(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = clamp(amount, 0.0, 1.0)
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def tinted(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return mix(color, (255, 255, 255), amount)


def shaded(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    return mix(color, (0, 0, 0), amount)


def draw_vertical_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    for offset in range(rect.height):
        t = offset / max(1, rect.height - 1)
        color = mix(top, bottom, t)
        pygame.draw.line(surface, color, (rect.x, rect.y + offset), (rect.right, rect.y + offset))


def load_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    if FONT_PATH.exists():
        font = pygame.font.Font(FONT_PATH, size)
        font.set_bold(bold)
        return font

    font_names = ["Noto Sans CJK KR", "NanumGothic", "malgungothic", "applegothic", "arial"]
    matched_font = pygame.font.match_font(font_names, bold=bold)
    if matched_font:
        font = pygame.font.Font(matched_font, size)
        font.set_bold(bold)
        return font

    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class GameApp:
    def __init__(self, headless: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("리프트 택틱스")
        flags = pygame.HIDDEN if headless else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True
        self.headless = headless

        self.font_tiny = load_font(13)
        self.font_small = load_font(16)
        self.font_ui = load_font(20)
        self.font_heading = load_font(25, bold=True)
        self.font_large = load_font(28, bold=True)
        self.font_title = load_font(44, bold=True)

        self.controller = BattleController()
        self.selected_ability_id: str | None = None
        self.preview_action: BattleAction | None = None
        self.pending_resolution: tuple[str, str | None] | None = None
        self.preview_timer = 0.0
        self.ai_think_timer = 0.45
        self.last_action_timer = 0.0

        self.floaters: list[FloatingText] = []
        self.projectiles: list[ProjectileEffect] = []
        self.rings: list[RingEffect] = []
        self.fx_state: dict[str, UnitFxState] = {
            unit.id: UnitFxState() for unit in self.controller.units
        }
        self.shake_time = 0.0
        self.shake_strength = 0.0
        self.time_accumulator = 0.0
        self.camera_offset = pygame.Vector2(0, 0)
        self.unit_hitboxes: dict[str, pygame.Rect] = {}
        self.reset_button = pygame.Rect(WINDOW_WIDTH - 214, 42, 162, 42)

        self.background_cache = self._build_background_cache()
        self.arena_cache = self._build_arena_cache()

    def run(self, max_frames: int | None = None, screenshot_path: str | None = None) -> None:
        frames = 0
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.time_accumulator += dt
            self._handle_events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                break

        if screenshot_path:
            pygame.image.save(self.screen, screenshot_path)
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self._reset()
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self._select_ability_index(0)
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self._select_ability_index(1)
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self._select_ability_index(2)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _update(self, dt: float) -> None:
        if self.preview_action is not None:
            self.preview_timer -= dt
            if self.preview_timer <= 0 and self.pending_resolution is not None:
                ability_id, target_id = self.pending_resolution
                self.preview_action = None
                self.pending_resolution = None
                resolved_action = self.controller.resolve_active_turn(ability_id, target_id)
                if resolved_action is not None:
                    self._apply_resolved_action_fx(resolved_action)
                    next_active = self.controller.get_active_unit()
                    self.ai_think_timer = 0.45 if next_active and next_active.team == "red" else 0.0
        else:
            active_unit = self.controller.get_active_unit()
            if (
                active_unit is not None
                and active_unit.team == "red"
                and self.controller.state.winner is None
            ):
                self.ai_think_timer -= dt
                if self.ai_think_timer <= 0:
                    planned = self.controller.plan_enemy_turn()
                    if planned is not None:
                        ability_id, target_id = planned
                        self._begin_preview(ability_id, target_id)

        for floater in list(self.floaters):
            floater.lifetime -= dt
            floater.y -= floater.drift * dt
            if floater.lifetime <= 0:
                self.floaters.remove(floater)

        for projectile in list(self.projectiles):
            projectile.progress += projectile.speed * dt
            if projectile.progress >= 1:
                self.projectiles.remove(projectile)

        for ring in list(self.rings):
            ring.radius += ring.growth * dt
            ring.alpha -= 235 * dt
            if ring.alpha <= 0:
                self.rings.remove(ring)

        for state in self.fx_state.values():
            state.hit_timer = max(0.0, state.hit_timer - dt)
            state.shield_timer = max(0.0, state.shield_timer - dt)
            state.stun_timer = max(0.0, state.stun_timer - dt)
            state.cast_timer = max(0.0, state.cast_timer - dt)
            state.flare_timer = max(0.0, state.flare_timer - dt)

        self.last_action_timer = max(0.0, self.last_action_timer - dt)
        self.shake_time = max(0.0, self.shake_time - dt)
        if self.shake_time > 0:
            self.camera_offset.x = random.uniform(-self.shake_strength, self.shake_strength)
            self.camera_offset.y = random.uniform(-self.shake_strength, self.shake_strength)
        else:
            self.camera_offset.update(0, 0)

    def _select_ability_index(self, index: int) -> None:
        active = self.controller.get_active_unit()
        if active is None or active.team != "blue" or self.preview_action is not None:
            return
        if index >= len(active.abilities):
            return
        self._handle_ability_click(active.abilities[index].id)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.reset_button.collidepoint(position):
            self._reset()
            return

        if self.preview_action is not None:
            return

        for button in self._ability_buttons():
            if button.rect.collidepoint(position) and not button.disabled:
                self._handle_ability_click(button.ability_id)
                return

        if self.selected_ability_id:
            for unit_id, rect in self.unit_hitboxes.items():
                if rect.collidepoint(position):
                    self._handle_target_click(unit_id)
                    return

    def _handle_ability_click(self, ability_id: str) -> None:
        active = self.controller.get_active_unit()
        if active is None or active.team != "blue":
            return

        ability = next((candidate for candidate in active.abilities if candidate.id == ability_id), None)
        if ability is None or active.cooldowns[ability.id] > 0:
            return

        if ability.target_type == "enemy":
            self.selected_ability_id = None if self.selected_ability_id == ability.id else ability.id
            return

        self.selected_ability_id = None
        self._begin_preview(ability.id, None)

    def _handle_target_click(self, target_id: str) -> None:
        if not self.selected_ability_id:
            return

        valid_targets = set(self.controller.get_valid_target_ids(self.selected_ability_id))
        if target_id not in valid_targets:
            return

        ability_id = self.selected_ability_id
        self.selected_ability_id = None
        self._begin_preview(ability_id, target_id)

    def _begin_preview(self, ability_id: str, target_id: str | None) -> None:
        preview = self.controller.create_preview_action(ability_id, target_id)
        if preview is None:
            return

        self.preview_action = preview
        self.pending_resolution = (ability_id, target_id)
        self.preview_timer = 0.55 if preview.target_type == "enemy" else 0.68

        actor_state = self.fx_state.get(preview.actor_id)
        if actor_state:
            actor_state.cast_timer = self.preview_timer
            actor_state.flare_timer = 0.42

        self._spawn_preview_fx(preview)

    def _spawn_preview_fx(self, action: BattleAction) -> None:
        actor = self.controller.get_unit(action.actor_id)
        if actor is None:
            return

        actor_pos = self._unit_anchor(actor.id)
        actor_color = hex_to_rgb(actor.accent)
        white = (244, 240, 226)

        if action.ability_id in {"orb-of-deception", "charm"} and action.target_ids:
            target_pos = self._unit_anchor(action.target_ids[0])
            self.projectiles.append(
                ProjectileEffect(
                    start=(actor_pos.x, actor_pos.y - 74),
                    end=(target_pos.x, target_pos.y - 92),
                    color=actor_color,
                    width=12,
                    speed=2.2,
                    style="orb" if action.ability_id == "orb-of-deception" else "heart",
                )
            )
            return

        if action.ability_id in {"zap", "piltover-peacemaker"} and action.target_ids:
            target_pos = self._unit_anchor(action.target_ids[0])
            self.projectiles.append(
                ProjectileEffect(
                    start=(actor_pos.x, actor_pos.y - 84),
                    end=(target_pos.x, target_pos.y - 96),
                    color=tinted(actor_color, 0.2),
                    width=9,
                    speed=4.6,
                    style="beam",
                )
            )
            return

        if action.ability_id == "super-mega-death-rocket" and action.target_ids:
            target_pos = self._unit_anchor(action.target_ids[1] if len(action.target_ids) > 1 else action.target_ids[0])
            self.projectiles.append(
                ProjectileEffect(
                    start=(actor_pos.x, actor_pos.y - 74),
                    end=(target_pos.x, target_pos.y - 88),
                    color=(255, 125, 115),
                    width=16,
                    speed=2.8,
                    style="rocket",
                )
            )
            return

        if action.ability_id in {"summon-tibbers", "judgment"}:
            self.rings.append(RingEffect(center=(actor_pos.x, actor_pos.y - 20), color=actor_color, radius=34, growth=220))
            return

        if action.ability_id in {"courage", "defy", "molten-shield"}:
            self.rings.append(RingEffect(center=(actor_pos.x, actor_pos.y - 42), color=(130, 226, 172), radius=26, growth=180))
            self.floaters.append(FloatingText(actor_pos.x, actor_pos.y - 118, "방어 태세", (180, 246, 197), 0.72, 28))
            return

        if action.ability_id == "spirit-rush" and action.target_ids:
            self.rings.append(RingEffect(center=(actor_pos.x, actor_pos.y - 44), color=(111, 225, 255), radius=22, growth=260))
            self.floaters.append(FloatingText(actor_pos.x, actor_pos.y - 128, "돌진", white, 0.58, 22))
            return

        if action.target_type == "enemy" and action.target_ids:
            target_pos = self._unit_anchor(action.target_ids[0])
            self.projectiles.append(
                ProjectileEffect(
                    start=(actor_pos.x, actor_pos.y - 76),
                    end=(target_pos.x, target_pos.y - 86),
                    color=actor_color,
                    style="bolt",
                )
            )
        elif action.target_type == "all-enemies":
            self.rings.append(RingEffect(center=(actor_pos.x, actor_pos.y - 28), color=actor_color))
        elif action.target_type == "self":
            self.rings.append(RingEffect(center=(actor_pos.x, actor_pos.y - 28), color=(137, 215, 157)))

    def _apply_resolved_action_fx(self, action: BattleAction) -> None:
        self.last_action_timer = 1.0
        heavy_hit = action.ability_id in {"super-mega-death-rocket", "noxian-guillotine", "summon-tibbers"}

        for impact in action.impacts:
            anchor = self._unit_anchor(impact.target_id)
            state = self.fx_state.get(impact.target_id)
            if state is None:
                continue

            if impact.damage_dealt > 0:
                state.hit_timer = 0.42
                self.shake_time = 0.22 if heavy_hit else 0.14
                self.shake_strength = 11 if heavy_hit else 6
                damage_text = f"-{impact.damage_dealt}"
                self.floaters.append(FloatingText(anchor.x, anchor.y - 138, damage_text, (255, 160, 140)))
                hit_color = (255, 116, 92) if heavy_hit else (255, 204, 124)
                self.rings.append(RingEffect(center=(anchor.x, anchor.y - 34), color=hit_color, radius=24, growth=220))
            if impact.blocked_damage > 0:
                self.floaters.append(
                    FloatingText(anchor.x, anchor.y - 166, f"막음 {impact.blocked_damage}", (154, 221, 242), 0.8, 26)
                )
            if impact.shield_gained > 0:
                state.shield_timer = 0.8
                self.rings.append(RingEffect(center=(anchor.x, anchor.y - 28), color=(137, 215, 157), radius=30, growth=165))
                self.floaters.append(FloatingText(anchor.x, anchor.y - 136, f"+보호막 {impact.shield_gained}", (170, 242, 190)))
            if impact.stun_turns_applied > 0:
                state.stun_timer = 0.92
                self.floaters.append(FloatingText(anchor.x, anchor.y - 164, "기절", (255, 229, 145), 0.82, 26))
            if impact.defeated:
                self.floaters.append(FloatingText(anchor.x, anchor.y - 188, "처치", (255, 216, 168), 0.95, 22))

    def _reset(self) -> None:
        self.controller.reset()
        self.selected_ability_id = None
        self.preview_action = None
        self.pending_resolution = None
        self.preview_timer = 0.0
        self.ai_think_timer = 0.45
        self.last_action_timer = 0.0
        self.floaters.clear()
        self.projectiles.clear()
        self.rings.clear()
        self.fx_state = {unit.id: UnitFxState() for unit in self.controller.units}

    def _unit_anchor(self, unit_id: str) -> pygame.Vector2:
        unit = next(candidate for candidate in self.controller.units if candidate.id == unit_id)
        blue_slots = [
            pygame.Vector2(486, 594),
            pygame.Vector2(404, 430),
            pygame.Vector2(486, 268),
        ]
        red_slots = [
            pygame.Vector2(1106, 268),
            pygame.Vector2(1188, 430),
            pygame.Vector2(1106, 594),
        ]
        team_units = [candidate for candidate in self.controller.units if candidate.team == unit.team]
        team_index = team_units.index(unit)
        return blue_slots[team_index] if unit.team == "blue" else red_slots[team_index]

    def _render_anchor(self, unit: CombatUnit, offset: pygame.Vector2) -> pygame.Vector2:
        anchor = self._unit_anchor(unit.id)
        state = self.fx_state[unit.id]
        idle = math.sin(self.time_accumulator * 2.4 + (0 if unit.team == "blue" else 1.3)) * 4.8
        cast_shift_x = 0.0
        cast_shift_y = 0.0

        if self.preview_action and self.preview_action.actor_id == unit.id:
            duration = 0.55 if self.preview_action.target_type == "enemy" else 0.68
            progress = 1 - (self.preview_timer / duration)
            progress = clamp(progress, 0.0, 1.0)
            hop = math.sin(progress * math.pi)
            if self.preview_action.target_type == "enemy":
                dash = hop * 76
                cast_shift_x = dash if unit.team == "blue" else -dash
                cast_shift_y = -hop * 22
            else:
                cast_shift_y = -hop * 20

        hit_offset = 0.0
        if state.hit_timer > 0:
            hit_offset = math.sin(state.hit_timer * 34) * (12 if unit.team == "blue" else -12)

        return pygame.Vector2(
            anchor.x + cast_shift_x + hit_offset + offset.x,
            anchor.y + idle + cast_shift_y + offset.y,
        )

    def _ability_buttons(self) -> list[Button]:
        active = self.controller.get_active_unit()
        buttons: list[Button] = []
        if active is None:
            return buttons

        widths = [234, 234, 234]
        x_positions = [ACTION_PANEL.x + 250, ACTION_PANEL.x + 500, ACTION_PANEL.x + 750]
        for index, ability in enumerate(active.abilities):
            rect = pygame.Rect(x_positions[index], ACTION_PANEL.y + 54, widths[index], 100)
            cooldown = active.cooldowns[ability.id]
            buttons.append(
                Button(
                    rect=rect,
                    label=ability.name,
                    sub_label=f"재사용 {cooldown}턴" if cooldown > 0 else ability.description,
                    ability_id=ability.id,
                    disabled=(
                        self.preview_action is not None
                        or self.controller.state.winner is not None
                        or active.team != "blue"
                        or cooldown > 0
                    ),
                    selected=self.selected_ability_id == ability.id,
                )
            )
        return buttons

    def _build_background_cache(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        draw_vertical_gradient(surface, surface.get_rect(), (8, 14, 24), (18, 30, 41))

        for index in range(72):
            x = (index * 173) % WINDOW_WIDTH
            y = (index * 97) % 320 + 30
            radius = 1 + (index % 3)
            alpha = 80 + (index % 4) * 35
            star = pygame.Surface((radius * 8, radius * 8), pygame.SRCALPHA)
            pygame.draw.circle(star, (255, 247, 218, alpha), (radius * 4, radius * 4), radius)
            surface.blit(star, (x, y))

        self._draw_glow(surface, (194, 142, 72), (1510, 116), 210, 120)
        self._draw_glow(surface, (56, 111, 168), (128, 820), 260, 110)
        self._draw_glow(surface, (240, 194, 108), (800, 170), 200, 36)

        left_banner = [(0, 550), (216, 468), (294, 882), (0, WINDOW_HEIGHT)]
        right_banner = [(WINDOW_WIDTH, 0), (1338, 0), (1530, 368), (WINDOW_WIDTH, 438)]
        pygame.draw.polygon(surface, (18, 58, 96), left_banner)
        pygame.draw.polygon(surface, (98, 42, 35), right_banner)

        ridge_one = [(0, 650), (180, 588), (350, 632), (582, 566), (834, 618), (1008, 554), (1260, 620), (WINDOW_WIDTH, 578), (WINDOW_WIDTH, WINDOW_HEIGHT), (0, WINDOW_HEIGHT)]
        ridge_two = [(0, 734), (202, 680), (424, 742), (706, 676), (908, 746), (1160, 696), (WINDOW_WIDTH, 742), (WINDOW_WIDTH, WINDOW_HEIGHT), (0, WINDOW_HEIGHT)]
        ridge_three = [(0, 812), (280, 770), (614, 816), (962, 768), (1268, 824), (WINDOW_WIDTH, 792), (WINDOW_WIDTH, WINDOW_HEIGHT), (0, WINDOW_HEIGHT)]
        pygame.draw.polygon(surface, (17, 29, 43), ridge_one)
        pygame.draw.polygon(surface, (11, 20, 31), ridge_two)
        pygame.draw.polygon(surface, (8, 14, 22), ridge_three)

        for x in (314, 1278):
            crystal = pygame.Surface((120, 220), pygame.SRCALPHA)
            pygame.draw.polygon(crystal, (211, 179, 108, 50), [(60, 0), (118, 86), (86, 218), (34, 218), (2, 86)])
            pygame.draw.polygon(crystal, (255, 240, 192, 180), [(60, 22), (98, 92), (78, 192), (42, 192), (22, 92)], 2)
            surface.blit(crystal, (x - 60, 98))

        vignette = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0, 0, 0, 0), vignette.get_rect())
        pygame.draw.rect(vignette, (0, 0, 0, 74), vignette.get_rect(), width=48, border_radius=30)
        surface.blit(vignette, (0, 0))
        return surface

    def _build_arena_cache(self) -> pygame.Surface:
        surface = pygame.Surface(ARENA_RECT.size, pygame.SRCALPHA)
        frame_rect = surface.get_rect()
        pygame.draw.rect(surface, (7, 13, 22), frame_rect, border_radius=36)

        stage_shadow = pygame.Surface(frame_rect.size, pygame.SRCALPHA)
        pygame.draw.ellipse(stage_shadow, (0, 0, 0, 86), pygame.Rect(66, 404, 870, 140))
        surface.blit(stage_shadow, (0, 0))

        platform = [(138, 474), (318, 310), (484, 250), (664, 210), (864, 244), (910, 344), (838, 500), (622, 562), (376, 544), (206, 520)]
        inner = [(182, 462), (334, 332), (498, 282), (664, 246), (834, 274), (872, 352), (806, 476), (614, 530), (398, 514), (248, 496)]
        pygame.draw.polygon(surface, (36, 49, 64), platform)
        pygame.draw.polygon(surface, (68, 82, 98), inner)
        pygame.draw.polygon(surface, (226, 204, 149), inner, 2)

        left_lane = [(118, 476), (286, 346), (344, 372), (176, 512)]
        right_lane = [(674, 242), (846, 272), (890, 362), (710, 312)]
        pygame.draw.polygon(surface, (19, 54, 87), left_lane)
        pygame.draw.polygon(surface, (91, 38, 32), right_lane)

        for radius, alpha in ((74, 80), (116, 74), (156, 62), (206, 40)):
            pygame.draw.circle(surface, (214, 186, 114, alpha), (502, 316), radius, 2)
        pygame.draw.circle(surface, (226, 196, 122, 26), (502, 316), 54)

        for index in range(6):
            angle = index * math.tau / 6
            start = (502 + math.cos(angle) * 26, 316 + math.sin(angle) * 26)
            end = (502 + math.cos(angle) * 206, 316 + math.sin(angle) * 206)
            pygame.draw.line(surface, (214, 186, 114, 44), start, end, 2)

        for index in range(8):
            offset = 156 + index * 78
            pygame.draw.line(surface, (255, 255, 255, 10), (offset, 224), (offset - 110, 520), 1)
        for index in range(5):
            offset = 214 + index * 126
            pygame.draw.line(surface, (255, 255, 255, 12), (188, offset), (840, offset - 88), 1)

        self._draw_glow(surface, (74, 175, 224), (146, 450), 120, 70)
        self._draw_glow(surface, (224, 95, 76), (866, 202), 140, 74)
        self._draw_glow(surface, (228, 194, 116), (500, 316), 150, 46)

        pygame.draw.rect(surface, (244, 236, 220, 24), frame_rect.inflate(-16, -16), width=2, border_radius=32)
        pygame.draw.rect(surface, (233, 215, 174), frame_rect, width=1, border_radius=36)
        return surface

    def _draw(self) -> None:
        self.screen.blit(self.background_cache, (0, 0))
        self._draw_header()
        self._draw_side_panel(LEFT_PANEL, "플레이어 팀", "blue")
        self._draw_side_panel(RIGHT_PANEL, "적 팀", "red")
        self._draw_arena()
        self._draw_action_panel()
        self._draw_log_panel()
        self._draw_winner_overlay()

    def _draw_panel(self, rect: pygame.Rect, accent: tuple[int, int, int], *, glow: bool = False) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (6, 13, 22), (11, 22, 34))
        pygame.draw.rect(panel, (*accent, 18), panel.get_rect(), border_radius=28)
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=28)
        pygame.draw.rect(panel, (*accent, 52), panel.get_rect().inflate(-18, -18), width=1, border_radius=22)
        if glow:
            glow_surface = pygame.Surface((rect.width + 60, rect.height + 60), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*accent, 16), glow_surface.get_rect(), border_radius=40)
            self.screen.blit(glow_surface, (rect.x - 30, rect.y - 30))
        self.screen.blit(panel, rect.topleft)

    def _draw_header(self) -> None:
        self._draw_panel(HEADER_RECT, (214, 182, 112), glow=True)
        title = "리그 오브 레전드: 리프트 택틱스"
        active = self.controller.get_active_unit()
        status = (
            "전투 종료"
            if self.controller.state.winner
            else f"{self.preview_action.ability_name} 시전 중"
            if self.preview_action
            else f"{active.name} 행동 대기"
            if active
            else "대기 중"
        )
        self._draw_text(title, self.font_large, (244, 239, 225), (52, 44))
        self._draw_text(f"라운드 {self.controller.state.round}", self.font_ui, (220, 188, 118), (52, 73))
        self._draw_text(status, self.font_ui, (192, 229, 235), (WINDOW_WIDTH // 2, 56), center=True)

        button_color = (214, 182, 112)
        pygame.draw.rect(self.screen, button_color, self.reset_button, border_radius=15)
        pygame.draw.rect(self.screen, (255, 244, 217), self.reset_button, 1, border_radius=15)
        self._draw_text("R 재시작", self.font_ui, (12, 20, 31), self.reset_button.center, center=True)

    def _draw_side_panel(self, rect: pygame.Rect, label: str, team: str) -> None:
        accent = (64, 158, 214) if team == "blue" else (212, 105, 86)
        self._draw_panel(rect, accent)
        self._draw_text(label, self.font_heading, (228, 209, 164), (rect.x + 22, rect.y + 18))
        self._draw_text("스쿼드 상태", self.font_small, (128, 160, 184), (rect.x + 24, rect.y + 48))

        team_units = [unit for unit in self.controller.units if unit.team == team]
        for index, unit in enumerate(team_units):
            item_rect = pygame.Rect(rect.x + 16, rect.y + 76 + index * 166, rect.width - 32, 148)
            item_accent = hex_to_rgb(unit.accent)
            item_surface = pygame.Surface(item_rect.size, pygame.SRCALPHA)
            draw_vertical_gradient(item_surface, item_surface.get_rect(), (12, 22, 35), (17, 30, 44))
            pygame.draw.rect(item_surface, (*item_accent, 18), item_surface.get_rect(), border_radius=22)
            pygame.draw.rect(item_surface, (236, 218, 176), item_surface.get_rect(), 1, border_radius=22)
            pygame.draw.rect(item_surface, item_accent, item_surface.get_rect().inflate(-20, -20), 1, border_radius=18)
            self.screen.blit(item_surface, item_rect.topleft)

            avatar_rect = pygame.Rect(item_rect.x + 12, item_rect.y + 16, 72, 90)
            self._draw_portrait(unit, avatar_rect)
            self._draw_text(unit.name, self.font_ui, (244, 239, 225), (item_rect.x + 96, item_rect.y + 20))
            self._draw_text(unit.title, self.font_small, (160, 184, 198), (item_rect.x + 96, item_rect.y + 48))
            hp_bar = pygame.Rect(item_rect.x + 14, item_rect.y + 112, item_rect.width - 28, 12)
            pygame.draw.rect(self.screen, (33, 48, 61), hp_bar, border_radius=999)
            ratio = max(0.0, unit.hp / unit.max_hp)
            fill_rect = pygame.Rect(hp_bar.x, hp_bar.y, int(hp_bar.width * ratio), hp_bar.height)
            pygame.draw.rect(self.screen, (108, 216, 137), fill_rect, border_radius=999)
            state_text = (
                "전투 불능"
                if unit.hp <= 0
                else f"기절 {unit.stun_turns}턴"
                if unit.stun_turns > 0
                else f"보호막 {unit.shield}"
                if unit.shield > 0
                else "정상"
            )
            self._draw_text(f"체력 {unit.hp}/{unit.max_hp}", self.font_small, (214, 222, 229), (item_rect.x + 14, item_rect.y + 128))
            self._draw_text(state_text, self.font_small, item_accent, (item_rect.right - 16, item_rect.y + 128), center=False, align_right=True)

    def _draw_arena(self) -> None:
        offset = self.camera_offset
        self.screen.blit(self.arena_cache, (ARENA_RECT.x + offset.x, ARENA_RECT.y + offset.y))
        self._draw_arena_fog(offset)
        self._draw_rings(offset)
        self._draw_projectiles(offset)

        self.unit_hitboxes.clear()
        draw_order = sorted(self.controller.units, key=lambda unit: self._unit_anchor(unit.id).y)
        for unit in draw_order:
            self._draw_unit(unit, offset)

        self._draw_floaters(offset)
        self._draw_arena_hud(offset)

    def _draw_arena_fog(self, offset: pygame.Vector2) -> None:
        fog = pygame.Surface(ARENA_RECT.size, pygame.SRCALPHA)
        pulse = (math.sin(self.time_accumulator * 1.4) + 1) * 0.5
        left_alpha = int(52 + pulse * 32)
        right_alpha = int(48 + (1 - pulse) * 34)
        pygame.draw.ellipse(fog, (40, 104, 162, left_alpha), pygame.Rect(30, 290, 320, 190))
        pygame.draw.ellipse(fog, (122, 50, 40, right_alpha), pygame.Rect(654, 90, 320, 190))
        pygame.draw.ellipse(fog, (214, 186, 114, 26), pygame.Rect(330, 232, 340, 150))
        self.screen.blit(fog, (ARENA_RECT.x + offset.x, ARENA_RECT.y + offset.y))

    def _draw_arena_hud(self, offset: pygame.Vector2) -> None:
        hud_rect = pygame.Rect(ARENA_RECT.x + 18 + offset.x, ARENA_RECT.y + 18 + offset.y, 384, 96)
        hud_surface = pygame.Surface(hud_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(hud_surface, hud_surface.get_rect(), (7, 16, 27), (12, 24, 37))
        pygame.draw.rect(hud_surface, (255, 255, 255, 18), hud_surface.get_rect(), border_radius=18)
        pygame.draw.rect(hud_surface, (236, 218, 176), hud_surface.get_rect(), 1, border_radius=18)
        self.screen.blit(hud_surface, hud_rect.topleft)

        active = self.controller.get_active_unit()
        title = (
            "블루 팀 승리"
            if self.controller.state.winner == "blue"
            else "레드 팀 승리"
            if self.controller.state.winner == "red"
            else f"{self.preview_action.ability_name} 시전 중"
            if self.preview_action
            else f"{active.name} 차례"
            if active
            else "전투 대기"
        )
        desc = (
            "우측 상단 재시작 버튼으로 다시 시작할 수 있습니다."
            if self.controller.state.winner
            else "전장 위 적 유닛을 클릭해서 타겟을 지정하세요."
            if self.selected_ability_id
            else self.controller.state.log[0]
        )
        self._draw_text(title, self.font_ui, (244, 239, 225), (hud_rect.x + 18, hud_rect.y + 16))
        self._draw_wrapped_text(desc, self.font_small, (176, 194, 208), pygame.Rect(hud_rect.x + 18, hud_rect.y + 46, hud_rect.width - 36, 40))

        if self.last_action_timer > 0 and self.controller.state.last_action is not None:
            action = self.controller.state.last_action
            banner_rect = pygame.Rect(ARENA_RECT.centerx - 150, ARENA_RECT.y + 18, 300, 44)
            banner = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
            alpha = int(120 * clamp(self.last_action_timer / 1.0, 0.0, 1.0))
            pygame.draw.rect(banner, (214, 182, 112, alpha), banner.get_rect(), border_radius=18)
            pygame.draw.rect(banner, (255, 243, 214, min(255, alpha + 50)), banner.get_rect(), 1, border_radius=18)
            self.screen.blit(banner, banner_rect.topleft)
            self._draw_text(action.ability_name, self.font_ui, (17, 20, 25), banner_rect.center, center=True)

    def _draw_floaters(self, offset: pygame.Vector2) -> None:
        for floater in self.floaters:
            alpha = int(255 * clamp(floater.lifetime / 0.85, 0.0, 1.0))
            text_surface = self.font_ui.render(floater.text, True, floater.color)
            text_surface.set_alpha(alpha)
            rect = text_surface.get_rect(center=(floater.x + offset.x, floater.y + offset.y))
            shadow = self.font_ui.render(floater.text, True, (0, 0, 0))
            shadow.set_alpha(alpha // 2)
            self.screen.blit(shadow, shadow.get_rect(center=(rect.centerx + 2, rect.centery + 2)))
            self.screen.blit(text_surface, rect)

    def _draw_rings(self, offset: pygame.Vector2) -> None:
        for ring in self.rings:
            surface = pygame.Surface(ARENA_RECT.size, pygame.SRCALPHA)
            pygame.draw.circle(
                surface,
                (*ring.color, max(0, min(255, int(ring.alpha)))),
                (int(ring.center[0] - ARENA_RECT.x), int(ring.center[1] - ARENA_RECT.y)),
                int(ring.radius),
                ring.width,
            )
            self.screen.blit(surface, (ARENA_RECT.x + offset.x, ARENA_RECT.y + offset.y))

    def _draw_projectiles(self, offset: pygame.Vector2) -> None:
        for projectile in self.projectiles:
            progress = clamp(projectile.progress, 0.0, 1.0)
            start = pygame.Vector2(projectile.start)
            end = pygame.Vector2(projectile.end)
            current = start.lerp(end, progress)
            beam = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

            if projectile.style == "beam":
                pygame.draw.line(beam, (*projectile.color, 70), start + offset, current + offset, projectile.width + 10)
                pygame.draw.line(beam, (*tinted(projectile.color, 0.5), 220), start + offset, current + offset, projectile.width)
            else:
                pygame.draw.line(beam, (*projectile.color, 90), start + offset, current + offset, max(2, projectile.width - 6))

            if projectile.style == "rocket":
                self._draw_rocket(beam, current + offset, projectile.color)
            elif projectile.style == "orb":
                self._draw_orb(beam, current + offset, projectile.color)
            elif projectile.style == "heart":
                self._draw_heart(beam, current + offset, projectile.color)
            else:
                pygame.draw.circle(beam, (*tinted(projectile.color, 0.6), 240), (int(current.x + offset.x), int(current.y + offset.y)), max(6, projectile.width))

            self.screen.blit(beam, (0, 0))

    def _draw_unit(self, unit: CombatUnit, offset: pygame.Vector2) -> None:
        anchor = self._render_anchor(unit, offset)
        rect = pygame.Rect(int(anchor.x - 74), int(anchor.y - 176), 148, 224)
        self.unit_hitboxes[unit.id] = rect

        state = self.fx_state[unit.id]
        accent = hex_to_rgb(unit.accent)
        team_color = (83, 170, 236) if unit.team == "blue" else (230, 114, 88)
        targetable = (
            self.selected_ability_id is not None
            and unit.id in self.controller.get_valid_target_ids(self.selected_ability_id)
            and self.preview_action is None
        )

        shadow_rect = pygame.Rect(rect.x + 10, rect.bottom - 26, rect.width - 20, 26)
        shadow = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 128), shadow.get_rect())
        self.screen.blit(shadow, shadow_rect.topleft)

        if targetable:
            marker = pygame.Surface((shadow_rect.width + 40, shadow_rect.height + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(marker, (95, 212, 196, 160), marker.get_rect(), 4)
            self.screen.blit(marker, (shadow_rect.x - 20, shadow_rect.y - 10))

        if self.controller.state.active_unit_id == unit.id and unit.hp > 0:
            pulse = 1 + (math.sin(self.time_accumulator * 7) + 1) * 0.5
            ring = pygame.Surface((shadow_rect.width + 54, shadow_rect.height + 24), pygame.SRCALPHA)
            pygame.draw.ellipse(ring, (214, 186, 114, int(120 + 30 * pulse)), ring.get_rect(), 4)
            self.screen.blit(ring, (shadow_rect.x - 27, shadow_rect.y - 12))

        if unit.shield > 0 or state.shield_timer > 0:
            shield_surface = pygame.Surface((220, 260), pygame.SRCALPHA)
            shield_alpha = int(100 + 90 * max(state.shield_timer, 0.2))
            pygame.draw.ellipse(shield_surface, (132, 226, 173, shield_alpha), pygame.Rect(12, 24, 196, 196), 4)
            self.screen.blit(shield_surface, (rect.x - 36, rect.y - 24))

        if state.flare_timer > 0:
            flare = pygame.Surface((240, 240), pygame.SRCALPHA)
            flare_alpha = int(120 * (state.flare_timer / 0.42))
            pygame.draw.circle(flare, (*accent, flare_alpha), (120, 120), 64)
            self.screen.blit(flare, (rect.centerx - 120, rect.centery - 132))

        self._draw_champion_sprite(unit, rect, accent, team_color, state)

        health_rect = pygame.Rect(rect.x + 14, rect.y - 14, rect.width - 28, 12)
        pygame.draw.rect(self.screen, (39, 52, 65), health_rect, border_radius=999)
        hp_ratio = max(0.0, unit.hp / unit.max_hp)
        hp_fill = pygame.Rect(health_rect.x, health_rect.y, int(health_rect.width * hp_ratio), health_rect.height)
        pygame.draw.rect(self.screen, (109, 214, 140), hp_fill, border_radius=999)
        pygame.draw.rect(self.screen, (244, 239, 225), health_rect, 1, border_radius=999)

        self._draw_text(unit.name, self.font_ui, (244, 239, 225), (rect.centerx, rect.y - 42), center=True)
        self._draw_text(f"{unit.hp}/{unit.max_hp}", self.font_small, (192, 232, 204), (rect.centerx, rect.y - 24), center=True)
        if state.stun_timer > 0 or unit.stun_turns > 0:
            self._draw_stun_icon(rect.centerx + 48, rect.y - 42)

    def _draw_champion_sprite(
        self,
        unit: CombatUnit,
        rect: pygame.Rect,
        accent: tuple[int, int, int],
        team_color: tuple[int, int, int],
        state: UnitFxState,
    ) -> None:
        canvas = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        outline = (15, 21, 31)
        metal = (198, 207, 220)
        skin = (241, 198, 170)
        cloth_dark = shaded(accent, 0.56)
        cloth_mid = shaded(accent, 0.15)
        cloth_light = tinted(accent, 0.2)

        if state.hit_timer > 0:
            hit = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            pygame.draw.circle(hit, (255, 126, 102, int(150 * state.hit_timer)), (74, 92), 74)
            canvas.blit(hit, (0, 0))

        bob = math.sin(self.time_accumulator * 6 + (0 if unit.team == "blue" else 1.2)) * 1.5
        base_y = 186 + bob

        if unit.id == "blue-garen":
            self._draw_garen(canvas, base_y, outline, skin, cloth_mid, team_color, metal)
        elif unit.id == "blue-ahri":
            self._draw_ahri(canvas, base_y, outline, skin, cloth_mid, cloth_light)
        elif unit.id == "blue-jinx":
            self._draw_jinx(canvas, base_y, outline, skin, cloth_mid, cloth_light, team_color)
        elif unit.id == "red-darius":
            self._draw_darius(canvas, base_y, outline, skin, cloth_mid, team_color, metal)
        elif unit.id == "red-annie":
            self._draw_annie(canvas, base_y, outline, skin, cloth_mid, cloth_light)
        elif unit.id == "red-caitlyn":
            self._draw_caitlyn(canvas, base_y, outline, skin, cloth_mid, cloth_dark, team_color, metal)

        if unit.hp <= 0:
            canvas.set_alpha(115)
            canvas = pygame.transform.rotate(canvas, -12 if unit.team == "blue" else 12)

        self.screen.blit(canvas, canvas.get_rect(center=rect.center))

    def _draw_portrait(self, unit: CombatUnit, rect: pygame.Rect) -> None:
        accent = hex_to_rgb(unit.accent)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (12, 21, 31), (16, 28, 42))
        pygame.draw.rect(panel, (*accent, 26), panel.get_rect(), border_radius=20)
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=20)
        self.screen.blit(panel, rect.topleft)

        sprite = pygame.Surface((80, 100), pygame.SRCALPHA)
        dummy_state = UnitFxState()
        self._draw_champion_sprite_to_surface(sprite, unit, dummy_state)
        portrait = pygame.transform.smoothscale(sprite, (70, 88))
        self.screen.blit(portrait, portrait.get_rect(center=rect.center))

    def _draw_champion_sprite_to_surface(self, surface: pygame.Surface, unit: CombatUnit, state: UnitFxState) -> None:
        accent = hex_to_rgb(unit.accent)
        team_color = (83, 170, 236) if unit.team == "blue" else (230, 114, 88)
        outline = (15, 21, 31)
        metal = (198, 207, 220)
        skin = (241, 198, 170)
        cloth_dark = shaded(accent, 0.56)
        cloth_mid = shaded(accent, 0.15)
        cloth_light = tinted(accent, 0.2)
        base_y = 86
        if unit.id == "blue-garen":
            self._draw_garen(surface, base_y, outline, skin, cloth_mid, team_color, metal, scale=0.46)
        elif unit.id == "blue-ahri":
            self._draw_ahri(surface, base_y, outline, skin, cloth_mid, cloth_light, scale=0.46)
        elif unit.id == "blue-jinx":
            self._draw_jinx(surface, base_y, outline, skin, cloth_mid, cloth_light, team_color, scale=0.46)
        elif unit.id == "red-darius":
            self._draw_darius(surface, base_y, outline, skin, cloth_mid, team_color, metal, scale=0.46)
        elif unit.id == "red-annie":
            self._draw_annie(surface, base_y, outline, skin, cloth_mid, cloth_light, scale=0.46)
        elif unit.id == "red-caitlyn":
            self._draw_caitlyn(surface, base_y, outline, skin, cloth_mid, cloth_dark, team_color, metal, scale=0.46)

    def _draw_garen(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        team_color: tuple[int, int, int],
        metal: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        self._draw_boots(surface, 74, base_y, outline, (30, 42, 58), scale)
        self._draw_cape(surface, [(48, base_y - 110), (32, base_y - 28), (46, base_y + 6), (74, base_y - 34), (98, base_y + 6), (114, base_y - 28), (100, base_y - 110)], outline, team_color, scale)
        self._draw_torso(surface, 74, base_y - 70, 64, 82, outline, cloth, scale)
        self._draw_shoulder(surface, 44, base_y - 110, 24, outline, metal, scale)
        self._draw_shoulder(surface, 104, base_y - 110, 24, outline, metal, scale)
        self._draw_head(surface, 74, base_y - 136, 24, outline, skin, scale)
        self._draw_hair_crest(surface, 74, base_y - 166, outline, (228, 197, 110), scale)
        self._draw_emblem(surface, pygame.Rect(*self._scale_rect(56, base_y - 96, 36, 30, scale)), outline, team_color)
        self._draw_sword(surface, 114, base_y - 84, outline, metal, (238, 213, 142), scale)

    def _draw_ahri(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        cloth_light: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        for offset in (-28, -10, 8, 26):
            self._draw_tail(surface, 74 + offset, base_y - 18 + abs(offset) * 0.22, outline, (245, 226, 235), scale)
        self._draw_boots(surface, 74, base_y, outline, (39, 34, 61), scale)
        self._draw_torso(surface, 74, base_y - 70, 58, 78, outline, cloth, scale)
        self._draw_head(surface, 74, base_y - 138, 22, outline, skin, scale)
        self._draw_fox_ears(surface, 74, base_y - 164, outline, (245, 219, 228), scale)
        self._draw_hair(surface, 74, base_y - 142, outline, (45, 45, 77), scale)
        orb_pos = (74 + 44 * scale, base_y - 92)
        pygame.draw.circle(surface, (111, 229, 255), (int(orb_pos[0]), int(orb_pos[1])), int(14 * scale))
        pygame.draw.circle(surface, (238, 249, 255), (int(orb_pos[0]), int(orb_pos[1])), int(14 * scale), max(1, int(3 * scale)))
        self._draw_sash(surface, 74, base_y - 74, outline, cloth_light, scale)

    def _draw_jinx(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        cloth_light: tuple[int, int, int],
        team_color: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        self._draw_boots(surface, 74, base_y, outline, (23, 34, 51), scale)
        self._draw_torso(surface, 74, base_y - 72, 50, 78, outline, cloth, scale)
        self._draw_head(surface, 74, base_y - 138, 22, outline, skin, scale)
        self._draw_hair(surface, 74, base_y - 142, outline, (84, 214, 232), scale)
        self._draw_braids(surface, 74, base_y - 120, outline, (84, 214, 232), scale)
        self._draw_emblem(surface, pygame.Rect(*self._scale_rect(58, base_y - 100, 30, 28, scale)), outline, team_color)
        self._draw_launcher(surface, 114, base_y - 82, outline, cloth_light, (234, 100, 126), scale)

    def _draw_darius(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        team_color: tuple[int, int, int],
        metal: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        self._draw_boots(surface, 74, base_y, outline, (68, 28, 24), scale)
        self._draw_cape(surface, [(42, base_y - 110), (28, base_y - 18), (42, base_y + 6), (74, base_y - 42), (108, base_y + 4), (120, base_y - 16), (106, base_y - 110)], outline, team_color, scale)
        self._draw_torso(surface, 74, base_y - 72, 66, 84, outline, cloth, scale)
        self._draw_shoulder(surface, 42, base_y - 112, 26, outline, metal, scale)
        self._draw_shoulder(surface, 106, base_y - 112, 26, outline, metal, scale)
        self._draw_head(surface, 74, base_y - 138, 23, outline, skin, scale)
        self._draw_axe(surface, 114, base_y - 86, outline, metal, team_color, scale)
        self._draw_emblem(surface, pygame.Rect(*self._scale_rect(58, base_y - 102, 32, 30, scale)), outline, team_color)

    def _draw_annie(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        cloth_light: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        self._draw_boots(surface, 74, base_y, outline, (64, 26, 18), scale)
        self._draw_torso(surface, 74, base_y - 72, 54, 82, outline, cloth, scale)
        self._draw_head(surface, 74, base_y - 138, 22, outline, skin, scale)
        self._draw_buns(surface, 74, base_y - 150, outline, (86, 44, 38), scale)
        self._draw_hair(surface, 74, base_y - 142, outline, (84, 40, 36), scale)
        self._draw_fire_orb(surface, 112, base_y - 90, outline, cloth_light, scale)

    def _draw_caitlyn(
        self,
        surface: pygame.Surface,
        base_y: float,
        outline: tuple[int, int, int],
        skin: tuple[int, int, int],
        cloth: tuple[int, int, int],
        cloth_dark: tuple[int, int, int],
        team_color: tuple[int, int, int],
        metal: tuple[int, int, int],
        *,
        scale: float = 1.0,
    ) -> None:
        self._draw_boots(surface, 74, base_y, outline, (52, 28, 26), scale)
        self._draw_torso(surface, 74, base_y - 72, 54, 82, outline, cloth, scale)
        self._draw_head(surface, 74, base_y - 140, 22, outline, skin, scale)
        self._draw_hat(surface, 74, base_y - 166, outline, cloth_dark, team_color, scale)
        self._draw_rifle(surface, 114, base_y - 84, outline, metal, cloth_dark, scale)
        self._draw_emblem(surface, pygame.Rect(*self._scale_rect(58, base_y - 102, 30, 28, scale)), outline, team_color)

    def _draw_boots(self, surface: pygame.Surface, cx: float, base_y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        left = pygame.Rect(*self._scale_rect(cx - 24, base_y - 18, 18, 30, scale))
        right = pygame.Rect(*self._scale_rect(cx + 6, base_y - 18, 18, 30, scale))
        pygame.draw.rect(surface, color, left, border_radius=max(3, int(6 * scale)))
        pygame.draw.rect(surface, color, right, border_radius=max(3, int(6 * scale)))
        pygame.draw.rect(surface, outline, left, max(1, int(3 * scale)), border_radius=max(3, int(6 * scale)))
        pygame.draw.rect(surface, outline, right, max(1, int(3 * scale)), border_radius=max(3, int(6 * scale)))

    def _draw_torso(self, surface: pygame.Surface, cx: float, y: float, w: float, h: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        rect = pygame.Rect(*self._scale_rect(cx - w / 2, y, w, h, scale))
        pygame.draw.rect(surface, color, rect, border_radius=max(8, int(16 * scale)))
        pygame.draw.rect(surface, outline, rect, max(1, int(3 * scale)), border_radius=max(8, int(16 * scale)))

    def _draw_head(self, surface: pygame.Surface, cx: float, cy: float, radius: float, outline: tuple[int, int, int], skin: tuple[int, int, int], scale: float) -> None:
        pygame.draw.circle(surface, skin, self._scale_point(cx, cy, scale), int(radius * scale))
        pygame.draw.circle(surface, outline, self._scale_point(cx, cy, scale), int(radius * scale), max(1, int(3 * scale)))

    def _draw_hair(self, surface: pygame.Surface, cx: float, cy: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        points = [self._scale_point(cx - 24, cy - 8, scale), self._scale_point(cx - 20, cy + 14, scale), self._scale_point(cx + 20, cy + 16, scale), self._scale_point(cx + 26, cy - 8, scale), self._scale_point(cx, cy - 22, scale)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, outline, points, max(1, int(3 * scale)))

    def _draw_braids(self, surface: pygame.Surface, cx: float, cy: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        left_points = [self._scale_point(cx - 18, cy, scale), self._scale_point(cx - 52, cy + 70, scale), self._scale_point(cx - 42, cy + 92, scale)]
        right_points = [self._scale_point(cx + 18, cy, scale), self._scale_point(cx + 54, cy + 70, scale), self._scale_point(cx + 44, cy + 92, scale)]
        pygame.draw.lines(surface, color, False, left_points, max(2, int(8 * scale)))
        pygame.draw.lines(surface, color, False, right_points, max(2, int(8 * scale)))
        pygame.draw.lines(surface, outline, False, left_points, max(1, int(3 * scale)))
        pygame.draw.lines(surface, outline, False, right_points, max(1, int(3 * scale)))

    def _draw_fox_ears(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        left = [self._scale_point(cx - 20, y, scale), self._scale_point(cx - 6, y + 18, scale), self._scale_point(cx - 30, y + 22, scale)]
        right = [self._scale_point(cx + 20, y, scale), self._scale_point(cx + 30, y + 22, scale), self._scale_point(cx + 6, y + 18, scale)]
        pygame.draw.polygon(surface, color, left)
        pygame.draw.polygon(surface, color, right)
        pygame.draw.polygon(surface, outline, left, max(1, int(3 * scale)))
        pygame.draw.polygon(surface, outline, right, max(1, int(3 * scale)))

    def _draw_tail(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        points = [self._scale_point(cx - 14, y, scale), self._scale_point(cx - 4, y - 24, scale), self._scale_point(cx + 10, y + 6, scale), self._scale_point(cx + 2, y + 30, scale)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, outline, points, max(1, int(3 * scale)))

    def _draw_shoulder(self, surface: pygame.Surface, cx: float, cy: float, radius: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        pygame.draw.circle(surface, color, self._scale_point(cx, cy, scale), int(radius * scale))
        pygame.draw.circle(surface, outline, self._scale_point(cx, cy, scale), int(radius * scale), max(1, int(3 * scale)))

    def _draw_cape(self, surface: pygame.Surface, points: list[tuple[float, float]], outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        scaled = [self._scale_point(x, y, scale) for x, y in points]
        pygame.draw.polygon(surface, color, scaled)
        pygame.draw.polygon(surface, outline, scaled, max(1, int(3 * scale)))

    def _draw_hair_crest(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        crest = [self._scale_point(cx, y, scale), self._scale_point(cx + 12, y + 18, scale), self._scale_point(cx - 12, y + 18, scale)]
        pygame.draw.polygon(surface, color, crest)
        pygame.draw.polygon(surface, outline, crest, max(1, int(3 * scale)))

    def _draw_sword(self, surface: pygame.Surface, x: float, y: float, outline: tuple[int, int, int], metal: tuple[int, int, int], gem: tuple[int, int, int], scale: float) -> None:
        blade = pygame.Rect(*self._scale_rect(x - 4, y - 54, 8, 94, scale))
        guard = pygame.Rect(*self._scale_rect(x - 16, y + 4, 32, 10, scale))
        handle = pygame.Rect(*self._scale_rect(x - 5, y + 8, 10, 24, scale))
        pygame.draw.rect(surface, metal, blade, border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, gem, guard, border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, shaded(gem, 0.48), handle, border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, outline, blade, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, outline, guard, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, outline, handle, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))

    def _draw_axe(self, surface: pygame.Surface, x: float, y: float, outline: tuple[int, int, int], metal: tuple[int, int, int], accent: tuple[int, int, int], scale: float) -> None:
        handle = pygame.Rect(*self._scale_rect(x - 4, y - 50, 8, 96, scale))
        blade_left = [self._scale_point(x - 2, y - 42, scale), self._scale_point(x - 34, y - 18, scale), self._scale_point(x - 10, y + 8, scale)]
        blade_right = [self._scale_point(x + 2, y - 30, scale), self._scale_point(x + 30, y - 6, scale), self._scale_point(x + 4, y + 8, scale)]
        pygame.draw.rect(surface, shaded(accent, 0.5), handle, border_radius=max(1, int(3 * scale)))
        pygame.draw.polygon(surface, metal, blade_left)
        pygame.draw.polygon(surface, metal, blade_right)
        pygame.draw.rect(surface, outline, handle, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))
        pygame.draw.polygon(surface, outline, blade_left, max(1, int(2 * scale)))
        pygame.draw.polygon(surface, outline, blade_right, max(1, int(2 * scale)))

    def _draw_launcher(self, surface: pygame.Surface, x: float, y: float, outline: tuple[int, int, int], body: tuple[int, int, int], accent: tuple[int, int, int], scale: float) -> None:
        main = pygame.Rect(*self._scale_rect(x - 22, y - 10, 42, 18, scale))
        barrel = pygame.Rect(*self._scale_rect(x + 18, y - 6, 24, 10, scale))
        wheel = self._scale_point(x - 6, y + 10, scale)
        pygame.draw.rect(surface, body, main, border_radius=max(3, int(7 * scale)))
        pygame.draw.rect(surface, accent, barrel, border_radius=max(3, int(5 * scale)))
        pygame.draw.circle(surface, accent, wheel, max(2, int(6 * scale)))
        pygame.draw.rect(surface, outline, main, max(1, int(2 * scale)), border_radius=max(3, int(7 * scale)))
        pygame.draw.rect(surface, outline, barrel, max(1, int(2 * scale)), border_radius=max(3, int(5 * scale)))
        pygame.draw.circle(surface, outline, wheel, max(2, int(6 * scale)), max(1, int(2 * scale)))

    def _draw_fire_orb(self, surface: pygame.Surface, x: float, y: float, outline: tuple[int, int, int], accent: tuple[int, int, int], scale: float) -> None:
        center = self._scale_point(x, y, scale)
        pygame.draw.circle(surface, accent, center, int(16 * scale))
        pygame.draw.circle(surface, (255, 188, 82), center, int(10 * scale))
        pygame.draw.circle(surface, outline, center, int(16 * scale), max(1, int(3 * scale)))

    def _draw_hat(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], brim: tuple[int, int, int], accent: tuple[int, int, int], scale: float) -> None:
        top = pygame.Rect(*self._scale_rect(cx - 20, y - 4, 40, 16, scale))
        band = pygame.Rect(*self._scale_rect(cx - 28, y + 8, 56, 10, scale))
        feather = [self._scale_point(cx + 8, y - 8, scale), self._scale_point(cx + 24, y - 26, scale), self._scale_point(cx + 18, y + 2, scale)]
        pygame.draw.rect(surface, brim, top, border_radius=max(2, int(4 * scale)))
        pygame.draw.rect(surface, brim, band, border_radius=max(2, int(4 * scale)))
        pygame.draw.polygon(surface, accent, feather)
        pygame.draw.rect(surface, outline, top, max(1, int(2 * scale)), border_radius=max(2, int(4 * scale)))
        pygame.draw.rect(surface, outline, band, max(1, int(2 * scale)), border_radius=max(2, int(4 * scale)))
        pygame.draw.polygon(surface, outline, feather, max(1, int(2 * scale)))

    def _draw_rifle(self, surface: pygame.Surface, x: float, y: float, outline: tuple[int, int, int], metal: tuple[int, int, int], stock: tuple[int, int, int], scale: float) -> None:
        barrel = pygame.Rect(*self._scale_rect(x - 22, y - 6, 52, 8, scale))
        stock_rect = pygame.Rect(*self._scale_rect(x - 30, y + 2, 24, 12, scale))
        sight = pygame.Rect(*self._scale_rect(x - 2, y - 12, 12, 6, scale))
        pygame.draw.rect(surface, metal, barrel, border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, stock, stock_rect, border_radius=max(1, int(4 * scale)))
        pygame.draw.rect(surface, stock, sight, border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, outline, barrel, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))
        pygame.draw.rect(surface, outline, stock_rect, max(1, int(2 * scale)), border_radius=max(1, int(4 * scale)))
        pygame.draw.rect(surface, outline, sight, max(1, int(2 * scale)), border_radius=max(1, int(3 * scale)))

    def _draw_sash(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        sash = [self._scale_point(cx - 18, y, scale), self._scale_point(cx + 16, y + 12, scale), self._scale_point(cx + 6, y + 32, scale), self._scale_point(cx - 24, y + 20, scale)]
        pygame.draw.polygon(surface, color, sash)
        pygame.draw.polygon(surface, outline, sash, max(1, int(3 * scale)))

    def _draw_emblem(self, surface: pygame.Surface, rect: pygame.Rect, outline: tuple[int, int, int], color: tuple[int, int, int]) -> None:
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, outline, rect, 2, border_radius=8)

    def _draw_buns(self, surface: pygame.Surface, cx: float, y: float, outline: tuple[int, int, int], color: tuple[int, int, int], scale: float) -> None:
        for offset in (-18, 18):
            pygame.draw.circle(surface, color, self._scale_point(cx + offset, y, scale), int(10 * scale))
            pygame.draw.circle(surface, outline, self._scale_point(cx + offset, y, scale), int(10 * scale), max(1, int(3 * scale)))

    def _draw_stun_icon(self, x: int, y: int) -> None:
        points = [(x, y - 8), (x + 8, y + 6), (x - 1, y + 6), (x + 2, y + 18), (x - 11, y + 1), (x, y + 1)]
        pygame.draw.polygon(self.screen, (255, 224, 143), points)
        pygame.draw.polygon(self.screen, (84, 58, 18), points, 2)

    def _draw_action_panel(self) -> None:
        self._draw_panel(ACTION_PANEL, (214, 182, 112), glow=True)
        active = self.controller.get_active_unit()
        if active is None:
            return

        title = "전투 결과" if self.controller.state.winner else f"조작 중: {active.name}"
        desc = (
            "전투가 끝났습니다. 재시작해 다시 플레이하세요."
            if self.controller.state.winner
            else "대상을 직접 클릭해 스킬을 발동하세요."
            if self.selected_ability_id
            else "스킬을 누르면 캐릭터가 전장 위에서 움직이며 시전합니다."
            if active.team == "blue"
            else "적이 다음 행동을 계산하고 있습니다."
        )
        self._draw_text(title, self.font_heading, (244, 239, 225), (ACTION_PANEL.x + 24, ACTION_PANEL.y + 18))
        self._draw_wrapped_text(desc, self.font_small, (166, 188, 202), pygame.Rect(ACTION_PANEL.x + 24, ACTION_PANEL.y + 50, 180, 70))

        for index, button in enumerate(self._ability_buttons(), start=1):
            fill = (17, 31, 47)
            border = (248, 240, 220)
            if button.selected:
                fill = (24, 71, 80)
                border = (100, 222, 201)
            elif button.disabled:
                fill = (13, 18, 24)
                border = (82, 94, 106)

            card = pygame.Surface(button.rect.size, pygame.SRCALPHA)
            draw_vertical_gradient(card, card.get_rect(), fill, mix(fill, (255, 255, 255), 0.08))
            pygame.draw.rect(card, (*hex_to_rgb(active.accent), 24), card.get_rect(), border_radius=18)
            pygame.draw.rect(card, border, card.get_rect(), 1, border_radius=18)
            self.screen.blit(card, button.rect.topleft)

            keycap = pygame.Rect(button.rect.x + 14, button.rect.y + 14, 26, 26)
            pygame.draw.rect(self.screen, (12, 20, 31), keycap, border_radius=8)
            pygame.draw.rect(self.screen, border, keycap, 1, border_radius=8)
            self._draw_text(str(index), self.font_small, border, keycap.center, center=True)

            label_color = (244, 239, 225) if not button.disabled else (124, 138, 151)
            label_font = self.font_ui if self.font_ui.size(button.label)[0] <= button.rect.width - 70 else self.font_small
            self._draw_text(button.label, label_font, label_color, (button.rect.x + 52, button.rect.y + 15))
            self._draw_wrapped_text(
                button.sub_label,
                self.font_small,
                (180, 198, 210) if not button.disabled else (94, 108, 122),
                pygame.Rect(button.rect.x + 18, button.rect.y + 46, button.rect.width - 36, 42),
            )

    def _draw_log_panel(self) -> None:
        self._draw_panel(LOG_PANEL, (214, 182, 112))
        self._draw_text("전투 기록", self.font_heading, (228, 209, 164), (LOG_PANEL.x + 18, LOG_PANEL.y + 18))
        for index, line in enumerate(self.controller.state.log[:5]):
            line_rect = pygame.Rect(LOG_PANEL.x + 18, LOG_PANEL.y + 54 + index * 24, LOG_PANEL.width - 36, 22)
            self._draw_wrapped_text(line, self.font_small, (214, 222, 229), line_rect, max_lines=1)

    def _draw_winner_overlay(self) -> None:
        if not self.controller.state.winner:
            return

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 118))
        self.screen.blit(overlay, (0, 0))
        banner_rect = pygame.Rect(WINDOW_WIDTH // 2 - 240, 158, 480, 112)
        banner = pygame.Surface(banner_rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(banner, banner.get_rect(), (30, 21, 9), (86, 58, 20))
        pygame.draw.rect(banner, (255, 243, 214), banner.get_rect(), 1, border_radius=24)
        self.screen.blit(banner, banner_rect.topleft)
        text = "블루 팀 승리" if self.controller.state.winner == "blue" else "레드 팀 승리"
        self._draw_text(text, self.font_title, (244, 239, 225), banner_rect.center, center=True)
        self._draw_text("R 키 또는 우측 상단 버튼으로 다시 시작", self.font_ui, (220, 188, 118), (WINDOW_WIDTH // 2, 286), center=True)

    def _draw_glow(
        self,
        surface: pygame.Surface,
        color: tuple[int, int, int],
        center: tuple[int, int],
        radius: int,
        alpha: int,
    ) -> None:
        glow = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for ring in range(4, 0, -1):
            current_radius = int(radius * ring / 4)
            current_alpha = int(alpha * ring / 5)
            pygame.draw.circle(glow, (*color, current_alpha), (radius, radius), current_radius)
        surface.blit(glow, (center[0] - radius, center[1] - radius))

    def _draw_orb(self, surface: pygame.Surface, center: pygame.Vector2, color: tuple[int, int, int]) -> None:
        pos = (int(center.x), int(center.y))
        pygame.draw.circle(surface, (*color, 220), pos, 14)
        pygame.draw.circle(surface, (255, 248, 240, 230), pos, 8)
        pygame.draw.circle(surface, (255, 255, 255, 255), pos, 14, 2)

    def _draw_heart(self, surface: pygame.Surface, center: pygame.Vector2, color: tuple[int, int, int]) -> None:
        heart = pygame.Surface((40, 36), pygame.SRCALPHA)
        pygame.draw.circle(heart, (*color, 230), (12, 10), 9)
        pygame.draw.circle(heart, (*color, 230), (28, 10), 9)
        pygame.draw.polygon(heart, (*color, 230), [(4, 16), (20, 34), (36, 16)])
        surface.blit(heart, heart.get_rect(center=(int(center.x), int(center.y))))

    def _draw_rocket(self, surface: pygame.Surface, center: pygame.Vector2, color: tuple[int, int, int]) -> None:
        rocket = pygame.Surface((54, 22), pygame.SRCALPHA)
        pygame.draw.rect(rocket, (*color, 240), pygame.Rect(8, 4, 28, 14), border_radius=7)
        pygame.draw.polygon(rocket, (255, 225, 188, 240), [(36, 4), (50, 11), (36, 18)])
        pygame.draw.polygon(rocket, (255, 132, 90, 220), [(8, 11), (0, 4), (0, 18)])
        pygame.draw.rect(rocket, (255, 255, 255, 220), pygame.Rect(18, 8, 8, 5), border_radius=2)
        surface.blit(rocket, rocket.get_rect(center=(int(center.x), int(center.y))))

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int] | tuple[float, float] | pygame.Vector2,
        *,
        center: bool = False,
        align_right: bool = False,
    ) -> None:
        rendered = font.render(text, True, color)
        if center:
            rect = rendered.get_rect(center=position)
        elif align_right:
            rect = rendered.get_rect(topright=position)
        else:
            rect = rendered.get_rect(topleft=position)
        self.screen.blit(rendered, rect)

    def _draw_wrapped_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        rect: pygame.Rect,
        *,
        max_lines: int | None = None,
    ) -> None:
        lines = self._wrap_text(text, font, rect.width, max_lines=max_lines)
        line_height = font.get_linesize()
        for index, line in enumerate(lines):
            self.screen.blit(font.render(line, True, color), (rect.x, rect.y + index * line_height))

    def _wrap_text(
        self,
        text: str,
        font: pygame.font.Font,
        max_width: int,
        *,
        max_lines: int | None = None,
    ) -> list[str]:
        lines: list[str] = []
        current = ""
        for char in text:
            if char == "\n":
                lines.append(current)
                current = ""
                if max_lines is not None and len(lines) >= max_lines:
                    return lines
                continue

            candidate = current + char
            if current and font.size(candidate)[0] > max_width:
                lines.append(current)
                current = char.lstrip()
                if max_lines is not None and len(lines) >= max_lines:
                    return lines
                continue
            current = candidate

        if current:
            lines.append(current)

        return lines[:max_lines] if max_lines is not None else lines

    def _scale_point(self, x: float, y: float, scale: float) -> tuple[int, int]:
        return int(x * scale), int(y * scale)

    def _scale_rect(self, x: float, y: float, w: float, h: float, scale: float) -> tuple[int, int, int, int]:
        return int(x * scale), int(y * scale), int(w * scale), int(h * scale)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rift Tactics native prototype")
    parser.add_argument("--frames", type=int, default=None, help="Run only for a fixed number of frames")
    parser.add_argument("--headless", action="store_true", help="Use a hidden window for smoke tests")
    parser.add_argument("--screenshot", type=str, default=None, help="Save the last rendered frame to a PNG path")
    return parser
