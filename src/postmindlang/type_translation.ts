/**
 * Type Translation: MindLang Types → PostMindLang Subspaces
 *
 * Maps MindLang's type system to mathematical subspaces in PostMindLang,
 * enabling type checking and semantic verification in vector spaces.
 */

import {
  Vector,
  Matrix,
  Subspace,
  Constraint,
  Shape,
} from './mindlang_to_postmindlang';

// ============================================================================
// PostMindLang Type System
// ============================================================================

export enum PostMindLangType {
  QUERY = 'Query',
  LATENT = 'Latent',
  PATH = 'Path',
  WEIGHT = 'Weight',
  ENSEMBLE = 'Ensemble',
  SCALAR = 'Scalar',
}

export interface TypeDefinition {
  name: PostMindLangType;
  dimension: number;
  subspace: Subspace;
  constraints: Constraint[];
  semanticMeaning: string;
  operations: string[]; // Valid operations on this type
  typeCheck(value: Vector): boolean;
  project(value: Vector): Vector;
}

export interface TypeEnvironment {
  types: Map<PostMindLangType, TypeDefinition>;
  variables: Map<string, PostMindLangType>;
  functions: Map<string, TypeSignature>;
}

export interface TypeSignature {
  name: string;
  inputTypes: PostMindLangType[];
  outputType: PostMindLangType;
  constraints: Constraint[];
}

// ============================================================================
// Query Type (Input)
// ============================================================================

/**
 * Query Type: ℝ^768
 * Represents input queries/prompts
 *
 * Properties:
 * - L2 normalized (norm = 1)
 * - Dense embedding representation
 * - Deterministic encoding of semantic content
 */
export class QueryType implements TypeDefinition {
  name = PostMindLangType.QUERY;
  dimension = 768;
  semanticMeaning = 'Normalized embedding of input query';
  operations = ['project', 'normalize', 'encode', 'distance'];

  subspace: Subspace = {
    basis: this.generateQueryBasis(),
    dimension: 768,
    constraints: [
      {
        type: 'norm',
        params: [1.0], // L2 unit norm
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'norm',
      params: [1.0],
    },
  ];

  private generateQueryBasis(): Matrix {
    // Query space basis: orthonormal vectors
    const basis: Matrix = [];
    for (let i = 0; i < 768; i++) {
      const vec = new Array(768).fill(0);
      vec[i % 768] = 1;
      basis.push(vec);
    }
    return basis;
  }

  /**
   * Project value onto query subspace
   */
  project(value: Vector): Vector {
    if (value.length !== 768) {
      throw new Error(`Query must be 768-dimensional, got ${value.length}`);
    }

    // Normalize to unit norm
    const norm = Math.sqrt(value.reduce((sum, x) => sum + x * x, 0));
    if (norm === 0) {
      return new Array(768).fill(1 / Math.sqrt(768));
    }

    return value.map(x => x / norm);
  }

  /**
   * Type check: verify value is valid query
   */
  typeCheck(value: Vector): boolean {
    if (value.length !== 768) return false;

    const norm = Math.sqrt(value.reduce((sum, x) => sum + x * x, 0));
    return Math.abs(norm - 1.0) < 1e-4;
  }
}

// ============================================================================
// Latent Type (Encoding Output)
// ============================================================================

/**
 * Latent Type: ℝ^512
 * Represents encoded latent representations
 *
 * Properties:
 * - Bounded range [-1, 1]
 * - Compressed representation of query
 * - Can be non-normalized
 */
export class LatentType implements TypeDefinition {
  name = PostMindLangType.LATENT;
  dimension = 512;
  semanticMeaning = 'Compressed latent encoding of query';
  operations = ['project', 'scale', 'combine', 'encode_to_path'];

