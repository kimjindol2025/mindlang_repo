#!/usr/bin/env python3
"""
Data Pipeline Orchestrator - ETL and data processing pipeline management
Orchestrates complex data workflows with dependencies, monitoring, and error handling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Set, Tuple
import hashlib
import json
import time
import random


class PipelineStatus(Enum):
    """Status of pipeline"""
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(Enum):
    """Status of pipeline task"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRYING = "RETRYING"


class DataSourceType(Enum):
    """Types of data sources"""
    DATABASE = "DATABASE"
    S3 = "S3"
    KAFKA = "KAFKA"
    API = "API"
    FILE_SYSTEM = "FILE_SYSTEM"
    WAREHOUSE = "WAREHOUSE"
    STREAMING = "STREAMING"


class TaskType(Enum):
    """Types of pipeline tasks"""
    EXTRACT = "EXTRACT"
    TRANSFORM = "TRANSFORM"
    LOAD = "LOAD"
    VALIDATION = "VALIDATION"
    AGGREGATION = "AGGREGATION"
    JOIN = "JOIN"
    FILTER = "FILTER"
    CUSTOM = "CUSTOM"


@dataclass
class DataSource:
    """Data source configuration"""
    source_id: str
    name: str
    source_type: DataSourceType
    connection_config: Dict
    schema: Dict = field(default_factory=dict)
    last_check: Optional[float] = None
    is_healthy: bool = True


@dataclass
class PipelineTask:
    """Individual task in pipeline"""
    task_id: str
    task_name: str
    task_type: TaskType
    description: str
    input_sources: List[str] = field(default_factory=list)  # Source IDs
    output_source: Optional[str] = None  # Destination
    dependencies: List[str] = field(default_factory=list)  # Task IDs
    retry_policy: Dict = field(default_factory=lambda: {"max_retries": 3, "backoff_seconds": 60})
    timeout_seconds: int = 3600
    estimated_duration: int = 60
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    execution_time: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0


@dataclass
class PipelineExecution:
    """Execution of a pipeline"""
    execution_id: str
    pipeline_id: str
    status: PipelineStatus
    started_at: float
    completed_at: Optional[float] = None
    tasks_status: Dict[str, TaskStatus] = field(default_factory=dict)
    rows_processed: int = 0
    rows_failed: int = 0
    total_duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DataPipeline:
    """Complete data pipeline definition"""
    pipeline_id: str
    pipeline_name: str
    description: str
    created_at: float
    owner: str
    status: PipelineStatus
    tasks: Dict[str, PipelineTask] = field(default_factory=dict)
    sources: Dict[str, DataSource] = field(default_factory=dict)
    schedule: str = ""  # Cron expression
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    sla_hours: int = 24
    execution_history: List[PipelineExecution] = field(default_factory=list)


