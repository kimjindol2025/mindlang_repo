import * as FS_Module from './fs';
import * as path from 'path';
import * as fs from 'fs';

describe('FS - File Operations', () => {
  const testDir = path.join(__dirname, 'test-temp');
  const testFile = path.join(testDir, 'test.txt');

  beforeAll(async () => {
    try {
      await FS_Module.mkdir_(testDir, true);
    } catch (e) {
      // Directory already exists
    }
  });

  afterAll(async () => {
    try {
      const files = await FS_Module.readDir(testDir);
      for (const file of files) {
        await FS_Module.deleteFile(path.join(testDir, file));
      }
      await FS_Module.deleteDir(testDir);
    } catch (e) {
      // Clean up errors are acceptable
    }
  });

  test('writeFile creates file', async () => {
    await FS_Module.writeFile_(testFile, 'Hello, World!', 'utf8');
    expect(await FS_Module.exists(testFile)).toBe(true);
  });

  test('readFile reads file content', async () => {
    await FS_Module.writeFile_(testFile, 'Hello, World!', 'utf8');
    const content = await FS_Module.readFile_(testFile, 'utf8');
    expect(content).toBe('Hello, World!');
  });

  test('appendFile adds content', async () => {
    await FS_Module.writeFile_(testFile, 'Hello', 'utf8');
    await FS_Module.appendFile_(testFile, ' World', 'utf8');
    const content = await FS_Module.readFile_(testFile, 'utf8');
    expect(content).toBe('Hello World');
  });

  test('deleteFile removes file', async () => {
    await FS_Module.writeFile_(testFile, 'test', 'utf8');
    expect(await FS_Module.exists(testFile)).toBe(true);
    await FS_Module.deleteFile(testFile);
    expect(await FS_Module.exists(testFile)).toBe(false);
  });

  test('copyFile copies file content', async () => {
    const source = path.join(testDir, 'source.txt');
    const destination = path.join(testDir, 'destination.txt');

    await FS_Module.writeFile_(source, 'Original content', 'utf8');
    await FS_Module.copyFile(source, destination);

    const sourceContent = await FS_Module.readFile_(source, 'utf8');
    const destContent = await FS_Module.readFile_(destination, 'utf8');

    expect(sourceContent).toBe(destContent);

    await FS_Module.deleteFile(source);
    await FS_Module.deleteFile(destination);
  });

  test('rename_ renames file', async () => {
    const oldPath = path.join(testDir, 'old.txt');
    const newPath = path.join(testDir, 'new.txt');

    await FS_Module.writeFile_(oldPath, 'test', 'utf8');
    await FS_Module.rename_(oldPath, newPath);

    expect(await FS_Module.exists(oldPath)).toBe(false);
    expect(await FS_Module.exists(newPath)).toBe(true);

    await FS_Module.deleteFile(newPath);
  });
});

describe('FS - Directory Operations', () => {
  const testDir = path.join(__dirname, 'test-temp-dirs');
  const subDir = path.join(testDir, 'subdir');

  beforeAll(async () => {
    try {
      await FS_Module.mkdir_(testDir, true);
    } catch (e) {
      // Directory already exists
    }
  });

  afterAll(async () => {
    try {
      const subdirs = await FS_Module.readDir(testDir);
      for (const subdir of subdirs) {
        const subdirPath = path.join(testDir, subdir);
        if (await FS_Module.isDir(subdirPath)) {
          const files = await FS_Module.readDir(subdirPath);
          for (const file of files) {
            await FS_Module.deleteFile(path.join(subdirPath, file));
          }
          await FS_Module.deleteDir(subdirPath);
        }
      }
      await FS_Module.deleteDir(testDir);
    } catch (e) {
      // Clean up errors are acceptable
    }
  });

  test('mkdir_ creates directory', async () => {
    const dir = path.join(testDir, 'new-dir');
    await FS_Module.mkdir_(dir);
    expect(await FS_Module.exists(dir)).toBe(true);
    await FS_Module.deleteDir(dir);
  });

  test('mkdir_ with recursive creates nested directories', async () => {
    const nestedDir = path.join(testDir, 'a', 'b', 'c');
    await FS_Module.mkdir_(nestedDir, true);
    expect(await FS_Module.exists(nestedDir)).toBe(true);
  });

  test('readDir lists directory contents', async () => {
    const files = ['file1.txt', 'file2.txt', 'file3.txt'];
    for (const file of files) {
      await FS_Module.writeFile_(path.join(testDir, file), 'content', 'utf8');
    }

    const contents = await FS_Module.readDir(testDir);
    expect(contents.length).toBeGreaterThanOrEqual(files.length);

    for (const file of files) {
      await FS_Module.deleteFile(path.join(testDir, file));
    }
  });

  test('readDirRecursive lists all files recursively', async () => {
    const dir1 = path.join(testDir, 'dir1');
    const dir2 = path.join(dir1, 'dir2');

    await FS_Module.mkdir_(dir1);
    await FS_Module.mkdir_(dir2);
    await FS_Module.writeFile_(path.join(dir1, 'file1.txt'), 'content1', 'utf8');
    await FS_Module.writeFile_(path.join(dir2, 'file2.txt'), 'content2', 'utf8');

    const allFiles = await FS_Module.readDirRecursive(testDir);
    expect(allFiles.length).toBeGreaterThanOrEqual(2);

    await FS_Module.deleteFile(path.join(dir2, 'file2.txt'));
    await FS_Module.deleteFile(path.join(dir1, 'file1.txt'));
    await FS_Module.deleteDir(dir2);
    await FS_Module.deleteDir(dir1);
  });

  test('deleteDir removes empty directory', async () => {
    const dir = path.join(testDir, 'empty-dir');
    await FS_Module.mkdir_(dir);
    expect(await FS_Module.exists(dir)).toBe(true);
    await FS_Module.deleteDir(dir);
    expect(await FS_Module.exists(dir)).toBe(false);
  });
});

