# game_engine.py
# ============================================================
# Game Engine
# Game logic layer separated from pygame screen layer
# ============================================================

import random
import threading
import time
from dataclasses import dataclass
from typing import Optional

import cfg
from hardware import LauncherController


@dataclass
class LaunchEvent:
    """
    가장 최근 launcher 작동 결과를 저장하는 데이터 구조입니다.
    """

    launcher_number: int
    success: bool
    message: str
    timestamp: float


class GameEngine:
    """
    게임 로직을 담당하는 클래스입니다.

    이 클래스는 pygame 화면을 알지 않습니다.
    즉, 화면을 그리거나 버튼을 처리하지 않습니다.

    담당 기능:
    1. 게임 시작/종료
    2. 난이도 관리
    3. 랜덤 시간 간격 계산
    4. 랜덤 launcher 선택
    5. launcher_controller 호출
    6. score, launch count, 상태 메시지 관리
    """

    STATE_MENU = "MENU"
    STATE_RUNNING = "RUNNING"
    STATE_FINISHED = "FINISHED"

    def __init__(self, launcher_controller: LauncherController):
        self.launcher_controller = launcher_controller

        self.state = self.STATE_MENU
        self.difficulty_name = cfg.DEFAULT_DIFFICULTY

        self.game_start_time = 0.0
        self.game_end_time = 0.0
        self.next_launch_time = 0.0

        self.score = 0
        self.total_launch_count = 0

        self.current_launcher: Optional[int] = None
        self.launch_in_progress = False

        self.status_message = "Select difficulty and press START."

        self.last_launch_event: Optional[LaunchEvent] = None

        self._lock = threading.Lock()
        self._pending_launch_event: Optional[LaunchEvent] = None

    # ========================================================
    # Public API used by game_screen.py
    # ========================================================

    def set_difficulty(self, difficulty_name: str) -> None:
        """
        난이도를 설정합니다.
        """
        if difficulty_name not in cfg.DIFFICULTIES:
            raise ValueError(f"Unknown difficulty: {difficulty_name}")

        if self.state == self.STATE_RUNNING:
            return

        self.difficulty_name = difficulty_name
        self.status_message = f"Difficulty set to {difficulty_name}."

    def start_game(self) -> None:
        """
        게임을 시작합니다.
        """
        self.state = self.STATE_RUNNING

        self.game_start_time = time.time()
        self.game_end_time = self.game_start_time + cfg.GAME_DURATION_SEC

        self.score = 0
        self.total_launch_count = 0

        self.current_launcher = None
        self.launch_in_progress = False

        self.last_launch_event = None
        self._pending_launch_event = None

        self.status_message = "Game started. Waiting for first launcher."

        self._schedule_next_launch()

    def finish_game(self) -> None:
        """
        게임을 종료합니다.
        """
        self.state = self.STATE_FINISHED
        self.current_launcher = None
        self.launch_in_progress = False
        self.status_message = "Game finished."

    def reset_to_menu(self) -> None:
        """
        메뉴 상태로 돌아갑니다.
        """
        self.state = self.STATE_MENU

        self.score = 0
        self.total_launch_count = 0

        self.current_launcher = None
        self.launch_in_progress = False

        self.last_launch_event = None
        self._pending_launch_event = None

        self.status_message = "Select difficulty and press START."

    def update(self) -> None:
        """
        게임 상태를 한 프레임 업데이트합니다.

        game_screen.py의 pygame loop에서 매 frame 호출됩니다.
        """
        self._consume_pending_launch_event()

        if self.state != self.STATE_RUNNING:
            return

        now = time.time()

        if now >= self.game_end_time:
            self.finish_game()
            return

        if (not self.launch_in_progress) and now >= self.next_launch_time:
            self._start_random_launcher()

    def get_remaining_time(self) -> float:
        """
        남은 게임 시간을 반환합니다.
        """
        if self.state != self.STATE_RUNNING:
            return 0.0

        return max(0.0, self.game_end_time - time.time())

    def get_time_until_next_launch(self) -> float:
        """
        다음 launcher 작동까지 남은 시간을 반환합니다.
        """
        if self.state != self.STATE_RUNNING or self.launch_in_progress:
            return 0.0

        return max(0.0, self.next_launch_time - time.time())

    def is_hardware_connected(self) -> bool:
        """
        launcher controller 연결 상태를 반환합니다.
        """
        return self.launcher_controller.is_connected

    # ========================================================
    # Internal game logic
    # ========================================================

    def _schedule_next_launch(self) -> None:
        """
        난이도 설정에 따라 다음 launcher 작동 시간을 랜덤하게 예약합니다.
        """
        difficulty = cfg.DIFFICULTIES[self.difficulty_name]

        interval = random.uniform(
            difficulty["min_interval_sec"],
            difficulty["max_interval_sec"],
        )

        self.next_launch_time = time.time() + interval

    def _start_random_launcher(self) -> None:
        """
        1~4번 launcher 중 하나를 랜덤 선택하고 비동기적으로 작동시킵니다.
        """
        launcher_number = random.randint(1, cfg.LAUNCHER_COUNT)

        self.current_launcher = launcher_number
        self.launch_in_progress = True
        self.total_launch_count += 1

        pin_pair = cfg.LAUNCHER_PIN_MAP[launcher_number]

        self.status_message = (
            f"Launcher {launcher_number} firing "
            f"(D{pin_pair[0]}, D{pin_pair[1]})."
        )

        worker = threading.Thread(
            target=self._launch_worker,
            args=(launcher_number,),
            daemon=True,
        )
        worker.start()

    def _launch_worker(self, launcher_number: int) -> None:
        """
        실제 launcher command 전송은 background thread에서 실행합니다.

        이 구조를 쓰는 이유:
        serial read/write 중 pygame 화면이 멈추는 것을 방지하기 위해서입니다.
        """
        try:
            responses = self.launcher_controller.activate_launcher(launcher_number)

            if responses:
                message = responses[-1]
            else:
                message = f"Launcher {launcher_number} command sent."

            event = LaunchEvent(
                launcher_number=launcher_number,
                success=True,
                message=message,
                timestamp=time.time(),
            )

        except Exception as exc:
            event = LaunchEvent(
                launcher_number=launcher_number,
                success=False,
                message=str(exc),
                timestamp=time.time(),
            )

        with self._lock:
            self._pending_launch_event = event

    def _consume_pending_launch_event(self) -> None:
        """
        background thread에서 생성된 launcher 결과를 main game loop에서 반영합니다.
        """
        with self._lock:
            event = self._pending_launch_event
            self._pending_launch_event = None

        if event is None:
            return

        self.last_launch_event = event
        self.current_launcher = None
        self.launch_in_progress = False

        if event.success:
            self.score += 1
            self.status_message = (
                f"Launcher {event.launcher_number} done. "
                f"Next launcher will fire soon."
            )
        else:
            self.status_message = f"Launcher error: {event.message}"

        if self.state == self.STATE_RUNNING:
            self._schedule_next_launch()