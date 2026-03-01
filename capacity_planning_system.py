#!/usr/bin/env python3
"""
Capacity Planning System - Infrastructure scaling and resource forecasting
Predicts future capacity needs, optimizes resource allocation, and recommends scaling strategies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional
import hashlib
import json
import time
import random
import statistics


class MetricType(Enum):
    """Types of capacity metrics"""
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"
    DATABASE_CONNECTIONS = "DATABASE_CONNECTIONS"
    QUEUE_DEPTH = "QUEUE_DEPTH"
    RPS = "RPS"
    P95_LATENCY = "P95_LATENCY"


class ScalingStrategy(Enum):
    """Scaling strategies"""
    VERTICAL = "VERTICAL"  # Add more resources to existing servers
    HORIZONTAL = "HORIZONTAL"  # Add more servers
    AUTO_SCALING = "AUTO_SCALING"  # Dynamic scaling based on load
    HYBRID = "HYBRID"  # Combination of vertical and horizontal


class ForecastPeriod(Enum):
    """Forecast time periods"""
    ONE_WEEK = "ONE_WEEK"
    TWO_WEEKS = "TWO_WEEKS"
    ONE_MONTH = "ONE_MONTH"
    THREE_MONTHS = "THREE_MONTHS"
    SIX_MONTHS = "SIX_MONTHS"
    ONE_YEAR = "ONE_YEAR"


@dataclass
class TimeSeriesPoint:
    """A single data point in time series"""
    timestamp: float
    value: float
    metric_type: MetricType


@dataclass
class CapacityMetric:
    """Current capacity metric"""
    metric_type: MetricType
    current_value: float
    capacity_threshold: float
    utilization_percent: float
    trend: str  # "INCREASING", "STABLE", "DECREASING"


@dataclass
class GrowthProjection:
    """Growth projection for a metric"""
    metric_type: MetricType
    period: ForecastPeriod
    current_value: float
    projected_value: float
    growth_rate_percent: float
    confidence_interval: Tuple[float, float]  # (low, high) estimates
    date_to_capacity: Optional[str] = None  # When capacity will be exceeded


@dataclass
class ScalingRecommendation:
    """Recommendation for capacity scaling"""
    metric_type: MetricType
    current_utilization: float
    recommended_strategy: ScalingStrategy
    estimated_cost_increase: float
    implementation_complexity: str  # "LOW", "MEDIUM", "HIGH"
    timeline: str  # "IMMEDIATE", "WITHIN_1_WEEK", "WITHIN_1_MONTH"
    description: str
    expected_impact: Dict[str, float]  # metric -> improvement


@dataclass
class CapacityPlan:
    """Overall capacity plan"""
    plan_id: str
    timestamp: float
    current_metrics: Dict[MetricType, CapacityMetric] = field(default_factory=dict)
    projections: List[GrowthProjection] = field(default_factory=list)
    recommendations: List[ScalingRecommendation] = field(default_factory=list)
    estimated_budget_increase: float = 0.0
    risk_assessment: str = ""
    optimization_opportunities: List[str] = field(default_factory=list)


class CapacityPlanner:
    """
    Comprehensive capacity planning system

    Performs:
    - Historical trend analysis
    - Growth projection with confidence intervals
    - Bottleneck identification
    - Scaling recommendations
    - Cost estimation
    - Risk assessment
    - Optimization suggestions
    """

    def __init__(self):
        self.capacity_plans: Dict[str, CapacityPlan] = {}
        self.historical_data: Dict[MetricType, List[TimeSeriesPoint]] = {
            metric: [] for metric in MetricType
        }
        self.resource_costs = {
            "cpu_core": 0.12,  # per hour
            "memory_gb": 0.015,
            "disk_gb": 0.0001,
            "network_gb": 0.12,
        }

    def add_historical_data(self, metrics: Dict[MetricType, List[Tuple[float, float]]]):
        """
        Add historical time series data

        Args:
            metrics: Dict mapping MetricType to list of (timestamp, value) tuples
        """
        for metric_type, data_points in metrics.items():
            for timestamp, value in data_points:
                point = TimeSeriesPoint(
                    timestamp=timestamp,
                    value=value,
                    metric_type=metric_type
                )
                self.historical_data[metric_type].append(point)

    def create_capacity_plan(self,
                            current_metrics: Dict[MetricType, Tuple[float, float]],
                            thresholds: Dict[MetricType, float]) -> CapacityPlan:
        """
        Create capacity plan with recommendations

        Args:
            current_metrics: Dict of metric type to (current_value, capacity_max)
            thresholds: Dict of metric type to utilization threshold (e.g., 0.8 = 80%)

        Returns:
            CapacityPlan with projections and recommendations
        """
        plan_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]
        plan = CapacityPlan(plan_id=plan_id, timestamp=time.time())

        # Analyze current metrics
        for metric_type, (current_val, capacity_max) in current_metrics.items():
            utilization = (current_val / capacity_max) * 100
            trend = self._analyze_trend(metric_type)

            metric = CapacityMetric(
                metric_type=metric_type,
                current_value=current_val,
                capacity_threshold=capacity_max,
                utilization_percent=utilization,
                trend=trend
            )
            plan.current_metrics[metric_type] = metric

            # Generate projections
            projection = self._project_growth(
                metric_type,
                current_val,
                capacity_max,
                thresholds.get(metric_type, 0.8)
            )
            plan.projections.append(projection)

        # Generate scaling recommendations
        plan.recommendations = self._generate_recommendations(plan)

        # Calculate budget impact
        plan.estimated_budget_increase = self._estimate_cost_increase(plan)

        # Risk assessment
        plan.risk_assessment = self._assess_risk(plan)

        # Optimization opportunities
        plan.optimization_opportunities = self._identify_optimizations(plan)

        self.capacity_plans[plan_id] = plan
        return plan

    def _analyze_trend(self, metric_type: MetricType) -> str:
        """Analyze historical trend"""
        data = self.historical_data.get(metric_type, [])
        if len(data) < 2:
            return "STABLE"

        # Look at recent trend
        recent = sorted(data[-10:], key=lambda x: x.timestamp)
        if len(recent) < 2:
            return "STABLE"

        values = [p.value for p in recent]
        start_val = values[0]
        end_val = values[-1]

        change_percent = ((end_val - start_val) / start_val * 100) if start_val > 0 else 0

        if change_percent > 10:
            return "INCREASING"
        elif change_percent < -10:
            return "DECREASING"
        else:
            return "STABLE"

    def _project_growth(self,
                       metric_type: MetricType,
                       current_value: float,
                       capacity_max: float,
                       threshold: float) -> GrowthProjection:
        """Project future growth"""
        # Calculate growth rate based on trend
        data = self.historical_data.get(metric_type, [])

        if len(data) >= 4:
            recent = sorted(data[-4:], key=lambda x: x.timestamp)
            recent_values = [p.value for p in recent]
            growth_rate = ((recent_values[-1] - recent_values[0]) / recent_values[0] / 4 * 100) if recent_values[0] > 0 else 5
        else:
            growth_rate = random.uniform(3, 15)  # Default growth rate

        # Project to 30 days
        days = 30
        projected_value = current_value * (1 + (growth_rate / 100) * days / 30)

        # Calculate when threshold will be reached
        threshold_value = capacity_max * threshold
        if current_value < threshold_value and growth_rate > 0:
            days_to_threshold = (threshold_value - current_value) / (current_value * (growth_rate / 100) / 30)
            date_to_capacity = f"~{int(days_to_threshold)} days"
        else:
            date_to_capacity = None

        # Confidence interval (±20%)
        low = projected_value * 0.8
        high = projected_value * 1.2

        return GrowthProjection(
            metric_type=metric_type,
            period=ForecastPeriod.ONE_MONTH,
            current_value=current_value,
            projected_value=projected_value,
            growth_rate_percent=growth_rate,
            confidence_interval=(low, high),
            date_to_capacity=date_to_capacity
        )

    def _generate_recommendations(self, plan: CapacityPlan) -> List[ScalingRecommendation]:
        """Generate scaling recommendations"""
        recommendations = []

        for projection in plan.projections:
            metric = plan.current_metrics.get(projection.metric_type)
            if not metric:
                continue

            utilization = metric.utilization_percent

            # Check if action is needed
            if utilization > 80 or projection.growth_rate_percent > 10:
                recommendation = ScalingRecommendation(
                    metric_type=projection.metric_type,
                    current_utilization=utilization,
                    recommended_strategy=self._choose_strategy(projection.metric_type, utilization),
                    estimated_cost_increase=self._estimate_metric_cost(projection.metric_type, projection.projected_value),
                    implementation_complexity=self._assess_complexity(projection.metric_type),
                    timeline=self._assess_timeline(utilization),
                    description=self._generate_description(projection, utilization),
                    expected_impact=self._calculate_impact(projection.metric_type, projection.projected_value)
                )
                recommendations.append(recommendation)

        return recommendations

    def _choose_strategy(self, metric_type: MetricType, utilization: float) -> ScalingStrategy:
        """Choose appropriate scaling strategy"""
        if metric_type in [MetricType.CPU, MetricType.MEMORY]:
            if utilization > 90:
                return ScalingStrategy.HORIZONTAL
            else:
                return ScalingStrategy.VERTICAL
        elif metric_type == MetricType.DATABASE_CONNECTIONS:
            return ScalingStrategy.HORIZONTAL
        elif metric_type == MetricType.RPS:
            return ScalingStrategy.AUTO_SCALING
        else:
            return ScalingStrategy.HYBRID

    def _assess_complexity(self, metric_type: MetricType) -> str:
        """Assess implementation complexity"""
        complexity_map = {
            MetricType.CPU: "MEDIUM",
            MetricType.MEMORY: "MEDIUM",
            MetricType.DISK: "HIGH",
            MetricType.NETWORK: "HIGH",
            MetricType.DATABASE_CONNECTIONS: "HIGH",
            MetricType.QUEUE_DEPTH: "MEDIUM",
            MetricType.RPS: "LOW",
            MetricType.P95_LATENCY: "MEDIUM",
        }
        return complexity_map.get(metric_type, "MEDIUM")

    def _assess_timeline(self, utilization: float) -> str:
        """Assess urgency of action"""
        if utilization > 90:
            return "IMMEDIATE"
        elif utilization > 75:
            return "WITHIN_1_WEEK"
        else:
            return "WITHIN_1_MONTH"

    def _generate_description(self, projection: GrowthProjection, utilization: float) -> str:
        """Generate human-readable description"""
        return f"{projection.metric_type.value} at {utilization:.0f}% utilization, expected to reach {projection.projected_value:.0f} in 30 days (growth rate: {projection.growth_rate_percent:.1f}%)"

    def _calculate_impact(self, metric_type: MetricType, new_value: float) -> Dict[str, float]:
        """Calculate expected impact of scaling"""
        return {
            "utilization_reduction": 0.3,  # 30% reduction
            "performance_improvement": 0.25,  # 25% improvement
            "reliability_improvement": 0.15,  # 15% improvement
        }

    def _estimate_metric_cost(self, metric_type: MetricType, new_value: float) -> float:
        """Estimate cost for scaling a metric"""
        cost_per_unit = {
            MetricType.CPU: self.resource_costs["cpu_core"],
            MetricType.MEMORY: self.resource_costs["memory_gb"],
            MetricType.DISK: self.resource_costs["disk_gb"],
            MetricType.NETWORK: self.resource_costs["network_gb"],
        }

        monthly_multiplier = 730  # hours per month

        cost = cost_per_unit.get(metric_type, 0.1) * new_value * monthly_multiplier
        return cost * 0.5  # Approximate cost increase

    def _estimate_cost_increase(self, plan: CapacityPlan) -> float:
        """Estimate total monthly cost increase"""
        total_cost = 0.0
        for recommendation in plan.recommendations:
            total_cost += recommendation.estimated_cost_increase
        return total_cost

    def _assess_risk(self, plan: CapacityPlan) -> str:
        """Assess capacity risk"""
        high_utilization = sum(1 for m in plan.current_metrics.values() if m.utilization_percent > 85)
        critical_metrics = sum(1 for m in plan.current_metrics.values() if m.utilization_percent > 95)

        if critical_metrics > 0:
            return "🔴 CRITICAL - Immediate action required to prevent service degradation"
        elif high_utilization > 2:
            return "🟠 HIGH - Scaling should be planned within 1 week"
        elif high_utilization > 0:
            return "🟡 MEDIUM - Monitor closely and plan scaling within 1 month"
        else:
            return "🟢 LOW - Capacity is healthy"

    def _identify_optimizations(self, plan: CapacityPlan) -> List[str]:
        """Identify optimization opportunities"""
        suggestions = []

        # Analyze metrics
        cpu_metric = plan.current_metrics.get(MetricType.CPU)
        mem_metric = plan.current_metrics.get(MetricType.MEMORY)

        if cpu_metric and cpu_metric.utilization_percent > 70:
            suggestions.append("🔄 Enable auto-scaling to handle traffic spikes dynamically")

        if mem_metric and mem_metric.utilization_percent > 80:
            suggestions.append("💾 Review memory allocation strategy, consider caching optimization")

        if len(plan.recommendations) > 3:
            suggestions.append("📊 High number of scaling needs - consider architectural review")

        suggestions.append("🔍 Implement detailed monitoring for real-time capacity tracking")

        return suggestions

    def generate_capacity_report(self, plan_id: str) -> str:
        """Generate detailed capacity report"""
        plan = self.capacity_plans.get(plan_id)
        if not plan:
            return f"❌ Plan {plan_id} not found"

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      CAPACITY PLANNING REPORT                              ║
║                      Plan ID: {plan_id}                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

{plan.risk_assessment}

📊 CURRENT UTILIZATION:
"""

        for metric_type, metric in plan.current_metrics.items():
            emoji = "🔴" if metric.utilization_percent > 90 else "🟠" if metric.utilization_percent > 75 else "🟢"
            bar_length = int(metric.utilization_percent / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            report += f"{emoji} {metric_type.value:20} {bar} {metric.utilization_percent:5.1f}%\n"

        report += f"\n📈 30-DAY PROJECTIONS:\n"
        for projection in plan.projections:
            report += f"  • {projection.metric_type.value}: {projection.current_value:.0f} → {projection.projected_value:.0f} "
            report += f"({projection.growth_rate_percent:+.1f}%)\n"
            if projection.date_to_capacity:
                report += f"    ⚠️  Will exceed threshold in {projection.date_to_capacity}\n"

        report += f"\n🔧 SCALING RECOMMENDATIONS:\n"
        for rec in plan.recommendations[:5]:
            report += f"  • {rec.metric_type.value}\n"
            report += f"    Strategy: {rec.recommended_strategy.value}\n"
            report += f"    Timeline: {rec.timeline}\n"
            report += f"    Est. Cost Increase: ${rec.estimated_cost_increase:.2f}/month\n"

        report += f"\n💰 ESTIMATED BUDGET IMPACT:\n"
        report += f"  Total Monthly Increase: ${plan.estimated_budget_increase:.2f}\n"
        report += f"  Annual Impact: ${plan.estimated_budget_increase * 12:.2f}\n"

        report += f"\n💡 OPTIMIZATION OPPORTUNITIES:\n"
        for suggestion in plan.optimization_opportunities:
            report += f"  {suggestion}\n"

        return report

    def export_plan(self, plan_id: str) -> str:
        """Export plan to JSON"""
        plan = self.capacity_plans.get(plan_id)
        if not plan:
            return "{}"

        export_data = {
            "plan_id": plan.plan_id,
            "timestamp": plan.timestamp,
            "current_metrics": {
                metric_type.value: {
                    "current_value": metric.current_value,
                    "capacity_threshold": metric.capacity_threshold,
                    "utilization_percent": metric.utilization_percent,
                    "trend": metric.trend,
                }
                for metric_type, metric in plan.current_metrics.items()
            },
            "projections": [
                {
                    "metric": p.metric_type.value,
                    "current": p.current_value,
                    "projected": p.projected_value,
                    "growth_rate": p.growth_rate_percent,
                    "days_to_capacity": p.date_to_capacity,
                }
                for p in plan.projections
            ],
            "recommendations": [
                {
                    "metric": r.metric_type.value,
                    "strategy": r.recommended_strategy.value,
                    "complexity": r.implementation_complexity,
                    "timeline": r.timeline,
                    "cost_increase": r.estimated_cost_increase,
                }
                for r in plan.recommendations
            ],
            "estimated_budget_increase": plan.estimated_budget_increase,
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 Capacity Planning System - Infrastructure Scaling")
    print("=" * 70)

    planner = CapacityPlanner()

    # Add historical data (simulated)
    historical_metrics = {
        MetricType.CPU: [(time.time() - 86400 * i, 40 + i * 1.5 + random.uniform(-5, 5)) for i in range(30)],
        MetricType.MEMORY: [(time.time() - 86400 * i, 60 + i * 1.2 + random.uniform(-5, 5)) for i in range(30)],
        MetricType.DATABASE_CONNECTIONS: [(time.time() - 86400 * i, 100 + i * 2 + random.uniform(-10, 10)) for i in range(30)],
        MetricType.RPS: [(time.time() - 86400 * i, 1000 + i * 50 + random.uniform(-100, 100)) for i in range(30)],
    }
    planner.add_historical_data(historical_metrics)

    print("\n📈 Creating capacity plan...")
    plan = planner.create_capacity_plan(
        current_metrics={
            MetricType.CPU: (75, 100),
            MetricType.MEMORY: (82, 128),
            MetricType.DATABASE_CONNECTIONS: (145, 200),
            MetricType.RPS: (1500, 2000),
            MetricType.P95_LATENCY: (250, 500),
        },
        thresholds={
            MetricType.CPU: 0.8,
            MetricType.MEMORY: 0.85,
            MetricType.DATABASE_CONNECTIONS: 0.75,
            MetricType.RPS: 0.8,
        }
    )

    # Print report
    print(planner.generate_capacity_report(plan.plan_id))

    # Export
    print("\n📄 Exporting capacity plan...")
    json_export = planner.export_plan(plan.plan_id)
    print(f"✅ Exported {len(json_export)} characters of plan data")

    print("\n" + "=" * 70)
    print("✨ Capacity planning complete")


if __name__ == "__main__":
    main()
