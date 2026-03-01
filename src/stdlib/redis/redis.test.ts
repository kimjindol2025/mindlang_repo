import * as Redis_Module from './redis';

describe('Cache - Basic Operations', () => {
  let cache: Redis_Module.Cache;

  beforeEach(() => {
    cache = Redis_Module.createCache();
  });

  test('set and get stores value', () => {
    cache.set('key1', 'value1');
    expect(cache.get('key1')).toBe('value1');
  });

  test('set overwrites existing value', () => {
    cache.set('key1', 'value1');
    cache.set('key1', 'value2');
    expect(cache.get('key1')).toBe('value2');
  });

  test('get returns null for nonexistent key', () => {
    expect(cache.get('nonexistent')).toBeNull();
  });

  test('has checks key existence', () => {
    cache.set('key1', 'value1');
    expect(cache.has('key1')).toBe(true);
    expect(cache.has('nonexistent')).toBe(false);
  });

  test('delete removes key', () => {
    cache.set('key1', 'value1');
    expect(cache.has('key1')).toBe(true);

    const deleted = cache.delete('key1');
    expect(deleted).toBe(true);
    expect(cache.has('key1')).toBe(false);
  });

  test('delete returns false for nonexistent key', () => {
    const deleted = cache.delete('nonexistent');
    expect(deleted).toBe(false);
  });

  test('keys returns all keys', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');
    cache.set('key3', 'value3');

    const keys = cache.keys();
    expect(keys).toContain('key1');
    expect(keys).toContain('key2');
    expect(keys).toContain('key3');
    expect(keys.length).toBe(3);
  });

  test('clear removes all entries', () => {
    cache.set('key1', 'value1');
    cache.set('key2', 'value2');

    cache.clear();
    expect(cache.size()).toBe(0);
    expect(cache.keys().length).toBe(0);
  });

  test('size returns cache size', () => {
    expect(cache.size()).toBe(0);

    cache.set('key1', 'value1');
    expect(cache.size()).toBe(1);

    cache.set('key2', 'value2');
    expect(cache.size()).toBe(2);

    cache.delete('key1');
    expect(cache.size()).toBe(1);
  });

  test('set with TTL expires value', async () => {
    cache.set('temp', 'value', 100);
    expect(cache.get('temp')).toBe('value');

    await new Promise((resolve) => setTimeout(resolve, 150));
    expect(cache.get('temp')).toBeNull();
  });

  test('ttl returns remaining time', () => {
    cache.set('key1', 'value1', 1000);
    const ttl = cache.ttl('key1');

    expect(ttl).toBeGreaterThan(0);
    expect(ttl).toBeLessThanOrEqual(1000);
  });

  test('ttl returns -1 for permanent key', () => {
    cache.set('key1', 'value1');
    expect(cache.ttl('key1')).toBe(-1);
  });

  test('ttl returns -2 for nonexistent key', () => {
    expect(cache.ttl('nonexistent')).toBe(-2);
  });

  test('expire sets expiration', async () => {
    cache.set('key1', 'value1');
    const success = cache.expire('key1', 100);

    expect(success).toBe(true);
    expect(cache.get('key1')).toBe('value1');

    await new Promise((resolve) => setTimeout(resolve, 150));
    expect(cache.get('key1')).toBeNull();
  });

  test('expire returns false for nonexistent key', () => {
    const success = cache.expire('nonexistent', 1000);
    expect(success).toBe(false);
  });
});

describe('Cache - Numeric Operations', () => {
  let cache: Redis_Module.Cache;

  beforeEach(() => {
    cache = Redis_Module.createCache();
  });

  test('increment increments value', () => {
    cache.set('counter', 5);
    const value = cache.increment('counter', 3);

    expect(value).toBe(8);
    expect(cache.get('counter')).toBe(8);
  });

  test('increment creates key if not exists', () => {
    const value = cache.increment('new_counter', 1);

    expect(value).toBe(1);
    expect(cache.get('new_counter')).toBe(1);
  });

  test('decrement decrements value', () => {
    cache.set('counter', 10);
    const value = cache.decrement('counter', 3);

    expect(value).toBe(7);
    expect(cache.get('counter')).toBe(7);
  });

  test('decrement with default delta', () => {
    cache.set('counter', 5);
    const value = cache.decrement('counter');

    expect(value).toBe(4);
  });
});

describe('Cache - List Operations', () => {
  let cache: Redis_Module.Cache;

  beforeEach(() => {
    cache = Redis_Module.createCache();
  });

  test('push adds items to list', () => {
    const len1 = cache.push('list', 'item1');
    expect(len1).toBe(1);

    const len2 = cache.push('list', 'item2', 'item3');
    expect(len2).toBe(3);

    const list = cache.get('list');
    expect(list).toEqual(['item1', 'item2', 'item3']);
  });

  test('pop removes item from list', () => {
    cache.push('list', 'item1', 'item2', 'item3');

    const popped = cache.pop('list');
    expect(popped).toBe('item3');

    const list = cache.get('list');
    expect(list).toEqual(['item1', 'item2']);
  });

  test('pop returns null for empty list', () => {
    const popped = cache.pop('empty_list');
    expect(popped).toBeNull();
  });

  test('listLength returns list size', () => {
    cache.push('list', 'a', 'b', 'c');
    expect(cache.listLength('list')).toBe(3);
  });

  test('listLength returns 0 for nonexistent key', () => {
    expect(cache.listLength('nonexistent')).toBe(0);
  });
});

