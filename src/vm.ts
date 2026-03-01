/**
 * MindLang Virtual Machine
 * Stack-based execution engine with memory management and threading
 */

import { Opcode, BytecodeProgram, Instruction } from './compiler';

// ============================================================================
// Memory Structures
// ============================================================================

interface MemorySegment {
  buffer: ArrayBuffer;
  view: Float64Array;
  size: number;
  used: number;
}

interface StackFrame {
  basePointer: number;
  returnAddress: number;
  localVariables: Map<number, number[]>;
}

interface VirtualMachineState {
  pc: number; // Program counter
  sp: number; // Stack pointer
  bp: number; // Base pointer
  registers: Map<number, number[]>; // r0-r7
  stack: number[][];
  heap: Map<number, number[]>;
  instructionCount: number;
  halted: boolean;
}

// ============================================================================
// Configuration
// ============================================================================

export interface VMConfig {
  stackSizeMB?: number;
  heapSizeMB?: number;
  maxInstructions?: number;
  maxThreads?: number;
  enableDebug?: boolean;
  enableProfiling?: boolean;
}

// ============================================================================
// Virtual Machine
// ============================================================================

export class VirtualMachine {
  private state: VirtualMachineState;
  private program: BytecodeProgram | null = null;
  private config: Required<VMConfig>;
  private heapAllocationMap: Map<number, { size: number; used: boolean }> = new Map();
  private instructionTiming: Map<number, number> = new Map();
  private threadPool: Map<number, VirtualMachineState> = new Map();
  private threadBarrier: Map<number, boolean> = new Map();
  private loopStack: number[] = [];

  constructor(config: VMConfig = {}) {
    this.config = {
      stackSizeMB: config.stackSizeMB || 10,
      heapSizeMB: config.heapSizeMB || 500,
      maxInstructions: config.maxInstructions || 10_000_000,
      maxThreads: config.maxThreads || 16,
      enableDebug: config.enableDebug || false,
      enableProfiling: config.enableProfiling || false,
    };

    this.state = {
      pc: 0,
      sp: 0,
      bp: 0,
      registers: new Map(),
      stack: [],
      heap: new Map(),
      instructionCount: 0,
      halted: false,
    };

    // Initialize registers
    for (let i = 0; i < 8; i++) {
      this.state.registers.set(i, []);
    }
  }

  /**
   * Load bytecode program
   */
  loadProgram(program: BytecodeProgram): void {
    this.program = program;
    this.state.pc = program.entryPoint;
    this.state.sp = 0;
    this.state.bp = 0;
  }

  /**
   * Execute the loaded program
   */
  execute(): number[] | null {
    if (!this.program) {
      throw new Error('No program loaded');
    }

    this.state.halted = false;
    this.state.instructionCount = 0;

    while (
      !this.state.halted &&
      this.state.instructionCount < this.config.maxInstructions &&
      this.state.pc < this.program.instructions.length
    ) {
      const instruction = this.program.instructions[this.state.pc];

      if (this.config.enableDebug) {
        console.log(`[PC=${this.state.pc}] Executing ${Opcode[instruction.opcode]}`);
      }

      this.executeInstruction(instruction);
      this.state.instructionCount++;
      this.state.pc++;
    }

    // Return top of stack if available
    if (this.state.stack.length > 0) {
      return this.state.stack[this.state.stack.length - 1];
    }

    return null;
  }

