/**
 * Stream 모듈 - 파일 및 데이터 스트림 처리
 *
 * 파일 스트림, 읽기 스트림, 쓰기 스트림 등의 기능을 제공합니다.
 */

import * as fs from 'fs';
import * as path from 'path';
import { Transform, Readable, Writable } from 'stream';

export interface StreamOptions {
  encoding?: BufferEncoding;
  highWaterMark?: number;
  start?: number;
  end?: number;
}

export class ReadStream {
  private stream: fs.ReadStream | null = null;
  private chunks: Buffer[] = [];
  private size: number = 0;
  private dataHandlers: ((data: Buffer) => void)[] = [];
  private endHandlers: (() => void)[] = [];
  private errorHandlers: ((error: Error) => void)[] = [];

  constructor(
    private filePath: string,
    private options?: StreamOptions
  ) {}

  /**
   * 스트림 시작
   */
  start(): void {
    this.stream = fs.createReadStream(this.filePath, {
      encoding: undefined, // Buffer로 처리
      highWaterMark: this.options?.highWaterMark || 64 * 1024,
      start: this.options?.start,
      end: this.options?.end,
    });

    this.stream.on('data', (chunk) => {
      this.chunks.push(chunk as Buffer);
      this.size += (chunk as Buffer).length;
      this.dataHandlers.forEach((handler) => handler(chunk as Buffer));
    });

    this.stream.on('end', () => {
      this.endHandlers.forEach((handler) => handler());
    });

    this.stream.on('error', (err) => {
      this.errorHandlers.forEach((handler) => handler(err));
    });
  }

  /**
   * 스트림 일시 중지
   */
  pause(): void {
    if (this.stream) {
      this.stream.pause();
    }
  }

  /**
   * 스트림 재개
   */
  resume(): void {
    if (this.stream) {
      this.stream.resume();
    }
  }

  /**
   * 스트림 종료
   */
  destroy(): void {
    if (this.stream) {
      this.stream.destroy();
    }
  }

  /**
   * 데이터 핸들러 등록
   */
  onData(handler: (data: Buffer) => void): void {
    this.dataHandlers.push(handler);
  }

  /**
   * 종료 핸들러 등록
   */
  onEnd(handler: () => void): void {
    this.endHandlers.push(handler);
  }

  /**
   * 에러 핸들러 등록
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 모든 청크 조회
   */
  getChunks(): Buffer[] {
    return this.chunks;
  }

  /**
   * 전체 데이터 조회
   */
  getData(): Buffer {
    return Buffer.concat(this.chunks);
  }

  /**
   * 전체 데이터 문자열로 조회
   */
  getString(): string {
    return this.getData().toString(this.options?.encoding || 'utf8');
  }

  /**
   * 스트림 크기
   */
  getSize(): number {
    return this.size;
  }

  /**
   * 모든 데이터 읽기 대기
   */
  async read(): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      if (!this.stream) {
        reject(new Error('Stream not started'));
        return;
      }

      this.onEnd(() => {
        resolve(this.getData());
      });

      this.onError(reject);
    });
  }
}

export class WriteStream {
  private stream: fs.WriteStream | null = null;
  private written: number = 0;
  private errorHandlers: ((error: Error) => void)[] = [];
  private finishHandlers: (() => void)[] = [];

  constructor(
    private filePath: string,
    private options?: StreamOptions
  ) {}

  /**
   * 스트림 시작
   */
  start(): void {
    this.stream = fs.createWriteStream(this.filePath, {
      encoding: this.options?.encoding || 'utf8',
      highWaterMark: this.options?.highWaterMark || 16 * 1024,
    });

    this.stream.on('finish', () => {
      this.finishHandlers.forEach((handler) => handler());
    });

    this.stream.on('error', (err) => {
      this.errorHandlers.forEach((handler) => handler(err));
    });
  }

  /**
   * 데이터 쓰기
   */
  write(data: string | Buffer): boolean {
    if (!this.stream) {
      throw new Error('Stream not started');
    }

    const buffer = typeof data === 'string' ? Buffer.from(data) : data;
    this.written += buffer.length;

    return this.stream.write(data);
  }

  /**
   * 스트림 종료
   */
  end(): void {
    if (this.stream) {
      this.stream.end();
    }
  }

