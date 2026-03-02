#!/usr/bin/env python3
"""
MindLang 캐싱 레이어
메트릭과 Red Team 분석 결과를 캐싱하여 성능 향상

구조:
├─ MetricsCache (메트릭 캐싱, TTL: 5분)
├─ RedTeamCache (Red Team 분석, TTL: 10분)
└─ CachingAsyncClient (통합)

성능 목표:
├─ 캐시 히트: <10ms
├─ 전체 응답: <50ms
└─ 처리량: 100+ req/sec
"""

import time
import asyncio
import json
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
from api_client_async import AsyncAPIClient
from mindlang_with_red_team import MindLangRedTeam
from config import Config
import logging

logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class MetricsCache:
    """메트릭 캐싱 (TTL: 5분)"""

    def __init__(self, ttl_seconds: int = 300):
        """
        메트릭 캐시 초기화

        Args:
            ttl_seconds: Time-To-Live (초), 기본값: 300초 (5분)
        """
        self.ttl = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key not in self.cache:
            self.stats['misses'] += 1
            return None

        value, timestamp = self.cache[key]
        elapsed = time.time() - timestamp

        # TTL 확인
        if elapsed > self.ttl:
            del self.cache[key]
            self.stats['evictions'] += 1
            self.stats['misses'] += 1
            logger.debug(f"🔄 캐시 만료: {key}")
            return None

        self.stats['hits'] += 1
        logger.debug(f"✅ 캐시 히트: {key} ({elapsed:.1f}초 경과)")
        return value

    def set(self, key: str, value: Any) -> None:
        """캐시에 값 저장"""
        self.cache[key] = (value, time.time())
        logger.debug(f"💾 캐시 저장: {key}")

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        logger.info("🗑️  캐시 전체 삭제")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
            'ttl_seconds': self.ttl
        }


class RedTeamCache:
    """Red Team 분석 결과 캐싱 (TTL: 10분)"""

    def __init__(self, ttl_seconds: int = 600):
        """
        Red Team 캐시 초기화

        Args:
            ttl_seconds: Time-To-Live (초), 기본값: 600초 (10분)
        """
        self.ttl = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }

    def _make_key(self, decision: str) -> str:
        """Red Team 분석 결과의 캐시 키 생성"""
        return f"red_team:{decision}"

    def get(self, decision: str) -> Optional[Any]:
        """Red Team 분석 결과 조회"""
        key = self._make_key(decision)

        if key not in self.cache:
            self.stats['misses'] += 1
            return None

        value, timestamp = self.cache[key]
        elapsed = time.time() - timestamp

        # TTL 확인
        if elapsed > self.ttl:
            del self.cache[key]
            self.stats['evictions'] += 1
            self.stats['misses'] += 1
            logger.debug(f"🔄 Red Team 캐시 만료: {decision}")
            return None

        self.stats['hits'] += 1
        logger.debug(f"✅ Red Team 캐시 히트: {decision} ({elapsed:.1f}초)")
        return value

    def set(self, decision: str, value: Any) -> None:
        """Red Team 분석 결과 저장"""
        key = self._make_key(decision)
        self.cache[key] = (value, time.time())
        logger.debug(f"💾 Red Team 캐시 저장: {decision}")

    def clear(self) -> None:
        """캐시 전체 삭제"""
        self.cache.clear()
        logger.info("🗑️  Red Team 캐시 전체 삭제")

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache),
            'ttl_seconds': self.ttl
        }


