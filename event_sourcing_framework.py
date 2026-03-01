#!/usr/bin/env python3
"""
Event Sourcing Framework - Event-driven architecture implementation
Implements event sourcing pattern with event store, replay capability, and snapshots
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class EventType(Enum):
    """Event types"""
    ENTITY_CREATED = "ENTITY_CREATED"
    ENTITY_UPDATED = "ENTITY_UPDATED"
    ENTITY_DELETED = "ENTITY_DELETED"
    STATE_CHANGED = "STATE_CHANGED"
    ACTION_PERFORMED = "ACTION_PERFORMED"


@dataclass
class Event:
    """Domain event"""
    event_id: str
    event_type: EventType
    aggregate_id: str
    aggregate_type: str
    timestamp: float
    version: int
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Snapshot:
    """Aggregate snapshot"""
    snapshot_id: str
    aggregate_id: str
    aggregate_type: str
    version: int
    state: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class AggregateRoot:
    """Aggregate root"""
    aggregate_id: str
    aggregate_type: str
    version: int
    state: Dict[str, Any] = field(default_factory=dict)
    uncommitted_events: List[Event] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class EventSourcingFramework:
    """
    Event Sourcing Framework

    Provides:
    - Event store implementation
    - Event append-only log
    - Event replay
    - Snapshots
    - Event subscriptions
    - Temporal queries
    """

    def __init__(self):
        self.event_store: List[Event] = []
        self.aggregates: Dict[str, AggregateRoot] = {}
        self.snapshots: Dict[str, Snapshot] = {}
        self.event_subscriptions: List[Dict] = []
        self.projections: Dict[str, Dict] = {}

    def append_event(self,
                    event_type: EventType,
                    aggregate_id: str,
                    aggregate_type: str,
                    payload: Dict[str, Any],
                    version: int = 1) -> Event:
        """Append event to store"""
        event_id = hashlib.md5(
            f"{aggregate_id}:{len(self.event_store)}:{time.time()}".encode()
        ).hexdigest()[:8]

        event = Event(
            event_id=event_id,
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            timestamp=time.time(),
            version=version,
            payload=payload,
            metadata={"source": "event_sourcing"}
        )

        self.event_store.append(event)
        self._notify_subscribers(event)

        return event

    def create_aggregate(self,
                        aggregate_id: str,
                        aggregate_type: str,
                        initial_state: Dict[str, Any]) -> AggregateRoot:
        """Create new aggregate"""
        aggregate = AggregateRoot(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            version=1,
            state=initial_state
        )

        self.aggregates[aggregate_id] = aggregate

        # Append creation event
        self.append_event(
            EventType.ENTITY_CREATED,
            aggregate_id,
            aggregate_type,
            initial_state,
            version=1
        )

        return aggregate

    def update_aggregate(self,
                        aggregate_id: str,
                        changes: Dict[str, Any]) -> Optional[AggregateRoot]:
        """Update aggregate with new changes"""
        aggregate = self.aggregates.get(aggregate_id)
        if not aggregate:
            return None

        aggregate.state.update(changes)
        aggregate.version += 1

        # Append update event
        self.append_event(
            EventType.ENTITY_UPDATED,
            aggregate_id,
            aggregate.aggregate_type,
            changes,
            version=aggregate.version
        )

        return aggregate

    def delete_aggregate(self, aggregate_id: str) -> bool:
        """Delete aggregate"""
        aggregate = self.aggregates.get(aggregate_id)
        if not aggregate:
            return False

        aggregate.version += 1

        # Append deletion event
        self.append_event(
            EventType.ENTITY_DELETED,
            aggregate_id,
            aggregate.aggregate_type,
            {"deleted": True},
            version=aggregate.version
        )

        # Remove from active aggregates
        del self.aggregates[aggregate_id]
        return True

    def create_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Create snapshot of aggregate"""
        aggregate = self.aggregates.get(aggregate_id)
        if not aggregate:
            return None

        snapshot_id = hashlib.md5(
            f"{aggregate_id}:{aggregate.version}:{time.time()}".encode()
        ).hexdigest()[:8]

        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate.aggregate_type,
            version=aggregate.version,
            state=aggregate.state.copy()
        )

        self.snapshots[aggregate_id] = snapshot
        return snapshot

    def replay_events(self,
                     aggregate_id: str,
                     from_version: int = 0) -> Optional[AggregateRoot]:
        """Replay events to reconstruct aggregate"""
        events = [e for e in self.event_store
                 if e.aggregate_id == aggregate_id and
                 e.version > from_version]

        if not events:
            return None

        # Check for snapshot
        snapshot = self.snapshots.get(aggregate_id)
        if snapshot and snapshot.version >= from_version:
            aggregate = AggregateRoot(
                aggregate_id=aggregate_id,
                aggregate_type=snapshot.aggregate_type,
                version=snapshot.version,
                state=snapshot.state.copy()
            )
            # Only replay events after snapshot
            events = [e for e in events if e.version > snapshot.version]
        else:
            # Start from first event
            if events:
                first_event = events[0]
                aggregate = AggregateRoot(
                    aggregate_id=aggregate_id,
                    aggregate_type=first_event.aggregate_type,
                    version=0,
                    state={}
                )
            else:
                return None

        # Apply events
        for event in events:
            aggregate.state.update(event.payload)
            aggregate.version = event.version

        return aggregate

    def subscribe_to_events(self,
                           event_type: EventType,
                           handler_name: str) -> str:
        """Subscribe to event type"""
        subscription_id = hashlib.md5(
            f"{event_type.value}:{handler_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        subscription = {
            "subscription_id": subscription_id,
            "event_type": event_type,
            "handler_name": handler_name,
            "subscribed_at": time.time()
        }

        self.event_subscriptions.append(subscription)
        return subscription_id

    def _notify_subscribers(self, event: Event):
        """Notify subscribers of new event"""
        for subscription in self.event_subscriptions:
            if subscription["event_type"] == event.event_type:
                # In real implementation, call handler
                pass

    def build_projection(self,
                        projection_name: str,
                        aggregate_type: str) -> Dict:
        """Build projection from events"""
        projection = {
            "name": projection_name,
            "aggregate_type": aggregate_type,
            "items": []
        }

        events = [e for e in self.event_store
                 if e.aggregate_type == aggregate_type]

        # Group by aggregate
        aggregates_map = {}
        for event in events:
            agg_id = event.aggregate_id
            if agg_id not in aggregates_map:
                aggregates_map[agg_id] = {"id": agg_id, "state": {}}

            aggregates_map[agg_id]["state"].update(event.payload)

        projection["items"] = list(aggregates_map.values())
        self.projections[projection_name] = projection

        return projection

    def get_event_history(self, aggregate_id: str) -> List[Event]:
        """Get event history for aggregate"""
        return [e for e in self.event_store
               if e.aggregate_id == aggregate_id]

    def get_sourcing_stats(self) -> Dict:
        """Get event sourcing statistics"""
        total_events = len(self.event_store)
        total_aggregates = len(self.aggregates)

        by_type = {}
        for event in self.event_store:
            type_name = event.event_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

        by_aggregate_type = {}
        for aggregate in self.aggregates.values():
            agg_type = aggregate.aggregate_type
            by_aggregate_type[agg_type] = by_aggregate_type.get(agg_type, 0) + 1

        return {
            "total_events": total_events,
            "total_aggregates": total_aggregates,
            "by_event_type": by_type,
            "by_aggregate_type": by_aggregate_type,
            "snapshots": len(self.snapshots),
            "projections": len(self.projections),
            "subscriptions": len(self.event_subscriptions),
        }

    def generate_sourcing_report(self) -> str:
        """Generate event sourcing report"""
        stats = self.get_sourcing_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              EVENT SOURCING FRAMEWORK REPORT                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Events: {stats['total_events']}
