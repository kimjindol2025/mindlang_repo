/**
 * Socket 모듈 - TCP/UDP 네트워크 통신
 *
 * TCP 서버/클라이언트 및 기본 UDP 기능을 제공합니다.
 */

import * as net from 'net';
import * as dgram from 'dgram';

export interface SocketMessage {
  data: string | Buffer;
  remoteAddress?: string;
  remotePort?: number;
}

export interface ServerConfig {
  port: number;
  host?: string;
  backlog?: number;
}

export interface ClientConfig {
  host: string;
  port: number;
  timeout?: number;
}

export class TCPServer {
  private server: net.Server;
  private clients: Set<net.Socket> = new Set();
  private messageHandlers: ((msg: SocketMessage, socket: net.Socket) => void)[] = [];
  private closeHandlers: (() => void)[] = [];
  private errorHandlers: ((error: Error) => void)[] = [];

  constructor(private config: ServerConfig) {
    this.server = net.createServer((socket) => {
      this.clients.add(socket);

      socket.on('data', (data) => {
        this.messageHandlers.forEach((handler) => {
          handler(
            {
              data: data.toString(),
              remoteAddress: socket.remoteAddress,
              remotePort: socket.remotePort,
            },
            socket
          );
        });
      });

      socket.on('end', () => {
        this.clients.delete(socket);
      });

      socket.on('error', (err) => {
        this.errorHandlers.forEach((handler) => handler(err));
      });
    });

    this.server.on('error', (err) => {
      this.errorHandlers.forEach((handler) => handler(err));
    });
  }

  /**
   * 서버 시작
   */
  async start(): Promise<void> {
    return new Promise((resolve) => {
      this.server.listen(this.config.port, this.config.host || 'localhost', () => {
        resolve();
      });
    });
  }

  /**
   * 서버 중지
   */
  async stop(): Promise<void> {
    return new Promise((resolve) => {
      this.server.close(() => {
        this.closeHandlers.forEach((handler) => handler());
        resolve();
      });
    });
  }

  /**
   * 메시지 핸들러 등록
   */
  onMessage(handler: (msg: SocketMessage, socket: net.Socket) => void): void {
    this.messageHandlers.push(handler);
  }

  /**
   * 종료 핸들러 등록
   */
  onClose(handler: () => void): void {
    this.closeHandlers.push(handler);
  }

  /**
   * 에러 핸들러 등록
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 모든 클라이언트에게 메시지 전송
   */
  broadcast(message: string): void {
    this.clients.forEach((socket) => {
      if (!socket.destroyed) {
        socket.write(message);
      }
    });
  }

  /**
   * 특정 클라이언트에게 메시지 전송
   */
  sendTo(socket: net.Socket, message: string): void {
    if (!socket.destroyed) {
      socket.write(message);
    }
  }

  /**
   * 연결된 클라이언트 수
   */
  getClientCount(): number {
    return this.clients.size;
  }

  /**
   * 서버 포트 조회
   */
  getPort(): number {
    const addr = this.server.address() as net.AddressInfo;
    return addr.port;
  }

  /**
   * 서버 주소 조회
   */
  getAddress(): string {
    const addr = this.server.address() as net.AddressInfo;
    return addr.address;
  }

  /**
   * 모든 클라이언트 종료
   */
  closeAllClients(): void {
    this.clients.forEach((socket) => {
      socket.destroy();
    });
    this.clients.clear();
  }
}

export class TCPClient {
  private socket: net.Socket | null = null;
  private messageHandlers: ((msg: SocketMessage) => void)[] = [];
  private closeHandlers: (() => void)[] = [];
  private errorHandlers: ((error: Error) => void)[] = [];

  /**
   * 서버에 연결
   */
  async connect(config: ClientConfig): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket = net.createConnection(
        {
          host: config.host,
          port: config.port,
          timeout: config.timeout,
        },
        () => {
          resolve();
        }
      );

