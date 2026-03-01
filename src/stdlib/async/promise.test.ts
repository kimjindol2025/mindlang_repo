import MindPromise from './promise';

describe('MindPromise - Basic Resolve', () => {
  test('basic resolve with value', (done) => {
    const p = new MindPromise<number>((resolve) => {
      resolve(42);
    });
    p.then((value: number) => {
      expect(value).toBe(42);
      done();
    });
  });

  test('resolve with object', (done) => {
    const obj = { name: 'test', id: 1 };
    const p = new MindPromise((resolve) => {
      resolve(obj);
    });
    p.then((value) => {
      expect(value).toEqual(obj);
      done();
    });
  });

  test('resolve with array', (done) => {
    const arr = [1, 2, 3];
    const p = new MindPromise((resolve) => {
      resolve(arr);
    });
    p.then((value) => {
      expect(value).toEqual(arr);
      done();
    });
  });
});

describe('MindPromise - Basic Reject', () => {
  test('basic reject with error', (done) => {
    const p = new MindPromise<number>((_, reject) => {
      reject(new Error('test error'));
    });
    p.catch((reason) => {
      expect(reason.message).toBe('test error');
      done();
    });
  });

  test('reject with string', (done) => {
    const p = new MindPromise<number>((_, reject) => {
      reject('error message');
    });
    p.catch((reason) => {
      expect(reason.message).toBe('error message');
      done();
    });
  });

  test('reject with number', (done) => {
    const p = new MindPromise<number>((_, reject) => {
      reject(404);
    });
    p.catch((reason) => {
      expect(reason.message).toBe('404');
      done();
    });
  });
});

describe('MindPromise - Then Chaining', () => {
  test('simple then chain', (done) => {
    new MindPromise<number>((resolve) => {
      resolve(5);
    })
      .then((v: number) => v * 2)
      .then((v: number) => {
        expect(v).toBe(10);
        done();
      });
  });

  test('triple then chain', (done) => {
    new MindPromise<number>((resolve) => {
      resolve(1);
    })
      .then((v: number) => v + 1)
      .then((v: number) => v * 2)
      .then((v: number) => v + 5)
      .then((v: number) => {
        expect(v).toBe(9); // ((1 + 1) * 2) + 5
        done();
      });
  });

  test('then with object transformation', (done) => {
    new MindPromise<{ x: number }>((resolve) => {
      resolve({ x: 10 });
    })
      .then((obj: { x: number }) => ({ x: obj.x * 2 }))
      .then((obj: { x: number }) => {
        expect(obj.x).toBe(20);
        done();
      });
  });

  test('then with type change', (done) => {
    new MindPromise<number>((resolve) => {
      resolve(42);
    })
      .then((v: number) => `value: ${v}`)
      .then((s: string) => {
        expect(s).toBe('value: 42');
        done();
      });
  });

  test('then with promise return', (done) => {
    (new MindPromise<number>((resolve) => {
      resolve(5);
    }) as any)
      .then((v: number) => {
        return new MindPromise<number>((resolve) => resolve(v * 2));
      })
      .then((v: number) => {
        expect(v).toBe(10);
        done();
      });
  });
});

describe('MindPromise - Catch Error Handling', () => {
  test('catch after error', (done) => {
    new MindPromise<number>((_, reject) => {
      reject(new Error('fail'));
    })
      .catch((e: Error) => {
        expect(e.message).toBe('fail');
        return 100;
      })
      .then((v: number) => {
        expect(v).toBe(100);
        done();
      });
  });

  test('catch and recover', (done) => {
    new MindPromise<number>((_, reject) => {
      reject(new Error('error'));
    })
      .catch(() => 'recovered')
      .then((v: string) => {
        expect(v).toBe('recovered');
        done();
      });
  });

  test('catch specific error', (done) => {
    new MindPromise<number>((_, reject) => {
      reject(new Error('not found'));
    })
      .catch((e: Error) => {
        if (e.message === 'not found') {
          return 404;
        }
        throw e;
      })
      .then((v: number) => {
        expect(v).toBe(404);
        done();
      });
  });

  test('then and catch chain', (done) => {
    new MindPromise<number>((_, reject) => {
      reject(new Error('test'));
    })
      .then(() => 'success')
      .catch((e: Error) => `error: ${e.message}`)
      .then((v: string) => {
        expect(v).toBe('error: test');
        done();
      });
  });

  test('error propagation', (done) => {
    new MindPromise<number>((resolve) => {
      resolve(5);
    })
      .then(() => {
        throw new Error('chain error');
      })
      .catch((e: Error) => {
        expect(e.message).toBe('chain error');
        done();
      });
  });
});

