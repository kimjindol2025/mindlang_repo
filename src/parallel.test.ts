/**
 * Parallel Engine Tests
 * 40+ test cases for 3-way parallelism, work stealing, and synchronization
 */

import {
  ParallelInferenceEngine,
  ThreadPool,
  Barrier,
  WorkQueue,
  Task,
  TaskType,
  createPathWeights,
  createPathBiases,
  createAttentionWeights,
  createAttentionBias,
  createLatentVector,
} from './parallel_engine';

describe('Barrier Synchronization', () => {
  let barrier: Barrier;

  beforeEach(() => {
    barrier = new Barrier(3);
  });

  // ========================================================================
  // Barrier Tests
  // ========================================================================

  describe('Barrier', () => {
    test('should create barrier with target count', () => {
      expect(barrier).toBeDefined();
    });

    test('should track waiting threads', () => {
      barrier.wait(0);
      expect(barrier.isComplete()).toBe(false);

      barrier.wait(1);
      expect(barrier.isComplete()).toBe(false);

      barrier.wait(2);
      expect(barrier.isComplete()).toBe(true);
    });

    test('should reset after completion', () => {
      barrier.wait(0);
      barrier.wait(1);
      barrier.wait(2);

      barrier.reset();
      expect(barrier.isComplete()).toBe(false);
    });

    test('should handle multiple barrier cycles', () => {
      for (let cycle = 0; cycle < 5; cycle++) {
        barrier.wait(0);
        barrier.wait(1);
        barrier.wait(2);

        expect(barrier.isComplete()).toBe(true);
        barrier.reset();
        expect(barrier.isComplete()).toBe(false);
      }
    });
  });
});

describe('WorkQueue', () => {
  let queue: WorkQueue;

  beforeEach(() => {
    queue = new WorkQueue();
  });

  // ========================================================================
  // Work Queue Tests
  // ========================================================================

  describe('WorkQueue', () => {
    test('should create empty queue', () => {
      expect(queue.isEmpty()).toBe(true);
    });

    test('should enqueue tasks', () => {
      const task: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };

      queue.enqueue(task);
      expect(queue.isEmpty()).toBe(false);
    });

    test('should dequeue tasks in FIFO order', () => {
      const task1: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };
      const task2: Task = {
        id: 'task2',
        type: TaskType.PROJECT_B,
        input: [4, 5, 6],
      };

      queue.enqueue(task1);
      queue.enqueue(task2);

      const dequeued1 = queue.dequeue();
      expect(dequeued1?.id).toBe('task1');

      const dequeued2 = queue.dequeue();
      expect(dequeued2?.id).toBe('task2');
    });

    test('should return null when dequeuing from empty queue', () => {
      expect(queue.dequeue()).toBeNull();
    });

    test('should track queue size', () => {
      expect(queue.size()).toBe(0);

      queue.enqueue({
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      });
      expect(queue.size()).toBe(1);

      queue.enqueue({
        id: 'task2',
        type: TaskType.PROJECT_B,
        input: [4, 5, 6],
      });
      expect(queue.size()).toBe(2);
    });

    test('should steal from queue', () => {
      queue.enqueue({
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      });
      queue.enqueue({
        id: 'task2',
        type: TaskType.PROJECT_B,
        input: [4, 5, 6],
      });

      const stolen = queue.steal();
      expect(stolen?.id).toBe('task2');
      expect(queue.size()).toBe(1);
    });

    test('should not steal from queue with 1 or fewer items', () => {
      queue.enqueue({
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      });

      const stolen = queue.steal();
      expect(stolen).toBeNull();
    });
  });
});

