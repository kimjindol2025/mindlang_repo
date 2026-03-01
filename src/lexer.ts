export enum TokenType {
  QUERY = 'QUERY',
  ENCODE = 'ENCODE',
  FORK = 'FORK',
  WEIGHT = 'WEIGHT',
  ENSEMBLE = 'ENSEMBLE',
  CRITIQUE = 'CRITIQUE',
  SAMPLE = 'SAMPLE',
  DETOKENIZE = 'DETOKENIZE',

  NUMBER = 'NUMBER',
  STRING = 'STRING',
  IDENT = 'IDENT',

  LPAREN = 'LPAREN',
  RPAREN = 'RPAREN',
  LBRACE = 'LBRACE',
  RBRACE = 'RBRACE',
  LBRACKET = 'LBRACKET',
  RBRACKET = 'RBRACKET',

  ARROW = 'ARROW',
  DOT = 'DOT',
  COMMA = 'COMMA',
  SEMICOLON = 'SEMICOLON',
  COLON = 'COLON',

  PLUS = 'PLUS',
  MINUS = 'MINUS',
  STAR = 'STAR',
  SLASH = 'SLASH',
  PERCENT = 'PERCENT',

  EQUALS = 'EQUALS',
  LPIPE = 'LPIPE',
  RPIPE = 'RPIPE',

  EOF = 'EOF',
  UNKNOWN = 'UNKNOWN',
}

export interface Token {
  type: TokenType;
  value: string | number;
  line: number;
  column: number;
}

export class Lexer {
  private source: string;
  private position: number;
  private line: number;
  private column: number;
  private tokens: Token[] = [];

  constructor(source: string) {
    this.source = source;
    this.position = 0;
    this.line = 1;
    this.column = 1;
  }

  tokenize(): Token[] {
    while (this.position < this.source.length) {
      this.skipWhitespaceAndComments();
      if (this.position >= this.source.length) break;

      const char = this.source[this.position];

      if (this.isDigit(char)) {
        this.readNumber();
      } else if (this.isStringDelimiter(char)) {
        this.readString();
      } else if (this.isIdentifierStart(char)) {
        this.readIdentifierOrKeyword();
      } else if (char === '(') {
        this.addToken(TokenType.LPAREN, '(');
        this.advance();
      } else if (char === ')') {
        this.addToken(TokenType.RPAREN, ')');
        this.advance();
      } else if (char === '{') {
        this.addToken(TokenType.LBRACE, '{');
        this.advance();
      } else if (char === '}') {
        this.addToken(TokenType.RBRACE, '}');
        this.advance();
      } else if (char === '[') {
        this.addToken(TokenType.LBRACKET, '[');
        this.advance();
      } else if (char === ']') {
        this.addToken(TokenType.RBRACKET, ']');
        this.advance();
      } else if (char === '-' && this.peek() === '>') {
        this.addToken(TokenType.ARROW, '->');
        this.advance();
        this.advance();
      } else if (char === '.') {
        this.addToken(TokenType.DOT, '.');
        this.advance();
      } else if (char === ',') {
        this.addToken(TokenType.COMMA, ',');
        this.advance();
      } else if (char === ';') {
        this.addToken(TokenType.SEMICOLON, ';');
        this.advance();
      } else if (char === ':') {
        this.addToken(TokenType.COLON, ':');
        this.advance();
      } else if (char === '+') {
        this.addToken(TokenType.PLUS, '+');
        this.advance();
      } else if (char === '-') {
        this.addToken(TokenType.MINUS, '-');
        this.advance();
      } else if (char === '*') {
        this.addToken(TokenType.STAR, '*');
        this.advance();
      } else if (char === '/') {
        this.addToken(TokenType.SLASH, '/');
        this.advance();
      } else if (char === '%') {
        this.addToken(TokenType.PERCENT, '%');
        this.advance();
      } else if (char === '=') {
        this.addToken(TokenType.EQUALS, '=');
        this.advance();
      } else if (char === '|') {
        if (this.peek() === '<') {
          this.addToken(TokenType.LPIPE, '|<');
          this.advance();
          this.advance();
        } else if (this.peek() === '>') {
          this.addToken(TokenType.RPIPE, '|>');
          this.advance();
          this.advance();
        } else {
          this.addToken(TokenType.UNKNOWN, char);
          this.advance();
        }
      } else {
        this.addToken(TokenType.UNKNOWN, char);
        this.advance();
      }
    }

    this.addToken(TokenType.EOF, '');
    return this.tokens;
  }

