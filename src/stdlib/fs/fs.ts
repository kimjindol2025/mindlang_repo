/**
 * FS 모듈 - 파일 시스템 접근
 *
 * 파일 읽기/쓰기, 디렉토리 조작 등의 파일 시스템 작업을 수행합니다.
 */

import * as fs from 'fs';
import * as path from 'path';
import { promisify } from 'util';

// Promise 기반 함수로 변환
const readFile = promisify(fs.readFile);
const writeFile = promisify(fs.writeFile);
const appendFile = promisify(fs.appendFile);
const mkdir = promisify(fs.mkdir);
const readdir = promisify(fs.readdir);
const stat = promisify(fs.stat);
const unlink = promisify(fs.unlink);
const rename = promisify(fs.rename);
const rmdir = promisify(fs.rmdir);
const chmod = promisify(fs.chmod);
const lstat = promisify(fs.lstat);

export interface FileStats {
  size: number;
  isFile: boolean;
  isDirectory: boolean;
  isSymbolicLink: boolean;
  created: Date;
  modified: Date;
  accessed: Date;
}

export interface ReadOptions {
  encoding?: BufferEncoding;
  flag?: string;
}

export interface WriteOptions {
  encoding?: BufferEncoding;
  flag?: string;
  mode?: number;
}

/**
 * 파일 읽기
 * @param filePath 파일 경로
 * @param encoding 인코딩 (기본값: 'utf8')
 */
