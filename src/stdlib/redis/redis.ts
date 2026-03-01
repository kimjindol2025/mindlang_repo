/**
 * Redis 모듈 - 캐시 및 메시지 큐
 *
 * 인메모리 캐시와 메시지 큐 기능을 제공합니다.
 */

export interface CacheItem {
  value: any;
  expiresAt?: number;
}

export interface QueueItem {
  id: string;
  data: any;
  timestamp: number;
}

export class Cache {
  private data: Map<string, CacheItem> = new Map();
  private subscribers: Map<string, Set<(value: any) => void>> = new Map();

  /**
   * 값 설정
   * @param key 키
   * @param value 값
   * @param ttl TTL (밀리초)
   */
  set(key: string, value: any, ttl?: number): void {
    let expiresAt: number | undefined;

    if (ttl) {
      expiresAt = Date.now() + ttl;
    }

    this.data.set(key, { value, expiresAt });
    this.notifySubscribers(key, value);
  }

  /**
   * 값 조회
   * @param key 키
   */
  get(key: string): any {
    const item = this.data.get(key);

    if (!item) {
      return null;
    }

    // 만료 확인
    if (item.expiresAt && Date.now() > item.expiresAt) {
      this.data.delete(key);
      return null;
    }

    return item.value;
  }

  /**
   * 키 존재 확인
   * @param key 키
   */
  has(key: string): boolean {
    const item = this.data.get(key);

    if (!item) {
      return false;
    }

    // 만료 확인
    if (item.expiresAt && Date.now() > item.expiresAt) {
      this.data.delete(key);
      return false;
    }

    return true;
  }

  /**
   * 값 삭제
   * @param key 키
   */
  delete(key: string): boolean {
    return this.data.delete(key);
  }

  /**
   * 모든 키 조회
   */
  keys(): string[] {
    const keys: string[] = [];

    for (const key of this.data.keys()) {
      if (this.has(key)) {
        keys.push(key);
      }
    }

    return keys;
  }

  /**
   * 캐시 초기화
   */
  clear(): void {
    this.data.clear();
    this.subscribers.clear();
  }

  /**
   * 캐시 크기
   */
  size(): number {
    return Array.from(this.data.keys()).filter((key) => this.has(key)).length;
  }

  /**
   * 값 증가
   * @param key 키
   * @param delta 증가량
   */
  increment(key: string, delta: number = 1): number {
    const value = this.get(key) || 0;
    const newValue = value + delta;
    this.set(key, newValue);
    return newValue;
  }

  /**
   * 값 감소
   * @param key 키
   * @param delta 감소량
   */
  decrement(key: string, delta: number = 1): number {
    return this.increment(key, -delta);
  }

  /**
   * 값 추가 (목록)
   * @param key 키
   * @param values 값들
   */
  push(key: string, ...values: any[]): number {
    const list = this.get(key) || [];
    const newList = [...list, ...values];
    this.set(key, newList);
    return newList.length;
  }

  /**
   * 값 제거 (목록)
   * @param key 키
   */
  pop(key: string): any {
    const list = this.get(key);

    if (!Array.isArray(list) || list.length === 0) {
      return null;
    }

    const value = list.pop();
    this.set(key, list);
    return value;
  }

  /**
   * 목록 길이
   * @param key 키
   */
  listLength(key: string): number {
    const list = this.get(key);
    return Array.isArray(list) ? list.length : 0;
  }

  /**
   * 값 구독
   * @param key 키
   * @param callback 콜백
   */
  subscribe(key: string, callback: (value: any) => void): void {
    if (!this.subscribers.has(key)) {
      this.subscribers.set(key, new Set());
    }

    this.subscribers.get(key)!.add(callback);
  }

  /**
   * 구독 취소
   * @param key 키
   * @param callback 콜백
   */
  unsubscribe(key: string, callback: (value: any) => void): void {
    const subscribers = this.subscribers.get(key);

    if (subscribers) {
      subscribers.delete(callback);
    }
  }

  /**
   * 구독자에게 알림
   */
  private notifySubscribers(key: string, value: any): void {
    const subscribers = this.subscribers.get(key);

    if (subscribers) {
      for (const callback of subscribers) {
        callback(value);
      }
    }
  }

  /**
   * TTL 조회
   * @param key 키
   */
  ttl(key: string): number {
    const item = this.data.get(key);

    if (!item) {
      return -2;
    }

    if (!item.expiresAt) {
      return -1;
    }

    const remaining = item.expiresAt - Date.now();
    return remaining > 0 ? remaining : -2;
  }

  /**
   * 만료 시간 설정
   * @param key 키
   * @param ttl TTL (밀리초)
   */
  expire(key: string, ttl: number): boolean {
    const item = this.data.get(key);

    if (!item) {
      return false;
    }

    item.expiresAt = Date.now() + ttl;
    return true;
  }
}

export class Queue {
  private items: QueueItem[] = [];
  private idCounter: number = 0;

  /**
   * 항목 추가
   * @param data 데이터
   */
  push(data: any): string {
    const id = `item-${++this.idCounter}`;
    this.items.push({
      id,
      data,
      timestamp: Date.now(),
    });
    return id;
  }

  /**
   * 항목 제거
   */
  pop(): QueueItem | null {
    if (this.items.length === 0) {
      return null;
    }

    return this.items.shift() || null;
  }

  /**
   * 큐 크기
   */
  size(): number {
    return this.items.length;
  }

  /**
   * 모든 항목 조회
   */
  getAll(): QueueItem[] {
    return [...this.items];
  }

  /**
   * 큐 초기화
   */
  clear(): void {
    this.items = [];
  }

  /**
   * 항목 조회 (ID로)
   * @param id 항목 ID
   */
  getById(id: string): QueueItem | null {
    return this.items.find((item) => item.id === id) || null;
  }

  /**
   * 항목 제거 (ID로)
   * @param id 항목 ID
   */
  removeById(id: string): boolean {
    const index = this.items.findIndex((item) => item.id === id);

    if (index === -1) {
      return false;
    }

    this.items.splice(index, 1);
    return true;
  }

  /**
   * 우선순위 큐 항목 추가
   * @param data 데이터
   * @param priority 우선순위 (높을수록 먼저)
   */
  pushWithPriority(data: any, priority: number): string {
    const id = `item-${++this.idCounter}`;
    const item: any = {
      id,
      data,
      timestamp: Date.now(),
      priority,
    };

    let inserted = false;

    for (let i = 0; i < this.items.length; i++) {
      if (((this.items[i] as any).priority || 0) < priority) {
        this.items.splice(i, 0, item);
        inserted = true;
        break;
      }
    }

    if (!inserted) {
      this.items.push(item);
    }

    return id;
  }
}

/**
 * 캐시 인스턴스 생성
 */
export function createCache(): Cache {
  return new Cache();
}

/**
 * 큐 인스턴스 생성
 */
export function createQueue(): Queue {
  return new Queue();
}

export default {
  createCache,
  createQueue,
  Cache,
  Queue,
};
