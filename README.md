# ME340 Reaction Launcher Project

KAIST ME340 공학설계 팀 프로젝트용 Raspberry Pi-Arduino 기반 반응속도 테스트 장치 제어 프로그램이다.

본 프로젝트는 Raspberry Pi를 상위 제어기(high-level controller)로 사용하고, Arduino Mega를 하위 하드웨어 제어기(actuator driver)로 사용한다. Raspberry Pi에서는 Python 프로그램을 실행하여 게임 화면, 난이도, 랜덤 런처 선택, 타이머, 점수 등을 관리하고, Arduino Mega는 Raspberry Pi에서 받은 serial 명령을 바탕으로 solenoid에 실제 전기 신호를 출력한다.

---

## 1. System Overview

전체 시스템 구조는 다음과 같다.

```text
[Raspberry Pi]
 - Python main program
 - Pygame screen
 - Game logic
 - Random launcher scheduling
 - Serial command transmission
        │
        │ USB Serial
        ▼
[Arduino Mega]
 - Receives command: '1', '2', '3', '4'
 - Generates PWM signals
 - Controls solenoids
        │
        ▼
[Launcher System]
 - Launcher 1: D2, D3
 - Launcher 2: D5, D6
 - Launcher 3: D9, D10
 - Launcher 4: D12, D13
```

설계 의도는 다음과 같다.

- Raspberry Pi는 게임 로직과 화면 표시를 담당한다.
- Arduino Mega는 실시간 pin output과 solenoid timing을 담당한다.
- Raspberry Pi의 Python 코드는 Arduino의 세부 PWM 제어를 직접 수행하지 않고, serial 명령만 전송한다.
- 하드웨어 모듈은 `hardware/` 폴더에 분리하여 향후 IR 판정 시스템, recirculation system 등을 추가할 수 있도록 한다.

---

## 2. Project Directory Structure

```text
ME340_ws/
│
├── main.py
├── cfg.py
│
├── game_engine.py
├── game_screen.py
│
├── hardware/
│   ├── __init__.py
│   ├── launcher_controller.py
│   └── IR_controller.py
│
└── arduino/
    ├── launcher/
    │   └── launcher.ino
    └── IR/
        └── IR.ino
```

현재 구현 대상은 launcher system이다.  
`IR_controller.py`와 `IR.ino`는 향후 IR 판정 시스템 개발을 위한 placeholder이다.

---

## 3. File Roles

### `main.py`

프로그램의 entry point이다.

역할:

- `LauncherController` 생성
- `GameEngine` 생성
- `GameScreen` 생성
- 전체 객체 연결
- 프로그램 종료 시 serial connection close

`main.py`에는 게임 세부 로직을 넣지 않고, 전체 모듈을 조립하는 역할만 둔다.

---

### `cfg.py`

프로젝트 전체 설정 파일이다.

포함 설정:

- Arduino serial port
- baudrate
- simulation mode
- launcher pin map
- game duration
- difficulty별 launcher interval
- pygame window size
- color, font size 설정

하드웨어 없이 화면만 테스트하려면 다음 값을 사용한다.

```python
SIMULATION_MODE = True
```

실제 Arduino Mega를 연결해서 사용할 때는 다음처럼 둔다.

```python
SIMULATION_MODE = False
```

---

### `game_engine.py`

게임 로직을 담당한다.

역할:

- 게임 상태 관리
- 난이도 관리
- 랜덤 시간 간격 계산
- 랜덤 launcher 선택
- launcher command 실행
- score 계산
- launch count 계산
- 상태 메시지 관리

`game_engine.py`는 pygame 화면을 직접 그리지 않는다.  
화면과 무관한 순수 게임 진행 로직을 담당한다.

---

### `game_screen.py`

pygame 기반 화면 출력과 사용자 입력 처리를 담당한다.

역할:

- 시작 화면 출력
- 난이도 버튼 표시
- start/restart 버튼 표시
- 타이머 표시
- 점수 표시
- 현재 launcher 상태 표시
- keyboard/mouse event 처리
- 사용자 입력을 `GameEngine`에 전달

`game_screen.py`는 `launcher_controller.py`를 직접 호출하지 않는다.  
하드웨어 제어는 항상 `GameEngine`을 통해 간접적으로 수행한다.

---

### `hardware/launcher_controller.py`

Arduino Mega와 serial 통신을 담당하는 launcher hardware controller이다.

역할:

- Arduino Mega와 serial 연결
- launcher 번호를 command로 전송
- Arduino 응답 수신
- serial connection 종료

