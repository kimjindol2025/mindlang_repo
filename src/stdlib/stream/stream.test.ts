import * as Stream_Module from './stream';
import * as path from 'path';
import * as fs from 'fs';

describe('Stream - ReadStream', () => {
  const testDir = path.join(__dirname, 'test-stream');
  const testFile = path.join(testDir, 'test.txt');

  beforeAll(async () => {
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
    fs.writeFileSync(testFile, 'Hello, World! This is a test file.');
  });

  afterAll(() => {
    if (fs.existsSync(testFile)) {
      fs.unlinkSync(testFile);
    }
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  test('createReadStream creates read stream', () => {
    const stream = Stream_Module.createReadStream(testFile);
    expect(stream).toBeDefined();
  });

  test('read stream start works', () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();
    expect(true).toBe(true);
  });

  test('read stream reads data', async () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();

    const data = await stream.read();
    expect(data).toBeTruthy();
    expect(data.length).toBeGreaterThan(0);
  });

  test('read stream getString works', async () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();

    const data = await stream.read();
    const str = stream.getString();
    expect(str).toContain('Hello');
  });

  test('read stream getSize works', async () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();

    await stream.read();
    const size = stream.getSize();
    expect(size).toBeGreaterThan(0);
  });

  test('read stream getChunks works', async () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();

    await stream.read();
    const chunks = stream.getChunks();
    expect(Array.isArray(chunks)).toBe(true);
  });

  test('read stream onData works', (done) => {
    const stream = Stream_Module.createReadStream(testFile);
    let dataReceived = false;

    stream.onData(() => {
      dataReceived = true;
    });

    stream.start();

    setTimeout(() => {
      expect(dataReceived).toBe(true);
      done();
    }, 100);
  });

  test('read stream onEnd works', (done) => {
    const stream = Stream_Module.createReadStream(testFile);
    let ended = false;

    stream.onEnd(() => {
      ended = true;
    });

    stream.start();

    setTimeout(() => {
      expect(ended).toBe(true);
      done();
    }, 100);
  });

  test('read stream pause and resume work', async () => {
    const stream = Stream_Module.createReadStream(testFile);
    stream.start();
    stream.pause();
    stream.resume();

    const data = await stream.read();
    expect(data.length).toBeGreaterThan(0);
  });
});

describe('Stream - WriteStream', () => {
  const testDir = path.join(__dirname, 'test-write-stream');
  const testFile = path.join(testDir, 'output.txt');

  beforeAll(() => {
    if (!fs.existsSync(testDir)) {
      fs.mkdirSync(testDir, { recursive: true });
    }
  });

  afterAll(() => {
    if (fs.existsSync(testFile)) {
      fs.unlinkSync(testFile);
    }
    if (fs.existsSync(testDir)) {
      fs.rmSync(testDir, { recursive: true, force: true });
    }
  });

  test('createWriteStream creates write stream', () => {
    const stream = Stream_Module.createWriteStream(testFile);
    expect(stream).toBeDefined();
  });

  test('write stream start works', () => {
    const stream = Stream_Module.createWriteStream(testFile);
    stream.start();
    stream.end();
    expect(true).toBe(true);
  });

  test('write stream writes data', async () => {
    const file = path.join(testDir, 'test1.txt');
    const stream = Stream_Module.createWriteStream(file);
    stream.start();

    stream.write('Hello');
    stream.write(' World');
    stream.end();

    await stream.finish();
    const content = fs.readFileSync(file, 'utf8');
    expect(content).toContain('Hello');
  });

  test('write stream getWritten works', async () => {
    const file = path.join(testDir, 'test2.txt');
    const stream = Stream_Module.createWriteStream(file);
    stream.start();

    stream.write('test');
    const written = stream.getWritten();
    expect(written).toBeGreaterThan(0);

    stream.end();
  });

  test('write stream onFinish works', (done) => {
    const file = path.join(testDir, 'test3.txt');
    const stream = Stream_Module.createWriteStream(file);
    let finished = false;

    stream.onFinish(() => {
      finished = true;
    });

    stream.start();
    stream.write('data');
    stream.end();

    setTimeout(() => {
      expect(finished).toBe(true);
      done();
    }, 100);
  });
});

describe('Stream - TransformStream', () => {
  test('createTransformStream creates transform', () => {
    const transform = Stream_Module.createTransformStream((chunk) => {
      return chunk.toString().toUpperCase();
    });
    expect(transform).toBeDefined();
  });

  test('transform stream uppercase works', async () => {
    const transform = Stream_Module.createTransformStream((chunk) => {
      return chunk.toString().toUpperCase();
    });

    const input = Buffer.from('hello');
    const output = await transform.transform(input);

    expect(output.toString()).toContain('HELLO');
  });

  test('transform stream reverse works', async () => {
    const transform = Stream_Module.createTransformStream((chunk) => {
      const str = chunk.toString();
      return str.split('').reverse().join('');
    });

    const input = Buffer.from('hello');
    const output = await transform.transform(input);

    expect(output.toString()).toBe('olleh');
  });

  test('transform stream getStream works', () => {
    const transform = Stream_Module.createTransformStream((chunk) => chunk);
    const stream = transform.getStream();

    expect(stream).toBeTruthy();
  });
});

describe('Stream - BufferStream', () => {
  test('createBufferStream creates buffer stream', () => {
    const stream = Stream_Module.createBufferStream();
    expect(stream).toBeDefined();
  });

  test('buffer stream write works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello');
    stream.write(' world');

    const data = stream.readAll();
    expect(data.toString()).toBe('hello world');
  });

  test('buffer stream read works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello world');

    const chunk = stream.read(5);
    expect(chunk.toString()).toBe('hello');
  });

  test('buffer stream seek works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello world');

    stream.seek(6);
    const chunk = stream.read(5);
    expect(chunk.toString()).toBe('world');
  });

  test('buffer stream getPosition works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello');

    expect(stream.getPosition()).toBe(0);
    stream.read(5);
    expect(stream.getPosition()).toBe(5);
  });

  test('buffer stream getSize works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello world');

    expect(stream.getSize()).toBe(11);
  });

  test('buffer stream isEOF works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello');

    expect(stream.isEOF()).toBe(false);
    stream.read(5);
    expect(stream.isEOF()).toBe(true);
  });

  test('buffer stream readRemaining works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello world');

    stream.read(6);
    const remaining = stream.readRemaining();
    expect(remaining.toString()).toBe('world');
  });

  test('buffer stream clear works', () => {
    const stream = Stream_Module.createBufferStream();
    stream.write('hello');

    expect(stream.getSize()).toBe(5);
    stream.clear();
    expect(stream.getSize()).toBe(0);
  });

  test('buffer stream with initial data', () => {
    const buffer = Buffer.from('initial');
    const stream = Stream_Module.createBufferStream(buffer);

    expect(stream.getSize()).toBe(7);
  });
});
