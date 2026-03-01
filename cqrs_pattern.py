#!/usr/bin/env python3
"""
CQRS Pattern Implementer - Command Query Responsibility Segregation
Separates commands (write) from queries (read) with independent data models
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
import hashlib
import json
import time
import random


class CommandType(Enum):
    """Types of commands"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRANSFER = "TRANSFER"
    PROCESS = "PROCESS"
    CUSTOM = "CUSTOM"


class CommandStatus(Enum):
    """Status of command execution"""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    PROCESSING = "PROCESSING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class Command:
    """Command (write operation)"""
    command_id: str
    command_type: CommandType
    aggregate_id: str
    aggregate_type: str
    payload: Dict[str, Any]
    issued_by: str
    issued_at: float
    status: CommandStatus = CommandStatus.RECEIVED
    result: Optional[Dict] = None
    error: Optional[str] = None
    executed_at: Optional[float] = None


@dataclass
class Query:
    """Query (read operation)"""
    query_id: str
    query_type: str
    filters: Dict[str, Any]
    sort_by: Optional[str] = None
    limit: int = 100
    offset: int = 0
    issued_at: float = field(default_factory=time.time)
    result: Optional[List[Dict]] = None
    execution_time_ms: float = 0.0


@dataclass
class ReadModel:
    """Materialized read model (denormalized)"""
    model_id: str
    model_name: str
    aggregate_type: str
    entities: Dict[str, Dict] = field(default_factory=dict)
    indexes: Dict[str, Set[str]] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)


@dataclass
class CommandHandler:
    """Handles commands"""
    handler_id: str
    command_type: CommandType
    handler_func: Callable
    validation_func: Optional[Callable] = None
    compensation_func: Optional[Callable] = None  # For rollback


@dataclass
class QueryHandler:
    """Handles queries"""
    handler_id: str
    query_type: str
    handler_func: Callable
    read_model: Optional[str] = None


