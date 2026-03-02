#!/usr/bin/env python3
"""
MindLang 대시보드 시스템
Day 13: 실시간 모니터링 대시보드 & 경고 시스템

컴포넌트:
├─ MetricsDashboard: 메트릭 실시간 표시
├─ PerformanceChart: 성능 차트 시각화
├─ AlertManager: 경고 시스템
└─ ReportBuilder: 자동 리포트 생성
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import statistics


class AlertLevel(Enum):
    """경고 수준"""
    INFO = "정보"
    WARNING = "경고"
    CRITICAL = "심각"


class MetricStatus(Enum):
    """메트릭 상태"""
    HEALTHY = "정상"
    WARNING = "주의"
    CRITICAL = "위험"


@dataclass
class Alert:
    """경고 항목"""
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold: float
    timestamp: float
    message: str


class MetricsDashboard:
    """메트릭 실시간 대시보드"""
    
    def __init__(self):
        """초기화"""
        self.metrics: Dict[str, float] = {}
        self.metrics_history: Dict[str, List[float]] = {}
        self.update_times: Dict[str, float] = {}
    
    def update_metric(self, metric_name: str, value: float):
        """메트릭 업데이트"""
        self.metrics[metric_name] = value
        self.update_times[metric_name] = time.time()
        
        if metric_name not in self.metrics_history:
            self.metrics_history[metric_name] = []
        
        self.metrics_history[metric_name].append(value)
        
        # 최근 100개만 유지
        if len(self.metrics_history[metric_name]) > 100:
            self.metrics_history[metric_name].pop(0)
    
    def get_metric_status(self, metric_name: str, 
                         warning_threshold: float,
                         critical_threshold: float) -> MetricStatus:
        """메트릭 상태 판정"""
        if metric_name not in self.metrics:
            return MetricStatus.HEALTHY
        
        value = self.metrics[metric_name]
        
        if value >= critical_threshold:
            return MetricStatus.CRITICAL
        elif value >= warning_threshold:
            return MetricStatus.WARNING
        else:
            return MetricStatus.HEALTHY
    
    def display_dashboard(self) -> str:
        """대시보드 표시"""
        dashboard = "\n" + "=" * 70 + "\n"
        dashboard += "📊 MindLang 실시간 대시보드\n"
        dashboard += "=" * 70 + "\n"
        
        if not self.metrics:
            return dashboard + "메트릭 없음\n"
        
        for metric_name in sorted(self.metrics.keys()):
            value = self.metrics[metric_name]
            
            # 상태 아이콘
            history = self.metrics_history.get(metric_name, [])
            if len(history) > 1:
                trend = "↑" if history[-1] > history[-2] else "↓"
            else:
                trend = "→"
            
            dashboard += f"  {metric_name:<20} {value:>10.2f}  {trend}\n"
        
        dashboard += "=" * 70
        return dashboard
    
    def get_dashboard_state(self) -> Dict[str, Any]:
        """대시보드 상태"""
        return {
            'metrics_count': len(self.metrics),
            'metrics': dict(self.metrics),
            'last_update': max(self.update_times.values()) if self.update_times else 0
        }


class PerformanceChart:
    """성능 차트 시각화"""
    
    @staticmethod
    def line_chart(metric_name: str, values: List[float], width: int = 50) -> str:
        """선 차트"""
        if not values:
            return "데이터 없음"
        
        chart = f"\n📈 {metric_name} 추세\n"
        chart += "=" * width + "\n"
        
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val > min_val else 1
        
        # 차트 높이 10줄
        height = 10
        
        for h in range(height, 0, -1):
            line = ""
            threshold = min_val + (h / height) * range_val
            
            for v in values[-width:]:
                if v >= threshold:
                    line += "█"
                else:
                    line += " "
            
            chart += f"{threshold:>6.1f} ┤ {line}\n"
        
        chart += "       └" + "─" * width + "\n"
        return chart
    
    @staticmethod
    def bar_chart(data: Dict[str, float], width: int = 40) -> str:
        """막대 차트"""
        chart = "\n📊 메트릭 비교\n"
        chart += "=" * 60 + "\n"
        
        if not data:
            return chart + "데이터 없음"
        
        max_val = max(data.values()) if data else 1
        
        for name, value in sorted(data.items(), key=lambda x: x[1], reverse=True):
            bar_width = int((value / max_val) * width)
            bar = "█" * bar_width
            chart += f"{name:<15} {bar:<40} {value:>8.1f}\n"
        
        chart += "=" * 60
        return chart
    
    @staticmethod
    def heatmap(data: List[List[float]], rows: int = 5, cols: int = 10) -> str:
        """히트맵"""
        chart = "\n🔥 히트맵\n"
        chart += "=" * (cols * 2 + 10) + "\n"
        
        if not data:
            return chart + "데이터 없음"
        
        flat = [v for row in data for v in row]
        min_val = min(flat)
        max_val = max(flat)
        range_val = max_val - min_val if max_val > min_val else 1
        
        for row in data[-rows:]:
            for val in row[-cols:]:
                # 0-9 색상 레벨
                level = int((val - min_val) / range_val * 9)
                char = "█▓▒░"[level // 3]
                chart += f"{char} "
            chart += "\n"
        
        chart += "=" * (cols * 2 + 10)
        return chart


class AlertManager:
    """경고 관리 시스템"""
    
    def __init__(self):
        """초기화"""
        self.alerts: List[Alert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}
    
    def set_threshold(self, metric_name: str, 
                     warning: float, critical: float):
        """임계값 설정"""
        self.thresholds[metric_name] = {
            'warning': warning,
            'critical': critical
        }
    
    def check_metric(self, metric_name: str, value: float) -> Optional[Alert]:
        """메트릭 확인 & 경고 생성"""
        if metric_name not in self.thresholds:
            return None
        
        thresholds = self.thresholds[metric_name]
        critical = thresholds['critical']
        warning = thresholds['warning']
        
        alert = None
        
        if value >= critical:
            alert = Alert(
                level=AlertLevel.CRITICAL,
                metric_name=metric_name,
                current_value=value,
                threshold=critical,
                timestamp=time.time(),
                message=f"🚨 심각: {metric_name}={value:.1f} (임계값: {critical})"
            )
        elif value >= warning:
            alert = Alert(
                level=AlertLevel.WARNING,
                metric_name=metric_name,
                current_value=value,
                threshold=warning,
                timestamp=time.time(),
                message=f"⚠️  경고: {metric_name}={value:.1f} (임계값: {warning})"
            )
        
        if alert:
            self.alerts.append(alert)
        
        return alert
    
    def get_active_alerts(self) -> List[Alert]:
        """활성 경고 조회"""
        cutoff_time = time.time() - 300  # 5분 이내
        return [a for a in self.alerts if a.timestamp > cutoff_time]
    
    def display_alerts(self) -> str:
        """경고 표시"""
        alerts = self.get_active_alerts()
        
        if not alerts:
            return "활성 경고 없음 ✅"
        
        display = "\n🚨 활성 경고\n"
        display += "=" * 70 + "\n"
        
        for alert in sorted(alerts, key=lambda a: a.level.value, reverse=True):
            display += f"{alert.message}\n"
        
        display += "=" * 70
        return display


class ReportBuilder:
    """자동 리포트 생성"""
    
    def __init__(self):
        """초기화"""
        self.analysis_history: List[Dict[str, Any]] = []
    
    def build_summary_report(self, metrics_dashboard: MetricsDashboard,
                            alert_manager: AlertManager) -> str:
        """요약 리포트 생성"""
        report = "\n" + "=" * 70 + "\n"
        report += "📋 MindLang 분석 리포트\n"
        report += "=" * 70 + "\n"
        
        # 메트릭 통계
        metrics = metrics_dashboard.metrics
        if metrics:
            values = list(metrics.values())
            report += f"\n📊 메트릭 통계\n"
            report += f"  - 메트릭 개수: {len(metrics)}\n"
            report += f"  - 평균: {statistics.mean(values):.2f}\n"
            report += f"  - 중앙값: {statistics.median(values):.2f}\n"
            report += f"  - 최소: {min(values):.2f}\n"
            report += f"  - 최대: {max(values):.2f}\n"
            
            if len(values) > 1:
                report += f"  - 표준편차: {statistics.stdev(values):.2f}\n"
        
        # 경고 통계
        active_alerts = alert_manager.get_active_alerts()
        critical_count = sum(1 for a in active_alerts if a.level == AlertLevel.CRITICAL)
        warning_count = sum(1 for a in active_alerts if a.level == AlertLevel.WARNING)
        
        report += f"\n⚠️  경고 현황\n"
        report += f"  - 심각: {critical_count}\n"
        report += f"  - 경고: {warning_count}\n"
        report += f"  - 총: {len(active_alerts)}\n"
        
        # 권장사항
        report += f"\n💡 권장사항\n"
        if critical_count > 0:
            report += f"  - 🚨 심각한 메트릭 {critical_count}개를 즉시 확인하세요\n"
        if warning_count > 0:
            report += f"  - ⚠️  경고 메트릭 {warning_count}개를 모니터링하세요\n"
        if not active_alerts:
            report += f"  - ✅ 모든 메트릭이 정상입니다\n"
        
        report += "=" * 70
        return report
    
    def build_performance_report(self, metric_values: Dict[str, List[float]]) -> str:
        """성능 리포트 생성"""
        report = "\n" + "=" * 70 + "\n"
        report += "⚡ 성능 분석 리포트\n"
        report += "=" * 70 + "\n"
        
        for metric_name, values in metric_values.items():
            if not values:
                continue
            
            report += f"\n📌 {metric_name}\n"
            report += f"  - 데이터 포인트: {len(values)}\n"
            report += f"  - 평균: {statistics.mean(values):.2f}\n"
            report += f"  - 최소: {min(values):.2f}\n"
            report += f"  - 최대: {max(values):.2f}\n"
            
            if len(values) > 1:
                report += f"  - 변동성: {statistics.stdev(values):.2f}\n"
                
                # 추세 분석
                recent = values[-5:] if len(values) >= 5 else values
                trend = "상승" if recent[-1] > statistics.mean(recent[:-1]) else "하강"
                report += f"  - 추세: {trend}\n"
        
        report += "=" * 70
        return report


class DashboardSystem:
    """통합 대시보드 시스템"""
    
    def __init__(self):
        """초기화"""
        self.dashboard = MetricsDashboard()
        self.alert_manager = AlertManager()
        self.report_builder = ReportBuilder()
        self.chart = PerformanceChart()
    
    def update_system(self, metrics: Dict[str, float]):
        """시스템 업데이트"""
        for metric_name, value in metrics.items():
            self.dashboard.update_metric(metric_name, value)
            self.alert_manager.check_metric(metric_name, value)
    
    def get_full_display(self) -> str:
        """전체 디스플레이"""
        display = self.dashboard.display_dashboard()
        display += self.alert_manager.display_alerts()
        return display
    
    def get_full_report(self) -> str:
        """전체 리포트"""
        report = self.report_builder.build_summary_report(
            self.dashboard,
            self.alert_manager
        )
        
        if self.dashboard.metrics_history:
            report += self.report_builder.build_performance_report(
                self.dashboard.metrics_history
            )
        
        return report


if __name__ == "__main__":
    print("✅ 대시보드 시스템 로드됨")
