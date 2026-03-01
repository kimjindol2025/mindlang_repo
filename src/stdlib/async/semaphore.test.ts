import Semaphore from './semaphore';

describe('Semaphore - Basic Operations', () => {
  test('acquire and release', async () => {
    const sem = new Semaphore(1);
    expect(sem.availablePermits()).toBe(1);

    await sem.acquire();
    expect(sem.availablePermits()).toBe(0);

    sem.release();
    expect(sem.availablePermits()).toBe(1);
  });

  test('multiple permits', async () => {
    const sem = new Semaphore(3);
    expect(sem.availablePermits()).toBe(3);

    await sem.acquire();
    expect(sem.availablePermits()).toBe(2);

    await sem.acquire();
    expect(sem.availablePermits()).toBe(1);

    await sem.acquire();
    expect(sem.availablePermits()).toBe(0);

    sem.release();
    expect(sem.availablePermits()).toBe(1);
  });

  test('constructor validation', () => {
    expect(() => new Semaphore(-1)).toThrow();
    expect(() => new Semaphore(0)).not.toThrow();
    expect(() => new Semaphore(5)).not.toThrow();
  });

  test('waiting count', async () => {
    const sem = new Semaphore(1);
    await sem.acquire();

    // 워커 시뮬레이션
    const p = sem.acquire(); // 대기 상태
    expect(sem.waitingCount()).toBe(1);

    sem.release();
    await p;
    expect(sem.waitingCount()).toBe(0);
  });

  test('drain permits', async () => {
    const sem = new Semaphore(3);
    const drained = sem.drainPermits();
    expect(drained).toBe(3);
    expect(sem.availablePermits()).toBe(0);
  });
});

describe('Semaphore - Concurrency Control', () => {
  test('limit concurrent execution', async () => {
    const sem = new Semaphore(2);
    let concurrent = 0;
    let maxConcurrent = 0;

    const task = async () => {
      await sem.acquire();
      try {
        concurrent++;
        maxConcurrent = Math.max(maxConcurrent, concurrent);
        await new Promise((resolve) => setTimeout(resolve, 50));
      } finally {
        concurrent--;
        sem.release();
      }
    };

    await Promise.all([task(), task(), task(), task()]);
    expect(maxConcurrent).toBe(2);
  });

  test('run method with function', async () => {
    const sem = new Semaphore(1);
    const results: number[] = [];

    await sem.run(async () => {
      results.push(1);
      return 1;
    });

    expect(results).toContain(1);
    expect(sem.availablePermits()).toBe(1);
  });

  test('run method with error', async () => {
    const sem = new Semaphore(1);

    try {
      await sem.run(async () => {
        throw new Error('task failed');
      });
    } catch (e) {
      expect((e as Error).message).toBe('task failed');
    }

    expect(sem.availablePermits()).toBe(1);
  });

  test('multiple concurrent tasks', async () => {
    const sem = new Semaphore(2);
    const results: number[] = [];

    const task = (id: number) =>
      sem.run(async () => {
        results.push(id);
        await new Promise((resolve) => setTimeout(resolve, 20));
        return id;
      });

    await Promise.all([task(1), task(2), task(3), task(4)]);
    expect(results.length).toBe(4);
  });

  test('sequential execution with semaphore(1)', async () => {
    const sem = new Semaphore(1);
    const order: number[] = [];

    const task = (id: number) =>
      sem.run(async () => {
        order.push(id);
        return id;
      });

    await Promise.all([task(1), task(2), task(3)]);
    expect(order.length).toBe(3);
  });
});

describe('Semaphore - State Management', () => {
  test('set permits', async () => {
    const sem = new Semaphore(1);
    sem.setPermits(5);
    expect(sem.availablePermits()).toBe(5);
  });

  test('set permits validation', () => {
    const sem = new Semaphore(1);
    expect(() => sem.setPermits(-1)).toThrow();
    expect(() => sem.setPermits(10)).not.toThrow();
  });

  test('semaphore with zero permits', async () => {
    const sem = new Semaphore(0);
    let released = false;

    const p = sem.acquire().then(() => {
      released = true;
    });

    // 대기 상태 확인
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(released).toBe(false);

    sem.release();
    await p;
    expect(released).toBe(true);
  });

  test('multiple releases', async () => {
    const sem = new Semaphore(1);
    await sem.acquire();

    sem.release();
    expect(sem.availablePermits()).toBe(1);

    sem.release();
    expect(sem.availablePermits()).toBe(2);

    sem.release();
    expect(sem.availablePermits()).toBe(3);
  });
});