  /**
   * Execute a single instruction
   */
  private executeInstruction(instr: Instruction): void {
    const opcode = instr.opcode;

    switch (opcode) {
      case Opcode.LOAD_QUERY:
        this.opLoadQuery(instr);
        break;
      case Opcode.LOAD_CONST:
        this.opLoadConst(instr);
        break;
      case Opcode.STORE_LOCAL:
        this.opStoreLocal(instr);
        break;
      case Opcode.LOAD_LOCAL:
        this.opLoadLocal(instr);
        break;
      case Opcode.HEAP_LOAD:
        this.opHeapLoad(instr);
        break;

      case Opcode.ENCODE_Q:
        this.opEncodeQ();
        break;
      case Opcode.NORM_L2:
        this.opNormL2();
        break;
      case Opcode.DROPOUT:
        this.opDropout(instr);
        break;

      case Opcode.RELU:
        this.opReLU();
        break;
      case Opcode.TANH:
        this.opTanh();
        break;
      case Opcode.SIGMOID:
        this.opSigmoid();
        break;
      case Opcode.SOFTMAX:
        this.opSoftmax();
        break;

      case Opcode.SCALE:
        this.opScale();
        break;
      case Opcode.ADD:
        this.opAdd();
        break;
      case Opcode.SUB:
        this.opSub();
        break;
      case Opcode.HADAMARD:
        this.opHadamard();
        break;
      case Opcode.MATMUL:
        this.opMatmul();
        break;
      case Opcode.OUTER:
        this.opOuter();
        break;

      case Opcode.PROJECT_A:
        this.opProjectA();
        break;
      case Opcode.PROJECT_B:
        this.opProjectB();
        break;
      case Opcode.PROJECT_C:
        this.opProjectC();
        break;

      case Opcode.FORK_PATHS:
        this.opForkPaths();
        break;
      case Opcode.BARRIER:
        this.opBarrier();
        break;
      case Opcode.THREAD_YIELD:
        this.opThreadYield();
        break;

      case Opcode.COMPUTE_WEIGHTS:
        this.opComputeWeights();
        break;
      case Opcode.TEMP_SCALE:
        this.opTempScale(instr);
        break;

      case Opcode.ENSEMBLE:
        this.opEnsemble();
        break;
      case Opcode.CONTRIB_A:
        this.opContribA();
        break;
      case Opcode.CONTRIB_B:
        this.opContribB();
        break;

      case Opcode.CRITIQUE:
        this.opCritique();
        break;
      case Opcode.CRIT_CHECK:
        this.opCritCheck(instr);
        break;
      case Opcode.RETRY_WEIGHTS:
        this.opRetryWeights();
        break;

      case Opcode.LOGITS_TO_PROB:
        this.opLogitsToProb();
        break;
      case Opcode.FILTER_THRESHOLD:
        this.opFilterThreshold(instr);
        break;
      case Opcode.SAMPLE:
        this.opSample();
        break;
      case Opcode.GREEDY:
        this.opGreedy();
        break;

      case Opcode.DECODE_MORPHEME:
        this.opDecodeMorpheme();
        break;
      case Opcode.COMPOSE_KOREAN:
        this.opComposeKorean();
        break;

      case Opcode.JUMP:
        this.opJump(instr);
        break;
      case Opcode.JUMP_IF_TRUE:
        this.opJumpIfTrue(instr);
        break;
      case Opcode.LOOP_START:
        this.opLoopStart(instr);
        break;
      case Opcode.LOOP_END:
        this.opLoopEnd();
        break;

      case Opcode.DEBUG_PRINT:
        this.opDebugPrint();
        break;
      case Opcode.HALT:
        this.state.halted = true;
        break;

      default:
        throw new Error(`Unknown opcode: 0x${(opcode as number).toString(16)}`);
    }
  }

  // ========================================================================
  // Data Movement Operations
  // ========================================================================

  private opLoadQuery(instr: Instruction): void {
    const addr = instr.operands[0] as number;
    const constant = this.program!.constants.get(addr);
    if (constant) {
      this.state.stack.push([...constant]);
    }
  }

  private opLoadConst(instr: Instruction): void {
    const constId = instr.operands[0] as number;
    const value = this.program!.constants.get(constId);
    if (value) {
      this.state.stack.push(Array.isArray(value) ? [...value] : value);
    }
  }

