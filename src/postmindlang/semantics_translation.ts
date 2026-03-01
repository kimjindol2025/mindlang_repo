/**
 * Semantics Translation: MindLang Concepts → PostMindLang Vector Spaces
 *
 * This module translates high-level MindLang semantic concepts into
 * mathematical objects in vector spaces, preserving meaning through subspace representation.
 */

import {
  Vector,
  Matrix,
  Tensor,
  Scalar,
  Subspace,
  Constraint,
  Shape,
  PathProperties,
} from './mindlang_to_postmindlang';

// ============================================================================
// Semantic Properties
// ============================================================================

export interface SemanticProperties {
  determinism: number; // 0: non-deterministic, 1: fully deterministic
  confidence: number; // 0-1: epistemic certainty
  diversity: number; // 0: monolithic, 1: highly diverse
  complexity: number; // 0: simple, 1: complex
  grounding: number; // 0: abstract, 1: empirically grounded
}

export interface ConceptMapping {
  concept: string;
  representation: 'subspace' | 'matrix' | 'tensor' | 'function';
  dimension: number;
  constraints: Constraint[];
  properties: SemanticProperties;
}

// ============================================================================
// Subspace Definitions for MindLang Concepts
// ============================================================================

/**
 * Analytical reasoning path: subspace of high-linearity transformations
 *
 * Characteristics:
 * - Linear transformations preserve vector structure
 * - Orthogonal basis vectors represent logical inference chains
 * - Deterministic: same input always produces same output
 * - High confidence due to formal logical structure
 */
export class AnalyticalPathTranslation {
  static translate(
    inputDim: number,
    outputDim: number,
  ): Subspace {
    // Create orthonormal basis for analytical subspace
    const basis = this.createOrthonormalBasis(inputDim, outputDim);

    return {
      basis,
      dimension: outputDim,
      constraints: [
        {
          type: 'orthogonal',
          params: [1.0], // Unit vectors
        },
        {
          type: 'norm',
          params: [1.0], // Each vector has norm 1
        },
      ],
    };
  }

  /**
   * Analytical path semantic mapping
   * Maps MindLang analytical reasoning concepts to vector space
   */
  static getSemantics(): SemanticProperties {
    return {
      determinism: 0.95,      // Highly deterministic
      confidence: 0.90,       // High epistemic confidence
      diversity: 0.05,        // Low diversity (single logical path)
      complexity: 0.40,       // Medium complexity
      grounding: 0.20,        // Abstract (not empirically grounded)
    };
  }

  /**
   * Create orthonormal basis using Gram-Schmidt
   */
  private static createOrthonormalBasis(
    inputDim: number,
    outputDim: number,
  ): Matrix {
    const basis: Matrix = [];
    const n = Math.min(inputDim, outputDim);

    // Generate initial vectors
    const vectors: Vector[] = [];
    for (let i = 0; i < n; i++) {
      const v = new Array(inputDim).fill(0);
      v[i % inputDim] = 1;
      vectors.push(v);
    }

    // Apply Gram-Schmidt orthogonalization
    for (let i = 0; i < vectors.length; i++) {
      let v = vectors[i];

      // Subtract projections onto previous vectors
      for (let j = 0; j < i; j++) {
        const dot = this.dotProduct(v, basis[j]);
        for (let k = 0; k < v.length; k++) {
          v[k] -= dot * basis[j][k];
        }
      }

      // Normalize
      const norm = Math.sqrt(this.dotProduct(v, v));
      if (norm > 1e-10) {
        v = v.map(x => x / norm);
        basis.push(v);
      }
    }

    return basis;
  }

  private static dotProduct(u: Vector, v: Vector): number {
    let sum = 0;
    for (let i = 0; i < u.length; i++) {
      sum += u[i] * v[i];
    }
    return sum;
  }
}

// ============================================================================
// Creative Path Semantics
// ============================================================================

/**
 * Creative reasoning path: subspace of high-diversity transformations
 *
 * Characteristics:
 * - Non-linear transformations enable novel combinations
 * - Many possible output vectors for same input
 * - Stochastic: includes randomness and exploration
 * - Moderate confidence due to exploration of uncertain space
 */