class CQRSBus:
    """
    CQRS Command-Query Bus

    Provides:
    - Command execution with handlers
    - Query execution with read models
    - Eventual consistency
    - Command validation and compensation
    - Read model synchronization
    - Audit trail
    """

    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.queries: Dict[str, Query] = {}
        self.command_handlers: Dict[CommandType, CommandHandler] = {}
        self.query_handlers: Dict[str, QueryHandler] = {}
        self.read_models: Dict[str, ReadModel] = {}
        self.event_log: List[Dict] = []

    def register_command_handler(self,
                                command_type: CommandType,
                                handler: Callable,
                                validator: Optional[Callable] = None,
                                compensator: Optional[Callable] = None):
        """Register command handler"""
        handler_id = hashlib.md5(f"{command_type.value}".encode()).hexdigest()[:8]

        cmd_handler = CommandHandler(
            handler_id=handler_id,
            command_type=command_type,
            handler_func=handler,
            validation_func=validator,
            compensation_func=compensator
        )

        self.command_handlers[command_type] = cmd_handler

    def register_query_handler(self,
                              query_type: str,
                              handler: Callable,
                              read_model: Optional[str] = None):
        """Register query handler"""
        handler_id = hashlib.md5(f"{query_type}".encode()).hexdigest()[:8]

        query_handler = QueryHandler(
            handler_id=handler_id,
            query_type=query_type,
            handler_func=handler,
            read_model=read_model
        )

        self.query_handlers[query_type] = query_handler

    def execute_command(self,
                       command_type: CommandType,
                       aggregate_id: str,
                       aggregate_type: str,
                       payload: Dict,
                       issued_by: str) -> Command:
        """
        Execute command

        Args:
            command_type: Type of command
            aggregate_id: Aggregate ID
            aggregate_type: Aggregate type
            payload: Command payload
            issued_by: Command issuer

        Returns:
            Executed Command
        """
        command_id = hashlib.md5(
            f"{aggregate_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        command = Command(
            command_id=command_id,
            command_type=command_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            payload=payload,
            issued_by=issued_by,
            issued_at=time.time()
        )

        # Validate command
        handler = self.command_handlers.get(command_type)
        if not handler:
            command.status = CommandStatus.FAILED
            command.error = f"No handler for {command_type.value}"
            self.commands[command_id] = command
            return command

        # Run validation
        if handler.validation_func:
            try:
                is_valid = handler.validation_func(command)
                if not is_valid:
                    command.status = CommandStatus.FAILED
                    command.error = "Command validation failed"
                    self.commands[command_id] = command
                    return command
            except Exception as e:
                command.status = CommandStatus.FAILED
                command.error = str(e)
                self.commands[command_id] = command
                return command

        command.status = CommandStatus.VALIDATED

        # Execute command
        try:
            command.status = CommandStatus.PROCESSING
            result = handler.handler_func(command)
            command.status = CommandStatus.EXECUTED
            command.result = result
            command.executed_at = time.time()

            # Log event
            self._log_event("COMMAND_EXECUTED", {
                "command_id": command_id,
                "command_type": command_type.value,
                "result": result
            })

        except Exception as e:
            command.status = CommandStatus.FAILED
            command.error = str(e)

            # Attempt compensation
            if handler.compensation_func:
                try:
                    handler.compensation_func(command)
                    command.status = CommandStatus.ROLLED_BACK
                except Exception as comp_error:
                    command.error = f"Rollback failed: {comp_error}"

        self.commands[command_id] = command
        return command

    def execute_query(self,
                     query_type: str,
                     filters: Dict = None,
                     sort_by: Optional[str] = None,
                     limit: int = 100,
                     offset: int = 0) -> Query:
        """
        Execute query

        Args:
            query_type: Type of query
            filters: Filter conditions
            sort_by: Sort field
            limit: Result limit
            offset: Result offset

        Returns:
            Query with results
        """
        query_id = hashlib.md5(
            f"{query_type}:{time.time()}".encode()
        ).hexdigest()[:8]

        query = Query(
            query_id=query_id,
            query_type=query_type,
            filters=filters or {},
            sort_by=sort_by,
            limit=limit,
            offset=offset
        )

        handler = self.query_handlers.get(query_type)
        if not handler:
            return query

        # Execute query
        start_time = time.time()
        try:
            result = handler.handler_func(query)
            query.result = result
        except Exception as e:
            query.result = []

        query.execution_time_ms = (time.time() - start_time) * 1000

        self.queries[query_id] = query
        return query

    def create_read_model(self, name: str, aggregate_type: str) -> ReadModel:
        """Create read model"""
        model_id = hashlib.md5(f"{name}".encode()).hexdigest()[:8]

        model = ReadModel(
            model_id=model_id,
            model_name=name,
            aggregate_type=aggregate_type
        )

        self.read_models[model_id] = model
        return model

    def update_read_model(self,
                         model_id: str,
                         entity_id: str,
                         data: Dict):
        """Update read model with entity data"""
        model = self.read_models.get(model_id)
        if not model:
            return

        model.entities[entity_id] = data
        model.last_updated = time.time()

        # Update indexes
        for key, value in data.items():
            if key not in model.indexes:
                model.indexes[key] = set()
            model.indexes[key].add(entity_id)

    def synchronize_read_models(self):
        """Synchronize all read models"""
        # Simulate synchronization of read models from command side
        for model in self.read_models.values():
            model.last_updated = time.time()
            self._log_event("READ_MODEL_SYNCHRONIZED", {
                "model_id": model.model_id,
                "entity_count": len(model.entities)
            })

    def get_command_history(self, aggregate_id: str) -> List[Command]:
        """Get command history for aggregate"""
        return [c for c in self.commands.values() if c.aggregate_id == aggregate_id]

    def _log_event(self, event_type: str, data: Dict):
        """Log event to audit trail"""
        self.event_log.append({
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        })

    def generate_cqrs_report(self) -> str:
        """Generate CQRS system report"""
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                         CQRS SYSTEM REPORT                                 ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Commands Executed: {len(self.commands)}
├─ Successful Commands: {sum(1 for c in self.commands.values() if c.status == CommandStatus.EXECUTED)}
├─ Failed Commands: {sum(1 for c in self.commands.values() if c.status == CommandStatus.FAILED)}
├─ Total Queries: {len(self.queries)}
├─ Read Models: {len(self.read_models)}
└─ Events Logged: {len(self.event_log)}

