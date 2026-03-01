import { Program, ASTNode, getNodeInputVariables, getNodeOutputVariable } from './ast';
import {
  isQueryNode,
  isEncodeNode,
  isPathNode,
  isWeightNode,
  isEnsembleNode,
  isCritiqueNode,
  isSampleNode,
  isDetokenizeNode,
} from './ast';

export type MindLangType =
  | 'Query'
  | 'Latent'
  | 'Path'
  | 'Weight'
  | 'Ensemble'
  | 'Critique'
  | 'Output'
  | 'Unknown';

export interface TypeInfo {
  type: MindLangType;
  dimension?: number;
  constraints?: string[];
}

export class TypeError extends Error {
  constructor(message: string) {
    super(`Type error: ${message}`);
  }
}

export class Checker {
  private symbolTable: Map<string, TypeInfo>;
  private errors: string[];
  private warnings: string[];

  constructor() {
    this.symbolTable = new Map();
    this.errors = [];
    this.warnings = [];
  }

  check(program: Program): void {
    this.errors = [];
    this.warnings = [];
    this.symbolTable.clear();

    this.checkStatements(program.statements);
  }

  private checkStatements(statements: ASTNode[]): void {
    for (const stmt of statements) {
      this.checkStatement(stmt);
    }
  }

  private checkStatement(stmt: ASTNode): void {
    if (isQueryNode(stmt)) {
      const varName = stmt.varName;
      this.define(varName, { type: 'Query', dimension: 768 });
    } else if (isEncodeNode(stmt)) {
      const inputVar = stmt.inputVar;
      const outputVar = stmt.outputVar;

      const inputType = this.lookup(inputVar);
      if (!inputType) {
        this.addError(`Variable '${inputVar}' is not defined`);
        return;
      }

      if (inputType.type !== 'Query') {
        this.addWarning(
          `Encode expects Query type, got ${inputType.type} for '${inputVar}'`
        );
      }

      this.define(outputVar, { type: 'Latent', dimension: 512 });
    } else if (isPathNode(stmt)) {
      const inputVar = stmt.inputVar;
      const outputVar = stmt.outputVar;
      const pathType = stmt.pathType;

      const inputType = this.lookup(inputVar);
      if (!inputType) {
        this.addError(`Variable '${inputVar}' is not defined`);
        return;
      }

      if (inputType.type !== 'Latent') {
        this.addError(
          `Path expects Latent type, got ${inputType.type} for '${inputVar}'`
        );
        return;
      }

      this.define(outputVar, {
        type: 'Path',
        dimension: 512,
        constraints: [pathType],
      });
    } else if (isWeightNode(stmt)) {
      if (stmt.weights) {
        const { alpha, beta, gamma } = stmt.weights;

        if (alpha < 0 || alpha > 1 || beta < 0 || beta > 1 || gamma < 0 || gamma > 1) {
          this.addError(
            `Weight values must be in [0, 1], got α=${alpha}, β=${beta}, γ=${gamma}`
          );
          return;
        }

        const sum = alpha + beta + gamma;
        if (Math.abs(sum - 1.0) > 1e-6) {
          this.addError(
            `Weight simplex constraint violated: α + β + γ = ${sum}, expected 1.0`
          );
          return;
        }

        this.define('weights', {
          type: 'Weight',
          constraints: ['simplex', 'normalized'],
        });
      }
    } else if (isEnsembleNode(stmt)) {
      const [path1, path2, path3] = stmt.pathVars;
      const weightsVar = stmt.weightsVar;
      const outputVar = stmt.outputVar;

      const pathVars = [path1, path2, path3];
      for (const pathVar of pathVars) {
        const pathType = this.lookup(pathVar);
        if (!pathType) {
          this.addError(`Variable '${pathVar}' is not defined`);
          return;
        }
        if (pathType.type !== 'Path') {
          this.addError(
            `Ensemble expects Path type, got ${pathType.type} for '${pathVar}'`
          );
          return;
        }
      }

      const weightType = this.lookup(weightsVar);
      if (!weightType) {
        this.addWarning(`Weight variable '${weightsVar}' not found, assuming default weights`);
      } else if (weightType.type !== 'Weight') {
        this.addError(
          `Ensemble expects Weight type, got ${weightType.type} for '${weightsVar}'`
        );
        return;
      }

      this.define(outputVar, {
        type: 'Ensemble',
        dimension: 512,
        constraints: ['composite'],
      });
    } else if (isCritiqueNode(stmt)) {
      const inputVar = stmt.inputVar;
      const outputVar = stmt.outputVar;

      const inputType = this.lookup(inputVar);
      if (!inputType) {
        this.addError(`Variable '${inputVar}' is not defined`);
        return;
      }

      if (inputType.type !== 'Ensemble') {
        this.addWarning(
          `Critique typically takes Ensemble input, got ${inputType.type} for '${inputVar}'`
        );
      }

      this.define(outputVar, {
        type: 'Critique',
        constraints: ['range', '[-1, 1]'],
      });
    } else if (isSampleNode(stmt)) {
      const inputVar = stmt.inputVar;
      const outputVar = stmt.outputVar;
      const threshold = stmt.threshold;

      const inputType = this.lookup(inputVar);
      if (!inputType) {
        this.addError(`Variable '${inputVar}' is not defined`);
        return;
      }

      if (threshold !== undefined) {
        if (threshold < 0 || threshold > 1) {
          this.addError(
            `Sampling threshold must be in [0, 1], got ${threshold}`
          );
          return;
        }
      }

      this.define(outputVar, {
        type: 'Output',
        constraints: ['token', 'vocabulary'],
      });
    } else if (isDetokenizeNode(stmt)) {
      const inputVar = stmt.inputVar;
      const outputVar = stmt.outputVar;

      const inputType = this.lookup(inputVar);
      if (!inputType) {
        this.addError(`Variable '${inputVar}' is not defined`);
        return;
      }

      this.define(outputVar, {
        type: 'Output',
        constraints: ['string', 'korean'],
      });
    }
  }

  private define(name: string, type: TypeInfo): void {
    this.symbolTable.set(name, type);
  }

  private lookup(name: string): TypeInfo | null {
    const type = this.symbolTable.get(name);
    return type || null;
  }

  private addError(message: string): void {
    this.errors.push(message);
  }

  private addWarning(message: string): void {
    this.warnings.push(message);
  }

  getErrors(): string[] {
    return this.errors;
  }

  getWarnings(): string[] {
    return this.warnings;
  }

  getSymbolTable(): Map<string, TypeInfo> {
    return new Map(this.symbolTable);
  }

  getTypeOf(name: string): MindLangType | null {
    const info = this.lookup(name);
    return info ? info.type : null;
  }

  isValid(): boolean {
    return this.errors.length === 0;
  }
}

export function check(program: Program): {
  valid: boolean;
  errors: string[];
  warnings: string[];
  symbolTable: Map<string, TypeInfo>;
} {
  const checker = new Checker();
  checker.check(program);

  return {
    valid: checker.isValid(),
    errors: checker.getErrors(),
    warnings: checker.getWarnings(),
    symbolTable: checker.getSymbolTable(),
  };
}

export function typeInference(program: Program): Map<string, TypeInfo> {
  const checker = new Checker();
  checker.check(program);
  return checker.getSymbolTable();
}

export function validateConstraints(program: Program): {
  valid: boolean;
  errors: string[];
} {
  const checker = new Checker();
  checker.check(program);

  return {
    valid: checker.isValid(),
    errors: checker.getErrors(),
  };
}