class DataPipelineOrchestrator:
    """
    Enterprise data pipeline orchestration system

    Provides:
    - Complex ETL pipeline orchestration
    - Task dependency management
    - Data quality validation
    - Error handling and retry logic
    - Pipeline monitoring and alerting
    - SLA tracking
    - Data lineage tracking
    - Performance optimization
    """

    def __init__(self):
        self.pipelines: Dict[str, DataPipeline] = {}
        self.executions: Dict[str, PipelineExecution] = {}
        self.data_sources: Dict[str, DataSource] = {}
        self.task_results: Dict[str, Dict] = {}

    def create_data_source(self,
                          name: str,
                          source_type: DataSourceType,
                          connection_config: Dict) -> DataSource:
        """
        Register data source

        Args:
            name: Source name
            source_type: Type of source
            connection_config: Connection configuration

        Returns:
            Created DataSource
        """
        source_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        source = DataSource(
            source_id=source_id,
            name=name,
            source_type=source_type,
            connection_config=connection_config,
            last_check=time.time()
        )

        self.data_sources[source_id] = source
        return source

    def create_pipeline(self,
                       name: str,
                       description: str,
                       owner: str,
                       sla_hours: int = 24) -> DataPipeline:
        """
        Create data pipeline

        Args:
            name: Pipeline name
            description: Pipeline description
            owner: Pipeline owner
            sla_hours: SLA in hours

        Returns:
            Created DataPipeline
        """
        pipeline_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        pipeline = DataPipeline(
            pipeline_id=pipeline_id,
            pipeline_name=name,
            description=description,
            owner=owner,
            created_at=time.time(),
            status=PipelineStatus.DRAFT,
            sla_hours=sla_hours
        )

        self.pipelines[pipeline_id] = pipeline
        return pipeline

    def add_task(self,
                pipeline_id: str,
                task_name: str,
                task_type: TaskType,
                description: str,
                input_sources: List[str] = None,
                dependencies: List[str] = None) -> Optional[PipelineTask]:
        """
        Add task to pipeline

        Args:
            pipeline_id: Target pipeline
            task_name: Task name
            task_type: Task type
            description: Task description
            input_sources: Input data sources
            dependencies: Dependent task IDs

        Returns:
            Created PipelineTask
        """
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None

        task_id = hashlib.md5(f"{pipeline_id}:{task_name}".encode()).hexdigest()[:8]

        task = PipelineTask(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            description=description,
            input_sources=input_sources or [],
            dependencies=dependencies or []
        )

        pipeline.tasks[task_id] = task
        return task

    def execute_pipeline(self, pipeline_id: str) -> PipelineExecution:
        """
        Execute pipeline

        Args:
            pipeline_id: Pipeline to execute

        Returns:
            PipelineExecution with results
        """
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return None

        execution_id = hashlib.md5(f"{pipeline_id}:{time.time()}".encode()).hexdigest()[:8]

        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            started_at=time.time()
        )

        # Validate data sources
        for source in pipeline.sources.values():
            if not self._validate_source(source):
                execution.errors.append(f"Data source '{source.name}' is unhealthy")
                source.is_healthy = False

        if execution.errors:
            execution.status = PipelineStatus.FAILED
            execution.completed_at = time.time()
            return execution

        # Execute tasks in order
        executed_tasks = set()
        pending_tasks = set(pipeline.tasks.keys())

        while pending_tasks:
            ready_tasks = [
                task_id for task_id in pending_tasks
                if all(dep in executed_tasks for dep in pipeline.tasks[task_id].dependencies)
            ]

            if not ready_tasks:
                execution.errors.append("Circular dependency detected")
                execution.status = PipelineStatus.FAILED
                break

            for task_id in ready_tasks:
                task = pipeline.tasks[task_id]
                success = self._execute_task(task, execution)

                if success:
                    task.status = TaskStatus.SUCCEEDED
                    executed_tasks.add(task_id)
                else:
                    task.status = TaskStatus.FAILED
                    if task.retry_count < task.retry_policy.get("max_retries", 3):
                        task.retry_count += 1
                        task.status = TaskStatus.RETRYING
                    else:
                        execution.errors.append(f"Task {task.task_name} failed after retries")
                        execution.status = PipelineStatus.FAILED

                pending_tasks.remove(task_id)

        # Finalize execution
        if execution.status != PipelineStatus.FAILED:
            execution.status = PipelineStatus.COMPLETED

        execution.completed_at = time.time()
        execution.total_duration = execution.completed_at - execution.started_at

        # Check SLA
        if execution.total_duration > (pipeline.sla_hours * 3600):
            execution.warnings.append(f"Pipeline exceeded SLA ({pipeline.sla_hours} hours)")

        pipeline.execution_history.append(execution)
        self.executions[execution_id] = execution

        return execution

    def _validate_source(self, source: DataSource) -> bool:
        """Validate data source is healthy"""
        # Simulate health check
        is_healthy = random.random() > 0.05  # 95% healthy rate
        source.is_healthy = is_healthy
        source.last_check = time.time()
        return is_healthy

    def _execute_task(self, task: PipelineTask, execution: PipelineExecution) -> bool:
        """Execute individual task"""
        task.started_at = time.time()

        try:
            # Simulate task execution
            execution_time = random.uniform(1, task.timeout_seconds / 2)
            time.sleep(min(execution_time / 100, 1))  # Scaled down for testing

            # Simulate random failures (10% failure rate)
            if random.random() < 0.10:
                task.error_message = f"Task execution failed"
                task.completed_at = time.time()
                task.execution_time = task.completed_at - task.started_at
                execution.rows_failed += random.randint(100, 1000)
                return False

            # Simulate data processing
            execution.rows_processed += random.randint(1000, 10000)

            task.completed_at = time.time()
            task.execution_time = task.completed_at - task.started_at

            return True

        except Exception as e:
            task.error_message = str(e)
            task.completed_at = time.time()
            return False

    def get_pipeline_status(self, pipeline_id: str) -> Dict:
        """Get pipeline status"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return {}

        last_execution = pipeline.execution_history[-1] if pipeline.execution_history else None

        status = {
            "pipeline_id": pipeline_id,
            "name": pipeline.pipeline_name,
            "status": pipeline.status.value,
            "tasks": len(pipeline.tasks),
            "sources": len(pipeline.sources),
            "last_execution": {
                "status": last_execution.status.value if last_execution else "Never",
                "rows_processed": last_execution.rows_processed if last_execution else 0,
                "duration": last_execution.total_duration if last_execution else 0,
            } if last_execution else None,
        }

        return status

    def generate_pipeline_report(self, pipeline_id: str) -> str:
        """Generate pipeline execution report"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return f"❌ Pipeline {pipeline_id} not found"

        last_exec = pipeline.execution_history[-1] if pipeline.execution_history else None

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     DATA PIPELINE EXECUTION REPORT                         ║
║                     {pipeline.pipeline_name}                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 PIPELINE DETAILS:
├─ ID: {pipeline.pipeline_id}
├─ Owner: {pipeline.owner}
├─ Status: {pipeline.status.value}
├─ Tasks: {len(pipeline.tasks)}
├─ Data Sources: {len(pipeline.sources)}
└─ SLA: {pipeline.sla_hours} hours

