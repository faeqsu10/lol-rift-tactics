from __future__ import annotations

import argparse
from dataclasses import dataclass

import pygame

from native_game.audio import SoundBank
from native_game.runtime import project_root

from .data import ART_FILE_BY_UNIT_ID
from .data import GRID_HEIGHT
from .data import GRID_WIDTH
from .engine import TacticalActionResult
from .engine import TacticsController

WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 960
GRID_CELL = 100
GRID_ORIGIN = pygame.Vector2(360, 130)
GRID_RECT = pygame.Rect(int(GRID_ORIGIN.x), int(GRID_ORIGIN.y), GRID_WIDTH * GRID_CELL, GRID_HEIGHT * GRID_CELL)
LEFT_PANEL = pygame.Rect(36, 120, 284, 694)
RIGHT_PANEL = pygame.Rect(1180, 120, 384, 694)
BOTTOM_PANEL = pygame.Rect(36, 832, WINDOW_WIDTH - 72, 92)
HEADER_RECT = pygame.Rect(36, 28, WINDOW_WIDTH - 72, 72)

PROJECT_ROOT = project_root()
FONT_PATH = PROJECT_ROOT / "assets" / "fonts" / "NotoSansKR-Variable.ttf"
CHAMPION_ART_DIR = PROJECT_ROOT / "assets" / "champions"


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: tuple[int, int, int]
    lifetime: float = 0.8


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    hex_code = hex_code.lstrip("#")
    return tuple(int(hex_code[index : index + 2], 16) for index in (0, 2, 4))


def mix(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = clamp(amount, 0.0, 1.0)
    return tuple(int(a + (b - a) * amount) for a, b in zip(color_a, color_b))


def draw_vertical_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    top: tuple[int, int, int],
    bottom: tuple[int, int, int],
) -> None:
    for offset in range(rect.height):
        progress = offset / max(1, rect.height - 1)
        pygame.draw.line(surface, mix(top, bottom, progress), (rect.x, rect.y + offset), (rect.right, rect.y + offset))


def load_font(size: int, *, bold: bool = False) -> pygame.font.Font:
    if FONT_PATH.exists():
        font = pygame.font.Font(FONT_PATH, size)
        font.set_bold(bold)
        return font

    matched = pygame.font.match_font(["Noto Sans CJK KR", "NanumGothic", "malgungothic", "arial"], bold=bold)
    if matched:
        font = pygame.font.Font(matched, size)
        font.set_bold(bold)
        return font

    font = pygame.font.Font(None, size)
    font.set_bold(bold)
    return font


