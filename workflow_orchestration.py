#!/usr/bin/env python3
"""
Workflow Orchestration System - Complex workflow management
Orchestrates multi-step workflows with conditional logic and error handling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import hashlib
import json
import time
import random


class TaskStatus(Enum):
    """Task status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    RETRY = "RETRY"


class WorkflowStatus(Enum):
    """Workflow status"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class WorkflowTask:
    """Workflow task"""
    task_id: str
    task_name: str
    task_type: str
    depends_on: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    handler: Optional[Callable] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300


@dataclass
class WorkflowExecution:
    """Workflow execution"""
    execution_id: str
    workflow_id: str
    status: WorkflowStatus
    tasks: Dict[str, TaskStatus] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_seconds: float = 0.0


class WorkflowOrchestrator:
    """
    Workflow Orchestration System

    Provides:
    - Complex workflow definition
    - Task dependency management
    - Conditional execution
    - Error handling and retries
    - Parallel task execution
    - Workflow monitoring
    """

    def __init__(self):
        self.workflows: Dict[str, Dict] = {}  # workflow_id -> {tasks, etc}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.task_handlers: Dict[str, Callable] = {}

    def create_workflow(self, workflow_name: str) -> str:
        """Create workflow"""
        workflow_id = hashlib.md5(
            f"{workflow_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        self.workflows[workflow_id] = {
            "name": workflow_name,
            "tasks": {},
            "created_at": time.time(),
            "status": WorkflowStatus.DRAFT
        }

        return workflow_id

    def add_task(self,
                workflow_id: str,
                task_name: str,
                task_type: str,
                depends_on: List[str] = None) -> Optional[str]:
        """Add task to workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        task_id = hashlib.md5(
            f"{workflow_id}:{task_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        task = WorkflowTask(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            depends_on=depends_on or []
        )

        workflow["tasks"][task_id] = task
        return task_id

    def register_task_handler(self, task_type: str, handler: Callable):
        """Register task handler"""
        self.task_handlers[task_type] = handler

    def execute_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Execute workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        execution_id = hashlib.md5(
            f"{workflow_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            started_at=time.time()
        )

        # Initialize task statuses
        for task_id in workflow["tasks"]:
            execution.tasks[task_id] = TaskStatus.PENDING

        # Execute tasks in dependency order
        executed = set()
        while len(executed) < len(workflow["tasks"]):
            progress_made = False

            for task_id, task in workflow["tasks"].items():
                if task_id in executed:
                    continue

                # Check dependencies
                deps_met = all(dep in executed for dep in task.depends_on)
                if not deps_met:
                    continue

                # Execute task
                success = self._execute_task(execution, task_id, task)
                executed.add(task_id)
                progress_made = True

            if not progress_made and len(executed) < len(workflow["tasks"]):
                # Circular dependency or error
                break

        # Complete execution
        execution.completed_at = time.time()
        execution.duration_seconds = execution.completed_at - execution.started_at

        # Determine final status
        if any(s == TaskStatus.FAILED for s in execution.tasks.values()):
            execution.status = WorkflowStatus.FAILED
        else:
            execution.status = WorkflowStatus.COMPLETED

        self.executions[execution_id] = execution
        return execution

    def _execute_task(self,
                     execution: WorkflowExecution,
                     task_id: str,
                     task: WorkflowTask) -> bool:
        """Execute single task"""
        execution.tasks[task_id] = TaskStatus.RUNNING

        try:
            # Get handler
            handler = self.task_handlers.get(task.task_type)
            if handler:
                result = handler()
            else:
                # Simulate task execution
                result = self._simulate_task_execution()

            if result.get("success", False):
                execution.tasks[task_id] = TaskStatus.COMPLETED
                execution.results[task_id] = result
                return True
            else:
                raise Exception(result.get("error", "Task failed"))

        except Exception as e:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                execution.tasks[task_id] = TaskStatus.RETRY
                return self._execute_task(execution, task_id, task)
            else:
                execution.tasks[task_id] = TaskStatus.FAILED
                execution.errors.append(f"Task {task.task_name} failed: {str(e)}")
                return False

    def _simulate_task_execution(self) -> Dict:
        """Simulate task execution"""
        success = random.random() > 0.1  # 90% success
        if success:
            return {
                "success": True,
                "result": "Task completed successfully",
                "duration_ms": random.uniform(100, 1000)
            }
        else:
            return {
                "success": False,
                "error": "Task execution failed"
            }

    def get_workflow_stats(self, execution_id: str) -> Dict:
        """Get workflow statistics"""
        execution = self.executions.get(execution_id)
        if not execution:
            return {}

        total_tasks = len(execution.tasks)
        completed = sum(1 for s in execution.tasks.values() if s == TaskStatus.COMPLETED)
        failed = sum(1 for s in execution.tasks.values() if s == TaskStatus.FAILED)

        return {
            "workflow_id": execution.workflow_id,
            "status": execution.status.value,
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "duration": execution.duration_seconds,
            "success_rate": completed / max(1, total_tasks),
        }

    def generate_workflow_report(self) -> str:
        """Generate workflow report"""
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              WORKFLOW ORCHESTRATION REPORT                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 WORKFLOWS:
├─ Total Workflows: {len(self.workflows)}
└─ Executions: {len(self.executions)}

