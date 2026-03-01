#!/usr/bin/env python3
"""
WebSocket Manager - Real-time communication infrastructure management
Manages WebSocket connections, pub/sub channels, and connection pooling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Optional, Callable
import hashlib
import json
import time
import random


class ConnectionState(Enum):
    """WebSocket connection states"""
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    AUTHENTICATING = "AUTHENTICATING"
    AUTHENTICATED = "AUTHENTICATED"
    RECONNECTING = "RECONNECTING"
    CLOSED = "CLOSED"
    ERROR = "ERROR"


class MessagePriority(Enum):
    """Message priority levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


class SubscriptionType(Enum):
    """Types of subscriptions"""
    BROADCAST = "BROADCAST"
    USER_SPECIFIC = "USER_SPECIFIC"
    GROUP = "GROUP"
    ROOM = "ROOM"
    TOPIC = "TOPIC"


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection"""
    connection_id: str
    client_id: str
    user_id: Optional[str]
    state: ConnectionState
    created_at: float
    last_activity: float
    subscriptions: Set[str] = field(default_factory=set)
    ip_address: str = ""
    user_agent: str = ""
    authenticated: bool = False
    auth_token: Optional[str] = None
    latency_ms: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0


@dataclass
class WebSocketMessage:
    """WebSocket message"""
    message_id: str
    sender_id: str
    channel: str
    data: Dict
    priority: MessagePriority
    timestamp: float
    ack_required: bool = False
    ack_timeout: int = 30  # seconds
    ttl: int = 3600  # Time to live in seconds


@dataclass
class Channel:
    """WebSocket channel/subscription"""
    channel_id: str
    channel_name: str
    channel_type: SubscriptionType
    created_at: float
    subscribers: Set[str] = field(default_factory=set)  # Connection IDs
    message_count: int = 0
    max_subscribers: Optional[int] = None
    retention_seconds: int = 3600
    encryption_enabled: bool = False


@dataclass
class ConnectionMetrics:
    """Metrics for WebSocket connections"""
    total_connections: int = 0
    active_connections: int = 0
    total_channels: int = 0
    total_messages: int = 0
    avg_latency: float = 0.0
    max_concurrent_connections: int = 0
    connection_errors: int = 0
    message_dropped: int = 0
    throughput_mps: float = 0.0  # Messages per second


@dataclass
class ConnectionPool:
    """Pool of WebSocket connections"""
    pool_id: str
    timestamp: float
    connections: Dict[str, WebSocketConnection] = field(default_factory=dict)
    channels: Dict[str, Channel] = field(default_factory=dict)
    metrics: ConnectionMetrics = field(default_factory=ConnectionMetrics)
    max_connections: int = 10000
    connection_timeout: int = 300  # seconds
    heartbeat_interval: int = 30  # seconds


class WebSocketManager:
    """
    Enterprise WebSocket and real-time communication system

    Manages:
    - WebSocket connections lifecycle
    - Pub/Sub channels
    - Message routing and delivery
    - Connection pooling and scaling
    - Heartbeat and connection monitoring
    - Message acknowledgments
    - Connection authentication
    - Broadcast and targeted messaging
    """

    def __init__(self, pool_size: int = 10000):
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.connections: Dict[str, WebSocketConnection] = {}
        self.channels: Dict[str, Channel] = {}
        self.message_queue: List[WebSocketMessage] = []
        self.max_pool_size = pool_size
        self.message_handlers: Dict[str, Callable] = {}

    def create_connection(self,
                         client_id: str,
                         ip_address: str,
                         user_agent: str) -> WebSocketConnection:
        """
        Create new WebSocket connection

        Args:
            client_id: Unique client identifier
            ip_address: Client IP address
            user_agent: Client user agent string

        Returns:
            Created WebSocketConnection
        """
        connection_id = hashlib.md5(f"{client_id}:{time.time()}:{random.random()}".encode()).hexdigest()[:8]

        connection = WebSocketConnection(
            connection_id=connection_id,
            client_id=client_id,
            state=ConnectionState.CONNECTING,
            created_at=time.time(),
            last_activity=time.time(),
            ip_address=ip_address,
            user_agent=user_agent,
            latency_ms=random.uniform(10, 100)
        )

        self.connections[connection_id] = connection
        return connection

    def authenticate_connection(self,
                               connection_id: str,
                               auth_token: str,
                               user_id: str) -> bool:
        """
        Authenticate WebSocket connection

        Args:
            connection_id: Connection ID
            auth_token: Authentication token
            user_id: User ID

        Returns:
            Authentication success status
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        # Simulate token validation
        is_valid = self._validate_token(auth_token)

        if is_valid:
            connection.state = ConnectionState.AUTHENTICATED
            connection.authenticated = True
            connection.auth_token = auth_token
            connection.user_id = user_id
            return True
        else:
            connection.state = ConnectionState.ERROR
            return False

    def _validate_token(self, token: str) -> bool:
        """Validate authentication token (simulated)"""
        return len(token) > 20 and random.random() > 0.05  # 95% success rate

    def create_channel(self,
                      channel_name: str,
                      channel_type: SubscriptionType,
                      max_subscribers: Optional[int] = None,
                      encryption_enabled: bool = False) -> Channel:
        """
        Create pub/sub channel

        Args:
            channel_name: Channel name
            channel_type: Type of subscription
            max_subscribers: Maximum allowed subscribers
            encryption_enabled: Enable message encryption

        Returns:
            Created Channel
        """
        channel_id = hashlib.md5(f"{channel_name}:{time.time()}".encode()).hexdigest()[:8]

        channel = Channel(
            channel_id=channel_id,
            channel_name=channel_name,
            channel_type=channel_type,
            created_at=time.time(),
            max_subscribers=max_subscribers,
            encryption_enabled=encryption_enabled
        )

        self.channels[channel_id] = channel
        return channel

    def subscribe(self,
                 connection_id: str,
                 channel_id: str) -> bool:
        """
        Subscribe connection to channel

        Args:
            connection_id: Connection ID
            channel_id: Channel ID

        Returns:
            Subscription success status
        """
        connection = self.connections.get(connection_id)
        channel = self.channels.get(channel_id)

        if not connection or not channel:
            return False

        # Check max subscribers
        if channel.max_subscribers and len(channel.subscribers) >= channel.max_subscribers:
            return False

        # Check authentication if required
        if channel.channel_type in [SubscriptionType.USER_SPECIFIC, SubscriptionType.ROOM]:
            if not connection.authenticated:
                return False

        connection.subscriptions.add(channel_id)
        channel.subscribers.add(connection_id)

        return True

    def unsubscribe(self,
                   connection_id: str,
                   channel_id: str) -> bool:
        """
        Unsubscribe connection from channel

        Args:
            connection_id: Connection ID
            channel_id: Channel ID

        Returns:
            Unsubscription success status
        """
        connection = self.connections.get(connection_id)
        channel = self.channels.get(channel_id)

        if not connection or not channel:
            return False

        connection.subscriptions.discard(channel_id)
        channel.subscribers.discard(connection_id)

        return True

    def send_message(self,
                    sender_id: str,
                    channel_id: str,
                    data: Dict,
                    priority: MessagePriority = MessagePriority.NORMAL,
                    ack_required: bool = False) -> WebSocketMessage:
        """
        Send message to channel

        Args:
            sender_id: Sender connection ID
            channel_id: Target channel ID
            data: Message data
            priority: Message priority
            ack_required: Require acknowledgment

        Returns:
            Sent WebSocketMessage
        """
        channel = self.channels.get(channel_id)
        if not channel:
            return None

        message_id = hashlib.md5(f"{channel_id}:{time.time()}".encode()).hexdigest()[:8]

        message = WebSocketMessage(
            message_id=message_id,
            sender_id=sender_id,
            channel=channel.channel_name,
            data=data,
            priority=priority,
            timestamp=time.time(),
            ack_required=ack_required
        )

        self.message_queue.append(message)
        channel.message_count += 1

        # Deliver to subscribers
        for subscriber_id in channel.subscribers:
            if subscriber_id in self.connections:
                conn = self.connections[subscriber_id]
                conn.messages_received += 1
                conn.last_activity = time.time()

        return message

    def broadcast_message(self,
                         sender_id: str,
                         data: Dict,
                         exclude_sender: bool = False) -> List[str]:
        """
        Broadcast message to all connections

        Args:
            sender_id: Sender connection ID
            data: Message data
            exclude_sender: Exclude sender from broadcast

        Returns:
            List of connection IDs that received message
        """
        broadcast_channel = None
        for channel in self.channels.values():
            if channel.channel_type == SubscriptionType.BROADCAST:
                broadcast_channel = channel
                break

        if not broadcast_channel:
            broadcast_channel = self.create_channel("__broadcast__", SubscriptionType.BROADCAST)

        delivered_to = []

        for connection_id, connection in self.connections.items():
            if exclude_sender and connection_id == sender_id:
                continue

            if connection.state == ConnectionState.AUTHENTICATED:
                self.send_message(sender_id, broadcast_channel.channel_id, data)
                delivered_to.append(connection_id)

        return delivered_to

    def close_connection(self, connection_id: str) -> bool:
        """
        Close WebSocket connection

        Args:
            connection_id: Connection ID

        Returns:
            Close success status
        """
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        # Unsubscribe from all channels
        for channel_id in list(connection.subscriptions):
            self.unsubscribe(connection_id, channel_id)

        connection.state = ConnectionState.CLOSED
        del self.connections[connection_id]

        return True

    def get_connection_metrics(self) -> ConnectionMetrics:
        """Get overall connection metrics"""
        metrics = ConnectionMetrics()

        metrics.total_connections = len(self.connections)
        metrics.active_connections = sum(
            1 for c in self.connections.values()
            if c.state in [ConnectionState.AUTHENTICATED, ConnectionState.CONNECTED]
        )
        metrics.total_channels = len(self.channels)
        metrics.total_messages = sum(c.message_count for c in self.channels.values())

        if self.connections:
            latencies = [c.latency_ms for c in self.connections.values()]
            metrics.avg_latency = sum(latencies) / len(latencies)

        metrics.max_concurrent_connections = max([
            len(c.subscribers) for c in self.channels.values()
        ]) if self.channels else 0

        metrics.throughput_mps = len(self.message_queue) / max(1, time.time())

        return metrics

    def health_check(self) -> Dict:
        """Perform health check on all connections"""
        healthy = 0
        unhealthy = 0
        dead_connections = []

        current_time = time.time()

        for connection_id, connection in self.connections.items():
            # Check for stale connections (no activity for 5+ minutes)
            if current_time - connection.last_activity > 300:
                dead_connections.append(connection_id)
                unhealthy += 1
            elif connection.state in [ConnectionState.AUTHENTICATED, ConnectionState.CONNECTED]:
                healthy += 1
            else:
                unhealthy += 1

        # Clean up dead connections
        for conn_id in dead_connections:
            self.close_connection(conn_id)

        return {
            "healthy_connections": healthy,
            "unhealthy_connections": unhealthy,
            "dead_connections_removed": len(dead_connections),
            "total_connections": len(self.connections),
        }

    def generate_status_report(self) -> str:
        """Generate WebSocket system status report"""
        metrics = self.get_connection_metrics()
        health = self.health_check()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    WEBSOCKET SYSTEM STATUS REPORT                          ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 CONNECTION METRICS:
