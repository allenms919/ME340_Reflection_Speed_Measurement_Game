// ===============================
// 4-Launcher Solenoid Controller
// Board: Arduino Mega
// ===============================

// Launcher 1: D2, D3
const int launcher1Solenoid1Pin = 2;
const int launcher1Solenoid2Pin = 3;

// Launcher 2: D5, D6
const int launcher2Solenoid1Pin = 5;
const int launcher2Solenoid2Pin = 6;

// Launcher 3: D9, D10
const int launcher3Solenoid1Pin = 9;
const int launcher3Solenoid2Pin = 10;

// Launcher 4: D12, D13
const int launcher4Solenoid1Pin = 12;
const int launcher4Solenoid2Pin = 13;

// PWM values
const int pullPower = 255;   // 100% duty cycle
const int holdPower = 127;   // 약 50% duty cycle
const int offPower  = 0;

// Timing values
const int solenoidGapTime = 20;   // 첫 번째 솔레노이드 작동 후 두 번째 솔레노이드까지 간격
const int pullTime = 80;          // 최대 힘으로 당기는 시간
const int holdTime = 100;         // 유지 시간

void setup() {
  pinMode(launcher1Solenoid1Pin, OUTPUT);
  pinMode(launcher1Solenoid2Pin, OUTPUT);

  pinMode(launcher2Solenoid1Pin, OUTPUT);
  pinMode(launcher2Solenoid2Pin, OUTPUT);

  pinMode(launcher3Solenoid1Pin, OUTPUT);
  pinMode(launcher3Solenoid2Pin, OUTPUT);

  pinMode(launcher4Solenoid1Pin, OUTPUT);
  pinMode(launcher4Solenoid2Pin, OUTPUT);

  // 처음에는 모든 솔레노이드 OFF
  allSolenoidsOff();

  // Serial communication start
  Serial.begin(9600);
  Serial.println("Ready.");
  Serial.println("Enter 1 for Launcher 1: pins 2, 3");
  Serial.println("Enter 2 for Launcher 2: pins 5, 6");
  Serial.println("Enter 3 for Launcher 3: pins 9, 10");
  Serial.println("Enter 4 for Launcher 4: pins 12, 13");
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == '1') {
      Serial.println("Launcher 1 activated. Pins 2, 3");
      activateLauncher(launcher1Solenoid1Pin, launcher1Solenoid2Pin);
      Serial.println("Launcher 1 done.");
    }

    else if (command == '2') {
      Serial.println("Launcher 2 activated. Pins 5, 6");
      activateLauncher(launcher2Solenoid1Pin, launcher2Solenoid2Pin);
      Serial.println("Launcher 2 done.");
    }

    else if (command == '3') {
      Serial.println("Launcher 3 activated. Pins 9, 10");
      activateLauncher(launcher3Solenoid1Pin, launcher3Solenoid2Pin);
      Serial.println("Launcher 3 done.");
    }

    else if (command == '4') {
      Serial.println("Launcher 4 activated. Pins 12, 13");
      activateLauncher(launcher4Solenoid1Pin, launcher4Solenoid2Pin);
      Serial.println("Launcher 4 done.");
    }

    else if (command == '\n' || command == '\r') {
      // 시리얼 모니터에서 줄바꿈 문자가 들어오는 경우 무시
    }

    else {
      Serial.println("Invalid input. Enter 1, 2, 3, or 4.");
    }
  }
}

// 특정 런처의 두 솔레노이드를 동일한 패턴으로 작동시키는 함수
void activateLauncher(int solenoid1Pin, int solenoid2Pin) {
  // 안전을 위해 시작 전 전체 OFF
  allSolenoidsOff();

  // 1단계: 첫 번째 솔레노이드 최대 힘으로 작동
  analogWrite(solenoid1Pin, pullPower);
  delay(solenoidGapTime);

  // 2단계: 두 번째 솔레노이드 최대 힘으로 작동
  analogWrite(solenoid2Pin, pullPower);
  delay(pullTime);

  // 3단계: 두 솔레노이드 유지 전력으로 낮춤
  analogWrite(solenoid1Pin, holdPower);
  analogWrite(solenoid2Pin, holdPower);
  delay(holdTime);

  // 4단계: 해당 런처 솔레노이드 OFF
  analogWrite(solenoid1Pin, offPower);
  analogWrite(solenoid2Pin, offPower);

  // 안전을 위해 전체 OFF
  allSolenoidsOff();
}

// 모든 솔레노이드를 끄는 함수
void allSolenoidsOff() {
  analogWrite(launcher1Solenoid1Pin, offPower);
  analogWrite(launcher1Solenoid2Pin, offPower);

  analogWrite(launcher2Solenoid1Pin, offPower);
  analogWrite(launcher2Solenoid2Pin, offPower);

  analogWrite(launcher3Solenoid1Pin, offPower);
  analogWrite(launcher3Solenoid2Pin, offPower);

  analogWrite(launcher4Solenoid1Pin, offPower);
  analogWrite(launcher4Solenoid2Pin, offPower);
}
