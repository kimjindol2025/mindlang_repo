/**
 * MindLang Compiler: AST → Bytecode
 * Converts AST nodes to 45 opcodes with bytecode generation
 */

// ============================================================================
// Opcode Definitions
// ============================================================================

export enum Opcode {
  // Data Movement (0x00-0x04)
  LOAD_QUERY = 0x00,
  LOAD_CONST = 0x01,
  STORE_LOCAL = 0x02,
  LOAD_LOCAL = 0x03,
  HEAP_LOAD = 0x04,

  // Encoding (0x10-0x12)
  ENCODE_Q = 0x10,
  NORM_L2 = 0x11,
  DROPOUT = 0x12,

  // Activation Functions (0x20-0x23)
  RELU = 0x20,
  TANH = 0x21,
  SIGMOID = 0x22,
  SOFTMAX = 0x23,

  // Arithmetic (0x30-0x35)
  SCALE = 0x30,
  ADD = 0x31,
  SUB = 0x32,
  HADAMARD = 0x33,
  MATMUL = 0x34,
  OUTER = 0x35,

  // Projections (0x40-0x42)
  PROJECT_A = 0x40,
  PROJECT_B = 0x41,
  PROJECT_C = 0x42,

  // Path Forking (0x50)
  FORK_PATHS = 0x50,

  // Synchronization (0x51-0x52)
  BARRIER = 0x51,
  THREAD_YIELD = 0x52,

  // Weight Computation (0x60-0x61)
  COMPUTE_WEIGHTS = 0x60,
  TEMP_SCALE = 0x61,

  // Ensemble (0x70-0x72)
  ENSEMBLE = 0x70,
  CONTRIB_A = 0x71,
  CONTRIB_B = 0x72,

  // Critique (0x80-0x82)
  CRITIQUE = 0x80,
  CRIT_CHECK = 0x81,
  RETRY_WEIGHTS = 0x82,

  // Sampling (0x90-0x93)
  LOGITS_TO_PROB = 0x90,
  FILTER_THRESHOLD = 0x91,
  SAMPLE = 0x92,
  GREEDY = 0x93,

  // Detokenization (0xA0-0xA1)
  DECODE_MORPHEME = 0xa0,
  COMPOSE_KOREAN = 0xa1,

  // Control Flow (0xB0-0xB3)
  JUMP = 0xb0,
  JUMP_IF_TRUE = 0xb1,
  LOOP_START = 0xb2,
  LOOP_END = 0xb3,

  // Debug & Admin (0xF0-0xF1)
  DEBUG_PRINT = 0xf0,
  HALT = 0xf1,
}

// ============================================================================
// AST Node Types
// ============================================================================

export interface ASTNode {
  type: string;
  id?: string | number;
}

export interface QueryNode extends ASTNode {
  type: 'QueryNode';
  embedding: number[];
  semanticContent: string;
  confidence: number;
  sourceLength: number;
}

export interface LatentNode extends ASTNode {
  type: 'LatentNode';
  latent: number[];
  latentDim: number;
  encoderWeights: number[][];
  encoderBias: number[];
  activationFunc: 'relu' | 'tanh' | 'sigmoid' | 'linear';
  paths?: PathNode[];
}

export interface PathNode extends ASTNode {
  type: 'PathNode';
  pathType: 'analytical' | 'creative' | 'empirical';
  output: number[];
  projectionMatrix: number[][];
  projectionBias: number[];
  activation: 'relu' | 'tanh' | 'sigmoid' | 'linear';
  noise?: number[];
  noiseScale?: number;
}

export interface WeightNode extends ASTNode {
  type: 'WeightNode';
  attentionMatrix: number[][];
  attentionBias: number[];
  input: number[];
  weights: { alpha: number; beta: number; gamma: number };
}

export interface EnsembleNode extends ASTNode {
  type: 'EnsembleNode';
  paths: number[][];
  weights: { alpha: number; beta: number; gamma: number };
  result: number[];
}

export interface CritiqueNode extends ASTNode {
  type: 'CritiqueNode';
  input: number[];
  confidence: number;
  shouldRetry: boolean;
}

export interface SampleNode extends ASTNode {
  type: 'SampleNode';
  latent: number[];
  vocabWeights: number[][];
  vocabBias: number[];
  distribution: number[];
  threshold: number;
  sampledTokenIndex: number;
}

