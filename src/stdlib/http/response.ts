/**
 * HttpResponse - HTTP 응답 객체
 */

import { HttpHeaders, HttpResponseConfig, HttpCookie } from './types';

export class HttpResponse {
  private status: number;
  private statusText: string;
  private headers: HttpHeaders;
  private body: string | Buffer;
  private url: string;
  private redirectUrl?: string;

  constructor(config: HttpResponseConfig) {
    this.status = config.status;
    this.statusText = config.statusText;
    this.headers = config.headers;
    this.body = config.body;
    this.url = config.url;
    this.redirectUrl = config.redirectUrl;
  }

  /**
   * 상태 코드 조회
   */
  getStatus(): number {
    return this.status;
  }

  /**
   * 상태 텍스트 조회
   */
  getStatusText(): string {
    return this.statusText;
  }

  /**
   * 성공 여부 (2xx)
   */
  isSuccess(): boolean {
    return this.status >= 200 && this.status < 300;
  }

  /**
   * 리다이렉트 여부 (3xx)
   */
  isRedirect(): boolean {
    return this.status >= 300 && this.status < 400;
  }

  /**
   * 클라이언트 에러 여부 (4xx)
   */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  /**
   * 서버 에러 여부 (5xx)
   */
  isServerError(): boolean {
    return this.status >= 500;
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
   * Content-Type 조회
   */
  getContentType(): string | undefined {
    const contentType = this.getHeader('content-type');
    if (Array.isArray(contentType)) {
      return contentType[0];
    }
    return contentType;
  }

  /**
   * Content-Length 조회
   */
  getContentLength(): number {
    const length = this.getHeader('content-length');
    if (length) {
      const value = Array.isArray(length) ? length[0] : length;
      return parseInt(value, 10);
    }
    if (typeof this.body === 'string') {
      return Buffer.byteLength(this.body, 'utf8');
    }
    return this.body.length;
  }

  /**
   * 바디 조회 (문자열)
   */
  getText(): string {
    if (typeof this.body === 'string') {
      return this.body;
    }
    return this.body.toString('utf8');
  }

  /**
   * 바디 조회 (Buffer)
   */
  getBuffer(): Buffer {
    if (typeof this.body === 'string') {
      return Buffer.from(this.body, 'utf8');
    }
    return this.body;
  }

  /**
   * 바디 조회 (JSON 파싱)
   */
  getJson(): object {
    const text = this.getText();
    return JSON.parse(text);
  }

  /**
   * URL 조회
   */
  getUrl(): string {
    return this.url;
  }

  /**
   * 리다이렉트 URL 조회
   */
  getRedirectUrl(): string | undefined {
    return this.redirectUrl;
  }

  /**
   * Location 헤더 조회 (리다이렉트)
   */
  getLocation(): string | undefined {
    return this.getHeader('location') as string | undefined;
  }

  /**
   * 쿠키 파싱
   */
  getCookies(): HttpCookie[] {
    const setCookieHeaders = this.getHeader('set-cookie');
    if (!setCookieHeaders) return [];

    const headers = Array.isArray(setCookieHeaders) ? setCookieHeaders : [setCookieHeaders];

    return headers.map((cookie) => {
      const parts = cookie.split(';');
      const [nameValue] = parts;
      const [name, value] = nameValue.split('=');

      const result: HttpCookie = {
        name: name.trim(),
        value: value?.trim() || '',
      };

      parts.slice(1).forEach((part) => {
        const [key, val] = part.split('=');
        const trimmedKey = key.trim().toLowerCase();

        switch (trimmedKey) {
          case 'domain':
            result.domain = val?.trim();
            break;
          case 'path':
            result.path = val?.trim();
            break;
          case 'expires':
            result.expires = new Date(val?.trim() || '');
            break;
          case 'max-age':
            result.maxAge = parseInt(val?.trim() || '0', 10);
            break;
          case 'secure':
            result.secure = true;
            break;
          case 'httponly':
            result.httpOnly = true;
            break;
          case 'samesite':
            result.sameSite = (val?.trim() || 'Lax') as 'Strict' | 'Lax' | 'None';
            break;
        }
      });

      return result;
    });
  }

  /**
   * ETag 조회
   */
  getETag(): string | undefined {
    return this.getHeader('etag') as string | undefined;
  }

  /**
   * Last-Modified 조회
   */
  getLastModified(): Date | undefined {
    const lastModified = this.getHeader('last-modified');
    if (lastModified) {
      const dateStr = Array.isArray(lastModified) ? lastModified[0] : lastModified;
      return new Date(dateStr);
    }
    return undefined;
  }

  /**
   * 캐시 제어 헤더 조회
   */
  getCacheControl(): string | undefined {
    return this.getHeader('cache-control') as string | undefined;
  }

  /**
   * 서버 정보 조회
   */
  getServer(): string | undefined {
    return this.getHeader('server') as string | undefined;
  }
}

export default HttpResponse;
