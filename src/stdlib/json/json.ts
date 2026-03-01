/**
 * JSON 모듈 - JSON 파싱 및 직렬화
 *
 * JSON 문자열을 객체로 변환하거나 객체를 JSON으로 변환합니다.
 */

export interface JsonValue {
  [key: string]: any;
}

export interface JsonOptions {
  indent?: number | string;
  replacer?: (key: string, value: any) => any;
  reviver?: (key: string, value: any) => any;
}

/**
 * JSON 파싱
 * @param json JSON 문자열
 * @param reviver 값을 변환하는 함수 (선택사항)
 */
export function parse(json: string, reviver?: (key: string, value: any) => any): any {
  try {
    if (reviver) {
      return JSON.parse(json, reviver);
    }
    return JSON.parse(json);
  } catch (e) {
    throw new Error(`Invalid JSON: ${(e as Error).message}`);
  }
}

/**
 * JSON 직렬화
 * @param value 직렬화할 값
 * @param replacer 값을 필터링하는 함수 (선택사항)
 * @param indent 들여쓰기 (숫자 또는 문자열, 선택사항)
 */
export function stringify(
  value: any,
  replacer?: (key: string, value: any) => any | null,
  indent?: number | string
): string {
  try {
    return JSON.stringify(value, replacer as any, indent);
  } catch (e) {
    throw new Error(`Failed to stringify: ${(e as Error).message}`);
  }
}

/**
 * JSON 유효성 검증
 * @param json JSON 문자열
 */
export function isValid(json: string): boolean {
  try {
    JSON.parse(json);
    return true;
  } catch {
    return false;
  }
}

/**
 * JSON 포맷팅 (들여쓰기 추가)
 * @param json JSON 문자열
 * @param indent 들여쓰기 스페이스 개수 (기본값: 2)
 */
export function format(json: string, indent: number = 2): string {
  try {
    const parsed = JSON.parse(json);
    return JSON.stringify(parsed, null, indent);
  } catch (e) {
    throw new Error(`Invalid JSON: ${(e as Error).message}`);
  }
}

/**
 * JSON 압축 (공백 제거)
 * @param json JSON 문자열
 */
export function minify(json: string): string {
  try {
    const parsed = JSON.parse(json);
    return JSON.stringify(parsed);
  } catch (e) {
    throw new Error(`Invalid JSON: ${(e as Error).message}`);
  }
}

/**
 * 깊은 복사 (JSON을 이용한)
 * @param value 복사할 값
 */
export function deepClone(value: any): any {
  try {
    return JSON.parse(JSON.stringify(value));
  } catch (e) {
    throw new Error(`Failed to clone: ${(e as Error).message}`);
  }
}

/**
 * 객체 병합
 * @param target 대상 객체
 * @param source 소스 객체
 * @param deep 깊은 병합 여부 (기본값: false)
 */
export function merge(target: any, source: any, deep: boolean = false): any {
  if (!deep) {
    return { ...target, ...source };
  }

  const result = deepClone(target);

  Object.keys(source).forEach((key) => {
    if (
      typeof source[key] === 'object' &&
      source[key] !== null &&
      !Array.isArray(source[key]) &&
      typeof result[key] === 'object' &&
      result[key] !== null &&
      !Array.isArray(result[key])
    ) {
      result[key] = merge(result[key], source[key], true);
    } else {
      result[key] = source[key];
    }
  });

  return result;
}

/**
 * 경로로 값 조회 (점 표기법)
 * @param obj 객체
 * @param path 경로 (예: "user.profile.name")
 */
export function getByPath(obj: any, path: string): any {
  const keys = path.split('.');
  let current = obj;

  for (const key of keys) {
    if (current === null || current === undefined) {
      return undefined;
    }
    current = current[key];
  }

  return current;
}

/**
 * 경로로 값 설정 (점 표기법)
 * @param obj 객체
 * @param path 경로 (예: "user.profile.name")
 * @param value 설정할 값
 */
export function setByPath(obj: any, path: string, value: any): any {
  const keys = path.split('.');
  let current = obj;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in current) || typeof current[key] !== 'object') {
      current[key] = {};
    }
    current = current[key];
  }

  current[keys[keys.length - 1]] = value;
  return obj;
}

/**
 * 경로로 값 삭제 (점 표기법)
 * @param obj 객체
 * @param path 경로 (예: "user.profile.name")
 */
export function deleteByPath(obj: any, path: string): any {
  const keys = path.split('.');
  let current = obj;

  for (let i = 0; i < keys.length - 1; i++) {
    const key = keys[i];
    if (!(key in current)) {
      return obj;
    }
    current = current[key];
  }

  delete current[keys[keys.length - 1]];
  return obj;
}

/**
 * 객체 필터링 (특정 키만 유지)
 * @param obj 객체
 * @param keys 유지할 키 배열
 */
export function pick(obj: any, keys: string[]): any {
  const result: any = {};
  keys.forEach((key) => {
    if (key in obj) {
      result[key] = obj[key];
    }
  });
  return result;
}

/**
 * 객체 필터링 (특정 키 제외)
 * @param obj 객체
 * @param keys 제외할 키 배열
 */
export function omit(obj: any, keys: string[]): any {
  const result = { ...obj };
  keys.forEach((key) => {
    delete result[key];
  });
  return result;
}

/**
 * 객체 크기 조회 (바이트)
 * @param obj 객체
 */
export function getSize(obj: any): number {
  const json = JSON.stringify(obj);
  return Buffer.byteLength(json, 'utf8');
}

/**
 * 객체 비교
 * @param obj1 첫 번째 객체
 * @param obj2 두 번째 객체
 */
export function equals(obj1: any, obj2: any): boolean {
  return JSON.stringify(obj1) === JSON.stringify(obj2);
}

export default {
  parse,
  stringify,
  isValid,
  format,
  minify,
  deepClone,
  merge,
  getByPath,
  setByPath,
  deleteByPath,
  pick,
  omit,
  getSize,
  equals,
};
