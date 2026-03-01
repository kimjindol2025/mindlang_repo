/**
 * MindLang to PostMindLang Compiler
 * Converts MindLang AST to PostMindLang Bytecode with Vector/Tensor representations
 *
 * This compiler performs semantic-preserving transformation of MindLang programs
 * into mathematical vector spaces, enabling parallel tensor operations.
 */

import {
  ASTNode,
  QueryNode,
  EncodeNode,
  PathNode,
  WeightNode,
  EnsembleNode,
  CritiqueNode,
  SampleNode,
  DetokenizeNode,
  Program,
  isQueryNode,
  isEncodeNode,
  isPathNode,
  isWeightNode,
  isEnsembleNode,
  isCritiqueNode,
  isSampleNode,
  isDetokenizeNode,
  getNodeInputVariables,
  getNodeOutputVariable,
} from '../ast';

// ============================================================================
// PostMindLang Core Types
// ============================================================================

export type Tensor = number[] | number[][] | number[][][];
export type Matrix = number[][];
export type Vector = number[];
export type Scalar = number;

export interface Shape {
  dimensions: number[];
  totalElements: number;
  stride?: number[];
}

export interface Subspace {
  basis: Matrix;
  dimension: number;
  constraints?: Constraint[];
}

export interface Constraint {
  type: 'norm' | 'range' | 'orthogonal' | 'probabilistic';
  params: number[];
}

export interface QueryEncoder {
  embed: (query: string) => Vector;
  project: (embedding: Vector, targetDim: number) => Vector;
  normalize: (embedding: Vector) => Vector;
}

export interface PathMatrix {
  matrix: Matrix;
  pathType: 'analytical' | 'creative' | 'empirical';
  properties: PathProperties;
}

export interface PathProperties {
  linearity: number; // 0: non-linear, 1: fully linear
  diversity: number; // 0: deterministic, 1: fully stochastic
  confidence: number; // 0-1: epistemic confidence
}

export interface WeightFunction {
  compute: (query: Vector) => Vector; // Softmax over weights
  gradient: (loss: number) => Vector; // Gradient for backprop
  constraints: Constraint[];
}

export interface EnsembleFunction {
  combine: (p_a: Vector, p_b: Vector, p_c: Vector, w: Vector) => Vector;
  votingRule: 'softmax' | 'majority' | 'borda';
  gradientFn: (output: Vector, loss: number) => { grad_a: Vector; grad_b: Vector; grad_c: Vector; grad_w: Vector };
}

export interface CritiqueFunction {
  lossFn: (output: Vector, target: Vector) => Scalar;
  gradientFn: (output: Vector, target: Vector) => Vector;
  confidenceThreshold: number;
}

export interface SamplerFunction {
  sample: (logits: Vector, temperature: number) => Vector;
  temperature: number;
  threshold: number;
}

export interface PostMindLangBytecode {
  metadata: {
    version: string;
    compiledAt: string;
    sourceNodes: number;
    tensorDimensions: { [key: string]: Shape };
  };
  encoder: QueryEncoder;
  pathMatrices: {
    analytical: PathMatrix;
    creative: PathMatrix;
    empirical: PathMatrix;
  };
  weightFunction: WeightFunction;
  ensembleFunction: EnsembleFunction;
  critiqueFunction: CritiqueFunction;
  samplerFunction: SamplerFunction;
  vectorSpace: {
    queryDim: number;
    latentDim: number;
    pathDim: number;
    weightDim: number;
  };
  executionPlan: ExecutionPlan;
  variables: VariableMap;
  constants: ConstantMap;
}

export interface ExecutionPlan {
  stages: ExecutionStage[];
  parallelGroups: ParallelGroup[];
  dataflow: DataflowEdge[];
}

export interface ExecutionStage {
  stageId: string;
  nodeIds: (string | number)[];
  dependencies: string[];
  isParallelizable: boolean;
  estimatedCost: number;
}