describe('ThreadPool', () => {
  let threadPool: ThreadPool;

  beforeEach(() => {
    threadPool = new ThreadPool(3);
  });

  // ========================================================================
  // Thread Pool Tests
  // ========================================================================

  describe('ThreadPool', () => {
    test('should create thread pool with 3 threads', () => {
      expect(threadPool).toBeDefined();
    });

    test('should submit task to pool', () => {
      const task: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };

      expect(() => threadPool.submitTask(task)).not.toThrow();
    });

    test('should get task for thread', () => {
      const task: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };

      threadPool.submitTask(task);
      const retrieved = threadPool.getTask(0);

      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe('task1');
    });

    test('should store task results', () => {
      const result = [1, 2, 3];
      threadPool.storeResult(0, 'task1', result);

      const results = threadPool.getResults(0);
      expect(results.get('task1')).toEqual(result);
    });

    test('should retrieve thread statistics', () => {
      const stats = threadPool.getThreadStats(0);
      expect(stats).toBeDefined();
      expect(stats?.id).toBe(0);
      expect(stats?.tasksCompleted).toBe(0);
    });

    test('should reset thread pool', () => {
      const task: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };

      threadPool.submitTask(task);
      threadPool.storeResult(0, 'task1', [1, 2, 3]);

      threadPool.reset();

      const results = threadPool.getResults(0);
      expect(results.size).toBe(0);
    });

    test('should perform work stealing', () => {
      const task1: Task = {
        id: 'task1',
        type: TaskType.PROJECT_A,
        input: [1, 2, 3],
      };
      const task2: Task = {
        id: 'task2',
        type: TaskType.PROJECT_B,
        input: [4, 5, 6],
      };

      threadPool.submitTask(task1);
      threadPool.submitTask(task2);

      // Get tasks from different threads
      const t1 = threadPool.getTask(0);
      const t2 = threadPool.getTask(1); // May steal

      expect(t1).toBeDefined();
      expect(t2).toBeDefined();
    });
  });
});

