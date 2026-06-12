# game_screen.py
# ============================================================
# ME340 Reaction Test Game — pygame UI
# Run: python3 main.py --gui
# ============================================================

import queue
import threading
import random
import time

import pygame

import cfg
from game_engine import GameEngine
from hardware import MegaController, UnoController


# ─────────────────────────────────────────────────────────────
# Colors
# ─────────────────────────────────────────────────────────────

C_BG       = (14, 14, 26)
C_PANEL    = (26, 26, 46)
C_LAUNCHER = (40, 42, 70)
C_FIRE     = (255, 195, 40)
C_BALL     = (230, 88, 36)
C_BALL_HI  = (255, 160, 80)
C_TEXT     = (208, 212, 222)
C_DIM      = (85, 90, 110)
C_ACCENT   = (76, 158, 252)
C_SUCCESS  = (68, 208, 68)
C_WARN     = (255, 172, 36)
C_DANGER   = (212, 62, 62)

# ─────────────────────────────────────────────────────────────
# Layout constants
# ─────────────────────────────────────────────────────────────

W, H = 900, 580

L_XS       = [150, 350, 550, 750]
L_TOP      = 62
L_BTM      = 215
L_W        = 66

BALL_R     = 13
BALL_SPAWN = L_BTM + BALL_R + 2
BALL_LAND  = 390

STATUS_CY  = 310
INPUT_Y    = 468


# ─────────────────────────────────────────────────────────────
# Ball animation
# ─────────────────────────────────────────────────────────────