export interface ParallelGroup {
  groupId: string;
  stages: string[];
  syncPoints: string[];
}

export interface DataflowEdge {
  from: string | number;
  to: string | number;
  variable: string;
  tensorShape: Shape;
}

export interface VariableMap {
  [varName: string]: {
    shape: Shape;
    subspace: Subspace;
    dtype: 'vector' | 'matrix' | 'scalar';
    dimension: number;
  };
}

export interface ConstantMap {
  [constName: string]: {
    value: Tensor;
    shape: Shape;
    dtype: 'vector' | 'matrix' | 'scalar';
  };
}

// ============================================================================
// Query Encoder Implementation
// ============================================================================

class SimpleQueryEncoder implements QueryEncoder {
  private embeddingDim: number;
  private dictionary: Map<string, Vector>;

  constructor(embeddingDim: number = 768) {
    this.embeddingDim = embeddingDim;
    this.dictionary = new Map();
    this.initializeDictionary();
  }

  private initializeDictionary(): void {
    // Simple hash-based embedding generation
    const commonTerms = [
      'query', 'context', 'analyze', 'create', 'empirical',
      'reasoning', 'logic', 'intuition', 'data', 'pattern'
    ];

    for (const term of commonTerms) {
      this.dictionary.set(term, this.generateSeededEmbedding(term));
    }
  }

  private generateSeededEmbedding(seed: string): Vector {
    const embedding: Vector = new Array(this.embeddingDim);
    let hash = 0;

    for (let i = 0; i < seed.length; i++) {
      const char = seed.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }

    for (let i = 0; i < this.embeddingDim; i++) {
      const angle = (hash * (i + 1)) / (this.embeddingDim * 31);
      embedding[i] = Math.sin(angle + Math.cos(hash * i / this.embeddingDim));
    }

    return this.normalize(embedding);
  }

  embed(query: string): Vector {
    const tokens = query.toLowerCase().split(/\s+/);
    const aggregatedEmbedding = new Array(this.embeddingDim).fill(0);

    for (const token of tokens) {
      const embedding = this.dictionary.has(token)
        ? this.dictionary.get(token)!
        : this.generateSeededEmbedding(token);

      for (let i = 0; i < this.embeddingDim; i++) {
        aggregatedEmbedding[i] += embedding[i];
      }
    }

    return this.normalize(aggregatedEmbedding);
  }

  project(embedding: Vector, targetDim: number): Vector {
    if (embedding.length <= targetDim) {
      const padded = [...embedding];
      while (padded.length < targetDim) {
        padded.push(0);
      }
      return padded;
    }

    // Simple projection via truncation and rescaling
    const projected = embedding.slice(0, targetDim);
    const scale = embedding.length / targetDim;
    return projected.map(x => x * scale);
  }

  normalize(vector: Vector): Vector {
    const norm = Math.sqrt(vector.reduce((sum, x) => sum + x * x, 0));
    if (norm === 0) return vector;
    return vector.map(x => x / norm);
  }
}

// ============================================================================
// Path Matrix Generators
// ============================================================================

class PathMatrixGenerator {
  static generateAnalyticalPath(inputDim: number, outputDim: number): PathMatrix {
    // Analytical path: High linearity, low diversity, high confidence
    // Use orthogonal matrix (Gram-Schmidt)
    const matrix = this.generateOrthogonalMatrix(inputDim, outputDim);

    return {
      matrix,
      pathType: 'analytical',
      properties: {
        linearity: 0.95,
        diversity: 0.05,
        confidence: 0.90,
      },
    };
  }

  static generateCreativePath(inputDim: number, outputDim: number): PathMatrix {
    // Creative path: Moderate linearity, high diversity, moderate confidence
    const matrix = this.generateRandomMatrix(inputDim, outputDim);
    // Apply non-linear transformations
    const transformedMatrix = matrix.map(row =>
      row.map(x => Math.tanh(x) * 0.5 + x * 0.5)
    );

    return {
      matrix: transformedMatrix,
      pathType: 'creative',
      properties: {
        linearity: 0.45,
        diversity: 0.85,
        confidence: 0.60,
      },
    };
  }

