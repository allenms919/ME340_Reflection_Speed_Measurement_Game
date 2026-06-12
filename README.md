# ME340 Reaction Test Game

KAIST ME340 공학설계 팀 프로젝트 — 탁구공 반응속도 테스트 장치 제어 프로그램.

---

## System Overview

```
[Raspberry Pi 4B]
  python3 main.py          ← SSH 운영
  python3 main.py --gui    ← 시뮬레이션 GUI
        │
        ├── USB Serial ──→ [Arduino Mega]   launcher 4개 solenoid + detector solenoid (pin 50)
        │
        └── USB Serial ──→ [Arduino Uno]    IR 센서 4개 + LCD 16×2
```

---

## Directory Structure

```
ME340_ws/
├── main.py               진입점 (SSH 모드 / --gui 플래그로 GUI 모드)
├── game_engine.py        게임 로직 (Round / Score / Train 모드)
├── hardware.py           MegaController, UnoController
├── game_screen.py        pygame UI (시뮬레이션 시각화)
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
- Round 1 → Difficulty 1, Round 2 → D2, ..., Round 4 → D4
- 4개 공 전부 성공해야 pass
- 라운드당 최대 3번 시도, 4라운드 클리어하면 종료

### Score Mode
- Difficulty 4 고정, 5라운드 자동 연속 진행
- 라운드 종료 후 사용자 입력 없이 즉시 다음 라운드
- 최종 결과: 20개 중 성공 개수

### Train Mode
- 매 라운드 Difficulty 1~4 자유 선택
- 라운드 종료마다 성공 개수 확인
- 계속 여부 및 다음 난이도를 운영자가 직접 선택

---

## Difficulty

| D | 이름 | 발사 간격 | 패턴 | 발사 방식 |
|---|---|---|---|---|
| 1 | default | 3s 고정 | 1~4 랜덤 순서, 1개씩 | fall |
| 2 | speed | 1s 고정 | 1~4 랜덤 순서, 1개씩 | shoot |
| 3 | random | 2s / 4s 랜덤 | 동시 발사 패턴 랜덤 | fall |
| 4 | mixed | 1s / 2s / 3s 랜덤 | 동시 발사 패턴 랜덤 | shoot |

동시 발사 패턴 (D3, D4): `(2,1,1)` `(1,2,1)` `(1,1,2)` `(2,2)` 중 랜덤 선택.

---

## Serial Protocol

### Mega (launcher + detector solenoid)
| 명령 | 동작 |
|---|---|
| `FALL:X` | 런처 X fall 모드 발사 |
| `SHOOT:X` | 런처 X shoot 모드 발사 |
| `FALL:X,Y` | 런처 X, Y 동시 fall 발사 |
| `SHOOT:X,Y` | 런처 X, Y 동시 shoot 발사 |
| `OPEN` | detector solenoid 열기 |
| `CLOSE` | detector solenoid 닫기 |

### Uno (detector + LCD)
| 방향 | 형식 | 내용 |
|---|---|---|
| Uno → RPi | `COUNT:N` | 200ms마다 현재 공 개수 |
| RPi → Uno | `LCD0:text` | LCD 상단 행 표시 |
| RPi → Uno | `LCD1:text` | LCD 하단 행 표시 |

---

## Pin Assignment

### Arduino Mega
| 런처 | Gate pin | Fire pin |
|---|---|---|
| 1 | D2 | D3 |
| 2 | D5 | D6 |
| 3 | D8 | D9 |
| 4 | D11 | D12 |
| Detector solenoid | D50 | — |

### Arduino Uno
| 역할 | 핀 |
|---|---|
| IR 센서 1~4 | D2, D3, D4, D5 |
| LCD SDA | A4 |
| LCD SCL | A5 |

---

## Configuration (`cfg.py`)

주요 설정값:

```python
SIMULATION_MODE = False          # True: 하드웨어 없이 동작

LAUNCHER_SERIAL_PORT = "/dev/ttyUSB0"   # Arduino Mega 포트
DETECTOR_SERIAL_PORT = "/dev/ttyACM2"  # Arduino Uno 포트

POST_LAUNCH_WAIT_SEC  = 4.0      # 마지막 발사 후 detector 읽기까지 대기
DETECTOR_OPEN_SEC     = 5.0      # detector solenoid 열림 시간
```

---

## Setup & Run

```bash
# 패키지 설치
pip3 install pyserial pygame

# SSH 모드 (RPi 실기)
python3 main.py

# GUI 시뮬레이션 (노트북)
python3 main.py --gui
```

포트 확인:
```bash
ls /dev/ttyACM* /dev/ttyUSB*
# 포트를 cfg.py에 반영 후 실행
```

---

## Troubleshooting

**포트 권한 오류:**
```bash
sudo usermod -a -G dialout $USER && sudo reboot
```

**LCD 글씨 안 보임:** I2C 모듈 뒷면 파란색 가변저항으로 contrast 조절.