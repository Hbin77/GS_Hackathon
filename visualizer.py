"""
실시간 시각화 모듈
- 토양 수분 그래프
- 예측 결과 시각화
- 센서 데이터 대시보드
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

class RealTimeVisualizer:
    """실시간 데이터 시각화 클래스"""
    
    def __init__(self, figsize=(14, 10)):
        """
        Args:
            figsize: 그래프 크기
        """
        self.figsize = figsize
        self.colors = {
            'moisture': '#2E86AB',      # 파랑
            'moisture_upper': '#A23B72', # 분홍
            'moisture_lower': '#F18F01', # 주황
            'temperature': '#C73E1D',    # 빨강
            'humidity': '#3B1F2B',       # 진한 보라
            'threshold': '#E74C3C',      # 임계값 빨강
            'prediction': '#27AE60'      # 예측 초록
        }
    
    def plot_sensor_data(self, df, save_path='sensor_plot.png'):
        """
        센서 데이터 시각화 (3개 서브플롯)
        
        Args:
            df: 센서 데이터 DataFrame
            save_path: 저장 경로
        """
        fig, axes = plt.subplots(3, 1, figsize=self.figsize, sharex=True)
        fig.suptitle('Smart Irrigation System - Sensor Data', fontsize=14, fontweight='bold')
        
        # 타임스탬프 변환
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 1. 토양 수분 그래프
        ax1 = axes[0]
        ax1.plot(df['timestamp'], df['soil_moisture'], 
                color=self.colors['moisture'], linewidth=2, label='Avg Moisture')
        ax1.fill_between(df['timestamp'], df['soil_upper'], df['soil_lower'],
                        alpha=0.3, color=self.colors['moisture'], label='Upper/Lower Range')
        ax1.axhline(y=30, color=self.colors['threshold'], linestyle='--', 
                   linewidth=1.5, label='Threshold (30%)')
        ax1.set_ylabel('Soil Moisture (%)')
        ax1.set_ylim(0, 100)
        ax1.legend(loc='upper right')
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Soil Moisture (Upper & Lower Sensors)')
        
        # 2. 온도 그래프
        ax2 = axes[1]
        ax2.plot(df['timestamp'], df['temperature'], 
                color=self.colors['temperature'], linewidth=2)
        ax2.set_ylabel('Temperature (C)')
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Temperature')
        
        # 3. 습도 그래프
        ax3 = axes[2]
        ax3.plot(df['timestamp'], df['humidity'], 
                color=self.colors['humidity'], linewidth=2)
        ax3.set_ylabel('Humidity (%)')
        ax3.set_xlabel('Time')
        ax3.grid(True, alpha=0.3)
        ax3.set_title('Humidity')
        
        # X축 포맷
        ax3.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax3.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[시각화] 센서 데이터 그래프 저장: {save_path}")
        plt.close()
    
    def plot_prediction(self, df, predictor, save_path='prediction_plot.png'):
        """
        예측 결과 시각화
        
        Args:
            df: 센서 데이터 DataFrame
            predictor: SoilMoisturePredictor 인스턴스
            save_path: 저장 경로
        """
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle('AI Prediction Analysis', fontsize=14, fontweight='bold')
        
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 1. 실제 vs 예측 비교
        ax1 = axes[0]
        
        # 특성 생성 및 예측
        X, y = predictor.create_features(df)
        if X is not None and predictor.model is not None:
            y_pred = predictor.model.predict(X)
            
            # 시간 인덱스 맞추기
            valid_timestamps = df['timestamp'].iloc[len(df)-len(y):]
            
            ax1.plot(valid_timestamps, y.values, 
                    color=self.colors['moisture'], linewidth=2, label='Actual', alpha=0.8)
            ax1.plot(valid_timestamps, y_pred, 
                    color=self.colors['prediction'], linewidth=2, 
                    linestyle='--', label='Predicted', alpha=0.8)
            ax1.axhline(y=30, color=self.colors['threshold'], 
                       linestyle=':', linewidth=1.5, label='Threshold')
            
            ax1.set_ylabel('Soil Moisture (%)')
            ax1.set_title('Actual vs Predicted Soil Moisture')
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
        
        # 2. 예측 오차 분포
        ax2 = axes[1]
        if X is not None and predictor.model is not None:
            errors = y.values - y_pred
            ax2.hist(errors, bins=30, color=self.colors['moisture'], 
                    alpha=0.7, edgecolor='black')
            ax2.axvline(x=0, color=self.colors['threshold'], 
                       linestyle='--', linewidth=2)
            ax2.set_xlabel('Prediction Error (%)')
            ax2.set_ylabel('Frequency')
            ax2.set_title(f'Prediction Error Distribution (Mean: {np.mean(errors):.2f}%, Std: {np.std(errors):.2f}%)')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[시각화] 예측 그래프 저장: {save_path}")
        plt.close()
    
    def plot_analysis(self, df, predictor, save_dir='.'):
        """
        종합 분석 시각화
        
        Args:
            df: 센서 데이터 DataFrame
            predictor: SoilMoisturePredictor 인스턴스
            save_dir: 저장 디렉토리
        """
        # 센서 데이터 그래프
        self.plot_sensor_data(df, os.path.join(save_dir, 'sensor_data.png'))
        
        # 예측 그래프
        self.plot_prediction(df, predictor, os.path.join(save_dir, 'prediction_analysis.png'))
        
        # 일별 통계 그래프
        self.plot_daily_stats(df, os.path.join(save_dir, 'daily_stats.png'))
        
        print(f"\n[시각화] 모든 그래프 저장 완료!")
    
    def plot_daily_stats(self, df, save_path='daily_stats.png'):
        """
        일별 통계 시각화
        
        Args:
            df: 센서 데이터 DataFrame
            save_path: 저장 경로
        """
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 일별 그룹화
        df['date'] = df['timestamp'].dt.date
        daily_stats = df.groupby('date').agg({
            'soil_moisture': ['mean', 'min', 'max'],
            'temperature': ['mean', 'min', 'max'],
            'humidity': ['mean', 'min', 'max']
        }).round(1)
        
        fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        fig.suptitle('Daily Statistics', fontsize=14, fontweight='bold')
        
        dates = daily_stats.index
        
        # 1. 일별 토양 수분
        ax1 = axes[0]
        ax1.fill_between(dates, 
                        daily_stats['soil_moisture']['min'],
                        daily_stats['soil_moisture']['max'],
                        alpha=0.3, color=self.colors['moisture'])
        ax1.plot(dates, daily_stats['soil_moisture']['mean'],
                color=self.colors['moisture'], linewidth=2, marker='o')
        ax1.axhline(y=30, color=self.colors['threshold'], linestyle='--')
        ax1.set_ylabel('Soil Moisture (%)')
        ax1.set_title('Daily Soil Moisture (Min/Avg/Max)')
        ax1.grid(True, alpha=0.3)
        
        # 2. 일별 온도
        ax2 = axes[1]
        ax2.fill_between(dates,
                        daily_stats['temperature']['min'],
                        daily_stats['temperature']['max'],
                        alpha=0.3, color=self.colors['temperature'])
        ax2.plot(dates, daily_stats['temperature']['mean'],
                color=self.colors['temperature'], linewidth=2, marker='o')
        ax2.set_ylabel('Temperature (C)')
        ax2.set_title('Daily Temperature (Min/Avg/Max)')
        ax2.grid(True, alpha=0.3)
        
        # 3. 일별 습도
        ax3 = axes[2]
        ax3.fill_between(dates,
                        daily_stats['humidity']['min'],
                        daily_stats['humidity']['max'],
                        alpha=0.3, color=self.colors['humidity'])
        ax3.plot(dates, daily_stats['humidity']['mean'],
                color=self.colors['humidity'], linewidth=2, marker='o')
        ax3.set_ylabel('Humidity (%)')
        ax3.set_xlabel('Date')
        ax3.set_title('Daily Humidity (Min/Avg/Max)')
        ax3.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[시각화] 일별 통계 그래프 저장: {save_path}")
        plt.close()
    
    def create_dashboard_html(self, df, predictor, output_path='dashboard.html'):
        """
        HTML 대시보드 생성 (발표용)
        
        Args:
            df: 센서 데이터 DataFrame
            predictor: SoilMoisturePredictor 인스턴스
            output_path: 출력 파일 경로
        """
        # 최신 데이터
        latest = df.iloc[-1]
        
        # 예측
        prediction = predictor.predict_next(df) if predictor.model else 0
        
        # 상태 결정
        if prediction < 30:
            status = "WATERING NEEDED"
            status_color = "#E74C3C"
        elif prediction < 40:
            status = "MONITORING"
            status_color = "#F39C12"
        else:
            status = "OPTIMAL"
            status_color = "#27AE60"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Smart Irrigation Dashboard</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.8;
        }}
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            font-size: 0.9em;
            opacity: 0.8;
        }}
        .card .value {{
            font-size: 2.5em;
            font-weight: bold;
        }}
        .card .unit {{
            font-size: 0.8em;
            opacity: 0.6;
        }}
        .status-card {{
            grid-column: span 2;
            background: {status_color};
        }}
        .status-card .value {{
            font-size: 1.8em;
        }}
        .moisture {{ color: #3498DB; }}
        .temp {{ color: #E74C3C; }}
        .humid {{ color: #9B59B6; }}
        .predict {{ color: #2ECC71; }}
        .footer {{
            text-align: center;
            padding: 20px;
            opacity: 0.6;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 AI Smart Irrigation System</h1>
        <p>Team: My Green Smart Farm | 2025 SCNU Hackathon</p>
    </div>
    
    <div class="dashboard">
        <div class="card">
            <h3>SOIL MOISTURE</h3>
            <div class="value moisture">{latest['soil_moisture']:.1f}</div>
            <div class="unit">%</div>
        </div>
        <div class="card">
            <h3>TEMPERATURE</h3>
            <div class="value temp">{latest['temperature']:.1f}</div>
            <div class="unit">°C</div>
        </div>
        <div class="card">
            <h3>HUMIDITY</h3>
            <div class="value humid">{latest['humidity']:.1f}</div>
            <div class="unit">%</div>
        </div>
        <div class="card">
            <h3>AI PREDICTION (1hr)</h3>
            <div class="value predict">{prediction:.1f}</div>
            <div class="unit">%</div>
        </div>
        <div class="card status-card">
            <h3>SYSTEM STATUS</h3>
            <div class="value">{status}</div>
        </div>
        <div class="card">
            <h3>UPPER SENSOR</h3>
            <div class="value moisture">{latest['soil_upper']:.1f}</div>
            <div class="unit">%</div>
        </div>
        <div class="card">
            <h3>LOWER SENSOR</h3>
            <div class="value moisture">{latest['soil_lower']:.1f}</div>
            <div class="unit">%</div>
        </div>
    </div>
    
    <div class="footer">
        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
        Threshold: 30% | Watering Duration: 180s
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[시각화] HTML 대시보드 저장: {output_path}")


# 테스트
if __name__ == "__main__":
    from data_collector import DataCollector
    from ai_predictor import SoilMoisturePredictor
    
    # 데이터 로드
    collector = DataCollector()
    df = collector.load_simulation_data(days=7)
    
    # 모델 학습
    predictor = SoilMoisturePredictor()
    predictor.train(df)
    
    # 시각화
    visualizer = RealTimeVisualizer()
    visualizer.plot_analysis(df, predictor)
    visualizer.create_dashboard_html(df, predictor)
    
    print("\n모든 시각화 완료!")
