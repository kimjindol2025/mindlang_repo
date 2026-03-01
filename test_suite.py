#!/usr/bin/env python3
"""
MindLang 통합 테스트 스위트
모든 도구와 모듈의 자동 테스트

테스트 항목:
- 의사결정 엔진
- 운영 도구
- 고급 도구
- 관리 도구
"""

import unittest
import asyncio
import time
import json
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestMindLangCore(unittest.TestCase):
    """핵심 시스템 테스트"""

    def test_decision_creation(self):
        """의사결정 생성 테스트"""
        from learning_engine import DecisionRecord

        record = DecisionRecord(
            timestamp=time.time(),
            metrics={'cpu': 85, 'memory': 78, 'error_rate': 0.025},
            decision='SCALE_UP',
            confidence=0.87,
            path1_action='ROLLBACK',
            path1_confidence=0.76,
            path2_action='SCALE_UP',
            path2_confidence=0.90,
            path3_action='NO_ACTION',
            path3_confidence=0.40,
            path4_recommendation='CANARY_FIRST',
            path4_confidence=0.88
        )

        self.assertEqual(record.decision, 'SCALE_UP')
        self.assertEqual(record.confidence, 0.87)
        self.assertIsNone(record.success)
        print("✅ 의사결정 생성 테스트 통과")

    def test_metrics_validation(self):
        """메트릭 검증 테스트"""
        metrics = {
            'cpu_usage': 85.5,
            'memory_usage': 78.2,
            'error_rate': 0.025,
            'latency_ms': 150
        }

        self.assertTrue(all(isinstance(v, (int, float)) for v in metrics.values()))
        self.assertTrue(metrics['cpu_usage'] > 80)
        print("✅ 메트릭 검증 테스트 통과")


class TestPolicyEngine(unittest.TestCase):
    """정책 엔진 테스트"""

    def setUp(self):
        """테스트 설정"""
        from auto_policy_engine import AutoPolicyEngine
        self.engine = AutoPolicyEngine('test_policies.json')

    def test_policy_creation_from_pattern(self):
        """패턴 기반 정책 생성 테스트"""
        policy = self.engine.create_policy_from_pattern(
            pattern_name="Test Pattern",
            pattern_description="테스트 패턴",
            condition={"cpu": ">80"},
            recommended_action="SCALE_UP",
            confidence=0.85,
            evidence_count=10
        )

        self.assertIsNotNone(policy.id)
        self.assertEqual(policy.name, "Test Pattern")
        self.assertEqual(policy.confidence, 0.85)
        print("✅ 정책 생성 테스트 통과")

    def test_policy_evaluation(self):
        """정책 평가 테스트"""
        policy = self.engine.create_policy_from_threshold(
            metric_name="cpu_usage",
            threshold_value=80,
            comparison=">",
            recommended_action="SCALE_UP",
            confidence=0.90,
            evidence_count=20
        )

        self.engine.activate_policy(policy.id)

        metrics = {'cpu_usage': 85, 'memory_usage': 70}
        action, policy_id, conf = self.engine.evaluate_policies(metrics)

        self.assertEqual(action, "SCALE_UP")
        self.assertIsNotNone(policy_id)
        print("✅ 정책 평가 테스트 통과")

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists('test_policies.json'):
            os.remove('test_policies.json')


