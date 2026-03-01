#!/usr/bin/env python3
"""
MindLang 비용 최적화 분석기
자동으로 비용 절감 기회를 발견하고 최적화 전략 수립

기능:
- 리소스 사용률 분석
- 비용 절감 기회 식별
- 최적화 전략 제안
- ROI 계산
- 예산 추적 및 알림
"""

import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum


class OptimizationType(Enum):
    """최적화 타입"""
    RESERVED_INSTANCES = "reserved_instances"
    SPOT_INSTANCES = "spot_instances"
    AUTO_SCALING = "auto_scaling"
    RIGHT_SIZING = "right_sizing"
    DATA_COMPRESSION = "data_compression"
    CACHING = "caching"
    SCHEDULE_BASED = "schedule_based"
    RESOURCE_CONSOLIDATION = "resource_consolidation"


@dataclass
class ResourceMetrics:
    """리소스 메트릭"""
    name: str
    resource_type: str  # compute, storage, network, database
    current_cost_per_hour: float
    current_capacity: float
    current_usage: float
    usage_percentage: float
    peak_usage: float
    average_usage: float
    lowest_usage: float


@dataclass
class OptimizationOpportunity:
    """최적화 기회"""
    id: str
    name: str
    optimization_type: str
    description: str
    current_cost_per_year: float
    optimized_cost_per_year: float
    potential_savings: float
    savings_percentage: float
    roi_months: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high
    confidence: float
    priority: int


@dataclass
class OptimizationPlan:
    """최적화 계획"""
    id: str
    timestamp: float
    total_annual_cost: float
    optimized_annual_cost: float
    total_potential_savings: float
    total_savings_percentage: float
    opportunities: List[OptimizationOpportunity]
    implementation_roadmap: List[str]
    estimated_implementation_time_days: int