  subspace: Subspace = {
    basis: this.generateLatentBasis(),
    dimension: 512,
    constraints: [
      {
        type: 'range',
        params: [-1, 1], // Bounded range
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'range',
      params: [-1, 1],
    },
  ];

  private generateLatentBasis(): Matrix {
    // Latent space basis: random but bounded
    const basis: Matrix = [];
    for (let i = 0; i < 512; i++) {
      const vec: Vector = [];
      for (let j = 0; j < 512; j++) {
        vec.push((Math.random() - 0.5) * 2); // [-1, 1]
      }
      basis.push(vec);
    }
    return basis;
  }

  /**
   * Project value onto latent subspace
   */
  project(value: Vector): Vector {
    if (value.length !== 512) {
      throw new Error(`Latent must be 512-dimensional, got ${value.length}`);
    }

    // Clip to [-1, 1]
    return value.map(x => Math.max(-1, Math.min(1, x)));
  }

  typeCheck(value: Vector): boolean {
    if (value.length !== 512) return false;
    return value.every(x => x >= -1 && x <= 1);
  }
}

// ============================================================================
// Path Type (Reasoning Outputs)
// ============================================================================

/**
 * Path Type: ℝ^256
 * Represents outputs from analytical/creative/empirical paths
 *
 * Properties:
 * - Medium-dimensional representation
 * - Bounded range [-2, 2]
 * - Represents reasoning outcomes
 */
export class PathType implements TypeDefinition {
  name = PostMindLangType.PATH;
  dimension = 256;
  semanticMeaning = 'Output from a reasoning path (analytical/creative/empirical)';
  operations = ['combine', 'ensemble', 'critique', 'distance'];

  subspace: Subspace = {
    basis: this.generatePathBasis(),
    dimension: 256,
    constraints: [
      {
        type: 'range',
        params: [-2, 2], // Slightly wider than latent
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'range',
      params: [-2, 2],
    },
  ];

  private generatePathBasis(): Matrix {
    // Path space basis
    const basis: Matrix = [];
    for (let i = 0; i < 256; i++) {
      const vec: Vector = [];
      for (let j = 0; j < 256; j++) {
        vec.push((Math.random() - 0.5) * 4); // [-2, 2]
      }
      basis.push(vec);
    }
    return basis;
  }

  /**
   * Project value onto path subspace
   */
  project(value: Vector): Vector {
    if (value.length !== 256) {
      throw new Error(`Path must be 256-dimensional, got ${value.length}`);
    }

    return value.map(x => Math.max(-2, Math.min(2, x)));
  }

  typeCheck(value: Vector): boolean {
    if (value.length !== 256) return false;
    return value.every(x => x >= -2 && x <= 2);
  }
}

// ============================================================================
// Weight Type (Adaptive Weights)
// ============================================================================

/**
 * Weight Type: Δ^2 (2-simplex)
 * Probability distribution over 3 paths
 *
 * Properties:
 * - 3-dimensional vector
 * - Sum to 1 (probability constraint)
 * - Each component in [0, 1]
 * - Represents mixing weights for paths
 */
export class WeightType implements TypeDefinition {
  name = PostMindLangType.WEIGHT;
  dimension = 3;
  semanticMeaning = 'Mixing weights for analytical/creative/empirical paths (probability simplex)';
  operations = ['softmax', 'scale', 'adapt', 'normalize'];

  subspace: Subspace = {
    basis: [
      [1, 0, 0],
      [0, 1, 0],
      [0, 0, 1],
    ],
    dimension: 3,
    constraints: [
      {
        type: 'probabilistic',
        params: [0, 1, 1], // Probability simplex
      },
      {
        type: 'norm',
        params: [1.0], // L1 norm = 1
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'probabilistic',
      params: [0, 1, 1],
    },
    {
      type: 'norm',
      params: [1.0],
    },
  ];

  /**
   * Project value onto probability simplex
   */
  project(value: Vector): Vector {
    if (value.length !== 3) {
      throw new Error(`Weight must be 3-dimensional, got ${value.length}`);
    }

    // Project to probability simplex
    let projected = [...value];

    // Clip to [0, 1]
    projected = projected.map(x => Math.max(0, Math.min(1, x)));

    // Normalize to sum to 1
    const sum = projected.reduce((a, b) => a + b, 0);
    if (sum === 0) {
      projected = [1 / 3, 1 / 3, 1 / 3];
    } else {
      projected = projected.map(x => x / sum);
    }

    return projected;
  }

  typeCheck(value: Vector): boolean {
    if (value.length !== 3) return false;

    // Check sum to 1
    const sum = value.reduce((a, b) => a + b, 0);
    if (Math.abs(sum - 1.0) > 1e-4) return false;

    // Check in [0, 1]
    return value.every(x => x >= 0 && x <= 1);
  }
}

// ============================================================================
// Ensemble Type (Weighted Combination)
// ============================================================================

/**
 * Ensemble Type: ℝ^256
 * Output of weighted combination of paths
 *
 * Properties:
 * - Same dimension as paths
 * - Bounded by path bounds due to convex combination
 */
export class EnsembleType implements TypeDefinition {
  name = PostMindLangType.ENSEMBLE;
  dimension = 256;
  semanticMeaning = 'Weighted combination of path outputs';
  operations = ['critique', 'sample', 'combine', 'distance'];

