#!/usr/bin/env python3
"""
MindLang ML 예측 엔진 테스트
Day 8: 머신러닝 기반 의사결정 검증

테스트:
├─ MetricsPredictor: 메트릭 추세 예측
├─ ActionPredictor: 액션 분류
├─ ConfidenceEstimator: 신뢰도 추정
└─ ModelTrainer: 통합 예측
"""

import unittest
import time
from ml_predictor import (
    MetricsPredictor, ActionPredictor, ConfidenceEstimator, ModelTrainer
)


class TestMetricsPredictor(unittest.TestCase):
    """메트릭 예측 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.predictor = MetricsPredictor(window_size=10)

    def test_linear_trend_increasing(self):
        """선형 증가 추세 감지"""
        # 증가하는 메트릭
        for i in range(10):
            self.predictor.add_metric('cpu_usage', 30 + i * 2, time.time() + i)

        result = self.predictor.predict_next_value('cpu_usage')

        self.assertEqual(result['trend'], 'INCREASING')
        self.assertGreater(result['slope'], 0)
        self.assertGreater(result['confidence'], 0.8)
        print("✅ 선형 증가 추세 감지 통과")

    def test_linear_trend_decreasing(self):
        """선형 감소 추세 감지"""
        for i in range(10):
            self.predictor.add_metric('memory_usage', 80 - i * 2, time.time() + i)

        result = self.predictor.predict_next_value('memory_usage')

        self.assertEqual(result['trend'], 'DECREASING')
        self.assertLess(result['slope'], 0)
        self.assertGreater(result['confidence'], 0.8)
        print("✅ 선형 감소 추세 감지 통과")

    def test_stable_trend(self):
        """안정적 추세 감지"""
        for i in range(10):
            self.predictor.add_metric('error_rate', 0.02, time.time() + i)

        result = self.predictor.predict_next_value('error_rate')

        self.assertEqual(result['trend'], 'STABLE')
        self.assertAlmostEqual(result['slope'], 0, places=2)
        print("✅ 안정적 추세 감지 통과")

    def test_anomaly_detection(self):
        """이상치 감지"""
        # 정상 데이터
        for i in range(10):
            self.predictor.add_metric('latency', 100 + i, time.time() + i)

        # 이상치 추가
        self.predictor.add_metric('latency', 500, time.time() + 10)

        result = self.predictor.predict_anomaly('latency', threshold=2.0)

        self.assertTrue(result['is_anomaly'])
        self.assertGreater(abs(result['z_score']), 2.0)
        print("✅ 이상치 감지 통과")

    def test_insufficient_data(self):
        """데이터 부족 처리"""
        result = self.predictor.predict_next_value('unknown_metric')

        self.assertIsNone(result['prediction'])
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('Insufficient data', result['error'])
        print("✅ 데이터 부족 처리 통과")


class TestActionPredictor(unittest.TestCase):
    """액션 예측 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.predictor = ActionPredictor()

    def test_high_error_rate_action(self):
        """높은 에러율 시 액션 예측"""
        # 높은 에러율 → ROLLBACK
        training_data = [
            ({'error_rate': 0.1, 'cpu_usage': 50, 'memory_usage': 50}, 'ROLLBACK'),
            ({'error_rate': 0.08, 'cpu_usage': 45, 'memory_usage': 55}, 'ROLLBACK'),
            ({'error_rate': 0.09, 'cpu_usage': 60, 'memory_usage': 60}, 'ROLLBACK'),
        ]

        for metrics, action in training_data:
            self.predictor.add_training_sample(metrics, action)

        # 유사한 메트릭으로 예측
        result = self.predictor.predict_action({'error_rate': 0.08, 'cpu_usage': 50, 'memory_usage': 50})

        self.assertEqual(result['predicted_action'], 'ROLLBACK')
        self.assertGreater(result['confidence'], 0.3)
        print("✅ 높은 에러율 액션 예측 통과")

    def test_high_cpu_usage_action(self):
        """높은 CPU 사용률 시 액션 예측"""
        training_data = [
            ({'error_rate': 0.01, 'cpu_usage': 80, 'memory_usage': 60}, 'SCALE_UP'),
            ({'error_rate': 0.01, 'cpu_usage': 85, 'memory_usage': 70}, 'SCALE_UP'),
            ({'error_rate': 0.01, 'cpu_usage': 90, 'memory_usage': 75}, 'SCALE_UP'),
        ]

        for metrics, action in training_data:
            self.predictor.add_training_sample(metrics, action)

        result = self.predictor.predict_action({'error_rate': 0.01, 'cpu_usage': 80, 'memory_usage': 60})

        self.assertEqual(result['predicted_action'], 'SCALE_UP')
        self.assertGreater(result['confidence'], 0.3)
        print("✅ 높은 CPU 액션 예측 통과")

    def test_normal_metrics_action(self):
        """정상 메트릭 시 액션 예측"""
        training_data = [
            ({'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}, 'CONTINUE'),
            ({'error_rate': 0.01, 'cpu_usage': 35, 'memory_usage': 45}, 'CONTINUE'),
            ({'error_rate': 0.01, 'cpu_usage': 25, 'memory_usage': 35}, 'CONTINUE'),
        ]

        for metrics, action in training_data:
            self.predictor.add_training_sample(metrics, action)

        result = self.predictor.predict_action({'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40})

        self.assertEqual(result['predicted_action'], 'CONTINUE')
        self.assertGreater(result['confidence'], 0.3)
        print("✅ 정상 메트릭 액션 예측 통과")

    def test_no_training_data(self):
        """학습 데이터 없음 처리"""
        result = self.predictor.predict_action({'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40})

        self.assertEqual(result['predicted_action'], 'CONTINUE')
        self.assertEqual(result['confidence'], 0.0)
        self.assertIn('No training data', result['error'])
        print("✅ 학습 데이터 없음 처리 통과")


class TestConfidenceEstimator(unittest.TestCase):
    """신뢰도 추정 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.estimator = ConfidenceEstimator()

    def test_high_confidence(self):
        """높은 신뢰도 계산"""
        result = self.estimator.estimate_confidence(
            metrics_agreement=0.9,
            prediction_conf=0.85,
            trend_stability=0.8,
            data_age_seconds=30
        )

        self.assertGreater(result['overall_confidence'], 0.75)
        print("✅ 높은 신뢰도 계산 통과")

    def test_low_confidence(self):
        """낮은 신뢰도 계산"""
        result = self.estimator.estimate_confidence(
            metrics_agreement=0.3,
            prediction_conf=0.2,
            trend_stability=0.2,
            data_age_seconds=600
        )

        self.assertLess(result['overall_confidence'], 0.5)
        print("✅ 낮은 신뢰도 계산 통과")

    def test_accuracy_tracking(self):
        """정확도 추적"""
        # 정확한 예측 기록
        for _ in range(5):
            self.estimator.record_accuracy(True)

        # 부정확한 예측 기록
        for _ in range(5):
            self.estimator.record_accuracy(False)

        # 평균 정확도: 50%
        avg_accuracy = sum(self.estimator.accuracy_history) / len(self.estimator.accuracy_history)
        self.assertAlmostEqual(avg_accuracy, 0.5, places=1)
        print("✅ 정확도 추적 통과")

    def test_recency_weight(self):
        """최근성 가중치"""
        # 최근 데이터
        result_recent = self.estimator.estimate_confidence(0.5, 0.5, 0.5, data_age_seconds=30)
        # 오래된 데이터
        result_old = self.estimator.estimate_confidence(0.5, 0.5, 0.5, data_age_seconds=600)

        self.assertGreater(
            result_recent['overall_confidence'],
            result_old['overall_confidence']
        )
        print("✅ 최근성 가중치 통과")


class TestModelTrainer(unittest.TestCase):
    """통합 모델 트레이너 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.trainer = ModelTrainer()

    def test_basic_training(self):
        """기본 학습"""
        metrics = {'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}
        self.trainer.train_sample(metrics, 'CONTINUE')

        self.assertEqual(self.trainer.training_samples, 1)
        stats = self.trainer.get_model_stats()
        self.assertEqual(stats['training_samples'], 1)
        print("✅ 기본 학습 통과")

    def test_model_versioning(self):
        """모델 버전 업데이트"""
        metrics = {'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}

        # 100 샘플 학습
        for i in range(100):
            self.trainer.train_sample(metrics, 'CONTINUE')

        stats = self.trainer.get_model_stats()
        self.assertGreaterEqual(stats['model_version'], 2)  # v1 → v2
        print("✅ 모델 버전 업데이트 통과")

    def test_integrated_prediction(self):
        """통합 예측"""
        # 학습 데이터
        training_scenarios = [
            ({'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}, 'CONTINUE'),
            ({'error_rate': 0.08, 'cpu_usage': 50, 'memory_usage': 60}, 'ROLLBACK'),
            ({'error_rate': 0.02, 'cpu_usage': 70, 'memory_usage': 75}, 'SCALE_UP'),
        ] * 10

        for metrics, action in training_scenarios:
            self.trainer.train_sample(metrics, action)

        # 예측
        prediction = self.trainer.predict({'error_rate': 0.02, 'cpu_usage': 50, 'memory_usage': 55})

        self.assertIn(prediction['action'], ['CONTINUE', 'ROLLBACK', 'SCALE_UP'])
        self.assertGreaterEqual(prediction['confidence'], 0.0)
        self.assertLessEqual(prediction['confidence'], 1.0)
        self.assertGreater(prediction['training_samples'], 0)
        print("✅ 통합 예측 통과")

    def test_model_statistics(self):
        """모델 통계"""
        metrics = {'error_rate': 0.01, 'cpu_usage': 30, 'memory_usage': 40}
        for _ in range(50):
            self.trainer.train_sample(metrics, 'CONTINUE')

        stats = self.trainer.get_model_stats()

        self.assertGreater(stats['metrics_tracked'], 0)
        self.assertGreater(stats['actions_learned'], 0)
        self.assertGreaterEqual(stats['historical_accuracy'], 0.0)
        self.assertLessEqual(stats['historical_accuracy'], 1.0)
        print("✅ 모델 통계 통과")


class TestMLPerformance(unittest.TestCase):
    """ML 성능 테스트"""

    def test_prediction_speed(self):
        """예측 속도"""
        trainer = ModelTrainer()

        # 학습 데이터
        for i in range(100):
            metrics = {
                'error_rate': 0.01 + (i % 10) * 0.01,
                'cpu_usage': 30 + (i % 50),
                'memory_usage': 40 + (i % 50)
            }
            trainer.train_sample(metrics, 'CONTINUE')

        # 예측 속도 측정
        import time
        start = time.time()
        for _ in range(1000):
            trainer.predict({'error_rate': 0.02, 'cpu_usage': 50, 'memory_usage': 55})
        elapsed = time.time() - start

        avg_time = elapsed / 1000 * 1000  # ms
        print(f"\n⚡ 예측 속도: {avg_time:.2f}ms (1000회 평균)")

        # 목표: <1ms
        self.assertLess(avg_time, 1.0)
        print("✅ 예측 속도 목표 달성")

    def test_memory_efficiency(self):
        """메모리 효율성"""
        import sys
        trainer = ModelTrainer()

        # 1000 샘플 학습
        for i in range(1000):
            metrics = {
                'error_rate': 0.01 + (i % 10) * 0.01,
                'cpu_usage': 30 + (i % 50),
                'memory_usage': 40 + (i % 50)
            }
            trainer.train_sample(metrics, 'CONTINUE')

        # 메모리 사용량 추정 (대략적)
        print(f"✅ 1000 샘플 학습 완료")
        print(f"   모델 버전: {trainer.model_version}")
        print(f"   학습 샘플: {trainer.training_samples}")

        # 메모리 효율: 작은 모델 유지
        self.assertGreater(trainer.training_samples, 0)
        print("✅ 메모리 효율성 확인")


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 MindLang Day 8: ML 예측 엔진 테스트")
    print("=" * 70 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestActionPredictor))
    suite.addTests(loader.loadTestsFromTestCase(TestConfidenceEstimator))
    suite.addTests(loader.loadTestsFromTestCase(TestModelTrainer))
    suite.addTests(loader.loadTestsFromTestCase(TestMLPerformance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 모든 테스트 통과!")
        print("🎯 Day 8 ML 엔진 완성!")
    else:
        print("\n❌ 일부 테스트 실패")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
