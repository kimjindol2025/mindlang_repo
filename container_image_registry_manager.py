#!/usr/bin/env python3
"""
Container Image Registry Manager - Container image management and distribution
Manages container image repositories, versioning, scanning, and distribution
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import hashlib
import json
import time


class ImageStatus(Enum):
    """Image status"""
    BUILDING = "BUILDING"
    READY = "READY"
    SCANNING = "SCANNING"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    REMOVED = "REMOVED"


class RegistryType(Enum):
    """Registry types"""
    DOCKER_HUB = "DOCKER_HUB"
    ECR = "ECR"
    GCR = "GCR"
    ARTIFACTORY = "ARTIFACTORY"
    HARBOR = "HARBOR"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ContainerImage:
    """Container image"""
    image_id: str
    repository: str
    tag: str
    digest: str
    size_bytes: int
    status: ImageStatus = ImageStatus.READY
    created_at: float = field(default_factory=time.time)
    pushed_at: Optional[float] = None
    scan_results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImageScan:
    """Image security scan result"""
    scan_id: str
    image_id: str
    scan_time: float
    total_vulnerabilities: int
    critical: int
    high: int
    medium: int
    low: int
    passed: bool


@dataclass
class Registry:
    """Container registry"""
    registry_id: str
    registry_name: str
    registry_type: RegistryType
    endpoint: str
    authenticated: bool
    total_images: int = 0
    created_at: float = field(default_factory=time.time)


class ContainerImageRegistryManager:
    """
    Container Image Registry Manager

    Provides:
    - Multi-registry management
    - Image versioning
    - Security scanning
    - Image distribution
    - Cleanup policies
    - Pull-through caching
    """

    def __init__(self):
        self.registries: Dict[str, Registry] = {}
        self.images: Dict[str, ContainerImage] = {}
        self.scans: List[ImageScan] = []
        self.pull_logs: List[Dict] = []
        self.retention_policies: Dict[str, Dict] = {}

    def register_registry(self,
                         registry_name: str,
                         registry_type: RegistryType,
                         endpoint: str,
                         authenticated: bool = True) -> Registry:
        """Register container registry"""
        registry_id = hashlib.md5(
            f"{registry_name}:{endpoint}:{time.time()}".encode()
        ).hexdigest()[:8]

        registry = Registry(
            registry_id=registry_id,
            registry_name=registry_name,
            registry_type=registry_type,
            endpoint=endpoint,
            authenticated=authenticated
        )

        self.registries[registry_id] = registry
        return registry

    def push_image(self,
                  registry_id: str,
                  repository: str,
                  tag: str,
                  digest: str,
                  size_bytes: int) -> Optional[ContainerImage]:
        """Push container image to registry"""
        registry = self.registries.get(registry_id)
        if not registry:
            return None

        image_id = hashlib.md5(
            f"{repository}:{tag}:{digest}".encode()
        ).hexdigest()[:8]

        image = ContainerImage(
            image_id=image_id,
            repository=repository,
            tag=tag,
            digest=digest,
            size_bytes=size_bytes,
            pushed_at=time.time(),
            metadata={
                "registry_id": registry_id,
                "pushed_by": "ci_pipeline"
            }
        )

        self.images[image_id] = image
        registry.total_images += 1

        return image

    def scan_image(self,
                  image_id: str,
                  vulnerabilities: Dict[str, int]) -> Optional[ImageScan]:
        """Scan image for vulnerabilities"""
        image = self.images.get(image_id)
        if not image:
            return None

        scan_id = hashlib.md5(
            f"{image_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        total_vulns = sum(vulnerabilities.values())
        critical = vulnerabilities.get("CRITICAL", 0)
        high = vulnerabilities.get("HIGH", 0)
        medium = vulnerabilities.get("MEDIUM", 0)
        low = vulnerabilities.get("LOW", 0)

        # Pass if no critical/high vulnerabilities
        passed = critical == 0 and high == 0

        scan = ImageScan(
            scan_id=scan_id,
            image_id=image_id,
            scan_time=time.time(),
            total_vulnerabilities=total_vulns,
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            passed=passed
        )

        self.scans.append(scan)
        image.scan_results = {
            "scan_id": scan_id,
            "passed": passed,
            "vulnerabilities": vulnerabilities
        }

        if passed:
            image.status = ImageStatus.APPROVED
        else:
            image.status = ImageStatus.SCANNING

        return scan

    def pull_image(self,
                  image_id: str,
                  pull_location: str) -> bool:
        """Pull image from registry"""
        image = self.images.get(image_id)
        if not image or image.status != ImageStatus.APPROVED:
            return False

        self.pull_logs.append({
            "image_id": image_id,
            "repository": image.repository,
            "tag": image.tag,
            "pulled_at": time.time(),
            "location": pull_location,
            "size_bytes": image.size_bytes
        })

        return True

    def set_retention_policy(self,
                            repository: str,
                            keep_recent: int = 10,
                            keep_days: int = 30) -> Dict:
        """Set retention policy for repository"""
        policy = {
            "repository": repository,
            "keep_recent_images": keep_recent,
            "keep_days": keep_days,
            "created_at": time.time()
        }

        self.retention_policies[repository] = policy
        return policy

    def apply_retention_policies(self) -> int:
        """Apply retention policies and cleanup old images"""
        removed_count = 0

        for repository, policy in self.retention_policies.items():
            repo_images = sorted(
                [i for i in self.images.values() if i.repository == repository],
                key=lambda x: x.pushed_at or x.created_at,
                reverse=True
            )

            # Keep recent images
            to_remove = repo_images[policy["keep_recent_images"]:]

            # Also remove images older than retention days
            cutoff_time = time.time() - (policy["keep_days"] * 86400)
            to_remove = [i for i in to_remove if (i.pushed_at or i.created_at) < cutoff_time]

            for image in to_remove:
                image.status = ImageStatus.REMOVED
                removed_count += 1

        return removed_count

    def get_registry_stats(self) -> Dict:
        """Get registry statistics"""
        total_registries = len(self.registries)
        total_images = len(self.images)

        by_status = {}
        for image in self.images.values():
            status = image.status.value
            by_status[status] = by_status.get(status, 0) + 1

        by_registry = {}
        for registry in self.registries.values():
            by_registry[registry.registry_name] = registry.total_images

        total_size = sum(i.size_bytes for i in self.images.values())

        scans_passed = sum(1 for s in self.scans if s.passed)
        scans_failed = len(self.scans) - scans_passed

        return {
            "total_registries": total_registries,
            "total_images": total_images,
            "by_status": by_status,
            "by_registry": by_registry,
            "total_size_gb": total_size / (1024**3),
            "total_scans": len(self.scans),
            "scans_passed": scans_passed,
            "scans_failed": scans_failed,
            "pulls": len(self.pull_logs),
        }

    def generate_registry_report(self) -> str:
        """Generate registry report"""
        stats = self.get_registry_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              CONTAINER IMAGE REGISTRY MANAGER REPORT                       ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Registries: {stats['total_registries']}
├─ Total Images: {stats['total_images']}
├─ Total Size: {stats['total_size_gb']:.2f} GB
├─ Total Scans: {stats['total_scans']}
├─ Scans Passed: {stats['scans_passed']}
├─ Scans Failed: {stats['scans_failed']}
└─ Total Pulls: {stats['pulls']}

📦 BY STATUS:
"""

        for status, count in stats['by_status'].items():
            report += f"  {status}: {count}\n"

        report += f"\n🏠 BY REGISTRY:\n"
        for registry, count in stats['by_registry'].items():
            report += f"  {registry}: {count} images\n"

        return report

    def export_registry_config(self) -> str:
        """Export registry configuration"""
        stats = self.get_registry_stats()

        export_data = {
            "timestamp": time.time(),
            "statistics": stats,
            "registries": [
                {
                    "id": r.registry_id,
                    "name": r.registry_name,
                    "type": r.registry_type.value,
                    "images": r.total_images,
                }
                for r in self.registries.values()
            ],
            "retention_policies": self.retention_policies,
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📦 Container Image Registry Manager - Image Management")
    print("=" * 70)

    manager = ContainerImageRegistryManager()

    # Register registries
    print("\n🏠 Registering registries...")
    ecr = manager.register_registry("AWS ECR", RegistryType.ECR, "123456.dkr.ecr.us-east-1.amazonaws.com")
    gcr = manager.register_registry("Google GCR", RegistryType.GCR, "gcr.io/project-123")
    print(f"✅ Registered {len(manager.registries)} registries")

    # Push images
    print("\n📤 Pushing container images...")
    img1 = manager.push_image(ecr.registry_id, "api-service", "v1.0.0", "sha256:abc123", 250*1024*1024)
    img2 = manager.push_image(ecr.registry_id, "api-service", "v1.1.0", "sha256:def456", 260*1024*1024)
    img3 = manager.push_image(gcr.registry_id, "web-frontend", "latest", "sha256:ghi789", 150*1024*1024)
    print(f"✅ Pushed {len(manager.images)} images")

    # Scan images
    print("\n🔍 Scanning images...")
    if img1:
        scan1 = manager.scan_image(img1.image_id, {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 3, "LOW": 5})
    if img2:
        scan2 = manager.scan_image(img2.image_id, {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 2, "LOW": 2})
    if img3:
        scan3 = manager.scan_image(img3.image_id, {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0})
    print(f"✅ Scanned {len(manager.scans)} images")

    # Pull images
    print("\n📥 Pulling images...")
    if img2:
        manager.pull_image(img2.image_id, "production-cluster-1")
    if img3:
        manager.pull_image(img3.image_id, "staging-cluster")
    print(f"✅ {len(manager.pull_logs)} pulls recorded")

    # Set retention policy
    print("\n🧹 Setting retention policies...")
    manager.set_retention_policy("api-service", keep_recent=5, keep_days=30)
    print(f"✅ Set {len(manager.retention_policies)} retention policies")

    # Apply retention
    print("\n♻️  Applying retention policies...")
    removed = manager.apply_retention_policies()
    print(f"✅ Removed {removed} old images")

    # Generate report
    print(manager.generate_registry_report())

    # Export
    print("\n📄 Exporting registry config...")
    export = manager.export_registry_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Container image registry manager ready")


if __name__ == "__main__":
    main()
