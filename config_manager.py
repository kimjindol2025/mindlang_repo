#!/usr/bin/env python3
"""
MindLang 중앙 설정 관리자
모든 도구의 설정을 한곳에서 관리

기능:
- 중앙 집중식 설정
- 실시간 설정 변경
- 설정 검증
- 설정 백업/복구
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from datetime import datetime
import copy


@dataclass
class ConfigSection:
    """설정 섹션"""
    name: str
    description: str
    enabled: bool = True
    settings: Dict[str, Any] = None

    def __post_init__(self):
        if self.settings is None:
            self.settings = {}


class ConfigManager:
    """설정 관리자"""

    def __init__(self, config_file: str = 'mindlang_config.json'):
        self.config_file = config_file
        self.config: Dict[str, Dict] = {}
        self.defaults: Dict[str, Dict] = self._get_defaults()
        self.history: list = []
        self.load_config()

    def _get_defaults(self) -> Dict[str, Dict]:
        """기본 설정 반환"""
        return {
            'system': {
                'description': '시스템 전역 설정',
                'debug_mode': False,
                'log_level': 'INFO',
                'timezone': 'Asia/Seoul',
                'environment': 'production',
                'max_workers': 4
            },
            'gateway': {
                'description': 'API Gateway 설정',
                'host': '0.0.0.0',
                'port': 8100,
                'timeout': 30,
                'max_retries': 3,
                'log_requests': True,
                'enable_cors': True
            },
            'dashboard': {
                'description': '대시보드 설정',
                'port': 8000,
                'update_interval_ms': 2000,
                'max_history': 1000,
                'enable_websocket': True
            },
            'learning': {
                'description': '학습 엔진 설정',
                'port': 8001,
                'max_memory': 1000,
                'enable_pattern_detection': True,
                'enable_warning_detection': True,
                'pattern_threshold': 0.8
            },
            'benchmark': {
                'description': '벤치마크 설정',
                'port': 8002,
                'iterations': 100,
                'timeout_per_model': 30,
                'enable_parallel': True
            },
            'analyzer': {
                'description': '분석기 설정',
                'port': 8003,
                'enable_export': True,
                'export_format': 'json',
                'max_report_size_mb': 10
            },
            'policy_engine': {
                'description': '정책 엔진 설정',
                'auto_activate': False,
                'min_confidence': 0.7,
                'max_policies': 1000,
                'enable_rollback': True,
                'rollback_threshold': 0.5
            },
            'orchestrator': {
                'description': '오케스트레이터 설정',
                'check_interval_sec': 30,
                'startup_timeout_sec': 60,
                'auto_restart': True,
                'max_restart_attempts': 3
            },
            'monitoring': {
                'description': '모니터링 대시보드 v2 설정',
                'port': 9000,
                'metrics_interval_sec': 30,
                'alert_check_interval_sec': 60,
                'max_metrics_history': 3600
            },
            'deployment': {
                'description': '배포 관리자 설정',
                'docker_enabled': True,
                'kubernetes_enabled': False,
                'health_check_timeout': 300,
                'auto_rollback_on_failure': True
            },
            'profiler': {
                'description': '성능 프로파일러 설정',
                'enable_cpu_profiling': True,
                'enable_memory_profiling': True,
                'enable_io_profiling': True,
                'max_profile_records': 10000
            },
            'alert_system': {
                'description': '알림 시스템 설정',
                'enabled': True,
                'channels': {
                    'local': True,
                    'email': False,
                    'slack': False,
                    'discord': False,
                    'telegram': False
                },
                'alert_repeat_interval': 300,
                'max_alerts': 10000
            },
            'database': {
                'description': '데이터베이스 설정',
                'enabled': False,
                'type': 'sqlite',
                'sqlite_path': './mindlang.db',
                'backup_enabled': True,
                'backup_interval_hours': 24
            },
            'security': {
                'description': '보안 설정',
                'enable_auth': False,
                'enable_encryption': False,
                'ssl_enabled': False,
                'ssl_cert_path': None,
                'api_key_required': False
            }
        }

    def load_config(self):
        """설정 로드"""
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.config = data.get('settings', copy.deepcopy(self.defaults))
                self.history = data.get('history', [])
        except FileNotFoundError:
            self._create_default_config()

    def _create_default_config(self):
        """기본 설정 파일 생성"""
        self.config = copy.deepcopy(self.defaults)
        self.save_config()
        print(f"✅ 기본 설정 파일 생성: {self.config_file}")

    def save_config(self):
        """설정 저장"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'settings': self.config,
            'history': self.history[-100:]  # 최근 100개 이력만 유지
        }

        with open(self.config_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, section: str, key: str = None, default: Any = None) -> Any:
        """설정 조회"""
        if section not in self.config:
            return default

        if key is None:
            return self.config[section]

        return self.config[section].get(key, default)

    def set(self, section: str, key: str, value: Any, validate: bool = True) -> bool:
        """설정 변경"""
        if section not in self.config:
            print(f"❌ 섹션 {section}을(를) 찾을 수 없습니다")
            return False

        # 검증
        if validate and not self._validate_value(section, key, value):
            print(f"❌ 잘못된 값: {section}.{key} = {value}")
            return False

        # 이전 값 기록
        old_value = self.config[section].get(key)

        # 변경
        self.config[section][key] = value

        # 이력 기록
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'section': section,
            'key': key,
            'old_value': old_value,
            'new_value': value
        })

        self.save_config()
        print(f"✅ 설정 변경: {section}.{key} = {value}")
        return True

    def _validate_value(self, section: str, key: str, value: Any) -> bool:
        """설정 값 검증"""
        # 기본 검증
        if section == 'gateway' and key == 'port':
            return isinstance(value, int) and 1 <= value <= 65535

        if section == 'system' and key == 'max_workers':
            return isinstance(value, int) and value > 0

        if key.endswith('_timeout') or key.endswith('_interval'):
            return isinstance(value, (int, float)) and value > 0

        if isinstance(value, bool) or isinstance(value, (int, float, str)):
            return True

        return True

    def get_section(self, section: str) -> Dict[str, Any]:
        """섹션 전체 조회"""
        return self.config.get(section, {})

    def update_section(self, section: str, settings: Dict[str, Any]) -> bool:
        """섹션 전체 업데이트"""
        if section not in self.config:
            return False

        for key, value in settings.items():
            self.set(section, key, value, validate=True)

        return True

    def reset_to_defaults(self, section: str = None) -> bool:
        """기본값으로 리셋"""
        if section:
            if section not in self.defaults:
                return False
            self.config[section] = copy.deepcopy(self.defaults[section])
            print(f"✅ {section} 섹션을 기본값으로 리셋")
        else:
            self.config = copy.deepcopy(self.defaults)
            print(f"✅ 모든 설정을 기본값으로 리셋")

        self.save_config()
        return True

    def export_config(self, filename: str = None) -> str:
        """설정 내보내기"""
        if filename is None:
            filename = f"mindlang_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

        print(f"✅ 설정 내보내기: {filename}")
        return filename

    def import_config(self, filename: str) -> bool:
        """설정 가져오기"""
        try:
            with open(filename, 'r') as f:
                imported = json.load(f)

            # 백업
            self.export_config(f"mindlang_config_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

            # 병합
            for section, settings in imported.items():
                if section in self.config:
                    self.config[section].update(settings)

            self.save_config()
            print(f"✅ 설정 가져오기: {filename}")
            return True

        except Exception as e:
            print(f"❌ 설정 가져오기 실패: {e}")
            return False

    def get_history(self, section: str = None, limit: int = 50) -> list:
        """변경 이력 조회"""
        history = self.history

        if section:
            history = [h for h in history if h['section'] == section]

        return history[-limit:]

    def validate_all(self) -> Dict[str, list]:
        """모든 설정 검증"""
        issues = {}

        # 포트 충돌 확인
        ports = {}
        for section, settings in self.config.items():
            if isinstance(settings, dict) and 'port' in settings:
                port = settings['port']
                if port in ports:
                    if 'port_conflicts' not in issues:
                        issues['port_conflicts'] = []
                    issues['port_conflicts'].append(
                        f"{section}과 {ports[port]}이 포트 {port} 사용"
                    )
                ports[port] = section

        # 범위 확인
        if self.config['policy_engine']['min_confidence'] > 1.0:
            if 'invalid_confidence' not in issues:
                issues['invalid_confidence'] = []
            issues['invalid_confidence'].append('min_confidence는 0-1 범위여야 함')

        return issues

    def print_config(self, section: str = None):
        """설정 출력"""
        print("\n" + "="*80)
        print("⚙️  MindLang 설정")
        print("="*80 + "\n")

        if section:
            sections = {section: self.config.get(section, {})}
        else:
            sections = self.config

        for sec_name, settings in sections.items():
            print(f"\n📋 {sec_name}")
            print("-" * 80)

            if isinstance(settings, dict):
                for key, value in settings.items():
                    if key != 'description':
                        if isinstance(value, dict):
                            print(f"  {key}:")
                            for k, v in value.items():
                                print(f"    - {k}: {v}")
                        else:
                            print(f"  {key}: {value}")

        print("\n" + "="*80 + "\n")


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = ConfigManager()

    if len(sys.argv) < 2:
        print("사용법: python config_manager.py [command] [args]")
        print("  show [section]              - 설정 표시")
        print("  get <section> <key>         - 설정 조회")
        print("  set <section> <key> <value> - 설정 변경")
        print("  reset [section]             - 기본값으로 리셋")
        print("  export [filename]           - 설정 내보내기")
        print("  import <filename>           - 설정 가져오기")
        print("  history [section] [limit]   - 변경 이력")
        print("  validate                    - 설정 검증")
        return

    command = sys.argv[1]

    if command == "show":
        section = sys.argv[2] if len(sys.argv) > 2 else None
        manager.print_config(section)

    elif command == "get":
        section = sys.argv[2] if len(sys.argv) > 2 else None
        key = sys.argv[3] if len(sys.argv) > 3 else None

        if section and key:
            value = manager.get(section, key)
            print(f"{section}.{key} = {value}")
        else:
            print("섹션과 키를 지정하세요")

    elif command == "set":
        section = sys.argv[2] if len(sys.argv) > 2 else None
        key = sys.argv[3] if len(sys.argv) > 3 else None
        value = sys.argv[4] if len(sys.argv) > 4 else None

        if section and key and value:
            # 타입 추론
            try:
                value = int(value)
            except:
                try:
                    value = float(value)
                except:
                    if value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'

            manager.set(section, key, value)
        else:
            print("섹션, 키, 값을 지정하세요")

    elif command == "reset":
        section = sys.argv[2] if len(sys.argv) > 2 else None
        manager.reset_to_defaults(section)

    elif command == "export":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        manager.export_config(filename)

    elif command == "import":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        if filename:
            manager.import_config(filename)
        else:
            print("파일명을 지정하세요")

    elif command == "history":
        section = sys.argv[2] if len(sys.argv) > 2 else None
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20

        history = manager.get_history(section, limit)
        print("\n📋 설정 변경 이력\n")
        for h in history:
            print(f"{h['timestamp']} | {h['section']}.{h['key']}: {h['old_value']} → {h['new_value']}")

    elif command == "validate":
        issues = manager.validate_all()
        if issues:
            print("\n⚠️  설정 검증 문제\n")
            for issue_type, items in issues.items():
                print(f"{issue_type}:")
                for item in items:
                    print(f"  - {item}")
        else:
            print("\n✅ 모든 설정이 유효합니다")
