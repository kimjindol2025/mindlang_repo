#!/usr/bin/env node
/**
 * MindLang CLI - Main Entry Point
 *
 * A multi-path intelligent reasoning language CLI
 * Supports various execution modes: execution, bytecode dump, tracing, profiling
 *
 * Usage:
 *   npx ts-node src/main.ts <file.ml>                    # Execute
 *   npx ts-node src/main.ts <file.ml> --dump-bc         # Dump bytecode
 *   npx ts-node src/main.ts <file.ml> --trace           # Execute with tracing
 *   npx ts-node src/main.ts <file.ml> --profile         # Profile execution
 */

import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { parse } from './parser';
import { isQueryNode } from './ast';
import { Checker } from './checker';
import { Compiler, ASTBuilder } from './compiler';
import { VirtualMachine, VMConfig } from './vm';

// Type definitions
interface ProgramOptions {
  dumpBytecode: boolean;
  trace: boolean;
  profile: boolean;
  verbose: boolean;
  file: string;
}

interface ParsedProgram {
  name: string;
  queries: string[];
  operations: Operation[];
  bytecode: string[];
}

interface Operation {
  type: string;
  args: any[];
  lineNumber: number;
}

interface ExecutionContext {
  variables: Map<string, any>;
  output: string[];
  startTime: number;
  endTime?: number;
  operationCount: number;
  bytecodeExecuted: string[];
}

// Parser for MindLang .ml files
class MindLangParser {
  static parse(content: string): ParsedProgram {
    const lines = content.split('\n').filter(l => !l.trim().startsWith('(*') && l.trim().length > 0);
    const operations: Operation[] = [];
    const queries: string[] = [];
    let programName = 'main';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      if (line.startsWith('program ')) {
        programName = line.match(/program\s+(\w+)/)?.[1] || 'main';
      } else if (line.startsWith('query ')) {
        const match = line.match(/query\s+"([^"]+)"/);
        if (match) queries.push(match[1]);
      } else if (line.includes('->')) {
        const operation = this.parseOperation(line, i);
        if (operation) operations.push(operation);
      } else if (line.includes('=') && !line.startsWith('program')) {
        const eqIdx = line.indexOf('=');
        const lv = line.substring(0, eqIdx).trim();
        const rv = line.substring(eqIdx + 1).trim();
        operations.push({ type: 'ASSIGN', args: [lv, rv], lineNumber: i });
      }
    }

    const bytecode = this.generateBytecode(operations);

    return { name: programName, queries, operations, bytecode };
  }

  private static parseOperation(line: string, lineNumber: number): Operation | null {
    const [left, right] = line.split('->').map(s => s.trim());

    if (left.startsWith('encode')) {
      return {
        type: 'ENCODE',
        args: [left.split(' ')[1], right],
        lineNumber
      };
    } else if (left.startsWith('sample')) {
      const parts = left.match(/sample\s+(\w+)\s+([\d.]+)/);
      return {
        type: 'SAMPLE',
        args: [parts?.[1], parseFloat(parts?.[2] || '0.5')],
        lineNumber
      };
    } else if (left.startsWith('detokenize')) {
      return {
        type: 'DETOKENIZE',
        args: [left.split(' ')[1]],
        lineNumber
      };
    } else if (left.startsWith('fork')) {
      return {
        type: 'FORK',
        args: [left.split(' ')[1]],
        lineNumber
      };
    } else if (left.startsWith('ensemble')) {
      return {
        type: 'ENSEMBLE',
        args: [left],
        lineNumber
      };
    } else if (left.startsWith('critique')) {
      return {
        type: 'CRITIQUE',
        args: [left.split(' ')[1]],
        lineNumber
      };
    }

    return {
      type: 'ASSIGN',
      args: [left, right],
      lineNumber
    };
  }

  private static generateBytecode(operations: Operation[]): string[] {
    return operations.map((op, idx) => {
      return `[${idx}] ${op.type} ${op.args.join(' ')}`;
    });
  }
}

// Interpreter for executing parsed programs
class MindLangInterpreter {
  private context: ExecutionContext;
  private program: ParsedProgram;
  private trace: boolean;

  constructor(program: ParsedProgram, trace: boolean = false) {
    this.program = program;
    this.trace = trace;
    this.context = {
      variables: new Map(),
      output: [],
      startTime: performance.now(),
      operationCount: 0,
      bytecodeExecuted: []
    };
  }

  execute(): ExecutionContext {
    if (this.trace) {
      console.log(chalk.cyan(`\n[TRACE] Starting execution of program: ${this.program.name}\n`));
    }

    // Process queries
    for (const query of this.program.queries) {
      this.context.variables.set('input_query', query);
      if (this.trace) {
        console.log(chalk.gray(`  [QUERY] "${query}"`));
      }
    }

    // If only queries exist (no other operations), count them as executed
    if (this.program.operations.length === 0) {
      this.context.operationCount += this.program.queries.length;
    }

    // Execute operations
    for (const operation of this.program.operations) {
      this.executeOperation(operation);
    }

    this.context.endTime = performance.now();
    return this.context;
  }

