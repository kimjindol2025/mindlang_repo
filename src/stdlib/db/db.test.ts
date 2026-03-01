import * as DB_Module from './db';

describe('Database - Table Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
  });

  test('createTable creates new table', () => {
    db.createTable('users');
    expect(db.tableExists('users')).toBe(true);
  });

  test('tableExists checks table existence', () => {
    expect(db.tableExists('users')).toBe(false);
    db.createTable('users');
    expect(db.tableExists('users')).toBe(true);
  });

  test('listTables returns all tables', () => {
    db.createTable('users');
    db.createTable('posts');
    const tables = db.listTables();

    expect(tables).toContain('users');
    expect(tables).toContain('posts');
    expect(tables.length).toBe(2);
  });

  test('dropTable removes table', () => {
    db.createTable('users');
    expect(db.tableExists('users')).toBe(true);

    db.dropTable('users');
    expect(db.tableExists('users')).toBe(false);
  });

  test('truncate clears table data', () => {
    db.createTable('users');
    db.insert('users', { name: 'Alice' });
    db.insert('users', { name: 'Bob' });

    expect(db.count('users')).toBe(2);
    db.truncate('users');
    expect(db.count('users')).toBe(0);
  });
});

describe('Database - Insert Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
    db.createTable('users');
  });

  test('insert adds record to table', () => {
    const record = db.insert('users', { name: 'Alice', age: 30 });

    expect(record.id).toBe(1);
    expect(record.name).toBe('Alice');
    expect(record.age).toBe(30);
  });

  test('insert increments ID', () => {
    const rec1 = db.insert('users', { name: 'Alice' });
    const rec2 = db.insert('users', { name: 'Bob' });
    const rec3 = db.insert('users', { name: 'Charlie' });

    expect(rec1.id).toBe(1);
    expect(rec2.id).toBe(2);
    expect(rec3.id).toBe(3);
  });

  test('insertMany adds multiple records', () => {
    const records = db.insertMany('users', [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
      { name: 'Charlie', age: 35 },
    ]);

    expect(records.length).toBe(3);
    expect(records[0].name).toBe('Alice');
    expect(records[1].name).toBe('Bob');
    expect(records[2].name).toBe('Charlie');
  });

  test('insert throws for nonexistent table', () => {
    expect(() => {
      db.insert('nonexistent', { name: 'test' });
    }).toThrow();
  });
});

describe('Database - Read Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
    db.createTable('users');

    db.insertMany('users', [
      { name: 'Alice', age: 30, city: 'NY' },
      { name: 'Bob', age: 25, city: 'LA' },
      { name: 'Charlie', age: 35, city: 'NYC' },
    ]);
  });

  test('findById retrieves record by ID', () => {
    const record = db.findById('users', 1);

    expect(record).not.toBeNull();
    expect(record?.name).toBe('Alice');
    expect(record?.age).toBe(30);
  });

  test('findById returns null for nonexistent ID', () => {
    const record = db.findById('users', 999);
    expect(record).toBeNull();
  });

  test('findAll retrieves all records', () => {
    const records = db.findAll('users');

    expect(records.length).toBe(3);
    expect(records[0].name).toBe('Alice');
    expect(records[2].name).toBe('Charlie');
  });

  test('find retrieves records by condition', () => {
    const records = db.find('users', (r) => r.age > 28);

    expect(records.length).toBe(2);
    expect(records.some((r) => r.name === 'Alice')).toBe(true);
    expect(records.some((r) => r.name === 'Charlie')).toBe(true);
  });

  test('findOne retrieves single record by condition', () => {
    const record = db.findOne('users', (r) => r.name === 'Bob');

    expect(record).not.toBeNull();
    expect(record?.age).toBe(25);
    expect(record?.city).toBe('LA');
  });

  test('findOne returns null when no match', () => {
    const record = db.findOne('users', (r) => r.name === 'David');
    expect(record).toBeNull();
  });

  test('findAll with limit', () => {
    const records = db.findAll('users', { limit: 2 });

    expect(records.length).toBe(2);
  });

  test('findAll with offset', () => {
    const records = db.findAll('users', { offset: 1 });

    expect(records.length).toBe(2);
    expect(records[0].name).toBe('Bob');
  });

  test('findAll with ordering', () => {
    const records = db.findAll('users', { orderBy: 'age', orderDir: 'ASC' });

    expect(records[0].age).toBe(25);
    expect(records[2].age).toBe(35);
  });

  test('findAll with ordering descending', () => {
    const records = db.findAll('users', { orderBy: 'age', orderDir: 'DESC' });

    expect(records[0].age).toBe(35);
    expect(records[2].age).toBe(25);
  });
});

