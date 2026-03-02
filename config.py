#!/usr/bin/env python3
"""
MindLang Configuration Module
외부 API를 실제 서비스 또는 Mock으로 선택하는 설정

사용 방법:
    from config import Config

    # 환경 변수로 설정
    export USE_MOCK_API=true

    # 또는 프로그래밍으로 설정
    Config.USE_MOCK_API = True
"""

import os
from typing import Dict, Optional


class Config:
    """MindLang 설정 클래스"""

    # ========================================================================
    # API 설정
    # ========================================================================

    # Mock API 사용 여부
    USE_MOCK_API: bool = os.getenv("USE_MOCK_API", "false").lower() == "true"

    # Mock API 서버 주소
    MOCK_API_HOST: str = os.getenv("MOCK_API_HOST", "localhost")
    MOCK_API_PORT: int = int(os.getenv("MOCK_API_PORT", "8000"))

    # 실제 API 서버 주소들
    PROMETHEUS_HOST: str = os.getenv("PROMETHEUS_HOST", "http://localhost:9090")
    KUBERNETES_HOST: str = os.getenv("KUBERNETES_HOST", "http://localhost:6443")
    ALERTMANAGER_HOST: str = os.getenv("ALERTMANAGER_HOST", "http://localhost:9093")
    DOCKER_REGISTRY_HOST: str = os.getenv(
        "DOCKER_REGISTRY_HOST", "http://localhost:5000"
    )
    DATADOG_HOST: str = os.getenv("DATADOG_HOST", "https://api.datadoghq.com")
    DATADOG_API_KEY: str = os.getenv("DATADOG_API_KEY", "")

    # ========================================================================
    # 데이터베이스 설정
    # ========================================================================

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./mindlang.db"
    )

    # ========================================================================
    # 로깅 설정
    # ========================================================================

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "mindlang.log")

    # ========================================================================
    # 성능 설정
    # ========================================================================

    # 메트릭 수집 간격 (초)
    METRICS_COLLECTION_INTERVAL: int = int(
        os.getenv("METRICS_COLLECTION_INTERVAL", "30")
    )

    # 배치 크기
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "100"))

    # 스레드 풀 크기
    THREAD_POOL_SIZE: int = int(os.getenv("THREAD_POOL_SIZE", "10"))

    # ========================================================================
    # MindLang 설정
    # ========================================================================

    # 3경로 가중치
    PATH1_WEIGHT: float = float(os.getenv("PATH1_WEIGHT", "0.5"))  # Error-Driven
    PATH2_WEIGHT: float = float(os.getenv("PATH2_WEIGHT", "0.3"))  # Performance-Driven
    PATH3_WEIGHT: float = float(os.getenv("PATH3_WEIGHT", "0.2"))  # Cost-Driven

    # Red Team 검증 활성화
    ENABLE_RED_TEAM: bool = os.getenv("ENABLE_RED_TEAM", "true").lower() == "true"

    # 신뢰도 임계값
    HIGH_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.7")
    )
    MEDIUM_CONFIDENCE_THRESHOLD: float = float(
        os.getenv("MEDIUM_CONFIDENCE_THRESHOLD", "0.5")
    )

    # ========================================================================
    # 테스트 설정
    # ========================================================================

    # 테스트 모드
    TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"

    # Mock 데이터 재현성 (시드)
    RANDOM_SEED: Optional[int] = (
        int(os.getenv("RANDOM_SEED", "0"))
        if os.getenv("RANDOM_SEED")
        else None
    )

    # ========================================================================
    # 메서드
    # ========================================================================

    @classmethod
    def get_api_url(cls, service: str) -> str:
        """서비스별 API URL 반환"""
        if cls.USE_MOCK_API:
            return f"http://{cls.MOCK_API_HOST}:{cls.MOCK_API_PORT}"

        service_urls = {
            "prometheus": cls.PROMETHEUS_HOST,
            "kubernetes": cls.KUBERNETES_HOST,
            "alertmanager": cls.ALERTMANAGER_HOST,
            "docker_registry": cls.DOCKER_REGISTRY_HOST,
            "datadog": cls.DATADOG_HOST,
        }
        return service_urls.get(service.lower(), "")

    @classmethod
    def enable_mock_api(cls) -> None:
        """Mock API 활성화"""
        cls.USE_MOCK_API = True
        print("✅ Mock API enabled")

    @classmethod
    def disable_mock_api(cls) -> None:
        """Mock API 비활성화"""
        cls.USE_MOCK_API = False
        print("❌ Mock API disabled")

    @classmethod
    def print_config(cls) -> None:
        """설정 정보 출력"""
        print("\n" + "=" * 60)
        print("MindLang Configuration")
        print("=" * 60)
        print(f"USE_MOCK_API: {cls.USE_MOCK_API}")
        print(f"TEST_MODE: {cls.TEST_MODE}")
        print(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        print(f"PATH1_WEIGHT (Error): {cls.PATH1_WEIGHT}")
        print(f"PATH2_WEIGHT (Performance): {cls.PATH2_WEIGHT}")
        print(f"PATH3_WEIGHT (Cost): {cls.PATH3_WEIGHT}")
        print(f"ENABLE_RED_TEAM: {cls.ENABLE_RED_TEAM}")
        print(f"METRICS_COLLECTION_INTERVAL: {cls.METRICS_COLLECTION_INTERVAL}s")
        print("=" * 60 + "\n")

    @classmethod
    def to_dict(cls) -> Dict:
        """설정을 딕셔너리로 반환"""
        return {
            "USE_MOCK_API": cls.USE_MOCK_API,
            "TEST_MODE": cls.TEST_MODE,
            "LOG_LEVEL": cls.LOG_LEVEL,
            "PATH1_WEIGHT": cls.PATH1_WEIGHT,
            "PATH2_WEIGHT": cls.PATH2_WEIGHT,
            "PATH3_WEIGHT": cls.PATH3_WEIGHT,
            "ENABLE_RED_TEAM": cls.ENABLE_RED_TEAM,
            "METRICS_COLLECTION_INTERVAL": cls.METRICS_COLLECTION_INTERVAL,
            "HIGH_CONFIDENCE_THRESHOLD": cls.HIGH_CONFIDENCE_THRESHOLD,
            "MEDIUM_CONFIDENCE_THRESHOLD": cls.MEDIUM_CONFIDENCE_THRESHOLD,
        }


# ============================================================================
# 환경 변수 설정 가이드
# ============================================================================

ENV_EXAMPLE = """
# .env 파일 예제

# API 설정
USE_MOCK_API=true
MOCK_API_HOST=localhost
MOCK_API_PORT=8000

# 테스트 모드
TEST_MODE=true
RANDOM_SEED=42

# 로깅
LOG_LEVEL=DEBUG
LOG_FILE=mindlang.log

# MindLang 파라미터
PATH1_WEIGHT=0.5
PATH2_WEIGHT=0.3
PATH3_WEIGHT=0.2
ENABLE_RED_TEAM=true

# 메트릭
METRICS_COLLECTION_INTERVAL=5

# Red Team
HIGH_CONFIDENCE_THRESHOLD=0.7
MEDIUM_CONFIDENCE_THRESHOLD=0.5
"""


if __name__ == "__main__":
    # 설정 출력
    Config.print_config()

    # Mock API 테스트
    print("API URL Examples:")
    print(f"  Prometheus: {Config.get_api_url('prometheus')}")
    print(f"  Kubernetes: {Config.get_api_url('kubernetes')}")
    print(f"  AlertManager: {Config.get_api_url('alertmanager')}")

    # 환경 변수 예제 출력
    print("\n.env 파일 예제:")
    print(ENV_EXAMPLE)