  static generateEmpiricalPath(inputDim: number, outputDim: number, data?: Vector[]): PathMatrix {
    // Empirical path: Data-driven, medium properties
    let matrix: Matrix;

    if (data && data.length > 0) {
      // PCA-like projection from data
      matrix = this.computePCAMatrix(data, outputDim);
    } else {
      // Fallback: Random but normalized
      matrix = this.generateRandomMatrix(inputDim, outputDim);
      for (let i = 0; i < matrix.length; i++) {
        const norm = Math.sqrt(matrix[i].reduce((sum, x) => sum + x * x, 0));
        if (norm > 0) {
          matrix[i] = matrix[i].map(x => x / norm);
        }
      }
    }

    return {
      matrix,
      pathType: 'empirical',
      properties: {
        linearity: 0.70,
        diversity: 0.50,
        confidence: 0.75,
      },
    };
  }

  private static generateOrthogonalMatrix(rows: number, cols: number): Matrix {
    const n = Math.min(rows, cols);
    const matrix: Matrix = [];

    for (let i = 0; i < n; i++) {
      const row = new Array(cols).fill(0);
      row[i % cols] = 1;
      matrix.push(row);
    }

    // Pad if needed
    while (matrix.length < rows) {
      const row = new Array(cols).fill(0);
      row[matrix.length % cols] = 1;
      matrix.push(row);
    }

    return matrix;
  }

  private static generateRandomMatrix(rows: number, cols: number): Matrix {
    const matrix: Matrix = [];
    for (let i = 0; i < rows; i++) {
      const row: Vector = [];
      for (let j = 0; j < cols; j++) {
        row.push(Math.random() * 2 - 1);
      }
      matrix.push(row);
    }
    return matrix;
  }

  private static computePCAMatrix(data: Vector[], outputDim: number): Matrix {
    // Simplified PCA: just use data rows as basis, weighted by variance
    const matrix: Matrix = [];
    const n = Math.min(data.length, outputDim);

    for (let i = 0; i < n; i++) {
      matrix.push([...data[i % data.length]]);
    }

    return matrix;
  }
}

// ============================================================================
// Weight Function
// ============================================================================

class AdaptiveWeightFunction implements WeightFunction {
  constraints: Constraint[];

  constructor(queryDim: number) {
    this.constraints = [
      {
        type: 'norm',
        params: [1.0], // L1 norm = 1 (probability simplex)
      },
      {
        type: 'range',
        params: [0, 1], // Each weight in [0, 1]
      },
    ];
  }

  compute(query: Vector): Vector {
    // Simulate f(q) that produces unnormalized weights
    const queryFeatures = [
      this.computeAnalyticalityScore(query),
      this.computeCreativityScore(query),
      this.computeEmpiricalityScore(query),
    ];

    // Apply softmax to get normalized weights
    return this.softmax(queryFeatures);
  }

  gradient(loss: number): Vector {
    // Simplified gradient: return loss signal distributed
    return [loss / 3, loss / 3, loss / 3];
  }

  private computeAnalyticalityScore(query: Vector): number {
    // Higher for deterministic, structured queries
    const variance = this.computeVariance(query);
    return 1 / (1 + variance); // Inverse sigmoid behavior
  }

  private computeCreativityScore(query: Vector): number {
    // Higher for diverse, exploratory queries
    const variance = this.computeVariance(query);
    return Math.tanh(variance);
  }

  private computeEmpiricalityScore(query: Vector): number {
    // Higher for data-heavy queries
    const magnitude = Math.sqrt(query.reduce((sum, x) => sum + x * x, 0));
    return Math.min(1, magnitude / 10);
  }