"""

        if last_exec:
            report += f"📊 LAST EXECUTION:\n"
            report += f"├─ Status: {last_exec.status.value}\n"
            report += f"├─ Rows Processed: {last_exec.rows_processed:,}\n"
            report += f"├─ Rows Failed: {last_exec.rows_failed}\n"
            report += f"├─ Duration: {last_exec.total_duration:.1f}s\n"

            if last_exec.errors:
                report += f"├─ Errors: {len(last_exec.errors)}\n"
                for error in last_exec.errors[:3]:
                    report += f"│  • {error}\n"

            if last_exec.warnings:
                report += f"└─ Warnings: {len(last_exec.warnings)}\n"
                for warning in last_exec.warnings[:3]:
                    report += f"   • {warning}\n"

        report += f"\n📋 TASKS:\n"
        for task_id, task in list(pipeline.tasks.items())[:10]:
            status_emoji = "✅" if task.status == TaskStatus.SUCCEEDED else "❌" if task.status == TaskStatus.FAILED else "⏳"
            report += f"{status_emoji} {task.task_name} ({task.task_type.value})\n"

        return report

    def export_pipeline(self, pipeline_id: str) -> str:
        """Export pipeline definition as JSON"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return "{}"

        export_data = {
            "pipeline_id": pipeline.pipeline_id,
            "name": pipeline.pipeline_name,
            "description": pipeline.description,
            "owner": pipeline.owner,
            "status": pipeline.status.value,
            "tasks": [
                {
                    "name": task.task_name,
                    "type": task.task_type.value,
                    "dependencies": task.dependencies,
                    "status": task.status.value,
                }
                for task in pipeline.tasks.values()
            ],
            "sources": [
                {
                    "name": source.name,
                    "type": source.source_type.value,
                    "healthy": source.is_healthy,
                }
                for source in pipeline.sources.values()
            ],
            "execution_count": len(pipeline.execution_history),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔀 Data Pipeline Orchestrator - ETL Pipeline Management")
    print("=" * 70)

    orchestrator = DataPipelineOrchestrator()

    # Create data sources
    print("\n🔌 Creating data sources...")
    source1 = orchestrator.create_data_source(
        "production_db",
        DataSourceType.DATABASE,
        {"host": "prod-db.example.com", "database": "transactions"}
    )

    source2 = orchestrator.create_data_source(
        "data_warehouse",
        DataSourceType.WAREHOUSE,
        {"bucket": "analytics-dw", "path": "/transactions"}
    )

    source3 = orchestrator.create_data_source(
        "s3_archive",
        DataSourceType.S3,
        {"bucket": "data-archive", "region": "us-east-1"}
    )

    print(f"✅ Created {len(orchestrator.data_sources)} data sources")

    # Create pipeline
    print("\n📐 Creating ETL pipeline...")
    pipeline = orchestrator.create_pipeline(
        "Daily Transaction ETL",
        "Daily extraction and loading of transaction data",
        "data-engineering@example.com",
        sla_hours=4
    )

    pipeline.sources[source1.source_id] = source1
    pipeline.sources[source2.source_id] = source2
    pipeline.sources[source3.source_id] = source3

    # Add tasks
    print("\n➕ Adding pipeline tasks...")
    extract_task = orchestrator.add_task(
        pipeline.pipeline_id,
        "Extract from Production",
        TaskType.EXTRACT,
        "Extract transaction data from production database",
        input_sources=[source1.source_id]
    )

    transform_task = orchestrator.add_task(
        pipeline.pipeline_id,
        "Transform Data",
        TaskType.TRANSFORM,
        "Clean and transform data",
        dependencies=[extract_task.task_id]
    )

    validate_task = orchestrator.add_task(
        pipeline.pipeline_id,
        "Validate Quality",
        TaskType.VALIDATION,
        "Validate data quality",
        dependencies=[transform_task.task_id]
    )

    load_task = orchestrator.add_task(
        pipeline.pipeline_id,
        "Load to Warehouse",
        TaskType.LOAD,
        "Load transformed data to warehouse",
        input_sources=[source2.source_id],
        dependencies=[validate_task.task_id]
    )

    archive_task = orchestrator.add_task(
        pipeline.pipeline_id,
        "Archive to S3",
        TaskType.LOAD,
        "Archive to S3 for long-term storage",
        input_sources=[source3.source_id],
        dependencies=[validate_task.task_id]
    )

    print(f"✅ Added {len(pipeline.tasks)} tasks")

    # Execute pipeline
    print("\n▶️  Executing pipeline...")
    execution = orchestrator.execute_pipeline(pipeline.pipeline_id)

    print(f"Status: {execution.status.value}")
    print(f"Rows Processed: {execution.rows_processed:,}")
    print(f"Duration: {execution.total_duration:.1f}s")

    # Generate report
    print(orchestrator.generate_pipeline_report(pipeline.pipeline_id))

    # Export
    print("\n📄 Exporting pipeline definition...")
    export = orchestrator.export_pipeline(pipeline.pipeline_id)
    print(f"✅ Exported {len(export)} characters of pipeline data")

    print("\n" + "=" * 70)
    print("✨ Data pipeline orchestration complete")


if __name__ == "__main__":
    main()
