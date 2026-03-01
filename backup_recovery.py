#!/usr/bin/env python3
"""
MindLang 백업/복구 시스템
모든 중요 데이터의 자동 백업 및 복구

기능:
- 자동 백업
- 증분 백업
- 백업 검증
- 자동 복구
- 백업 관리
"""

import os
import json
import shutil
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import tarfile
import glob


@dataclass
class BackupMetadata:
    """백업 메타데이터"""
    id: str
    timestamp: float
    backup_type: str  # full, incremental
    files_count: int
    total_size_mb: float
    checksum: str
    location: str
    retention_days: int = 30
    compressed: bool = True


class BackupRecoveryManager:
    """백업/복구 관리자"""

    def __init__(self, backup_dir: str = './backups'):
        self.backup_dir = backup_dir
        self.metadata_file = os.path.join(backup_dir, 'backup_metadata.json')
        self.backups: Dict[str, BackupMetadata] = {}
        self.important_files = [
            'decision_memory.json',
            'policies.json',
            'benchmark_results.json',
            'decision_analysis_report.txt',
            'mindlang_config.json',
            'deployment_history.json',
            'alert_config.json',
            'orchestrator_config.json'
        ]
        self._init_backup_dir()
        self.load_metadata()

    def _init_backup_dir(self):
        """백업 디렉토리 초기화"""
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'full'), exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, 'incremental'), exist_ok=True)

    def load_metadata(self):
        """메타데이터 로드"""
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                for backup_data in data.get('backups', []):
                    backup = BackupMetadata(**backup_data)
                    self.backups[backup.id] = backup
        except FileNotFoundError:
            pass

    def save_metadata(self):
        """메타데이터 저장"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'backups': [asdict(b) for b in self.backups.values()]
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_full_backup(self) -> Optional[BackupMetadata]:
        """전체 백업 생성"""
        backup_id = f"full_{int(datetime.now().timestamp())}"
        backup_path = os.path.join(self.backup_dir, 'full', backup_id)
        os.makedirs(backup_path, exist_ok=True)

        print(f"\n🔄 전체 백업 시작: {backup_id}")

        try:
            files_count = 0
            total_size = 0

            # 중요 파일 백업
            for filename in self.important_files:
                if os.path.exists(filename):
                    dest = os.path.join(backup_path, filename)
                    shutil.copy2(filename, dest)
                    files_count += 1
                    total_size += os.path.getsize(dest)
                    print(f"  ✅ {filename}")

            # 데이터 디렉토리 백업
            if os.path.exists('mindlang_data'):
                shutil.copytree('mindlang_data', os.path.join(backup_path, 'mindlang_data'), dirs_exist_ok=True)
                for root, dirs, files in os.walk(os.path.join(backup_path, 'mindlang_data')):
                    for file in files:
                        total_size += os.path.getsize(os.path.join(root, file))
                        files_count += 1

            # 압축
            tar_path = backup_path + '.tar.gz'
            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_id)

            # 체크섬 계산
            checksum = self._calculate_checksum(tar_path)

            # 메타데이터 생성
            metadata = BackupMetadata(
                id=backup_id,
                timestamp=datetime.now().timestamp(),
                backup_type='full',
                files_count=files_count,
                total_size_mb=total_size / 1024 / 1024,
                checksum=checksum,
                location=tar_path,
                compressed=True
            )

            self.backups[backup_id] = metadata
            self.save_metadata()

            # 원본 디렉토리 삭제
            shutil.rmtree(backup_path)

            print(f"\n✅ 전체 백업 완료")
            print(f"  파일: {files_count}개")
            print(f"  크기: {metadata.total_size_mb:.1f}MB")
            print(f"  체크섬: {checksum[:16]}...")

            return metadata

        except Exception as e:
            print(f"❌ 백업 생성 실패: {e}")
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            return None

    def create_incremental_backup(self) -> Optional[BackupMetadata]:
        """증분 백업 생성"""
        # 마지막 전체 백업 찾기
        full_backups = [b for b in self.backups.values() if b.backup_type == 'full']
        if not full_backups:
            print("⚠️  마지막 전체 백업을 찾을 수 없습니다. 전체 백업을 생성합니다.")
            return self.create_full_backup()

        last_full_backup = max(full_backups, key=lambda b: b.timestamp)
        last_backup_time = last_full_backup.timestamp

        backup_id = f"incr_{int(datetime.now().timestamp())}"
        backup_path = os.path.join(self.backup_dir, 'incremental', backup_id)
        os.makedirs(backup_path, exist_ok=True)

        print(f"\n🔄 증분 백업 시작: {backup_id}")

        try:
            files_count = 0
            total_size = 0

            # 변경된 파일만 백업
            for filename in self.important_files:
                if os.path.exists(filename):
                    file_mtime = os.path.getmtime(filename)
                    if file_mtime > last_backup_time:
                        dest = os.path.join(backup_path, filename)
                        shutil.copy2(filename, dest)
                        files_count += 1
                        total_size += os.path.getsize(dest)
                        print(f"  ✅ {filename}")

            if files_count == 0:
                print("  ℹ️  변경된 파일 없음")
                shutil.rmtree(backup_path)
                return None

            # 압축
            tar_path = backup_path + '.tar.gz'
            with tarfile.open(tar_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_id)

            checksum = self._calculate_checksum(tar_path)

            metadata = BackupMetadata(
                id=backup_id,
                timestamp=datetime.now().timestamp(),
                backup_type='incremental',
                files_count=files_count,
                total_size_mb=total_size / 1024 / 1024,
                checksum=checksum,
                location=tar_path,
                compressed=True
            )

            self.backups[backup_id] = metadata
            self.save_metadata()

            shutil.rmtree(backup_path)

            print(f"\n✅ 증분 백업 완료")
            print(f"  파일: {files_count}개")
            print(f"  크기: {metadata.total_size_mb:.1f}MB")

            return metadata

        except Exception as e:
            print(f"❌ 증분 백업 실패: {e}")
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            return None

    def restore_backup(self, backup_id: str, restore_dir: str = './') -> bool:
        """백업 복구"""
        if backup_id not in self.backups:
            print(f"❌ 백업 {backup_id}을(를) 찾을 수 없습니다")
            return False

        metadata = self.backups[backup_id]
        tar_path = metadata.location

        if not os.path.exists(tar_path):
            print(f"❌ 백업 파일을 찾을 수 없습니다: {tar_path}")
            return False

        print(f"\n🔄 복구 시작: {backup_id}")

        try:
            # 체크섬 검증
            checksum = self._calculate_checksum(tar_path)
            if checksum != metadata.checksum:
                print("❌ 백업 파일 검증 실패 (체크섬 불일치)")
                return False

            # 복구
            temp_extract_dir = os.path.join(self.backup_dir, 'temp_extract')
            os.makedirs(temp_extract_dir, exist_ok=True)

            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(temp_extract_dir)

            # 파일 복사
            backup_content_dir = os.path.join(temp_extract_dir, backup_id)

            for item in os.listdir(backup_content_dir):
                src = os.path.join(backup_content_dir, item)
                dst = os.path.join(restore_dir, item)

                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

                print(f"  ✅ {item}")

            # 정리
            shutil.rmtree(temp_extract_dir)

            print(f"\n✅ 복구 완료")
            return True

        except Exception as e:
            print(f"❌ 복구 실패: {e}")
            return False

    def verify_backup(self, backup_id: str) -> bool:
        """백업 검증"""
        if backup_id not in self.backups:
            return False

        metadata = self.backups[backup_id]
        tar_path = metadata.location

        if not os.path.exists(tar_path):
            print(f"❌ 백업 파일 없음: {tar_path}")
            return False

        print(f"\n🔍 백업 검증 중: {backup_id}")

        try:
            # 체크섬 검증
            checksum = self._calculate_checksum(tar_path)
            if checksum != metadata.checksum:
                print(f"❌ 체크섬 불일치")
                return False

            # 압축 파일 무결성 검증
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.getmembers()

            print("✅ 백업이 유효합니다")
            return True

        except Exception as e:
            print(f"❌ 검증 실패: {e}")
            return False

    def _calculate_checksum(self, filepath: str) -> str:
        """파일 체크섬 계산"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def cleanup_old_backups(self, days: int = 30) -> int:
        """오래된 백업 정리"""
        now = datetime.now().timestamp()
        cutoff_time = now - (days * 24 * 60 * 60)
        removed_count = 0

        print(f"\n🧹 {days}일 이상 된 백업 정리 중")

        for backup_id, metadata in list(self.backups.items()):
            if metadata.timestamp < cutoff_time:
                try:
                    if os.path.exists(metadata.location):
                        os.remove(metadata.location)
                    del self.backups[backup_id]
                    removed_count += 1
                    print(f"  🗑️  {backup_id} 삭제")
                except Exception as e:
                    print(f"  ❌ {backup_id} 삭제 실패: {e}")

        self.save_metadata()
        print(f"\n✅ {removed_count}개 백업 삭제 완료")
        return removed_count

    def list_backups(self) -> None:
        """백업 목록 표시"""
        if not self.backups:
            print("백업이 없습니다")
            return

        print("\n📋 백업 목록\n")
        print(f"{'ID':<30} {'타입':<12} {'크기':<10} {'생성 시간':<20}")
        print("-" * 75)

        for backup_id, metadata in sorted(self.backups.items(), key=lambda x: x[1].timestamp, reverse=True):
            backup_type = metadata.backup_type[:10]
            size = f"{metadata.total_size_mb:.1f}MB"
            time = datetime.fromtimestamp(metadata.timestamp).strftime('%Y-%m-%d %H:%M')

            print(f"{backup_id:<30} {backup_type:<12} {size:<10} {time:<20}")

    def get_backup_stats(self) -> Dict:
        """백업 통계"""
        if not self.backups:
            return {}

        full_backups = [b for b in self.backups.values() if b.backup_type == 'full']
        incremental_backups = [b for b in self.backups.values() if b.backup_type == 'incremental']

        total_size = sum(b.total_size_mb for b in self.backups.values())

        return {
            'total_backups': len(self.backups),
            'full_backups': len(full_backups),
            'incremental_backups': len(incremental_backups),
            'total_size_mb': total_size,
            'oldest_backup': min(b.timestamp for b in self.backups.values()) if self.backups else None,
            'newest_backup': max(b.timestamp for b in self.backups.values()) if self.backups else None
        }


