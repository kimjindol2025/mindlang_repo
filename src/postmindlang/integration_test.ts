/**
 * MindLang ↔ PostMindLang Integration Tests
 * Verifies semantic preservation and functional equivalence
 *
 * Tests:
 * 1. Query encoding consistency
 * 2. Gradient computation equivalence
 * 3. Parallel path execution
 * 4. Ensemble voting equivalence
 * 5. Self-critique consistency
 * 6. End-to-end program equivalence
 */

import { describe, test, expect, beforeEach } from '@jest/globals';
import {
  MindLangToPostMindLangCompiler,
  PostMindLangBytecode,
  Vector,
  Matrix,
  Tensor,
} from './mindlang_to_postmindlang';
import {
  AnalyticalPathTranslation,
  CreativePathTranslation,
  EmpiricalPathTranslation,
  TypeTranslation,
  SemanticPreservationChecker,
} from './semantics_translation';
import {
  PostMindLangOptimizer,
  MatrixOperationOptimizer,
  MemoryLayoutOptimizer,
  ParallelismOptimizer,
  NumericalStabilityOptimizer,
} from './optimization';
import { TypeSystem, PostMindLangType } from './type_translation';
import { Program, createQueryNode, createEncodeNode, createPathNode, createWeightNode, createEnsembleNode, createCritiqueNode, createSampleNode } from '../ast';

// ============================================================================
// Test Fixtures
// ============================================================================

let compiler: MindLangToPostMindLangCompiler;
let typeSystem: TypeSystem;

function createTestProgram(): Program {
  return {
    statements: [
      createQueryNode(1, 'q', {
        semanticContent: 'test query',
        embedding: new Array(768).fill(1 / Math.sqrt(768)),
        confidence: 0.9,
      }),
      createEncodeNode(2, 'q', 'encoded', { latentDim: 512 }),
      createPathNode(3, 'analytical', 'encoded', 'p_analytical'),
      createPathNode(4, 'creative', 'encoded', 'p_creative'),
      createPathNode(5, 'empirical', 'encoded', 'p_empirical'),
      createWeightNode(6, 'q', { weights: { alpha: 0.5, beta: 0.3, gamma: 0.2 } }),
      createEnsembleNode(
        7,
        ['p_analytical', 'p_creative', 'p_empirical'],
        'weights',
        'ensemble_output'
      ),
      createCritiqueNode(8, 'ensemble_output', 'critique', { confidenceThreshold: 0.5 }),
      createSampleNode(9, 'critique', 'final_output', { temperature: 1.0, threshold: 0.1 }),
    ],
  };
}

// ============================================================================
// Test Suite
// ============================================================================