describe('MindPromise - Finally', () => {
  test('finally after success', (done) => {
    let finallyCalled = false;
    new MindPromise<number>((resolve) => {
      resolve(42);
    })
      .finally(() => {
        finallyCalled = true;
      })
      .then((v: number) => {
        expect(finallyCalled).toBe(true);
        expect(v).toBe(42);
        done();
      });
  });

  test('finally after error', (done) => {
    let finallyCalled = false;
    new MindPromise<number>((_, reject) => {
      reject(new Error('fail'));
    })
      .finally(() => {
        finallyCalled = true;
      })
      .catch((e: Error) => {
        expect(finallyCalled).toBe(true);
        expect(e.message).toBe('fail');
        done();
      });
  });

  test('finally with chain', (done) => {
    new MindPromise<number>((resolve) => {
      resolve(5);
    })
      .then((v: number) => v * 2)
      .finally(() => {
        // no-op
      })
      .then((v: number) => {
        expect(v).toBe(10);
        done();
      });
  });
});

describe('MindPromise - Static Methods', () => {
  test('Promise.resolve', (done) => {
    MindPromise.resolve<number>(42).then((v: number) => {
      expect(v).toBe(42);
      done();
    });
  });

  test('Promise.resolve with promise', (done) => {
    const p = new MindPromise<number>((resolve) => {
      resolve(100);
    });
    ((MindPromise.resolve(p as any) as any) as MindPromise<number>).then((v: number) => {
      expect(v).toBe(100);
      done();
    });
  });

  test('Promise.reject', (done) => {
    MindPromise.reject<number>(new Error('rejected')).catch((e: Error) => {
      expect(e.message).toBe('rejected');
      done();
    });
  });
});

describe('MindPromise - All', () => {
  test('Promise.all with success', (done) => {
    MindPromise.all<number>([
      MindPromise.resolve(1),
      MindPromise.resolve(2),
      MindPromise.resolve(3),
    ]).then((values: number[]) => {
      expect(values).toEqual([1, 2, 3]);
      done();
    });
  });

  test('Promise.all empty array', (done) => {
    MindPromise.all<number>([]).then((values: number[]) => {
      expect(values).toEqual([]);
      done();
    });
  });

  test('Promise.all with rejection', (done) => {
    MindPromise.all<number>([
      MindPromise.resolve(1),
      MindPromise.reject(new Error('fail')),
      MindPromise.resolve(3),
    ]).catch((e: Error) => {
      expect(e.message).toBe('fail');
      done();
    });
  });

  test('Promise.all with multiple items', (done) => {
    MindPromise.all<number>([
      new MindPromise((resolve) => resolve(10)),
      new MindPromise((resolve) => resolve(20)),
      new MindPromise((resolve) => resolve(30)),
      new MindPromise((resolve) => resolve(40)),
      new MindPromise((resolve) => resolve(50)),
    ]).then((values: number[]) => {
      expect(values).toEqual([10, 20, 30, 40, 50]);
      done();
    });
  });

  test('Promise.all preserves order', (done) => {
    MindPromise.all<number>([
      MindPromise.resolve(3),
      MindPromise.resolve(1),
      MindPromise.resolve(2),
    ]).then((values: number[]) => {
      expect(values).toEqual([3, 1, 2]);
      done();
    });
  });
});

describe('MindPromise - Race', () => {
  test('Promise.race returns first', (done) => {
    MindPromise.race<number>([
      new MindPromise((resolve) => {
        setTimeout(() => resolve(2), 100);
      }),
      MindPromise.resolve(1),
    ]).then((v: number) => {
      expect(v).toBe(1);
      done();
    });
  });

  test('Promise.race with rejection', (done) => {
    MindPromise.race<number>([
      new MindPromise((_, reject) => {
        reject(new Error('first fails'));
      }),
      MindPromise.resolve(1),
    ]).catch((e: Error) => {
      expect(e.message).toBe('first fails');
      done();
    });
  });

  test('Promise.race multiple items', (done) => {
    MindPromise.race<number>([
      MindPromise.resolve(3),
      MindPromise.resolve(1),
      MindPromise.resolve(2),
    ]).then((v: number) => {
      expect([3, 1, 2]).toContain(v);
      done();
    });
  });

  test('Promise.race with promise-like', (done) => {
    MindPromise.race<number>([
      MindPromise.resolve(100),
      new MindPromise((resolve) => resolve(200)),
    ]).then((v: number) => {
      expect([100, 200]).toContain(v);
      done();
    });
  });

  test('Promise.race single item', (done) => {
    MindPromise.race<number>([MindPromise.resolve(42)]).then((v: number) => {
      expect(v).toBe(42);
      done();
    });
  });
});

