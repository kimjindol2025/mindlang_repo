import * as http from 'http';
import HttpClient from './client';
import HttpRequest from './request';
import HttpResponse from './response';

/**
 * 테스트용 HTTP 서버
 */
let testServer: http.Server;
let testPort: number;

beforeAll((done) => {
  testServer = http.createServer((req, res) => {
    // 요청 경로에 따라 다른 응답
    if (req.url === '/api/users' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify([{ id: 1, name: 'Alice' }, { id: 2, name: 'Bob' }]));
    } else if (req.url === '/api/users' && req.method === 'POST') {
      res.writeHead(201, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ id: 3, name: 'Charlie' }));
    } else if (req.url === '/api/users/1' && req.method === 'PUT') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ id: 1, name: 'Alice Updated' }));
    } else if (req.url === '/api/users/1' && req.method === 'DELETE') {
      res.writeHead(204);
      res.end();
    } else if (req.url === '/api/users/1' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ id: 1, name: 'Alice' }));
    } else if (req.url === '/redirect' && req.method === 'GET') {
      res.writeHead(302, { 'Location': '/api/users' });
      res.end();
    } else if (req.url === '/text' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'text/plain' });
      res.end('Hello, World!');
    } else if (req.url === '/headers' && req.method === 'GET') {
      res.writeHead(200, {
        'X-Custom-Header': 'custom-value',
        'Cache-Control': 'max-age=3600',
        'ETag': '"12345"',
      });
      res.end('OK');
    } else if (req.url === '/cookies' && req.method === 'GET') {
      res.writeHead(200, {
        'Set-Cookie': 'sessionId=abc123; Path=/; HttpOnly; Secure',
      });
      res.end('OK');
    } else if (req.url === '/error' && req.method === 'GET') {
      res.writeHead(500);
      res.end('Internal Server Error');
    } else if (req.url === '/notfound' && req.method === 'GET') {
      res.writeHead(404);
      res.end('Not Found');
    } else {
      res.writeHead(404);
      res.end('Not Found');
    }
  });

  testServer.listen(0, 'localhost', () => {
    testPort = (testServer.address() as any).port;
    done();
  });
});

afterAll((done) => {
  testServer.close(done);
});

describe('HttpRequest', () => {
  test('create basic request', () => {
    const req = new HttpRequest('http://localhost/api');
    expect(req.getUrl()).toBe('http://localhost/api');
    expect(req.getMethod()).toBe('GET');
  });

  test('set method', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setMethod('POST');
    expect(req.getMethod()).toBe('POST');
  });

  test('set headers', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setHeader('Authorization', 'Bearer token');
    expect(req.getHeader('authorization')).toBe('Bearer token');
  });

  test('set body string', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setBody('test body');
    expect(req.getBody()).toBe('test body');
  });

  test('set body object', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setJsonBody({ name: 'test' });
    expect(req.getBody()).toBe(JSON.stringify({ name: 'test' }));
    expect(req.getHeader('content-type')).toBe('application/json');
  });

  test('set form body', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setFormBody({ name: 'test', age: '25' });
    expect(req.getBody()).toContain('name=test');
    expect(req.getHeader('content-type')).toBe('application/x-www-form-urlencoded');
  });

  test('add query params', () => {
    const req = new HttpRequest('http://localhost/api');
    req.addQueryParams({ page: 1, limit: 10 });
    expect(req.getUrl()).toContain('page=1');
    expect(req.getUrl()).toContain('limit=10');
  });

  test('set auth', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setAuth('user', 'password');
    const header = req.getHeader('authorization');
    expect(header).toContain('Basic');
  });

  test('set bearer token', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setBearerToken('mytoken123');
    expect(req.getHeader('authorization')).toBe('Bearer mytoken123');
  });

  test('set content type', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setContentType('application/xml');
    expect(req.getHeader('content-type')).toBe('application/xml');
  });

  test('set user agent', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setUserAgent('Custom/1.0');
    expect(req.getHeader('user-agent')).toBe('Custom/1.0');
  });

  test('set timeout', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setTimeout(5000);
    expect(req.getTimeout()).toBe(5000);
  });

  test('set follow redirects', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setFollowRedirects(false, 3);
    const config = req.getRedirectConfig();
    expect(config.follow).toBe(false);
    expect(config.max).toBe(3);
  });

  test('get content length', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setBody('test');
    expect(req.getContentLength()).toBeGreaterThan(0);
  });

  test('clear request', () => {
    const req = new HttpRequest('http://localhost/api');
    req.setHeader('X-Test', 'value');
    req.setBody('test');
    req.clear();
    expect(req.getHeaders()['x-test']).toBeUndefined();
    expect(req.getBody()).toBeUndefined();
  });
});