  subspace: Subspace = {
    basis: this.generateEnsembleBasis(),
    dimension: 256,
    constraints: [
      {
        type: 'norm',
        params: [1.0], // Convex combination constraint
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'norm',
      params: [1.0],
    },
  ];

  private generateEnsembleBasis(): Matrix {
    const basis: Matrix = [];
    for (let i = 0; i < 256; i++) {
      const vec: Vector = [];
      for (let j = 0; j < 256; j++) {
        vec.push(i === j ? 1 : 0); // Identity basis
      }
      basis.push(vec);
    }
    return basis;
  }

  /**
   * Project value onto ensemble subspace
   */
  project(value: Vector): Vector {
    if (value.length !== 256) {
      throw new Error(`Ensemble must be 256-dimensional, got ${value.length}`);
    }

    // Normalize
    const norm = Math.sqrt(value.reduce((sum, x) => sum + x * x, 0));
    if (norm === 0) {
      return value;
    }

    return value.map(x => x / norm);
  }

  typeCheck(value: Vector): boolean {
    if (value.length !== 256) return false;

    const norm = Math.sqrt(value.reduce((sum, x) => sum + x * x, 0));
    return Math.abs(norm - 1.0) < 1e-4;
  }
}

// ============================================================================
// Scalar Type (Loss/Confidence)
// ============================================================================

/**
 * Scalar Type: ℝ
 * Scalar values like loss or confidence
 */
export class ScalarType implements TypeDefinition {
  name = PostMindLangType.SCALAR;
  dimension = 1;
  semanticMeaning = 'Scalar value (loss, confidence, etc.)';
  operations = ['compare', 'arithmetic'];

  subspace: Subspace = {
    basis: [[1]],
    dimension: 1,
    constraints: [
      {
        type: 'range',
        params: [0, 1], // Typical [0, 1] for confidence/loss
      },
    ],
  };

  constraints: Constraint[] = [
    {
      type: 'range',
      params: [0, 1],
    },
  ];

  /**
   * Project value onto scalar subspace
   */
  project(value: Vector): Vector {
    if (value.length !== 1) {
      throw new Error('Scalar must be 1-dimensional');
    }

    return [Math.max(0, Math.min(1, value[0]))];
  }

  typeCheck(value: Vector): boolean {
    return value.length === 1 && value[0] >= 0 && value[0] <= 1;
  }
}

// ============================================================================
// Type System Manager
// ============================================================================

export class TypeSystem {
  private environment: TypeEnvironment;

  constructor() {
    this.environment = {
      types: new Map(),
      variables: new Map(),
      functions: new Map(),
    };

    this.initializeTypes();
    this.initializeFunctions();
  }

  /**
   * Initialize all built-in types
   */
  private initializeTypes(): void {
    const types: TypeDefinition[] = [
      new QueryType(),
      new LatentType(),
      new PathType(),
      new WeightType(),
      new EnsembleType(),
      new ScalarType(),
    ];

    for (const type of types) {
      this.environment.types.set(type.name, type);
    }
  }

  /**
   * Initialize all built-in functions with type signatures
   */
  private initializeFunctions(): void {
    const functions: TypeSignature[] = [
      {
        name: 'encode',
        inputTypes: [PostMindLangType.QUERY],
        outputType: PostMindLangType.LATENT,
        constraints: [],
      },
      {
        name: 'project_analytical',
        inputTypes: [PostMindLangType.LATENT],
        outputType: PostMindLangType.PATH,
        constraints: [],
      },
      {
        name: 'project_creative',
        inputTypes: [PostMindLangType.LATENT],
        outputType: PostMindLangType.PATH,
        constraints: [],
      },
      {
        name: 'project_empirical',
        inputTypes: [PostMindLangType.LATENT],
        outputType: PostMindLangType.PATH,
        constraints: [],
      },
      {
        name: 'compute_weights',
        inputTypes: [PostMindLangType.QUERY],
        outputType: PostMindLangType.WEIGHT,
        constraints: [],
      },
      {
        name: 'ensemble',
        inputTypes: [
          PostMindLangType.PATH,
          PostMindLangType.PATH,
          PostMindLangType.PATH,
          PostMindLangType.WEIGHT,
        ],
        outputType: PostMindLangType.ENSEMBLE,
        constraints: [],
      },
      {
        name: 'critique',
        inputTypes: [PostMindLangType.ENSEMBLE],
        outputType: PostMindLangType.SCALAR,
        constraints: [],
      },
      {
        name: 'sample',
        inputTypes: [PostMindLangType.ENSEMBLE],
        outputType: PostMindLangType.PATH,
        constraints: [],
      },
    ];

    for (const func of functions) {
      this.environment.functions.set(func.name, func);
    }
  }