  private computeVariance(vector: Vector): number {
    const mean = vector.reduce((sum, x) => sum + x, 0) / vector.length;
    return vector.reduce((sum, x) => sum + (x - mean) ** 2, 0) / vector.length;
  }

  private softmax(values: Vector): Vector {
    const maxVal = Math.max(...values);
    const exps = values.map(v => Math.exp(v - maxVal));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sum);
  }
}

// ============================================================================
// Ensemble Function
// ============================================================================

class VectorEnsembleFunction implements EnsembleFunction {
  votingRule: 'softmax' | 'majority' | 'borda' = 'softmax';

  combine(p_a: Vector, p_b: Vector, p_c: Vector, w: Vector): Vector {
    // w = [w_a, w_b, w_c] where sum(w) = 1
    const result = new Array(p_a.length).fill(0);

    for (let i = 0; i < p_a.length; i++) {
      result[i] = w[0] * p_a[i] + w[1] * p_b[i] + w[2] * p_c[i];
    }

    return result;
  }

  gradientFn(output: Vector, loss: number): {
    grad_a: Vector;
    grad_b: Vector;
    grad_c: Vector;
    grad_w: Vector;
  } {
    const batchSize = output.length;
    const lossPerElement = loss / batchSize;

    return {
      grad_a: new Array(output.length).fill(lossPerElement),
      grad_b: new Array(output.length).fill(lossPerElement),
      grad_c: new Array(output.length).fill(lossPerElement),
      grad_w: [lossPerElement / 3, lossPerElement / 3, lossPerElement / 3],
    };
  }
}

// ============================================================================
// Critique Function
// ============================================================================

class VectorCritiqueFunction implements CritiqueFunction {
  confidenceThreshold: number;

  constructor(threshold: number = 0.5) {
    this.confidenceThreshold = threshold;
  }

  lossFn(output: Vector, target: Vector): Scalar {
    // L2 loss
    let sum = 0;
    for (let i = 0; i < output.length; i++) {
      const diff = output[i] - (target[i] || 0);
      sum += diff * diff;
    }
    return sum / output.length;
  }

  gradientFn(output: Vector, target: Vector): Vector {
    // Gradient of L2 loss
    const gradient = new Array(output.length);
    for (let i = 0; i < output.length; i++) {
      gradient[i] = 2 * (output[i] - (target[i] || 0)) / output.length;
    }
    return gradient;
  }
}

// ============================================================================
// Sampler Function
// ============================================================================

class TemperatureSampler implements SamplerFunction {
  temperature: number;
  threshold: number;

  constructor(temperature: number = 1.0, threshold: number = 0.1) {
    this.temperature = temperature;
    this.threshold = threshold;
  }

  sample(logits: Vector, temperature: number = this.temperature): Vector {
    // Apply temperature scaling
    const scaledLogits = logits.map(x => x / temperature);

    // Apply softmax
    const maxLogit = Math.max(...scaledLogits);
    const exps = scaledLogits.map(x => Math.exp(x - maxLogit));
    const sum = exps.reduce((a, b) => a + b, 0);
    const probs = exps.map(e => e / sum);

    // Filter by threshold
    const filtered = probs.map(p => (p >= this.threshold ? p : 0));
    const normSum = filtered.reduce((a, b) => a + b, 0);

    return normSum > 0
      ? filtered.map(p => p / normSum)
      : probs; // Fallback to original if all filtered out
  }
}

// ============================================================================
// Main Compiler Class
// ============================================================================

export class MindLangToPostMindLangCompiler {
  private encoder: QueryEncoder;
  private variableMap: VariableMap = {};
  private constantMap: ConstantMap = {};
  private dataflow: DataflowEdge[] = [];
  private queryDim: number = 768;
  private latentDim: number = 512;
  private pathDim: number = 256;