describe('Database - Update Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
    db.createTable('users');

    db.insertMany('users', [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
      { name: 'Charlie', age: 35 },
    ]);
  });

  test('update modifies record', () => {
    const updated = db.update('users', 1, { age: 31 });

    expect(updated?.name).toBe('Alice');
    expect(updated?.age).toBe(31);
  });

  test('update returns null for nonexistent ID', () => {
    const updated = db.update('users', 999, { age: 40 });
    expect(updated).toBeNull();
  });

  test('updateWhere modifies multiple records', () => {
    const count = db.updateWhere('users', (r) => r.age > 28, { status: 'senior' });

    expect(count).toBe(2);

    const alice = db.findById('users', 1) as any;
    expect(alice.status).toBe('senior');

    const bob = db.findById('users', 2) as any;
    expect(bob.status).toBeUndefined();
  });

  test('updateWhere returns count of updated records', () => {
    const count = db.updateWhere('users', (r) => r.age < 30, { verified: true });
    expect(count).toBe(1);
  });
});

describe('Database - Delete Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
    db.createTable('users');

    db.insertMany('users', [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
      { name: 'Charlie', age: 35 },
    ]);
  });

  test('delete removes record', () => {
    expect(db.count('users')).toBe(3);

    const deleted = db.delete('users', 1);
    expect(deleted).toBe(true);
    expect(db.count('users')).toBe(2);
  });

  test('delete returns false for nonexistent ID', () => {
    const deleted = db.delete('users', 999);
    expect(deleted).toBe(false);
  });

  test('deleteWhere removes matching records', () => {
    const count = db.deleteWhere('users', (r) => r.age > 28);

    expect(count).toBe(2);
    expect(db.count('users')).toBe(1);

    const remaining = db.findAll('users');
    expect(remaining[0].name).toBe('Bob');
  });

  test('deleteWhere returns count of deleted records', () => {
    const count = db.deleteWhere('users', (r) => r.name.startsWith('C'));
    expect(count).toBe(1);
  });
});

describe('Database - Count Operations', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
    db.createTable('users');

    db.insertMany('users', [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
      { name: 'Charlie', age: 35 },
    ]);
  });

  test('count returns table size', () => {
    expect(db.count('users')).toBe(3);
  });

  test('count returns 0 for empty table', () => {
    db.createTable('empty');
    expect(db.count('empty')).toBe(0);
  });

  test('countWhere returns matching record count', () => {
    const count = db.countWhere('users', (r) => r.age > 28);
    expect(count).toBe(2);
  });

  test('countWhere returns 0 when no match', () => {
    const count = db.countWhere('users', (r) => r.age > 100);
    expect(count).toBe(0);
  });
});

describe('Database - Import/Export', () => {
  let db: DB_Module.Database;

  beforeEach(() => {
    db = DB_Module.createDatabase();
  });

  test('export returns all table data', () => {
    db.createTable('users');
    db.insertMany('users', [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
    ]);

    const exported = db.export('users');

    expect(exported.length).toBe(2);
    expect(exported[0].name).toBe('Alice');
    expect(exported[1].name).toBe('Bob');
  });

  test('import loads data into table', () => {
    const data = [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
    ];

    db.import('users', data);

    expect(db.count('users')).toBe(2);
    expect(db.findById('users', 1)?.name).toBe('Alice');
    expect(db.findById('users', 2)?.name).toBe('Bob');
  });

  test('import and export roundtrip', () => {
    const original = [
      { name: 'Alice', age: 30 },
      { name: 'Bob', age: 25 },
    ];

    db.import('users', original);
    const exported = db.export('users');

    expect(exported.length).toBe(original.length);
    expect(exported[0].name).toBe(original[0].name);
  });
});