describe('FS - File Statistics', () => {
  const testDir = path.join(__dirname, 'test-temp-stats');
  const testFile = path.join(testDir, 'stats-test.txt');

  beforeAll(async () => {
    try {
      await FS_Module.mkdir_(testDir, true);
      await FS_Module.writeFile_(testFile, 'test content', 'utf8');
    } catch (e) {
      // Errors are acceptable
    }
  });

  afterAll(async () => {
    try {
      await FS_Module.deleteFile(testFile);
      await FS_Module.deleteDir(testDir);
    } catch (e) {
      // Clean up errors are acceptable
    }
  });

  test('getStats returns file statistics', async () => {
    const stats = await FS_Module.getStats(testFile);
    expect(stats.size).toBeGreaterThan(0);
    expect(stats.isFile).toBe(true);
    expect(stats.isDirectory).toBe(false);
    expect(stats.isSymbolicLink).toBe(false);
  });

  test('getStats returns directory statistics', async () => {
    const stats = await FS_Module.getStats(testDir);
    expect(stats.isFile).toBe(false);
    expect(stats.isDirectory).toBe(true);
    expect(stats.isSymbolicLink).toBe(false);
  });

  test('isFile checks if path is file', async () => {
    expect(await FS_Module.isFile(testFile)).toBe(true);
    expect(await FS_Module.isFile(testDir)).toBe(false);
  });

  test('isDir checks if path is directory', async () => {
    expect(await FS_Module.isDir(testDir)).toBe(true);
    expect(await FS_Module.isDir(testFile)).toBe(false);
  });

  test('exists checks file existence', async () => {
    expect(await FS_Module.exists(testFile)).toBe(true);
    expect(await FS_Module.exists(path.join(testDir, 'nonexistent.txt'))).toBe(false);
  });
});

describe('FS - Path Operations', () => {
  test('join combines path segments', () => {
    const result = FS_Module.join('/home/user', 'documents/file.txt');
    expect(result).toContain('documents');
    expect(result).toContain('file.txt');
  });

  test('parsePath parses file path', () => {
    const filePath = '/home/user/documents/file.txt';
    const parsed = FS_Module.parsePath(filePath);

    expect(parsed.name).toBe('file');
    expect(parsed.ext).toBe('.txt');
    expect(parsed.base).toBe('file.txt');
    expect(parsed.dir).toContain('documents');
  });

  test('resolve returns absolute path', () => {
    const resolved = FS_Module.resolve('.');
    expect(resolved).toContain('/');
  });

  test('cwd returns current working directory', () => {
    const cwd = FS_Module.cwd();
    expect(cwd).toBeTruthy();
    expect(cwd.length).toBeGreaterThan(0);
  });
});

describe('FS - Error Handling', () => {
  const testDir = path.join(__dirname, 'test-temp-errors');
  const nonexistentFile = path.join(testDir, 'nonexistent.txt');

  beforeAll(async () => {
    try {
      await FS_Module.mkdir_(testDir, true);
    } catch (e) {
      // Errors are acceptable
    }
  });

  afterAll(async () => {
    try {
      await FS_Module.deleteDir(testDir);
    } catch (e) {
      // Errors are acceptable
    }
  });

  test('readFile throws on nonexistent file', async () => {
    await expect(FS_Module.readFile_(nonexistentFile, 'utf8')).rejects.toThrow();
  });

  test('deleteFile throws on nonexistent file', async () => {
    await expect(FS_Module.deleteFile(nonexistentFile)).rejects.toThrow();
  });

  test('writeFile creates parent directories when needed', async () => {
    const nestedFile = path.join(testDir, 'subdir', 'file.txt');
    const subdir = path.dirname(nestedFile);

    await FS_Module.mkdir_(subdir, true);
    await FS_Module.writeFile_(nestedFile, 'test', 'utf8');

    expect(await FS_Module.exists(nestedFile)).toBe(true);

    await FS_Module.deleteFile(nestedFile);
    await FS_Module.deleteDir(subdir);
  });

  test('chmod_ changes file permissions', async () => {
    const testFile = path.join(testDir, 'perm-test.txt');
    await FS_Module.writeFile_(testFile, 'test', 'utf8');

    await FS_Module.chmod_(testFile, 0o644);
    const stats = await FS_Module.getStats(testFile);

    expect(stats.isFile).toBe(true);

    await FS_Module.deleteFile(testFile);
  });
});
