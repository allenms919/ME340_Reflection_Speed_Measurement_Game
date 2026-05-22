# game_screen.py
# ============================================================
# Pygame Screen Layer
# This module focuses on display and user input only.
# ============================================================

from typing import Optional, Tuple

import pygame

import cfg
from game_engine import GameEngine


class Button:
    """
    pygame 화면에서 사용하는 단순 버튼 클래스입니다.
    """

    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font

    def is_hovered(self, mouse_pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(mouse_pos)

    def draw(
        self,
        surface: pygame.Surface,
        mouse_pos: Tuple[int, int],
        active: bool = False,
    ) -> None:
        if active:
            color = cfg.COLOR_BUTTON_ACTIVE
        elif self.is_hovered(mouse_pos):
            color = cfg.COLOR_BUTTON_HOVER
        else:
            color = cfg.COLOR_BUTTON

        pygame.draw.rect(surface, color, self.rect, border_radius=14)

        text_surface = self.font.render(self.text, True, cfg.COLOR_TEXT)
        text_rect = text_surface.get_rect(center=self.rect.center)

        surface.blit(text_surface, text_rect)


class GameScreen:
    """
    pygame 화면과 사용자 입력을 담당합니다.

    이 클래스는 launcher_controller를 직접 사용하지 않습니다.
    게임 로직은 GameEngine에 위임합니다.
    """

    def __init__(self, engine: GameEngine):
        pygame.init()

        self.engine = engine

        self.screen = pygame.display.set_mode(
            (cfg.WINDOW_WIDTH, cfg.WINDOW_HEIGHT)
        )
        pygame.display.set_caption(cfg.WINDOW_TITLE)

        self.clock = pygame.time.Clock()
        self.running = True

        self.font_title = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_TITLE)
        self.font_large = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_LARGE)
        self.font_medium = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_MEDIUM)
        self.font_small = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_SMALL)
        self.font_tiny = pygame.font.SysFont(cfg.FONT_NAME, cfg.FONT_SIZE_TINY)

        self.start_button = Button(
            rect=(cfg.WINDOW_WIDTH // 2 - 120, 330, 240, 70),
            text="START",
            font=self.font_medium,
        )

        self.restart_button = Button(
            rect=(cfg.WINDOW_WIDTH // 2 - 120, 330, 240, 70),
            text="RESTART",
            font=self.font_medium,
        )

        self.difficulty_buttons = {
            "EASY": Button((170, 230, 150, 55), "EASY", self.font_small),
            "NORMAL": Button((375, 230, 150, 55), "NORMAL", self.font_small),
            "HARD": Button((580, 230, 150, 55), "HARD", self.font_small),
        }

    def run(self) -> None:
        """
        pygame main loop를 실행합니다.
        """
        while self.running:
            self.clock.tick(cfg.FPS)

            self._handle_events()

            # 게임 로직 업데이트는 engine에 위임합니다.
            self.engine.update()

            self._draw()

        pygame.quit()

    # ========================================================
    # Event handling
    # ========================================================

    def _handle_events(self) -> None:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(mouse_pos)

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE or key == pygame.K_q:
            self.running = False

        elif key == pygame.K_SPACE:
            if self.engine.state in [
                GameEngine.STATE_MENU,
                GameEngine.STATE_FINISHED,
            ]:
                self.engine.start_game()

        elif key == pygame.K_r:
            self.engine.reset_to_menu()

        elif key == pygame.K_1:
            self.engine.set_difficulty("EASY")

        elif key == pygame.K_2:
            self.engine.set_difficulty("NORMAL")

        elif key == pygame.K_3:
            self.engine.set_difficulty("HARD")

    def _handle_mouse_click(self, mouse_pos: Tuple[int, int]) -> None:
        if self.engine.state == GameEngine.STATE_MENU:
            for difficulty_name, button in self.difficulty_buttons.items():
                if button.is_hovered(mouse_pos):
                    self.engine.set_difficulty(difficulty_name)

            if self.start_button.is_hovered(mouse_pos):
                self.engine.start_game()

        elif self.engine.state == GameEngine.STATE_FINISHED:
            if self.restart_button.is_hovered(mouse_pos):
                self.engine.start_game()

    # ========================================================
    # Draw
    # ========================================================

    def _draw(self) -> None:
        self.screen.fill(cfg.COLOR_BG)

        if self.engine.state == GameEngine.STATE_MENU:
            self._draw_menu()

        elif self.engine.state == GameEngine.STATE_RUNNING:
            self._draw_running()

        elif self.engine.state == GameEngine.STATE_FINISHED:
            self._draw_finished()

        pygame.display.flip()

    def _draw_menu(self) -> None:
        mouse_pos = pygame.mouse.get_pos()

        self._draw_text(
            "ME340 Reaction Launcher",
            self.font_title,
            cfg.COLOR_TEXT,
            center=(cfg.WINDOW_WIDTH // 2, 95),
        )

        self._draw_text(
            "Raspberry Pi: high-level controller  |  Arduino Mega: actuator driver",
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 155),
        )

        self._draw_text(
            "Select difficulty",
            self.font_medium,
            cfg.COLOR_TEXT,
            center=(cfg.WINDOW_WIDTH // 2, 200),
        )

        for difficulty_name, button in self.difficulty_buttons.items():
            button.draw(
                self.screen,
                mouse_pos,
                active=(difficulty_name == self.engine.difficulty_name),
            )

        self.start_button.draw(self.screen, mouse_pos)

        self._draw_text(
            self.engine.status_message,
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 425),
        )

        self._draw_text(
            "Keyboard: 1=Easy, 2=Normal, 3=Hard, Space=Start, Q=Quit",
            self.font_tiny,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 470),
        )

        self._draw_connection_status()

    def _draw_running(self) -> None:
        self._draw_top_bar()

        remaining_time = self.engine.get_remaining_time()
        next_launch_time = self.engine.get_time_until_next_launch()

        self._draw_text(
            f"{remaining_time:04.1f}",
            self.font_title,
            cfg.COLOR_ACCENT,
            center=(cfg.WINDOW_WIDTH // 2, 125),
        )

        self._draw_text(
            "seconds remaining",
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 175),
        )

        self._draw_game_panel()

        if self.engine.current_launcher is not None:
            launcher_text = f"Launcher {self.engine.current_launcher}"
            launcher_color = cfg.COLOR_WARNING
        else:
            launcher_text = "Waiting"
            launcher_color = cfg.COLOR_TEXT_MUTED

        self._draw_text(
            launcher_text,
            self.font_large,
            launcher_color,
            center=(cfg.WINDOW_WIDTH // 2, 285),
        )

        if self.engine.launch_in_progress:
            sub_text = "Command sent to Arduino Mega."
        else:
            sub_text = f"Next launch in {next_launch_time:03.1f} sec"

        self._draw_text(
            sub_text,
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 330),
        )

        self._draw_text(
            self.engine.status_message,
            self.font_tiny,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 365),
        )

        self._draw_text(
            "ESC/Q: Quit    R: Menu",
            self.font_tiny,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 490),
        )

    def _draw_finished(self) -> None:
        mouse_pos = pygame.mouse.get_pos()

        self._draw_text(
            "Game Finished",
            self.font_title,
            cfg.COLOR_TEXT,
            center=(cfg.WINDOW_WIDTH // 2, 105),
        )

        self._draw_text(
            f"Score: {self.engine.score}",
            self.font_large,
            cfg.COLOR_SUCCESS,
            center=(cfg.WINDOW_WIDTH // 2, 190),
        )

        self._draw_text(
            f"Total launcher commands: {self.engine.total_launch_count}",
            self.font_medium,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 245),
        )

        self.restart_button.draw(self.screen, mouse_pos)

        self._draw_text(
            "Space: Restart    R: Menu    Q: Quit",
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 455),
        )

        self._draw_connection_status()

    def _draw_top_bar(self) -> None:
        pygame.draw.rect(
            self.screen,
            cfg.COLOR_PANEL,
            pygame.Rect(0, 0, cfg.WINDOW_WIDTH, 72),
        )

        self._draw_text(
            f"Difficulty: {self.engine.difficulty_name}",
            self.font_small,
            cfg.COLOR_TEXT,
            topleft=(28, 24),
        )

        self._draw_text(
            f"Score: {self.engine.score}",
            self.font_small,
            cfg.COLOR_TEXT,
            topright=(cfg.WINDOW_WIDTH - 28, 24),
        )

    def _draw_game_panel(self) -> None:
        panel_rect = pygame.Rect(150, 215, 600, 190)

        pygame.draw.rect(
            self.screen,
            cfg.COLOR_PANEL,
            panel_rect,
            border_radius=20,
        )

        self._draw_text(
            f"Launch Count: {self.engine.total_launch_count}",
            self.font_small,
            cfg.COLOR_TEXT_MUTED,
            center=(cfg.WINDOW_WIDTH // 2, 395),
        )

    def _draw_connection_status(self) -> None:
        if self.engine.is_hardware_connected():
            text = "Launcher Arduino: Connected"
            color = cfg.COLOR_SUCCESS
        else:
            text = "Launcher Arduino: Not connected"
            color = cfg.COLOR_ERROR

        self._draw_text(
            text,
            self.font_tiny,
            color,
            bottomright=(cfg.WINDOW_WIDTH - 24, cfg.WINDOW_HEIGHT - 18),
        )

    def _draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: Tuple[int, int, int],
        center: Optional[Tuple[int, int]] = None,
        topleft: Optional[Tuple[int, int]] = None,
        topright: Optional[Tuple[int, int]] = None,
        bottomright: Optional[Tuple[int, int]] = None,
    ) -> None:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()

        if center is not None:
            text_rect.center = center
        elif topleft is not None:
            text_rect.topleft = topleft
        elif topright is not None:
            text_rect.topright = topright
        elif bottomright is not None:
            text_rect.bottomright = bottomright
        else:
            text_rect.topleft = (0, 0)

        self.screen.blit(text_surface, text_rect)