  private opStoreLocal(instr: Instruction): void {
    const slot = instr.operands[0] as number;
    const value = this.state.stack.pop();
    if (value !== undefined) {
      this.state.registers.set(slot, Array.isArray(value) ? [...value] : [value]);
    }
  }

  private opLoadLocal(instr: Instruction): void {
    const slot = instr.operands[0] as number;
    const value = this.state.registers.get(slot);
    if (value !== undefined) {
      this.state.stack.push([...value]);
    }
  }

  private opHeapLoad(instr: Instruction): void {
    const addr = instr.operands[0] as number;
    const size = instr.operands[1] as number;
    const value = this.state.heap.get(addr);
    if (value) {
      this.state.stack.push([...value]);
    }
  }

  // ========================================================================
  // Encoding Operations
  // ========================================================================

  private opEncodeQ(): void {
    const b = this.state.stack.pop() as number[]; // bias
    const W = this.state.stack.pop() as unknown as number[][]; // weights
    const q = this.state.stack.pop() as number[]; // query

    const m = W.length;
    const result: number[] = new Array(m);

    for (let i = 0; i < m; i++) {
      let sum = b[i] || 0;
      for (let j = 0; j < q.length; j++) {
        sum += W[i][j] * q[j];
      }
      result[i] = sum;
    }

    this.state.stack.push(result);
  }

  private opNormL2(): void {
    const v = this.state.stack.pop() as number[];
    const norm = Math.sqrt(v.reduce((sum, x) => sum + x * x, 0));
    const result = norm > 0 ? v.map(x => x / norm) : v;
    this.state.stack.push(result);
  }

  private opDropout(instr: Instruction): void {
    const rate = instr.operands[0] as number;
    const v = this.state.stack.pop() as number[];
    const result = v.map(x => (Math.random() > rate ? x / (1 - rate) : 0));
    this.state.stack.push(result);
  }

  // ========================================================================
  // Activation Functions
  // ========================================================================

  private opReLU(): void {
    const v = this.state.stack.pop() as number[];
    const result = v.map(x => Math.max(0, x));
    this.state.stack.push(result);
  }

  private opTanh(): void {
    const v = this.state.stack.pop() as number[];
    const result = v.map(x => Math.tanh(x));
    this.state.stack.push(result);
  }

  private opSigmoid(): void {
    const v = this.state.stack.pop() as number[];
    const result = v.map(x => 1 / (1 + Math.exp(-x)));
    this.state.stack.push(result);
  }

  private opSoftmax(): void {
    const v = this.state.stack.pop() as number[];
    const max = Math.max(...v);
    const exp = v.map(x => Math.exp(x - max));
    const sum = exp.reduce((a, b) => a + b, 0);
    const result = exp.map(x => x / sum);
    this.state.stack.push(result);
  }

  // ========================================================================
  // Arithmetic Operations
  // ========================================================================

  private opScale(): void {
    const alpha = this.state.stack.pop() as number | number[];
    const v = this.state.stack.pop() as number[];
    const scalar = Array.isArray(alpha) ? alpha[0] : alpha;
    const result = v.map(x => x * scalar);
    this.state.stack.push(result);
  }

  private opAdd(): void {
    const v2 = this.state.stack.pop() as number[];
    const v1 = this.state.stack.pop() as number[];
    const result = v1.map((x, i) => x + (v2[i] || 0));
    this.state.stack.push(result);
  }

  private opSub(): void {
    const v2 = this.state.stack.pop() as number[];
    const v1 = this.state.stack.pop() as number[];
    const result = v1.map((x, i) => x - (v2[i] || 0));
    this.state.stack.push(result);
  }

  private opHadamard(): void {
    const v2 = this.state.stack.pop() as number[];
    const v1 = this.state.stack.pop() as number[];
    const result = v1.map((x, i) => x * (v2[i] || 0));
    this.state.stack.push(result);
  }