describe('MindPromise - AllSettled', () => {
  test('Promise.allSettled with success', (done) => {
    MindPromise.allSettled<number>([
      MindPromise.resolve(1),
      MindPromise.resolve(2),
    ]).then((results) => {
      expect(results).toEqual([
        { status: 'fulfilled', value: 1 },
        { status: 'fulfilled', value: 2 },
      ]);
      done();
    });
  });

  test('Promise.allSettled with mixed', (done) => {
    MindPromise.allSettled<number>([
      MindPromise.resolve(1),
      MindPromise.reject(new Error('fail')),
    ]).then((results) => {
      expect(results[0]).toEqual({ status: 'fulfilled', value: 1 });
      expect(results[1].status).toBe('rejected');
      expect((results[1].reason as Error).message).toBe('fail');
      done();
    });
  });

  test('Promise.allSettled all rejected', (done) => {
    MindPromise.allSettled<number>([
      MindPromise.reject(new Error('e1')),
      MindPromise.reject(new Error('e2')),
    ]).then((results) => {
      expect(results.every((r) => r.status === 'rejected')).toBe(true);
      done();
    });
  });

  test('Promise.allSettled empty', (done) => {
    MindPromise.allSettled<number>([]).then((results) => {
      expect(results).toEqual([]);
      done();
    });
  });

  test('Promise.allSettled multiple items', (done) => {
    MindPromise.allSettled<number>([
      MindPromise.resolve(10),
      MindPromise.reject(new Error('x')),
      MindPromise.resolve(30),
      MindPromise.reject(new Error('y')),
      MindPromise.resolve(50),
    ]).then((results) => {
      expect(results.length).toBe(5);
      expect(results[0].status).toBe('fulfilled');
      expect(results[2].status).toBe('fulfilled');
      expect(results[4].status).toBe('fulfilled');
      done();
    });
  });
});

describe('MindPromise - Any', () => {
  test('Promise.any returns first success', (done) => {
    MindPromise.any<number>([
      MindPromise.reject(new Error('fail1')),
      MindPromise.resolve(42),
      MindPromise.reject(new Error('fail2')),
    ]).then((v: number) => {
      expect(v).toBe(42);
      done();
    });
  });

  test('Promise.any all rejected', (done) => {
    MindPromise.any<number>([
      MindPromise.reject(new Error('fail1')),
      MindPromise.reject(new Error('fail2')),
    ]).catch((e: Error) => {
      expect(e.name).toBe('AggregateError');
      done();
    });
  });

  test('Promise.any single success', (done) => {
    MindPromise.any<number>([MindPromise.resolve(100)]).then((v: number) => {
      expect(v).toBe(100);
      done();
    });
  });

  test('Promise.any mixed results', (done) => {
    MindPromise.any<number>([
      MindPromise.reject(new Error('e1')),
      MindPromise.resolve(50),
      MindPromise.reject(new Error('e2')),
    ]).then((v: number) => {
      expect(v).toBe(50);
      done();
    });
  });

  test('Promise.any empty array', (done) => {
    MindPromise.any<number>([]).catch((e: Error) => {
      expect(e.message).toBe('No promises provided');
      done();
    });
  });
});

describe('MindPromise - Complex Scenarios', () => {
  test('nested promise chains', (done) => {
    (new MindPromise<number>((resolve) => {
      resolve(5);
    }) as any)
      .then((v: number) => {
        return new MindPromise((resolve) => resolve(v * 2));
      })
      .then((v: number) => {
        return new MindPromise((resolve) => resolve(v + 10));
      })
      .then((v: number) => {
        expect(v).toBe(20);
        done();
      });
  });

  test('promise with constructor error', (done) => {
    new MindPromise<number>(() => {
      throw new Error('constructor error');
    }).catch((e: Error) => {
      expect(e.message).toBe('constructor error');
      done();
    });
  });

  test('multiple handlers on same promise', (done) => {
    const p = new MindPromise<number>((resolve) => {
      resolve(42);
    });

    let count = 0;
    p.then((v: number) => {
      expect(v).toBe(42);
      count++;
    });
    p.then((v: number) => {
      expect(v).toBe(42);
      count++;
      if (count === 2) done();
    });
  });
});
