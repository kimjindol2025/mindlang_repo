#!/usr/bin/env python3
"""
Chaos Engineering Manager - Controlled failure injection and resilience testing
Manages chaos experiments, failure scenarios, and system resilience validation
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class FailureType(Enum):
    """Failure types"""
    LATENCY = "LATENCY"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"
    NETWORK_PARTITION = "NETWORK_PARTITION"


class ExperimentStatus(Enum):
    """Experiment status"""
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class ChaosExperiment:
    """Chaos experiment"""
    experiment_id: str
    experiment_name: str
    failure_type: FailureType
    target_service: str
    duration_seconds: int
    failure_rate: float  # 0-100
    created_at: float
    status: ExperimentStatus = ExperimentStatus.PLANNED


@dataclass
class ExperimentResult:
    """Experiment result"""
    result_id: str
    experiment_id: str
    started_at: float
    completed_at: Optional[float]
    error_rate: float
    latency_increase: float
    system_recovered: bool
    observations: List[str] = field(default_factory=list)


class ChaosEngineeringManager:
    """
    Chaos Engineering Manager

    Provides:
    - Controlled failure injection
    - Experiment scheduling
    - System resilience testing
    - Failure scenario simulation
    - Recovery validation
    - Resilience metrics tracking
    """

    def __init__(self):
        self.experiments: Dict[str, ChaosExperiment] = {}
        self.results: List[ExperimentResult] = []
        self.failure_injections: List[Dict] = []
        self.resilience_scores: Dict[str, float] = {}

    def create_experiment(self,
                         experiment_name: str,
                         failure_type: FailureType,
                         target_service: str,
                         duration_seconds: int,
                         failure_rate: float) -> ChaosExperiment:
        """Create chaos experiment"""
        experiment_id = hashlib.md5(
            f"{experiment_name}:{target_service}:{time.time()}".encode()
        ).hexdigest()[:8]

        experiment = ChaosExperiment(
            experiment_id=experiment_id,
            experiment_name=experiment_name,
            failure_type=failure_type,
            target_service=target_service,
            duration_seconds=duration_seconds,
            failure_rate=failure_rate,
            created_at=time.time()
        )

        self.experiments[experiment_id] = experiment
        return experiment

    def run_experiment(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Run chaos experiment"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return None

        result_id = hashlib.md5(
            f"{experiment_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        result = ExperimentResult(
            result_id=result_id,
            experiment_id=experiment_id,
            started_at=time.time(),
            error_rate=experiment.failure_rate,
            latency_increase=100.0 if experiment.failure_type == FailureType.LATENCY else 0.0,
            system_recovered=True,
            observations=[f"Injected {experiment.failure_type.value} failure at {experiment.failure_rate}%"]
        )

        # Simulate experiment completion
        result.completed_at = time.time()

        experiment.status = ExperimentStatus.COMPLETED
        self.results.append(result)

        return result

    def get_resilience_metrics(self, service_name: str) -> Dict:
        """Get resilience metrics for service"""
        service_results = [r for r in self.results
                          if any(e.target_service == service_name
                                for e in self.experiments.values()
                                if e.experiment_id == r.experiment_id)]

        if not service_results:
            return {}

        recovery_rate = sum(1 for r in service_results if r.system_recovered) / len(service_results) * 100
        avg_latency = sum(r.latency_increase for r in service_results) / len(service_results)

        return {
            "service": service_name,
            "experiments": len(service_results),
            "recovery_rate": recovery_rate,
            "avg_latency_increase": avg_latency,
            "resilience_score": recovery_rate / 100.0,
        }

    def get_chaos_stats(self) -> Dict:
        """Get chaos engineering statistics"""
        return {
            "total_experiments": len(self.experiments),
            "completed": sum(1 for e in self.experiments.values()
                           if e.status == ExperimentStatus.COMPLETED),
            "total_results": len(self.results),
            "recovered": sum(1 for r in self.results if r.system_recovered),
        }

    def generate_chaos_report(self) -> str:
        """Generate chaos engineering report"""
        stats = self.get_chaos_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              CHAOS ENGINEERING MANAGER REPORT                              ║
╚════════════════════════════════════════════════════════════════════════════╝

🔬 STATISTICS:
├─ Total Experiments: {stats['total_experiments']}
├─ Completed: {stats['completed']}
├─ Results: {stats['total_results']}
└─ Recovered: {stats['recovered']}
"""
        return report

    def export_chaos_config(self) -> str:
        """Export chaos configuration"""
        return json.dumps({"timestamp": time.time(), "experiments": len(self.experiments)}, indent=2)


def main():
    """CLI interface"""
    print("🔬 Chaos Engineering Manager - Resilience Testing")
    print("=" * 70)

    manager = ChaosEngineeringManager()

    # Create experiments
    print("\n🧪 Creating chaos experiments...")
    exp1 = manager.create_experiment("Latency Spike", FailureType.LATENCY, "api-service", 300, 50.0)
    exp2 = manager.create_experiment("High Error Rate", FailureType.ERROR, "database", 180, 25.0)
    print(f"✅ Created {len(manager.experiments)} experiments")

    # Run experiments
    print("\n▶️  Running experiments...")
    result1 = manager.run_experiment(exp1.experiment_id)
    result2 = manager.run_experiment(exp2.experiment_id)
    print(f"✅ Completed {len(manager.results)} experiments")

    # Generate report
    print(manager.generate_chaos_report())

    print("\n" + "=" * 70)
    print("✨ Chaos engineering manager ready")


if __name__ == "__main__":
    main()
