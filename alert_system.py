#!/usr/bin/env python3
"""
MindLang 실시간 알림 시스템
여러 채널을 통한 실시간 알림

채널:
- Email
- Slack
- Discord
- Telegram
- 로컬 알림
"""

import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime


class AlertSeverity(str, Enum):
    """알림 심각도"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """알림 채널"""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    LOCAL = "local"


@dataclass
class Alert:
    """알림"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    source: str  # 알림 출처 (서비스명)
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution_notes: Optional[str] = None


@dataclass
class AlertRule:
    """알림 규칙"""
    id: str
    name: str
    condition: str  # 조건 (예: "cpu > 80")
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    repeat_interval: int = 300  # 반복 간격 (초)
    last_triggered: Optional[float] = None


class AlertManager:
    """알림 관리자"""

    def __init__(self, config_file: str = 'alert_config.json'):
        self.config_file = config_file
        self.alerts: Dict[str, Alert] = {}
        self.rules: Dict[str, AlertRule] = {}
        self.channels_config: Dict[str, Dict] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 10000
        self.load_config()

    def load_config(self):
        """설정 로드"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)

                # 규칙 로드
                for rule_data in data.get('rules', []):
                    rule = AlertRule(
                        id=rule_data['id'],
                        name=rule_data['name'],
                        condition=rule_data['condition'],
                        severity=AlertSeverity(rule_data['severity']),
                        channels=[AlertChannel(c) for c in rule_data['channels']],
                        enabled=rule_data.get('enabled', True)
                    )
                    self.rules[rule.id] = rule

                # 채널 설정 로드
                self.channels_config = data.get('channels', {})

        except FileNotFoundError:
            self._create_default_config()

    def _create_default_config(self):
        """기본 설정 생성"""
        default_config = {
            'rules': [
                {
                    'id': 'cpu_high',
                    'name': 'CPU 높음',
                    'condition': 'cpu > 80',
                    'severity': 'warning',
                    'channels': ['local', 'email'],
                    'enabled': True
                },
                {
                    'id': 'memory_critical',
                    'name': '메모리 부족',
                    'condition': 'memory > 90',
                    'severity': 'critical',
                    'channels': ['local', 'email', 'slack'],
                    'enabled': True
                },
                {
                    'id': 'service_down',
                    'name': '서비스 다운',
                    'condition': 'service_status == down',
                    'severity': 'critical',
                    'channels': ['local', 'email', 'slack', 'discord'],
                    'enabled': True
                }
            ],
            'channels': {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'sender': 'your_email@gmail.com',
                    'recipients': ['admin@example.com']
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
                },
                'discord': {
                    'enabled': False,
                    'webhook_url': 'https://discord.com/api/webhooks/YOUR/WEBHOOK/URL'
                },
                'telegram': {
                    'enabled': False,
                    'bot_token': 'YOUR_BOT_TOKEN',
                    'chat_id': 'YOUR_CHAT_ID'
                }
            }
        }

        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)

        self.load_config()

    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        source: str
    ) -> Alert:
        """알림 생성"""
        alert_id = f"{source}_{int(time.time())}_{len(self.alerts)}"

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            source=source,
            timestamp=time.time()
        )

        self.alerts[alert_id] = alert
        self.alert_history.append(alert)

        if len(self.alert_history) > self.max_history:
            self.alert_history.pop(0)

        # 규칙에 따른 알림 전송
        self._send_alert(alert)

        return alert

    def _send_alert(self, alert: Alert):
        """알림 전송"""
        # 규칙 확인
        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # 심각도 매칭
            if rule.severity.value != alert.severity.value:
                continue

            # 반복 간격 확인
            if rule.last_triggered:
                if time.time() - rule.last_triggered < rule.repeat_interval:
                    continue

            # 채널별 전송
            for channel in rule.channels:
                self._send_to_channel(alert, channel)

            rule.last_triggered = time.time()

    def _send_to_channel(self, alert: Alert, channel: AlertChannel):
        """특정 채널로 알림 전송"""
        try:
            if channel == AlertChannel.LOCAL:
                self._send_local(alert)
            elif channel == AlertChannel.EMAIL:
                self._send_email(alert)
            elif channel == AlertChannel.SLACK:
                self._send_slack(alert)
            elif channel == AlertChannel.DISCORD:
                self._send_discord(alert)
            elif channel == AlertChannel.TELEGRAM:
                self._send_telegram(alert)
        except Exception as e:
            print(f"알림 전송 실패 ({channel.value}): {e}")

    def _send_local(self, alert: Alert):
        """로컬 알림"""
        severity_icon = {
            AlertSeverity.INFO: '🔵',
            AlertSeverity.WARNING: '🟡',
            AlertSeverity.CRITICAL: '🔴'
        }.get(alert.severity, '❓')

        print(f"\n{severity_icon} [{alert.source}] {alert.title}")
        print(f"   {alert.message}")
        print(f"   {datetime.fromtimestamp(alert.timestamp).isoformat()}")

    def _send_email(self, alert: Alert):
        """이메일 전송"""
        config = self.channels_config.get('email', {})
        if not config.get('enabled'):
            return

        try:
            import smtplib
            from email.mime.text import MIMEText

            msg = MIMEText(f"{alert.message}\n\n출처: {alert.source}")
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            msg['From'] = config['sender']
            msg['To'] = ', '.join(config['recipients'])

            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                server.starttls()
                server.login(config['sender'], config.get('password', ''))
                server.send_message(msg)

            print(f"✅ 이메일 전송: {alert.title}")
        except Exception as e:
            print(f"❌ 이메일 전송 실패: {e}")

    def _send_slack(self, alert: Alert):
        """Slack 전송"""
        config = self.channels_config.get('slack', {})
        if not config.get('enabled'):
            return

        try:
            import httpx

            color_map = {
                AlertSeverity.INFO: '#36a64f',
                AlertSeverity.WARNING: '#ffa500',
                AlertSeverity.CRITICAL: '#ff0000'
            }

            payload = {
                'attachments': [
                    {
                        'color': color_map.get(alert.severity, '#cccccc'),
                        'title': alert.title,
                        'text': alert.message,
                        'fields': [
                            {
                                'title': '출처',
                                'value': alert.source,
                                'short': True
                            },
                            {
                                'title': '심각도',
                                'value': alert.severity.value.upper(),
                                'short': True
                            }
                        ],
                        'footer': 'MindLang Alert System',
                        'ts': int(alert.timestamp)
                    }
                ]
            }

            httpx.post(config['webhook_url'], json=payload, timeout=10)
            print(f"✅ Slack 전송: {alert.title}")
        except Exception as e:
            print(f"❌ Slack 전송 실패: {e}")

    def _send_discord(self, alert: Alert):
        """Discord 전송"""
        config = self.channels_config.get('discord', {})
        if not config.get('enabled'):
            return

        try:
            import httpx

            color_map = {
                AlertSeverity.INFO: 0x36a64f,
                AlertSeverity.WARNING: 0xffa500,
                AlertSeverity.CRITICAL: 0xff0000
            }

            payload = {
                'embeds': [
                    {
                        'title': alert.title,
                        'description': alert.message,
                        'color': color_map.get(alert.severity, 0xcccccc),
                        'fields': [
                            {
                                'name': '출처',
                                'value': alert.source,
                                'inline': True
                            },
                            {
                                'name': '심각도',
                                'value': alert.severity.value.upper(),
                                'inline': True
                            }
                        ],
                        'footer': {
                            'text': 'MindLang Alert System'
                        },
                        'timestamp': datetime.fromtimestamp(alert.timestamp).isoformat()
                    }
                ]
            }

            httpx.post(config['webhook_url'], json=payload, timeout=10)
            print(f"✅ Discord 전송: {alert.title}")
        except Exception as e:
            print(f"❌ Discord 전송 실패: {e}")

    def _send_telegram(self, alert: Alert):
        """Telegram 전송"""
        config = self.channels_config.get('telegram', {})
        if not config.get('enabled'):
            return

        try:
            import httpx

            severity_emoji = {
                AlertSeverity.INFO: '🔵',
                AlertSeverity.WARNING: '🟡',
                AlertSeverity.CRITICAL: '🔴'
            }.get(alert.severity, '❓')

            message = (
                f"{severity_emoji} <b>{alert.title}</b>\n\n"
                f"{alert.message}\n\n"
                f"<i>출처: {alert.source}</i>"
            )

            payload = {
                'chat_id': config['chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }

            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            httpx.post(url, json=payload, timeout=10)
            print(f"✅ Telegram 전송: {alert.title}")
        except Exception as e:
            print(f"❌ Telegram 전송 실패: {e}")

    def resolve_alert(self, alert_id: str, notes: str = ""):
        """알림 해결"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = time.time()
            alert.resolution_notes = notes

            print(f"✅ 알림 해결: {alert.title}")

    def get_active_alerts(self) -> List[Dict]:
        """활성 알림 조회"""
        return [
            {
                'id': alert.id,
                'title': alert.title,
                'message': alert.message,
                'severity': alert.severity.value,
                'source': alert.source,
                'timestamp': datetime.fromtimestamp(alert.timestamp).isoformat(),
                'duration': time.time() - alert.timestamp
            }
            for alert in self.alerts.values()
            if not alert.resolved
        ]

    def get_alert_summary(self) -> Dict:
        """알림 요약"""
        active_alerts = self.get_active_alerts()

        return {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(self.alerts),
            'active_alerts': len(active_alerts),
            'resolved_alerts': len(self.alerts) - len(active_alerts),
            'by_severity': {
                'critical': len([a for a in active_alerts if a['severity'] == 'critical']),
                'warning': len([a for a in active_alerts if a['severity'] == 'warning']),
                'info': len([a for a in active_alerts if a['severity'] == 'info'])
            },
            'by_source': {
                source: len([a for a in active_alerts if a['source'] == source])
                for source in set(a['source'] for a in active_alerts)
            },
            'active_alerts': active_alerts
        }


# 사용 예시
if __name__ == "__main__":
    manager = AlertManager()

    # 알림 생성
    alert1 = manager.create_alert(
        title="높은 CPU 사용률",
        message="CPU 사용률이 85%를 초과했습니다",
        severity=AlertSeverity.WARNING,
        source="system"
    )

    alert2 = manager.create_alert(
        title="서비스 다운",
        message="dashboard 서비스가 응답하지 않습니다",
        severity=AlertSeverity.CRITICAL,
        source="dashboard"
    )

    # 알림 해결
    manager.resolve_alert(alert1.id, "자동 스케일링으로 정상화됨")

    # 요약 조회
    summary = manager.get_alert_summary()
    print("\n📊 알림 요약")
    print(f"활성 알림: {summary['active_alerts']}")
    print(f"해결됨: {summary['resolved_alerts']}")
    print(f"심각도별: Critical {summary['by_severity']['critical']}, "
          f"Warning {summary['by_severity']['warning']}")
