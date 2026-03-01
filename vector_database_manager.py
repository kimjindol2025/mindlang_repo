#!/usr/bin/env python3
"""
Vector Database Manager - Vector embedding storage and similarity search
Manages vector embeddings, similarity search, and semantic retrieval
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
import hashlib
import json
import time
import random
import math


class VectorType(Enum):
    """Types of vectors"""
    EMBEDDING = "EMBEDDING"
    FEATURE = "FEATURE"
    DENSE = "DENSE"
    SPARSE = "SPARSE"


class IndexType(Enum):
    """Vector index types"""
    FLAT = "FLAT"
    IVF_FLAT = "IVF_FLAT"
    IVFPQ = "IVFPQ"
    HNSW = "HNSW"
    FAISS = "FAISS"


class DistanceMetric(Enum):
    """Distance/similarity metrics"""
    L2 = "L2"  # Euclidean
    COSINE = "COSINE"
    INNER_PRODUCT = "INNER_PRODUCT"
    HAMMING = "HAMMING"
    MANHATTAN = "MANHATTAN"


@dataclass
class Vector:
    """Vector data point"""
    vector_id: str
    embedding: List[float]
    metadata: Dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    vector_type: VectorType = VectorType.EMBEDDING


@dataclass
class VectorIndex:
    """Index over vectors"""
    index_id: str
    name: str
    index_type: IndexType
    dimension: int
    distance_metric: DistanceMetric
    vectors: Dict[str, Vector] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    size_mb: float = 0.0
    indexed: bool = False


@dataclass
class SearchResult:
    """Result of vector search"""
    result_id: str
    query_vector_id: str
    matched_vector_id: str
    distance: float
    similarity_score: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class VectorQuery:
    """Vector similarity search query"""
    query_id: str
    query_vector: List[float]
    index_id: str
    top_k: int = 10
    threshold: float = 0.0
    filters: Dict = field(default_factory=dict)
    results: List[SearchResult] = field(default_factory=list)
    execution_time_ms: float = 0.0


class VectorDatabaseManager:
    """
    Vector database management system

    Provides:
    - Vector storage and indexing
    - Similarity search (semantic search)
    - Approximate nearest neighbor search
    - Vector quantization
    - Batch operations
    - Index optimization
    """

    def __init__(self):
        self.indexes: Dict[str, VectorIndex] = {}
        self.vectors: Dict[str, Vector] = {}
        self.search_history: List[VectorQuery] = []
        self.embeddings_model = self._init_embeddings_model()

    def _init_embeddings_model(self) -> Dict:
        """Initialize embeddings model"""
        return {
            "model_name": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "trained_on": "1B text examples"
        }

    def create_index(self,
                    name: str,
                    dimension: int,
                    index_type: IndexType = IndexType.HNSW,
                    distance_metric: DistanceMetric = DistanceMetric.COSINE) -> VectorIndex:
        """
        Create vector index

        Args:
            name: Index name
            dimension: Vector dimension
            index_type: Type of index
            distance_metric: Distance metric

        Returns:
            Created VectorIndex
        """
        index_id = hashlib.md5(f"{name}:{time.time()}".encode()).hexdigest()[:8]

        index = VectorIndex(
            index_id=index_id,
            name=name,
            index_type=index_type,
            dimension=dimension,
            distance_metric=distance_metric
        )

        self.indexes[index_id] = index
        return index

    def add_vector(self,
                  index_id: str,
                  embedding: List[float],
                  metadata: Dict = None,
                  tags: Set[str] = None) -> Optional[Vector]:
        """
        Add vector to index

        Args:
            index_id: Target index
            embedding: Vector embedding
            metadata: Metadata
            tags: Tags for grouping

        Returns:
            Added Vector
        """
        index = self.indexes.get(index_id)
        if not index:
            return None

        # Validate dimension
        if len(embedding) != index.dimension:
            return None

        vector_id = hashlib.md5(
            f"{index_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()[:8]

        vector = Vector(
            vector_id=vector_id,
            embedding=embedding,
            metadata=metadata or {},
            tags=tags or set()
        )

        index.vectors[vector_id] = vector
        self.vectors[vector_id] = vector

        # Update index size
        index.size_mb += (len(embedding) * 8) / (1024 * 1024)

        return vector

    def add_vectors_batch(self,
                         index_id: str,
                         embeddings: List[List[float]],
                         metadatas: List[Dict] = None) -> List[Vector]:
        """Add multiple vectors"""
        vectors = []
        for i, embedding in enumerate(embeddings):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            vector = self.add_vector(index_id, embedding, metadata)
            if vector:
                vectors.append(vector)

        return vectors

    def build_index(self, index_id: str) -> bool:
        """Build index for faster search"""
        index = self.indexes.get(index_id)
        if not index:
            return False

        # Simulate index building
        time.sleep(0.1)

        index.indexed = True
        return True

    def search_similar(self,
                      index_id: str,
                      query_vector: List[float],
                      top_k: int = 10,
                      threshold: float = 0.0) -> VectorQuery:
        """
        Search for similar vectors

        Args:
            index_id: Target index
            query_vector: Query vector
            top_k: Number of results
            threshold: Minimum similarity threshold

        Returns:
            VectorQuery with results
        """
        query_id = hashlib.md5(f"{index_id}:{time.time()}".encode()).hexdigest()[:8]

        query = VectorQuery(
            query_id=query_id,
            query_vector=query_vector,
            index_id=index_id,
            top_k=top_k,
            threshold=threshold
        )

        index = self.indexes.get(index_id)
        if not index:
            return query

        start_time = time.time()

        # Calculate distances
        distances = []
        for vector_id, vector in index.vectors.items():
            distance = self._calculate_distance(
                query_vector,
                vector.embedding,
                index.distance_metric
            )

            similarity = 1 / (1 + distance) if index.distance_metric != DistanceMetric.COSINE else distance

            if similarity >= threshold:
                result = SearchResult(
                    result_id=hashlib.md5(f"{query_id}:{vector_id}".encode()).hexdigest()[:8],
                    query_vector_id=query_id,
                    matched_vector_id=vector_id,
                    distance=distance,
                    similarity_score=similarity,
                    metadata=vector.metadata
                )
                distances.append((result, similarity))

        # Sort by similarity and get top_k
        distances.sort(key=lambda x: x[1], reverse=True)
        query.results = [result for result, _ in distances[:top_k]]

        query.execution_time_ms = (time.time() - start_time) * 1000

        self.search_history.append(query)
        return query

    def _calculate_distance(self,
                           vec1: List[float],
                           vec2: List[float],
                           metric: DistanceMetric) -> float:
        """Calculate distance between vectors"""
        if metric == DistanceMetric.COSINE:
            return self._cosine_similarity(vec1, vec2)
        elif metric == DistanceMetric.L2:
            return self._euclidean_distance(vec1, vec2)
        elif metric == DistanceMetric.INNER_PRODUCT:
            return self._inner_product(vec1, vec2)
        else:
            return 0.0

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a ** 2 for a in vec1))
        norm2 = math.sqrt(sum(b ** 2 for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Euclidean distance"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))

    def _inner_product(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate inner product"""
        return sum(a * b for a, b in zip(vec1, vec2))

    def filter_by_metadata(self,
                          index_id: str,
                          filters: Dict) -> List[Vector]:
        """Filter vectors by metadata"""
        index = self.indexes.get(index_id)
        if not index:
            return []

        results = []
        for vector in index.vectors.values():
            matches = True
            for key, value in filters.items():
                if vector.metadata.get(key) != value:
                    matches = False
                    break
            if matches:
                results.append(vector)

        return results

    def get_index_stats(self, index_id: str) -> Dict:
        """Get index statistics"""
        index = self.indexes.get(index_id)
        if not index:
            return {}

        return {
            "index_id": index_id,
            "name": index.name,
            "type": index.index_type.value,
            "dimension": index.dimension,
            "metric": index.distance_metric.value,
            "vector_count": len(index.vectors),
            "size_mb": index.size_mb,
            "indexed": index.indexed,
        }

    def generate_vector_report(self) -> str:
        """Generate vector database report"""
        report = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                    VECTOR DATABASE REPORT                                  ║
