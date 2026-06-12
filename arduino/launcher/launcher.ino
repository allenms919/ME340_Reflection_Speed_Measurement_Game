// =============================================
// Launcher Controller
// Board: Arduino Mega
// =============================================
//
// RPi → Mega commands (newline-terminated):
//   FALL:X          fire launcher X, fall mode
//   SHOOT:X         fire launcher X, shoot mode
//   FALL:X,Y        fire launchers X and Y simultaneously, fall mode
//   SHOOT:X,Y       fire launchers X and Y simultaneously, shoot mode
//
// Mega → RPi:
//   done.           after each fire command

// ── Shot timing (ms) ─────────────────────────
const int FALL_OPEN_TO_FIRE_MS  = 30;   // 개폐 ON → 발사 ON (fall: 늦게 타격 = 자유낙하)
const int SHOOT_OPEN_TO_FIRE_MS = 10;   // 개폐 ON → 발사 ON (shoot: 빠르게 타격)
const int DURATION_MS           = 40;   // 각 솔레노이드가 켜져 있는 시간

// ── Shot power (PWM 0-255) ───────────────────
const int GATE_POWER = 255;
const int FIRE_POWER = 255;

// ── Launcher pin assignments ─────────────────
//   Index: launcher number - 1  (launcher 1 = index 0)
const int GATE_PINS[4] = {11,  8,  5,  2};
const int FIRE_PINS[4] = {12,  9,  6,  3};

// ── Serial command buffer ────────────────────
char cmdBuf[32];

// ─────────────────────────────────────────────

void setup() {
  for (int i = 0; i < 4; i++) {
    pinMode(GATE_PINS[i], OUTPUT);
    pinMode(FIRE_PINS[i], OUTPUT);
    analogWrite(GATE_PINS[i], 0);
    analogWrite(FIRE_PINS[i], 0);
  }

  Serial.begin(9600);
  Serial.setTimeout(100);
  Serial.println("Ready.");
}

void loop() {
  if (Serial.available() > 0) {
    int len = Serial.readBytesUntil('\n', cmdBuf, sizeof(cmdBuf) - 1);
    cmdBuf[len] = '\0';
    if (len > 0 && cmdBuf[len - 1] == '\r') cmdBuf[--len] = '\0';

    if (strncmp(cmdBuf, "FALL:", 5) == 0) {
      parseFire(cmdBuf + 5, FALL_OPEN_TO_FIRE_MS);
    } else if (strncmp(cmdBuf, "SHOOT:", 6) == 0) {
      parseFire(cmdBuf + 6, SHOOT_OPEN_TO_FIRE_MS);
    }
  }
}

// ─────────────────────────────────────────────

void parseFire(const char* args, int openToFireMs) {
  int a = -1, b = -1;
  const char* comma = strchr(args, ',');

  if (comma != NULL) {
    a = atoi(args) - 1;
    b = atoi(comma + 1) - 1;
  } else {
    a = atoi(args) - 1;
  }

  if (b >= 0) {
    fireTwoLaunchers(a, b, openToFireMs);
  } else if (a >= 0) {
    fireOneLauncher(a, openToFireMs);
  }

  Serial.println("done.");
}

void fireOneLauncher(int idx, int openToFireMs) {
  allOff();
  analogWrite(GATE_PINS[idx], GATE_POWER);
  delay(openToFireMs);
  analogWrite(FIRE_PINS[idx], FIRE_POWER);
  delay(DURATION_MS - openToFireMs);
  analogWrite(GATE_PINS[idx], 0);
  delay(openToFireMs);
  analogWrite(FIRE_PINS[idx], 0);
  allOff();
}

void fireTwoLaunchers(int idxA, int idxB, int openToFireMs) {
  allOff();
  analogWrite(GATE_PINS[idxA], GATE_POWER);
  analogWrite(GATE_PINS[idxB], GATE_POWER);
  delay(openToFireMs);
  analogWrite(FIRE_PINS[idxA], FIRE_POWER);
  analogWrite(FIRE_PINS[idxB], FIRE_POWER);
  delay(DURATION_MS - openToFireMs);
  analogWrite(GATE_PINS[idxA], 0);
  analogWrite(GATE_PINS[idxB], 0);
  delay(openToFireMs);
  analogWrite(FIRE_PINS[idxA], 0);
  analogWrite(FIRE_PINS[idxB], 0);
  allOff();
}

void allOff() {
  for (int i = 0; i < 4; i++) {
    analogWrite(GATE_PINS[i], 0);
    analogWrite(FIRE_PINS[i], 0);
  }
}