class CachingAsyncClient:
    """캐싱을 포함한 비동기 API 클라이언트"""

    def __init__(self, use_mock_api: bool = True, metrics_ttl: int = 300, redteam_ttl: int = 600):
        """
        캐싱 클라이언트 초기화

        Args:
            use_mock_api: Mock API 사용 여부
            metrics_ttl: 메트릭 캐시 TTL (초)
            redteam_ttl: Red Team 캐시 TTL (초)
        """
        self.async_client = AsyncAPIClient(use_mock_api=use_mock_api)
        self.mindlang = MindLangRedTeam()

        self.metrics_cache = MetricsCache(ttl_seconds=metrics_ttl)
        self.redteam_cache = RedTeamCache(ttl_seconds=redteam_ttl)

        logger.info(f"✓ 캐싱 클라이언트 초기화")
        logger.info(f"  메트릭 캐시 TTL: {metrics_ttl}초 (5분)")
        logger.info(f"  Red Team 캐시 TTL: {redteam_ttl}초 (10분)")

    async def collect_metrics_cached(self) -> Dict[str, Any]:
        """캐싱된 메트릭 수집"""
        cache_key = "all_metrics"

        # 캐시 확인
        cached = self.metrics_cache.get(cache_key)
        if cached is not None:
            return cached

        # 캐시 미스: 실제 수집
        logger.info("📊 메트릭 수집 중 (캐시 미스)...")
        start = time.time()
        result = await self.async_client.collect_all_metrics()
        elapsed = time.time() - start

        # 캐시에 저장
        self.metrics_cache.set(cache_key, result)
        logger.info(f"✓ 메트릭 수집 완료: {elapsed*1000:.1f}ms")

        return result

    async def analyze_with_redteam_cached(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """캐싱된 Red Team 분석"""
        # MindLang 분석 (항상 실행)
        start = time.time()
        analysis = self.mindlang.analyze(metrics)
        elapsed = time.time() - start

        primary_decision = analysis['primary_decision']['action']

        # Red Team 분석 캐시 확인
        cached_redteam = self.redteam_cache.get(primary_decision)
        if cached_redteam is not None:
            logger.info(f"✅ Red Team 캐시 사용: {primary_decision}")
            analysis['red_team'] = cached_redteam
        else:
            # Red Team 분석은 이미 MindLang에 포함됨
            self.redteam_cache.set(primary_decision, analysis['red_team'])

        return {
            'analysis': analysis,
            'collection_time': analysis.get('total_collection_time', 0),
            'analysis_time': elapsed
        }

    async def full_pipeline_cached(self) -> Dict[str, Any]:
        """전체 파이프라인 (캐싱 포함)"""
        logger.info("\n" + "="*70)
        logger.info("🚀 MindLang Full Pipeline (캐싱)")
        logger.info("="*70)

        start = time.time()

        # 메트릭 수집 (캐싱)
        metrics = await self.collect_metrics_cached()

        # MindLang 분석 (Red Team 캐싱)
        result = await self.analyze_with_redteam_cached(metrics)

        total_time = time.time() - start

        logger.info(f"\n✅ 전체 파이프라인 완료: {total_time*1000:.1f}ms")
        logger.info("="*70 + "\n")

        return {
            'decision': result['analysis']['primary_decision']['action'],
            'confidence': result['analysis']['primary_decision']['confidence'],
            'collection_time': result['collection_time'],
            'analysis_time': result['analysis_time'],
            'total_time': total_time,
            'metrics_cache_stats': self.metrics_cache.get_stats(),
            'redteam_cache_stats': self.redteam_cache.get_stats()
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return {
            'metrics': self.metrics_cache.get_stats(),
            'redteam': self.redteam_cache.get_stats()
        }

    def clear_all_caches(self) -> None:
        """모든 캐시 삭제"""
        self.metrics_cache.clear()
        self.redteam_cache.clear()


# ============================================================================
# 성능 벤치마크
# ============================================================================

async def benchmark_caching():
    """캐싱 성능 벤치마크"""
    print("\n" + "="*70)
    print("📊 캐싱 성능 벤치마크")
    print("="*70)

    client = CachingAsyncClient(use_mock_api=True)

    print("\n📈 **첫 번째 요청 (캐시 미스)**")
    start = time.time()
    result1 = await client.full_pipeline_cached()
    time1 = time.time() - start

    print(f"  응답 시간: {time1*1000:.1f}ms")
    print(f"  결정: {result1['decision']}")
    print(f"  신뢰도: {result1['confidence']*100:.0f}%")

    print("\n📈 **두 번째 요청 (캐시 히트)**")
    start = time.time()
    result2 = await client.full_pipeline_cached()
    time2 = time.time() - start

    print(f"  응답 시간: {time2*1000:.1f}ms")
    print(f"  캐시로부터: {time1/time2:.1f}배 빠름 ⚡")

    print("\n📊 **캐시 통계**")
    stats = client.get_cache_stats()

    print(f"\n메트릭 캐시:")
    for key, value in stats['metrics'].items():
        print(f"  {key}: {value}")

    print(f"\nRed Team 캐시:")
    for key, value in stats['redteam'].items():
        print(f"  {key}: {value}")

    print("\n📈 **성능 개선**")
    improvement = (time1 - time2) / time1 * 100
    speedup = time1 / time2

    print(f"  응답 시간 감소: {improvement:.1f}%")
    print(f"  속도 향상: {speedup:.1f}x")

    if time2 < 0.05:  # 50ms
        print(f"\n✅ 성능 목표 달성: <50ms ✨")
    else:
        print(f"\n⚠️  성능 목표 미달: {time2*1000:.1f}ms (목표: <50ms)")

    print("="*70 + "\n")

    return {
        'first_request': time1,
        'cached_request': time2,
        'improvement': improvement,
        'speedup': speedup
    }


if __name__ == "__main__":
    result = asyncio.run(benchmark_caching())

    print(f"\n📋 **벤치마크 결과**")
    print(f"  첫 요청: {result['first_request']*1000:.1f}ms")
    print(f"  캐시 히트: {result['cached_request']*1000:.1f}ms")
    print(f"  개선율: {result['improvement']:.1f}%")
    print(f"  속도 향상: {result['speedup']:.1f}x\n")
