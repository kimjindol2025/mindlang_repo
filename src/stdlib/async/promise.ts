/**
 * MindPromise - Promise/A+ 호환 구현
 *
 * 비동기 연산 결과를 나타내는 객체로, resolve/reject 콜백과
 * then/catch/finally 메서드 체이닝을 지원합니다.
 */

// AggregateError 정의
export class AggregateError extends Error {
  errors: Error[];
  constructor(errors: Error[], message: string) {
    super(message);
    this.errors = errors;
    this.name = 'AggregateError';
    Object.setPrototypeOf(this, AggregateError.prototype);
  }
}

export class MindPromise<T> {
  private state: 'pending' | 'fulfilled' | 'rejected' = 'pending';
  private value?: T;
  private reason?: Error;
  private callbacks: Array<{
    onFulfilled?: (value: T) => any;
    onRejected?: (reason: Error) => any;
  }> = [];

  /**
   * Promise 생성
   * @param executor (resolve, reject) => void 함수
   */
  constructor(
    executor: (
      resolve: (value: T | PromiseLike<T>) => void,
      reject: (reason?: any) => void
    ) => void
  ) {
    try {
      executor(this.resolve.bind(this), this.reject.bind(this));
    } catch (e) {
      this.reject(e);
    }
  }

  /**
   * Promise를 resolved 상태로 전환
   */
  private resolve(value: T | PromiseLike<T>): void {
    if (this.state !== 'pending') return;

    // PromiseLike 처리
    if (value && typeof (value as any).then === 'function') {
      (value as any).then(this.resolve.bind(this), this.reject.bind(this));
      return;
    }

    this.state = 'fulfilled';
    this.value = value as T;
    this.notifyCallbacks();
  }

  /**
   * Promise를 rejected 상태로 전환
   */
  private reject(reason?: any): void {
    if (this.state !== 'pending') return;

    this.state = 'rejected';
    this.reason = reason instanceof Error ? reason : new Error(String(reason));
    this.notifyCallbacks();
  }

  /**
   * Promise 결과에 따라 콜백 실행
   */
  then<U = any>(
    onFulfilled?: ((value: T) => U | any) | null,
    onRejected?: ((reason: Error) => U | any) | null
  ): MindPromise<U> {
    return new MindPromise<U>((resolve, reject) => {
      const handleFulfilled = (value: T) => {
        try {
          if (onFulfilled) {
            const result = onFulfilled(value);
            // PromiseLike 또는 MindPromise인 경우 처리
            if (result && typeof (result as any).then === 'function') {
              (result as any).then(resolve, reject);
            } else {
              resolve(result as any);
            }
          } else {
            resolve(value as any);
          }
        } catch (e) {
          reject(e);
        }
      };

      const handleRejected = (reason: Error) => {
        try {
          if (onRejected) {
            const result = onRejected(reason);
            // PromiseLike 또는 MindPromise인 경우 처리
            if (result && typeof (result as any).then === 'function') {
              (result as any).then(resolve, reject);
            } else {
              resolve(result as any);
            }
          } else {
            reject(reason);
          }
        } catch (e) {
          reject(e);
        }
      };

      if (this.state === 'fulfilled') {
        // 동기적으로 실행 (microtask 대신 동기 처리)
        handleFulfilled(this.value!);
      } else if (this.state === 'rejected') {
        handleRejected(this.reason!);
      } else {
        // pending 상태: 콜백 등록
        this.callbacks.push({ onFulfilled: handleFulfilled, onRejected: handleRejected });
      }
    });
  }

  /**
   * rejection 처리
   */
  catch<U>(onRejected?: ((reason: Error) => U | PromiseLike<U>) | null): MindPromise<U> {
    return this.then<U>(undefined, onRejected);
  }

  /**
   * 항상 실행되는 콜백
   */
  finally(onFinally?: (() => void) | null): MindPromise<T> {
    return this.then(
      (value) => {
        if (onFinally) onFinally();
        return value;
      },
      (reason) => {
        if (onFinally) onFinally();
        throw reason;
      }
    );
  }

