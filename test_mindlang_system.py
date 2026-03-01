#!/usr/bin/env python3
"""
MindLang 4경로 시스템 테스트
Path 1, 2, 3 + Red Team (Path 4) 검증

테스트 시나리오:
1. 정상 상황 (액션 불필요)
2. 고에러율 (ROLLBACK 권장)
3. 고부하 (SCALE_UP 권장)
4. 비용 최적화 (CONTINUE 권장)
"""

import unittest
import sys
from typing import Dict, List
from mindlang_with_red_team import MindLangRedTeam


class TestMindLangPaths(unittest.TestCase):
    """MindLang 경로 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.mindlang = MindLangRedTeam()

    def test_path1_error_driven_high_error(self):
        """Path 1: 높은 에러율 테스트"""
        metrics = {
            'error_rate': 0.08,
            'error_trend': 'stable',
            'cpu_usage': 40,
            'memory_usage': 50,
            'latency_p95': 200
        }

        result = self.mindlang.path1_error_driven(metrics)

        self.assertEqual(result['action'], 'ROLLBACK')
        self.assertGreater(result['confidence'], 0.8)
        print(f"✅ Path 1 테스트 통과: {result['action']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_path1_error_driven_normal(self):
        """Path 1: 정상 에러율 테스트"""
        metrics = {
            'error_rate': 0.002,
            'error_trend': 'stable',
            'cpu_usage': 30,
            'memory_usage': 40,
            'latency_p95': 150
        }

        result = self.mindlang.path1_error_driven(metrics)

        self.assertEqual(result['action'], 'CONTINUE')
        self.assertLess(result['confidence'], 0.6)
        print(f"✅ Path 1 테스트 통과: {result['action']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_path2_performance_driven_high_load(self):
        """Path 2: 높은 부하 테스트"""
        metrics = {
            'error_rate': 0.005,
            'cpu_usage': 85,
            'memory_usage': 80,
            'latency_p95': 600,
            'throughput': 5000
        }

        result = self.mindlang.path2_performance_driven(metrics)

        self.assertEqual(result['action'], 'SCALE_UP')
        self.assertGreater(result['confidence'], 0.7)
        print(f"✅ Path 2 테스트 통과: {result['action']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_path2_performance_driven_low_load(self):
        """Path 2: 낮은 부하 테스트"""
        metrics = {
            'error_rate': 0.001,
            'cpu_usage': 30,
            'memory_usage': 35,
            'latency_p95': 100,
            'throughput': 20000
        }

        result = self.mindlang.path2_performance_driven(metrics)

        self.assertEqual(result['action'], 'SCALE_DOWN')
        self.assertGreater(result['confidence'], 0.6)
        print(f"✅ Path 2 테스트 통과: {result['action']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_path3_cost_driven_high_cost(self):
        """Path 3: 높은 비용 테스트"""
        metrics = {
            'error_rate': 0.002,
            'cpu_usage': 85,
            'memory_usage': 80,
            'latency_p95': 200,
            'cost_per_hour': 200
        }

        result = self.mindlang.path3_cost_driven(metrics)

        self.assertEqual(result['action'], 'SCALE_DOWN')
        self.assertGreater(result['confidence'], 0.6)
        print(f"✅ Path 3 테스트 통과: {result['action']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_path4_red_team_analysis(self):
        """Path 4: Red Team 자동 비판 테스트"""
        metrics = {
            'error_rate': 0.08,
            'error_trend': 'stable',
            'cpu_usage': 40,
            'memory_usage': 50,
            'latency_p95': 200
        }

        path1_result = self.mindlang.path1_error_driven(metrics)
        red_team_analysis = self.mindlang.path4_red_team(metrics, path1_result)

        self.assertIsNotNone(red_team_analysis['questioned_assumptions'])
        self.assertIsNotNone(red_team_analysis['failure_scenarios'])
        self.assertIsNotNone(red_team_analysis['counter_recommendation'])

        self.assertGreater(len(red_team_analysis['questioned_assumptions']), 0)
        self.assertGreater(len(red_team_analysis['failure_scenarios']), 0)

        print(f"✅ Path 4 테스트 통과: Red Team이 {len(red_team_analysis['questioned_assumptions'])}개 가정 검증")

    def test_full_analyze_scenario1(self):
        """전체 분석: 정상 상황"""
        metrics = {
            'error_rate': 0.002,
            'cpu_usage': 50,
            'memory_usage': 55,
            'latency_p95': 200,
            'throughput': 15000,
            'cost_per_hour': 60
        }

        result = self.mindlang.analyze(metrics)

        self.assertIn(result['primary_decision'], ['ROLLBACK', 'SCALE_UP', 'CONTINUE'])
        self.assertGreater(result['confidence'], 0.5)
        self.assertIn('red_team_analysis', result)

        print(f"✅ 전체 분석 테스트 1 통과: {result['primary_decision']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_full_analyze_scenario2(self):
        """전체 분석: 위기 상황"""
        metrics = {
            'error_rate': 0.10,
            'cpu_usage': 95,
            'memory_usage': 92,
            'latency_p95': 800,
            'throughput': 2000,
            'cost_per_hour': 150
        }

        result = self.mindlang.analyze(metrics)

        # 위기 상황에서는 ROLLBACK이 우선
        self.assertEqual(result['primary_decision'], 'ROLLBACK')
        self.assertGreater(result['confidence'], 0.8)

        print(f"✅ 전체 분석 테스트 2 통과: {result['primary_decision']} (신뢰도: {result['confidence']*100:.0f}%)")

    def test_confidence_consistency(self):
        """신뢰도 일관성 테스트"""
        metrics = {
            'error_rate': 0.05,
            'cpu_usage': 75,
            'memory_usage': 70,
            'latency_p95': 400,
            'throughput': 8000,
            'cost_per_hour': 80
        }

        # 여러 번 분석
        results = [self.mindlang.analyze(metrics) for _ in range(5)]

        # 모든 결과의 최종 결정이 일관되어야 함
        decisions = [r['primary_decision'] for r in results]
        self.assertEqual(len(set(decisions)), 1, "신뢰도가 일관되지 않음")

        print(f"✅ 신뢰도 일관성 테스트 통과: {decisions[0]} (5회 반복 일관성)")


class TestRedTeamEffectiveness(unittest.TestCase):
    """Red Team 효과성 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.mindlang = MindLangRedTeam()

    def test_red_team_catches_assumptions(self):
        """Red Team이 숨겨진 가정을 캐치하는지 테스트"""
        metrics = {
            'error_rate': 0.001,
            'cpu_usage': 80,
            'memory_usage': 75,
            'latency_p95': 150,
            'throughput': 10000
        }

        path2_result = self.mindlang.path2_performance_driven(metrics)
        red_team = self.mindlang.path4_red_team(metrics, path2_result)

        # Red Team은 CPU만 봐서는 안 된다는 것을 지적해야 함
        assumptions = red_team['questioned_assumptions']
        self.assertTrue(
            any('cpu' not in a.lower() or '다른' in a.lower() for a in assumptions),
            "Red Team이 CPU 외 다른 요인을 언급해야 함"
        )

        print(f"✅ Red Team 검증 테스트 통과: 숨겨진 가정 {len(assumptions)}개 발견")

    def test_red_team_identifies_risks(self):
        """Red Team이 위험을 식별하는지 테스트"""
        metrics = {
            'error_rate': 0.001,
            'cpu_usage': 85,
            'memory_usage': 80,
            'latency_p95': 200,
            'throughput': 5000
        }

        path2_result = self.mindlang.path2_performance_driven(metrics)
        red_team = self.mindlang.path4_red_team(metrics, path2_result)

        # SCALE_UP이 항상 좋은 것은 아니라는 것을 지적해야 함
        scenarios = red_team['failure_scenarios']
        self.assertGreater(len(scenarios), 0, "Red Team이 실패 시나리오를 제시해야 함")

        print(f"✅ Red Team 위험 식별 테스트 통과: {len(scenarios)}개 실패 시나리오 발견")


