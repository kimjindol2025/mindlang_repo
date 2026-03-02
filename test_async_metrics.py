#!/usr/bin/env python3
"""
MindLang 비동기 메트릭 수집 테스트
Day 5: 성능 최적화
"""

import unittest
import asyncio
import time
from api_client_async import AsyncAPIClient
from mindlang_with_red_team import MindLangRedTeam
from config import Config


class TestAsyncMetrics(unittest.TestCase):
    """비동기 메트릭 수집 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        Config.USE_MOCK_API = True
        self.client = AsyncAPIClient(max_workers=5)
        self.mindlang = MindLangRedTeam()

    def test_async_error_metrics(self):
        """비동기 에러 메트릭 수집"""
        async def run_test():
            start = time.time()
            result = await self.client.collect_error_metrics()
            elapsed = time.time() - start

            self.assertIn('error_rate', result)
            self.assertIn('alerts', result)
            self.assertLess(elapsed, 0.5)  # 500ms 이내
            return elapsed

        elapsed = asyncio.run(run_test())
        print(f"✅ 비동기 에러 메트릭: {elapsed*1000:.1f}ms")

    def test_async_performance_metrics(self):
        """비동기 성능 메트릭 수집"""
        async def run_test():
            start = time.time()
            result = await self.client.collect_performance_metrics()
            elapsed = time.time() - start

            self.assertIn('deployments', result)
            self.assertIn('registry_tags', result)
            self.assertIn('datadog_host', result)
            self.assertLess(elapsed, 0.5)  # 500ms 이내
            return elapsed

        elapsed = asyncio.run(run_test())
        print(f"✅ 비동기 성능 메트릭: {elapsed*1000:.1f}ms")

    def test_async_all_metrics(self):
        """모든 메트릭 비동기 수집"""
        async def run_test():
            start = time.time()
            result = await self.client.collect_all_metrics()
            elapsed = time.time() - start

            self.assertIn('error_metrics', result)
            self.assertIn('performance_metrics', result)
            self.assertLess(elapsed, 0.3)  # 300ms 이내 (목표)
            return elapsed

        elapsed = asyncio.run(run_test())

        if elapsed < 0.3:
            status = "✅ 목표 달성"
        else:
            status = "⚠️  목표 미달"

        print(f"{status}: 전체 메트릭 수집 {elapsed*1000:.1f}ms")

    def test_mindlang_with_async_metrics(self):
        """MindLang + 비동기 메트릭"""
        async def run_test():
            # 메트릭 수집
            start = time.time()
            metrics_result = await self.client.collect_all_metrics()
            collection_time = time.time() - start

            # 메트릭을 MindLang에 전달
            combined_metrics = {
                'error_rate': 0.002,
                'cpu_usage': 45,
                'memory_usage': 50,
                'latency_p95': 150,
                'throughput': 5000,
                'collection_time': collection_time
            }

            # MindLang 분석
            analysis_start = time.time()
            result = self.mindlang.analyze(combined_metrics)
            analysis_time = time.time() - analysis_start

            return {
                'collection_time': collection_time,
                'analysis_time': analysis_time,
                'total_time': collection_time + analysis_time,
                'decision': result['primary_decision']['action']
            }

        result = asyncio.run(run_test())

        total = result['collection_time'] + result['analysis_time']
        print(f"\n📊 MindLang + 비동기 메트릭:")
        print(f"  메트릭 수집 : {result['collection_time']*1000:6.1f}ms")
        print(f"  분석 시간   : {result['analysis_time']*1000:6.1f}ms")
        print(f"  총 시간     : {total*1000:6.1f}ms")
        print(f"  결정        : {result['decision']}")

        self.assertLess(total, 0.5)  # 500ms 이내

    def test_parallel_performance_target(self):
        """병렬 수집 300ms 목표 달성 확인"""
        async def run_test():
            # 병렬
            start = time.time()
            parallel = await self.client.collect_all_metrics()
            parallel_time = time.time() - start

            return parallel_time

        parallel_time = asyncio.run(run_test())

        print(f"\n⚡ 성능 목표 확인:")
        print(f"  병렬 수집  : {parallel_time*1000:6.1f}ms")
        print(f"  목표       : <300ms")

        if parallel_time < 0.3:
            print(f"  상태       : ✅ 목표 달성")
        else:
            print(f"  상태       : ⚠️  목표 미달")

        # 병렬이 300ms 이내인지 확인
        self.assertLess(parallel_time, 0.3)


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 MindLang Day 5: 비동기 메트릭 수집 테스트")
    print("=" * 70 + "\n")

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAsyncMetrics)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"에러: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 모든 테스트 통과!")
        print("🎯 성능 목표 달성: <300ms ✨")
    else:
        print("\n❌ 일부 테스트 실패")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