  private skipWhitespaceAndComments(): void {
    while (this.position < this.source.length) {
      const char = this.source[this.position];

      if (char === ' ' || char === '\t' || char === '\r') {
        this.advance();
      } else if (char === '\n') {
        this.line++;
        this.column = 1;
        this.position++;
      } else if (char === '#') {
        while (this.position < this.source.length && this.source[this.position] !== '\n') {
          this.advance();
        }
      } else {
        break;
      }
    }
  }

  private readNumber(): void {
    const startLine = this.line;
    const startColumn = this.column;
    let value = '';

    while (this.position < this.source.length && this.isDigit(this.source[this.position])) {
      value += this.source[this.position];
      this.advance();
    }

    if (this.source[this.position] === '.' && this.isDigit(this.source[this.position + 1])) {
      value += '.';
      this.advance();
      while (this.position < this.source.length && this.isDigit(this.source[this.position])) {
        value += this.source[this.position];
        this.advance();
      }
    }

    this.tokens.push({
      type: TokenType.NUMBER,
      value: parseFloat(value),
      line: startLine,
      column: startColumn,
    });
  }

  private readString(): void {
    const startLine = this.line;
    const startColumn = this.column;
    const delimiter = this.source[this.position];
    this.advance();

    let value = '';
    while (this.position < this.source.length && this.source[this.position] !== delimiter) {
      if (this.source[this.position] === '\\' && this.position + 1 < this.source.length) {
        this.advance();
        const nextChar = this.source[this.position];
        if (nextChar === 'n') value += '\n';
        else if (nextChar === 't') value += '\t';
        else if (nextChar === 'r') value += '\r';
        else if (nextChar === '\\') value += '\\';
        else if (nextChar === '"') value += '"';
        else if (nextChar === "'") value += "'";
        else value += nextChar;
      } else {
        value += this.source[this.position];
      }
      this.advance();
    }

    if (this.position < this.source.length) {
      this.advance();
    }

    this.tokens.push({
      type: TokenType.STRING,
      value,
      line: startLine,
      column: startColumn,
    });
  }

  private readIdentifierOrKeyword(): void {
    const startLine = this.line;
    const startColumn = this.column;
    let value = '';

    while (
      this.position < this.source.length &&
      this.isIdentifierChar(this.source[this.position])
    ) {
      value += this.source[this.position];
      this.advance();
    }

    const keywordMap: { [key: string]: TokenType } = {
      query: TokenType.QUERY,
      encode: TokenType.ENCODE,
      fork: TokenType.FORK,
      weight: TokenType.WEIGHT,
      ensemble: TokenType.ENSEMBLE,
      critique: TokenType.CRITIQUE,
      sample: TokenType.SAMPLE,
      detokenize: TokenType.DETOKENIZE,
    };

    const type = keywordMap[value] || TokenType.IDENT;
    this.tokens.push({
      type,
      value,
      line: startLine,
      column: startColumn,
    });
  }

  private addToken(type: TokenType, value: string | number): void {
    this.tokens.push({
      type,
      value,
      line: this.line,
      column: this.column,
    });
  }

  private advance(): void {
    this.column++;
    this.position++;
  }

  private peek(): string {
    if (this.position + 1 >= this.source.length) return '\0';
    return this.source[this.position + 1];
  }

  private isDigit(char: string): boolean {
    return char >= '0' && char <= '9';
  }

  private isIdentifierStart(char: string): boolean {
    return (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || char === '_';
  }

  private isIdentifierChar(char: string): boolean {
    return this.isIdentifierStart(char) || this.isDigit(char);
  }

  private isStringDelimiter(char: string): boolean {
    return char === '"' || char === "'";
  }
}

export function createLexer(source: string): Lexer {
  return new Lexer(source);
}
