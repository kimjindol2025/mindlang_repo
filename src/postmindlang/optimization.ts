/**
 * PostMindLang Optimizer
 * Optimizes compiled PostMindLang bytecode for performance and efficiency
 *
 * Includes:
 * - Matrix operation reordering
 * - Memory layout optimization
 * - Parallelism analysis and scheduling
 * - Numerical stability improvements
 */

import {
  PostMindLangBytecode,
  ExecutionPlan,
  ExecutionStage,
  ParallelGroup,
  DataflowEdge,
  Matrix,
  Vector,
  Tensor,
  Shape,
} from './mindlang_to_postmindlang';

// ============================================================================
// Memory Layout Configuration
// ============================================================================

export enum MemoryLayout {
  ROW_MAJOR = 'row_major',
  COLUMN_MAJOR = 'column_major',
  BLOCKED = 'blocked',
  INTERLEAVED = 'interleaved',
}

export interface MemoryLayoutConfig {
  layout: MemoryLayout;
  blockSize?: number; // For blocked layout
  alignment?: number; // Byte alignment
}

export interface MemoryOptimizationResult {
  recommendedLayout: MemoryLayout;
  estimatedMemoryUsage: number;
  accessPatterns: AccessPattern[];
  cacheLineUtilization: number; // 0-1
}

export interface AccessPattern {
  description: string;
  sequentiality: number; // 0-1: how sequential the access is
  stride: number; // Memory stride in elements
}

// ============================================================================
// Matrix Operation Optimization
// ============================================================================

export interface MatrixOperation {
  operationId: string;
  type: 'multiply' | 'add' | 'hadamard' | 'transpose';
  operands: {
    a: { shape: Shape; alias: string };
    b?: { shape: Shape; alias: string };
  };
  result: { shape: Shape; alias: string };
  flops: number;
}

export interface MatmulOptimization {
  originalOrder: string[];
  optimizedOrder: string[];
  estimatedSpeedup: number;
  estimatedMemorySaved: number;
}

export class MatrixOperationOptimizer {
  /**
   * Optimize matrix multiplication order using dynamic programming
   * Minimizes scalar multiplications (cost metric)
   */
  static optimizeMatmulOrder(operations: MatrixOperation[]): MatmulOptimization {
    // Find chain of matrix multiplications
    const chains = this.identifyMatmulChains(operations);
    const optimized: string[] = [];
    let totalSpeedup = 1.0;

    for (const chain of chains) {
      const dims = this.extractDimensions(chain, operations);
      const optimalOrder = this.computeOptimalOrder(dims);
      optimized.push(...optimalOrder);
      totalSpeedup *= this.computeSpeedup(dims);
    }

    return {
      originalOrder: operations.map(op => op.operationId),
      optimizedOrder: optimized,
      estimatedSpeedup: totalSpeedup,
      estimatedMemorySaved: totalSpeedup * 0.15, // Heuristic
    };
  }

  /**
   * Identify chains of matrix multiplications
   */
  private static identifyMatmulChains(operations: MatrixOperation[]): MatrixOperation[][] {
    const chains: MatrixOperation[][] = [];
    let currentChain: MatrixOperation[] = [];

    for (const op of operations) {
      if (op.type === 'multiply') {
        currentChain.push(op);
      } else {
        if (currentChain.length > 1) {
          chains.push(currentChain);
        }
        currentChain = [];
      }
    }

    if (currentChain.length > 1) {
      chains.push(currentChain);
    }

    return chains;
  }

  /**
   * Extract dimensions from operation chain
   */
  private static extractDimensions(
    chain: MatrixOperation[],
    allOps: MatrixOperation[],
  ): number[] {
    const dims: number[] = [];

    for (const op of chain) {
      const shapeA = op.operands.a.shape;
      dims.push(shapeA.dimensions[0] || 1);
      dims.push(shapeA.dimensions[1] || 1);

      if (op.operands.b) {
        dims.push(op.operands.b.shape.dimensions[1] || 1);
      }
    }

    return dims;
  }