export class CreativePathTranslation {
  static translate(
    inputDim: number,
    outputDim: number,
  ): Subspace {
    // Create random basis with non-linear structure
    const basis = this.createNonlinearBasis(inputDim, outputDim);

    return {
      basis,
      dimension: outputDim,
      constraints: [
        {
          type: 'range',
          params: [-1, 1], // Bounded outputs
        },
      ],
    };
  }

  /**
   * Creative path semantic mapping
   */
  static getSemantics(): SemanticProperties {
    return {
      determinism: 0.25,      // Low determinism (exploratory)
      confidence: 0.50,       // Moderate confidence
      diversity: 0.85,        // High diversity
      complexity: 0.75,       // Higher complexity
      grounding: 0.30,        // Somewhat abstract
    };
  }

  /**
   * Create basis with non-linear structure
   */
  private static createNonlinearBasis(
    inputDim: number,
    outputDim: number,
  ): Matrix {
    const basis: Matrix = [];

    for (let i = 0; i < outputDim; i++) {
      const vector: Vector = [];
      for (let j = 0; j < inputDim; j++) {
        // Create non-linear activation patterns
        const angle = (i + j) * Math.PI / (outputDim + inputDim);
        const value = Math.sin(angle) * Math.cos(angle * (i + 1));
        vector.push(value);
      }
      basis.push(vector);
    }

    return basis;
  }
}

// ============================================================================
// Empirical Path Semantics
// ============================================================================

/**
 * Empirical reasoning path: subspace grounded in observed data
 *
 * Characteristics:
 * - Learned from actual data patterns
 * - Medium linearity (captures both linear and non-linear patterns)
 * - Deterministic given training data
 * - High confidence in data-consistent regions
 */
export class EmpiricalPathTranslation {
  static translate(
    inputDim: number,
    outputDim: number,
    trainingData?: Vector[],
  ): Subspace {
    const basis = this.extractBasisFromData(inputDim, outputDim, trainingData);

    return {
      basis,
      dimension: outputDim,
      constraints: [
        {
          type: 'range',
          params: [-2, 2], // Empirical range
        },
        {
          type: 'norm',
          params: [1.0, 2.0], // Bounded norm
        },
      ],
    };
  }

  /**
   * Empirical path semantic mapping
   */
  static getSemantics(): SemanticProperties {
    return {
      determinism: 0.75,      // Mostly deterministic
      confidence: 0.80,       // High confidence in known regions
      diversity: 0.50,        // Medium diversity
      complexity: 0.60,       // Moderate complexity
      grounding: 0.95,        // Highly empirically grounded
    };
  }

  /**
   * Extract basis from training data using PCA-like approach
   */
  private static extractBasisFromData(
    inputDim: number,
    outputDim: number,
    trainingData?: Vector[],
  ): Matrix {
    if (!trainingData || trainingData.length === 0) {
      return this.createDefaultBasis(inputDim, outputDim);
    }

    // Simplified PCA: compute covariance and eigenvalues
    const basis: Matrix = [];

    // Use top data vectors as basis (simple approximation)
    for (let i = 0; i < Math.min(outputDim, trainingData.length); i++) {
      const dataVec = trainingData[i];
      // Project to input dimension if needed
      const basisVec = new Array(inputDim).fill(0);
      for (let j = 0; j < Math.min(inputDim, dataVec.length); j++) {
        basisVec[j] = dataVec[j];
      }
      basis.push(basisVec);
    }

    // Fill remaining with orthogonal vectors
    while (basis.length < outputDim) {
      const v = new Array(inputDim).fill(0);
      v[basis.length % inputDim] = 1;
      basis.push(v);
    }

    return basis;
  }

  private static createDefaultBasis(
    inputDim: number,
    outputDim: number,
  ): Matrix {
    const basis: Matrix = [];
    for (let i = 0; i < outputDim; i++) {
      const v = new Array(inputDim).fill(0);
      v[i % inputDim] = 1;
      basis.push(v);
    }
    return basis;
  }
}

