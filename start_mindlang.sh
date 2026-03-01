#!/bin/bash

###############################################################################
# MindLang 완전 시스템 시작 스크립트
# 모든 서비스를 한 명령어로 시작
###############################################################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

###############################################################################
# 메인 실행
###############################################################################

main() {
    clear

    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║          🧠 MindLang 완전 시스템 시작 스크립트                 ║"
    echo "║                                                                ║"
    echo "║     다중 AI 의사결정 시스템 v3.0 - 프로덕션 레디              ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # 1. 환경 확인
    log_info "환경 확인 중..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3이 설치되어 있지 않습니다"
        exit 1
    fi

    if ! command -v git &> /dev/null; then
        log_error "Git이 설치되어 있지 않습니다"
        exit 1
    fi

    log_success "환경 확인 완료"
    echo ""

    # 2. 의존성 설치
    log_info "필수 라이브러리 설치 확인 중..."

    if [ -f "requirements.txt" ]; then
        pip install -q -r requirements.txt
        log_success "라이브러리 설치 완료"
    else
        log_warning "requirements.txt를 찾을 수 없습니다"
    fi
    echo ""

    # 3. 설정 초기화
    log_info "설정 초기화 중..."

    python3 config_manager.py reset &> /dev/null || true
    python3 backup_recovery.py list &> /dev/null || true

    log_success "설정 초기화 완료"
    echo ""

    # 4. 테스트 실행 (선택사항)
    if [ "$1" == "--test" ]; then
        log_info "자동 테스트 실행 중..."
        echo ""
        python3 test_suite.py || log_warning "일부 테스트가 실패했습니다"
        echo ""
    fi

    # 5. 백업 생성
    log_info "자동 백업 생성 중..."

    python3 backup_recovery.py full-backup &> /dev/null || log_warning "백업 생성 실패"
    python3 backup_recovery.py cleanup 30 &> /dev/null || true

    log_success "백업 생성 완료"
    echo ""

    # 6. 서비스 시작
    log_info "모든 서비스 시작 중..."
    echo ""

    python3 orchestrator.py start &
    ORCHESTRATOR_PID=$!

    # 서비스 시작 대기
    sleep 10

    log_success "서비스 시작 완료"
    echo ""

    # 7. 상태 확인
    log_info "시스템 상태 확인 중..."
    echo ""

    python3 orchestrator.py status || true
    echo ""

    # 8. 모니터링 시작 안내
    log_info "모니터링 대시보드 시작..."
    echo ""

    echo "🌐 웹 대시보드:"
    echo "   📊 실시간 대시보드: http://localhost:8000"
    echo "   📈 모니터링 v2:     http://localhost:9000"
    echo "   🔌 API Gateway:     http://localhost:8100"
    echo ""

    # 9. CLI 사용법 표시
    echo "💻 CLI 사용법:"
    echo "   python3 mindlang_cli.py decision cpu:85,mem:78 --verbose"
    echo "   python3 mindlang_cli.py analyze --report"
    echo "   python3 mindlang_cli.py status --detailed"
    echo ""

    # 10. 추가 명령어
    echo "⚙️  관리 명령어:"
    echo "   python3 config_manager.py show           # 설정 보기"
    echo "   python3 backup_recovery.py list          # 백업 목록"
    echo "   python3 test_suite.py                    # 테스트 실행"
    echo ""

    # 11. 최종 상태
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║                   🚀 MindLang 시스템 준비 완료!              ║"
    echo "║                                                                ║"
    echo "║              모든 서비스가 정상 작동 중입니다                 ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    # 12. 모니터링 대시보드 시작
    log_info "모니터링 대시보드를 시작하시겠습니까? (y/n)"
    read -r response

    if [ "$response" == "y" ] || [ "$response" == "Y" ]; then
        log_info "모니터링 대시보드 시작 중 (http://localhost:9000)..."
        python3 monitoring_dashboard_v2.py &

        log_info "모니터링을 시작하시겠습니까? (y/n)"
        read -r monitor_response

        if [ "$monitor_response" == "y" ] || [ "$monitor_response" == "Y" ]; then
            python3 orchestrator.py monitor
        fi
    fi
}

# 정리 함수
cleanup() {
    log_warning "시스템 종료 중..."
    python3 orchestrator.py stop || true
    log_success "시스템 종료 완료"
}

# Ctrl+C 처리
trap cleanup SIGINT SIGTERM

# 메인 실행
main "$@"
