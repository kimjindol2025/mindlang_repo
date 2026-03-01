/**
 * Queue - 순차 실행 큐
 *
 * 여러 비동기 작업을 순서대로 실행합니다.
 * FIFO 방식으로 작업을 처리하며, 한 번에 하나의 작업만 실행됩니다.
 */

export class Queue<T> {
  private tasks: Array<() => Promise<T>> = [];
  private running = false;
  private results: T[] = [];
  private processScheduled = false;

  /**
   * 큐에 작업 추가
   */
  enqueue(task: () => Promise<T>): void {
    this.tasks.push(task);
    this.scheduleProcess();
  }

  /**
   * 큐 처리 스케줄
   */
  private scheduleProcess(): void {
    if (this.processScheduled || this.running) return;
    this.processScheduled = true;
    setImmediate(() => {
      this.processScheduled = false;
      this.process();
    });
  }

  /**
   * 큐 처리 시작
   */
  async process(): Promise<void> {
    if (this.running) return;
    this.running = true;

    while (this.tasks.length > 0) {
      const task = this.tasks.shift();
      if (task) {
        try {
          const result = await task();
          this.results.push(result);
        } catch (e) {
          // 에러 발생 시에도 계속 진행
          // console.error('Task error:', e);
        }
      }
    }

    this.running = false;
  }

  /**
   * 큐의 크기
   */
  size(): number {
    return this.tasks.length;
  }

  /**
   * 현재 실행 중인지 확인
   */
  isRunning(): boolean {
    return this.running;
  }

  /**
   * 큐가 비어있는지 확인
   */
  isEmpty(): boolean {
    return this.tasks.length === 0;
  }

  /**
   * 모든 작업 취소
   */
  cancel(): void {
    this.tasks = [];
  }

  /**
   * 큐 초기화
   */
  clear(): void {
    this.tasks = [];
    this.results = [];
  }

  /**
   * 모든 작업 완료 대기
   */
  async waitAll(): Promise<T[]> {
    while (this.running || this.tasks.length > 0) {
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
    return this.results;
  }

  /**
   * 결과 조회
   */
  getResults(): T[] {
    return this.results;
  }
}

export default Queue;
