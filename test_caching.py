#!/usr/bin/env python3
"""
MindLang 캐싱 레이어 테스트
Day 6: 캐싱 성능 검증
"""

import unittest
import asyncio
import time
from cache_layer import MetricsCache, RedTeamCache, CachingAsyncClient
from config import Config


class TestMetricsCache(unittest.TestCase):
    """메트릭 캐시 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        Config.USE_MOCK_API = True
        self.cache = MetricsCache(ttl_seconds=5)

    def test_cache_hit(self):
        """캐시 히트 테스트"""
        # 값 저장
        test_data = {'error_rate': 0.01, 'cpu': 45}
        self.cache.set('test_key', test_data)

        # 값 조회
        result = self.cache.get('test_key')

        self.assertEqual(result, test_data)
        self.assertEqual(self.cache.stats['hits'], 1)
        print("✅ 캐시 히트 테스트 통과")

    def test_cache_miss(self):
        """캐시 미스 테스트"""
        result = self.cache.get('nonexistent')

        self.assertIsNone(result)
        self.assertEqual(self.cache.stats['misses'], 1)
        print("✅ 캐시 미스 테스트 통과")

    def test_cache_expiration(self):
        """캐시 만료 테스트"""
        # 1초 TTL로 캐시 생성
        cache = MetricsCache(ttl_seconds=1)

        test_data = {'temp': 'data'}
        cache.set('expiring_key', test_data)

        # 즉시 조회 - 히트
        result1 = cache.get('expiring_key')
        self.assertEqual(result1, test_data)

        # 2초 대기 후 조회 - 미스 (만료)
        time.sleep(2)
        result2 = cache.get('expiring_key')
        self.assertIsNone(result2)

        self.assertEqual(cache.stats['evictions'], 1)
        print("✅ 캐시 만료 테스트 통과")

    def test_cache_stats(self):
        """캐시 통계 테스트"""
        # 몇 가지 작업 수행
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        self.cache.get('key1')  # 히트
        self.cache.get('key3')  # 미스

        stats = self.cache.get_stats()

        self.assertEqual(stats['hits'], 1)
        self.assertEqual(stats['misses'], 1)
        self.assertEqual(stats['size'], 2)
        print("✅ 캐시 통계 테스트 통과")


class TestRedTeamCache(unittest.TestCase):
    """Red Team 캐시 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        Config.USE_MOCK_API = True
        self.cache = RedTeamCache(ttl_seconds=5)

    def test_redteam_cache_hit(self):
        """Red Team 캐시 히트"""
        analysis = {'counter_action': 'MONITOR', 'confidence': 0.8}
        self.cache.set('ROLLBACK', analysis)

        result = self.cache.get('ROLLBACK')

        self.assertEqual(result, analysis)
        self.assertEqual(self.cache.stats['hits'], 1)
        print("✅ Red Team 캐시 히트 테스트 통과")

    def test_redteam_cache_different_decisions(self):
        """다양한 결정에 대한 Red Team 캐싱"""
        decisions = ['ROLLBACK', 'SCALE_UP', 'CONTINUE']

        for decision in decisions:
            analysis = {'action': decision, 'confidence': 0.7}
            self.cache.set(decision, analysis)

        # 모두 조회
        for decision in decisions:
            result = self.cache.get(decision)
            self.assertIsNotNone(result)

        stats = self.cache.get_stats()
        self.assertEqual(stats['hits'], 3)
        self.assertEqual(stats['size'], 3)
        print("✅ Red Team 다중 캐시 테스트 통과")


class TestCachingAsyncClient(unittest.TestCase):
    """캐싱 클라이언트 통합 테스트"""

    def setUp(self):
        """테스트 전 초기화"""
        Config.USE_MOCK_API = True
        self.client = CachingAsyncClient(use_mock_api=True)

    def test_first_request_no_cache(self):
        """첫 요청 (캐시 없음)"""
        async def run_test():
            start = time.time()
            result = await self.client.full_pipeline_cached()
            elapsed = time.time() - start

            self.assertIn('decision', result)
            self.assertIn('confidence', result)
            self.assertLess(elapsed, 0.5)  # 500ms 이내
            return elapsed

        elapsed = asyncio.run(run_test())
        print(f"✅ 첫 요청 (캐시 없음): {elapsed*1000:.1f}ms")

    def test_cached_request_performance(self):
        """캐시된 요청 성능"""
        async def run_test():
            # 첫 요청 (캐시 미스)
            await self.client.full_pipeline_cached()

            # 두 번째 요청 (캐시 히트)
            start = time.time()
            result = await self.client.full_pipeline_cached()
            elapsed = time.time() - start

            self.assertLess(elapsed, 0.05)  # 50ms 이내
            return elapsed

        elapsed = asyncio.run(run_test())

        # 캐시 통계 확인
        stats = self.client.get_cache_stats()
        hit_rate = stats['metrics']['hit_rate']

        print(f"✅ 캐시된 요청: {elapsed*1000:.1f}ms")
        print(f"   캐시 히트율: {hit_rate}")

    def test_cache_speedup(self):
        """캐시 속도 향상 검증"""
        async def run_test():
            # 첫 요청
            start = time.time()
            await self.client.full_pipeline_cached()
            time1 = time.time() - start

            # 캐시된 요청
            start = time.time()
            await self.client.full_pipeline_cached()
            time2 = time.time() - start

            return time1, time2

        time1, time2 = asyncio.run(run_test())

        speedup = time1 / time2
        improvement = (time1 - time2) / time1 * 100

        print(f"\n⚡ 캐싱 성능:")
        print(f"  첫 요청    : {time1*1000:6.1f}ms")
        print(f"  캐시 히트  : {time2*1000:6.1f}ms")
        print(f"  속도 향상  : {speedup:6.1f}x")
        print(f"  개선율    : {improvement:6.1f}%")

        # 성능 목표: 10배 이상 향상
        self.assertGreater(speedup, 10)

    def test_cache_clear(self):
        """캐시 삭제 테스트"""
        async def run_test():
            # 캐시 채우기
            await self.client.full_pipeline_cached()

            stats_before = self.client.get_cache_stats()

            # 캐시 삭제
            self.client.clear_all_caches()

            stats_after = self.client.get_cache_stats()

            self.assertEqual(stats_before['metrics']['size'], 1)
            self.assertEqual(stats_after['metrics']['size'], 0)

        asyncio.run(run_test())
        print("✅ 캐시 삭제 테스트 통과")

    def test_multiple_requests_cache_reuse(self):
        """여러 요청에서 캐시 재사용"""
        async def run_test():
            # 5개 요청 실행
            for i in range(5):
                await self.client.full_pipeline_cached()

            stats = self.client.get_cache_stats()
            hit_rate = float(stats['metrics']['hit_rate'].rstrip('%'))

            # 첫 요청 제외, 4개 요청은 캐시 히트
            # 따라서 히트율은 약 80% (4/5)
            self.assertGreater(hit_rate, 70)

            return hit_rate

        hit_rate = asyncio.run(run_test())
        print(f"✅ 캐시 재사용: {hit_rate:.1f}% 히트율")


def run_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 70)
    print("🚀 MindLang Day 6: 캐싱 레이어 테스트")
    print("=" * 70 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 테스트 추가
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsCache))
    suite.addTests(loader.loadTestsFromTestCase(TestRedTeamCache))
    suite.addTests(loader.loadTestsFromTestCase(TestCachingAsyncClient))

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
        print("🎯 성능 목표 달성: <50ms + 10배 이상 속도 향상 ✨")
    else:
        print("\n❌ 일부 테스트 실패")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