export interface DetokenizeNode extends ASTNode {
  type: 'DetokenizeNode';
  latent: number[];
  previousTokens: string[];
  koreanText: string;
}

// ============================================================================
// Bytecode Structures
// ============================================================================

export interface Instruction {
  opcode: Opcode;
  operands: (number | string)[];
}

export interface BytecodeProgram {
  magic: string; // "MIND"
  version: number; // 1.0
  entryPoint: number; // offset in bytecode
  size: number; // total bytecode length
  constants: Map<number, any>; // constant pool
  instructions: Instruction[]; // executable instructions
  jumpTable: Map<number, number>; // label -> offset
}

// ============================================================================
// Compiler Class
// ============================================================================

export class Compiler {
  private constants: Map<number, any> = new Map();
  private constantId: number = 0;
  private instructions: Instruction[] = [];
  private jumpTable: Map<number, number> = new Map();
  private labelCounter: number = 0;
  private registerAllocations: Map<string, number> = new Map();

  /**
   * Compile an AST node to bytecode
   */
  compile(node: ASTNode): BytecodeProgram {
    this.instructions = [];
    this.constants.clear();
    this.constantId = 0;
    this.jumpTable.clear();
    this.labelCounter = 0;
    this.registerAllocations.clear();

    this.compileNode(node);

    // Add halt instruction at end
    this.emit(Opcode.HALT);

    return this.buildProgram();
  }

  /**
   * Emit an instruction with operands
   */
  private emit(opcode: Opcode, ...operands: (number | string)[]): number {
    const offset = this.instructions.length;
    this.instructions.push({ opcode, operands });
    return offset;
  }

  /**
   * Add a constant to the pool
   */
  private addConstant(value: any): number {
    const id = this.constantId++;
    this.constants.set(id, value);
    return id;
  }

  /**
   * Create a label for jump targets
   */
  private createLabel(): number {
    return this.labelCounter++;
  }

  /**
   * Patch a jump instruction with target address
   */
  private patchJump(instructionIndex: number, targetAddress: number): void {
    if (instructionIndex < this.instructions.length) {
      this.instructions[instructionIndex].operands[0] = targetAddress;
    }
  }

  /**
   * Recursively compile AST nodes
   */
  private compileNode(node: ASTNode | null): void {
    if (!node) return;

    switch (node.type) {
      case 'QueryNode':
        this.compileQueryNode(node as QueryNode);
        break;
      case 'LatentNode':
        this.compileLatentNode(node as LatentNode);
        break;
      case 'PathNode':
        this.compilePathNode(node as PathNode);
        break;
      case 'WeightNode':
        this.compileWeightNode(node as WeightNode);
        break;
      case 'EnsembleNode':
        this.compileEnsembleNode(node as EnsembleNode);
        break;
      case 'CritiqueNode':
        this.compileCritiqueNode(node as CritiqueNode);
        break;
      case 'SampleNode':
        this.compileSampleNode(node as SampleNode);
        break;
      case 'DetokenizeNode':
        this.compileDetokenizeNode(node as DetokenizeNode);
        break;
    }
  }

  /**
   * Compile QueryNode: LOAD_QUERY opcode
   */
  private compileQueryNode(node: QueryNode): void {
    const embeddingConstId = this.addConstant(node.embedding);
    const addr = embeddingConstId;
    this.emit(Opcode.LOAD_QUERY, addr);
  }

  /**
   * Compile LatentNode: ENCODE_Q + NORM_L2
   */
  private compileLatentNode(node: LatentNode): void {
    const latentId = this.addConstant(node.latent);
    const weightsId = this.addConstant(node.encoderWeights);
    const biasId = this.addConstant(node.encoderBias);

    this.emit(Opcode.LOAD_CONST, latentId);  // push q (latent input)
    this.emit(Opcode.LOAD_CONST, weightsId);
    this.emit(Opcode.LOAD_CONST, biasId);
    this.emit(Opcode.ENCODE_Q);
    this.emit(Opcode.NORM_L2);

    // Apply activation function
    this.compileActivation(node.activationFunc);

    // Store in register
    this.emit(Opcode.STORE_LOCAL, 0); // r0 = z

    // Compile child paths if present
    if (node.paths && node.paths.length === 3) {
      // Load z again for fork
      this.emit(Opcode.LOAD_LOCAL, 0);

      // Fork into 3 parallel paths
      this.emit(Opcode.FORK_PATHS);

      // Compile each path
      for (const path of node.paths) {
        this.compilePathNode(path);
      }

      // Barrier synchronization
      this.emit(Opcode.BARRIER);
    }
  }

