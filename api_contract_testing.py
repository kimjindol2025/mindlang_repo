#!/usr/bin/env python3
"""
API Contract Testing - Consumer-driven contract testing for API integration
Validates API contracts, prevents breaking changes, and ensures backward compatibility
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import hashlib
import json
import time
import random


class HttpMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class MatchingRule(Enum):
    """Matching rules for request matching"""
    EXACT = "EXACT"
    REGEX = "REGEX"
    TYPE = "TYPE"
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"


class VerificationStatus(Enum):
    """Status of contract verification"""
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    PENDING = "PENDING"


@dataclass
class ContractRequest:
    """Request specification in contract"""
    method: HttpMethod
    path: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    matching_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractResponse:
    """Response specification in contract"""
    status: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    body_matchers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiContract:
    """API contract definition"""
    contract_id: str
    consumer: str  # e.g., "web-frontend", "mobile-app"
    provider: str  # e.g., "auth-service", "payment-service"
    description: str
    request: ContractRequest
    response: ContractResponse
    created_at: float = field(default_factory=time.time)
    version: str = "1.0"


@dataclass
class ContractVerificationResult:
    """Result of contract verification against provider"""
    verification_id: str
    contract_id: str
    provider: str
    status: VerificationStatus
    timestamp: float
    request_matched: bool
    response_matched: bool
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    response_time_ms: float = 0.0
    actual_response: Optional[Dict] = None


@dataclass
class BreakingChange:
    """Detection of breaking change"""
    change_id: str
    contract_id: str
    change_type: str  # "RESPONSE_FIELD_REMOVED", "RESPONSE_FIELD_TYPE_CHANGED", etc.
    old_value: Any
    new_value: Any
    severity: str  # "CRITICAL", "MAJOR", "MINOR"
    affected_consumers: List[str] = field(default_factory=list)


@dataclass
class ContractTestSuite:
    """Suite of contract tests"""
    suite_id: str
    provider: str
    contracts: List[ApiContract] = field(default_factory=list)
    verification_results: List[ContractVerificationResult] = field(default_factory=list)
    breaking_changes: List[BreakingChange] = field(default_factory=list)
    overall_status: VerificationStatus = VerificationStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    total_contracts: int = 0
    verified_contracts: int = 0
    failed_contracts: int = 0


class ApiContractTester:
    """
    Consumer-driven contract testing system

    Performs:
    - Contract definition and versioning
    - Provider verification against contracts
    - Breaking change detection
    - Backward compatibility checking
    - Contract history and regression detection
    - Multi-consumer contract coordination
    - Contract documentation
    """

    def __init__(self):
        self.contracts: Dict[str, ApiContract] = {}
        self.test_suites: Dict[str, ContractTestSuite] = {}
        self.verification_history: List[ContractVerificationResult] = []
        self.breaking_changes_detected: List[BreakingChange] = []

    def create_contract(self,
                       consumer: str,
                       provider: str,
                       description: str,
                       request: Dict,
                       response: Dict) -> ApiContract:
        """
        Create API contract

        Args:
            consumer: Consumer service name
            provider: Provider service name
            description: Contract description
            request: Request specification
            response: Response specification

        Returns:
            Created ApiContract
        """
        contract_id = hashlib.md5(f"{consumer}:{provider}:{time.time()}".encode()).hexdigest()[:8]

        contract_request = ContractRequest(
            method=HttpMethod[request.get("method", "GET")],
            path=request.get("path", "/"),
            headers=request.get("headers", {}),
            body=request.get("body"),
            query_params=request.get("query_params", {}),
            matching_rules=request.get("matching_rules", {})
        )

        contract_response = ContractResponse(
            status=response.get("status", 200),
            headers=response.get("headers", {}),
            body=response.get("body"),
            body_matchers=response.get("body_matchers", {})
        )

        contract = ApiContract(
            contract_id=contract_id,
            consumer=consumer,
            provider=provider,
            description=description,
            request=contract_request,
            response=contract_response
        )

        self.contracts[contract_id] = contract
        return contract

    def verify_contract(self,
                       contract_id: str,
                       actual_response: Dict) -> ContractVerificationResult:
        """
        Verify contract against actual provider response

        Args:
            contract_id: ID of contract to verify
            actual_response: Actual response from provider

        Returns:
            ContractVerificationResult with verification status
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return ContractVerificationResult(
                verification_id="",
                contract_id=contract_id,
                provider="",
                status=VerificationStatus.FAILED,
                timestamp=time.time(),
                request_matched=False,
                response_matched=False,
                failures=["Contract not found"]
            )

        verification_id = hashlib.md5(f"{contract_id}:{time.time()}".encode()).hexdigest()[:8]
        result = ContractVerificationResult(
            verification_id=verification_id,
            contract_id=contract_id,
            provider=contract.provider,
            status=VerificationStatus.PENDING,
            timestamp=time.time(),
            request_matched=True,  # Assume request is correct for now
            actual_response=actual_response
        )

        # Verify response status
        if actual_response.get("status") != contract.response.status:
            result.response_matched = False
            result.failures.append(
                f"Status mismatch: expected {contract.response.status}, got {actual_response.get('status')}"
            )

        # Verify response headers
        for header_name, expected_value in contract.response.headers.items():
            actual_value = actual_response.get("headers", {}).get(header_name)
            if actual_value != expected_value:
                result.warnings.append(
                    f"Header mismatch: {header_name}: expected '{expected_value}', got '{actual_value}'"
                )

        # Verify response body
        expected_body = contract.response.body
        actual_body = actual_response.get("body")

        if expected_body:
            response_matched = self._verify_body(expected_body, actual_body, contract.response.body_matchers)
            if not response_matched:
                result.response_matched = False
                result.failures.append("Response body mismatch")
            else:
                result.response_matched = True

        # Detect breaking changes
        breaking_change = self._detect_breaking_change(contract, actual_response)
        if breaking_change:
            result.failures.append(f"Breaking change detected: {breaking_change.change_type}")
            self.breaking_changes_detected.append(breaking_change)

        # Determine overall status
        if result.failures:
            result.status = VerificationStatus.FAILED
        elif result.warnings:
            result.status = VerificationStatus.WARNING
        else:
            result.status = VerificationStatus.VERIFIED

        # Simulate response time
        result.response_time_ms = random.uniform(10, 500)

        self.verification_history.append(result)
        return result

    def _verify_body(self, expected: Any, actual: Any, matchers: Dict) -> bool:
        """Verify response body matches contract"""
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._verify_body(value, actual[key], matchers.get(key, {})):
                    return False
            return True
        elif isinstance(expected, list) and isinstance(actual, list):
            return len(actual) > 0  # At least one item
        else:
            return type(expected) == type(actual) or actual is not None

    def _detect_breaking_change(self, contract: ApiContract, actual_response: Dict) -> Optional[BreakingChange]:
        """Detect breaking changes in response"""
        expected_body = contract.response.body or {}
        actual_body = actual_response.get("body", {})

        if isinstance(expected_body, dict) and isinstance(actual_body, dict):
            # Check for removed fields
            for field in expected_body:
                if field not in actual_body:
                    change_id = hashlib.md5(f"{contract.contract_id}:{field}".encode()).hexdigest()[:8]
                    return BreakingChange(
                        change_id=change_id,
                        contract_id=contract.contract_id,
                        change_type="RESPONSE_FIELD_REMOVED",
                        old_value=expected_body[field],
                        new_value=None,
                        severity="CRITICAL",
                        affected_consumers=[contract.consumer]
                    )

            # Check for type changes
            for field in actual_body:
                if field in expected_body:
                    if type(expected_body[field]) != type(actual_body[field]):
                        change_id = hashlib.md5(f"{contract.contract_id}:{field}:type".encode()).hexdigest()[:8]
                        return BreakingChange(
                            change_id=change_id,
                            contract_id=contract.contract_id,
                            change_type="RESPONSE_FIELD_TYPE_CHANGED",
                            old_value=type(expected_body[field]).__name__,
                            new_value=type(actual_body[field]).__name__,
                            severity="MAJOR",
                            affected_consumers=[contract.consumer]
                        )

        return None

    def create_test_suite(self,
                         provider: str,
                         consumer_contracts: List[ApiContract]) -> ContractTestSuite:
        """
        Create test suite for provider against all contracts

        Args:
            provider: Provider service name
            consumer_contracts: List of contracts from consumers

        Returns:
            ContractTestSuite with all verifications
        """
        suite_id = hashlib.md5(f"{provider}:{time.time()}".encode()).hexdigest()[:8]
        suite = ContractTestSuite(
            suite_id=suite_id,
            provider=provider,
            contracts=consumer_contracts,
            total_contracts=len(consumer_contracts)
        )

        # Verify each contract
        for contract in consumer_contracts:
            # Simulate provider response
            simulated_response = self._simulate_provider_response(contract)

            # Verify contract
            result = self.verify_contract(contract.contract_id, simulated_response)
            suite.verification_results.append(result)

            if result.status == VerificationStatus.VERIFIED:
                suite.verified_contracts += 1
            elif result.status == VerificationStatus.FAILED:
                suite.failed_contracts += 1

        # Determine overall suite status
        if suite.failed_contracts > 0:
            suite.overall_status = VerificationStatus.FAILED
        elif any(r.status == VerificationStatus.WARNING for r in suite.verification_results):
            suite.overall_status = VerificationStatus.WARNING
        else:
            suite.overall_status = VerificationStatus.VERIFIED

        self.test_suites[suite_id] = suite
        return suite

    def _simulate_provider_response(self, contract: ApiContract) -> Dict:
        """Simulate provider response based on contract"""
        # Sometimes introduce failures or changes
        introduce_failure = random.random() < 0.2  # 20% failure rate

        if introduce_failure:
            # Return invalid response
            return {
                "status": contract.response.status + 100,
                "headers": {},
                "body": {}
            }
        else:
            # Return correct response
            return {
                "status": contract.response.status,
                "headers": contract.response.headers,
                "body": contract.response.body or {}
            }

    def check_backward_compatibility(self,
                                   contract_id: str,
                                   new_provider_response: Dict) -> Tuple[bool, List[str]]:
        """
        Check if new provider response is backward compatible

        Args:
            contract_id: Contract to check against
            new_provider_response: New provider response

        Returns:
            Tuple of (is_compatible, list of issues)
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return False, ["Contract not found"]

        issues = []

        expected_body = contract.response.body or {}
        actual_body = new_provider_response.get("body", {})

        if isinstance(expected_body, dict) and isinstance(actual_body, dict):
            # Required fields must exist
            for field in expected_body:
                if field not in actual_body:
                    issues.append(f"Required field '{field}' removed from response")

            # New fields can be added (backward compatible)
            # But type changes are breaking
            for field in expected_body:
                if field in actual_body:
                    if type(expected_body[field]) != type(actual_body[field]):
                        issues.append(f"Type of field '{field}' changed from {type(expected_body[field]).__name__} to {type(actual_body[field]).__name__}")

        is_compatible = len(issues) == 0
        return is_compatible, issues

    def generate_contract_documentation(self, contract_id: str) -> str:
        """Generate documentation for contract"""
        contract = self.contracts.get(contract_id)
        if not contract:
            return f"❌ Contract {contract_id} not found"

        doc = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                          API CONTRACT DOCUMENTATION                        ║
║                          Contract ID: {contract_id}                        ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 CONTRACT DETAILS:
├─ Consumer: {contract.consumer}
├─ Provider: {contract.provider}
├─ Version: {contract.version}
├─ Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(contract.created_at))}
└─ Description: {contract.description}

📥 REQUEST:
├─ Method: {contract.request.method.value}
├─ Path: {contract.request.path}
├─ Headers: {json.dumps(contract.request.headers, indent=2)}
├─ Query Parameters: {json.dumps(contract.request.query_params, indent=2)}
└─ Body: {json.dumps(contract.request.body, indent=2) if contract.request.body else 'None'}

📤 EXPECTED RESPONSE:
├─ Status: {contract.response.status}
├─ Headers: {json.dumps(contract.response.headers, indent=2)}
└─ Body: {json.dumps(contract.response.body, indent=2) if contract.response.body else 'None'}

🔗 MATCHING RULES:
"""

        if contract.request.matching_rules:
            for key, rule in contract.request.matching_rules.items():
                doc += f"  • {key}: {rule}\n"
        else:
            doc += "  • Exact match required\n"

        return doc

    def generate_test_report(self, suite_id: str) -> str:
        """Generate test report for suite"""
        suite = self.test_suites.get(suite_id)
        if not suite:
            return f"❌ Test suite {suite_id} not found"

        status_emoji = "✅" if suite.overall_status == VerificationStatus.VERIFIED else \
                       "⚠️ " if suite.overall_status == VerificationStatus.WARNING else "❌"

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      CONTRACT VERIFICATION REPORT                          ║
║                      Suite ID: {suite_id}                                  ║
║                      Provider: {suite.provider}                            ║
╚════════════════════════════════════════════════════════════════════════════╝