  private executeOperation(operation: Operation): void {
    this.context.operationCount++;
    const bytecodeStr = `[${this.context.operationCount - 1}] ${operation.type}`;
    this.context.bytecodeExecuted.push(bytecodeStr);

    if (this.trace) {
      console.log(chalk.gray(`  [${operation.lineNumber}] ${operation.type} ${operation.args.join(' ')}`));
    }

    switch (operation.type) {
      case 'ENCODE': {
        const variable = operation.args[0];
        const targetVar = (operation.args[1] as string) || variable;
        const input = this.context.variables.get('input_query') || 'default';
        const encoded = this.simulateEncoding(input);
        this.context.variables.set(targetVar, encoded);
        if (this.trace) console.log(chalk.green(`    → ${targetVar} = ${JSON.stringify(encoded).substring(0, 50)}...`));
        break;
      }

      case 'SAMPLE': {
        const variable = operation.args[0];
        const temperature = operation.args[1];
        const encoded = this.context.variables.get(variable) || [];
        const sampled = this.simulateSampling(encoded, temperature);
        this.context.variables.set(`${variable}_sampled`, sampled);
        if (this.trace) console.log(chalk.green(`    → sampled with temp ${temperature}`));
        break;
      }

      case 'DETOKENIZE': {
        const variable = operation.args[0];
        const value = this.context.variables.get(variable) || 'output';
        const detokenized = this.simulateDetokenization(value);
        this.context.output.push(detokenized);
        if (this.trace) console.log(chalk.green(`    → "${detokenized}"`));
        break;
      }

      case 'FORK': {
        if (this.trace) console.log(chalk.blue(`    → Forking into 3 branches`));
        this.context.variables.set('branched', true);
        break;
      }

      case 'ENSEMBLE': {
        if (this.trace) console.log(chalk.blue(`    → Combining ensemble results`));
        break;
      }

      case 'CRITIQUE': {
        if (this.trace) console.log(chalk.yellow(`    → Applying critique`));
        break;
      }

      case 'ASSIGN': {
        const [left, right] = operation.args;
        const value = this.evaluateExpression(right);
        this.context.variables.set(left, value);
        if (this.trace) console.log(chalk.green(`    → ${left} assigned`));
        break;
      }
    }
  }

  private simulateEncoding(input: string): number[] {
    // Simulate encoding by hashing input to vector
    const seed = input.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
    const vector: number[] = [];
    for (let i = 0; i < 8; i++) {
      vector.push(Math.sin((seed + i) * 0.1) * 100);
    }
    return vector;
  }

  private simulateSampling(encoded: number[], temperature: number): string {
    // Simulate sampling from encoded representation
    const maxIndex = encoded.reduce((maxIdx, val, idx) => encoded[maxIdx] < val ? idx : maxIdx, 0);
    return `token_${maxIndex}`;
  }

  private simulateDetokenization(value: any): string {
    // Simulate detokenization
    if (Array.isArray(value)) {
      return `[数値結果] ${value.map(v => v.toFixed(2)).join(', ')}`;
    }
    return String(value);
  }

  private evaluateExpression(expr: string): any {
    if (expr.includes('+')) {
      const parts = expr.split('+').map(p => this.context.variables.get(p.trim()) || 0);
      return parts.reduce((a, b) => a + b, 0);
    }
    return this.context.variables.get(expr.trim()) || expr;
  }
}

// CLI Handler
class MindLangCLI {
  static parseArguments(): ProgramOptions {
    const args = process.argv.slice(2);

    if (args.length === 0) {
      this.printUsage();
      process.exit(1);
    }

    const options: ProgramOptions = {
      dumpBytecode: args.includes('--dump-bc'),
      trace: args.includes('--trace'),
      profile: args.includes('--profile'),
      verbose: args.includes('--verbose'),
      file: args.find(arg => !arg.startsWith('--')) || ''
    };

    return options;
  }

  static printUsage(): void {
    console.log(chalk.bold.cyan('\nMindLang CLI v0.1.0'));
    console.log(chalk.cyan('Multi-path Intelligent Reasoning Language\n'));
    console.log(chalk.bold('Usage:'));
    console.log('  npx ts-node src/main.ts <file.ml> [options]\n');
    console.log(chalk.bold('Options:'));
    console.log('  --dump-bc    Dump bytecode representation');
    console.log('  --trace      Show execution trace');
    console.log('  --profile    Show performance profile');
    console.log('  --verbose    Verbose output');
    console.log('  --help       Show this help message\n');
    console.log(chalk.bold('Examples:'));
    console.log('  npx ts-node src/main.ts examples/hello.ml');
    console.log('  npx ts-node src/main.ts examples/parallel_reasoning.ml --trace');
    console.log('  npx ts-node src/main.ts examples/ensemble_voting.ml --dump-bc\n');
  }

  static readFile(filePath: string): string {
    try {
      return fs.readFileSync(filePath, 'utf-8');
    } catch (error) {
      console.error(chalk.red(`Error: Cannot read file "${filePath}"`));
      process.exit(1);
    }
  }