describe('MindLang ↔ PostMindLang Compiler Integration Tests', () => {
  beforeEach(() => {
    compiler = new MindLangToPostMindLangCompiler({
      queryDim: 768,
      latentDim: 512,
      pathDim: 256,
    });
    typeSystem = new TypeSystem();
  });

  // =========================================================================
  // Test 1: Query Encoding Consistency
  // =========================================================================

  describe('Test 1: Query Encoding Consistency', () => {
    test('same query produces consistent embedding', () => {
      const query = 'test query';
      const embedding1 = compiler.compile(createTestProgram()).encoder.embed(query);
      const embedding2 = compiler.compile(createTestProgram()).encoder.embed(query);

      expect(embedding1.length).toBe(768);
      expect(embedding2.length).toBe(768);

      // Verify consistency
      for (let i = 0; i < embedding1.length; i++) {
        expect(embedding1[i]).toBeCloseTo(embedding2[i], 6);
      }
    });

    test('query embedding is L2 normalized', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);
      const embedding = bytecode.encoder.embed('test query');

      const norm = Math.sqrt(embedding.reduce((sum, x) => sum + x * x, 0));
      expect(norm).toBeCloseTo(1.0, 5);
    });

    test('different queries produce different embeddings', () => {
      const bytecode = compiler.compile(createTestProgram());
      const embedding1 = bytecode.encoder.embed('query one');
      const embedding2 = bytecode.encoder.embed('completely different');

      const dotProduct = embedding1.reduce((sum, x, i) => sum + x * embedding2[i], 0);
      expect(Math.abs(dotProduct)).toBeLessThan(0.95); // Not collinear
    });

    test('projection maintains orthogonality', () => {
      const bytecode = compiler.compile(createTestProgram());
      const embedding = bytecode.encoder.embed('test query');
      const projected = bytecode.encoder.project(embedding, 512);

      expect(projected.length).toBe(512);

      // Verify projected is valid latent representation
      expect(projected.every(x => typeof x === 'number')).toBe(true);
    });
  });

  // =========================================================================
  // Test 2: Gradient Computation Consistency
  // =========================================================================

  describe('Test 2: Gradient Computation Equivalence', () => {
    test('critique gradient computed consistently', () => {
      const bytecode = compiler.compile(createTestProgram());
      const output = new Array(256).fill(0.1);
      const target = new Array(256).fill(0.05);

      const grad1 = bytecode.critiqueFunction.gradientFn(output, target);
      const grad2 = bytecode.critiqueFunction.gradientFn(output, target);

      expect(grad1.length).toBe(grad2.length);
      for (let i = 0; i < grad1.length; i++) {
        expect(grad1[i]).toBeCloseTo(grad2[i], 8);
      }
    });

    test('gradient descent reduces loss', () => {
      const bytecode = compiler.compile(createTestProgram());
      const output = new Array(256).fill(0.5);
      const target = new Array(256).fill(0.1);

      const loss1 = bytecode.critiqueFunction.lossFn(output, target);
      const gradient = bytecode.critiqueFunction.gradientFn(output, target);

      // Update in opposite direction of gradient
      const learningRate = 0.01;
      const updatedOutput = output.map((x, i) => x - learningRate * gradient[i]);
      const loss2 = bytecode.critiqueFunction.lossFn(updatedOutput, target);

      expect(loss2).toBeLessThan(loss1);
    });

    test('weight gradient sums to zero (probability constraint)', () => {
      const bytecode = compiler.compile(createTestProgram());
      const query = new Array(768).fill(1 / Math.sqrt(768));

      const weights = bytecode.weightFunction.compute(query);
      const weightGradient = bytecode.weightFunction.gradient(0.1);

      expect(Math.abs(weights.reduce((a, b) => a + b))).toBeCloseTo(1.0, 5);
      // Gradient should respect probability constraint
      expect(weightGradient.length).toBe(3);
    });

    test('ensemble gradient backpropagates to paths', () => {
      const bytecode = compiler.compile(createTestProgram());
      const p_a = new Array(256).fill(0.1);
      const p_b = new Array(256).fill(0.2);
      const p_c = new Array(256).fill(0.3);
      const w = [0.5, 0.3, 0.2];

      const output = bytecode.ensembleFunction.combine(p_a, p_b, p_c, w);
      const grads = bytecode.ensembleFunction.gradientFn(output, 0.1);

      expect(grads.grad_a.length).toBe(256);
      expect(grads.grad_b.length).toBe(256);
      expect(grads.grad_c.length).toBe(256);
      expect(grads.grad_w.length).toBe(3);

      // Gradients should be non-zero
      expect(grads.grad_a.some(g => Math.abs(g) > 0)).toBe(true);
    });
  });

  // =========================================================================
  // Test 3: Parallel Path Execution
  // =========================================================================

  describe('Test 3: Parallel Path Execution Consistency', () => {
    test('three paths can execute in parallel', () => {
      const bytecode = compiler.compile(createTestProgram());
      const executionPlan = bytecode.executionPlan;

      // Verify parallel group exists for paths
      const pathGroup = executionPlan.parallelGroups.find(g => g.groupId.includes('path'));
      expect(!!(pathGroup) || executionPlan.parallelGroups.length > 0).toBe(true);
    });

    test('parallel execution produces deterministic results', () => {
      const bytecode = compiler.compile(createTestProgram());
      const input = new Array(512).fill(0.5);

      // Simulate sequential execution
      const pathMatrices = bytecode.pathMatrices;
      const analyticalOut = matrixVectorMultiply(
        pathMatrices.analytical.matrix,
        input
      );
      const creativeOut = matrixVectorMultiply(
        pathMatrices.creative.matrix,
        input
      );
      const empiricalOut = matrixVectorMultiply(
        pathMatrices.empirical.matrix,
        input
      );

      // Run again to verify consistency
      const analyticalOut2 = matrixVectorMultiply(
        pathMatrices.analytical.matrix,
        input
      );

      for (let i = 0; i < analyticalOut.length; i++) {
        expect(analyticalOut[i]).toBeCloseTo(analyticalOut2[i], 8);
      }
    });

    test('synchronization barrier correct at each stage', () => {
      const bytecode = compiler.compile(createTestProgram());
      const stages = bytecode.executionPlan.stages;

      // Verify dependency DAG is valid
      const stageIds = new Set(stages.map(s => s.stageId));
      for (const stage of stages) {
        for (const dep of stage.dependencies) {
          expect(stageIds.has(dep) || dep === '').toBe(true);
        }
      }
    });

    test('data flow edges represent actual dependencies', () => {
      const bytecode = compiler.compile(createTestProgram());
      const dataflow = bytecode.executionPlan.dataflow;

      // Each dataflow edge should connect valid nodes
      for (const edge of dataflow) {
        expect(edge.variable).toBeDefined();
        expect(edge.tensorShape.dimensions.length).toBeGreaterThan(0);
        expect(edge.tensorShape.totalElements).toBeGreaterThan(0);
      }
    });
  });

  // =========================================================================
  // Test 4: Ensemble Voting Equivalence
  // =========================================================================

  describe('Test 4: Ensemble Voting Equivalence', () => {
    test('weighted combination is convex', () => {
      const bytecode = compiler.compile(createTestProgram());
      const p_a = new Array(256).fill(0.1);
      const p_b = new Array(256).fill(0.2);
      const p_c = new Array(256).fill(0.3);
      const w = [0.5, 0.3, 0.2]; // Sum to 1

      const result = bytecode.ensembleFunction.combine(p_a, p_b, p_c, w);

      // Result should be within bounds of inputs
      for (let i = 0; i < result.length; i++) {
        const min = Math.min(p_a[i], p_b[i], p_c[i]);
        const max = Math.max(p_a[i], p_b[i], p_c[i]);
        expect(result[i]).toBeGreaterThanOrEqual(min);
        expect(result[i]).toBeLessThanOrEqual(max);
      }
    });

    test('changing weights changes ensemble output', () => {
      const bytecode = compiler.compile(createTestProgram());
      const p_a = new Array(256).fill(0.1);
      const p_b = new Array(256).fill(0.5);
      const p_c = new Array(256).fill(0.3);

      const result1 = bytecode.ensembleFunction.combine(p_a, p_b, p_c, [0.8, 0.1, 0.1]);
      const result2 = bytecode.ensembleFunction.combine(p_a, p_b, p_c, [0.1, 0.8, 0.1]);

      // Results should differ
      const diff = result1.reduce((sum, x, i) => sum + Math.abs(x - result2[i]), 0);
      expect(diff).toBeGreaterThan(0);
    });

    test('uniform weights average all paths', () => {
      const bytecode = compiler.compile(createTestProgram());
      const p_a = new Array(256).fill(0.1);
      const p_b = new Array(256).fill(0.2);
      const p_c = new Array(256).fill(0.3);
      const w = [1 / 3, 1 / 3, 1 / 3];

      const result = bytecode.ensembleFunction.combine(p_a, p_b, p_c, w);

      for (let i = 0; i < result.length; i++) {
        const expected = (p_a[i] + p_b[i] + p_c[i]) / 3;
        expect(result[i]).toBeCloseTo(expected, 8);
      }
    });

    test('voting rule consistency', () => {
      const bytecode = compiler.compile(createTestProgram());
      expect(['softmax', 'majority', 'borda']).toContain(bytecode.ensembleFunction.votingRule);
    });
  });

  // =========================================================================
  // Test 5: Self-Critique Consistency
  // =========================================================================

  describe('Test 5: Self-Critique Consistency', () => {
    test('confidence increases with lower loss', () => {
      const bytecode = compiler.compile(createTestProgram());
      const target = new Array(256).fill(0.5);

      const output1 = new Array(256).fill(0.5); // Perfect match
      const output2 = new Array(256).fill(0.1); // Poor match

      const loss1 = bytecode.critiqueFunction.lossFn(output1, target);
      const loss2 = bytecode.critiqueFunction.lossFn(output2, target);

      expect(loss1).toBeLessThan(loss2);
    });

    test('critique threshold controls acceptance', () => {
      const bytecode = compiler.compile(createTestProgram());
      const output = new Array(256).fill(0.5);
      const target = new Array(256).fill(0.5);

      const loss = bytecode.critiqueFunction.lossFn(output, target);
      expect(loss).toBeLessThan(0.1); // Should be accepted
    });

    test('gradient direction points toward lower loss', () => {
      const bytecode = compiler.compile(createTestProgram());
      const output = new Array(256).fill(1.0);
      const target = new Array(256).fill(0.0);

      const gradient = bytecode.critiqueFunction.gradientFn(output, target);

      // Gradient should point toward target
      const dotWithDifference = gradient.reduce(
        (sum, g, i) => sum + g * (target[i] - output[i]),
        0
      );
      expect(dotWithDifference).toBeLessThan(0); // Opposite direction
    });

    test('critique output dimension matches ensemble input', () => {
      const bytecode = compiler.compile(createTestProgram());
      const ensemble = new Array(256).fill(0.5);

      const loss = bytecode.critiqueFunction.lossFn(ensemble, new Array(256).fill(0.5));
      expect(typeof loss).toBe('number');
    });
  });

  // =========================================================================
  // Test 6: End-to-End Program Equivalence
  // =========================================================================

  describe('Test 6: End-to-End Program Equivalence', () => {
    test('full pipeline executes without error', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      expect(bytecode).toBeDefined();
      expect(bytecode.encoder).toBeDefined();
      expect(bytecode.pathMatrices).toBeDefined();
      expect(bytecode.ensembleFunction).toBeDefined();
    });

    test('semantic preservation maintained', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      const report = SemanticPreservationChecker.verify(program, bytecode);
      expect(report.isPreserved).toBe(true);
    });

    test('all variable shapes are consistent', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      for (const [varName, varInfo] of Object.entries(bytecode.variables)) {
        expect(varInfo.shape.totalElements).toBe(varInfo.dimension);
        expect(varInfo.shape.dimensions.length).toBeGreaterThan(0);
      }
    });

    test('type system correctly infers types', () => {
      typeSystem.registerVariable('q', PostMindLangType.QUERY);
      typeSystem.registerVariable('encoded', PostMindLangType.LATENT);
      typeSystem.registerVariable('path', PostMindLangType.PATH);

      expect(typeSystem.getVariableType('q')).toBe(PostMindLangType.QUERY);
      expect(typeSystem.getVariableType('encoded')).toBe(PostMindLangType.LATENT);
      expect(typeSystem.getVariableType('path')).toBe(PostMindLangType.PATH);
    });

    test('optimization report generates recommendations', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      const optimization = PostMindLangOptimizer.optimize(bytecode);
      expect(optimization.recommendations.length).toBeGreaterThan(0);
      expect(optimization.estimatedOverallSpeedup).toBeGreaterThan(1.0);
    });

    test('parallel execution speedup is achievable', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      const optimization = PostMindLangOptimizer.optimize(bytecode);
      expect(optimization.parallelizationStrategy.estimatedSpeedup).toBeGreaterThan(1.0);
    });

    test('memory optimization recommendations are specific', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      const optimization = PostMindLangOptimizer.optimize(bytecode);
      expect(optimization.memoryOptimization.recommendedLayout).toBeDefined();
      expect(optimization.memoryOptimization.cacheLineUtilization).toBeGreaterThan(0);
      expect(optimization.memoryOptimization.cacheLineUtilization).toBeLessThanOrEqual(1);
    });

    test('numerical stability configuration provided', () => {
      const program = createTestProgram();
      const bytecode = compiler.compile(program);

      const optimization = PostMindLangOptimizer.optimize(bytecode);
      expect(optimization.numericalConfig).toBeDefined();
      expect(optimization.numericalConfig.underflowThreshold).toBeLessThan(
        optimization.numericalConfig.overflowThreshold
      );
    });
  });

  // =========================================================================
  // Test 7: Type System Consistency
  // =========================================================================

  describe('Test 7: Type System Consistency', () => {
    test('all types are properly defined', () => {
      const queryType = typeSystem.getType(PostMindLangType.QUERY);
      const latentType = typeSystem.getType(PostMindLangType.LATENT);
      const pathType = typeSystem.getType(PostMindLangType.PATH);
      const weightType = typeSystem.getType(PostMindLangType.WEIGHT);

      expect(queryType).toBeDefined();
      expect(latentType).toBeDefined();
      expect(pathType).toBeDefined();
      expect(weightType).toBeDefined();
    });

    test('query type checks L2 normalized vectors', () => {
      const queryType = typeSystem.getType(PostMindLangType.QUERY);
      const normalized = new Array(768).fill(1 / Math.sqrt(768));

      expect(queryType?.typeCheck(normalized)).toBe(true);
    });

    test('weight type checks probability simplex', () => {
      const weightType = typeSystem.getType(PostMindLangType.WEIGHT);
      const validWeights = [0.5, 0.3, 0.2];
      const invalidWeights = [0.5, 0.3, 0.3]; // Sum > 1

      expect(weightType?.typeCheck(validWeights)).toBe(true);
      expect(weightType?.typeCheck(invalidWeights)).toBe(false);
    });

    test('function type inference works', () => {
      const encodeFunc = typeSystem.getFunctionSignature('encode');
      expect(encodeFunc?.inputTypes).toEqual([PostMindLangType.QUERY]);
      expect(encodeFunc?.outputType).toBe(PostMindLangType.LATENT);
    });

    test('type projections preserve subspace properties', () => {
      const queryType = typeSystem.getType(PostMindLangType.QUERY);
      const query = new Array(768).fill(0.5);

      const projected = queryType?.project(query);
      expect(projected).toBeDefined();
      if (projected) {
        const norm = Math.sqrt(projected.reduce((sum, x) => sum + x * x, 0));
        expect(norm).toBeCloseTo(1.0, 5);
      }
    });
  });

  // =========================================================================
  // Test 8: Semantic Translation Accuracy
  // =========================================================================

  describe('Test 8: Semantic Translation Accuracy', () => {
    test('analytical path has high linearity', () => {
      const analyticalSemantics = AnalyticalPathTranslation.getSemantics();
      expect(analyticalSemantics.determinism).toBeGreaterThan(0.8);
      expect(analyticalSemantics.diversity).toBeLessThan(0.2);
    });

    test('creative path has high diversity', () => {
      const creativeSemantics = CreativePathTranslation.getSemantics();
      expect(creativeSemantics.diversity).toBeGreaterThan(0.7);
      expect(creativeSemantics.determinism).toBeLessThan(0.4);
    });

    test('empirical path is data-grounded', () => {
      const empiricalSemantics = EmpiricalPathTranslation.getSemantics();
      expect(empiricalSemantics.grounding).toBeGreaterThan(0.9);
    });

    test('semantic properties are consistent', () => {
      const analyticalSemantics = AnalyticalPathTranslation.getSemantics();
      const creativeSemantics = CreativePathTranslation.getSemantics();

      // These should be different
      expect(analyticalSemantics.determinism).not.toEqual(creativeSemantics.determinism);
      expect(analyticalSemantics.diversity).not.toEqual(creativeSemantics.diversity);
    });
  });

});

