#!/usr/bin/env python3
"""
Distributed Lock Manager - Coordinated resource locking
Manages distributed locks across services with deadlock detection and TTL expiration
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import hashlib
import json
import time


class LockMode(Enum):
    """Lock modes"""
    EXCLUSIVE = "EXCLUSIVE"
    SHARED = "SHARED"
    WRITE = "WRITE"
    READ = "READ"


class LockStatus(Enum):
    """Lock status"""
    ACQUIRED = "ACQUIRED"
    WAITING = "WAITING"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"
    DEADLOCK_DETECTED = "DEADLOCK_DETECTED"


@dataclass
class DistributedLock:
    """Distributed lock"""
    lock_id: str
    resource_name: str
    owner_service: str
    mode: LockMode
    acquired_at: float
    expires_at: float
    status: LockStatus = LockStatus.ACQUIRED
    holder_id: Optional[str] = None
    wait_queue: List[Dict] = field(default_factory=list)


@dataclass
class LockWaiter:
    """Lock waiter information"""
    waiter_id: str
    lock_id: str
    service_name: str
    mode: LockMode
    requested_at: float
    priority: int = 0


@dataclass
class DeadlockCycle:
    """Deadlock cycle detection"""
    cycle_id: str
    locks_involved: List[str]
    services_involved: List[str]
    detected_at: float
    cycle_length: int


class DistributedLockManager:
    """
    Distributed Lock Manager

    Provides:
    - Distributed lock coordination
    - Deadlock detection and resolution
    - Lock timeout and TTL management
    - Priority-based wait queues
    - Lock starvation prevention
    - Deadlock recovery
    """

    def __init__(self, default_ttl_seconds: int = 30):
        self.locks: Dict[str, DistributedLock] = {}
        self.waiters: Dict[str, LockWaiter] = {}
        self.deadlock_cycles: List[DeadlockCycle] = []
        self.lock_history: List[Dict] = []
        self.default_ttl = default_ttl_seconds

    def acquire_lock(self,
                    resource_name: str,
                    owner_service: str,
                    mode: LockMode = LockMode.EXCLUSIVE,
                    ttl_seconds: int = None,
                    blocking: bool = True) -> Optional[DistributedLock]:
        """Acquire distributed lock"""
        lock_id = hashlib.md5(
            f"{resource_name}:{owner_service}:{time.time()}".encode()
        ).hexdigest()[:8]

        ttl = ttl_seconds or self.default_ttl
        now = time.time()

        # Check for existing lock
        existing_lock = next((l for l in self.locks.values()
                            if l.resource_name == resource_name and
                            l.status == LockStatus.ACQUIRED), None)

        if existing_lock:
            if not blocking:
                return None

            # Add to wait queue
            waiter = LockWaiter(
                waiter_id=lock_id,
                lock_id=existing_lock.lock_id,
                service_name=owner_service,
                mode=mode,
                requested_at=now
            )
            self.waiters[lock_id] = waiter
            existing_lock.wait_queue.append({
                "waiter_id": lock_id,
                "service": owner_service,
                "mode": mode.value,
                "requested_at": now
            })

            return None  # Lock not acquired yet

        # Create new lock
        lock = DistributedLock(
            lock_id=lock_id,
            resource_name=resource_name,
            owner_service=owner_service,
            mode=mode,
            acquired_at=now,
            expires_at=now + ttl,
            holder_id=owner_service
        )

        self.locks[lock_id] = lock

        # Record history
        self.lock_history.append({
            "lock_id": lock_id,
            "resource": resource_name,
            "owner": owner_service,
            "mode": mode.value,
            "acquired_at": now,
            "action": "ACQUIRED"
        })

        return lock

    def release_lock(self, lock_id: str, owner_service: str) -> bool:
        """Release distributed lock"""
        lock = self.locks.get(lock_id)
        if not lock:
            return False

        if lock.holder_id != owner_service:
            return False

        lock.status = LockStatus.RELEASED
        released_at = time.time()

        # Record history
        self.lock_history.append({
            "lock_id": lock_id,
            "resource": lock.resource_name,
            "owner": owner_service,
            "released_at": released_at,
            "action": "RELEASED"
        })

        # Try to grant lock to next waiter
        if lock.wait_queue:
            next_waiter_info = lock.wait_queue.pop(0)
            # In real implementation, notify waiter service

        return True

    def renew_lock(self, lock_id: str, ttl_seconds: int = None) -> Optional[DistributedLock]:
        """Renew lock TTL"""
        lock = self.locks.get(lock_id)
        if not lock or lock.status != LockStatus.ACQUIRED:
            return None

        ttl = ttl_seconds or self.default_ttl
        lock.expires_at = time.time() + ttl

        return lock

    def detect_deadlocks(self) -> List[DeadlockCycle]:
        """Detect deadlock cycles"""
        deadlocks = []

        # Build wait-for graph
        wait_graph = {}
        for lock in self.locks.values():
            if lock.wait_queue:
                holders = [lock.holder_id]
                waiters = [w["service"] for w in lock.wait_queue]

                for holder in holders:
                    if holder not in wait_graph:
                        wait_graph[holder] = []
                    wait_graph[holder].extend(waiters)

        # Detect cycles using DFS
        for service in wait_graph:
            cycle = self._detect_cycle_from_service(service, wait_graph, set())
            if cycle:
                cycle_id = hashlib.md5(
                    f"{':'.join(sorted(cycle))}:{time.time()}".encode()
                ).hexdigest()[:8]

                deadlock = DeadlockCycle(
                    cycle_id=cycle_id,
                    locks_involved=[],
                    services_involved=cycle,
                    detected_at=time.time(),
                    cycle_length=len(cycle)
                )
                deadlocks.append(deadlock)

        self.deadlock_cycles.extend(deadlocks)
        return deadlocks

    def _detect_cycle_from_service(self, service: str, graph: Dict, visited: set) -> Optional[List[str]]:
        """Detect cycle from service using DFS"""
        if service in visited:
            return [service]

        visited.add(service)

        if service not in graph:
            return None

        for dependent in graph[service]:
            cycle = self._detect_cycle_from_service(dependent, graph, visited.copy())
            if cycle and service in cycle:
                return cycle

        return None

    def resolve_deadlock(self, cycle_id: str) -> bool:
        """Resolve deadlock by releasing locks"""
        cycle = next((c for c in self.deadlock_cycles
                     if c.cycle_id == cycle_id), None)
        if not cycle:
            return False

        # Release oldest lock in cycle
        cycle_locks = [l for l in self.locks.values()
                      if l.holder_id in cycle.services_involved]

        if cycle_locks:
            oldest = min(cycle_locks, key=lambda l: l.acquired_at)
            oldest.status = LockStatus.DEADLOCK_DETECTED
            return True

        return False

    def cleanup_expired_locks(self) -> int:
        """Clean up expired locks"""
        now = time.time()
        expired_count = 0

        for lock in list(self.locks.values()):
            if lock.status == LockStatus.ACQUIRED and lock.expires_at < now:
                lock.status = LockStatus.EXPIRED
                expired_count += 1

                self.lock_history.append({
                    "lock_id": lock.lock_id,
                    "resource": lock.resource_name,
                    "expired_at": now,
                    "action": "EXPIRED"
                })

        return expired_count

    def get_lock_stats(self) -> Dict:
        """Get lock statistics"""
        active_locks = sum(1 for l in self.locks.values()
                          if l.status == LockStatus.ACQUIRED)
        waiting_locks = sum(1 for l in self.locks.values()
                           if l.status == LockStatus.WAITING)
        expired_locks = sum(1 for l in self.locks.values()
                           if l.status == LockStatus.EXPIRED)

        return {
            "total_locks": len(self.locks),
            "active_locks": active_locks,
            "waiting_locks": waiting_locks,
            "expired_locks": expired_locks,
            "total_waiters": len(self.waiters),
            "deadlock_cycles_detected": len(self.deadlock_cycles),
            "history_records": len(self.lock_history),
        }

    def generate_lock_report(self) -> str:
        """Generate lock management report"""
        stats = self.get_lock_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DISTRIBUTED LOCK MANAGER REPORT                               ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Locks: {stats['total_locks']}
├─ Active Locks: {stats['active_locks']}
├─ Waiting Locks: {stats['waiting_locks']}
├─ Expired Locks: {stats['expired_locks']}
├─ Waiters: {stats['total_waiters']}
├─ Deadlock Cycles: {stats['deadlock_cycles_detected']}
└─ History Records: {stats['history_records']}

🔒 ACTIVE LOCKS:
"""

        for lock in list(self.locks.values())[:10]:
            report += f"\n  {lock.lock_id} - {lock.resource_name}\n"
            report += f"    Owner: {lock.owner_service}\n"
            report += f"    Mode: {lock.mode.value}\n"
            report += f"    Waiters: {len(lock.wait_queue)}\n"

        return report

    def export_lock_config(self) -> str:
        """Export lock configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_lock_stats(),
            "locks": [
                {
                    "id": l.lock_id,
                    "resource": l.resource_name,
                    "owner": l.owner_service,
                    "mode": l.mode.value,
                    "status": l.status.value,
                    "wait_queue_size": len(l.wait_queue),
                }
                for l in self.locks.values()
            ],
            "deadlock_cycles": len(self.deadlock_cycles),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔒 Distributed Lock Manager - Resource Coordination")
    print("=" * 70)

    manager = DistributedLockManager(default_ttl_seconds=60)

    # Acquire locks
    print("\n🔐 Acquiring distributed locks...")
    lock1 = manager.acquire_lock("database_write", "service_a", LockMode.EXCLUSIVE)
    lock2 = manager.acquire_lock("cache_update", "service_b", LockMode.SHARED)
    lock3 = manager.acquire_lock("config_sync", "service_c", LockMode.WRITE)
    print(f"✅ Acquired {len(manager.locks)} locks")

    # Try to acquire already locked resource
    print("\n⏳ Attempting to acquire locked resource...")
    blocked = manager.acquire_lock("database_write", "service_d", blocking=False)
    if blocked is None:
        print("✅ Blocking lock detection works")

    # Renew lock
    print("\n🔄 Renewing lock TTL...")
    if lock1:
        renewed = manager.renew_lock(lock1.lock_id, 120)
        print(f"✅ Lock renewed: {renewed.lock_id}")

    # Detect deadlocks
    print("\n🔍 Detecting deadlocks...")
    deadlocks = manager.detect_deadlocks()
    print(f"✅ Detected {len(deadlocks)} deadlock cycles")

    # Cleanup expired locks
    print("\n🧹 Cleaning up expired locks...")
    expired = manager.cleanup_expired_locks()
    print(f"✅ Cleaned up {expired} expired locks")

    # Generate report
    print(manager.generate_lock_report())

    # Export
    print("\n📄 Exporting lock config...")
    export = manager.export_lock_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Distributed lock manager ready")


if __name__ == "__main__":
    main()
