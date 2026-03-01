import * as Crypto_Module from './crypto';

describe('Crypto - Hash Functions', () => {
  test('hash with sha256 works', () => {
    const data = 'hello world';
    const hash = Crypto_Module.hash(data, 'sha256');

    expect(hash).toBeTruthy();
    expect(hash.length).toBeGreaterThan(0);
    expect(/^[a-f0-9]+$/.test(hash)).toBe(true);
  });

  test('hash with md5 works', () => {
    const data = 'test data';
    const hash = Crypto_Module.hash(data, 'md5');

    expect(hash).toBeTruthy();
    expect(hash.length).toBe(32); // MD5 = 32 hex chars
  });

  test('hash with sha1 works', () => {
    const hash = Crypto_Module.hash('test', 'sha1');
    expect(hash.length).toBe(40); // SHA1 = 40 hex chars
  });

  test('hash with sha512 works', () => {
    const hash = Crypto_Module.hash('test', 'sha512');
    expect(hash.length).toBe(128); // SHA512 = 128 hex chars
  });

  test('hash is deterministic', () => {
    const data = 'hello';
    const hash1 = Crypto_Module.hash(data);
    const hash2 = Crypto_Module.hash(data);

    expect(hash1).toBe(hash2);
  });

  test('hash differs for different input', () => {
    const hash1 = Crypto_Module.hash('hello');
    const hash2 = Crypto_Module.hash('world');

    expect(hash1).not.toBe(hash2);
  });

  test('verifyHash validates correct hash', () => {
    const data = 'secret';
    const h = Crypto_Module.hash(data);

    const valid = Crypto_Module.verifyHash(data, h);
    expect(valid).toBe(true);
  });

  test('verifyHash rejects wrong hash', () => {
    const data = 'secret';
    const wrongHash = Crypto_Module.hash('other');

    const valid = Crypto_Module.verifyHash(data, wrongHash);
    expect(valid).toBe(false);
  });
});

describe('Crypto - HMAC Functions', () => {
  test('hmac creates HMAC', () => {
    const data = 'message';
    const secret = 'secret-key';
    const h = Crypto_Module.hmac(data, secret);

    expect(h).toBeTruthy();
    expect(/^[a-f0-9]+$/.test(h)).toBe(true);
  });

  test('hmac is deterministic', () => {
    const data = 'test';
    const secret = 'key';

    const h1 = Crypto_Module.hmac(data, secret);
    const h2 = Crypto_Module.hmac(data, secret);

    expect(h1).toBe(h2);
  });

  test('hmac differs for different secret', () => {
    const data = 'test';

    const h1 = Crypto_Module.hmac(data, 'key1');
    const h2 = Crypto_Module.hmac(data, 'key2');

    expect(h1).not.toBe(h2);
  });

  test('hmac with different algorithm', () => {
    const data = 'test';
    const secret = 'key';

    const h256 = Crypto_Module.hmac(data, secret, 'sha256');
    const h512 = Crypto_Module.hmac(data, secret, 'sha512');

    expect(h256).not.toBe(h512);
  });

  test('verifyHmac validates correct HMAC', () => {
    const data = 'message';
    const secret = 'secret';
    const h = Crypto_Module.hmac(data, secret);

    const valid = Crypto_Module.verifyHmac(data, h, secret);
    expect(valid).toBe(true);
  });

  test('verifyHmac rejects wrong HMAC', () => {
    const data = 'message';
    const secret = 'secret';
    const wrongHmac = Crypto_Module.hmac('other', secret);

    const valid = Crypto_Module.verifyHmac(data, wrongHmac, secret);
    expect(valid).toBe(false);
  });
});

describe('Crypto - Random Functions', () => {
  test('randomBytes generates random hex', () => {
    const rand = Crypto_Module.randomBytes(16);

    expect(rand).toBeTruthy();
    expect(rand.length).toBe(32); // 16 bytes = 32 hex chars
    expect(/^[a-f0-9]+$/.test(rand)).toBe(true);
  });

  test('randomBytes generates different values', () => {
    const rand1 = Crypto_Module.randomBytes(16);
    const rand2 = Crypto_Module.randomBytes(16);

    expect(rand1).not.toBe(rand2);
  });

  test('randomBytesBuffer generates buffer', () => {
    const rand = Crypto_Module.randomBytesBuffer(16);

    expect(Buffer.isBuffer(rand)).toBe(true);
    expect(rand.length).toBe(16);
  });

  test('randomUUID generates valid UUID', () => {
    const uuid = Crypto_Module.randomUUID();

    expect(uuid).toBeTruthy();
    expect(uuid.length).toBe(36); // Standard UUID length
    expect(uuid.includes('-')).toBe(true);
  });

  test('randomUUID generates different UUIDs', () => {
    const uuid1 = Crypto_Module.randomUUID();
    const uuid2 = Crypto_Module.randomUUID();

    expect(uuid1).not.toBe(uuid2);
  });
});

