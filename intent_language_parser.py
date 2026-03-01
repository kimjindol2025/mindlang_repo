#!/usr/bin/env python3
"""
Intent Language Parser
자연어 명령어를 의도(Intent)로 파싱

예:
  "CPU가 80% 넘으니까 스케일 업 해"
  → Intent: SCALE_UP, Confidence: 0.92, Conditions: [cpu > 80]

철학: 자연어 해석은 명확해야 한다
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple


class Intent(Enum):
    """인식할 수 있는 의도"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    ROLLBACK = "rollback"
    CONTINUE = "continue"
    MONITOR = "monitor"
    RESTART = "restart"
    UPDATE = "update"
    UNKNOWN = "unknown"


class Severity(Enum):
    """심각도"""
    CRITICAL = "critical"    # 즉시 조치 필요
    HIGH = "high"            # 높은 우선순위
    MEDIUM = "medium"        # 중간 우선순위
    LOW = "low"              # 낮은 우선순위


@dataclass
class ParsedIntent:
    """파싱된 의도"""
    intent: Intent
    confidence: float
    severity: Severity
    conditions: List[str]
    reasoning: str
    original_text: str

    def __str__(self) -> str:
        return (f"Intent: {self.intent.value} "
                f"({self.confidence*100:.0f}%) "
                f"[{self.severity.value}]\n"
                f"  조건: {', '.join(self.conditions)}\n"
                f"  근거: {self.reasoning}")