  /**
   * Compile PathNode: PROJECT_A/B/C opcodes
   */
  private compilePathNode(node: PathNode): void {
    const projectionMatrixId = this.addConstant(node.projectionMatrix);
    const projectionBiasId = this.addConstant(node.projectionBias);

    this.emit(Opcode.LOAD_CONST, projectionMatrixId);
    this.emit(Opcode.LOAD_CONST, projectionBiasId);

    // Choose projection based on path type
    switch (node.pathType) {
      case 'analytical':
        this.emit(Opcode.PROJECT_A);
        break;
      case 'creative':
        // Noise is added internally by PROJECT_B opcode
        this.emit(Opcode.PROJECT_B);
        break;
      case 'empirical':
        this.emit(Opcode.PROJECT_C);
        break;
    }

    // Apply activation
    this.compileActivation(node.activation);
  }

  /**
   * Compile WeightNode: COMPUTE_WEIGHTS opcode
   */
  private compileWeightNode(node: WeightNode): void {
    const attentionMatrixId = this.addConstant(node.attentionMatrix);
    const attentionBiasId = this.addConstant(node.attentionBias);

    this.emit(Opcode.LOAD_CONST, attentionMatrixId);
    this.emit(Opcode.LOAD_CONST, attentionBiasId);
    this.emit(Opcode.COMPUTE_WEIGHTS);

    // Store weights in register
    this.emit(Opcode.STORE_LOCAL, 4); // r4 = [α, β, γ]
  }

  /**
   * Compile EnsembleNode: ENSEMBLE opcode
   */
  private compileEnsembleNode(node: EnsembleNode): void {
    // Load weights
    this.emit(Opcode.LOAD_LOCAL, 4); // [α, β, γ]

    // Load paths (r1, r2, r3)
    this.emit(Opcode.LOAD_LOCAL, 1); // z_a
    this.emit(Opcode.LOAD_LOCAL, 2); // z_b
    this.emit(Opcode.LOAD_LOCAL, 3); // z_c

    // Compute ensemble
    this.emit(Opcode.ENSEMBLE);

    // Store result
    this.emit(Opcode.STORE_LOCAL, 5); // r5 = z_ens
  }

  /**
   * Compile CritiqueNode: CRITIQUE + CRIT_CHECK opcodes
   */
  private compileCritiqueNode(node: CritiqueNode): void {
    this.emit(Opcode.LOAD_LOCAL, 5); // z_ens

    // Compute critique
    this.emit(Opcode.CRITIQUE);
    this.emit(Opcode.STORE_LOCAL, 6); // r6 = δ

    // Check confidence
    const lowThreshold = -0.3;
    const highThreshold = 1.0;
    this.emit(Opcode.CRIT_CHECK, lowThreshold, highThreshold);

    // If low confidence, retry
    if (node.shouldRetry) {
      this.emit(Opcode.RETRY_WEIGHTS);
      this.emit(Opcode.STORE_LOCAL, 4); // Updated weights
      this.emit(Opcode.JUMP, 0); // Jump back (will be patched)
    }
  }

  /**
   * Compile SampleNode: LOGITS_TO_PROB + SAMPLE opcodes
   */
  private compileSampleNode(node: SampleNode): void {
    const vocabWeightsId = this.addConstant(node.vocabWeights);
    const vocabBiasId = this.addConstant(node.vocabBias);
    const thresholdId = this.addConstant(node.threshold);

    this.emit(Opcode.LOAD_LOCAL, 5); // z_ens
    this.emit(Opcode.LOAD_CONST, vocabWeightsId);
    this.emit(Opcode.LOAD_CONST, vocabBiasId);

    this.emit(Opcode.LOGITS_TO_PROB);
    this.emit(Opcode.LOAD_CONST, thresholdId);
    this.emit(Opcode.FILTER_THRESHOLD);
    this.emit(Opcode.SAMPLE);
  }

  /**
   * Compile DetokenizeNode: DECODE_MORPHEME + COMPOSE_KOREAN
   */
  private compileDetokenizeNode(node: DetokenizeNode): void {
    this.emit(Opcode.DECODE_MORPHEME);
    this.emit(Opcode.COMPOSE_KOREAN);
  }

