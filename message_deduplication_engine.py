#!/usr/bin/env python3
"""
Message Deduplication Engine - Duplicate message detection and handling
Detects and handles duplicate messages in distributed systems with multiple strategies
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class DeduplicationType(Enum):
    """Deduplication strategies"""
    CONTENT_HASH = "CONTENT_HASH"
    MESSAGE_ID = "MESSAGE_ID"
    IDEMPOTENCY_KEY = "IDEMPOTENCY_KEY"
    TIMESTAMP_RANGE = "TIMESTAMP_RANGE"
    SEMANTIC = "SEMANTIC"


class DuplicateAction(Enum):
    """Actions for duplicates"""
    IGNORE = "IGNORE"
    PROCESS = "PROCESS"
    QUARANTINE = "QUARANTINE"
    DEDUPLICATE = "DEDUPLICATE"
    MERGE = "MERGE"


@dataclass
class Message:
    """Message with deduplication metadata"""
    message_id: str
    content_hash: str
    source: str
    destination: str
    timestamp: float
    payload: Dict[str, Any] = field(default_factory=dict)
    idempotency_key: Optional[str] = None
    is_duplicate: bool = False
    original_message_id: Optional[str] = None


@dataclass
class DeduplicationPolicy:
    """Deduplication policy"""
    policy_id: str
    dedup_type: DeduplicationType
    window_seconds: int
    action: DuplicateAction
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class DuplicateRecord:
    """Duplicate detection record"""
    record_id: str
    original_message_id: str
    duplicate_message_id: str
    detected_at: float
    dedup_strategy: DeduplicationType
    confidence: float


class MessageDeduplicationEngine:
    """
    Message Deduplication Engine

    Provides:
    - Multiple deduplication strategies
    - Content-based duplicate detection
    - ID-based deduplication
    - Time-window deduplication
    - Idempotency key tracking
    - Duplicate action handling
    """

    def __init__(self):
        self.messages: Dict[str, Message] = {}
        self.policies: Dict[str, DeduplicationPolicy] = {}
        self.duplicate_records: List[DuplicateRecord] = []
        self.dedup_cache: Dict[str, str] = {}  # hash -> message_id
        self.idempotency_cache: Dict[str, str] = {}  # idempotency_key -> message_id
        self.processing_history: List[Dict] = []

    def register_policy(self,
                       dedup_type: DeduplicationType,
                       window_seconds: int = 300,
                       action: DuplicateAction = DuplicateAction.IGNORE) -> DeduplicationPolicy:
        """Register deduplication policy"""
        policy_id = hashlib.md5(
            f"{dedup_type.value}:{window_seconds}:{time.time()}".encode()
        ).hexdigest()[:8]

        policy = DeduplicationPolicy(
            policy_id=policy_id,
            dedup_type=dedup_type,
            window_seconds=window_seconds,
            action=action
        )

        self.policies[policy_id] = policy
        return policy

    def ingest_message(self,
                      source: str,
                      destination: str,
                      payload: Dict[str, Any],
                      idempotency_key: str = None) -> Optional[Message]:
        """Ingest message and check for duplicates"""
        now = time.time()
        message_id = hashlib.md5(
            f"{source}:{destination}:{now}:{json.dumps(payload, sort_keys=True)}".encode()
        ).hexdigest()[:8]

        # Calculate content hash
        content_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:16]

        # Check for duplicates
        duplicate_info = self._detect_duplicate(
            message_id, content_hash, idempotency_key, payload, now
        )

        is_dup = duplicate_info is not None

        message = Message(
            message_id=message_id,
            content_hash=content_hash,
            source=source,
            destination=destination,
            timestamp=now,
            payload=payload,
            idempotency_key=idempotency_key,
            is_duplicate=is_dup,
            original_message_id=duplicate_info["original_id"] if duplicate_info else None
        )

        self.messages[message_id] = message

        # Update caches
        self.dedup_cache[content_hash] = message_id
        if idempotency_key:
            self.idempotency_cache[idempotency_key] = message_id

        # Record detection
        if is_dup and duplicate_info:
            dup_record = DuplicateRecord(
                record_id=hashlib.md5(f"{message_id}:{now}".encode()).hexdigest()[:8],
                original_message_id=duplicate_info["original_id"],
                duplicate_message_id=message_id,
                detected_at=now,
                dedup_strategy=duplicate_info["strategy"],
                confidence=duplicate_info["confidence"]
            )
            self.duplicate_records.append(dup_record)

        return message

    def _detect_duplicate(self,
                         message_id: str,
                         content_hash: str,
                         idempotency_key: str,
                         payload: Dict,
                         timestamp: float) -> Optional[Dict]:
        """Detect if message is duplicate"""
        now = time.time()

        # Check idempotency key
        if idempotency_key and idempotency_key in self.idempotency_cache:
            return {
                "original_id": self.idempotency_cache[idempotency_key],
                "strategy": DeduplicationType.IDEMPOTENCY_KEY,
                "confidence": 0.99
            }

        # Check content hash (within time window)
        if content_hash in self.dedup_cache:
            original_id = self.dedup_cache[content_hash]
            original_msg = self.messages.get(original_id)

            if original_msg and (now - original_msg.timestamp) < 300:  # 5 min window
                return {
                    "original_id": original_id,
                    "strategy": DeduplicationType.CONTENT_HASH,
                    "confidence": 0.95
                }

        # Check for semantic duplicates (simplified)
        for msg in list(self.messages.values())[-100:]:  # Check recent messages
            if (self._is_semantically_duplicate(payload, msg.payload) and
                (now - msg.timestamp) < 300):
                return {
                    "original_id": msg.message_id,
                    "strategy": DeduplicationType.SEMANTIC,
                    "confidence": 0.85
                }

        return None

    def _is_semantically_duplicate(self, payload1: Dict, payload2: Dict) -> bool:
        """Check for semantic duplication"""
        if payload1.get("action") != payload2.get("action"):
            return False

        if payload1.get("user_id") != payload2.get("user_id"):
            return False

        return True

    def process_message(self, message_id: str, action_override: Optional[DuplicateAction] = None) -> bool:
        """Process message based on deduplication policy"""
        message = self.messages.get(message_id)
        if not message:
            return False

        # Get applicable policy
        policy = next((p for p in self.policies.values()
                      if p.enabled), None)

        if not policy:
            return False

        action = action_override or policy.action

        if not message.is_duplicate:
            self.processing_history.append({
                "message_id": message_id,
                "action": "PROCESSED",
                "processed_at": time.time()
            })
            return True

        # Handle duplicate
        if action == DuplicateAction.IGNORE:
            self.processing_history.append({
                "message_id": message_id,
                "action": "IGNORED",
                "processed_at": time.time()
            })
            return False

        elif action == DuplicateAction.QUARANTINE:
            self.processing_history.append({
                "message_id": message_id,
                "action": "QUARANTINED",
                "processed_at": time.time()
            })
            return False

        elif action == DuplicateAction.DEDUPLICATE:
            self.processing_history.append({
                "message_id": message_id,
                "action": "DEDUPLICATED",
                "merged_with": message.original_message_id,
                "processed_at": time.time()
            })
            return True

        return False

    def get_dedup_stats(self) -> Dict:
        """Get deduplication statistics"""
        total_messages = len(self.messages)
        duplicates = sum(1 for m in self.messages.values() if m.is_duplicate)
        unique = total_messages - duplicates

        by_strategy = {}
        for dup in self.duplicate_records:
            strategy = dup.dedup_strategy.value
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1

        return {
            "total_messages": total_messages,
            "unique_messages": unique,
            "duplicates_detected": duplicates,
            "duplicate_percent": (duplicates / total_messages * 100) if total_messages > 0 else 0,
            "by_strategy": by_strategy,
            "policies": len(self.policies),
            "processed": len(self.processing_history),
        }

    def generate_dedup_report(self) -> str:
        """Generate deduplication report"""
        stats = self.get_dedup_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              MESSAGE DEDUPLICATION ENGINE REPORT                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Messages: {stats['total_messages']}
├─ Unique Messages: {stats['unique_messages']}
├─ Duplicates Detected: {stats['duplicates_detected']}
├─ Duplicate Rate: {stats['duplicate_percent']:.2f}%
├─ Policies: {stats['policies']}
└─ Processed: {stats['processed']}

🔍 BY STRATEGY:
"""

        for strategy, count in stats['by_strategy'].items():
            report += f"  {strategy}: {count}\n"

        return report

    def export_dedup_config(self) -> str:
        """Export deduplication configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_dedup_stats(),
            "policies": [
                {
                    "type": p.dedup_type.value,
                    "window_seconds": p.window_seconds,
                    "action": p.action.value,
                }
                for p in self.policies.values()
            ],
            "recent_duplicates": [
                {
                    "original": d.original_message_id,
                    "duplicate": d.duplicate_message_id,
                    "strategy": d.dedup_strategy.value,
                    "confidence": d.confidence,
                }
                for d in self.duplicate_records[-10:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Message Deduplication Engine - Duplicate Detection")
    print("=" * 70)

    engine = MessageDeduplicationEngine()

    # Register policies
    print("\n📋 Registering deduplication policies...")
    policy1 = engine.register_policy(DeduplicationType.IDEMPOTENCY_KEY, 300, DuplicateAction.IGNORE)
    policy2 = engine.register_policy(DeduplicationType.CONTENT_HASH, 300, DuplicateAction.DEDUPLICATE)
    print(f"✅ Registered {len(engine.policies)} policies")

    # Ingest messages
    print("\n📨 Ingesting messages...")
    msg1 = engine.ingest_message(
        "service_a", "service_b",
        {"action": "transfer", "amount": 100, "user_id": "user_1"},
        idempotency_key="idempotency_001"
    )

    msg2 = engine.ingest_message(
        "service_a", "service_b",
        {"action": "transfer", "amount": 100, "user_id": "user_1"},
        idempotency_key="idempotency_001"
    )

    msg3 = engine.ingest_message(
        "service_c", "service_d",
        {"action": "payment", "amount": 50, "user_id": "user_2"}
    )

    print(f"✅ Ingested {len(engine.messages)} messages")
    print(f"   Duplicates detected: {sum(1 for m in engine.messages.values() if m.is_duplicate)}")

    # Process messages
    print("\n⚙️  Processing messages...")
    if msg1:
        processed1 = engine.process_message(msg1.message_id)
        print(f"✅ Message 1 processed: {processed1}")

    if msg2:
        processed2 = engine.process_message(msg2.message_id)
        print(f"✅ Message 2 processed: {processed2}")

    # Generate report
    print(engine.generate_dedup_report())

    # Export
    print("\n📄 Exporting deduplication config...")
    export = engine.export_dedup_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Message deduplication engine ready")


if __name__ == "__main__":
    main()