╚════════════════════════════════════════════════════════════════════════════╝

📊 STATISTICS:
├─ Indexes: {len(self.indexes)}
├─ Total Vectors: {len(self.vectors)}
├─ Searches Performed: {len(self.search_history)}
└─ Model: {self.embeddings_model['model_name']}

📚 INDEXES:
"""

        for index in self.indexes.values():
            status = "🟢 Indexed" if index.indexed else "🟡 Not indexed"
            report += f"\n{status} {index.name}\n"
            report += f"  Type: {index.index_type.value}\n"
            report += f"  Dimension: {index.dimension}\n"
            report += f"  Metric: {index.distance_metric.value}\n"
            report += f"  Vectors: {len(index.vectors)}\n"
            report += f"  Size: {index.size_mb:.2f}MB\n"

        report += f"\n🔍 RECENT SEARCHES:\n"
        for search in self.search_history[-5:]:
            report += f"  • Query {search.query_id}: {len(search.results)} results in {search.execution_time_ms:.1f}ms\n"

        return report

    def export_vectors(self, index_id: str) -> str:
        """Export vectors as JSON"""
        index = self.indexes.get(index_id)
        if not index:
            return "{}"

        export_data = {
            "index_id": index_id,
            "name": index.name,
            "dimension": index.dimension,
            "vector_count": len(index.vectors),
            "sample_vectors": [
                {
                    "vector_id": vector_id,
                    "metadata": vector.metadata,
                    "tags": list(vector.tags),
                }
                for vector_id, vector in list(index.vectors.items())[:10]
            ]
        }
        return json.dumps(export_data, indent=2)


def main():
    """CLI interface"""
    print("🔍 Vector Database Manager - Semantic Search Infrastructure")
    print("=" * 70)

    manager = VectorDatabaseManager()

    # Create index
    print("\n📚 Creating vector index...")
    index = manager.create_index(
        "documents",
        dimension=384,
        index_type=IndexType.HNSW,
        distance_metric=DistanceMetric.COSINE
    )
    print(f"✅ Created index with dimension {index.dimension}")

    # Add vectors (simulated embeddings)
    print("\n➕ Adding vectors...")
    documents = [
        {"text": "Machine learning is powerful", "category": "ml"},
        {"text": "Deep learning transforms AI", "category": "dl"},
        {"text": "Natural language processing", "category": "nlp"},
        {"text": "Computer vision applications", "category": "cv"},
        {"text": "Neural networks are amazing", "category": "dl"},
    ]

    vectors = []
    for doc in documents:
        # Simulate embedding (random for demo)
        embedding = [random.uniform(-1, 1) for _ in range(384)]
        vector = manager.add_vector(
            index.index_id,
            embedding,
            metadata={"text": doc["text"], "category": doc["category"]},
            tags={doc["category"]}
        )
        if vector:
            vectors.append(vector)

    print(f"✅ Added {len(vectors)} vectors")

    # Build index
    print("\n🔨 Building index...")
    manager.build_index(index.index_id)
    print(f"✅ Index built")

    # Search
    print("\n🔎 Performing similarity search...")
    query_embedding = [random.uniform(-1, 1) for _ in range(384)]
    results = manager.search_similar(
        index.index_id,
        query_embedding,
        top_k=3,
        threshold=0.0
    )

    print(f"Found {len(results.results)} similar vectors")
    for i, result in enumerate(results.results[:3], 1):
        print(f"  {i}. Similarity: {result.similarity_score:.4f}")
        print(f"     Metadata: {result.metadata}")

    # Filter by metadata
    print("\n🔍 Filtering by metadata...")
    filtered = manager.filter_by_metadata(
        index.index_id,
        {"category": "dl"}
    )
    print(f"Found {len(filtered)} vectors with category='dl'")

    # Generate report
    print(manager.generate_vector_report())

    # Export
    print("\n📄 Exporting vectors...")
    export = manager.export_vectors(index.index_id)
    print(f"✅ Exported {len(export)} characters")

    print("\n" + "=" * 70)
    print("✨ Vector database ready for semantic search")


if __name__ == "__main__":
    main()