⚙️  COMMAND HANDLERS: {len(self.command_handlers)}
"""

        for cmd_type, handler in self.command_handlers.items():
            report += f"  • {cmd_type.value}\n"

        report += f"\n📖 QUERY HANDLERS: {len(self.query_handlers)}\n"
        for query_type, handler in self.query_handlers.items():
            report += f"  • {query_type}\n"

        report += f"\n📚 READ MODELS:\n"
        for model in self.read_models.values():
            report += f"  • {model.model_name}: {len(model.entities)} entities\n"

        report += f"\n📋 RECENT COMMANDS:\n"
        for cmd in list(self.commands.values())[-5:]:
            status_emoji = "✅" if cmd.status == CommandStatus.EXECUTED else "❌"
            report += f"{status_emoji} {cmd.command_type.value}: {cmd.status.value}\n"

        return report

    def export_cqrs_state(self) -> str:
        """Export CQRS state as JSON"""
        export_data = {
            "timestamp": time.time(),
            "commands": {
                "total": len(self.commands),
                "executed": sum(1 for c in self.commands.values() if c.status == CommandStatus.EXECUTED),
                "failed": sum(1 for c in self.commands.values() if c.status == CommandStatus.FAILED),
            },
            "queries": {
                "total": len(self.queries),
                "avg_execution_time_ms": (
                    sum(q.execution_time_ms for q in self.queries.values()) / len(self.queries)
                    if self.queries else 0
                ),
            },
            "read_models": {
                model_id: {
                    "name": model.model_name,
                    "entities": len(model.entities),
                    "last_updated": model.last_updated,
                }
                for model_id, model in self.read_models.items()
            },
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 CQRS Pattern Implementer - Command Query Separation")
    print("=" * 70)

    bus = CQRSBus()

    # Register command handlers
    print("\n⚙️  Registering command handlers...")

    def create_user_handler(cmd: Command) -> Dict:
        return {"user_id": cmd.aggregate_id, "created": True}

    def validate_create_user(cmd: Command) -> bool:
        return "email" in cmd.payload and "name" in cmd.payload

    bus.register_command_handler(
        CommandType.CREATE,
        create_user_handler,
        validate_create_user
    )

    def update_user_handler(cmd: Command) -> Dict:
        return {"user_id": cmd.aggregate_id, "updated": True}

    bus.register_command_handler(
        CommandType.UPDATE,
        update_user_handler
    )

    print(f"✅ Registered {len(bus.command_handlers)} command handlers")

    # Register query handlers
    print("\n🔍 Registering query handlers...")

    def get_users_handler(query: Query) -> List[Dict]:
        return [
            {"user_id": f"user_{i}", "name": f"User {i}", "email": f"user{i}@example.com"}
            for i in range(min(query.limit, 10))
        ]

    bus.register_query_handler("GetUsers", get_users_handler)

    def get_user_handler(query: Query) -> List[Dict]:
        user_id = query.filters.get("user_id")
        return [{"user_id": user_id, "name": "John", "email": "john@example.com"}] if user_id else []

    bus.register_query_handler("GetUserById", get_user_handler)

    print(f"✅ Registered {len(bus.query_handlers)} query handlers")

    # Create read models
    print("\n📚 Creating read models...")
    user_model = bus.create_read_model("UserReadModel", "User")
    print(f"✅ Created read model")

    # Execute commands
    print("\n✍️  Executing commands...")
    cmd1 = bus.execute_command(
        CommandType.CREATE,
        "user_123",
        "User",
        {"name": "John Doe", "email": "john@example.com"},
        "admin@system.com"
    )
    print(f"Command Status: {cmd1.status.value}")

    # Update read model
    bus.update_read_model(
        user_model.model_id,
        "user_123",
        {"name": "John Doe", "email": "john@example.com"}
    )

    cmd2 = bus.execute_command(
        CommandType.UPDATE,
        "user_123",
        "User",
        {"email": "john.doe@example.com"},
        "john@example.com"
    )
    print(f"Command Status: {cmd2.status.value}")

    # Execute queries
    print("\n🔎 Executing queries...")
    query1 = bus.execute_query("GetUsers")
    print(f"Query Results: {len(query1.result) if query1.result else 0} users")
    print(f"Execution Time: {query1.execution_time_ms:.2f}ms")

    query2 = bus.execute_query("GetUserById", {"user_id": "user_123"})
    print(f"Query Results: {len(query2.result) if query2.result else 0} user")

    # Synchronize read models
    print("\n🔄 Synchronizing read models...")
    bus.synchronize_read_models()
    print(f"✅ Read models synchronized")

    # Generate report
    print(bus.generate_cqrs_report())

    # Export
    print("\n📄 Exporting CQRS state...")
    export = bus.export_cqrs_state()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ CQRS implementation ready")


if __name__ == "__main__":
    main()
