import { parse } from './parser';
import { check, typeInference, validateConstraints, Checker, MindLangType } from './checker';

describe('Type Checker', () => {
  describe('Query Type', () => {
    test('assigns Query type to query statements', () => {
      const program = parse('query q');
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.symbolTable.has('q')).toBe(true);
      const qType = result.symbolTable.get('q');
      expect(qType?.type).toBe('Query');
    });

    test('query has dimension 768', () => {
      const program = parse('query q');
      const result = check(program);

      const qType = result.symbolTable.get('q');
      expect(qType?.dimension).toBe(768);
    });

    test('multiple queries', () => {
      const program = parse(`query q1
query q2
query q3`);
      const result = check(program);

      expect(result.symbolTable.has('q1')).toBe(true);
      expect(result.symbolTable.has('q2')).toBe(true);
      expect(result.symbolTable.has('q3')).toBe(true);
    });
  });

  describe('Encode Type', () => {
    test('encode transforms Query to Latent', () => {
      const program = parse(`query q
encode q -> z`);
      const result = check(program);

      expect(result.valid).toBe(true);
      const zType = result.symbolTable.get('z');
      expect(zType?.type).toBe('Latent');
    });

    test('encode has dimension 512', () => {
      const program = parse(`query q
encode q -> z`);
      const result = check(program);

      const zType = result.symbolTable.get('z');
      expect(zType?.dimension).toBe(512);
    });

    test('errors when encoding undefined variable', () => {
      const program = parse('encode undefined -> z');
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0]).toContain('not defined');
    });

    test('warns when encoding wrong type', () => {
      const program = parse(`query q
query q2
encode q2 -> z
encode z -> z2`);
      const result = check(program);

      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Path Type', () => {
    test('paths have type Path', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }`);
      const result = check(program);

      expect(result.symbolTable.has('z_a')).toBe(true);
      expect(result.symbolTable.has('z_b')).toBe(true);
      expect(result.symbolTable.has('z_c')).toBe(true);

      const zaType = result.symbolTable.get('z_a');
      expect(zaType?.type).toBe('Path');
    });

    test('path dimensions match latent', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }`);
      const result = check(program);

      const zaType = result.symbolTable.get('z_a');
      expect(zaType?.dimension).toBe(512);
    });

    test('paths have analytical, creative, empirical constraints', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }`);
      const result = check(program);

      const zaType = result.symbolTable.get('z_a');
      expect(zaType?.constraints).toContain('analytical');

      const zbType = result.symbolTable.get('z_b');
      expect(zbType?.constraints).toContain('creative');

      const zcType = result.symbolTable.get('z_c');
      expect(zcType?.constraints).toContain('empirical');
    });

    test('error when forking non-latent', () => {
      const program = parse(`query q
