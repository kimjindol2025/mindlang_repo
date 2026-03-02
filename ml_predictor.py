#!/usr/bin/env python3
"""
MindLang ML 예측 엔진
Day 8: 머신러닝 기반 의사결정 개선

구조:
├─ MetricsPredictor (메트릭 예측)
├─ ActionPredictor (액션 예측)
├─ ConfidenceEstimator (신뢰도 추정)
└─ ModelTrainer (온라인 학습)

알고리즘:
├─ 선형 회귀 (Trend 예측)
├─ 나이브 베이즈 (Action 분류)
└─ 신경망 시뮬레이션 (신뢰도)
"""

import json
import time
import math
from typing import Dict, List, Any, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsPredictor:
    """메트릭 예측 (선형 회귀)"""

    def __init__(self, window_size: int = 10):
        """
        메트릭 예측 초기화

        Args:
            window_size: 트렌드 계산을 위한 윈도우 크기
        """
        self.window_size = window_size
        self.history = defaultdict(lambda: deque(maxlen=window_size))
        self.trend_cache = {}

    def add_metric(self, metric_name: str, value: float, timestamp: float = None) -> None:
        """메트릭 추가"""
        if timestamp is None:
            timestamp = time.time()
        self.history[metric_name].append((timestamp, value))
        # 캐시 무효화
        if metric_name in self.trend_cache:
            del self.trend_cache[metric_name]

    def predict_next_value(self, metric_name: str) -> Dict[str, Any]:
        """다음 메트릭 값 예측 (선형 회귀)"""
        if metric_name not in self.history or len(self.history[metric_name]) < 2:
            return {
                'prediction': None,
                'confidence': 0.0,
                'trend': 'UNKNOWN',
                'error': 'Insufficient data'
            }

        # 캐시 확인
        if metric_name in self.trend_cache:
            return self.trend_cache[metric_name]

        history = list(self.history[metric_name])

        # 시간과 값 추출
        timestamps = [t for t, v in history]
        values = [v for t, v in history]

        # 선형 회귀 계산
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))

        # 기울기 (slope)와 절편 계산
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # 다음 값 예측
        next_x = n
        predicted_value = intercept + slope * next_x

        # 추세 판단
        if slope > 0.01:
            trend = 'INCREASING'
        elif slope < -0.01:
            trend = 'DECREASING'
        else:
            trend = 'STABLE'

        # 신뢰도 계산 (R-제곱)
        mean_y = sum_y / n
        ss_res = sum((values[i] - (intercept + slope * i)) ** 2 for i in range(n))
        ss_tot = sum((v - mean_y) ** 2 for v in values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = max(0, min(1, r_squared))

        result = {
            'prediction': predicted_value,
            'confidence': confidence,
            'trend': trend,
            'slope': slope,
            'current': values[-1],
            'history_length': n
        }

        self.trend_cache[metric_name] = result
        return result

    def predict_anomaly(self, metric_name: str, threshold: float = 2.0) -> Dict[str, Any]:
        """이상치 감지 (표준편차 기반)"""
        if metric_name not in self.history or len(self.history[metric_name]) < 2:
            return {'is_anomaly': False, 'z_score': 0.0}

        history = list(self.history[metric_name])
        values = [v for t, v in history]

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = math.sqrt(variance) if variance > 0 else 0

        current = values[-1]
        z_score = (current - mean) / std_dev if std_dev > 0 else 0

        return {
            'is_anomaly': abs(z_score) > threshold,
            'z_score': z_score,
            'mean': mean,
            'std_dev': std_dev,
            'current': current
        }


class ActionPredictor:
    """액션 예측 (나이브 베이즈)"""

    def __init__(self):
        """액션 예측 초기화"""
        # 액션별 조건부 확률 추적
        self.action_counts = defaultdict(int)
        self.action_metric_counts = defaultdict(lambda: defaultdict(int))
        self.total_samples = 0

    def add_training_sample(self, metrics: Dict[str, float], action: str) -> None:
        """학습 데이터 추가"""
        self.action_counts[action] += 1
        self.total_samples += 1

        # 메트릭을 범주로 변환 (상/중/하)
        error_rate = metrics.get('error_rate', 0)
        cpu_usage = metrics.get('cpu_usage', 50)
        memory_usage = metrics.get('memory_usage', 50)

        # 이산화 (Discretization)
        error_category = 'HIGH' if error_rate > 0.05 else ('LOW' if error_rate < 0.01 else 'MEDIUM')
        cpu_category = 'HIGH' if cpu_usage > 70 else ('LOW' if cpu_usage < 30 else 'MEDIUM')
        memory_category = 'HIGH' if memory_usage > 70 else ('LOW' if memory_usage < 30 else 'MEDIUM')

        # 조건부 확률 업데이트
        self.action_metric_counts[action][f'error={error_category}'] += 1
        self.action_metric_counts[action][f'cpu={cpu_category}'] += 1
        self.action_metric_counts[action][f'memory={memory_category}'] += 1

    def predict_action(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """액션 예측 (나이브 베이즈)"""
        if self.total_samples == 0:
            return {
                'predicted_action': 'CONTINUE',
                'confidence': 0.0,
                'probabilities': {},
                'error': 'No training data'
            }

        # 메트릭 이산화
        error_rate = metrics.get('error_rate', 0)
        cpu_usage = metrics.get('cpu_usage', 50)
        memory_usage = metrics.get('memory_usage', 50)

        error_category = 'HIGH' if error_rate > 0.05 else ('LOW' if error_rate < 0.01 else 'MEDIUM')
        cpu_category = 'HIGH' if cpu_usage > 70 else ('LOW' if cpu_usage < 30 else 'MEDIUM')
        memory_category = 'HIGH' if memory_usage > 70 else ('LOW' if memory_usage < 30 else 'MEDIUM')

        # 사전 확률 계산
        action_probs = {}
        for action in self.action_counts:
            prior = self.action_counts[action] / self.total_samples

            # 조건부 확률 계산 (라플라스 스무딩)
            features = [f'error={error_category}', f'cpu={cpu_category}', f'memory={memory_category}']
            likelihood = 1.0
            for feature in features:
                count = self.action_metric_counts[action].get(feature, 0)
                # 라플라스 스무딩: (count + 1) / (total + num_features)
                prob = (count + 1) / (self.action_counts[action] + 3)
                likelihood *= prob

            # 사후 확률 (정규화 안 함)
            action_probs[action] = prior * likelihood

        # 정규화
        total_prob = sum(action_probs.values())
        if total_prob > 0:
            action_probs = {k: v / total_prob for k, v in action_probs.items()}

        # 최고 확률 액션 선택
        best_action = max(action_probs, key=action_probs.get) if action_probs else 'CONTINUE'
        confidence = max(action_probs.values()) if action_probs else 0.0

        return {
            'predicted_action': best_action,
            'confidence': confidence,
            'probabilities': action_probs,
            'features': {
                'error_rate': error_category,
                'cpu_usage': cpu_category,
                'memory_usage': memory_category
            }
        }


class ConfidenceEstimator:
    """신뢰도 추정 (신경망 시뮬레이션)"""

    def __init__(self):
        """신뢰도 추정 초기화"""
        self.weights = {
            'metrics_agreement': 0.3,  # 메트릭들의 합의 정도
            'prediction_confidence': 0.25,  # 예측 신뢰도
            'historical_accuracy': 0.2,  # 역사적 정확도
            'trend_stability': 0.15,  # 추세 안정성
            'recency': 0.1  # 최근 데이터 가중치
        }
        self.accuracy_history = deque(maxlen=100)

    def estimate_confidence(self,
                          metrics_agreement: float,
                          prediction_conf: float,
                          trend_stability: float,
                          data_age_seconds: float = 0) -> Dict[str, Any]:
        """종합 신뢰도 추정"""

        # 최근성 가중치 계산 (1분 이내: 1.0, 5분: 0.5, 10분 이상: 0.2)
        if data_age_seconds < 60:
            recency_weight = 1.0
        elif data_age_seconds < 300:
            recency_weight = 0.5 + 0.5 * (1 - data_age_seconds / 300)
        else:
            recency_weight = 0.2

        # 역사적 정확도 계산
        if self.accuracy_history:
            historical_accuracy = sum(self.accuracy_history) / len(self.accuracy_history)
        else:
            historical_accuracy = 0.5

        # 가중 합산
        confidence = (
            self.weights['metrics_agreement'] * metrics_agreement +
            self.weights['prediction_confidence'] * prediction_conf +
            self.weights['historical_accuracy'] * historical_accuracy +
            self.weights['trend_stability'] * trend_stability +
            self.weights['recency'] * recency_weight
        )

        return {
            'overall_confidence': max(0, min(1, confidence)),
            'components': {
                'metrics_agreement': metrics_agreement,
                'prediction_confidence': prediction_conf,
                'historical_accuracy': historical_accuracy,
                'trend_stability': trend_stability,
                'recency_weight': recency_weight
            }
        }

    def record_accuracy(self, actual_vs_predicted_match: bool) -> None:
        """정확도 기록 (학습용)"""
        self.accuracy_history.append(1.0 if actual_vs_predicted_match else 0.0)


class ModelTrainer:
    """온라인 학습 모델"""

    def __init__(self):
        """모델 트레이너 초기화"""
        self.metrics_predictor = MetricsPredictor(window_size=20)
        self.action_predictor = ActionPredictor()
        self.confidence_estimator = ConfidenceEstimator()

        # 학습 통계
        self.training_samples = 0
        self.last_training_time = time.time()
        self.model_version = 1

    def train_sample(self, metrics: Dict[str, float], actual_action: str) -> None:
        """학습 샘플 추가"""
        # 메트릭 히스토리 추가
        for metric_name, value in metrics.items():
            self.metrics_predictor.add_metric(metric_name, value)

        # 액션 학습
        self.action_predictor.add_training_sample(metrics, actual_action)

        self.training_samples += 1

        # 100 샘플마다 모델 버전 업데이트
        if self.training_samples % 100 == 0:
            self.model_version += 1
            logger.info(f"🔄 Model updated to v{self.model_version} ({self.training_samples} samples)")

    def predict(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """통합 예측"""

        # 각 컴포넌트 예측
        error_pred = self.metrics_predictor.predict_next_value('error_rate')
        cpu_pred = self.metrics_predictor.predict_next_value('cpu_usage')

        action_pred = self.action_predictor.predict_action(metrics)

        # 메트릭 합의도 계산 (얼마나 일치하는가)
        predictions_agree = 0
        if error_pred.get('trend') == 'STABLE' and cpu_pred.get('trend') == 'STABLE':
            metrics_agreement = 0.9
        elif error_pred.get('trend') == cpu_pred.get('trend'):
            metrics_agreement = 0.7
        else:
            metrics_agreement = 0.4

        # 신뢰도 추정
        confidence_result = self.confidence_estimator.estimate_confidence(
            metrics_agreement=metrics_agreement,
            prediction_conf=action_pred['confidence'],
            trend_stability=min(0.9, (error_pred.get('confidence', 0) + cpu_pred.get('confidence', 0)) / 2),
            data_age_seconds=0
        )

        return {
            'action': action_pred['predicted_action'],
            'confidence': confidence_result['overall_confidence'],
            'action_confidence': action_pred['confidence'],
            'error_rate_trend': error_pred.get('trend', 'UNKNOWN'),
            'cpu_trend': cpu_pred.get('trend', 'UNKNOWN'),
            'error_rate_prediction': error_pred.get('prediction'),
            'cpu_prediction': cpu_pred.get('prediction'),
            'model_version': self.model_version,
            'training_samples': self.training_samples,
            'confidence_components': confidence_result['components']
        }

    def get_model_stats(self) -> Dict[str, Any]:
        """모델 통계"""
        return {
            'model_version': self.model_version,
            'training_samples': self.training_samples,
            'last_training_time': self.last_training_time,
            'metrics_tracked': len(self.metrics_predictor.history),
            'actions_learned': len(self.action_predictor.action_counts),
            'historical_accuracy': (
                sum(self.confidence_estimator.accuracy_history) / len(self.confidence_estimator.accuracy_history)
                if self.confidence_estimator.accuracy_history else 0.0
            )
        }


# ============================================================================
# 사용 예시 & 벤치마크
# ============================================================================

async def demo_ml_predictor():
    """ML 예측 엔진 데모"""
    print("\n" + "=" * 70)
    print("🤖 MindLang ML 예측 엔진 데모")
    print("=" * 70)

    trainer = ModelTrainer()

    # 학습 데이터 생성 (시뮬레이션)
    print("\n📚 모델 학습 중...")

    training_scenarios = [
        # (메트릭, 실제 액션)
        ({'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}, 'CONTINUE'),
        ({'error_rate': 0.01, 'cpu_usage': 31, 'memory_usage': 41}, 'CONTINUE'),
        ({'error_rate': 0.02, 'cpu_usage': 45, 'memory_usage': 50}, 'SCALE_UP'),
        ({'error_rate': 0.08, 'cpu_usage': 50, 'memory_usage': 60}, 'ROLLBACK'),
        ({'error_rate': 0.08, 'cpu_usage': 51, 'memory_usage': 61}, 'ROLLBACK'),
        ({'error_rate': 0.03, 'cpu_usage': 60, 'memory_usage': 55}, 'SCALE_UP'),
        ({'error_rate': 0.001, 'cpu_usage': 20, 'memory_usage': 30}, 'CONTINUE'),
        ({'error_rate': 0.09, 'cpu_usage': 85, 'memory_usage': 80}, 'ROLLBACK'),
        ({'error_rate': 0.02, 'cpu_usage': 40, 'memory_usage': 45}, 'SCALE_UP'),
        ({'error_rate': 0.01, 'cpu_usage': 32, 'memory_usage': 42}, 'CONTINUE'),
    ]

    for metrics, action in training_scenarios * 5:  # 50 샘플
        trainer.train_sample(metrics, action)

    print(f"✅ {trainer.training_samples} 샘플 학습 완료")

    # 테스트 예측
    print("\n🔮 새로운 데이터 예측:")
    test_metrics = {'error_rate': 0.02, 'cpu_usage': 50, 'memory_usage': 55}
    prediction = trainer.predict(test_metrics)

    print(f"\n입력 메트릭:")
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    print(f"\n✨ ML 예측 결과:")
    print(f"  추천 액션: {prediction['action']}")
    print(f"  신뢰도: {prediction['confidence']:.1%}")
    print(f"  에러율 추세: {prediction['error_rate_trend']}")
    print(f"  CPU 추세: {prediction['cpu_trend']}")
    print(f"  모델 버전: v{prediction['model_version']}")

    print(f"\n📊 모델 통계:")
    stats = trainer.get_model_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}" if key == 'historical_accuracy' else f"  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    return trainer


if __name__ == "__main__":
    import asyncio
    trainer = asyncio.run(demo_ml_predictor())