  /**
   * Helper: compile activation function
   */
  private compileActivation(func: 'relu' | 'tanh' | 'sigmoid' | 'linear'): void {
    switch (func) {
      case 'relu':
        this.emit(Opcode.RELU);
        break;
      case 'tanh':
        this.emit(Opcode.TANH);
        break;
      case 'sigmoid':
        this.emit(Opcode.SIGMOID);
        break;
      case 'linear':
        // No operation
        break;
    }
  }

  /**
   * Build the final bytecode program
   */
  private buildProgram(): BytecodeProgram {
    return {
      magic: 'MIND',
      version: 1.0,
      entryPoint: 0,
      size: this.instructions.length,
      constants: this.constants,
      instructions: this.instructions,
      jumpTable: this.jumpTable,
    };
  }

  /**
   * Generate binary bytecode buffer
   */
  generateBytecode(program: BytecodeProgram): Buffer {
    const buffer: number[] = [];

    // Write header
    buffer.push(...this.stringToBytes(program.magic)); // "MIND"
    buffer.push(...this.writeU32(program.version)); // version
    buffer.push(...this.writeU32(program.entryPoint)); // entry point
    buffer.push(...this.writeU32(program.size)); // size

    // Write instructions
    for (const instr of program.instructions) {
      buffer.push(instr.opcode);

      // Write operands based on instruction type
      for (const operand of instr.operands) {
        if (typeof operand === 'number') {
          if (instr.opcode === Opcode.STORE_LOCAL || instr.opcode === Opcode.LOAD_LOCAL) {
            buffer.push(operand); // u8
          } else {
            buffer.push(...this.writeU32(operand)); // u32
          }
        }
      }
    }

    return Buffer.from(buffer);
  }

  /**
   * Helper: convert string to bytes
   */
  private stringToBytes(str: string): number[] {
    return Array.from(str).map(c => c.charCodeAt(0));
  }

  /**
   * Helper: write u32
   */
  private writeU32(value: number): number[] {
    return [
      (value >>> 24) & 0xff,
      (value >>> 16) & 0xff,
      (value >>> 8) & 0xff,
      value & 0xff,
    ];
  }
}

// ============================================================================
// AST Builder (for testing)
// ============================================================================

export class ASTBuilder {
  static createSimpleQuery(text: string, dim: number = 128): QueryNode {
    return {
      type: 'QueryNode',
      embedding: Array(dim).fill(0).map(() => Math.random()),
      semanticContent: text,
      confidence: 0.9,
      sourceLength: text.length,
    };
  }

  static createLatentNode(dim: number = 256): LatentNode {
    return {
      type: 'LatentNode',
      latent: Array(dim).fill(0).map(() => Math.random()),
      latentDim: dim,
      encoderWeights: Array(dim)
        .fill(0)
        .map(() => Array(128).fill(0).map(() => Math.random())),
      encoderBias: Array(dim).fill(0).map(() => Math.random()),
      activationFunc: 'relu',
      paths: [
        ASTBuilder.createPathNode('analytical', dim),
        ASTBuilder.createPathNode('creative', dim),
        ASTBuilder.createPathNode('empirical', dim),
      ],
    };
  }

  static createPathNode(
    pathType: 'analytical' | 'creative' | 'empirical',
    dim: number = 256
  ): PathNode {
    return {
      type: 'PathNode',
      pathType,
      output: Array(dim).fill(0).map(() => Math.random()),
      projectionMatrix: Array(dim)
        .fill(0)
        .map(() => Array(dim).fill(0).map(() => Math.random())),
      projectionBias: Array(dim).fill(0).map(() => Math.random()),
      activation: pathType === 'analytical' ? 'relu' : pathType === 'creative' ? 'tanh' : 'sigmoid',
      noise: pathType === 'creative' ? Array(dim).fill(0).map(() => Math.random()) : undefined,
      noiseScale: pathType === 'creative' ? 0.1 : undefined,
    };
  }

  static createCompleteProgram(
    text: string = 'test query'
  ): QueryNode & { latent?: LatentNode } {
    const query = ASTBuilder.createSimpleQuery(text);
    const latent = ASTBuilder.createLatentNode();
    return { ...query, latent };
  }
}
