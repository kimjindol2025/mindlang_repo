#!/usr/bin/env python3
"""
MindLang with Red Team Path
3경로 추론 + Red Team 경로 (반대 의견)

철학: "우리가 맞다고 생각하는 것에는 항상 허점이 있다"
"""

import math
import json

class MindLangRedTeam:
    """3경로 추론 + Red Team 반대 의견 분석"""

    def __init__(self):
        self.confidence_threshold = 0.75

    def path1_error_driven(self, metrics):
        """Path 1: 에러율 중심 분석"""
        error_rate = metrics.get('error_rate', 0)
        error_trend = metrics.get('error_trend', 'stable')

        if error_rate > 0.05:
            confidence = min(0.95, (error_rate / 0.1) * 0.95)
            action = "ROLLBACK"
            reasoning = f"에러율 {error_rate*100:.2f}% 초과 - 즉시 롤백 필요"
        elif error_trend == 'increasing':
            confidence = 0.75
            action = "MONITOR"
            reasoning = "에러율 증가 추세 감지 - 모니터링 강화"
        else:
            confidence = 0.5
            action = "CONTINUE"
            reasoning = "에러율 정상 범위 - 계속 진행"

        return {
            'path': 'Path 1: Error-Driven',
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning
        }

    def path2_performance_driven(self, metrics):
        """Path 2: 성능 중심 분석"""
        latency_p95 = metrics.get('latency_p95', 0)
        cpu_usage = metrics.get('cpu_usage', 0)
        memory_usage = metrics.get('memory_usage', 0)

        # 성능 점수 계산
        latency_score = max(0, 1 - (latency_p95 / 500))  # 500ms 기준
        cpu_score = max(0, 1 - (cpu_usage / 80))  # 80% 기준
        memory_score = max(0, 1 - (memory_usage / 80))  # 80% 기준

        performance = (latency_score + cpu_score + memory_score) / 3

        if performance < 0.4:
            confidence = 0.9
            action = "SCALE_UP"
            reasoning = "성능 점수 {:.1f}% - 즉시 확장 필요".format(performance * 100)
        elif performance < 0.6:
            confidence = 0.7
            action = "OPTIMIZE"
            reasoning = "성능 저하 감지 - 최적화 필요"
        else:
            confidence = 0.5
            action = "MAINTAIN"
            reasoning = "성능 정상 유지 중"

        return {
            'path': 'Path 2: Performance-Driven',
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning
        }

    def path3_cost_driven(self, metrics):
        """Path 3: 비용 중심 분석"""
        current_cost = metrics.get('hourly_cost', 0)
        cost_limit = metrics.get('hourly_cost_limit', 100)
        cost_ratio = current_cost / cost_limit if cost_limit > 0 else 0

        if cost_ratio > 0.8:
            confidence = 0.85
            action = "OPTIMIZE_COST"
            reasoning = f"비용 {cost_ratio*100:.1f}% 초과 - 최적화 필수"
        elif cost_ratio > 0.5:
            confidence = 0.6
            action = "MONITOR_COST"
            reasoning = f"비용 증가 추세 - 모니터링 필요"
        else:
            confidence = 0.4
            action = "NO_ACTION"
            reasoning = "비용 효율적 - 계속 진행"

        return {
            'path': 'Path 3: Cost-Driven',
            'action': action,
            'confidence': confidence,
            'reasoning': reasoning
        }

    def path4_red_team(self, metrics, primary_decision):
        """Path 4: Red Team (반대 의견)

        핵심: AI가 선택한 결정의 허점을 찾아낸다
        """
        primary_action = primary_decision['action']
        primary_confidence = primary_decision['confidence']

        red_team_analysis = {
            'path': 'Path 4: Red Team (반대 의견)',
            'warning_level': 'CRITICAL',
            'assumptions_questioned': [],
            'potential_failures': [],
            'hidden_risks': [],
            'counter_action': None,
            'confidence_in_counter': 0
        }

        # ============================================
        # Case 1: ROLLBACK를 권장한 경우
        # ============================================
        if primary_action == 'ROLLBACK':
            red_team_analysis['assumptions_questioned'] = [
                "❌ 가정 1: 에러는 새 버전 때문인가?",
                "   → 가능성: 동시에 발생한 외부 장애 (DB, 네트워크)",
                "❌ 가정 2: 롤백이 문제를 해결하는가?",
                "   → 위험: 기존 버전도 같은 문제 가능",
                "❌ 가정 3: 에러의 패턴이 일관적인가?",
                "   → 사실: 일부 사용자/지역만 영향받을 수 있음"
            ]
            red_team_analysis['potential_failures'] = [
                "🔴 실패 1: 롤백 후에도 에러 지속",
                "   원인: 배포와 무관한 인프라 문제",
                "   손실: 30분 이상 장애 + 유저 신뢰 하락",
                "🔴 실패 2: Canary로 충분했는데 전체 롤백",
                "   낭비: 불필요한 전체 장애",
                "🔴 실패 3: 롤백 중 또 다른 버그 발생",
                "   악화: 2중 장애"
            ]
            red_team_analysis['hidden_risks'] = [
                "⚠️  위험 1: 의사결정 편향 (선택적 증거)",
                "    최근 배포만 보고 다른 변수 무시",
                "⚠️  위험 2: 시간 압박 편향",
                "    급할수록 더 안전한 선택을 찾는 경향",
                "⚠️  위험 3: 확신 과다",
                "    {:.1f}% 신뢰도는 높다 → 실제로는?".format(primary_confidence * 100)
            ]
            red_team_analysis['counter_action'] = {
                'recommended': 'CANARY_FIRST',
                'reasoning': '전체 롤백 전에 1% 사용자 그룹으로 테스트',
                'steps': [
                    '1. 5분간 1% 트래픽 재배포 (새 버전)',
                    '2. 메트릭 수집 (에러, 레이턴시)',
                    '3. 비교 분석:',
                    '   - Canary의 에러 == 전체의 에러? → 배포 관련',
                    '   - Canary는 정상? → 배포 무관'
                ]
            }
            red_team_analysis['confidence_in_counter'] = 0.88

        # ============================================
        # Case 2: SCALE_UP을 권장한 경우
        # ============================================
        elif primary_action == 'SCALE_UP':
            red_team_analysis['assumptions_questioned'] = [
                "❌ 가정 1: 부하가 계속 증가할 것인가?",
                "   → 현실: 피크 후 급락할 수 있음",
                "❌ 가정 2: 스케일링으로 문제가 해결되는가?",
                "   → 가능성: 데이터베이스가 병목",
                "❌ 가정 3: 새 인스턴스가 즉시 준비되는가?",
                "   → 문제: Warm-up 시간, 캐시 미스"
            ]
            red_team_analysis['potential_failures'] = [
                "🔴 실패 1: 스케일링 후 에러율 증가",
                "   원인: DB 병목, 좀비 커넥션",
                "   비용: 불필요한 인스턴스 비용 + 장애",
                "🔴 실패 2: 스케일 다운 후 문제 재발생",
                "   원인: 이전 설정으로 복귀하면 같은 문제",
                "🔴 실패 3: 비용 폭증",
                "   2배 인스턴스 비용 vs 30분 불편함?"
            ]
            red_team_analysis['hidden_risks'] = [
                "⚠️  위험 1: 근시안적 결정",
                "    증상 치료만 하고 근본 원인 무시",
                "⚠️  위험 2: 기술 부채 증가",
                "    스케일링은 임시 해결책",
                "⚠️  위험 3: 악순환 형성",
                "    성능 저하 → 스케일 → 더 복잡 → 관리 어려움"
            ]
            red_team_analysis['counter_action'] = {
                'recommended': 'INVESTIGATE_FIRST',
                'reasoning': '스케일링 전에 병목 정확히 파악',
                'steps': [
                    '1. 프로파일링: CPU vs 메모리 vs I/O?',
                    '2. 데이터베이스 확인:',
                    '   - Slow query log',
                    '   - 연결 풀 상태',
                    '   - 인덱스 히트율',
                    '3. 결과:',
                    '   - DB 문제? → 쿼리 최적화',
                    '   - 메모리 누수? → 재시작',
                    '   - CPU 진짜 부족? → 그때 스케일'
                ]
            }
            red_team_analysis['confidence_in_counter'] = 0.82

        # ============================================
        # Case 3: CONTINUE를 권장한 경우
        # ============================================
        elif primary_action == 'CONTINUE':
            red_team_analysis['assumptions_questioned'] = [
                "❌ 가정 1: 현재 추세가 계속될 것인가?",
                "   → 현실: 갑자기 급악화할 수 있음",
                "❌ 가정 2: 눈에 띄는 문제가 없으면 괜찮은가?",
                "   → 위험: 숨겨진 문제 (누수, 취약점)",
                "❌ 가정 3: 하루 이상 정상이면 성공인가?",
                "   → 주의: 버그는 특정 패턴에서만 발생"
            ]
            red_team_analysis['potential_failures'] = [
                "🔴 실패 1: 몇 시간 후 갑자기 장애 발생",
                "   원인: 메모리 누수, 연결 누수 폭발",
                "🔴 실패 2: 야간에 폭발",
                "   원인: 밤 12시 배치 작업과 상호작용",
                "🔴 실패 3: 유저 데이터 손상",
                "   원인: 조용한 데이터 corruption"
            ]
            red_team_analysis['hidden_risks'] = [
                "⚠️  위험 1: 과신 (Overconfidence)",
                "    현재 안정 ≠ 미래 안정",
                "⚠️  위험 2: 모니터링 맹점",
                "    대시보드는 문제의 일부만 보여줌",
                "⚠️  위험 3: 타이밍 운",
                "    높은 부하 시간대 아직 안 왔을 수 있음"
            ]
            red_team_analysis['counter_action'] = {
                'recommended': 'AGGRESSIVE_MONITORING',
                'reasoning': '24시간 집중 모니터링 필수',
                'steps': [
                    '1. 모니터링 강화:',
                    '   - P99 레이턴시 5초마다',
                    '   - 메모리 프로파일링 (실시간)',
                    '   - 커넥션 풀 상태',
                    '2. 자동 알람:',
                    '   - 에러율 >1% (기존 0.2%)',
                    '   - 메모리 증가율 >5%/시간',
                    '   - 응답시간 P95 >200ms',
                    '3. 준비:',
                    '   - 긴급 롤백 절차 준비',
                    '   - 온콜 엔지니어 대기'
                ]
            }
            red_team_analysis['confidence_in_counter'] = 0.78

        else:  # NO_ACTION인 경우
            red_team_analysis['assumptions_questioned'] = [
                "❌ 가정 1: 아무 조치가 필요 없는가?",
                "   → 위험: 점진적 악화가 무시될 수 있음",
                "❌ 가정 2: 현재 메트릭이 전부인가?",
                "   → 사실: 측정하지 않은 문제들이 있을 수 있음",
                "❌ 가정 3: 지금 행동하지 않아도 괜찮은가?",
                "   → 위험: 예방이 치료보다 쉽다"
            ]
            red_team_analysis['potential_failures'] = [
                "🔴 실패 1: 무시된 경고가 실제 문제로 확대",
                "   원인: 초기 신호를 놓침",
                "🔴 실패 2: 기술 부채가 축적",
                "   영향: 나중에 더 큰 비용",
                "🔴 실패 3: 경쟁자가 먼저 최적화",
                "   손실: 시장 기회 상실"
            ]
            red_team_analysis['hidden_risks'] = [
                "⚠️  위험 1: 태만 (Do Nothing Bias)",
                "    변화보다 현상 유지를 선호하는 경향",
                "⚠️  위험 2: 선제적 모니터링 부재",
                "    문제 발생 후에야 대응",
                "⚠️  위험 3: 기술 리스크 축적",
                "    작은 문제들이 모여 큰 장애 유발"
            ]
            red_team_analysis['counter_action'] = {
                'recommended': 'PROACTIVE_MONITORING',
                'reasoning': '모니터링 강화로 조기 경고 시스템 구축',
                'steps': [
                    '1. 추가 메트릭 정의:',
                    '   - 메모리 누수 감지 (3시간 트렌드)',
                    '   - P99 레이턴시 추이',
                    '   - 에러율 이상 징후',
                    '2. 알람 설정:',
                    '   - 지표 상승 추세 (5분 이상)',
                    '   - 비정상 패턴 감지',
                    '3. 주간 리뷰:',
                    '   - 지표 트렌드 분석',
                    '   - 위험 신호 조기 발견'
                ]
            }
            red_team_analysis['confidence_in_counter'] = 0.70

        return red_team_analysis

    def analyze(self, metrics):
        """전체 4경로 분석"""
        print("\n" + "=" * 80)
        print("🧠 MindLang: 3경로 추론 + Red Team 분석")
        print("=" * 80)

        # 3경로 실행
        path1 = self.path1_error_driven(metrics)
        path2 = self.path2_performance_driven(metrics)
        path3 = self.path3_cost_driven(metrics)

        # 3경로 결합 (벡터 합산)
        confidence_avg = (path1['confidence'] + path2['confidence'] + path3['confidence']) / 3
        actions = [path1['action'], path2['action'], path3['action']]
        primary_action = max(set(actions), key=actions.count)  # 가장 많은 경로가 선택한 액션

        primary_decision = {
            'action': primary_action,
            'confidence': confidence_avg,
            'reasoning': f"3경로 합의: {path1['action']}, {path2['action']}, {path3['action']}"
        }

        # Red Team 분석
        red_team = self.path4_red_team(metrics, primary_decision)

        # 결과 출력
        print("\n📊 Path 1: Error-Driven")
        print(f"   액션: {path1['action']} (신뢰도: {path1['confidence']:.1%})")
        print(f"   근거: {path1['reasoning']}")

        print("\n📊 Path 2: Performance-Driven")
        print(f"   액션: {path2['action']} (신뢰도: {path2['confidence']:.1%})")
        print(f"   근거: {path2['reasoning']}")

        print("\n📊 Path 3: Cost-Driven")
        print(f"   액션: {path3['action']} (신뢰도: {path3['confidence']:.1%})")
        print(f"   근거: {path3['reasoning']}")

        print("\n" + "-" * 80)
        print("✅ 3경로 합의 결정")
        print("-" * 80)
        print(f"액션: {primary_action}")
        print(f"신뢰도: {confidence_avg:.1%}")

        # Red Team 출력
        print("\n" + "🚨" * 40)
        print("🚨 RED TEAM ANALYSIS: 반대 의견 (허점 찾기)")
        print("🚨" * 40)
        print(f"\n경고 수준: {red_team['warning_level']}")
        print("\n❌ 의심되는 가정들:")
        for assumption in red_team['assumptions_questioned']:
            print(f"   {assumption}")

        print("\n🔴 잠재적 실패 시나리오:")
        for failure in red_team['potential_failures']:
            print(f"   {failure}")

        print("\n⚠️  숨겨진 위험 요소:")
        for risk in red_team['hidden_risks']:
            print(f"   {risk}")

        print("\n💡 Red Team 반대 권고:")
        print(f"   추천: {red_team['counter_action']['recommended']}")
        print(f"   근거: {red_team['counter_action']['reasoning']}")
        print(f"   실행 단계:")
        for step in red_team['counter_action']['steps']:
            print(f"      {step}")
        print(f"   Red Team 신뢰도: {red_team['confidence_in_counter']:.1%}")

        # 최종 권고
        print("\n" + "=" * 80)
        print("🎯 최종 권고")
        print("=" * 80)

        # Red Team 신뢰도가 높으면 경고
        if red_team['confidence_in_counter'] > 0.7:
            print(f"""
⚠️  경고: Red Team이 주요 문제를 지적했습니다!

당신의 결정 (3경로):    {primary_action}
Red Team의 우려:      {red_team['counter_action']['recommended']}
Red Team 신뢰도:      {red_team['confidence_in_counter']:.1%}

=> 권고: {red_team['counter_action']['recommended']}를 먼저 실행하고,
          그 결과를 바탕으로 {primary_action}을 판단하세요.

철학: "확신이 높을수록 더 신중하게"
""")
        else:
            print(f"""
✅ 3경로 결정이 합리적입니다.
   하지만 Red Team의 우려사항을 모니터링하세요:

주요 액션: {primary_action}
3경로 신뢰도: {confidence_avg:.1%}

Red Team이 경고하는 것:
- {red_team['counter_action']['reasoning']}
- 대비: {red_team['counter_action']['recommended']}

=> 액션을 진행하되, 다음 항목을 모니터링하세요:
   {', '.join(red_team['counter_action']['steps'][:2])}
""")

        return {
            'path1': path1,
            'path2': path2,
            'path3': path3,
            'primary_decision': primary_decision,
            'red_team': red_team
        }