class Ball:
    def __init__(self, launcher_idx: int):
        self.x  = float(L_XS[launcher_idx])
        self.y  = float(BALL_SPAWN)
        self.vy = 2.8

    def update(self) -> bool:
        self.y  += self.vy
        self.vy += 0.20
        return self.y < BALL_LAND

    def draw(self, surf):
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surf, C_BALL,    (ix, iy),     BALL_R)
        pygame.draw.circle(surf, C_BALL_HI, (ix-4, iy-4), BALL_R // 3)


# ─────────────────────────────────────────────────────────────
# Shared state
# ─────────────────────────────────────────────────────────────

class GameState:
    def __init__(self):
        self.lock               = threading.Lock()
        self.screen             = "menu"   # "menu" | "game"
        self.mode               = ""
        self.active_launchers   : set  = set()
        self.pending_spawns     : list = []
        # status lines
        self.line0              = ""
        self.line1              = ""
        # input prompts
        self.waiting_input      = False
        self.selecting_diff     = False
        self.selecting_launcher = False   # dual mode questioner
        self.questioner         = ""      # "A" or "B"
        self.prompt             = ""
        # round/train result (set by _on_round_result)
        self.round_result       = None    # None | {"count": int, "total": int, "passed": bool, "level": int}
        # dual final result
        self.dual_result        = None    # None | {"a": int, "b": int | None}


# ─────────────────────────────────────────────────────────────
# GUI hardware stubs
# ─────────────────────────────────────────────────────────────

class _GUIMega:
    is_connected = True

    def __init__(self, st: GameState):
        self.st = st

    def fire(self, launcher_numbers: list, mode: str = "fall") -> None:
        print(f"    [GUI] fire {launcher_numbers} ({mode})")
        with self.st.lock:
            self.st.active_launchers = set(launcher_numbers)
            self.st.pending_spawns.extend(launcher_numbers)
        time.sleep(0.13)
        with self.st.lock:
            self.st.active_launchers = set()

    def close(self) -> None: pass


class _GUIUno:
    is_connected = True

    def reset_count(self) -> None: pass

    def read_count_fast(self) -> int: return 0

    def read_ball_count(self) -> int:
        n = random.randint(0, cfg.SCORE_BALLS)   # score mode 기준 상한
        print(f"    [GUI] ball count: {n}")
        return n

    def close(self) -> None: pass


# ─────────────────────────────────────────────────────────────
# Real hardware wrapper
# ─────────────────────────────────────────────────────────────

class _RealMega(MegaController):
    def __init__(self, st: GameState):
        super().__init__()
        self.st = st

    def fire(self, launcher_numbers: list, mode: str = "fall") -> None:
        with self.st.lock:
            self.st.active_launchers = set(launcher_numbers)
            self.st.pending_spawns.extend(launcher_numbers)
        super().fire(launcher_numbers, mode)
        with self.st.lock:
            self.st.active_launchers = set()


# ─────────────────────────────────────────────────────────────
# GUI game engine
# ─────────────────────────────────────────────────────────────

class _GUIEngine(GameEngine):
    def __init__(self, st: GameState):
        if cfg.SIMULATION_MODE:
            mega = _GUIMega(st)
            uno  = _GUIUno()
        else:
            mega = _RealMega(st)
            uno  = UnoController()
        super().__init__(mega, uno)
        self.st = st
        self.q  : queue.Queue = queue.Queue()

    def _set(self, l0: str, l1: str = "") -> None:
        with self.st.lock:
            self.st.line0 = l0
            self.st.line1 = l1

    # ── Display overrides ─────────────────────────────────────

    def _preflight_countdown(self) -> None:
        with self.st.lock:
            self.st.round_result = None
        for i in range(3, 0, -1):
            self._set("Starting in", str(i))
            print(f"    Starting in {i}...")
            time.sleep(1.0)
        self._set("", "")

    def _wait_and_read(self) -> int:
        for i in range(int(cfg.POST_FIRE_WAIT_SEC), 0, -1):
            self._set("Reading...", str(i))
            print(f"    {i}...")
            time.sleep(1.0)
        self._set("", "")
        return self._read_delta()

    def _fire_level(self, diff, total_balls=None) -> None:
        with self.st.lock:
            self.st.round_result = None
        self._set("Firing...", "")
        super()._fire_level(diff, total_balls)

    # ── Result hooks ──────────────────────────────────────────

    def _on_round_result(self, level: int, count: int, passed: bool) -> None:
        with self.st.lock:
            self.st.round_result = {
                "count":  count,
                "total":  cfg.ROUND_BALLS,
                "passed": passed,
                "level":  level,
            }
        self._set("", "")

    def _on_game_end(self, grade: str, cleared: bool) -> None:
        with self.st.lock:
            self.st.round_result = None
        if cleared:
            self._set("GAME CLEAR!", f"Grade: {grade}")
        else:
            self._set("GAME OVER", f"Grade: {grade}")

    def _on_score_result(self, count: int, score: int) -> None:
        max_s = cfg.SCORE_BALLS * cfg.SCORE_PER_BALL
        self._set(f"Score: {score}/{max_s}", f"{count}/{cfg.SCORE_BALLS} balls")

    def _on_dual_a_result(self, a_count: int) -> None:
        self._set(f"Player A: {a_count}/{cfg.DUAL_BALLS}", "")

    def _on_dual_final(self, a_count: int, b_count) -> None:
        with self.st.lock:
            self.st.dual_result = {"a": a_count, "b": b_count}

    def _on_dual_round_end(self) -> None:
        with self.st.lock:
            self.st.selecting_launcher = False
            self.st.questioner         = ""

    # ── Input overrides ───────────────────────────────────────

    def _ask_ssh(self, prompt: str) -> bool:
        with self.st.lock:
            self.st.prompt        = prompt
            self.st.waiting_input = True
        result = self.q.get()
        with self.st.lock:
            self.st.prompt        = ""
            self.st.waiting_input = False
        return result

    def _ask_difficulty(self) -> int:
        with self.st.lock:
            self.st.selecting_diff = True
            self.st.prompt         = "Choose level:"
        result = self.q.get()
        with self.st.lock:
            self.st.selecting_diff = False
            self.st.prompt         = ""
        return result

    def _ask_launcher(self, questioner: str, timeout: float = 20.0) -> int | None:
        with self.st.lock:
            self.st.selecting_launcher = True
            self.st.questioner         = questioner
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None


# ─────────────────────────────────────────────────────────────
# Button helper
# ─────────────────────────────────────────────────────────────

class _Btn:
    def __init__(self, rect, label, font, cn=C_PANEL, ch=C_ACCENT, ct=C_TEXT):
        self.r  = pygame.Rect(rect)
        self.lb = label
        self.fn = font
        self.cn, self.ch, self.ct = cn, ch, ct

    def draw(self, surf, mp):
        c = self.ch if self.r.collidepoint(mp) else self.cn
        pygame.draw.rect(surf, c, self.r, border_radius=10)
        t = self.fn.render(self.lb, True, self.ct)
        surf.blit(t, t.get_rect(center=self.r.center))

    def hit(self, mp, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN
                and ev.button == 1
                and self.r.collidepoint(mp))


# ─────────────────────────────────────────────────────────────
# Main screen
# ─────────────────────────────────────────────────────────────

class GameScreen:

    def __init__(self):
        pygame.init()
        self._fullscreen  = False
        self._screen_surf = pygame.display.set_mode((W, H))
        self.surf         = pygame.Surface((W, H))
        pygame.display.set_caption("REFLECTION SPEED MEASUREMENT GAME")
        self.clock = pygame.time.Clock()
        self.alive = True

        self.st    = GameState()
        self.eng   = _GUIEngine(self.st)
        self.balls : list[Ball] = []

        F = pygame.font.SysFont
        self.fT  = F("monospace", 40, bold=True)
        self.fL  = F("monospace", 27, bold=True)
        self.fM  = F("monospace", 21)
        self.fS  = F("monospace", 16)
        self.fX  = F("monospace", 13)
        self.fLN = F("monospace", 30, bold=True)

        self._build_buttons()

    def _build_buttons(self):
        cx, bw, bh = W // 2, 235, 52

        self.menu_btns = [
            _Btn((cx - bw//2, 160, bw, bh), "1   Round Mode", self.fM),
            _Btn((cx - bw//2, 222, bw, bh), "2   Score Mode", self.fM),
            _Btn((cx - bw//2, 284, bw, bh), "3   Train Mode", self.fM),
            _Btn((cx - bw//2, 346, bw, bh), "4   Dual Mode",  self.fM),
        ]

        by = INPUT_Y + 32
        self.yes_btn = _Btn((cx - 122, by, 108, 44), "Y   Yes", self.fM,
                            (22, 62, 22), (42, 138, 42))
        self.no_btn  = _Btn((cx + 14,  by, 108, 44), "N   No",  self.fM,
                            (68, 22, 22), (138, 42, 42))

        # 5 difficulty buttons
        dw, dh, gap = 128, 44, 8
        tw  = 5 * dw + 4 * gap
        dx0 = (W - tw) // 2
        self.diff_btns = [
            _Btn((dx0 + i * (dw + gap), INPUT_Y + 32, dw, dh),
                 f"{i+1} {cfg.DIFFICULTY[i+1]['name']}", self.fS)
            for i in range(5)
        ]

        # Launcher buttons for dual mode (questioner)
        lw, lh = 120, 52
        lx0 = (W - (4 * lw + 3 * gap)) // 2
        self.launcher_btns = [
            _Btn((lx0 + i * (lw + gap), INPUT_Y + 32, lw, lh),
                 f"Launcher {i+1}", self.fS, cn=(34, 42, 70), ch=C_ACCENT)
            for i in range(4)
        ]

    # ─────────────────────────────────────────────────────────
    # Fullscreen
    # ─────────────────────────────────────────────────────────

    def _toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._screen_surf = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self._screen_surf = pygame.display.set_mode((W, H))

    def _canvas_mouse(self):
        mx, my = pygame.mouse.get_pos()
        if not self._fullscreen:
            return mx, my
        sw, sh = self._screen_surf.get_size()
        scale = min(sw / W, sh / H)
        ox = (sw - W * scale) / 2
        oy = (sh - H * scale) / 2
        return (mx - ox) / scale, (my - oy) / scale

    # ─────────────────────────────────────────────────────────
    # Run
    # ─────────────────────────────────────────────────────────

    def run(self) -> None:
        while self.alive:
            self.clock.tick(60)
            evs = pygame.event.get()
            mp  = self._canvas_mouse()
            self._events(evs, mp)
            self._update()
            self._draw(mp)
        pygame.quit()

    # ─────────────────────────────────────────────────────────
    # Events
    # ─────────────────────────────────────────────────────────

    def _events(self, evs, mp):
        for ev in evs:
            if ev.type == pygame.QUIT:
                self.alive = False
            elif ev.type == pygame.KEYDOWN:
                self._key(ev.key)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                self._click(mp, ev)

    def _key(self, k):
        if k == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if k == pygame.K_ESCAPE:
            if self._fullscreen:
                self._toggle_fullscreen()
            else:
                self.alive = False
            return
        if k == pygame.K_q:
            self.alive = False
            return

        with self.st.lock:
            scr = self.st.screen
            wi  = self.st.waiting_input
            sd  = self.st.selecting_diff
            sl  = self.st.selecting_launcher

        if scr == "menu":
            m = {pygame.K_1: "round", pygame.K_2: "score",
                 pygame.K_3: "train",  pygame.K_4: "dual"}
            if k in m: self._start(m[k])

        elif sl:
            d = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 4}
            if k in d: self.eng.q.put(d[k])

        elif wi:
            if k == pygame.K_y: self.eng.q.put(True)
            elif k == pygame.K_n: self.eng.q.put(False)

        elif sd:
            d = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
                 pygame.K_4: 4, pygame.K_5: 5}
            if k in d: self.eng.q.put(d[k])

    def _click(self, mp, ev):
        with self.st.lock:
            scr = self.st.screen
            wi  = self.st.waiting_input
            sd  = self.st.selecting_diff
            sl  = self.st.selecting_launcher

        if scr == "menu":
            for i, b in enumerate(self.menu_btns):
                if b.hit(mp, ev):
                    self._start(["round", "score", "train", "dual"][i])

        elif sl:
            for i, b in enumerate(self.launcher_btns):
                if b.hit(mp, ev): self.eng.q.put(i + 1)

        elif wi:
            if self.yes_btn.hit(mp, ev): self.eng.q.put(True)
            elif self.no_btn.hit(mp, ev): self.eng.q.put(False)

        elif sd:
            for i, b in enumerate(self.diff_btns):
                if b.hit(mp, ev): self.eng.q.put(i + 1)

    def _start(self, mode: str):
        with self.st.lock:
            self.st.screen       = "game"
            self.st.mode         = mode
            self.st.line0        = ""
            self.st.line1        = ""
            self.st.round_result = None
            self.st.dual_result  = None
        self.balls.clear()

        fn = {
            "round": self.eng.run_round_mode,
            "score": self.eng.run_score_mode,
            "train": self.eng.run_train_mode,
            "dual":  self.eng.run_dual_mode,
        }[mode]

        def _run():
            try:
                fn()
            except Exception:
                import traceback; traceback.print_exc()
            finally:
                with self.st.lock:
                    self.st.screen       = "menu"
                    self.st.line0        = ""
                    self.st.line1        = ""
                    self.st.round_result = None
                    self.st.dual_result  = None

        threading.Thread(target=_run, daemon=True).start()

    # ─────────────────────────────────────────────────────────
    # Update
    # ─────────────────────────────────────────────────────────

    def _update(self):
        with self.st.lock:
            spawns = self.st.pending_spawns.copy()
            self.st.pending_spawns.clear()
        for n in spawns:
            self.balls.append(Ball(n - 1))
        self.balls = [b for b in self.balls if b.update()]

    # ─────────────────────────────────────────────────────────
    # Draw
    # ─────────────────────────────────────────────────────────

    def _draw(self, mp):
        self.surf.fill(C_BG)

        with self.st.lock:
            scr  = self.st.screen
            mode = self.st.mode
            act  = self.st.active_launchers.copy()
            l0   = self.st.line0
            l1   = self.st.line1
            rr   = self.st.round_result
            wi   = self.st.waiting_input
            sd   = self.st.selecting_diff
            sl   = self.st.selecting_launcher
            qr   = self.st.questioner
            prm  = self.st.prompt
            dr   = self.st.dual_result

        if scr == "menu":
            self._draw_menu(mp)
        elif dr is not None:
            self._draw_dual_result(dr, wi, mp, prm)
        else:
            self._draw_top(mode)
            self._draw_launchers(act)
            for b in self.balls:
                b.draw(self.surf)
            self._draw_status(l0, l1, act, rr)

            if wi:
                self._draw_yn(mp, prm)
            elif sl:
                self._draw_launcher_select(mp, qr)
            elif sd:
                self._draw_diff(mp)
            else:
                self._t("Q: Quit", self.fX, C_DIM, br=(W-12, H-8))

        sw, sh = self._screen_surf.get_size()
        if self._fullscreen:
            scale = min(sw / W, sh / H)
            nw, nh = int(W * scale), int(H * scale)
            scaled = pygame.transform.smoothscale(self.surf, (nw, nh))
            self._screen_surf.fill((0, 0, 0))
            self._screen_surf.blit(scaled, ((sw - nw) // 2, (sh - nh) // 2))
        else:
            self._screen_surf.blit(self.surf, (0, 0))
        pygame.display.flip()

    # ── Menu ──────────────────────────────────────────────────

    def _draw_menu(self, mp):
        self._t("REFLECTION SPEED MEASUREMENT GAME", self.fL, C_TEXT, c=(W//2, 105))
        if cfg.SIMULATION_MODE:
            self._t("SIMULATION MODE", self.fS, C_WARN, c=(W//2, 142))
        for b in self.menu_btns:
            b.draw(self.surf, mp)
        self._t("1-4 or click    Q: Quit    F11: Fullscreen", self.fX, C_DIM, c=(W//2, 520))

    # ── Game screen ───────────────────────────────────────────

    def _draw_top(self, mode: str):
        pygame.draw.rect(self.surf, C_PANEL, (0, 0, W, 52))
        names = {"round": "Round Mode", "score": "Score Mode",
                 "train": "Train Mode", "dual":  "Dual Mode"}
        self._t(names.get(mode, ""), self.fM, C_TEXT, tl=(18, 14))
        if cfg.SIMULATION_MODE:
            self._t("[SIM]", self.fX, C_WARN, tr=(W-80, 18))
        self._t("Q: Quit", self.fX, C_DIM, tr=(W-15, 18))

    def _draw_launchers(self, active: set):
        for i, cx in enumerate(L_XS):
            n       = i + 1
            on_fire = n in active
            col     = C_FIRE if on_fire else C_LAUNCHER
            pygame.draw.rect(self.surf, col,
                             (cx-L_W//2, L_TOP, L_W, L_BTM-L_TOP),
                             border_radius=8)
            pygame.draw.rect(self.surf, C_BG,
                             (cx-L_W//2+8, L_BTM-10, L_W-16, 14),
                             border_radius=4)
            if on_fire:
                pygame.draw.rect(self.surf, C_FIRE,
                                 (cx-L_W//2, L_TOP, L_W, L_BTM-L_TOP),
                                 3, border_radius=8)
            nc = (20, 12, 4) if on_fire else C_DIM
            self._t(str(n), self.fLN, nc, c=(cx, L_TOP + (L_BTM-L_TOP)//2))

    def _draw_status(self, l0: str, l1: str, active: set, rr: dict | None):
        l0s, l1s = l0.strip(), l1.strip()
        cy = STATUS_CY

        if active:
            self._t("LAUNCHING", self.fT, C_WARN, c=(W//2, cy-8))
            nums = "  ".join(str(n) for n in sorted(active))
            self._t(f"Launcher  {nums}", self.fM, C_FIRE, c=(W//2, cy+38))

        elif rr is not None:
            # explicit round result — always show this regardless of line content
            cnt  = rr["count"]
            tot  = rr["total"]
            lvl  = rr["level"]
            ok   = rr["passed"]
            self._t(f"Level {lvl}", self.fM, C_DIM, c=(W//2, cy-34))
            col  = C_SUCCESS if ok else C_DANGER
            label = "PASS" if ok else "FAIL"
            self._t(f"{label}  {cnt} / {tot}", self.fT, col, c=(W//2, cy+4))

        elif l1s.isdigit():
            if "Starting" in l0:
                self._t(l0s, self.fM, C_TEXT,  c=(W//2, cy - 30))
                self._t(l1s, self.fT, C_ACCENT, c=(W//2, cy + 14))
            elif "Firing" in l0:
                self._t(l1s, self.fT, C_ACCENT, c=(W//2, cy - 12))
                self._t(l0s, self.fM, C_WARN,   c=(W//2, cy + 36))
            else:
                self._t(l1s, self.fT, C_ACCENT, c=(W//2, cy - 12))
                self._t("seconds remaining", self.fS, C_DIM, c=(W//2, cy + 36))

        elif "GAME CLEAR" in l0:
            self._t(l0s, self.fT, C_SUCCESS, c=(W//2, cy-18))
            self._t(l1s, self.fL, C_WARN,    c=(W//2, cy+28))

        elif "GAME OVER" in l0:
            self._t(l0s, self.fT, C_DANGER, c=(W//2, cy-18))
            self._t(l1s, self.fL, C_WARN,   c=(W//2, cy+28))

        elif "Score:" in l0:
            self._t(l0s, self.fT, C_SUCCESS, c=(W//2, cy-14))
            self._t(l1s, self.fM, C_DIM,     c=(W//2, cy+32))

        else:
            if l0s:
                self._t(l0s, self.fL, C_TEXT, c=(W//2, cy-14))
            if l1s:
                self._t(l1s, self.fM, C_DIM,  c=(W//2, cy+22))

    def _draw_yn(self, mp, prompt: str):
        pygame.draw.rect(self.surf, C_PANEL, (0, INPUT_Y-10, W, H-INPUT_Y+10))
        self._t(prompt.strip(), self.fM, C_TEXT, c=(W//2, INPUT_Y+6))
        self.yes_btn.draw(self.surf, mp)
        self.no_btn.draw(self.surf, mp)
        self._t("Y / N   or click", self.fX, C_DIM, c=(W//2, H-10))

    def _draw_diff(self, mp):
        pygame.draw.rect(self.surf, C_PANEL, (0, INPUT_Y-10, W, H-INPUT_Y+10))
        self._t("Choose Level (1-5)", self.fM, C_TEXT, c=(W//2, INPUT_Y+4))
        for b in self.diff_btns:
            b.draw(self.surf, mp)
        self._t("1-5   or click", self.fX, C_DIM, c=(W//2, H-10))

    def _draw_launcher_select(self, mp, questioner: str):
        pygame.draw.rect(self.surf, C_PANEL, (0, INPUT_Y-10, W, H-INPUT_Y+10))
        self._t(f"Player {questioner}: select launcher (1-4)",
                self.fM, C_WARN, c=(W//2, INPUT_Y+6))
        for b in self.launcher_btns:
            b.draw(self.surf, mp)
        self._t("1-4   or click    20s timeout", self.fX, C_DIM, c=(W//2, H-10))

    # ── Dual final result ─────────────────────────────────────

    def _draw_dual_result(self, dr: dict, wi: bool, mp, prompt: str):
        a = dr["a"]
        b = dr.get("b")

        if b is None:
            # Only A played
            self._t("DUAL MODE", self.fL, C_TEXT, c=(W//2, 120))
            self._t(f"Player A:  {a} / {cfg.DUAL_BALLS}",
                    self.fT, C_ACCENT, c=(W//2, 240))
        else:
            # Split screen
            mid = W // 2
            pygame.draw.rect(self.surf, C_PANEL,  (0,   0, mid, H))
            pygame.draw.rect(self.surf, (20,20,40), (mid, 0, mid, H))
            pygame.draw.line(self.surf, C_DIM, (mid, 0), (mid, H), 2)

            col_a = C_SUCCESS if a >= b else C_TEXT
            col_b = C_SUCCESS if b > a  else C_TEXT

            self._t("Player A", self.fL, C_DIM,   c=(mid//2, 160))
            self._t(str(a),     self.fT, col_a,   c=(mid//2, 240))
            self._t(f"/ {cfg.DUAL_BALLS}", self.fM, C_DIM, c=(mid//2, 295))

            self._t("Player B", self.fL, C_DIM,          c=(mid + mid//2, 160))
            self._t(str(b),     self.fT, col_b,          c=(mid + mid//2, 240))
            self._t(f"/ {cfg.DUAL_BALLS}", self.fM, C_DIM, c=(mid + mid//2, 295))

            if a > b:
                winner = "Winner: Player A"
                wc = col_a
            elif b > a:
                winner = "Winner: Player B"
                wc = col_b
            else:
                winner = "Draw!"
                wc = C_WARN
            self._t(winner, self.fL, wc, c=(W//2, 380))

        if wi:
            pygame.draw.rect(self.surf, C_PANEL, (0, INPUT_Y-10, W, H-INPUT_Y+10))
            self._t(prompt.strip(), self.fM, C_TEXT, c=(W//2, INPUT_Y+6))
            self.yes_btn.draw(self.surf, mp)
            self.no_btn.draw(self.surf, mp)

    # ── Text helper ───────────────────────────────────────────

    def _t(self, text, font, color, c=None, tl=None, tr=None, br=None):
        s = font.render(text, True, color)
        r = s.get_rect()
        if c:    r.center      = c
        elif tl: r.topleft     = tl
        elif tr: r.topright    = tr
        elif br: r.bottomright = br
        self.surf.blit(s, r)


# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    GameScreen().run()