📋 RECENT EXECUTIONS:
"""

        for exec_id, execution in list(self.executions.items())[-5:]:
            stats = self.get_workflow_stats(exec_id)
            report += f"\n  {execution.workflow_id[:8]} - {execution.status.value}\n"
            report += f"    Tasks: {stats['completed']}/{stats['total_tasks']}\n"
            report += f"    Duration: {stats['duration']:.2f}s\n"

        return report

    def export_workflow_config(self) -> str:
        """Export workflow configuration"""
        export_data = {
            "timestamp": time.time(),
            "workflows": len(self.workflows),
            "executions": [
                {
                    "workflow_id": e.workflow_id,
                    "status": e.status.value,
                    "duration": e.duration_seconds,
                }
                for e in self.executions.values()
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Workflow Orchestration - Complex Workflow Management")
    print("=" * 70)

    orchestrator = WorkflowOrchestrator()

    # Create workflow
    print("\n📝 Creating workflow...")
    workflow_id = orchestrator.create_workflow("Data Processing Pipeline")
    print(f"✅ Created workflow: {workflow_id}")

    # Add tasks
    print("\n📋 Adding tasks...")
    extract_task = orchestrator.add_task(workflow_id, "Extract Data", "extract")
    transform_task = orchestrator.add_task(workflow_id, "Transform Data", "transform", [extract_task])
    validate_task = orchestrator.add_task(workflow_id, "Validate Data", "validate", [transform_task])
    load_task = orchestrator.add_task(workflow_id, "Load Data", "load", [validate_task])
    notify_task = orchestrator.add_task(workflow_id, "Send Notification", "notify", [load_task])

    print(f"✅ Added 5 tasks")

    # Register handlers
    print("\n⚙️  Registering handlers...")
    def extract_handler():
        return {"success": True, "records": 1000}

    def transform_handler():
        return {"success": True, "transformed": 1000}

    orchestrator.register_task_handler("extract", extract_handler)
    orchestrator.register_task_handler("transform", transform_handler)
    print("✅ Handlers registered")

    # Execute workflow
    print("\n🚀 Executing workflow...")
    execution = orchestrator.execute_workflow(workflow_id)
    print(f"✅ Workflow execution: {execution.status.value}")

    # Get stats
    stats = orchestrator.get_workflow_stats(execution.execution_id)
    print(f"✅ Completed: {stats['completed']}/{stats['total_tasks']} tasks")

    # Generate report
    print(orchestrator.generate_workflow_report())

    # Export
    print("\n📄 Exporting workflow config...")
    export = orchestrator.export_workflow_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Workflow orchestration ready")


if __name__ == "__main__":
    main()