  /**
   * 스트림 종료 대기
   */
  async finish(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.onFinish(() => resolve());
      this.onError(reject);
    });
  }

  /**
   * 종료 핸들러 등록
   */
  onFinish(handler: () => void): void {
    this.finishHandlers.push(handler);
  }

  /**
   * 에러 핸들러 등록
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 쓴 바이트 수
   */
  getWritten(): number {
    return this.written;
  }
}

export class TransformStream {
  private transformStream: Transform;

  constructor(
    private transformFn: (chunk: Buffer, encoding: string) => Buffer | string | null
  ) {
    this.transformStream = new Transform({
      transform: (chunk, encoding, callback) => {
        try {
          const result = this.transformFn(chunk, encoding);
          callback(null, result);
        } catch (error) {
          callback(error as Error);
        }
      },
    });
  }

  /**
   * 데이터 변환
   */
  async transform(data: Buffer): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = [];

      this.transformStream.on('data', (chunk) => {
        chunks.push(chunk);
      });

      this.transformStream.on('end', () => {
        resolve(Buffer.concat(chunks));
      });

      this.transformStream.on('error', reject);

      this.transformStream.write(data);
      this.transformStream.end();
    });
  }

  /**
   * Transform 스트림 객체 조회
   */
  getStream(): Transform {
    return this.transformStream;
  }
}

export class BufferStream {
  private chunks: Buffer[] = [];
  private position: number = 0;

  constructor(initialData?: Buffer) {
    if (initialData) {
      this.chunks.push(initialData);
    }
  }

  /**
   * 데이터 추가
   */
  write(data: Buffer | string): void {
    const buffer = typeof data === 'string' ? Buffer.from(data) : data;
    this.chunks.push(buffer);
  }

  /**
   * 지정된 크기만큼 읽기
   */
  read(size: number): Buffer {
    const buffer = Buffer.concat(this.chunks);
    const result = buffer.slice(this.position, this.position + size);
    this.position += result.length;
    return result;
  }

  /**
   * 모든 데이터 읽기
   */
  readAll(): Buffer {
    return Buffer.concat(this.chunks);
  }

  /**
   * 남은 데이터 읽기
   */
  readRemaining(): Buffer {
    const buffer = Buffer.concat(this.chunks);
    const result = buffer.slice(this.position);
    this.position = buffer.length;
    return result;
  }

  /**
   * 위치 설정
   */
  seek(position: number): void {
    this.position = position;
  }

  /**
   * 현재 위치
   */
  getPosition(): number {
    return this.position;
  }

  /**
   * 스트림 크기
   */
  getSize(): number {
    return Buffer.concat(this.chunks).length;
  }

  /**
   * 스트림 초기화
   */
  clear(): void {
    this.chunks = [];
    this.position = 0;
  }

  /**
   * 끝에 도달했는지 확인
   */
  isEOF(): boolean {
    return this.position >= this.getSize();
  }
}

/**
 * 파일 읽기 스트림 생성
 */
export function createReadStream(filePath: string, options?: StreamOptions): ReadStream {
  return new ReadStream(filePath, options);
}

/**
 * 파일 쓰기 스트림 생성
 */
export function createWriteStream(filePath: string, options?: StreamOptions): WriteStream {
  return new WriteStream(filePath, options);
}

/**
 * 변환 스트림 생성
 */
export function createTransformStream(
  transformFn: (chunk: Buffer, encoding: string) => Buffer | string | null
): TransformStream {
  return new TransformStream(transformFn);
}

/**
 * 버퍼 스트림 생성
 */
export function createBufferStream(initialData?: Buffer): BufferStream {
  return new BufferStream(initialData);
}

/**
 * 파일 복사 (스트림 기반)
 */
export async function copyFileStream(source: string, destination: string): Promise<void> {
  const readStream = createReadStream(source);
  const writeStream = createWriteStream(destination);

  readStream.start();
  writeStream.start();

  return new Promise((resolve, reject) => {
    readStream.onEnd(() => {
      writeStream.write(readStream.getData());
      writeStream.end();
    });

    writeStream.onFinish(() => {
      resolve();
    });

    readStream.onError(reject);
    writeStream.onError(reject);
  });
}

export default {
  createReadStream,
  createWriteStream,
  createTransformStream,
  createBufferStream,
  copyFileStream,
  ReadStream,
  WriteStream,
  TransformStream,
  BufferStream,
};
