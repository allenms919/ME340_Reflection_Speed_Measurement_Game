# 핀 번호, serial port, 난이도 설정 저장

# cfg.py
# ============================================================
# ME340 Reaction Launcher Game
# Global Configuration
# ============================================================

# ============================================================
# Serial settings
# ============================================================

# Arduino Mega가 연결된 포트입니다.
# Raspberry Pi에서는 보통 /dev/ttyACM0 또는 /dev/ttyUSB0입니다.
LAUNCHER_SERIAL_PORT = "/dev/ttyACM0"

LAUNCHER_BAUDRATE = 9600
LAUNCHER_SERIAL_TIMEOUT_SEC = 1.0

# Arduino Mega는 serial 연결 직후 reset될 수 있으므로 대기 시간이 필요합니다.
ARDUINO_RESET_WAIT_SEC = 2.0

# Arduino에서 "done." 응답을 기다리는 최대 시간입니다.
LAUNCHER_RESPONSE_TIMEOUT_SEC = 2.0

# 하드웨어 없이 화면과 게임 로직만 테스트할 때 True로 바꿉니다.
# 실제 Arduino Mega를 사용할 때는 False로 둡니다.
SIMULATION_MODE = True


# ============================================================
# Launcher settings
# ============================================================

LAUNCHER_COUNT = 4

LAUNCHER_PIN_MAP = {
    1: (2, 3),
    2: (5, 6),
    3: (9, 10),
    4: (12, 13),
}


# ============================================================
# Game settings
# ============================================================

GAME_DURATION_SEC = 30.0

DIFFICULTIES = {
    "EASY": {
        "label": "EASY",
        "min_interval_sec": 2.0,
        "max_interval_sec": 4.0,
    },
    "NORMAL": {
        "label": "NORMAL",
        "min_interval_sec": 1.2,
        "max_interval_sec": 2.8,
    },
    "HARD": {
        "label": "HARD",
        "min_interval_sec": 0.7,
        "max_interval_sec": 1.8,
    },
}

DEFAULT_DIFFICULTY = "NORMAL"


# ============================================================
# Screen settings
# ============================================================

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 540
FPS = 60

WINDOW_TITLE = "ME340 Reaction Launcher Game"


# ============================================================
# Colors
# ============================================================

COLOR_BG = (18, 20, 24)
COLOR_PANEL = (34, 38, 46)
COLOR_PANEL_LIGHT = (48, 54, 64)

COLOR_TEXT = (240, 240, 240)
COLOR_TEXT_MUTED = (170, 175, 185)

COLOR_ACCENT = (90, 170, 255)
COLOR_ACCENT_DARK = (50, 120, 210)

COLOR_SUCCESS = (80, 220, 140)
COLOR_WARNING = (255, 190, 80)
COLOR_ERROR = (255, 90, 90)

COLOR_BUTTON = (60, 70, 85)
COLOR_BUTTON_HOVER = (80, 95, 115)
COLOR_BUTTON_ACTIVE = (90, 170, 255)


# ============================================================
# Font settings
# ============================================================

# None이면 pygame 기본 시스템 폰트를 사용합니다.
FONT_NAME = None

FONT_SIZE_TITLE = 54
FONT_SIZE_LARGE = 40
FONT_SIZE_MEDIUM = 28
FONT_SIZE_SMALL = 22
FONT_SIZE_TINY = 18