// ============================================================================
// Weight Adaptation Semantics
// ============================================================================

/**
 * Adaptive weights: Dynamic distribution over reasoning paths
 * Represented as a probability simplex in ℝ³
 *
 * Semantics:
 * - w_a, w_b, w_c ∈ [0, 1]
 * - w_a + w_b + w_c = 1 (probability constraint)
 * - Adaptation: f(query) → weights based on query characteristics
 */
export class AdaptiveWeightSemantics {
  static translate(): Subspace {
    return {
      basis: [
        [1, 0, 0], // Pure analytical
        [0, 1, 0], // Pure creative
        [0, 0, 1], // Pure empirical
      ],
      dimension: 3,
      constraints: [
        {
          type: 'probabilistic',
          params: [0, 1, 1], // Probability simplex constraint
        },
        {
          type: 'norm',
          params: [1.0], // L1 norm = 1
        },
      ],
    };
  }

  /**
   * Semantic meaning: weight vector represents query characteristics
   */
  static interpretWeights(
    weights: [number, number, number],
    query: Vector,
  ): {
    analyticalityScore: number;
    creativityScore: number;
    empiricalityScore: number;
  } {
    return {
      analyticalityScore: weights[0],
      creativityScore: weights[1],
      empiricalityScore: weights[2],
    };
  }

  /**
   * Adaptation function semantics
   * Encodes how query characteristics should adjust weights
   */
  static getAdaptationSemantics(): {
    deterministic_queries_favor: 'analytical' | 'empirical';
    exploratory_queries_favor: 'creative';
    specific_queries_favor: 'empirical';
    abstract_queries_favor: 'analytical';
  } {
    return {
      deterministic_queries_favor: 'analytical',
      exploratory_queries_favor: 'creative',
      specific_queries_favor: 'empirical',
      abstract_queries_favor: 'analytical',
    };
  }
}

// ============================================================================
// Ensemble Semantics
// ============================================================================

/**
 * Ensemble combination: Convex combination of path outputs
 * y = w_a * p_a + w_b * p_b + w_c * p_c
 *
 * Semantics:
 * - Represents balanced synthesis of different reasoning approaches
 * - Convexity ensures output stays within reasonable bounds
 * - Weights determine influence of each path
 */
export class EnsembleSemantics {
  static translate(): Subspace {
    // Ensemble operates in the same space as paths
    // But with additional constraint: convex combination
    return {
      basis: [], // Inherited from paths
      dimension: 256, // Path dimension
      constraints: [
        {
          type: 'norm',
          params: [1.0], // Convex combination constraint
        },
      ],
    };
  }

  /**
   * Ensemble voting rule semantics
   */
  static getVotingRuleSemantics(): {
    softmax: string;
    majority: string;
    borda: string;
  } {
    return {
      softmax: 'Soft voting with temperature control for exploration vs exploitation',
      majority: 'Hard voting - outputs majority path outcome',
      borda: 'Ranked voting - aggregates preference ordering across paths',
    };
  }

  /**
   * Semantic interpretation of ensemble output
   */
  static interpretEnsembleOutput(
    output: Vector,
    weights: Vector,
    paths: { analytical: Vector; creative: Vector; empirical: Vector },
  ): {
    dominantPath: 'analytical' | 'creative' | 'empirical';
    consensus: number; // 0: high disagreement, 1: full consensus
    confidence: number; // 0-1
  } {
    const maxWeight = Math.max(...weights);
    let dominantPath: 'analytical' | 'creative' | 'empirical' = 'analytical';
    if (maxWeight === weights[1]) dominantPath = 'creative';
    if (maxWeight === weights[2]) dominantPath = 'empirical';

    // Compute consensus as negative entropy
    const entropy = -weights.reduce((sum, w) => sum + (w > 0 ? w * Math.log(w) : 0), 0);
    const maxEntropy = Math.log(3);
    const consensus = 1 - entropy / maxEntropy;

    // Confidence based on alignment
    const alignment = this.computeAlignment(output, paths);

    return {
      dominantPath,
      consensus: Math.max(0, Math.min(1, consensus)),
      confidence: alignment,
    };
  }

