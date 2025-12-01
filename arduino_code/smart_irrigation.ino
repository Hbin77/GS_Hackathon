/*
 * AI기반 예측형 스마트 관개 시스템 - 아두이노 코드
 * 팀: 내가 그린 스마트팜
 * 2025 SCNU 그린스마트팜 청소년 해커톤 경진대회
 * 
 * 하드웨어 연결:
 * - 토양 수분 센서 1 (상단): A0
 * - 토양 수분 센서 2 (하단): A1
 * - DHT11 온습도 센서: D4
 * - 릴레이 모듈: D2
 * 
 * 시리얼 통신:
 * - 전송 형식: "SOIL_UP:45.2,SOIL_LOW:48.5,TEMP:25.3,HUMID:60.5"
 * - 수신 형식: "WATER_ON:180" (180초 동안 급수)
 */

#include <DHT.h>

// ============== 핀 설정 ==============
#define SOIL_SENSOR_UPPER A0    // 상단 토양 수분 센서
#define SOIL_SENSOR_LOWER A1    // 하단 토양 수분 센서
#define DHT_PIN 4               // DHT11 센서 핀
#define RELAY_PIN 2             // 릴레이 제어 핀

// ============== DHT 설정 ==============
#define DHT_TYPE DHT11
DHT dht(DHT_PIN, DHT_TYPE);

// ============== 설정값 ==============
const unsigned long SENSOR_INTERVAL = 300000;  // 센서 읽기 주기 (5분 = 300000ms)
const int SOIL_DRY = 1023;      // 토양 센서 건조 시 값 (보정 필요)
const int SOIL_WET = 300;       // 토양 센서 습윤 시 값 (보정 필요)

// ============== 변수 ==============
unsigned long lastSensorTime = 0;
unsigned long wateringEndTime = 0;
bool isWatering = false;

void setup() {
  // 시리얼 통신 시작
  Serial.begin(9600);
  
  // 핀 모드 설정
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);  // 릴레이 OFF (NC 타입)
  
  // DHT 센서 시작
  dht.begin();
  
  // 초기화 메시지
  Serial.println("=================================");
  Serial.println("Smart Irrigation System Started!");
  Serial.println("Team: My Green Smart Farm");
  Serial.println("=================================");
  
  delay(2000);  // 센서 안정화 대기
}

void loop() {
  unsigned long currentTime = millis();
  
  // 1. 시리얼 명령 수신 확인
  checkSerialCommand();
  
  // 2. 급수 중인지 확인 및 종료 처리
  if (isWatering && currentTime >= wateringEndTime) {
    stopWatering();
  }
  
  // 3. 센서 읽기 주기 확인
  if (currentTime - lastSensorTime >= SENSOR_INTERVAL) {
    readAndSendSensorData();
    lastSensorTime = currentTime;
  }
}

// 센서 데이터 읽기 및 전송
void readAndSendSensorData() {
  // 토양 수분 센서 읽기
  int soilRawUpper = analogRead(SOIL_SENSOR_UPPER);
  int soilRawLower = analogRead(SOIL_SENSOR_LOWER);
  
  // 토양 수분을 %로 변환 (0~100%)
  float soilUpper = map(soilRawUpper, SOIL_DRY, SOIL_WET, 0, 100);
  float soilLower = map(soilRawLower, SOIL_DRY, SOIL_WET, 0, 100);
  
  // 범위 제한
  soilUpper = constrain(soilUpper, 0, 100);
  soilLower = constrain(soilLower, 0, 100);
  
  // DHT11 읽기
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();
  
  // DHT 읽기 실패 확인
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("ERROR:DHT_READ_FAILED");
    return;
  }
  
  // 시리얼로 데이터 전송
  Serial.print("SOIL_UP:");
  Serial.print(soilUpper, 1);
  Serial.print(",SOIL_LOW:");
  Serial.print(soilLower, 1);
  Serial.print(",TEMP:");
  Serial.print(temperature, 1);
  Serial.print(",HUMID:");
  Serial.println(humidity, 1);
}

// 시리얼 명령 확인
void checkSerialCommand() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // WATER_ON:duration 명령 파싱
    if (command.startsWith("WATER_ON:")) {
      int duration = command.substring(9).toInt();
      if (duration > 0 && duration <= 600) {  // 최대 10분
        startWatering(duration);
      } else {
        Serial.println("ERROR:INVALID_DURATION");
      }
    }
    // WATER_OFF 명령
    else if (command == "WATER_OFF") {
      stopWatering();
    }
    // STATUS 명령 - 현재 상태 확인
    else if (command == "STATUS") {
      sendStatus();
    }
    // TEST 명령 - 즉시 센서 데이터 전송
    else if (command == "TEST") {
      readAndSendSensorData();
    }
  }
}

// 급수 시작
void startWatering(int durationSeconds) {
  digitalWrite(RELAY_PIN, HIGH);  // 릴레이 ON -> 밸브/펌프 작동
  isWatering = true;
  wateringEndTime = millis() + (unsigned long)durationSeconds * 1000;
  
  Serial.print("WATERING_START:");
  Serial.println(durationSeconds);
}

// 급수 종료
void stopWatering() {
  digitalWrite(RELAY_PIN, LOW);  // 릴레이 OFF
  isWatering = false;
  wateringEndTime = 0;
  
  Serial.println("WATERING_STOP");
}

// 상태 전송
void sendStatus() {
  Serial.print("STATUS:");
  Serial.print(isWatering ? "WATERING" : "IDLE");
  Serial.print(",RELAY:");
  Serial.println(digitalRead(RELAY_PIN) ? "ON" : "OFF");
}

/*
 * ============== 센서 보정 방법 ==============
 * 
 * 1. 완전히 건조한 공기 중에서 센서 값 확인 -> SOIL_DRY 값 설정
 * 2. 물에 담근 상태에서 센서 값 확인 -> SOIL_WET 값 설정
 * 
 * 테스트 방법:
 * 1. 시리얼 모니터 열기 (9600 baud)
 * 2. "TEST" 입력 -> 현재 센서값 확인
 * 3. "WATER_ON:10" 입력 -> 10초 급수 테스트
 * 
 * ============== 주의사항 ==============
 * 
 * 1. 12V 전원은 릴레이 모듈의 COM 단자에 연결
 * 2. 전자밸브와 펌프는 직렬로 연결 (릴레이 NO 단자)
 * 3. 아두이노는 별도 USB 5V 전원 사용
 * 4. DHT11은 5V, GND, 데이터(D4) 연결
 * 
 * ============== 회로 연결도 ==============
 * 
 * [아두이노 우노]
 *   5V -----> DHT11 VCC
 *   GND ----> DHT11 GND
 *   D4 -----> DHT11 DATA (10K 풀업 저항 권장)
 *   
 *   A0 -----> 토양센서1 (상단)
 *   A1 -----> 토양센서2 (하단)
 *   
 *   D2 -----> 릴레이 IN
 *   5V -----> 릴레이 VCC
 *   GND ----> 릴레이 GND
 * 
 * [릴레이 모듈]
 *   COM ----> 12V 전원 (+)
 *   NO -----> 전자밸브/펌프 (+)
 *   
 * [전자밸브 + 펌프]
 *   전자밸브 (-) ---> 펌프 (+)
 *   펌프 (-) -------> 12V 전원 (-)
 */
