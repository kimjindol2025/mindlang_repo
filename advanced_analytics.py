#!/usr/bin/env python3
"""
MindLang 고급 분석 및 예측 엔진
머신러닝 기반 시스템 행동 예측

기능:
- 시계열 데이터 분석
- 추세 예측
- 이상 탐지
- 상관관계 분석
- 의사결정 최적화 제안
"""

import json
import statistics
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class Prediction:
    """예측 결과"""
    metric: str
    current_value: float
    predicted_value: float
    confidence: float
    time_horizon: str  # 1min, 5min, 1hour, 1day
    trend: str  # up, down, stable
    recommendation: str


@dataclass
class Anomaly:
    """이상 탐지"""
    timestamp: float
    metric: str
    value: float
    expected_range: Tuple[float, float]
    severity: str  # info, warning, critical


class AdvancedAnalytics:
    """고급 분석 엔진"""

    def __init__(self):
        self.metrics_history: Dict[str, List[float]] = {}
        self.timestamps: Dict[str, List[float]] = {}

    def add_metric(self, metric_name: str, value: float, timestamp: float = None):
        """메트릭 추가"""
        if timestamp is None:
            import time
            timestamp = time.time()

        if metric_name not in self.metrics_history:
            self.metrics_history[metric_name] = []
            self.timestamps[metric_name] = []

        self.metrics_history[metric_name].append(value)
        self.timestamps[metric_name].append(timestamp)

        # 최근 1000개만 유지
        if len(self.metrics_history[metric_name]) > 1000:
            self.metrics_history[metric_name].pop(0)
            self.timestamps[metric_name].pop(0)

    def predict_metric(self, metric_name: str, horizon: str = '1hour') -> Optional[Prediction]:
        """메트릭 예측"""
        if metric_name not in self.metrics_history:
            return None

        values = self.metrics_history[metric_name]
        if len(values) < 3:
            return None

        # 현재 값
        current_value = values[-1]

        # 선형 회귀로 추세 계산
        trend_slope = self._calculate_trend(values)
        mean_value = statistics.mean(values)
        stdev_value = statistics.stdev(values) if len(values) > 1 else 0

        # 시간 지평선에 따른 예측
        horizon_multiplier = {
            '1min': 1,
            '5min': 5,
            '1hour': 60,
            '1day': 1440
        }.get(horizon, 1)

        predicted_value = current_value + (trend_slope * horizon_multiplier)

        # 신뢰도 계산 (과거 추세의 안정성)
        confidence = self._calculate_confidence(values)

        # 추세 판정
        if trend_slope > 0.01:
            trend = "상승"
        elif trend_slope < -0.01:
            trend = "하강"
        else:
            trend = "안정"

        # 추천 생성
        recommendation = self._generate_recommendation(
            metric_name, current_value, predicted_value, trend
        )

        return Prediction(
            metric=metric_name,
            current_value=current_value,
            predicted_value=predicted_value,
            confidence=confidence,
            time_horizon=horizon,
            trend=trend,
            recommendation=recommendation
        )

    def detect_anomalies(self, metric_name: str, sensitivity: float = 2.0) -> List[Anomaly]:
        """이상 탐지"""
        if metric_name not in self.metrics_history:
            return []

        values = self.metrics_history[metric_name]
        if len(values) < 10:
            return []

        mean = statistics.mean(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0

        anomalies = []
        current_value = values[-1]
        current_timestamp = self.timestamps[metric_name][-1]

        # 표준편차 기반 이상 탐지
        lower_bound = mean - (stdev * sensitivity)
        upper_bound = mean + (stdev * sensitivity)

        if current_value < lower_bound or current_value > upper_bound:
            # 심각도 판정
            distance = abs(current_value - mean)
            deviation_ratio = distance / stdev if stdev > 0 else 0

            if deviation_ratio > 3.0:
                severity = "critical"
            elif deviation_ratio > 2.5:
                severity = "warning"
            else:
                severity = "info"

            anomalies.append(Anomaly(
                timestamp=current_timestamp,
                metric=metric_name,
                value=current_value,
                expected_range=(lower_bound, upper_bound),
                severity=severity
            ))

        return anomalies

    def analyze_correlation(self, metric1: str, metric2: str) -> Dict:
        """두 메트릭 간 상관관계 분석"""
        if (metric1 not in self.metrics_history or
                metric2 not in self.metrics_history):
            return {}

        values1 = self.metrics_history[metric1]
        values2 = self.metrics_history[metric2]

        # 길이 동기화
        min_len = min(len(values1), len(values2))
        if min_len < 2:
            return {}

        values1 = values1[-min_len:]
        values2 = values2[-min_len:]

        # 피어슨 상관계수 계산
        correlation = self._calculate_pearson_correlation(values1, values2)

        return {
            'metric1': metric1,
            'metric2': metric2,
            'correlation': correlation,
            'interpretation': self._interpret_correlation(correlation),
            'recommendation': self._recommend_action(metric1, metric2, correlation)
        }

    def _calculate_trend(self, values: List[float]) -> float:
        """추세 계산 (선형 회귀의 기울기)"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_mean = (n - 1) / 2  # 인덱스의 평균
        y_mean = statistics.mean(values)

        numerator = sum(
            (i - x_mean) * (values[i] - y_mean)
            for i in range(n)
        )

        denominator = sum(
            (i - x_mean) ** 2
            for i in range(n)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_confidence(self, values: List[float]) -> float:
        """신뢰도 계산"""
        if len(values) < 3:
            return 0.0

        # 최근 값들의 변동성이 낮을수록 신뢰도 높음
        recent_values = values[-10:]
        stdev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0
        mean = statistics.mean(recent_values)

        if mean == 0:
            return 0.5

        cv = stdev / abs(mean)  # 변동계수

        # 변동계수에 따른 신뢰도
        if cv < 0.1:
            return 0.95
        elif cv < 0.2:
            return 0.85
        elif cv < 0.5:
            return 0.70
        else:
            return 0.50

    def _calculate_pearson_correlation(self, values1: List[float], values2: List[float]) -> float:
        """피어슨 상관계수"""
        n = len(values1)
        if n < 2:
            return 0.0

        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        stdev1 = statistics.stdev(values1) if n > 1 else 0
        stdev2 = statistics.stdev(values2) if n > 1 else 0

        if stdev1 == 0 or stdev2 == 0:
            return 0.0

        covariance = sum(
            (values1[i] - mean1) * (values2[i] - mean2)
            for i in range(n)
        ) / n

        correlation = covariance / (stdev1 * stdev2)
        return max(-1.0, min(1.0, correlation))

    def _interpret_correlation(self, correlation: float) -> str:
        """상관계수 해석"""
        abs_corr = abs(correlation)

        if abs_corr > 0.8:
            strength = "매우 강한"
        elif abs_corr > 0.6:
            strength = "강한"
        elif abs_corr > 0.4:
            strength = "중간"
        elif abs_corr > 0.2:
            strength = "약한"
        else:
            strength = "매우 약한"

        direction = "양의" if correlation > 0 else "음의"

        return f"{strength} {direction} 상관관계"

    def _recommend_action(self, metric1: str, metric2: str, correlation: float) -> str:
        """행동 추천"""
        if abs(correlation) > 0.8:
            return f"{metric1}과 {metric2}는 강하게 연관됨 - 한쪽 변화를 모니터링"
        elif abs(correlation) > 0.5:
            return f"{metric1}과 {metric2}는 연관성 있음 - 함께 모니터링 권장"
        else:
            return f"{metric1}과 {metric2}는 독립적 - 별도 처리 가능"

    def _generate_recommendation(self, metric: str, current: float, predicted: float, trend: str) -> str:
        """의사결정 추천"""
        change_percent = abs((predicted - current) / current * 100) if current != 0 else 0

        if trend == "상승":
            if change_percent > 20:
                return f"⚠️  {metric} 급증 예상 - 사전 대응 필요"
            elif change_percent > 10:
                return f"📈 {metric} 증가 추세 - 모니터링 강화"
            else:
                return f"📊 {metric} 약간 증가 - 정상 모니터링"

        elif trend == "하강":
            if change_percent > 20:
                return f"✅ {metric} 급감 예상 - 리소스 절감 기회"
            elif change_percent > 10:
                return f"📉 {metric} 감소 추세 - 정상"
            else:
                return f"📊 {metric} 약간 감소 - 정상 모니터링"

        else:
            return f"✅ {metric} 안정적 - 현재 정책 유지"

    def get_system_health_score(self) -> Dict:
        """시스템 건강도 점수"""
        scores = {}

        for metric_name in self.metrics_history:
            values = self.metrics_history[metric_name]
            if len(values) < 2:
                continue

            # 변동성 점수 (낮을수록 좋음)
            stdev = statistics.stdev(values)
            mean = statistics.mean(values)

            if mean == 0:
                volatility_score = 50
            else:
                cv = stdev / abs(mean)
                volatility_score = max(0, 100 - (cv * 100))

            # 현재 값 정상성 점수
            current = values[-1]
            expected_range = (mean - 2 * stdev, mean + 2 * stdev)

            if expected_range[0] <= current <= expected_range[1]:
                normality_score = 100
            else:
                distance = min(
                    abs(current - expected_range[0]),
                    abs(current - expected_range[1])
                )
                normality_score = max(0, 100 - (distance / stdev * 100)) if stdev > 0 else 50

            # 종합 점수
            overall_score = (volatility_score * 0.4 + normality_score * 0.6)

            scores[metric_name] = {
                'volatility_score': volatility_score,
                'normality_score': normality_score,
                'overall_score': overall_score
            }

        # 전체 시스템 점수
        if scores:
            system_score = statistics.mean(s['overall_score'] for s in scores.values())
        else:
            system_score = 0

        return {
            'system_health_score': system_score,
            'metric_scores': scores,
            'status': self._get_health_status(system_score)
        }

    def _get_health_status(self, score: float) -> str:
        """건강도 상태"""
        if score >= 80:
            return "🟢 우수"
        elif score >= 60:
            return "🟡 양호"
        elif score >= 40:
            return "🟠 주의"
        else:
            return "🔴 위험"

    def generate_analytics_report(self) -> Dict:
        """분석 리포트 생성"""
        return {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_metrics': len(self.metrics_history),
                'data_points': sum(len(v) for v in self.metrics_history.values())
            },
            'health_score': self.get_system_health_score(),
            'predictions': {
                metric: self.predict_metric(metric, '1hour')
                for metric in self.metrics_history.keys()
            },
            'anomalies': {
                metric: self.detect_anomalies(metric)
                for metric in self.metrics_history.keys()
            }
        }


# 사용 예시
if __name__ == "__main__":
    import random
    import time

    analytics = AdvancedAnalytics()

    print("🔬 고급 분석 엔진 데모\n")

    # 샘플 데이터 생성
    print("📊 샘플 데이터 생성 중...")

    base_time = time.time()
    for i in range(100):
        # CPU 데이터 (추세: 상승)
        cpu_value = 30 + i * 0.3 + random.gauss(0, 5)
        analytics.add_metric('cpu_usage', cpu_value, base_time + i * 60)

        # 메모리 데이터 (안정적)
        memory_value = 50 + random.gauss(0, 3)
        analytics.add_metric('memory_usage', memory_value, base_time + i * 60)

        # 에러율 (변동성 높음)
        error_value = 0.01 + random.gauss(0, 0.005)
        analytics.add_metric('error_rate', max(0, error_value), base_time + i * 60)

    print("✅ 샘플 데이터 생성 완료\n")

    # 예측
    print("📈 1시간 후 예측:")
    for metric in ['cpu_usage', 'memory_usage', 'error_rate']:
        pred = analytics.predict_metric(metric, '1hour')
        if pred:
            print(f"\n{metric}:")
            print(f"  현재값: {pred.current_value:.2f}")
            print(f"  예측값: {pred.predicted_value:.2f}")
            print(f"  추세: {pred.trend}")
            print(f"  신뢰도: {pred.confidence:.1%}")
            print(f"  추천: {pred.recommendation}")

    # 이상 탐지
    print("\n\n🚨 이상 탐지:")
    for metric in ['cpu_usage', 'memory_usage', 'error_rate']:
        anomalies = analytics.detect_anomalies(metric)
        if anomalies:
            for anomaly in anomalies:
                print(f"\n{anomaly.metric} - {anomaly.severity.upper()}")
                print(f"  값: {anomaly.value:.2f}")
                print(f"  범위: {anomaly.expected_range[0]:.2f} ~ {anomaly.expected_range[1]:.2f}")

    # 상관관계
    print("\n\n🔗 상관관계 분석:")
    corr = analytics.analyze_correlation('cpu_usage', 'memory_usage')
    if corr:
        print(f"\nCPU vs 메모리:")
        print(f"  상관계수: {corr['correlation']:.3f}")
        print(f"  해석: {corr['interpretation']}")
        print(f"  추천: {corr['recommendation']}")

    # 시스템 건강도
    print("\n\n💊 시스템 건강도:")
    health = analytics.get_system_health_score()
    print(f"\n전체 건강도: {health['system_health_score']:.1f} {health['status']}")
    print("\n메트릭별 점수:")
    for metric, scores in health['metric_scores'].items():
        print(f"  {metric}: {scores['overall_score']:.1f} {analytics._get_health_status(scores['overall_score'])}")