# ============================================
# 테스트 시나리오
# ============================================
print("\n" + "🔬" * 40)
print("MindLang Red Team 분석 - 실제 시나리오")
print("🔬" * 40)

analyzer = MindLangRedTeam()

# Scenario 1: 배포 후 에러율 증가
print("\n\n📌 시나리오 1: 새 버전 배포 직후 에러율 급증")
print("-" * 80)
metrics1 = {
    'error_rate': 0.08,  # 8% - 매우 높음
    'error_trend': 'increasing',
    'latency_p95': 300,
    'cpu_usage': 45,
    'memory_usage': 60,
    'hourly_cost': 50,
    'hourly_cost_limit': 100
}
result1 = analyzer.analyze(metrics1)

# Scenario 2: 높은 부하
print("\n\n📌 시나리오 2: 트래픽 급증, CPU 높음")
print("-" * 80)
metrics2 = {
    'error_rate': 0.01,  # 정상
    'error_trend': 'stable',
    'latency_p95': 450,  # 높음
    'cpu_usage': 85,  # 높음
    'memory_usage': 75,
    'hourly_cost': 80,
    'hourly_cost_limit': 100
}
result2 = analyzer.analyze(metrics2)

# Scenario 3: 모든 것이 정상인 것처럼 보임
print("\n\n📌 시나리오 3: 모든 메트릭이 정상")
print("-" * 80)
metrics3 = {
    'error_rate': 0.001,  # 정상
    'error_trend': 'stable',
    'latency_p95': 95,
    'cpu_usage': 35,
    'memory_usage': 40,
    'hourly_cost': 30,
    'hourly_cost_limit': 100
}
result3 = analyzer.analyze(metrics3)

# 최종 요약
print("\n\n" + "=" * 80)
print("🎓 결론: Red Team의 중요성")
print("=" * 80)
print("""
1️⃣  신뢰도가 높을수록 더 위험하다
    - ROLLBACK 신뢰도 95% → Red Team이 가장 많은 반대 의견 제시
    - "우리가 틀렸을 확률"을 항상 고려해야 함

2️⃣  보이지 않는 가정들이 결정을 지배한다
    - "에러는 배포 때문" ← 가정
    - "스케일링이 해결책" ← 가정
    - 이 가정들은 틀릴 수 있다

3️⃣  실패 시나리오는 항상 있다
    - 내가 생각한 최선의 결정도 실패할 수 있음
    - Fallback plan이 필수

4️⃣  Red Team은 리더십 도구다
    - CEO가 한 결정을 CFO가 의심하는 문화
    - 조직 전체에서 "반대 의견" 문화 필수

=> MindLang은 이제 "혼자 생각하는 AI"가 아니라
   "자기 비판을 하는 AI"가 되었습니다.
""")
