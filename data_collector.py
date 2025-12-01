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
    
    def load_simulation_data(self, days=7):
        """
        시뮬레이션용 데이터 생성
        Mendeley 오픈 데이터(Arduino 기반 토양 수분 데이터) 구조 참고
        
        실제 농업 환경을 모사:
        - 토양 수분: 일중 변화 + 급수 후 상승 + 자연 건조
        - 온도: 일교차 반영
        - 습도: 온도와 반비례 경향
        
        Args:
            days: 생성할 데이터 일수
        """
        print(f"[시뮬레이션] {days}일치 데이터 생성 중...")
        
        np.random.seed(42)  # 재현성을 위한 시드 고정
        
        # 시간 설정 (1시간 간격, days일치)
        hours = days * 24
        start_time = datetime.now() - timedelta(days=days)
        timestamps = [start_time + timedelta(hours=i) for i in range(hours)]
        
        data = []
        
        # 초기값
        soil_moisture = 55.0  # 초기 토양 수분 (%)
        last_watering = 0     # 마지막 급수 시점
        
        for i, ts in enumerate(timestamps):
            hour = ts.hour
            
            # === 온도 시뮬레이션 ===
            # 일교차: 새벽 4시 최저, 오후 2시 최고
            base_temp = 24.0  # 기준 온도
            daily_variation = 6.0 * np.sin((hour - 4) * np.pi / 12)
            noise = np.random.normal(0, 0.5)
            temperature = base_temp + daily_variation + noise
            temperature = np.clip(temperature, 15, 35)
            
            # === 습도 시뮬레이션 ===
            # 온도와 반비례, 새벽에 높고 낮에 낮음
            base_humid = 65.0
            humid_variation = -0.8 * daily_variation  # 온도 높으면 습도 낮음
            humid_noise = np.random.normal(0, 3)
            humidity = base_humid + humid_variation + humid_noise
            humidity = np.clip(humidity, 40, 90)
            
            # === 토양 수분 시뮬레이션 ===
            # 자연 건조율 (온도 높을수록, 낮 시간대에 더 빠름)
            evaporation_rate = 0.3 + 0.1 * (temperature - 20) / 10
            if 10 <= hour <= 16:  # 낮 시간대
                evaporation_rate *= 1.5
            
            # 토양 수분 감소
            soil_moisture -= evaporation_rate + np.random.normal(0, 0.2)
            
            # 급수 시뮬레이션 (수분이 30% 이하로 떨어지면 급수)
            if soil_moisture < 30:
                soil_moisture += np.random.uniform(25, 35)  # 급수로 상승
                last_watering = i
                print(f"  [급수 이벤트] {ts.strftime('%Y-%m-%d %H:%M')} - 수분 {soil_moisture:.1f}%로 상승")
            
            # 급수 직후 수분 서서히 분산
            if i - last_watering < 3:
                soil_moisture -= np.random.uniform(1, 3)
            
            soil_moisture = np.clip(soil_moisture, 15, 80)
            
            # 상단/하단 센서 (상단이 약간 더 건조)
            soil_upper = soil_moisture + np.random.uniform(-3, 0)
            soil_lower = soil_moisture + np.random.uniform(0, 3)
            
            data.append({
                'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
                'soil_upper': round(soil_upper, 1),
                'soil_lower': round(soil_lower, 1),
                'soil_moisture': round((soil_upper + soil_lower) / 2, 1),
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1)
            })
        
        self.data_buffer = data
        print(f"[시뮬레이션] {len(data)}개 데이터 생성 완료")
        
        # 데이터 통계 출력
        df = self.get_dataframe()
        print(f"\n📊 데이터 통계:")
        print(f"  - 토양 수분: {df['soil_moisture'].min():.1f}% ~ {df['soil_moisture'].max():.1f}% (평균: {df['soil_moisture'].mean():.1f}%)")
        print(f"  - 온도: {df['temperature'].min():.1f}°C ~ {df['temperature'].max():.1f}°C (평균: {df['temperature'].mean():.1f}°C)")
        print(f"  - 습도: {df['humidity'].min():.1f}% ~ {df['humidity'].max():.1f}% (평균: {df['humidity'].mean():.1f}%)")
        
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
