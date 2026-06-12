# main.py
# ============================================================
# ME340 Reaction Test Game — entry point
# Run: python3 main.py        → SSH mode (RPi + hardware)
#      python3 main.py --gui  → GUI mode (simulation window)
# ============================================================

import sys
import cfg
from hardware import MegaController, UnoController
from game_engine import GameEngine

MODES = {
    "1": ("round", "Round mode  (L1→L2→L3→L4→L5, grade system)"),
    "2": ("score", "Score mode  (20 balls, 100 pts max)"),
    "3": ("train", "Train mode  (choose level each round)"),
    "4": ("dual",  "Dual mode   (questioner vs player)"),
}


def main() -> None:
    print("=" * 42)
    print("   ME340 Reaction Test Game")
    print("=" * 42)
    if cfg.SIMULATION_MODE:
        print("   [SIMULATION MODE]")
    print()

    print("Connecting to Arduino Mega...")
    mega = MegaController()

    print("Connecting to Arduino Uno...")
    uno = UnoController()

    if not cfg.SIMULATION_MODE:
        if not mega.is_connected:
            print(f"ERROR: Mega not found on {cfg.LAUNCHER_SERIAL_PORT}")
            sys.exit(1)
        if not uno.is_connected:
            print(f"ERROR: Uno not found on {cfg.DETECTOR_SERIAL_PORT}")
            mega.close()
            sys.exit(1)
    print()

    for key, (_, desc) in MODES.items():
        print(f"  {key}: {desc}")
    print()

    mode = None
    while mode is None:
        try:
            raw = input("Select mode (1/2/3/4): ").strip()
        except (EOFError, KeyboardInterrupt):
            _shutdown(mega, uno)
            sys.exit(0)
        if raw in MODES:
            mode = MODES[raw][0]
        else:
            print("  Please enter 1, 2, 3, or 4.")

    engine = GameEngine(mega, uno)
    try:
        if mode == "round":
            engine.run_round_mode()
        elif mode == "score":
            engine.run_score_mode()
        elif mode == "train":
            engine.run_train_mode()
        elif mode == "dual":
            engine.run_dual_mode()
    except KeyboardInterrupt:
        print("\nInterrupted by operator.")
    finally:
        _shutdown(mega, uno)


def _shutdown(mega: MegaController, uno: UnoController) -> None:
    mega.close()
    uno.close()
    print("Shutdown complete.")


if __name__ == "__main__":
    if "--gui" in sys.argv:
        from game_screen import GameScreen
        GameScreen().run()
    else:
        main()
