# hardware.py
# ============================================================
# Hardware abstraction layer
#   MegaController : Arduino Mega  (launcher solenoids)
#   UnoController  : Arduino Uno   (IR sensors)
# ============================================================

import time
from typing import List, Optional

import cfg

try:
    import serial
    _SERIAL_AVAILABLE = True
except ImportError:
    _SERIAL_AVAILABLE = False


class MegaController:
    """
    Serial interface to Arduino Mega.

    RPi → Mega commands:
        FALL:X          fire launcher X in fall mode
        SHOOT:X         fire launcher X in shoot mode
        FALL:X,Y        fire launchers X and Y simultaneously (fall)
        SHOOT:X,Y       fire launchers X and Y simultaneously (shoot)

    Mega → RPi:
        done.           after each fire command completes
    """

    def __init__(self):
        self.ser: Optional["serial.Serial"] = None
        self.is_connected = False
        self._connect()

    def _connect(self) -> None:
        if cfg.SIMULATION_MODE:
            self.is_connected = True
            return
        if not _SERIAL_AVAILABLE:
            print("[Mega] pyserial not installed.")
            return
        try:
            self.ser = serial.Serial(
                cfg.LAUNCHER_SERIAL_PORT,
                cfg.LAUNCHER_BAUDRATE,
                timeout=cfg.LAUNCHER_SERIAL_TIMEOUT_SEC,
            )
            time.sleep(cfg.ARDUINO_RESET_WAIT_SEC)
            self.ser.reset_input_buffer()
            self.is_connected = True
            print(f"[Mega] Connected on {cfg.LAUNCHER_SERIAL_PORT}")
        except serial.SerialException as exc:
            print(f"[Mega] Connection failed: {exc}")

    def fire(self, launcher_numbers: List[int], mode: str = "fall") -> None:
        """
        Fire one or two launchers.
        launcher_numbers: e.g. [1], [3], [1, 2]
        mode: "fall" or "shoot"
        """
        if cfg.SIMULATION_MODE:
            label = ",".join(str(n) for n in launcher_numbers)
            print(f"    [SIM Mega] Launcher(s) {label} fired ({mode})")
            time.sleep(0.1)
            return
        if not self.is_connected or self.ser is None:
            raise RuntimeError("Mega not connected")

        prefix = "FALL" if mode == "fall" else "SHOOT"
        cmd = f"{prefix}:{','.join(str(n) for n in launcher_numbers)}"

        self.ser.reset_input_buffer()
        self.ser.write((cmd + "\n").encode())

        deadline = time.time() + cfg.LAUNCHER_RESPONSE_TIMEOUT_SEC
        while time.time() < deadline:
            line = self.ser.readline().decode(errors="replace").strip()
            if "done" in line.lower():
                break

    def _send(self, cmd: str) -> None:
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\n").encode())

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()


class UnoController:
    """
    Serial interface to Arduino Uno.

    Uno → RPi  : "COUNT:N" every 100 ms
    RPi → Uno  : "RESET"
    """

    def __init__(self):
        self.ser: Optional["serial.Serial"] = None
        self.is_connected = False
        self._connect()

    def _connect(self) -> None:
        if cfg.SIMULATION_MODE:
            self.is_connected = True
            return
        if not _SERIAL_AVAILABLE:
            print("[Uno] pyserial not installed.")
            return
        try:
            self.ser = serial.Serial(
                cfg.DETECTOR_SERIAL_PORT,
                cfg.DETECTOR_BAUDRATE,
                timeout=cfg.DETECTOR_SERIAL_TIMEOUT_SEC,
                write_timeout=1.0,
            )
            time.sleep(cfg.ARDUINO_UNO_RESET_WAIT_SEC)
            self.ser.reset_input_buffer()
            self.is_connected = True
            print(f"[Uno] Connected on {cfg.DETECTOR_SERIAL_PORT}")
        except serial.SerialException as exc:
            print(f"[Uno] Connection failed: {exc}")

    def read_count_fast(self) -> int:
        """Read one COUNT sample quickly (300 ms max). Used as baseline after RESET."""
        if cfg.SIMULATION_MODE:
            return 0
        if not self.is_connected or self.ser is None:
            return 0
        self.ser.reset_input_buffer()
        deadline = time.time() + 0.3
        while time.time() < deadline:
            line = self.ser.readline().decode(errors="replace").strip()
            if line.startswith("COUNT:"):
                try:
                    return int(line.split(":")[1])
                except ValueError:
                    pass
        return 0

    def reset_count(self) -> None:
        """Reset the Uno's ball counter to 0 (send before each round)."""
        if cfg.SIMULATION_MODE:
            print("    [SIM Uno] COUNT reset")
            return
        self._send("RESET")
        if self.ser and self.ser.is_open:
            self.ser.flush()  # block until "RESET\n" is physically transmitted

    def read_ball_count(self) -> int:
        """
        Read COUNT samples and return the maximum.
        Count is cumulative since last RESET, so max = most recent value.
        Returns -1 if no samples collected.
        """
        if cfg.SIMULATION_MODE:
            import random
            count = random.randint(0, 8)
            print(f"    [SIM Uno] Ball count: {count}")
            return count

        if not self.is_connected or self.ser is None:
            return -1

        self.ser.reset_input_buffer()
        samples = []
        deadline = time.time() + cfg.DETECTOR_SAMPLE_COUNT * 0.3

        while len(samples) < cfg.DETECTOR_SAMPLE_COUNT and time.time() < deadline:
            line = self.ser.readline().decode(errors="replace").strip()
            if line.startswith("COUNT:"):
                try:
                    samples.append(int(line.split(":")[1]))
                except ValueError:
                    pass

        if not samples:
            return -1
        return max(samples)

    def _send(self, cmd: str) -> None:
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\n").encode())

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            self.ser.close()
