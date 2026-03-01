/**
 * Crypto 모듈 - 암호화, 해싱, 압축
 *
 * 데이터 암호화, 해싱, 압축 및 검증 기능을 제공합니다.
 */

import * as crypto from 'crypto';
import * as zlib from 'zlib';
import { promisify } from 'util';

const gzip = promisify(zlib.gzip);
const gunzip = promisify(zlib.gunzip);

// 해싱 알고리즘
export type HashAlgorithm = 'md5' | 'sha1' | 'sha256' | 'sha512';

// 대칭 암호화 알고리즘
export type CipherAlgorithm = 'aes-256-cbc' | 'aes-192-cbc' | 'aes-128-cbc';

/**
 * 해시 계산
 * @param data 데이터
 * @param algorithm 해시 알고리즘
 */
export function hash(data: string | Buffer, algorithm: HashAlgorithm = 'sha256'): string {
  const hash = crypto.createHash(algorithm);
  hash.update(data);
  return hash.digest('hex');
}

/**
 * HMAC 생성
 * @param data 데이터
 * @param secret 비밀 키
 * @param algorithm 해시 알고리즘
 */
export function hmac(
  data: string | Buffer,
  secret: string | Buffer,
  algorithm: HashAlgorithm = 'sha256'
): string {
  const hmac = crypto.createHmac(algorithm, secret);
  hmac.update(data);
  return hmac.digest('hex');
}

/**
 * 해시 검증
 * @param data 데이터
 * @param expectedHash 예상 해시값
 * @param algorithm 해시 알고리즘
 */
export function verifyHash(
  data: string | Buffer,
  expectedHash: string,
  algorithm: HashAlgorithm = 'sha256'
): boolean {
  const computed = hash(data, algorithm);
  return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(expectedHash));
}

/**
 * HMAC 검증
 * @param data 데이터
 * @param expectedHmac 예상 HMAC
 * @param secret 비밀 키
 * @param algorithm 해시 알고리즘
 */
export function verifyHmac(
  data: string | Buffer,
  expectedHmac: string,
  secret: string | Buffer,
  algorithm: HashAlgorithm = 'sha256'
): boolean {
  const computed = hmac(data, secret, algorithm);
  return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(expectedHmac));
}

/**
 * 난수 생성
 * @param size 바이트 크기
 */
export function randomBytes(size: number): string {
  return crypto.randomBytes(size).toString('hex');
}

/**
 * 난수 버퍼 생성
 * @param size 바이트 크기
 */
export function randomBytesBuffer(size: number): Buffer {
  return crypto.randomBytes(size);
}

/**
 * UUID v4 생성
 */
export function randomUUID(): string {
  return crypto.randomUUID();
}

/**
 * 대칭 암호화
 * @param data 평문
 * @param key 암호화 키 (32바이트 for aes-256)
 * @param iv 초기화 벡터 (16바이트)
 */
export function encrypt(
  data: string | Buffer,
  key: string | Buffer,
  iv?: string | Buffer,
  algorithm: CipherAlgorithm = 'aes-256-cbc'
): string {
  const keyBuffer = typeof key === 'string' ? Buffer.from(key, 'hex') : key;
  const ivBuffer = iv ? (typeof iv === 'string' ? Buffer.from(iv, 'hex') : iv) : crypto.randomBytes(16);

  const cipher = crypto.createCipheriv(algorithm, keyBuffer, ivBuffer);

  let encrypted = cipher.update(data);
  encrypted = Buffer.concat([encrypted, cipher.final()]);

  // IV + encrypted data (hex)
  return ivBuffer.toString('hex') + ':' + encrypted.toString('hex');
}

/**
 * 대칭 복호화
 * @param encrypted 암호문 (IV:encrypted 형식)
 * @param key 복호화 키
 */
export function decrypt(
  encrypted: string,
  key: string | Buffer,
  algorithm: CipherAlgorithm = 'aes-256-cbc'
): string {
  const keyBuffer = typeof key === 'string' ? Buffer.from(key, 'hex') : key;

  const parts = encrypted.split(':');
  const ivBuffer = Buffer.from(parts[0], 'hex');
  const encryptedBuffer = Buffer.from(parts[1], 'hex');

  const decipher = crypto.createDecipheriv(algorithm, keyBuffer, ivBuffer);

  let decrypted = decipher.update(encryptedBuffer);
  decrypted = Buffer.concat([decrypted, decipher.final()]);

  return decrypted.toString('utf8');
}

/**
 * gzip 압축
 * @param data 데이터
 */
export async function compress(data: string | Buffer): Promise<Buffer> {
  const buffer = typeof data === 'string' ? Buffer.from(data, 'utf8') : data;
  return await gzip(buffer);
}

/**
 * gzip 압축 해제
 * @param data 압축된 데이터
 */
export async function decompress(data: Buffer): Promise<Buffer> {
  return await gunzip(data);
}

/**
 * 압축 문자열화
 * @param data 데이터
 */
export async function compressString(data: string): Promise<string> {
  const compressed = await compress(data);
  return compressed.toString('base64');
}

/**
 * 압축 해제 문자열화
 * @param data 압축된 데이터 (base64)
 */
export async function decompressString(data: string): Promise<string> {
  const buffer = Buffer.from(data, 'base64');
  const decompressed = await decompress(buffer);
  return decompressed.toString('utf8');
}

/**
 * Base64 인코딩
 * @param data 데이터
 */
export function base64Encode(data: string | Buffer): string {
  const buffer = typeof data === 'string' ? Buffer.from(data, 'utf8') : data;
  return buffer.toString('base64');
}

/**
 * Base64 디코딩
 * @param data Base64 문자열
 */
export function base64Decode(data: string): string {
  return Buffer.from(data, 'base64').toString('utf8');
}

/**
 * Hex 인코딩
 * @param data 데이터
 */
export function hexEncode(data: string | Buffer): string {
  const buffer = typeof data === 'string' ? Buffer.from(data, 'utf8') : data;
  return buffer.toString('hex');
}

/**
 * Hex 디코딩
 * @param data Hex 문자열
 */
export function hexDecode(data: string): string {
  return Buffer.from(data, 'hex').toString('utf8');
}

/**
 * URL Safe Base64 인코딩
 * @param data 데이터
 */
export function urlSafeBase64Encode(data: string | Buffer): string {
  const encoded = base64Encode(data);
  return encoded.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

/**
 * URL Safe Base64 디코딩
 * @param data URL Safe Base64 문자열
 */
export function urlSafeBase64Decode(data: string): string {
  let base64 = data.replace(/-/g, '+').replace(/_/g, '/');
  // Padding 추가
  const padding = 4 - (base64.length % 4);
  if (padding !== 4) {
    base64 += '='.repeat(padding);
  }
  return base64Decode(base64);
}

/**
 * 암호화 키 생성
 * @param size 바이트 크기 (기본 32 for AES-256)
 */
export function generateKey(size: number = 32): string {
  return randomBytes(size);
}

/**
 * 암호화 IV 생성
 * @param size 바이트 크기 (기본 16)
 */
export function generateIV(size: number = 16): string {
  return randomBytes(size);
}

export default {
  hash,
  hmac,
  verifyHash,
  verifyHmac,
  randomBytes,
  randomBytesBuffer,
  randomUUID,
  encrypt,
  decrypt,
  compress,
  decompress,
  compressString,
  decompressString,
  base64Encode,
  base64Decode,
  hexEncode,
  hexDecode,
  urlSafeBase64Encode,
  urlSafeBase64Decode,
  generateKey,
  generateIV,
};
