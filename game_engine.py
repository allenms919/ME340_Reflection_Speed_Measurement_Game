# game_engine.py
# ============================================================
# ME340 Reaction Test Game — game logic
# ============================================================

import random
import select
import sys
import time
from typing import Dict, Optional

import cfg
from hardware import MegaController, UnoController


class GameEngine:

    def __init__(self, mega: MegaController, uno: UnoController):
        self.mega = mega
        self.uno  = uno

    # ──────────────────────────────────────────────────────────
    # Public: modes
    # ──────────────────────────────────────────────────────────

    def run_round_mode(self) -> None:
        print("\n=== ROUND MODE ===")
        current_level = 1
        fails         = 0
        self._preflight_countdown()

        while True:
            diff = cfg.DIFFICULTY[current_level]
            print(f"\n--- Level {current_level} ({diff['name']}) ---")

            self._fire_level(diff)
            count  = min(self._wait_and_read(), cfg.ROUND_BALLS)
            passed = count >= cfg.ROUND_SUCCESS_MIN
            print(f"  Result: {count}/{cfg.ROUND_BALLS}  {'PASS' if passed else 'FAIL'}")
            self._on_round_result(current_level, count, passed)

            if passed:
                if current_level >= cfg.ROUND_MAX_LEVELS:
                    grade = cfg.ROUND_CLEAR_GRADE
                    print(f"\nGAME CLEAR!  Grade: {grade}")
                    self._on_game_end(grade, cleared=True)
                    if self._ask_ssh("Restart? (y/n): "):
                        current_level = 1
                        fails = 0
                        self._preflight_countdown()
                    else:
                        return
                else:
                    current_level += 1
                    fails = 0
                    if not self._ask_ssh("Continue? (y/n): "):
                        return
                    self._preflight_countdown()

            else:
                fails += 1
                if fails > cfg.ROUND_MAX_FAILS:
                    grade = cfg.ROUND_GRADES.get(current_level, "?")
                    print(f"\nGAME OVER  Level {current_level}  Grade: {grade}")
                    self._on_game_end(grade, cleared=False)
                    if self._ask_ssh("Restart? (y/n): "):
                        current_level = 1
                        fails = 0
                        self._preflight_countdown()
                    else:
                        return
                else:
                    print(f"  Fails: {fails}/{cfg.ROUND_MAX_FAILS}")
                    if not self._ask_ssh("Retry? (y/n): "):
                        return
                    self._preflight_countdown()

    def run_score_mode(self) -> None:
        print("\n=== SCORE MODE ===")

        while True:
            diff = cfg.DIFFICULTY[4]
            print(f"\n--- Score Mode ({cfg.SCORE_BALLS} balls) ---")

            self._fire_level(diff, total_balls=cfg.SCORE_BALLS)
            count = min(self._wait_and_read(), cfg.SCORE_BALLS)
            score = count * cfg.SCORE_PER_BALL

            max_score = cfg.SCORE_BALLS * cfg.SCORE_PER_BALL
            print(f"\n  Score: {score}/{max_score}  ({count}/{cfg.SCORE_BALLS} balls)")
            self._on_score_result(count, score)

            if not self._ask_ssh("Retry? (y/n): "):
                return

    def run_train_mode(self) -> None:
        print("\n=== TRAIN MODE ===")

        while True:
            diff_num = self._ask_difficulty()
            diff     = cfg.DIFFICULTY[diff_num]
            print(f"\n--- Train Level {diff_num} ({diff['name']}) ---")
            self._preflight_countdown()

            self._fire_level(diff)
            count  = min(self._wait_and_read(), cfg.ROUND_BALLS)
            passed = count >= cfg.ROUND_SUCCESS_MIN
            print(f"  Result: {count}/{cfg.ROUND_BALLS}")
            self._on_round_result(diff_num, count, passed)

            if not self._ask_ssh("Retry? (y/n): "):
                return

    def run_dual_mode(self) -> None:
        print("\n=== DUAL MODE ===")
        print("Player B is questioner. Player A plays.")

        a_count = self._play_dual_round(player="A", questioner="B")
        print(f"\n  Player A: {a_count}/{cfg.DUAL_BALLS}")
        self._on_dual_a_result(a_count)

        if not self._ask_ssh("Next player? (y/n): "):
            self._on_dual_final(a_count, None)
            self._ask_ssh("Exit? (y/n): ")
            return

        print("\nPlayer A is questioner. Player B plays.")
        b_count = self._play_dual_round(player="B", questioner="A")
        print(f"\n  Player A: {a_count}/{cfg.DUAL_BALLS}")
        print(f"  Player B: {b_count}/{cfg.DUAL_BALLS}")

        self._on_dual_final(a_count, b_count)
        self._ask_ssh("Exit? (y/n): ")

    # ──────────────────────────────────────────────────────────
    # Internal: firing
    # ──────────────────────────────────────────────────────────

    def _fire_level(self, diff: Dict, total_balls: int = None) -> None:
        if total_balls is None:
            total_balls = cfg.ROUND_BALLS
        self.uno.reset_count()
        time.sleep(0.5)                               # wait for RESET to be processed
        self._count_baseline = self.uno.read_count_fast()  # baseline (should be 0)
        shot = diff["shot"]
        if shot == "single":
            self._fire_single(diff, total_balls)
        elif shot == "double":
            self._fire_double(diff, total_balls)
        else:
            self._fire_random(diff, total_balls)

    def _fire_single(self, diff: Dict, total_balls: int) -> None:
        mode = diff["shot_mode"]
        for _ in range(total_balls):
            self._do_interval(diff)
            launcher = random.randint(1, 4)
            print(f"    → {launcher} ({mode})")
            self.mega.fire([launcher], mode)

    def _fire_double(self, diff: Dict, total_balls: int) -> None:
        mode = diff["shot_mode"]
        for _ in range(total_balls // 2):
            self._do_interval(diff)
            launchers = random.sample(range(1, 5), 2)
            print(f"    → {launchers} ({mode})")
            self.mega.fire(launchers, mode)

    def _fire_random(self, diff: Dict, total_balls: int) -> None:
        balls_left = total_balls
        while balls_left > 0:
            interval = random.choice(diff["interval_choices"])
            print(f"    wait {interval}s")
            time.sleep(interval)

            count = 1 if balls_left == 1 else random.choice([1, 2])
            mode  = random.choice(["fall", "shoot"])

            if count == 1:
                launcher = random.randint(1, 4)
                print(f"    → {launcher} ({mode})")
                self.mega.fire([launcher], mode)
            else:
                launchers = random.sample(range(1, 5), 2)
                print(f"    → {launchers} ({mode})")
                self.mega.fire(launchers, mode)

            balls_left -= count

    def _do_interval(self, diff: Dict) -> None:
        interval = diff["interval_sec"]
        print(f"    wait {interval}s")
        time.sleep(interval)

    # ──────────────────────────────────────────────────────────
    # Internal: result / countdown
    # ──────────────────────────────────────────────────────────

    def _wait_and_read(self) -> int:
        print(f"    Waiting {cfg.POST_FIRE_WAIT_SEC}s...")
        time.sleep(cfg.POST_FIRE_WAIT_SEC)
        return self._read_delta()

    def _read_delta(self) -> int:
        """Read current count and subtract baseline set in _fire_level()."""
        raw = self.uno.read_ball_count()
        if raw < 0:
            print("    WARNING: could not read; treating as 0")
            raw = 0
        baseline = getattr(self, "_count_baseline", 0)
        count = max(0, raw - baseline)
        print(f"    raw={raw}  baseline={baseline}  delta={count}")
        return count

    def _preflight_countdown(self) -> None:
        for i in range(3, 0, -1):
            print(f"    Firing in {i}...")
            time.sleep(1.0)

    # ──────────────────────────────────────────────────────────
    # Internal: dual mode
    # ──────────────────────────────────────────────────────────

    def _play_dual_round(self, player: str, questioner: str) -> int:
        self.uno.reset_count()
        balls_fired    = 0
        last_fire_time = 0.0

        print(f"  [{questioner}] Fire for Player {player}.")
        print(f"  Enter 1-4 to fire. 20s idle = game over.\n")

        while balls_fired < cfg.DUAL_BALLS:
            launcher = self._ask_launcher(questioner, timeout=cfg.DUAL_IDLE_TIMEOUT)
            if launcher is None:
                print("  Timeout. Round over.")
                break

            elapsed = time.time() - last_fire_time
            if last_fire_time and elapsed < cfg.DUAL_MIN_INTERVAL:
                time.sleep(cfg.DUAL_MIN_INTERVAL - elapsed)

            self.mega.fire([launcher], "fall")
            last_fire_time = time.time()
            balls_fired   += 1
            print(f"  Fired {launcher}  ({balls_fired}/{cfg.DUAL_BALLS})")

        self._on_dual_round_end()
        time.sleep(cfg.POST_FIRE_WAIT_SEC)
        count = self.uno.read_ball_count()
        if count < 0:
            count = 0
        return min(count, cfg.DUAL_BALLS)

    # ──────────────────────────────────────────────────────────
    # Hooks: overridden by GUI engine to update display
    # ──────────────────────────────────────────────────────────

    def _on_round_result(self, level: int, count: int, passed: bool) -> None:
        del level, count, passed

    def _on_game_end(self, grade: str, cleared: bool) -> None:
        del grade, cleared

    def _on_score_result(self, count: int, score: int) -> None:
        del count, score

    def _on_dual_a_result(self, a_count: int) -> None:
        del a_count

    def _on_dual_final(self, a_count: int, b_count: Optional[int]) -> None:
        del a_count, b_count

    def _on_dual_round_end(self) -> None:
        pass

    # ──────────────────────────────────────────────────────────
    # Input helpers
    # ──────────────────────────────────────────────────────────

    def _ask_ssh(self, prompt: str) -> bool:
        try:
            return input(prompt).strip().lower() == "y"
        except (EOFError, KeyboardInterrupt):
            return False

    def _ask_difficulty(self) -> int:
        while True:
            try:
                raw = input("Level (1-5): ").strip()
                n = int(raw)
                if n in cfg.DIFFICULTY:
                    return n
            except (ValueError, EOFError, KeyboardInterrupt):
                pass
            print("  Enter 1-5.")

    def _ask_launcher(self, questioner: str, timeout: float = 20.0) -> Optional[int]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            print(f"  [{questioner}] launcher (1-4): ", end="", flush=True)
            r, _, _ = select.select([sys.stdin], [], [], remaining)
            if not r:
                return None
            line = sys.stdin.readline().strip()
            try:
                n = int(line)
                if 1 <= n <= 4:
                    return n
            except ValueError:
                pass
        return None