  /**
   * Compute optimal parenthesization using DP
   */
  private static computeOptimalOrder(dims: number[]): string[] {
    const n = dims.length;
    const dp: number[][] = Array(n).fill(0).map(() => Array(n).fill(0));
    const split: number[][] = Array(n).fill(0).map(() => Array(n).fill(0));

    // Fill DP table
    for (let len = 2; len < n; len++) {
      for (let i = 0; i < n - len; i++) {
        const j = i + len;
        dp[i][j] = Infinity;

        for (let k = i + 1; k < j; k++) {
          const cost = dp[i][k] + dp[k][j] + dims[i] * dims[k] * dims[j];
          if (cost < dp[i][j]) {
            dp[i][j] = cost;
            split[i][j] = k;
          }
        }
      }
    }

    // Reconstruct order
    return this.reconstructOrder(split, 0, n - 1, []);
  }

  private static reconstructOrder(
    split: number[][],
    i: number,
    j: number,
    order: string[],
  ): string[] {
    if (i === j) {
      order.push(`A${i}`);
    } else {
      const k = split[i][j];
      this.reconstructOrder(split, i, k, order);
      this.reconstructOrder(split, k + 1, j, order);
      order.push(`*`);
    }
    return order;
  }

  private static computeSpeedup(dims: number[]): number {
    if (dims.length < 2) return 1.0;

    // Heuristic: typical speedup from reordering is 1.2-2x
    const avgDim = dims.reduce((a, b) => a + b) / dims.length;
    return 1 + Math.log(avgDim) / 10;
  }
}

// ============================================================================
// Memory Layout Optimizer
// ============================================================================

export class MemoryLayoutOptimizer {
  /**
   * Analyze access patterns and recommend optimal layout
   */
  static optimizeMemoryLayout(
    bytecode: PostMindLangBytecode,
  ): MemoryOptimizationResult {
    const accessPatterns = this.analyzeAccessPatterns(bytecode);
    const recommendedLayout = this.selectLayout(accessPatterns);
    const cacheUtilization = this.estimateCacheUtilization(accessPatterns, recommendedLayout);
    const memoryUsage = this.estimateMemoryUsage(bytecode);

    return {
      recommendedLayout,
      estimatedMemoryUsage: memoryUsage,
      accessPatterns,
      cacheLineUtilization: cacheUtilization,
    };
  }

  /**
   * Analyze memory access patterns from execution plan
   */
  private static analyzeAccessPatterns(bytecode: PostMindLangBytecode): AccessPattern[] {
    const patterns: AccessPattern[] = [];

    // Pattern 1: Sequential query access
    patterns.push({
      description: 'Query embedding read-only sequential',
      sequentiality: 0.95,
      stride: 1,
    });

    // Pattern 2: Matrix multiplication (typically 0-1 stride on one dimension)
    patterns.push({
      description: 'Matrix multiplication row-wise',
      sequentiality: 0.85,
      stride: bytecode.vectorSpace.pathDim,
    });

    // Pattern 3: Path computations (block-wise)
    patterns.push({
      description: 'Path computation block access',
      sequentiality: 0.70,
      stride: 64, // Typical cache line
    });

    // Pattern 4: Weight updates (sparse)
    patterns.push({
      description: 'Weight vector access (3 elements)',
      sequentiality: 1.0,
      stride: 1,
    });

    return patterns;
  }

  /**
   * Select optimal memory layout based on access patterns
   */
  private static selectLayout(patterns: AccessPattern[]): MemoryLayout {
    const avgSequentiality = patterns.reduce((sum, p) => sum + p.sequentiality, 0) / patterns.length;

    if (avgSequentiality > 0.85) {
      return MemoryLayout.ROW_MAJOR;
    } else if (avgSequentiality > 0.60) {
      return MemoryLayout.BLOCKED;
    } else {
      return MemoryLayout.COLUMN_MAJOR;
    }
  }