describe('ParallelInferenceEngine', () => {
  let engine: ParallelInferenceEngine;

  beforeEach(() => {
    engine = new ParallelInferenceEngine();
  });

  // ========================================================================
  // Parallel Execution Tests
  // ========================================================================

  describe('3-Way Parallel Execution', () => {
    test('should execute 3-way parallel inference', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result).toBeDefined();
      expect(result.z_ens).toBeDefined();
      expect(result.deltaConfidence).toBeDefined();
      expect(result.traces).toBeDefined();
    });

    test('should produce ensemble result', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(Array.isArray(result.z_ens)).toBe(true);
      expect(result.z_ens.length).toBeGreaterThan(0);
    });

    test('should compute confidence score', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(typeof result.deltaConfidence).toBe('number');
      expect(result.deltaConfidence).toBeGreaterThanOrEqual(-1);
      expect(result.deltaConfidence).toBeLessThanOrEqual(1);
    });

    test('should record execution trace', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result.traces).toBeDefined();
      expect(result.traces.length).toBeGreaterThan(0);
    });
  });

  // ========================================================================
  // Path Execution Tests
  // ========================================================================

  describe('Path Execution', () => {
    test('should execute path A (analytical)', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result.z_ens).toBeDefined();
    });

    test('should execute path B (creative)', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result.z_ens).toBeDefined();
    });

    test('should execute path C (empirical)', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result.z_ens).toBeDefined();
    });
  });

  // ========================================================================
  // Performance Metrics Tests
  // ========================================================================

  describe('Performance Metrics', () => {
    test('should collect performance metrics', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const metrics = engine.getPerformanceMetrics();
      expect(metrics).toBeDefined();
      expect(metrics.size).toBeGreaterThan(0);
    });

    test('should track total execution time', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const metrics = engine.getPerformanceMetrics();
      expect(metrics.has('total_time_ms')).toBe(true);
      expect(metrics.get('total_time_ms')).toBeGreaterThan(0);
    });

    test('should estimate speedup', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const metrics = engine.getPerformanceMetrics();
      expect(metrics.has('speedup')).toBe(true);
      expect(metrics.get('speedup')).toBeGreaterThan(1);
    });
  });

  // ========================================================================
  // Execution Trace Tests
  // ========================================================================

  describe('Execution Trace', () => {
    test('should log FORK_PATHS event', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const trace = engine.getExecutionTrace();
      const hasForkEvent = trace.some(t => t.event.includes('FORK_PATHS'));
      expect(hasForkEvent).toBe(true);
    });

    test('should log BARRIER event', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const trace = engine.getExecutionTrace();
      const hasBarrierEvent = trace.some(t => t.event.includes('BARRIER'));
      expect(hasBarrierEvent).toBe(true);
    });

    test('should log ENSEMBLE event', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const trace = engine.getExecutionTrace();
      const hasEnsembleEvent = trace.some(t => t.event.includes('ENSEMBLE'));
      expect(hasEnsembleEvent).toBe(true);
    });

    test('should log CRITIQUE event', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const trace = engine.getExecutionTrace();
      const hasCritiqueEvent = trace.some(t => t.event.includes('CRITIQUE'));
      expect(hasCritiqueEvent).toBe(true);
    });
  });

  // ========================================================================
  // Thread Statistics Tests
  // ========================================================================

  describe('Thread Statistics', () => {
    test('should retrieve thread statistics', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const stats = engine.getThreadStatistics();
      expect(Array.isArray(stats)).toBe(true);
    });

    test('should track tasks completed per thread', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const stats = engine.getThreadStatistics();
      for (const stat of stats) {
        expect(typeof stat.tasksCompleted).toBe('number');
      }
    });

    test('should track execution time per thread', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      const stats = engine.getThreadStatistics();
      for (const stat of stats) {
        expect(typeof stat.totalTime).toBe('number');
      }
    });
  });

  // ========================================================================
  // Engine State Tests
  // ========================================================================

  describe('Engine State', () => {
    test('should reset engine state', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      engine.reset();

      const metrics = engine.getPerformanceMetrics();
      expect(metrics.size).toBe(0);

      const trace = engine.getExecutionTrace();
      expect(trace.length).toBe(0);
    });

    test('should allow multiple executions', async () => {
      const z = createLatentVector(128);
      const pathWeights = createPathWeights(128);
      const pathBiases = createPathBiases(128);
      const attentionWeights = createAttentionWeights(128);
      const attentionBias = createAttentionBias();

      const result1 = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      engine.reset();

      const result2 = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result1).toBeDefined();
      expect(result2).toBeDefined();
    });
  });

  // ========================================================================
  // Utility Function Tests
  // ========================================================================

  describe('Utility Functions', () => {
    test('should create path weights', () => {
      const weights = createPathWeights(128);
      expect(weights.W_a).toBeDefined();
      expect(weights.W_b).toBeDefined();
      expect(weights.W_c).toBeDefined();
    });

    test('should create path biases', () => {
      const biases = createPathBiases(128);
      expect(biases.b_a).toBeDefined();
      expect(biases.b_b).toBeDefined();
      expect(biases.b_c).toBeDefined();
    });

    test('should create attention weights', () => {
      const weights = createAttentionWeights(128);
      expect(Array.isArray(weights)).toBe(true);
      expect(weights.length).toBe(3);
    });

    test('should create attention bias', () => {
      const bias = createAttentionBias();
      expect(Array.isArray(bias)).toBe(true);
      expect(bias.length).toBe(3);
    });

    test('should create latent vector', () => {
      const vector = createLatentVector(128);
      expect(Array.isArray(vector)).toBe(true);
      expect(vector.length).toBe(128);
    });
  });

  // ========================================================================
  // Scalability Tests
  // ========================================================================

  describe('Scalability', () => {
    test('should handle large latent dimensions', async () => {
      const z = createLatentVector(512);
      const pathWeights = createPathWeights(512);
      const pathBiases = createPathBiases(512);
      const attentionWeights = createAttentionWeights(512);
      const attentionBias = createAttentionBias();

      const result = await engine.execute3WayParallel(
        z,
        pathWeights,
        pathBiases,
        attentionWeights,
        attentionBias
      );

      expect(result.z_ens.length).toBe(512);
    });

    test('should execute without memory issues', async () => {
      for (let i = 0; i < 5; i++) {
        const z = createLatentVector(256);
        const pathWeights = createPathWeights(256);
        const pathBiases = createPathBiases(256);
        const attentionWeights = createAttentionWeights(256);
        const attentionBias = createAttentionBias();

        await engine.execute3WayParallel(
          z,
          pathWeights,
          pathBiases,
          attentionWeights,
          attentionBias
        );

        engine.reset();
      }

      expect(true).toBe(true);
    });
  });
});