class TestLearningEngine(unittest.TestCase):
    """학습 엔진 테스트"""

    def setUp(self):
        """테스트 설정"""
        from learning_engine import LearningEngine
        self.engine = LearningEngine('test_memory.json')

    def test_decision_recording(self):
        """의사결정 기록 테스트"""
        from learning_engine import DecisionRecord

        record = DecisionRecord(
            timestamp=time.time(),
            metrics={'cpu': 85, 'memory': 78},
            decision='SCALE_UP',
            confidence=0.87,
            path1_action='ROLLBACK',
            path1_confidence=0.76,
            path2_action='SCALE_UP',
            path2_confidence=0.90,
            path3_action='NO_ACTION',
            path3_confidence=0.40,
            path4_recommendation='CANARY_FIRST',
            path4_confidence=0.88
        )

        self.engine.record_decision(record)
        self.assertEqual(len(self.engine.decisions), 1)
        print("✅ 의사결정 기록 테스트 통과")

    def test_outcome_recording(self):
        """결과 기록 테스트"""
        from learning_engine import DecisionRecord

        record = DecisionRecord(
            timestamp=time.time(),
            metrics={'cpu': 85, 'memory': 78},
            decision='SCALE_UP',
            confidence=0.87,
            path1_action='ROLLBACK',
            path1_confidence=0.76,
            path2_action='SCALE_UP',
            path2_confidence=0.90,
            path3_action='NO_ACTION',
            path3_confidence=0.40,
            path4_recommendation='CANARY_FIRST',
            path4_confidence=0.88
        )

        self.engine.record_decision(record)
        self.engine.record_outcome(0, "CPU reduced to 45%", True)

        self.assertTrue(self.engine.decisions[0].success)
        self.assertEqual(self.engine.decisions[0].outcome, "CPU reduced to 45%")
        print("✅ 결과 기록 테스트 통과")

    def test_learning_insights(self):
        """학습 통찰 테스트"""
        from learning_engine import DecisionRecord

        # 여러 의사결정 기록
        for i in range(10):
            record = DecisionRecord(
                timestamp=time.time() - (10 - i) * 60,
                metrics={'cpu': 50 + i * 3, 'memory': 60 + i * 2},
                decision='SCALE_UP' if i % 2 == 0 else 'CONTINUE',
                confidence=0.75 + i * 0.01,
                path1_action='ROLLBACK',
                path1_confidence=0.60,
                path2_action='SCALE_UP',
                path2_confidence=0.80,
                path3_action='NO_ACTION',
                path3_confidence=0.50,
                path4_recommendation='MONITOR',
                path4_confidence=0.70,
                success=True
            )
            self.engine.record_decision(record)

        insights = self.engine.learn_from_history()
        self.assertGreater(len(insights), 0)
        print("✅ 학습 통찰 테스트 통과")

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists('test_memory.json'):
            os.remove('test_memory.json')


class TestAlertSystem(unittest.TestCase):
    """알림 시스템 테스트"""

    def setUp(self):
        """테스트 설정"""
        from alert_system import AlertManager, AlertSeverity
        self.manager = AlertManager('test_alert_config.json')
        self.AlertSeverity = AlertSeverity

    def test_alert_creation(self):
        """알림 생성 테스트"""
        alert = self.manager.create_alert(
            title="Test Alert",
            message="테스트 알림입니다",
            severity=self.AlertSeverity.WARNING,
            source="test"
        )

        self.assertIsNotNone(alert.id)
        self.assertEqual(alert.title, "Test Alert")
        self.assertFalse(alert.resolved)
        print("✅ 알림 생성 테스트 통과")

    def test_alert_resolution(self):
        """알림 해결 테스트"""
        alert = self.manager.create_alert(
            title="Test Alert",
            message="테스트",
            severity=self.AlertSeverity.INFO,
            source="test"
        )

        self.manager.resolve_alert(alert.id, "테스트 완료")
        resolved_alert = self.manager.alerts[alert.id]

        self.assertTrue(resolved_alert.resolved)
        self.assertEqual(resolved_alert.resolution_notes, "테스트 완료")
        print("✅ 알림 해결 테스트 통과")

    def test_alert_summary(self):
        """알림 요약 테스트"""
        self.manager.create_alert("Alert 1", "메시지 1", self.AlertSeverity.CRITICAL, "source1")
        self.manager.create_alert("Alert 2", "메시지 2", self.AlertSeverity.WARNING, "source1")
        self.manager.create_alert("Alert 3", "메시지 3", self.AlertSeverity.INFO, "source2")

        summary = self.manager.get_alert_summary()

        self.assertEqual(summary['total_alerts'], 3)
        self.assertEqual(summary['active_alerts'], 3)
        self.assertEqual(summary['by_severity']['critical'], 1)
        self.assertEqual(summary['by_severity']['warning'], 1)
        print("✅ 알림 요약 테스트 통과")

    def tearDown(self):
        """테스트 정리"""
        if os.path.exists('test_alert_config.json'):
            os.remove('test_alert_config.json')


class TestPerformanceProfiler(unittest.TestCase):
    """성능 프로파일러 테스트"""

    def setUp(self):
        """테스트 설정"""
        from performance_profiler import PerformanceProfiler
        self.profiler = PerformanceProfiler()

    def test_function_profiling(self):
        """함수 프로파일링 테스트"""
        @self.profiler.profile_function
        def test_function():
            time.sleep(0.01)
            return "완료"

        result = test_function()
        self.assertEqual(result, "완료")

        profile = self.profiler.function_profiles.get("test_function")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.call_count, 1)
        self.assertGreater(profile.total_time, 0.01)
        print("✅ 함수 프로파일링 테스트 통과")

    def test_code_block_profiling(self):
        """코드 블록 프로파일링 테스트"""
        with self.profiler.profile_code_block("test_block"):
            time.sleep(0.01)

        profile = self.profiler.function_profiles.get("test_block")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.call_count, 1)
        print("✅ 코드 블록 프로파일링 테스트 통과")

    def test_bottleneck_detection(self):
        """병목 지점 감지 테스트"""
        @self.profiler.profile_function
        def slow_function():
            time.sleep(0.05)

        @self.profiler.profile_function
        def fast_function():
            time.sleep(0.01)

        for _ in range(3):
            slow_function()
            fast_function()

        bottlenecks = self.profiler.get_bottlenecks(5)
        self.assertGreater(len(bottlenecks), 0)
        # 느린 함수가 더 많은 시간 소비
        print("✅ 병목 지점 감지 테스트 통과")


