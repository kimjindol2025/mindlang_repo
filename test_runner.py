#!/usr/bin/env python3
"""
MindLang Test Runner
Mock API로 테스트 자동 실행 및 리포팅

사용:
    python test_runner.py                    # 모든 테스트
    python test_runner.py --mock-only        # Mock API만
    python test_runner.py --with-coverage    # 커버리지 포함
    python test_runner.py --parallel         # 병렬 실행
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict
import argparse
import time
from datetime import datetime


class TestRunner:
    """테스트 실행기"""

    def __init__(self, repo_dir: str = "."):
        self.repo_dir = Path(repo_dir)
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'total': 0,
            'duration': 0,
        }

    def setup_environment(self) -> None:
        """테스트 환경 설정"""
        os.environ['USE_MOCK_API'] = 'true'
        os.environ['TEST_MODE'] = 'true'
        os.environ['LOG_LEVEL'] = 'INFO'

        print("✅ Environment Setup:")
        print(f"   USE_MOCK_API: {os.environ.get('USE_MOCK_API')}")
        print(f"   TEST_MODE: {os.environ.get('TEST_MODE')}")
        print()

    def build_pytest_command(
        self,
        args: argparse.Namespace
    ) -> List[str]:
        """pytest 명령어 구성"""
        cmd = [
            sys.executable,
            '-m',
            'pytest',
            str(self.repo_dir),
            '-v',
            '--tb=short',
        ]

        # 커버리지
        if args.coverage:
            cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])

        # 병렬 실행
        if args.parallel:
            cmd.extend(['-n', 'auto'])

        # 마커
        if args.marker:
            cmd.extend(['-m', args.marker])

        # 출력 설정
        if args.quiet:
            cmd.append('-q')

        # 소속
        if args.show_output:
            cmd.append('-s')

        return cmd

    def run_tests(self, args: argparse.Namespace) -> int:
        """테스트 실행"""
        self.setup_environment()

        print("=" * 70)
        print("🧠 MindLang Test Suite")
        print("=" * 70)
        print(f"📍 Test Directory: {self.repo_dir}")
        print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # pytest 명령어 구성
        cmd = self.build_pytest_command(args)

        print("📋 Command:")
        print(f"   {' '.join(cmd)}")
        print()

        # 테스트 실행
        print("🧪 Running tests...\n")
        start_time = time.time()

        try:
            result = subprocess.run(cmd, cwd=self.repo_dir)
            self.results['duration'] = time.time() - start_time
            return result.returncode

        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return 1

    def print_summary(self) -> None:
        """테스트 결과 요약"""
        print("\n" + "=" * 70)
        print("📊 Test Summary")
        print("=" * 70)
        print(f"⏱️  Duration: {self.results['duration']:.2f}s")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏭️  Skipped: {self.results['skipped']}")
        print(f"📈 Total: {self.results['total']}")

        if self.results['failed'] == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {self.results['failed']} test(s) failed")

        print("=" * 70 + "\n")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="MindLang Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # 모든 테스트
  python test_runner.py --coverage         # 커버리지 포함
  python test_runner.py --parallel         # 병렬 실행
  python test_runner.py -m path1           # Path 1 테스트만
  python test_runner.py -m "not slow"      # Slow 테스트 제외
        """
    )

    parser.add_argument(
        '--repo',
        type=str,
        default='.',
        help='Repository directory (default: current directory)'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generate coverage report'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel (requires pytest-xdist)'
    )

    parser.add_argument(
        '-m', '--marker',
        type=str,
        help='Run tests matching marker (e.g., path1, kubernetes)'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output'
    )

    parser.add_argument(
        '-s', '--show-output',
        action='store_true',
        help='Show print statements (capture=no)'
    )

    parser.add_argument(
        '--mock-only',
        action='store_true',
        help='Run only Mock API tests'
    )

    parser.add_argument(
        '--no-mock',
        action='store_true',
        help='Disable Mock API (use real APIs)'
    )

    args = parser.parse_args()

    # Mock API 설정
    if args.no_mock:
        os.environ['USE_MOCK_API'] = 'false'
    if args.mock_only:
        os.environ['USE_MOCK_API'] = 'true'

    # 테스트 실행
    runner = TestRunner(args.repo)
    exit_code = runner.run_tests(args)

    # 결과 요약
    runner.print_summary()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