  private opMatmul(): void {
    const v = this.state.stack.pop() as number[];
    const M = this.state.stack.pop() as unknown as number[][];
    const result = new Array(M.length);

    for (let i = 0; i < M.length; i++) {
      let sum = 0;
      for (let j = 0; j < v.length; j++) {
        sum += M[i][j] * v[j];
      }
      result[i] = sum;
    }

    this.state.stack.push(result);
  }

  private opOuter(): void {
    const v = this.state.stack.pop() as number[];
    const u = this.state.stack.pop() as number[];
    const result = u.map(ui => v.map(vi => ui * vi));
    this.state.stack.push(result as unknown as number[]);
  }

  // ========================================================================
  // Projection Operations
  // ========================================================================

  private opProjectA(): void {
    // PROJECT_A: z_a = W_a·z + b_a
    const b = this.state.stack.pop() as number[];
    const W = this.state.stack.pop() as unknown as number[][];
    const z = (this.state.registers.get(0) || []) as number[]; // z from r0 (set by FORK_PATHS)

    const result = new Array(W.length);
    for (let i = 0; i < W.length; i++) {
      let sum = b[i] || 0;
      for (let j = 0; j < z.length; j++) {
        sum += W[i][j] * z[j];
      }
      result[i] = sum;
    }

    this.state.stack.push(result);
    this.state.registers.set(1, result); // r1 = z_a
  }

  private opProjectB(): void {
    // PROJECT_B: z_b = W_b·z + b_b + ε
    const b = this.state.stack.pop() as number[];
    const W = this.state.stack.pop() as unknown as number[][];
    const z = (this.state.registers.get(0) || []) as number[]; // z from r0 (set by FORK_PATHS)

    const result = new Array(W.length);
    for (let i = 0; i < W.length; i++) {
      let sum = b[i] || 0;
      for (let j = 0; j < z.length; j++) {
        sum += W[i][j] * z[j];
      }
      result[i] = sum + (Math.random() - 0.5) * 0.1; // Add noise
    }

    this.state.stack.push(result);
    this.state.registers.set(2, result); // r2 = z_b
  }

  private opProjectC(): void {
    // PROJECT_C: z_c = W_c·z + b_c
    const b = this.state.stack.pop() as number[];
    const W = this.state.stack.pop() as unknown as number[][];
    const z = (this.state.registers.get(0) || []) as number[]; // z from r0 (set by FORK_PATHS)

    const result = new Array(W.length);
    for (let i = 0; i < W.length; i++) {
      let sum = b[i] || 0;
      for (let j = 0; j < z.length; j++) {
        sum += W[i][j] * z[j];
      }
      result[i] = sum;
    }

    this.state.stack.push(result);
    this.state.registers.set(3, result); // r3 = z_c
  }

  // ========================================================================
  // Parallelism Operations
  // ========================================================================

  private opForkPaths(): void {
    // Fork into 3 parallel threads (simulate by storing state)
    const z = this.state.stack.pop() as number[];
    this.state.registers.set(0, z); // r0 = z (for all threads)

    // In a real implementation, this would spawn worker threads
    // For now, we just mark that threads should be spawned
  }

  private opBarrier(): void {
    // Barrier synchronization point
    // In a real implementation, this would wait for all threads
    // For now, it's a no-op
  }

  private opThreadYield(): void {
    // Yield control to other threads
    // No-op in single-threaded simulation
  }

  // ========================================================================
  // Weight Operations
  // ========================================================================

  private opComputeWeights(): void {
    // [α, β, γ] = softmax(W·z + b)
    const z = this.state.stack.pop() as number[];
    const logits = [
      0.3 + Math.random() * 0.4, // α
      0.3 + Math.random() * 0.4, // β
      0.3 + Math.random() * 0.4, // γ
    ];

    // Softmax
    const max = Math.max(...logits);
    const exp = logits.map(x => Math.exp(x - max));
    const sum = exp.reduce((a, b) => a + b, 0);
    const weights = exp.map(x => x / sum);

    this.state.stack.push(weights);
    this.state.registers.set(4, weights); // r4 = [α, β, γ]
  }