class TestAPIGateway(unittest.TestCase):
    """API 게이트웨이 테스트"""

    def setUp(self):
        """테스트 설정"""
        from api_gateway import APIGateway
        self.gateway = APIGateway()

    def test_gateway_initialization(self):
        """게이트웨이 초기화 테스트"""
        self.assertGreater(len(self.gateway.services), 0)
        self.assertEqual(len(self.gateway.request_logs), 0)
        print("✅ 게이트웨이 초기화 테스트 통과")

    def test_metrics_collection(self):
        """메트릭 수집 테스트"""
        self.gateway._log_request(
            service_name="test",
            method="GET",
            path="/test",
            status_code=200,
            response_time=0.05,
            client_ip="127.0.0.1"
        )

        self.assertEqual(len(self.gateway.request_logs), 1)
        self.assertEqual(self.gateway.request_count['test'], 1)
        print("✅ 메트릭 수집 테스트 통과")

    def test_metrics_summary(self):
        """메트릭 요약 테스트"""
        self.gateway._log_request("service1", "GET", "/", 200, 0.05, "127.0.0.1")
        self.gateway._log_request("service1", "POST", "/", 201, 0.08, "127.0.0.1")
        self.gateway._log_request("service2", "GET", "/", 500, 0.02, "127.0.0.1")

        metrics = self.gateway.get_metrics()

        self.assertEqual(metrics['total_requests'], 3)
        self.assertEqual(metrics['total_errors'], 1)
        print("✅ 메트릭 요약 테스트 통과")


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def test_end_to_end_workflow(self):
        """종단간 워크플로우 테스트"""
        from learning_engine import LearningEngine, DecisionRecord
        from auto_policy_engine import AutoPolicyEngine
        from alert_system import AlertManager, AlertSeverity

        # 1. 의사결정 기록
        engine = LearningEngine('test_e2e.json')

        record = DecisionRecord(
            timestamp=time.time(),
            metrics={'cpu': 85, 'memory': 78},
            decision='SCALE_UP',
            confidence=0.87,
            path1_action='ROLLBACK',
            path1_confidence=0.76,
            path2_action='SCALE_UP',
            path2_confidence=0.90,
            path3_action='NO_ACTION',
            path3_confidence=0.40,
            path4_recommendation='CANARY_FIRST',
            path4_confidence=0.88
        )
        engine.record_decision(record)

        # 2. 학습
        insights = engine.learn_from_history()

        # 3. 정책 생성
        policy_engine = AutoPolicyEngine('test_e2e_policies.json')
        policy = policy_engine.create_policy_from_threshold(
            metric_name="cpu_usage",
            threshold_value=85,
            comparison=">",
            recommended_action="SCALE_UP",
            confidence=0.87,
            evidence_count=1
        )

        # 4. 알림
        alert_manager = AlertManager('test_e2e_alert.json')
        alert = alert_manager.create_alert(
            title="스케일 업 실행",
            message="CPU 85% → SCALE_UP 결정",
            severity=AlertSeverity.WARNING,
            source="workflow"
        )

        # 검증
        self.assertEqual(len(engine.decisions), 1)
        self.assertIsNotNone(policy.id)
        self.assertFalse(alert.resolved)

        print("✅ 종단간 워크플로우 테스트 통과")

        # 정리
        for f in ['test_e2e.json', 'test_e2e_policies.json', 'test_e2e_alert.json']:
            if os.path.exists(f):
                os.remove(f)


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*80)
    print("🧪 MindLang 통합 테스트 스위트 시작")
    print("="*80 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMindLangCore))
    suite.addTests(loader.loadTestsFromTestCase(TestPolicyEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestLearningEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceProfiler))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIGateway))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 요약
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")
    print(f"\n상태: {'✅ 모든 테스트 통과!' if result.wasSuccessful() else '❌ 테스트 실패'}")
    print("="*80 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
