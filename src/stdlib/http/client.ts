/**
 * HttpClient - HTTP 클라이언트
 */

import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';
import HttpRequest from './request';
import HttpResponse from './response';
import { HttpMethod, HttpRequestConfig, HttpError, RequestStats } from './types';

export class HttpClient {
  private timeout: number = 30000; // 30초 기본값
  private defaultHeaders: { [key: string]: string } = {
    'User-Agent': 'MindLang/1.0',
  };
  private followRedirects: boolean = true;
  private maxRedirects: number = 5;

  /**
   * 기본 헤더 설정
   */
  setDefaultHeader(name: string, value: string): this {
    this.defaultHeaders[name.toLowerCase()] = value;
    return this;
  }

  /**
   * 기본 헤더 조회
   */
  getDefaultHeaders(): { [key: string]: string } {
    return { ...this.defaultHeaders };
  }

  /**
   * 기본 타임아웃 설정
   */
  setDefaultTimeout(ms: number): this {
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
   * GET 요청
   */
  async get(url: string, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'GET' });
    return this.send(request);
  }

  /**
   * POST 요청
   */
  async post(url: string, body?: string | object, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'POST', body });
    return this.send(request);
  }

  /**
   * PUT 요청
   */
  async put(url: string, body?: string | object, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'PUT', body });
    return this.send(request);
  }

  /**
   * DELETE 요청
   */
  async delete(url: string, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'DELETE' });
    return this.send(request);
  }

  /**
   * PATCH 요청
   */
  async patch(url: string, body?: string | object, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'PATCH', body });
    return this.send(request);
  }

  /**
   * HEAD 요청
   */
  async head(url: string, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'HEAD' });
    return this.send(request);
  }

  /**
   * OPTIONS 요청
   */
  async options(url: string, config?: HttpRequestConfig): Promise<HttpResponse> {
    const request = new HttpRequest(url, { ...config, method: 'OPTIONS' });
    return this.send(request);
  }

  /**
   * 요청 전송 (메인 메서드)
   */
  async send(request: HttpRequest): Promise<HttpResponse> {
    const startTime = Date.now();
    const parsedUrl = new URL(request.getUrl());
    const isHttps = parsedUrl.protocol === 'https:';
    const client = isHttps ? https : http;

    const timeout = request.getTimeout() || this.timeout;
    const redirectConfig = request.getRedirectConfig();
    const followRedirects = redirectConfig.follow !== undefined ? redirectConfig.follow : this.followRedirects;
    const maxRedirects = redirectConfig.max || this.maxRedirects;

    return new Promise((resolve, reject) => {
      const makeRequest = (url: string, redirectCount: number = 0) => {
        const parsedUrl = new URL(url);
        const requestStartTime = Date.now();

        const headers: any = {
          ...this.defaultHeaders,
          ...request.getHeaders(),
        };

        // Content-Length 자동 설정
        const body = request.getBody();
        if (body) {
          const contentLength = request.getContentLength();
          headers['content-length'] = contentLength;
        }

        const options: http.RequestOptions = {
          hostname: parsedUrl.hostname,
          port: parsedUrl.port,
          path: parsedUrl.pathname + parsedUrl.search,
          method: request.getMethod(),
          headers,
          timeout,
        };

        const req = client.request(options, (res) => {
          const chunks: Buffer[] = [];
          const responseStartTime = Date.now();

          res.on('data', (chunk) => {
            chunks.push(chunk);
          });

          res.on('end', () => {
            const responseBody = Buffer.concat(chunks);
            const responseTime = Date.now();

            // 리다이렉트 처리
            if (followRedirects && (res.statusCode === 301 || res.statusCode === 302 || res.statusCode === 307 || res.statusCode === 308) && redirectCount < maxRedirects) {
              const location = res.headers.location;
              if (location) {
                const redirectUrl = location.startsWith('http') ? location : `${parsedUrl.protocol}//${parsedUrl.host}${location}`;
                makeRequest(redirectUrl, redirectCount + 1);
                return;
              }
            }

            const response = new HttpResponse({
              status: res.statusCode || 200,
              statusText: res.statusMessage || '',
              headers: res.headers as any,
              body: responseBody,
              url,
              redirectUrl: res.headers.location as string | undefined,
            });

            resolve(response);
          });
        });

        req.on('error', (error) => {
          const httpError: HttpError = new Error(`Request failed: ${error.message}`) as HttpError;
          httpError.code = (error as any).code;
          httpError.url = url;
          reject(httpError);
        });

        req.on('timeout', () => {
          req.destroy();
          const httpError: HttpError = new Error(`Request timeout after ${timeout}ms`) as HttpError;
          httpError.url = url;
          reject(httpError);
        });

        // 바디 전송
        if (body) {
          if (typeof body === 'string') {
            req.write(body);
          } else {
            req.write(body);
          }
        }

        req.end();
      };

      makeRequest(request.getUrl());
    });
  }

  /**
   * 여러 요청 동시 실행
   */
  async sendAll(requests: HttpRequest[]): Promise<HttpResponse[]> {
    return Promise.all(requests.map((req) => this.send(req)));
  }
}

export default HttpClient;
