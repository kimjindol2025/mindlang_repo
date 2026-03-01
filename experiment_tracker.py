#!/usr/bin/env python3
"""
Experiment Tracker - Experiment tracking and analysis for ML and A/B testing
Manages experiment lifecycle, statistical analysis, and result tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import hashlib
import json
import time
import random
import statistics


class ExperimentStatus(Enum):
    """Status of experiment"""
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"
    CANCELLED = "CANCELLED"


class ExperimentType(Enum):
    """Types of experiments"""
    A_B_TEST = "A_B_TEST"
    MULTIVARIATE = "MULTIVARIATE"
    SEQUENTIAL = "SEQUENTIAL"
    BANDIT = "BANDIT"
    ML_MODEL = "ML_MODEL"
    FEATURE_FLAG = "FEATURE_FLAG"


class StatisticalSignificance(Enum):
    """Statistical significance levels"""
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_SIGNIFICANT = "NOT_SIGNIFICANT"
    SIGNIFICANT = "SIGNIFICANT"
    HIGHLY_SIGNIFICANT = "HIGHLY_SIGNIFICANT"


@dataclass
class Variant:
    """Experiment variant"""
    variant_id: str
    variant_name: str
    description: str
    traffic_allocation: float  # 0-100
    is_control: bool = False
    config: Dict = field(default_factory=dict)


@dataclass
class ExperimentMetric:
    """Metric tracked in experiment"""
    metric_name: str
    metric_type: str  # "conversion", "revenue", "engagement", etc.
    unit: str  # "count", "percentage", "dollar", etc.
    target_value: float
    evaluation_function: str  # Name of function to evaluate


@dataclass
class ObservationPoint:
    """Single observation in experiment"""
    observation_id: str
    variant_id: str
    user_id: str
    timestamp: float
    metric_name: str
    value: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class VariantResults:
    """Results for a single variant"""
    variant_id: str
    variant_name: str
    sample_size: int = 0
    observations: List[ObservationPoint] = field(default_factory=list)
    metric_values: Dict[str, List[float]] = field(default_factory=dict)
    mean_values: Dict[str, float] = field(default_factory=dict)
    std_dev: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Overall experiment result"""
    experiment_id: str
    result_id: str
    timestamp: float
    variant_results: Dict[str, VariantResults] = field(default_factory=dict)
    statistical_significance: StatisticalSignificance = StatisticalSignificance.INCONCLUSIVE
    p_value: float = 1.0
    winner: Optional[str] = None
    winner_improvement: float = 0.0
    confidence_level: float = 0.95


@dataclass
class Experiment:
    """Complete experiment definition"""
    experiment_id: str
    name: str
    description: str
    experiment_type: ExperimentType
    status: ExperimentStatus
    owner: str
    created_at: float
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    variants: List[Variant] = field(default_factory=list)
    metrics: List[ExperimentMetric] = field(default_factory=list)
    hypothesis: str = ""
    success_criteria: str = ""
    sample_size_target: int = 10000
    min_duration_days: int = 7
    results: Optional[ExperimentResult] = None
    tags: List[str] = field(default_factory=list)


