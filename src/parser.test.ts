import { parse, Parser, ParseError } from './parser';
import { Lexer } from './lexer';
import {
  isQueryNode,
  isEncodeNode,
  isPathNode,
  isWeightNode,
  isEnsembleNode,
  isCritiqueNode,
  isSampleNode,
  isDetokenizeNode,
  QueryNode,
  EncodeNode,
  EnsembleNode,
  WeightNode,
} from './ast';

describe('Parser', () => {
  function parseSource(source: string) {
    return parse(source);
  }

  describe('Query Parsing', () => {
    test('parses simple query', () => {
      const program = parseSource('query q');
      expect(program.statements.length).toBe(1);
      expect(isQueryNode(program.statements[0])).toBe(true);
      expect((program.statements[0] as QueryNode).varName).toBe('q');
    });

    test('parses query with semicolon', () => {
      const program = parseSource('query q;');
      expect(program.statements.length).toBe(1);
      expect((program.statements[0] as QueryNode).varName).toBe('q');
    });

    test('parses multiple queries', () => {
      const program = parseSource('query q1\nquery q2\nquery q3');
      expect(program.statements.length).toBe(3);
      expect((program.statements[0] as QueryNode).varName).toBe('q1');
      expect((program.statements[1] as QueryNode).varName).toBe('q2');
      expect((program.statements[2] as QueryNode).varName).toBe('q3');
    });
  });

  describe('Encode Parsing', () => {
    test('parses simple encode', () => {
      const program = parseSource('encode q -> z');
      expect(program.statements.length).toBe(1);
      expect(isEncodeNode(program.statements[0])).toBe(true);
      const enc = program.statements[0] as EncodeNode;
      expect(enc.inputVar).toBe('q');
      expect(enc.outputVar).toBe('z');
    });

    test('parses encode with underscore variables', () => {
      const program = parseSource('encode query_in -> latent_out');
      expect(program.statements.length).toBe(1);
      const enc = program.statements[0] as EncodeNode;
      expect(enc.inputVar).toBe('query_in');
      expect(enc.outputVar).toBe('latent_out');
    });
  });

  describe('Fork Parsing', () => {
    test('parses fork into three paths', () => {
      const program = parseSource('fork z -> { z_a, z_b, z_c }');
      expect(program.statements.length).toBe(3);
      expect(isPathNode(program.statements[0])).toBe(true);
      expect(isPathNode(program.statements[1])).toBe(true);
      expect(isPathNode(program.statements[2])).toBe(true);
    });

    test('fork creates correct path types', () => {
      const program = parseSource('fork z -> { z_a, z_b, z_c }');
      const paths = program.statements.filter(isPathNode);
      expect(paths[0].pathType).toBe('analytical');
      expect(paths[1].pathType).toBe('creative');
      expect(paths[2].pathType).toBe('empirical');
    });

    test('fork with different variable names', () => {
      const program = parseSource('fork latent -> { analytical, creative, empirical }');
      const paths = program.statements.filter(isPathNode);
      expect(paths[0].outputVar).toBe('analytical');
      expect(paths[1].outputVar).toBe('creative');
      expect(paths[2].outputVar).toBe('empirical');
    });

    test('fork rejects fewer than 3 paths', () => {
      expect(() => parseSource('fork z -> { z_a, z_b }')).toThrow(ParseError);
    });
  });

  describe('Weight Parsing', () => {
    test('parses weight with simplex values', () => {
      const program = parseSource('weight [0.5, 0.3, 0.2]');
      expect(program.statements.length).toBe(1);
      expect(isWeightNode(program.statements[0])).toBe(true);
      const weights = program.statements[0] as WeightNode;
      expect(weights.weights).toBeDefined();
      if (weights.weights) {
        expect(weights.weights.alpha).toBe(0.5);
        expect(weights.weights.beta).toBe(0.3);
        expect(weights.weights.gamma).toBe(0.2);
      }
    });

    test('parses weight with equal distribution', () => {
      const program = parseSource('weight [0.33, 0.33, 0.34]');
      const weights = program.statements[0] as WeightNode;
      if (weights.weights) {
        expect(weights.weights.alpha + weights.weights.beta + weights.weights.gamma).toBeCloseTo(1.0, 5);
      }
    });

    test('parses weight with integers', () => {
      const program = parseSource('weight [1, 0, 0]');
      const weights = program.statements[0] as WeightNode;
      if (weights.weights) {
        expect(weights.weights.alpha).toBe(1);
        expect(weights.weights.beta).toBe(0);
        expect(weights.weights.gamma).toBe(0);
      }
    });
  });

  describe('Ensemble Parsing', () => {
    test('parses ensemble', () => {
      const program = parseSource('ensemble z_a z_b z_c -> result');
      expect(program.statements.length).toBe(1);
      expect(isEnsembleNode(program.statements[0])).toBe(true);
      const ens = program.statements[0] as EnsembleNode;
      expect(ens.pathVars[0]).toBe('z_a');
      expect(ens.pathVars[1]).toBe('z_b');
      expect(ens.pathVars[2]).toBe('z_c');
      expect(ens.outputVar).toBe('result');
    });

    test('parses ensemble with different names', () => {
      const program = parseSource('ensemble analytical creative empirical -> ensemble_result');
      const ens = program.statements[0] as EnsembleNode;
      expect(ens.pathVars[0]).toBe('analytical');
      expect(ens.outputVar).toBe('ensemble_result');
    });
  });

  describe('Critique Parsing', () => {
    test('parses critique', () => {
      const program = parseSource('critique result -> delta');
      expect(program.statements.length).toBe(1);
      expect(isCritiqueNode(program.statements[0])).toBe(true);
      const crit = program.statements[0];
      if (isCritiqueNode(crit)) {
        expect(crit.inputVar).toBe('result');
        expect(crit.outputVar).toBe('delta');
      }
    });

    test('parses critique with descriptive names', () => {
      const program = parseSource('critique ensemble_out -> confidence_score');
      const crit = program.statements[0];
      if (isCritiqueNode(crit)) {
        expect(crit.inputVar).toBe('ensemble_out');
        expect(crit.outputVar).toBe('confidence_score');
      }
    });
  });

  describe('Sample Parsing', () => {
    test('parses sample without threshold', () => {
      const program = parseSource('sample delta -> output');
      expect(program.statements.length).toBe(1);
      expect(isSampleNode(program.statements[0])).toBe(true);
      const samp = program.statements[0];
      if (isSampleNode(samp)) {
        expect(samp.inputVar).toBe('delta');
        expect(samp.outputVar).toBe('output');
      }
    });

    test('parses sample with threshold', () => {
      const program = parseSource('sample delta 0.9 -> output');
      const samp = program.statements[0];
      if (isSampleNode(samp)) {
        expect(samp.threshold).toBe(0.9);
        expect(samp.outputVar).toBe('output');
      }
    });

    test('parses sample with different thresholds', () => {
      const program1 = parseSource('sample confidence 0.1 -> token1');
      const program2 = parseSource('sample confidence 0.5 -> token2');
      const program3 = parseSource('sample confidence 0.99 -> token3');

      const samp1 = program1.statements[0];
      const samp2 = program2.statements[0];
      const samp3 = program3.statements[0];

      if (isSampleNode(samp1)) expect(samp1.threshold).toBe(0.1);
      if (isSampleNode(samp2)) expect(samp2.threshold).toBe(0.5);
      if (isSampleNode(samp3)) expect(samp3.threshold).toBe(0.99);
    });
  });

  describe('Detokenize Parsing', () => {
    test('parses detokenize', () => {
      const program = parseSource('detokenize output -> korean_text');
      expect(program.statements.length).toBe(1);
      expect(isDetokenizeNode(program.statements[0])).toBe(true);
      const det = program.statements[0];
      if (isDetokenizeNode(det)) {
        expect(det.inputVar).toBe('output');
        expect(det.outputVar).toBe('korean_text');
      }
    });
  });

  describe('Complete Programs', () => {
    test('parses simple pipeline', () => {
      const source = `query q
encode q -> z
fork z -> { z_a, z_b, z_c }
weight [0.5, 0.3, 0.2]
ensemble z_a z_b z_c -> result
critique result -> delta
sample delta 0.9 -> output
detokenize output -> korean_text`;

      const program = parseSource(source);
      expect(program.statements.length).toBeGreaterThan(8);

      let hasQuery = false;
      let hasEncode = false;
      let hasEnsemble = false;
      let hasCritique = false;

      for (const stmt of program.statements) {
        if (isQueryNode(stmt)) hasQuery = true;
        if (isEncodeNode(stmt)) hasEncode = true;
        if (isEnsembleNode(stmt)) hasEnsemble = true;
        if (isCritiqueNode(stmt)) hasCritique = true;
      }

      expect(hasQuery).toBe(true);
      expect(hasEncode).toBe(true);
      expect(hasEnsemble).toBe(true);
      expect(hasCritique).toBe(true);
    });

    test('parses program with comments', () => {
      const source = `# Initialize query
query q
# Encode to latent space
encode q -> z`;

      const program = parseSource(source);
      expect(program.statements.length).toBe(2);
    });

    test('parses program with empty lines', () => {
      const source = `query q

encode q -> z

fork z -> { z_a, z_b, z_c }`;

      const program = parseSource(source);
      expect(program.statements.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Error Handling', () => {
    test('throws on missing identifier', () => {
      expect(() => parseSource('query')).toThrow(ParseError);
    });

    test('throws on missing arrow', () => {
      expect(() => parseSource('encode q z')).toThrow(ParseError);
    });

    test('throws on missing output variable', () => {
      expect(() => parseSource('encode q ->')).toThrow(ParseError);
    });

    test('throws on invalid statement', () => {
      expect(() => parseSource('invalid_keyword x y z')).toThrow(ParseError);
    });

    test('throws on unmatched brace in fork', () => {
      expect(() => parseSource('fork z -> { z_a, z_b')).toThrow(ParseError);
    });

    test('throws on missing closing brace in weight', () => {
      expect(() => parseSource('weight [0.5, 0.3, 0.2')).toThrow(ParseError);
    });
  });

  describe('Whitespace Handling', () => {
    test('handles multiple spaces', () => {
      const program = parseSource('query    q');
      expect(program.statements.length).toBe(1);
    });

    test('handles tabs', () => {
      const program = parseSource('query\tq');
      expect(program.statements.length).toBe(1);
    });

    test('handles mixed whitespace', () => {
      const program = parseSource('encode   q  \t->  z');
      expect(program.statements.length).toBe(1);
    });
  });

  describe('Program Structure', () => {
    test('identifies statement types', () => {
      const program = parseSource(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }
ensemble z_a z_b z_c -> result`);

      const types = program.statements.map(s => s.nodeType);
      expect(types).toContain('QueryNode');
      expect(types).toContain('EncodeNode');
      expect(types).toContain('PathNode');
      expect(types).toContain('EnsembleNode');
    });

    test('maintains statement order', () => {
      const program = parseSource(`query q
encode q -> z
critique z -> c`);

      expect(isQueryNode(program.statements[0])).toBe(true);
      expect(isEncodeNode(program.statements[1])).toBe(true);
      expect(isCritiqueNode(program.statements[2])).toBe(true);
    });
  });

  describe('Node IDs', () => {
    test('assigns unique node IDs', () => {
      const program = parseSource(`query q
encode q -> z
fork z -> { z_a, z_b, z_c }`);

      const ids = new Set();
      for (const stmt of program.statements) {
        expect(stmt.id).toBeDefined();
        ids.add(stmt.id);
      }
      expect(ids.size).toBeGreaterThan(1);
    });

    test('IDs are numeric and incrementing', () => {
      const program = parseSource(`query q
encode q -> z`);

      expect(typeof program.statements[0].id).toBe('number');
      expect(typeof program.statements[1].id).toBe('number');
      expect((program.statements[1].id as number) > (program.statements[0].id as number)).toBe(true);
    });
  });

  describe('Complex Variable Names', () => {
    test('handles underscores', () => {
      const program = parseSource('query query_variable');
      const q = program.statements[0] as QueryNode;
      expect(q.varName).toBe('query_variable');
    });

    test('handles numbers in names', () => {
      const program = parseSource('query z_123');
      const q = program.statements[0] as QueryNode;
      expect(q.varName).toBe('z_123');
    });

    test('handles single letter variables', () => {
      const program = parseSource('query x');
      const q = program.statements[0] as QueryNode;
      expect(q.varName).toBe('x');
    });
  });

  describe('Semantic Validation (Pre-Type-Check)', () => {
    test('recognizes all fork outputs', () => {
      const program = parseSource('fork z -> { a, b, c }');
      const paths = program.statements.filter(isPathNode);
      expect(paths.length).toBe(3);
      expect(paths.map(p => p.outputVar)).toEqual(['a', 'b', 'c']);
    });

    test('path types are assigned correctly', () => {
      const program = parseSource('fork z -> { p1, p2, p3 }');
      const paths = program.statements.filter(isPathNode);
      expect(paths[0].pathType).toBe('analytical');
      expect(paths[1].pathType).toBe('creative');
      expect(paths[2].pathType).toBe('empirical');
    });
  });
});