describe('Cache - Subscriptions', () => {
  let cache: Redis_Module.Cache;

  beforeEach(() => {
    cache = Redis_Module.createCache();
  });

  test('subscribe notifies on set', () => {
    const callback = jest.fn();
    cache.subscribe('key1', callback);

    cache.set('key1', 'value1');
    expect(callback).toHaveBeenCalledWith('value1');

    cache.set('key1', 'value2');
    expect(callback).toHaveBeenCalledWith('value2');
    expect(callback).toHaveBeenCalledTimes(2);
  });

  test('unsubscribe stops notifications', () => {
    const callback = jest.fn();
    cache.subscribe('key1', callback);

    cache.set('key1', 'value1');
    expect(callback).toHaveBeenCalledTimes(1);

    cache.unsubscribe('key1', callback);
    cache.set('key1', 'value2');
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('multiple subscriptions on same key', () => {
    const callback1 = jest.fn();
    const callback2 = jest.fn();

    cache.subscribe('key1', callback1);
    cache.subscribe('key1', callback2);

    cache.set('key1', 'value1');

    expect(callback1).toHaveBeenCalledWith('value1');
    expect(callback2).toHaveBeenCalledWith('value1');
  });
});

describe('Queue - Basic Operations', () => {
  let queue: Redis_Module.Queue;

  beforeEach(() => {
    queue = Redis_Module.createQueue();
  });

  test('push adds item to queue', () => {
    const id = queue.push('item1');
    expect(id).toBeTruthy();
    expect(queue.size()).toBe(1);
  });

  test('pop removes item from queue', () => {
    queue.push('item1');
    queue.push('item2');

    const item1 = queue.pop();
    expect(item1?.data).toBe('item1');

    const item2 = queue.pop();
    expect(item2?.data).toBe('item2');

    expect(queue.size()).toBe(0);
  });

  test('pop returns null for empty queue', () => {
    const item = queue.pop();
    expect(item).toBeNull();
  });

  test('size returns queue size', () => {
    expect(queue.size()).toBe(0);

    queue.push('item1');
    expect(queue.size()).toBe(1);

    queue.push('item2');
    expect(queue.size()).toBe(2);

    queue.pop();
    expect(queue.size()).toBe(1);
  });

  test('clear removes all items', () => {
    queue.push('item1');
    queue.push('item2');
    queue.push('item3');

    queue.clear();
    expect(queue.size()).toBe(0);
  });

  test('getAll returns all items', () => {
    queue.push('item1');
    queue.push('item2');

    const items = queue.getAll();
    expect(items.length).toBe(2);
    expect(items[0].data).toBe('item1');
    expect(items[1].data).toBe('item2');
  });

  test('getById retrieves item by ID', () => {
    const id = queue.push('item1');
    const item = queue.getById(id);

    expect(item).not.toBeNull();
    expect(item?.data).toBe('item1');
  });

  test('removeById removes item by ID', () => {
    const id = queue.push('item1');
    queue.push('item2');

    const removed = queue.removeById(id);
    expect(removed).toBe(true);
    expect(queue.size()).toBe(1);
  });

  test('removeById returns false for nonexistent ID', () => {
    const removed = queue.removeById('nonexistent-id');
    expect(removed).toBe(false);
  });
});

describe('Queue - Priority Queue', () => {
  let queue: Redis_Module.Queue;

  beforeEach(() => {
    queue = Redis_Module.createQueue();
  });

  test('pushWithPriority adds item with priority', () => {
    queue.pushWithPriority('low', 1);
    queue.pushWithPriority('high', 10);
    queue.pushWithPriority('medium', 5);

    const items = queue.getAll();
    expect(items[0].data).toBe('high');
    expect(items[1].data).toBe('medium');
    expect(items[2].data).toBe('low');
  });

  test('priority queue maintains order on pop', () => {
    queue.pushWithPriority('low', 1);
    queue.pushWithPriority('high', 10);
    queue.pushWithPriority('medium', 5);

    const first = queue.pop();
    expect(first?.data).toBe('high');

    const second = queue.pop();
    expect(second?.data).toBe('medium');

    const third = queue.pop();
    expect(third?.data).toBe('low');
  });

  test('queue timestamp is recorded', () => {
    const before = Date.now();
    const id = queue.push('item');
    const after = Date.now();

    const item = queue.getById(id);
    expect(item?.timestamp).toBeGreaterThanOrEqual(before);
    expect(item?.timestamp).toBeLessThanOrEqual(after);
  });
});