  private opTempScale(instr: Instruction): void {
    const T = instr.operands[0] as number;
    const logits = this.state.stack.pop() as number[];
    const result = logits.map(x => x / T);
    this.state.stack.push(result);
  }

  // ========================================================================
  // Ensemble Operations
  // ========================================================================

  private opEnsemble(): void {
    // z_ens = α·z_a + β·z_b + γ·z_c
    const z_c = this.state.stack.pop() as number[];
    const z_b = this.state.stack.pop() as number[];
    const z_a = this.state.stack.pop() as number[];
    const weights = this.state.stack.pop() as number[];

    const [alpha, beta, gamma] = weights;
    const result = z_a.map((x, i) => alpha * x + beta * (z_b[i] || 0) + gamma * (z_c[i] || 0));

    this.state.stack.push(result);
    this.state.registers.set(5, result); // r5 = z_ens
  }

  private opContribA(): void {
    // Compute α·z_a
    const alpha = this.state.stack.pop() as number | number[];
    const z_a = this.state.stack.pop() as number[];
    const scalar = Array.isArray(alpha) ? alpha[0] : alpha;
    const result = z_a.map(x => x * scalar);
    this.state.stack.push(result);
  }

  private opContribB(): void {
    // Compute β·z_b
    const beta = this.state.stack.pop() as number | number[];
    const z_b = this.state.stack.pop() as number[];
    const scalar = Array.isArray(beta) ? beta[0] : beta;
    const result = z_b.map(x => x * scalar);
    this.state.stack.push(result);
  }

  // ========================================================================
  // Critique Operations
  // ========================================================================

  private opCritique(): void {
    // δ = crit(z_ens) ∈ [-1, 1]
    const z_ens = this.state.stack.pop() as number[];

    // Simple heuristic: confidence based on norm
    const norm = Math.sqrt(z_ens.reduce((sum, x) => sum + x * x, 0));
    const confidence = Math.tanh(norm / z_ens.length);

    this.state.stack.push([confidence]);
    this.state.registers.set(6, [confidence]); // r6 = δ
  }

  private opCritCheck(instr: Instruction): void {
    const lowThreshold = instr.operands[0] as number;
    const highThreshold = instr.operands[1] as number;
    const delta = this.state.stack.pop() as number[];

    const confidence = delta[0] || 0;
    const isValid = confidence >= lowThreshold && confidence <= highThreshold;

    this.state.stack.push([isValid ? 1 : 0]);
  }

  private opRetryWeights(): void {
    // critique 결과(r6 = δ)를 기반으로 가중치 동적 조정
    const delta = (this.state.registers.get(6) || [0.5])[0];
    // delta 높으면 analytical 강화, 낮으면 creative 강화
    const alpha = Math.max(0.1, 0.5 - delta * 0.2);
    const beta  = Math.max(0.1, 0.3 + delta * 0.1);
    const gamma = Math.max(0.1, 1 - alpha - beta);
    const sum = alpha + beta + gamma;
    const newWeights = [alpha / sum, beta / sum, gamma / sum];
    this.state.stack.push(newWeights);
    this.state.registers.set(4, newWeights);
  }

  // ========================================================================
  // Sampling Operations
  // ========================================================================

  private opLogitsToProb(): void {
    // p = softmax(W·z_ens)
    const vocabBias = this.state.stack.pop() as number[];
    const vocabWeights = this.state.stack.pop() as unknown as number[][];
    const z_ens = this.state.stack.pop() as number[];

    // Simplified: compute logits then softmax
    const logits = vocabWeights.map((row, i) => {
      let sum = vocabBias[i] || 0;
      for (let j = 0; j < z_ens.length; j++) {
        sum += row[j] * z_ens[j];
      }
      return sum;
    });

    // Softmax
    const max = Math.max(...logits);
    const exp = logits.map(x => Math.exp(x - max));
    const sum = exp.reduce((a, b) => a + b, 0);
    const probs = exp.map(x => x / sum);

    this.state.stack.push(probs);
  }

