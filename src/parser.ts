import { Token, TokenType, Lexer } from './lexer';
import {
  Program,
  ASTNode,
  QueryNode,
  EncodeNode,
  PathNode,
  WeightNode,
  EnsembleNode,
  CritiqueNode,
  SampleNode,
  DetokenizeNode,
  createQueryNode,
  createEncodeNode,
  createPathNode,
  createWeightNode,
  createEnsembleNode,
  createCritiqueNode,
  createSampleNode,
  createDetokenizeNode,
} from './ast';

export class ParseError extends Error {
  constructor(message: string, token?: Token) {
    const loc = token ? ` at line ${token.line}, column ${token.column}` : '';
    super(`Parse error: ${message}${loc}`);
  }
}

export class Parser {
  private tokens: Token[];
  private position: number;
  private nodeIdCounter: number;

  constructor(tokens: Token[]) {
    this.tokens = tokens;
    this.position = 0;
    this.nodeIdCounter = 0;
  }

  parse(): Program {
    const statements: ASTNode[] = [];

    while (!this.isAtEnd()) {
      if (this.check(TokenType.EOF)) break;

      const stmt = this.parseStatement();
      if (stmt) {
        if (Array.isArray(stmt)) {
          statements.push(...stmt);
        } else {
          statements.push(stmt);
        }
      }
    }

    return { statements };
  }

  private parseStatement(): ASTNode | ASTNode[] | null {
    if (this.match(TokenType.QUERY)) {
      return this.parseQuery();
    } else if (this.match(TokenType.ENCODE)) {
      return this.parseEncode();
    } else if (this.match(TokenType.FORK)) {
      return this.parseFork();
    } else if (this.match(TokenType.WEIGHT)) {
      return this.parseWeight();
    } else if (this.match(TokenType.ENSEMBLE)) {
      return this.parseEnsemble();
    } else if (this.match(TokenType.CRITIQUE)) {
      return this.parseCritique();
    } else if (this.match(TokenType.SAMPLE)) {
      return this.parseSample();
    } else if (this.match(TokenType.DETOKENIZE)) {
      return this.parseDetokenize();
    } else if (this.check(TokenType.SEMICOLON)) {
      this.advance();
      return null;
    } else {
      throw new ParseError(
        `Unexpected token: ${this.peek().value}`,
        this.peek()
      );
    }
  }

  private parseQuery(): QueryNode {
    const varName = this.expectIdentifier('variable name after query');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createQueryNode(nodeId, varName);
  }

  private parseEncode(): EncodeNode {
    const inputVar = this.expectIdentifier('input variable for encode');
    this.expectArrow();
    const outputVar = this.expectIdentifier('output variable for encode');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createEncodeNode(nodeId, inputVar, outputVar);
  }

  private parseFork(): ASTNode[] {
    const inputVar = this.expectIdentifier('input variable for fork');
    this.expectArrow();

    if (this.match(TokenType.LBRACE)) {
      const vars: string[] = [];

      vars.push(this.expectIdentifier('path variable in fork'));

      while (this.match(TokenType.COMMA)) {
        vars.push(this.expectIdentifier('path variable in fork'));
      }

      this.expect(TokenType.RBRACE, 'closing brace after path variables');

      if (vars.length !== 3) {
        throw new ParseError(`Fork must create exactly 3 paths, got ${vars.length}`);
      }

      this.consumeStatementEnd();

      const nodes: ASTNode[] = [];
      nodes.push(
        createPathNode(this.nextNodeId(), 'analytical', inputVar, vars[0])
      );
      nodes.push(
        createPathNode(this.nextNodeId(), 'creative', inputVar, vars[1])
      );
      nodes.push(
        createPathNode(this.nextNodeId(), 'empirical', inputVar, vars[2])
      );

      return nodes;
    } else {
      throw new ParseError('Expected { after fork arrow');
    }
  }

  private parseWeight(): WeightNode {
    let weights: { alpha: number; beta: number; gamma: number } | undefined;

    if (this.match(TokenType.LBRACKET)) {
      const alpha = this.expectSignedNumber('weight alpha value');
      this.expect(TokenType.COMMA, 'comma between weights');
      const beta = this.expectSignedNumber('weight beta value');
      this.expect(TokenType.COMMA, 'comma between weights');
      const gamma = this.expectSignedNumber('weight gamma value');
      this.expect(TokenType.RBRACKET, 'closing bracket after weights');

      weights = { alpha, beta, gamma };
    }

    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createWeightNode(nodeId, '', { weights });
  }

