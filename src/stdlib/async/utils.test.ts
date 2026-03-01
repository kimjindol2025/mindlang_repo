import {
  sleep,
  timeout,
  retry,
  debounce,
  throttle,
  repeat,
  sequential,
  parallel,
  retryIf,
  withTimeout,
} from './utils';

describe('Utils - Sleep', () => {
  test('sleep resolves after delay', async () => {
    const start = Date.now();
    await sleep(100);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeGreaterThanOrEqual(100);
    expect(elapsed).toBeLessThan(150);
  });

  test('sleep with zero delay', async () => {
    const start = Date.now();
    await sleep(0);
    const elapsed = Date.now() - start;
    expect(elapsed).toBeLessThan(50);
  });
});

describe('Utils - Timeout', () => {
  test('timeout succeeds before limit', async () => {
    const result = await timeout(
      new Promise((resolve) => {
        setTimeout(() => resolve(42), 50);
      }),
      200
    );
    expect(result).toBe(42);
  });

  test('timeout throws on exceed', async () => {
    try {
      await timeout(
        new Promise((resolve) => {
          setTimeout(() => resolve(42), 200);
        }),
        100
      );
      expect(true).toBe(false); // Should not reach here
    } catch (e) {
      expect((e as Error).message).toContain('timeout');
    }
  });
});

describe('Utils - Retry', () => {
  test('retry succeeds on first attempt', async () => {
    let attempts = 0;
    const result = await retry(
      async () => {
        attempts++;
        return 42;
      },
      3,
      10
    );
    expect(result).toBe(42);
    expect(attempts).toBe(1);
  });

  test('retry succeeds after failure', async () => {
    let attempts = 0;
    const result = await retry(
      async () => {
        attempts++;
        if (attempts < 3) throw new Error('fail');
        return 42;
      },
      5,
      10
    );
    expect(result).toBe(42);
    expect(attempts).toBe(3);
  });

  test('retry throws after max attempts', async () => {
    let attempts = 0;
    try {
      await retry(
        async () => {
          attempts++;
          throw new Error('always fail');
        },
        3,
        10
      );
      expect(true).toBe(false);
    } catch (e) {
      expect(attempts).toBe(3);
    }
  });

  test('retry with exponential backoff', async () => {
    const times: number[] = [];
    const start = Date.now();

    try {
      await retry(
        async () => {
          times.push(Date.now() - start);
          throw new Error('fail');
        },
        3,
        10,
        true
      );
    } catch (e) {
      // Exponential backoff: 10ms, 20ms
      expect(times.length).toBe(3);
      expect(times[0]).toBeLessThan(50);
    }
  });
});

describe('Utils - Debounce', () => {
  test('debounce delays execution', (done) => {
    let callCount = 0;
    const debounced = debounce(() => {
      callCount++;
    }, 100);

    debounced();
    debounced();
    debounced();

    expect(callCount).toBe(0);

    setTimeout(() => {
      expect(callCount).toBe(1);
      done();
    }, 150);
  });

  test('debounce resets on new call', (done) => {
    let callCount = 0;
    const debounced = debounce(() => {
      callCount++;
    }, 100);

    debounced();
    setTimeout(() => debounced(), 50);
    setTimeout(() => {
      expect(callCount).toBe(1);
      done();
    }, 200);
  });

  test('debounce with arguments', (done) => {
    const results: number[] = [];
    const debounced = debounce((value: number) => {
      results.push(value);
    }, 100);

    debounced(1);
    debounced(2);
    debounced(3);

    setTimeout(() => {
      expect(results).toEqual([3]);
      done();
    }, 150);
  });
});

describe('Utils - Throttle', () => {
  test('throttle limits call frequency', (done) => {
    let callCount = 0;
    const throttled = throttle(() => {
      callCount++;
    }, 100);

    throttled();
    throttled();
    throttled();

    expect(callCount).toBe(1);

    setTimeout(() => {
      throttled();
      expect(callCount).toBe(2);
      done();
    }, 150);
  });

  test('throttle with arguments', (done) => {
    const results: number[] = [];
    const throttled = throttle((value: number) => {
      results.push(value);
    }, 100);

    throttled(1);
    throttled(2);
    throttled(3);

    expect(results).toEqual([1]);

    setTimeout(() => {
      throttled(4);
      expect(results).toEqual([1, 4]);
      done();
    }, 150);
  });
});

describe('Utils - Repeat', () => {
  test('repeat executes specified times', async () => {
    let count = 0;
    const results = await repeat(
      async () => {
        count++;
        return count;
      },
      10,
      3
    );
    expect(results.length).toBe(3);
    expect(results).toEqual([1, 2, 3]);
  });

  test('repeat with interval', async () => {
    const times: number[] = [];
    const start = Date.now();

    await repeat(
      async () => {
        times.push(Date.now() - start);
        return 1;
      },
      50,
      2
    );

    expect(times.length).toBe(2);
    expect(times[1] - times[0]).toBeGreaterThanOrEqual(50);
  });
});

describe('Utils - Sequential and Parallel', () => {
  test('sequential executes in order', async () => {
    const order: number[] = [];
    const results = await sequential([
      async () => {
        order.push(1);
        return 1;
      },
      async () => {
        order.push(2);
        return 2;
      },
      async () => {
        order.push(3);
        return 3;
      },
    ]);

    expect(order).toEqual([1, 2, 3]);
    expect(results).toEqual([1, 2, 3]);
  });

  test('parallel executes concurrently', async () => {
    const results = await parallel([
      async () => 1,
      async () => 2,
      async () => 3,
    ]);
    expect(results).toContain(1);
    expect(results).toContain(2);
    expect(results).toContain(3);
  });
});

describe('Utils - RetryIf', () => {
  test('retryIf with condition', async () => {
    let attempts = 0;
    const result = await retryIf(
      async () => {
        attempts++;
        if (attempts < 2) throw new Error('temporary');
        return 42;
      },
      (error) => error.message === 'temporary',
      3,
      10
    );

    expect(result).toBe(42);
    expect(attempts).toBe(2);
  });

  test('retryIf stops on non-matching error', async () => {
    let attempts = 0;
    try {
      await retryIf(
        async () => {
          attempts++;
          throw new Error('permanent');
        },
        (error) => error.message === 'temporary',
        3,
        10
      );
    } catch (e) {
      expect(attempts).toBe(1);
    }
  });
});

describe('Utils - WithTimeout', () => {
  test('withTimeout succeeds', async () => {
    const result = await withTimeout(async () => 42, 200);
    expect(result).toBe(42);
  });

  test('withTimeout throws on exceed', async () => {
    try {
      await withTimeout(
        async () => {
          await sleep(200);
          return 42;
        },
        100
      );
      expect(true).toBe(false);
    } catch (e) {
      expect((e as Error).message).toContain('timeout');
    }
  });
});
