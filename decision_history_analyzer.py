#!/usr/bin/env python3
"""
의사결정 이력 분석기
MindLang의 모든 의사결정을 분석하고 시각화

분석 항목:
- 시계열 의사결정 추세
- 의사결정 분포 (Pie chart)
- 신뢰도 추이
- 경로별 정확도
- 메트릭 vs 의사결정 상관관계
- 최고/최악의 결정
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import statistics


@dataclass
class TimeSeriesData:
    """시계열 데이터"""
    timestamps: List[float]
    decisions: List[str]
    confidences: List[float]
    metrics: List[Dict]


class DecisionHistoryAnalyzer:
    """의사결정 이력 분석기"""

    def __init__(self, history_file: str = 'decision_memory.json'):
        self.history_file = history_file
        self.decisions = []
        self.load_history()

    def load_history(self):
        """이력 로드"""
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.decisions = data.get('decisions', [])
        except FileNotFoundError:
            print(f"⚠️ {self.history_file}를 찾을 수 없습니다.")
            self.decisions = []

    def analyze_decision_distribution(self) -> Dict:
        """의사결정 분포 분석"""
        if not self.decisions:
            return {}

        decisions = [d['decision'] for d in self.decisions]
        distribution = {}

        for decision in decisions:
            distribution[decision] = distribution.get(decision, 0) + 1

        # 비율 계산
        total = len(decisions)
        distribution_pct = {
            k: v/total for k, v in distribution.items()
        }

        return {
            'count': distribution,
            'percentage': distribution_pct,
            'total': total
        }

    def analyze_confidence_trends(self) -> Dict:
        """신뢰도 추이 분석"""
        if not self.decisions:
            return {}

        confidences = [d['confidence'] for d in self.decisions if 'confidence' in d]

        if not confidences:
            return {}

        # 전체 통계
        stats = {
            'average': statistics.mean(confidences),
            'median': statistics.median(confidences),
            'min': min(confidences),
            'max': max(confidences),
            'stdev': statistics.stdev(confidences) if len(confidences) > 1 else 0
        }

        # 시간대별 신뢰도
        recent_10 = confidences[-10:] if len(confidences) >= 10 else confidences
        recent_50 = confidences[-50:] if len(confidences) >= 50 else confidences

        stats['recent_10_avg'] = statistics.mean(recent_10)
        stats['recent_50_avg'] = statistics.mean(recent_50)

        # 추세
        if len(recent_50) >= 25:
            first_half = recent_50[:25]
            second_half = recent_50[25:]
            trend = "📈 상승" if statistics.mean(second_half) > statistics.mean(first_half) else "📉 하락"
            stats['trend'] = trend

        return stats

    def analyze_path_accuracy(self) -> Dict:
        """경로별 정확도 분석"""
        if not self.decisions:
            return {}

        path_accuracy = {
            'path1': {'correct': 0, 'total': 0},
            'path2': {'correct': 0, 'total': 0},
            'path3': {'correct': 0, 'total': 0},
            'path4': {'correct': 0, 'total': 0}
        }

        for d in self.decisions:
            if d.get('success') is not None:
                decision = d.get('decision')

                # 각 경로 확인
                if d.get('path1_action') == decision:
                    path_accuracy['path1']['total'] += 1
                    if d.get('success'):
                        path_accuracy['path1']['correct'] += 1

                if d.get('path2_action') == decision:
                    path_accuracy['path2']['total'] += 1
                    if d.get('success'):
                        path_accuracy['path2']['correct'] += 1

                if d.get('path3_action') == decision:
                    path_accuracy['path3']['total'] += 1
                    if d.get('success'):
                        path_accuracy['path3']['correct'] += 1

                if d.get('path4_recommendation') == decision:
                    path_accuracy['path4']['total'] += 1
                    if d.get('success'):
                        path_accuracy['path4']['correct'] += 1

        # 정확도 계산
        for path, data in path_accuracy.items():
            if data['total'] > 0:
                data['accuracy'] = data['correct'] / data['total']
            else:
                data['accuracy'] = 0.0

        return path_accuracy

    def analyze_metric_correlation(self) -> Dict:
        """메트릭 vs 의사결정 상관관계"""
        if len(self.decisions) < 10:
            return {}

        correlations = {
            'high_cpu_scale_up': 0,
            'high_error_rollback': 0,
            'high_cost_continue': 0
        }

        for d in self.decisions:
            metrics = d.get('metrics', {})
            decision = d.get('decision')

            # CPU 높음 → SCALE_UP
            if metrics.get('cpu_usage', 0) > 75 and decision == 'SCALE_UP':
                correlations['high_cpu_scale_up'] += 1

            # 에러 높음 → ROLLBACK
            if metrics.get('error_rate', 0) > 0.05 and decision == 'ROLLBACK':
                correlations['high_error_rollback'] += 1

            # 비용 낮음 → CONTINUE
            if metrics.get('hourly_cost', 0) < 50 and decision == 'CONTINUE':
                correlations['high_cost_continue'] += 1

        return correlations

    def get_best_decisions(self, limit: int = 5) -> List[Dict]:
        """최고의 결정 찾기"""
        successful = [
            d for d in self.decisions
            if d.get('success') is True
        ]

        # 신뢰도 높은 순으로 정렬
        successful.sort(
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )

        return successful[:limit]

    def get_worst_decisions(self, limit: int = 5) -> List[Dict]:
        """최악의 결정 찾기"""
        failures = [
            d for d in self.decisions
            if d.get('success') is False
        ]

        # 신뢰도 높았지만 실패한 것들
        failures.sort(
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )

        return failures[:limit]

    def generate_report(self) -> str:
        """전체 분석 리포트 생성"""
        report = []

        report.append("\n" + "="*80)
        report.append("📊 MindLang 의사결정 이력 분석 보고서")
        report.append("="*80)

        report.append(f"\n📅 분석 시간: {datetime.now().isoformat()}")
        report.append(f"📈 총 의사결정: {len(self.decisions)}개")

        # 의사결정 분포
        report.append("\n" + "-"*80)
        report.append("1️⃣ 의사결정 분포")
        report.append("-"*80)

        dist = self.analyze_decision_distribution()
        if dist:
            for decision, count in dist['count'].items():
                pct = dist['percentage'].get(decision, 0)
                bar = "█" * int(pct * 30)
                report.append(f"\n  {decision}: {count}개 ({pct:.1%})")
                report.append(f"  {bar}")

        # 신뢰도 추이
        report.append("\n" + "-"*80)
        report.append("2️⃣ 신뢰도 분석")
        report.append("-"*80)

        conf = self.analyze_confidence_trends()
        if conf:
            report.append(f"\n  평균: {conf['average']:.1%}")
            report.append(f"  중앙값: {conf['median']:.1%}")
            report.append(f"  범위: {conf['min']:.1%} ~ {conf['max']:.1%}")
            report.append(f"  표준편차: {conf['stdev']:.1%}")
            if 'trend' in conf:
                report.append(f"  추세: {conf['trend']}")

        # 경로별 정확도
        report.append("\n" + "-"*80)
        report.append("3️⃣ 경로별 정확도")
        report.append("-"*80)

        path_acc = self.analyze_path_accuracy()
        if path_acc:
            for path, data in sorted(path_acc.items()):
                accuracy = data['accuracy']
                bar = "█" * int(accuracy * 20)
                report.append(f"\n  {path.upper()}: {accuracy:.1%} ({data['correct']}/{data['total']})")
                report.append(f"  {bar}")

        # 메트릭 상관관계
        report.append("\n" + "-"*80)
        report.append("4️⃣ 메트릭 상관관계")
        report.append("-"*80)

        corr = self.analyze_metric_correlation()
        if corr:
            for correlation, count in corr.items():
                report.append(f"\n  {correlation}: {count}회 발생")

        # 최고의 결정
        report.append("\n" + "-"*80)
        report.append("5️⃣ 최고의 결정 (Top 5)")
        report.append("-"*80)

        best = self.get_best_decisions(5)
        if best:
            for i, decision in enumerate(best, 1):
                report.append(f"\n  {i}. {decision.get('decision')} "
                            f"(신뢰도: {decision.get('confidence', 0):.1%})")

        # 최악의 결정
        report.append("\n" + "-"*80)
        report.append("6️⃣ 최악의 결정 (Top 5)")
        report.append("-"*80)

        worst = self.get_worst_decisions(5)
        if worst:
            for i, decision in enumerate(worst, 1):
                report.append(f"\n  {i}. {decision.get('decision')} "
                            f"(신뢰도: {decision.get('confidence', 0):.1%}) ❌")

        report.append("\n" + "="*80)

        return "\n".join(report)

    def print_report(self):
        """리포트 출력"""
        report = self.generate_report()
        print(report)

        # 파일로 저장
        with open('decision_analysis_report.txt', 'w') as f:
            f.write(report)

        print("\n✅ 리포트 저장: decision_analysis_report.txt")


# 사용 예시
if __name__ == "__main__":
    analyzer = DecisionHistoryAnalyzer()

    if analyzer.decisions:
        analyzer.print_report()
    else:
        print("❌ 의사결정 이력이 없습니다.")
        print("먼저 learning_engine.py를 실행하여 테스트 데이터를 생성하세요.")
