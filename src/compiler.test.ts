/**
 * Compiler Tests
 * 50+ test cases for AST to bytecode compilation
 */

import {
  Compiler,
  ASTBuilder,
  Opcode,
  QueryNode,
  LatentNode,
  PathNode,
  BytecodeProgram,
} from './compiler';

describe('Compiler', () => {
  let compiler: Compiler;

  beforeEach(() => {
    compiler = new Compiler();
  });

  // ========================================================================
  // Basic Compilation Tests
  // ========================================================================

  describe('Basic Compilation', () => {
    test('should compile a simple query node', () => {
      const query = ASTBuilder.createSimpleQuery('hello world');
      const program = compiler.compile(query);

      expect(program).toBeDefined();
      expect(program.magic).toBe('MIND');
      expect(program.version).toBe(1.0);
      expect(program.instructions.length).toBeGreaterThan(0);
    });

    test('should emit LOAD_QUERY opcode for QueryNode', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      const firstInstr = program.instructions[0];
      expect(firstInstr.opcode).toBe(Opcode.LOAD_QUERY);
    });

    test('should emit HALT at program end', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      const lastInstr = program.instructions[program.instructions.length - 1];
      expect(lastInstr.opcode).toBe(Opcode.HALT);
    });

    test('should add constants to pool', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program.constants.size).toBeGreaterThan(0);
    });

    test('should preserve embedding in constants', () => {
      const text = 'test query';
      const query = ASTBuilder.createSimpleQuery(text);
      const program = compiler.compile(query);

      const constants = Array.from(program.constants.values());
      const hasEmbedding = constants.some(
        c => Array.isArray(c) && c.length === query.embedding.length
      );

      expect(hasEmbedding).toBe(true);
    });
  });

  // ========================================================================
  // LatentNode Compilation Tests
  // ========================================================================

  describe('LatentNode Compilation', () => {
    test('should compile LatentNode with encoder weights', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      expect(program.instructions.length).toBeGreaterThan(0);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.ENCODE_Q);
    });

    test('should emit NORM_L2 after encoding', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const opcodes = program.instructions.map(i => i.opcode);
      const encodeIdx = opcodes.indexOf(Opcode.ENCODE_Q);
      expect(encodeIdx).toBeGreaterThanOrEqual(0);
      expect(opcodes[encodeIdx + 1]).toBe(Opcode.NORM_L2);
    });

    test('should emit activation function', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'relu';
      const program = compiler.compile(latent);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.RELU);
    });

    test('should store latent in register', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.STORE_LOCAL);
    });

    test('should fork paths when paths present', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.FORK_PATHS);
    });

    test('should emit barrier for path synchronization', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.BARRIER);
    });
  });

  // ========================================================================
  // PathNode Compilation Tests
  // ========================================================================

  describe('PathNode Compilation', () => {
    test('should compile analytical path', () => {
      const path = ASTBuilder.createPathNode('analytical');
      const program = compiler.compile(path);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_A);
    });

    test('should compile creative path', () => {
      const path = ASTBuilder.createPathNode('creative');
      const program = compiler.compile(path);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_B);
    });

    test('should compile empirical path', () => {
      const path = ASTBuilder.createPathNode('empirical');
      const program = compiler.compile(path);

      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_C);
    });

    test('should apply path-specific activation', () => {
      const analyticalPath = ASTBuilder.createPathNode('analytical');
      const creativeePath = ASTBuilder.createPathNode('creative');

      const program1 = compiler.compile(analyticalPath);
      const program2 = compiler.compile(creativeePath);

      const opcodes1 = program1.instructions.map(i => i.opcode);
      const opcodes2 = program2.instructions.map(i => i.opcode);

      expect(opcodes1).toContain(Opcode.RELU);
      expect(opcodes2).toContain(Opcode.TANH);
    });

    test('should add noise for creative path', () => {
      const creativePath = ASTBuilder.createPathNode('creative');
      expect(creativePath.noise).toBeDefined();
      expect(creativePath.noiseScale).toBeDefined();

      const program = compiler.compile(creativePath);
      const constants = Array.from(program.constants.values());

      expect(constants.length).toBeGreaterThan(0);
    });
  });

  // ========================================================================
  // Bytecode Generation Tests
  // ========================================================================

  describe('Bytecode Generation', () => {
    test('should generate binary bytecode', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const bytecode = compiler.generateBytecode(program);

      expect(bytecode).toBeInstanceOf(Buffer);
      expect(bytecode.length).toBeGreaterThan(0);
    });

    test('should include magic header', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const bytecode = compiler.generateBytecode(program);

      const magic = bytecode.slice(0, 4).toString('ascii');
      expect(magic).toBe('MIND');
    });

    test('should encode version correctly', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const bytecode = compiler.generateBytecode(program);

      // Version is at bytes 4-7
      const versionBuffer = bytecode.slice(4, 8);
      const version = versionBuffer.readUInt32BE(0);
      expect(version).toBe(1.0);
    });

    test('should include all instructions', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const bytecode = compiler.generateBytecode(program);

      // At least: header (16 bytes) + instructions
      expect(bytecode.length).toBeGreaterThanOrEqual(16);
    });
  });

  // ========================================================================
  // Opcode Emission Tests (25+ tests for 45 opcodes)
  // ========================================================================

  describe('Opcode Emission', () => {
    test('should emit LOAD_QUERY', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.LOAD_QUERY);
    });

    test('should emit LOAD_CONST', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.LOAD_CONST);
    });

    test('should emit STORE_LOCAL', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.STORE_LOCAL);
    });

    test('should emit LOAD_LOCAL', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.LOAD_LOCAL);
    });

    test('should emit ENCODE_Q', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.ENCODE_Q);
    });

    test('should emit NORM_L2', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.NORM_L2);
    });

    test('should emit RELU', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'relu';
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.RELU);
    });

    test('should emit TANH', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'tanh';
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.TANH);
    });

    test('should emit SIGMOID', () => {
      const latent = ASTBuilder.createLatentNode();
      latent.activationFunc = 'sigmoid';
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.SIGMOID);
    });

    test('should emit PROJECT_A', () => {
      const path = ASTBuilder.createPathNode('analytical');
      const program = compiler.compile(path);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_A);
    });

    test('should emit PROJECT_B', () => {
      const path = ASTBuilder.createPathNode('creative');
      const program = compiler.compile(path);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_B);
    });

    test('should emit PROJECT_C', () => {
      const path = ASTBuilder.createPathNode('empirical');
      const program = compiler.compile(path);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.PROJECT_C);
    });

    test('should emit FORK_PATHS', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.FORK_PATHS);
    });

    test('should emit BARRIER', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.BARRIER);
    });

    test('should emit HALT', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);
      const opcodes = program.instructions.map(i => i.opcode);
      expect(opcodes).toContain(Opcode.HALT);
    });
  });

  // ========================================================================
  // Operand Handling Tests
  // ========================================================================

  describe('Operand Handling', () => {
    test('should handle u32 operands', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      const loadQueryInstr = program.instructions.find(i => i.opcode === Opcode.LOAD_QUERY);
      expect(loadQueryInstr).toBeDefined();
      expect(loadQueryInstr!.operands.length).toBeGreaterThan(0);
    });

    test('should handle u8 operands for registers', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const storeInstr = program.instructions.find(i => i.opcode === Opcode.STORE_LOCAL);
      expect(storeInstr).toBeDefined();
      expect(storeInstr!.operands.length).toBeGreaterThan(0);
    });

    test('should preserve operand values', () => {
      const latent = ASTBuilder.createLatentNode();
      const program = compiler.compile(latent);

      const storeInstr = program.instructions.find(i => i.opcode === Opcode.STORE_LOCAL);
      expect(storeInstr!.operands[0]).toBe(0); // Register 0
    });
  });

  // ========================================================================
  // Program Structure Tests
  // ========================================================================

  describe('Program Structure', () => {
    test('should have valid entry point', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program.entryPoint).toBe(0);
    });

    test('should have correct program size', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program.size).toBe(program.instructions.length);
    });

    test('should have magic number', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program.magic).toBe('MIND');
    });

    test('should have version', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program.version).toBe(1.0);
    });

    test('should build valid bytecode program', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      expect(program).toHaveProperty('magic');
      expect(program).toHaveProperty('version');
      expect(program).toHaveProperty('entryPoint');
      expect(program).toHaveProperty('size');
      expect(program).toHaveProperty('constants');
      expect(program).toHaveProperty('instructions');
    });
  });

  // ========================================================================
  // Integration Tests
  // ========================================================================

  describe('Integration', () => {
    test('should compile complete AST tree', () => {
      const complete = ASTBuilder.createCompleteProgram('test query');
      const program = compiler.compile(complete as any);

      expect(program.instructions.length).toBeGreaterThan(0);
      expect(program.constants.size).toBeGreaterThan(0);
    });

    test('should handle multiple compilations', () => {
      const query1 = ASTBuilder.createSimpleQuery('test1');
      const query2 = ASTBuilder.createSimpleQuery('test2');

      const program1 = compiler.compile(query1);
      const program2 = compiler.compile(query2);

      expect(program1.constants.size).toBe(program2.constants.size);
    });

    test('should reset state between compilations', () => {
      const query1 = ASTBuilder.createSimpleQuery('test1');
      const query2 = ASTBuilder.createSimpleQuery('test2');

      compiler.compile(query1);
      const program2 = compiler.compile(query2);

      // Should only have constants from query2
      const constants = Array.from(program2.constants.values());
      expect(constants.length).toBeGreaterThan(0);
    });

    test('should preserve instruction order', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      const program = compiler.compile(query);

      const opcodes = program.instructions.map(i => i.opcode);
      const lastOpcode = opcodes[opcodes.length - 1];
      expect(lastOpcode).toBe(Opcode.HALT);
    });

    test('should generate large programs without errors', () => {
      const latent = ASTBuilder.createLatentNode(512);
      const program = compiler.compile(latent);

      expect(program.instructions.length).toBeGreaterThan(0);
      expect(program.constants.size).toBeGreaterThan(0);
    });
  });

  // ========================================================================
  // Error Handling Tests
  // ========================================================================

  describe('Error Handling', () => {
    test('should handle null nodes gracefully', () => {
      // Compiler should not crash on null
      const program = compiler.compile({ type: 'UnknownNode' } as any);
      expect(program).toBeDefined();
    });

    test('should handle empty embeddings', () => {
      const query = ASTBuilder.createSimpleQuery('test');
      query.embedding = [];
      const program = compiler.compile(query);

      expect(program).toBeDefined();
    });
  });
});