  private static computeAlignment(output: Vector, paths: any): number {
    let alignment = 0;
    let count = 0;

    for (const pathName of ['analytical', 'creative', 'empirical']) {
      const path = (paths as any)[pathName];
      const dot = this.dotProduct(output, path);
      alignment += dot;
      count++;
    }

    return Math.max(0, Math.min(1, alignment / count + 0.5));
  }

  private static dotProduct(u: Vector, v: Vector): number {
    let sum = 0;
    for (let i = 0; i < u.length; i++) {
      sum += u[i] * (v[i] || 0);
    }
    return sum;
  }
}

// ============================================================================
// Critique Semantics (Self-Critique)
// ============================================================================

/**
 * Self-critique: Loss-based feedback mechanism
 * δ = ∇L(y, ŷ) - gradient indicates improvement direction
 *
 * Semantics:
 * - Loss measures deviation from ideal output
 * - Gradient shows direction to improve
 * - Confidence = 1 / (1 + loss) - higher loss = lower confidence
 */
export class CritiqueSemantics {
  static translate(): Subspace {
    return {
      basis: [],
      dimension: 256, // Operates in path space
      constraints: [
        {
          type: 'range',
          params: [0, 1], // Loss in [0, 1]
        },
      ],
    };
  }

  /**
   * Interpret critique output
   */
  static interpretCritique(
    loss: number,
    threshold: number,
  ): {
    acceptanceDecision: boolean;
    confidence: number;
    improvementPotential: number;
  } {
    const confidence = 1 / (1 + loss);
    const acceptanceDecision = loss < threshold;
    const improvementPotential = Math.max(0, 1 - confidence);

    return {
      acceptanceDecision,
      confidence,
      improvementPotential,
    };
  }

  /**
   * Semantic meaning of loss components
   */
  static getLossComponentMeaning(): {
    l2_distance: string;
    kl_divergence: string;
    entropy: string;
  } {
    return {
      l2_distance: 'Euclidean distance to reference output',
      kl_divergence: 'Distributional divergence from reference',
      entropy: 'Uncertainty in output distribution',
    };
  }
}

// ============================================================================
// Sampling Semantics
// ============================================================================

/**
 * Sampling: Probabilistic selection from output distribution
 * Controlled by temperature parameter
 *
 * Semantics:
 * - Low temperature: Exploitation (deterministic)
 * - High temperature: Exploration (uniform)
 * - Threshold: Minimum probability to consider
 */
export class SamplingSemantics {
  static translate(): Subspace {
    return {
      basis: [],
      dimension: 256,
      constraints: [
        {
          type: 'probabilistic',
          params: [0, 1, 1], // Valid probability distribution
        },
      ],
    };
  }

  /**
   * Temperature semantics
   */
  static getTemperatureSemantics(): {
    low: string;
    medium: string;
    high: string;
  } {
    return {
      low: 'Temperature < 1: Sharp distribution, exploit best outputs',
      medium: 'Temperature ≈ 1: Balanced exploration/exploitation',
      high: 'Temperature > 1: Flat distribution, explore alternatives',
    };
  }

  /**
   * Threshold semantics
   */
  static getThresholdSemantics(): string {
    return 'Probability threshold for candidate selection - higher threshold = fewer candidates';
  }
}

// ============================================================================
// Type System Translation
// ============================================================================