  private parseEnsemble(): EnsembleNode {
    const pathVar1 = this.expectIdentifier('first path variable for ensemble');
    const pathVar2 = this.expectIdentifier('second path variable for ensemble');
    const pathVar3 = this.expectIdentifier('third path variable for ensemble');

    // optional: with <weightsVar>
    let weightsVar = 'weights';
    if (this.check(TokenType.IDENT) && this.peek().value === 'with') {
      this.advance(); // 'with' 소비
      weightsVar = this.expectIdentifier('weights variable after with');
    }

    this.expectArrow();

    const outputVar = this.expectIdentifier('output variable for ensemble');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createEnsembleNode(nodeId, [pathVar1, pathVar2, pathVar3], weightsVar, outputVar);
  }

  private parseCritique(): CritiqueNode {
    const inputVar = this.expectIdentifier('input variable for critique');
    this.expectArrow();
    const outputVar = this.expectIdentifier('output variable for critique');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createCritiqueNode(nodeId, inputVar, outputVar);
  }

  private parseSample(): SampleNode {
    const inputVar = this.expectIdentifier('input variable for sample');
    let threshold: number | undefined;

    if (this.check(TokenType.NUMBER)) {
      threshold = this.expectNumber('sampling threshold');
    }

    this.expectArrow();

    const outputVar = this.expectIdentifier('output variable for sample');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createSampleNode(nodeId, inputVar, outputVar, { threshold });
  }

  private parseDetokenize(): DetokenizeNode {
    const inputVar = this.expectIdentifier('input variable for detokenize');
    this.expectArrow();
    const outputVar = this.expectIdentifier('output variable for detokenize');
    this.consumeStatementEnd();

    const nodeId = this.nextNodeId();
    return createDetokenizeNode(nodeId, inputVar, outputVar);
  }

  private expectArrow(): void {
    this.expect(TokenType.ARROW, 'arrow (->)');
  }

  private expectIdentifier(context: string): string {
    if (!this.check(TokenType.IDENT)) {
      throw new ParseError(`Expected identifier ${context}, got ${this.peek().value}`);
    }
    const value = this.peek().value as string;
    this.advance();
    return value;
  }

  private expectNumber(context: string): number {
    if (!this.check(TokenType.NUMBER)) {
      throw new ParseError(`Expected number ${context}, got ${this.peek().value}`);
    }
    const value = this.peek().value as number;
    this.advance();
    return value;
  }

  private expectSignedNumber(context: string): number {
    let sign = 1;
    if (this.match(TokenType.MINUS)) {
      sign = -1;
    }
    return sign * this.expectNumber(context);
  }

  private expect(type: TokenType, context: string): Token {
    if (!this.check(type)) {
      throw new ParseError(
        `Expected ${context}, got ${this.peek().value}`,
        this.peek()
      );
    }
    const token = this.peek();
    this.advance();
    return token;
  }

  private match(...types: TokenType[]): boolean {
    for (const type of types) {
      if (this.check(type)) {
        this.advance();
        return true;
      }
    }
    return false;
  }

  private check(type: TokenType): boolean {
    if (this.isAtEnd()) return false;
    return this.peek().type === type;
  }

  private advance(): Token {
    if (!this.isAtEnd()) this.position++;
    return this.previous();
  }

  private isAtEnd(): boolean {
    return this.peek().type === TokenType.EOF;
  }

  private peek(): Token {
    return this.tokens[this.position];
  }

  private previous(): Token {
    return this.tokens[this.position - 1];
  }

  private consumeStatementEnd(): void {
    if (this.match(TokenType.SEMICOLON)) {
      return;
    }
    if (this.check(TokenType.EOF) || this.isNewStatement()) {
      return;
    }
  }

  private isNewStatement(): boolean {
    const type = this.peek().type;
    return (
      type === TokenType.QUERY ||
      type === TokenType.ENCODE ||
      type === TokenType.FORK ||
      type === TokenType.WEIGHT ||
      type === TokenType.ENSEMBLE ||
      type === TokenType.CRITIQUE ||
      type === TokenType.SAMPLE ||
      type === TokenType.DETOKENIZE
    );
  }

  private nextNodeId(): number {
    return this.nodeIdCounter++;
  }
}

export function parse(source: string): Program {
  const lexer = new Lexer(source);
  const tokens = lexer.tokenize();
  const parser = new Parser(tokens);
  return parser.parse();
}

export function parseProgram(source: string): Program {
  return parse(source);
}
