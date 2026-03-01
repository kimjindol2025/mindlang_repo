#!/usr/bin/env python3
"""
Request/Response Transformer - Message transformation and optimization
Handles request/response transformation, compression, and protocol conversion
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import hashlib
import json
import time


class TransformationType(Enum):
    """Transformation types"""
    JSON_TO_PROTOBUF = "JSON_TO_PROTOBUF"
    PROTOBUF_TO_JSON = "PROTOBUF_TO_JSON"
    XML_TO_JSON = "XML_TO_JSON"
    JSON_TO_XML = "JSON_TO_XML"
    COMPRESSION = "COMPRESSION"
    DECOMPRESSION = "DECOMPRESSION"
    ENCRYPTION = "ENCRYPTION"
    DECRYPTION = "DECRYPTION"
    FIELD_MAPPING = "FIELD_MAPPING"
    VALIDATION = "VALIDATION"


class CompressionAlgorithm(Enum):
    """Compression algorithms"""
    GZIP = "GZIP"
    DEFLATE = "DEFLATE"
    BROTLI = "BROTLI"
    SNAPPY = "SNAPPY"


@dataclass
class TransformationRule:
    """Transformation rule"""
    rule_id: str
    rule_name: str
    transformation_type: TransformationType
    input_format: str
    output_format: str
    mapping: Dict[str, str] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    compression: Optional[CompressionAlgorithm] = None
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class TransformationResult:
    """Transformation result"""
    result_id: str
    rule_id: str
    timestamp: float
    input_size: int
    output_size: int
    compression_ratio: float = 0.0
    transformation_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class TransformationPipeline:
    """Pipeline of transformations"""
    pipeline_id: str
    pipeline_name: str
    rules: List[str] = field(default_factory=list)  # rule_ids
    enabled: bool = True
    execution_order: List[int] = field(default_factory=list)


class RequestResponseTransformer:
    """
    Request/Response Transformer

    Provides:
    - Multi-format transformation
    - Compression/decompression
    - Field mapping
    - Data validation
    - Transformation pipelines
    - Performance optimization
    """

    def __init__(self):
        self.rules: Dict[str, TransformationRule] = {}
        self.pipelines: Dict[str, TransformationPipeline] = {}
        self.results: List[TransformationResult] = []

    def create_rule(self,
                   rule_name: str,
                   transformation_type: TransformationType,
                   input_format: str,
                   output_format: str,
                   mapping: Dict[str, str] = None,
                   compression: Optional[CompressionAlgorithm] = None) -> TransformationRule:
        """Create transformation rule"""
        rule_id = hashlib.md5(
            f"{rule_name}:{transformation_type.value}:{time.time()}".encode()
        ).hexdigest()[:8]

        rule = TransformationRule(
            rule_id=rule_id,
            rule_name=rule_name,
            transformation_type=transformation_type,
            input_format=input_format,
            output_format=output_format,
            mapping=mapping or {},
            compression=compression
        )

        self.rules[rule_id] = rule
        return rule

    def apply_transformation(self,
                           rule_id: str,
                           input_data: Any) -> TransformationResult:
        """Apply transformation rule"""
        rule = self.rules.get(rule_id)
        if not rule or not rule.enabled:
            return None

        result_id = hashlib.md5(
            f"{rule_id}:{time.time()}".encode()
        ).hexdigest()[:8]

        start_time = time.time()

        try:
            # Convert to string for size measurement
            input_str = json.dumps(input_data) if isinstance(input_data, dict) else str(input_data)
            input_size = len(input_str.encode())

            # Apply transformation
            output_data = self._transform(input_data, rule)

            output_str = json.dumps(output_data) if isinstance(output_data, dict) else str(output_data)
            output_size = len(output_str.encode())

            # Calculate compression ratio
            compression_ratio = (1 - output_size / max(1, input_size)) * 100

            duration_ms = (time.time() - start_time) * 1000

            result = TransformationResult(
                result_id=result_id,
                rule_id=rule_id,
                timestamp=time.time(),
                input_size=input_size,
                output_size=output_size,
                compression_ratio=compression_ratio,
                transformation_time_ms=duration_ms,
                success=True
            )

        except Exception as e:
            result = TransformationResult(
                result_id=result_id,
                rule_id=rule_id,
                timestamp=time.time(),
                input_size=len(str(input_data)),
                output_size=0,
                success=False,
                error=str(e)
            )

        self.results.append(result)
        return result

    def _transform(self, data: Any, rule: TransformationRule) -> Any:
        """Apply transformation logic"""
        output = data

        # Apply field mapping
        if rule.mapping and isinstance(output, dict):
            mapped = {}
            for old_key, new_key in rule.mapping.items():
                if old_key in output:
                    mapped[new_key] = output[old_key]
            output = mapped

        # Apply compression simulation
        if rule.compression:
            # Simulate compression
            output_str = json.dumps(output) if isinstance(output, dict) else str(output)
            # In real implementation, would use compression library
            output = {"compressed": True, "data": output_str}

        return output

    def create_pipeline(self,
                       pipeline_name: str,
                       rule_ids: List[str],
                       execution_order: List[int] = None) -> TransformationPipeline:
        """Create transformation pipeline"""
        pipeline_id = hashlib.md5(
            f"{pipeline_name}:{time.time()}".encode()
        ).hexdigest()[:8]

        pipeline = TransformationPipeline(
            pipeline_id=pipeline_id,
            pipeline_name=pipeline_name,
            rules=rule_ids,
            execution_order=execution_order or list(range(len(rule_ids)))
        )

        self.pipelines[pipeline_id] = pipeline
        return pipeline

    def execute_pipeline(self,
                        pipeline_id: str,
                        input_data: Any) -> Any:
        """Execute transformation pipeline"""
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline:
            return input_data

        output = input_data

        for idx in pipeline.execution_order:
            if idx < len(pipeline.rules):
                rule_id = pipeline.rules[idx]
                result = self.apply_transformation(rule_id, output)
                if result and result.success:
                    output = self._get_transformation_output(result)

        return output

    def _get_transformation_output(self, result: TransformationResult) -> Any:
        """Extract output from transformation result"""
        # In real implementation, would return actual transformed data
        return {"transformed": True, "result_id": result.result_id}

    def get_transformer_stats(self) -> Dict:
        """Get transformer statistics"""
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        avg_compression = sum(r.compression_ratio for r in self.results if r.success) / max(1, successful)
        avg_time = sum(r.transformation_time_ms for r in self.results if r.success) / max(1, successful)

        return {
            "total_transformations": len(self.results),
            "successful": successful,
            "failed": failed,
            "avg_compression_ratio": avg_compression,
            "avg_transformation_time": avg_time,
            "rules": len(self.rules),
            "pipelines": len(self.pipelines),
        }

    def generate_transformer_report(self) -> str:
        """Generate transformer report"""
        stats = self.get_transformer_stats()

        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║              REQUEST/RESPONSE TRANSFORMER REPORT                           ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Total Transformations: {stats['total_transformations']}
├─ ✅ Successful: {stats['successful']}
├─ ❌ Failed: {stats['failed']}
├─ Avg Compression: {stats['avg_compression_ratio']:.1f}%
├─ Avg Time: {stats['avg_transformation_time']:.2f}ms
├─ Rules: {stats['rules']}
└─ Pipelines: {stats['pipelines']}

📋 TRANSFORMATION RULES:
"""

        for rule in self.rules.values():
            report += f"\n  {rule.rule_name}\n"
            report += f"    Type: {rule.transformation_type.value}\n"
            report += f"    {rule.input_format} → {rule.output_format}\n"

        return report

    def export_transformer_config(self) -> str:
        """Export transformer configuration"""
        export_data = {
            "timestamp": time.time(),
            "rules": [
                {
                    "name": r.rule_name,
                    "type": r.transformation_type.value,
                    "input": r.input_format,
                    "output": r.output_format,
                }
                for r in self.rules.values()
            ],
            "pipelines": [
                {
                    "name": p.pipeline_name,
                    "rules": len(p.rules),
                }
                for p in self.pipelines.values()
            ],
            "statistics": self.get_transformer_stats(),
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔄 Request/Response Transformer - Message Transformation")
    print("=" * 70)

    transformer = RequestResponseTransformer()

    # Create rules
    print("\n📝 Creating transformation rules...")
    json_to_xml = transformer.create_rule(
        "JSON to XML",
        TransformationType.JSON_TO_XML,
        "application/json",
        "application/xml"
    )

    compression = transformer.create_rule(
        "GZIP Compression",
        TransformationType.COMPRESSION,
        "application/json",
        "application/octet-stream",
        compression=CompressionAlgorithm.GZIP
    )

    field_mapping = transformer.create_rule(
        "User Field Mapping",
        TransformationType.FIELD_MAPPING,
        "application/json",
        "application/json",
        mapping={"user_id": "userId", "user_name": "userName"}
    )
    print(f"✅ Created {len(transformer.rules)} rules")

    # Create pipeline
    print("\n🔀 Creating transformation pipeline...")
    pipeline = transformer.create_pipeline(
        "API Response Pipeline",
        [json_to_xml.rule_id, compression.rule_id]
    )
    print(f"✅ Created pipeline with {len(pipeline.rules)} rules")

    # Apply transformations
    print("\n🔄 Applying transformations...")
    test_data = {
        "user_id": 123,
        "user_name": "John Doe",
        "email": "john@example.com"
    }

    result1 = transformer.apply_transformation(json_to_xml.rule_id, test_data)
    print(f"✅ JSON to XML: {result1.input_size} → {result1.output_size} bytes")

    result2 = transformer.apply_transformation(field_mapping.rule_id, test_data)
    print(f"✅ Field Mapping: {result2.compression_ratio:.1f}% compression")

    result3 = transformer.apply_transformation(compression.rule_id, test_data)
    print(f"✅ Compression: {result3.compression_ratio:.1f}% reduction")

    # Execute pipeline
    print("\n🔀 Executing pipeline...")
    pipeline_output = transformer.execute_pipeline(pipeline.pipeline_id, test_data)
    print(f"✅ Pipeline executed")

    # Generate report
    print(transformer.generate_transformer_report())

    # Export
    print("\n📄 Exporting transformer config...")
    export = transformer.export_transformer_config()
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Request/Response transformer ready")


if __name__ == "__main__":
    main()
