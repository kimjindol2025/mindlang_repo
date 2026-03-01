#!/usr/bin/env python3
"""
Feature Flag System - Feature toggles and A/B testing
Manages feature flags, rollouts, and A/B testing experiments
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time
import random


class FlagType(Enum):
    """Feature flag types"""
    BOOLEAN = "BOOLEAN"
    PERCENTAGE = "PERCENTAGE"
    TARGETING = "TARGETING"
    EXPERIMENT = "EXPERIMENT"


class FlagStatus(Enum):
    """Flag status"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DEPRECATED = "DEPRECATED"


class RolloutStrategy(Enum):
    """Rollout strategies"""
    ALL_USERS = "ALL_USERS"
    PERCENTAGE = "PERCENTAGE"
    USER_LIST = "USER_LIST"
    PERCENTAGE_WITH_SEED = "PERCENTAGE_WITH_SEED"


@dataclass
class FeatureFlag:
    """Feature flag"""
    flag_id: str
    flag_name: str
    flag_type: FlagType
    description: str
    status: FlagStatus = FlagStatus.DRAFT
    rollout_strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE
    rollout_percentage: float = 0.0
    target_users: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    enabled: bool = False


@dataclass
class Experiment:
    """A/B test experiment"""
    experiment_id: str
    experiment_name: str
    flag_id: str
    variants: Dict[str, float]  # variant_name -> percentage
    started_at: float
    ended_at: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlagEvaluation:
    """Flag evaluation result"""
    evaluation_id: str
    flag_id: str
    user_id: str
    enabled: bool
    variant: Optional[str] = None
    evaluated_at: float = field(default_factory=time.time)


class FeatureFlagSystem:
    """
    Feature Flag System

    Provides:
    - Feature flag management
    - Percentage-based rollouts
    - User targeting
    - A/B testing
    - Flag analytics
    - Gradual rollout
    """

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}
        self.experiments: Dict[str, Experiment] = {}
        self.evaluations: List[FlagEvaluation] = []
        self.flag_analytics: Dict[str, Dict] = {}

    def create_flag(self,
                   flag_name: str,
                   flag_type: FlagType,
                   description: str = "",
                   rollout_strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE) -> FeatureFlag:
        """Create feature flag"""
        flag_id = hashlib.md5(
            f"{flag_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        flag = FeatureFlag(
            flag_id=flag_id,
            flag_name=flag_name,
            flag_type=flag_type,
            description=description,
            rollout_strategy=rollout_strategy
        )

        self.flags[flag_id] = flag
        self.flag_analytics[flag_id] = {
            "evaluations": 0,
            "enabled_count": 0,
            "disabled_count": 0,
            "variants": {}
        }

        return flag

    def enable_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Enable feature flag"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        flag.enabled = True
        flag.status = FlagStatus.ACTIVE

        return flag

    def disable_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Disable feature flag"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        flag.enabled = False
        flag.status = FlagStatus.INACTIVE

        return flag

    def set_rollout_percentage(self, flag_id: str, percentage: float) -> Optional[FeatureFlag]:
        """Set rollout percentage"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        flag.rollout_percentage = max(0, min(100, percentage))
        return flag

    def add_target_users(self, flag_id: str, user_ids: List[str]) -> Optional[FeatureFlag]:
        """Add users to targeting list"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        flag.target_users.extend(user_ids)
        return flag

    def create_experiment(self,
                         experiment_name: str,
                         flag_id: str,
                         variants: Dict[str, float]) -> Optional[Experiment]:
        """Create A/B test experiment"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        experiment_id = hashlib.md5(
            f"{experiment_name}:{flag_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        experiment = Experiment(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            flag_id=flag_id,
            variants=variants,
            started_at=time.time()
        )

        self.experiments[experiment_id] = experiment
        return experiment

    def evaluate_flag(self,
                     flag_id: str,
                     user_id: str,
                     attributes: Dict[str, Any] = None) -> FlagEvaluation:
        """Evaluate flag for user"""
        flag = self.flags.get(flag_id)
        if not flag:
            return None

        evaluation_id = hashlib.md5(
            f"{flag_id}:{user_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        enabled = False
        variant = None

        if not flag.enabled:
            enabled = False
        elif flag.rollout_strategy == RolloutStrategy.ALL_USERS:
            enabled = True
        elif flag.rollout_strategy == RolloutStrategy.USER_LIST:
            enabled = user_id in flag.target_users
        elif flag.rollout_strategy == RolloutStrategy.PERCENTAGE:
            # Use consistent hashing for deterministic rollout
            user_hash = hash(f"{flag_id}:{user_id}") % 100
            enabled = user_hash < flag.rollout_percentage
        elif flag.rollout_strategy == RolloutStrategy.PERCENTAGE_WITH_SEED:
            enabled = random.random() * 100 < flag.rollout_percentage

        # Handle experiment variants
        active_experiment = next((e for e in self.experiments.values()
                                 if e.flag_id == flag_id and e.ended_at is None), None)

        if active_experiment and enabled:
            random_val = random.random()
            cumulative = 0
            for variant_name, percentage in active_experiment.variants.items():
                cumulative += percentage / 100
                if random_val <= cumulative:
                    variant = variant_name
                    break

        evaluation = FlagEvaluation(
            evaluation_id=evaluation_id,
            flag_id=flag_id,
            user_id=user_id,
            enabled=enabled,
            variant=variant
        )

        self.evaluations.append(evaluation)

        # Update analytics
        analytics = self.flag_analytics[flag_id]
        analytics["evaluations"] += 1
        if enabled:
            analytics["enabled_count"] += 1
        else:
            analytics["disabled_count"] += 1

        if variant:
            analytics["variants"][variant] = analytics["variants"].get(variant, 0) + 1

        return evaluation

    def end_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """End experiment and analyze results"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        experiment.ended_at = time.time()

        # Analyze results
        experiment_evaluations = [e for e in self.evaluations
                                 if e.flag_id == experiment.flag_id and
                                 e.variant is not None]

        variant_stats = {}
        for variant_name in experiment.variants.keys():
            variant_evals = [e for e in experiment_evaluations
                           if e.variant == variant_name]
            variant_stats[variant_name] = {
                "count": len(variant_evals),
                "percentage": (len(variant_evals) / len(experiment_evaluations) * 100)
                             if experiment_evaluations else 0
            }

        experiment.results = variant_stats
        return experiment

    def get_flag_stats(self) -> Dict:
        """Get flag statistics"""
        total_flags = len(self.flags)
        active_flags = sum(1 for f in self.flags.values() if f.status == FlagStatus.ACTIVE)
        total_evaluations = len(self.evaluations)

        by_type = {}
        for flag in self.flags.values():
            flag_type = flag.flag_type.value
            by_type[flag_type] = by_type.get(flag_type, 0) + 1

        active_experiments = sum(1 for e in self.experiments.values() if e.ended_at is None)

        return {
            "total_flags": total_flags,
            "active_flags": active_flags,
            "total_evaluations": total_evaluations,
            "by_type": by_type,
            "active_experiments": active_experiments,
            "completed_experiments": len(self.experiments) - active_experiments,
        }

    def generate_flag_report(self) -> str:
        """Generate flag report"""
        stats = self.get_flag_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              FEATURE FLAG SYSTEM REPORT                                    ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Flags: {stats['total_flags']}