  private opFilterThreshold(instr: Instruction): void {
    const theta = instr.operands[0] as number;
    const probs = this.state.stack.pop() as number[];

    const candidates = probs
      .map((p, i) => (p > theta ? i : -1))
      .filter(i => i >= 0);

    this.state.stack.push(candidates.map(i => probs[i]));
  }

  private opSample(): void {
    // Sample from filtered distribution
    const probs = this.state.stack.pop() as number[];
    const r = Math.random();

    let cumsum = 0;
    let sampleIdx = 0;
    for (let i = 0; i < probs.length; i++) {
      cumsum += probs[i];
      if (r < cumsum) {
        sampleIdx = i;
        break;
      }
    }

    this.state.stack.push([sampleIdx]);
  }

  private opGreedy(): void {
    // Greedy: argmax(p)
    const p = this.state.stack.pop() as number[];
    const maxIdx = p.indexOf(Math.max(...p));
    this.state.stack.push([maxIdx]);
  }

  // ========================================================================
  // Detokenization Operations
  // ========================================================================

  private opDecodeMorpheme(): void {
    // 잠재 벡터를 스택에서 읽어 형태소 시퀀스 생성 (시뮬레이션)
    const latent = this.state.stack.pop() as number[];
    const norm = latent ? Math.sqrt(latent.reduce((s, x) => s + x * x, 0)) : 1;
    const morphemeCount = Math.max(1, Math.min(5, Math.round(norm * 2)));
    const morphemes = Array.from({ length: morphemeCount }, (_, i) => `형태${i}`);
    this.state.stack.push(morphemes as unknown as number[]);
  }

  private opComposeKorean(): void {
    // Compose Korean text
    const morphemes = this.state.stack.pop() as unknown as string[];
    const text = morphemes.join('');
    this.state.stack.push([text] as unknown as number[]);
  }

  // ========================================================================
  // Control Flow Operations
  // ========================================================================

  private opJump(instr: Instruction): void {
    this.state.pc = (instr.operands[0] as number) - 1; // -1 because PC will be incremented
  }

  private opJumpIfTrue(instr: Instruction): void {
    const cond = this.state.stack.pop();
    const value = Array.isArray(cond) ? cond[0] : cond;

    if (value) {
      this.state.pc = (instr.operands[0] as number) - 1;
    }
  }

  private opLoopStart(instr: Instruction): void {
    const iterCount = instr.operands[0] as number;
    this.state.registers.set(7, [iterCount]);
    this.loopStack.push(this.state.pc); // LOOP_START PC 저장
  }

  private opLoopEnd(): void {
    const counter = this.state.registers.get(7) || [0];
    counter[0]--;
    this.state.registers.set(7, counter);

    if (counter[0] > 0 && this.loopStack.length > 0) {
      // 루프 바디 처음으로 점프 (execute()에서 pc++하므로 loopStartPc로 설정 → loopStartPc+1 실행)
      this.state.pc = this.loopStack[this.loopStack.length - 1];
    } else {
      this.loopStack.pop(); // 루프 완료 시 제거
    }
  }

  // ========================================================================
  // Debug Operations
  // ========================================================================

  private opDebugPrint(): void {
    if (this.config.enableDebug) {
      console.log('Stack:', this.state.stack);
      console.log('Registers:', this.state.registers);
    }
  }

  // ========================================================================
  // Utility Methods
  // ========================================================================

  getState(): VirtualMachineState {
    return { ...this.state };
  }

  getStack(): number[][] {
    return [...this.state.stack];
  }

  getRegisters(): Map<number, number[]> {
    return new Map(this.state.registers);
  }

  getInstructionCount(): number {
    return this.state.instructionCount;
  }
}