export class TypeTranslation {
  /**
   * Map MindLang types to PostMindLang subspaces
   */
  static translateTypes(): ConceptMapping[] {
    return [
      {
        concept: 'Query',
        representation: 'tensor',
        dimension: 768,
        constraints: [
          { type: 'norm', params: [1.0] }, // L2 normalized
        ],
        properties: {
          determinism: 1.0,
          confidence: 0.95,
          diversity: 0.1,
          complexity: 0.3,
          grounding: 0.9,
        },
      },
      {
        concept: 'Latent',
        representation: 'tensor',
        dimension: 512,
        constraints: [
          { type: 'range', params: [-1, 1] },
        ],
        properties: {
          determinism: 0.8,
          confidence: 0.85,
          diversity: 0.4,
          complexity: 0.5,
          grounding: 0.7,
        },
      },
      {
        concept: 'Path',
        representation: 'tensor',
        dimension: 256,
        constraints: [
          { type: 'range', params: [-2, 2] },
        ],
        properties: {
          determinism: 0.65,
          confidence: 0.7,
          diversity: 0.6,
          complexity: 0.7,
          grounding: 0.6,
        },
      },
      {
        concept: 'Weight',
        representation: 'tensor',
        dimension: 3,
        constraints: [
          { type: 'probabilistic', params: [0, 1, 1] },
          { type: 'norm', params: [1.0] },
        ],
        properties: {
          determinism: 0.7,
          confidence: 0.8,
          diversity: 0.3,
          complexity: 0.2,
          grounding: 0.5,
        },
      },
      {
        concept: 'Ensemble',
        representation: 'tensor',
        dimension: 256,
        constraints: [
          { type: 'norm', params: [1.0] },
        ],
        properties: {
          determinism: 0.7,
          confidence: 0.75,
          diversity: 0.5,
          complexity: 0.6,
          grounding: 0.65,
        },
      },
    ];
  }

  /**
   * Type checking: Verify value belongs to subspace
   */
  static typeCheck(
    value: Vector,
    expectedType: ConceptMapping,
    tolerance: number = 1e-5,
  ): boolean {
    if (value.length !== expectedType.dimension) {
      return false;
    }

    // Check constraints
    for (const constraint of expectedType.constraints) {
      if (!this.checkConstraint(value, constraint)) {
        return false;
      }
    }

    return true;
  }

  private static checkConstraint(value: Vector, constraint: Constraint): boolean {
    switch (constraint.type) {
      case 'norm': {
        const norm = Math.sqrt(value.reduce((sum, x) => sum + x * x, 0));
        const expectedNorm = constraint.params[0];
        return Math.abs(norm - expectedNorm) < 1e-4;
      }

      case 'range': {
        const [min, max] = constraint.params;
        return value.every(x => x >= min && x <= max);
      }

      case 'probabilistic': {
        const sum = value.reduce((a, b) => a + b, 0);
        return Math.abs(sum - 1.0) < 1e-4 && value.every(x => x >= 0);
      }

      default:
        return true;
    }
  }
}

// ============================================================================
// Semantic Preservation Verification
// ============================================================================

export interface SemanticPreservationReport {
  isPreserved: boolean;
  properties: {
    originalSemantics: SemanticProperties;
    compiledSemantics: SemanticProperties;
    differences: Partial<SemanticProperties>;
  };
  pathProperties: {
    analytical: PathProperties;
    creative: PathProperties;
    empirical: PathProperties;
  };
}

export class SemanticPreservationChecker {
  static verify(
    originalProgram: any,
    compiledBytecode: any,
  ): SemanticPreservationReport {
    // 원본 프로그램 의미론 분석
    const originalSemantics = this.analyzeProgram(originalProgram);

    // 컴파일된 바이트코드 의미론 추출
    const compiledSemantics = this.analyzeBytecode(compiledBytecode);

    // 경로 속성 추출 (컴파일된 바이트코드에서)
    const pathProperties = this.extractPathProperties(compiledBytecode);

    // 의미 보존 여부 판단: 각 속성 차이가 임계값 이내인지 확인
    const threshold = 0.15;
    const differences: Partial<SemanticProperties> = {};
    let isPreserved = true;

    const keys: (keyof SemanticProperties)[] = [
      'determinism', 'confidence', 'diversity', 'complexity', 'grounding',
    ];
    for (const key of keys) {
      const diff = Math.abs(originalSemantics[key] - compiledSemantics[key]);
      if (diff > threshold) {
        differences[key] = diff;
        isPreserved = false;
      }
    }

    return {
      isPreserved,
      properties: {
        originalSemantics,
        compiledSemantics,
        differences,
      },
      pathProperties,
    };
  }

