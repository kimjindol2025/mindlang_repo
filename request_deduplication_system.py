#!/usr/bin/env python3
"""
Request Deduplication System - Duplicate request detection and handling
Identifies and deduplicates identical requests in distributed systems with caching
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class DeduplicationMethod(Enum):
    """Deduplication methods"""
    REQUEST_HASH = "REQUEST_HASH"
    REQUEST_ID = "REQUEST_ID"
    FINGERPRINT = "FINGERPRINT"
    CORRELATION_ID = "CORRELATION_ID"


class CacheStrategy(Enum):
    """Cache strategies"""
    WRITE_THROUGH = "WRITE_THROUGH"
    WRITE_BACK = "WRITE_BACK"
    WRITE_AROUND = "WRITE_AROUND"


@dataclass
class Request:
    """Request with deduplication metadata"""
    request_id: str
    method: str
    path: str
    headers: Dict[str, str]
    body: Dict[str, Any]
    timestamp: float
    request_hash: str
    correlation_id: Optional[str] = None


@dataclass
class CachedResponse:
    """Cached response"""
    response_id: str
    request_id: str
    status_code: int
    headers: Dict[str, str]
    body: Dict[str, Any]
    cached_at: float
    ttl_seconds: int
    hit_count: int = 0


@dataclass
class DuplicateDetection:
    """Duplicate detection record"""
    detection_id: str
    original_request_id: str
    duplicate_request_id: str
    method: DeduplicationMethod
    confidence: float
    detected_at: float


class RequestDeduplicationSystem:
    """
    Request Deduplication System

    Provides:
    - Request fingerprinting
    - Duplicate detection
    - Response caching
    - Cache invalidation
    - Correlation tracking
    - Deduplication strategies
    """

    def __init__(self, cache_strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH):
        self.requests: Dict[str, Request] = {}
        self.responses: Dict[str, CachedResponse] = {}
        self.detections: List[DuplicateDetection] = []
        self.request_hashes: Dict[str, str] = {}  # hash -> request_id
        self.correlation_map: Dict[str, List[str]] = {}  # correlation_id -> request_ids
        self.cache_strategy = cache_strategy
        self.dedup_stats: Dict = {}

    def register_request(self,
                        method: str,
                        path: str,
                        headers: Dict[str, str],
                        body: Dict[str, Any],
                        correlation_id: str = None) -> Optional[Request]:
        """Register incoming request"""
        now = time.time()
        request_id = hashlib.md5(
            f"{method}:{path}:{now}:{json.dumps(body, sort_keys=True)}".encode()
        ).hexdigest()[:8]

        # Calculate request hash
        request_hash = self._calculate_request_hash(method, path, body)

        # Check for duplicates
        duplicate_info = self._detect_duplicate(request_hash, correlation_id)

        request = Request(
            request_id=request_id,
            method=method,
            path=path,
            headers=headers,
            body=body,
            timestamp=now,
            request_hash=request_hash,
            correlation_id=correlation_id
        )

        self.requests[request_id] = request

        # Update hashes
        self.request_hashes[request_hash] = request_id

        # Update correlation map
        if correlation_id:
            if correlation_id not in self.correlation_map:
                self.correlation_map[correlation_id] = []
            self.correlation_map[correlation_id].append(request_id)

        # Record duplicate detection
        if duplicate_info:
            detection = DuplicateDetection(
                detection_id=hashlib.md5(f"{request_id}:{now}".encode()).hexdigest()[:8],
                original_request_id=duplicate_info["original_id"],
                duplicate_request_id=request_id,
                method=duplicate_info["method"],
                confidence=duplicate_info["confidence"],
                detected_at=now
            )
            self.detections.append(detection)

        return request

    def _calculate_request_hash(self, method: str, path: str, body: Dict) -> str:
        """Calculate request hash for deduplication"""
        content = f"{method}:{path}:{json.dumps(body, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _detect_duplicate(self, request_hash: str, correlation_id: str = None) -> Optional[Dict]:
        """Detect if request is duplicate"""
        # Check hash-based duplicates
        if request_hash in self.request_hashes:
            original_id = self.request_hashes[request_hash]
            original_request = self.requests.get(original_id)

            if original_request and (time.time() - original_request.timestamp) < 300:
                return {
                    "original_id": original_id,
                    "method": DeduplicationMethod.REQUEST_HASH,
                    "confidence": 0.98
                }

        # Check correlation-based duplicates
        if correlation_id and correlation_id in self.correlation_map:
            requests_in_correlation = self.correlation_map[correlation_id]
            if len(requests_in_correlation) > 1:
                return {
                    "original_id": requests_in_correlation[0],
                    "method": DeduplicationMethod.CORRELATION_ID,
                    "confidence": 0.95
                }

        return None

    def cache_response(self,
                      request_id: str,
                      status_code: int,
                      headers: Dict[str, str],
                      body: Dict[str, Any],
                      ttl_seconds: int = 300) -> Optional[CachedResponse]:
        """Cache response for request"""
        request = self.requests.get(request_id)
        if not request:
            return None

        response_id = hashlib.md5(
            f"{request_id}:{status_code}:{time.time()}".encode()
        ).hexdigest()[:8]

        response = CachedResponse(
            response_id=response_id,
            request_id=request_id,
            status_code=status_code,
            headers=headers,
            body=body,
            cached_at=time.time(),
            ttl_seconds=ttl_seconds
        )

        self.responses[response_id] = response

        return response

    def get_cached_response(self, request_id: str) -> Optional[CachedResponse]:
        """Get cached response for request"""
        for response in self.responses.values():
            if response.request_id == request_id:
                if time.time() - response.cached_at < response.ttl_seconds:
                    response.hit_count += 1
                    return response

        return None

    def get_response_for_duplicate(self, duplicate_request_id: str) -> Optional[CachedResponse]:
        """Get cached response for duplicate request"""
        duplicate = next((d for d in self.detections
                         if d.duplicate_request_id == duplicate_request_id), None)

        if duplicate:
            return self.get_cached_response(duplicate.original_request_id)

        return None

    def invalidate_cache(self, request_id: str) -> int:
        """Invalidate cache entries"""
        responses_to_remove = [r for r in self.responses.values()
                              if r.request_id == request_id]

        for response in responses_to_remove:
            del self.responses[response.response_id]

        return len(responses_to_remove)

    def invalidate_by_pattern(self, path_pattern: str) -> int:
        """Invalidate cache by path pattern"""
        responses_to_remove = []
        for request in self.requests.values():
            if path_pattern in request.path:
                for response in self.responses.values():
                    if response.request_id == request.request_id:
                        responses_to_remove.append(response.response_id)

        for response_id in responses_to_remove:
            if response_id in self.responses:
                del self.responses[response_id]

        return len(responses_to_remove)

    def get_dedup_stats(self) -> Dict:
        """Get deduplication statistics"""
        total_requests = len(self.requests)
        duplicates = len(self.detections)
        unique_requests = total_requests - duplicates

        cached_responses = len(self.responses)
        cache_hits = sum(r.hit_count for r in self.responses.values())

        by_method = {}
        for detection in self.detections:
            method = detection.method.value
            by_method[method] = by_method.get(method, 0) + 1

        return {
            "total_requests": total_requests,
            "unique_requests": unique_requests,
            "duplicates_detected": duplicates,
            "duplicate_rate": (duplicates / total_requests * 100) if total_requests > 0 else 0,
            "cached_responses": cached_responses,
            "cache_hits": cache_hits,
            "deduplication_methods": by_method,
            "correlation_groups": len(self.correlation_map),
        }

    def generate_dedup_report(self) -> str:
        """Generate deduplication report"""
        stats = self.get_dedup_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              REQUEST DEDUPLICATION SYSTEM REPORT                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Requests: {stats['total_requests']}
├─ Unique Requests: {stats['unique_requests']}
├─ Duplicates Detected: {stats['duplicates_detected']}
├─ Duplicate Rate: {stats['duplicate_rate']:.2f}%
├─ Cached Responses: {stats['cached_responses']}
├─ Cache Hits: {stats['cache_hits']}
└─ Correlation Groups: {stats['correlation_groups']}

🔍 DEDUPLICATION METHODS:
"""

        for method, count in stats['deduplication_methods'].items():
            report += f"  {method}: {count}\n"

        return report

    def export_dedup_config(self) -> str:
        """Export deduplication configuration"""
        export_data = {
            "timestamp": time.time(),
            "cache_strategy": self.cache_strategy.value,
            "statistics": self.get_dedup_stats(),
            "cached_responses": [
                {
                    "response_id": r.response_id,
                    "status_code": r.status_code,
                    "hit_count": r.hit_count,
                    "ttl_seconds": r.ttl_seconds,
                }
                for r in self.responses.values()
            ],
            "recent_detections": [
                {
                    "method": d.method.value,
                    "confidence": d.confidence,
                    "detected_at": d.detected_at,
                }
                for d in self.detections[-20:]
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Request Deduplication System - Request Caching")
    print("=" * 70)

    dedup = RequestDeduplicationSystem(CacheStrategy.WRITE_THROUGH)

    # Register requests
    print("\n📝 Registering requests...")
    req1 = dedup.register_request(
        "GET", "/api/users/1",
        {"Content-Type": "application/json"},
        {"filter": "active"},
        correlation_id="corr_001"
    )

    req2 = dedup.register_request(
        "GET", "/api/users/1",
        {"Content-Type": "application/json"},
        {"filter": "active"},
        correlation_id="corr_001"
    )

    req3 = dedup.register_request(
        "POST", "/api/users",
        {"Content-Type": "application/json"},
        {"name": "John", "email": "john@example.com"}
    )

    print(f"✅ Registered {len(dedup.requests)} requests")
    print(f"   Duplicates detected: {len(dedup.detections)}")

    # Cache responses
    print("\n💾 Caching responses...")
    if req1:
        cache1 = dedup.cache_response(
            req1.request_id, 200,
            {"Content-Type": "application/json"},
            {"users": [{"id": "1", "name": "Alice"}]},
            ttl_seconds=600
        )
        print(f"✅ Cached response for request {req1.request_id}")

    # Get cached response for duplicate
    print("\n📥 Retrieving cached responses...")
    if req2:
        cached = dedup.get_response_for_duplicate(req2.request_id)
        if cached:
            print(f"✅ Retrieved cached response (Hit #{cached.hit_count})")

    # Invalidate cache
    print("\n🧹 Invalidating cache...")
    invalidated = dedup.invalidate_by_pattern("/api/users")
    print(f"✅ Invalidated {invalidated} cache entries")

    # Generate report
    print(dedup.generate_dedup_report())

    # Export
    print("\n📄 Exporting deduplication config...")
    export = dedup.export_dedup_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Request deduplication system ready")


if __name__ == "__main__":
    main()