├─ Total Connections: {metrics.total_connections}
├─ Active Connections: {metrics.active_connections}
├─ Average Latency: {metrics.avg_latency:.1f}ms
└─ Throughput: {metrics.throughput_mps:.1f} msg/s

📡 CHANNEL METRICS:
├─ Total Channels: {metrics.total_channels}
├─ Total Messages: {metrics.total_messages}
└─ Max Concurrent: {metrics.max_concurrent_connections}

🏥 HEALTH STATUS:
├─ Healthy: {health['healthy_connections']}
├─ Unhealthy: {health['unhealthy_connections']}
└─ Cleaned Up: {health['dead_connections_removed']}

📌 RECENT CHANNELS:
"""

        for channel_name, channel in list(self.channels.items())[-5:]:
            report += f"\n  • {channel.channel_name} ({channel.channel_type.value})\n"
            report += f"    Subscribers: {len(channel.subscribers)}\n"
            report += f"    Messages: {channel.message_count}\n"

        return report

    def export_state(self) -> str:
        """Export WebSocket manager state as JSON"""
        export_data = {
            "timestamp": time.time(),
            "connections": {
                conn_id: {
                    "client_id": conn.client_id,
                    "user_id": conn.user_id,
                    "state": conn.state.value,
                    "authenticated": conn.authenticated,
                    "subscriptions": len(conn.subscriptions),
                    "latency_ms": conn.latency_ms,
                    "messages_sent": conn.messages_sent,
                    "messages_received": conn.messages_received,
                }
                for conn_id, conn in self.connections.items()
            },
            "channels": {
                chan_id: {
                    "name": chan.channel_name,
                    "type": chan.channel_type.value,
                    "subscribers": len(chan.subscribers),
                    "messages": chan.message_count,
                }
                for chan_id, chan in self.channels.items()
            },
            "metrics": {
                "active_connections": sum(
                    1 for c in self.connections.values()
                    if c.state == ConnectionState.AUTHENTICATED
                ),
                "total_channels": len(self.channels),
                "pending_messages": len(self.message_queue),
            },
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔌 WebSocket Manager - Real-time Communication System")
    print("=" * 70)

    manager = WebSocketManager(pool_size=10000)

    # Create connections
    print("\n🔗 Creating WebSocket connections...")
    conn1 = manager.create_connection("client1", "192.168.1.100", "Mozilla/5.0")
    conn2 = manager.create_connection("client2", "192.168.1.101", "Mozilla/5.0")
    conn3 = manager.create_connection("client3", "192.168.1.102", "Mozilla/5.0")

    # Authenticate connections
    print("\n🔐 Authenticating connections...")
    manager.authenticate_connection(conn1.connection_id, "token_abc123def456", "user_001")
    manager.authenticate_connection(conn2.connection_id, "token_xyz789uvw012", "user_002")
    manager.authenticate_connection(conn3.connection_id, "token_pqr345stu678", "user_003")

    # Create channels
    print("\n📡 Creating pub/sub channels...")
    chat_channel = manager.create_channel("chat#general", SubscriptionType.ROOM)
    notifications = manager.create_channel("notifications", SubscriptionType.BROADCAST)
    user_feed = manager.create_channel("feed#user_001", SubscriptionType.USER_SPECIFIC)

    # Subscribe
    print("\n📥 Subscribing to channels...")
    manager.subscribe(conn1.connection_id, chat_channel.channel_id)
    manager.subscribe(conn2.connection_id, chat_channel.channel_id)
    manager.subscribe(conn3.connection_id, chat_channel.channel_id)
    manager.subscribe(conn1.connection_id, notifications.channel_id)

    # Send messages
    print("\n💬 Sending messages...")
    msg1 = manager.send_message(
        conn1.connection_id,
        chat_channel.channel_id,
        {"text": "Hello everyone!", "user": "user_001"},
        priority=MessagePriority.NORMAL
    )
    msg2 = manager.send_message(
        conn2.connection_id,
        chat_channel.channel_id,
        {"text": "Hi there!", "user": "user_002"},
        priority=MessagePriority.NORMAL
    )

    # Broadcast
    print("\n📢 Broadcasting message...")
    delivered = manager.broadcast_message(
        conn1.connection_id,
        {"notification": "Server maintenance in 1 hour", "severity": "HIGH"}
    )
    print(f"Delivered to {len(delivered)} connections")

    # Get metrics
    print(manager.generate_status_report())

    # Export state
    print("\n📄 Exporting WebSocket state...")
    export = manager.export_state()
    print(f"✅ Exported {len(export)} characters of state data")

    print("\n" + "=" * 70)
    print("✨ WebSocket management complete")


if __name__ == "__main__":
    main()