      this.socket.on('data', (data) => {
        this.messageHandlers.forEach((handler) => {
          handler({
            data: data.toString(),
            remoteAddress: this.socket?.remoteAddress,
            remotePort: this.socket?.remotePort,
          });
        });
      });

      this.socket.on('end', () => {
        this.closeHandlers.forEach((handler) => handler());
      });

      this.socket.on('error', (err) => {
        this.errorHandlers.forEach((handler) => handler(err));
        reject(err);
      });
    });
  }

  /**
   * 연결 종료
   */
  disconnect(): void {
    if (this.socket && !this.socket.destroyed) {
      this.socket.destroy();
    }
  }

  /**
   * 메시지 전송
   */
  send(message: string): void {
    if (this.socket && !this.socket.destroyed) {
      this.socket.write(message);
    }
  }

  /**
   * 메시지 핸들러 등록
   */
  onMessage(handler: (msg: SocketMessage) => void): void {
    this.messageHandlers.push(handler);
  }

  /**
   * 종료 핸들러 등록
   */
  onClose(handler: () => void): void {
    this.closeHandlers.push(handler);
  }

  /**
   * 에러 핸들러 등록
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 연결 상태 확인
   */
  isConnected(): boolean {
    return this.socket !== null && !this.socket.destroyed;
  }

  /**
   * 로컬 주소 조회
   */
  getLocalAddress(): string | undefined {
    return this.socket?.localAddress;
  }

  /**
   * 로컬 포트 조회
   */
  getLocalPort(): number | undefined {
    return this.socket?.localPort;
  }

  /**
   * 원격 주소 조회
   */
  getRemoteAddress(): string | undefined {
    return this.socket?.remoteAddress;
  }

  /**
   * 원격 포트 조회
   */
  getRemotePort(): number | undefined {
    return this.socket?.remotePort;
  }
}

export class UDPSocket {
  private socket: dgram.Socket;
  private messageHandlers: ((msg: SocketMessage) => void)[] = [];
  private closeHandlers: (() => void)[] = [];
  private errorHandlers: ((error: Error) => void)[] = [];

  constructor() {
    this.socket = dgram.createSocket('udp4');

    this.socket.on('message', (msg, rinfo) => {
      this.messageHandlers.forEach((handler) => {
        handler({
          data: msg.toString(),
          remoteAddress: rinfo.address,
          remotePort: rinfo.port,
        });
      });
    });

    this.socket.on('close', () => {
      this.closeHandlers.forEach((handler) => handler());
    });

    this.socket.on('error', (err) => {
      this.errorHandlers.forEach((handler) => handler(err));
    });
  }

  /**
   * UDP 소켓 바인드
   */
  async bind(port: number, address?: string): Promise<void> {
    return new Promise((resolve) => {
      this.socket.bind(port, address || 'localhost', () => {
        resolve();
      });
    });
  }

  /**
   * 메시지 전송
   */
  async send(message: string, port: number, address: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.socket.send(message, 0, message.length, port, address, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * 소켓 종료
   */
  close(): void {
    try {
      this.socket.close();
    } catch (e) {
      // Socket might already be closed
    }
  }

  /**
   * 메시지 핸들러 등록
   */
  onMessage(handler: (msg: SocketMessage) => void): void {
    this.messageHandlers.push(handler);
  }

  /**
   * 종료 핸들러 등록
   */
  onClose(handler: () => void): void {
    this.closeHandlers.push(handler);
  }

  /**
   * 에러 핸들러 등록
   */
  onError(handler: (error: Error) => void): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 소켓 주소 조회
   */
  getAddress(): any {
    return this.socket.address();
  }
}

/**
 * TCP 서버 생성
 */
export function createServer(config: ServerConfig): TCPServer {
  return new TCPServer(config);
}

/**
 * TCP 클라이언트 생성
 */
export function createClient(): TCPClient {
  return new TCPClient();
}

/**
 * UDP 소켓 생성
 */
export function createUDPSocket(): UDPSocket {
  return new UDPSocket();
}

export default {
  createServer,
  createClient,
  createUDPSocket,
  TCPServer,
  TCPClient,
  UDPSocket,
};