export async function readFile_(filePath: string, encoding: BufferEncoding = 'utf8'): Promise<string> {
  try {
    return await readFile(filePath, encoding);
  } catch (e) {
    throw new Error(`Failed to read file: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 쓰기
 * @param filePath 파일 경로
 * @param content 파일 내용
 * @param encoding 인코딩 (기본값: 'utf8')
 */
export async function writeFile_(
  filePath: string,
  content: string | Buffer,
  encoding: BufferEncoding = 'utf8'
): Promise<void> {
  try {
    await writeFile(filePath, content, encoding);
  } catch (e) {
    throw new Error(`Failed to write file: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 파일에 내용 추가
 * @param filePath 파일 경로
 * @param content 추가할 내용
 * @param encoding 인코딩 (기본값: 'utf8')
 */
export async function appendFile_(
  filePath: string,
  content: string | Buffer,
  encoding: BufferEncoding = 'utf8'
): Promise<void> {
  try {
    await appendFile(filePath, content, encoding);
  } catch (e) {
    throw new Error(`Failed to append to file: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 삭제
 * @param filePath 파일 경로
 */
export async function deleteFile(filePath: string): Promise<void> {
  try {
    await unlink(filePath);
  } catch (e) {
    throw new Error(`Failed to delete file: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 존재 확인
 * @param filePath 파일 경로
 */
export async function exists(filePath: string): Promise<boolean> {
  try {
    await stat(filePath);
    return true;
  } catch {
    return false;
  }
}

/**
 * 파일 정보 조회
 * @param filePath 파일 경로
 */
export async function getStats(filePath: string): Promise<FileStats> {
  try {
    const stats = await stat(filePath);
    return {
      size: stats.size,
      isFile: stats.isFile(),
      isDirectory: stats.isDirectory(),
      isSymbolicLink: stats.isSymbolicLink(),
      created: new Date(stats.birthtime),
      modified: new Date(stats.mtime),
      accessed: new Date(stats.atime),
    };
  } catch (e) {
    throw new Error(`Failed to get stats: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 디렉토리 생성
 * @param dirPath 디렉토리 경로
 * @param recursive 재귀 생성 여부 (기본값: false)
 */
export async function mkdir_(dirPath: string, recursive: boolean = false): Promise<void> {
  try {
    await mkdir(dirPath, { recursive });
  } catch (e) {
    throw new Error(`Failed to create directory: ${dirPath} - ${(e as Error).message}`);
  }
}

/**
 * 디렉토리 읽기
 * @param dirPath 디렉토리 경로
 */
export async function readDir(dirPath: string): Promise<string[]> {
  try {
    return await readdir(dirPath);
  } catch (e) {
    throw new Error(`Failed to read directory: ${dirPath} - ${(e as Error).message}`);
  }
}

/**
 * 디렉토리 내의 모든 파일 (재귀)
 * @param dirPath 디렉토리 경로
 */
export async function readDirRecursive(dirPath: string): Promise<string[]> {
  const files: string[] = [];

  async function walk(dir: string) {
    const entries = await readdir(dir);

    for (const entry of entries) {
      const fullPath = path.join(dir, entry);
      const stats = await stat(fullPath);

      if (stats.isFile()) {
        files.push(fullPath);
      } else if (stats.isDirectory()) {
        await walk(fullPath);
      }
    }
  }

  try {
    await walk(dirPath);
    return files;
  } catch (e) {
    throw new Error(`Failed to read directory recursively: ${dirPath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 복사
 * @param source 소스 경로
 * @param destination 대상 경로
 */
export async function copyFile(source: string, destination: string): Promise<void> {
  try {
    const content = await readFile(source);
    await writeFile(destination, content);
  } catch (e) {
    throw new Error(`Failed to copy file: ${source} -> ${destination} - ${(e as Error).message}`);
  }
}

/**
 * 파일 이름 변경
 * @param oldPath 이전 경로
 * @param newPath 새 경로
 */
export async function rename_(oldPath: string, newPath: string): Promise<void> {
  try {
    await rename(oldPath, newPath);
  } catch (e) {
    throw new Error(`Failed to rename file: ${oldPath} -> ${newPath} - ${(e as Error).message}`);
  }
}

/**
 * 디렉토리 삭제
 * @param dirPath 디렉토리 경로
 */
export async function deleteDir(dirPath: string): Promise<void> {
  try {
    await rmdir(dirPath);
  } catch (e) {
    throw new Error(`Failed to delete directory: ${dirPath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 권한 변경
 * @param filePath 파일 경로
 * @param mode 권한 (8진수)
 */
export async function chmod_(filePath: string, mode: number): Promise<void> {
  try {
    await chmod(filePath, mode);
  } catch (e) {
    throw new Error(`Failed to change permissions: ${filePath} - ${(e as Error).message}`);
  }
}

/**
 * 파일 또는 디렉토리인지 확인
 * @param filePath 경로
 */
export async function isFile(filePath: string): Promise<boolean> {
  try {
    const stats = await stat(filePath);
    return stats.isFile();
  } catch {
    return false;
  }
}

/**
 * 디렉토리인지 확인
 * @param filePath 경로
 */
export async function isDir(filePath: string): Promise<boolean> {
  try {
    const stats = await stat(filePath);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

/**
 * 상대 경로 연결
 * @param base 기본 경로
 * @param relative 상대 경로
 */
export function join(base: string, relative: string): string {
  return path.join(base, relative);
}

/**
 * 경로 분석
 * @param filePath 경로
 */
export function parsePath(filePath: string): {
  dir: string;
  base: string;
  name: string;
  ext: string;
} {
  const parsed = path.parse(filePath);
  return {
    dir: parsed.dir,
    base: parsed.base,
    name: parsed.name,
    ext: parsed.ext,
  };
}

/**
 * 절대 경로 반환
 * @param filePath 경로
 */
export function resolve(filePath: string): string {
  return path.resolve(filePath);
}

/**
 * 현재 작업 디렉토리
 */
export function cwd(): string {
  return process.cwd();
}

export default {
  readFile: readFile_,
  writeFile: writeFile_,
  appendFile: appendFile_,
  deleteFile,
  exists,
  getStats,
  mkdir: mkdir_,
  readDir,
  readDirRecursive,
  copyFile,
  rename: rename_,
  deleteDir,
  chmod: chmod_,
  isFile,
  isDir,
  join,
  parsePath,
  resolve,
  cwd,
};
