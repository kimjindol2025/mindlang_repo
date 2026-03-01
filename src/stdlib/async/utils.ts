/**
 * Utils - 비동기 유틸리티 함수
 *
 * sleep, timeout, retry, debounce, throttle 등의 비동기 작업 보조 함수
 */

import MindPromise from './promise';

/**
 * 주어진 시간 동안 대기
 * @param ms 대기 시간 (밀리초)
 */
export async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Promise에 타임아웃 추가
 * @param promise 실행할 Promise
 * @param ms 타임아웃 시간 (밀리초)
 */
export async function timeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return Promise.race([
    promise,
    sleep(ms).then(() => {
      throw new Error(`Promise timeout after ${ms}ms`);
    }),
  ]) as Promise<T>;
}

/**
 * 작업 재시도
 * @param fn 실행할 함수
 * @param maxAttempts 최대 시도 횟수 (기본값: 3)
 * @param delayMs 재시도 대기 시간 (기본값: 1000)
 * @param backoff 지수 백오프 사용 (기본값: true)
 */
export async function retry<T>(
  fn: () => Promise<T>,
  maxAttempts: number = 3,
  delayMs: number = 1000,
  backoff: boolean = true
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e as Error;
      if (attempt < maxAttempts) {
        const waitTime = backoff ? delayMs * Math.pow(2, attempt - 1) : delayMs;
        await sleep(waitTime);
      }
    }
  }

  throw lastError || new Error('Max attempts reached');
}

/**
 * 디바운스 함수
 * 연속으로 호출되는 함수를 마지막 호출 이후 지정된 시간 후에만 실행합니다.
 * @param fn 디바운스할 함수
 * @param delayMs 대기 시간 (밀리초)
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = setTimeout(() => {
      fn(...args);
      timeoutId = null;
    }, delayMs);
  };
}

/**
 * 스로틀 함수
 * 함수를 주어진 간격으로만 실행합니다.
 * @param fn 스로틀할 함수
 * @param delayMs 실행 간격 (밀리초)
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;

  return (...args: Parameters<T>) => {
    const now = Date.now();
    if (now - lastCall >= delayMs) {
      lastCall = now;
      fn(...args);
    }
  };
}

/**
 * 반복 실행
 * @param fn 반복 실행할 함수
 * @param interval 반복 간격 (밀리초)
 * @param times 반복 횟수 (기본값: 무한)
 */
export async function repeat<T>(
  fn: () => Promise<T>,
  interval: number,
  times?: number
): Promise<T[]> {
  const results: T[] = [];
  let count = 0;

  while (times === undefined || count < times) {
    try {
      const result = await fn();
      results.push(result);
    } catch (e) {
      throw e;
    }

    if (times === undefined || count < times - 1) {
      await sleep(interval);
    }
    count++;
  }

  return results;
}

/**
 * 작업 순차 실행
 * @param tasks 실행할 작업 배열
 */
export async function sequential<T>(
  tasks: Array<() => Promise<T>>
): Promise<T[]> {
  const results: T[] = [];

  for (const task of tasks) {
    const result = await task();
    results.push(result);
  }

  return results;
}

/**
 * 작업 병렬 실행
 * @param tasks 실행할 작업 배열
 */
export async function parallel<T>(
  tasks: Array<() => Promise<T>>
): Promise<T[]> {
  return Promise.all(tasks.map((task) => task()));
}

/**
 * 조건부 재시도
 * @param fn 실행할 함수
 * @param shouldRetry 재시도 조건
 * @param maxAttempts 최대 시도 횟수
 * @param delayMs 대기 시간
 */
export async function retryIf<T>(
  fn: () => Promise<T>,
  shouldRetry: (error: Error) => boolean,
  maxAttempts: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (e) {
      lastError = e as Error;
      if (shouldRetry(lastError) && attempt < maxAttempts) {
        await sleep(delayMs);
      } else {
        throw lastError;
      }
    }
  }

  throw lastError || new Error('Max attempts reached');
}

/**
 * Timeout과 함께 함수 실행
 * @param fn 실행할 함수
 * @param ms 타임아웃 시간
 */
export async function withTimeout<T>(
  fn: () => Promise<T>,
  ms: number
): Promise<T> {
  return timeout(fn(), ms);
}

export default {
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
};
