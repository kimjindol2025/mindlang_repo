/**
 * Semaphore - 동시성 제어
 *
 * 동시에 실행될 수 있는 작업의 개수를 제어합니다.
 * Permit 기반의 동시성 제어로, 일정 개수의 작업만 동시 실행을 허용합니다.
 */

export class Semaphore {
  private permits: number;
  private waiters: Array<() => void> = [];

  /**
   * Semaphore 생성
   * @param permits 동시 실행 허용 개수
   */
  constructor(permits: number) {
    if (permits < 0) {
      throw new Error('Permits must be non-negative');
    }
    this.permits = permits;
  }

  /**
   * Permit 획득
   * Permit이 없으면 대기합니다.
   */
  async acquire(): Promise<void> {
    if (this.permits > 0) {
      this.permits--;
      return;
    }

    return new Promise<void>((resolve) => {
      this.waiters.push(() => {
        this.permits--;
        resolve();
      });
    });
  }

  /**
   * Permit 반환
   */
  release(): void {
    this.permits++;
    if (this.waiters.length > 0) {
      const waiter = this.waiters.shift();
      if (waiter) {
        waiter();
      }
    }
  }

  /**
   * 현재 사용 가능한 Permit 개수
   */
  availablePermits(): number {
    return this.permits;
  }

  /**
   * 대기 중인 작업 개수
   */
  waitingCount(): number {
    return this.waiters.length;
  }

  /**
   * Semaphore를 사용하여 함수 실행
   */
  async run<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }

  /**
   * 모든 대기자를 깨우기
   */
  drainPermits(): number {
    const count = this.permits;
    this.permits = 0;
    return count;
  }

  /**
   * Permit 개수 재설정
   */
  setPermits(permits: number): void {
    if (permits < 0) {
      throw new Error('Permits must be non-negative');
    }
    this.permits = permits;
  }
}

export default Semaphore;
