#!/usr/bin/env python3
"""
Data Lineage Tracker - Data flow and transformation tracking
Tracks data lineage, transformations, and dependencies across systems
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set
import hashlib
import json
import time


class DataAssetType(Enum):
    """Data asset types"""
    TABLE = "TABLE"
    FILE = "FILE"
    STREAM = "STREAM"
    MODEL = "MODEL"
    DATASET = "DATASET"


class TransformationType(Enum):
    """Transformation types"""
    EXTRACTION = "EXTRACTION"
    TRANSFORMATION = "TRANSFORMATION"
    LOADING = "LOADING"
    AGGREGATION = "AGGREGATION"
    ENRICHMENT = "ENRICHMENT"
    FILTERING = "FILTERING"


@dataclass
class DataAsset:
    """Data asset"""
    asset_id: str
    asset_name: str
    asset_type: DataAssetType
    location: str
    schema: Dict[str, str] = field(default_factory=dict)
    row_count: int = 0
    size_bytes: int = 0
    created_at: float = field(default_factory=time.time)
    owner: Optional[str] = None


@dataclass
class DataTransformation:
    """Data transformation"""
    transformation_id: str
    name: str
    type: TransformationType
    source_assets: List[str]
    target_assets: List[str]
    query: str
    executed_at: float = field(default_factory=time.time)
    execution_time_ms: float = 0.0
    record_count: int = 0


@dataclass
class LineageNode:
    """Lineage graph node"""
    node_id: str
    asset_id: str
    asset_name: str
    asset_type: DataAssetType
    depth: int
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)


class DataLineageTracker:
    """
    Data Lineage Tracker

    Provides:
    - Data asset tracking
    - Transformation tracking
    - Lineage graph building
    - Impact analysis
    - Data quality tracking
    - Compliance reporting
    """

    def __init__(self):
        self.assets: Dict[str, DataAsset] = {}
        self.transformations: List[DataTransformation] = []
        self.lineage_graph: Dict[str, LineageNode] = {}
        self.data_quality_scores: Dict[str, float] = {}
        self.audit_log: List[Dict] = []

    def register_asset(self,
                      asset_name: str,
                      asset_type: DataAssetType,
                      location: str,
                      schema: Dict[str, str] = None,
                      owner: str = None) -> DataAsset:
        """Register data asset"""
        asset_id = hashlib.md5(
            f"{asset_name}:{location}:{time.time()}".encode()
        ).hexdigest()[:8]

        asset = DataAsset(
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            location=location,
            schema=schema or {},
            owner=owner
        )

        self.assets[asset_id] = asset

        # Create lineage node
        node = LineageNode(
            node_id=asset_id,
            asset_id=asset_id,
            asset_name=asset_name,
            asset_type=asset_type,
            depth=0
        )
        self.lineage_graph[asset_id] = node

        # Log registration
        self.audit_log.append({
            "action": "ASSET_REGISTERED",
            "asset_id": asset_id,
            "asset_name": asset_name,
            "timestamp": time.time()
        })

        return asset

    def record_transformation(self,
                             name: str,
                             trans_type: TransformationType,
                             source_ids: List[str],
                             target_ids: List[str],
                             query: str,
                             execution_time_ms: float = 0,
                             record_count: int = 0) -> DataTransformation:
        """Record data transformation"""
        trans_id = hashlib.md5(
            f"{name}:{source_ids}:{target_ids}:{time.time()}".encode()
        ).hexdigest()[:8]

        transformation = DataTransformation(
            transformation_id=trans_id,
            name=name,
            type=trans_type,
            source_assets=source_ids,
            target_assets=target_ids,
            query=query,
            execution_time_ms=execution_time_ms,
            record_count=record_count
        )

        self.transformations.append(transformation)

        # Update lineage graph
        for target_id in target_ids:
            if target_id in self.lineage_graph:
                target_node = self.lineage_graph[target_id]
                for source_id in source_ids:
                    if source_id not in target_node.parents:
                        target_node.parents.append(source_id)

                    if source_id in self.lineage_graph:
                        source_node = self.lineage_graph[source_id]
                        if target_id not in source_node.children:
                            source_node.children.append(target_id)

        # Log transformation
        self.audit_log.append({
            "action": "TRANSFORMATION_RECORDED",
            "transformation_id": trans_id,
            "name": name,
            "timestamp": time.time()
        })

        return transformation

    def get_upstream_lineage(self, asset_id: str, max_depth: int = 10) -> Set[str]:
        """Get all upstream dependencies"""
        visited = set()
        to_visit = [asset_id]

        while to_visit and len(visited) < max_depth:
            current = to_visit.pop(0)
            if current in visited:
                continue

            visited.add(current)
            node = self.lineage_graph.get(current)
            if node:
                to_visit.extend(node.parents)

        return visited

    def get_downstream_impact(self, asset_id: str, max_depth: int = 10) -> Set[str]:
        """Get all downstream dependencies"""
        visited = set()
        to_visit = [asset_id]

        while to_visit and len(visited) < max_depth:
            current = to_visit.pop(0)
            if current in visited:
                continue

            visited.add(current)
            node = self.lineage_graph.get(current)
            if node:
                to_visit.extend(node.children)

        return visited

    def update_data_quality(self, asset_id: str, quality_score: float) -> bool:
        """Update data quality score"""
        if asset_id not in self.assets:
            return False

        quality_score = max(0, min(1.0, quality_score))  # Clamp to 0-1
        self.data_quality_scores[asset_id] = quality_score

        self.audit_log.append({
            "action": "QUALITY_UPDATED",
            "asset_id": asset_id,
            "quality_score": quality_score,
            "timestamp": time.time()
        })

        return True

    def analyze_impact(self, asset_id: str) -> Dict:
        """Analyze impact of asset change"""
        upstream = self.get_upstream_lineage(asset_id)
        downstream = self.get_downstream_impact(asset_id)

        # Find transformations affecting this asset
        related_transformations = [
            t for t in self.transformations
            if asset_id in t.source_assets or asset_id in t.target_assets
        ]

        return {
            "asset_id": asset_id,
            "upstream_dependencies": len(upstream) - 1,  # Exclude self
            "downstream_impacted": len(downstream) - 1,  # Exclude self
            "related_transformations": len(related_transformations),
            "total_affected_assets": len(upstream | downstream),
        }

    def get_lineage_stats(self) -> Dict:
        """Get lineage statistics"""
        total_assets = len(self.assets)
        total_transformations = len(self.transformations)

        by_asset_type = {}
        for asset in self.assets.values():
            asset_type = asset.asset_type.value
            by_asset_type[asset_type] = by_asset_type.get(asset_type, 0) + 1

        by_trans_type = {}
        for trans in self.transformations:
            trans_type = trans.type.value
            by_trans_type[trans_type] = by_trans_type.get(trans_type, 0) + 1

        avg_quality = (sum(self.data_quality_scores.values()) /
                      len(self.data_quality_scores)) if self.data_quality_scores else 0

        return {
            "total_assets": total_assets,
            "total_transformations": total_transformations,
            "by_asset_type": by_asset_type,
            "by_transformation_type": by_trans_type,
            "avg_data_quality": avg_quality,
            "audit_log_entries": len(self.audit_log),
        }

    def generate_lineage_report(self) -> str:
        """Generate lineage report"""
        stats = self.get_lineage_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              DATA LINEAGE TRACKER REPORT                                   ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Assets: {stats['total_assets']}
├─ Total Transformations: {stats['total_transformations']}
├─ Avg Data Quality: {stats['avg_data_quality']:.2%}
└─ Audit Entries: {stats['audit_log_entries']}

📦 BY ASSET TYPE:
"""

        for asset_type, count in stats['by_asset_type'].items():
            report += f"  {asset_type}: {count}\n"

        report += f"\n🔄 BY TRANSFORMATION TYPE:\n"
        for trans_type, count in stats['by_transformation_type'].items():
            report += f"  {trans_type}: {count}\n"

        report += f"\n📋 RECENT ASSETS:\n"
        for asset in sorted(self.assets.values(), key=lambda a: a.created_at, reverse=True)[:5]:
            quality = self.data_quality_scores.get(asset.asset_id, 0)
            report += f"  {asset.asset_name} ({asset.asset_type.value}): Quality {quality:.1%}\n"

        return report

    def export_lineage_config(self) -> str:
        """Export lineage configuration"""
        export_data = {
            "timestamp": time.time(),
            "statistics": self.get_lineage_stats(),
            "assets": [
                {
                    "id": a.asset_id,
                    "name": a.asset_name,
                    "type": a.asset_type.value,
                    "owner": a.owner,
                }
                for a in self.assets.values()
            ],
            "transformations": [
                {
                    "name": t.name,
                    "type": t.type.value,
                    "source_count": len(t.source_assets),
                    "target_count": len(t.target_assets),
                }
                for t in self.transformations
            ],
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("📊 Data Lineage Tracker - Data Flow Tracking")
    print("=" * 70)

    tracker = DataLineageTracker()

    # Register assets
    print("\n📦 Registering data assets...")
    asset1 = tracker.register_asset(
        "raw_users", DataAssetType.TABLE,
        "postgresql://db/raw_users",
        {"id": "bigint", "email": "varchar", "created": "timestamp"},
        owner="data_team"
    )
    asset2 = tracker.register_asset(
        "users_processed", DataAssetType.TABLE,
        "postgresql://db/users_processed",
        {"id": "bigint", "email": "varchar", "email_verified": "boolean"},
        owner="data_team"
    )
    asset3 = tracker.register_asset(
        "user_analytics", DataAssetType.DATASET,
        "s3://analytics/user_metrics",
        {"user_id": "string", "metrics": "json"},
        owner="analytics_team"
    )
    print(f"✅ Registered {len(tracker.assets)} assets")

    # Record transformations
    print("\n🔄 Recording transformations...")
    tracker.record_transformation(
        "Clean and validate users",
        TransformationType.TRANSFORMATION,
        [asset1.asset_id],
        [asset2.asset_id],
        "SELECT id, email, email LIKE '%@%' as email_verified FROM raw_users WHERE email IS NOT NULL",
        execution_time_ms=245,
        record_count=10000
    )
    tracker.record_transformation(
        "Generate user metrics",
        TransformationType.AGGREGATION,
        [asset2.asset_id],
        [asset3.asset_id],
        "SELECT user_id, COUNT(*) as action_count FROM user_actions GROUP BY user_id",
        execution_time_ms=512,
        record_count=5000
    )
    print(f"✅ Recorded {len(tracker.transformations)} transformations")

    # Update data quality
    print("\n✅ Updating data quality scores...")
    tracker.update_data_quality(asset1.asset_id, 0.85)
    tracker.update_data_quality(asset2.asset_id, 0.92)
    tracker.update_data_quality(asset3.asset_id, 0.88)
    print("✅ Quality scores updated")

    # Analyze impact
    print("\n📈 Analyzing impact...")
    impact = tracker.analyze_impact(asset1.asset_id)
    print(f"✅ Asset {asset1.asset_name} impacts {impact['downstream_impacted']} downstream assets")

    # Get lineage
    print("\n📍 Tracing lineage...")
    upstream = tracker.get_upstream_lineage(asset3.asset_id)
    downstream = tracker.get_downstream_impact(asset1.asset_id)
    print(f"✅ Upstream: {len(upstream)}, Downstream: {len(downstream)}")

    # Generate report
    print(tracker.generate_lineage_report())

    # Export
    print("\n📄 Exporting lineage config...")
    export = tracker.export_lineage_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Data lineage tracker ready")


if __name__ == "__main__":
    main()