├─ Active Flags: {stats['active_flags']}
├─ Total Evaluations: {stats['total_evaluations']}
├─ Active Experiments: {stats['active_experiments']}
└─ Completed Experiments: {stats['completed_experiments']}

📋 BY TYPE:
"""

        for flag_type, count in stats['by_type'].items():
            report += f"  {flag_type}: {count}\n"

        report += f"\n🚀 ACTIVE FLAGS:\n"
        for flag in [f for f in self.flags.values() if f.status == FlagStatus.ACTIVE][:5]:
            analytics = self.flag_analytics.get(flag.flag_id, {})
            report += f"  {flag.flag_name}\n"
            report += f"    Rollout: {flag.rollout_percentage:.1f}%\n"
            report += f"    Evaluations: {analytics.get('evaluations', 0)}\n"

        return report

    def export_flag_config(self) -> str:
        """Export flag configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_flag_stats(),
            "flags": [
                {
                    "id": f.flag_id,
                    "name": f.flag_name,
                    "type": f.flag_type.value,
                    "status": f.status.value,
                    "rollout_percentage": f.rollout_percentage,
                }
                for f in self.flags.values()
            ],
            "active_experiments": [
                {
                    "name": e.experiment_name,
                    "flag_id": e.flag_id,
                    "variants": e.variants,
                }
                for e in self.experiments.values() if e.ended_at is None
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🚀 Feature Flag System - Feature Toggles & A/B Testing")
    print("=" * 70)

    system = FeatureFlagSystem()

    # Create flags
    print("\n🚀 Creating feature flags...")
    flag1 = system.create_flag("new_dashboard", FlagType.PERCENTAGE, "New dashboard design")
    flag2 = system.create_flag("dark_mode", FlagType.BOOLEAN, "Dark mode support")
    flag3 = system.create_flag("payment_v2", FlagType.EXPERIMENT, "New payment system")
    print(f"✅ Created {len(system.flags)} flags")

    # Enable flags
    print("\n✅ Enabling flags...")
    system.enable_flag(flag1.flag_id)
    system.enable_flag(flag2.flag_id)
    system.enable_flag(flag3.flag_id)
    print("✅ Flags enabled")

    # Set rollout percentages
    print("\n📊 Setting rollout percentages...")
    system.set_rollout_percentage(flag1.flag_id, 25.0)
    system.set_rollout_percentage(flag2.flag_id, 50.0)
    system.set_rollout_percentage(flag3.flag_id, 100.0)
    print("✅ Rollout percentages set")

    # Create experiment
    print("\n🧪 Creating A/B test experiment...")
    experiment = system.create_experiment(
        "Payment V2 Test",
        flag3.flag_id,
        {"variant_a": 50, "variant_b": 50}
    )
    print(f"✅ Experiment created: {experiment.experiment_name}")

    # Evaluate flags for users
    print("\n🧪 Evaluating flags for users...")
    for i in range(100):
        user_id = f"user_{i}"
        system.evaluate_flag(flag1.flag_id, user_id)
        system.evaluate_flag(flag2.flag_id, user_id)
        system.evaluate_flag(flag3.flag_id, user_id)

    print(f"✅ Evaluated {len(system.evaluations)} flag evaluations")

    # End experiment
    print("\n📊 Analyzing experiment results...")
    if experiment:
        system.end_experiment(experiment.experiment_id)
        print(f"✅ Experiment results: {experiment.results}")

    # Generate report
    print(system.generate_flag_report())

    # Export
    print("\n📄 Exporting flag config...")
    export = system.export_flag_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Feature flag system ready")


if __name__ == "__main__":
    main()