  static run(): void {
    const options = this.parseArguments();

    if (options.file === '') {
      this.printUsage();
      process.exit(1);
    }

    const resolvedPath = path.resolve(options.file);
    const content = this.readFile(resolvedPath);

    try {
      const program = MindLangParser.parse(content);

      if (options.dumpBytecode) {
        this.dumpBytecode(program);
      }

      const profileStart = performance.now();
      const interpreter = new MindLangInterpreter(program, options.trace);
      const context = interpreter.execute();
      const profileEnd = performance.now();

      this.printResults(context, profileEnd - profileStart);

      if (options.profile) {
        this.printProfile(context, profileEnd - profileStart);
      }
    } catch (error) {
      console.error(chalk.red(`\nExecution error: ${error}`));
      process.exit(1);
    }
  }

  private static dumpBytecode(program: ParsedProgram): void {
    console.log(chalk.bold.magenta('\n=== Bytecode Dump ===\n'));
    console.log(chalk.cyan(`Program: ${program.name}`));
    console.log(chalk.cyan(`Operations: ${program.operations.length}\n`));
    program.bytecode.forEach(bc => console.log(chalk.gray(bc)));
    console.log();
  }

  private static printResults(context: ExecutionContext, executionTime: number): void {
    console.log(chalk.bold.cyan('\n=== Execution Results ===\n'));

    if (context.output.length > 0) {
      console.log(chalk.bold('Output:'));
      context.output.forEach(line => console.log(chalk.green(line)));
    }

    console.log(chalk.bold('\nStatistics:'));
    console.log(`  Operations executed: ${context.operationCount}`);
    console.log(`  Variables set: ${context.variables.size}`);
    console.log(`  Execution time: ${executionTime.toFixed(2)}ms`);
    console.log(`  Output lines: ${context.output.length}\n`);
  }

  private static printProfile(context: ExecutionContext, executionTime: number): void {
    console.log(chalk.bold.yellow('\n=== Performance Profile ===\n'));
    console.log(chalk.yellow(`Total time: ${executionTime.toFixed(2)}ms`));
    console.log(chalk.yellow(`Operations: ${context.operationCount}`));
    console.log(chalk.yellow(`Time per operation: ${(executionTime / context.operationCount).toFixed(3)}ms`));
    console.log(chalk.yellow(`Output size: ${JSON.stringify(context.output).length} bytes\n`));
  }
}

// ============================================================================
// MindLangRunner: Layer 1 (Compiler) ↔ Layer 2 (VM) 연결 파이프라인
// ============================================================================

export interface RunnerResult {
  success: boolean;
  output: number[] | null;
  executionTime: number;
  bytecodeCount: number;
  errors: string[];
  warnings: string[];
}

/**
 * MindLang 소스 코드를 완전한 컴파일러 파이프라인으로 실행:
 * Lexer → Parser → TypeChecker → Compiler → VirtualMachine
 */
export class MindLangRunner {
  static run(source: string, config: VMConfig = {}): RunnerResult {
    const startTime = performance.now();
    const errors: string[] = [];
    const warnings: string[] = [];

    try {
      // Step 1: Lexing + Parsing → AST (text-level)
      const parsedAst = parse(source);

      // Step 2: Type checking
      const checker = new Checker();
      checker.check(parsedAst);
      const checkErrors = checker.getErrors();
      const checkWarnings = checker.getWarnings();
      warnings.push(...checkWarnings);

      if (checkErrors.length > 0) {
        errors.push(...checkErrors);
        return {
          success: false,
          output: null,
          executionTime: performance.now() - startTime,
          bytecodeCount: 0,
          errors,
          warnings,
        };
      }

      // Step 3: Bridge Layer 1 AST → Layer 2 (Compiler) AST
      // Extract query text from parsed AST, use ASTBuilder for compiler-compatible format
      const queryNode = parsedAst.statements.find(s => isQueryNode(s));
      const queryText = (queryNode && isQueryNode(queryNode) && queryNode.semanticContent)
        ? queryNode.semanticContent
        : 'default_query';
      const compilerAst = ASTBuilder.createCompleteProgram(queryText);

      // Step 4: Compile to bytecode
      const compiler = new Compiler();
      const bytecodeProgram = compiler.compile(compilerAst);

      // Step 4: Execute on virtual machine
      const vm = new VirtualMachine(config);
      vm.loadProgram(bytecodeProgram);
      const output = vm.execute();

      const endTime = performance.now();

      return {
        success: true,
        output,
        executionTime: endTime - startTime,
        bytecodeCount: bytecodeProgram.instructions.length,
        errors: [],
        warnings,
      };
    } catch (err) {
      errors.push(String(err));
      return {
        success: false,
        output: null,
        executionTime: performance.now() - startTime,
        bytecodeCount: 0,
        errors,
        warnings,
      };
    }
  }
}

// Main execution
if (require.main === module) {
  MindLangCLI.run();
}

export { MindLangParser, MindLangInterpreter, MindLangCLI };
