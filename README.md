# ME340 Reaction Test Game

KAIST ME340 공학설계 팀 프로젝트 — 탁구공 반응속도 측정 장치 제어 프로그램.

---

## System Overview

```
[Raspberry Pi]
  python3 main.py          ← 터미널 모드
  python3 main.py --gui    ← GUI 모드 (pygame)
        │
        ├── USB Serial (9600 baud) ──→ [Arduino Mega]   launcher solenoid 4개 제어
        │
        └── USB Serial (115200 baud) → [Arduino Uno]    IR 센서 1개, 공 통과 카운팅
```

---

## Directory Structure

```
ME340_ws/
├── main.py               진입점
├── game_engine.py        게임 로직 (Round / Score / Train / Dual 모드)
├── hardware.py           MegaController, UnoController
├── game_screen.py        pygame GUI
├── cfg.py                전체 설정
└── arduino/
    ├── launcher/
    │   └── launcher.ino  Arduino Mega 펌웨어
    └── detector/
        └── detector.ino  Arduino Uno 펌웨어
```

---

## Game Modes

### Round Mode
- Level 1 → 5 순차 진행, 레벨마다 난이도 상승
- 라운드당 공 8개, 6개 이상 통과 시 통과
- 같은 레벨에서 4번 실패 시 Game Over
- 게임 종료 시 최종 도달 난이도에 따라 등급 부여

| 결과 | 등급 |
|---|---|
| Level 1 실패 | Sloth |
| Level 2 실패 | NPC |
| Level 3 실패 | Rookie |
| Level 4 실패 | Gifted |
| Level 5 실패 | Beast |
| 전 레벨 클리어 | GOAT |

### Score Mode
- Difficulty 4 (random) 고정, 공 20개
- 통과한 공 개수 × 5점 (최대 100점)
- 종료 후 재도전 여부 선택 가능

### Train Mode
- 매 라운드 Difficulty 1~5 자유 선택
- 라운드당 공 8개, 결과 확인 후 계속 여부 선택

### Dual Mode
- 2인 대결: 한 명이 questioner(발사), 다른 한 명이 player(수비)
- 라운드당 공 8개, A·B 순서로 번갈아 플레이
- 최종 결과 비교

---

## Difficulty

| Level | 이름 | 발사 패턴 | 발사 방식 | 간격 |
|---|---|---|---|---|
| 1 | default | 1개씩 순차 | fall | 3s 고정 |
| 2 | fast | 1개씩 순차 | shoot | 1s 고정 |
| 3 | double | 2개씩 동시 | fall | 3s 고정 |
| 4 | random | 1~2개 랜덤 | fall/shoot 랜덤 | 2/3/4s 랜덤 |
| 5 | fast double | 2개씩 동시 | shoot | 1s 고정 |

---

## Serial Protocol

### Mega (launcher)

| RPi → Mega | 동작 |
|---|---|
| `FALL:X` | launcher X fall 모드 발사 |
| `SHOOT:X` | launcher X shoot 모드 발사 |
| `FALL:X,Y` | launcher X, Y 동시 fall 발사 |
| `SHOOT:X,Y` | launcher X, Y 동시 shoot 발사 |

| Mega → RPi | 내용 |
|---|---|
| `done.` | 발사 완료 응답 |

### Uno (detector)

| 방향 | 형식 | 내용 |
|---|---|---|
| Uno → RPi | `COUNT:N` | 100ms마다 공 누적 통과 횟수 |
| RPi → Uno | `RESET` | 누적 카운터 초기화 |

---

## Pin Assignment

### Arduino Mega

| Launcher | Gate pin | Fire pin |
|---|---|---|
| 1 (플레이어 기준 왼쪽) | D11 | D12 |
| 2 | D8 | D9 |
| 3 | D5 | D6 |
| 4 (플레이어 기준 오른쪽) | D2 | D3 |

### Arduino Uno

| 역할 | 핀 |
|---|---|
| IR 센서 | D2 |

---

## Configuration (`cfg.py`)

```python
SIMULATION_MODE = False           # True: 하드웨어 없이 동작

LAUNCHER_SERIAL_PORT = "/dev/ttyUSB0"    # Arduino Mega 포트
DETECTOR_SERIAL_PORT = "/dev/ttyACM2"   # Arduino Uno 포트

ROUND_BALLS       = 8     # 라운드당 발사 공 개수
ROUND_SUCCESS_MIN = 6     # 통과 판정 최소 개수
ROUND_MAX_FAILS   = 3     # 레벨당 허용 실패 횟수 (초과 시 Game Over)
ROUND_MAX_LEVELS  = 5     # 최대 레벨

SCORE_BALLS       = 20    # Score Mode 공 개수
SCORE_PER_BALL    = 5     # 공 1개당 점수

DUAL_BALLS        = 8     # Dual Mode 라운드당 공 개수

POST_FIRE_WAIT_SEC = 3.0  # 마지막 발사 후 카운트 읽기까지 대기 시간
```

---

## Setup & Run

```bash
pip3 install pyserial pygame
```

```bash
# 터미널 모드
python3 main.py

# GUI 모드
python3 main.py --gui
```

포트 확인:
```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

포트 번호를 `cfg.py`의 `LAUNCHER_SERIAL_PORT`, `DETECTOR_SERIAL_PORT`에 반영 후 실행.

---

## Troubleshooting

**포트 권한 오류:**
```bash
sudo usermod -a -G dialout $USER && sudo reboot
```
