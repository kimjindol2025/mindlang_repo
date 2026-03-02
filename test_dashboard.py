#!/usr/bin/env python3
"""
MindLang 대시보드 시스템 테스트
Day 13: 메트릭 표시, 차트, 경고, 리포트 검증

테스트:
├─ MetricsDashboard: 메트릭 표시
├─ PerformanceChart: 성능 차트
├─ AlertManager: 경고 시스템
└─ ReportBuilder: 리포트 생성
"""

import unittest
import time
import random
from dashboard_system import (
    MetricsDashboard, PerformanceChart, AlertManager,
    ReportBuilder, DashboardSystem, AlertLevel, MetricStatus
)


class TestMetricsDashboard(unittest.TestCase):
    """메트릭 대시보드 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.dashboard = MetricsDashboard()
    
    def test_update_metric(self):
        """메트릭 업데이트"""
        self.dashboard.update_metric("cpu_usage", 45.5)
        
        self.assertIn("cpu_usage", self.dashboard.metrics)
        self.assertEqual(self.dashboard.metrics["cpu_usage"], 45.5)
        print("✅ 메트릭 업데이트 통과")
    
    def test_metric_history(self):
        """메트릭 히스토리"""
        for i in range(10):
            self.dashboard.update_metric("temperature", 20 + i)
        
        history = self.dashboard.metrics_history["temperature"]
        self.assertEqual(len(history), 10)
        self.assertEqual(history[0], 20)
        self.assertEqual(history[-1], 29)
        print("✅ 메트릭 히스토리 통과")
    
    def test_metric_status_healthy(self):
        """메트릭 상태: 정상"""
        self.dashboard.update_metric("cpu", 30)
        status = self.dashboard.get_metric_status("cpu", 70, 90)
        
        self.assertEqual(status, MetricStatus.HEALTHY)
        print("✅ 정상 상태 통과")
    
    def test_metric_status_warning(self):
        """메트릭 상태: 경고"""
        self.dashboard.update_metric("cpu", 75)
        status = self.dashboard.get_metric_status("cpu", 70, 90)
        
        self.assertEqual(status, MetricStatus.WARNING)
        print("✅ 경고 상태 통과")
    
    def test_metric_status_critical(self):
        """메트릭 상태: 심각"""
        self.dashboard.update_metric("cpu", 95)
        status = self.dashboard.get_metric_status("cpu", 70, 90)
        
        self.assertEqual(status, MetricStatus.CRITICAL)
        print("✅ 심각 상태 통과")
    
    def test_display_dashboard(self):
        """대시보드 표시"""
        self.dashboard.update_metric("cpu", 50)
        self.dashboard.update_metric("memory", 60)
        
        display = self.dashboard.display_dashboard()
        
        self.assertIn("실시간 대시보드", display)
        self.assertIn("cpu", display)
        self.assertIn("memory", display)
        print("✅ 대시보드 표시 통과")


class TestPerformanceChart(unittest.TestCase):
    """성능 차트 테스트"""
    
    def test_line_chart(self):
        """선 차트"""
        values = [10, 20, 15, 25, 30, 28, 35]
        chart = PerformanceChart.line_chart("test_metric", values)
        
        self.assertIn("추세", chart)
        self.assertIn("█", chart)
        print("✅ 선 차트 통과")
    
    def test_bar_chart(self):
        """막대 차트"""
        data = {"cpu": 50, "memory": 70, "disk": 30}
        chart = PerformanceChart.bar_chart(data)
        
        self.assertIn("비교", chart)
        self.assertIn("█", chart)
        self.assertIn("memory", chart)
        print("✅ 막대 차트 통과")
    
    def test_heatmap(self):
        """히트맵"""
        data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        heatmap = PerformanceChart.heatmap(data)
        
        self.assertIn("히트맵", heatmap)
        self.assertIn("█", heatmap)
        print("✅ 히트맵 통과")
    
    def test_empty_chart(self):
        """빈 차트"""
        chart = PerformanceChart.line_chart("empty", [])
        self.assertIn("데이터 없음", chart)
        print("✅ 빈 차트 처리 통과")


class TestAlertManager(unittest.TestCase):
    """경고 관리 시스템 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.alerts = AlertManager()
    
    def test_set_threshold(self):
        """임계값 설정"""
        self.alerts.set_threshold("cpu", 70, 90)
        
        self.assertIn("cpu", self.alerts.thresholds)
        self.assertEqual(self.alerts.thresholds["cpu"]["warning"], 70)
        self.assertEqual(self.alerts.thresholds["cpu"]["critical"], 90)
        print("✅ 임계값 설정 통과")
    
    def test_alert_no_threshold(self):
        """임계값 없음"""
        alert = self.alerts.check_metric("unknown", 50)
        
        self.assertIsNone(alert)
        print("✅ 임계값 없음 처리 통과")
    
    def test_alert_healthy(self):
        """경고 없음 (정상)"""
        self.alerts.set_threshold("cpu", 70, 90)
        alert = self.alerts.check_metric("cpu", 50)
        
        self.assertIsNone(alert)
        print("✅ 경고 없음 통과")
    
    def test_alert_warning(self):
        """경고 발생 (주의)"""
        self.alerts.set_threshold("cpu", 70, 90)
        alert = self.alerts.check_metric("cpu", 75)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.WARNING)
        print("✅ 경고 발생 통과")
    
    def test_alert_critical(self):
        """경고 발생 (심각)"""
        self.alerts.set_threshold("cpu", 70, 90)
        alert = self.alerts.check_metric("cpu", 95)
        
        self.assertIsNotNone(alert)
        self.assertEqual(alert.level, AlertLevel.CRITICAL)
        print("✅ 심각 경고 발생 통과")
    
    def test_get_active_alerts(self):
        """활성 경고 조회"""
        self.alerts.set_threshold("cpu", 70, 90)
        self.alerts.check_metric("cpu", 95)
        
        active = self.alerts.get_active_alerts()
        
        self.assertEqual(len(active), 1)
        print("✅ 활성 경고 조회 통과")
    
    def test_display_alerts(self):
        """경고 표시"""
        self.alerts.set_threshold("cpu", 70, 90)
        self.alerts.check_metric("cpu", 95)
        
        display = self.alerts.display_alerts()
        
        self.assertIn("활성 경고", display)
        self.assertIn("심각", display)
        print("✅ 경고 표시 통과")