  /**
   * 원본 AST 프로그램에서 의미론적 속성 분석
   */
  private static analyzeProgram(program: any): SemanticProperties {
    const statements: any[] = program?.statements ?? [];

    // 어떤 경로 타입이 있는지 확인
    let hasAnalytical = false;
    let hasCreative = false;
    let hasEmpirical = false;
    let hasCritique = false;
    let hasEnsemble = false;

    for (const stmt of statements) {
      if (stmt.type === 'Path' || stmt.pathType !== undefined) {
        const pathType = stmt.pathType ?? stmt.path;
        if (pathType === 'analytical') hasAnalytical = true;
        if (pathType === 'creative') hasCreative = true;
        if (pathType === 'empirical') hasEmpirical = true;
      }
      if (stmt.type === 'Critique' || stmt.nodeType === 'CritiqueNode') hasCritique = true;
      if (stmt.type === 'Ensemble' || stmt.nodeType === 'EnsembleNode') hasEnsemble = true;
    }

    // 경로 타입에 따라 의미론적 속성 계산
    const pathCount = [hasAnalytical, hasCreative, hasEmpirical].filter(Boolean).length;
    const effectivePaths = pathCount > 0 ? pathCount : 1;

    const deterministicScore = (hasAnalytical ? 0.95 : 0) + (hasCreative ? 0.25 : 0) + (hasEmpirical ? 0.75 : 0);
    const confidenceScore = (hasAnalytical ? 0.90 : 0) + (hasCreative ? 0.50 : 0) + (hasEmpirical ? 0.80 : 0);
    const diversityScore = (hasAnalytical ? 0.05 : 0) + (hasCreative ? 0.85 : 0) + (hasEmpirical ? 0.50 : 0);

    return {
      determinism: deterministicScore / effectivePaths,
      confidence: confidenceScore / effectivePaths,
      diversity: diversityScore / effectivePaths,
      complexity: hasCritique && hasEnsemble ? 0.6 : 0.4,
      grounding: hasEmpirical ? 0.75 : 0.45,
    };
  }

  /**
   * 컴파일된 바이트코드에서 의미론적 속성 추출
   */
  private static analyzeBytecode(bytecode: any): SemanticProperties {
    if (!bytecode) {
      return { determinism: 0.7, confidence: 0.75, diversity: 0.5, complexity: 0.6, grounding: 0.65 };
    }

    const pathMatrices = bytecode.pathMatrices ?? {};
    const analytical: PathProperties = pathMatrices.analytical?.properties ?? { linearity: 0.95, diversity: 0.05, confidence: 0.90 };
    const creative: PathProperties = pathMatrices.creative?.properties ?? { linearity: 0.45, diversity: 0.85, confidence: 0.60 };
    const empirical: PathProperties = pathMatrices.empirical?.properties ?? { linearity: 0.70, diversity: 0.50, confidence: 0.75 };

    const pathCount = Object.keys(pathMatrices).length || 3;

    return {
      determinism: (analytical.linearity + (1 - creative.diversity) + empirical.linearity) / pathCount,
      confidence: (analytical.confidence + creative.confidence + empirical.confidence) / pathCount,
      diversity: (analytical.diversity + creative.diversity + empirical.diversity) / pathCount,
      complexity: bytecode.critiqueFunction && bytecode.ensembleFunction ? 0.6 : 0.4,
      grounding: empirical.linearity * 0.8 + 0.1,
    };
  }

  /**
   * 바이트코드에서 경로 속성 추출
   */
  private static extractPathProperties(bytecode: any): {
    analytical: PathProperties;
    creative: PathProperties;
    empirical: PathProperties;
  } {
    const pathMatrices = bytecode?.pathMatrices ?? {};

    return {
      analytical: pathMatrices.analytical?.properties ?? {
        linearity: 0.95,
        diversity: 0.05,
        confidence: 0.90,
      },
      creative: pathMatrices.creative?.properties ?? {
        linearity: 0.45,
        diversity: 0.85,
        confidence: 0.60,
      },
      empirical: pathMatrices.empirical?.properties ?? {
        linearity: 0.70,
        diversity: 0.50,
        confidence: 0.75,
      },
    };
  }
}
