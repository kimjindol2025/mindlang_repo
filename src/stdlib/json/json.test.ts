import * as JSON_Module from './json';

describe('JSON - Basic Operations', () => {
  test('parse simple object', () => {
    const json = '{"name":"Alice","age":30}';
    const result = JSON_Module.parse(json);
    expect(result.name).toBe('Alice');
    expect(result.age).toBe(30);
  });

  test('parse array', () => {
    const json = '[1,2,3,4,5]';
    const result = JSON_Module.parse(json);
    expect(result).toEqual([1, 2, 3, 4, 5]);
  });

  test('stringify object', () => {
    const obj = { name: 'Bob', age: 25 };
    const result = JSON_Module.stringify(obj);
    expect(result).toBe('{"name":"Bob","age":25}');
  });

  test('stringify with indent', () => {
    const obj = { name: 'Charlie' };
    const result = JSON_Module.stringify(obj, undefined, 2);
    expect(result).toContain('  "name"');
  });

  test('parse array of objects', () => {
    const json = '[{"id":1,"name":"Alice"},{"id":2,"name":"Bob"}]';
    const result = JSON_Module.parse(json);
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBe(2);
    expect(result[0].name).toBe('Alice');
  });
});

describe('JSON - Validation', () => {
  test('isValid with valid json', () => {
    expect(JSON_Module.isValid('{"name":"test"}')).toBe(true);
    expect(JSON_Module.isValid('[1,2,3]')).toBe(true);
    expect(JSON_Module.isValid('"string"')).toBe(true);
  });

  test('isValid with invalid json', () => {
    expect(JSON_Module.isValid('{invalid}')).toBe(false);
    expect(JSON_Module.isValid("{'key': 'value'}")). toBe(false);
    expect(JSON_Module.isValid('undefined')).toBe(false);
  });

  test('parse invalid json throws', () => {
    expect(() => JSON_Module.parse('{invalid}')).toThrow();
  });
});

describe('JSON - Formatting', () => {
  test('format adds indentation', () => {
    const json = '{"name":"test","age":30}';
    const formatted = JSON_Module.format(json);
    expect(formatted).toContain('\n');
    expect(formatted).toContain('  ');
  });

  test('format with custom indent', () => {
    const json = '{"name":"test"}';
    const formatted = JSON_Module.format(json, 4);
    expect(formatted).toContain('    ');
  });

  test('minify removes whitespace', () => {
    const json = '{\n  "name": "test",\n  "age": 30\n}';
    const minified = JSON_Module.minify(json);
    expect(minified).toBe('{"name":"test","age":30}');
  });
});

describe('JSON - Deep Clone', () => {
  test('deepClone copies object', () => {
    const original = { name: 'test', nested: { value: 42 } };
    const cloned = JSON_Module.deepClone(original);
    expect(cloned).toEqual(original);
    expect(cloned).not.toBe(original);
    expect(cloned.nested).not.toBe(original.nested);
  });

  test('deepClone handles arrays', () => {
    const original = [1, 2, { value: 3 }];
    const cloned = JSON_Module.deepClone(original);
    expect(cloned).toEqual(original);
    expect(cloned).not.toBe(original);
  });
});

describe('JSON - Merge', () => {
  test('merge shallow objects', () => {
    const obj1 = { name: 'Alice', age: 30 };
    const obj2 = { age: 31, city: 'NY' };
    const result = JSON_Module.merge(obj1, obj2);
    expect(result.name).toBe('Alice');
    expect(result.age).toBe(31);
    expect(result.city).toBe('NY');
  });

  test('merge deep objects', () => {
    const obj1 = { user: { name: 'Alice', age: 30 } };
    const obj2 = { user: { age: 31 } };
    const result = JSON_Module.merge(obj1, obj2, true);
    expect(result.user.name).toBe('Alice');
    expect(result.user.age).toBe(31);
  });
});

describe('JSON - Path Operations', () => {
  test('getByPath retrieves value', () => {
    const obj = { user: { profile: { name: 'Alice' } } };
    expect(JSON_Module.getByPath(obj, 'user.profile.name')).toBe('Alice');
    expect(JSON_Module.getByPath(obj, 'user.profile.age')).toBeUndefined();
  });

  test('setByPath sets value', () => {
    const obj: any = {};
    JSON_Module.setByPath(obj, 'user.profile.name', 'Bob');
    expect(obj.user.profile.name).toBe('Bob');
  });

  test('deleteByPath removes value', () => {
    const obj = { user: { name: 'Alice', age: 30 } };
    JSON_Module.deleteByPath(obj, 'user.age');
    expect((obj as any).user.age).toBeUndefined();
    expect((obj as any).user.name).toBe('Alice');
  });
});

describe('JSON - Utilities', () => {
  test('pick selects keys', () => {
    const obj = { name: 'Alice', age: 30, city: 'NY' };
    const result = JSON_Module.pick(obj, ['name', 'age']);
    expect(result).toEqual({ name: 'Alice', age: 30 });
  });

  test('omit excludes keys', () => {
    const obj = { name: 'Alice', age: 30, city: 'NY' };
    const result = JSON_Module.omit(obj, ['city']);
    expect(result).toEqual({ name: 'Alice', age: 30 });
  });

  test('getSize returns byte size', () => {
    const obj = { name: 'test' };
    const size = JSON_Module.getSize(obj);
    expect(size).toBeGreaterThan(0);
  });

  test('equals compares objects', () => {
    const obj1 = { name: 'Alice', age: 30 };
    const obj2 = { name: 'Alice', age: 30 };
    const obj3 = { name: 'Bob', age: 25 };
    expect(JSON_Module.equals(obj1, obj2)).toBe(true);
    expect(JSON_Module.equals(obj1, obj3)).toBe(false);
  });
});