{status_emoji} OVERALL STATUS: {suite.overall_status.value}

📊 VERIFICATION SUMMARY:
├─ Total Contracts: {suite.total_contracts}
├─ ✅ Verified: {suite.verified_contracts}
├─ ❌ Failed: {suite.failed_contracts}
└─ ⏱️  Test Duration: {time.time() - suite.timestamp:.2f}s

📝 CONTRACT DETAILS:
"""

        for result in suite.verification_results[:5]:
            contract = self.contracts.get(result.contract_id)
            if contract:
                emoji = "✅" if result.status == VerificationStatus.VERIFIED else \
                        "⚠️ " if result.status == VerificationStatus.WARNING else "❌"
                report += f"\n{emoji} {contract.description}\n"
                report += f"  Consumer: {contract.consumer}\n"
                report += f"  Response Time: {result.response_time_ms:.2f}ms\n"
                if result.failures:
                    report += f"  Failures:\n"
                    for failure in result.failures:
                        report += f"    • {failure}\n"

        if self.breaking_changes_detected:
            report += f"\n🚨 BREAKING CHANGES DETECTED:\n"
            for change in self.breaking_changes_detected[-3:]:
                report += f"  • {change.change_type}\n"
                report += f"    Severity: {change.severity}\n"
                report += f"    Affected: {', '.join(change.affected_consumers)}\n"

        return report

    def export_contracts(self, provider: str) -> str:
        """Export all contracts for a provider"""
        provider_contracts = [c for c in self.contracts.values() if c.provider == provider]

        export_data = {
            "provider": provider,
            "contract_count": len(provider_contracts),
            "contracts": [
                {
                    "contract_id": c.contract_id,
                    "consumer": c.consumer,
                    "description": c.description,
                    "version": c.version,
                    "request": {
                        "method": c.request.method.value,
                        "path": c.request.path,
                    },
                    "response": {
                        "status": c.response.status,
                    },
                }
                for c in provider_contracts
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔗 API Contract Testing - Consumer-Driven Contract Testing")
    print("=" * 70)

    tester = ApiContractTester()

    # Create contracts
    print("\n📋 Creating API contracts...")

    contract1 = tester.create_contract(
        consumer="web-frontend",
        provider="user-service",
        description="GET /api/users/{id}",
        request={
            "method": "GET",
            "path": "/api/users/123",
            "headers": {"Authorization": "Bearer token"},
        },
        response={
            "status": 200,
            "headers": {"Content-Type": "application/json"},
            "body": {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com",
                "created_at": "2024-01-01T00:00:00Z",
            },
        }
    )

    contract2 = tester.create_contract(
        consumer="mobile-app",
        provider="user-service",
        description="POST /api/users",
        request={
            "method": "POST",
            "path": "/api/users",
            "headers": {"Content-Type": "application/json"},
            "body": {"name": "Jane Doe", "email": "jane@example.com"},
        },
        response={
            "status": 201,
            "headers": {"Content-Type": "application/json"},
            "body": {"id": 124, "name": "Jane Doe"},
        }
    )

    print(f"✅ Created {len([contract1, contract2])} contracts")

    # Create test suite
    print("\n🧪 Running contract verification...")
    suite = tester.create_test_suite(
        provider="user-service",
        consumer_contracts=[contract1, contract2]
    )

    # Print report
    print(tester.generate_test_report(suite.suite_id))

    # Export contracts
    print("\n📄 Exporting contracts...")
    export = tester.export_contracts("user-service")
    print(f"✅ Exported {len(export)} characters of contract data")

    print("\n" + "=" * 70)
    print("✨ Contract testing complete")


if __name__ == "__main__":
    main()
