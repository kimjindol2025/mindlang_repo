#!/usr/bin/env python3
"""
pytest 설정 파일
MindLang Mock API 자동 활성화
"""

import pytest
import os
from config import Config

try:
    from api_client_simple import APIClient
except ImportError:
    # Fallback if api_client_simple not found
    APIClient = None


@pytest.fixture(scope="session", autouse=True)
def setup_mock_api_session():
    """테스트 세션 시작 시 Mock API 설정"""
    print("\n" + "=" * 70)
    print("🧠 MindLang Test Suite")
    print("=" * 70)

    # Mock API 활성화
    Config.USE_MOCK_API = True
    Config.TEST_MODE = True

    print(f"✅ Mock API: {'ENABLED' if Config.USE_MOCK_API else 'DISABLED'}")
    print(f"✅ Test Mode: {'ON' if Config.TEST_MODE else 'OFF'}")
    print(f"✅ API Host: {Config.MOCK_API_HOST}:{Config.MOCK_API_PORT}")
    print(f"✅ Weights: Path1={Config.PATH1_WEIGHT}, Path2={Config.PATH2_WEIGHT}, Path3={Config.PATH3_WEIGHT}")
    print(f"✅ Red Team: {'ENABLED' if Config.ENABLE_RED_TEAM else 'DISABLED'}")
    print("=" * 70 + "\n")

    yield

    print("\n" + "=" * 70)
    print("✅ Test session complete")
    print("=" * 70 + "\n")


@pytest.fixture(autouse=True)
def enable_mock_api():
    """모든 테스트에서 Mock API 자동 활성화"""
    original_use_mock = Config.USE_MOCK_API
    original_test_mode = Config.TEST_MODE

    # 테스트 시작 시 Mock API 활성화
    Config.USE_MOCK_API = True
    Config.TEST_MODE = True

    yield

    # 테스트 종료 시 원래 상태로 복원
    Config.USE_MOCK_API = original_use_mock
    Config.TEST_MODE = original_test_mode


@pytest.fixture
def api_client():
    """API 클라이언트 픽스처"""
    client = APIClient()
    yield client
    # 정리 작업 (필요시)


@pytest.fixture
def sample_metrics():
    """테스트용 샘플 메트릭"""
    return {
        'error_rate': 0.002,
        'error_trend': 'stable',
        'cpu_usage': 45,
        'memory_usage': 60,
        'latency_p95': 250,
        'throughput': 3000,
    }


@pytest.fixture
def high_error_metrics():
    """높은 에러율 메트릭"""
    return {
        'error_rate': 0.15,
        'error_trend': 'increasing',
        'cpu_usage': 40,
        'memory_usage': 50,
        'latency_p95': 300,
        'throughput': 2000,
    }


@pytest.fixture
def high_load_metrics():
    """높은 부하 메트릭"""
    return {
        'error_rate': 0.005,
        'cpu_usage': 92,
        'memory_usage': 88,
        'latency_p95': 800,
        'throughput': 8000,
    }


@pytest.fixture
def low_load_metrics():
    """낮은 부하 메트릭"""
    return {
        'error_rate': 0.001,
        'cpu_usage': 15,
        'memory_usage': 20,
        'latency_p95': 50,
        'throughput': 500,
    }


# 로그 설정
def pytest_configure(config):
    """pytest 설정"""
    # 환경 변수 설정
    os.environ['USE_MOCK_API'] = 'true'
    os.environ['TEST_MODE'] = 'true'
    os.environ['LOG_LEVEL'] = 'DEBUG'


def pytest_collection_modifyitems(config, items):
    """테스트 마커 추가"""
    for item in items:
        # 테스트 이름으로 마커 자동 지정
        if "prometheus" in item.nodeid:
            item.add_marker(pytest.mark.prometheus)
        if "k8s" in item.nodeid or "kubernetes" in item.nodeid:
            item.add_marker(pytest.mark.kubernetes)
        if "alert" in item.nodeid:
            item.add_marker(pytest.mark.alerts)
        if "path1" in item.nodeid:
            item.add_marker(pytest.mark.path1)
        if "path2" in item.nodeid:
            item.add_marker(pytest.mark.path2)
        if "path3" in item.nodeid:
            item.add_marker(pytest.mark.path3)
        if "red_team" in item.nodeid:
            item.add_marker(pytest.mark.red_team)


# pytest 마커 정의
pytest_plugins = []
