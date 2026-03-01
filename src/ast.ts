export type NodeId = string | number;

export interface BaseNode {
  id: NodeId;
  nodeType: string;
  line?: number;
  column?: number;
}

export interface QueryNode extends BaseNode {
  nodeType: 'QueryNode';
  varName: string;
  embedding?: number[];
  semanticContent?: string;
  confidence?: number;
}

export interface EncodeNode extends BaseNode {
  nodeType: 'EncodeNode';
  inputVar: string;
  outputVar: string;
  latentDim?: number;
}

export interface PathNode extends BaseNode {
  nodeType: 'PathNode';
  pathType: 'analytical' | 'creative' | 'empirical';
  inputVar: string;
  outputVar: string;
}

export interface WeightNode extends BaseNode {
  nodeType: 'WeightNode';
  inputVar: string;
  weights?: {
    alpha: number;
    beta: number;
    gamma: number;
  };
}

export interface EnsembleNode extends BaseNode {
  nodeType: 'EnsembleNode';
  pathVars: [string, string, string];
  weightsVar: string;
  outputVar: string;
}

export interface CritiqueNode extends BaseNode {
  nodeType: 'CritiqueNode';
  inputVar: string;
  outputVar: string;
  confidenceThreshold?: number;
}

export interface SampleNode extends BaseNode {
  nodeType: 'SampleNode';
  inputVar: string;
  outputVar: string;
  threshold?: number;
  temperature?: number;
}

export interface DetokenizeNode extends BaseNode {
  nodeType: 'DetokenizeNode';
  inputVar: string;
  outputVar: string;
  language?: string;
}

export type ASTNode =
  | QueryNode
  | EncodeNode
  | PathNode
  | WeightNode
  | EnsembleNode
  | CritiqueNode
  | SampleNode
  | DetokenizeNode;

export interface Program {
  statements: ASTNode[];
}

export function getNodeType(node: ASTNode): string {
  return node.nodeType;
}

export function isQueryNode(node: ASTNode): node is QueryNode {
  return node.nodeType === 'QueryNode';
}

export function isEncodeNode(node: ASTNode): node is EncodeNode {
  return node.nodeType === 'EncodeNode';
}

export function isPathNode(node: ASTNode): node is PathNode {
  return node.nodeType === 'PathNode';
}

export function isWeightNode(node: ASTNode): node is WeightNode {
  return node.nodeType === 'WeightNode';
}

export function isEnsembleNode(node: ASTNode): node is EnsembleNode {
  return node.nodeType === 'EnsembleNode';
}

export function isCritiqueNode(node: ASTNode): node is CritiqueNode {
  return node.nodeType === 'CritiqueNode';
}

export function isSampleNode(node: ASTNode): node is SampleNode {
  return node.nodeType === 'SampleNode';
}

export function isDetokenizeNode(node: ASTNode): node is DetokenizeNode {
  return node.nodeType === 'DetokenizeNode';
}

export function createQueryNode(
  id: NodeId,
  varName: string,
  options?: Partial<QueryNode>
): QueryNode {
  return {
    id,
    nodeType: 'QueryNode',
    varName,
    ...options,
  };
}

export function createEncodeNode(
  id: NodeId,
  inputVar: string,
  outputVar: string,
  options?: Partial<EncodeNode>
): EncodeNode {
  return {
    id,
    nodeType: 'EncodeNode',
    inputVar,
    outputVar,
    ...options,
  };
}

export function createPathNode(
  id: NodeId,
  pathType: 'analytical' | 'creative' | 'empirical',
  inputVar: string,
  outputVar: string,
  options?: Partial<PathNode>
): PathNode {
  return {
    id,
    nodeType: 'PathNode',
    pathType,
    inputVar,
    outputVar,
    ...options,
  };
}

export function createWeightNode(
  id: NodeId,
  inputVar: string,
  options?: Partial<WeightNode>
): WeightNode {
  return {
    id,
    nodeType: 'WeightNode',
    inputVar,
    ...options,
  };
}

export function createEnsembleNode(
  id: NodeId,
  pathVars: [string, string, string],
  weightsVar: string,
  outputVar: string,
  options?: Partial<EnsembleNode>
): EnsembleNode {
  return {
    id,
    nodeType: 'EnsembleNode',
    pathVars,
    weightsVar,
    outputVar,
    ...options,
  };
}

export function createCritiqueNode(
  id: NodeId,
  inputVar: string,
  outputVar: string,
  options?: Partial<CritiqueNode>
): CritiqueNode {
  return {
    id,
    nodeType: 'CritiqueNode',
    inputVar,
    outputVar,
    ...options,
  };
}