fork q -> { q_a, q_b, q_c }`);
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    test('error when forking undefined', () => {
      const program = parse('fork undefined -> { a, b, c }');
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain('not defined');
    });
  });

  describe('Weight Type', () => {
    test('weight has Weight type', () => {
      const program = parse('weight [0.5, 0.3, 0.2]');
      const result = check(program);

      expect(result.symbolTable.has('weights')).toBe(true);
      const wType = result.symbolTable.get('weights');
      expect(wType?.type).toBe('Weight');
    });

    test('weight has simplex constraint', () => {
      const program = parse('weight [0.5, 0.3, 0.2]');
      const result = check(program);

      const wType = result.symbolTable.get('weights');
      expect(wType?.constraints).toContain('simplex');
    });

    test('rejects non-simplex weights', () => {
      const program = parse('weight [0.5, 0.3, 0.3]');
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain('simplex constraint');
    });

    test('rejects negative weights', () => {
      const program = parse('weight [-0.1, 0.6, 0.5]');
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain('[0, 1]');
    });

    test('rejects weights > 1', () => {
      const program = parse('weight [1.1, 0.0, 0.0]');
      const result = check(program);

      expect(result.valid).toBe(false);
    });

    test('accepts valid simplex', () => {
      const program = parse('weight [0.33, 0.33, 0.34]');
      const result = check(program);

      expect(result.valid).toBe(true);
    });

    test('accepts corner simplex', () => {
      const program = parse('weight [1.0, 0.0, 0.0]');
      const result = check(program);

      expect(result.valid).toBe(true);
    });
  });

  describe('Ensemble Type', () => {
    test('ensemble has Ensemble type', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result`);
      const result = check(program);

      expect(result.symbolTable.has('result')).toBe(true);
      const resType = result.symbolTable.get('result');
      expect(resType?.type).toBe('Ensemble');
    });

    test('ensemble dimension matches paths', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result`);
      const result = check(program);

      const resType = result.symbolTable.get('result');
      expect(resType?.dimension).toBe(512);
    });

    test('error when ensemble with non-paths', () => {
      const program = parse(`query q
ensemble q q q -> result`);
      const result = check(program);

      expect(result.valid).toBe(false);
    });

    test('error when ensemble undefined paths', () => {
      const program = parse('ensemble a b c -> result');
      const result = check(program);

      expect(result.valid).toBe(false);
    });

    test('warning when weights not defined', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result`);
      const result = check(program);

      expect(result.warnings.length).toBeGreaterThan(0);
    });

    test('no warning when weights defined', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
weight [0.5, 0.3, 0.2]
ensemble z_a z_b z_c -> result`);
      const result = check(program);

      const warnings = result.warnings.filter(w => w.includes('Weight'));
      expect(warnings.length).toBe(0);
    });
  });

  describe('Critique Type', () => {
    test('critique has Critique type', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result
critique result -> delta`);
      const result = check(program);

      expect(result.symbolTable.has('delta')).toBe(true);
      const deltaType = result.symbolTable.get('delta');
      expect(deltaType?.type).toBe('Critique');
    });

    test('critique has range constraint', () => {
      const program = parse(`query q
encode q -> z
critique z -> c`);
      const result = check(program);

      const cType = result.symbolTable.get('c');
      expect(cType?.constraints).toContain('range');
    });

    test('warning when critiquing non-ensemble', () => {
      const program = parse(`query q
critique q -> c`);
      const result = check(program);

      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings[0]).toContain('Critique');
    });

    test('error when critiquing undefined', () => {
      const program = parse('critique undefined -> c');
      const result = check(program);

      expect(result.valid).toBe(false);
    });
  });

  describe('Sample Type', () => {
    test('sample has Output type', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result
sample result -> output`);
      const result = check(program);

      expect(result.symbolTable.has('output')).toBe(true);
      const outType = result.symbolTable.get('output');
      expect(outType?.type).toBe('Output');
    });

    test('sample with threshold constraint', () => {
      const program = parse(`query q
encode q -> z
sample z 0.5 -> token`);
      const result = check(program);

      expect(result.valid).toBe(true);
    });

    test('rejects threshold outside [0, 1]', () => {
      const program = parse(`query q
sample q 1.5 -> token`);
      const result = check(program);

      expect(result.valid).toBe(false);
      expect(result.errors[0]).toContain('[0, 1]');
    });

    test('error when sampling undefined', () => {
      const program = parse('sample undefined -> token');
      const result = check(program);

      expect(result.valid).toBe(false);
    });
  });

  describe('Detokenize Type', () => {
    test('detokenize has Output type', () => {
      const program = parse(`query q
detokenize q -> text`);
      const result = check(program);

      expect(result.symbolTable.has('text')).toBe(true);
      const textType = result.symbolTable.get('text');
      expect(textType?.type).toBe('Output');
    });

    test('detokenize has korean constraint', () => {
      const program = parse(`query q
detokenize q -> korean`);
      const result = check(program);

      const krType = result.symbolTable.get('korean');
      expect(krType?.constraints).toContain('korean');
    });

    test('error when detokenizing undefined', () => {
      const program = parse('detokenize undefined -> text');
      const result = check(program);

      expect(result.valid).toBe(false);
    });
  });

  describe('Complete Pipeline', () => {
    test('valid complete pipeline', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
weight [0.5, 0.3, 0.2]
ensemble z_a z_b z_c -> result
critique result -> delta
sample delta 0.9 -> output
detokenize output -> korean_text`);
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.errors.length).toBe(0);
    });

    test('tracks all variables', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result
critique result -> delta
sample delta -> output
detokenize output -> text`);
      const result = check(program);

      const varNames = ['q', 'z', 'z_a', 'z_b', 'z_c', 'result', 'delta', 'output', 'text'];
      for (const name of varNames) {
        expect(result.symbolTable.has(name)).toBe(true);
      }
    });

    test('validates type flow through pipeline', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result
critique result -> delta
sample delta -> output
detokenize output -> text`);
      const result = check(program);

      expect(result.symbolTable.get('q')?.type).toBe('Query');
      expect(result.symbolTable.get('z')?.type).toBe('Latent');
      expect(result.symbolTable.get('z_a')?.type).toBe('Path');
      expect(result.symbolTable.get('result')?.type).toBe('Ensemble');
      expect(result.symbolTable.get('delta')?.type).toBe('Critique');
      expect(result.symbolTable.get('output')?.type).toBe('Output');
      expect(result.symbolTable.get('text')?.type).toBe('Output');
    });
  });

  describe('Type Inference', () => {
    test('infers types without explicit annotations', () => {
      const program = parse(`query q
encode q -> z`);
      const symbols = typeInference(program);

      expect(symbols.has('q')).toBe(true);
      expect(symbols.has('z')).toBe(true);
      expect(symbols.get('q')?.type).toBe('Query');
      expect(symbols.get('z')?.type).toBe('Latent');
    });

    test('infers path types', () => {
      const program = parse(`query q
encode q -> z
fork z -> { a, b, c }`);
      const symbols = typeInference(program);

      expect(symbols.get('a')?.constraints).toContain('analytical');
      expect(symbols.get('b')?.constraints).toContain('creative');
      expect(symbols.get('c')?.constraints).toContain('empirical');
    });

    test('infers ensemble type', () => {
      const program = parse(`query q
encode q -> z
fork z -> { a, b, c }
ensemble a b c -> result`);
      const symbols = typeInference(program);

      expect(symbols.get('result')?.type).toBe('Ensemble');
    });
  });

  describe('Constraint Validation', () => {
    test('validates simplex constraint', () => {
      const program1 = parse('weight [0.5, 0.3, 0.2]');
      const program2 = parse('weight [0.5, 0.3, 0.3]');

      const result1 = validateConstraints(program1);
      const result2 = validateConstraints(program2);

      expect(result1.valid).toBe(true);
      expect(result2.valid).toBe(false);
    });

    test('validates threshold constraint', () => {
      const program1 = parse('query q\nsample q 0.5 -> token');
      const program2 = parse('query q\nsample q 1.5 -> token');

      const result1 = validateConstraints(program1);
      const result2 = validateConstraints(program2);

      expect(result1.valid).toBe(true);
      expect(result2.valid).toBe(false);
    });

    test('validates dimension constraints', () => {
      const program = parse(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }`);
      const result = validateConstraints(program);

      expect(result.valid).toBe(true);
    });
  });

  describe('Error Messages', () => {
    test('undefined variable error', () => {
      const program = parse('encode undefined -> z');
      const result = check(program);

      expect(result.errors[0]).toContain('undefined');
      expect(result.errors[0]).toContain('not defined');
    });

    test('type mismatch error', () => {
      const program = parse(`query q
fork q -> { a, b, c }`);
      const result = check(program);

      expect(result.errors[0]).toContain('Path expects Latent');
    });

    test('constraint violation error', () => {
      const program = parse('weight [0.5, 0.3, 0.3]');
      const result = check(program);

      expect(result.errors[0]).toContain('simplex');
    });
  });

  describe('Multiple Statements', () => {
    test('checks multiple queries', () => {
      const program = parse(`query q1
query q2
query q3`);
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.symbolTable.size).toBe(3);
    });

    test('checks multiple encodes', () => {
      const program = parse(`query q1
query q2
encode q1 -> z1
encode q2 -> z2`);
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.symbolTable.get('z1')?.type).toBe('Latent');
      expect(result.symbolTable.get('z2')?.type).toBe('Latent');
    });

    test('sequential variable dependencies', () => {
      const program = parse(`query q
encode q -> z1
encode z1 -> z2`);
      const result = check(program);

      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    test('empty program', () => {
      const program = parse('');
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.symbolTable.size).toBe(0);
    });

    test('program with only queries', () => {
      const program = parse(`query q1
query q2
query q3`);
      const result = check(program);

      expect(result.valid).toBe(true);
    });

    test('single statement program', () => {
      const program = parse('query q');
      const result = check(program);

      expect(result.valid).toBe(true);
      expect(result.symbolTable.size).toBe(1);
    });
  });
});
