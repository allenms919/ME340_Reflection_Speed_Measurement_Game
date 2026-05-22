# Arduino와 serial 통신
# 4개 Launcher 제어

# hardware/launcher_controller.py
# ============================================================
# Arduino Mega Launcher Controller
# Raspberry Pi -> Arduino Mega serial command interface
# ============================================================

import time
import threading
from typing import List, Optional

import serial

import cfg


class LauncherController:
    """
    Arduino Mega에 launcher 명령을 보내는 하위 하드웨어 제어 모듈입니다.

    이 클래스는 게임 로직을 알지 않습니다.
    오직 다음 역할만 담당합니다.

    1. Arduino Mega와 serial 연결
    2. launcher 번호를 Arduino로 전송
    3. Arduino 응답 수신
    4. 연결 종료

    Arduino Mega에는 arduino/launcher/launcher.ino가 업로드되어 있어야 합니다.
    """

    def __init__(
        self,
        port: str = cfg.LAUNCHER_SERIAL_PORT,
        baudrate: int = cfg.LAUNCHER_BAUDRATE,
        timeout: float = cfg.LAUNCHER_SERIAL_TIMEOUT_SEC,
        simulation_mode: bool = cfg.SIMULATION_MODE,
        auto_connect: bool = True,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.simulation_mode = simulation_mode

        self._serial: Optional[serial.Serial] = None
        self._lock = threading.Lock()

        if auto_connect:
            self.connect()

    @property
    def is_connected(self) -> bool:
        """
        하드웨어 연결 상태를 반환합니다.
        simulation mode에서는 항상 True로 취급합니다.
        """
        if self.simulation_mode:
            return True

        return self._serial is not None and self._serial.is_open

    def connect(self) -> None:
        """
        Arduino Mega와 serial 연결을 시작합니다.
        """
        if self.simulation_mode:
            print("[LauncherController] Simulation mode enabled. No Arduino connection.")
            return

        if self.is_connected:
            return

        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
            )

            # Arduino Mega는 serial 연결 시 reset될 수 있습니다.
            time.sleep(cfg.ARDUINO_RESET_WAIT_SEC)

            self._clear_initial_messages()

            print(f"[LauncherController] Connected to Arduino Mega on {self.port}")

        except serial.SerialException as exc:
            raise RuntimeError(
                f"Arduino Mega serial connection failed on {self.port}.\n"
                f"포트 이름을 확인하세요. 예: /dev/ttyACM0 또는 /dev/ttyUSB0\n"
                f"Original error: {exc}"
            ) from exc

    def _clear_initial_messages(self) -> None:
        """
        Arduino setup()에서 출력한 Ready 메시지들을 읽어서 비웁니다.
        """
        if self.simulation_mode or self._serial is None:
            return

        time.sleep(0.2)

        while self._serial.in_waiting > 0:
            line = self._serial.readline().decode("utf-8", errors="ignore").strip()
            if line:
                print(f"[Arduino] {line}")

    def activate_launcher(self, launcher_number: int) -> List[str]:
        """
        특정 launcher를 작동시킵니다.

        Parameters
        ----------
        launcher_number:
            1, 2, 3, 4 중 하나입니다.

        Returns
        -------
        List[str]
            Arduino에서 받은 응답 메시지 목록입니다.
        """
        if launcher_number not in cfg.LAUNCHER_PIN_MAP:
            raise ValueError(
                f"launcher_number must be between 1 and {cfg.LAUNCHER_COUNT}"
            )

        return self._send_command(str(launcher_number))

    def _send_command(self, command: str) -> List[str]:
        """
        Arduino에 '1', '2', '3', '4' 명령을 전송합니다.
        """
        if command not in ["1", "2", "3", "4"]:
            raise ValueError("command must be one of '1', '2', '3', '4'")

        if self.simulation_mode:
            launcher_number = int(command)
            pin_pair = cfg.LAUNCHER_PIN_MAP[launcher_number]

            print(
                f"[SIM] Launcher {launcher_number} activated. "
                f"Pins {pin_pair[0]}, {pin_pair[1]}"
            )

            time.sleep(0.25)

            print(f"[SIM] Launcher {launcher_number} done.")

            return [
                f"Launcher {launcher_number} activated. Pins {pin_pair[0]}, {pin_pair[1]}",
                f"Launcher {launcher_number} done.",
            ]

        if not self.is_connected:
            self.connect()

        responses: List[str] = []

        with self._lock:
            if self._serial is None:
                raise RuntimeError("Serial connection is not available.")

            # 이전 buffer에 남아 있는 메시지를 제거합니다.
            self._serial.reset_input_buffer()

            # Arduino launcher.ino는 char command = Serial.read() 방식입니다.
            # 따라서 개행 없이 한 글자만 보내면 됩니다.
            self._serial.write(command.encode("utf-8"))
            self._serial.flush()

            start_time = time.time()

            while time.time() - start_time < cfg.LAUNCHER_RESPONSE_TIMEOUT_SEC:
                if self._serial.in_waiting > 0:
                    line = (
                        self._serial.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )

                    if line:
                        responses.append(line)
                        print(f"[Arduino] {line}")

                        if "done" in line.lower():
                            break

                time.sleep(0.01)

        return responses

    def close(self) -> None:
        """
        serial 연결을 종료합니다.
        """
        if self.simulation_mode:
            print("[LauncherController] Simulation mode closed.")
            return

        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            print("[LauncherController] Serial connection closed.")