class TestPathWeights(unittest.TestCase):
    """경로별 가중치 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        self.mindlang = MindLangRedTeam()

    def test_conflict_resolution(self):
        """경로가 충돌할 때 우선순위 테스트"""
        # Path 1과 Path 3이 충돌하는 상황
        metrics = {
            'error_rate': 0.001,      # Path 1: CONTINUE
            'cpu_usage': 95,          # Path 2: SCALE_UP
            'memory_usage': 90,       # Path 2: SCALE_UP
            'latency_p95': 500,       # Path 2: SCALE_UP
            'throughput': 20000,      # Path 2: 좋음
            'cost_per_hour': 200      # Path 3: SCALE_DOWN
        }

        result = self.mindlang.analyze(metrics)

        # Path 2 (성능)가 우선되어야 함
        self.assertEqual(result['primary_decision'], 'SCALE_UP')

        print(f"✅ 경로 충돌 해결 테스트 통과: {result['primary_decision']} (Path 2 우선)")


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🧪 MindLang 시스템 전체 테스트")
    print("=" * 70 + "\n")

    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestMindLangPaths))
    suite.addTests(loader.loadTestsFromTestCase(TestRedTeamEffectiveness))
    suite.addTests(loader.loadTestsFromTestCase(TestPathWeights))

    # 테스트 실행
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
    else:
        print("\n❌ 일부 테스트 실패")
        return False

    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