class GameApp:
    def __init__(self, headless: bool = False) -> None:
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("리프트 택틱스: 전술 실험")
        flags = pygame.HIDDEN if headless else 0
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        self.clock = pygame.time.Clock()
        self.running = True
        self.headless = headless

        self.font_tiny = load_font(13)
        self.font_small = load_font(16)
        self.font_ui = load_font(20)
        self.font_heading = load_font(26, bold=True)
        self.font_large = load_font(34, bold=True)
        self.font_title = load_font(42, bold=True)

        self.controller = TacticsController()
        self.audio = SoundBank()
        self.audio.start_ambient()
        self.mode = "move"
        self.status_text = "이동할 칸을 고르거나 스킬을 선택하세요."
        self.ai_timer = 0.55
        self.last_active_id: str | None = None
        self.floaters: list[FloatingText] = []
        self.hit_flash: dict[str, float] = {unit.id: 0.0 for unit in self.controller.units}
        self.tile_rects: dict[tuple[int, int], pygame.Rect] = {}
        self.button_rects: dict[str, pygame.Rect] = {}
        self.unit_visual_positions: dict[str, pygame.Vector2] = {
            unit.id: pygame.Vector2(self._tile_center(unit.position)) for unit in self.controller.units
        }
        self.champion_art = self._load_champion_art()
        self.background_cache = self._build_background()

    def run(self, max_frames: int | None = None, screenshot_path: str | None = None) -> None:
        frames = 0
        while self.running:
            dt = self.clock.tick(60) / 1000.0
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

    def _load_champion_art(self) -> dict[str, pygame.Surface]:
        art: dict[str, pygame.Surface] = {}
        for unit_id, filename in ART_FILE_BY_UNIT_ID.items():
            path = CHAMPION_ART_DIR / filename
            if path.exists():
                art[unit_id] = pygame.image.load(path).convert_alpha()
        return art

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        draw_vertical_gradient(surface, surface.get_rect(), (11, 18, 29), (20, 31, 48))
        for index in range(14):
            color = (214, 184, 114) if index % 2 == 0 else (78, 119, 155)
            alpha = 20 if index % 2 == 0 else 14
            circle = pygame.Surface((340, 340), pygame.SRCALPHA)
            pygame.draw.circle(circle, (*color, alpha), (170, 170), 170)
            surface.blit(circle, (index * 110 - 120, (index % 3) * 210 - 90))
        return surface

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self._reset()
                elif event.key == pygame.K_m:
                    self.mode = "move"
                elif event.key == pygame.K_1:
                    self.mode = "basic"
                elif event.key == pygame.K_2:
                    self._choose_special_mode()
                elif event.key == pygame.K_e:
                    self._end_turn()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.button_rects.get("reset") and self.button_rects["reset"].collidepoint(position):
            self._reset()
            return

        active = self.controller.get_active_unit()
        if active is None:
            return

        if active.team == "blue":
            for key in ("move", "basic", "special", "end"):
                rect = self.button_rects.get(key)
                if rect and rect.collidepoint(position):
                    if key == "move":
                        self.mode = "move"
                        self.status_text = "도달 가능한 칸을 클릭해 이동하세요."
                    elif key == "basic":
                        self.mode = "basic"
                        self.status_text = "사거리 안 적을 클릭해 기본 공격을 사용하세요."
                    elif key == "special":
                        self._choose_special_mode()
                    elif key == "end":
                        self._end_turn()
                    return

            clicked_tile = self._tile_from_screen(position)
            if clicked_tile is None:
                return

            if self.mode == "move" and clicked_tile in self.controller.get_reachable_tiles():
                result = self.controller.move_active(clicked_tile)
                if result:
                    self._apply_action_result(result)
                return

            target = self._unit_at_tile(clicked_tile)
            if target is None or target.team == active.team:
                return

            if self.mode == "basic" and target.id in self.controller.get_valid_targets("basic"):
                result = self.controller.use_basic(target.id)
                if result:
                    self._apply_action_result(result)
                return

            if self.mode == "special" and target.id in self.controller.get_valid_targets("special"):
                result = self.controller.use_special(target.id)
                if result:
                    self._apply_action_result(result)

    def _choose_special_mode(self) -> None:
        active = self.controller.get_active_unit()
        if active is None:
            return
        ability = active.special_ability
        if active.cooldowns[ability.id] > 0 or active.has_acted:
            self.status_text = "특수기는 아직 사용할 수 없습니다."
            self.audio.play("reset")
            return
        if ability.target_mode == "self":
            result = self.controller.use_special(active.id)
            if result:
                self._apply_action_result(result)
            return
        self.mode = "special"
        self.status_text = f"사거리 안 적을 클릭해 {ability.name}을(를) 사용하세요."

    def _end_turn(self) -> None:
        result = self.controller.end_turn()
        if result:
            self.mode = "move"
            self.status_text = "턴을 넘겼습니다."
            self.audio.play("ui-confirm")

    def _reset(self) -> None:
        self.controller.reset()
        self.mode = "move"
        self.status_text = "전술 전투를 다시 시작했습니다."
        self.floaters.clear()
        self.hit_flash = {unit.id: 0.0 for unit in self.controller.units}
        self.unit_visual_positions = {unit.id: pygame.Vector2(self._tile_center(unit.position)) for unit in self.controller.units}
        self.last_active_id = None
        self.ai_timer = 0.55
        self.audio.play("reset")

    def _update(self, dt: float) -> None:
        active = self.controller.get_active_unit()
        active_id = active.id if active else None
        if active_id != self.last_active_id:
            if active and active.team == "blue":
                self.mode = "move"
                self.status_text = f"{active.name} 차례입니다. 이동 후 행동하거나, 바로 행동할 수 있습니다."
            elif active and active.team == "red":
                self.mode = "observe"
                self.status_text = f"{active.name}가 행동을 고르는 중입니다."
                self.ai_timer = 0.55
            self.last_active_id = active_id

        for unit in self.controller.units:
            target = pygame.Vector2(self._tile_center(unit.position))
            current = self.unit_visual_positions.setdefault(unit.id, target)
            current.update(current.lerp(target, clamp(dt * 8.5, 0.0, 1.0)))

        for unit_id in list(self.hit_flash):
            self.hit_flash[unit_id] = max(0.0, self.hit_flash[unit_id] - dt)

        for floater in list(self.floaters):
            floater.lifetime -= dt
            floater.y -= dt * 34
            if floater.lifetime <= 0:
                self.floaters.remove(floater)

        active = self.controller.get_active_unit()
        if active and active.team == "red" and not self.controller.state.winner:
            self.ai_timer -= dt
            if self.ai_timer <= 0:
                results = self.controller.run_ai_turn()
                for result in results:
                    self._apply_action_result(result)
                self.ai_timer = 0.55

    def _apply_action_result(self, result: TacticalActionResult) -> None:
        if result.kind == "move":
            self.audio.play("ui-confirm", champion_id=result.actor_id)
            self.status_text = "이동 완료. 행동을 선택하거나 턴을 끝낼 수 있습니다."
            return

        if result.kind == "end":
            return

        self.audio.play("cast", champion_id=result.actor_id)
        any_damage = False
        any_shield = False
        any_stun = False
        for impact in result.impacts:
            unit = self.controller.get_unit(impact.target_id)
            if unit is None:
                continue
            anchor = self.unit_visual_positions[unit.id]
            if impact.damage:
                any_damage = True
                self.hit_flash[unit.id] = 0.28
                self.floaters.append(FloatingText(anchor.x, anchor.y - 46, f"-{impact.damage}", (255, 172, 144)))
            if impact.shield_gained:
                any_shield = True
                self.floaters.append(FloatingText(anchor.x, anchor.y - 70, f"+보호막 {impact.shield_gained}", (166, 235, 191)))
            if impact.stun_applied:
                any_stun = True
                self.floaters.append(FloatingText(anchor.x, anchor.y - 94, "기절", (255, 229, 145)))
            if impact.defeated:
                self.floaters.append(FloatingText(anchor.x, anchor.y - 118, "처치", (255, 216, 168)))

        if any_damage:
            heavy = any(impact.damage >= 18 for impact in result.impacts)
            self.audio.play("hit-heavy" if heavy else "hit")
        if any_shield:
            self.audio.play("shield")
        if any_stun:
            self.audio.play("stun")

        if result.kind == "basic":
            self.status_text = "기본 공격 사용 완료."
        else:
            self.status_text = f"{result.ability_name} 사용 완료."

        if self.controller.state.winner == "blue":
            self.audio.play("victory")
            self.status_text = "블루 팀이 승리했습니다."
        elif self.controller.state.winner == "red":
            self.audio.play("defeat")
            self.status_text = "레드 팀이 승리했습니다."

    def _draw(self) -> None:
        self.screen.blit(self.background_cache, (0, 0))
        self._draw_header()
        self._draw_panel(LEFT_PANEL, (59, 129, 191))
        self._draw_panel(RIGHT_PANEL, (189, 92, 82))
        self._draw_panel(BOTTOM_PANEL, (214, 182, 112))
        self._draw_grid()
        self._draw_left_panel()
        self._draw_right_panel()
        self._draw_bottom_panel()
        self._draw_floaters()
        self._draw_winner_overlay()

    def _draw_header(self) -> None:
        panel = pygame.Surface(HEADER_RECT.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (15, 24, 37), (19, 31, 47))
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=24)
        self.screen.blit(panel, HEADER_RECT.topleft)
        self._draw_text("리그 오브 레전드: 리프트 택틱스", self.font_title, (244, 239, 225), (56, 38))
        self._draw_text("전술 실험 빌드", self.font_ui, (226, 204, 156), (58, 80))
        self._draw_text("8x6 그리드 · 이동 + 행동 턴제", self.font_ui, (158, 185, 207), (WINDOW_WIDTH // 2, 48), center=True)
        reset_rect = pygame.Rect(WINDOW_WIDTH - 234, 42, 154, 42)
        self.button_rects["reset"] = reset_rect
        pygame.draw.rect(self.screen, (214, 182, 112), reset_rect, border_radius=14)
        pygame.draw.rect(self.screen, (255, 244, 217), reset_rect, 1, border_radius=14)
        self._draw_text("R 리셋", self.font_ui, (13, 21, 31), reset_rect.center, center=True)

    def _draw_panel(self, rect: pygame.Rect, glow_color: tuple[int, int, int]) -> None:
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_vertical_gradient(panel, panel.get_rect(), (10, 19, 29), (17, 28, 42))
        pygame.draw.rect(panel, (*glow_color, 18), panel.get_rect(), border_radius=26)
        pygame.draw.rect(panel, (236, 218, 176), panel.get_rect(), 1, border_radius=26)
        self.screen.blit(panel, rect.topleft)

    def _draw_grid(self) -> None:
        grid_surface = pygame.Surface(GRID_RECT.size, pygame.SRCALPHA)
        draw_vertical_gradient(grid_surface, grid_surface.get_rect(), (7, 16, 26), (10, 22, 36))
        self.screen.blit(grid_surface, GRID_RECT.topleft)

        reachable = self.controller.get_reachable_tiles()
        basic_targets = set(self.controller.get_valid_targets("basic")) if self.mode == "basic" else set()
        special_targets = set(self.controller.get_valid_targets("special")) if self.mode == "special" else set()
        active = self.controller.get_active_unit()

        self.tile_rects.clear()
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(GRID_RECT.x + x * GRID_CELL, GRID_RECT.y + y * GRID_CELL, GRID_CELL, GRID_CELL)
                self.tile_rects[(x, y)] = rect
                base = (18, 31, 49) if (x + y) % 2 == 0 else (15, 26, 41)
                pygame.draw.rect(self.screen, base, rect)
                pygame.draw.rect(self.screen, (255, 255, 255, 18), rect, 1)

                if (x, y) in self.controller.blocked_tiles:
                    pygame.draw.rect(self.screen, (47, 57, 68), rect.inflate(-18, -18), border_radius=18)
                    pygame.draw.rect(self.screen, (173, 139, 104), rect.inflate(-18, -18), 1, border_radius=18)

                if (x, y) in reachable:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((89, 170, 219, 58))
                    self.screen.blit(overlay, rect.topleft)

        for target_id in basic_targets | special_targets:
            unit = self.controller.get_unit(target_id)
            if unit is None:
                continue
            rect = self.tile_rects[unit.position]
            color = (255, 183, 88) if target_id in basic_targets else (255, 129, 129)
            pygame.draw.rect(self.screen, color, rect.inflate(-8, -8), 3, border_radius=18)

        for unit in self.controller.units:
            if unit.hp <= 0:
                continue
            self._draw_unit(unit, active.id == unit.id if active else False)

        pygame.draw.rect(self.screen, (236, 218, 176), GRID_RECT, 1, border_radius=26)

    def _draw_unit(self, unit, is_active: bool) -> None:
        center = self.unit_visual_positions[unit.id]
        tile_rect = self.tile_rects[unit.position]
        accent = hex_to_rgb(unit.accent)
        pulse = 0.2 + 0.2 * self.hit_flash.get(unit.id, 0.0)

        shadow_rect = pygame.Rect(0, 0, 64, 18)
        shadow_rect.center = (int(center.x), int(center.y + 28))
        pygame.draw.ellipse(self.screen, (0, 0, 0, 90), shadow_rect)

        if is_active:
            pygame.draw.rect(self.screen, (255, 219, 122), tile_rect.inflate(-12, -12), 3, border_radius=18)

        frame_rect = pygame.Rect(0, 0, 74, 74)
        frame_rect.center = (int(center.x), int(center.y - 2))
        pygame.draw.rect(self.screen, mix(accent, (255, 255, 255), pulse), frame_rect, border_radius=22)
        pygame.draw.rect(self.screen, (245, 239, 224), frame_rect, 2, border_radius=22)

        art = self.champion_art.get(unit.id)
        if art is not None:
            portrait = self._masked_art_surface(art, (66, 66), border_radius=18)
            self.screen.blit(portrait, portrait.get_rect(center=frame_rect.center))

        hp_ratio = unit.hp / unit.max_hp
        hp_rect = pygame.Rect(frame_rect.x, frame_rect.y - 14, frame_rect.width, 8)
        pygame.draw.rect(self.screen, (28, 40, 53), hp_rect, border_radius=4)
        pygame.draw.rect(self.screen, (101, 226, 148), (hp_rect.x, hp_rect.y, int(hp_rect.width * hp_ratio), hp_rect.height), border_radius=4)
        pygame.draw.rect(self.screen, (255, 255, 255), hp_rect, 1, border_radius=4)
        if unit.shield > 0:
            self._draw_text(f"보 {unit.shield}", self.font_tiny, (164, 225, 243), (frame_rect.x, frame_rect.bottom + 6))
        if unit.stun_turns > 0:
            self._draw_text("기절", self.font_tiny, (255, 228, 150), (frame_rect.right - 28, frame_rect.bottom + 6))
        self._draw_text(unit.name, self.font_small, (244, 239, 225), (frame_rect.centerx, frame_rect.bottom + 18), center=True)

    def _draw_left_panel(self) -> None:
        active = self.controller.get_active_unit()
        self._draw_text("전술 브리핑", self.font_heading, (244, 239, 225), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 18))
        self._draw_text(self.status_text, self.font_small, (167, 192, 212), (LEFT_PANEL.x + 18, LEFT_PANEL.y + 54))

        info_rect = pygame.Rect(LEFT_PANEL.x + 16, LEFT_PANEL.y + 96, LEFT_PANEL.width - 32, 214)
        pygame.draw.rect(self.screen, (13, 24, 37), info_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), info_rect, 1, border_radius=24)
        if active is not None:
            accent = hex_to_rgb(active.accent)
            portrait_rect = pygame.Rect(info_rect.x + 18, info_rect.y + 18, 92, 92)
            art = self.champion_art.get(active.id)
            pygame.draw.rect(self.screen, accent, portrait_rect, border_radius=24)
            pygame.draw.rect(self.screen, (255, 244, 217), portrait_rect, 1, border_radius=24)
            if art is not None:
                portrait = self._masked_art_surface(art, (84, 84), border_radius=20)
                self.screen.blit(portrait, portrait.get_rect(center=portrait_rect.center))
            self._draw_text(active.name, self.font_heading, (244, 239, 225), (info_rect.x + 128, info_rect.y + 20))
            self._draw_text(active.title, self.font_small, (170, 191, 207), (info_rect.x + 128, info_rect.y + 54))
            self._draw_text(f"{active.role} · 체력 {active.hp}/{active.max_hp}", self.font_small, accent, (info_rect.x + 128, info_rect.y + 82))
            self._draw_text(f"이동 {active.move_range}칸 · 속도 {active.speed}", self.font_small, (206, 215, 222), (info_rect.x + 18, info_rect.y + 126))
            self._draw_text(f"기본기: {active.basic_ability.name}", self.font_small, (223, 206, 164), (info_rect.x + 18, info_rect.y + 154))
            special_label = f"특수기: {active.special_ability.name}"
            cooldown = active.cooldowns[active.special_ability.id]
            if cooldown > 0:
                special_label += f" (CD {cooldown})"
            self._draw_text(special_label, self.font_small, (223, 206, 164), (info_rect.x + 18, info_rect.y + 182))

        guide_rect = pygame.Rect(LEFT_PANEL.x + 16, LEFT_PANEL.y + 330, LEFT_PANEL.width - 32, 280)
        pygame.draw.rect(self.screen, (11, 20, 31), guide_rect, border_radius=24)
        pygame.draw.rect(self.screen, (236, 218, 176), guide_rect, 1, border_radius=24)
        self._draw_text("조작", self.font_ui, (229, 210, 164), (guide_rect.x + 18, guide_rect.y + 18))
        guides = [
            "1. 이동 버튼 후 파란 칸 클릭",
            "2. 기본기 또는 특수기 선택",
            "3. 사거리 안 적을 클릭해 공격",
            "4. 이동과 행동을 모두 쓰면 자동 종료",
            "5. E로 턴 종료, R로 전투 리셋",
        ]
        for index, line in enumerate(guides):
            self._draw_text(line, self.font_small, (201, 213, 221), (guide_rect.x + 18, guide_rect.y + 58 + index * 36))

    def _draw_right_panel(self) -> None:
        self._draw_text("전장 현황", self.font_heading, (244, 239, 225), (RIGHT_PANEL.x + 18, RIGHT_PANEL.y + 18))
        self._draw_text(f"라운드 {self.controller.state.round}", self.font_small, (189, 200, 208), (RIGHT_PANEL.right - 24, RIGHT_PANEL.y + 22), align_right=True)

        blue_header_y = RIGHT_PANEL.y + 62
        self._draw_text("블루 팀", self.font_ui, (108, 192, 235), (RIGHT_PANEL.x + 18, blue_header_y))
        for index, unit in enumerate([unit for unit in self.controller.units if unit.team == "blue"]):
            self._draw_roster_row(unit, RIGHT_PANEL.x + 18, blue_header_y + 34 + index * 64)

        red_header_y = RIGHT_PANEL.y + 286
        self._draw_text("레드 팀", self.font_ui, (237, 129, 111), (RIGHT_PANEL.x + 18, red_header_y))
        for index, unit in enumerate([unit for unit in self.controller.units if unit.team == "red"]):
            self._draw_roster_row(unit, RIGHT_PANEL.x + 18, red_header_y + 34 + index * 64)

        log_rect = pygame.Rect(RIGHT_PANEL.x + 16, RIGHT_PANEL.bottom - 180, RIGHT_PANEL.width - 32, 164)
        pygame.draw.rect(self.screen, (11, 20, 31), log_rect, border_radius=22)
        pygame.draw.rect(self.screen, (236, 218, 176), log_rect, 1, border_radius=22)
        self._draw_text("최근 로그", self.font_ui, (229, 210, 164), (log_rect.x + 16, log_rect.y + 14))
        for index, line in enumerate(self.controller.state.log[:4]):
            self._draw_wrapped_text(line, self.font_small, (210, 220, 227), pygame.Rect(log_rect.x + 16, log_rect.y + 48 + index * 26, log_rect.width - 28, 22), max_lines=1)

    def _draw_roster_row(self, unit, x: int, y: int) -> None:
        row_rect = pygame.Rect(x, y, RIGHT_PANEL.width - 36, 52)
        pygame.draw.rect(self.screen, (15, 26, 39), row_rect, border_radius=16)
        pygame.draw.rect(self.screen, (236, 218, 176), row_rect, 1, border_radius=16)
        accent = hex_to_rgb(unit.accent)
        pygame.draw.circle(self.screen, accent, (row_rect.x + 22, row_rect.y + 26), 10)
        self._draw_text(unit.name, self.font_small, (244, 239, 225), (row_rect.x + 44, row_rect.y + 8))
        self._draw_text(f"{unit.hp}/{unit.max_hp}", self.font_tiny, (176, 201, 219), (row_rect.x + 44, row_rect.y + 28))
        status = []
        if unit.shield > 0:
            status.append(f"보호막 {unit.shield}")
        if unit.stun_turns > 0:
            status.append("기절")
        if unit.hp <= 0:
            status.append("전투불능")
        self._draw_text(" · ".join(status) if status else unit.role, self.font_tiny, accent, (row_rect.right - 12, row_rect.y + 18), align_right=True)

    def _draw_bottom_panel(self) -> None:
        active = self.controller.get_active_unit()
        self.button_rects.pop("move", None)
        self.button_rects.pop("basic", None)
        self.button_rects.pop("special", None)
        self.button_rects.pop("end", None)

        if active is None:
            return

        buttons = [
            ("move", "이동", not active.has_moved and active.team == "blue"),
            ("basic", active.basic_ability.name, not active.has_acted and active.team == "blue"),
            ("special", active.special_ability.name, not active.has_acted and active.cooldowns[active.special_ability.id] == 0 and active.team == "blue"),
            ("end", "턴 종료", active.team == "blue"),
        ]
        start_x = BOTTOM_PANEL.x + 18
        for index, (key, label, enabled) in enumerate(buttons):
            rect = pygame.Rect(start_x + index * 250, BOTTOM_PANEL.y + 18, 220, 56)
            self.button_rects[key] = rect
            fill = (214, 182, 112) if enabled else (70, 80, 92)
            text = (13, 21, 31) if enabled else (177, 187, 196)
            if key == "move" and self.mode == "move":
                fill = (104, 191, 234)
            elif key == "basic" and self.mode == "basic":
                fill = (104, 191, 234)
            elif key == "special" and self.mode == "special":
                fill = (104, 191, 234)
            pygame.draw.rect(self.screen, fill, rect, border_radius=18)
            pygame.draw.rect(self.screen, (255, 244, 217), rect, 1, border_radius=18)
            self._draw_text(label, self.font_ui, text, rect.center, center=True)

        info_x = BOTTOM_PANEL.right - 340
        self._draw_text("현재 턴", self.font_small, (223, 206, 164), (info_x, BOTTOM_PANEL.y + 18))
        self._draw_text(active.name, self.font_heading, (244, 239, 225), (info_x, BOTTOM_PANEL.y + 38))
        if active.team == "blue":
            move_state = "완료" if active.has_moved else "가능"
            action_state = "완료" if active.has_acted else "가능"
            self._draw_text(f"이동 {move_state} · 행동 {action_state}", self.font_small, (184, 205, 221), (info_x, BOTTOM_PANEL.y + 66))
        else:
            self._draw_text("적 AI가 경로와 타겟을 계산 중", self.font_small, (214, 191, 184), (info_x, BOTTOM_PANEL.y + 66))

    def _draw_floaters(self) -> None:
        for floater in self.floaters:
            alpha = int(255 * clamp(floater.lifetime / 0.8, 0.0, 1.0))
            rendered = self.font_ui.render(floater.text, True, floater.color)
            rendered.set_alpha(alpha)
            self.screen.blit(rendered, rendered.get_rect(center=(int(floater.x), int(floater.y))))

    def _draw_winner_overlay(self) -> None:
        if not self.controller.state.winner:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 8, 13, 180))
        self.screen.blit(overlay, (0, 0))
        title = "블루 팀 승리" if self.controller.state.winner == "blue" else "레드 팀 승리"
        self._draw_text(title, self.font_title, (255, 244, 217), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20), center=True)
        self._draw_text("R로 다시 시작하거나 ESC로 종료", self.font_ui, (208, 219, 226), (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 34), center=True)

    def _tile_center(self, tile: tuple[int, int]) -> tuple[int, int]:
        return (
            GRID_RECT.x + tile[0] * GRID_CELL + GRID_CELL // 2,
            GRID_RECT.y + tile[1] * GRID_CELL + GRID_CELL // 2,
        )

    def _tile_from_screen(self, position: tuple[int, int]) -> tuple[int, int] | None:
        if not GRID_RECT.collidepoint(position):
            return None
        x = (position[0] - GRID_RECT.x) // GRID_CELL
        y = (position[1] - GRID_RECT.y) // GRID_CELL
        tile = (int(x), int(y))
        return tile if tile in self.tile_rects else None

    def _unit_at_tile(self, tile: tuple[int, int]):
        for unit in self.controller.units:
            if unit.hp > 0 and unit.position == tile:
                return unit
        return None

    def _masked_art_surface(self, art: pygame.Surface, size: tuple[int, int], *, border_radius: int = 18) -> pygame.Surface:
        scaled = pygame.transform.smoothscale(art, size)
        mask = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=border_radius)
        output = pygame.Surface(size, pygame.SRCALPHA)
        output.blit(scaled, (0, 0))
        output.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return output

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int] | pygame.Vector2,
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
        for index, line in enumerate(lines):
            self.screen.blit(font.render(line, True, color), (rect.x, rect.y + index * font.get_linesize()))

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int, *, max_lines: int | None = None) -> list[str]:
        lines: list[str] = []
        current = ""
        for char in text:
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rift Tactics grid tactics prototype")
    parser.add_argument("--frames", type=int, default=None, help="Run only for a fixed number of frames")
    parser.add_argument("--headless", action="store_true", help="Use a hidden window for smoke tests")
    parser.add_argument("--screenshot", type=str, default=None, help="Save the last rendered frame to a PNG path")
    return parser