  /**
   * Estimate cache line utilization
   */
  private static estimateCacheUtilization(
    patterns: AccessPattern[],
    layout: MemoryLayout,
  ): number {
    const baseUtilization = patterns.reduce((sum, p) => sum + p.sequentiality, 0) / patterns.length;

    const layoutBonus = {
      [MemoryLayout.ROW_MAJOR]: 0.1,
      [MemoryLayout.COLUMN_MAJOR]: 0.05,
      [MemoryLayout.BLOCKED]: 0.15,
      [MemoryLayout.INTERLEAVED]: 0.08,
    };

    return Math.min(1.0, baseUtilization + (layoutBonus[layout] || 0));
  }

  /**
   * Estimate memory usage in bytes
   */
  private static estimateMemoryUsage(bytecode: PostMindLangBytecode): number {
    const { queryDim, latentDim, pathDim, weightDim } = bytecode.vectorSpace;

    // Estimate: paths (3) + intermediate results
    const pathMemory = 3 * pathDim * 8; // 3 paths × pathDim floats × 8 bytes
    const vectorMemory = (queryDim + latentDim + pathDim) * 8;
    const constantMemory = pathDim * pathDim * 3 * 8; // Path matrices

    return pathMemory + vectorMemory + constantMemory;
  }
}

// ============================================================================
// Parallelism Optimizer
// ============================================================================

export interface ParallelizationStrategy {
  stages: ExecutionStage[];
  parallelGroups: ParallelGroup[];
  estimatedSpeedup: number;
  syncPointCount: number;
}

export interface DataDependencyGraph {
  nodes: Set<string | number>;
  edges: Map<string | number, (string | number)[]>;
  criticalPath: (string | number)[];
}

export class ParallelismOptimizer {
  /**
   * Analyze and optimize parallelization opportunities
   */
  static optimizeParallelism(
    plan: ExecutionPlan,
    numThreads: number = 3,
  ): ParallelizationStrategy {
    // Build dependency graph
    const depGraph = this.buildDependencyGraph(plan);

    // Identify parallelizable stages
    const parallelGroups = this.identifyParallelGroups(plan, depGraph, numThreads);

    // Compute speedup
    const criticalPathLength = this.computeCriticalPathLength(depGraph);
    const estimatedSpeedup = this.estimateSpeedup(plan, parallelGroups, criticalPathLength);

    return {
      stages: plan.stages,
      parallelGroups,
      estimatedSpeedup,
      syncPointCount: parallelGroups.reduce((sum, g) => sum + g.syncPoints.length, 0),
    };
  }

  /**
   * Build data dependency graph
   */
  private static buildDependencyGraph(plan: ExecutionPlan): DataDependencyGraph {
    const nodes = new Set<string | number>();
    const edges = new Map<string | number, (string | number)[]>();

    // Add nodes
    for (const stage of plan.stages) {
      for (const nodeId of stage.nodeIds) {
        nodes.add(nodeId);
      }
    }

    // Add edges from dataflow
    for (const edge of plan.dataflow) {
      if (!edges.has(edge.from)) {
        edges.set(edge.from, []);
      }
      edges.get(edge.from)!.push(edge.to);
    }

    // Compute critical path
    const criticalPath = this.computeCriticalPath(nodes, edges);

    return { nodes, edges, criticalPath };
  }

  /**
   * Compute critical path (longest path in DAG)
   */
  private static computeCriticalPath(
    nodes: Set<string | number>,
    edges: Map<string | number, (string | number)[]>,
  ): (string | number)[] {
    const path: (string | number)[] = [];
    const maxLength = Array.from(nodes).length;

    // Simple heuristic: follow longest chain
    let current: string | number | null = null;
    let maxOutEdges = 0;

    for (const node of nodes) {
      const outEdgeCount = edges.get(node)?.length || 0;
      if (outEdgeCount > maxOutEdges) {
        maxOutEdges = outEdgeCount;
        current = node;
      }
    }

    if (current) path.push(current);

    for (let i = 0; i < maxLength && current; i++) {
      const nextNodes = edges.get(current) || [];
      if (nextNodes.length > 0) {
        current = nextNodes[0];
        path.push(current);
      } else {
        break;
      }
    }

    return path;
  }