Python에서 Arduino로 보내는 명령은 다음과 같다.

```text
1 -> Launcher 1
2 -> Launcher 2
3 -> Launcher 3
4 -> Launcher 4
```

Arduino Mega에는 `arduino/launcher/launcher.ino`가 업로드되어 있어야 한다.

---

### `hardware/__init__.py`

`hardware` 폴더를 Python package로 인식시키는 파일이다.

현재는 다음 controller를 export한다.

```python
from .launcher_controller import LauncherController
```

---

### `arduino/launcher/launcher.ino`

Arduino Mega에 업로드되는 sketch이다.

역할:

- serial command 수신
- command에 따라 launcher 선택
- 각 launcher의 두 solenoid를 순차적으로 작동
- PWM pull/hold/off sequence 수행

현재 launcher pin mapping은 다음과 같다.

| Launcher | Solenoid Pins |
|---|---|
| Launcher 1 | D2, D3 |
| Launcher 2 | D5, D6 |
| Launcher 3 | D9, D10 |
| Launcher 4 | D12, D13 |

- 아두이노에 업로드되는 .ino 코드는 유일하므로, 다른 하드웨어 컨트롤 동작도 이 코드에 병합하여 작성
- 병합 시 launcher.ino 파일명 적절하게 변경

---

## 4. Required Python Packages

현재 필요한 Python package는 다음 두 개이다.

```bash
pip install pyserial pygame
```

역할:

| Package | Role |
|---|---|
| `pyserial` | Raspberry Pi와 Arduino Mega 간 USB serial 통신 |
| `pygame` | 게임 화면, 버튼, 타이머, 키보드/마우스 입력 처리 |

---

## 5. Setup

프로젝트 폴더로 이동한다.

```bash
cd ME340_ws
```

가상환경을 생성한다.

```bash
python3 -m venv .venv
```

가상환경을 활성화한다.

```bash
source .venv/bin/activate
```

필요 package를 설치한다.

```bash
pip install --upgrade pip
pip install pyserial pygame
```

설치 확인:

```bash
python -c "import serial; import pygame; print('Package import OK')"
```

---

## 6. Arduino Setup

Arduino IDE에서 `arduino/launcher/launcher.ino`를 Arduino Mega에 업로드한다.

보드 설정:

```text
Tools > Board > Arduino Mega or Mega 2560
```

포트 설정:

```text
Tools > Port > 사용 중인 Arduino Mega 포트 선택
```

업로드 후 Raspberry Pi에 Arduino Mega를 USB로 연결한다.

Raspberry Pi에서 포트를 확인한다.

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
```

일반적으로 Arduino Mega는 다음 포트 중 하나로 인식된다.

```text
/dev/ttyACM0
/dev/ttyUSB0
```

확인한 포트를 `cfg.py`에 반영한다.

```python
LAUNCHER_SERIAL_PORT = "/dev/ttyACM0"
```

권한 문제가 발생하면 다음 명령을 실행한 뒤 재부팅한다.

```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

---

## 7. Running the Program

프로젝트 루트에서 실행한다.

```bash
cd ME340_ws
source .venv/bin/activate
python main.py
```

실행 후 pygame window가 열리며, 화면에서 난이도를 선택하고 `START` 버튼을 누르면 게임이 시작된다.

---

## 8. Game Controls

### Mouse Control

- `EASY`, `NORMAL`, `HARD`: 난이도 선택
- `START`: 게임 시작
- `RESTART`: 게임 재시작

### Keyboard Control

| Key | Function |
|---|---|
| `1` | Easy 난이도 선택 |
| `2` | Normal 난이도 선택 |
| `3` | Hard 난이도 선택 |
| `Space` | Start 또는 Restart |
| `R` | Menu로 돌아가기 |
| `Q` | Quit |
| `ESC` | Quit |

---

## 9. Difficulty Settings

난이도별 launcher 작동 간격은 `cfg.py`에서 설정한다.

```python
DIFFICULTIES = {
    "EASY": {
        "min_interval_sec": 2.0,
        "max_interval_sec": 4.0,
    },
    "NORMAL": {
        "min_interval_sec": 1.2,
        "max_interval_sec": 2.8,
    },
    "HARD": {
        "min_interval_sec": 0.7,
        "max_interval_sec": 1.8,
    },
}
```

각 launcher command는 해당 interval 범위 안에서 랜덤한 시간 간격으로 실행된다.

---

