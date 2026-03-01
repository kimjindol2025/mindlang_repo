import { Lexer, TokenType, Token } from './lexer';

describe('Lexer', () => {
  function lex(source: string): Token[] {
    const lexer = new Lexer(source);
    return lexer.tokenize();
  }

  describe('Keywords', () => {
    test('recognizes query keyword', () => {
      const tokens = lex('query');
      expect(tokens[0].type).toBe(TokenType.QUERY);
      expect(tokens[1].type).toBe(TokenType.EOF);
    });

    test('recognizes encode keyword', () => {
      const tokens = lex('encode');
      expect(tokens[0].type).toBe(TokenType.ENCODE);
    });

    test('recognizes fork keyword', () => {
      const tokens = lex('fork');
      expect(tokens[0].type).toBe(TokenType.FORK);
    });

    test('recognizes weight keyword', () => {
      const tokens = lex('weight');
      expect(tokens[0].type).toBe(TokenType.WEIGHT);
    });

    test('recognizes ensemble keyword', () => {
      const tokens = lex('ensemble');
      expect(tokens[0].type).toBe(TokenType.ENSEMBLE);
    });

    test('recognizes critique keyword', () => {
      const tokens = lex('critique');
      expect(tokens[0].type).toBe(TokenType.CRITIQUE);
    });

    test('recognizes sample keyword', () => {
      const tokens = lex('sample');
      expect(tokens[0].type).toBe(TokenType.SAMPLE);
    });

    test('recognizes detokenize keyword', () => {
      const tokens = lex('detokenize');
      expect(tokens[0].type).toBe(TokenType.DETOKENIZE);
    });
  });

  describe('Identifiers', () => {
    test('recognizes single letter identifier', () => {
      const tokens = lex('q');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[0].value).toBe('q');
    });

    test('recognizes multi-character identifier', () => {
      const tokens = lex('query_var');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[0].value).toBe('query_var');
    });

    test('recognizes identifier with numbers', () => {
      const tokens = lex('z_a123');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[0].value).toBe('z_a123');
    });

    test('multiple identifiers', () => {
      const tokens = lex('x y z');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[2].type).toBe(TokenType.IDENT);
      expect(tokens[3].type).toBe(TokenType.EOF);
    });
  });

  describe('Numbers', () => {
    test('recognizes integer', () => {
      const tokens = lex('42');
      expect(tokens[0].type).toBe(TokenType.NUMBER);
      expect(tokens[0].value).toBe(42);
    });

    test('recognizes float', () => {
      const tokens = lex('3.14');
      expect(tokens[0].type).toBe(TokenType.NUMBER);
      expect(tokens[0].value).toBe(3.14);
    });

    test('recognizes zero', () => {
      const tokens = lex('0');
      expect(tokens[0].type).toBe(TokenType.NUMBER);
      expect(tokens[0].value).toBe(0);
    });

    test('recognizes multiple numbers', () => {
      const tokens = lex('0.5 0.3 0.2');
      expect(tokens[0].type).toBe(TokenType.NUMBER);
      expect(tokens[0].value).toBe(0.5);
      expect(tokens[1].type).toBe(TokenType.NUMBER);
      expect(tokens[1].value).toBe(0.3);
      expect(tokens[2].type).toBe(TokenType.NUMBER);
      expect(tokens[2].value).toBe(0.2);
    });
  });

  describe('Strings', () => {
    test('recognizes double-quoted string', () => {
      const tokens = lex('"hello world"');
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('hello world');
    });

    test('recognizes single-quoted string', () => {
      const tokens = lex("'hello world'");
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('hello world');
    });

    test('recognizes string with escape sequences', () => {
      const tokens = lex('"hello\\nworld"');
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('hello\nworld');
    });

    test('recognizes korean string', () => {
      const tokens = lex('"안녕하세요"');
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('안녕하세요');
    });

    test('recognizes empty string', () => {
      const tokens = lex('""');
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('');
    });
  });

  describe('Punctuation', () => {
    test('recognizes left paren', () => {
      const tokens = lex('(');
      expect(tokens[0].type).toBe(TokenType.LPAREN);
    });

    test('recognizes right paren', () => {
      const tokens = lex(')');
      expect(tokens[0].type).toBe(TokenType.RPAREN);
    });

    test('recognizes left brace', () => {
      const tokens = lex('{');
      expect(tokens[0].type).toBe(TokenType.LBRACE);
    });

    test('recognizes right brace', () => {
      const tokens = lex('}');
      expect(tokens[0].type).toBe(TokenType.RBRACE);
    });

    test('recognizes left bracket', () => {
      const tokens = lex('[');
      expect(tokens[0].type).toBe(TokenType.LBRACKET);
    });

    test('recognizes right bracket', () => {
      const tokens = lex(']');
      expect(tokens[0].type).toBe(TokenType.RBRACKET);
    });

    test('recognizes arrow', () => {
      const tokens = lex('->');
      expect(tokens[0].type).toBe(TokenType.ARROW);
    });

    test('recognizes dot', () => {
      const tokens = lex('.');
      expect(tokens[0].type).toBe(TokenType.DOT);
    });

    test('recognizes comma', () => {
      const tokens = lex(',');
      expect(tokens[0].type).toBe(TokenType.COMMA);
    });

    test('recognizes semicolon', () => {
      const tokens = lex(';');
      expect(tokens[0].type).toBe(TokenType.SEMICOLON);
    });

    test('recognizes colon', () => {
      const tokens = lex(':');
      expect(tokens[0].type).toBe(TokenType.COLON);
    });
  });

  describe('Operators', () => {
    test('recognizes plus', () => {
      const tokens = lex('+');
      expect(tokens[0].type).toBe(TokenType.PLUS);
    });

    test('recognizes minus', () => {
      const tokens = lex('-');
      expect(tokens[0].type).toBe(TokenType.MINUS);
    });

    test('recognizes star', () => {
      const tokens = lex('*');
      expect(tokens[0].type).toBe(TokenType.STAR);
    });

    test('recognizes slash', () => {
      const tokens = lex('/');
      expect(tokens[0].type).toBe(TokenType.SLASH);
    });

    test('recognizes percent', () => {
      const tokens = lex('%');
      expect(tokens[0].type).toBe(TokenType.PERCENT);
    });

    test('recognizes equals', () => {
      const tokens = lex('=');
      expect(tokens[0].type).toBe(TokenType.EQUALS);
    });

    test('recognizes lpipe', () => {
      const tokens = lex('|<');
      expect(tokens[0].type).toBe(TokenType.LPIPE);
    });

    test('recognizes rpipe', () => {
      const tokens = lex('|>');
      expect(tokens[0].type).toBe(TokenType.RPIPE);
    });
  });

  describe('Whitespace and Comments', () => {
    test('skips spaces', () => {
      const tokens = lex('a   b');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[2].type).toBe(TokenType.EOF);
    });

    test('skips tabs', () => {
      const tokens = lex('a\tb');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[1].type).toBe(TokenType.IDENT);
    });

    test('skips comment', () => {
      const tokens = lex('a # comment\nb');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[0].value).toBe('a');
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[1].value).toBe('b');
    });

    test('handles newlines', () => {
      const tokens = lex('a\nb');
      expect(tokens[0].type).toBe(TokenType.IDENT);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[0].line).toBe(1);
      expect(tokens[1].line).toBe(2);
    });
  });

  describe('Complex Programs', () => {
    test('lexes simple query program', () => {
      const source = 'query q';
      const tokens = lex(source);
      expect(tokens[0].type).toBe(TokenType.QUERY);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[2].type).toBe(TokenType.EOF);
    });

    test('lexes encode statement', () => {
      const source = 'encode q -> z';
      const tokens = lex(source);
      expect(tokens[0].type).toBe(TokenType.ENCODE);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[2].type).toBe(TokenType.ARROW);
      expect(tokens[3].type).toBe(TokenType.IDENT);
    });

    test('lexes fork statement', () => {
      const source = 'fork z -> { z_a, z_b, z_c }';
      const tokens = lex(source);
      expect(tokens[0].type).toBe(TokenType.FORK);
      expect(tokens[1].type).toBe(TokenType.IDENT);
      expect(tokens[2].type).toBe(TokenType.ARROW);
      expect(tokens[3].type).toBe(TokenType.LBRACE);
      expect(tokens[4].type).toBe(TokenType.IDENT);
    });

    test('lexes weight statement', () => {
      const source = 'weight [0.5, 0.3, 0.2]';
      const tokens = lex(source);
      expect(tokens[0].type).toBe(TokenType.WEIGHT);
      expect(tokens[1].type).toBe(TokenType.LBRACKET);
      expect(tokens[2].type).toBe(TokenType.NUMBER);
    });

    test('lexes complete pipeline', () => {
      const source = `query q
encode q -> z
fork z -> {z_a, z_b, z_c}
weight [0.5, 0.3, 0.2]
ensemble z_a z_b z_c -> result
critique result -> delta
sample delta 0.9 -> output
detokenize output -> korean_text`;

      const tokens = lex(source);
      const types = tokens.map(t => t.type);

      expect(types[0]).toBe(TokenType.QUERY);
      expect(types[1]).toBe(TokenType.IDENT);
      expect(types).toContain(TokenType.ENCODE);
      expect(types).toContain(TokenType.FORK);
      expect(types).toContain(TokenType.WEIGHT);
      expect(types).toContain(TokenType.ENSEMBLE);
      expect(types).toContain(TokenType.CRITIQUE);
      expect(types).toContain(TokenType.SAMPLE);
      expect(types).toContain(TokenType.DETOKENIZE);
      expect(types[types.length - 1]).toBe(TokenType.EOF);
    });
  });

  describe('Line and Column Tracking', () => {
    test('tracks line numbers', () => {
      const tokens = lex('a\nb\nc');
      expect(tokens[0].line).toBe(1);
      expect(tokens[1].line).toBe(2);
      expect(tokens[2].line).toBe(3);
    });

    test('tracks column numbers', () => {
      const tokens = lex('a b c');
      expect(tokens[0].column).toBe(1);
      expect(tokens[1].column).toBe(3);
      expect(tokens[2].column).toBe(5);
    });

    test('resets column on newline', () => {
      const tokens = lex('abc\ndef');
      expect(tokens[0].column).toBe(1);
      expect(tokens[1].column).toBe(1);
    });
  });

  describe('Edge Cases', () => {
    test('handles empty input', () => {
      const tokens = lex('');
      expect(tokens.length).toBe(1);
      expect(tokens[0].type).toBe(TokenType.EOF);
    });

    test('handles only whitespace', () => {
      const tokens = lex('   \n  \t  ');
      expect(tokens.length).toBe(1);
      expect(tokens[0].type).toBe(TokenType.EOF);
    });

    test('handles only comments', () => {
      const tokens = lex('# comment\n# another comment');
      expect(tokens.length).toBe(1);
      expect(tokens[0].type).toBe(TokenType.EOF);
    });

    test('handles consecutive operators', () => {
      const tokens = lex('+-*/');
      expect(tokens[0].type).toBe(TokenType.PLUS);
      expect(tokens[1].type).toBe(TokenType.MINUS);
      expect(tokens[2].type).toBe(TokenType.STAR);
      expect(tokens[3].type).toBe(TokenType.SLASH);
    });

    test('distinguishes minus from arrow', () => {
      const tokens1 = lex('-');
      expect(tokens1[0].type).toBe(TokenType.MINUS);

      const tokens2 = lex('->');
      expect(tokens2[0].type).toBe(TokenType.ARROW);
    });

    test('handles large numbers', () => {
      const tokens = lex('999999999.999999');
      expect(tokens[0].type).toBe(TokenType.NUMBER);
      expect(tokens[0].value).toBe(999999999.999999);
    });

    test('handles consecutive strings', () => {
      const tokens = lex('"first" "second"');
      expect(tokens[0].type).toBe(TokenType.STRING);
      expect(tokens[0].value).toBe('first');
      expect(tokens[1].type).toBe(TokenType.STRING);
      expect(tokens[1].value).toBe('second');
    });
  });
});