  constructor(config?: { queryDim?: number; latentDim?: number; pathDim?: number }) {
    this.queryDim = config?.queryDim || 768;
    this.latentDim = config?.latentDim || 512;
    this.pathDim = config?.pathDim || 256;
    this.encoder = new SimpleQueryEncoder(this.queryDim);
  }

  /**
   * Compile a complete MindLang program to PostMindLang bytecode
   */
  compile(program: Program): PostMindLangBytecode {
    this.variableMap = {};
    this.constantMap = {};
    this.dataflow = [];

    // Analyze program structure
    this.analyzeProgram(program);

    // Compile individual components
    const pathMatrices = this.compilePathMatrices(program);
    const weightFunction = this.compileWeightFunction(program);
    const ensembleFunction = this.compileEnsembleFunction(program);
    const critiqueFunction = this.compileCritiqueFunction(program);
    const samplerFunction = this.compileSamplerFunction(program);

    // Build execution plan
    const executionPlan = this.buildExecutionPlan(program);

    return {
      metadata: {
        version: '1.0.0',
        compiledAt: new Date().toISOString(),
        sourceNodes: program.statements.length,
        tensorDimensions: this.extractTensorDimensions(),
      },
      encoder: this.encoder,
      pathMatrices,
      weightFunction,
      ensembleFunction,
      critiqueFunction,
      samplerFunction,
      vectorSpace: {
        queryDim: this.queryDim,
        latentDim: this.latentDim,
        pathDim: this.pathDim,
        weightDim: 3, // Fixed: alpha, beta, gamma
      },
      executionPlan,
      variables: this.variableMap,
      constants: this.constantMap,
    };
  }

  /**
   * Analyze program structure and build variable map
   */
  private analyzeProgram(program: Program): void {
    for (const node of program.statements) {
      const outputVar = getNodeOutputVariable(node);
      if (outputVar) {
        this.variableMap[outputVar] = this.inferVariableShape(node);
      }

      // Track dataflow edges
      const inputVars = getNodeInputVariables(node);
      for (const inputVar of inputVars) {
        this.dataflow.push({
          from: inputVar,
          to: node.id || 'unknown',
          variable: inputVar,
          tensorShape: this.variableMap[inputVar]?.shape || this.getDefaultShape(),
        });
      }
    }
  }

  /**
   * Infer variable shape based on node type
   */
  private inferVariableShape(node: ASTNode): {
    shape: Shape;
    subspace: Subspace;
    dtype: 'vector' | 'matrix' | 'scalar';
    dimension: number;
  } {
    if (isQueryNode(node)) {
      return {
        shape: { dimensions: [this.queryDim], totalElements: this.queryDim },
        subspace: { basis: [[]], dimension: this.queryDim },
        dtype: 'vector',
        dimension: this.queryDim,
      };
    }

    if (isEncodeNode(node)) {
      return {
        shape: { dimensions: [this.latentDim], totalElements: this.latentDim },
        subspace: { basis: [[]], dimension: this.latentDim },
        dtype: 'vector',
        dimension: this.latentDim,
      };
    }

    if (isPathNode(node)) {
      return {
        shape: { dimensions: [this.pathDim], totalElements: this.pathDim },
        subspace: { basis: [[]], dimension: this.pathDim },
        dtype: 'vector',
        dimension: this.pathDim,
      };
    }

    if (isWeightNode(node)) {
      return {
        shape: { dimensions: [3], totalElements: 3 },
        subspace: { basis: [[]], dimension: 3 },
        dtype: 'vector',
        dimension: 3,
      };
    }

    if (isEnsembleNode(node)) {
      return {
        shape: { dimensions: [this.pathDim], totalElements: this.pathDim },
        subspace: { basis: [[]], dimension: this.pathDim },
        dtype: 'vector',
        dimension: this.pathDim,
      };
    }

    // Default
    return {
      shape: { dimensions: [this.queryDim], totalElements: this.queryDim },
      subspace: { basis: [[]], dimension: this.queryDim },
      dtype: 'vector',
      dimension: this.queryDim,
    };
  }