  /**
   * 이미 resolved된 Promise 생성
   */
  static resolve<T>(value: T | PromiseLike<T>): MindPromise<T> {
    if (value instanceof MindPromise) return value;
    return new MindPromise((resolve) => resolve(value));
  }

  /**
   * 이미 rejected된 Promise 생성
   */
  static reject<T>(reason?: any): MindPromise<T> {
    return new MindPromise((_, reject) => reject(reason));
  }

  /**
   * 모든 Promise가 fulfilled될 때까지 대기
   */
  static all<T>(promises: Array<MindPromise<T> | T>): MindPromise<T[]> {
    return new MindPromise((resolve, reject) => {
      if (promises.length === 0) {
        resolve([]);
        return;
      }

      const results: T[] = [];
      let completed = 0;

      promises.forEach((promise: any, index: number) => {
        const p = promise instanceof MindPromise ? promise : MindPromise.resolve(promise);
        p.then(
          (value: T) => {
            results[index] = value;
            completed++;
            if (completed === promises.length) {
              resolve(results);
            }
          },
          (reason: Error) => {
            reject(reason);
          }
        );
      });
    });
  }

  /**
   * 가장 먼저 settled된 Promise 반환
   */
  static race<T>(promises: Array<MindPromise<T> | T>): MindPromise<T> {
    return new MindPromise((resolve, reject) => {
      if (promises.length === 0) return;

      promises.forEach((promise: any) => {
        const p = promise instanceof MindPromise ? promise : MindPromise.resolve(promise);
        p.then(resolve, reject);
      });
    });
  }

  /**
   * 모든 Promise의 결과 반환 (rejected 포함)
   */
  static allSettled<T>(
    promises: Array<MindPromise<T> | T>
  ): MindPromise<Array<{ status: 'fulfilled' | 'rejected'; value?: T; reason?: Error }>> {
    return new MindPromise((resolve) => {
      if (promises.length === 0) {
        resolve([]);
        return;
      }

      const results: Array<{ status: 'fulfilled' | 'rejected'; value?: T; reason?: Error }> = [];
      let completed = 0;

      promises.forEach((promise: any, index: number) => {
        const p = promise instanceof MindPromise ? promise : MindPromise.resolve(promise);
        p.then(
          (value: T) => {
            results[index] = { status: 'fulfilled', value };
            completed++;
            if (completed === promises.length) {
              resolve(results);
            }
          },
          (reason: Error) => {
            results[index] = { status: 'rejected', reason };
            completed++;
            if (completed === promises.length) {
              resolve(results);
            }
          }
        );
      });
    });
  }

  /**
   * 모든 Promise 실행, 가장 먼저 resolved된 값 반환
   */
  static any<T>(promises: Array<MindPromise<T> | T>): MindPromise<T> {
    return new MindPromise((resolve, reject) => {
      if (promises.length === 0) {
        reject(new Error('No promises provided'));
        return;
      }

      let rejected = 0;
      const errors: Error[] = [];

      promises.forEach((promise: any, index: number) => {
        const p = promise instanceof MindPromise ? promise : MindPromise.resolve(promise);
        p.then(
          (value: T) => {
            resolve(value);
          },
          (reason: Error) => {
            errors[index] = reason;
            rejected++;
            if (rejected === promises.length) {
              reject(new AggregateError(errors, 'All promises rejected'));
            }
          }
        );
      });
    });
  }

  /**
   * 등록된 콜백들에 알림
   */
  private notifyCallbacks(): void {
    this.callbacks.forEach((callback) => {
      if (this.state === 'fulfilled' && callback.onFulfilled) {
        callback.onFulfilled(this.value!);
      } else if (this.state === 'rejected' && callback.onRejected) {
        callback.onRejected(this.reason!);
      }
    });
    this.callbacks = [];
  }
}

export default MindPromise;