class CostOptimizer:
    """비용 최적화 엔진"""

    def __init__(self):
        self.resources: Dict[str, ResourceMetrics] = {}
        self.optimization_opportunities: Dict[str, OptimizationOpportunity] = {}
        self.optimization_plans: List[OptimizationPlan] = []
        self.cost_history: List[Dict] = []
        self.budget_alerts: List[Dict] = []

    def add_resource(self, resource: ResourceMetrics):
        """리소스 추가"""
        self.resources[resource.name] = resource
        print(f"✅ 리소스 등록: {resource.name}")

    def analyze_resources(self) -> Dict:
        """리소스 분석"""
        print(f"\n📊 리소스 분석 중: {len(self.resources)}개 리소스\n")

        analysis = {
            'total_resources': len(self.resources),
            'by_type': {},
            'overprovisioned': [],
            'underutilized': [],
            'total_cost_per_year': 0,
            'opportunities': []
        }

        for resource in self.resources.values():
            # 타입별 분류
            res_type = resource.resource_type
            if res_type not in analysis['by_type']:
                analysis['by_type'][res_type] = {'count': 0, 'cost': 0}

            analysis['by_type'][res_type]['count'] += 1
            annual_cost = resource.current_cost_per_hour * 24 * 365
            analysis['by_type'][res_type]['cost'] += annual_cost
            analysis['total_cost_per_year'] += annual_cost

            # 활용률 분석
            usage_percentage = resource.usage_percentage

            if usage_percentage > 85:
                print(f"⚠️  {resource.name}: {usage_percentage:.1f}% 활용 (과부하 위험)")

            elif usage_percentage < 30:
                print(f"⚡ {resource.name}: {usage_percentage:.1f}% 활용 (과잉 프로비저닝)")
                analysis['underutilized'].append({
                    'name': resource.name,
                    'usage': usage_percentage,
                    'potential_savings': annual_cost * 0.5
                })

            else:
                print(f"✓ {resource.name}: {usage_percentage:.1f}% 활용 (정상)")

        print(f"\n💰 연간 총 비용: ${analysis['total_cost_per_year']:,.2f}\n")

        return analysis

    def find_opportunities(self) -> List[OptimizationOpportunity]:
        """최적화 기회 식별"""
        print(f"\n🔍 최적화 기회 식별 중\n")

        opportunities = []

        for resource in self.resources.values():
            # 저활용 리소스 - Right Sizing
            if resource.usage_percentage < 30:
                opportunity = OptimizationOpportunity(
                    id=f"opp_{int(time.time())}_rs_{resource.name}",
                    name=f"{resource.name} Right Sizing",
                    optimization_type=OptimizationType.RIGHT_SIZING.value,
                    description=f"평균 사용률 {resource.average_usage:.1f}%에 맞게 리소스 축소",
                    current_cost_per_year=resource.current_cost_per_hour * 24 * 365,
                    optimized_cost_per_year=resource.current_cost_per_hour * 24 * 365 * 0.5,
                    potential_savings=resource.current_cost_per_hour * 24 * 365 * 0.5,
                    savings_percentage=50.0,
                    roi_months=1,
                    implementation_effort="low",
                    risk_level="low",
                    confidence=0.90,
                    priority=1
                )
                opportunities.append(opportunity)
                print(f"💰 기회 1: {resource.name} Right Sizing - {opportunity.potential_savings:,.0f}$/년 절감")

            # 예약 인스턴스
            if resource.average_usage > 50:
                annual_cost = resource.current_cost_per_hour * 24 * 365
                opportunity = OptimizationOpportunity(
                    id=f"opp_{int(time.time())}_ri_{resource.name}",
                    name=f"{resource.name} Reserved Instances",
                    optimization_type=OptimizationType.RESERVED_INSTANCES.value,
                    description="1년 또는 3년 예약 인스턴스로 전환",
                    current_cost_per_year=annual_cost,
                    optimized_cost_per_year=annual_cost * 0.70,
                    potential_savings=annual_cost * 0.30,
                    savings_percentage=30.0,
                    roi_months=2,
                    implementation_effort="low",
                    risk_level="low",
                    confidence=0.85,
                    priority=2
                )
                opportunities.append(opportunity)
                print(f"💰 기회 2: {resource.name} Reserved Instances - {opportunity.potential_savings:,.0f}$/년 절감")

            # 스팟 인스턴스
            if resource.resource_type == "compute" and resource.usage_percentage < 60:
                annual_cost = resource.current_cost_per_hour * 24 * 365
                opportunity = OptimizationOpportunity(
                    id=f"opp_{int(time.time())}_si_{resource.name}",
                    name=f"{resource.name} Spot Instances",
                    optimization_type=OptimizationType.SPOT_INSTANCES.value,
                    description="스팟 인스턴스로 전환 (최대 90% 할인)",
                    current_cost_per_year=annual_cost,
                    optimized_cost_per_year=annual_cost * 0.40,
                    potential_savings=annual_cost * 0.60,
                    savings_percentage=60.0,
                    roi_months=1,
                    implementation_effort="medium",
                    risk_level="medium",
                    confidence=0.75,
                    priority=3
                )
                opportunities.append(opportunity)
                print(f"💰 기회 3: {resource.name} Spot Instances - {opportunity.potential_savings:,.0f}$/년 절감")

            # 자동 스케일링
            if resource.peak_usage > resource.average_usage * 1.5:
                annual_cost = resource.current_cost_per_hour * 24 * 365
                opportunity = OptimizationOpportunity(
                    id=f"opp_{int(time.time())}_as_{resource.name}",
                    name=f"{resource.name} Auto Scaling",
                    optimization_type=OptimizationType.AUTO_SCALING.value,
                    description="부하 기반 자동 스케일링으로 평시 리소스 축소",
                    current_cost_per_year=annual_cost,
                    optimized_cost_per_year=annual_cost * 0.65,
                    potential_savings=annual_cost * 0.35,
                    savings_percentage=35.0,
                    roi_months=2,
                    implementation_effort="low",
                    risk_level="low",
                    confidence=0.88,
                    priority=2
                )
                opportunities.append(opportunity)
                print(f"💰 기회 4: {resource.name} Auto Scaling - {opportunity.potential_savings:,.0f}$/년 절감")

        # 교차 리소스 최적화
        if len(self.resources) > 1:
            opportunity = OptimizationOpportunity(
                id=f"opp_{int(time.time())}_rc",
                name="리소스 통합",
                optimization_type=OptimizationType.RESOURCE_CONSOLIDATION.value,
                description="소규모 리소스들을 통합하여 사용률 향상",
                current_cost_per_year=sum(r.current_cost_per_hour * 24 * 365 for r in self.resources.values()) * 0.2,
                optimized_cost_per_year=sum(r.current_cost_per_hour * 24 * 365 for r in self.resources.values()) * 0.15,
                potential_savings=sum(r.current_cost_per_hour * 24 * 365 for r in self.resources.values()) * 0.05,
                savings_percentage=5.0,
                roi_months=3,
                implementation_effort="high",
                risk_level="medium",
                confidence=0.70,
                priority=4
            )
            opportunities.append(opportunity)

        # 우선순위 정렬
        opportunities = sorted(opportunities, key=lambda x: (x.priority, -x.savings_percentage))

        for opp in opportunities:
            self.optimization_opportunities[opp.id] = opp

        print(f"\n✅ {len(opportunities)}개의 최적화 기회 발견\n")

        return opportunities

    def create_optimization_plan(self) -> OptimizationPlan:
        """최적화 계획 수립"""
        print(f"\n📋 최적화 계획 수립 중\n")

        opportunities = list(self.optimization_opportunities.values())

        if not opportunities:
            opportunities = self.find_opportunities()

        # 우선순위 기반 로드맵 생성
        implementation_roadmap = []
        total_savings = 0
        current_annual_cost = sum(r.current_cost_per_hour * 24 * 365 for r in self.resources.values())

        month = 1
        for opp in opportunities[:5]:  # 상위 5개 우선
            if opp.implementation_effort == "low":
                phase = f"Phase 1 (Month {month})"
                month += 1
            elif opp.implementation_effort == "medium":
                phase = f"Phase 2 (Month {month}-{month+1})"
                month += 2
            else:
                phase = f"Phase 3 (Month {month}-{month+2})"
                month += 3

            implementation_roadmap.append(f"{phase}: {opp.name} (+${opp.potential_savings:,.0f}/년)")
            total_savings += opp.potential_savings

        plan = OptimizationPlan(
            id=f"plan_{int(time.time())}",
            timestamp=time.time(),
            total_annual_cost=current_annual_cost,
            optimized_annual_cost=current_annual_cost - total_savings,
            total_potential_savings=total_savings,
            total_savings_percentage=total_savings / current_annual_cost * 100 if current_annual_cost > 0 else 0,
            opportunities=opportunities,
            implementation_roadmap=implementation_roadmap,
            estimated_implementation_time_days=sum([
                30 if o.implementation_effort == "low" else 60 if o.implementation_effort == "medium" else 90
                for o in opportunities[:5]
            ])
        )

        self.optimization_plans.append(plan)

        self._print_optimization_plan(plan)

        return plan

    def calculate_roi(self, opportunity: OptimizationOpportunity) -> Dict:
        """ROI 계산"""
        potential_savings = opportunity.potential_savings
        roi_months = opportunity.roi_months

        # 간단한 ROI 계산 (구현 비용 없다고 가정)
        roi_percentage = (potential_savings / 12 / 1000) * 100  # 대략적 계산
        roi_months_actual = roi_months

        return {
            'potential_savings': potential_savings,
            'roi_months': roi_months_actual,
            'roi_percentage': roi_percentage,
            'annual_saving': potential_savings,
            'monthly_saving': potential_savings / 12
        }

    def get_budget_status(self, budget_limit: float) -> Dict:
        """예산 상태 조회"""
        current_cost = sum(r.current_cost_per_hour * 24 * 365 for r in self.resources.values())
        spent_percentage = (current_cost / budget_limit * 100) if budget_limit > 0 else 0

        status = "good"
        if spent_percentage > 100:
            status = "critical"
        elif spent_percentage > 85:
            status = "warning"

        return {
            'budget_limit': budget_limit,
            'current_annual_cost': current_cost,
            'spent_percentage': spent_percentage,
            'status': status,
            'remaining_budget': budget_limit - current_cost
        }

    def _print_optimization_plan(self, plan: OptimizationPlan):
        """최적화 계획 출력"""
        print("\n" + "=" * 80)
        print("💰 비용 최적화 계획")
        print("=" * 80 + "\n")

        print(f"현재 연간 비용: ${plan.total_annual_cost:,.2f}")
        print(f"최적화 후 비용: ${plan.optimized_annual_cost:,.2f}")
        print(f"총 절감액: ${plan.total_potential_savings:,.2f} ({plan.total_savings_percentage:.1f}%)\n")

        print("📋 구현 로드맵:")
        for step in plan.implementation_roadmap:
            print(f"  • {step}")

        print(f"\n⏱️  예상 구현 기간: {plan.estimated_implementation_time_days}일\n")

        print("최적화 기회 상세:")
        print(f"{'우선순위':<5} {'기회':<30} {'절감액':<15} {'ROI':<12} {'위험':<10}")
        print("-" * 75)

        for i, opp in enumerate(plan.opportunities[:5], 1):
            roi = self.calculate_roi(opp)
            savings_str = f"${opp.potential_savings:,.0f}"
            roi_str = f"{roi['roi_months']:.0f}개월"

            print(f"{i:<5} {opp.name[:28]:<30} {savings_str:<15} {roi_str:<12} {opp.risk_level:<10}")

        print("\n" + "=" * 80 + "\n")

    def export_plan(self, plan: OptimizationPlan, filename: str = None) -> Optional[str]:
        """계획 내보내기"""
        if filename is None:
            filename = f"cost_optimization_plan_{int(time.time())}.json"

        plan_data = {
            'timestamp': datetime.fromtimestamp(plan.timestamp).isoformat(),
            'summary': {
                'current_annual_cost': plan.total_annual_cost,
                'optimized_annual_cost': plan.optimized_annual_cost,
                'total_potential_savings': plan.total_potential_savings,
                'savings_percentage': plan.total_savings_percentage,
                'implementation_time_days': plan.estimated_implementation_time_days
            },
            'opportunities': [
                {
                    'name': opp.name,
                    'type': opp.optimization_type,
                    'description': opp.description,
                    'potential_savings': opp.potential_savings,
                    'savings_percentage': opp.savings_percentage,
                    'implementation_effort': opp.implementation_effort,
                    'risk_level': opp.risk_level,
                    'confidence': opp.confidence,
                    'priority': opp.priority
                }
                for opp in plan.opportunities
            ],
            'implementation_roadmap': plan.implementation_roadmap
        }

        try:
            with open(filename, 'w') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)

            print(f"✅ 계획 내보내기 완료: {filename}")
            return filename

        except Exception as e:
            print(f"❌ 내보내기 실패: {e}")
            return None

    def get_optimization_stats(self) -> Dict:
        """최적화 통계"""
        total_opportunities = len(self.optimization_opportunities)
        total_potential_savings = sum(
            opp.potential_savings for opp in self.optimization_opportunities.values()
        )

        by_type = {}
        for opp in self.optimization_opportunities.values():
            opt_type = opp.optimization_type
            by_type[opt_type] = by_type.get(opt_type, 0) + 1

        return {
            'total_opportunities': total_opportunities,
            'total_potential_savings': total_potential_savings,
            'by_type': by_type,
            'plans_created': len(self.optimization_plans)
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_optimization_stats()

        print("\n" + "=" * 80)
        print("📊 비용 최적화 통계")
        print("=" * 80 + "\n")

        print(f"발견된 기회: {stats['total_opportunities']}개")
        print(f"총 절감 가능액: ${stats['total_potential_savings']:,.2f}")
        print(f"생성된 계획: {stats['plans_created']}개\n")

        print("기회 타입별:")
        for opt_type, count in stats['by_type'].items():
            print(f"  - {opt_type}: {count}개")

        print("\n" + "=" * 80 + "\n")


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    optimizer = CostOptimizer()

    # 샘플 리소스 추가
    optimizer.add_resource(ResourceMetrics(
        name="api-gateway",
        resource_type="compute",
        current_cost_per_hour=5.0,
        current_capacity=4,
        current_usage=1.2,
        usage_percentage=30,
        peak_usage=3.5,
        average_usage=1.2,
        lowest_usage=0.8
    ))

    optimizer.add_resource(ResourceMetrics(
        name="database-primary",
        resource_type="database",
        current_cost_per_hour=8.0,
        current_capacity=32,
        current_usage=28,
        usage_percentage=87.5,
        peak_usage=30,
        average_usage=27,
        lowest_usage=24
    ))

    optimizer.add_resource(ResourceMetrics(
        name="cache-layer",
        resource_type="storage",
        current_cost_per_hour=2.0,
        current_capacity=256,
        current_usage=60,
        usage_percentage=23,
        peak_usage=120,
        average_usage=60,
        lowest_usage=40
    ))

    if len(sys.argv) < 2:
        print("사용법: python cost_optimizer.py [command] [args]")
        print("  analyze        - 리소스 분석")
        print("  opportunities  - 최적화 기회 식별")
        print("  plan           - 최적화 계획 수립")
        print("  stats          - 통계 조회")
        return

    command = sys.argv[1]

    if command == "analyze":
        optimizer.analyze_resources()

    elif command == "opportunities":
        optimizer.find_opportunities()

    elif command == "plan":
        plan = optimizer.create_optimization_plan()
        optimizer.export_plan(plan)

    elif command == "stats":
        optimizer.print_stats()
