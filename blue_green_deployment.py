#!/usr/bin/env python3
"""
Blue-Green Deployment Manager - Zero-downtime deployment strategy
Manages simultaneous blue and green environments with traffic switching
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time
import random


class Environment(Enum):
    """Deployment environment"""
    BLUE = "BLUE"
    GREEN = "GREEN"


class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATION = "VALIDATION"
    READY = "READY"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


class TrafficSplit(Enum):
    """Traffic split strategy"""
    ALL_BLUE = "ALL_BLUE"
    ALL_GREEN = "ALL_GREEN"
    SPLIT_50_50 = "SPLIT_50_50"
    SPLIT_10_90 = "SPLIT_10_90"
    SPLIT_25_75 = "SPLIT_25_75"
    CUSTOM = "CUSTOM"


@dataclass
class ServiceInstance:
    """Service instance in environment"""
    instance_id: str
    host: str
    port: int
    status: str = "RUNNING"
    health: float = 1.0  # 0.0 - 1.0
    request_count: int = 0
    error_count: int = 0


@dataclass
class EnvironmentDeployment:
    """Deployment environment"""
    environment_id: str
    environment: Environment
    version: str
    instances: Dict[str, ServiceInstance] = field(default_factory=dict)
    status: DeploymentStatus = DeploymentStatus.PENDING
    deployed_at: Optional[float] = None
    last_health_check: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class DeploymentSwitchEvent:
    """Traffic switch event"""
    switch_id: str
    from_env: Environment
    to_env: Environment
    traffic_split: TrafficSplit
    switch_time: float
    duration_seconds: float
    successful: bool = True
    errors: List[str] = field(default_factory=list)


class BlueGreenDeploymentManager:
    """
    Blue-Green Deployment Manager

    Provides:
    - Simultaneous blue and green environments
    - Zero-downtime deployments
    - Traffic switching and gradual rollout
    - Health validation
    - Automatic rollback
    - Deployment history
    """

    def __init__(self, service_name: str = "default-service"):
        self.service_name = service_name
        self.blue: EnvironmentDeployment = None
        self.green: EnvironmentDeployment = None
        self.active_environment: Environment = Environment.BLUE
        self.traffic_split: TrafficSplit = TrafficSplit.ALL_BLUE
        self.deployment_history: List[EnvironmentDeployment] = []
        self.switch_history: List[DeploymentSwitchEvent] = []

        # Initialize blue environment
        self._initialize_environment(Environment.BLUE, "v1.0.0")

    def _initialize_environment(self, env: Environment, version: str) -> EnvironmentDeployment:
        """Initialize environment"""
        env_id = hashlib.md5(
            f"{env.value}:{self.service_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        deployment = EnvironmentDeployment(
            environment_id=env_id,
            environment=env,
            version=version,
            status=DeploymentStatus.ACTIVE if env == self.active_environment else DeploymentStatus.PENDING
        )

        # Add sample instances
        for i in range(3):
            instance_id = hashlib.md5(
                f"{env.value}:{i}:{time.time()}".encode()
            ).hexdigest()[:8]
            deployment.instances[instance_id] = ServiceInstance(
                instance_id=instance_id,
                host=f"10.0.{env.value.lower()}.{10+i}",
                port=8000 + i
            )

        if env == Environment.BLUE:
            self.blue = deployment
        else:
            self.green = deployment

        return deployment

    def deploy_new_version(self, new_version: str, deployment_config: Dict) -> EnvironmentDeployment:
        """Deploy new version to inactive environment"""
        # Determine inactive environment
        inactive_env = Environment.GREEN if self.active_environment == Environment.BLUE else Environment.BLUE

        # Create new deployment
        env_id = hashlib.md5(
            f"{inactive_env.value}:{self.service_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        deployment = EnvironmentDeployment(
            environment_id=env_id,
            environment=inactive_env,
            version=new_version,
            status=DeploymentStatus.IN_PROGRESS
        )

        # Simulate deployment process
        time.sleep(0.1)  # Simulate deployment time

        # Add instances
        for i in range(deployment_config.get("instance_count", 3)):
            instance_id = hashlib.md5(
                f"{inactive_env.value}:{i}:{time.time()}".encode()
            ).hexdigest()[:8]
            deployment.instances[instance_id] = ServiceInstance(
                instance_id=instance_id,
                host=f"10.0.{inactive_env.value.lower()}.{10+i}",
                port=8000 + i,
                status="RUNNING"
            )

        deployment.status = DeploymentStatus.READY
        deployment.deployed_at = time.time()

        # Update reference
        if inactive_env == Environment.GREEN:
            self.green = deployment
        else:
            self.blue = deployment

        self.deployment_history.append(deployment)
        return deployment

    def validate_deployment(self, environment: Environment) -> bool:
        """Validate deployment health"""
        deployment = self.green if environment == Environment.GREEN else self.blue

        if not deployment:
            return False

        deployment.status = DeploymentStatus.VALIDATION

        # Simulate health checks
        healthy_count = sum(1 for inst in deployment.instances.values()
                          if inst.status == "RUNNING" and inst.health > 0.8)

        all_healthy = healthy_count == len(deployment.instances)

        if all_healthy:
            deployment.status = DeploymentStatus.READY
        else:
            deployment.status = DeploymentStatus.FAILED
            return False

        deployment.last_health_check = time.time()
        return True

    def switch_traffic(self,
                      to_environment: Environment,
                      traffic_split: TrafficSplit = TrafficSplit.ALL_GREEN,
                      gradual: bool = False) -> DeploymentSwitchEvent:
        """Switch traffic to new environment"""
        switch_id = hashlib.md5(
            f"{self.active_environment.value}:{to_environment.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        switch_event = DeploymentSwitchEvent(
            switch_id=switch_id,
            from_env=self.active_environment,
            to_env=to_environment,
            traffic_split=traffic_split,
            switch_time=time.time(),
            duration_seconds=0
        )

        try:
            # Validate target environment
            target_deployment = self.green if to_environment == Environment.GREEN else self.blue
            if target_deployment.status != DeploymentStatus.READY:
                switch_event.successful = False
                switch_event.errors.append("Target environment not ready")
                return switch_event

            # Switch traffic
            if gradual:
                # Implement gradual traffic shift
                splits = [TrafficSplit.SPLIT_10_90, TrafficSplit.SPLIT_25_75,
                         TrafficSplit.SPLIT_50_50, TrafficSplit.ALL_GREEN]
                for split in splits:
                    self.traffic_split = split
                    time.sleep(0.05)  # Simulate gradual shift
            else:
                self.traffic_split = traffic_split

            self.active_environment = to_environment
            target_deployment.status = DeploymentStatus.ACTIVE

            # Mark previous as inactive
            previous_deployment = self.blue if to_environment == Environment.GREEN else self.green
            if previous_deployment:
                previous_deployment.status = DeploymentStatus.READY

            switch_event.duration_seconds = time.time() - switch_event.switch_time
            switch_event.successful = True

        except Exception as e:
            switch_event.successful = False
            switch_event.errors.append(str(e))

        self.switch_history.append(switch_event)
        return switch_event

    def rollback(self) -> bool:
        """Rollback to previous environment"""
        previous_env = Environment.GREEN if self.active_environment == Environment.BLUE else Environment.BLUE

        try:
            self.switch_traffic(previous_env, TrafficSplit.ALL_BLUE if previous_env == Environment.BLUE else TrafficSplit.ALL_GREEN)
            return True
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False

    def get_deployment_metrics(self, environment: Environment) -> Dict:
        """Get deployment metrics"""
        deployment = self.green if environment == Environment.GREEN else self.blue

        if not deployment:
            return {}

        total_requests = sum(inst.request_count for inst in deployment.instances.values())
        total_errors = sum(inst.error_count for inst in deployment.instances.values())
        error_rate = total_errors / max(1, total_requests)

        return {
            "version": deployment.version,
            "status": deployment.status.value,
            "instances": len(deployment.instances),
            "healthy_instances": sum(1 for inst in deployment.instances.values() if inst.health > 0.8),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "deployed_at": deployment.deployed_at,
        }

    def check_environment_health(self, environment: Environment):
        """Perform health checks"""
        deployment = self.green if environment == Environment.GREEN else self.blue

        if not deployment:
            return

        for instance in deployment.instances.values():
            # Simulate health check
            instance.health = max(0, instance.health + (random.random() - 0.5) * 0.1)
            instance.request_count += random.randint(1, 100)
            if random.random() > 0.95:
                instance.error_count += random.randint(1, 5)

        deployment.last_health_check = time.time()

    def get_deployment_stats(self) -> Dict:
        """Get deployment statistics"""
        return {
            "service_name": self.service_name,
            "active_environment": self.active_environment.value,
            "traffic_split": self.traffic_split.value,
            "total_deployments": len(self.deployment_history),
            "total_switches": len(self.switch_history),
            "blue_metrics": self.get_deployment_metrics(Environment.BLUE) if self.blue else {},
            "green_metrics": self.get_deployment_metrics(Environment.GREEN) if self.green else {},
        }

    def generate_deployment_report(self) -> str:
        """Generate deployment report"""
        stats = self.get_deployment_stats()
        blue_metrics = stats.get("blue_metrics", {})
        green_metrics = stats.get("green_metrics", {})

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              BLUE-GREEN DEPLOYMENT REPORT                                  ║
║              Service: {stats['service_name']}                                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🎯 ACTIVE ENVIRONMENT:
├─ Environment: {stats['active_environment']}
└─ Traffic Split: {stats['traffic_split']}

📊 STATISTICS:
├─ Total Deployments: {stats['total_deployments']}
└─ Traffic Switches: {stats['total_switches']}

🔵 BLUE ENVIRONMENT:
├─ Version: {blue_metrics.get('version', 'N/A')}
├─ Status: {blue_metrics.get('status', 'N/A')}
├─ Instances: {blue_metrics.get('healthy_instances', 0)}/{blue_metrics.get('instances', 0)} healthy
└─ Error Rate: {blue_metrics.get('error_rate', 0):.2%}

🟢 GREEN ENVIRONMENT:
├─ Version: {green_metrics.get('version', 'N/A')}
├─ Status: {green_metrics.get('status', 'N/A')}
├─ Instances: {green_metrics.get('healthy_instances', 0)}/{green_metrics.get('instances', 0)} healthy
└─ Error Rate: {green_metrics.get('error_rate', 0):.2%}

📜 RECENT SWITCHES:
"""

        for switch in self.switch_history[-3:]:
            status = "✅" if switch.successful else "❌"
            report += f"{status} {switch.from_env.value} → {switch.to_env.value} ({switch.duration_seconds:.2f}s)\n"

        return report

    def export_deployment_config(self) -> str:
        """Export deployment configuration"""
        export_data = {
            "service_name": self.service_name,
            "timestamp": time.time(),
            "active_environment": self.active_environment.value,
            "traffic_split": self.traffic_split.value,
            "deployments": [
                {
                    "environment": d.environment.value,
                    "version": d.version,
                    "status": d.status.value,
                    "instances": len(d.instances),
                    "deployed_at": d.deployed_at,
                }
                for d in self.deployment_history
            ],
            "statistics": self.get_deployment_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Blue-Green Deployment Manager - Zero-Downtime Deployments")
    print("=" * 70)

    manager = BlueGreenDeploymentManager("payment-service")

    # Deploy new version to green
    print("\n📦 Deploying new version...")
    green_deploy = manager.deploy_new_version("v2.0.0", {"instance_count": 3})
    print(f"✅ Deployed v2.0.0 to GREEN environment")

    # Validate deployment
    print("\n🏥 Validating deployment...")
    manager.check_environment_health(Environment.GREEN)
    is_valid = manager.validate_deployment(Environment.GREEN)
    print(f"✅ Validation: {'PASSED' if is_valid else 'FAILED'}")

    # Switch traffic gradually
    print("\n🔄 Switching traffic (gradual)...")
    switch_event = manager.switch_traffic(
        Environment.GREEN,
        traffic_split=TrafficSplit.ALL_GREEN,
        gradual=True
    )
    print(f"✅ Traffic switched in {switch_event.duration_seconds:.2f}s")

    # Check health
    print("\n🏥 Checking health...")
    manager.check_environment_health(Environment.GREEN)
    manager.check_environment_health(Environment.BLUE)
    print("✅ Health checks completed")

    # Generate report
    print(manager.generate_deployment_report())

    # Export
    print("\n📄 Exporting deployment config...")
    export = manager.export_deployment_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Blue-Green deployment manager ready")


if __name__ == "__main__":
    main()
