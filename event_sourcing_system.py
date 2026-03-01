#!/usr/bin/env python3
"""
Event Sourcing System - Event-driven architecture with full event history
Implements event sourcing pattern for immutable event log and state reconstruction
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Set
import hashlib
import json
import time
import random


class EventType(Enum):
    """Types of domain events"""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    ACTIVATED = "ACTIVATED"
    DEACTIVATED = "DEACTIVATED"
    TRANSFERRED = "TRANSFERRED"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    CUSTOM = "CUSTOM"


class AggregateType(Enum):
    """Types of aggregates"""
    USER = "USER"
    ORDER = "ORDER"
    PAYMENT = "PAYMENT"
    INVENTORY = "INVENTORY"
    SUBSCRIPTION = "SUBSCRIPTION"
    ACCOUNT = "ACCOUNT"


@dataclass
class DomainEvent:
    """Immutable domain event"""
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: AggregateType
    timestamp: float
    data: Dict[str, Any]
    version: int
    actor: str  # Who triggered the event
    metadata: Dict = field(default_factory=dict)
    correlation_id: Optional[str] = None


@dataclass
class EventSnapshot:
    """Snapshot of aggregate state"""
    aggregate_id: str
    aggregate_type: AggregateType
    version: int
    state: Dict[str, Any]
    timestamp: float
    created_at: float


@dataclass
class EventStream:
    """Stream of events for an aggregate"""
    stream_id: str
    aggregate_id: str
    aggregate_type: AggregateType
    events: List[DomainEvent] = field(default_factory=list)
    snapshots: List[EventSnapshot] = field(default_factory=list)
    version: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class ProjectionState:
    """Materialized view (projection)"""
    projection_id: str
    projection_name: str
    aggregate_type: AggregateType
    data: Dict[str, Any] = field(default_factory=dict)
    last_updated: float = field(default_factory=time.time)
    event_version: int = 0


@dataclass
class Replay:
    """Event replay operation"""
    replay_id: str
    from_event_id: Optional[str]
    to_event_id: Optional[str]
    target_aggregate: Optional[str]
    started_at: float
    completed_at: Optional[float] = None
    events_replayed: int = 0
    status: str = "PENDING"  # PENDING, IN_PROGRESS, COMPLETED


class EventStore:
    """
    Event sourcing and event store implementation

    Provides:
    - Immutable event log
    - Event replay and reconstruction
    - Snapshot support
    - Projections (materialized views)
    - Event versioning
    - Audit trail
    - Time travel queries
    """

    def __init__(self):
        self.events: Dict[str, DomainEvent] = {}
        self.event_streams: Dict[str, EventStream] = {}
        self.snapshots: Dict[str, EventSnapshot] = {}
        self.projections: Dict[str, ProjectionState] = {}
        self.replays: List[Replay] = []
        self.subscribers: Dict[EventType, List[Callable]] = {}

    def append_event(self,
                    aggregate_id: str,
                    aggregate_type: AggregateType,
                    event_type: EventType,
                    data: Dict,
                    actor: str,
                    correlation_id: Optional[str] = None) -> DomainEvent:
        """
        Append event to event store

        Args:
            aggregate_id: ID of aggregate
            aggregate_type: Type of aggregate
            event_type: Type of event
            data: Event data
            actor: Actor performing action
            correlation_id: Correlation ID for tracing

        Returns:
            Appended DomainEvent
        """
        event_id = hashlib.md5(
            f"{aggregate_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:8]

        # Get or create event stream
        stream_id = f"{aggregate_type.value}#{aggregate_id}"
        if stream_id not in self.event_streams:
            self.event_streams[stream_id] = EventStream(
                stream_id=stream_id,
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type
            )

        stream = self.event_streams[stream_id]
        version = stream.version + 1

        event = DomainEvent(
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            timestamp=time.time(),
            data=data,
            version=version,
            actor=actor,
            correlation_id=correlation_id
        )

        stream.events.append(event)
        stream.version = version
        self.events[event_id] = event

        # Notify subscribers
        self._notify_subscribers(event)

        return event

    def _notify_subscribers(self, event: DomainEvent):
        """Notify subscribers of event"""
        if event.event_type in self.subscribers:
            for subscriber in self.subscribers[event.event_type]:
                try:
                    subscriber(event)
                except Exception as e:
                    print(f"Error notifying subscriber: {e}")

    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def get_aggregate_state(self, aggregate_id: str, aggregate_type: AggregateType) -> Dict:
        """
        Reconstruct aggregate state from events

        Args:
            aggregate_id: Aggregate ID
            aggregate_type: Aggregate type

        Returns:
            Current state of aggregate
        """
        stream_id = f"{aggregate_type.value}#{aggregate_id}"
        stream = self.event_streams.get(stream_id)

        if not stream:
            return {}

        # Check for latest snapshot
        latest_snapshot = None
        if stream.snapshots:
            latest_snapshot = stream.snapshots[-1]

        # Start from snapshot if exists
        state = latest_snapshot.state.copy() if latest_snapshot else {}
        start_version = latest_snapshot.version + 1 if latest_snapshot else 0

        # Replay events
        for event in stream.events:
            if event.version >= start_version:
                state = self._apply_event(state, event)

        return state

    def _apply_event(self, state: Dict, event: DomainEvent) -> Dict:
        """Apply event to state"""
        if event.event_type == EventType.CREATED:
            state = event.data.copy()
        elif event.event_type == EventType.UPDATED:
            state.update(event.data)
        elif event.event_type == EventType.DELETED:
            state["deleted"] = True
            state["deleted_at"] = event.timestamp
        elif event.event_type == EventType.ACTIVATED:
            state["active"] = True
        elif event.event_type == EventType.DEACTIVATED:
            state["active"] = False
        else:
            # Apply custom data
            state.update(event.data)

        state["version"] = event.version
        state["last_modified"] = event.timestamp

        return state

    def create_snapshot(self,
                       aggregate_id: str,
                       aggregate_type: AggregateType) -> Optional[EventSnapshot]:
        """
        Create snapshot of aggregate state

        Args:
            aggregate_id: Aggregate ID
            aggregate_type: Aggregate type

        Returns:
            Created EventSnapshot
        """
        stream_id = f"{aggregate_type.value}#{aggregate_id}"
        stream = self.event_streams.get(stream_id)

        if not stream:
            return None

        state = self.get_aggregate_state(aggregate_id, aggregate_type)

        snapshot = EventSnapshot(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            version=stream.version,
            state=state,
            timestamp=time.time(),
            created_at=time.time()
        )

        stream.snapshots.append(snapshot)
        self.snapshots[f"{aggregate_type.value}#{aggregate_id}"] = snapshot

        return snapshot

    def update_projection(self,
                         projection_name: str,
                         aggregate_type: AggregateType,
                         event: DomainEvent):
        """
        Update materialized view projection

        Args:
            projection_name: Name of projection
            aggregate_type: Aggregate type
            event: Triggering event
        """
        projection_id = f"{aggregate_type.value}#{projection_name}"

        if projection_id not in self.projections:
            self.projections[projection_id] = ProjectionState(
                projection_id=projection_id,
                projection_name=projection_name,
                aggregate_type=aggregate_type
            )

        projection = self.projections[projection_id]

        # Update projection based on event
        if event.aggregate_id not in projection.data:
            projection.data[event.aggregate_id] = {}

        projection.data[event.aggregate_id].update(event.data)
        projection.last_updated = time.time()
        projection.event_version = event.version

    def replay_events(self,
                     from_event: Optional[str] = None,
                     to_event: Optional[str] = None,
                     aggregate_id: Optional[str] = None) -> Replay:
        """
        Replay events

        Args:
            from_event: Start event ID
            to_event: End event ID
            aggregate_id: Target aggregate

        Returns:
            Replay operation record
        """
        replay_id = hashlib.md5(f"{time.time()}".encode()).hexdigest()[:8]

        replay = Replay(
            replay_id=replay_id,
            from_event_id=from_event,
            to_event_id=to_event,
            target_aggregate=aggregate_id,
            started_at=time.time(),
            status="IN_PROGRESS"
        )

        # Simulate event replay
        events_to_replay = []
        for event in self.events.values():
            if aggregate_id and event.aggregate_id != aggregate_id:
                continue
            if from_event and event.event_id < from_event:
                continue
            if to_event and event.event_id > to_event:
                continue
            events_to_replay.append(event)

        # Reprocess events
        for event in sorted(events_to_replay, key=lambda e: e.timestamp):
            self._notify_subscribers(event)
            replay.events_replayed += 1

        replay.completed_at = time.time()
        replay.status = "COMPLETED"

        self.replays.append(replay)
        return replay

    def get_event_history(self,
                         aggregate_id: str,
                         aggregate_type: AggregateType) -> List[DomainEvent]:
        """Get complete event history"""
        stream_id = f"{aggregate_type.value}#{aggregate_id}"
        stream = self.event_streams.get(stream_id)

        if not stream:
            return []

        return sorted(stream.events, key=lambda e: e.timestamp)

    def get_events_by_type(self, event_type: EventType) -> List[DomainEvent]:
        """Get all events of specific type"""
        return [e for e in self.events.values() if e.event_type == event_type]

    def generate_audit_trail(self, aggregate_id: str, aggregate_type: AggregateType) -> str:
        """Generate audit trail"""
        history = self.get_event_history(aggregate_id, aggregate_type)

        trail = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                           EVENT AUDIT TRAIL                                ║
║                           {aggregate_type.value}#{aggregate_id}                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 EVENT HISTORY ({len(history)} events):

"""

        for event in history:
            trail += f"\n{event.event_id} - {event.event_type.value}\n"
            trail += f"  Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event.timestamp))}\n"
            trail += f"  Actor: {event.actor}\n"
            trail += f"  Version: {event.version}\n"
            trail += f"  Data: {json.dumps(event.data, indent=4)}\n"

        return trail

    def export_event_store(self) -> str:
        """Export event store as JSON"""
        export_data = {
            "timestamp": time.time(),
            "total_events": len(self.events),
            "event_streams": len(self.event_streams),
            "projections": len(self.projections),
            "events": [
                {
                    "event_id": e.event_id,
                    "type": e.event_type.value,
                    "aggregate": f"{e.aggregate_type.value}#{e.aggregate_id}",
                    "version": e.version,
                    "timestamp": e.timestamp,
                }
                for e in sorted(self.events.values(), key=lambda x: x.timestamp)[-100:]
            ]
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📚 Event Sourcing System - Event-Driven Architecture")
    print("=" * 70)

    event_store = EventStore()

    # Setup projection subscriber
    def update_user_projection(event: DomainEvent):
        event_store.update_projection("user_details", AggregateType.USER, event)

    event_store.subscribe(EventType.CREATED, update_user_projection)
    event_store.subscribe(EventType.UPDATED, update_user_projection)

    # Create user events
    print("\n📝 Creating user events...")
    user_id = "user_123"

    event1 = event_store.append_event(
        user_id, AggregateType.USER, EventType.CREATED,
        {"name": "John Doe", "email": "john@example.com", "status": "active"},
        "admin@system.com",
        correlation_id="txn_001"
    )
    print(f"✅ Created user: {event1.event_id}")

    event2 = event_store.append_event(
        user_id, AggregateType.USER, EventType.UPDATED,
        {"email": "john.doe@example.com"},
        "john@example.com"
    )
    print(f"✅ Updated user: {event2.event_id}")

    event3 = event_store.append_event(
        user_id, AggregateType.USER, EventType.ACTIVATED,
        {"activated_at": time.time()},
        "admin@system.com"
    )
    print(f"✅ Activated user: {event3.event_id}")

    # Reconstruct state
    print("\n🔄 Reconstructing aggregate state...")
    state = event_store.get_aggregate_state(user_id, AggregateType.USER)
    print(f"Current State: {json.dumps(state, indent=2)}")

    # Create snapshot
    print("\n📸 Creating snapshot...")
    snapshot = event_store.create_snapshot(user_id, AggregateType.USER)
    print(f"✅ Snapshot created at version {snapshot.version}")

    # Generate audit trail
    print(event_store.generate_audit_trail(user_id, AggregateType.USER))

    # Export
    print("\n📄 Exporting event store...")
    export = event_store.export_event_store()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Event sourcing system ready")


if __name__ == "__main__":
    main()
