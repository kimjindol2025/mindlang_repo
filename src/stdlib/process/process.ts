/**
 * Process 모듈 - 자식 프로세스 관리
 *
 * 자식 프로세스 생성, 제어, 모니터링 등의 기능을 제공합니다.
 */

import { spawn as spawnProcess, exec as execProcess, ChildProcess } from 'child_process';
import { promisify } from 'util';
import * as os from 'os';

const execPromise = promisify(execProcess);

export interface ProcessInfo {
  pid: number;
  isRunning: boolean;
  exitCode: number | null;
  signal: string | null;
}

export interface ExecResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

export interface ProcessOptions {
  cwd?: string;
  env?: NodeJS.ProcessEnv;
  timeout?: number;
  maxBuffer?: number;
}

export class Process {
  private child: ChildProcess;
  private exitCode: number | null = null;
  private signal: string | null = null;
  private stdout: string = '';
  private stderr: string = '';

  constructor(command: string, args?: string[], options?: ProcessOptions) {
    this.child = spawnProcess(command, args || [], {
      cwd: options?.cwd,
      env: options?.env,
      stdio: 'pipe',
    });

    // stdout 수집
    if (this.child.stdout) {
      this.child.stdout.on('data', (data) => {
        this.stdout += data.toString();
      });
    }

    // stderr 수집
    if (this.child.stderr) {
      this.child.stderr.on('data', (data) => {
        this.stderr += data.toString();
      });
    }

    // 프로세스 종료 이벤트
    this.child.on('exit', (code, signal) => {
      this.exitCode = code;
      this.signal = signal;
    });

    // 타임아웃 설정
    if (options?.timeout) {
      setTimeout(() => {
        if (this.isRunning()) {
          this.kill();
        }
      }, options.timeout);
    }
  }

  /**
   * 프로세스 ID 반환
   */
  getPid(): number {
    return this.child.pid!;
  }

  /**
   * 프로세스 실행 중 확인
   */
  isRunning(): boolean {
    return !this.child.killed && this.exitCode === null;
  }

  /**
   * 프로세스 종료 코드
   */
  getExitCode(): number | null {
    return this.exitCode;
  }

  /**
   * 프로세스 종료 신호
   */
  getSignal(): string | null {
    return this.signal;
  }

  /**
   * 표준 출력
   */
  getStdout(): string {
    return this.stdout;
  }

  /**
   * 표준 에러
   */
  getStderr(): string {
    return this.stderr;
  }

  /**
   * 프로세스 정보
   */
  getInfo(): ProcessInfo {
    return {
      pid: this.getPid(),
      isRunning: this.isRunning(),
      exitCode: this.exitCode,
      signal: this.signal,
    };
  }

  /**
   * 프로세스 종료 대기
   */
  async wait(): Promise<ProcessInfo> {
    return new Promise((resolve) => {
      if (!this.isRunning()) {
        resolve(this.getInfo());
        return;
      }

      const interval = setInterval(() => {
        if (!this.isRunning()) {
          clearInterval(interval);
          resolve(this.getInfo());
        }
      }, 100);
    });
  }

  /**
   * 프로세스 종료 (SIGTERM)
   */
  kill(signal: string | number = 'SIGTERM'): boolean {
    if (!this.isRunning()) {
      return false;
    }
    this.child.kill(signal as any);
    return true;
  }

  /**
   * 표준 입력에 데이터 쓰기
   */
  write(data: string): void {
    if (this.child.stdin) {
      this.child.stdin.write(data);
    }
  }

  /**
   * 표준 입력 종료
   */
  closeStdin(): void {
    if (this.child.stdin) {
      this.child.stdin.end();
    }
  }

  /**
   * 프로세스 종료 이벤트 핸들러
   */
  onExit(callback: (info: ProcessInfo) => void): void {
    this.child.on('exit', () => {
      callback(this.getInfo());
    });
  }

  /**
   * 에러 이벤트 핸들러
   */
  onError(callback: (error: Error) => void): void {
    this.child.on('error', callback);
  }
}

/**
 * 자식 프로세스 생성
 * @param command 실행할 명령어
 * @param args 명령어 인자
 * @param options 옵션
 */
export function spawn(command: string, args?: string[], options?: ProcessOptions): Process {
  return new Process(command, args, options);
}

/**
 * 명령어 실행 (내용 수집)
 * @param command 실행할 명령어
 * @param options 옵션
 */
export async function exec(command: string, options?: ProcessOptions): Promise<ExecResult> {
  try {
    const result = await execPromise(command, {
      cwd: options?.cwd,
      env: options?.env,
      maxBuffer: options?.maxBuffer || 1024 * 1024 * 10,
      timeout: options?.timeout,
    });

    return {
      stdout: result.stdout,
      stderr: result.stderr,
      exitCode: 0,
    };
  } catch (error: any) {
    return {
      stdout: error.stdout || '',
      stderr: error.stderr || '',
      exitCode: error.code || 1,
    };
  }
}

/**
 * 현재 프로세스 ID
 */
export function pid(): number {
  return process.pid;
}

/**
 * 현재 프로세스 메모리 사용량
 */
export function memoryUsage(): { rss: number; heapTotal: number; heapUsed: number; external: number } {
  const usage = process.memoryUsage();
  return {
    rss: usage.rss,
    heapTotal: usage.heapTotal,
    heapUsed: usage.heapUsed,
    external: usage.external,
  };
}

/**
 * CPU 코어 수
 */
export function cpuCount(): number {
  return os.cpus().length;
}

/**
 * 시스템 로드 평균
 */
export function loadAverage(): number[] {
  return os.loadavg();
}

/**
 * 가용 메모리
 */
export function freeMemory(): number {
  return os.freemem();
}

/**
 * 총 메모리
 */
export function totalMemory(): number {
  return os.totalmem();
}

/**
 * 프로세스 환경 변수 접근
 */
export function env(key: string): string | undefined {
  return process.env[key];
}

/**
 * 프로세스 환경 변수 설정
 */
export function setEnv(key: string, value: string): void {
  process.env[key] = value;
}

/**
 * 프로세스 종료
 */
export function exit(code: number = 0): void {
  process.exit(code);
}

/**
 * 프로세스 업타임 (초)
 */
export function uptime(): number {
  return process.uptime();
}

/**
 * 현재 작업 디렉토리
 */
export function cwd(): string {
  return process.cwd();
}

/**
 * 작업 디렉토리 변경
 */
export function chdir(path: string): void {
  process.chdir(path);
}

/**
 * 아키텍처 정보
 */
export function arch(): string {
  return process.arch;
}

/**
 * 플랫폼 정보
 */
export function platform(): string {
  return process.platform;
}

/**
 * 노드 버전
 */
export function version(): string {
  return process.version;
}

export default {
  spawn,
  exec,
  pid,
  memoryUsage,
  cpuCount,
  loadAverage,
  freeMemory,
  totalMemory,
  env,
  setEnv,
  exit,
  uptime,
  cwd,
  chdir,
  arch,
  platform,
  version,
  Process,
};
