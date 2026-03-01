import Queue from './queue';

describe('Queue - Basic Operations', () => {
  test('enqueue and process single task', (done) => {
    const queue = new Queue<number>();
    let executed = false;

    queue.enqueue(async () => {
      executed = true;
      return 42;
    });

    setTimeout(() => {
      expect(executed).toBe(true);
      done();
    }, 100);
  });

  test('enqueue multiple tasks in sequence', (done) => {
    const queue = new Queue<number>();
    const results: number[] = [];

    queue.enqueue(async () => {
      results.push(1);
      return 1;
    });
    queue.enqueue(async () => {
      results.push(2);
      return 2;
    });
    queue.enqueue(async () => {
      results.push(3);
      return 3;
    });

    setTimeout(() => {
      expect(results).toEqual([1, 2, 3]);
      done();
    }, 200);
  });

  test('queue size', () => {
    const queue = new Queue<number>();
    queue.enqueue(async () => 1);
    queue.enqueue(async () => 2);
    expect(queue.size()).toBe(2);
  });

  test('queue is empty', () => {
    const queue = new Queue<number>();
    expect(queue.isEmpty()).toBe(true);
    queue.enqueue(async () => 1);
    expect(queue.isEmpty()).toBe(false);
  });

  test('queue is running', (done) => {
    const queue = new Queue<number>();
    const flags: boolean[] = [];

    queue.enqueue(async () => {
      flags.push(queue.isRunning());
      return 1;
    });

    setTimeout(() => {
      expect(flags[0]).toBe(true);
      done();
    }, 50);
  });
});

describe('Queue - Task Execution', () => {
  test('sequential execution order', (done) => {
    const queue = new Queue<number>();
    const order: number[] = [];
    const start = Date.now();

    queue.enqueue(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      order.push(1);
      return 1;
    });

    queue.enqueue(async () => {
      order.push(2);
      return 2;
    });

    queue.enqueue(async () => {
      order.push(3);
      return 3;
    });

    setTimeout(() => {
      expect(order).toEqual([1, 2, 3]);
      const elapsed = Date.now() - start;
      expect(elapsed).toBeGreaterThanOrEqual(50);
      done();
    }, 200);
  });

  test('task with delay', (done) => {
    const queue = new Queue<string>();
    const times: number[] = [];
    const start = Date.now();

    queue.enqueue(async () => {
      times.push(Date.now() - start);
      await new Promise((resolve) => setTimeout(resolve, 100));
      return 'done';
    });

    setTimeout(() => {
      expect(times[0]).toBeLessThan(50);
      done();
    }, 200);
  });

  test('task error handling', (done) => {
    const queue = new Queue<number>();
    const results: number[] = [];

    queue.enqueue(async () => {
      throw new Error('task failed');
    });

    queue.enqueue(async () => {
      results.push(1);
      return 1;
    });

    setTimeout(() => {
      expect(results).toContain(1);
      done();
    }, 200);
  });

  test('wait for all tasks', (done) => {
    const queue = new Queue<number>();
    queue.enqueue(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
      return 1;
    });
    queue.enqueue(async () => 2);
    queue.enqueue(async () => 3);

    queue.waitAll().then((results) => {
      expect(results.length).toBeGreaterThan(0);
      done();
    });
  });
});

describe('Queue - Control Operations', () => {
  test('cancel queue', () => {
    const queue = new Queue<number>();
    queue.enqueue(async () => 1);
    queue.enqueue(async () => 2);
    expect(queue.size()).toBe(2);

    queue.cancel();
    expect(queue.size()).toBe(0);
  });

  test('clear queue and results', (done) => {
    const queue = new Queue<number>();
    queue.enqueue(async () => 1);

    setTimeout(() => {
      expect(queue.getResults().length).toBeGreaterThan(0);
      queue.clear();
      expect(queue.getResults().length).toBe(0);
      done();
    }, 100);
  });

  test('get results', (done) => {
    const queue = new Queue<number>();
    queue.enqueue(async () => 10);
    queue.enqueue(async () => 20);
    queue.enqueue(async () => 30);

    setTimeout(() => {
      const results = queue.getResults();
      expect(results.length).toBe(3);
      expect(results).toEqual([10, 20, 30]);
      done();
    }, 200);
  });

  test('multiple enqueues from different sources', (done) => {
    const queue = new Queue<number>();
    const results: number[] = [];

    queue.enqueue(async () => {
      results.push(1);
      return 1;
    });

    queue.enqueue(async () => {
      results.push(2);
      return 2;
    });

    queue.enqueue(async () => {
      results.push(3);
      return 3;
    });

    setTimeout(() => {
      expect(results).toEqual([1, 2, 3]);
      done();
    }, 200);
  });

  test('queue state after processing', (done) => {
    const queue = new Queue<number>();
    queue.enqueue(async () => 1);

    setTimeout(() => {
      expect(queue.isEmpty()).toBe(true);
      expect(queue.isRunning()).toBe(false);
      done();
    }, 100);
  });
});

describe('Queue - Edge Cases', () => {
  test('empty queue processing', (done) => {
    const queue = new Queue<number>();
    queue.process();

    setTimeout(() => {
      expect(queue.isEmpty()).toBe(true);
      done();
    }, 50);
  });

  test('rapid enqueues', (done) => {
    const queue = new Queue<number>();
    const results: number[] = [];

    for (let i = 1; i <= 10; i++) {
      queue.enqueue(async () => {
        results.push(i);
        return i;
      });
    }

    setTimeout(() => {
      expect(results.length).toBe(10);
      done();
    }, 500);
  });

  test('large queue processing', (done) => {
    const queue = new Queue<number>();
    const count = 100;

    for (let i = 0; i < count; i++) {
      queue.enqueue(async () => i);
    }

    setTimeout(() => {
      expect(queue.getResults().length).toBeGreaterThan(0);
      expect(queue.isEmpty()).toBe(true);
      done();
    }, 2000);
  });

  test('queue with async task that returns value', (done) => {
    const queue = new Queue<string>();
    queue.enqueue(async () => {
      return 'hello';
    });

    setTimeout(() => {
      const results = queue.getResults();
      expect(results[0]).toBe('hello');
      done();
    }, 100);
  });

  test('queue processing with setTimeout inside task', (done) => {
    const queue = new Queue<number>();
    const order: number[] = [];

    queue.enqueue(async () => {
      return new Promise<number>((resolve) => {
        setTimeout(() => {
          order.push(1);
          resolve(1);
        }, 30);
      });
    });

    queue.enqueue(async () => {
      order.push(2);
      return 2;
    });

    setTimeout(() => {
      expect(order).toEqual([1, 2]);
      done();
    }, 200);
  });
});
