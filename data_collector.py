"""
데이터 수집 및 저장 모듈
- 센서 데이터 수집
- CSV 파일 저장/로드
- 시뮬레이션 데이터 생성 (Mendeley 오픈 데이터 구조 참고)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

class DataCollector:
    """센서 데이터 수집 및 관리 클래스"""
    
    def __init__(self, csv_path='sensor_data.csv'):
        """
        Args:
            csv_path: CSV 파일 저장 경로
        """
        self.csv_path = csv_path
        self.data_buffer = []
        
        # 기존 데이터 로드
        if os.path.exists(csv_path):
            self.load_from_csv()
    
    def add_data(self, data):
        """
        새로운 센서 데이터 추가
        
        Args:
            data: dict with keys: soil_upper, soil_lower, soil_moisture, 
                  temperature, humidity
        """
        record = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'soil_upper': data.get('soil_upper', 0),
            'soil_lower': data.get('soil_lower', 0),
            'soil_moisture': data.get('soil_moisture', 0),
            'temperature': data.get('temperature', 0),
            'humidity': data.get('humidity', 0)
        }
        
        self.data_buffer.append(record)
        
        # 자동 저장 (100개마다)
        if len(self.data_buffer) % 100 == 0:
            self.save_to_csv()
    
    def get_dataframe(self):
        """버퍼 데이터를 DataFrame으로 반환"""
        if not self.data_buffer:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.data_buffer)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    def save_to_csv(self):
        """데이터를 CSV 파일로 저장"""
        if not self.data_buffer:
            print("[저장] 저장할 데이터가 없습니다.")
            return
        
        df = self.get_dataframe()
        df.to_csv(self.csv_path, index=False)
        print(f"[저장] {len(df)}개 데이터 저장 완료: {self.csv_path}")
    
    def load_from_csv(self):
        """CSV 파일에서 데이터 로드"""
        try:
            df = pd.read_csv(self.csv_path)
            self.data_buffer = df.to_dict('records')
            print(f"[로드] {len(self.data_buffer)}개 데이터 로드 완료")
        except Exception as e:
            print(f"[로드 오류] {e}")
    
    def load_simulation_data(self, days=14):
        """
        시뮬레이션용 고품질 데이터 생성
        Mendeley 오픈 데이터(Arduino 기반 토양 수분 데이터) 구조 참고
        
        개선된 시뮬레이션:
        - 날씨 패턴(맑음, 흐림, 비) 반영
        - 날씨에 따른 증발량 및 수분 변화 차별화
        - 비 오는 날 자연 급수 효과
        
        Args:
            days: 생성할 데이터 일수
        """
        print(f"[시뮬레이션] {days}일치 고품질 데이터 생성 중...")
        
        np.random.seed(42)  # 재현성을 위한 시드 고정
        
        # 시간 설정 (1시간 간격, days일치)
        hours = days * 24
        start_time = datetime.now() - timedelta(days=days)
        timestamps = [start_time + timedelta(hours=i) for i in range(hours)]
        
        data = []
        
        # 초기값
        soil_moisture = 55.0  # 초기 토양 수분 (%)
        last_watering = 0     # 마지막 급수 시점
        
        # 날씨 상태 (0: 맑음, 1: 흐림, 2: 비)
        # 하루 단위로 날씨 변경
        weather_pattern = []
        for _ in range(days):
            r = np.random.random()
            if r < 0.6: weather = 0      # 맑음 (60%)
            elif r < 0.85: weather = 1   # 흐림 (25%)
            else: weather = 2            # 비 (15%)
            weather_pattern.extend([weather] * 24)
            
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            current_weather = weather_pattern[i]
            
            # === 온도 시뮬레이션 ===
            # 맑음: 일교차 큼, 흐림/비: 일교차 작음
            base_temp = 24.0
            
            if current_weather == 0:   # 맑음
                daily_variation = 8.0 * np.sin((hour - 4) * np.pi / 12)
                temp_noise = 0.5
            elif current_weather == 1: # 흐림
                daily_variation = 4.0 * np.sin((hour - 4) * np.pi / 12)
                temp_noise = 0.3
                base_temp -= 2.0
            else:                      # 비
                daily_variation = 2.0 * np.sin((hour - 4) * np.pi / 12)
                temp_noise = 0.2
                base_temp -= 4.0
                
            noise = np.random.normal(0, temp_noise)
            temperature = base_temp + daily_variation + noise
            temperature = np.clip(temperature, 10, 40)
            
            # === 습도 시뮬레이션 ===
            # 비 > 흐림 > 맑음
            if current_weather == 0:   # 맑음
                base_humid = 50.0
                humid_var = -1.0 * daily_variation # 온도와 반비례
            elif current_weather == 1: # 흐림
                base_humid = 70.0
                humid_var = -0.5 * daily_variation
            else:                      # 비
                base_humid = 90.0
                humid_var = -0.2 * daily_variation
            
            humid_noise = np.random.normal(0, 2)
            humidity = base_humid + humid_var + humid_noise
            humidity = np.clip(humidity, 30, 100)
            
            # === 토양 수분 시뮬레이션 ===
            # 증발률: 온도 높음, 습도 낮음, 맑음 -> 높음
            evaporation = 0.0
            
            if current_weather == 0: # 맑음
                evaporation = 0.4 + 0.1 * (temperature - 20) / 10
                if 10 <= hour <= 16: evaporation *= 1.8 # 낮 시간 가속
            elif current_weather == 1: # 흐림
                evaporation = 0.1 + 0.05 * (temperature - 20) / 10
            else: # 비
                evaporation = -0.5 # 오히려 습기 참 (빗물)
            
            # 토양 수분 변화
            if current_weather == 2: # 비 오는 중
                soil_moisture += np.random.uniform(1.0, 3.0) # 자연 급수
                print(f"  [날씨] 비 내림 🌧️ ({ts.strftime('%m-%d %H:%M')}) - 수분 증가")
            else:
                soil_moisture -= evaporation + np.random.normal(0, 0.1)
            
            # 인공 급수 시뮬레이션 (수분이 25% 이하로 떨어지면 급수)
            # 비가 오지 않을 때만
            if soil_moisture < 25 and current_weather != 2:
                soil_moisture += np.random.uniform(30, 40)  # 급수로 대폭 상승
                last_watering = i
                print(f"  [급수 이벤트] 💧 {ts.strftime('%m-%d %H:%M')} - 수분 {soil_moisture:.1f}%로 회복")
            
            # 급수/비 직후 수분 서서히 분산 (drainage)
            if soil_moisture > 80:
                soil_moisture -= np.random.uniform(2, 4) # 배수 빠름
            elif i - last_watering < 3 and current_weather != 2:
                soil_moisture -= np.random.uniform(1, 2)
            
            soil_moisture = np.clip(soil_moisture, 10, 95)
            
            # 상단/하단 센서 차이 (비 올때는 상단이 훨씬 높음)
            if current_weather == 2:
                soil_upper = soil_moisture + np.random.uniform(2, 5)
                soil_lower = soil_moisture - np.random.uniform(1, 3)
            else:
                soil_upper = soil_moisture - np.random.uniform(1, 4) # 상단이 더 빨리 마름
                soil_lower = soil_moisture + np.random.uniform(0, 2)
            
            data.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'soil_upper': round(soil_upper, 1),
                'soil_lower': round(soil_lower, 1),
                'soil_moisture': round((soil_upper + soil_lower) / 2, 1),
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'weather': ['Sunny', 'Cloudy', 'Rainy'][current_weather] # 디버깅용
            })
        
        self.data_buffer = data
        print(f"[시뮬레이션] {len(data)}개 고품질 데이터 생성 완료 (날씨 반영)")
        
        # 데이터 통계 출력
        df = self.get_dataframe()
        print(f"\n📊 데이터 통계:")
        print(f"  - 토양 수분: {df['soil_moisture'].min():.1f}% ~ {df['soil_moisture'].max():.1f}%")
        print(f"  - 온도: {df['temperature'].min():.1f}°C ~ {df['temperature'].max():.1f}°C")
        print(f"  - 날씨 분포: 맑음 {weather_pattern.count(0)/24}일, 흐림 {weather_pattern.count(1)/24}일, 비 {weather_pattern.count(2)/24}일")
        
        return df
    
    def get_recent_data(self, hours=24):
        """최근 N시간 데이터 반환"""
        df = self.get_dataframe()
        if df.empty:
            return df
        
        cutoff = datetime.now() - timedelta(hours=hours)
        return df[df['timestamp'] >= cutoff]
    
    def clear_buffer(self):
        """버퍼 초기화"""
        self.data_buffer = []
        print("[초기화] 데이터 버퍼 초기화 완료")


# 테스트
if __name__ == "__main__":
    collector = DataCollector('test_data.csv')
    
    # 시뮬레이션 데이터 생성
    df = collector.load_simulation_data(days=7)
    
    # CSV 저장
    collector.save_to_csv()
    
    print("\n최근 24시간 데이터 샘플:")
    print(df.tail(24))
