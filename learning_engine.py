#!/usr/bin/env python3
"""
MindLang 학습 엔진
과거 의사결정으로부터 자동으로 학습

학습 항목:
- 의사결정의 정확도 (후속 결과로 검증)
- 각 경로의 신뢰도 재계산
- 최적 AI 모델 선택 학습
- 위험 패턴 인식
- 자동 정책 조정
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics


@dataclass
class DecisionRecord:
    """의사결정 기록"""
    timestamp: float
    metrics: Dict
    decision: str
    confidence: float
    path1_action: str
    path1_confidence: float
    path2_action: str
    path2_confidence: float
    path3_action: str
    path3_confidence: float
    path4_recommendation: str
    path4_confidence: float
    outcome: Optional[str] = None  # 실제 결과
    outcome_time: Optional[float] = None  # 결과 확인 시간
    success: Optional[bool] = None  # 성공 여부


@dataclass
class ModelPerformance:
    """모델별 성능 추적"""
    model: str
    total_recommendations: int = 0
    correct_recommendations: int = 0
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    avg_latency: float = 0.0
    cost_total: float = 0.0
    recent_decisions: List[Dict] = field(default_factory=list)

    def update_accuracy(self):
        """정확도 재계산"""
        if self.total_recommendations == 0:
            self.accuracy = 0.0
        else:
            self.accuracy = self.correct_recommendations / self.total_recommendations


@dataclass
class LearningInsight:
    """학습 통찰"""
    insight_type: str  # pattern, warning, recommendation
    description: str
    confidence: float
    evidence: List[Dict]
    timestamp: float


class LearningEngine:
    """의사결정 학습 엔진"""

    def __init__(self, memory_file: str = 'decision_memory.json'):
        self.memory_file = memory_file
        self.decisions: List[DecisionRecord] = []
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.insights: List[LearningInsight] = []
        self.load_memory()

    def load_memory(self):
        """메모리 로드"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.decisions = [
                    DecisionRecord(**d) for d in data.get('decisions', [])
                ]
        except FileNotFoundError:
            self.decisions = []

    def save_memory(self):
        """메모리 저장"""
        data = {
            'timestamp': time.time(),
            'decisions': [asdict(d) for d in self.decisions],
            'total_decisions': len(self.decisions)
        }
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)

    def record_decision(self, record: DecisionRecord):
        """의사결정 기록"""
        self.decisions.append(record)
        if len(self.decisions) > 1000:  # 최대 1000개 유지
            self.decisions.pop(0)
        self.save_memory()

    def record_outcome(self, decision_index: int, outcome: str, success: bool):
        """의사결정 결과 기록"""
        if 0 <= decision_index < len(self.decisions):
            self.decisions[decision_index].outcome = outcome
            self.decisions[decision_index].outcome_time = time.time()
            self.decisions[decision_index].success = success
            self.save_memory()

    def learn_from_history(self) -> List[LearningInsight]:
        """과거로부터 학습"""
        self.insights = []

        # 1. 정확도 분석
        self._analyze_accuracy()

        # 2. 패턴 인식
        self._recognize_patterns()

        # 3. 위험 신호 탐지
        self._detect_warnings()

        # 4. 최적 모델 학습
        self._learn_optimal_models()

        return self.insights

    def _analyze_accuracy(self):
        """정확도 분석"""
        if not self.decisions:
            return

        # 최근 50개 결정만 분석 (최근이 중요)
        recent = self.decisions[-50:]
        successful = [d for d in recent if d.success is True]
        accuracy = len(successful) / len(recent) if recent else 0

        # 정확도 추세
        if len(recent) >= 10:
            recent_10 = recent[-10:]
            successful_10 = [d for d in recent_10 if d.success]
            recent_accuracy = len(successful_10) / 10

            trend = "📈 상승" if recent_accuracy > accuracy else "📉 하락"

            insight = LearningInsight(
                insight_type='accuracy',
                description=f"의사결정 정확도: {accuracy:.1%} (최근 10개: {recent_accuracy:.1%}) {trend}",
                confidence=0.85,
                evidence=[{'accuracy': accuracy, 'recent_accuracy': recent_accuracy}],
                timestamp=time.time()
            )
            self.insights.append(insight)

    def _recognize_patterns(self):
        """패턴 인식"""
        if len(self.decisions) < 10:
            return

        recent = self.decisions[-30:]

        # 같은 결정이 반복되는 패턴
        decision_counts = {}
        for d in recent:
            decision_counts[d.decision] = decision_counts.get(d.decision, 0) + 1

        # 80% 이상 같은 결정
        if decision_counts:
            most_common = max(decision_counts, key=decision_counts.get)
            count = decision_counts[most_common]
            if count / len(recent) > 0.8:
                insight = LearningInsight(
                    insight_type='pattern',
                    description=f"반복 패턴: '{most_common}'이 {count}/{len(recent)}번 (80% 이상). 상황이 안정적이거나 동일한 문제 반복.",
                    confidence=0.8,
                    evidence=[{'pattern': most_common, 'frequency': count / len(recent)}],
                    timestamp=time.time()
                )
                self.insights.append(insight)

        # CPU 높음 → SCALE_UP 패턴
        scale_up_decisions = [d for d in recent if d.decision == 'SCALE_UP']
        if len(scale_up_decisions) >= 3:
            avg_cpu = statistics.mean([
                d.metrics.get('cpu_usage', 0) for d in scale_up_decisions
            ])
            insight = LearningInsight(
                insight_type='pattern',
                description=f"CPU 높음 → SCALE_UP 패턴: CPU 평균 {avg_cpu:.1f}%에서 스케일업 결정",
                confidence=0.75,
                evidence=[{'avg_cpu': avg_cpu, 'decisions': len(scale_up_decisions)}],
                timestamp=time.time()
            )
            self.insights.append(insight)

    def _detect_warnings(self):
        """위험 신호 탐지"""
        if not self.decisions:
            return

        recent = self.decisions[-20:]

        # 연속 실패
        failures = 0
        for d in recent[-5:]:
            if d.success is False:
                failures += 1

        if failures >= 3:
            insight = LearningInsight(
                insight_type='warning',
                description=f"⚠️  경고: 최근 5개 결정 중 {failures}개 실패. 의사결정 로직 재검토 필요.",
                confidence=0.9,
                evidence=[{'failures': failures, 'recent': 5}],
                timestamp=time.time()
            )
            self.insights.append(insight)

        # 과도한 변동성
        actions = [d.decision for d in recent]
        unique_actions = len(set(actions))
        if unique_actions >= 4 and len(recent) >= 10:
            insight = LearningInsight(
                insight_type='warning',
                description=f"🔄 경고: 의사결정이 불안정 ({unique_actions}가지 다른 결정 in {len(recent)}). 시스템이 진동 상태.",
                confidence=0.7,
                evidence=[{'unique_actions': unique_actions, 'total': len(recent)}],
                timestamp=time.time()
            )
            self.insights.append(insight)

    def _learn_optimal_models(self):
        """최적 모델 학습"""
        if not self.decisions:
            return

        # 각 모델의 성능 추적
        models = {
            'path1': [d.path1_action for d in self.decisions],
            'path2': [d.path2_action for d in self.decisions],
            'path3': [d.path3_action for d in self.decisions],
            'path4': [d.path4_recommendation for d in self.decisions]
        }

        # 최근 결정에서 각 경로의 정확도
        recent = self.decisions[-30:]
        if recent:
            path_correctness = {
                'path1': 0,
                'path2': 0,
                'path3': 0,
                'path4': 0
            }
            for d in recent:
                if d.success:
                    # 성공한 결정의 경로들에 점수 부여
                    if d.path1_action == d.decision:
                        path_correctness['path1'] += 1
                    if d.path2_action == d.decision:
                        path_correctness['path2'] += 1
                    if d.path3_action == d.decision:
                        path_correctness['path3'] += 1
                    if d.path4_recommendation == d.decision:
                        path_correctness['path4'] += 1

            best_path = max(path_correctness, key=path_correctness.get)
            score = path_correctness[best_path] / len(recent)

            if score > 0.6:
                insight = LearningInsight(
                    insight_type='recommendation',
                    description=f"💡 최적 모델: {best_path.upper()} (정확도 {score:.1%}). "
                               f"이 경로를 신뢰도 조정에 사용하세요.",
                    confidence=0.8,
                    evidence=[path_correctness],
                    timestamp=time.time()
                )
                self.insights.append(insight)

    def get_recommendations(self) -> Dict:
        """권고사항 생성"""
        insights = self.learn_from_history()

        return {
            'timestamp': datetime.now().isoformat(),
            'total_decisions': len(self.decisions),
            'insights': [
                {
                    'type': i.insight_type,
                    'description': i.description,
                    'confidence': i.confidence,
                    'evidence': i.evidence
                }
                for i in insights
            ],
            'next_action': self._generate_next_action(insights)
        }

    def _generate_next_action(self, insights: List[LearningInsight]) -> str:
        """다음 행동 추천"""
        warnings = [i for i in insights if i.insight_type == 'warning']
        if warnings:
            high_confidence = [w for w in warnings if w.confidence > 0.8]
            if high_confidence:
                return f"⚠️  긴급: {high_confidence[0].description}"

        recommendations = [i for i in insights if i.insight_type == 'recommendation']
        if recommendations:
            return f"💡 {recommendations[0].description}"

        return "✅ 시스템이 정상 작동 중입니다."

    def print_insights(self):
        """통찰 출력"""
        recs = self.get_recommendations()

        print("\n" + "="*80)
        print("🧠 MindLang 학습 엔진 분석")
        print("="*80)

        print(f"\n📊 총 의사결정: {recs['total_decisions']}개")

        print("\n" + "-"*80)
        print("📋 발견된 통찰:")
        print("-"*80)

        for insight in recs['insights']:
            icon = {
                'accuracy': '📈',
                'pattern': '🔄',
                'warning': '⚠️',
                'recommendation': '💡'
            }.get(insight['type'], '📌')

            print(f"\n{icon} {insight['type'].upper()}")
            print(f"   설명: {insight['description']}")
            print(f"   신뢰도: {insight['confidence']:.1%}")

        print("\n" + "="*80)
        print("🎯 다음 단계")
        print("="*80)
        print(f"\n{recs['next_action']}")


# 사용 예시
if __name__ == "__main__":
    engine = LearningEngine()

    # 테스트 데이터 추가
    print("📚 테스트 데이터 로딩...")
    for i in range(20):
        record = DecisionRecord(
            timestamp=time.time() - (20 - i) * 300,
            metrics={
                'cpu_usage': 50 + i % 40,
                'memory_usage': 60 + i % 30,
                'error_rate': 0.01 + (i % 5) * 0.005
            },
            decision='SCALE_UP' if i % 3 == 0 else 'CONTINUE',
            confidence=0.75 + (i % 3) * 0.1,
            path1_action='ROLLBACK',
            path1_confidence=0.6,
            path2_action='SCALE_UP',
            path2_confidence=0.8,
            path3_action='CONTINUE',
            path3_confidence=0.7,
            path4_recommendation='MONITOR',
            path4_confidence=0.65,
            success=i % 4 != 0  # 75% 성공률
        )
        engine.record_decision(record)

    # 분석
    engine.print_insights()
