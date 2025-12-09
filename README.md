# 🌱 AI기반 예측형 스마트 관개 시스템

> **팀명:** 내가 그린 스마트팜
> **대회:** 2025 SCNU 그린스마트팜 청소년 해커톤 경진대회

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Arduino](https://img.shields.io/badge/Arduino-Uno%20R3-00979D.svg)](https://www.arduino.cc/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📋 프로젝트 개요

IoT 센서 네트워크와 AI 머신러닝 예측 알고리즘을 결합하여, **토양 수분이 부족해지기 전에 미리 예측**하고 최적의 타이밍에 자동 급수하는 시스템입니다.

### 🎯 핵심 특징
- **🔮 예측형 관개**: 1시간 후 토양 수분을 예측하여 선제적 급수
- **🌡️ 듀얼 센서**: 상단/하단 토양 수분 센서로 정확한 측정
- **🤖 AI 기반**: RandomForest 모델로 수분 변화 예측 (R² 0.99+)
- **📊 실시간 시각화**: 센서 데이터, AI 예측, 통계 그래프 자동 생성
- **⚡ 자동 제어**: 예측 기반 전자밸브 + 펌프 제어

## 📁 파일 구조

```
project/
├── 📄 main.py                    # 메인 통합 모듈 (시리얼 통신 + AI + 제어)
├── 📄 data_collector.py          # 데이터 수집/저장 모듈
├── 📄 ai_predictor.py            # AI 예측 모델 (RandomForest)
├── 📄 visualizer.py              # 실시간 시각화 모듈
├── 📄 requirements.txt           # Python 패키지 목록
├── 📄 README.md                  # 프로젝트 설명서
├── 📄 HARDWARE_GUIDE.md          # 🔧 하드웨어 조립 가이드 (필독!)
├── 📄 soil_model.pkl             # 학습된 AI 모델 (자동 생성)
├── 📊 sensor_data.png            # 센서 데이터 그래프 (자동 생성)
├── 📊 prediction_analysis.png   # AI 예측 분석 그래프
├── 📊 daily_stats.png            # 일별 통계 그래프
└── 📁 arduino_code/
    └── smart_irrigation/
        └── smart_irrigation.ino  # 아두이노 펌웨어
```

## 🔧 하드웨어 구성

> 💡 **자세한 조립 가이드는 [HARDWARE_GUIDE.md](HARDWARE_GUIDE.md) 참조!**

| 부품 | 수량 | 연결 핀 | 용도 |
|------|------|---------|------|
| **Arduino Uno R3** | 1 | - | 메인 컨트롤러 |
| **토양 수분 센서** | 2 | A0 (상단), A1 (하단) | 토양 습도 측정 |
| **DHT11 온습도 센서** | 1 | D4 | 대기 온습도 측정 |
| **5V 릴레이 모듈** | 1 | D2 (제어), COM/NO (전원) | 12V 전원 스위칭 |
| **12V 전자밸브** | 1 | 릴레이 NO | 물 차단/개방 |
| **12V 워터펌프** | 1 | 전자밸브와 직렬 | 물 이송 |
| **12V 어댑터** | 1 | 릴레이 COM | 펌프/밸브 전원 |
| **USB 케이블** | 1 | 아두이노 - PC | 통신 + 5V 전원 |
| **점퍼선 세트** | 1 | - | 센서 연결 |
| **브레드보드** | 1 | - | 회로 구성 |

**총 예상 비용:** 약 25,000~35,000원

## 💻 소프트웨어 설치

### 1️⃣ Python 환경 설정

```bash
# Python 3.8 이상 필요
python --version

# 패키지 설치
pip install -r requirements.txt
```

**설치되는 패키지:**
- `pandas` - 데이터 처리
- `numpy` - 수치 계산
- `scikit-learn` - AI 모델 (RandomForest)
- `matplotlib` - 그래프 생성
- `pyserial` - 아두이노 통신

### 2️⃣ 아두이노 펌웨어 업로드

```bash
1. Arduino IDE 설치 (https://www.arduino.cc/)
2. DHT sensor library 설치 (라이브러리 관리자에서 "DHT sensor library" 검색)
3. arduino_code/smart_irrigation/smart_irrigation.ino 열기
4. 아두이노 우노 연결 후 업로드
```

## 🚀 사용 방법

### 🧪 시뮬레이션 모드 (테스트용)

아두이노 없이도 AI 모델 테스트 가능!

```bash
python main.py
```

**실행 결과:**
```
🌱 AI 예측형 스마트 관개 시스템 - 시뮬레이션 모드
==================================================

[1단계] 오픈 데이터 로드 중...
[시뮬레이션] 336개 고품질 데이터 생성 완료 (날씨 반영)

[2단계] AI 모델 학습 중...
  - R² Score: 0.9964
  - RMSE: 0.93%
  - MAE: 0.72%

[3단계] 예측 테스트...
  예측 1: 65.9% ✅ 수분 충분

[4단계] 시각화 생성 중...
  - sensor_data.png
  - prediction_analysis.png
  - daily_stats.png

✅ 시뮬레이션 완료!
```

---

### ⚡ 실제 모드 (해커톤 당일)

하드웨어 연결 후 실행:

```bash
# main.py 18번째 줄 수정
SERIAL_PORT = 'COM3'  # Windows
# 또는
SERIAL_PORT = '/dev/ttyUSB0'  # Mac/Linux

# 실행
python main.py --real
```

**동작 과정:**
1. 5분마다 센서 데이터 수집
2. 데이터가 24개 이상 쌓이면 AI 모델 자동 학습
3. 1시간 후 토양 수분 예측
4. 예측값 < 35% 이면 자동 급수 (180초)
5. 데이터는 `sensor_data.csv`에 자동 저장

## 🤖 AI 모델 상세

### 알고리즘
**RandomForest Regressor** (n_estimators=100, max_depth=10)
- 비선형 패턴 학습 가능
- 과적합 방지
- 특성 중요도 분석 가능

### 입력 특성 (12개)

| 특성 | 설명 | 중요도 |
|------|------|--------|
| `soil_moisture` | 현재 토양 수분 (%) | ⭐⭐⭐⭐⭐ 86.2% |
| `soil_moisture_1h` | 1시간 전 수분 | ⭐⭐ 8.8% |
| `soil_moisture_2h` | 2시간 전 수분 | ⭐ 3.0% |
| `soil_moisture_3h` | 3시간 전 수분 | 0.4% |
| `moisture_change` | 1시간 수분 변화율 | 0.1% |
| `moisture_change_3h` | 3시간 수분 변화율 | 0.1% |
| `moisture_rolling_mean` | 6시간 평균 수분 | 0.7% |
| `moisture_rolling_std` | 6시간 표준편차 | 0.3% |
| `temperature` | 현재 온도 (°C) | 0.1% |
| `humidity` | 현재 습도 (%) | 0.3% |
| `hour` | 시간대 (0~23) | 0.1% |
| `is_daytime` | 낮/밤 여부 (0/1) | 0.0% |

### 출력 (타겟)
- **1시간 후 토양 수분 (%)** 예측값

### 성능 지표

| 지표 | 의미 | 값 |
|------|------|-----|
| **R² Score** | 설명력 (1에 가까울수록 좋음) | **0.9964** ✅ |
| **RMSE** | 평균 오차 (낮을수록 좋음) | **0.93%** ✅ |
| **MAE** | 절대 오차 (낮을수록 좋음) | **0.72%** ✅ |

### 급수 로직

```python
if predicted_moisture < 35:  # 임계값
    send_water_command(duration=180)  # 3분 급수
    print("💧 급수 시작!")
else:
    print("✅ 수분 충분 - 급수 불필요")
```

## 🔌 회로 연결도

> 💡 **상세 조립 가이드는 [HARDWARE_GUIDE.md](HARDWARE_GUIDE.md) 참조!**

```
┌─────────────────────────────────────────────────────────┐
│                    아두이노 우노 R3                        │
│                                                           │
│  A0 ←─── 토양센서1 AOUT (상단)                            │
│  A1 ←─── 토양센서2 AOUT (하단)                            │
│  D4 ←─── DHT11 DATA (온습도)                              │
│  D2 ───→ 릴레이 IN                                        │
│                                                           │
│  5V ───┬─→ 센서들 VCC                                     │
│        └─→ 릴레이 VCC                                     │
│  GND ──┬─→ 센서들 GND                                     │
│        └─→ 릴레이 GND                                     │
│                                                           │
│  USB ←───────── PC (전원 + 통신)                          │
└─────────────────────────────────────────────────────────┘
                           │
                           │ D2 제어 신호
                           ↓
                    ┌──────────────┐
                    │  릴레이 모듈  │
                    │              │
                    │  COM ← 12V(+)│ ← 12V 어댑터
                    │  NO  → 밸브  │
                    └──────────────┘
                           │
                           ↓
                    전자밸브(+)
                           │
                           ↓
                    전자밸브(-)
                           │
                           ↓
                    펌프(+)
                           │
                           ↓
                    펌프(-) → 12V(-)

물의 흐름: 💧 물통 → 전자밸브 → 펌프 → 🌱 화분
```

## 📈 시각화 결과

시스템 실행 시 자동 생성되는 그래프:

### 1. `sensor_data.png` - 센서 데이터
- 토양 수분 변화 (상단/하단/평균)
- 온도 변화
- 습도 변화

### 2. `prediction_analysis.png` - AI 예측 분석
- 실제값 vs 예측값 비교
- 예측 오차 분포

### 3. `daily_stats.png` - 일별 통계
- 일별 최소/평균/최대값
- 급수 이벤트 표시

## 👥 팀원

| 이름 | 학번 | 역할 |
|------|------|------|
| **박현빈** | 20244300 | 팀장, AI 모델 개발, Python 백엔드 |
| **김가연** | 20234307 | 발표 자료 제작, 시연 준비 |
| **이영민** | 20234280 | 하드웨어 조립, 아두이노 코드 |

---

## 📚 참고 자료

### 공식 문서
- [Arduino 공식 사이트](https://www.arduino.cc/)
- [scikit-learn RandomForest 문서](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html)
- [DHT11 센서 라이브러리](https://github.com/adafruit/DHT-sensor-library)

### 데이터셋 참고
- Mendeley 오픈 데이터: Arduino 기반 토양 수분 측정 데이터셋
- 날씨 패턴 반영한 시뮬레이션 데이터 생성

---

## 🎯 해커톤 당일 체크리스트

### 출발 전 ✅
```
[ ] 노트북 (Python 환경 설치됨)
[ ] 아두이노 우노 + USB 케이블
[ ] 센서 3개 (토양 x2, DHT11 x1)
[ ] 릴레이 모듈
[ ] 펌프 + 전자밸브 + 12V 어댑터
[ ] 점퍼선 세트 + 브레드보드
[ ] 물통 + 물 + 호스
[ ] 테스트용 화분/흙
[ ] 예비 부품 (센서, 점퍼선)
```

### 현장 일정 (총 5시간)
```
0:00-0:30  하드웨어 조립
0:30-1:00  센서 보정 + 테스트
1:00-2:00  Python 연동 + AI 학습
2:00-3:00  통합 테스트 + 디버깅
3:00-4:00  발표 자료 준비
4:00-5:00  최종 시연 연습
```

---

## 🏆 프로젝트 특장점

### 기술적 차별화
1. **예측형 시스템**: 반응형(Reactive)이 아닌 예측형(Predictive) 관개
2. **듀얼 센서**: 토양 깊이별 수분 측정으로 정확도 향상
3. **고성능 AI**: R² 0.99+ 달성, 오차 1% 미만
4. **실시간 시각화**: 데이터 분석 그래프 자동 생성

### 실용성
- 저비용 구현 (약 3만원)
- 재사용 가능한 부품
- 확장 가능한 아키텍처 (센서 추가, 클라우드 연동 등)

---

## 🐛 문제 해결 (Troubleshooting)

| 문제 | 원인 | 해결 방법 |
|------|------|----------|
| 시리얼 포트 연결 실패 | USB 드라이버 미설치 | Arduino IDE 재설치 |
| DHT11 읽기 실패 | 연결 불량 | VCC/GND/DATA 재확인, 10K 저항 추가 |
| 릴레이 작동하나 펌프 안 돔 | 12V 전원 부족 | 어댑터 전압 확인, 극성 확인 |
| 센서 값이 이상함 | 보정 안 됨 | SOIL_DRY/SOIL_WET 값 재측정 |
| Python 오류 | 패키지 미설치 | `pip install -r requirements.txt` |

자세한 내용은 [HARDWARE_GUIDE.md](HARDWARE_GUIDE.md)의 "문제 해결" 섹션 참조

---

## 📜 라이선스

MIT License - 2025 내가 그린 스마트팜

---

## 📞 연락처

- **GitHub**: (저장소 URL)
- **Email**: (팀 대표 이메일)

---

**⭐ 2025 SCNU 그린스마트팜 청소년 해커톤 ⭐**
