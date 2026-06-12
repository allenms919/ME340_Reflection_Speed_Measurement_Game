# cfg.py  —  ME340 Reaction Test Game

# ============================================================
# Simulation
# ============================================================

SIMULATION_MODE = True

# ============================================================
# Serial — Arduino Mega (launcher)
# ============================================================

LAUNCHER_SERIAL_PORT          = "/dev/ttyUSB0"
LAUNCHER_BAUDRATE             = 9600
LAUNCHER_SERIAL_TIMEOUT_SEC   = 1.0
ARDUINO_RESET_WAIT_SEC        = 2.0
LAUNCHER_RESPONSE_TIMEOUT_SEC = 5.0

# ============================================================
# Serial — Arduino Uno (detector)
# ============================================================

DETECTOR_SERIAL_PORT        = "/dev/ttyACM2"
DETECTOR_BAUDRATE           = 115200
DETECTOR_SERIAL_TIMEOUT_SEC = 1.0
ARDUINO_UNO_RESET_WAIT_SEC  = 2.0

# ============================================================
# Detector timing
# ============================================================

POST_FIRE_WAIT_SEC    = 3.0   # seconds after last ball before reading count
DETECTOR_SAMPLE_COUNT = 5     # COUNT readings collected for noise filtering

# ============================================================
# Game rules
# ============================================================

ROUND_BALLS        = 2    # balls per attempt
ROUND_SUCCESS_MIN  = 2    # minimum balls to pass
ROUND_MAX_FAILS    = 1    # failures allowed before game over (4th = over)
ROUND_MAX_LEVELS   = 5

SCORE_BALLS        = 20   # total balls in score mode
SCORE_PER_BALL     = 5    # points per ball (100 max)

DUAL_BALLS         = 8
DUAL_MIN_INTERVAL  = 1.0   # minimum seconds between questioner fires
DUAL_IDLE_TIMEOUT  = 20.0  # idle seconds before auto end

# ============================================================
# Difficulty definitions
# ============================================================
#
# shot:          "single" | "double" | "random"
# shot_mode:     "fall"   | "shoot"  | "random"
# interval_mode: "fixed"  | "random"

DIFFICULTY = {
    1: {
        "name":          "default",
        "shot":          "single",
        "shot_mode":     "fall",
        "interval_mode": "fixed",
        "interval_sec":  3.0,
    },
    2: {
        "name":          "fast",
        "shot":          "single",
        "shot_mode":     "shoot",
        "interval_mode": "fixed",
        "interval_sec":  1.0,
    },
    3: {
        "name":          "double",
        "shot":          "double",
        "shot_mode":     "fall",
        "interval_mode": "fixed",
        "interval_sec":  3.0,
    },
    4: {
        "name":             "random",
        "shot":             "random",
        "shot_mode":        "random",
        "interval_mode":    "random",
        "interval_choices": [2.0, 3.0, 4.0],
    },
    5: {
        "name":          "fast double",
        "shot":          "double",
        "shot_mode":     "shoot",
        "interval_mode": "fixed",
        "interval_sec":  1.0,
    },
}

ROUND_GRADES = {
    1: "Sloth",
    2: "NPC",
    3: "Rookie",
    4: "Gifted",
    5: "Beast",
}
ROUND_CLEAR_GRADE = "GOAT"
