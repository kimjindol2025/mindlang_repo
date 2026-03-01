#!/usr/bin/env python3
"""
API Contract Testing Framework - Consumer-driven contract testing
Implements consumer-driven contract testing for API compatibility verification
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class ContractType(Enum):
    """Contract types"""
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    INTERACTION = "INTERACTION"


class TestStatus(Enum):
    """Test status"""
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class ContractInteraction:
    """API contract interaction"""
    interaction_id: str
    consumer: str
    provider: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    description: str
    created_at: float = field(default_factory=time.time)


@dataclass
class ContractTest:
    """Contract test"""
    test_id: str
    interaction_id: str
    status: TestStatus = TestStatus.PENDING
    actual_response: Optional[Dict] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    executed_at: Optional[float] = None


@dataclass
class ContractPact:
    """Pact between consumer and provider"""
    pact_id: str
    consumer_name: str
    provider_name: str
    interactions: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)


class APIContractTestingFramework:
    """
    API Contract Testing Framework

    Provides:
    - Consumer-driven contract testing
    - Pact generation
    - Contract verification
    - Breaking change detection
    - Version management
    - Contract publishing
    """

    def __init__(self):
        self.interactions: Dict[str, ContractInteraction] = {}
        self.tests: List[ContractTest] = []
        self.pacts: Dict[str, ContractPact] = {}
        self.test_results_history: List[Dict] = []
        self.breaking_changes: List[Dict] = []

    def define_interaction(self,
                         consumer: str,
                         provider: str,
                         description: str,
                         request: Dict[str, Any],
                         response: Dict[str, Any]) -> ContractInteraction:
        """Define API contract interaction"""
        interaction_id = hashlib.md5(
            f"{consumer}:{provider}:{description}:{time.time()}".encode()
        ).hexdigest()[:8]

        interaction = ContractInteraction(
            interaction_id=interaction_id,
            consumer=consumer,
            provider=provider,
            request=request,
            response=response,
            description=description
        )

        self.interactions[interaction_id] = interaction
        return interaction

    def create_pact(self,
                   consumer_name: str,
                   provider_name: str,
                   interaction_ids: List[str]) -> Optional[ContractPact]:
        """Create pact between consumer and provider"""
        pact_id = hashlib.md5(
            f"{consumer_name}:{provider_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        pact = ContractPact(
            pact_id=pact_id,
            consumer_name=consumer_name,
            provider_name=provider_name,
            interactions=interaction_ids
        )

        self.pacts[pact_id] = pact
        return pact

    def execute_contract_test(self,
                             interaction_id: str,
                             actual_response: Dict[str, Any]) -> ContractTest:
        """Execute contract test"""
        interaction = self.interactions.get(interaction_id)
        if not interaction:
            return None

        test_id = hashlib.md5(
            f"{interaction_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        start_time = time.time()
        test = ContractTest(
            test_id=test_id,
            interaction_id=interaction_id,
            actual_response=actual_response
        )

        # Check if response matches contract
        if self._compare_response(interaction.response, actual_response):
            test.status = TestStatus.PASSED
        else:
            test.status = TestStatus.FAILED
            test.error_message = "Response does not match contract"
            # Detect breaking changes
            self._detect_breaking_changes(interaction, actual_response)

        test.execution_time_ms = (time.time() - start_time) * 1000
        test.executed_at = time.time()

        self.tests.append(test)
        return test

    def _compare_response(self, expected: Dict, actual: Dict) -> bool:
        """Compare actual response with expected"""
        # Simple equality check (in real implementation, use deep comparison with type matching)
        if set(expected.keys()) != set(actual.keys()):
            return False

        for key in expected.keys():
            if isinstance(expected[key], dict) and isinstance(actual[key], dict):
                if not self._compare_response(expected[key], actual[key]):
                    return False
            elif expected[key] != actual[key]:
                return False

        return True

    def _detect_breaking_changes(self, interaction: ContractInteraction, actual_response: Dict):
        """Detect breaking changes in response"""
        expected = interaction.response

        # Check for missing fields
        missing_fields = set(expected.keys()) - set(actual_response.keys())
        if missing_fields:
            self.breaking_changes.append({
                "type": "MISSING_FIELDS",
                "interaction_id": interaction.interaction_id,
                "fields": list(missing_fields),
                "timestamp": time.time()
            })

        # Check for type changes
        for key in set(expected.keys()) & set(actual_response.keys()):
            if type(expected[key]) != type(actual_response[key]):
                self.breaking_changes.append({
                    "type": "TYPE_CHANGE",
                    "interaction_id": interaction.interaction_id,
                    "field": key,
                    "expected_type": str(type(expected[key])),
                    "actual_type": str(type(actual_response[key])),
                    "timestamp": time.time()
                })

    def get_pact_verification_status(self, pact_id: str) -> Dict:
        """Get verification status for pact"""
        pact = self.pacts.get(pact_id)
        if not pact:
            return {}

        pact_tests = [t for t in self.tests
                     if t.interaction_id in pact.interactions]

        passed = sum(1 for t in pact_tests if t.status == TestStatus.PASSED)
        failed = sum(1 for t in pact_tests if t.status == TestStatus.FAILED)
        total = len(pact_tests)

        return {
            "pact_id": pact_id,
            "consumer": pact.consumer_name,
            "provider": pact.provider_name,
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
        }

    def get_testing_stats(self) -> Dict:
        """Get contract testing statistics"""
        total_interactions = len(self.interactions)
        total_tests = len(self.tests)

        passed = sum(1 for t in self.tests if t.status == TestStatus.PASSED)
        failed = sum(1 for t in self.tests if t.status == TestStatus.FAILED)

        by_consumer = {}
        for interaction in self.interactions.values():
            consumer = interaction.consumer
            by_consumer[consumer] = by_consumer.get(consumer, 0) + 1

        return {
            "total_interactions": total_interactions,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total_tests * 100) if total_tests > 0 else 0,
            "pacts": len(self.pacts),
            "breaking_changes": len(self.breaking_changes),
            "by_consumer": by_consumer,
        }

    def generate_testing_report(self) -> str:
        """Generate contract testing report"""
        stats = self.get_testing_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              API CONTRACT TESTING FRAMEWORK REPORT                         ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Interactions: {stats['total_interactions']}
├─ Total Tests: {stats['total_tests']}
├─ Passed: {stats['passed']}
├─ Failed: {stats['failed']}
├─ Success Rate: {stats['success_rate']:.1f}%
├─ Pacts: {stats['pacts']}
└─ Breaking Changes: {stats['breaking_changes']}

👥 BY CONSUMER:
"""

        for consumer, count in stats['by_consumer'].items():
            report += f"  {consumer}: {count} interactions\n"

        if self.breaking_changes:
            report += f"\n⚠️  BREAKING CHANGES:\n"
            for change in self.breaking_changes[:5]:
                report += f"  {change['type']}: {change.get('field', 'multiple fields')}\n"

        return report

    def export_testing_config(self) -> str:
        """Export testing configuration"""
        stats = self.get_testing_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "pacts": [
                {
                    "consumer": p.consumer_name,
                    "provider": p.provider_name,
                    "version": p.version,
                    "interactions_count": len(p.interactions),
                }
                for p in self.pacts.values()
            ],
            "test_results": [
                {
                    "test_id": t.test_id,
                    "status": t.status.value,
                    "execution_time_ms": t.execution_time_ms,
                }
                for t in self.tests[-20:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📋 API Contract Testing Framework - Consumer-Driven Contracts")
    print("=" * 70)

    framework = APIContractTestingFramework()

    # Define interactions
    print("\n📝 Defining contract interactions...")
    int1 = framework.define_interaction(
        "web-app", "user-api",
        "Get user by ID",
        {"method": "GET", "path": "/users/123"},
        {"status": 200, "body": {"id": "123", "name": "Alice", "email": "alice@example.com"}}
    )
    int2 = framework.define_interaction(
        "mobile-app", "user-api",
        "Create user",
        {"method": "POST", "path": "/users", "body": {"name": "Bob"}},
        {"status": 201, "body": {"id": "456", "name": "Bob"}}
    )
    print(f"✅ Defined {len(framework.interactions)} interactions")

    # Create pacts
    print("\n📋 Creating pacts...")
    pact1 = framework.create_pact("web-app", "user-api", [int1.interaction_id, int2.interaction_id])
    pact2 = framework.create_pact("mobile-app", "user-api", [int2.interaction_id])
    print(f"✅ Created {len(framework.pacts)} pacts")

    # Execute tests
    print("\n🧪 Executing contract tests...")
    test1 = framework.execute_contract_test(int1.interaction_id, {"status": 200, "body": {"id": "123", "name": "Alice", "email": "alice@example.com"}})
    test2 = framework.execute_contract_test(int2.interaction_id, {"status": 201, "body": {"id": "456", "name": "Bob"}})
    print(f"✅ Executed {len(framework.tests)} tests")

    # Get pact status
    print("\n📊 Checking pact verification...")
    if pact1:
        status = framework.get_pact_verification_status(pact1.pact_id)
        print(f"✅ Pact {pact1.consumer_name}→{pact1.provider_name}: {status['success_rate']:.1f}%")

    # Generate report
    print(framework.generate_testing_report())

    # Export
    print("\n📄 Exporting testing config...")
    export = framework.export_testing_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ API contract testing framework ready")


if __name__ == "__main__":
    main()