├─ Total Aggregates: {stats['total_aggregates']}
├─ Snapshots: {stats['snapshots']}
├─ Projections: {stats['projections']}
├─ Subscriptions: {stats['subscriptions']}
└─ Aggregate Types: {len(stats['by_aggregate_type'])}

📝 BY EVENT TYPE:
"""

        for event_type, count in stats['by_event_type'].items():
            report += f"  {event_type}: {count}\n"

        report += f"\n📦 BY AGGREGATE TYPE:\n"
        for agg_type, count in stats['by_aggregate_type'].items():
            report += f"  {agg_type}: {count}\n"

        return report

    def export_sourcing_config(self) -> str:
        """Export event sourcing configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_sourcing_stats(),
            "aggregates": [
                {
                    "id": a.aggregate_id,
                    "type": a.aggregate_type,
                    "version": a.version,
                }
                for a in self.aggregates.values()
            ],
            "recent_events": [
                {
                    "event_id": e.event_id,
                    "type": e.event_type.value,
                    "aggregate_id": e.aggregate_id,
                    "version": e.version,
                }
                for e in self.event_store[-20:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("⚙️  Event Sourcing Framework - Event-Driven Architecture")
    print("=" * 70)

    framework = EventSourcingFramework()

    # Create aggregates
    print("\n🏗️  Creating aggregates...")
    user1 = framework.create_aggregate(
        "user_001", "User",
        {"name": "Alice", "email": "alice@example.com", "status": "active"}
    )
    order1 = framework.create_aggregate(
        "order_001", "Order",
        {"user_id": "user_001", "total": 100.0, "status": "pending"}
    )
    print(f"✅ Created {len(framework.aggregates)} aggregates")

    # Update aggregates
    print("\n📝 Updating aggregates...")
    framework.update_aggregate("user_001", {"status": "verified"})
    framework.update_aggregate("order_001", {"status": "confirmed"})
    print(f"✅ Updated aggregates, total events: {len(framework.event_store)}")

    # Create snapshots
    print("\n📸 Creating snapshots...")
    snap1 = framework.create_snapshot("user_001")
    snap2 = framework.create_snapshot("order_001")
    print(f"✅ Created {len(framework.snapshots)} snapshots")

    # Replay events
    print("\n▶️  Replaying events...")
    replayed_user = framework.replay_events("user_001")
    if replayed_user:
        print(f"✅ Replayed user aggregate: version {replayed_user.version}")

    # Subscribe to events
    print("\n🔔 Subscribing to events...")
    framework.subscribe_to_events(EventType.ENTITY_UPDATED, "email_notifier")
    framework.subscribe_to_events(EventType.ENTITY_CREATED, "audit_logger")
    print(f"✅ Created {len(framework.event_subscriptions)} subscriptions")

    # Build projections
    print("\n🔄 Building projections...")
    user_projection = framework.build_projection("user_view", "User")
    order_projection = framework.build_projection("order_view", "Order")
    print(f"✅ Built {len(framework.projections)} projections")

    # Generate report
    print(framework.generate_sourcing_report())

    # Export
    print("\n📄 Exporting sourcing config...")
    export = framework.export_sourcing_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Event sourcing framework ready")


if __name__ == "__main__":
    main()