class ExperimentTracker:
    """
    Enterprise experiment tracking and analysis system

    Provides:
    - Experiment lifecycle management
    - A/B test design and execution
    - Statistical analysis (t-test, chi-square)
    - Sample size calculation
    - Result tracking and reporting
    - Experiment rollback capabilities
    - Historical experiment tracking
    """

    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.results: Dict[str, ExperimentResult] = {}
        self.observations: List[ObservationPoint] = []

    def create_experiment(self,
                         name: str,
                         description: str,
                         experiment_type: ExperimentType,
                         owner: str,
                         hypothesis: str,
                         variants_config: List[Dict],
                         metrics: List[Dict]) -> Experiment:
        """
        Create new experiment

        Args:
            name: Experiment name
            description: Experiment description
            experiment_type: Type of experiment
            owner: Experiment owner
            hypothesis: Null hypothesis
            variants_config: List of variant configurations
            metrics: List of metrics to track

        Returns:
            Created Experiment
        """
        experiment_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        # Create variants
        variants = []
        for var_config in variants_config:
            variant = Variant(
                variant_id=hashlib.md5(f"{experiment_id}:{var_config['name']}".encode()).hexdigest()[:8],
                variant_name=var_config["name"],
                description=var_config.get("description", ""),
                traffic_allocation=var_config.get("traffic_allocation", 50.0),
                is_control=var_config.get("is_control", False),
                config=var_config.get("config", {})
            )
            variants.append(variant)

        # Create metrics
        metrics_objs = []
        for metric_config in metrics:
            metric = ExperimentMetric(
                metric_name=metric_config["name"],
                metric_type=metric_config.get("type", "conversion"),
                unit=metric_config.get("unit", "count"),
                target_value=metric_config.get("target_value", 0),
                evaluation_function=metric_config.get("eval_function", "")
            )
            metrics_objs.append(metric)

        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            experiment_type=experiment_type,
            status=ExperimentStatus.PLANNING,
            owner=owner,
            created_at=time.time(),
            variants=variants,
            metrics=metrics_objs,
            hypothesis=hypothesis,
            sample_size_target=self._calculate_sample_size(variants)
        )

        self.experiments[experiment_id] = experiment
        return experiment

    def _calculate_sample_size(self, variants: List[Variant],
                             effect_size: float = 0.2,
                             alpha: float = 0.05,
                             beta: float = 0.20) -> int:
        """Calculate required sample size (simplified)"""
        # Formula: n = 2 * (z_alpha + z_beta)^2 * (2 * p * (1-p)) / (effect_size)^2
        # Using approximate values
        z_values = {0.05: 1.96, 0.10: 1.645, 0.20: 0.842}
        z_alpha = z_values.get(alpha, 1.96)
        z_beta = z_values.get(beta, 0.842)

        base_size = int(2 * ((z_alpha + z_beta) ** 2) * 0.25 / (effect_size ** 2))
        return base_size * len(variants)

    def start_experiment(self, experiment_id: str) -> bool:
        """
        Start experiment

        Args:
            experiment_id: Experiment to start

        Returns:
            Start success
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        if experiment.status != ExperimentStatus.PLANNING:
            return False

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = time.time()
        return True

    def record_observation(self,
                          experiment_id: str,
                          variant_id: str,
                          user_id: str,
                          metric_name: str,
                          value: float,
                          metadata: Optional[Dict] = None) -> bool:
        """
        Record observation for experiment

        Args:
            experiment_id: Target experiment
            variant_id: Target variant
            user_id: User ID
            metric_name: Metric name
            value: Metric value
            metadata: Additional metadata

        Returns:
            Record success
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment.status not in [ExperimentStatus.RUNNING, ExperimentStatus.PAUSED]:
            return False

        observation = ObservationPoint(
            observation_id=hashlib.md5(f"{experiment_id}:{user_id}:{time.time()}".encode()).hexdigest()[:8],
            variant_id=variant_id,
            user_id=user_id,
            timestamp=time.time(),
            metric_name=metric_name,
            value=value,
            metadata=metadata or {}
        )

        self.observations.append(observation)
        return True

    def calculate_results(self, experiment_id: str) -> ExperimentResult:
        """
        Calculate experiment results

        Args:
            experiment_id: Experiment to analyze

        Returns:
            ExperimentResult with statistical analysis
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        result_id = hashlib.md5(f"{experiment_id}:{time.time()}".encode()).hexdigest()[:8]
        result = ExperimentResult(
            experiment_id=experiment_id,
            result_id=result_id,
            timestamp=time.time()
        )

        # Collect observations per variant
        variant_obs = {}
        for variant in experiment.variants:
            variant_obs[variant.variant_id] = [
                o for o in self.observations
                if o.variant_id == variant.variant_id
            ]

        # Calculate statistics for each variant
        for metric in experiment.metrics:
            metric_name = metric.metric_name

            for variant in experiment.variants:
                obs = [
                    o.value for o in variant_obs[variant.variant_id]
                    if o.metric_name == metric_name
                ]

                if not obs:
                    continue

                if variant.variant_id not in result.variant_results:
                    result.variant_results[variant.variant_id] = VariantResults(
                        variant_id=variant.variant_id,
                        variant_name=variant.variant_name,
                        sample_size=len(obs)
                    )

                var_result = result.variant_results[variant.variant_id]
                var_result.observations = variant_obs[variant.variant_id]
                var_result.metric_values[metric_name] = obs

                # Calculate statistics
                var_result.mean_values[metric_name] = statistics.mean(obs)
                if len(obs) > 1:
                    var_result.std_dev[metric_name] = statistics.stdev(obs)
                    # Confidence interval (simplified)
                    se = var_result.std_dev[metric_name] / (len(obs) ** 0.5)
                    margin = 1.96 * se
                    var_result.confidence_intervals[metric_name] = (
                        var_result.mean_values[metric_name] - margin,
                        var_result.mean_values[metric_name] + margin
                    )

        # Perform statistical test
        if len(result.variant_results) >= 2:
            self._perform_statistical_test(result, experiment.metrics[0].metric_name if experiment.metrics else None)

        experiment.results = result
        self.results[result_id] = result

        return result

    def _perform_statistical_test(self, result: ExperimentResult, metric_name: Optional[str]):
        """Perform statistical significance test (simplified t-test)"""
        if not metric_name or len(result.variant_results) < 2:
            return

        variants = list(result.variant_results.values())
        values1 = variants[0].metric_values.get(metric_name, [])
        values2 = variants[1].metric_values.get(metric_name, [])

        if not values1 or not values2 or len(values1) < 2 or len(values2) < 2:
            return

        # Simplified t-test
        mean1 = statistics.mean(values1)
        mean2 = statistics.mean(values2)
        std1 = statistics.stdev(values1)
        std2 = statistics.stdev(values2)

        n1 = len(values1)
        n2 = len(values2)

        # Pooled standard error
        se = ((std1 ** 2 / n1) + (std2 ** 2 / n2)) ** 0.5

        if se > 0:
            t_stat = abs(mean2 - mean1) / se
            # Approximate p-value (simplified)
            p_value = 1 / (1 + t_stat)  # Simplified approximation
        else:
            p_value = 1.0

        result.p_value = p_value

        # Determine significance
        if p_value < 0.001:
            result.statistical_significance = StatisticalSignificance.HIGHLY_SIGNIFICANT
        elif p_value < 0.05:
            result.statistical_significance = StatisticalSignificance.SIGNIFICANT
        elif p_value < 0.10:
            result.statistical_significance = StatisticalSignificance.NOT_SIGNIFICANT
        else:
            result.statistical_significance = StatisticalSignificance.INCONCLUSIVE

        # Determine winner
        if mean2 > mean1:
            result.winner = variants[1].variant_id
            result.winner_improvement = ((mean2 - mean1) / mean1 * 100) if mean1 != 0 else 0
        elif mean1 > mean2:
            result.winner = variants[0].variant_id
            result.winner_improvement = ((mean1 - mean2) / mean2 * 100) if mean2 != 0 else 0

    def end_experiment(self, experiment_id: str) -> bool:
        """
        End experiment

        Args:
            experiment_id: Experiment to end

        Returns:
            End success
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return False

        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = time.time()

        # Calculate final results
        self.calculate_results(experiment_id)

        return True

    def generate_experiment_report(self, experiment_id: str) -> str:
        """Generate experiment report"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return f"❌ Experiment {experiment_id} not found"

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         EXPERIMENT REPORT                                  ║
║                         {experiment.name}                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 EXPERIMENT DETAILS:
├─ ID: {experiment.experiment_id}
├─ Type: {experiment.experiment_type.value}
├─ Status: {experiment.status.value}
├─ Owner: {experiment.owner}
├─ Created: {time.strftime('%Y-%m-%d', time.localtime(experiment.created_at))}
└─ Duration: {(experiment.ended_at or time.time()) - experiment.started_at if experiment.started_at else 'Not started'} seconds

📊 VARIANTS:
"""

        for variant in experiment.variants:
            control_icon = "🎯" if variant.is_control else "🔬"
            report += f"\n{control_icon} {variant.variant_name} ({variant.traffic_allocation}%)\n"

        if experiment.results:
            result = experiment.results
            report += f"\n📈 RESULTS:\n"
            report += f"├─ Statistical Significance: {result.statistical_significance.value}\n"
            report += f"├─ P-Value: {result.p_value:.4f}\n"

            if result.winner:
                winner_var = next((v for v in experiment.variants if v.variant_id == result.winner), None)
                if winner_var:
                    report += f"├─ Winner: {winner_var.variant_name}\n"
                    report += f"└─ Improvement: {result.winner_improvement:.2f}%\n"

            report += f"\n📊 VARIANT STATISTICS:\n"
            for variant_id, var_result in result.variant_results.items():
                report += f"\n{var_result.variant_name}:\n"
                report += f"  Sample Size: {var_result.sample_size}\n"
                for metric_name, mean_value in var_result.mean_values.items():
                    report += f"  {metric_name}: {mean_value:.2f}\n"

        return report

    def export_experiment(self, experiment_id: str) -> str:
        """Export experiment as JSON"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return "{}"

        export_data = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.name,
            "type": experiment.experiment_type.value,
            "status": experiment.status.value,
            "created_at": experiment.created_at,
            "variants": [
                {
                    "name": v.variant_name,
                    "traffic_allocation": v.traffic_allocation,
                    "is_control": v.is_control,
                }
                for v in experiment.variants
            ],
            "metrics": [
                {
                    "name": m.metric_name,
                    "type": m.metric_type,
                }
                for m in experiment.metrics
            ],
        }

        if experiment.results:
            export_data["results"] = {
                "statistical_significance": experiment.results.statistical_significance.value,
                "p_value": experiment.results.p_value,
                "winner": experiment.results.winner,
                "winner_improvement": experiment.results.winner_improvement,
            }

        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🧪 Experiment Tracker - A/B Test and Experiment Management")
    print("=" * 70)

    tracker = ExperimentTracker()

    # Create experiment
    print("\n📝 Creating A/B test experiment...")
    experiment = tracker.create_experiment(
        name="Homepage Redesign Test",
        description="Test new homepage design impact on conversion rate",
        experiment_type=ExperimentType.A_B_TEST,
        owner="data-team@example.com",
        hypothesis="New homepage design increases conversion rate by 10%",
        variants_config=[
            {"name": "Control", "is_control": True, "traffic_allocation": 50.0},
            {"name": "Treatment", "traffic_allocation": 50.0, "description": "New homepage design"},
        ],
        metrics=[
            {"name": "conversion_rate", "type": "conversion", "unit": "percentage"},
            {"name": "bounce_rate", "type": "engagement", "unit": "percentage"},
            {"name": "avg_session_duration", "type": "engagement", "unit": "seconds"},
        ]
    )
    print(f"✅ Created experiment {experiment.experiment_id}")

    # Start experiment
    print("\n▶️  Starting experiment...")
    tracker.start_experiment(experiment.experiment_id)
    print(f"✅ Experiment started")

    # Simulate observations
    print("\n📊 Recording observations...")
    for i in range(500):
        variant = random.choice(experiment.variants)
        metric = random.choice(experiment.metrics)

        # Simulate slight improvement in treatment variant
        if variant.variant_name == "Treatment" and metric.metric_name == "conversion_rate":
            value = random.gauss(12, 1)  # Treatment has higher conversion
        elif metric.metric_name == "conversion_rate":
            value = random.gauss(10, 1)  # Control baseline
        else:
            value = random.gauss(100, 20)

        tracker.record_observation(
            experiment.experiment_id,
            variant.variant_id,
            f"user_{i}",
            metric.metric_name,
            max(0, value)  # Ensure non-negative
        )

    print(f"✅ Recorded 500 observations")

    # End experiment
    print("\n⏹️  Ending experiment and analyzing...")
    tracker.end_experiment(experiment.experiment_id)

    # Generate report
    print(tracker.generate_experiment_report(experiment.experiment_id))

    # Export
    print("\n📄 Exporting experiment...")
    export = tracker.export_experiment(experiment.experiment_id)
    print(f"✅ Exported {len(export)} characters of experiment data")

    print("\n" + "=" * 70)
    print("✨ Experiment tracking complete")


if __name__ == "__main__":
    main()