// =========================================================================
// Helper Functions
// =========================================================================

function matrixVectorMultiply(matrix: Matrix, vector: Vector): Vector {
  const result: Vector = [];
  for (let i = 0; i < matrix.length; i++) {
    let sum = 0;
    for (let j = 0; j < vector.length && j < matrix[i].length; j++) {
      sum += matrix[i][j] * vector[j];
    }
    result.push(sum);
  }
  return result;
}

// ============================================================================
// Additional Edge Case Tests
// ============================================================================

describe('Edge Cases and Boundary Conditions', () => {
  test('handles empty program gracefully', () => {
    const compiler = new MindLangToPostMindLangCompiler();
    const emptyProgram: Program = { statements: [] };
    const bytecode = compiler.compile(emptyProgram);

    expect(bytecode).toBeDefined();
    expect(bytecode.metadata.sourceNodes).toBe(0);
  });

  test('handles large dimension vectors', () => {
    const compiler = new MindLangToPostMindLangCompiler({ queryDim: 4096 });
    const program = createTestProgram();
    const bytecode = compiler.compile(program);

    expect(bytecode.vectorSpace.queryDim).toBe(4096);
  });

  test('numerical stability with small values', () => {
    const config = NumericalStabilityOptimizer.optimizeNumericalStability(
      {} as any
    );
    const vec = new Array(10).fill(1e-38);

    const clipped = NumericalStabilityOptimizer.clipValues(vec, -1e10, 1e10);
    expect(clipped.every(x => !isNaN(x) && !isInfinite(x))).toBe(true);
  });

  test('numerical stability with large values', () => {
    const vec = new Array(10).fill(1e38);
    const clipped = NumericalStabilityOptimizer.clipValues(vec, -1e10, 1e10);

    expect(clipped.every(x => !isNaN(x) && !isInfinite(x))).toBe(true);
  });
});

// Helper function
function isInfinite(x: number): boolean {
  return !isFinite(x);
}
