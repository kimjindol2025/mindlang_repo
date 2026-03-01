/**
 * HTTP 모듈 타입 정의
 */

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

export interface HttpHeaders {
  [key: string]: string | string[];
}

export interface HttpRequestConfig {
  method?: HttpMethod;
  headers?: HttpHeaders;
  body?: string | Buffer | object;
  timeout?: number;
  followRedirects?: boolean;
  maxRedirects?: number;
  auth?: {
    username: string;
    password: string;
  };
  proxy?: {
    host: string;
    port: number;
  };
  query?: { [key: string]: string | number | boolean };
}

export interface HttpResponseConfig {
  status: number;
  statusText: string;
  headers: HttpHeaders;
  body: string | Buffer;
  url: string;
  redirectUrl?: string;
}

export interface HttpError extends Error {
  status?: number;
  code?: string;
  url?: string;
  response?: HttpResponseConfig;
}

export interface HttpCookie {
  name: string;
  value: string;
  domain?: string;
  path?: string;
  expires?: Date;
  maxAge?: number;
  secure?: boolean;
  httpOnly?: boolean;
  sameSite?: 'Strict' | 'Lax' | 'None';
}

export interface UploadFile {
  fieldName: string;
  fileName: string;
  content: Buffer | string;
  contentType?: string;
}

export interface RequestStats {
  requestTime: number; // ms
  responseTime: number; // ms
  totalTime: number; // ms
  bodySize: number; // bytes
  headerSize: number; // bytes
}