  /**
   * Get type definition by name
   */
  getType(typeName: PostMindLangType): TypeDefinition | undefined {
    return this.environment.types.get(typeName);
  }

  /**
   * Register a variable with its type
   */
  registerVariable(varName: string, typeName: PostMindLangType): void {
    this.environment.variables.set(varName, typeName);
  }

  /**
   * Get variable type
   */
  getVariableType(varName: string): PostMindLangType | undefined {
    return this.environment.variables.get(varName);
  }

  /**
   * Type check a value against a variable
   */
  typeCheckVariable(varName: string, value: Vector): boolean {
    const typeName = this.getVariableType(varName);
    if (!typeName) return false;

    const type = this.getType(typeName);
    if (!type) return false;

    return type.typeCheck(value);
  }

  /**
   * Infer type of function output
   */
  inferFunctionType(
    functionName: string,
    inputTypes: PostMindLangType[],
  ): PostMindLangType | undefined {
    const func = this.environment.functions.get(functionName);
    if (!func) return undefined;

    // Check input types match
    if (inputTypes.length !== func.inputTypes.length) return undefined;

    for (let i = 0; i < inputTypes.length; i++) {
      if (inputTypes[i] !== func.inputTypes[i]) return undefined;
    }

    return func.outputType;
  }

  /**
   * Get function signature
   */
  getFunctionSignature(functionName: string): TypeSignature | undefined {
    return this.environment.functions.get(functionName);
  }

  /**
   * Print type environment (for debugging)
   */
  printEnvironment(): string {
    let output = '=== Type Environment ===\n\n';

    output += '--- Registered Types ---\n';
    for (const [name, type] of this.environment.types) {
      output += `${name}: dimension=${type.dimension}, semantic="${type.semanticMeaning}"\n`;
    }

    output += '\n--- Registered Variables ---\n';
    for (const [varName, typeName] of this.environment.variables) {
      output += `${varName}: ${typeName}\n`;
    }

    output += '\n--- Registered Functions ---\n';
    for (const [funcName, sig] of this.environment.functions) {
      const inputStr = sig.inputTypes.join(', ');
      output += `${funcName}(${inputStr}) -> ${sig.outputType}\n`;
    }

    return output;
  }
}

// ============================================================================
// Type Conversion and Projection
// ============================================================================

export class TypeConverter {
  /**
   * Convert between compatible types via projection
   */
  static convert(value: Vector, fromType: TypeDefinition, toType: TypeDefinition): Vector {
    if (fromType.dimension === toType.dimension) {
      return toType.project(value);
    }

    // If dimensions differ, use interpolation
    if (fromType.dimension > toType.dimension) {
      return this.downproject(value, toType.dimension);
    } else {
      return this.upproject(value, toType.dimension);
    }
  }

  /**
   * Downproject to lower dimension (e.g., via PCA)
   */
  private static downproject(value: Vector, targetDim: number): Vector {
    // Simple truncation with rescaling
    const factor = value.length / targetDim;
    const projected: Vector = [];

    for (let i = 0; i < targetDim; i++) {
      let sum = 0;
      const start = Math.floor(i * factor);
      const end = Math.floor((i + 1) * factor);

      for (let j = start; j < end && j < value.length; j++) {
        sum += value[j];
      }

      projected.push(sum / (end - start));
    }

    return projected;
  }

  /**
   * Upproject to higher dimension
   */
  private static upproject(value: Vector, targetDim: number): Vector {
    // Simple linear interpolation
    const projected = new Array(targetDim).fill(0);
    const factor = value.length / targetDim;

    for (let i = 0; i < value.length; i++) {
      const idx = Math.floor(i / factor);
      if (idx < projected.length) {
        projected[idx] += value[i];
      }
    }

    return projected;
  }
}
