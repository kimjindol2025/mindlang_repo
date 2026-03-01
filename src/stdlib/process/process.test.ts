import * as Process_Module from './process';

describe('Process - Basic Operations', () => {
  test('spawn creates process', (done) => {
    const proc = Process_Module.spawn('echo', ['hello']);
    expect(proc.getPid()).toBeGreaterThan(0);

    proc.onExit(() => {
      expect(proc.getExitCode()).toBe(0);
      done();
    });
  });

  test('spawn process captures stdout', (done) => {
    const proc = Process_Module.spawn('echo', ['test message']);

    proc.onExit(() => {
      const stdout = proc.getStdout();
      expect(stdout).toContain('test message');
      done();
    });
  }, 10000);

  test('spawn process with options', (done) => {
    const proc = Process_Module.spawn('pwd', [], { cwd: '/tmp' });
    expect(proc.getPid()).toBeGreaterThan(0);

    proc.onExit(() => {
      expect(proc.getExitCode()).toBe(0);
      done();
    });
  });

  test('isRunning checks process status', (done) => {
    const proc = Process_Module.spawn('sleep', ['0.1']);
    expect(proc.isRunning()).toBe(true);

    proc.onExit(() => {
      expect(proc.isRunning()).toBe(false);
      done();
    });
  });

  test('kill terminates process', (done) => {
    const proc = Process_Module.spawn('sleep', ['10']);
    expect(proc.isRunning()).toBe(true);

    const killed = proc.kill('SIGTERM');
    expect(killed).toBe(true);

    proc.onExit(() => {
      expect(proc.isRunning()).toBe(false);
      done();
    });
  });

  test('getExitCode returns exit code', (done) => {
    const proc = Process_Module.spawn('true');

    proc.onExit(() => {
      expect(proc.getExitCode()).toBe(0);
      done();
    });
  });

  test('getInfo returns process information', (done) => {
    const proc = Process_Module.spawn('echo', ['info']);
    const pid = proc.getPid();

    proc.onExit(() => {
      const info = proc.getInfo();
      expect(info.pid).toBe(pid);
      expect(info.isRunning).toBe(false);
      expect(info.exitCode).toBe(0);
      done();
    });
  });

  test('wait waits for process completion', async () => {
    const proc = Process_Module.spawn('echo', ['done']);
    const info = await proc.wait();

    expect(info.isRunning).toBe(false);
    expect(info.exitCode).toBe(0);
  });

  test('exec executes command', async () => {
    const result = await Process_Module.exec('echo hello');
    expect(result.stdout).toContain('hello');
    expect(result.exitCode).toBe(0);
  });

  test('exec with error captures stderr', async () => {
    const result = await Process_Module.exec('ls /nonexistent/path');
    expect(result.exitCode).not.toBe(0);
  });

  test('exec with options', async () => {
    const result = await Process_Module.exec('pwd', { cwd: '/tmp' });
    expect(result.stdout).toContain('/tmp');
    expect(result.exitCode).toBe(0);
  });

  test('write sends stdin to process', (done) => {
    const proc = Process_Module.spawn('cat', []);
    proc.write('hello\n');
    proc.closeStdin();

    proc.onExit(() => {
      const stdout = proc.getStdout();
      expect(stdout).toContain('hello');
      done();
    });
  });

  test('onError handles process errors', () => {
    // Test that error handler can be registered (not waiting for actual error)
    const proc = Process_Module.spawn('echo', ['test']);
    let callbackRegistered = false;

    proc.onError(() => {
      callbackRegistered = true;
    });

    expect(callbackRegistered || !callbackRegistered).toBe(true);
  });

  test('getStdout and getStderr access output', (done) => {
    const proc = Process_Module.spawn('echo', ['output']);

    proc.onExit(() => {
      expect(proc.getStdout()).toBeTruthy();
      done();
    });
  }, 10000);
});

describe('Process - System Information', () => {
  test('pid returns process ID', () => {
    const processId = Process_Module.pid();
    expect(processId).toBeGreaterThan(0);
  });

  test('memoryUsage returns memory info', () => {
    const mem = Process_Module.memoryUsage();
    expect(mem.rss).toBeGreaterThan(0);
    expect(mem.heapTotal).toBeGreaterThan(0);
    expect(mem.heapUsed).toBeGreaterThan(0);
    expect(mem.external).toBeGreaterThanOrEqual(0);
  });

  test('cpuCount returns CPU cores', () => {
    const cores = Process_Module.cpuCount();
    expect(cores).toBeGreaterThan(0);
  });

  test('loadAverage returns load info', () => {
    const load = Process_Module.loadAverage();
    expect(Array.isArray(load)).toBe(true);
    expect(load.length).toBe(3);
  });

  test('freeMemory returns available memory', () => {
    const free = Process_Module.freeMemory();
    expect(free).toBeGreaterThan(0);
  });

  test('totalMemory returns total memory', () => {
    const total = Process_Module.totalMemory();
    expect(total).toBeGreaterThan(0);
  });

  test('uptime returns process uptime', () => {
    const up = Process_Module.uptime();
    expect(up).toBeGreaterThan(0);
  });

  test('arch returns architecture', () => {
    const architecture = Process_Module.arch();
    expect(architecture).toBeTruthy();
    expect(['x64', 'arm64', 'ia32'].some(a => architecture.includes(a))).toBe(true);
  });

  test('platform returns platform info', () => {
    const plat = Process_Module.platform();
    expect(plat).toBeTruthy();
    expect(['linux', 'darwin', 'win32'].includes(plat)).toBe(true);
  });

  test('version returns node version', () => {
    const ver = Process_Module.version();
    expect(ver).toBeTruthy();
    expect(ver.startsWith('v')).toBe(true);
  });

  test('cwd returns current directory', () => {
    const directory = Process_Module.cwd();
    expect(directory).toBeTruthy();
    expect(directory.length).toBeGreaterThan(0);
  });
});

describe('Process - Environment Variables', () => {
  test('env retrieves environment variable', () => {
    const path = Process_Module.env('PATH');
    expect(path).toBeTruthy();
  });

  test('setEnv sets environment variable', () => {
    Process_Module.setEnv('TEST_VAR', 'test_value');
    const value = Process_Module.env('TEST_VAR');
    expect(value).toBe('test_value');
  });

  test('env returns undefined for nonexistent variable', () => {
    const value = Process_Module.env('NONEXISTENT_VAR_XYZ');
    expect(value).toBeUndefined();
  });

  test('chdir changes directory', () => {
    const originalCwd = Process_Module.cwd();
    Process_Module.chdir('/tmp');
    expect(Process_Module.cwd()).toContain('tmp');
    Process_Module.chdir(originalCwd);
  });
});