describe('HttpResponse', () => {
  test('create response with success status', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: {},
      body: Buffer.from('test'),
      url: 'http://localhost',
    });
    expect(res.getStatus()).toBe(200);
    expect(res.isSuccess()).toBe(true);
  });

  test('check status codes', () => {
    const success = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: {},
      body: Buffer.from(''),
      url: 'http://localhost',
    });

    const redirect = new HttpResponse({
      status: 301,
      statusText: 'Moved Permanently',
      headers: {},
      body: Buffer.from(''),
      url: 'http://localhost',
    });

    const clientError = new HttpResponse({
      status: 404,
      statusText: 'Not Found',
      headers: {},
      body: Buffer.from(''),
      url: 'http://localhost',
    });

    const serverError = new HttpResponse({
      status: 500,
      statusText: 'Internal Server Error',
      headers: {},
      body: Buffer.from(''),
      url: 'http://localhost',
    });

    expect(success.isSuccess()).toBe(true);
    expect(redirect.isRedirect()).toBe(true);
    expect(clientError.isClientError()).toBe(true);
    expect(serverError.isServerError()).toBe(true);
  });

  test('get text body', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: {},
      body: Buffer.from('Hello'),
      url: 'http://localhost',
    });
    expect(res.getText()).toBe('Hello');
  });

  test('get json body', () => {
    const data = { name: 'test', age: 25 };
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'content-type': 'application/json' },
      body: Buffer.from(JSON.stringify(data)),
      url: 'http://localhost',
    });
    expect(res.getJson()).toEqual(data);
  });

  test('get content type', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'content-type': 'application/json; charset=utf-8' },
      body: Buffer.from('{}'),
      url: 'http://localhost',
    });
    expect(res.getContentType()).toContain('application/json');
  });

  test('get headers', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'x-custom': 'value' },
      body: Buffer.from(''),
      url: 'http://localhost',
    });
    expect(res.getHeader('x-custom')).toBe('value');
  });

  test('parse cookies', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: {
        'set-cookie': 'sessionId=abc123; Path=/; HttpOnly',
      },
      body: Buffer.from(''),
      url: 'http://localhost',
    });
    const cookies = res.getCookies();
    expect(cookies.length).toBe(1);
    expect(cookies[0].name).toBe('sessionId');
    expect(cookies[0].value).toBe('abc123');
  });

  test('get cache control', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'cache-control': 'max-age=3600' },
      body: Buffer.from(''),
      url: 'http://localhost',
    });
    expect(res.getCacheControl()).toBe('max-age=3600');
  });

  test('get etag', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'etag': '"12345"' },
      body: Buffer.from(''),
      url: 'http://localhost',
    });
    expect(res.getETag()).toBe('"12345"');
  });

  test('get location', () => {
    const res = new HttpResponse({
      status: 301,
      statusText: 'Moved Permanently',
      headers: { 'location': 'http://example.com' },
      body: Buffer.from(''),
      url: 'http://localhost',
    });
    expect(res.getLocation()).toBe('http://example.com');
  });

  test('get content length', () => {
    const res = new HttpResponse({
      status: 200,
      statusText: 'OK',
      headers: { 'content-length': '1024' },
      body: Buffer.from('x'.repeat(1024)),
      url: 'http://localhost',
    });
    expect(res.getContentLength()).toBe(1024);
  });
});

describe('HttpClient - GET', () => {
  test('simple get request', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/api/users`);
    expect(response.getStatus()).toBe(200);
    expect(response.isSuccess()).toBe(true);
  });

  test('get with json response', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/api/users`);
    const data = response.getJson() as any[];
    expect(Array.isArray(data)).toBe(true);
  });

  test('get specific user', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/api/users/1`);
    const data = response.getJson() as any;
    expect(data.id).toBe(1);
  });

  test('get text response', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/text`);
    expect(response.getText()).toBe('Hello, World!');
  });

  test('get with custom headers', async () => {
    const client = new HttpClient();
    const request = new HttpRequest(`http://localhost:${testPort}/api/users`);
    request.setHeader('X-Custom', 'value');
    const response = await client.send(request);
    expect(response.isSuccess()).toBe(true);
  });

  test('get response headers', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/headers`);
    expect(response.getHeader('x-custom-header')).toBe('custom-value');
  });
});

describe('HttpClient - POST', () => {
  test('post with string body', async () => {
    const client = new HttpClient();
    const response = await client.post(`http://localhost:${testPort}/api/users`, 'new user');
    expect(response.getStatus()).toBe(201);
  });

  test('post with json body', async () => {
    const client = new HttpClient();
    const response = await client.post(`http://localhost:${testPort}/api/users`, { name: 'Charlie' });
    expect(response.getStatus()).toBe(201);
  });
});

describe('HttpClient - PUT', () => {
  test('put request', async () => {
    const client = new HttpClient();
    const response = await client.put(`http://localhost:${testPort}/api/users/1`, { name: 'Alice Updated' });
    expect(response.getStatus()).toBe(200);
  });
});

describe('HttpClient - DELETE', () => {
  test('delete request', async () => {
    const client = new HttpClient();
    const response = await client.delete(`http://localhost:${testPort}/api/users/1`);
    expect(response.getStatus()).toBe(204);
  });
});

describe('HttpClient - Error Handling', () => {
  test('404 not found', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/notfound`);
    expect(response.isClientError()).toBe(true);
  });

  test('500 server error', async () => {
    const client = new HttpClient();
    const response = await client.get(`http://localhost:${testPort}/error`);
    expect(response.isServerError()).toBe(true);
  });
});

describe('HttpClient - Advanced', () => {
  test('set default headers', async () => {
    const client = new HttpClient();
    client.setDefaultHeader('X-API-Key', 'secret123');
    const response = await client.get(`http://localhost:${testPort}/api/users`);
    expect(response.isSuccess()).toBe(true);
  });

  test('send multiple requests', async () => {
    const client = new HttpClient();
    const requests = [
      new HttpRequest(`http://localhost:${testPort}/api/users`),
      new HttpRequest(`http://localhost:${testPort}/api/users/1`),
    ];
    const responses = await client.sendAll(requests);
    expect(responses.length).toBe(2);
    expect(responses[0].isSuccess()).toBe(true);
    expect(responses[1].isSuccess()).toBe(true);
  });

  test('request builder pattern', async () => {
    const client = new HttpClient();
    const request = new HttpRequest(`http://localhost:${testPort}/api/users`)
      .setMethod('GET')
      .setHeader('X-Custom', 'value')
      .setTimeout(10000);

    const response = await client.send(request);
    expect(response.isSuccess()).toBe(true);
  });
});
