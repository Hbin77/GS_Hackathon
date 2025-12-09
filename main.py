"""
AI기반 예측형 스마트 관개 시스템
팀: 내가 그린 스마트팜
2025 SCNU 그린스마트팜 청소년 해커톤 경진대회

메인 통합 모듈: 시리얼 통신 + AI 예측 + 급수 제어
"""

import serial
import time
import threading
from datetime import datetime
from data_collector import DataCollector
from ai_predictor import SoilMoisturePredictor
from visualizer import RealTimeVisualizer

# ============== 설정 ==============
SERIAL_PORT = ''  # Windows: 'COM3', Linux/Mac: '/dev/ttyUSB0'
BAUD_RATE = 9600
MOISTURE_THRESHOLD = 35.0  # 급수 임계값 (%)
WATERING_DURATION = 180    # 급수 시간 (초)
PREDICTION_INTERVAL = 300  # 예측 주기 (5분 = 300초)

class SmartIrrigationSystem:
    """스마트 관개 시스템 메인 클래스"""
    
    def __init__(self, port=SERIAL_PORT, baud_rate=BAUD_RATE, simulation=True):
        """
        Args:
            port: 시리얼 포트
            baud_rate: 통신 속도
            simulation: True면 시뮬레이션 모드 (아두이노 없이 테스트)
        """
        self.simulation = simulation
        self.running = False
        self.serial_conn = None
        
        # 모듈 초기화
        self.collector = DataCollector()
        self.predictor = SoilMoisturePredictor()
        self.visualizer = None  # 필요시 초기화
        
        # 시리얼 연결 (시뮬레이션 모드가 아닐 때만)
        if not simulation:
            try:
                self.serial_conn = serial.Serial(port, baud_rate, timeout=1)
                print(f"[시리얼] {port} 연결 성공")
                time.sleep(2)  # 아두이노 리셋 대기
            except Exception as e:
                print(f"[시리얼] 연결 실패: {e}")
                print("[시리얼] 시뮬레이션 모드로 전환합니다.")
                self.simulation = True
    
    def parse_sensor_data(self, line):
        """
        아두이노에서 받은 데이터 파싱
        형식: "SOIL:45.2,TEMP:25.3,HUMID:60.5"
        
        Returns:
            dict: {'soil_upper': float, 'soil_lower': float, 'temperature': float, 'humidity': float}
        """
        try:
            data = {}
            parts = line.strip().split(',')
            
            for part in parts:
                key, value = part.split(':')
                if key == 'SOIL_UP':
                    data['soil_upper'] = float(value)
                elif key == 'SOIL_LOW':
                    data['soil_lower'] = float(value)
                elif key == 'TEMP':
                    data['temperature'] = float(value)
                elif key == 'HUMID':
                    data['humidity'] = float(value)
            
            # 평균 토양 수분 계산
            if 'soil_upper' in data and 'soil_lower' in data:
                data['soil_moisture'] = (data['soil_upper'] + data['soil_lower']) / 2
            
            return data
            
        except Exception as e:
            print(f"[파싱 오류] {e}: {line}")
            return None
    
    def send_water_command(self, duration=WATERING_DURATION):
        """
        아두이노에 급수 명령 전송
        
        Args:
            duration: 급수 시간 (초)
        """
        command = f"WATER_ON:{duration}\n"
        
        if self.simulation:
            print(f"[시뮬레이션] 급수 명령 전송: {command.strip()}")
        else:
            try:
                self.serial_conn.write(command.encode())
                print(f"[급수] 명령 전송: {duration}초 동안 급수")
            except Exception as e:
                print(f"[급수 오류] {e}")
    
    def check_and_water(self):
        """예측 기반 급수 판단"""
        # 충분한 데이터가 있는지 확인 (최소 12시간 = 144개 데이터)
        if len(self.collector.data_buffer) < 12:
            print(f"[예측] 데이터 부족 ({len(self.collector.data_buffer)}/12), 대기 중...")
            return
        
        # AI 모델 학습 및 예측
        df = self.collector.get_dataframe()
        
        if self.predictor.model is None:
            print("[예측] 모델 학습 중...")
            self.predictor.train(df)
        
        # 1시간 후 토양 수분 예측
        prediction = self.predictor.predict_next(df)
        
        if prediction is not None:
            print(f"[예측] 1시간 후 토양 수분: {prediction:.1f}%")
            
            # 임계값 미만이면 급수
            if prediction < MOISTURE_THRESHOLD:
                print(f"[판단] 예측값 {prediction:.1f}% < 임계값 {MOISTURE_THRESHOLD}%")
                print("[판단] 급수를 시작합니다!")
                self.send_water_command()
            else:
                print(f"[판단] 수분 충분 - 급수 불필요")
    
    def read_serial_data(self):
        """시리얼 데이터 읽기 (스레드)"""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    
                    if line:
                        data = self.parse_sensor_data(line)
                        if data:
                            self.collector.add_data(data)
                            print(f"[수신] 토양수분: {data.get('soil_moisture', 0):.1f}%, "
                                  f"온도: {data.get('temperature', 0):.1f}°C, "
                                  f"습도: {data.get('humidity', 0):.1f}%")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[시리얼 읽기 오류] {e}")
                time.sleep(1)
    
    def run_simulation(self):
        """시뮬레이션 모드 실행"""
        print("\n" + "="*50)
        print("🌱 AI 예측형 스마트 관개 시스템 - 시뮬레이션 모드")
        print("="*50)
        
        # 시뮬레이션 데이터 로드
        print("\n[1단계] 오픈 데이터 로드 중...")
        self.collector.load_simulation_data()
        
        # 모델 학습
        print("\n[2단계] AI 모델 학습 중...")
        df = self.collector.get_dataframe()
        metrics = self.predictor.train(df)
        
        if metrics:
            print(f"  - 학습 완료!")
            print(f"  - R² Score: {metrics['r2']:.4f}")
            print(f"  - RMSE: {metrics['rmse']:.2f}%")
            print(f"  - MAE: {metrics['mae']:.2f}%")
        
        # 예측 테스트
        print("\n[3단계] 예측 테스트...")
        recent_data = df.tail(24)  # 최근 24시간 데이터
        
        for i in range(5):
            test_df = recent_data.iloc[:12+i]
            prediction = self.predictor.predict_next(test_df)
            actual = recent_data.iloc[12+i]['soil_moisture'] if 12+i < len(recent_data) else None
            
            status = "💧 급수 필요" if prediction < MOISTURE_THRESHOLD else "✅ 수분 충분"
            
            print(f"  예측 {i+1}: {prediction:.1f}% {status}", end="")
            if actual:
                print(f" (실제: {actual:.1f}%)")
            else:
                print()
        
        # 시각화
        print("\n[4단계] 시각화 생성 중...")
        self.visualizer = RealTimeVisualizer()
        self.visualizer.plot_analysis(df, self.predictor)
        
        print("\n" + "="*50)
        print("✅ 시뮬레이션 완료!")
        print("="*50)
    
    def run(self):
        """실제 모드 실행 (아두이노 연결)"""
        print("\n" + "="*50)
        print("🌱 AI 예측형 스마트 관개 시스템 - 실행 모드")
        print("="*50)
        
        self.running = True
        
        # 시리얼 읽기 스레드 시작
        serial_thread = threading.Thread(target=self.read_serial_data)
        serial_thread.daemon = True
        serial_thread.start()
        
        print("\n시스템 시작! (Ctrl+C로 종료)")
        print(f"예측 주기: {PREDICTION_INTERVAL}초")
        print(f"급수 임계값: {MOISTURE_THRESHOLD}%\n")
        
        last_prediction_time = 0
        
        try:
            while self.running:
                current_time = time.time()
                
                # 예측 주기마다 급수 판단
                if current_time - last_prediction_time >= PREDICTION_INTERVAL:
                    self.check_and_water()
                    last_prediction_time = current_time
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n시스템 종료 중...")
            self.running = False
            
            if self.serial_conn:
                self.serial_conn.close()
            
            # 데이터 저장
            self.collector.save_to_csv()
            print("데이터 저장 완료!")


def main():
    """메인 함수"""
    import sys
    
    print("\n🌱 AI기반 예측형 스마트 관개 시스템")
    print("팀: 내가 그린 스마트팜\n")
    
    # 실행 모드 선택
    if len(sys.argv) > 1 and sys.argv[1] == '--real':
        # 실제 모드: python main.py --real
        system = SmartIrrigationSystem(simulation=False)
        system.run()
    else:
        # 시뮬레이션 모드: python main.py
        system = SmartIrrigationSystem(simulation=True)
        system.run_simulation()


if __name__ == "__main__":
    main()