  /**
   * Get default shape for unknown variables
   */
  private getDefaultShape(): Shape {
    return {
      dimensions: [this.queryDim],
      totalElements: this.queryDim,
    };
  }

  /**
   * Compile path matrices (analytical, creative, empirical)
   */
  private compilePathMatrices(program: Program): {
    analytical: PathMatrix;
    creative: PathMatrix;
    empirical: PathMatrix;
  } {
    // Extract data if available from empirical paths
    const empiricalData: Vector[] = [];

    for (const node of program.statements) {
      if (isPathNode(node) && node.pathType === 'empirical') {
        // In a real implementation, would extract actual data
        // For now, create placeholder
      }
    }

    return {
      analytical: PathMatrixGenerator.generateAnalyticalPath(this.queryDim, this.pathDim),
      creative: PathMatrixGenerator.generateCreativePath(this.queryDim, this.pathDim),
      empirical: PathMatrixGenerator.generateEmpiricalPath(this.queryDim, this.pathDim, empiricalData),
    };
  }

  /**
   * Compile weight function
   */
  private compileWeightFunction(program: Program): WeightFunction {
    return new AdaptiveWeightFunction(this.queryDim);
  }

  /**
   * Compile ensemble function
   */
  private compileEnsembleFunction(program: Program): EnsembleFunction {
    return new VectorEnsembleFunction();
  }

  /**
   * Compile critique function
   */
  private compileCritiqueFunction(program: Program): CritiqueFunction {
    let threshold = 0.5;

    for (const node of program.statements) {
      if (isCritiqueNode(node)) {
        threshold = node.confidenceThreshold || 0.5;
        break;
      }
    }

    return new VectorCritiqueFunction(threshold);
  }

  /**
   * Compile sampler function
   */
  private compileSamplerFunction(program: Program): SamplerFunction {
    let temperature = 1.0;
    let threshold = 0.1;

    for (const node of program.statements) {
      if (isSampleNode(node)) {
        temperature = node.temperature || 1.0;
        threshold = node.threshold || 0.1;
        break;
      }
    }

    return new TemperatureSampler(temperature, threshold);
  }