class TestReportBuilder(unittest.TestCase):
    """리포트 생성 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.builder = ReportBuilder()
        self.dashboard = MetricsDashboard()
        self.alerts = AlertManager()
    
    def test_build_summary_report(self):
        """요약 리포트"""
        self.dashboard.update_metric("cpu", 50)
        self.dashboard.update_metric("memory", 60)
        
        report = self.builder.build_summary_report(self.dashboard, self.alerts)
        
        self.assertIn("분석 리포트", report)
        self.assertIn("메트릭 통계", report)
        self.assertIn("경고 현황", report)
        print("✅ 요약 리포트 통과")
    
    def test_build_performance_report(self):
        """성능 리포트"""
        metrics = {
            "cpu": [20, 30, 40, 50, 60],
            "memory": [50, 55, 60, 65, 70]
        }
        
        report = self.builder.build_performance_report(metrics)
        
        self.assertIn("성능 분석", report)
        self.assertIn("cpu", report)
        self.assertIn("평균", report)
        print("✅ 성능 리포트 통과")


class TestDashboardSystem(unittest.TestCase):
    """통합 대시보드 시스템 테스트"""
    
    def setUp(self):
        """테스트 전 초기화"""
        self.system = DashboardSystem()
        
        # 임계값 설정
        self.system.alert_manager.set_threshold("cpu", 70, 90)
        self.system.alert_manager.set_threshold("memory", 75, 90)
    
    def test_update_system(self):
        """시스템 업데이트"""
        metrics = {"cpu": 45, "memory": 55}
        self.system.update_system(metrics)
        
        self.assertEqual(self.system.dashboard.metrics["cpu"], 45)
        self.assertEqual(self.system.dashboard.metrics["memory"], 55)
        print("✅ 시스템 업데이트 통과")
    
    def test_full_display(self):
        """전체 디스플레이"""
        metrics = {"cpu": 45, "memory": 55}
        self.system.update_system(metrics)
        
        display = self.system.get_full_display()
        
        self.assertIn("실시간 대시보드", display)
        self.assertIn("활성 경고", display)
        print("✅ 전체 디스플레이 통과")
    
    def test_full_report(self):
        """전체 리포트"""
        for i in range(10):
            metrics = {"cpu": 40 + i, "memory": 50 + i}
            self.system.update_system(metrics)
        
        report = self.system.get_full_report()
        
        self.assertIn("분석 리포트", report)
        self.assertIn("성능 분석", report)
        print("✅ 전체 리포트 통과")
    
    def test_system_with_alerts(self):
        """경고 포함 시스템"""
        # 정상 메트릭
        self.system.update_system({"cpu": 50, "memory": 60})
        
        # 경고 메트릭
        self.system.update_system({"cpu": 85, "memory": 95})
        
        active_alerts = self.system.alert_manager.get_active_alerts()
        
        self.assertGreater(len(active_alerts), 0)
        print("✅ 경고 포함 시스템 통과")


class TestDashboardPerformance(unittest.TestCase):
    """대시보드 성능 테스트"""
    
    def test_dashboard_update_speed(self):
        """대시보드 업데이트 속도"""
        import time
        dashboard = MetricsDashboard()
        
        start = time.time()
        for i in range(1000):
            dashboard.update_metric(f"metric_{i%10}", random.random() * 100)
        elapsed = (time.time() - start) * 1000
        
        avg_time = elapsed / 1000
        print(f"⚡ 업데이트 속도: {avg_time:.3f}ms (1000회)")
        
        self.assertLess(avg_time, 1.0)
        print("✅ 업데이트 속도 목표 달성")
    
    def test_report_generation_speed(self):
        """리포트 생성 속도"""
        import time
        system = DashboardSystem()
        
        # 데이터 생성
        for i in range(100):
            system.update_system({"cpu": 40 + random.random() * 20})
        
        start = time.time()
        report = system.get_full_report()
        elapsed = (time.time() - start) * 1000
        
        print(f"⚡ 리포트 생성: {elapsed:.1f}ms")
        
        self.assertLess(elapsed, 100)
        print("✅ 리포트 생성 속도 목표 달성")


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 MindLang Day 13: 대시보드 시스템 테스트")
    print("=" * 70 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsDashboard))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformanceChart))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertManager))
    suite.addTests(loader.loadTestsFromTestCase(TestReportBuilder))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestDashboardPerformance))
    
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
        print("🎯 Day 13 대시보드 시스템 완성!")
    else:
        print("\n❌ 일부 테스트 실패")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
