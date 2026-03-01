/**
 * DB 모듈 - 데이터베이스 접근
 *
 * SQLite 기반 간단한 CRUD 작업을 제공합니다.
 */

export interface QueryResult {
  id?: string | number;
  [key: string]: any;
}

export interface QueryOptions {
  limit?: number;
  offset?: number;
  orderBy?: string;
  orderDir?: 'ASC' | 'DESC';
}

export class Database {
  private data: Map<string, Map<string | number, QueryResult>> = new Map();
  private counters: Map<string, number> = new Map();

  /**
   * 테이블 생성
   * @param tableName 테이블명
   */
  createTable(tableName: string): void {
    if (!this.data.has(tableName)) {
      this.data.set(tableName, new Map());
      this.counters.set(tableName, 0);
    }
  }

  /**
   * 테이블 존재 확인
   * @param tableName 테이블명
   */
  tableExists(tableName: string): boolean {
    return this.data.has(tableName);
  }

  /**
   * 테이블 삭제
   * @param tableName 테이블명
   */
  dropTable(tableName: string): void {
    this.data.delete(tableName);
    this.counters.delete(tableName);
  }

  /**
   * 모든 테이블 나열
   */
  listTables(): string[] {
    return Array.from(this.data.keys());
  }

  /**
   * 데이터 삽입
   * @param tableName 테이블명
   * @param data 데이터
   */
  insert(tableName: string, data: QueryResult): QueryResult {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    const id = (this.counters.get(tableName) || 0) + 1;
    this.counters.set(tableName, id);

    const record = { ...data, id };
    table.set(id, record);
    return record;
  }

  /**
   * 데이터 일괄 삽입
   * @param tableName 테이블명
   * @param dataArray 데이터 배열
   */
  insertMany(tableName: string, dataArray: QueryResult[]): QueryResult[] {
    return dataArray.map((data) => this.insert(tableName, data));
  }

  /**
   * 데이터 조회 (ID로)
   * @param tableName 테이블명
   * @param id ID
   */
  findById(tableName: string, id: string | number): QueryResult | null {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    return table.get(id) || null;
  }

  /**
   * 모든 데이터 조회
   * @param tableName 테이블명
   * @param options 옵션
   */
  findAll(tableName: string, options?: QueryOptions): QueryResult[] {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    let results = Array.from(table.values());

    // 정렬
    if (options?.orderBy) {
      results.sort((a, b) => {
        const aVal = a[options.orderBy!];
        const bVal = b[options.orderBy!];

        if (aVal < bVal) return options.orderDir === 'DESC' ? 1 : -1;
        if (aVal > bVal) return options.orderDir === 'DESC' ? -1 : 1;
        return 0;
      });
    }

    // 오프셋 및 리미트
    const offset = options?.offset || 0;
    const limit = options?.limit;

    if (limit) {
      return results.slice(offset, offset + limit);
    }
    return results.slice(offset);
  }

  /**
   * 조건으로 조회
   * @param tableName 테이블명
   * @param condition 조건 함수
   */
  find(tableName: string, condition: (record: QueryResult) => boolean): QueryResult[] {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    const results: QueryResult[] = [];

    for (const record of table.values()) {
      if (condition(record)) {
        results.push(record);
      }
    }

    return results;
  }

  /**
   * 단일 조건 조회
   * @param tableName 테이블명
   * @param condition 조건 함수
   */
  findOne(tableName: string, condition: (record: QueryResult) => boolean): QueryResult | null {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;

    for (const record of table.values()) {
      if (condition(record)) {
        return record;
      }
    }

    return null;
  }

  /**
   * 데이터 업데이트
   * @param tableName 테이블명
   * @param id ID
   * @param data 업데이트 데이터
   */
  update(tableName: string, id: string | number, data: Partial<QueryResult>): QueryResult | null {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    const record = table.get(id);

    if (!record) {
      return null;
    }

    const updated = { ...record, ...data, id };
    table.set(id, updated);
    return updated;
  }

  /**
   * 조건으로 업데이트
   * @param tableName 테이블명
   * @param condition 조건 함수
   * @param data 업데이트 데이터
   */
  updateWhere(tableName: string, condition: (record: QueryResult) => boolean, data: Partial<QueryResult>): number {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    let count = 0;

    for (const [id, record] of table.entries()) {
      if (condition(record)) {
        const updated = { ...record, ...data };
        table.set(id, updated);
        count++;
      }
    }

    return count;
  }

  /**
   * 데이터 삭제
   * @param tableName 테이블명
   * @param id ID
   */
  delete(tableName: string, id: string | number): boolean {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    return table.delete(id);
  }

  /**
   * 조건으로 삭제
   * @param tableName 테이블명
   * @param condition 조건 함수
   */
  deleteWhere(tableName: string, condition: (record: QueryResult) => boolean): number {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    const idsToDelete: (string | number)[] = [];

    for (const [id, record] of table.entries()) {
      if (condition(record)) {
        idsToDelete.push(id);
      }
    }

    for (const id of idsToDelete) {
      table.delete(id);
    }

    return idsToDelete.length;
  }

  /**
   * 테이블 행 수
   * @param tableName 테이블명
   */
  count(tableName: string): number {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    return this.data.get(tableName)!.size;
  }

  /**
   * 조건 행 수
   * @param tableName 테이블명
   * @param condition 조건 함수
   */
  countWhere(tableName: string, condition: (record: QueryResult) => boolean): number {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    const table = this.data.get(tableName)!;
    let count = 0;

    for (const record of table.values()) {
      if (condition(record)) {
        count++;
      }
    }

    return count;
  }

  /**
   * 테이블 초기화
   * @param tableName 테이블명
   */
  truncate(tableName: string): void {
    if (!this.tableExists(tableName)) {
      throw new Error(`Table not found: ${tableName}`);
    }

    this.data.get(tableName)!.clear();
    this.counters.set(tableName, 0);
  }

  /**
   * 데이터 내보내기
   * @param tableName 테이블명
   */
  export(tableName: string): QueryResult[] {
    return this.findAll(tableName);
  }

  /**
   * 데이터 가져오기
   * @param tableName 테이블명
   * @param dataArray 데이터 배열
   */
  import(tableName: string, dataArray: QueryResult[]): void {
    this.createTable(tableName);
    for (const data of dataArray) {
      this.insert(tableName, data);
    }
  }
}

/**
 * 인메모리 데이터베이스 인스턴스 생성
 */
export function createDatabase(): Database {
  return new Database();
}

export default {
  createDatabase,
  Database,
};
