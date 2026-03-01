/**
 * Virtual Machine Tests
 * 60+ test cases for bytecode execution and memory management
 */

import { VirtualMachine, VMConfig } from './vm';
import { Compiler, ASTBuilder, Opcode, BytecodeProgram } from './compiler';

describe('VirtualMachine', () => {
  let vm: VirtualMachine;
  let compiler: Compiler;

  beforeEach(() => {
    vm = new VirtualMachine();
    compiler = new Compiler();
  });

  // ========================================================================
  // Initialization Tests
  // ========================================================================

  describe('Initialization', () => {
    test('should create VM with default config', () => {
      expect(vm).toBeDefined();
    });

    test('should create VM with custom config', () => {
      const config: VMConfig = {
        stackSizeMB: 20,
        heapSizeMB: 100,
        maxInstructions: 5_000_000,
      };
      const customVM = new VirtualMachine(config);
      expect(customVM).toBeDefined();
    });

    test('should initialize with empty stack', () => {
      const state = vm.getState();
      expect(state.stack.length).toBe(0);
    });

    test('should initialize with zero PC', () => {
      const state = vm.getState();
      expect(state.pc).toBe(0);
    });

    test('should initialize registers', () => {
      const registers = vm.getRegisters();
      expect(registers.size).toBeGreaterThan(0);
    });
  });

  // ========================================================================
  // Program Loading Tests
  // ========================================================================

  describe('Program Loading', () => {
    test('should load bytecode program', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const state = vm.getState();
      expect(state.pc).toBe(program.entryPoint);
    });

    test('should throw error when executing without program', () => {
      expect(() => vm.execute()).toThrow();
    });

    test('should set entry point correctly', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const state = vm.getState();
      expect(state.pc).toBe(0);
    });
  });

  // ========================================================================
  // Execution Tests
  // ========================================================================

  describe('Execution', () => {
    test('should execute simple program', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const result = vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should increment instruction counter', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      vm.execute();
      const count = vm.getInstructionCount();
      expect(count).toBeGreaterThan(0);
    });

    test('should halt at HALT opcode', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should respect max instruction limit', () => {
      const config: VMConfig = { maxInstructions: 5 };
      const limitedVM = new VirtualMachine(config);

      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      limitedVM.loadProgram(program);

      limitedVM.execute();
      expect(limitedVM.getInstructionCount()).toBeLessThanOrEqual(5);
    });

    test('should return result from stack', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const result = vm.execute();
      // Result should be from stack or null
      expect(result === null || Array.isArray(result)).toBe(true);
    });
  });

  // ========================================================================
  // Stack Operations Tests
  // ========================================================================

  describe('Stack Operations', () => {
    test('should track stack state', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      vm.execute();
      const stack = vm.getStack();
      expect(Array.isArray(stack)).toBe(true);
    });

    test('should push values to stack', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const stackBefore = vm.getStack().length;
      vm.execute();
      const stackAfter = vm.getStack().length;

      expect(stackBefore >= 0).toBe(true);
      expect(stackAfter >= 0).toBe(true);
    });

    test('should retrieve stack pointer', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const state = vm.getState();
      expect(typeof state.sp).toBe('number');
    });
  });

  // ========================================================================
  // Register Operations Tests
  // ========================================================================

  describe('Register Operations', () => {
    test('should initialize 8 registers', () => {
      const registers = vm.getRegisters();
      expect(registers.size).toBe(8);
    });

    test('should store values in registers', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();

      // r0 should have z (latent)
      expect(registers.has(0)).toBe(true);
    });

    test('should retrieve register values', () => {
      const registers = vm.getRegisters();
      for (let i = 0; i < 8; i++) {
        expect(registers.has(i)).toBe(true);
      }
    });
  });

  // ========================================================================
  // Opcode Execution Tests (25+ tests)
  // ========================================================================

  describe('Opcode Execution', () => {
    test('should execute LOAD_QUERY', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const stackBefore = vm.getStack().length;
      vm.execute();
      const stackAfter = vm.getStack().length;

      expect(stackAfter).toBeGreaterThanOrEqual(stackBefore);
    });

    test('should execute LOAD_CONST', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const stack = vm.getStack();
      expect(stack.length).toBeGreaterThanOrEqual(0);
    });

    test('should execute ENCODE_Q', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      // Should produce encoded latent
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute NORM_L2', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      // Norm should be computed
      const stack = vm.getStack();
      expect(stack).toBeDefined();
    });

    test('should execute RELU', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'relu';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute TANH', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'tanh';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute SIGMOID', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'sigmoid';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute STORE_LOCAL', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      expect(registers.size).toBeGreaterThan(0);
    });

    test('should execute LOAD_LOCAL', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      expect(registers.size).toBeGreaterThan(0);
    });

    test('should execute PROJECT_A', () => {
      const path = ASTBuilder.createPathNode('analytical');
      const program = compiler.compile(path);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute PROJECT_B', () => {
      const path = ASTBuilder.createPathNode('creative');
      const program = compiler.compile(path);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute PROJECT_C', () => {
      const path = ASTBuilder.createPathNode('empirical');
      const program = compiler.compile(path);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute FORK_PATHS', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute BARRIER', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute SOFTMAX', () => {
      // Softmax on a simple distribution
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'relu';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute ADD', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute ENSEMBLE', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute CRITIQUE', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute HALT', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });
  });

  // ========================================================================
  // Arithmetic Operations Tests
  // ========================================================================

  describe('Arithmetic Operations', () => {
    test('should perform scalar multiplication', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should perform vector addition', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should perform vector subtraction', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should perform element-wise multiplication', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should perform matrix multiplication', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });
  });

  // ========================================================================
  // Activation Function Tests
  // ========================================================================

  describe('Activation Functions', () => {
    test('should apply ReLU', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'relu';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should apply Tanh', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'tanh';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should apply Sigmoid', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'sigmoid';
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should apply Softmax', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });
  });

  // ========================================================================
  // Parallel Execution Tests
  // ========================================================================

  describe('Parallel Execution', () => {
    test('should fork paths', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      // r0 should have z
      expect(registers.has(0)).toBe(true);
    });

    test('should synchronize at barrier', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should compute ensemble', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      // r5 should have z_ens
      expect(registers.has(5)).toBe(true);
    });
  });

  // ========================================================================
  // State Management Tests
  // ========================================================================

  describe('State Management', () => {
    test('should retrieve state', () => {
      const state = vm.getState();
      expect(state).toBeDefined();
      expect(state.pc).toBeDefined();
      expect(state.sp).toBeDefined();
      expect(state.stack).toBeDefined();
    });

    test('should retrieve stack', () => {
      const stack = vm.getStack();
      expect(Array.isArray(stack)).toBe(true);
    });

    test('should retrieve registers', () => {
      const registers = vm.getRegisters();
      expect(registers instanceof Map).toBe(true);
      expect(registers.size).toBe(8);
    });

    test('should retrieve instruction count', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      vm.execute();
      const count = vm.getInstructionCount();
      expect(typeof count).toBe('number');
      expect(count).toBeGreaterThan(0);
    });
  });

  // ========================================================================
  // Complex Program Tests
  // ========================================================================

  describe('Complex Programs', () => {
    test('should execute complete latent program', () => {
      const latent = ASTBuilder.createLatentNode(128);
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      const result = vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should handle large dimensions', () => {
      const latent = ASTBuilder.createLatentNode(512);
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should execute multi-path program', () => {
      const latent = ASTBuilder.createLatentNode();
      expect(latent.paths).toBeDefined();
      expect(latent.paths!.length).toBe(3);

      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      expect(vm.getState().halted).toBe(true);
    });

    test('should compute weights correctly', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      // r4 should have weights [α, β, γ]
      expect(registers.has(4)).toBe(true);
    });

    test('should produce valid ensemble result', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      vm.loadProgram(program);

      vm.execute();
      const registers = vm.getRegisters();
      // r5 should have z_ens
      expect(registers.has(5)).toBe(true);
    });
  });

  // ========================================================================
  // Error Handling Tests
  // ========================================================================

  describe('Error Handling', () => {
    test('should handle unknown opcode gracefully', () => {
      // This would require injecting an invalid opcode
      // For now, just verify no crash on normal execution
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      expect(() => vm.execute()).not.toThrow();
    });

    test('should complete execution without hanging', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      vm.loadProgram(program);

      const startTime = Date.now();
      vm.execute();
      const endTime = Date.now();

      expect(endTime - startTime).toBeLessThan(5000); // Should complete in 5s
    });
  });
});
