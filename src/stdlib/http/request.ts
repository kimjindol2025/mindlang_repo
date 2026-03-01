/**
 * HttpRequest - HTTP 요청 객체
 */

import { HttpMethod, HttpHeaders, HttpRequestConfig } from './types';

export class HttpRequest {
  private method: HttpMethod = 'GET';
  private url: string;
  private headers: HttpHeaders = {};
  private body?: string | Buffer;
  private timeout: number = 30000; // 30초 기본값
  private followRedirects: boolean = true;
  private maxRedirects: number = 5;

  constructor(url: string, config?: HttpRequestConfig) {
    this.url = url;

    if (config) {
      this.method = config.method || 'GET';
      if (config.headers) {
        this.headers = config.headers;
      }
      if (config.body) {
        this.setBody(config.body);
      }
      if (config.timeout !== undefined) {
        this.timeout = config.timeout;
      }
      if (config.followRedirects !== undefined) {
        this.followRedirects = config.followRedirects;
      }
      if (config.maxRedirects !== undefined) {
        this.maxRedirects = config.maxRedirects;
      }

      // 쿼리 파라미터 추가
      if (config.query) {
        this.addQueryParams(config.query);
      }

      // 기본 인증 추가
      if (config.auth) {
        this.setAuth(config.auth.username, config.auth.password);
      }
    }
  }

  /**
   * HTTP 메서드 설정
   */
  setMethod(method: HttpMethod): this {
    this.method = method;
    return this;
  }

  /**
   * URL 설정
   */
  setUrl(url: string): this {
    this.url = url;
    return this;
  }

  /**
   * 헤더 설정
   */
  setHeader(name: string, value: string): this {
    this.headers[name.toLowerCase()] = value;
    return this;
  }

  /**
   * 헤더 여러 개 설정
   */
  setHeaders(headers: HttpHeaders): this {
    Object.keys(headers).forEach((key) => {
      this.headers[key.toLowerCase()] = headers[key];
    });
    return this;
  }

  /**
   * 헤더 조회
   */
  getHeader(name: string): string | string[] | undefined {
    return this.headers[name.toLowerCase()];
  }

  /**
   * 모든 헤더 조회
   */
  getHeaders(): HttpHeaders {
    return { ...this.headers };
  }

  /**
   * 요청 바디 설정
   */
  setBody(body: string | Buffer | object): this {
    if (typeof body === 'object' && !(body instanceof Buffer)) {
      this.body = JSON.stringify(body);
      this.setHeader('Content-Type', 'application/json');
    } else if (body instanceof Buffer) {
      this.body = body;
    } else {
      this.body = body;
    }
    return this;
  }

  /**
   * 요청 바디 조회
   */
  getBody(): string | Buffer | undefined {
    return this.body;
  }

  /**
   * JSON 바디 설정
   */
  setJsonBody(data: object): this {
    this.body = JSON.stringify(data);
    this.setHeader('Content-Type', 'application/json');
    return this;
  }

  /**
   * Form 바디 설정
   */
  setFormBody(data: { [key: string]: string }): this {
    const params = Object.keys(data)
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(data[key])}`)
      .join('&');
    this.body = params;
    this.setHeader('Content-Type', 'application/x-www-form-urlencoded');
    return this;
  }

  /**
   * 쿼리 파라미터 추가
   */
  addQueryParams(params: { [key: string]: string | number | boolean }): this {
    const queryString = Object.keys(params)
      .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(String(params[key]))}`)
      .join('&');

    const separator = this.url.includes('?') ? '&' : '?';
    this.url += separator + queryString;
    return this;
  }

  /**
   * 기본 인증 설정
   */
  setAuth(username: string, password: string): this {
    const credentials = Buffer.from(`${username}:${password}`).toString('base64');
    this.setHeader('Authorization', `Basic ${credentials}`);
    return this;
  }

  /**
   * Bearer 토큰 설정
   */
  setBearerToken(token: string): this {
    this.setHeader('Authorization', `Bearer ${token}`);
    return this;
  }

  /**
   * Content-Type 설정
   */
  setContentType(contentType: string): this {
    this.setHeader('Content-Type', contentType);
    return this;
  }

  /**
   * User-Agent 설정
   */
  setUserAgent(userAgent: string): this {
    this.setHeader('User-Agent', userAgent);
    return this;
  }

  /**
   * 타임아웃 설정
   */
  setTimeout(ms: number): this {
    this.timeout = ms;
    return this;
  }

  /**
   * 리다이렉트 설정
   */
  setFollowRedirects(follow: boolean, maxRedirects: number = 5): this {
    this.followRedirects = follow;
    this.maxRedirects = maxRedirects;
    return this;
  }

  /**
   * 메서드 조회
   */
  getMethod(): HttpMethod {
    return this.method;
  }

  /**
   * URL 조회
   */
  getUrl(): string {
    return this.url;
  }

  /**
   * 타임아웃 조회
   */
  getTimeout(): number {
    return this.timeout;
  }

  /**
   * 리다이렉트 설정 조회
   */
  getRedirectConfig(): { follow: boolean; max: number } {
    return {
      follow: this.followRedirects,
      max: this.maxRedirects,
    };
  }

  /**
   * Content-Length 계산
   */
  getContentLength(): number {
    if (!this.body) return 0;
    if (typeof this.body === 'string') {
      return Buffer.byteLength(this.body, 'utf8');
    }
    return this.body.length;
  }

  /**
   * 요청 초기화
   */
  clear(): this {
    this.headers = {};
    this.body = undefined;
    return this;
  }
}

export default HttpRequest;
