"""
AI 예측 모듈
- LinearRegression 기반 토양 수분 예측
- 특성 엔지니어링
- 모델 학습 및 평가
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import os

class SoilMoisturePredictor:
    """토양 수분 예측 AI 모델"""
    
    def __init__(self, model_path='soil_model.pkl'):
        """
        Args:
            model_path: 학습된 모델 저장 경로
        """
        self.model_path = model_path
        self.model = None
        self.feature_columns = [
            'soil_moisture',      # 현재 수분
            'soil_moisture_1h',   # 1시간 전 수분
            'moisture_change',    # 수분 변화율
            'temperature',        # 현재 온도
            'humidity',           # 현재 습도
            'hour'                # 시간대 (일중 변화 반영)
        ]
        
        # 기존 모델 로드
        if os.path.exists(model_path):
            self.load_model()
    
    def create_features(self, df):
        """
        특성 엔지니어링
        
        특성:
        1. 현재 토양 수분
        2. 1시간 전 토양 수분 (12개 행 이전 - 5분 간격 기준)
        3. 수분 변화율
        4. 온도
        5. 습도
        6. 시간대 (hour)
        
        타겟:
        - 1시간 후 토양 수분
        
        Args:
            df: 센서 데이터 DataFrame
            
        Returns:
            X: 특성 DataFrame
            y: 타겟 Series (1시간 후 수분)
        """
        df = df.copy()
        
        # 타임스탬프가 문자열이면 datetime으로 변환
        if df['timestamp'].dtype == 'object':
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 시간대 추출
        df['hour'] = df['timestamp'].dt.hour
        
        # 데이터가 1시간 간격인지 5분 간격인지 확인
        if len(df) > 1:
            time_diff = (df['timestamp'].iloc[1] - df['timestamp'].iloc[0]).total_seconds()
            if time_diff < 600:  # 10분 미만이면 5분 간격으로 추정
                lag = 12  # 5분 * 12 = 1시간
            else:
                lag = 1   # 1시간 간격
        else:
            lag = 1
        
        # 1시간 전 수분 (lag 개 행 이전)
        df['soil_moisture_1h'] = df['soil_moisture'].shift(lag)
        
        # 수분 변화율 (1시간 동안의 변화)
        df['moisture_change'] = df['soil_moisture'] - df['soil_moisture_1h']
        
        # 타겟: 1시간 후 수분
        df['target'] = df['soil_moisture'].shift(-lag)
        
        # NaN 제거
        df = df.dropna()
        
        if len(df) == 0:
            return None, None
        
        X = df[self.feature_columns]
        y = df['target']
        
        return X, y
    
    def train(self, df, test_size=0.2):
        """
        모델 학습
        
        Args:
            df: 학습 데이터 DataFrame
            test_size: 테스트 데이터 비율
            
        Returns:
            dict: 평가 지표 (R², RMSE, MAE)
        """
        X, y = self.create_features(df)
        
        if X is None or len(X) < 10:
            print("[학습] 데이터가 부족합니다. 최소 10개 이상의 데이터가 필요합니다.")
            return None
        
        # 학습/테스트 분할
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # 모델 학습
        self.model = LinearRegression()
        self.model.fit(X_train, y_train)
        
        # 예측 및 평가
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'r2': r2_score(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred)
        }
        
        # 모델 저장
        self.save_model()
        
        # 특성 중요도 출력
        print("\n📈 특성별 계수 (영향력):")
        for feature, coef in zip(self.feature_columns, self.model.coef_):
            importance = "↑" if coef > 0 else "↓"
            print(f"  - {feature}: {coef:.4f} {importance}")
        print(f"  - 절편(intercept): {self.model.intercept_:.4f}")
        
        return metrics
    
    def predict_next(self, df):
        """
        1시간 후 토양 수분 예측
        
        Args:
            df: 최근 센서 데이터 DataFrame (최소 12개 이상)
            
        Returns:
            float: 예측된 토양 수분 (%)
        """
        if self.model is None:
            print("[예측] 학습된 모델이 없습니다. 먼저 train()을 호출하세요.")
            return None
        
        X, _ = self.create_features(df)
        
        if X is None or len(X) == 0:
            print("[예측] 특성 생성 실패. 데이터를 확인하세요.")
            return None
        
        # 가장 최근 데이터로 예측
        latest_features = X.iloc[-1:].values
        prediction = self.model.predict(latest_features)[0]
        
        # 예측값 범위 제한 (0~100%)
        prediction = np.clip(prediction, 0, 100)
        
        return prediction
    
    def predict_sequence(self, df, hours=6):
        """
        다중 시간 예측 (N시간 후까지)
        
        Args:
            df: 최근 센서 데이터
            hours: 예측할 시간 수
            
        Returns:
            list: 시간별 예측값
        """
        predictions = []
        current_df = df.copy()
        
        for i in range(hours):
            pred = self.predict_next(current_df)
            if pred is None:
                break
            
            predictions.append({
                'hour': i + 1,
                'predicted_moisture': round(pred, 1)
            })
            
            # 예측값을 다음 입력으로 사용 (시뮬레이션)
            # 실제로는 더 정교한 방법 필요
            new_row = current_df.iloc[-1:].copy()
            new_row['soil_moisture'] = pred
            new_row['timestamp'] = pd.to_datetime(new_row['timestamp'].iloc[0]) + pd.Timedelta(hours=1)
            current_df = pd.concat([current_df, new_row], ignore_index=True)
        
        return predictions
    
    def save_model(self):
        """모델 저장"""
        if self.model:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            print(f"[저장] 모델 저장 완료: {self.model_path}")
    
    def load_model(self):
        """모델 로드"""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"[로드] 모델 로드 완료: {self.model_path}")
        except Exception as e:
            print(f"[로드 오류] {e}")
    
    def get_watering_recommendation(self, current_moisture, predicted_moisture, threshold=30):
        """
        급수 추천
        
        Args:
            current_moisture: 현재 토양 수분 (%)
            predicted_moisture: 예측된 토양 수분 (%)
            threshold: 급수 임계값 (%)
            
        Returns:
            dict: 급수 추천 정보
        """
        recommendation = {
            'current': current_moisture,
            'predicted': predicted_moisture,
            'threshold': threshold,
            'should_water': False,
            'urgency': 'none',
            'message': ''
        }
        
        if predicted_moisture < threshold:
            recommendation['should_water'] = True
            
            if predicted_moisture < threshold - 10:
                recommendation['urgency'] = 'high'
                recommendation['message'] = f"⚠️ 긴급! 예측 수분 {predicted_moisture:.1f}%가 매우 낮습니다. 즉시 급수하세요."
            elif predicted_moisture < threshold - 5:
                recommendation['urgency'] = 'medium'
                recommendation['message'] = f"💧 주의: 예측 수분 {predicted_moisture:.1f}%가 낮습니다. 급수를 권장합니다."
            else:
                recommendation['urgency'] = 'low'
                recommendation['message'] = f"💡 알림: 예측 수분 {predicted_moisture:.1f}%가 임계값에 근접합니다. 급수를 고려하세요."
        else:
            recommendation['message'] = f"✅ 양호: 예측 수분 {predicted_moisture:.1f}%로 충분합니다."
        
        return recommendation


# 테스트
if __name__ == "__main__":
    from data_collector import DataCollector
    
    # 데이터 로드
    collector = DataCollector()
    df = collector.load_simulation_data(days=7)
    
    # 모델 학습
    predictor = SoilMoisturePredictor('test_model.pkl')
    metrics = predictor.train(df)
    
    print(f"\n📊 모델 성능:")
    print(f"  - R² Score: {metrics['r2']:.4f} (1에 가까울수록 좋음)")
    print(f"  - RMSE: {metrics['rmse']:.2f}% (낮을수록 좋음)")
    print(f"  - MAE: {metrics['mae']:.2f}% (낮을수록 좋음)")
    
    # 예측 테스트
    print("\n🔮 예측 테스트:")
    prediction = predictor.predict_next(df)
    print(f"  1시간 후 예측 토양 수분: {prediction:.1f}%")
    
    # 다중 시간 예측
    print("\n📈 6시간 예측:")
    sequence = predictor.predict_sequence(df.tail(48), hours=6)
    for pred in sequence:
        status = "💧" if pred['predicted_moisture'] < 30 else "✅"
        print(f"  {pred['hour']}시간 후: {pred['predicted_moisture']}% {status}")
    
    # 급수 추천
    print("\n💡 급수 추천:")
    rec = predictor.get_watering_recommendation(
        current_moisture=df['soil_moisture'].iloc[-1],
        predicted_moisture=prediction
    )
    print(f"  {rec['message']}")
