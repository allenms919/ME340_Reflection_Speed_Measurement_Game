// =============================================
// Detector controller
// Board: Arduino Uno
// =============================================
//
// Uno → RPi  (every COUNT_INTERVAL_MS):
//   COUNT:N      N = 지금까지 지나간 공 누적 개수 (RESET으로 초기화)
//
// RPi → Uno:
//   RESET        누적 개수를 0으로 초기화

// ── Pin ──────────────────────────────────────
const int SENSOR_PIN = 2;
const bool ACTIVE_LOW = true;

// ── Ball counting ─────────────────────────────
int  total_count  = 0;
bool prevDetected = false;

// ── Timing ───────────────────────────────────
unsigned long lastSampleUs = 0;
const unsigned long SAMPLE_US = 1000;          // 1ms 센서 샘플링

unsigned long lastCountMs = 0;
const unsigned long COUNT_INTERVAL_MS = 100;   // 100ms마다 COUNT 출력

// ── Serial buffer ─────────────────────────────
char cmdBuf[32];

// ─────────────────────────────────────────────

void setup() {
  pinMode(SENSOR_PIN, INPUT_PULLUP);

  Serial.begin(115200);
  Serial.setTimeout(50);

  // 현재 센서 상태로 초기화 → 켜지는 순간 false rising edge 방지
  bool raw = (digitalRead(SENSOR_PIN) == LOW);
  prevDetected = ACTIVE_LOW ? raw : !raw;

  Serial.println("READY");
}

// ─────────────────────────────────────────────

void loop() {
  unsigned long nowUs = micros();
  unsigned long nowMs = millis();

  // ── 1ms 센서 샘플링 ───────────────────────
  if (nowUs - lastSampleUs >= SAMPLE_US) {
    lastSampleUs = nowUs;

    bool detected = ACTIVE_LOW
      ? (digitalRead(SENSOR_PIN) == LOW)
      : (digitalRead(SENSOR_PIN) == HIGH);

    if (detected && !prevDetected) {   // 0→1 rising edge = 공 1개 통과
      total_count++;
    }
    prevDetected = detected;
  }

  // ── COUNT 출력 (100ms마다) ────────────────
  if (nowMs - lastCountMs >= COUNT_INTERVAL_MS) {
    Serial.print("COUNT:");
    Serial.println(total_count);
    lastCountMs = nowMs;
  }

  // ── RPi 커맨드 처리 ───────────────────────
  if (Serial.available() > 0) {
    int len = Serial.readBytesUntil('\n', cmdBuf, sizeof(cmdBuf) - 1);
    cmdBuf[len] = '\0';
    if (len > 0 && cmdBuf[len - 1] == '\r') cmdBuf[--len] = '\0';

    if (strcmp(cmdBuf, "RESET") == 0) {
      total_count  = 0;
      prevDetected = false;
    }
  }
}