# CLI 인터페이스
if __name__ == "__main__":
    import sys

    manager = BackupRecoveryManager()

    if len(sys.argv) < 2:
        print("사용법: python backup_recovery.py [command] [args]")
        print("  full-backup           - 전체 백업 생성")
        print("  incr-backup           - 증분 백업 생성")
        print("  list                  - 백업 목록")
        print("  verify <backup-id>    - 백업 검증")
        print("  restore <backup-id>   - 백업 복구")
        print("  cleanup [days]        - 오래된 백업 정리 (기본: 30일)")
        print("  stats                 - 백업 통계")
        return

    command = sys.argv[1]

    if command == "full-backup":
        manager.create_full_backup()

    elif command == "incr-backup":
        manager.create_incremental_backup()

    elif command == "list":
        manager.list_backups()

    elif command == "verify":
        backup_id = sys.argv[2] if len(sys.argv) > 2 else None
        if backup_id:
            manager.verify_backup(backup_id)
        else:
            print("백업 ID를 지정하세요")

    elif command == "restore":
        backup_id = sys.argv[2] if len(sys.argv) > 2 else None
        restore_dir = sys.argv[3] if len(sys.argv) > 3 else './'

        if backup_id:
            manager.restore_backup(backup_id, restore_dir)
        else:
            print("백업 ID를 지정하세요")

    elif command == "cleanup":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        manager.cleanup_old_backups(days)

    elif command == "stats":
        stats = manager.get_backup_stats()
        print("\n📊 백업 통계\n")
        print(f"총 백업: {stats.get('total_backups', 0)}개")
        print(f"  - 전체: {stats.get('full_backups', 0)}개")
        print(f"  - 증분: {stats.get('incremental_backups', 0)}개")
        print(f"총 크기: {stats.get('total_size_mb', 0):.1f}MB")