  /**
   * Identify groups of stages that can execute in parallel
   */
  private static identifyParallelGroups(
    plan: ExecutionPlan,
    depGraph: DataDependencyGraph,
    numThreads: number,
  ): ParallelGroup[] {
    const groups: ParallelGroup[] = [];
    const processed = new Set<string>();

    for (const stage of plan.stages) {
      if (processed.has(stage.stageId)) continue;

      if (stage.isParallelizable) {
        // Check for independent stages
        const independentStages = [stage.stageId];

        for (const otherStage of plan.stages) {
          if (otherStage.stageId === stage.stageId || processed.has(otherStage.stageId)) {
            continue;
          }

          if (this.areStagesIndependent(stage, otherStage, depGraph)) {
            independentStages.push(otherStage.stageId);
            if (independentStages.length >= numThreads) break;
          }
        }

        if (independentStages.length > 1) {
          groups.push({
            groupId: `group_${groups.length}`,
            stages: independentStages,
            syncPoints: [
              `sync_before_${stage.stageId}`,
              `sync_after_${stage.stageId}`,
            ],
          });

          for (const stageId of independentStages) {
            processed.add(stageId);
          }
        }
      }
    }

    return groups;
  }

  /**
   * Check if two stages are data-independent
   */
  private static areStagesIndependent(
    stage1: ExecutionStage,
    stage2: ExecutionStage,
    depGraph: DataDependencyGraph,
  ): boolean {
    // Check if any node in stage1 depends on nodes in stage2
    for (const nodeId1 of stage1.nodeIds) {
      const deps = depGraph.edges.get(nodeId1) || [];
      for (const nodeId2 of stage2.nodeIds) {
        if (deps.includes(nodeId2)) {
          return false;
        }
      }
    }

    // Check reverse
    for (const nodeId2 of stage2.nodeIds) {
      const deps = depGraph.edges.get(nodeId2) || [];
      for (const nodeId1 of stage1.nodeIds) {
        if (deps.includes(nodeId1)) {
          return false;
        }
      }
    }

    return true;
  }

  /**
   * Compute critical path length
   */
  private static computeCriticalPathLength(depGraph: DataDependencyGraph): number {
    return depGraph.criticalPath.length;
  }

  /**
   * Estimate speedup from parallelization
   */
  private static estimateSpeedup(
    plan: ExecutionPlan,
    parallelGroups: ParallelGroup[],
    criticalPathLength: number,
  ): number {
    if (parallelGroups.length === 0) return 1.0;

    const totalStages = plan.stages.length;
    const parallelizedStages = parallelGroups.reduce((sum, g) => sum + g.stages.length, 0);
    const sequentialStages = totalStages - parallelizedStages;

    // Amdahl's law approximation
    const parallelFraction = parallelizedStages / totalStages;
    const numThreads = 3; // Fixed for 3-way fork-join

    return 1 / (1 - parallelFraction + parallelFraction / numThreads);
  }
}

// ============================================================================
// Numerical Stability Optimizer
// ============================================================================

export interface NumericalConfig {
  underflowThreshold: number;
  overflowThreshold: number;
  normalizationStrategy: 'layer_norm' | 'batch_norm' | 'none';
  preconditioning: boolean;
}

export class NumericalStabilityOptimizer {
  /**
   * Generate numerical stability configuration
   */
  static optimizeNumericalStability(
    bytecode: PostMindLangBytecode,
  ): NumericalConfig {
    return {
      underflowThreshold: 1e-37,
      overflowThreshold: 1e37,
      normalizationStrategy: 'layer_norm',
      preconditioning: true,
    };
  }

  /**
   * Apply layer normalization to prevent numerical issues
   */
  static applyLayerNormalization(vector: Vector): Vector {
    const mean = vector.reduce((sum, x) => sum + x, 0) / vector.length;
    const variance = vector.reduce((sum, x) => sum + (x - mean) ** 2, 0) / vector.length;
    const stddev = Math.sqrt(variance + 1e-8);

    return vector.map(x => (x - mean) / stddev);
  }

  /**
   * Clip values to prevent overflow/underflow
   */
  static clipValues(vector: Vector, min: number = -1e10, max: number = 1e10): Vector {
    return vector.map(x => Math.max(min, Math.min(max, x)));
  }

