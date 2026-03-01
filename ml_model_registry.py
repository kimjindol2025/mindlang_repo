#!/usr/bin/env python3
"""
ML Model Registry - Model versioning, tracking, and lifecycle management
Manages ML models, versions, metrics, and deployment tracking
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time
import random


class ModelStatus(Enum):
    """Status of model"""
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"
    DEPRECATED = "DEPRECATED"


class MetricType(Enum):
    """Types of model metrics"""
    ACCURACY = "ACCURACY"
    PRECISION = "PRECISION"
    RECALL = "RECALL"
    F1_SCORE = "F1_SCORE"
    AUC_ROC = "AUC_ROC"
    LOSS = "LOSS"
    RMSE = "RMSE"
    MAE = "MAE"
    CUSTOM = "CUSTOM"


class FrameworkType(Enum):
    """ML frameworks"""
    TENSORFLOW = "TENSORFLOW"
    PYTORCH = "PYTORCH"
    SCIKIT_LEARN = "SCIKIT_LEARN"
    XGBOOST = "XGBOOST"
    KERAS = "KERAS"
    ONNX = "ONNX"
    JINJA = "JINJA"
    CUSTOM = "CUSTOM"


@dataclass
class ModelMetrics:
    """Metrics for model"""
    metric_type: MetricType
    value: float
    dataset: str
    computed_at: float


@dataclass
class ModelVersion:
    """Version of a model"""
    version_id: str
    model_id: str
    version_number: str  # e.g., "1.0.0"
    created_at: float
    created_by: str
    description: str
    status: ModelStatus
    framework: FrameworkType
    input_schema: Dict
    output_schema: Dict
    metrics: List[ModelMetrics] = field(default_factory=list)
    parameters: Dict = field(default_factory=dict)
    training_data: Dict = field(default_factory=dict)
    model_size_mb: float = 0.0
    inference_time_ms: float = 0.0
    deployment_info: Optional[Dict] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ModelComparison:
    """Comparison between two model versions"""
    comparison_id: str
    model_id: str
    version1_id: str
    version2_id: str
    timestamp: float
    metric_deltas: Dict[str, float] = field(default_factory=dict)
    winner: Optional[str] = None
    improvement_percent: float = 0.0


@dataclass
class DeploymentRecord:
    """Record of model deployment"""
    deployment_id: str
    model_id: str
    version_id: str
    environment: str  # "staging", "production"
    deployed_at: float
    deployed_by: str
    status: str  # "ACTIVE", "ROLLED_BACK"
    endpoint_url: Optional[str] = None
    traffic_percentage: float = 100.0
    request_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class Model:
    """ML Model"""
    model_id: str
    model_name: str
    description: str
    task_type: str  # "classification", "regression", "NLP", etc.
    created_at: float
    created_by: str
    owner: str
    versions: Dict[str, ModelVersion] = field(default_factory=dict)
    current_production_version: Optional[str] = None
    deployments: List[DeploymentRecord] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class MLModelRegistry:
    """
    Enterprise ML Model Registry

    Provides:
    - Model versioning and lifecycle
    - Performance metrics tracking
    - Model comparison and evaluation
    - Deployment management
    - Model serving and inference
    - Model registry and discoverability
    - Audit and compliance tracking
    """

    def __init__(self):
        self.models: Dict[str, Model] = {}
        self.versions: Dict[str, ModelVersion] = {}
        self.deployments: Dict[str, DeploymentRecord] = {}
        self.comparisons: List[ModelComparison] = []

    def create_model(self,
                    name: str,
                    description: str,
                    task_type: str,
                    owner: str,
                    created_by: str) -> Model:
        """
        Create new model

        Args:
            name: Model name
            description: Model description
            task_type: Task type (classification, regression, etc.)
            owner: Model owner
            created_by: Creator

        Returns:
            Created Model
        """
        model_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        model = Model(
            model_id=model_id,
            model_name=name,
            description=description,
            task_type=task_type,
            created_at=time.time(),
            created_by=created_by,
            owner=owner
        )

        self.models[model_id] = model
        return model

    def register_version(self,
                        model_id: str,
                        version_number: str,
                        description: str,
                        framework: FrameworkType,
                        created_by: str,
                        input_schema: Dict,
                        output_schema: Dict,
                        parameters: Dict = None) -> Optional[ModelVersion]:
        """
        Register new model version

        Args:
            model_id: Target model
            version_number: Version number (e.g., "1.0.0")
            description: Version description
            framework: ML framework
            created_by: Creator
            input_schema: Input schema
            output_schema: Output schema
            parameters: Model parameters

        Returns:
            Registered ModelVersion
        """
        model = self.models.get(model_id)
        if not model:
            return None

        version_id = hashlib.md5(f"{model_id}:{version_number}".encode()).hexdigest()[:8]

        version = ModelVersion(
            version_id=version_id,
            model_id=model_id,
            version_number=version_number,
            created_at=time.time(),
            created_by=created_by,
            description=description,
            status=ModelStatus.DEVELOPMENT,
            framework=framework,
            input_schema=input_schema,
            output_schema=output_schema,
            parameters=parameters or {},
            model_size_mb=random.uniform(10, 500),
            inference_time_ms=random.uniform(10, 100)
        )

        model.versions[version_id] = version
        self.versions[version_id] = version

        return version

    def record_metrics(self,
                      version_id: str,
                      metrics: List[Dict]) -> int:
        """
        Record model metrics

        Args:
            version_id: Model version
            metrics: List of metrics

        Returns:
            Number of metrics recorded
        """
        version = self.versions.get(version_id)
        if not version:
            return 0

        recorded = 0
        for metric_data in metrics:
            metric = ModelMetrics(
                metric_type=MetricType[metric_data.get("type", "ACCURACY")],
                value=metric_data.get("value", 0.0),
                dataset=metric_data.get("dataset", "test"),
                computed_at=time.time()
            )
            version.metrics.append(metric)
            recorded += 1

        return recorded

    def promote_version(self,
                       version_id: str,
                       new_status: ModelStatus) -> bool:
        """
        Promote model version to new status

        Args:
            version_id: Model version to promote
            new_status: Target status

        Returns:
            Promotion success
        """
        version = self.versions.get(version_id)
        if not version:
            return False

        version.status = new_status

        # If promoting to production, update model
        if new_status == ModelStatus.PRODUCTION:
            model = self.models.get(version.model_id)
            if model:
                model.current_production_version = version_id

        return True

    def compare_versions(self,
                        version1_id: str,
                        version2_id: str) -> Optional[ModelComparison]:
        """
        Compare two model versions

        Args:
            version1_id: First version
            version2_id: Second version

        Returns:
            ModelComparison with deltas
        """
        v1 = self.versions.get(version1_id)
        v2 = self.versions.get(version2_id)

        if not v1 or not v2:
            return None

        comparison_id = hashlib.md5(f"{version1_id}:{version2_id}".encode()).hexdigest()[:8]

        comparison = ModelComparison(
            comparison_id=comparison_id,
            model_id=v1.model_id,
            version1_id=version1_id,
            version2_id=version2_id,
            timestamp=time.time()
        )

        # Compare metrics
        v1_metrics = {m.metric_type.value: m.value for m in v1.metrics}
        v2_metrics = {m.metric_type.value: m.value for m in v2.metrics}

        for metric_name in set(list(v1_metrics.keys()) + list(v2_metrics.keys())):
            if metric_name in v1_metrics and metric_name in v2_metrics:
                delta = v2_metrics[metric_name] - v1_metrics[metric_name]
                comparison.metric_deltas[metric_name] = delta

        # Determine winner
        if comparison.metric_deltas:
            avg_improvement = sum(comparison.metric_deltas.values()) / len(comparison.metric_deltas)
            if avg_improvement > 0:
                comparison.winner = version2_id
                comparison.improvement_percent = abs(avg_improvement)
            elif avg_improvement < 0:
                comparison.winner = version1_id
                comparison.improvement_percent = abs(avg_improvement)

        self.comparisons.append(comparison)
        return comparison

    def deploy_version(self,
                      version_id: str,
                      environment: str,
                      deployed_by: str,
                      endpoint_url: Optional[str] = None,
                      traffic_percentage: float = 100.0) -> Optional[DeploymentRecord]:
        """
        Deploy model version

        Args:
            version_id: Version to deploy
            environment: Environment (staging, production)
            deployed_by: Deployer
            endpoint_url: Endpoint URL
            traffic_percentage: Traffic allocation (for canary)

        Returns:
            DeploymentRecord
        """
        version = self.versions.get(version_id)
        if not version:
            return None

        deployment_id = hashlib.md5(f"{version_id}:{environment}:{time.time()}".encode()).hexdigest()[:8]

        deployment = DeploymentRecord(
            deployment_id=deployment_id,
            model_id=version.model_id,
            version_id=version_id,
            environment=environment,
            deployed_at=time.time(),
            deployed_by=deployed_by,
            status="ACTIVE",
            endpoint_url=endpoint_url,
            traffic_percentage=traffic_percentage
        )

        model = self.models.get(version.model_id)
        if model:
            model.deployments.append(deployment)

        self.deployments[deployment_id] = deployment

        return deployment

    def get_model_status(self, model_id: str) -> Dict:
        """Get model status"""
        model = self.models.get(model_id)
        if not model:
            return {}

        status = {
            "model_id": model_id,
            "name": model.model_name,
            "task_type": model.task_type,
            "total_versions": len(model.versions),
            "production_version": model.current_production_version,
            "latest_version": max(model.versions.values(), key=lambda v: v.created_at).version_id if model.versions else None,
            "active_deployments": len([d for d in model.deployments if d.status == "ACTIVE"]),
        }

        if model.current_production_version:
            prod_version = model.versions.get(model.current_production_version)
            if prod_version:
                prod_metrics = {m.metric_type.value: m.value for m in prod_version.metrics}
                status["production_metrics"] = prod_metrics

        return status

    def generate_model_report(self, model_id: str) -> str:
        """Generate model report"""
        model = self.models.get(model_id)
        if not model:
            return f"❌ Model {model_id} not found"

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         ML MODEL REGISTRY REPORT                           ║
║                         {model.model_name}                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 MODEL DETAILS:
├─ ID: {model.model_id}
├─ Task Type: {model.task_type}
├─ Owner: {model.owner}
├─ Created: {time.strftime('%Y-%m-%d', time.localtime(model.created_at))}
└─ Versions: {len(model.versions)}

📊 VERSIONS:
"""

        for version_id, version in sorted(model.versions.items(), key=lambda x: x[1].created_at, reverse=True)[:5]:
            report += f"\n  • v{version.version_number} ({version.status.value})\n"
            report += f"    Framework: {version.framework.value}\n"
            report += f"    Size: {version.model_size_mb:.1f}MB\n"
            report += f"    Inference: {version.inference_time_ms:.1f}ms\n"

            if version.metrics:
                report += f"    Metrics:\n"
                for metric in version.metrics[-3:]:
                    report += f"      • {metric.metric_type.value}: {metric.value:.4f}\n"

        report += f"\n🚀 DEPLOYMENTS: {len(model.deployments)}\n"
        for deployment in model.deployments[-3:]:
            emoji = "✅" if deployment.status == "ACTIVE" else "❌"
            report += f"{emoji} {deployment.environment}: {deployment.traffic_percentage:.0f}% traffic\n"

        if model.current_production_version:
            report += f"\n📌 PRODUCTION VERSION: {model.current_production_version}\n"

        return report

    def export_model(self, model_id: str) -> str:
        """Export model metadata as JSON"""
        model = self.models.get(model_id)
        if not model:
            return "{}"

        export_data = {
            "model_id": model.model_id,
            "name": model.model_name,
            "task_type": model.task_type,
            "created_at": model.created_at,
            "versions": [
                {
                    "version": v.version_number,
                    "status": v.status.value,
                    "framework": v.framework.value,
                    "created_at": v.created_at,
                    "metrics": [
                        {
                            "type": m.metric_type.value,
                            "value": m.value,
                        }
                        for m in v.metrics
                    ]
                }
                for v in model.versions.values()
            ],
            "deployments": [
                {
                    "environment": d.environment,
                    "version": d.version_id,
                    "status": d.status,
                    "deployed_at": d.deployed_at,
                }
                for d in model.deployments
            ]
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🤖 ML Model Registry - Model Versioning and Deployment")
    print("=" * 70)

    registry = MLModelRegistry()

    # Create model
    print("\n📝 Creating model...")
    model = registry.create_model(
        "Customer Churn Prediction",
        "Predicts customer churn probability",
        "classification",
        "data-science-team",
        "alice@example.com"
    )
    print(f"✅ Created model {model.model_id}")

    # Register versions
    print("\n📦 Registering model versions...")
    v1 = registry.register_version(
        model.model_id,
        "1.0.0",
        "Initial baseline model",
        FrameworkType.SCIKIT_LEARN,
        "alice@example.com",
        {"features": ["age", "tenure", "monthly_charges"]},
        {"prediction": "float", "probability": "float"},
        {"n_estimators": 100}
    )

    v2 = registry.register_version(
        model.model_id,
        "1.1.0",
        "Improved with feature engineering",
        FrameworkType.XGBOOST,
        "bob@example.com",
        {"features": ["age", "tenure", "monthly_charges", "derived_value"]},
        {"prediction": "float", "probability": "float"},
        {"n_estimators": 200, "max_depth": 5}
    )

    # Record metrics
    print("\n📊 Recording metrics...")
    registry.record_metrics(v1.version_id, [
        {"type": "ACCURACY", "value": 0.82, "dataset": "test"},
        {"type": "PRECISION", "value": 0.79, "dataset": "test"},
        {"type": "RECALL", "value": 0.75, "dataset": "test"},
    ])

    registry.record_metrics(v2.version_id, [
        {"type": "ACCURACY", "value": 0.86, "dataset": "test"},
        {"type": "PRECISION", "value": 0.84, "dataset": "test"},
        {"type": "RECALL", "value": 0.81, "dataset": "test"},
    ])
    print(f"✅ Recorded metrics for {len(model.versions)} versions")

    # Compare versions
    print("\n🔍 Comparing versions...")
    comparison = registry.compare_versions(v1.version_id, v2.version_id)
    if comparison:
        print(f"Winner: v{registry.versions[comparison.winner].version_number}")
        print(f"Improvement: {comparison.improvement_percent:.2f}%")

    # Promote to production
    print("\n🚀 Promoting to production...")
    registry.promote_version(v2.version_id, ModelStatus.STAGING)
    registry.promote_version(v2.version_id, ModelStatus.PRODUCTION)
    print(f"✅ Promoted v{v2.version_number} to PRODUCTION")

    # Deploy
    print("\n📤 Deploying model...")
    deployment = registry.deploy_version(
        v2.version_id,
        "production",
        "ops@example.com",
        "https://api.example.com/churn-model/predict",
        100.0
    )
    print(f"✅ Deployed to {deployment.environment}")

    # Generate report
    print(registry.generate_model_report(model.model_id))

    # Export
    print("\n📄 Exporting model metadata...")
    export = registry.export_model(model.model_id)
    print(f"✅ Exported {len(export)} characters of metadata")

    print("\n" + "=" * 70)
    print("✨ ML model registry setup complete")


if __name__ == "__main__":
    main()
