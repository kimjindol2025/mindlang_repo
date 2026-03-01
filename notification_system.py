#!/usr/bin/env python3
from typing import Dict, List
import time
class NotificationSystem:
    def __init__(self):
        self.notifications: List[Dict] = []
    def send_notification(self, recipient: str, message: str) -> Dict:
        notif = {"recipient": recipient, "message": message, "timestamp": time.time()}
        self.notifications.append(notif)
        return notif
    def get_stats(self) -> Dict:
        return {"total_sent": len(self.notifications)}
def main():
    print("🔔 Notification System")
    system = NotificationSystem()
    system.send_notification("admin@company.com", "Alert: High CPU usage")
    print(f"✅ Sent {len(system.notifications)} notifications")
if __name__ == "__main__":
    main()
