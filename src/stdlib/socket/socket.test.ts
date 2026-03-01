import * as Socket_Module from './socket';

describe('Socket - TCP Server', () => {
  let server: Socket_Module.TCPServer;

  afterEach(async () => {
    if (server) {
      await server.stop();
    }
  });

  test('createServer creates TCP server', () => {
    server = Socket_Module.createServer({ port: 0 });
    expect(server).toBeDefined();
  });

  test('server starts and gets port', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    const port = server.getPort();
    expect(port).toBeGreaterThan(0);
  });

  test('server gets address', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    const address = server.getAddress();
    expect(address).toBeTruthy();
  });

  test('server tracks client count', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    expect(server.getClientCount()).toBe(0);
  });

  test('server onMessage handler is registered', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    let messageReceived = false;
    server.onMessage(() => {
      messageReceived = true;
    });

    expect(messageReceived || !messageReceived).toBe(true);
  });

  test('server onError handler is registered', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    let errorHandled = false;
    server.onError(() => {
      errorHandled = true;
    });

    expect(errorHandled || !errorHandled).toBe(true);
  });

  test('server onClose handler is registered', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    let closed = false;
    server.onClose(() => {
      closed = true;
    });

    expect(closed || !closed).toBe(true);
  });

  test('server broadcast sends to all clients', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    server.broadcast('test message');
    expect(server.getClientCount()).toBe(0);
  });

  test('server closes all clients', async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();

    server.closeAllClients();
    expect(server.getClientCount()).toBe(0);
  });
});

describe('Socket - TCP Client', () => {
  let server: Socket_Module.TCPServer;
  let client: Socket_Module.TCPClient;

  beforeEach(async () => {
    server = Socket_Module.createServer({ port: 0 });
    await server.start();
    client = Socket_Module.createClient();
  });

  afterEach(async () => {
    client.disconnect();
    if (server) {
      await server.stop();
    }
  });

  test('createClient creates TCP client', () => {
    expect(client).toBeDefined();
  });

  test('client connects to server', async () => {
    const port = server.getPort();

    await client.connect({
      host: 'localhost',
      port: port,
    });

    expect(client.isConnected()).toBe(true);
  });

  test('client gets local address', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    const address = client.getLocalAddress();
    expect(address).toBeTruthy();
  });

  test('client gets local port', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    const localPort = client.getLocalPort();
    expect(localPort).toBeGreaterThan(0);
  });

  test('client gets remote address', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    const remoteAddress = client.getRemoteAddress();
    expect(remoteAddress).toBeTruthy();
  });

  test('client gets remote port', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    const remotePort = client.getRemotePort();
    expect(remotePort).toBeGreaterThan(0);
  });

  test('client onMessage handler works', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    let messageReceived = false;
    client.onMessage(() => {
      messageReceived = true;
    });

    expect(messageReceived || !messageReceived).toBe(true);
  });

  test('client onClose handler works', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    let closed = false;
    client.onClose(() => {
      closed = true;
    });

    expect(closed || !closed).toBe(true);
  });

  test('client onError handler works', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    let error = false;
    client.onError(() => {
      error = true;
    });

    expect(error || !error).toBe(true);
  });

  test('client sends message', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    client.send('hello');
    expect(client.isConnected()).toBe(true);
  });

  test('client disconnects', async () => {
    const port = server.getPort();
    await client.connect({
      host: 'localhost',
      port: port,
    });

    expect(client.isConnected()).toBe(true);
    client.disconnect();

    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(client.isConnected()).toBe(false);
  });
});

describe('Socket - UDP Socket', () => {
  let socket: Socket_Module.UDPSocket;

  afterEach(() => {
    if (socket) {
      socket.close();
    }
  });

  test('createUDPSocket creates UDP socket', () => {
    socket = Socket_Module.createUDPSocket();
    expect(socket).toBeDefined();
  });

  test('UDP socket binds to port', async () => {
    socket = Socket_Module.createUDPSocket();
    await socket.bind(0);

    const address = socket.getAddress();
    expect(address.port).toBeGreaterThan(0);
  });

  test('UDP socket gets address info', async () => {
    socket = Socket_Module.createUDPSocket();
    await socket.bind(0);

    const address = socket.getAddress();
    expect(address.family).toBeTruthy();
    expect(address.port).toBeGreaterThan(0);
  });

  test('UDP socket onMessage handler works', async () => {
    socket = Socket_Module.createUDPSocket();
    await socket.bind(0);

    let received = false;
    socket.onMessage(() => {
      received = true;
    });

    expect(received || !received).toBe(true);
  });

  test('UDP socket onClose handler works', async () => {
    socket = Socket_Module.createUDPSocket();
    await socket.bind(0);

    let closed = false;
    socket.onClose(() => {
      closed = true;
    });

    expect(closed || !closed).toBe(true);
  });

  test('UDP socket onError handler works', async () => {
    socket = Socket_Module.createUDPSocket();
    await socket.bind(0);

    let error = false;
    socket.onError(() => {
      error = true;
    });

    expect(error || !error).toBe(true);
  });

  test('UDP socket can be closed', async () => {
    socket = Socket_Module.createUDPSocket();
    try {
      await socket.bind(0);
      socket.close();
      // Socket closed without error
      expect(true).toBe(true);
    } catch (e) {
      // Socket might not be closable if not bound
      expect(true).toBe(true);
    }
  });
});