describe('Crypto - Encryption/Decryption', () => {
  test('encrypt and decrypt work', () => {
    const key = Crypto_Module.generateKey();
    const plaintext = 'secret message';

    const encrypted = Crypto_Module.encrypt(plaintext, key);
    const decrypted = Crypto_Module.decrypt(encrypted, key);

    expect(decrypted).toBe(plaintext);
  });

  test('encrypt with custom IV works', () => {
    const key = Crypto_Module.generateKey();
    const iv = Crypto_Module.generateIV();
    const plaintext = 'secret message';

    const encrypted = Crypto_Module.encrypt(plaintext, key, iv);
    const decrypted = Crypto_Module.decrypt(encrypted, key);

    expect(decrypted).toBe(plaintext);
  });

  test('encrypt produces different ciphertexts', () => {
    const key = Crypto_Module.generateKey();
    const plaintext = 'same message';

    const encrypted1 = Crypto_Module.encrypt(plaintext, key);
    const encrypted2 = Crypto_Module.encrypt(plaintext, key);

    expect(encrypted1).not.toBe(encrypted2);
  });

  test('decrypt with wrong key fails', () => {
    const key1 = Crypto_Module.generateKey();
    const key2 = Crypto_Module.generateKey();
    const plaintext = 'secret';

    const encrypted = Crypto_Module.encrypt(plaintext, key1);

    expect(() => {
      Crypto_Module.decrypt(encrypted, key2);
    }).toThrow();
  });
});

describe('Crypto - Compression', () => {
  test('compress and decompress work', async () => {
    const data = 'Hello, World! This is a test string for compression.';

    const compressed = await Crypto_Module.compress(data);
    expect(Buffer.isBuffer(compressed)).toBe(true);

    const decompressed = await Crypto_Module.decompress(compressed);
    expect(decompressed.toString()).toBe(data);
  });

  test('compressString and decompressString work', async () => {
    const data = 'Test data for compression';

    const compressed = await Crypto_Module.compressString(data);
    expect(typeof compressed).toBe('string');

    const decompressed = await Crypto_Module.decompressString(compressed);
    expect(decompressed).toBe(data);
  });

  test('compression reduces size for repetitive data', async () => {
    const data = 'a'.repeat(1000);

    const original = Buffer.byteLength(data);
    const compressed = await Crypto_Module.compress(data);

    expect(compressed.length).toBeLessThan(original);
  });
});

describe('Crypto - Encoding Functions', () => {
  test('base64Encode and base64Decode work', () => {
    const data = 'hello world';

    const encoded = Crypto_Module.base64Encode(data);
    expect(typeof encoded).toBe('string');

    const decoded = Crypto_Module.base64Decode(encoded);
    expect(decoded).toBe(data);
  });

  test('hexEncode and hexDecode work', () => {
    const data = 'test string';

    const encoded = Crypto_Module.hexEncode(data);
    expect(/^[a-f0-9]+$/.test(encoded)).toBe(true);

    const decoded = Crypto_Module.hexDecode(encoded);
    expect(decoded).toBe(data);
  });

  test('urlSafeBase64Encode and urlSafeBase64Decode work', () => {
    const data = 'hello+world/data=';

    const encoded = Crypto_Module.urlSafeBase64Encode(data);
    expect(encoded.includes('=')).toBe(false);
    expect(!encoded.includes('/') && !encoded.includes('+')).toBe(true);

    const decoded = Crypto_Module.urlSafeBase64Decode(encoded);
    expect(decoded).toBe(data);
  });

  test('base64Encode handles buffer', () => {
    const buffer = Buffer.from('binary data');
    const encoded = Crypto_Module.base64Encode(buffer);

    expect(typeof encoded).toBe('string');
    const decoded = Crypto_Module.base64Decode(encoded);
    expect(decoded).toBe('binary data');
  });
});

describe('Crypto - Key Generation', () => {
  test('generateKey creates key', () => {
    const key = Crypto_Module.generateKey();

    expect(key).toBeTruthy();
    expect(key.length).toBe(64); // 32 bytes = 64 hex chars
  });

  test('generateKey with custom size', () => {
    const key = Crypto_Module.generateKey(16);

    expect(key.length).toBe(32); // 16 bytes = 32 hex chars
  });

  test('generateIV creates IV', () => {
    const iv = Crypto_Module.generateIV();

    expect(iv).toBeTruthy();
    expect(iv.length).toBe(32); // 16 bytes = 32 hex chars
  });

  test('generateIV with custom size', () => {
    const iv = Crypto_Module.generateIV(8);

    expect(iv.length).toBe(16); // 8 bytes = 16 hex chars
  });

  test('generateKey creates different keys', () => {
    const key1 = Crypto_Module.generateKey();
    const key2 = Crypto_Module.generateKey();

    expect(key1).not.toBe(key2);
  });
});