## 10. Simulation Mode

Arduino Mega 없이 UI와 게임 로직만 테스트하고 싶을 때 사용한다.

`cfg.py`에서 다음과 같이 설정한다.

```python
SIMULATION_MODE = True
```

이 경우 실제 serial connection을 열지 않고, launcher 작동은 console log로만 출력된다.

실제 하드웨어를 사용할 때는 다음처럼 설정한다.

```python
SIMULATION_MODE = False
```

---

## 11. Software Architecture

현재 구조는 다음의 역할 분리를 따른다.

```text
main.py
 └─ 전체 객체 생성 및 연결

game_screen.py
 └─ pygame 화면 표시
 └─ 사용자 입력 처리
 └─ engine에 명령 전달

game_engine.py
 └─ 게임 상태 관리
 └─ 랜덤 launcher scheduling
 └─ launcher_controller 호출

hardware/launcher_controller.py
 └─ Arduino Mega serial 통신

arduino/launcher/launcher.ino
 └─ 실제 solenoid PWM 출력
```

이 구조의 장점은 다음과 같다.

- 화면 코드와 게임 로직이 분리된다.
- 게임 로직과 하드웨어 통신이 분리된다.
- 향후 IR 판정 시스템이나 recirculation system을 쉽게 추가할 수 있다.
- pygame 화면이 serial 통신 때문에 멈추지 않도록 launcher command는 background thread에서 실행된다.

---

## 12. Future Expansion

향후 추가 예정 모듈:

```text
hardware/IR_controller.py
```

예상 역할:

- IR sensor input 수신
- 성공 ball 개수 판정
- score system과 연동

향후 구조 예시는 다음과 같다.

```python
from hardware import LauncherController
from hardware.IR_controller import IRController

launcher_controller = LauncherController()
ir_controller = IRController()

engine = GameEngine(
    launcher_controller=launcher_controller,
    ir_controller=ir_controller,
)
```

즉, 하드웨어가 추가되어도 `game_screen.py`는 화면 표시에 집중하고, 게임 규칙과 하드웨어 연동은 `game_engine.py`에서 관리한다.

---

## 13. Troubleshooting

### 1. Arduino serial port를 찾을 수 없는 경우

다음 명령으로 연결된 포트를 확인한다.

```bash
ls /dev/ttyACM*
ls /dev/ttyUSB*
```

확인한 포트를 `cfg.py`에 반영한다.

```python
LAUNCHER_SERIAL_PORT = "/dev/ttyACM0"
```

---

### 2. Permission denied 에러가 발생하는 경우

다음 명령을 실행한다.

```bash
sudo usermod -a -G dialout $USER
sudo reboot
```

---

### 3. pygame 화면만 먼저 확인하고 싶은 경우

`cfg.py`에서 simulation mode를 켠다.

```python
SIMULATION_MODE = True
```

---

### 4. Arduino는 연결되어 있는데 launcher가 작동하지 않는 경우

확인할 항목:

1. Arduino Mega에 `launcher.ino`가 업로드되어 있는지 확인한다.
2. `cfg.py`의 `LAUNCHER_SERIAL_PORT`가 실제 포트와 일치하는지 확인한다.
3. Arduino Serial Monitor가 열려 있지 않은지 확인한다.
4. solenoid driver 회로의 외부 전원과 GND common이 연결되어 있는지 확인한다.
5. MOSFET, flyback diode, SMPS 극성이 올바른지 확인한다.

---

## 14. Safety Notes

Solenoid는 Arduino pin으로 직접 구동하면 안 된다.

반드시 다음 구성이 필요하다.

- 외부 전원 공급 장치
- MOSFET 또는 적절한 driver circuit
- flyback diode
- Arduino GND와 외부 전원 GND common connection
- solenoid 정격 전압과 전류에 맞는 전원 용량

Arduino pin은 solenoid에 직접 전류를 공급하는 역할이 아니라, MOSFET gate에 제어 신호를 주는 역할만 해야 한다.

---

## 15. Current Status

현재 구현된 기능:

- Raspberry Pi pygame GUI
- 난이도 선택
- start/restart 기능
- 게임 타이머
- 점수 표시
- 랜덤 launcher 선택
- 랜덤 시간 간격 launcher 작동
- Arduino Mega serial command 전송
- simulation mode 지원

아직 구현되지 않은 기능:

- IR sensor 기반 판정 시스템
- reaction time 측정
- recirculation system 제어
- map별 launcher pattern
- 사용자별 score logging