class IntentLanguageParser:
    """자연어 의도 파서"""

    def __init__(self):
        # 의도별 키워드
        self.intent_patterns = {
            Intent.SCALE_UP: [
                r'스케일\s*업|scale\s*up|확대|늘려?|증가',
                r'cpu.*높|부하.*높|트래픽.*많',
                r'인스턴스.*추가|서버.*늘려?'
            ],
            Intent.SCALE_DOWN: [
                r'스케일\s*다운|scale\s*down|축소|줄려?|감소',
                r'cpu.*낮|부하.*낮|트래픽.*적',
                r'인스턴스.*제거|서버.*줄려?'
            ],
            Intent.ROLLBACK: [
                r'롤백|roll\s*back|돌려?놓|이전\s*버전',
                r'문제|에러|오류|장애|실패',
                r'배포.*실패|배포.*문제'
            ],
            Intent.CONTINUE: [
                r'계속|continue|유지|그대로',
                r'정상|문제없|괜찮',
                r'진행하|진행해'
            ],
            Intent.MONITOR: [
                r'모니터링|monitor|감시|지켜?봐?|지켜줘',
                r'주시|살펴봐?|체크',
                r'경과\s*지켜?봐'
            ],
            Intent.RESTART: [
                r'재시작|restart|다시\s*시작|리셋',
                r'초기화|reset|새로\s*시작',
                r'서비스.*재시작'
            ],
            Intent.UPDATE: [
                r'업데이트|update|패치|새\s*버전',
                r'배포|deploy|출시',
                r'개선|수정|버그\s*수정'
            ]
        }

        # 심각도 패턴
        self.severity_patterns = {
            Severity.CRITICAL: [
                r'즉시|긴급|ASAP|critical|매우\s*심각',
                r'지금\s*당장|서둘러|빨리',
                r'장애|다운|크래시'
            ],
            Severity.HIGH: [
                r'높|중요|priority|urgent',
                r'빠르|ASAP아닌데도',
                r'주의|주의(?!할)'
            ],
            Severity.MEDIUM: [
                r'중간|normal|보통',
                r'여유있게|괜찮|조금'
            ],
            Severity.LOW: [
                r'낮|minor|천천히|언제든',
                r'급하지|여유롭'
            ]
        }

        # 조건 추출 패턴
        self.condition_patterns = [
            (r'cpu[가\s]*(\d+)%?', lambda m: f"cpu > {m.group(1)}%"),
            (r'메모리[가\s]*(\d+)%?', lambda m: f"memory > {m.group(1)}%"),
            (r'에러율[이\s]*(\d+)%?', lambda m: f"error_rate > {m.group(1)}%"),
            (r'지연[이\s]*(\d+)ms?', lambda m: f"latency > {m.group(1)}ms"),
            (r'트래픽.*(\d+)', lambda m: f"traffic > {m.group(1)}"),
        ]

    def parse(self, text: str) -> ParsedIntent:
        """자연어 텍스트를 의도로 파싱"""
        text_lower = text.lower()

        # 1단계: 의도 인식
        intent, intent_confidence = self._recognize_intent(text_lower)

        # 2단계: 심각도 판단
        severity = self._determine_severity(text_lower)

        # 3단계: 조건 추출
        conditions = self._extract_conditions(text_lower)

        # 4단계: 근거 생성
        reasoning = self._generate_reasoning(intent, conditions, severity)

        # 5단계: 최종 신뢰도 계산
        final_confidence = self._calculate_confidence(
            intent_confidence, conditions, severity
        )

        return ParsedIntent(
            intent=intent,
            confidence=final_confidence,
            severity=severity,
            conditions=conditions,
            reasoning=reasoning,
            original_text=text
        )

    def _recognize_intent(self, text: str) -> Tuple[Intent, float]:
        """의도 인식"""
        scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    matches += 1
                    score += 0.3

            if matches > 0:
                scores[intent] = score

        if not scores:
            return Intent.UNKNOWN, 0.0

        best_intent = max(scores, key=scores.get)
        confidence = min(0.99, scores[best_intent])

        return best_intent, confidence

    def _determine_severity(self, text: str) -> Severity:
        """심각도 판단"""
        for severity, patterns in self.severity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return severity

        return Severity.MEDIUM

    def _extract_conditions(self, text: str) -> List[str]:
        """조건 추출"""
        conditions = []

        for pattern, converter in self.condition_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                condition = converter(match)
                conditions.append(condition)

        return conditions if conditions else ["no specific conditions"]

    def _generate_reasoning(self,
                          intent: Intent,
                          conditions: List[str],
                          severity: Severity) -> str:
        """근거 생성"""
        if intent == Intent.UNKNOWN:
            return "인식할 수 없는 의도"

        if conditions[0] == "no specific conditions":
            return f"{intent.value} 의도 감지 (구체적 조건 없음)"

        conditions_str = ", ".join(conditions)
        return f"{intent.value} (조건: {conditions_str}) [심각도: {severity.value}]"

    def _calculate_confidence(self,
                            intent_confidence: float,
                            conditions: List[str],
                            severity: Severity) -> float:
        """최종 신뢰도 계산"""
        confidence = intent_confidence

        # 조건이 구체적일수록 신뢰도 증가
        if conditions[0] != "no specific conditions":
            confidence = min(0.99, confidence + 0.1 * len(conditions))

        # 심각도가 높을수록 신뢰도 감소 (재확인 필요)
        if severity in [Severity.CRITICAL, Severity.HIGH]:
            confidence *= 0.9  # 재확인 권장

        return confidence

    def parse_batch(self, texts: List[str]) -> List[ParsedIntent]:
        """배치 파싱"""
        return [self.parse(text) for text in texts]


# 사용 예시
if __name__ == "__main__":
    parser = IntentLanguageParser()

    test_cases = [
        "CPU가 80% 넘으니까 스케일 업 해",
        "에러율이 5% 이상이면 롤백해줘. 긴급이야!",
        "메모리 사용량을 주시해줄 수 있어?",
        "트래픽 많으니까 인스턴스 추가하자",
        "문제 없으니까 계속 진행",
    ]

    print("🔍 Intent Language Parser 테스트\n")
    print("=" * 60)

    for text in test_cases:
        result = parser.parse(text)
        print(f"\n📝 입력: {text}")
        print(result)
        print("-" * 60)
