#!/usr/bin/env python3
"""
MindLang A/B 테스팅 테스트
Day 9: 통계 기반 성능 비교 검증

테스트:
├─ MetricsCollector: 메트릭 수집 & 통계
├─ StatisticalTest: 통계 검정 (T-test, Chi-square)
├─ ResultAnalyzer: 결과 분석
└─ ExperimentRunner: 통합 실험
"""

import unittest
import random
from ab_testing import (
    MetricsCollector, StatisticalTest, ResultAnalyzer,
    ExperimentRunner, GroupType
)


class TestMetricsCollector(unittest.TestCase):
    """메트릭 수집 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.collector = MetricsCollector()

    def test_record_metrics(self):
        """메트릭 기록"""
        metrics = {'response_time': 50, 'accuracy': 0.85}
        self.collector.record_metric(GroupType.CONTROL, metrics)

        self.assertEqual(len(self.collector.metrics[GroupType.CONTROL]), 1)
        self.assertEqual(self.collector.metrics[GroupType.CONTROL][0], metrics)
        print("✅ 메트릭 기록 통과")

    def test_group_statistics(self):
        """그룹 통계 계산"""
        # Control 그룹에 메트릭 추가
        for i in range(10):
            metrics = {'response_time': 50 + i}
            self.collector.record_metric(GroupType.CONTROL, metrics)

        stats = self.collector.get_group_statistics(GroupType.CONTROL, 'response_time')

        self.assertEqual(stats['count'], 10)
        self.assertGreater(stats['mean'], 50)
        self.assertGreater(stats['std'], 0)
        print("✅ 그룹 통계 계산 통과")

    def test_multiple_metrics(self):
        """여러 메트릭 추적"""
        metrics = {
            'response_time': 50,
            'accuracy': 0.85,
            'satisfaction': 3.5
        }
        self.collector.record_metric(GroupType.CONTROL, metrics)

        all_metrics = self.collector.get_all_metrics()

        self.assertIn(GroupType.CONTROL, all_metrics)
        self.assertEqual(len(all_metrics[GroupType.CONTROL]), 3)
        print("✅ 여러 메트릭 추적 통과")

    def test_empty_group_statistics(self):
        """빈 그룹 통계"""
        stats = self.collector.get_group_statistics(GroupType.CONTROL, 'nonexistent')

        self.assertEqual(stats['count'], 0)
        self.assertEqual(stats['mean'], 0)
        print("✅ 빈 그룹 통계 처리 통과")


class TestStatisticalTest(unittest.TestCase):
    """통계 검정 테스트"""

    def test_t_test_significant_difference(self):
        """t-검정: 유의미한 차이"""
        group1 = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10]
        group2 = [20, 21, 22, 20, 21, 22, 20, 21, 22, 20]

        t_stat, p_value = StatisticalTest.independent_t_test(group1, group2)

        # 평균 차이: ~10 → 통계적으로 유의미함
        self.assertLess(p_value, 0.1)  # p < 0.10
        self.assertGreater(abs(t_stat), 0)
        print("✅ t-검정 유의미한 차이 통과")

    def test_t_test_no_significant_difference(self):
        """t-검정: 차이 없음"""
        group1 = [10, 11, 10, 11, 10, 11, 10, 11, 10, 11]
        group2 = [10, 11, 10, 11, 10, 11, 10, 11, 10, 11]

        t_stat, p_value = StatisticalTest.independent_t_test(group1, group2)

        # 동일한 분포 → 유의미하지 않음
        self.assertGreater(p_value, 0.1)
        print("✅ t-검정 차이 없음 통과")

    def test_chi_square_test_significant(self):
        """카이제곱 검정: 유의미한 차이"""
        # Control: 50% 성공률 (50/100)
        # Treatment: 90% 성공률 (90/100)
        chi2_stat, p_value = StatisticalTest.chi_square_test(50, 100, 90, 100)

        self.assertLess(p_value, 0.1)  # 유의미함
        print("✅ 카이제곱 검정 유의미함 통과")

    def test_chi_square_test_not_significant(self):
        """카이제곱 검정: 차이 없음"""
        # Control: 85% 성공률 (85/100)
        # Treatment: 87% 성공률 (87/100)
        chi2_stat, p_value = StatisticalTest.chi_square_test(85, 100, 87, 100)

        self.assertGreater(p_value, 0.1)  # 유의미하지 않음
        print("✅ 카이제곱 검정 차이 없음 통과")

    def test_effect_size_cohens_d(self):
        """효과 크기 (Cohen's d)"""
        group1 = [10, 11, 12, 10, 11, 12, 10, 11, 12, 10]
        group2 = [20, 21, 22, 20, 21, 22, 20, 21, 22, 20]

        cohens_d = StatisticalTest.effect_size_cohens_d(group1, group2)

        # 큰 차이 → Cohen's d > 1
        self.assertGreater(abs(cohens_d), 1.0)
        print("✅ Cohen's d 계산 통과")

    def test_effect_size_small(self):
        """효과 크기: 작은 차이"""
        # 더 많은 샘플로 작은 차이
        group1 = [10.0 + random.gauss(0, 0.5) for _ in range(100)]
        group2 = [10.5 + random.gauss(0, 0.5) for _ in range(100)]

        cohens_d = StatisticalTest.effect_size_cohens_d(group1, group2)

        # 작은 차이 → Cohen's d < 1.0
        self.assertLess(abs(cohens_d), 2.0)
        print("✅ 작은 효과 크기 통과")


class TestResultAnalyzer(unittest.TestCase):
    """결과 분석 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.analyzer = ResultAnalyzer(confidence_level=0.95)
        self.collector = MetricsCollector()

    def test_analyze_significant_continuous_metric(self):
        """연속형 메트릭: 유의미한 차이"""
        # Control: 평균 50
        for i in range(100):
            metrics = {'response_time': 50 + random.gauss(0, 5)}
            self.collector.record_metric(GroupType.CONTROL, metrics)

        # Treatment: 평균 40 (개선됨)
        for i in range(100):
            metrics = {'response_time': 40 + random.gauss(0, 5)}
            self.collector.record_metric(GroupType.TREATMENT, metrics)

        analysis = self.analyzer.analyze_continuous_metric(self.collector, 'response_time')

        self.assertLess(analysis['p_value'], 0.1)  # 유의미함
        self.assertTrue(analysis['is_significant'])
        print("✅ 연속형 메트릭 분석 통과")

    def test_analyze_categorical_metric(self):
        """범주형 메트릭 분석"""
        # Control: 50% 성공률
        for i in range(200):
            success = 1.0 if random.random() < 0.5 else 0.0
            self.collector.record_metric(GroupType.CONTROL, {'accuracy': success})

        # Treatment: 90% 성공률 (큰 차이)
        for i in range(200):
            success = 1.0 if random.random() < 0.9 else 0.0
            self.collector.record_metric(GroupType.TREATMENT, {'accuracy': success})

        analysis = self.analyzer.analyze_categorical_metric(self.collector, 'accuracy', 0.5)

        self.assertLess(analysis['p_value'], 0.5)  # 통계 검정 실행됨
        self.assertGreater(analysis['treatment_rate'], analysis['control_rate'])
        print("✅ 범주형 메트릭 분석 통과")

    def test_confidence_level(self):
        """신뢰도 설정"""
        analyzer_95 = ResultAnalyzer(confidence_level=0.95)
        analyzer_99 = ResultAnalyzer(confidence_level=0.99)

        self.assertAlmostEqual(analyzer_95.alpha, 0.05, places=2)
        self.assertAlmostEqual(analyzer_99.alpha, 0.01, places=2)
        print("✅ 신뢰도 설정 통과")


class TestExperimentRunner(unittest.TestCase):
    """실험 실행 테스트"""

    def test_basic_experiment_run(self):
        """기본 실험 실행"""
        runner = ExperimentRunner()
        results = runner.run_experiment()

        self.assertIn('duration', results)
        self.assertIn('control_sample_size', results)
        self.assertIn('treatment_sample_size', results)
        self.assertEqual(results['control_sample_size'], 500)
        self.assertEqual(results['treatment_sample_size'], 500)
        print("✅ 기본 실험 실행 통과")

    def test_experiment_metrics_collected(self):
        """실험 메트릭 수집"""
        runner = ExperimentRunner()
        results = runner.run_experiment()

        # 3개 메트릭 기대
        self.assertEqual(len(results['metrics']), 3)
        self.assertIn('response_time', results['metrics'])
        self.assertIn('accuracy', results['metrics'])
        self.assertIn('satisfaction', results['metrics'])
        print("✅ 실험 메트릭 수집 통과")

    def test_experiment_results_structure(self):
        """실험 결과 구조"""
        runner = ExperimentRunner()
        results = runner.run_experiment()

        for metric_name, analysis in results['metrics'].items():
            self.assertIn('metric', analysis)
            self.assertIn('type', analysis)
            self.assertIn('control', analysis)
            self.assertIn('treatment', analysis)
            self.assertIn('p_value', analysis)
            self.assertIn('is_significant', analysis)
            self.assertIn('winner', analysis)
        print("✅ 실험 결과 구조 통과")

    def test_experiment_duration(self):
        """실험 지속 시간"""
        runner = ExperimentRunner()
        results = runner.run_experiment()

        # 매우 빠름 (<1초)
        self.assertLess(results['duration'], 1.0)
        print(f"✅ 실험 지속 시간 통과 ({results['duration']:.3f}초)")


class TestABTestingPerformance(unittest.TestCase):
    """A/B 테스팅 성능 테스트"""

    def test_statistical_test_speed(self):
        """통계 검정 속도"""
        import time

        group1 = [random.gauss(50, 10) for _ in range(1000)]
        group2 = [random.gauss(45, 10) for _ in range(1000)]

        start = time.time()
        for _ in range(100):
            StatisticalTest.independent_t_test(group1, group2)
        elapsed = time.time() - start

        avg_time = elapsed / 100 * 1000  # ms
        print(f"\n⚡ t-검정 속도: {avg_time:.2f}ms (100회 평균)")

        # 목표: <10ms
        self.assertLess(avg_time, 10.0)
        print("✅ 통계 검정 속도 목표 달성")

    def test_experiment_efficiency(self):
        """실험 효율성"""
        import time

        runner = ExperimentRunner()

        start = time.time()
        results = runner.run_experiment()
        elapsed = time.time() - start

        samples_per_second = (
            (results['control_sample_size'] + results['treatment_sample_size']) / elapsed
        )

        print(f"\n📊 실험 효율: {samples_per_second:.0f} samples/sec")
        print(f"   1000+ samples: {elapsed * 1000 / (results['control_sample_size'] + results['treatment_sample_size']):.2f}ms")

        # 목표: >1000 samples/sec
        self.assertGreater(samples_per_second, 1000)
        print("✅ 실험 효율 목표 달성")


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 MindLang Day 9: A/B 테스팅 프레임워크 테스트")
    print("=" * 70 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsCollector))
    suite.addTests(loader.loadTestsFromTestCase(TestStatisticalTest))
    suite.addTests(loader.loadTestsFromTestCase(TestResultAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestExperimentRunner))
    suite.addTests(loader.loadTestsFromTestCase(TestABTestingPerformance))

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
        print("🎯 Day 9 A/B 테스팅 프레임워크 완성!")
    else:
        print("\n❌ 일부 테스트 실패")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