  /**
   * Compute condition number estimate
   */
  static estimateConditionNumber(matrix: Matrix): number {
    // Simplified: ratio of max to min eigenvalue
    if (matrix.length === 0) return 1;

    const norms = matrix.map(row => Math.sqrt(row.reduce((sum, x) => sum + x * x, 0)));
    const maxNorm = Math.max(...norms);
    const minNorm = Math.min(...norms.filter(n => n > 0));

    return maxNorm / Math.max(minNorm, 1e-10);
  }
}

// ============================================================================
// Optimization Report
// ============================================================================

export interface OptimizationReport {
  matmulOptimization: MatmulOptimization;
  memoryOptimization: MemoryOptimizationResult;
  parallelizationStrategy: ParallelizationStrategy;
  numericalConfig: NumericalConfig;
  estimatedOverallSpeedup: number;
  recommendations: string[];
}

export class PostMindLangOptimizer {
  /**
   * Run full optimization suite
   */
  static optimize(bytecode: PostMindLangBytecode): OptimizationReport {
    const matmulOpt = this.optimizeMatmul(bytecode);
    const memoryOpt = MemoryLayoutOptimizer.optimizeMemoryLayout(bytecode);
    const parallelOpt = ParallelismOptimizer.optimizeParallelism(bytecode.executionPlan, 3);
    const numericalOpt = NumericalStabilityOptimizer.optimizeNumericalStability(bytecode);

    const overallSpeedup = matmulOpt.estimatedSpeedup * parallelOpt.estimatedSpeedup * 1.1;

    const recommendations = this.generateRecommendations(
      matmulOpt,
      memoryOpt,
      parallelOpt,
      numericalOpt,
    );

    return {
      matmulOptimization: matmulOpt,
      memoryOptimization: memoryOpt,
      parallelizationStrategy: parallelOpt,
      numericalConfig: numericalOpt,
      estimatedOverallSpeedup: overallSpeedup,
      recommendations,
    };
  }

  private static optimizeMatmul(bytecode: PostMindLangBytecode): MatmulOptimization {
    const operations: MatrixOperation[] = [];

    // Create synthetic matrix operations for optimization
    operations.push({
      operationId: 'encode_q',
      type: 'multiply',
      operands: {
        a: { shape: { dimensions: [1, bytecode.vectorSpace.queryDim], totalElements: bytecode.vectorSpace.queryDim }, alias: 'Q' },
        b: { shape: { dimensions: [bytecode.vectorSpace.queryDim, bytecode.vectorSpace.latentDim], totalElements: bytecode.vectorSpace.queryDim * bytecode.vectorSpace.latentDim }, alias: 'E_matrix' },
      },
      result: { shape: { dimensions: [1, bytecode.vectorSpace.latentDim], totalElements: bytecode.vectorSpace.latentDim }, alias: 'encoded' },
      flops: bytecode.vectorSpace.queryDim * bytecode.vectorSpace.latentDim,
    });

    return MatrixOperationOptimizer.optimizeMatmulOrder(operations);
  }

  private static generateRecommendations(
    matmulOpt: MatmulOptimization,
    memoryOpt: MemoryOptimizationResult,
    parallelOpt: ParallelizationStrategy,
    numericalOpt: NumericalConfig,
  ): string[] {
    const recommendations: string[] = [];

    if (matmulOpt.estimatedSpeedup > 1.2) {
      recommendations.push(`Use optimized matrix multiplication order for ${matmulOpt.estimatedSpeedup.toFixed(2)}x speedup`);
    }

    recommendations.push(`Use ${memoryOpt.recommendedLayout} memory layout (cache utilization: ${(memoryOpt.cacheLineUtilization * 100).toFixed(1)}%)`);

    if (parallelOpt.estimatedSpeedup > 1.5) {
      recommendations.push(`Parallelize ${parallelOpt.parallelGroups.length} stage groups for ${parallelOpt.estimatedSpeedup.toFixed(2)}x speedup`);
    }

    if (numericalOpt.preconditioning) {
      recommendations.push('Apply layer normalization for numerical stability');
    }

    return recommendations;
  }
}
