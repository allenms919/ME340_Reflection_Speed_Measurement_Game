# main.py
# ============================================================
# ME340 Reaction Launcher Game
# Program Entry Point
# ============================================================

from hardware import LauncherController
from game_engine import GameEngine
from game_screen import GameScreen


def main() -> None:
    launcher_controller = None

    try:
        # 1. 하드웨어 controller 생성
        launcher_controller = LauncherController()

        # 2. 게임 로직 engine 생성
        engine = GameEngine(
            launcher_controller=launcher_controller,
        )

        # 3. 화면 layer 생성 및 실행
        screen = GameScreen(
            engine=engine,
        )

        screen.run()

    finally:
        if launcher_controller is not None:
            launcher_controller.close()


if __name__ == "__main__":
    main()