export function createSampleNode(
  id: NodeId,
  inputVar: string,
  outputVar: string,
  options?: Partial<SampleNode>
): SampleNode {
  return {
    id,
    nodeType: 'SampleNode',
    inputVar,
    outputVar,
    ...options,
  };
}

export function createDetokenizeNode(
  id: NodeId,
  inputVar: string,
  outputVar: string,
  options?: Partial<DetokenizeNode>
): DetokenizeNode {
  return {
    id,
    nodeType: 'DetokenizeNode',
    inputVar,
    outputVar,
    ...options,
  };
}

export function printAST(node: ASTNode, depth: number = 0): string {
  const indent = '  '.repeat(depth);

  switch (node.nodeType) {
    case 'QueryNode': {
      const qn = node as QueryNode;
      return `${indent}QueryNode: ${qn.varName}`;
    }
    case 'EncodeNode': {
      const en = node as EncodeNode;
      return `${indent}EncodeNode: ${en.inputVar} -> ${en.outputVar}`;
    }
    case 'PathNode': {
      const pn = node as PathNode;
      return `${indent}PathNode(${pn.pathType}): ${pn.inputVar} -> ${pn.outputVar}`;
    }
    case 'WeightNode': {
      const wn = node as WeightNode;
      const weights = wn.weights
        ? ` [α=${wn.weights.alpha.toFixed(2)}, β=${wn.weights.beta.toFixed(2)}, γ=${wn.weights.gamma.toFixed(2)}]`
        : '';
      return `${indent}WeightNode: ${wn.inputVar}${weights}`;
    }
    case 'EnsembleNode': {
      const ens = node as EnsembleNode;
      return `${indent}EnsembleNode: (${ens.pathVars.join(', ')}) with ${ens.weightsVar} -> ${ens.outputVar}`;
    }
    case 'CritiqueNode': {
      const cn = node as CritiqueNode;
      return `${indent}CritiqueNode: ${cn.inputVar} -> ${cn.outputVar}`;
    }
    case 'SampleNode': {
      const sn = node as SampleNode;
      return `${indent}SampleNode: ${sn.inputVar} -> ${sn.outputVar}`;
    }
    case 'DetokenizeNode': {
      const dn = node as DetokenizeNode;
      return `${indent}DetokenizeNode: ${dn.inputVar} -> ${dn.outputVar}`;
    }
    default:
      return `${indent}UnknownNode`;
  }
}

export function printProgram(program: Program): string {
  return program.statements.map((node) => printAST(node, 0)).join('\n');
}

export function collectVariables(program: Program): Set<string> {
  const vars = new Set<string>();

  for (const node of program.statements) {
    switch (node.nodeType) {
      case 'QueryNode':
        vars.add((node as QueryNode).varName);
        break;
      case 'EncodeNode':
        vars.add((node as EncodeNode).outputVar);
        break;
      case 'PathNode':
        vars.add((node as PathNode).outputVar);
        break;
      case 'WeightNode':
        break;
      case 'EnsembleNode':
        vars.add((node as EnsembleNode).outputVar);
        break;
      case 'CritiqueNode':
        vars.add((node as CritiqueNode).outputVar);
        break;
      case 'SampleNode':
        vars.add((node as SampleNode).outputVar);
        break;
      case 'DetokenizeNode':
        vars.add((node as DetokenizeNode).outputVar);
        break;
    }
  }

  return vars;
}

export function getNodeInputVariables(node: ASTNode): string[] {
  switch (node.nodeType) {
    case 'QueryNode':
      return [];
    case 'EncodeNode':
      return [(node as EncodeNode).inputVar];
    case 'PathNode':
      return [(node as PathNode).inputVar];
    case 'WeightNode':
      return [(node as WeightNode).inputVar];
    case 'EnsembleNode': {
      const ens = node as EnsembleNode;
      return [...ens.pathVars, ens.weightsVar];
    }
    case 'CritiqueNode':
      return [(node as CritiqueNode).inputVar];
    case 'SampleNode':
      return [(node as SampleNode).inputVar];
    case 'DetokenizeNode':
      return [(node as DetokenizeNode).inputVar];
    default:
      return [];
  }
}

export function getNodeOutputVariable(node: ASTNode): string | null {
  switch (node.nodeType) {
    case 'QueryNode':
      return (node as QueryNode).varName;
    case 'EncodeNode':
      return (node as EncodeNode).outputVar;
    case 'PathNode':
      return (node as PathNode).outputVar;
    case 'WeightNode':
      return null;
    case 'EnsembleNode':
      return (node as EnsembleNode).outputVar;
    case 'CritiqueNode':
      return (node as CritiqueNode).outputVar;
    case 'SampleNode':
      return (node as SampleNode).outputVar;
    case 'DetokenizeNode':
      return (node as DetokenizeNode).outputVar;
    default:
      return null;
  }
}