  /**
   * Build execution plan with parallelization information
   */
  private buildExecutionPlan(program: Program): ExecutionPlan {
    const stages: ExecutionStage[] = [];
    const parallelGroups: ParallelGroup[] = [];
    let stageCounter = 0;

    // Stage 1: Query and Encoding
    const stage1Nodes: (string | number)[] = [];
    for (const node of program.statements) {
      if (isQueryNode(node) || isEncodeNode(node)) {
        stage1Nodes.push(node.id || stageCounter);
      }
    }
    if (stage1Nodes.length > 0) {
      stages.push({
        stageId: 'stage_query_encode',
        nodeIds: stage1Nodes,
        dependencies: [],
        isParallelizable: true,
        estimatedCost: stage1Nodes.length * 100,
      });
    }

    // Stage 2: Path computation (highly parallelizable)
    const pathNodes = program.statements.filter(n => isPathNode(n));
    if (pathNodes.length > 0) {
      stages.push({
        stageId: 'stage_paths_parallel',
        nodeIds: pathNodes.map((n, i) => n.id || stageCounter + i),
        dependencies: ['stage_query_encode'],
        isParallelizable: true,
        estimatedCost: pathNodes.length * 200,
      });

      parallelGroups.push({
        groupId: 'group_paths',
        stages: ['stage_paths_parallel'],
        syncPoints: ['sync_paths_complete'],
      });
    }

    // Stage 3: Weight computation
    const weightNodes = program.statements.filter(n => isWeightNode(n));
    if (weightNodes.length > 0) {
      stages.push({
        stageId: 'stage_weights',
        nodeIds: weightNodes.map((n, i) => n.id || stageCounter + i),
        dependencies: ['stage_query_encode'],
        isParallelizable: false,
        estimatedCost: weightNodes.length * 50,
      });
    }

    // Stage 4: Ensemble
    const ensembleNodes = program.statements.filter(n => isEnsembleNode(n));
    if (ensembleNodes.length > 0) {
      stages.push({
        stageId: 'stage_ensemble',
        nodeIds: ensembleNodes.map((n, i) => n.id || stageCounter + i),
        dependencies: ['stage_paths_parallel', 'stage_weights'],
        isParallelizable: false,
        estimatedCost: ensembleNodes.length * 150,
      });
    }

    // Stage 5: Critique
    const critiqueNodes = program.statements.filter(n => isCritiqueNode(n));
    if (critiqueNodes.length > 0) {
      stages.push({
        stageId: 'stage_critique',
        nodeIds: critiqueNodes.map((n, i) => n.id || stageCounter + i),
        dependencies: ['stage_ensemble'],
        isParallelizable: false,
        estimatedCost: critiqueNodes.length * 120,
      });
    }

    // Stage 6: Sampling and Detokenization
    const finalNodes = program.statements.filter(n => isSampleNode(n) || isDetokenizeNode(n));
    if (finalNodes.length > 0) {
      stages.push({
        stageId: 'stage_sampling',
        nodeIds: finalNodes.map((n, i) => n.id || stageCounter + i),
        dependencies: ['stage_critique'],
        isParallelizable: true,
        estimatedCost: finalNodes.length * 80,
      });
    }

    return {
      stages,
      parallelGroups,
      dataflow: this.dataflow,
    };
  }

  /**
   * Extract tensor dimensions from variable map
   */
  private extractTensorDimensions(): { [key: string]: Shape } {
    const result: { [key: string]: Shape } = {};
    for (const [varName, varInfo] of Object.entries(this.variableMap)) {
      result[varName] = varInfo.shape;
    }
    return result;
  }

  /**
   * Compile a query node to a vector representation
   */
  private compileQueryNode(node: QueryNode): {
    tensor: Tensor;
    shape: Shape;
  } {
    const embedding = node.embedding || this.encoder.embed(node.semanticContent || '');
    return {
      tensor: embedding,
      shape: {
        dimensions: [embedding.length],
        totalElements: embedding.length,
      },
    };
  }

  /**
   * Compile an encode node
   */
  private compileEncodeNode(node: EncodeNode): {
    encoder: QueryEncoder;
    outputShape: Shape;
  } {
    const outputDim = node.latentDim || this.latentDim;
    return {
      encoder: this.encoder,
      outputShape: {
        dimensions: [outputDim],
        totalElements: outputDim,
      },
    };
  }

  /**
   * Compile path nodes
   */
  private compilePathNodes(
    analytical: PathNode,
    creative: PathNode,
    empirical: PathNode,
  ): { P_a: Matrix; P_b: Matrix; P_c: Matrix } {
    return {
      P_a: PathMatrixGenerator.generateAnalyticalPath(this.queryDim, this.pathDim).matrix,
      P_b: PathMatrixGenerator.generateCreativePath(this.queryDim, this.pathDim).matrix,
      P_c: PathMatrixGenerator.generateEmpiricalPath(this.queryDim, this.pathDim).matrix,
    };
  }
}

// ============================================================================
// Export helper functions
// ============================================================================

export function parseAndCompile(
  mindlangCode: string,
  parser: (code: string) => Program,
): PostMindLangBytecode {
  const program = parser(mindlangCode);
  const compiler = new MindLangToPostMindLangCompiler();
  return compiler.compile(program);
}

export function getCompilerConfig() {
  return {
    defaultQueryDim: 768,
    defaultLatentDim: 512,
    defaultPathDim: 256,
    defaultWeightDim: 3,
  };
}
